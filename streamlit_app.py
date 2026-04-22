from __future__ import annotations

import json
import os
from pathlib import Path

from oxidus.bootstrap import ensure_runtime_dependencies

ensure_runtime_dependencies(
    Path(__file__).with_name("requirements.txt"),
    modules=("pandas", "plotly", "requests"),
)

import pandas as pd
import streamlit as st

from oxidus.ai import AISettings, generate_ai_recommendation
from oxidus.models import PrinterSpec
from oxidus.parts_catalog import build_parts_list, printable_parts, resolve_parts, supplier_modes
from oxidus.print_bridge import TargetConfig, command_available, normalize_base_url, send_gcode, slice_with_orca
from oxidus.render import build_printer_figure
from oxidus.stl import make_box_stl


st.set_page_config(page_title="Oxidus Print!", page_icon="🛠️", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Archivo+Black&display=swap');

:root {
    --ox-dark: #0B1D26;
    --ox-deep: #16313D;
    --ox-accent: #08A4BD;
    --ox-fire: #F4A261;
    --ox-light: #F2F7F8;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.main {
    background: radial-gradient(circle at 10% 0%, #E9F5F8, #F6FAFB 45%, #F0F5F7 100%);
}

.hero {
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, var(--ox-dark), var(--ox-deep));
    color: var(--ox-light);
    border: 1px solid rgba(8, 164, 189, 0.35);
    box-shadow: 0 10px 35px rgba(11, 29, 38, 0.18);
    margin-bottom: 1.2rem;
}

.hero h1 {
    font-family: 'Archivo Black', sans-serif;
    letter-spacing: 0.5px;
    margin: 0;
}

.hero p {
    margin: 0.4rem 0 0 0;
    opacity: 0.95;
}

.pill {
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 700;
    margin-top: 0.7rem;
    color: var(--ox-dark);
    background: var(--ox-fire);
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
    <h1>Oxidus Print!</h1>
    <p>Design your dream modular printer with live XYZ scaling, a generated build sheet, and export-ready printable part mockups.</p>
    <span class="pill">Voron-inspired open hardware workflow</span>
    <p><strong>Built by PartonDemand</strong></p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Build Envelope")
    preset = st.selectbox(
        "Base Profile",
        ["Custom", "Compact 180", "Voron-like 250", "Voron-like 300", "Large 350"],
    )

    defaults = {
        "Custom": (250, 250, 250),
        "Compact 180": (180, 180, 210),
        "Voron-like 250": (250, 250, 250),
        "Voron-like 300": (300, 300, 300),
        "Large 350": (350, 350, 350),
    }
    default_x, default_y, default_z = defaults[preset]

    x_mm = st.slider("X axis (mm)", min_value=120, max_value=500, value=default_x, step=10)
    y_mm = st.slider("Y axis (mm)", min_value=120, max_value=500, value=default_y, step=10)
    z_mm = st.slider("Z axis (mm)", min_value=150, max_value=600, value=default_z, step=10)

    st.header("Sourcing Logic")

    raw_parts = build_parts_list(PrinterSpec(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm))
    supplier_mode = st.selectbox(
        "Supplier Mode",
        supplier_modes(raw_parts),
        index=0,
        help="Auto is the default path and will scale better as new vendors are added.",
    )

    st.header("AI Intuition")
    default_ai_base_url = os.getenv("OXIDUS_AI_BASE_URL", "")
    default_ai_model = os.getenv("OXIDUS_AI_MODEL", "gptoss20b")
    ai_enabled = st.toggle("Use Network AI", value=bool(default_ai_base_url))
    ai_base_url = st.text_input(
        "AI Endpoint",
        value=default_ai_base_url,
        placeholder="https://your-network-endpoint/v1",
        help="Use an OpenAI-compatible network endpoint for your remote GPTOSS20B deployment.",
    )
    ai_model = st.text_input("Model", value=default_ai_model)

    st.caption("Source references: https://vorondesign.com/")
    st.caption("Supplier refs: https://dllpdf.com/ and https://www.phaetus.com/en-us")
    st.caption("AI model target: GPTOSS20B on the network")

spec = PrinterSpec(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm)
parts = resolve_parts(raw_parts, supplier_mode)
printable = printable_parts(parts)

ai_settings = AISettings(enabled=ai_enabled, base_url=ai_base_url, model=ai_model)

try:
    ai_guidance = generate_ai_recommendation(spec, parts, ai_settings)
    ai_error = None
except Exception as exc:
    ai_guidance = {
        "summary": "The network AI endpoint is not currently reachable. Oxidus Print is using local heuristics instead.",
        "watchouts": [
            "Validate frame stiffness against your target acceleration.",
            "Use enclosure-safe materials for printed structural parts.",
        ],
        "recommended_materials": ["ABS/ASA for hot-zone printed parts", "PETG for cable chain and low-heat brackets"],
        "next_step": "Verify the network endpoint and confirm the GPTOSS20B model identifier exposed by your inference service.",
        "status": "fallback",
    }
    ai_error = str(exc)

tab_studio, tab_sheet, tab_stl, tab_print, tab_ai, tab_inspiration, tab_data = st.tabs(
    ["3D Studio", "Build Sheet", "STL Lab", "Print Bridge", "AI Studio", "Inspiration", "Project Data"]
)

with tab_studio:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Build X", f"{spec.x_mm} mm")
    col_b.metric("Build Y", f"{spec.y_mm} mm")
    col_c.metric("Build Z", f"{spec.z_mm} mm")
    st.metric("Build Volume", f"{spec.volume_liters:.1f} L")

    fig = build_printer_figure(spec)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "3D preview is unavailable because Plotly is not installed in this environment. "
            "Install dependencies from requirements.txt to enable the interactive renderer."
        )
    st.info(
        "This preview is a parametric concept model for planning dimensions and BOM scale. "
        "It is not a final mechanical validation."
    )

with tab_sheet:
    st.subheader("Generated Build Sheet")
    st.markdown(f"**Supplier mode:** {supplier_mode}")
    st.markdown("**Sourcing shortlist:** [DLLPDF](https://dllpdf.com/) and [Phaetus](https://www.phaetus.com/en-us)")
    sheet_df = pd.DataFrame(
        [
            {
                "Part": p.name,
                "Qty": p.qty,
                "Category": p.category,
                "Printable": "Yes" if p.printable else "No",
                "Material": p.material,
                "Recommended Source": p.source,
                "Supplier": p.supplier.name,
                "Supplier URL": p.supplier.url,
                "Nominal Dimensions (mm)": f"{p.dimensions_mm[0]:.1f} x {p.dimensions_mm[1]:.1f} x {p.dimensions_mm[2]:.1f}",
                "Print/Build Notes": p.print_notes,
            }
            for p in parts
        ]
    )
    st.dataframe(
        sheet_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Supplier URL": st.column_config.LinkColumn("Supplier URL"),
        },
    )

    extrusion_cutlist = pd.DataFrame(
        [
            {"Profile": "2020", "Length (mm)": spec.x_mm + 140, "Qty": 4, "Use": "X frame rails"},
            {"Profile": "2020", "Length (mm)": spec.y_mm + 140, "Qty": 4, "Use": "Y frame rails"},
            {"Profile": "2020", "Length (mm)": spec.z_mm + 190, "Qty": 4, "Use": "Vertical posts"},
        ]
    )
    st.markdown("#### Extrusion Cut List")
    st.table(extrusion_cutlist)

    st.download_button(
        "Download Build Sheet (CSV)",
        data=sheet_df.to_csv(index=False).encode("utf-8"),
        file_name=f"oxidus_build_sheet_{spec.x_mm}x{spec.y_mm}x{spec.z_mm}.csv",
        mime="text/csv",
    )

with tab_stl:
    st.subheader("Printable Parts STL Exports")
    st.caption(
        "STLs below are parametric starter solids sized from your envelope. "
        "Swap in official or community-tested geometry before production use."
    )

    for idx, part in enumerate(printable):
        dim_x, dim_y, dim_z = part.dimensions_mm
        st.markdown(f"**{part.name}** x{part.qty}")
        st.write(f"Material: {part.material}")
        st.write(f"Supplier: [{part.supplier.name}]({part.supplier.url})")
        st.write(f"Guidance: {part.print_notes}")

        stl_bytes = make_box_stl(
            name=part.name.lower().replace(" ", "_"),
            x_mm=dim_x,
            y_mm=dim_y,
            z_mm=dim_z,
        )
        st.download_button(
            label=f"Download STL: {part.name}",
            data=stl_bytes,
            file_name=f"oxidus_{part.name.lower().replace(' ', '_')}_{spec.x_mm}x{spec.y_mm}x{spec.z_mm}.stl",
            mime="model/stl",
            key=f"stl_{idx}",
        )
        st.divider()

with tab_print:
    st.subheader("OrcaSlicer Print Bridge")
    st.caption(
        "Browser-to-printer workflow: upload STL/OBJ or G-code, optionally slice via Orca CLI, then send to a printer host by IP."
    )

    col_backend, col_start = st.columns([2, 1])
    backend = col_backend.selectbox("Print Backend", ["OctoPrint", "Moonraker"], index=0)
    auto_start = col_start.toggle("Auto Start Print", value=True)

    raw_target = st.text_input(
        "Printer Host/IP",
        placeholder="192.168.1.55:7125 or https://printer.local",
        help="For OctoPrint include the server port. For Moonraker include its API port.",
    )
    target_url = normalize_base_url(raw_target)
    api_key = st.text_input(
        "API Key (OctoPrint only)",
        type="password",
        help="Leave blank for Moonraker or if your OctoPrint instance allows anonymous uploads.",
    )

    upload = st.file_uploader("Upload STL, OBJ, or G-code", type=["stl", "obj", "gcode"])

    st.markdown("#### Orca CLI Slicing")
    slice_stl = st.toggle("Slice STL with Orca before sending", value=True)
    orca_cmd = st.text_input("Orca CLI Command", value=os.getenv("ORCA_SLICER_CMD", "orca-slicer"))
    command_template = st.text_input(
        "Command Template",
        value='{orca_cmd} --export-gcode "{input_stl}" --output "{output_gcode}"',
        help="Edit this template to match your Orca CLI flags. Placeholders: {orca_cmd}, {input_stl}, {output_gcode}",
    )

    if not command_available(orca_cmd):
        st.info(
            "Orca CLI command is not currently found on PATH. STL/OBJ slicing will fail until the command is available. "
            "G-code uploads can still be sent directly."
        )

    if st.button("Slice/Send to Printer", use_container_width=True):
        if upload is None:
            st.error("Upload a .stl, .obj, or .gcode file first.")
        elif not target_url:
            st.error("Enter a valid printer host/IP.")
        else:
            filename = upload.name
            raw_bytes = upload.getvalue()
            ext = Path(filename).suffix.lower()

            gcode_bytes = b""
            gcode_name = filename if ext == ".gcode" else f"{Path(filename).stem}.gcode"
            slicer_log = ""

            try:
                if ext in {".stl", ".obj"}:
                    if not slice_stl:
                        st.error("STL/OBJ requires slicing enabled before sending to OctoPrint/Moonraker.")
                    else:
                        with st.spinner("Slicing model using Orca CLI..."):
                            gcode_bytes, gcode_name, slicer_log = slice_with_orca(
                                model_bytes=raw_bytes,
                                model_filename=filename,
                                command=orca_cmd,
                                template=command_template,
                            )
                else:
                    gcode_bytes = raw_bytes

                if not gcode_bytes:
                    raise RuntimeError("No G-code was produced or uploaded.")

                config = TargetConfig(
                    backend=backend,
                    base_url=target_url,
                    api_key=api_key,
                    auto_start=auto_start,
                )

                with st.spinner(f"Sending {gcode_name} to {backend} at {target_url}..."):
                    result = send_gcode(config=config, gcode_bytes=gcode_bytes, gcode_filename=gcode_name)

                st.success(f"Sent {gcode_name} to {backend} successfully.")
                st.json(result)

                if slicer_log:
                    with st.expander("Orca Slicer Log"):
                        st.text(slicer_log)

                st.download_button(
                    "Download Generated G-code",
                    data=gcode_bytes,
                    file_name=gcode_name,
                    mime="text/plain",
                    key="download_generated_gcode",
                )
            except Exception as exc:
                st.error(str(exc))

with tab_ai:
    st.subheader("AI Build Intuition")
    st.caption("Remote inference target: GPTOSS20B served on your network through an OpenAI-compatible endpoint.")
    st.markdown(f"**AI status:** {ai_guidance['status']}")
    st.write(ai_guidance["summary"])

    watchouts = ai_guidance.get("watchouts", [])
    if watchouts:
        st.markdown("#### Watchouts")
        for item in watchouts:
            st.write(f"- {item}")

    materials = ai_guidance.get("recommended_materials", [])
    if materials:
        st.markdown("#### Recommended Materials")
        for item in materials:
            st.write(f"- {item}")

    st.markdown("#### Next Step")
    st.write(ai_guidance.get("next_step", "Review the generated plan."))

    if ai_error:
        st.warning(f"AI endpoint connection issue: {ai_error}")

with tab_inspiration:
    st.subheader("Inspiration + Strategic Mix")
    st.markdown("**PartonDemand is run by Jonathon Ward and Russile Schlack.**")
    st.markdown(
        "This direction is inspired by [Magpie](https://github.com/magpie-printer/magpie) and "
        "[SpiteDriven](https://www.spitedriven.com/)."
    )

    st.markdown("#### Strategic Integration Plan")
    strategy_df = pd.DataFrame(
        [
            {
                "Phase": "1. Attribution Layer",
                "Objective": "Keep visible credit in UI, exports, and docs",
                "Deliverable": "Inspiration tab + metadata fields + README section",
            },
            {
                "Phase": "2. Design DNA Import",
                "Objective": "Extract reusable mechanical patterns",
                "Deliverable": "Magpie-inspired profile templates and frame presets",
            },
            {
                "Phase": "3. Workflow Alignment",
                "Objective": "Align slicing and print flow with high-agility practices",
                "Deliverable": "Preset packs for speed, quality, and reliability",
            },
            {
                "Phase": "4. Co-Credit Release",
                "Objective": "Publish transparent lineage for the community",
                "Deliverable": "Public credits page and release notes attribution",
            },
        ]
    )
    st.dataframe(strategy_df, use_container_width=True, hide_index=True)

    st.markdown("#### Suggested Next Moves")
    st.write("- Add a dedicated Magpie-inspired machine profile family in Build Envelope presets.")
    st.write("- Add a SpiteDriven inspiration note to generated build sheets.")
    st.write("- Keep all derivative references linked back to original sources.")

with tab_data:
    st.subheader("Configuration JSON")
    payload = {
        "project": "Oxidus Print!",
        "built_by": "PartonDemand",
        "inspiration": {
            "magpie": "https://github.com/magpie-printer/magpie",
            "spitedriven": "https://www.spitedriven.com/",
        },
        "source": "Voron-inspired open source workflow",
        "supplier_mode": supplier_mode,
        "ai": {
            "enabled": ai_enabled,
            "base_url": ai_base_url,
            "model": ai_model,
            "status": ai_guidance["status"],
            "provider": "openai-compatible-network-endpoint",
        },
        "build_envelope_mm": {"x": spec.x_mm, "y": spec.y_mm, "z": spec.z_mm},
        "parts": [
            {
                "name": p.name,
                "qty": p.qty,
                "printable": p.printable,
                "material": p.material,
                "supplier": p.supplier.name,
                "supplier_url": p.supplier.url,
                "dimensions_mm": list(p.dimensions_mm),
            }
            for p in parts
        ],
    }
    st.code(json.dumps(payload, indent=2), language="json")

st.markdown(
    """
#### Open-Source Note
Oxidus Print is designed as a planning and prototyping layer. For certified release files and official documentation,
use Voron Design resources and licensing guidance directly from https://vorondesign.com/.

Strategic inspiration credit: https://github.com/magpie-printer/magpie and https://www.spitedriven.com/.

Built by PartonDemand.
"""
)

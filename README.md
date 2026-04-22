# Oxidus Print!

Oxidus Print is a modular Streamlit app for planning a custom 3D printer build.

Built by PartonDemand.
PartonDemand is run by Jonathon Ward and Russell Schlack.

Inspired by Magpie and SpiteDriven:
- https://github.com/magpie-printer/magpie
- https://www.spitedriven.com/

## Recent updates

- Added Inspiration tab with strategic collaboration roadmap and source credit links
- Added Print Bridge with Orca CLI slicing and direct printer upload by IP
- Added OBJ support in slicing flow (in addition to STL and direct G-code)
- Added network AI recommendation support targeting GPTOSS20B endpoints

## Current MVP features

- Intuitive sliders for X/Y/Z build envelope sizing
- Interactive 3D concept visualization of frame and build volume
- Generated build sheet with part categories, materials, and print notes
- Parametric downloadable STL starter files for printable parts
- Exportable JSON/CSV project data
- Build-sheet supplier references including DLLPDF and Phaetus
- Auto supplier mode as the default sourcing strategy
- Network AI build intuition via an OpenAI-compatible endpoint using GPTOSS20B
- Print Bridge tab with optional Orca CLI slicing and direct send-to-IP printer hosts (OctoPrint or Moonraker)

## Open-source workflow

This project is Voron-inspired and intended as a planning layer. Use official release assets,
licenses, and documentation from https://vorondesign.com/ for production builds.

Current supplier references in-app:
- https://dllpdf.com/
- https://www.phaetus.com/en-us

## AI workflow

Oxidus Print can call a network-hosted inference service using an OpenAI-compatible API.

- Default endpoint: configured by `OXIDUS_AI_BASE_URL` or entered in the sidebar
- Default model target: `gptoss20b`
- Default sourcing behavior: Auto

If the network AI service is unavailable, the app falls back to local heuristic guidance instead of failing hard.

## Print bridge workflow

The Print Bridge tab supports:

- Upload `.stl` or `.obj` and slice via Orca CLI, then upload generated `.gcode`
- Upload `.gcode` directly without slicing
- Send to printer host by IP/URL using OctoPrint or Moonraker APIs

For STL/OBJ slicing, ensure Orca CLI is installed and adjust the command template in-app if your CLI flags differ.

## Inspiration strategy

Oxidus Print now includes an in-app Inspiration tab with a practical collaboration path:

- Keep visible attribution in UI, exports, and docs
- Introduce Magpie-inspired profile families where appropriate
- Align high-agility print workflow presets
- Preserve transparent source lineage in release notes

## Run locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the app:

   ```bash
   streamlit run streamlit_app.py
   ```

If `pandas`, `plotly`, or `requests` are missing from the interpreter used to launch Streamlit,
Oxidus Print will bootstrap them automatically from `requirements.txt` on first startup.

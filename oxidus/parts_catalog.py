from __future__ import annotations

from dataclasses import dataclass

from .models import PrinterSpec


@dataclass(frozen=True)
class SupplierOption:
    name: str
    url: str
    priority: int


@dataclass(frozen=True)
class PartSpec:
    name: str
    qty: int
    category: str
    source: str
    suppliers: tuple[SupplierOption, ...]
    printable: bool
    material: str
    print_notes: str
    dimensions_mm: tuple[float, float, float]


@dataclass(frozen=True)
class ResolvedPartSpec:
    name: str
    qty: int
    category: str
    source: str
    supplier: SupplierOption
    printable: bool
    material: str
    print_notes: str
    dimensions_mm: tuple[float, float, float]


def _supplier(name: str, url: str, priority: int) -> SupplierOption:
    return SupplierOption(name=name, url=url, priority=priority)


DLLPDF = _supplier("DLLPDF", "https://dllpdf.com/", 100)
PHAETUS = _supplier("Phaetus", "https://www.phaetus.com/en-us", 100)


def _scale(spec: PrinterSpec) -> float:
    return max(0.75, min(1.8, spec.max_axis / 250.0))


def build_parts_list(spec: PrinterSpec) -> list[PartSpec]:
    s = _scale(spec)
    chain_links = max(16, int((spec.x_mm + spec.y_mm + spec.z_mm) / 40))
    return [
        PartSpec(
            name="Corner Frame Bracket",
            qty=8,
            category="Frame",
            source="Voron-inspired open hardware",
            suppliers=(DLLPDF,),
            printable=True,
            material="ABS/ASA",
            print_notes="4-6 perimeters, 40% gyroid infill, no supports",
            dimensions_mm=(32 * s, 32 * s, 32 * s),
        ),
        PartSpec(
            name="Gantry Idler Mount",
            qty=2,
            category="Motion",
            source="Voron-inspired open hardware",
            suppliers=(DLLPDF,),
            printable=True,
            material="ABS/ASA",
            print_notes="6 perimeters, 50% infill, heat-set inserts",
            dimensions_mm=(48 * s, 32 * s, 20 * s),
        ),
        PartSpec(
            name="Belt Tensioner Block",
            qty=2,
            category="Motion",
            source="Voron-inspired open hardware",
            suppliers=(DLLPDF,),
            printable=True,
            material="ABS/ASA",
            print_notes="5 perimeters, 45% infill, print face-down",
            dimensions_mm=(36 * s, 24 * s, 18 * s),
        ),
        PartSpec(
            name="Electronics Mount Plate",
            qty=1,
            category="Electronics",
            source="Custom Oxidus parametric",
            suppliers=(DLLPDF,),
            printable=True,
            material="PETG/ASA",
            print_notes="4 perimeters, 30% infill, add captive nuts",
            dimensions_mm=(120 * s, 95 * s, 4.2),
        ),
        PartSpec(
            name="Cable Chain Link",
            qty=chain_links,
            category="Cable Management",
            source="Custom Oxidus parametric",
            suppliers=(DLLPDF,),
            printable=True,
            material="PETG",
            print_notes="0.2 mm layer, 3 perimeters, 25% infill",
            dimensions_mm=(22.0, 13.0, 8.0),
        ),
        PartSpec(
            name="2020 Aluminum Extrusion Set",
            qty=1,
            category="Frame",
            source="Vendor BOM",
            suppliers=(DLLPDF,),
            printable=False,
            material="Aluminum 6063-T5",
            print_notes="Cut list generated in build sheet",
            dimensions_mm=(spec.x_mm + 140, spec.y_mm + 140, spec.z_mm + 190),
        ),
        PartSpec(
            name="Linear Rail Set",
            qty=1,
            category="Motion",
            source="Vendor BOM",
            suppliers=(DLLPDF,),
            printable=False,
            material="Hardened steel",
            print_notes="Use MGN rails sized to each axis",
            dimensions_mm=(spec.x_mm, spec.y_mm, spec.z_mm),
        ),
        PartSpec(
            name="Heated Bed Assembly",
            qty=1,
            category="Print Surface",
            source="Vendor BOM",
            suppliers=(DLLPDF,),
            printable=False,
            material="Cast aluminum + PEI",
            print_notes="Bed size should match X/Y envelope",
            dimensions_mm=(spec.x_mm + 20, spec.y_mm + 20, 8.0),
        ),
        PartSpec(
            name="Hotend + Nozzle Kit",
            qty=1,
            category="Extrusion",
            source="Performance motion component",
            suppliers=(PHAETUS,),
            printable=False,
            material="Copper alloy + hardened steel",
            print_notes="Select nozzle size by target speed and layer profile",
            dimensions_mm=(65.0, 35.0, 35.0),
        ),
    ]


def resolve_parts(parts: list[PartSpec], supplier_mode: str) -> list[ResolvedPartSpec]:
    resolved_parts = []
    for part in parts:
        if supplier_mode == "Auto":
            supplier = max(part.suppliers, key=lambda option: option.priority)
        else:
            supplier = next(
                (option for option in part.suppliers if option.name == supplier_mode),
                max(part.suppliers, key=lambda option: option.priority),
            )
        resolved_parts.append(
            ResolvedPartSpec(
                name=part.name,
                qty=part.qty,
                category=part.category,
                source=part.source,
                supplier=supplier,
                printable=part.printable,
                material=part.material,
                print_notes=part.print_notes,
                dimensions_mm=part.dimensions_mm,
            )
        )
    return resolved_parts


def supplier_modes(parts: list[PartSpec]) -> list[str]:
    supplier_names = sorted({option.name for part in parts for option in part.suppliers})
    return ["Auto", *supplier_names]


def printable_parts(parts: list[ResolvedPartSpec]) -> list[ResolvedPartSpec]:
    return [part for part in parts if part.printable]

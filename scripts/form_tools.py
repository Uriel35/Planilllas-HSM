import argparse
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pdfrw import PdfArray, PdfDict, PdfName, PdfObject, PdfReader, PdfWriter
from pdfrw.objects.pdfstring import PdfString


def _pdf_str_unwrap(token: Any) -> Optional[str]:
    """
    Best-effort decode for strings that pdfrw may surface as raw PDF literals,
    e.g. '(field_name)' with backslash escapes.
    """
    if token is None:
        return None
    if not isinstance(token, str):
        # pdfrw can surface PdfString-like objects; try to_unicode if present.
        to_uni = getattr(token, "to_unicode", None)
        if callable(to_uni):
            return to_uni()
        return str(token)

    s = token
    if len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        s = s[1:-1]
    # Unescape the most common sequences used in literal strings.
    s = s.replace("\\\\", "\\").replace("\\(", "(").replace("\\)", ")")
    return s


def _ensure_helv(acr: PdfDict) -> None:
    """Ensure /AcroForm has /DR /Font /Helv set (Helvetica)."""
    if acr.DR is None:
        acr.DR = PdfDict()
    if acr.DR.Font is None:
        acr.DR.Font = PdfDict()
    if acr.DR.Font.Helv is None:
        # Built-in PDF font; no embedding required for basic usage.
        acr.DR.Font.Helv = PdfDict(
            Type=PdfName.Font,
            Subtype=PdfName.Type1,
            BaseFont=PdfName.Helvetica,
            Encoding=PdfName.WinAnsiEncoding,
            indirect=True,
        )


def list_fields(pdf_path: str) -> int:
    pdf = PdfReader(pdf_path)
    acro = getattr(pdf.Root, "AcroForm", None)
    fields = []
    if acro and acro.Fields:
        fields = list(acro.Fields)

    print(f"fields={len(fields)} pages={len(pdf.pages)}")
    for i, f in enumerate(fields):
        ft = f.get("/FT")
        name = _pdf_str_unwrap(f.get("/T"))
        kids = f.get("/Kids")
        rect = None
        if kids:
            rect = kids[0].get("/Rect")
        else:
            rect = f.get("/Rect")
        print(f"{i:02d}\t{ft}\t{name}\t{rect}")
    return 0


def _as_pdf_rect(rect: List[float]) -> PdfArray:
    if len(rect) != 4:
        raise ValueError(f"rect must have 4 numbers, got: {rect}")
    return PdfArray([PdfObject(str(float(x))) for x in rect])


def _rect_to_floats(rect: PdfArray) -> Optional[Tuple[float, float, float, float]]:
    try:
        if rect and len(rect) == 4:
            return tuple(float(x) for x in rect)  # type: ignore[return-value]
    except Exception:
        pass
    return None


@dataclass(frozen=True)
class FieldSpec:
    type: str
    name: str
    page: int
    rect: List[float]
    font_size: float = 0  # 0 == autosize in many viewers
    multiline: bool = False
    value: str = ""
    checked: bool = False
    check_style: str = "check"


def _parse_specs(path: str) -> List[FieldSpec]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("fields.json must be a JSON array")

    specs: List[FieldSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"Each entry must be an object, got: {item!r}")
        specs.append(
            FieldSpec(
                type=str(item.get("type", "text")),
                name=str(item["name"]),
                page=int(item.get("page", 0)),
                rect=list(item["rect"]),
                font_size=float(item.get("font_size", 0)),
                multiline=bool(item.get("multiline", False)),
                value=str(item.get("value", "")),
                checked=bool(item.get("checked", False)),
                check_style=str(item.get("check_style", "check")),
            )
        )
    return specs


def add_fields(pdf_in: str, fields_json: str, pdf_out: str) -> int:
    pdf = PdfReader(pdf_in)

    if pdf.Root.AcroForm is None:
        pdf.Root.AcroForm = PdfDict(indirect=True, Fields=PdfArray())

    acro = pdf.Root.AcroForm
    if acro.Fields is None:
        acro.Fields = PdfArray()
    _ensure_helv(acro)

    # Let PDF viewers generate appearances for new fields/widgets.
    acro.NeedAppearances = PdfObject("true")
    # Tell viewers this document contains signature fields.
    if acro.SigFlags is None:
        acro.SigFlags = PdfObject("3")

    # Existing field names to avoid collisions.
    existing = set()
    for f in acro.Fields:
        existing.add(_pdf_str_unwrap(f.get("/T")))

    specs = _parse_specs(fields_json)
    for spec in specs:
        if spec.page < 0 or spec.page >= len(pdf.pages):
            raise ValueError(f"Invalid page index {spec.page} for {pdf_in}")
        if spec.name in existing:
            raise ValueError(f"Field already exists: {spec.name}")

        page = pdf.pages[spec.page]
        if page.Annots is None:
            page.Annots = PdfArray()

        if spec.type.lower() in ("text", "tx"):
            ff = 0
            if spec.multiline:
                ff |= 4096  # Multiline flag for /Tx fields.

            widget = PdfDict(
                indirect=True,
                Type=PdfName.Annot,
                Subtype=PdfName.Widget,
                Rect=_as_pdf_rect(spec.rect),
                F=4,
                Border=PdfArray([0, 0, 0]),
            )
            field = PdfDict(
                indirect=True,
                FT=PdfName.Tx,
                T=PdfString.encode(spec.name),
                Ff=PdfObject(str(ff)),
                V=PdfString.encode(spec.value),
                Kids=PdfArray([widget]),
                # Default appearance: Helvetica + autosize (0) by default.
                DA=PdfString.encode(f"/Helv {spec.font_size:g} Tf 0 g"),
                Q=PdfObject("0"),
            )
            widget.Parent = field
            page.Annots.append(widget)
            acro.Fields.append(field)
            existing.add(spec.name)
            continue

        if spec.type.lower() in ("checkbox", "cb", "btn"):
            on_state = PdfName.Yes
            off_state = PdfName.Off
            v = on_state if spec.checked else off_state
            captions = {
                "check": "4",
                "circle": "l",
                "cross": "8",
                "diamond": "u",
                "square": "n",
                "star": "H",
            }
            caption = captions.get(spec.check_style.lower(), "4")

            widget = PdfDict(
                indirect=True,
                Type=PdfName.Annot,
                Subtype=PdfName.Widget,
                Rect=_as_pdf_rect(spec.rect),
                F=4,
                Border=PdfArray([0, 0, 0]),
                MK=PdfDict(CA=PdfString.encode(caption)),
                AS=v,
            )
            field = PdfDict(
                indirect=True,
                FT=PdfName.Btn,
                T=PdfString.encode(spec.name),
                V=v,
                Kids=PdfArray([widget]),
            )
            widget.Parent = field
            page.Annots.append(widget)
            acro.Fields.append(field)
            existing.add(spec.name)
            continue

        if spec.type.lower() in ("signature", "sig"):
            # Creates a visible signature field placeholder. The actual cryptographic
            # signing is performed by a PDF signer (Adobe Reader, Acrobat, etc.).
            widget = PdfDict(
                indirect=True,
                Type=PdfName.Annot,
                Subtype=PdfName.Widget,
                Rect=_as_pdf_rect(spec.rect),
                F=4,
                Border=PdfArray([0, 0, 0]),
            )
            field = PdfDict(
                indirect=True,
                FT=PdfName.Sig,
                T=PdfString.encode(spec.name),
                Kids=PdfArray([widget]),
            )
            widget.Parent = field
            page.Annots.append(widget)
            acro.Fields.append(field)
            existing.add(spec.name)
            continue

        raise ValueError(f"Unknown field type: {spec.type!r} (name={spec.name})")

    PdfWriter().write(pdf_out, pdf)
    return 0


def _iter_widgets(field: PdfDict) -> List[PdfDict]:
    """
    Return widget annotations for a field.

    Many PDFs represent fields as a widget annotation directly (no /Kids),
    while others store widgets under /Kids.
    """
    kids = field.get("/Kids")
    if kids:
        return [k for k in kids]
    subtype = field.get("/Subtype")
    if subtype == PdfName.Widget:
        return [field]
    return []


def _btn_on_state(widget: PdfDict) -> PdfName:
    """
    Best-effort detection of the "on" appearance state for a checkbox/radio.
    """
    ap = widget.get("/AP")
    if ap:
        n = ap.get("/N")
        if n:
            for k in n.keys():
                if k != PdfName.Off:
                    return k
    # Common fallback.
    return PdfName.Yes


def _field_rect(field: PdfDict) -> Optional[PdfArray]:
    """Return the first available widget rect for a field."""
    rect = field.get("/Rect")
    if rect:
        return rect
    for widget in _iter_widgets(field):
        rect = widget.get("/Rect")
        if rect:
            return rect
    return None


def _choose_font_size(field: PdfDict, *, min_size: float = 8.0, max_size: float = 12.0) -> float:
    """
    Pick a reasonable font size for /Tx fields based on the widget rect height.
    This avoids relying on font-size 0 (auto), which some renderers handle poorly.
    """
    rect = _field_rect(field)
    try:
        if rect and len(rect) == 4:
            h = float(rect[3]) - float(rect[1])
            # Typical single-line fields in this PDF are ~11-20 pt tall.
            # Keep it conservative to avoid clipping.
            return max(min_size, min(max_size, h * 0.72))
    except Exception:
        pass
    return min_size


def _ensure_min_widget_height(field: PdfDict, min_height: float) -> None:
    """Grow text-field widget rects so the requested font size can fit."""
    if min_height <= 0:
        return
    for widget in _iter_widgets(field):
        rect = _rect_to_floats(widget.get("/Rect"))
        if not rect:
            continue
        x1, y1, x2, y2 = rect
        h = y2 - y1
        if h >= min_height:
            continue
        center = (y1 + y2) / 2.0
        new_y1 = center - (min_height / 2.0)
        new_y2 = center + (min_height / 2.0)
        widget.Rect = _as_pdf_rect([x1, new_y1, x2, new_y2])


def set_text_field_font_sizes(
    pdf_in: str,
    pdf_out: str,
    *,
    font_size: Optional[float] = None,
    min_size: float = 8.0,
    max_size: float = 12.0,
    min_height: float = 0.0,
) -> int:
    """
    Normalize /DA for existing text fields to avoid tiny autosized text.
    """
    pdf = PdfReader(pdf_in)
    acro = getattr(pdf.Root, "AcroForm", None)
    if not acro or not acro.Fields:
        raise ValueError(f"{pdf_in} has no AcroForm fields to update")

    _ensure_helv(acro)
    acro.NeedAppearances = PdfObject("true")

    for field in acro.Fields:
        if field.get("/FT") != PdfName.Tx:
            continue
        _ensure_min_widget_height(field, min_height)
        fs = float(font_size) if font_size is not None else _choose_font_size(
            field, min_size=min_size, max_size=max_size
        )
        da = PdfString.encode(f"/Helv {fs:g} Tf 0 g")
        field.DA = da
        for widget in _iter_widgets(field):
            widget.DA = da

    PdfWriter().write(pdf_out, pdf)
    return 0


def fill_fields(pdf_in: str, data_json: str, pdf_out: str) -> int:
    """
    Fill existing AcroForm fields from a JSON object.

    JSON format:
      {
        "Field Name": "text value",
        "Checkbox Field": true,
        "Another Checkbox": {"checked": false},
        "Text Field": {"value": "..." }
      }
    """
    with open(data_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("data.json must be a JSON object mapping field name -> value")

    pdf = PdfReader(pdf_in)
    acro = getattr(pdf.Root, "AcroForm", None)
    if not acro or not acro.Fields:
        raise ValueError(f"{pdf_in} has no AcroForm fields to fill")

    # Let PDF viewers generate appearances for updated fields.
    acro.NeedAppearances = PdfObject("true")

    def _coerce_item(v: Any) -> Tuple[Optional[str], Optional[bool]]:
        if isinstance(v, dict):
            val = v.get("value", None)
            chk = v.get("checked", None)
            if val is not None:
                val = str(val)
            if chk is not None:
                chk = bool(chk)
            return val, chk
        if isinstance(v, bool):
            return None, v
        if v is None:
            return "", None
        return str(v), None

    fields_by_name: Dict[str, PdfDict] = {}
    for f in acro.Fields:
        name = _pdf_str_unwrap(f.get("/T"))
        if name:
            fields_by_name[name] = f

    missing = []
    for name, raw in data.items():
        if name not in fields_by_name:
            missing.append(name)
            continue
        field = fields_by_name[name]
        ft = field.get("/FT")
        text_val, checked = _coerce_item(raw)

        if ft == PdfName.Tx:
            if text_val is None:
                text_val = ""
            field.V = PdfString.encode(text_val)
            # Some viewers also look at /DV.
            field.DV = PdfString.encode(text_val)
            # Enable multiline for large narrative fields (and when value contains newlines).
            try:
                ff_raw = field.get("/Ff")
                ff = int(str(ff_raw)) if ff_raw is not None else 0
            except Exception:
                ff = 0
            if ("\n" in text_val) or (_pdf_str_unwrap(field.get("/T")) in ("Diagnostico", "Observaciones")):
                ff |= 4096
            field.Ff = PdfObject(str(ff))
            # Force a non-zero font size to make appearances consistent.
            fs = _choose_font_size(field)
            field.DA = PdfString.encode(f"/Helv {fs:g} Tf 0 g")
            continue

        if ft == PdfName.Btn:
            widgets = _iter_widgets(field)
            # If the field itself isn't a widget, still set V for completeness.
            target_widget = widgets[0] if widgets else field
            on_state = _btn_on_state(target_widget)
            v = on_state if bool(checked) else PdfName.Off
            field.V = v
            field.AS = v
            for w in widgets:
                w.AS = v
            continue

        # Ignore other field types for now (Sig, Ch, etc.)

    if missing:
        raise ValueError(f"Unknown field(s) in data.json: {missing}")

    PdfWriter().write(pdf_out, pdf)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="List/add PDF AcroForm fields (pdfrw).")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List existing fields")
    p_list.add_argument("pdf", help="Input PDF")

    p_add = sub.add_parser("add", help="Add fields from a JSON spec")
    p_add.add_argument("pdf_in", help="Input PDF")
    p_add.add_argument("fields_json", help="JSON array with fields")
    p_add.add_argument("-o", "--out", required=True, help="Output PDF")

    p_fill = sub.add_parser("fill", help="Fill existing fields from a JSON object")
    p_fill.add_argument("pdf_in", help="Input PDF with existing fields")
    p_fill.add_argument("data_json", help="JSON object with field values")
    p_fill.add_argument("-o", "--out", required=True, help="Output PDF")

    p_font = sub.add_parser("fontsize", help="Set font sizes for existing text fields")
    p_font.add_argument("pdf_in", help="Input PDF with existing fields")
    p_font.add_argument("-o", "--out", required=True, help="Output PDF")
    p_font.add_argument("--font-size", type=float, default=None, help="Fixed font size for all text fields")
    p_font.add_argument("--min-size", type=float, default=8.0, help="Minimum auto font size")
    p_font.add_argument("--max-size", type=float, default=12.0, help="Maximum auto font size")
    p_font.add_argument("--min-height", type=float, default=0.0, help="Minimum widget height for text fields")

    args = p.parse_args(argv)

    if args.cmd == "list":
        return list_fields(args.pdf)
    if args.cmd == "add":
        return add_fields(args.pdf_in, args.fields_json, args.out)
    if args.cmd == "fill":
        return fill_fields(args.pdf_in, args.data_json, args.out)
    if args.cmd == "fontsize":
        return set_text_field_font_sizes(
            args.pdf_in,
            args.out,
            font_size=args.font_size,
            min_size=args.min_size,
            max_size=args.max_size,
            min_height=args.min_height,
        )
    raise RuntimeError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())

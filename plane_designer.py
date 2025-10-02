#!/usr/bin/env python3
"""
RC Plane Designer (interactive) — corrected & formatted

Note: Requires reportlab for PDF export:
    pip install reportlab

Units: mm for lengths, mm^2 for areas (m and m^2 also displayed)
"""
import math
import sys
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------- Utility functions ----------------------
def get_float(prompt, min_val=None, max_val=None, default=None):
    while True:
        try:
            raw = input(prompt).strip()
            if raw == "" and default is not None:
                val = float(default)
            else:
                val = float(raw)
        except ValueError:
            print("  -> Please enter a numeric value.")
            continue
        if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
            if min_val is not None and max_val is not None:
                print(f"  -> Enter a value between {min_val} and {max_val}.")
            elif min_val is not None:
                print(f"  -> Enter a value >= {min_val}.")
            else:
                print(f"  -> Enter a value <= {max_val}.")
            continue
        return val

def mm_to_m(x_mm):
    return x_mm / 1000.0

def mm2_to_m2(x_mm2):
    return x_mm2 / 1_000_000.0

def fmt_mm(x):   return f"{x:,.3f} mm"
def fmt_m(x_mm): return f"{mm_to_m(x_mm):.3f} m"
def fmt_mm2(x):  return f"{x:,.3f} mm²"
def fmt_m2(x_mm2):return f"{mm2_to_m2(x_mm2):.4f} m²"

# ---------------------- Design functions ----------------------
def design_wing():
    print("\n=== WING DESIGN ===")
    span = get_float("Enter wingspan b (in millimeters, mm): ")
    AR = get_float("Enter Aspect Ratio (AR): ")
    taper_ratio = get_float("Enter Taper Ratio λ (tip chord / root chord) (0 < λ <= 1 typical): ")

    # Wing area
    wing_area = (span ** 2) / AR  # S = b^2 / AR

    # Root chord (Cr) and tip chord (Ct) for trapezoidal wing
    c_root = (2 * wing_area) / (span * (1 + taper_ratio))
    c_tip = taper_ratio * c_root

    # Correct MAC formula (trapezoidal wing):
    # MAC = (2/3) * Cr * (1 + λ + λ^2) / (1 + λ)
    # If we want MAC in terms of S and b, substituting Cr gives:
    # MAC = (4S/(3b)) * ((1 + λ + λ^2) / (1 + λ)^2)
    MAC = (4.0 * wing_area / (3.0 * span)) * ((1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)**2)

    # Print nicely
    print("\n--- Results (Wing) ---")
    print(f"Span (b):           {fmt_mm(span)}")
    print(f"Aspect Ratio (AR):  {AR:.3f}")
    print(f"Wing Area (S):      {fmt_mm2(wing_area)}   ({fmt_m2(wing_area)})")
    print(f"Mean Aero Chord:    {fmt_mm(MAC)}   ({fmt_m(MAC)})")
    print(f"Root Chord (Cr):    {fmt_mm(c_root)}")
    print(f"Tip Chord (Ct):     {fmt_mm(c_tip)}")

    return {"span": span, "AR": AR, "taper_ratio": taper_ratio,
            "wing_area": wing_area, "MAC": MAC, "c_root": c_root, "c_tip": c_tip}

def design_empennage(wing_area):
    print("\n=== EMPENNAGE DESIGN ===")
    print("Horizontal Stabilizer (HS): HS area = 18-20% of wing area (choose in range).")
    percent_hs = get_float("Choose HS area % of wing area [18-20]: ", 18.0, 20.0)
    S_hs = (percent_hs / 100.0) * wing_area
    AR_hs = get_float("Enter HS Aspect Ratio AR_HS [recommended 3-5]: ", 1.0, 20.0)
    taper_hs = get_float("Enter HS taper ratio λ_HS [recommended 0.3-0.6]: ", 0.05, 1.5)
    b_hs = math.sqrt(AR_hs * S_hs)
    c_root_hs = (2 * S_hs) / (b_hs * (1 + taper_hs))
    c_tip_hs = taper_hs * c_root_hs
    percent_elev = get_float("Choose Elevator area % of HS area [25-50]: ", 25.0, 50.0)
    S_elev = (percent_elev / 100.0) * S_hs

    print("\nVertical Stabilizer (VS): VS area = 9-10% of wing area (choose in range).")
    percent_vs = get_float("Choose VS area % of wing area [9-10]: ", 9.0, 10.0)
    S_vs = (percent_vs / 100.0) * wing_area
    AR_vs = get_float("Enter VS Aspect Ratio AR_VS [recommended 1.3-2.0]: ", 1.0, 10.0)
    taper_vs = get_float("Enter VS taper ratio λ_VS [recommended 0.3-0.6]: ", 0.05, 1.5)
    b_vs = math.sqrt(AR_vs * S_vs)
    c_root_vs = (2 * S_vs) / (b_vs * (1 + taper_vs))
    c_tip_vs = taper_vs * c_root_vs
    percent_rudder = get_float("Choose Rudder area % of VS area [25-50]: ", 25.0, 50.0)
    S_rudder = (percent_rudder / 100.0) * S_vs

    # Print nicely
    print("\n--- Results (Empennage) ---")
    print("Horizontal Stabilizer (HS):")
    print(f"  HS Area:     {fmt_mm2(S_hs)}   ({fmt_m2(S_hs)})")
    print(f"  HS Span:     {fmt_mm(b_hs)}")
    print(f"  HS Root Cr:  {fmt_mm(c_root_hs)}")
    print(f"  HS Tip Ct:   {fmt_mm(c_tip_hs)}")
    print(f"  Elevator:    {fmt_mm2(S_elev)}   ({fmt_m2(S_elev)})")

    print("\nVertical Stabilizer (VS):")
    print(f"  VS Area:     {fmt_mm2(S_vs)}   ({fmt_m2(S_vs)})")
    print(f"  VS Span:     {fmt_mm(b_vs)}")
    print(f"  VS Root Cr:  {fmt_mm(c_root_vs)}")
    print(f"  VS Tip Ct:   {fmt_mm(c_tip_vs)}")
    print(f"  Rudder:      {fmt_mm2(S_rudder)}   ({fmt_m2(S_rudder)})")

    hs = {"S": S_hs, "span": b_hs, "root": c_root_hs, "tip": c_tip_hs, "Elevator": S_elev, "percent_hs": percent_hs, "percent_elev": percent_elev}
    vs = {"S": S_vs, "span": b_vs, "root": c_root_vs, "tip": c_tip_vs, "Rudder": S_rudder, "percent_vs": percent_vs, "percent_rudder": percent_rudder}
    return {"HS": hs, "VS": vs}

def design_fuselage(span):
    print("\n=== FUSELAGE DESIGN ===")
    print("Fuselage length recommended: 60-75% of wingspan.")
    percent_fus_len = get_float("Choose fuselage length % of wingspan [60-75]: ", 60.0, 75.0)
    fus_length = (percent_fus_len / 100.0) * span
    percent_fus_h = get_float("Choose fuselage height % of fuselage length [10-15]: ", 10.0, 15.0)
    fus_height = (percent_fus_h / 100.0) * fus_length
    print(f"Fuselage length: {fmt_mm(fus_length)}  | Height: {fmt_mm(fus_height)}")
    return {"length": fus_length, "height": fus_height, "percent_len": percent_fus_len, "percent_h": percent_fus_h}

def cg_and_static_margin(MAC_mm):
    print("\n=== CG & STATIC MARGIN ===")
    print("Neutral Point typical range: 25-40% MAC. Suggested default: 30% MAC.")
    NP_percent = get_float("Neutral Point %MAC [25-40] (default 30): ", 25.0, 40.0, 30.0)
    CG_percent = get_float("CG location %MAC [20-35]: ", 0.0, 100.0)
    SM = NP_percent - CG_percent
    print(f"Neutral Point (NP): {NP_percent:.2f}% of MAC  -> {fmt_mm((NP_percent/100.0)*MAC_mm)}")
    print(f"CG location:         {CG_percent:.2f}% of MAC  -> {fmt_mm((CG_percent/100.0)*MAC_mm)}")
    print(f"Static Margin (NP - CG) = {SM:.2f}% of MAC")
    if SM <= 0:
        print("  WARNING: Static margin is <= 0% -> aircraft likely unstable. Move CG forward or increase tail volume.")
    elif SM < 5:
        print("  NOTE: Static margin < 5% (low). Handling may be very sensitive.")
    elif SM > 15:
        print("  NOTE: Static margin > 15% (very stable but potentially sluggish).")
    return {"NP_percent": NP_percent, "CG_percent": CG_percent, "SM_percent": SM, "NP_mm": (NP_percent/100.0)*MAC_mm, "CG_mm": (CG_percent/100.0)*MAC_mm}

#-----------------Airfoil calculations ----------------
def airfoil_input():
    print("\n=== AIRFOIL DESIGN ===")
    calculate = input("Enter yes if you want to do calculation related to Airfoil").lower()
    if (calculate== "yes"):
        print("Thank you for your input")
    else:
        print("Thank you for not your input")
    print("Hello world")
    return "hello worrld"


# ---------------------- Exports ----------------------
def export_text(data, filename="rc_plane_design.txt"):
    """Export RC plane design as a nicely formatted text report."""
    lines = []

    def add_line(name, value, unit=""):
        lines.append(f"{name:<30}: {value} {unit}")

    lines.append("RC PLANE DESIGN REPORT")
    lines.append("=" * 50)
    lines.append("\n--- WING ---")
    wing = data["Wing"]
    add_line("Span (b)", f"{wing['span']:.3f}", "mm")
    add_line("Aspect Ratio (AR)", f"{wing['AR']:.3f}")
    add_line("Wing Area (S)", f"{wing['wing_area']:.3f}", "mm²")
    add_line("Wing Area (S)", f"{mm2_to_m2(wing['wing_area']):.4f}", "m²")
    add_line("MAC", f"{wing['MAC']:.3f}", "mm")
    add_line("MAC", f"{mm_to_m(wing['MAC']):.3f}", "m")
    add_line("Root Chord (Cr)", f"{wing['c_root']:.3f}", "mm")
    add_line("Tip Chord (Ct)", f"{wing['c_tip']:.3f}", "mm")

    lines.append("\n--- EMPENNAGE ---")
    hs = data["Empennage"]["HS"]
    lines.append("Horizontal Stabilizer (HS):")
    add_line("HS Area", f"{hs['S']:.3f}", "mm²")
    add_line("HS Span", f"{hs['span']:.3f}", "mm")
    add_line("HS Root Chord", f"{hs['root']:.3f}", "mm")
    add_line("HS Tip Chord", f"{hs['tip']:.3f}", "mm")
    add_line("Elevator Area", f"{hs['Elevator']:.3f}", "mm²")

    vs = data["Empennage"]["VS"]
    lines.append("\nVertical Stabilizer (VS):")
    add_line("VS Area", f"{vs['S']:.3f}", "mm²")
    add_line("VS Span", f"{vs['span']:.3f}", "mm")
    add_line("VS Root Chord", f"{vs['root']:.3f}", "mm")
    add_line("VS Tip Chord", f"{vs['tip']:.3f}", "mm")
    add_line("Rudder Area", f"{vs['Rudder']:.3f}", "mm²")

    lines.append("\n--- FUSELAGE ---")
    fus = data["Fuselage"]
    add_line("Fuselage Length", f"{fus['length']:.3f}", "mm")
    add_line("Fuselage Height", f"{fus['height']:.3f}", "mm")

    lines.append("\n--- CG & Static Margin ---")
    cg = data["CG_StaticMargin"]
    add_line("Neutral Point %MAC", f"{cg['NP_percent']:.3f}", "%")
    add_line("CG %MAC", f"{cg['CG_percent']:.3f}", "%")
    add_line("Static Margin %MAC", f"{cg['SM_percent']:.3f}", "%")
    add_line("NP position (mm from MAC LE)", f"{cg['NP_mm']:.3f}", "mm")
    add_line("CG position (mm from MAC LE)", f"{cg['CG_mm']:.3f}", "mm")

    # Write to file
    with open(filename, "w") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Text report exported to {filename}")


def export_pdf(data, filename="rc_plane_design.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50

    def draw_heading(t):
        nonlocal y
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, t)
        y -= 18
        c.setFont("Helvetica", 10)

    def draw_key_val(k, v):
        nonlocal y
        c.drawString(50, y, f"{k}")
        c.drawRightString(width - 40, y, f"{v}")
        y -= 14

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, y, "RC PLANE DESIGN REPORT")
    y -= 28
    c.setFont("Helvetica", 10)

    # Wing
    wing = data["Wing"]
    draw_heading("WING DESIGN")
    draw_key_val("Span (mm)", f"{wing['span']:.3f}")
    draw_key_val("Aspect Ratio (AR)", f"{wing['AR']:.3f}")
    draw_key_val("Wing Area (mm²)", f"{wing['wing_area']:.3f}")
    draw_key_val("Wing Area (m²)", f"{mm2_to_m2(wing['wing_area']):.4f}")
    draw_key_val("Mean Aero Chord (MAC) (mm)", f"{wing['MAC']:.3f}")
    draw_key_val("Root Chord (Cr) (mm)", f"{wing['c_root']:.3f}")
    draw_key_val("Tip  Chord (Ct) (mm)", f"{wing['c_tip']:.3f}")
    y -= 6
    c.line(40, y, width - 40, y); y -= 18

    # Empennage
    draw_heading("EMPENNAGE")
    hs = data["Empennage"]["HS"]
    vs = data["Empennage"]["VS"]
    c.setFont("Helvetica-Bold", 11); c.drawString(50, y, "Horizontal Stabilizer (HS)"); y -= 14; c.setFont("Helvetica", 10)
    draw_key_val("HS Area (mm²)", f"{hs['S']:.3f}")
    draw_key_val("HS Span (mm)", f"{hs['span']:.3f}")
    draw_key_val("HS Root (mm)", f"{hs['root']:.3f}")
    draw_key_val("HS Tip (mm)", f"{hs['tip']:.3f}")
    draw_key_val("Elevator Area (mm²)", f"{hs['Elevator']:.3f}")
    y -= 6
    c.setFont("Helvetica-Bold", 11); c.drawString(50, y, "Vertical Stabilizer (VS)"); y -= 14; c.setFont("Helvetica", 10)
    draw_key_val("VS Area (mm²)", f"{vs['S']:.3f}")
    draw_key_val("VS Span (mm)", f"{vs['span']:.3f}")
    draw_key_val("VS Root (mm)", f"{vs['root']:.3f}")
    draw_key_val("VS Tip (mm)", f"{vs['tip']:.3f}")
    draw_key_val("Rudder Area (mm²)", f"{vs['Rudder']:.3f}")
    y -= 12
    c.line(40, y, width - 40, y); y -= 18

    # Fuselage
    draw_heading("FUSELAGE")
    fus = data["Fuselage"]
    draw_key_val("Fuselage Length (mm)", f"{fus['length']:.3f}")
    draw_key_val("Fuselage Height (mm)", f"{fus['height']:.3f}")
    y -= 6
    c.line(40, y, width - 40, y); y -= 18

    # CG & static margin
    draw_heading("CG & STATIC MARGIN")
    cg = data["CG_StaticMargin"]
    draw_key_val("Neutral Point (%MAC)", f"{cg['NP_percent']:.3f}%")
    draw_key_val("CG (%MAC)", f"{cg['CG_percent']:.3f}%")
    draw_key_val("Static Margin (%MAC)", f"{cg['SM_percent']:.3f}%")
    draw_key_val("NP position (mm from MAC LE)", f"{cg['NP_mm']:.3f}")
    draw_key_val("CG position (mm from MAC LE)", f"{cg['CG_mm']:.3f}")

    c.save()
    print(f"PDF exported to {filename}")

# ---------------------- Main ----------------------
def main():
    print("RC Plane Designer — interactive\n(enter values in mm; follow prompts)")
    airfoil = airfoil_input()
    wing = design_wing()
    emp = design_empennage(wing["wing_area"])
    fus = design_fuselage(wing["span"])
    cg = cg_and_static_margin(wing["MAC"])

    results = {"Wing": wing, "Empennage": emp, "Fuselage": fus, "CG_StaticMargin": cg}
    export_text(results)
    export_pdf(results)
    print("\nDesign completed. CSV and PDF generated.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)

import json
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# =========================
# Default Design Parameters
# =========================
DEFAULTS = {
    "weight": 2.0,               # kg
    "cl_max": 1.4,
    "taper_ratio": 1.0,
    "tail_taper_H": 1.0,
    "tail_taper_V": 1.0,
    "motor_kv": 1200,
    "battery_voltage": 11.1,
    "propeller": "9x4.5"
}

# =========================
# Input Handling
# =========================
def load_input(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    for key, val in DEFAULTS.items():
        if key not in data:
            data[key] = val
    return data

# =========================
# Wing Calculations
# =========================
def calc_wing_geometry(b, AR, taper_ratio):
    S = b**2 / AR
    MAC = S / b
    C_root = 2*S / (b*(1 + taper_ratio))
    C_tip = taper_ratio * C_root
    return S, MAC, C_root, C_tip

# =========================
# Tail Calculations
# =========================
def calc_tail_geometry(S_tail, span_tail, taper_ratio):
    C_root = 2 * S_tail / (span_tail * (1 + taper_ratio))
    C_tip = taper_ratio * C_root
    return C_root, C_tip

# =========================
# Aerodynamics
# =========================
def calc_aerodynamics(rho, V, S, CL, CD0, AR, e):
    L = 0.5 * rho * V**2 * S * CL
    CD = CD0 + CL**2 / (np.pi * e * AR)
    D = 0.5 * rho * V**2 * S * CD
    return L, D, CD

def stall_speed(W, rho, S, CLmax):
    return np.sqrt(2*W / (rho*S))

# =========================
# Stability
# =========================
def stability(MAC, x_cg, x_np):
    SM = (x_np - x_cg) / MAC
    x_ac = 0.25 * MAC
    return SM, x_ac

# =========================
# Tail & Fuselage
# =========================
def tail_areas(S):
    SH = 0.19 * S
    SV = 0.095 * S
    return SH, SV

def fuselage_dimensions(b):
    Lf = 0.675 * b
    Hf = 0.125 * Lf
    Wf = 0.2 * Hf
    return Lf, Hf, Wf

# =========================
# Plots
# =========================
def plot_lift_curve(CLmax):
    AoA = np.linspace(-5, 15, 50)
    CL = 0.1 * AoA  # linear approx
    CL = np.clip(CL, 0, CLmax)
    plt.figure()
    plt.plot(AoA, CL, label="Lift Curve")
    plt.xlabel("Angle of Attack (deg)")
    plt.ylabel("CL")
    plt.title("Lift Curve")
    plt.grid(True)
    plt.savefig("lift_curve.png")
    plt.close()

def plot_drag_polar(AR, e, CD0):
    CL = np.linspace(0, 1.5, 50)
    CD = CD0 + CL**2 / (np.pi * e * AR)
    plt.figure()
    plt.plot(CL, CD, label="Drag Polar")
    plt.xlabel("CL")
    plt.ylabel("CD")
    plt.title("Drag Polar")
    plt.grid(True)
    plt.savefig("drag_polar.png")
    plt.close()

def plot_cg_vs_np(MAC):
    x_cg = np.linspace(0, MAC, 50)
    x_np = 0.4 * MAC
    plt.figure()
    plt.plot(x_cg, [x_np]*len(x_cg), label="Neutral Point")
    plt.axvline(x=0.3*MAC, color='r', linestyle='--', label="CG Example")
    plt.xlabel("x (mm)")
    plt.ylabel("Position (mm)")
    plt.title("CG vs Neutral Point")
    plt.legend()
    plt.grid(True)
    plt.savefig("cg_vs_np.png")
    plt.close()

# =========================
# PDF Report
# =========================
def generate_pdf(data, results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RC Plane Design Report", 0, 1, 'C')
    
    pdf.set_font("Arial", '', 12)
    pdf.ln(5)
    pdf.cell(0, 10, "Input Parameters (mm / kg):", 0, 1)
    for key, val in data.items():
        pdf.cell(0, 8, f"{key}: {val}", 0, 1)
    
    pdf.ln(5)
    pdf.cell(0, 10, "Design Results (mm / kg / N):", 0, 1)
    for key, val in results.items():
        pdf.cell(0, 8, f"{key}: {val}", 0, 1)
    
    # Add images
    for img in ["lift_curve.png", "drag_polar.png", "cg_vs_np.png"]:
        if os.path.exists(img):
            pdf.add_page()
            pdf.image(img, x=15, y=30, w=180)
    
    pdf.output("design_report.pdf")

# =========================
# Main
# =========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    args = parser.parse_args()
    
    data = load_input(args.input)
    
    # Convert inputs to meters internally
    b = data["wingspan"] / 1000  # mm → m
    AR = data["aspect_ratio"]
    W = data["weight"] * 9.81  # kg → N
    CLmax = data["cl_max"]
    taper_ratio = data["taper_ratio"]
    
    # Wing geometry
    S, MAC, C_root, C_tip = calc_wing_geometry(b, AR, taper_ratio)
    
    # Tail areas
    SH, SV = tail_areas(S)
    Lf, Hf, Wf = fuselage_dimensions(b)
    
    # Tail geometry with taper
    b_H = 0.4 * b  # horizontal tail span
    b_V = Hf       # vertical tail height
    C_root_H, C_tip_H = calc_tail_geometry(SH, b_H, data["tail_taper_H"])
    C_root_V, C_tip_V = calc_tail_geometry(SV, b_V, data["tail_taper_V"])
    
    # Aerodynamics
    rho = 1.225
    V = 10  # m/s
    CD0 = 0.02
    e = 0.8
    L, D, CD = calc_aerodynamics(rho, V, S, CLmax, CD0, AR, e)
    Vstall = stall_speed(W, rho, S, CLmax)
    
    # Stability
    x_cg = 0.3*MAC
    x_np = 0.4*MAC
    SM, x_ac = stability(MAC, x_cg, x_np)
    
    # Convert all lengths to mm
    S_mm2 = S * 1e6
    MAC_mm = MAC * 1000
    C_root_mm = C_root * 1000
    C_tip_mm = C_tip * 1000
    Lf_mm = Lf * 1000
    Hf_mm = Hf * 1000
    Wf_mm = Wf * 1000
    SH_mm2 = SH * 1e6
    SV_mm2 = SV * 1e6
    C_root_H_mm = C_root_H * 1000
    C_tip_H_mm = C_tip_H * 1000
    C_root_V_mm = C_root_V * 1000
    C_tip_V_mm = C_tip_V * 1000
    x_ac_mm = x_ac * 1000
    x_cg_mm = x_cg * 1000
    x_np_mm = x_np * 1000
    
    results = {
        "Wing Area (S) mm²": round(S_mm2,1),
        "MAC mm": round(MAC_mm,1),
        "Root Chord mm": round(C_root_mm,1),
        "Tip Chord mm": round(C_tip_mm,1),
        "Horizontal Tail Area SH mm²": round(SH_mm2,1),
        "Vertical Tail Area SV mm²": round(SV_mm2,1),
        "Horizontal Tail Root Chord mm": round(C_root_H_mm,1),
        "Horizontal Tail Tip Chord mm": round(C_tip_H_mm,1),
        "Vertical Tail Root Chord mm": round(C_root_V_mm,1),
        "Vertical Tail Tip Chord mm": round(C_tip_V_mm,1),
        "Fuselage Length mm": round(Lf_mm,1),
        "Fuselage Height mm": round(Hf_mm,1),
        "Fuselage Width mm": round(Wf_mm,1),
        "Lift L (N)": round(L,2),
        "Drag D (N)": round(D,2),
        "Stall Speed Vstall (m/s)": round(Vstall,2),
        "Static Margin": round(SM,3),
        "Aerodynamic Center x_ac mm": round(x_ac_mm,1),
        "CG Position mm": round(x_cg_mm,1),
        "Neutral Point x_np mm": round(x_np_mm,1)
    }
    
    # Console output
    print("========== RC Plane Detailed Design Summary ==========")
    for key, val in results.items():
        print(f"{key}: {val}")
    
    # CSV Output
    df = pd.DataFrame(list(results.items()), columns=["Parameter", "Value"])
    df.to_csv("results.csv", index=False)
    
    # Plots
    plot_lift_curve(CLmax)
    plot_drag_polar(AR, e, CD0)
    plot_cg_vs_np(MAC_mm)
    
    # PDF
    generate_pdf(data, results)
    print("\nResults saved to results.csv and design_report.pdf")

if __name__ == "__main__":
    main()

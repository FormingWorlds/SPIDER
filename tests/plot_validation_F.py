#!/usr/bin/env python
"""Generate validation plots for SPIDER PR (Block F tests).

Creates plots demonstrating:
1. Round-trip comparison: F1 (internal AW) vs F2 (external AW mesh)
2. Field validation summary: F4 results
3. Non-AW mesh test: F3 evolution
4. High-resolution mesh: F6 evolution
5. Reaction test: F5 volatile fields

Output: tests/output/plots/
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUTDIR = Path("tests/output")
PLOTDIR = OUTDIR / "plots"
PLOTDIR.mkdir(parents=True, exist_ok=True)


def load_spider_json(path):
    """Load SPIDER output JSON and extract key fields.

    Parameters
    ----------
    path : str or Path
        Path to SPIDER output JSON file.

    Returns
    -------
    dict
        Extracted fields with SI values (scaling applied).
    """
    with open(path) as f:
        raw = json.load(f)

    result = {"time_years": raw.get("time_years", 0)}

    data = raw.get("data", {})
    for field_name in ["radius_b", "radius_s", "pressure_b", "pressure_s",
                       "entropy_b", "entropy_s", "temperature_b", "temperature_s",
                       "dPdr_b", "melt_fraction_b", "melt_fraction_s",
                       "dxidr_b", "xi_b", "mass_s", "S_s",
                       "kappah_b", "Etot_b"]:
        entry = data.get(field_name)
        if entry:
            scaling = float(entry["scaling"])
            values = np.array(entry["values"], dtype=float) * scaling
            result[field_name] = values

    # Atmosphere data
    atmos = raw.get("atmosphere", {})
    for field_name in ["mass_mantle"]:
        entry = atmos.get(field_name)
        if entry:
            result[field_name] = float(entry["values"][0]) * float(entry["scaling"])

    # Solution data (entropy derivatives)
    sol = raw.get("solution", {})
    subdomain = sol.get("subdomain data", [])
    if len(subdomain) >= 2:
        s0 = subdomain[0]
        result["dSdxi_values"] = np.array(s0["values"], dtype=float) * float(s0["scaling"])
        s1 = subdomain[1]
        result["S_top"] = float(s1["values"][0]) * float(s1["scaling"])

    return result


def plot_round_trip(f1_dir, f2_dir):
    """Plot 1: F1 vs F2 round-trip comparison at final timestep.

    Compares internal AW mesh (F1) against external AW mesh (F2) at t=1200 yr.
    Shows T(r), S(r), phi(r), and residuals.
    """
    d1 = load_spider_json(f1_dir / "1200.json")
    d2 = load_spider_json(f2_dir / "1200.json")

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    # Row 1: absolute values
    fields = [
        ("temperature_s", "Temperature [K]", "T(r)"),
        ("entropy_s", "Entropy [J/(kg K)]", "S(r)"),
        ("melt_fraction_s", "Melt fraction", "phi(r)"),
    ]

    for ax, (field, ylabel, title) in zip(axes[0], fields):
        if field in d1 and field in d2:
            r1 = d1.get("radius_s", np.arange(len(d1[field]))) / 1e6
            r2 = d2.get("radius_s", np.arange(len(d2[field]))) / 1e6
            ax.plot(r1, d1[field], "b-", linewidth=1.5, label="F1 (internal AW)")
            ax.plot(r2, d2[field], "r--", linewidth=1.5, label="F2 (external AW)")
            ax.set_xlabel("Radius [km]")
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.legend(fontsize=8)
        else:
            ax.set_title(f"{title} (not available)")

    # Row 2: residuals
    for ax, (field, ylabel, title) in zip(axes[1], fields):
        if field in d1 and field in d2:
            v1 = d1[field]
            v2 = d2[field]
            if len(v1) == len(v2):
                r = d1.get("radius_s", np.arange(len(v1))) / 1e6
                denom = np.maximum(np.abs(v1), 1e-30)
                rel_diff = (v2 - v1) / denom
                ax.plot(r, rel_diff, "k-", linewidth=0.8)
                ax.axhline(0, color="gray", linestyle=":", alpha=0.5)
                ax.set_xlabel("Radius [km]")
                ax.set_ylabel(f"Relative diff")
                ax.set_title(f"(F2-F1)/F1")
                max_rel = np.max(np.abs(rel_diff))
                ax.text(0.05, 0.95, f"max |rel diff| = {max_rel:.2e}",
                        transform=ax.transAxes, fontsize=9, va="top",
                        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    fig.suptitle("Block F1 vs F2: AW mesh round-trip (t=1200 yr)", fontsize=13)
    fig.tight_layout()
    fig.savefig(PLOTDIR / "F_round_trip_comparison.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {PLOTDIR / 'F_round_trip_comparison.png'}")


def plot_evolution_comparison(f1_dir, f2_dir, f3_dir, f6_dir):
    """Plot 2: Evolution curves for F1, F2, F3, F6.

    Shows melt fraction and entropy evolution over time.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    cases = [
        (f1_dir, "F1: AW internal (n=50)", "b-"),
        (f2_dir, "F2: AW external (n=50)", "r--"),
        (f3_dir, "F3: non-AW (n=50)", "g-."),
        (f6_dir, "F6: AW external (n=200)", "m:"),
    ]

    for case_dir, label, style in cases:
        jsons = sorted(case_dir.glob("*.json"), key=lambda p: float(p.stem))
        if not jsons:
            continue

        times = []
        phi_mean = []
        s_top = []

        for jp in jsons:
            d = load_spider_json(jp)
            times.append(d["time_years"])
            if "melt_fraction_s" in d:
                phi_mean.append(np.mean(d["melt_fraction_s"]))
            if "S_top" in d:
                s_top.append(d["S_top"])

        if phi_mean:
            axes[0].plot(times[:len(phi_mean)], phi_mean, style, label=label, linewidth=1.2)
        if s_top:
            axes[1].plot(times[:len(s_top)], s_top, style, label=label, linewidth=1.2)

    axes[0].set_xlabel("Time [yr]")
    axes[0].set_ylabel("Mean melt fraction")
    axes[0].set_title("Melt fraction evolution")
    axes[0].legend(fontsize=8)

    axes[1].set_xlabel("Time [yr]")
    axes[1].set_ylabel("Surface entropy [J/(kg K)]")
    axes[1].set_title("Surface entropy evolution")
    axes[1].legend(fontsize=8)

    fig.suptitle("Block F: Evolution across mesh types", fontsize=13)
    fig.tight_layout()
    fig.savefig(PLOTDIR / "F_evolution_comparison.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {PLOTDIR / 'F_evolution_comparison.png'}")


def plot_reaction_volatiles(f5_dir):
    """Plot 3: F5 reaction test — volatile partial pressures over time."""
    jsons = sorted(f5_dir.glob("*.json"), key=lambda p: float(p.stem))
    if not jsons:
        print("  No F5 output found")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    # Extract volatile pressures from solution subdomain data
    times = []
    vol_data = {}

    for jp in jsons:
        with open(jp) as f:
            raw = json.load(f)
        t = raw.get("time_years", 0)
        times.append(t)

        sol = raw.get("solution", {}).get("subdomain data", [])
        for s in sol:
            if "Volatile" in s.get("description", ""):
                vals = np.array(s["values"], dtype=float) * float(s["scaling"])
                for i, v in enumerate(vals):
                    key = f"volatile_{i}"
                    vol_data.setdefault(key, []).append(v)

    colors = ["b", "r", "g", "orange"]
    labels = ["H2O", "H2", "CO2", "CO"]
    for i, (key, vals) in enumerate(sorted(vol_data.items())):
        if i < len(labels):
            ax.plot(times[:len(vals)], np.array(vals) / 1e5,
                    color=colors[i % len(colors)], linewidth=1.5, label=labels[i])

    ax.set_xlabel("Time [yr]")
    ax.set_ylabel("Partial pressure [bar]")
    ax.set_title("F5: Volatile evolution (reaction test, n=100)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(PLOTDIR / "F_reaction_volatiles.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {PLOTDIR / 'F_reaction_volatiles.png'}")


def plot_field_validation(f2_dir):
    """Plot 4: F4 field validation summary — computed vs expected."""
    d = load_spider_json(f2_dir / "1200.json")

    # Load mesh file
    mesh = np.loadtxt("tests/data/aw_mesh_50.dat")
    nb = 50
    r_b_file = mesh[:nb, 0]
    P_b_file = mesh[:nb, 1]
    rho_b_file = mesh[:nb, 2]
    g_b_file = mesh[:nb, 3]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    # Top row: absolute fields
    pairs = [
        ("radius_b", r_b_file, "Radius [m]", "radius_b"),
        ("pressure_b", P_b_file, "Pressure [Pa]", "pressure_b"),
        ("dPdr_b", rho_b_file * g_b_file, "dP/dr [Pa/m]", "dPdr_b = rho*g"),
    ]

    for ax, (json_key, expected, ylabel, title) in zip(axes[0], pairs):
        if json_key in d:
            actual = d[json_key]
            n = min(len(actual), len(expected))
            idx = np.arange(n)
            ax.plot(idx, actual[:n], "b-", linewidth=1.5, label="SPIDER JSON")
            ax.plot(idx, expected[:n], "r--", linewidth=1.5, label="Mesh file")
            ax.set_xlabel("Node index")
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.legend(fontsize=8)

    # Bottom row: residuals
    for ax, (json_key, expected, ylabel, title) in zip(axes[1], pairs):
        if json_key in d:
            actual = d[json_key]
            n = min(len(actual), len(expected))
            denom = np.maximum(np.abs(expected[:n]), 1e-30)
            rel = (actual[:n] - expected[:n]) / denom
            ax.plot(np.arange(n), rel, "k-", linewidth=0.8)
            ax.axhline(0, color="gray", linestyle=":", alpha=0.5)
            ax.set_xlabel("Node index")
            ax.set_ylabel("Relative error")
            max_rel = np.max(np.abs(rel))
            ax.set_title(f"max |rel err| = {max_rel:.2e}")

    fig.suptitle("Block F4: External mesh field validation (SPIDER vs mesh file)", fontsize=13)
    fig.tight_layout()
    fig.savefig(PLOTDIR / "F_field_validation.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {PLOTDIR / 'F_field_validation.png'}")


def plot_high_res_profiles(f2_dir, f6_dir):
    """Plot 5: F2 (50 nodes) vs F6 (200 nodes) radial profiles."""
    d2 = load_spider_json(f2_dir / "500.json")
    d6 = load_spider_json(f6_dir / "500.json")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    fields = [
        ("temperature_s", "Temperature [K]"),
        ("entropy_s", "Entropy [J/(kg K)]"),
        ("melt_fraction_s", "Melt fraction"),
    ]

    for ax, (field, ylabel) in zip(axes, fields):
        for d, label, style in [(d2, "n=50", "b-"), (d6, "n=200", "r--")]:
            if field in d:
                r = d.get("radius_s", np.arange(len(d[field]))) / 1e6
                ax.plot(r, d[field], style, linewidth=1.2, label=label)
        ax.set_xlabel("Radius [km]")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=9)

    fig.suptitle("Block F: Resolution comparison at t=500 yr (50 vs 200 nodes)", fontsize=13)
    fig.tight_layout()
    fig.savefig(PLOTDIR / "F_resolution_comparison.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {PLOTDIR / 'F_resolution_comparison.png'}")


def main():
    print("Generating SPIDER PR validation plots (Block F)")
    print()

    f1 = OUTDIR / "F1"
    f2 = OUTDIR / "F2"
    f3 = OUTDIR / "F3"
    f5 = OUTDIR / "F5"
    f6 = OUTDIR / "F6"

    print("Plot 1: Round-trip comparison (F1 vs F2)")
    plot_round_trip(f1, f2)

    print("Plot 2: Evolution across mesh types")
    plot_evolution_comparison(f1, f2, f3, f6)

    print("Plot 3: Reaction volatiles (F5)")
    plot_reaction_volatiles(f5)

    print("Plot 4: Field validation (F4)")
    plot_field_validation(f2)

    print("Plot 5: Resolution comparison (F2 vs F6)")
    plot_high_res_profiles(f2, f6)

    print()
    print(f"All plots saved to {PLOTDIR}/")


if __name__ == "__main__":
    main()

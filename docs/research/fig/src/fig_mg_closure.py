"""그림 r5: 유효 매질 폐합 E = (2a - b - ab)/((1-a)(1-b))의 크기와 판별력 (estimates 5.4절).
가상 자료: Booth et al. 2023 이동도(c = 5.01 깨끗 / 12.63 굳음)로 alpha, j, d/H에서 beta를 만든 뒤 E를 계산.
회색 띠 = 3 sigma(alpha 상대 5 %, beta 상대 2 %, 측정 E 절대 0.02) 안쪽: 측정으로 판별 불가.
"""
import importlib.util
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("mg", os.path.join(HERE, "mg_closure.py"))
mg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mg)

OUT = os.path.join(HERE, "..", "fig_r5_mg_closure.png")
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"   # validated categorical slots 1-3 (all pairs)
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
BAND = "#d9d8d3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False})

RA, RB, DEM = 0.05, 0.02, 0.02
SERIES = [(3, S1), (10, S2), (30, S3)]


def three_sigma(alpha, beta):
    d = math.hypot(2 / (1 - alpha) ** 2 * RA * alpha, 1 / (1 - beta) ** 2 * RB * beta)
    return 3 * math.hypot(d, DEM)


def curve_alpha(dH, c, j, alphas):
    E, B = [], []
    for a in alphas:
        _, _, b = mg.solve(a, j, dH, c)
        E.append(mg.E_mg(a, b))
        B.append(b)
    return np.array(E), np.array(B)


def curve_j(dH, c, a, js):
    E, B = [], []
    for j in js:
        _, _, b = mg.solve(a, j, dH, c)
        E.append(mg.E_mg(a, b))
        B.append(b)
    return np.array(E), np.array(B)


fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6), gridspec_kw={"wspace": 0.22})

# (a) E vs alpha, j = 0.2 m/s
ax = axs[0]
al = np.linspace(0.02, 0.35, 60)
_, Bref = curve_alpha(10, 5.01, 0.2, al)
band = np.array([three_sigma(a, b) for a, b in zip(al, Bref)])
ax.fill_between(al, 0, band, color=BAND, lw=0, zorder=1)
ax.text(0.205, 0.035, "within 3σ of measurement:\nnot testable", fontsize=8.5, color=INK2, ha="left", va="center")
for dH, col in SERIES:
    E5, _ = curve_alpha(dH, 5.01, 0.2, al)
    E12, _ = curve_alpha(dH, 12.63, 0.2, al)
    ax.plot(al, E5, color=col, lw=2, zorder=3, solid_capstyle="round")
    ax.plot(al, E12, color=col, lw=2, ls=(0, (4, 3)), zorder=3)
    ax.text(al[-1] + 0.006, E5[-1], f"d/H = {dH}", color=INK, fontsize=9, va="center")
ax.set_xlim(0, 0.40)
ax.set_ylim(0, 1.05)
ax.set_xlabel("projected void fraction α (from images)")
ax.set_ylabel("φ_L² − 1  (excess pressure drop / liquid-only)")
ax.set_title("(a) excess vs void fraction, j = 0.2 m/s", fontsize=10.5, loc="left")

# (b) E vs j, alpha = 0.2
ax = axs[1]
js = np.logspace(math.log10(0.02), 0, 60)
_, Bref = curve_j(10, 5.01, 0.2, js)
band = np.array([three_sigma(0.2, b) for b in Bref])
ax.fill_between(js, 0, band, color=BAND, lw=0, zorder=1)
for dH, col in SERIES:
    E5, _ = curve_j(dH, 5.01, 0.2, js)
    E12, _ = curve_j(dH, 12.63, 0.2, js)
    ax.plot(js, E5, color=col, lw=2, zorder=3, solid_capstyle="round")
    ax.plot(js, E12, color=col, lw=2, ls=(0, (4, 3)), zorder=3)
    ax.text(js[-1] * 1.06, E5[-1], f"d/H = {dH}", color=INK, fontsize=9, va="center")
ca_lim = 5e-3 * mg.sig / mg.mu      # V at Ca_V = 5e-3
ax.axvline(ca_lim / 1.3, color=MUTED, lw=1, zorder=2)
ax.text(ca_lim / 1.3 * 1.05, 0.5, "Ca_V = 5×10⁻³ if V ≈ 1.3 j\n(Bretherton constants\nwithin 10 % to the left)", fontsize=8, color=INK2, va="center")
ax.set_xscale("log")
ax.set_xlim(0.02, 1.6)
ax.set_ylim(0, 0.55)
ax.set_xlabel("mixture velocity j (m/s)")
ax.set_title("(b) excess vs flow rate, α = 0.2", fontsize=10.5, loc="left")

from matplotlib.lines import Line2D
from matplotlib.patches import Patch
handles = [Line2D([0], [0], color=INK2, lw=2, label="clean interface (c = 5.01)"),
           Line2D([0], [0], color=INK2, lw=2, ls=(0, (4, 3)), label="rigid interface (c = 12.63)"),
           Patch(color=BAND, label="not testable (< 3σ)")]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.0))
fig.suptitle("Effective-medium closure: φ_L² − 1 = (2α − β − αβ)/((1 − α)(1 − β)), β = j_G/j — needs only images + flowmeters",
             fontsize=11, color=INK, y=1.07)
fig.text(0.5, -0.04, "Synthetic data: bubble mobility from Booth et al. 2023 (pancakes, Darcy). σ: α ±5 %, β ±2 %, measured φ_L² ±0.02. "
         "Same d/H gives the same curve in any gap.", fontsize=8, color=INK2, ha="center")
fig.savefig(OUT, dpi=170, bbox_inches="tight")
print("saved", os.path.abspath(OUT))

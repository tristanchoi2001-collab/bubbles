"""모세관 퍼텐셜 표류(I105)와 기울임 두 방향 응답 비(I106)의 예상, 그림 r18. 예상만, 자료 없음.

(a) 가로 표류각 tanφ = K(−∂_yΨ)/(2U), Ψ = 2σ(T)/H − ρgζ, K = H²/12μ (원형, 크기·마찰과 무관).
    갭 기울기 σ∂H/(12μU), 기울임 H²ρg·sinθ/(24μU), 온도 기울기 H|dσ/dT|∂T/(12μU). 물 20 °C.
    잡음 바닥: 쌍극자 요동(I99) 코시 척도 α|λ| = 0.1, 기포 3000개 중앙값 → 약 3 mrad.
(b) 흐름 방향 응답 / 가로 응답 R = (1 + Δ)/(1 + mΔ). Δ = 2/s − 1은 측정 이동도에서 오므로 깨끗한 막의 s(d/H)(0.3 mm, U 0.05 m/s)를 쓰고
    m만 바꿔 그린다(같은 s에서 m에 따라 R이 얼마나 갈리는지).
"""
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

HERE = "/home/user/bubbles/docs/research/fig"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
MU, SIG, RHO, G, DSDT = 1.0e-3, 0.072, 998.0, 9.81, 1.6e-4
KC = 16.85 / (12 * math.pi)


def mobility(aH, u):
    lo, hi = 1e-9, 2.0
    for _ in range(200):
        s = math.sqrt(lo * hi)
        dl = KC / aH * (MU * s * u / SIG) ** (-1 / 3)
        if s > 2 / (1 + dl):
            hi = s
        else:
            lo = s
    return s, dl


U = np.logspace(np.log10(0.005), np.log10(0.2), 100)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.2))
ax1.fill_between(U, 0.05, 3.0, color=GRID, lw=0, zorder=0)
ax1.axhspan(300, 1000, color=GRID, alpha=0.6, lw=0, zorder=0)
ax1.text(0.19, 820, "tan φ ≳ 0.3: crowding, not a small drift", color=MUTED, fontsize=7.2, ha="right", va="top")
ax1.text(0.19, 0.065, "dipole-noise floor (~3000 bubbles, α|λ| 0.1)", color=MUTED, fontsize=7.2, ha="right", va="bottom")
ax1.plot(U, 1e3 * SIG * 1.3e-3 / (12 * MU * U), color=C1, lw=1.6, ls="--", zorder=3)
ax1.plot(U, 1e3 * SIG * 1e-4 / (12 * MU * U), color=C1, lw=2.2, zorder=3)
for H, ls in ((1e-3, "-"), (0.3e-3, ":")):
    ax1.plot(U, 1e3 * H * H * RHO * G * 1e-3 / (24 * MU * U), color=C2, lw=1.8, ls=ls, zorder=3)
    ax1.plot(U, 1e3 * H * DSDT * 200 / (12 * MU * U), color=C3, lw=1.8, ls=ls, zorder=3)
ax1.set_xscale("log"); ax1.set_yscale("log")
ax1.set_xlim(U[0], U[-1]); ax1.set_ylim(0.05, 1000)
ax1.set_xlabel("local liquid speed U_loc (m/s)")
ax1.set_ylabel("lateral drift angle tan φ (mrad)")
ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax1.grid(color=GRID, lw=0.8, which="major", axis="y"); ax1.set_axisbelow(True)
ax1.plot([], [], color=C1, lw=1.6, ls="--", label="cover sag, max slope 1.3×10⁻³ (acrylic 5 mm, 50 kPa, width 50 mm)")
ax1.plot([], [], color=C1, lw=2.2, label="gap slope 10⁻⁴ (2 µm over 20 mm), any H")
ax1.plot([], [], color=C3, lw=1.8, label="liquid ∂T/∂y 200 K/m: H 1 mm (solid), 0.3 mm (dotted)")
ax1.plot([], [], color=C2, lw=1.8, label="tilt 1 mrad: H 1 mm (solid), 0.3 mm (dotted)")
ax1.legend(frameon=False, fontsize=7.0, loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=1)
ax1.set_title("(a) Every source drifts all bubbles by nearly the same angle (∝ 1/U)", fontsize=9.5, color=INK, loc="left")

dH = np.logspace(np.log10(2.0), np.log10(40.0), 80)
D = np.array([mobility(x / 2, 0.05)[1] for x in dH])
for m, col, lab in ((2 / 3, C1, "m = 2/3 (clean film)"), (1 / 3, C3, "m = 1/3"), (0.0, C4, "m = 0 (contact-line threshold): R = 1 + Δ")):
    ax2.plot(dH, (1 + D) / (1 + m * D), color=col, lw=2.0, label=lab)
for x in (3, 10, 30):
    d = mobility(x / 2, 0.05)[1]
    ax2.plot([x], [(1 + d) / (1 + 2 / 3 * d)], "o", ms=8, color=C1, mec=SURF, mew=2.0, zorder=4)
    ax2.annotate(f"{(1 + d) / (1 + 2 / 3 * d):.2f}", (x, (1 + d) / (1 + 2 / 3 * d)), textcoords="offset points",
                 xytext=(0, 8), ha="center", color=INK2, fontsize=7.5)
ax2.set_xscale("log"); ax2.set_yscale("log")
ax2.set_xlim(2, 40); ax2.set_ylim(0.95, 8)
ax2.set_yticks([1, 1.5, 2, 3, 5, 8])
ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax2.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax2.set_xticks([2, 3, 5, 10, 20, 30, 40])
ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax2.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax2.set_xlabel("bubble size d/H")
ax2.set_ylabel("streamwise / lateral tilt response R")
ax2.grid(color=GRID, lw=0.8, which="major", axis="y"); ax2.set_axisbelow(True)
ax2.legend(frameon=False, fontsize=7.2, loc="upper right")
ax2.set_title("(b) Tilting along vs across the flow reads m per size (I106)", fontsize=9.5, color=INK, loc="left")
fig.suptitle("Capillary-potential drift Ψ = 2σ(T)/H − ρgζ: gap, tilt and liquid temperature gradients seen in bubble tracks (expected, I105–I106)",
             fontsize=10, color=INK, x=0.01, ha="left")
fig.text(0.01, -0.035, "(a) Circular pancakes in depth-averaged Darcy flow; the lateral response is the secant mobility, so size and friction cancel in tan φ. "
         "Streamwise speed changes carry the factor R of panel (b).\n"
         "To O(H/d): the thermal term gains (1 + 0.82H/d) from the rim Marangoni boundary layer, the tilt term loses 0.43H/d (rim volume); above tan φ ≈ 0.3 bubbles crowd toward the centre within a few widths (review 8).\n"
         "Sag scales with width⁴: 21 µm at 50 mm becomes 0.55 µm at 20 mm. Gasket or machined-depth expansion adds to the thermal term; only a gap that narrows where hot (e.g. cover bowing) pushes bubbles cold-ward.\n"
         "The sign of the temperature term is to be measured: confined experiments (PDMS cavity dilation, surfactant systems) reported migration to the cold side. "
         "Water at 20 °C, |dσ/dT| = 1.6×10⁻⁴ N/mK.\n"
         "(b) Δ = 2/s − 1 from the measured mobility (here clean films, 0.3 mm, U_loc 0.05 m/s); R = (1 + Δ)/(1 + mΔ). Prediction only — no data.",
         fontsize=7.0, color=MUTED, va="top")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(f"{HERE}/fig_r18_capillary_drift.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("saved")

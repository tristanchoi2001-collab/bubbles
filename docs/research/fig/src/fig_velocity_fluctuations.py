"""추적 속도 요동으로 쌍극자 세기와 마찰 지수를 읽는다(I99·I100), 그림 r16. 예상만, 자료 없음.

(a) 무작위(겹치지 않는) 원판의 2차원 쌍극자 장 λUa²(cos2θ, sin2θ)/r²를 원판 중심에서 더한 값의 반사분위폭.
    코시 극한(안정 지수 2/2 = 1)에서 폭 = πn|D| = α|λ|U. 겹치지 않는 조건이 꼬리를 잘라 g(α) ≈ 1/(1 + 6.7α)(맞춤),
    α → 0에서 1 − 4α(해석). 두 크기 섞임(λ −0.6·+0.55)은 폭이 Σα|λ|를 따르고 부호 있는 합(평균장)은 거의 상쇄된다.
(b) 분포 모양: α 0.02는 코시 중심부, α 0.3은 꼬리가 잘려 정규에 가까워진다.
(c) D ∝ V^m 마찰의 선형 응답: 흐름 방향 요동은 접선 이동도 2/(1 + mΔ), 가로는 할선 이동도 2/(1 + Δ).
    비 R = (1 + Δ)/(1 + mΔ), Δ = 2/s − 1(원형). 작은 기포(s < 1)가 m에 민감하다.
자료: data/i99_dipole_fluct.json(scratchpad의 mc_fig.py로 만든 몬테카를로 결과).
"""
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = "/home/user/bubbles/docs/research/fig"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

d = json.load(open(f"{HERE}/data/i99_dipole_fluct.json"))
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13.2, 4.4))

# (a) 폭 / (α|λ|U)
al = np.array([r["alpha"] for r in d["mono"]])
gx = np.array([r["hiqr_x"] for r in d["mono"]]) / al
gy = np.array([r["hiqr_y"] for r in d["mono"]]) / al
aa = np.linspace(0.0, 0.32, 100)
ax1.plot(aa, 1 / (1 + 6.7 * aa), color=C1, lw=2, zorder=2)
ax1.plot(aa[aa < 0.09], 1 - 4 * aa[aa < 0.09], color=MUTED, lw=1.2, ls="--", zorder=2)
ax1.plot(al, gx, "o", ms=6.5, color=C1, mec=SURF, mew=1.2, zorder=4)
ax1.plot(al, gy, "o", ms=6.5, mfc=SURF, mec=C1, mew=1.4, zorder=4)
for r in d["mix"]:
    at = sum(r["alpha"])
    ax1.plot(at, r["hiqr_small"] / r["sum_abs"], "s", ms=7, color=C2, mec=SURF, mew=1.2, zorder=5)
    ax1.plot(at, r["hiqr_large"] / r["sum_abs"], "^", ms=7.5, color=C2, mec=SURF, mew=1.2, zorder=5)
ax1.text(0.165, 0.535, "1/(1 + 6.7α), fit", color=C1, fontsize=7.6, ha="left")
ax1.text(0.012, 0.66, "1 − 4α\n(α → 0)", color=INK2, fontsize=7.3, ha="left", va="top")
ax1.text(0.105, 0.86, "two-size mixture, λ −0.6 and +0.55:\n■ small probes  ▲ large probes\n(signed mean-field sum is 0.04 of Σα|λ|)",
         color=INK2, fontsize=7.2, ha="left", va="top")
ax1.set_xlim(0, 0.32); ax1.set_ylim(0, 1.15)
ax1.set_xlabel("void fraction α")
ax1.set_ylabel("width (half-IQR) of the field  /  Σα|λ|·U")
ax1.grid(color=GRID, lw=0.8); ax1.set_axisbelow(True)
ax1.plot([], [], "o", ms=6.5, color=C1, mec=SURF, label="streamwise (Monte Carlo)")
ax1.plot([], [], "o", ms=6.5, mfc=SURF, mec=C1, mew=1.4, label="lateral (Monte Carlo)")
ax1.legend(frameon=False, fontsize=7.2, loc="lower left")
ax1.set_title("(a) Width = α|λ|U at small α, both directions", fontsize=9.5, color=INK, loc="left")

# (b) 분포 모양
x = np.linspace(-8, 8, 400)
ax2.plot(x, 1 / (math.pi * (1 + x * x)), color=MUTED, lw=1.4, ls="--", zorder=2)
sig = 1 / 0.67449
ax2.plot(x, np.exp(-x * x / (2 * sig * sig)) / (sig * math.sqrt(2 * math.pi)), color=MUTED, lw=1.4, ls=":", zorder=2)
for key, col in (("0.02", C1), ("0.3", C2)):
    v = np.array(d["hist"][key])
    rec = min(d["mono"], key=lambda r: abs(r["alpha"] - float(key)))
    h = 0.5 * (rec["hiqr_x"] + rec["hiqr_y"]) / rec["alpha"]
    z = v / h
    cnt, edges = np.histogram(z, bins=np.linspace(-8, 8, 41))
    cen = 0.5 * (edges[1:] + edges[:-1])
    pdf = cnt / (len(z) * (edges[1] - edges[0]))
    m = pdf > 0
    ax2.plot(cen[m], pdf[m], "o", ms=5.5, color=col, mec=SURF, mew=1.0, zorder=4)
ax2.set_yscale("log"); ax2.set_ylim(2e-4, 0.8); ax2.set_xlim(-8, 8)
ax2.text(4.2, 0.03, "Cauchy", color=INK2, fontsize=7.4)
ax2.text(2.35, 0.004, "Gaussian", color=INK2, fontsize=7.4, ha="left")
ax2.text(1.7, 0.5, "α 0.02: Cauchy core", color=C1, fontsize=7.4)
ax2.text(1.7, 0.32, "α 0.3: tails cut (no overlap)", color=C2, fontsize=7.4)
ax2.set_xlabel("field fluctuation / its half-IQR")
ax2.set_ylabel("probability density")
ax2.grid(color=GRID, lw=0.8); ax2.set_axisbelow(True)
ax2.set_title("(b) Shape: heavy-tailed, so use quantiles", fontsize=9.5, color=INK, loc="left")

# (c) 비등방 비 R(s; m)
s = np.linspace(0.12, 1.85, 200)
Dl = 2 / s - 1
for m, col, lab, pos in ((1.0, C4, "m = 1 (linear friction)", (1.2, 0.93)), (2 / 3, C1, "m = 2/3 (clean)", (0.55, 1.13)),
                         (1 / 3, C2, "m = 1/3", (0.42, 2.45)), (0.0, C3, "m = 0 (threshold, dry)", (0.66, 3.85))):
    ax3.plot(s, (1 + Dl) / (1 + m * Dl), color=col, lw=2, zorder=3)
    ax3.text(*pos, lab, color=INK2, fontsize=7.4, ha="left")
s0 = 0.345; D0 = 2 / s0 - 1; R0 = (1 + D0) / (1 + 2 / 3 * D0)
ax3.errorbar([s0], [R0], yerr=[[0.03 * R0], [0.03 * R0]], fmt="o", ms=6, color=INK, mec=SURF, capsize=3, zorder=5)
ax3.annotate("±3% in the regression ratio\n→ m ± 0.03 (synthetic test:\nbias −6% → m +0.05)", (s0, R0 * 1.03), xytext=(0.98, 2.95), textcoords="data", fontsize=7.2, color=INK2, va="top",
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
for sv, lab in ((0.345, "d/H 3"), (0.994, "10"), (1.549, "30")):
    ax3.axvline(sv, color=GRID, lw=1.0, zorder=1)
    ax3.text(sv, 4.08, lab, color=MUTED, fontsize=7.0, ha="center", va="bottom")
ax3.set_xlim(0.12, 1.85); ax3.set_ylim(0.9, 4.3)
ax3.set_xlabel("mean mobility s = V/U_loc  (Δ = 2/s − 1)")
ax3.set_ylabel("streamwise / lateral fluctuation width")
ax3.grid(color=GRID, lw=0.8, axis="y"); ax3.set_axisbelow(True)
ax3.set_title("(c) Anisotropy reads the friction exponent m", fontsize=9.5, color=INK, loc="left")

fig.suptitle("Velocity fluctuations of tracked bubbles read the dipole strength Σα|λ| and the friction exponent m, "
             "without pressure or flowmeters (expected, I99·I100)", x=0.01, ha="left", fontsize=10, color=INK)
fig.text(0.01, -0.03, "(a) Monte Carlo: random non-overlapping discs in a 400a square, field λ·U·a²(cos 2θ, sin 2θ)/r² summed at disc centres in the central half (U = a = 1). "
         "A 1/r² field in two dimensions gives a Cauchy sum (stable index 2/2 = 1)\nwith scale πn|D| = α|λ|U; excluded overlap trims the tails. "
         "A bubble's velocity fluctuation is its mobility times this field, so the relative width is the same for every probe size as α → 0;\n"
         "at finite α larger probes keep neighbours further away and see less (triangles). Mixture: equal α of λ = −0.6 (radius a) and +0.55 (3a).\n(c) For a friction D ∝ V^m the streamwise response uses the tangent mobility 2/(1 + mΔ), the lateral response the secant 2/(1 + Δ) (circles, C = 1; checked by solving the vector force balance). "
         "d/H marks: clean films, 0.3 mm, 0.05 m/s.\nCommon-mode pulsation, size and shape spread within a class and position noise inflate the widths and must be removed first (I99). "
         "In moving synthetic suspensions the field's own streamwise/lateral width ratio drifted\nbetween 0.83 and 1.28 with the configuration, so m is read by regressing the velocities on the computed dipole field "
         "(tools/velocity_fluctuations.py --regress: lateral slope 0.347 vs 0.345;\nratio −6% at Δ = 4.8, exact at Δ = 0.29). Prediction only — no data.",
         fontsize=7.0, color=MUTED, va="top")
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r16_velocity_fluctuations.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("g(α) 맞춤 대 몬테카를로:", [(round(r["alpha"], 3), round(0.5 * (r["hiqr_x"] + r["hiqr_y"]) / r["alpha"], 3), round(1 / (1 + 6.7 * r["alpha"]), 3)) for r in d["mono"]])

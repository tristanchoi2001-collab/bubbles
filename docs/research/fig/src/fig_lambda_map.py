"""운전 범위 지도: 갭별로 j_L에 따른 관성 비 Λ = ρ U H²/(10 μ d)(I75). 모양만 보이는 그림.

- U = j_L/(1 − α) ≈ j_L (α ≈ 0.1~0.2면 10~25% 큼, 여기서는 무시).
- 기포 크기 d/H = 10을 굵은 선, 3~30을 띠로. 물 20 °C.
- 기준: Λ < 0.1 깨끗한 Darcy 시험, 0.1~1 경계, > 1 후류가 기포 크기만큼 남을 수 있음(가설, I75: 깊이 평균 퍼텐셜 해는 모든 Λ에서 정확하고,
  벗어남은 와도·단면 분포·가장자리 3차원에서만 생긴다. 와도 감쇠 길이 = Λ·d). Fourar 1993의 1.05 mm 기포는 Λ ≈ 0.3~3이지만 판정 불가(독립 검토 3).
- Moriyama & Inoue 1993의 Re_B = 10 s² Λ(s ≈ 1.5면 22Λ). 그들의 모양 변화 시작 Re_B ≈ 0.4는 Λ ≈ 0.02.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RHO, MU = 998.0, 1.0e-3
GAPS = {0.3: "#86b6ef", 0.7: "#2a78d6", 1.0: "#104281", 3.0: "#eb6834"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

jl = np.logspace(-2.3, np.log10(0.5), 100)
fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.axhspan(1e-4, 0.1, color="#e9f2fc", lw=0, zorder=0)
ax.axhspan(1.0, 1e3, color="#fbe9e1", lw=0, zorder=0)
for H_mm, col in GAPS.items():
    H = H_mm * 1e-3
    lam = lambda dh: RHO * jl * H * H / (10 * MU * dh * H)
    ax.fill_between(jl, lam(30), lam(3), color=col, alpha=0.18, lw=0, zorder=1)
    ax.plot(jl, lam(10), color=col, lw=2.2, zorder=2, label=f"H = {H_mm:g} mm (d/H = 10; band 3–30)")
    ax.text(jl[-1] * 1.05, lam(10)[-1], f"{H_mm:g} mm", color=INK2, fontsize=8, va="center")
ax.axhline(0.1, color=MUTED, lw=1); ax.axhline(1.0, color=MUTED, lw=1)
ax.text(0.0052, 0.06, "clean Darcy test (Λ < 0.1)", color=INK2, fontsize=8, va="top")
ax.text(0.0052, 1.6, "Λ > 1: wakes as long as the bubble may add form drag (hypothesis, idea I75)", color=INK2, fontsize=8, va="bottom")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.005, 0.75); ax.set_ylim(3e-3, 300)
ax.grid(color=GRID, lw=0.8, which="major"); ax.set_axisbelow(True)
ax.set_xlabel("liquid superficial velocity j_L (m/s)")
ax.set_ylabel("Λ = ρ U H² / (10 μ d)   (inertia / Darcy friction)")
ax.legend(frameon=False, fontsize=7.8, loc="lower right")
ax.set_title("Where the zero-parameter closure can be tested: Λ < 0.1 needs 0.3 mm, or 0.7–1 mm\n"
             "with large pancakes at low liquid velocity", fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.12, "Λ uses U ≈ j_L (underestimates by 1/(1 − α)). Water at 20 °C. Bands: bubble diameters d/H = 3 (top) to 30 (bottom).\n"
         "Λ is also the vorticity decay length divided by d. Moriyama & Inoue's bubble Reynolds number Re_B = 10 s² Λ;\n"
         "their shape change starts at Re_B ≈ 0.4 (Λ ≈ 0.02 for s ≈ 1.5). Fourar et al. 1993 bubbles (1.05 mm, d ≈ 15–33 mm):\n"
         "Λ ≈ 0.3–3, but their data cannot separate inertia from a calibration factor. For scale: 0.1 L/min of water in a\n"
         "20-mm-wide channel gives j_L = 0.28 / 0.12 / 0.083 / 0.028 m/s at H = 0.3 / 0.7 / 1 / 3 mm.",
         fontsize=7.2, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r11_lambda_map.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for H_mm in GAPS:
    H = H_mm * 1e-3
    j_at = {dh: 0.1 * 10 * MU * dh * H / (RHO * H * H) for dh in (3, 10, 30)}
    print(f"H {H_mm} mm: j_L for Λ = 0.1 at d/H 3/10/30 = " + ", ".join(f"{v:.3f}" for v in j_at.values()) + " m/s")

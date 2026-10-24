"""판별 평면 위의 문헌 자료(데이터 목록 8절, I80의 예비판). 모양만 보이는 그림, 숫자는 원문 그림·상관식에서 읽은 대략값.

- Moriyama 외 1992(7~98 µm, R113–N₂, Darcy 영역): φ_L² = 1 + K/χ², K = 0.9·Re_L^0.3 → E = K(μ_G/μ_L)B, μ_G/μ_L ≈ 0.026.
  α' = β/C₀(C₀ = 1.35, 96 µm) → s̄ = (C₀ − β)/(1 − β). β 0.2~0.6, K 1~2.8로 띠를 그린다.
- Fourar 외 1993(매끈한 1.05 mm, 공기-물, 관성 영역 Λ ≈ 1.5~9): 그림 6a 판독(S_L 0.96/0.9/0.8 → α, k_rL, k_rG).
  B = (μ_L/μ_G)·k_rG/k_rL, E = 1/k_rL − 1. 독립 점검(review_3.md) 결과에 따라 고칠 수 있다.
- Iida & Takahashi 1976(α = 0.75β), Mishima 외 1993(C₀ ≈ 1.35): E가 같은 정의로 없어 x 범위만 띠로 표시.
- 우리 0.3 mm 예상(설계 17장): x −0.4~−0.7, y 0~0.5.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

# Moriyama 1992 band
mor = []
for C0 in (1.35,):
    for beta in np.linspace(0.2, 0.6, 9):
        s_bar = (C0 - beta) / (1 - beta)
        for K in (1.0, 2.8):
            y = K * 0.026 * s_bar
            mor.append((1 - s_bar, y))
mor = np.array(mor)
# Fourar 1993 readings (S_L, k_rL, k_rG)
four = [(0.96, 0.75, 7e-4), (0.90, 0.72, 1.2e-3), (0.80, 0.68, 4.5e-3)]
fp = []
for SL, krl, krg in four:
    al = 1 - SL
    B = (1e-3 / 1.8e-5) * krg / krl
    E = 1 / krl - 1
    kap = (1 - al) / al
    fp.append((1 - B * kap, E * kap, SL))

fig, ax = plt.subplots(figsize=(7.2, 5.0))
x = np.linspace(-1.2, 1.1, 50)
for ba, lw, al in ((1.0, 2.2, 1.0), (1.5, 1.2, 0.7), (2.0, 1.2, 0.7)):
    ax.plot(x, 1 + ba * x, color=S1, lw=lw, alpha=al, zorder=2,
            label="closure y = 1 + (b/a)x  (b/a = 1, 1.5, 2)" if ba == 1.0 else None)
    if ba > 1:
        ax.text(0.45, 1 + ba * 0.45 + 0.04, f"b/a = {ba:g}", color=INK2, fontsize=7.5, ha="right")
ax.plot(x, np.ones_like(x), color=S2, lw=2, zorder=2, label="separated model y = 1 (Sadatomi 1992)")
ax.plot(x, 1 - x, color=S3, lw=1.6, zorder=2, label="homogeneous y = 1 − x")
ax.axvspan(-0.7, -0.33, ymin=0, ymax=1, color=GRID, lw=0, zorder=0)
ax.text(-0.515, 0.93, "x from α = 0.75β (Iida 1976)\nand C₀ ≈ 1.35 (Mishima 1993)",
        color=INK2, fontsize=7.0, ha="center", va="top")
ax.add_patch(plt.Rectangle((-0.7, 0.0), 0.3, 0.5, fill=False, ec=INK, lw=1.2, ls=(0, (3, 2)), zorder=3))
ax.text(-0.38, 0.52, "our 0.3 mm\n(expected)", color=INK, fontsize=7.6, ha="left", va="bottom")
ax.scatter(mor[:, 0], mor[:, 1], s=16, marker="s", color=INK2, zorder=4,
           label="Moriyama 1992, 7–98 µm (Darcy, Λ ≲ 0.05): C ≈ 0")
YTOP = 2.2
for xx, yy, SL in fp:
    if yy < YTOP:
        ax.plot(xx, yy, "^", ms=8, color=SURF, mec=INK, mew=1.5, zorder=5)
        ax.annotate(f"S_L {SL}", (xx, yy), xytext=(6, 0), textcoords="offset points", fontsize=7.3, color=INK2, va="center")
    else:
        ax.annotate("", xy=(xx, YTOP - 0.02), xytext=(xx, YTOP - 0.22),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=5)
        left = xx < 0
        ax.text(xx + (-0.03 if left else 0.03), YTOP - 0.14, f"S_L {SL}: y = {yy:.1f}", color=INK2, fontsize=7.3,
                va="center", ha="right" if left else "left")
ax.plot([], [], "^", ms=8, color=SURF, mec=INK, mew=1.5, label="Fourar 1993, 1.05 mm (inertial, Λ ≈ 1.5–9), Fig. 6a reading")
ax.set_xlim(-1.2, 1.1); ax.set_ylim(-0.2, YTOP)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("x = 1 − s̄")
ax.set_ylabel("y = E (1 − α)/α")
ax.legend(frameon=False, fontsize=7.4, loc="upper left", bbox_to_anchor=(-0.02, -0.13), ncol=1)
ax.set_title("Literature on the discrimination plane: Darcy-regime data sit near the shape-corrected closure,\n"
             "inertial-regime data lie far above every Darcy line", fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.36, "Moriyama 1992 band: their correlation φ_L² = 1 + K/χ² (K = 1–2.8) with α' = β/C₀ (C₀ = 1.35, 96 µm), β 0.2–0.6 — a consistency check, not point data.\n"
         "Fourar 1993: k_rL, k_rG read from Fig. 6a at S_L = 0.96, 0.9, 0.8 (volume-balance saturation); B = (μ_L/μ_G)k_rG/k_rL, E = 1/k_rL − 1.\n"
         "Shaded band: x implied by literature void-fraction correlations without matching E. Box: expected position of our 0.3 mm data (design ch. 17).",
         fontsize=7.0, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r10_plane_literature.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("Moriyama x", mor[:, 0].min().round(2), mor[:, 0].max().round(2), "y", mor[:, 1].min().round(3), mor[:, 1].max().round(3))
print("Fourar", [(round(a, 2), round(b, 2)) for a, b, _ in fp])

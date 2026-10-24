"""판별 평면 위의 문헌 자료(데이터 목록 8절, I80의 예비판). 모양만 보이는 그림, 숫자는 원문 그림·상관식에서 읽은 대략값.

- Moriyama 외 1992(7~98 µm, R113–N₂, Darcy 영역): φ_L² = 1 + K/χ², K = 0.9·Re_L^0.3 → E = K(μ_G/μ_L)B, μ_G/μ_L ≈ 0.026.
  α' = β/C₀(C₀ = 1.35, 96 µm) → s̄ = (C₀ − β)/(1 − β). β 0.2~0.6, K 1~2.8로 띠를 그린다.
- Fourar 외 1993(매끈한 1.05 mm, 공기-물): 독립 검토 3(review_3.md)의 판독 띠를 쓴다. k_rL은 그림 6a(곡선 9개의 띠),
  B = V_GS/V_LS는 그림 5a의 포화도 등고선(= (μ_L/μ_G)k_rG/k_rL, 항등식), E = 1/k_rL − 1.
  사진(그림 4)에 축척이 없어 d ≈ 15~33 mm(탭 간격 추정), D형 → Λ ≈ 0.3~3. 세 S_L이 서로 다른 V_LS에서 오고,
  k_rL에 공통 배율 0.77 하나로도 폐합과 맞으므로 **판정 불가**로 표시한다.
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
# Fourar 1993 reading bands (review_3 table): S_L, k_rL range, B range (Fig. 5a)
four = [(0.96, (0.72, 0.78), (0.04, 0.06)), (0.90, (0.65, 0.80), (0.07, 0.13)), (0.80, (0.55, 0.75), (0.26, 0.31))]
fp = []
for SL, (k1, k2), (b1, b2) in four:
    al = 1 - SL
    kap = (1 - al) / al
    fp.append((1 - b2 * kap, 1 - b1 * kap, (1 / k2 - 1) * kap, (1 / k1 - 1) * kap, SL))

fig, ax = plt.subplots(figsize=(7.2, 5.0))
x = np.linspace(-1.2, 1.1, 50)
for ba, lw, al in ((1.0, 2.2, 1.0), (1.5, 1.2, 0.7), (2.0, 1.2, 0.7)):
    ax.plot(x, 1 + ba * x, color=S1, lw=lw, alpha=al, zorder=2,
            label="closure y = 1 + (b/a)x  (b/a = 1, 1.5, 2)" if ba == 1.0 else None)
    if ba > 1:
        ax.text(0.45, 1 + ba * 0.45 + 0.04, f"b/a = {ba:g}", color=INK2, fontsize=7.5, ha="right")
ax.plot(x, np.ones_like(x), color=S2, lw=2, zorder=2, label="separated model, laminar: y = 1 (Sadatomi 1992)")
ax.plot(x, 1 - x, color=S3, lw=1.6, zorder=2, label="homogeneous y = 1 − x")
ax.axvspan(-0.7, -0.33, ymin=0, ymax=1, color=GRID, lw=0, zorder=0)
ax.text(-0.515, 0.93, "x from α = 0.75β (Iida 1976)\nand C₀ ≈ 1.35 (Mishima 1993)",
        color=INK2, fontsize=7.0, ha="center", va="top")
ax.add_patch(plt.Rectangle((-0.7, 0.0), 0.3, 0.5, fill=False, ec=INK, lw=1.2, ls=(0, (3, 2)), zorder=3))
ax.text(-0.73, 0.42, "our 0.3 mm\n(expected)", color=INK, fontsize=7.6, ha="right", va="center")
ax.scatter(mor[:, 0], mor[:, 1], s=16, marker="s", color=INK2, zorder=4,
           label="Moriyama 1992, 7–98 µm (Darcy, Λ ≲ 0.05): C ≈ 0")
YTOP = 3.6
for k, (x1, x2, y1, y2, SL) in enumerate(fp):
    ls = ("-", (0, (4, 2)), (0, (1, 1.5)))[k]
    top = min(y2, YTOP - 0.05)
    if y1 < YTOP:
        ax.add_patch(plt.Rectangle((x1, y1), x2 - x1, top - y1, fill=False, ec=INK, lw=1.3, ls=ls, zorder=5))
    else:
        ax.plot([x1, x2], [YTOP - 0.05, YTOP - 0.05], color=INK, lw=1.3, ls=ls, zorder=5)
    if y2 > YTOP:
        xm = 0.5 * (x1 + x2)
        ax.annotate("", xy=(xm, YTOP - 0.01), xytext=(xm, YTOP - 0.3),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=6)
    lab = f"Fourar S_L {SL}: y {y1:.1f}–{y2:.1f}"
    ly = {0.96: YTOP - 0.08, 0.9: 2.45, 0.8: 1.45}[SL]
    lx = {0.96: x1 - 0.03, 0.9: x2 + 0.03, 0.8: x1 - 0.03}[SL]
    ax.text(lx, ly, lab, color=INK2, fontsize=7.0, va="center", ha="left" if SL == 0.9 else "right")
ax.plot([], [], marker="s", ms=9, ls="none", mfc="none", mec=INK, mew=1.3,
        label="Fourar 1993, 1.05 mm (Λ ≈ 0.3–3): boxes = reading bands. Undecidable: one ×0.77 factor on k_rL fits the closure")
ax.set_xlim(-1.2, 1.1); ax.set_ylim(-0.2, YTOP)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("x = 1 − s̄")
ax.set_ylabel("y = E (1 − α)/α")
ax.legend(frameon=False, fontsize=7.4, loc="upper left", bbox_to_anchor=(-0.02, -0.13), ncol=1)
ax.set_title("Literature on the discrimination plane: the Darcy-regime correlation (Moriyama 1992) sits near the\n"
             "shape-corrected closure; the 1-mm bubble data (Fourar 1993) lie above every line but cannot decide", fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.34, "Moriyama 1992 band: their correlation φ_L² = 1 + K/χ² (K = 1–2.8) with α' = β/C₀ (C₀ = 1.35, 96 µm), β 0.2–0.6 — a consistency check, not point data.\n"
         "Fourar 1993: k_rL from Fig. 6a (band of 9 curves) at S_L = 0.96, 0.9, 0.8 (volume-balance saturation); B = V_GS/V_LS from Fig. 5a; E = 1/k_rL − 1. The three S_L come\n"
         "from different V_LS, and a common factor 0.77 on k_rL (8% effective gap or ~10 K) puts all three on the closure. Fig. 4 has no scale: d ≈ 15–33 mm, D-shaped.\n"
         "Shaded band: x implied by literature void-fraction correlations without matching E. Box: expected position of our 0.3 mm data (design ch. 17).",
         fontsize=7.0, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r10_plane_literature.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("Moriyama x", mor[:, 0].min().round(2), mor[:, 0].max().round(2), "y", mor[:, 1].min().round(3), mor[:, 1].max().round(3))
print("Fourar", [tuple(round(v, 2) for v in f[:4]) for f in fp])

"""판별 평면 위의 문헌 자료(데이터 목록 8절, I80의 예비판). 모양만 보이는 그림, 숫자는 원문 그림·상관식에서 읽은 대략값.

- Moriyama 외 1992(R113–N₂): 독립 검토 4(review_4.md 2.1절)의 원자료 판독 점. φ_L²는 그림 6(98 µm), α'·S'은 그림 8·9(96 µm).
  y = (φ_L² − 1)(1 − α')/α', x = 1 − S'. 막대 = φ_L² 판독 ±0.03. β 0.42~0.67은 채운 점(납작·D형 C_A 1.3~2.3과 맞음,
  Λ ≈ 0.07~0.36), β 0.30~0.33은 빈 점(필요 C_A < 1, 낮은 α' 측정 의심), β 0.22(x = −1.85)는 왼쪽 화살표.
  앞 판은 상관식(K, C₀ = 1.35)을 합친 띠였는데 β 배정이 원자료와 반대였다.
- Fourar 외 1993(매끈한 1.05 mm, 공기-물): 독립 검토 3(review_3.md)의 판독 띠를 쓴다. k_rL은 그림 6a(곡선 9개의 띠),
  B = V_GS/V_LS는 그림 5a의 포화도 등고선(= (μ_L/μ_G)k_rG/k_rL, 항등식), E = 1/k_rL − 1.
  사진(그림 4)에 축척이 없어 d ≈ 15~33 mm(탭 간격 추정), D형 → Λ ≈ 0.3~3. 세 S_L이 서로 다른 V_LS에서 오고,
  k_rL에 공통 배율 0.77 하나로도 폐합과 맞으므로 **판정 불가**로 표시한다.
- Iida & Takahashi 1976(α = 0.75β, πb/8 보정 기공률): 투영 기공률로 바꾸면 s̄ ≈ 1.1~1.55(β 0.2~0.5, 대부분 천이·슬러그) →
  x 범위만 띠로 표시(E가 같은 정의로 없음). Mishima 1993의 C₀ ≈ 1.35는 슬러그 위주 맞춤이라 뺐다.
- 우리 0.3 mm 예상(설계 17장, 독립 검토 4 반영): Booth 이동도로 x ≈ −0.6~0.2, 모양 C_A 1~1.5 → 두 폐합 직선 사이의 쐐기.
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

# Moriyama 1992 point readings (review_4 table 2.1): beta, alpha', S', phi_L^2
MOR = [(0.22, 0.09, 2.85, 1.02), (0.30, 0.18, 1.86, 1.11), (0.33, 0.21, 1.78, 1.11), (0.42, 0.31, 1.52, 1.10),
       (0.52, 0.42, 1.50, 1.10), (0.55, 0.46, 1.39, 1.10), (0.62, 0.51, 1.50, 1.12), (0.67, 0.54, 1.67, 1.15)]
mor = []
for beta, al_, S, phi2 in MOR:
    kap = (1 - al_) / al_
    mor.append((beta, 1 - S, (phi2 - 1) * kap, (phi2 - 1 - 0.03) * kap, (phi2 - 1 + 0.03) * kap))
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
ax.axvspan(-0.55, -0.1, ymin=0, ymax=1, color=GRID, lw=0, zorder=0)
ax.text(-0.6, 2.85, "grey band: x from Iida 1976\n(α = 0.75β → projected α,\nmostly slug flow)",
        color=INK2, fontsize=7.0, ha="right", va="center")
xw = np.linspace(-0.6, 0.2, 30)
ax.fill_between(xw, np.minimum(1 + xw, 1 + 1.5 * xw), np.maximum(1 + xw, 1 + 1.5 * xw), color=S1, alpha=0.18, lw=0, zorder=1)
ax.annotate("our 0.3 mm (expected)", xy=(0.15, 1.18), xytext=(0.62, 0.72), color=INK, fontsize=7.6, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
for beta, xx, yy, ylo, yhi in mor:
    good = beta >= 0.4
    if xx < -1.2:
        ax.annotate("", xy=(-1.19, yy), xytext=(-1.02, yy), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.0), zorder=4)
        ax.text(-1.18, yy + 0.07, f"β {beta} (x {xx:.2f})", color=INK2, fontsize=6.8, va="bottom")
        continue
    ax.plot([xx, xx], [ylo, yhi], color=INK2, lw=1.0, zorder=4)
    ax.plot(xx, yy, "s", ms=5.5, color=INK2 if good else SURF, mec=INK2, mew=1.2, zorder=5)
ax.plot([], [], "s", ms=5.5, color=INK2, label="Moriyama 1992, 96–98 µm R113 (Λ ≈ 0.07–0.36), β 0.42–0.67: needs C_A 1.3–2.3")
ax.plot([], [], "s", ms=5.5, color=SURF, mec=INK2, mew=1.2, label="Moriyama 1992, β 0.30–0.33 (and 0.22, arrow): inconsistent, low-α' suspect")
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
    ly = {0.96: YTOP - 0.08, 0.9: 2.45, 0.8: 2.0}[SL]
    lx = {0.96: x1 - 0.03, 0.9: x2 + 0.03, 0.8: x1 - 0.03}[SL]
    ax.text(lx, ly, lab, color=INK2, fontsize=7.0, va="center", ha="left" if SL == 0.9 else "right")
ax.plot([], [], marker="s", ms=9, ls="none", mfc="none", mec=INK, mew=1.3,
        label="Fourar 1993, 1.05 mm (Λ ≈ 0.3–3): boxes = reading bands. Undecidable: one ×0.77 factor on k_rL fits the closure")
ax.set_xlim(-1.2, 1.1); ax.set_ylim(-0.2, YTOP)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("x = 1 − s̄")
ax.set_ylabel("y = E (1 − α)/α")
ax.legend(frameon=False, fontsize=7.4, loc="upper left", bbox_to_anchor=(-0.02, -0.13), ncol=1)
ax.set_title("Literature on the discrimination plane: Moriyama 1992 (β 0.4–0.7) fits the closure only with flat or\n"
             "D-shaped bubbles (C_A 1.3–2.3); Fourar 1993 lies above every line but cannot decide", fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.36, "Moriyama 1992: φ_L² from Fig. 6 (98 µm), α' and slip S' from Figs. 8–9 (96 µm), read point by point (independent review 4); bars: φ_L² ± 0.03. C_A is not measured, so this is consistency, not a test.\n"
         "Fourar 1993: k_rL from Fig. 6a (band of 9 curves) at S_L = 0.96, 0.9, 0.8 (volume-balance saturation); B = V_GS/V_LS from Fig. 5a; E = 1/k_rL − 1. The three S_L come\n"
         "from different V_LS, and a common factor 0.77 on k_rL (8% effective gap or ~10 K) puts all three on the closure. Fig. 4 has no scale: d ≈ 15–33 mm, D-shaped.\n"
         "Grey band: x from Iida 1976 converted to projected void fraction (no matching E). Blue wedge: expected 0.3 mm data (Booth mobility, C_A 1–1.5; design ch. 17).",
         fontsize=7.0, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r10_plane_literature.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("Moriyama", [(b, round(x, 2), round(y, 2)) for b, x, y, _, _ in mor])
print("Fourar", [tuple(round(v, 2) for v in f[:4]) for f in fp])

"""판별 평면(I73, 추정 5.4절): y = E(1 − α)/α 대 x = 1 − s̄. 모양만 보이는 그림.

- 폐합(모양 인자 c = 1 + b/a): E = c·α/(1 − α) − (c − 1)·B → y = 1 + (b/a)·x. 원형이면 y = 1 + x.
- 분리류 모델(측정 α로 액체 간극 속도, Chierici 외 1974, Sadatomi 외 1992 층류 m = 1): E = α/(1 − α) → y = 1. 난류형(m = 0.25)은 y ≈ 1.75~2.0.
- 균질류(액체 점도, 층류): E = B → y = s̄ = 1 − x.
- 유량만 쓰는 상관식: 같은 B에서 E 고정 → y = (E/B)(1 − x), (1, 0)을 지난다. 예: Chisholm C = 5, 두 상 층류, B = 0.25(s̄ = 1에서 E = 1.36B라 (0, 1)을 지나지 않음).
- α를 쓰는 구조 모델(폐합 가족·분리류·액체 점도 균질류)만 (0, 1)을 지난다.
- 배치(I74, 독립 검토 3): 기울기 b/a → b/a − 2Q/(1 − α). 기울기 0.5 선은 b/a 0.5이거나 흐름 방향 줄(ℓ ≈ 3a, α 0.1)의 원형 기포다.
- 멈춘 기체(s̄ = 0, x = 1): y = c. 하한: 등방 배치면 y ≥ 2(Hashin–Shtrikman), 어떤 배치든 y ≥ 1(Wiener).
- 예상 점: 같은 유량(B = 0.25, j_L = 0.05 m/s)에서 주입기만 바꿔 d/H = 3, 10, 30(깨끗한 계면, Booth 2023 이동도).
  오차: E ±0.02(세로), α ±10%(x와 y를 같은 비율로 바꿔 점을 (1, 0)을 지나는 직선 위로 옮김).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

MU, SIG, MUG = 1.0e-3, 0.072, 1.8e-5
B, JL = 0.25, 0.05


def booth_s(delta):
    lo, hi = 1e-12, 2.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if mid ** (2 / 3) - delta * (2 - mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def point(dh):
    s = 1.0
    for _ in range(100):
        alpha = B / (B + s)
        s = booth_s(1.12 * (MU * JL / (1 - alpha) / SIG) ** (1 / 3) * dh)
    return alpha, s


x = np.linspace(-1.05, 1.15, 50)
fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.axvspan(0.97, 1.03, ymin=0, ymax=1, color=GRID, lw=0, zorder=0)
ax.plot([1, 1], [2, 3.1], color=MUTED, lw=3, solid_capstyle="butt", zorder=1)
ax.plot([1, 1], [1, 2], color=MUTED, lw=1.2, solid_capstyle="butt", zorder=1)
ax.text(1.06, 2.55, "stuck gas,\nisotropic:\ny ≥ 2", color=INK2, fontsize=7.6, va="center")
ax.text(1.06, 1.35, "any\nstuck\nlayout:\ny ≥ 1", color=INK2, fontsize=7.6, va="center")

for ba, ls in ((0.5, (0, (4, 2))), (2.0, (0, (4, 2)))):
    ax.plot(x, 1 + ba * x, color=S1, lw=1.1, ls=ls, alpha=0.7, zorder=2)
    xe, ye = (-1.02, 0.95) if ba < 1 else (0.2, 1.52)
    lab = "slope 0.5: b/a = 0.5, or circles in\nstreamwise trains (ℓ ≈ 3a, α 0.1)" if ba < 1 else f"b/a = {ba:g}"
    ax.text(xe, ye, lab, color=INK2, fontsize=7.6, ha="right" if ba > 1 else "left", va="top" if ba < 1 else "baseline")
ax.plot(x, 1 + x, color=S1, lw=2.2, label="2D closure, circular pancakes: y = 1 + x  (slope = b/a)", zorder=3)
ax.plot(x, np.ones_like(x), color=S2, lw=2, label="separated / interstitial-velocity model, laminar m = 1 (Chierici 1974, Sadatomi 1992): y = 1", zorder=3)
ax.plot(x, 1 - x, color=S3, lw=2, label="homogeneous, liquid viscosity: y = 1 − x", zorder=3)
e_over_b = 5 * np.sqrt(MUG / MU) / np.sqrt(B) + MUG / MU
ax.plot(x, e_over_b * (1 - x), color=S4, lw=2, ls=(0, (6, 3)),
        label=f"flow-rate correlation at fixed B (Chisholm C = 5, B = {B}): y = (E/B)(1 − x)", zorder=3)

pts = []
for dh in (3, 10, 30):
    al, s = point(dh)
    xx, yy = 1 - s, 2 - s
    pts.append((dh, al, s, xx, yy))
    k = (1 - al * 1.1) / (al * 1.1) / ((1 - al) / al)
    k2 = (1 - al * 0.9) / (al * 0.9) / ((1 - al) / al)
    ax.plot([1 - k * s, 1 - k2 * s], [k * yy, k2 * yy], color=INK2, lw=1.2, zorder=4)
    dy = 0.02 * (1 - al) / al
    ax.plot([xx, xx], [yy - dy, yy + dy], color=INK2, lw=1.2, zorder=4)
    inside = al <= 0.3
    ax.plot(xx, yy, "o", ms=8, color=INK if inside else SURF, mec=INK if not inside else SURF, mew=2 if inside else 1.6, zorder=5)
    lab = f"d/H = {dh}" + ("" if inside else f"  (α {al:.2f})")
    if dh == 3:
        ax.text(xx + 0.08, yy, lab, color=INK2, fontsize=8, va="center")
    elif dh == 10:
        ax.annotate(lab, xy=(xx, yy - 0.1), xytext=(0.06, 0.62), fontsize=8, color=INK2,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    else:
        ax.text(xx, yy - 0.25, lab, color=INK2, fontsize=8, ha="center")
ax.plot([], [], "o", ms=8, color=INK, mec=SURF, mew=2,
        label="expected: same flow rates, injector changed (clean, Booth 2023); bars: E ±0.02, α ±10%; hollow: α > 0.3")

ax.plot(0, 1, "o", ms=5, color=SURF, mec=INK2, mew=1.2, zorder=6,
        label="s̄ = 1: structural models (closure, separated, liquid-viscosity homogeneous) give E = B; flow-rate correlations pass (1, 0)")
ax.set_xlim(-1.05, 1.3); ax.set_ylim(-0.1, 3.1)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("x = 1 − s̄   (mobility deficit; s̄ = B(1 − α)/α from imaged α and flow rates)")
ax.set_ylabel("y = E (1 − α)/α   (pressure, normalised by imaged α)")
ax.legend(frameon=False, fontsize=7.6, loc="upper left", bbox_to_anchor=(-0.1, -0.13), ncol=1)
ax.set_title("Structural models are lines through (0, 1); at fixed flow rates, changing only the injector moves\n"
             "points along slope b/a − 2Q/(1 − α) (closure), 0 (separated model) or towards (1, 0) (flow-rate correlations)",
             fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.33,
         "Closure with shape factor c = 1 + b/a (b across, a along the flow): E = c·α/(1 − α) − (c − 1)·B = α/(1 − α) + (b/a)·α(1 − s̄)/(1 − α). "
         "Darcy limit, near-circular, α ≲ 0.3.\n"
         "An error in α moves a point exactly along a line through (1, 0), so random α errors cannot create a positive slope on average (useful where E > 0). "
         "A common relative\nbias in α keeps the line nearly parallel (±10%: fitted slope 0.92/1.08 for these points); a rim-thickness bias δr does not "
         "(δr = ±0.1H: slope 0.70/1.41 from d/H 3 to 30), so calibrate δr first.\n"
         "Bubble layout rotates the line about (0, 1): slope b/a − 2Q/(1 − α), with Q the pair anisotropy including side-wall images (I74). "
         "The wedge correction (β_f) shifts points by O(H/d).\n"
         "Expected d/H = 30 bubbles are near the non-circular limit (δ ≈ ε^(−1/3)); such points should follow the line of their measured b/a, not y = 1 + x.",
         fontsize=7.2, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r9_discrimination_plane.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for dh, al, s, xx, yy in pts:
    print(f"d/H {dh}: alpha {al:.3f}, s {s:.2f}, x {xx:.2f}, y {yy:.2f}, E {yy * al / (1 - al):.3f}")
print("E/B for correlation", round(e_over_b, 3))

"""배치 효과의 부호 교차(I83, I74 정정판): 측정 B로 본 E의 변화 ΔE = 2λQ/(1 − α − λQ)·α/(1 − α). 모양만 보이는 그림.

- λ = s − 1(Booth 이동도, 0.3 mm 물 j_L 0.05 m/s): 작은 기포 d/H 3 → s 0.41, 큰 기포 d/H 30 → s 1.57, 중간 d/H 10 → s 1.04.
- Q = 배치 계수(측벽 거울상 포함, 원 합 = Lorentz 기준). 직사각 격자 Q = (πa/ℓ_x)²[1/3 − 2Σsinh⁻²(πmℓ_y/ℓ_x)] − α.
- 설계 점(폭 20 mm, 큰 기포 가로줄만 폭 60 mm): 작은 기포 a 0.45 mm — 바늘 4·8개 줄(ℓ_x 3a), 가로줄(ℓ_x 5a, ℓ_y 3a).
  큰 기포 a 4.5 mm — 한 줄 ℓ_x 2.5a·3a, 가로줄(셋 나란히 ℓ_y 2.5a, ℓ_x 20 mm). 무리 배치는 Q ≈ 0.
- 곡선은 각 크기의 대표 α로 그린 것이고, 점은 그 배치의 α로 계산한 값이다(그래서 점이 곡선에서 조금 벗어난다).
"""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S1, S2, S3 = "#2a78d6", "#eb6834", "#8a8986"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def q_lattice(a, lx, ly):
    tail = sum(1 / math.sinh(math.pi * m * ly / lx) ** 2 for m in range(1, 200) if math.pi * m * ly / lx < 300)
    return (math.pi * a / lx) ** 2 * (1 / 3 - 2 * tail) - math.pi * a * a / (lx * ly)


def d_e(lam, q, al):
    return 2 * lam * q / (1 - al - lam * q) * al / (1 - al)


small = dict(lam=0.41 - 1, col=S1, name="small pancakes, d/H ≈ 3 (s ≈ 0.41, λ = −0.59)")
large = dict(lam=1.57 - 1, col=S2, name="large pancakes, d/H ≈ 30 (s ≈ 1.57, λ = +0.57)")
mid = dict(lam=1.04 - 1, col=S3, name="middle, d/H ≈ 10 (s ≈ 1.04): anchor, no layout effect (I84)")

pts = []
a = 0.45
for n, lab in ((4, "4 needle trains"), (8, "8 needle trains")):
    lx, ly = 3 * a, 20.0 / n
    pts.append((small, q_lattice(a, lx, ly), math.pi * a * a / (lx * ly), lab))
lx, ly = 5 * a, 3 * a
pts.append((small, q_lattice(a, lx, ly), math.pi * a * a / (lx * ly), "pulsed rows"))
pts.append((small, 0.0, 0.19, "random (porous plug)"))
a = 4.5
for k in (2.5, 3.0):
    lx, ly = k * a, 20.0
    pts.append((large, q_lattice(a, lx, ly), math.pi * a * a / (lx * ly), f"one train, spacing {k:g}a"))
lx, ly = 20.0, 2.5 * a
pts.append((large, q_lattice(a, lx, ly), math.pi * a * a / (lx * ly), "rows of 3 (60-mm channel)"))
a = 1.5
lx, ly = 3 * a, 10.0
pts.append((mid, q_lattice(a, lx, ly), math.pi * a * a / (lx * ly), "2 trains"))

fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.axhspan(-0.02, 0.02, color=GRID, lw=0, zorder=0)
ax.axhline(0, color=MUTED, lw=0.8, zorder=1)
ax.axvline(0, color=MUTED, lw=0.8, zorder=1)
q = np.linspace(-0.3, 0.32, 100)
for g, al in ((small, 0.19), (large, 0.24), (mid, 0.16)):
    ax.plot(q, d_e(g["lam"], q, al), color=g["col"], lw=2, zorder=2, label=g["name"])
offs = {"4 needle trains": (8, -4), "8 needle trains": (8, -12), "pulsed rows": (8, 6), "random (porous plug)": (-8, -14),
        "one train, spacing 2.5a": (-10, 6), "one train, spacing 3a": (8, 4), "rows of 3 (60-mm channel)": (8, -8), "2 trains": (8, -12)}
for g, qq, al, lab in pts:
    de = d_e(g["lam"], qq, al)
    ax.plot(qq, de, "o", ms=7.5, color=g["col"], mec=SURF, mew=1.8, zorder=4)
    dx, dy = offs[lab]
    ax.annotate(f"{lab} (α {al:.2f})", (qq, de), xytext=(dx, dy), textcoords="offset points", fontsize=7.2, color=INK2,
                ha="left" if dx > 0 else "right", va="center")
ax.text(-0.295, 0.024, "±0.02: E resolution at 0.3 mm (13 Pa)", color=INK2, fontsize=7.2, va="bottom")
ax.text(0.31, -0.15, "streamwise trains →", color=INK2, fontsize=7.6, ha="right")
ax.text(-0.29, 0.195, "← cross-stream rows", color=INK2, fontsize=7.6, ha="left")
ax.set_xlim(-0.3, 0.32); ax.set_ylim(-0.17, 0.21)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("layout coefficient Q  (pair anisotropy with side-wall images; random layout ≈ 0)")
ax.set_ylabel("ΔE at measured α and B  (layout − random)")
ax.legend(frameon=False, fontsize=7.6, loc="upper left", bbox_to_anchor=(-0.02, -0.14), ncol=1)
ax.set_title("Predicted crossover: arranging bubbles in streamwise trains lowers the pressure drop of slow\n"
             "bubbles and raises it for fast ones, with the opposite for cross-stream rows (I83)",
             fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.33, "ΔE = [2λQ/(1 − α − λQ)]·α/(1 − α), λ = s − 1 (dipole-level local-field correction, independent review 3; periodic-lattice check within 1–2%).\n"
         "Mobility from Booth et al. (2023) for water, H = 0.3 mm, j_L = 0.05 m/s. Channel width 20 mm unless noted; Q from the rectangular-lattice formula.\n"
         "Curves use one representative α per size class; points use the α of each layout. Prediction only — no data.",
         fontsize=7.0, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r12_layout_crossover.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for g, qq, al, lab in pts:
    print(f"{g['name'][:14]:14s} {lab:28s} Q {qq:+.3f} α {al:.3f} ΔE {d_e(g['lam'], qq, al):+.3f}")

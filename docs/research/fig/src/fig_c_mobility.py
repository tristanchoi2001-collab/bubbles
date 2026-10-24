"""Chisholm C의 예상값: 기포 이동도(Booth 2023 법칙) + 유효 매질 폐합 대 Lee & Lee 2001 층류-층류 상관식.

정밀 계산이 아니라 경향을 보이는 그림이다(estimates_microgap.md 5.4절 "다른 꼴과 L–M 연결").
- 한 크기 d/H의 팬케이크만 있다고 본다. Booth: s^(2/3) = δ(2 − s), δ = 1.12·Ca_U^(1/3)·d/H, Ca_U = μU_m/σ.
- 기체 보존 α = B/(B + s), U_m = j_L/(1 − α). E = B(2 − s)/s, C = √(μ_L/μ_G)·√B·(2 − s)/s − √(μ_G/μ_L)·√B.
- Lee & Lee 2001a 층류-층류: C = 6.833e-8·λ^−1.317·ψ^0.719·Re_Lo^0.557, λ = μ²/(ρσD_h), ψ = μj_L/σ
  (Wang 외 2018 JATSR 표 1의 2차 인용. ψ의 j는 액체 겉보기 속도로 가정). 폭 20 mm 가정.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAMP = {3: "#86b6ef", 10: "#2a78d6", 30: "#104281"}
REF = "#eb6834"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

MU, RHO, SIG, MUG, W = 1.0e-3, 998.0, 0.072, 1.8e-5, 20e-3
B = 0.25  # j_G/j_L (β = 0.2)


def booth_s(delta):
    lo, hi = 1e-12, 2.0  # s^(2/3) − δ(2 − s)는 s에 대해 증가 → 이분법
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if mid ** (2 / 3) - delta * (2 - mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def c_mobility(jl, dh_ratio):
    s = 1.0
    for _ in range(100):
        alpha = B / (B + s)
        ca = MU * jl / (1 - alpha) / SIG
        s = booth_s(1.12 * ca ** (1 / 3) * dh_ratio)
    c = np.sqrt(MU / MUG) * np.sqrt(B) * (2 - s) / s - np.sqrt(MUG / MU) * np.sqrt(B)
    return c, ca


def c_leelee(jl, h):
    dh = 2 * h * W / (h + W)
    lam = MU ** 2 / (RHO * SIG * dh)
    psi = MU * jl / SIG
    re = RHO * jl * dh / MU
    return 6.833e-8 * lam ** -1.317 * psi ** 0.719 * re ** 0.557, re


jl = np.logspace(-2, np.log10(0.5), 120)
fig, ax = plt.subplots(figsize=(7.6, 4.6))
for dh_ratio, col in RAMP.items():
    cc, ca = np.array([c_mobility(j, dh_ratio) for j in jl]).T
    ok = ca <= 5e-3
    ax.plot(jl[ok], cc[ok], color=col, lw=2, label=f"pancakes, d/H = {dh_ratio} (any gap)")
    ax.plot(jl[~ok], cc[~ok], color=col, lw=2, ls=(0, (1, 2)))
    ax.text(0.0105, cc[0] * 1.12, f"d/H = {dh_ratio}", color=INK2, fontsize=8, va="bottom")
for h, dash in ((0.3e-3, (0, (2, 2))), (0.7e-3, (0, (5, 2))), (1.0e-3, (0, (9, 3)))):
    cl, re = np.array([c_leelee(j, h) for j in jl]).T
    inside = re >= 175
    ax.plot(jl, cl, color=REF, lw=1.2, ls=dash, alpha=0.45)
    if inside.any():
        ax.plot(jl[inside], cl[inside], color=REF, lw=2, ls=dash,
                label=f"Lee & Lee 2001 lam.-lam., H = {h * 1e3:.1f} mm")
    ax.text(jl[-1] * 1.06, cl[-1], f"LL {h * 1e3:.1f} mm", color=INK2, fontsize=8, va="center")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.009, 0.9); ax.set_ylim(5e-4, 60)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("liquid superficial velocity j_L (m/s)")
ax.set_ylabel("Chisholm C  (β = 0.2, air–water)")
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_title("Expected Chisholm C from bubble mobility: set by bubble size (injector), falls with velocity,\n"
             "and lies far above Lee & Lee's laminar fit", fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.07, "Pancakes: Booth et al. 2023 mobility s(δ), δ = 1.12 Ca^(1/3) d/H (clean), one size per curve; "
         "C = √(μ_L/μ_G)·√B·(2 − s)/s (2D effective-medium closure).\n"
         "Same d/H and Ca give the same C in every gap. Dotted: Ca > 5×10⁻³ (outside Booth's range). "
         "Lee & Lee 2001a via Wang et al. 2018 (secondary), width 20 mm;\nfaint where Re_Lo < 175 (outside their fit). "
         "Width-spanning plugs (1D flow) are expected to give small C like Lee & Lee.", fontsize=7.2, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r7_chisholm_c_mobility.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for h in (0.3e-3, 1e-3):
    for j in (0.02, 0.05, 0.1, 0.2):
        print(f"H {h*1e3:.1f} jl {j}: " + ", ".join(f"d/H {d}: C {c_mobility(j, d)[0]:.2f}" for d in RAMP) + f", LeeLee {c_leelee(j, h)[0]:.3f}")

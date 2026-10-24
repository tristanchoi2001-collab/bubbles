"""보이지 않는 크기 d*(이동도 1)의 예상, 그림 r17 (I104). 예상만, 자료 없음.

원형 기포에서 s = 1 ↔ Δ = 1. 깨끗한 막(D = 16.85σaCa^(2/3))이면 d*/H = 1/(1.12·Ca_loc^(1/3)).
마찰 계수가 f배면 d* ∝ f, 마찰이 D ∝ V^m이면 d* ∝ Ca^(m − 1)(같은 Ca_ref에서 맞춰 그림).
가로로 넓은 타원(b/a 1.27)은 마찰이 1.17배(모양 배율)라 d*가 1.17배(f와 섞임).
Darcy 영역에서 d*/H는 갭과 무관하다(0.3·0.7·1 mm 공통). 물 20 °C의 Ca_loc = μU_loc/σ, U_loc = j_L/(1 − α).
"""
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

ca = np.logspace(-4.3, -2.3, 100)
ref = 7e-4                                    # m 비교의 기준 Ca(0.3 mm, 0.05 m/s 근처)
clean = 1 / (1.12 * ca ** (1 / 3))
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.fill_between(ca, 1.26 * clean, 2.52 * clean, color=C2, alpha=0.22, lw=0, zorder=1)
ax.plot(ca, clean, color=C1, lw=2.2, zorder=3)
ax.plot(ca, 1.26 * clean, color=C2, lw=1.0, zorder=2)
ax.plot(ca, 2.52 * clean, color=C2, lw=1.0, zorder=2)
d_ref = 1 / (1.12 * ref ** (1 / 3))
ax.plot(ca, d_ref * (ca / ref) ** (1 / 3 - 1), color=C3, lw=1.6, ls="--", zorder=3)
ax.plot(ca, d_ref * (ca / ref) ** (0 - 1), color=C4, lw=1.6, ls=":", zorder=3)
for U, lab in ((0.02, "0.02"), (0.05, "0.05"), (0.1, "0.1"), (0.2, "0.2 m/s")):
    c = 1e-3 * U / 0.072
    ax.axvline(c, color=GRID, lw=1.0, zorder=0)
    ax.text(c, 3.15, lab, color=MUTED, fontsize=7.0, ha="center", va="bottom")
ax.text(5.5e-5, 11.5, "clean films: d*/H = 1/(1.12 Ca^(1/3))", color=C1, fontsize=7.6, ha="left", va="top")
ax.text(5.0e-4, 1.78 / (1.12 * 5.0e-4 ** (1 / 3)), "soluble surfactant ×1.26–2.52", color=INK2, fontsize=7.6, ha="left", va="center", rotation=-15.5, rotation_mode="anchor")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(ca[0], ca[-1]); ax.set_ylim(3, 60)
ax.set_yticks([3, 5, 10, 20, 30, 50])
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_xlabel("local capillary number Ca_loc = μ U_loc / σ   (U_loc = j_L/(1 − α); labels: U_loc for water)")
ax.set_ylabel("invisible bubble size d*/H  (mobility s = 1)")
ax.grid(color=GRID, lw=0.8, which="major", axis="y"); ax.set_axisbelow(True)
ax.plot([], [], color=C1, lw=2.2, label="clean interface, m = 2/3")
ax.fill_between([], [], [], color=C2, alpha=0.22, label="soluble surfactant, f = 1.26–2.52")
ax.plot([], [], color=C3, lw=1.6, ls="--", label="m = 1/3: slope m − 1 = −2/3 (matched at Ca 7×10⁻⁴)")
ax.plot([], [], color=C4, lw=1.6, ls=":", label="m = 0 (threshold): slope −1 (matched at Ca 7×10⁻⁴)")
ax.legend(frameon=False, fontsize=7.2, loc="lower left", bbox_to_anchor=(0.0, 0.07))
ax.set_title("The size that moves exactly with the liquid reads the friction law without pressure taps:\n"
             "its magnitude gives the contamination factor f (needs Ca_loc, i.e. U_loc), its slope against Ca gives m − 1 (expected, I104)",
             fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.03, "Circular pancakes, s = 2/(1 + Δ) = 1 ⇔ Δ = 1 ⇔ δ_B = 1.12·Ca^(1/3)·d/H = 1 (Booth et al. 2023). In Darcy flow d*/H is independent of the gap, so 0.3, 0.7 and 1 mm share these lines.\n"
         "Four signals vanish at d* to O(2h/H): mean mobility − 1 (I91) at s = 1; the velocity-fluctuation share (I99), the side-wall speed change (I101) and the tracer dipole signal (I88)\n"
         "at s = 1 + 1.34Ca^(2/3), because the deposited films stay on the walls (d* differs by 1.7–4.4%, independent review 8).\n"
         "Bubbles wider than long (b/a 1.27) carry 1.17× the meniscus friction of the equal-area circle, which shifts d* like f; report b/a with d*. Prediction only — no data.",
         fontsize=7.0, color=MUTED, va="top")
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r17_invisible_size.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for U in (0.02, 0.05, 0.1):
    c = 1e-3 * U / 0.072
    print(f"U_loc {U}: Ca {c:.2e}, d*/H 깨끗 {1 / (1.12 * c ** (1 / 3)):.1f}")

"""마찰 법칙의 두 판독(I89~I91), 그림 r14. 독립 검토 6 반영판.

앞 판의 (a) "원판 계산에서 힘 균형은 정확"은 원판 모형의 대수 항등식(E = Σ B_i/ε_i)이라 지웠다(검토 6 #1).
지금 판은 예상만 그린다. 0.3 mm 갭, 20 °C 물, 묽은 극한(국소 유속 U_loc = j_L = 0.05 m/s), 원형(C = 1), 단분산.
(a) 압력 판독: 시간 평균 힘 균형 E = B·⟨Δ⟩_j에서 단분산이면 E/B = Δ = K·D/(V·A·H), K = H²/12μ.
(b) 추적만의 판독: 이동도 s = V/U_loc = 2/(1 + Δ).
계면 상태 셋(검토 6 §3.2의 판독표, I90).
- 깨끗: D = 16.85σaCa_V^(2/3)(평면 Bretherton 앞·뒤 3.88 + 1.13을 둘레로 적분, Booth 외 2023의 δ_B = 1.12Ca^(1/3)d/H와 같음).
- 잘 녹는 계면활성제(굴림: 계면이 벽과 함께): 같은 꼴, 계수 ×1.26(벽 힘, Cantat 2013) ~ ×2.52(메니스커스 압력 점프, Booth 외). 띠로 그린다.
- 녹지 않는 계면활성제(미끄럼: 계면이 기포와 함께): 메니스커스 ×1.38 + 발자국 막 전단 6.86σ(a²/H)Ca_V^(1/3).
  자기 일관으로 풀면 s ≈ 1300·Ca_loc²(여기서 6×10⁻⁴, 막 약 20 nm) → 사실상 걸린 기포. 검토 6의 "s 0.02~0.1"은 U 0.3~0.6 m/s의 값이다.
Ca_V = μV/σ(기포 속도), Ca_loc = μU_loc/σ.
"""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

HERE = "/home/user/bubbles/docs/research/fig"
CLEAN, SOL, SLIDE = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

MU, SIG, H, JL = 1.0e-3, 0.072, 0.3e-3, 0.05
KC = 16.85 / (12 * math.pi)        # 깨끗: Δ = KC·(H/a)·Ca_V^(−1/3)
KF = 6.86 / (12 * math.pi)         # 미끄럼 발자국 막 전단: Δ = KF·Ca_V^(−2/3)


def mobility(aH, u_loc, state, f=1.0):
    """s = 2/(1 + Δ(V)), V = s·u_loc를 로그 이분법으로 푼다. (s, Δ)."""
    lo, hi = 1e-9, 2.0
    for _ in range(200):
        s = math.sqrt(lo * hi)
        ca = MU * s * u_loc / SIG
        if state == "slide":
            dl = 1.38 * KC / aH * ca ** (-1 / 3) + KF * ca ** (-2 / 3)
        else:
            dl = f * KC / aH * ca ** (-1 / 3)
        if s > 2 / (1 + dl):
            hi = s
        else:
            lo = s
    return s, dl


dH = np.logspace(np.log10(2.0), np.log10(40.0), 90)
aH = dH / 2
cl = np.array([mobility(x, JL, "clean") for x in aH])
s1 = np.array([mobility(x, JL, "clean", 1.26) for x in aH])
s2 = np.array([mobility(x, JL, "clean", 2.52) for x in aH])
sl = np.array([mobility(x, JL, "slide") for x in aH])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.5))
ax1.fill_between(dH, s1[:, 1], s2[:, 1], color=SOL, alpha=0.28, lw=0, zorder=2)
ax1.plot(dH, s1[:, 1], color=SOL, lw=1.0, zorder=3)
ax1.plot(dH, s2[:, 1], color=SOL, lw=1.0, zorder=3)
ax1.plot(dH, cl[:, 1], color=CLEAN, lw=2, zorder=4)
ax1.axhline(1, color=MUTED, lw=0.9, zorder=1)
ax1.text(2.1, 0.93, "Δ = 1 ⇔ s = 1: E = B (I84)", color=INK2, fontsize=7.3, ha="left", va="top")
ax1.text(2.9, 3.3, "clean, k = 16.85", color=CLEAN, fontsize=7.6, ha="left", va="top", rotation=-31)
ax1.text(3.3, 9.2, "soluble surfactant ×1.26–2.52", color=INK2, fontsize=7.6, ha="left", va="center", rotation=-31)
ax1.annotate("fully rigid, sliding interface:\nΔ ≈ 3×10³ (off scale)", xy=(14, 40), xytext=(14, 20), textcoords="data",
             color=INK2, fontsize=7.3, ha="center", va="top",
             arrowprops=dict(arrowstyle="->", color=SLIDE, lw=1.6))
ax1.set_xscale("log"); ax1.set_yscale("log")
ax1.set_ylim(0.1, 40)
ax1.set_ylabel("excess pressure per gas flow  E/B = Δ")
ax1.set_title("(a) Pressure readout (needs ΔP and the gas flow)", fontsize=9.5, color=INK, loc="left")

ax2.fill_between(dH, s1[:, 0], s2[:, 0], color=SOL, alpha=0.28, lw=0, zorder=2)
ax2.plot(dH, s1[:, 0], color=SOL, lw=1.0, zorder=3)
ax2.plot(dH, s2[:, 0], color=SOL, lw=1.0, zorder=3)
ax2.plot(dH, cl[:, 0], color=CLEAN, lw=2, zorder=4)
ax2.plot(dH, sl[:, 0], color=SLIDE, lw=2, ls="--", zorder=4)
ax2.axhline(1, color=MUTED, lw=0.9, zorder=1)
ax2.text(2.1, 1.08, "s = 1: bubble moves with the local liquid", color=INK2, fontsize=7.3, va="bottom")
ax2.text(39, 1.75, "clean", color=CLEAN, fontsize=7.6, ha="right", va="bottom")
ax2.text(39, 0.62, "soluble surfactant\n×1.26–2.52", color=INK2, fontsize=7.6, ha="right", va="top")
ax2.text(39, 8.5e-4, "fully rigid, sliding (insoluble surfactant):\ns ≈ 1300·Ca_loc², films ≈ 20 nm → pinned",
         color=INK2, fontsize=7.3, ha="right", va="bottom")
ax2.set_xscale("log"); ax2.set_yscale("log")
ax2.set_ylim(2e-4, 3)
ax2.set_ylabel("tracked mobility  s = V / U_loc")
ax2.set_title("(b) Tracking-only readout (no pressure needed)", fontsize=9.5, color=INK, loc="left")

for ax in (ax1, ax2):
    ax.set_xlim(2, 40)
    ax.set_xticks([2, 3, 5, 10, 20, 30])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("bubble diameter d/H  (0.3 mm gap, water)")
    ax.grid(color=GRID, lw=0.8, which="major"); ax.set_axisbelow(True)
ax1.plot([], [], color=CLEAN, lw=2, label="clean interface (Bretherton films)")
ax1.fill_between([], [], [], color=SOL, alpha=0.28, label="soluble surfactant (rolling), ×1.26–2.52")
ax1.plot([], [], color=SLIDE, lw=2, ls="--", label="insoluble surfactant (rigid, sliding)")
ax1.legend(frameon=False, fontsize=7.2, loc="lower left")
fig.suptitle("A contaminated interface shows twice: a larger excess pressure per gas flow (a) and a lower tracked mobility (b);\n"
             "a fully rigid, sliding interface would leave the bubbles practically stuck (expected, I89–I91)",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.text(0.01, -0.10, "Time-averaged force balance for moving bubbles with all gas in counted bubbles: E = B·⟨Δ⟩_j, Δ = K·D/(V·A·H), K = H²/12μ; one size ⇒ E/B = Δ. "
         "Circle (C = 1): s = 2/(1 + Δ); dilute limit U_loc = j_L = 0.05 m/s.\n"
         "Clean: D = 16.85σa·Ca_V^(2/3) (planar Bretherton front/rear 3.88 + 1.13 integrated round the rim = Booth et al. 2023). "
         "Soluble surfactant: same law ×1.26 (wall force, Cantat 2013) to ×2.52 (meniscus jump, Booth et al.).\n"
         "Rigid sliding: meniscus ×1.38 + footprint film shear 6.86σ(a²/H)·Ca_V^(1/3) (Cantat 2013 over the footprint, review 6), solved self-consistently "
         "(0.02–0.1 only at U ≈ 0.3–0.6 m/s).\nCa_V = μV/σ, Ca_loc = μU_loc/σ. At j_L = 0.2 m/s the clean curve rises to s 0.56/1.26/1.70 at d/H 3/10/30. Prediction only — no data.",
         fontsize=7.0, color=MUTED)
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r14_velocity_closure.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for x in (3, 10, 30):
    c, a, b, r = (mobility(x / 2, JL, "clean"), mobility(x / 2, JL, "clean", 1.26),
                  mobility(x / 2, JL, "clean", 2.52), mobility(x / 2, JL, "slide"))
    print(f"d/H {x}: 깨끗 s {c[0]:.3f} Δ {c[1]:.3f} | 녹는 s {b[0]:.3f}~{a[0]:.3f} Δ {a[1]:.2f}~{b[1]:.2f} | 미끄럼 s {r[0]:.2e} Δ {r[1]:.3g}")

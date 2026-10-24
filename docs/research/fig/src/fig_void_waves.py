"""공극률 파(밀도 무늬)의 속도와 기포 속도의 차(I110), 그림 r20. 예상 + 합성 자가 시험, 실측 자료 없음.

(a) 0.3 mm·U_loc 0.05 m/s·α 0.1, 깨끗한 막(m = 2/3, Booth 외 2023의 s^(2/3)/(2 − s) = δ_B, δ_B = 1.12·Ca^(1/3)·d/H).
    폭을 채운 띠의 결손 D = 1 − c/V̄ = αλR(묽은 극한)와 단분산 평균장 정확식 αλR/[1 + α(Rs − 1)], 45° 무늬의 αλ,
    한 줄 기포 열(중심 간격 8a)의 −(2π²/3)λR(a/d)². 이동도 1인 크기 d*에서 모두 0이다.
    점: `tools/void_waves.py --demo`와 같은 평균장 입자 모의(α 0.10, 3000 프레임)의 시드별 결과(빠른 큰 기포 s 1.55 여섯 개,
    느린 작은 기포 s 0.35 다섯 개)를 그 s에 해당하는 d/H에 놓았다.
(b) 방향 의존 D(θ)/(αλ) = 1 + (R − 1)·cos 2θ(θ = 파수와 흐름 사이 각). 선형 마찰(R = 1, Desreumaux 외 2013의 액적)은 수평선이다.
검토 9 반영(2026-10-24): (a)에 지금 시야(흐름 방향 1080~1200 px, 0.02 mm/px)로 잴 수 있는 d/H 범위(a ≤ 0.3·L_s/(4π), 0.3 mm에서
d/H ≤ 3.4~3.8)를 칠하고, 제목의 "ID-free"를 뺐다(무늬 속도만 ID 불필요). (b)의 합성 점은 평균장 정확식 역산(R 1.36 [1.07~1.73]).
"""
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

MU, SIG, U, ALPHA, M = 1.0e-3, 0.072, 0.05, 0.10, 2 / 3
CA = MU * U / SIG


def s_of(dH):
    """s^(2/3)/(2 − s) = δ_B를 이분법으로."""
    delta = 1.12 * CA ** (1 / 3) * dH
    lo, hi = 1e-6, 2 - 1e-9
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid ** (2 / 3) / (2 - mid) > delta:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def R_of(s):
    dl = 2 / s - 1
    return (1 + dl) / (1 + M * dl)


def dH_of_s(s_target):
    lo, hi = 0.1, 500.0
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if s_of(mid) > s_target:
            hi = mid
        else:
            lo = mid
    return math.sqrt(lo * hi)


dH = np.logspace(np.log10(2), np.log10(50), 300)
s = np.array([s_of(x) for x in dH])
lam = s - 1
R = np.array([R_of(x) for x in s])
D_band = ALPHA * lam * R
D_exact = ALPHA * lam * R / (1 + ALPHA * (R * s - 1))
D_45 = ALPHA * lam
D_train = -(2 * math.pi ** 2 / 3) * lam * R / 64.0             # 한 줄 열, 중심 간격 d = 8a(4지름)
d_star = dH_of_s(1.0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.7), gridspec_kw={"width_ratios": [1.35, 1]})
ax1.axvspan(2, 3.6, color=GRID, alpha=0.9, lw=0, zorder=0)
ax1.text(2.06, 0.8, "measurable now:\nfield 1080–1200 px,\nka ≤ 0.3, mode ≥ 2", color=INK2, fontsize=7.0, ha="left", va="bottom")
ax1.axhline(0, color=MUTED, lw=0.8, zorder=1)
ax1.axvline(d_star, color=MUTED, lw=0.8, ls=":", zorder=1)
ax1.text(d_star * 1.04, -14.2, f"d* = {d_star:.1f}H (s = 1)", color=MUTED, fontsize=7.6, ha="left", va="bottom")
ax1.plot(dH, 100 * D_band, color=C1, lw=2.2, zorder=3)
ax1.plot(dH, 100 * D_exact, color=C1, lw=1.2, ls=(0, (1, 1.5)), zorder=3)
ax1.plot(dH, 100 * D_45, color=C3, lw=1.8, ls="--", zorder=3)
ax1.plot(dH, np.clip(100 * D_train, -15, 15), color=C2, lw=1.8, zorder=3)
# 합성 자가 시험(시드별): 그 s의 d/H에 놓는다
fast = [1.078, 1.116, 0.972, 0.954, 1.105, 1.116]
slow = [1.004, 1.000, 1.001, 0.945, 0.931]                    # 마지막은 --demo(시드 8)의 −0.0835/−0.0897
for s_t, ratios, col in ((1.55, fast, C1), (0.35, slow, C1)):
    x0 = dH_of_s(s_t)
    Dt = ALPHA * (s_t - 1) * R_of(s_t)
    xs = x0 * np.exp(np.linspace(-0.05, 0.05, len(ratios)))
    ax1.plot(xs, [100 * Dt * r_ for r_ in ratios], "o", ms=5.5, color=SURF, mec=col, mew=1.5, zorder=4)
ax1.set_xscale("log")
ax1.set_xlim(2, 50); ax1.set_ylim(-15, 15)
ax1.set_xticks([2, 3, 5, 10, 20, 30, 50]); ax1.set_xticklabels(["2", "3", "5", "10", "20", "30", "50"])
ax1.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax1.set_xlabel("bubble size d/H")
ax1.set_ylabel("pattern-speed deficit 1 − c/V̄ (%)")
ax1.grid(color=GRID, lw=0.8, axis="y"); ax1.set_axisbelow(True)
ax1.text(13.5, 1.0, "bands across the width (αλR)", color=C1, fontsize=8, ha="left", va="bottom")
ax1.text(48, 3.6, "45° patterns (αλ)", color=C3, fontsize=8, ha="right", va="top")
ax1.text(2.15, 100 * D_train[0] + 0.8, "single-file train, spacing 8a:\nopposite sign (Booth 2023 cradle)", color=C2, fontsize=8, ha="left", va="bottom")
ax1.text(2.15, 100 * D_band[0] - 0.8, "slow bubbles: pattern runs ahead", color=INK2, fontsize=7.6, ha="left", va="top")
ax1.text(48, 13.6, "fast bubbles: pattern lags\n(needs a field ≥ 42a along the flow)", color=INK2, fontsize=7.6, ha="right", va="top")
ax1.plot([], [], color=C1, lw=1.2, ls=(0, (1, 1.5)), label="bands, mean-field exact αλR/[1 + α(Rs − 1)]")
ax1.plot([], [], "o", ms=5.5, color=SURF, mec=C1, mew=1.5, label="synthetic self-test, one point per seed (void_waves.py)")
ax1.legend(frameon=False, fontsize=7.4, loc="lower right", bbox_to_anchor=(1.0, 0.13))
ax1.set_title("(a) Pattern speed vs bubble speed (0.3 mm, U_loc 0.05 m/s, α 0.1)",
              fontsize=9.5, color=INK, loc="left")

th = np.linspace(0, 90, 181)
for dh, col in ((3, C2), (10, C4), (30, C1)):
    s_ = s_of(dh); R_ = R_of(s_)
    ax2.plot(th, 1 + (R_ - 1) * np.cos(np.radians(2 * th)), color=col, lw=2.0, zorder=3)
    ax2.text(2, 1 + (R_ - 1) + 0.012, f"d/H {dh}: R = {R_:.2f}", color=col, fontsize=8, ha="left", va="bottom")
ax2.axhline(1, color=MUTED, lw=1.0, ls="--", zorder=2)
ax2.text(88, 1.01, "linear friction (droplets, R = 1)", color=MUTED, fontsize=7.6, ha="right", va="bottom")
# 합성 B 경우(s 0.35, d/H ≈ 3): 평균장 정확식 역산 R 1.36 [1.07, 1.73](검토 9 반영 회귀자)
ax2.errorbar([0], [1.36], yerr=[[0.29], [0.37]], fmt="o", ms=5.5, color=C2, mfc=SURF, mec=C2, mew=1.5, capsize=3, zorder=4)
ax2.text(40, 1.62, "synthetic fit (d/H ≈ 3, marker at θ = 0):\nR 1.36 [1.07–1.73], true 1.38; m 0.68 [0.47–0.89]\nwide: a cross-check only, needs a field ≥ 42a across", color=INK2, fontsize=7.2, ha="left", va="center")
ax2.set_xlim(-3, 90); ax2.set_ylim(0.55, 1.8)
ax2.set_xticks([0, 15, 30, 45, 60, 75, 90])
ax2.set_xlabel("angle between pattern wavevector and flow θ (deg)")
ax2.set_ylabel("deficit / αλ = 1 + (R − 1)·cos 2θ")
ax2.grid(color=GRID, lw=0.8, axis="y"); ax2.set_axisbelow(True)
ax2.set_title("(b) Direction dependence from meniscus friction", fontsize=9.5, color=INK, loc="left")
fig.suptitle("Void-fraction waves as a pressure-free readout of the signed mobility deficit λ and the tangent/secant ratio R (expected, I110, review 9)",
             fontsize=10, color=INK, x=0.01, ha="left")
fig.text(0.01, -0.03,
         "Dilute mean field: δu = −λU·δα·(cos 2θ, sin 2θ); streamwise response uses the tangent mobility, lateral the secant one, so ω = k_x·V̄·{1 − αλ[1 + (R − 1)cos 2θ]}. "
         "Linear friction (R = 1) reproduces Desreumaux et al. 2013.\n"
         "A constant-C₀ drift-flux model predicts zero deficit (c/V̄ − 1 = α·d ln C₀/dα). Long waves only (ka ≲ 0.3, wavelength ≤ field/2, so a ≤ 0.3·L_s/4π); "
         "a speed spread inside a class changes the deficit (×1.17–1.28 at 15–30%).\n"
         "Pattern speed needs no track IDs; the reference V̄ does. In a realistic 1080 × 416 px field the sign needs ~200 field transits. "
         "Synthetic points: mean-field particle simulation, not data.",
         fontsize=7.0, color=MUTED, va="top")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(f"{HERE}/fig_r20_void_waves.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print(f"d* = {d_star:.2f}H; D_band at d/H 3/30 = {100 * ALPHA * (s_of(3) - 1) * R_of(s_of(3)):.2f}/{100 * ALPHA * (s_of(30) - 1) * R_of(s_of(30)):.2f}%")

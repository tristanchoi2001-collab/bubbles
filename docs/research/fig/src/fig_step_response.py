"""기체 계단 응답의 예상 모양 (아이디어 I53·I58, design_predictions.md 16.1절).

정밀 계산이 아니라 모양을 보이는 장난감 모델이다.
- 1차원 기포 수송: 크기 구분 k의 면적 비율 α_k(x, t), 속도 V_k = s_k·U_loc.
- 비압축: 단면 전체 유속 j는 어디서나 같다(기체를 켜면 j_L + j_G, 끄면 j_L).
- 국소 기포 사이 액체 속도 U_loc = j / (1 − α + Σ α_k s_k).
- 국소 압력 구배(2차원 유효 매질 폐합의 국소형): G = (12μ/H²)·[U_loc(1 + α) − Σ α_k V_k].
  정상 상태에서는 G/G_L(j_L) = 1 + 2α/(1 − α) − β/(1 − β)로 돌아간다(estimates 5.4절).
- 탭 구간 ΔP = 구간 평균 G. 단상 ΔP_L(j_L)로 나눠 보인다.
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

J_L, BETA = 0.05, 0.15            # 액체 겉보기 속도 (m/s), 기체 유량비
J = J_L / (1 - BETA)
J_G = J - J_L
X1, L = 0.05, 0.10                # 주입부 → 첫 탭 (m), 탭 간격 (m)
G_SPLIT = np.array([0.5, 0.5])    # 기체 유량을 나눠 갖는 비율 (작은 기포, 큰 기포)
CASES = {"mobile: large clean pancakes (s = 1.2 / 1.8)": np.array([1.2, 1.8]),
         "slow: small or contaminated (s = 0.6 / 0.9)": np.array([0.6, 0.9]),
         "mixed sizes (s = 0.6 / 1.8)": np.array([0.6, 1.8])}
SHORT = {"mobile": "mobile", "slow": "slow", "mixed": "mixed"}

N = 1700
x = np.linspace(0, X1 + L + 0.02, N + 1)
xc, dx = 0.5 * (x[1:] + x[:-1]), x[1] - x[0]
tap = (xc >= X1) & (xc <= X1 + L)


def local(al, s, j):
    a = al.sum(0)
    u = j / (1 - a + (al * s[:, None]).sum(0))
    v = s[:, None] * u
    g = (u * (1 + a) - (al * v).sum(0)) / J_L
    return v, g


def run(s, al, j, inflow, t_end):
    ts, dps = [0.0], [local(al, s, j)[1][tap].mean()]
    t = 0.0
    while t < t_end:
        v, _ = local(al, s, j)
        dt = 0.4 * dx / v.max()
        flux = al * v
        upstream = np.concatenate([inflow[:, None], flux[:, :-1]], axis=1)
        al = al - dt / dx * (flux - upstream)
        t += dt
        ts.append(t)
        dps.append(local(al, s, j)[1][tap].mean())
    return np.array(ts), np.array(dps), al


def steady(s):
    # 정상 상태: α_k V_k = g_k j_G, V_k = s_k U_m, U_m = j_L / (1 − α)
    a = 0.0
    for _ in range(200):
        um = J_L / (1 - a)
        ak = G_SPLIT * J_G / (s * um)
        a = ak.sum()
    e = 2 * a / (1 - a) - BETA / (1 - BETA)
    return ak, a, e


fig, axs = plt.subplots(1, 2, figsize=(10.2, 4.2), sharey=True)
results = {}
for (name, s), col in zip(CASES.items(), (S1, S2, S3)):
    al0 = np.zeros((2, N))
    t_on, dp_on, al_ss = run(s, al0, J, G_SPLIT * J_G, 8.0)
    t_off, dp_off, _ = run(s, al_ss, J_L, np.zeros(2), 10.0)
    ak, a, e = steady(s)
    sbar = (ak * s).sum() / a
    results[name] = (a, e, sbar, dp_on.max(), dp_on.min(), dp_on[-1], dp_off.max(), dp_off.min())
    short = name.split(":")[0].split(" ")[0]
    for ax, t, dp in ((axs[0], t_on, dp_on), (axs[1], t_off, dp_off)):
        ax.plot(t, dp, color=col, lw=2, label=name)
    axs[0].text(8.15, dp_on[-1], f"{short}, s\u0304 = {sbar:.2f}", color=INK2, fontsize=8, va="center")

for ax in axs:
    ax.axhline(1, color=MUTED, lw=1, ls=(0, (2, 2)))
    ax.axhline(1 / (1 - BETA), color=MUTED, lw=1, ls=(0, (6, 3)))
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("time after switching the gas (s)")
axs[0].text(4.6, 1 / (1 - BETA) - 0.006, "jump = 1/(1 \u2212 \u03b2) while the tap section is still\nliquid-only \u2192 \u03b2 without a flowmeter (0.3\u20130.7 mm)",
            fontsize=8, color=INK2, va="top")
axs[0].text(5.2, 1.0 + 0.012, "liquid only, j_L", fontsize=8, color=INK2, va="bottom")
axs[1].text(3.0, 0.93, "s\u0304 > 1: dips below the liquid-only value", fontsize=8, color=INK2, va="center")
axs[0].set_title("Gas ON at t = 0", fontsize=10, color=INK, loc="left")
axs[1].set_title("Gas OFF at t = 0 (total flux drops j \u2192 j_L)", fontsize=10, color=INK, loc="left")
axs[0].set_ylabel("\u0394P / \u0394P_L(j_L)   (tap section)")
axs[0].set_xlim(0, 10.6)
axs[1].set_xlim(0, 10)
axs[0].legend(frameon=False, fontsize=8, loc="lower right")
fig.suptitle("Expected \u0394P transient (toy model): the curve shape shows whether bubbles outrun the mixture (s\u0304 > 1), lag it, or are mixed",
             fontsize=10, color=INK, x=0.01, ha="left")
fig.text(0.01, -0.08, f"Model: 1D bubble transport, two size classes sharing the gas flux 50/50, j_L = {J_L} m/s, \u03b2 = {BETA}, injector-to-tap {X1*1000:.0f} mm, tap spacing {L*1000:.0f} mm, mobility s fixed per class.\n"
         "Local closure G/G_L(j_L) = [U(1 + \u03b1) \u2212 \u03a3\u03b1V]/j_L (2D effective medium); each bubble adds 2(1 \u2212 V/j_tot), so fast bubbles lower \u0394P and mixed sizes give non-monotonic curves.\n"
         "s\u0304 > 1 depends on bubble size and Ca as well as contamination (small clean pancakes have s < 1). (1 \u2212 \u03b2)\u00b7ON(t) + OFF(t/(1 \u2212 \u03b2)) = const if bubbles do not interact. Shapes only.",
         fontsize=7.2, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r6_step_response.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for k, (a, e, sbar, mx, mn, ss, offmx, offmn) in results.items():
    print(f"{k}: alpha {a:.3f}, E {e:.3f}, sbar {sbar:.2f}, steady 1+E {1+e:.3f}, ON min {mn:.3f} max {mx:.3f} end {ss:.3f}, OFF min {offmn:.3f} max {offmx:.3f}, jump {1/(1-BETA):.3f}")

"""속도(마찰) 쪽 폐합(I89)이 공극률 쪽 폐합보다 근본적임을 보이는 그림 r14.

(a) I82 원판 계산 재해석: 전도 원판(ε = s/(2 − s))은 선형 마찰 D = HAV/(εK)를 가진 기포와 같아서,
    힘 균형(초과 압력 강하 = 기포 마찰 합)은 E = B/ε가 된다. 원판 하나로 정한 격자 상수로 나눈 비 E·ε/B를
    공극률 폐합(같은 격자 상수 C로 보정)의 상대 오차와 함께 α에 대해 그린다.
(b) 예상: 단분산 기포면 E/B = δ = K·D/(VAH)(기포 하나의 마찰 매개변수). 깨끗한 Bretherton 막 D ≈ 6.7c·σ·a·Ca^(2/3)(c 2.5 =
    평면 Bretherton 앞·뒤 계수 3.88·1.13의 평균, Booth 2023의 1.12와 같음)과 굳은 계면(막 두께·마찰 4^(2/3)배로 가정)을 0.3 mm 물, j_L 0.05·0.1 m/s에서. 묽은 극한(국소 유속 = j_L).
자료: data/i82_sweep.json, data/i82_gap4.json.
"""
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

HERE = "/home/user/bubbles/docs/research/fig"
S = {"0.41": "#2a78d6", "0.8": "#1baf7a", "1.57": "#eb6834"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

d = json.load(open(f"{HERE}/data/i82_sweep.json"))
gap4 = json.load(open(f"{HERE}/data/i82_gap4.json"))
cal = {k: v["E"] * (float(k) / (2 - float(k))) / v["B"] for k, v in d["calib"].items()}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.4))
for s, col in S.items():
    eps = float(s) / (2 - float(s))
    C = d["calib"][s]["C_eff"]
    runs = [r for r in d["runs"] if f"{r['s']:g}" == s] + [r for r in gap4 if f"{r['s']:g}" == s]
    a = np.array([r["alpha"] for r in runs])
    fb = np.array([r["E"] * eps / r["B"] / cal[s] - 1 for r in runs])                    # 힘 균형의 상대 오차
    ecl = np.array([(r["alpha"] * (1 + C) - C * r["B"] * (1 - r["alpha"])) / (1 - r["alpha"]) for r in runs])
    rel = np.array([e / r["E"] - 1 for e, r in zip(ecl, runs)])                          # 공극률 폐합의 상대 오차
    lab = f"s = {s}"
    ax1.plot(a, 100 * rel, "o", ms=6, mfc="none", mec=col, mew=1.3, zorder=3)
    ax1.plot(a, 100 * fb, "o", ms=6, color=col, mec=SURF, mew=1.2, zorder=4, label=lab)
ax1.axhline(0, color=MUTED, lw=0.8, zorder=1)
ax1.plot([], [], "o", ms=6, color=INK2, mec=SURF, label="force balance: Σ friction (velocities only)")
ax1.plot([], [], "o", ms=6, mfc="none", mec=INK2, mew=1.3, label="void-fraction closure (mean field)")
ax1.set_xlabel("void fraction α")
ax1.set_ylabel("prediction error of E (%)")
ax1.set_xlim(0, 0.43)
ax1.grid(color=GRID, lw=0.8); ax1.set_axisbelow(True)
ax1.legend(frameon=False, fontsize=7.4, loc="lower left")
ax1.set_title("(a) Random-disc computation (I82 data)", fontsize=9.5, color=INK, loc="left")

# (b) 예상: E/B = δ(d/H) 단분산
mu, sig, H = 1.0e-3, 0.072, 0.3e-3
K_C = 6.73 * 2.5 / (12 * math.pi)          # δ = K_C·(H/a)·Ca_V^(−1/3)


def delta(aH, jl, factor=1.0):
    dl = 1.0
    for _ in range(200):
        s_ = 2 / (1 + dl)
        ca = mu * s_ * jl / sig
        dl = factor * K_C / aH * ca ** (-1 / 3)
    return dl


aH = np.logspace(np.log10(1.0), np.log10(30.0), 80)
dH = 2 * aH
for jl, ls in ((0.05, "-"), (0.1, "--")):
    ax2.plot(dH, [delta(x, jl) for x in aH], ls, color="#2a78d6", lw=2,
             label=f"clean films, j_L = {jl:g} m/s")
    ax2.plot(dH, [delta(x, jl, 4 ** (2 / 3)) for x in aH], ls, color="#eb6834", lw=2,
             label=f"rigid interface (×4^(2/3), assumed), j_L = {jl:g} m/s")
ax2.axhline(1, color=MUTED, lw=0.9, zorder=1)
ax2.text(2.05, 0.9, "E = B (s = 1, I84)", color=INK2, fontsize=7.3, va="top")
ax2.set_xscale("log"); ax2.set_yscale("log")
ax2.set_xticks([2, 3, 5, 10, 20, 30, 60])
ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax2.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax2.set_xlabel("bubble diameter d/H  (0.3 mm gap, water)")
ax2.set_ylabel("excess pressure per gas flow  E/B = δ")
ax2.grid(color=GRID, lw=0.8, which="both"); ax2.set_axisbelow(True)
ax2.legend(frameon=False, fontsize=7.2, loc="lower left")
ax2.set_title("(b) Expected: one bubble size per injector", fontsize=9.5, color=INK, loc="left")
fig.suptitle("Tracked velocities close the pressure drop exactly: in Darcy flow the liquid wall friction depends only on j_L,\n"
             "so the excess pressure drop is the sum of the bubbles' friction forces (I89)",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.text(0.01, -0.08, "(a) Conducting discs (ε = s/(2 − s)) are bubbles with linear friction D = HAV/(εK), for which the force balance gives E = B/ε; "
         "both predictions use the same single-disc grid constant.\n"
         "(b) δ = K·D/(V·A·H) with D ≈ 6.7c·σ·a·Ca^(2/3), c = 2.5 = mean of the planar Bretherton front/rear coefficients 3.88 and 1.13 (= Booth et al. 2023), dilute limit; "
         "polydisperse flows give the gas-flux-weighted mean of δ.\nRigid-interface factor 4^(2/3) is the Bretherton/Ratulowski–Chang scaling, assumed here. Prediction only — no data.",
         fontsize=7.0, color=MUTED)
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r14_velocity_closure.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for x in (1.5, 5, 15):
    print(f"d/H {2 * x:g}: δ clean {delta(x, 0.05):.3f} (s {2 / (1 + delta(x, 0.05)):.2f}), rigid {delta(x, 0.05, 4 ** (2 / 3)):.3f} (s {2 / (1 + delta(x, 0.05, 4 ** (2 / 3))):.2f})")

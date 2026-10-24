"""단위 쌍극자 장 회귀(I111), 그림 r22. 합성 자가 시험(다분산) + 윤곽 규약 감도 예상, 실측 자료 없음.

(a) `tools/velocity_fluctuations.py`의 다분산 합성(make_demo poly, 시드 1: d/H 2~5·5~14에서 d 고르게, s(d/H)는 0.3 mm·물·0.05 m/s의
    Booth 관계 s^(2/3)/(2 − s) = 1.12(d/H)Ca_U^(1/3), 각 α 0.03, m 2/3, U 6 px/frame, 위치 잡음 0.15 px)에서 되찾은 λ(d) 마디
    (ln d/H 삼각 기저, 95% 트랙 부트스트랩 구간)와 참 곡선. λ = 0인 크기 d*(s = 1)를 표시했다.
(b) 같은 자료의 기포(트랙)마다 평균 속도 V̄_i(회색)와 V̄_i/(1 + λ̂(d_i))(파랑). 크기마다 3배 가까이 다른 속도가 국소장 하나로
    모인다(U가 지워진 회귀에서 거꾸로 U를 냄). d* 근처 기포의 속도는 그대로 국소장이다(U_loc(d*)).
(c) 예상: 검출 윤곽 반경이 0.5 px 어긋날 때 구분별 U_loc = V̄/(1 + λ̂)의 상대 오차 |1 − 1/s|·δA/A(δA/A = 2·0.5/a).
    0.3 mm·0.02 mm/px와 1 mm·0.05 mm/px(철, 가정), U 0.05 m/s. d*에서 0이다(검토 10 #4).
"""
import math
import os
import sys
import tempfile
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

HERE = "/home/user/bubbles/docs/research/fig"
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import velocity_fluctuations as VF  # noqa: E402

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

# (a)(b) 합성 자료
tmp = tempfile.mkdtemp(prefix="fig_i111_")
path = VF.make_demo(tmp, seed=1, poly=True, name="poly.csv")[0]
H_px, k, per, U = 16.0 / 3, 4, (2000.0, 1000.0), 6.0
bins = ((2, 5), (5, 14))
nodes = [2.0, 3.5, 6.0, 10.0, 14.0]
tracks = VF.read_tracks(path, "right", 0.02, H_px * 0.02)
obs, _ = VF.track_velocities(tracks, k, 1, H_px, VF.near_contact(tracks, 0.5, periodic=per))
basis = VF.lam_basis_fields(tracks, bins, nodes, H_px, obs, k, 1, periodic=per, scheme="euler")
lr, tab = VF.lamreg_fit(obs, bins, basis, nodes, periodic=per, n_boot=100)
beta = np.array([t[1] for t in tab])
hat = VF.hat_weights(nodes)
vt, dt = defaultdict(list), defaultdict(list)
for o in obs:
    vt[o[0]].append(o[2]); dt[o[0]].append(o[4])
d_t = np.array([np.median(dt[t]) for t in vt]); v_t = np.array([np.mean(vt[t]) for t in vt])
lam_t = np.array([hat(d) @ np.nan_to_num(beta) for d in d_t])
r1 = lr.get(1, {})

fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.2))
ax = axs[0]
dd = np.geomspace(2, 14, 200)
ax.axhline(0, color=GRID, lw=1)
ax.plot(dd, [VF._s_booth_demo(x) - 1 for x in dd], color=INK2, lw=1.6, label="truth s(d/H) − 1 (Booth, f = 1)")
ok = np.isfinite(beta)
ax.errorbar(np.array(nodes)[ok], beta[ok], yerr=[beta[ok] - np.array([t[2] for t in tab])[ok], np.array([t[3] for t in tab])[ok] - beta[ok]],
            fmt="o", ms=7, color=C1, mec=SURF, mew=1.2, capsize=3, lw=1.4, label="I111 nodes (U_loc not used)", zorder=3)
if r1.get("dstar") == r1.get("dstar"):
    ax.axvline(r1["dstar"], color=C2, lw=1.2, ls="--")
    ax.text(r1["dstar"] * 1.03, -0.62, f"d* = {r1['dstar']:.2f}\n(truth 10.08)", color=C2, fontsize=8.5, va="bottom")
ax.set_xscale("log"); ax.set_xticks([2, 3, 5, 7, 10, 14]); ax.set_xticklabels(["2", "3", "5", "7", "10", "14"])
ax.set_xlabel("d/H"); ax.set_ylabel("mobility deficit λ = s − 1")
ax.set_title("(a) signed λ(d) from fluctuations alone", loc="left", fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8.2, loc="upper left")

ax = axs[1]
ax.scatter(d_t, v_t, s=12, color=MUTED, alpha=0.7, lw=0, label="track mean speed V̄_i")
ax.scatter(d_t, v_t / (1 + lam_t), s=12, color=C1, alpha=0.85, lw=0, label="V̄_i / (1 + λ̂(d_i))")
ax.axhline(U, color=INK2, lw=1.0, ls=":", label=f"true U = {U:g} px/frame (synthetic)")
if r1.get("U_loc_dstar") == r1.get("U_loc_dstar"):
    ax.plot([r1["dstar"]], [r1["U_loc_dstar"]], "D", ms=8, color=C2, mec=SURF, mew=1.2, zorder=4,
            label=f"U_loc(d*) = {r1['U_loc_dstar']:.2f} (+{r1['U_loc_dstar'] / U - 1:.1%})")
ax.set_xscale("log"); ax.set_xticks([2, 3, 5, 7, 10, 14]); ax.set_xticklabels(["2", "3", "5", "7", "10", "14"])
ax.set_xlabel("d/H"); ax.set_ylabel("speed (px/frame)")
ax.set_ylim(0, 1.25 * max(v_t.max(), U))
ax.set_title("(b) per-bubble local field: speeds collapse to U", loc="left", fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8.2, loc="upper left")

ax = axs[2]
MU, SIG, Um = 1e-3, 0.072, 0.05
for H_mm, px_mm, col, lab in ((0.3, 0.02, C1, "0.3 mm, 0.02 mm/px"), (1.0, 0.05, C2, "1 mm, 0.05 mm/px (steel, assumed)")):
    xs = np.geomspace(2, 40, 300)
    sens = []
    for x in xs:
        s = VF._s_booth_demo(x, U=Um, mu=MU, sig=SIG)
        a_px = x * (H_mm / px_mm) / 2
        sens.append(abs(1 - 1 / s) * 2 * 0.5 / a_px)
    ax.plot(xs, 100 * np.array(sens), color=col, lw=1.8, label=lab)
ax.axvspan(9, 11.5, color=GRID, alpha=0.6, lw=0)
ax.text(10.1, 2.2, "d*\n(s = 1)", color=INK2, fontsize=8.2, ha="center")
ax.set_xscale("log"); ax.set_xticks([2, 3, 5, 10, 20, 40]); ax.set_xticklabels(["2", "3", "5", "10", "20", "40"])
ax.set_xlabel("d/H (class)"); ax.set_ylabel("|δU_loc/U_loc| for 0.5 px contour error (%)")
ax.set_ylim(0, 24)
ax.set_title("(c) class U_loc vs contour convention", loc="left", fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8.2, loc="upper right")
for ax in axs:
    ax.xaxis.set_minor_formatter(NullFormatter())

fig.text(0.01, -0.06,
         "I111: lateral velocity divided by each bubble's own mean speed, regressed on unit dipole fields of a continuous λ(d) basis "
         "(frame and position-cell fixed effects removed identically from velocity and fields; independent review 10). "
         "Synthetic: λ nodes within ±0.008, class U_loc +0.6% and +1.5% (old tool −19% and −9.5%). "
         "Regression returns λ·(a_eff/a)², so class U_loc inherits |1 − 1/s| × area error (c); "
         "U_loc read at d* (λ = 0) does not. Prediction and synthetic test only — no measured data.",
         fontsize=7.6, color=MUTED, wrap=True)
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r22_i111_regression.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("saved", {k: round(v, 4) if isinstance(v, float) else v for k, v in r1.items() if k.startswith(("dstar", "U_loc"))})

"""이동도 붕괴(I91)의 수치 확인, 그림 r15.

I82 원판 계산(전도 원판 = 국소장의 s배로 움직이는 원)에서 원판 속도 V = j_G/α를 두 가지로 정규화한다.
- 드리프트 플럭스 꼴 V/J(J = j_L + j_G): 기공률에 따라 퍼질 것.
- 2차원 Lorentz 국소장 꼴 s* = 2V/(U_P + J)(U_P = 압력이 말하는 Darcy 속도 = K·G = 1): 고유 이동도 s 하나에 모일 것.
배치 보정은 s*·(1 − λQ)(λ = s − 1, Q = 그 배치의 배치 계수, I74).
자료: data/i82_sweep.json, data/i82_layout_q.json.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = "/home/user/bubbles/docs/research/fig"
S = {"0.41": "#2a78d6", "0.8": "#1baf7a", "1.57": "#eb6834"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

d = json.load(open(f"{HERE}/data/i82_sweep.json"))
qmap = json.load(open(f"{HERE}/data/i82_layout_q.json"))
NOM = (0.05, 0.1, 0.2, 0.3, 0.4)
rows = []
for k, r in enumerate(d["runs"]):
    a, E, B, s = r["alpha"], r["E"], r["B"], r["s"]
    jl = 1 / (1 + E)
    jg = B * jl
    J = jl + jg
    V = jg / a
    q = qmap[f"{NOM[k // 6]:g}_{1 + k % 2}"][0]
    rows.append((f"{s:g}", a, V / J, 2 * V / (1 + J), 2 * V / (1 + J) * (1 - (s - 1) * q)))

fig, ax = plt.subplots(figsize=(7.0, 4.6))
for s, col in S.items():
    pts = sorted((r for r in rows if r[0] == s), key=lambda r: r[1])
    a = np.array([p[1] for p in pts])
    vj = np.array([p[2] for p in pts]); ss = np.array([p[3] for p in pts]); sl = np.array([p[4] for p in pts])
    ax.plot(a, vj, "o", ms=6, mfc="none", mec=col, mew=1.3, zorder=3)
    ax.plot(a, sl, "o", ms=6.5, color=col, mec=SURF, mew=1.2, zorder=4, label=f"s = {s}")
    am = sorted(set(round(x, 2) for x in a))
    ax.plot(am, [np.mean([v for x, v in zip(a, vj) if round(x, 2) == m]) for m in am], color=col, lw=1.0, ls="--", zorder=2)
    ax.plot(am, [np.mean([v for x, v in zip(a, sl) if round(x, 2) == m]) for m in am], color=col, lw=1.6, zorder=2)
ax.plot([], [], "o", ms=6, mfc="none", mec=INK2, mew=1.3, label="V/J (drift-flux normalisation)")
ax.plot([], [], "o", ms=6.5, color=INK2, mec=SURF, label="2V/(U_P + J), layout-corrected (I91)")
ax.set_xlabel("void fraction α")
ax.set_ylabel("normalised bubble (disc) speed")
ax.set_xlim(0, 0.43); ax.set_ylim(0.2, 1.8)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.6, loc="lower left", ncol=2)
ax.set_title("Dividing by the mean of the pressure-implied Darcy velocity and the total flux keeps each\n"
             "mobility constant from α = 0.05 to 0.4; dividing by the total flux does not (random discs)",
             fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.06, "Same random-disc computations as figure r13 (conducting discs ε = s/(2 − s), 512² periodic grid, two layouts per α). "
         "V = j_G/α, U_P = K·ΔP/L, J = j_L + j_G.\nThe 2–5% offset from the nominal s at small α is the single-disc grid constant. "
         "Layout correction: multiply by (1 − λQ), λ = s − 1. Numerical check only — no data.",
         fontsize=7.0, color=MUTED)
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r15_mobility_collapse.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for s in S:
    pts = [r for r in rows if r[0] == s]
    vj = [p[2] for p in pts]; sl = [p[4] for p in pts]
    print(f"s {s}: V/J {min(vj):.3f}~{max(vj):.3f} (폭 {max(vj) / min(vj) - 1:.1%}), s* 배치 보정 {min(sl):.4f}~{max(sl):.4f} (폭 {max(sl) / min(sl) - 1:.1%})")

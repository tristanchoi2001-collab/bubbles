"""I82 수치 실험: 주기 상자 속 무작위(겹치지 않는) 원판 무리의 2차원 Darcy 흐름으로 평균장 폐합이 어느 α까지 맞는지.

- 국소장의 s배로 움직이는 원 = 전도도 ε = s/(2 − s)인 원판(쌍극자 수준에서 같음, 독립 검토 3).
- 풀이: 512 × 512 주기 격자, 원판 반지름 14화소(화소 4 × 4 표본으로 덮임 비율), 면 전도도 조화 평균, 행렬 없는 CG.
  원판 안 플럭스 = 기체 유량 j_G, 나머지 = 액체 j_L. E = G/j_L − 1, B = j_G/j_L(G = K = 1).
- 격자 오차(1/R에 비례, R 14에서 원판 하나 2~6%)를 지우려고 같은 반지름의 원판 하나로 유효 C(= (y − 1)/x)를 먼저 정하고,
  폐합 E_cl = [α(1 + C) − C·B(1 − α)]/(1 − α)를 그 C로 계산한다. 남는 차 E − E_cl이 여러 기포의 몫이다.
- 배치 보정(I74): 배치마다 Q(원 합, 주기 상)를 구해 ΔE = [2λQ/(1 − α − λQ)]·α/(1 − α), λ = s − 1을 뺀다.
- 자료: data/i82_sweep.json(최소 간격 1 px), data/i82_layout_q.json(같은 배치의 Q), data/i82_gap4.json(최소 간격 4 px, 있으면).
  계산 도구: tools/darcy_disks.py(--sweep이 Q까지 기록).
"""
import json
import os
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
gap4 = json.load(open(f"{HERE}/data/i82_gap4.json")) if os.path.exists(f"{HERE}/data/i82_gap4.json") else []
NOM = (0.05, 0.1, 0.2, 0.3, 0.4)


def closure(a, B, C):
    return (a * (1 + C) - C * B * (1 - a)) / (1 - a)


def layout(a, lam, q):
    return 2 * lam * q / (1 - a - lam * q) * a / (1 - a)


rows = []
for k, r in enumerate(d["runs"]):
    s = f"{r['s']:g}"
    C = d["calib"][s]["C_eff"]
    a, E, B = r["alpha"], r["E"], r["B"]
    q = qmap[f"{NOM[k // 6]:g}_{1 + k % 2}"][0]
    E_cl = closure(a, B, C)
    rows.append(dict(s=s, a=a, E=E, E_cl=E_cl, raw=E - E_cl, lay=layout(a, r["s"] - 1, q), q=q))
for r in rows:
    r["after"] = r["raw"] - r["lay"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.4))
for s, col in S.items():
    pts = sorted((r for r in rows if r["s"] == s), key=lambda r: r["a"])
    if not pts:
        continue
    a = np.array([r["a"] for r in pts])
    lab = f"s = {s} (λ = {float(s) - 1:+.2f})"
    ax1.plot([r["E_cl"] for r in pts], [r["E"] for r in pts], "o", ms=6.5, mfc="none", mec=col, mew=1.4, zorder=3)
    ax1.plot([r["E_cl"] + r["lay"] for r in pts], [r["E"] for r in pts], "o", ms=6.5, color=col, mec=SURF, mew=1.2,
             zorder=4, label=lab)
    ax2.plot(a, [r["raw"] for r in pts], "o", ms=6, mfc="none", mec=col, mew=1.3, zorder=3)
    ax2.plot(a, [r["after"] for r in pts], "o", ms=6.5, color=col, mec=SURF, mew=1.2, zorder=4, label=lab)
    am = sorted(set(round(x, 2) for x in a))
    mean_after = [np.mean([r["after"] for r in pts if round(r["a"], 2) == x]) for x in am]
    ax2.plot(am, mean_after, color=col, lw=1.6, zorder=2)
    g = sorted((r for r in gap4 if f"{r['s']:g}" == s), key=lambda r: r["alpha"])
    if g:
        ax2.plot([r["alpha"] + 0.008 for r in g], [r["after"] for r in g], "D", ms=5, color=col, mec=INK2, mew=0.8, zorder=5)
lim = max(max(r["E"] for r in rows), max(r["E_cl"] + r["lay"] for r in rows)) * 1.06
ax1.plot([0, lim], [0, lim], color=MUTED, lw=1, zorder=1)
ax1.set_xlim(0, lim); ax1.set_ylim(0, lim)
ax1.set_xlabel("closure E (single-disc C, measured α and B)")
ax1.set_ylabel("computed E (random hard discs)")
ax1.grid(color=GRID, lw=0.8); ax1.set_axisbelow(True)
ax1.plot([], [], "o", ms=6.5, mfc="none", mec=INK2, mew=1.3, label="closure alone")
ax1.plot([], [], "o", ms=6.5, color=INK2, mec=SURF, label="closure + layout term (I74)")
ax1.legend(frameon=False, fontsize=7.6, loc="upper left")
ax1.set_title("Computed vs predicted E", fontsize=9.5, color=INK, loc="left")

ax2.axhspan(-0.02, 0.02, color=GRID, lw=0, zorder=0)
ax2.axhline(0, color=MUTED, lw=0.8, zorder=1)
ax2.text(0.215, -0.016, "±0.02: E resolution at 0.3 mm", color=INK2, fontsize=7.4, va="center")
ax2.set_xlabel("void fraction α")
ax2.set_ylabel("E − prediction")
ax2.grid(color=GRID, lw=0.8); ax2.set_axisbelow(True)
ax2.plot([], [], "o", ms=6, mfc="none", mec=INK2, mew=1.3, label="closure alone (each layout)")
ax2.plot([], [], "o", ms=6.5, color=INK2, mec=SURF, label="after layout term; line = mean")
if gap4:
    ax2.plot([], [], "D", ms=5, color=INK2, mec=INK2, label="after layout term, min gap 4 px (shifted right)")
ax2.legend(frameon=False, fontsize=7.3, loc="upper left")
ax2.set_xlim(0, 0.43)
ax2.set_title("Residual vs void fraction", fontsize=9.5, color=INK, loc="left")
fig.suptitle("How far the closure holds for random pancakes: the layout term removes the scatter between layouts;\n"
             "a smooth positive residual remains above α ≈ 0.2 (2D Darcy, moving discs = conductive discs)",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.text(0.01, -0.07, "512 × 512 periodic grid, disc radius 14 px, random sequential addition, two layouts per α (the same layouts for every s). "
         "Grid error removed by calibrating C on one disc of the same radius.\nQ from each layout (circle sum with periodic images). "
         "Dipole-level equivalence of a disc moving at s times the local flow and a disc of conductivity s/(2 − s);\nreal pancakes also have films and menisci. "
         "Numerical check only — no data.", fontsize=7.2, color=MUTED)
fig.tight_layout()
fig.savefig(f"{HERE}/fig_r13_closure_alpha_limit.png", dpi=170, bbox_inches="tight")
plt.close(fig)
for r in sorted(rows, key=lambda r: (r["s"], r["a"])):
    print(f"s {r['s']:>5} α {r['a']:.3f} E {r['E']:.4f} E_cl {r['E_cl']:.4f} raw {r['raw']:+.4f} Q {r['q']:+.4f} layout {r['lay']:+.4f} after {r['after']:+.4f}")

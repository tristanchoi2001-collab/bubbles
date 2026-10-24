"""공기 주입 가열의 예상 h_TP/h_1φ: 열적 유효 매질(I7) + 발자국 열관 항(I29). 모양만 보이는 그림.

h_TP/h_1φ ≈ (1 − φ_c)·max[1, 0.42·Fo^(−1/2)] + φ_c·r_b(T)
- Fo = α_th·T_l/H², T_l = 액체가 한 점을 덮는 시간(≈ (1 − φ_c)/f). 0.42 = (2/√π)/2.69(한쪽 가열 평행판 Nu 5.385, D_h = 2H).
- r_b = h_b/h_1φ. 기포 속 수증기 열관 h_b와 h_1φ가 둘 다 1/H에 비례하므로 갭과 무관하고 온도로만 정해진다.
  1 mm 열관 0.31/0.89/4.0 kW/m²K(50/70/90 °C, 아이디어 점검 2, Stefan 흐름 포함 자릿수), h_1φ(1 mm) ≈ 1.62 kW/m²K
  → r_b ≈ 0.19/0.55/2.5. 마른 공기의 순 잠열 수송(I29)과 후류 혼합은 넣지 않았다.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAMP = {50: "#86b6ef", 70: "#2a78d6", 90: "#104281"}
REF = "#8a8986"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})

PHI_C = 0.3
H1PHI_1MM = 5.385 * 0.6 / 2e-3 / 1e3     # kW/m²K
HP_1MM = {50: 0.31, 70: 0.89, 90: 4.0}   # kW/m²K
RB = {t: v / H1PHI_1MM for t, v in HP_1MM.items()}

x = np.logspace(-0.55, np.log10(12), 200)          # Fo^(−1/2)
liquid = (1 - PHI_C) * np.maximum(1.0, 0.42 * x)

fig, ax = plt.subplots(figsize=(7.4, 4.5))
ax.plot(x, liquid, color=REF, lw=1.6, ls=(0, (5, 3)), label="footprint adiabatic (I7)")
for t, col in RAMP.items():
    y = liquid + PHI_C * RB[t]
    ax.plot(x, y, color=col, lw=2, label=f"wall {t} °C (r_b = {RB[t]:.2f})")
    dy = {50: -0.06, 70: 0.06, 90: 0.0}[t]
    ax.text(x[0] * 0.93, y[0] + dy, f"{t} °C", color=INK2, fontsize=8, ha="right", va="center")
ax.axhline(1, color=INK2, lw=1)
ax.text(x[-1], 1.03, "single phase", color=INK2, fontsize=8, ha="right", va="bottom")
ax.set_xscale("log")
ax.set_xlim(0.2, 13); ax.set_ylim(0.5, 4.6)
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("renewal number  Fo^(−1/2) = H / √(α T_l)   (larger = more frequent bubble passage)")
ax.set_ylabel("h_TP / h_1φ   (contact fraction φ_c = 0.3)")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.set_title("Expected effect of air injection on heat transfer: loss at low passage frequency and 50 °C,\n"
             "gain when passage is frequent or when vapour diffusion makes footprints conduct (≈ 80 °C and above)",
             fontsize=10, color=INK, loc="left")
fig.text(0.01, -0.09,
         "Model: (1 − φ_c)·max[1, 0.42·Fo^(−1/2)] + φ_c·r_b, r_b = h_b/h_1φ from the in-bubble vapour 'heat pipe' (gap-independent: both scale as 1/H).\n"
         "Fo^(−1/2) = 1, 3, 10 corresponds to passage frequency f ≈ 1, 10, 110 Hz at 0.3 mm and 0.1, 0.9, 10 Hz at 1 mm (φ_c 0.3).\n"
         "Not included: net latent transport by dry air, wake mixing, thermal entry effects. Order-of-magnitude heat-pipe values; shapes only.",
         fontsize=7.2, color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r8_thermal_em.png", dpi=170, bbox_inches="tight")
plt.close(fig)
cross = {t: (1 - PHI_C) + PHI_C * RB[t] for t in RB}
print("r_b", {t: round(v, 2) for t, v in RB.items()}, "low-frequency limit", {t: round(v, 2) for t, v in cross.items()})

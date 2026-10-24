"""철 바닥 발자국의 건조 경계, 그림 r21 (I112). 예상, 실측 없음.

(크기 d, 속도 V) 평면에서 네 후보의 경계 모양. 1 mm·물 20 °C.
(a) 단열: 거칠기 뚫음 V_c(Rz)(세로선, H^(−3/2)), 강제 풀림 V*(θ_r)(세로 띠, ln 10~15, H 무관),
    늦은 터짐 d_w ∝ V^(1.7~2)(앞계수 모름: V 0.05 m/s에서 20 mm를 지나게 둔 기울기 띠).
(b) 가열: 증발 d_ev = h_f(V)·ρh_fg·V/q_ev ∝ V^(5/3)/q(에너지 한계, 공기 기포는 확산 제한이라 더 늦게 마름). 단열 경계는 회색.
검토 11 반영(2026-10-24): 모양과 기구는 일대일이 아니다. (a)에 옆 막(Burgess & Foster 1990, H(H/d)^(2/5)Ca^(4/5))의 거칠기 뚫음
d ∝ V²(Rz 5 µm, d/H 10에서 V 0.13~0.72 m/s, 앞계수 0.5~2, 추정)을 더하고, 한 시야(19 mm)·채널 반폭으로 보기 어려운 d > 13 mm를
회색으로 칠했다(늦은 터짐의 큰 쪽 교차는 34~350 mm). (b)의 d_ev는 20 °C의 μ·σ와 100 °C의 h_fg를 섞은 값이고, 포화 물성이면 약 0.47배다.
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
MU, SIG, RHO, HFG, H = 1e-3, 0.072, 1000.0, 2.26e6, 1e-3
V = np.logspace(np.log10(0.005), np.log10(0.5), 300)
hf = 0.669 * H * (MU * V / SIG) ** (2 / 3)
Vr, dr = 0.05, 20.0


def vc(Rz):
    return (SIG / MU) * (Rz / (0.67 * H)) ** 1.5


def vstar(th):
    t = math.radians(th)
    return (SIG / MU) * t ** 3 / (9 * 15), (SIG / MU) * t ** 3 / (9 * 10)


def frame(ax):
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.005, 0.5); ax.set_ylim(1, 400)
    ax.set_xlabel("bubble speed V (m/s)")
    ax.grid(color=GRID, lw=0.8, which="major"); ax.set_axisbelow(True)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.4), sharey=True)
# (a) 단열
for Rz, ls in ((2e-6, ":"), (5e-6, "--"), (10e-6, "-")):
    ax1.axvline(vc(Rz), color=C2, lw=1.6, ls=ls, zorder=2)
    ax1.text(vc(Rz) * 1.05, 1.12, f"V_c, Rz {Rz * 1e6:.0f} µm", color=C2, fontsize=7.4, rotation=90, ha="left", va="bottom")
for th in (20, 30, 45):
    lo, hi = vstar(th)
    ax1.axvspan(lo, hi, color=C3, alpha=0.20, lw=0, zorder=1)
    ax1.text(math.sqrt(lo * hi), 1.12, f"V*, θ_r {th}°", color=C3, fontsize=7.4, rotation=90, ha="center", va="bottom")
d_lo, d_hi = dr * (V / Vr) ** 1.7, dr * (V / Vr) ** 2.0
ax1.fill_between(V, np.minimum(d_lo, d_hi), np.maximum(d_lo, d_hi), color=C1, alpha=0.22, lw=0, zorder=1)
ax1.plot(V, dr * (V / Vr) ** 1.85, color=C1, lw=1.6, zorder=3)
ax1.text(0.0056, 300, "late rupture at the thin side ravines:\ndry above the blue band, d_w ∝ V^(1.7–2)\n(prefactor unknown, wettability ×10)",
         color=C1, fontsize=7.6, ha="left", va="top")
# 옆 막(Burgess & Foster 1990)의 거칠기 뚫음: Ca_c ∝ (Rz/H)^(5/4)(d/H)^(1/2) → d = 10 mm·(V/V_ref)², V_ref 0.13~0.72 m/s(Rz 5 µm)
s_lo, s_hi = 10.0 * (V / 0.72) ** 2, 10.0 * (V / 0.13) ** 2
ax1.fill_between(V, s_lo, s_hi, facecolor="none", edgecolor=C2, hatch="////", lw=0, alpha=0.55, zorder=1)
ax1.plot(V, 10.0 * (V / 0.3) ** 2, color=C2, lw=1.1, ls="-.", zorder=2)
ax1.text(0.33, 2.6, "Rz 5 µm, side film:\nsides dry above,\nd ∝ V² (hatched:\nprefactor 0.5–2)", color=C2, fontsize=7.0, ha="left", va="bottom")
ax1.text(0.0056, 45, "left of a vertical line:\ndry at every size", color=INK2, fontsize=7.6, ha="left", va="center",
         bbox=dict(facecolor=SURF, edgecolor="none", pad=1.5), zorder=4)
ax1.text(0.19, 2.2, "wet film", color=INK2, fontsize=8.4, ha="center", va="bottom")
# 운전점의 기포들: 젖은 막 Booth 곡선 V(d) = U·s(1.12·(d/H)·Ca_U^(1/3)), f = 1. 경계와 두 번 만나면 가운데 크기만 젖는다.
ld = np.linspace(np.log(1e-5), np.log(1e5), 4001)
dl = np.exp(ld); lo_, hi_ = np.full_like(dl, 1e-12), np.full_like(dl, 2 - 1e-12)
for _ in range(90):
    mid = 0.5 * (lo_ + hi_); big = mid ** (2 / 3) / (2 - mid) > dl
    hi_ = np.where(big, mid, hi_); lo_ = np.where(big, lo_, mid)
st = 0.5 * (lo_ + hi_)
dd = np.logspace(0, np.log10(400), 200)                   # mm
for U, yl in ((0.02, 300), (0.05, 300), (0.12, 300)):
    sv = np.interp(np.log(1.12 * (dd / (H * 1e3)) * (MU * U / SIG) ** (1 / 3)), ld, st)
    ax1.plot(U * sv, dd, color=INK2, lw=0.9, ls="-", alpha=0.75, zorder=2)
    k = int(np.argmin(np.abs(dd - 160)))
    ax1.text(U * sv[k] * 1.04, 160, f"run U {U:g}", color=INK2, fontsize=7.0, ha="left", va="center")
for ax_ in (ax1, ax2):
    ax_.axhspan(13.3, 400, color=GRID, alpha=0.55, lw=0, zorder=0)
ax1.text(0.0056, 16, "d > 13 mm: beyond 0.7 × field of view (19 mm) / half width,\nmerges with width-filling (I95) — kinks not read here",
         color=MUTED, fontsize=7.0, ha="left", va="bottom")
frame(ax1)
ax1.set_ylabel("footprint length d (mm)")
ax1.set_title("(a) Adiabatic: roughness, forced dewetting, late rupture", fontsize=9.5, color=INK, loc="left")
# (b) 가열
ax2.axvline(vc(5e-6), color=MUTED, lw=1.2, ls="--", zorder=1)
lo, hi = vstar(30)
ax2.axvspan(lo, hi, color=MUTED, alpha=0.12, lw=0, zorder=0)
ax2.plot(V, dr * (V / Vr) ** 1.85, color=MUTED, lw=1.2, zorder=1)
ax2.text(vc(5e-6) * 1.05, 1.12, "adiabatic: V_c 5 µm, V* 30°, late rupture", color=MUTED, fontsize=7.2, rotation=90, ha="left", va="bottom")
for q, ls in ((1e4, "-"), (3e4, "--"), (1e5, ":")):
    dev = hf * RHO * HFG * V / q * 1e3
    ax2.plot(V, dev, color=C4, lw=2.0, ls=ls, zorder=3)
    y0 = {1e4: 12.0, 3e4: 30.0, 1e5: 80.0}[q]
    k = int(np.argmin(np.abs(dev - y0)))
    ax2.text(V[k] * 0.86, y0, f"{q / 1e4:g} W/cm²", color=C4, fontsize=8.0, ha="right", va="center")
ax2.text(0.0056, 300, "evaporation uses up the film during d/V:\ndry above each line, d_ev ∝ V^(5/3)/q\n(20 °C μ, σ with h_fg at 100 °C; saturated properties ×0.47.\nAir bubbles: vapour-diffusion limited, set by wall temperature)",
         color=C4, fontsize=7.6, ha="left", va="top")
frame(ax2)
ax2.set_title("(b) Heated: the evaporation boundary moves as 1/q", fontsize=9.5, color=INK, loc="left")
fig.suptitle("Where steel footprints should dry: candidate boundaries in the (size, speed) plane (1 mm, water; expected, I112, review 11)",
             fontsize=10, color=INK, x=0.01, ha="left")
fig.text(0.01, -0.02,
         "Film 0.669·H·Ca^(2/3). Roughness: film thinner than Rz, V_c ∝ H^(−3/2). Forced dewetting: V* ≈ (σ/μ)θ_r³/(9 ln(ℓ/λ)), independent of H (Snoeijer 2006). "
         "Late rupture: L_w ∝ Ca^(1.7–2) (Khodaparast 2018, microchannels).\n"
         "Grey: one run's bubbles lie on its Booth curve, which can cross a sloped boundary twice (slow small and long large bubbles dry, a wet window between).\n"
         "Read the boundary from significant mobility kinks at ≥ 5 flow rates (tools/mobility_kink.py, U_loc = j_L/(1 − α)). Shape narrows the candidates only: side-film roughness is also sloped (d ∝ V²), "
         "speed-dependent contamination gives near-vertical kinks without drying,\nand a 3% low U_loc gives false small-side kinks. A dry verdict needs a non-kinematic signal (brightness, top-view dry patch). "
         "Heating also shifts late rupture 2–3× through μ(T), σ(T) → plot against Ca at film temperature.",
         fontsize=7.0, color=MUTED, va="top")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(f"{HERE}/fig_r21_dry_boundary.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("saved")

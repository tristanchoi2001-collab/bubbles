"""속도 중심 판독 지도, 그림 r19. 어떤 판독이 무엇을 주고 무엇이 필요한지(velocity_links.md 2·3절의 그림판).

행 = 판독(아이디어), 열 = 주는 양(●)과 필요한 것(■). 마지막 열은 도구.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = "/home/user/bubbles/docs/research/fig"
C1, C2 = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.0, "figure.facecolor": SURF, "savefig.facecolor": SURF})

gives = ["λ = s − 1", "friction factor f", "friction exponent m", "local field U_loc", "void fraction α", "gap map / tilt", "liquid ∇T",
         "pressure drop E", "wet / dry footprint"]
needs = ["ΔP taps", "U_loc", "new runs", "contour masks"]
rows = [  # (label, gives set, needs set, tool)
    ("I89–I91 force balance, mobility collapse", {0, 1, 2, 7}, {0}, "plane_from_csv.py"),
    ("I99 fluctuation width |λ|", {0}, set(), "velocity_fluctuations.py"),
    ("I100 streamwise/lateral response ratio", {2, 8}, {1}, "velocity_fluctuations.py --regress"),
    ("I101 side-wall speed change", {0}, set(), "plane_from_csv.py (s_starW)"),
    ("I102 lateral tilt deflection", {3}, {2}, "—"),
    ("I104 invisible size d* (s = 1)", {1, 2}, {1}, "plane_from_csv.py tables"),
    ("I105 capillary-potential drift", {5, 6}, {1}, "drift_map.py"),
    ("I106 tilt along vs across", {2}, {1, 2}, "—"),
    ("I107 relaxation after merging", {1, 2, 8}, {3}, "merge_relax.py"),
    ("I108 two-view flow difference vs pressure", {4}, {0, 2}, "—"),
    ("I109 steady flattening", {1, 2, 8}, {3}, "shape_flatten.py"),
    ("I110 void-wave speed vs bubble speed", {0, 2}, set(), "void_waves.py"),
    ("I111 regression on unit dipole fields", {0, 2, 3, 8}, set(), "velocity_fluctuations.py"),
    ("I112 drying boundary from mobility kinks", {8}, {1}, "mobility_kink.py"),
    ("I113 pressure drop without taps", {7}, set(), "(from I111 output)"),
    ("I114 stick–slip intermittency", {8}, set(), "mobility_kink.py"),
]
ncol = len(gives) + len(needs)
fig, ax = plt.subplots(figsize=(12.6, 7.0))
x0_label, x_cols, x_tool = 0.0, 4.6, 4.6 + 0.62 * ncol + 0.25
for i, (lab, gv, nd, tool) in enumerate(rows):
    y = len(rows) - 1 - i
    if i % 2 == 0:
        ax.add_patch(plt.Rectangle((-0.1, y - 0.5), x_tool + 4.3, 1.0, color=GRID, alpha=0.45, lw=0, zorder=0))
    ax.text(x0_label, y, lab, va="center", ha="left", fontsize=8.6, color=INK)
    for j in range(len(gives)):
        if j in gv:
            ax.plot(x_cols + 0.62 * j, y, "o", ms=10, color=C1, mec=SURF, mew=1.5, zorder=3)
    for j in range(len(needs)):
        if j in nd:
            ax.plot(x_cols + 0.62 * (len(gives) + j), y, "s", ms=9, color=C2, mec=SURF, mew=1.5, zorder=3)
    ax.text(x_tool, y, tool, va="center", ha="left", fontsize=7.8, color=INK2, family="DejaVu Sans Mono")
ytop = len(rows) - 0.4
for j, g in enumerate(gives):
    ax.text(x_cols + 0.62 * j, ytop, g, rotation=55, ha="left", va="bottom", fontsize=8.0, color=INK)
for j, n in enumerate(needs):
    ax.text(x_cols + 0.62 * (len(gives) + j), ytop, n, rotation=55, ha="left", va="bottom", fontsize=8.0, color=INK2)
ax.text(x_tool, ytop, "tool", rotation=55, ha="left", va="bottom", fontsize=8.0, color=INK2)
ax.axvline(x_cols + 0.62 * (len(gives) - 0.5), color=MUTED, lw=0.8, ymin=0.02, ymax=0.8)
ax.set_xlim(-0.1, x_tool + 4.3); ax.set_ylim(-0.6, len(rows) + 3.6)
ax.axis("off")
ax.plot([], [], "o", ms=9, color=C1, label="gives")
ax.plot([], [], "s", ms=8, color=C2, label="needs (beyond tracking + flowmeters)")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=8.2, ncol=2)
ax.set_title("What each tracked-velocity readout gives and what it needs (velocity-first program, I89–I114)",
             fontsize=10, color=INK, loc="left", pad=2)
fig.text(0.01, 0.01, "U_loc can come from ΔP + flow rates ((U_P + J)/2), from imaged α and flowmeters (j_L/(1 − α), mean-field closure) or from a lateral tilt (I102). "
         "Readouts that need neither pressure nor U_loc: I99, I101 (sign of λ), I107, I109, I110 (signed λ), I111 (signed λ and U_loc = V̄/(1 + λ) itself), I113 (E from I111), I114.\n"
         "f is read five ways and m eight ways; agreement between them is the main test (velocity_links.md section 3). I110: pattern speed needs no track IDs, "
         "the reference V̄ does; current fields of view reach only small bubbles at 0.3 mm.\n"
         "Independent reviews 6–9 corrected I90–I110 (review 9: I108 recast as a two-view local mass balance; liquid inertia dominates the single-point phase).",
         fontsize=7.2, color=MUTED, va="bottom")
fig.savefig(f"{HERE}/fig_r19_readout_map.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("saved")

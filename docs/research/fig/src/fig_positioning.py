"""선행 다중 갭 연구의 H/Lc 범위 비교 (lit_7_closest_novelty.md 1-2표의 Co 범위를 1/Co로 바꿈. Gasanov 2026은 lit_2 #1)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
S1,S2,GRAY="#2a78d6","#eb6834","#9b9a96"
INK,INK2,MUTED,GRID,SURF="#0b0b0b","#52514e","#8a8986","#e6e5e1","#fcfcfb"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9.5,"axes.edgecolor":MUTED,"axes.labelcolor":INK2,
    "xtick.color":INK2,"ytick.color":INK2,"figure.facecolor":SURF,"axes.facecolor":SURF,"savefig.facecolor":SURF,
    "axes.spines.top":False,"axes.spines.right":False})
# (label, kind, Co_max, Co_min) ; kind: ours / forced / pool
rows=[("This study (water, 0.3/0.7/1/3/7 mm)","ours",9.1,0.39),
("Gasanov 2026 (water boiling, 0.3/0.6/3 mm)","forced",9.1,0.91),
("Xu 1999 (air-water, vertical, 0.3-1 mm)","forced",9.1,2.7),
("Lee & Lee 2001a (air-water, horiz., 0.4-4 mm)","forced",6.8,0.68),
("Zhu 2023 (water boiling, 0.5-2 mm)","forced",5.0,1.25),
("Shinmoto 2017 (water, horiz. bottom-heated, 0.5-2 mm)","forced",5.0,1.25),
("Mishima 1993 (air-water, vertical, 1-5 mm)","forced",2.7,0.55),
("Lee & Lee 2001b (R113 boiling, horiz., 0.4-2 mm)","forced",2.5,0.5),
("Omisanya 2024 (water boiling, 1-5 mm)","forced",2.5,0.5),
("Lee J 2013 (vertical down, 2.5-4.1 mm)","forced",1.0,0.61),
("Albahloul 2015 (air-Novec, horiz., 1.3-1.5 mm)","forced",0.64,0.56),
("He 2022 (air-water, vertical, 4-10 mm)","forced",0.68,0.27),
("Willingham 1992 (FC-72 boiling, 2-10 mm)","forced",0.36,0.073),
("Alam 2012 (water boiling, 0.08-1 mm)","forced",31,2.5),
("Chinnov 2016 (gas-liquid, horiz., 0.1-0.5 mm)","forced",27,5.5),
("Cardoso 2011 (pool, FC72/87)","pool",7.3,0.056),
("Fujita 1988 (pool, water)","pool",16.7,0.50),
("Kim YH 2005 (pool, water, inclined)","pool",2.5,0.25),
("Bonjour 1998 (pool, R-113, vertical)","pool",2.0,0.5),
("Klugmann 2019 (thermosyphon)","pool",2.5,0.83)]
fig,ax=plt.subplots(figsize=(8.6,6.4))
n=len(rows)
for i,(lab,kind,cmax,cmin) in enumerate(rows):
    y=n-1-i
    lo,hi=1/cmax,1/cmin
    col={"ours":S2,"forced":S1,"pool":GRAY}[kind]
    ax.plot([lo,hi],[y,y],color=col,lw=6 if kind=="ours" else 4,solid_capstyle="round")
    if kind=="ours":
        for H in (0.3,0.7,1,3,7):
            ax.plot(H/2.73,y,"o",ms=7,mfc=col,mec=SURF,mew=2)
for x,t in ((1,"H = Lc"),(2,"H = 2Lc (horizontal: a top-wall puddle no longer touches the bottom)")):
    ax.axvline(x,color=INK2,lw=1)
    ax.text(x*1.04,5.5,t,fontsize=8,color=INK2,va="center")
ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in rows][::-1],fontsize=8.3)
ax.set_xscale("log"); ax.set_xlim(0.025,25); ax.set_ylim(-0.8,n-0.2)
ax.set_xlabel("H / Lc  (fluid-specific capillary length; Co = Lc/H)")
ax.grid(axis="x",color=GRID,lw=0.8); ax.set_axisbelow(True)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([0],[0],color=S2,lw=6,label="this study"),Line2D([0],[0],color=S1,lw=4,label="forced flow"),
                   Line2D([0],[0],color=GRAY,lw=4,label="pool / thermosyphon")],frameon=False,fontsize=8.5,loc="lower right")
ax.set_title("Gap range of multi-gap studies: only this set crosses both H = Lc and H = 2Lc in forced flow",fontsize=10,color=INK,loc="left")
fig.text(0.01,0.005,"Source: docs/research/lit_7_closest_novelty.md table 1-2 (Co ranges from each paper; Lc of each fluid), lit_2 #1 for Gasanov 2026. The 2Lc argument applies to horizontal channels only.",fontsize=7,color=MUTED)
fig.savefig("/home/user/bubbles/docs/research/fig/fig_r4_gap_range_positioning.png",dpi=170,bbox_inches="tight"); plt.close(fig)
print("ok")

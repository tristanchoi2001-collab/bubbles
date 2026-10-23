import math, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
OUT="/home/user/bubbles/docs/research/fig/"
S1,S2,S3,S4,S5="#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4"   # validated categorical slots 1-5 (adjacent pairs)
INK,INK2,MUTED,GRID,SURF="#0b0b0b","#52514e","#8a8986","#e6e5e1","#fcfcfb"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.edgecolor":MUTED,"axes.labelcolor":INK2,
    "xtick.color":INK2,"ytick.color":INK2,"axes.titlecolor":INK,"figure.facecolor":SURF,"axes.facecolor":SURF,
    "savefig.facecolor":SURF,"axes.grid":True,"grid.color":GRID,"grid.linewidth":0.8,"grid.linestyle":"-",
    "axes.spines.top":False,"axes.spines.right":False})

# ---------- Fig 1: regimes in a horizontal channel heated from below ----------
fig,axs=plt.subplots(1,3,figsize=(13.5,4.6),gridspec_kw={"wspace":0.06})
steel="#b9bcc2"; cover="#d6e4f5"; liquid=(42/255,120/255,214/255,0.08); edge=INK2
Lc=2.73
info={1:"H < Lc (0.3, 0.7, 1 mm; drawn: 1 mm):\nevery bubble wider than ~H spans the gap;\nthin film 1.5-30 um on the heated wall",
      3:"Lc < H < 2Lc: small bubbles float under the cover;\nlarge bubbles span the gap and touch the heated wall",
      7:"H > 2Lc: even large bubbles stay under the cover as\npuddles; a liquid layer (>= 1.5 mm) covers the heated wall"}
for ax,H in zip(axs,(1,3,7)):
    W=24
    ax.add_patch(Rectangle((0,-1.0),W,1.0,color=steel,lw=0))
    ax.add_patch(Rectangle((0,H),W,0.45,color=cover,lw=0))
    ax.add_patch(Rectangle((0,0),W,H,color=liquid,lw=0))
    ax.text(0.4,-0.55,"heated steel",fontsize=8.5,color=INK2,va="center")
    ax.text(0.4,H+0.85,"transparent cover",fontsize=8.5,color=INK2,va="center")
    f=0.06  # film drawn exaggerated
    if H==1:
        ax.add_patch(FancyBboxPatch((5,f),14,H-2*f,boxstyle=f"round,pad=0,rounding_size={(H-2*f)/2}",fc="white",ec=edge,lw=1.5))
        ax.annotate("pancake (touches both walls)",xy=(12,0.75),xytext=(13,3.0),fontsize=9,color=INK,ha="center",va="center",arrowprops=dict(arrowstyle="-",color=INK2,lw=0.8))
    if H==3:
        ax.add_patch(Circle((4.5,H-0.95-f),0.95,fc="white",ec=edge,lw=1.5))
        ax.add_patch(FancyBboxPatch((9,f),11,H-2*f,boxstyle=f"round,pad=0,rounding_size={(H-2*f)/2}",fc="white",ec=edge,lw=1.5))
        ax.text(14.5,1.5,"spans gap",fontsize=9,color=INK,ha="center",va="center")
        ax.text(4.5,H-0.95-f,"free",fontsize=8,color=INK,ha="center",va="center")
    if H==7:
        ax.add_patch(Circle((3.4,H-0.95-f),0.95,fc="white",ec=edge,lw=1.5)); ax.text(3.4,H-0.95-f,"free",fontsize=8,color=INK,ha="center",va="center")
        e=5.0
        ax.add_patch(FancyBboxPatch((6.5,H-f-e),12,e,boxstyle=f"round,pad=0,rounding_size={e/2}",fc="white",ec=edge,lw=1.5))
        ax.text(12.5,H-f-e/2,"puddle",fontsize=9,color=INK,ha="center",va="center")
        ax.annotate("",xy=(19.4,H-f),xytext=(19.4,H-f-e),arrowprops=dict(arrowstyle="<->",color=INK2,lw=1))
        ax.text(19.8,H-f-e/2,"e ~ 2Lc\n~ 4.5-5.5 mm",fontsize=8,color=INK2,ha="left",va="center")
        ax.annotate("",xy=(12.5,0),xytext=(12.5,H-f-e),arrowprops=dict(arrowstyle="<->",color=INK2,lw=1))
        ax.text(12.9,(H-f-e)/2,"liquid ~2 mm",fontsize=8,color=INK2,ha="left",va="center")
    ax.set_xlim(0,W); ax.set_ylim(-3.2,8.4); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s_ in ax.spines.values(): s_.set_visible(False)
    ttl={1:"H = 0.3 / 0.7 / 1 mm    H/Lc = 0.11 / 0.26 / 0.37",3:f"H = 3 mm    H/Lc = {3/Lc:.2f}    H/2Lc = {3/(2*Lc):.2f}",7:f"H = 7 mm    H/Lc = {7/Lc:.2f}    H/2Lc = {7/(2*Lc):.2f}"}
    ax.set_title(ttl[H],fontsize=10.5,color=INK,pad=2)
    ax.text(0.2,-1.35,info[H],fontsize=8.5,color=INK2,va="top")
fig.suptitle("Horizontal channel heated from below: how much gas can touch the heated wall (water 20 C, Lc = 2.7 mm)",fontsize=11.5,color=INK,y=0.98)
fig.savefig(OUT+"fig_r1_gap_regimes_horizontal.png",dpi=170,bbox_inches="tight"); plt.close(fig)

# ---------- Fig 2: predicted C0 for pancakes ----------
X=np.logspace(np.log10(0.05),np.log10(10),300)
fig,ax=plt.subplots(figsize=(6.6,4.2))
ax.axvspan(0.04,3.8,color="#000000",alpha=0.04,lw=0)
ax.text(0.40,0.08,"typical pancakes in 0.3-3 mm gaps\n(d/H 3-100, U 0.05-1 m/s)",fontsize=8.5,color=INK2,ha="center")
for c,col,lab in ((5.0,S1,"clean interface (c = 5)"),(12.6,S2,"rigid interface (c = 12.6)")):
    y=2/(1+0.1785*c*X)
    ax.plot(X,y,color=col,lw=2,label=lab,solid_capstyle="round")
    ax.text(X[-1]*1.05,y[-1],lab.split(" (")[0],fontsize=8.5,color=INK2,va="center")
ax.axhline(2,color=MUTED,lw=1); ax.text(0.052,2.03,"no film friction: 2x mean flow (Taylor & Saffman 1959)",fontsize=8,color=INK2)
ax.axhline(1,color=MUTED,lw=1); ax.text(0.052,1.03,"bubble = mean flow",fontsize=8,color=INK2)
ax.set_xscale("log"); ax.set_xlim(0.05,25); ax.set_ylim(0,2.2)
ax.set_xlabel("X = (H/d) Ca^(-1/3)"); ax.set_ylabel("C0 = V_bubble / j")
ax.set_title("Predicted pancake-bubble velocity (Darcy-Bretherton estimate, to be calibrated)",fontsize=10,color=INK,loc="left")
ax.legend(frameon=False,fontsize=8.5,loc="lower left",bbox_to_anchor=(0.0,0.17))
fig.savefig(OUT+"fig_r2_c0_model.png",dpi=170,bbox_inches="tight"); plt.close(fig)

# ---------- Fig 3: single-phase frictional dP over 0.1 m vs measurement offsets ----------
rho,mu=998.2,1.002e-3
U=np.logspace(np.log10(0.03),0,200)
fig,ax=plt.subplots(figsize=(6.6,4.2))
for H,col in ((0.3e-3,S1),(0.7e-3,S2),(1e-3,S3),(3e-3,S4),(7e-3,S5)):
    Dh=2*H; Re=rho*U*Dh/mu
    lam=12*mu*U/H**2; tur=0.316*Re**-0.25/Dh*rho*U**2/2
    dp=np.where(Re<2300,lam,np.maximum(lam,tur))*0.1
    ax.plot(U,dp,color=col,lw=2,label=f"friction, H = {H*1e3:g} mm")
    ax.text(1.04,dp[-1],f"H = {H*1e3:g} mm",fontsize=8.5,color=INK2,va="center")
ax.plot(U,rho*U**2/2,color=MUTED,lw=1.2); ax.text(0.031,rho*0.031**2/2*1.25,"inlet/outlet loss, K = 1",fontsize=8,color=INK2)
g1=rho*9.81*0.1*math.sin(math.radians(1))
ax.axhline(g1,color=MUTED,lw=1.2); ax.text(0.031,g1*1.12,"1 deg tilt (hydrostatic)",fontsize=8,color=INK2)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.03,1.7); ax.set_ylim(0.3,40000)
ax.set_xlabel("mean velocity U (m/s)"); ax.set_ylabel("pressure difference over 0.1 m (Pa)")
ax.set_title("Single-phase friction vs. offsets that can hide it (water 20 C)",fontsize=10,color=INK,loc="left")
ax.text(1.55,0.45,"laminar below Re 2300, Blasius above",fontsize=7.5,color=MUTED,ha="right")
ax.legend(frameon=False,fontsize=8.5,loc="upper left",ncol=2)
fig.savefig(OUT+"fig_r3_dp_magnitudes.png",dpi=170,bbox_inches="tight"); plt.close(fig)
print("ok")

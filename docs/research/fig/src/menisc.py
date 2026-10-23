import math
mu=1.002e-3; sig=0.0728; rho=998.2
# Darcy-Bretherton model for circular pancakes (clean or rigid interfaces), see estimates_microgap.md
def V_over_j(j,H,d,ctot):
    beta=0.1785*ctot
    V=j
    for _ in range(200):
        Ca=mu*V/sig
        V=2*j/(1+beta*(H/d)*Ca**(-1/3))
    return V/j
def terms(j,H,d,alpha,ctot):
    r=V_over_j(j,H,d,ctot); V=r*j; Ca=mu*V/sig
    Gam=4*alpha/d
    dPb=r*0.5356*ctot*sig*Ca**(2/3)*Gam/H
    jG=alpha*V; jL=max(j-jG,1e-9)
    uL=jL/(1-alpha)
    dPL=12*mu*uL/H**2
    return r,dPb,dPL,jG,jL
for ctot,lab in [(5.0,'clean c=5'),(12.6,'rigid c=12.6')]:
    print(f"\n### {lab}")
    print("| H mm | d/H | alpha | j m/s | V/j(=C0) | dP_b Pa/m | dP_L Pa/m | R=dP_b/dP_L | j_G | j_L |")
    for H in (0.3e-3,0.7e-3,1e-3,3e-3):
        for dH in (3,10,30):
            for alpha in (0.1,0.3):
                for j in (0.05,0.2,1.0):
                    r,b,L,jG,jL=terms(j,H,dH*H,alpha,ctot)
                    print(f"| {H*1e3:g} | {dH} | {alpha} | {j} | {r:.2f} | {b:.0f} | {L:.0f} | {b/L:.2f} | {jG:.3f} | {jL:.3f} |")
print("\n### C0 = V/j vs X=(H/d)Ca^(-1/3): C0 = 2/(1+beta X), beta=0.1785 c")
for ctot in (5.0,12.6):
    beta=0.1785*ctot
    print(f"c={ctot}: beta={beta:.2f}; X where C0=1: {1/beta:.2f}; C0 at X=0.1,0.3,1,3: "+", ".join(f"{2/(1+beta*X):.2f}" for X in (0.1,0.3,1,3)))
# Re*: reduced Reynolds for Darcy validity
print("\n### Darcy 가정 점검: Re_H*(H/d) (작아야 함)")
for H in (0.3e-3,0.7e-3,1e-3,3e-3):
    for j in (0.05,0.2,1.0):
        ReH=rho*j*H/mu
        print(f"H={H*1e3:g} mm j={j}: Re_H={ReH:.0f}; d/H=3 -> {ReH/3:.0f}; d/H=30 -> {ReH/30:.1f}")

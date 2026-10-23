import math
g=9.81
# water 20C / air, saturated water 100C (standard property tables)
W20=dict(rho=998.2,mu=1.002e-3,sigma=0.0728,k=0.598,cp=4182,rhog=1.204)
W100=dict(rho=958.4,mu=2.82e-4,sigma=0.0589,k=0.679,cp=4216,rhog=0.598,hfg=2.257e6)
Hs=[1e-3,3e-3,7e-3]
def Lc(P): return math.sqrt(P['sigma']/(g*(P['rho']-P['rhog'])))
print("## A. 길이 척도")
for name,P in [('물 20C',W20),('포화수 100C',W100)]:
    L=Lc(P)
    print(f"{name}: Lc={L*1e3:.2f} mm, 2Lc={2*L*1e3:.2f} mm")
    for H in Hs:
        print(f"  H={H*1e3:.0f} mm: Co=Lc/H={L/H:.2f}, Co(Dh=2H)={L/(2*H):.2f}, Bo=(H/Lc)^2={(H/L)**2:.2f}")
P=W20
print("\n## B. 단상 흐름(물 20C), U=평균 속도")
Us=[0.05,0.1,0.2,0.5,1.0]
print("| H mm | U m/s | Re(Dh=2H) | Re_H | Ca | We_H | dP/dx 층류 Pa/m | dP/dx Blasius Pa/m |")
for H in Hs:
    for U in Us:
        Dh=2*H; Re=P['rho']*U*Dh/P['mu']; ReH=Re/2
        Ca=P['mu']*U/P['sigma']; We=P['rho']*U**2*H/P['sigma']
        lam=12*P['mu']*U/H**2
        f=0.316*Re**-0.25; tur=f/Dh*P['rho']*U**2/2
        print(f"| {H*1e3:.0f} | {U} | {Re:.0f} | {ReH:.0f} | {Ca:.2e} | {We:.2f} | {lam:.0f} | {tur:.0f} |")
print("\n## C. 갇힌 기포 밑 액막 두께(Aussillous-Quere, b=H/2), um")
print("| H mm | " + " | ".join(f"U={U}" for U in Us)+" |")
for H in Hs:
    b=H/2; row=[]
    for U in Us:
        Ca=P['mu']*U/P['sigma']; c=Ca**(2/3)
        h=1.34*c/(1+2.5*1.34*c)*b
        row.append(f"{h*1e6:.1f}")
    print(f"| {H*1e3:.0f} | "+" | ".join(row)+" |")
# boiling film
Q=W100
print("\n## C2. 포화수 100C, 1 mm 갭 액막(Bretherton 0.643 b (3Ca)^(2/3))과 건조 시간 t=rho hfg d0/q")
for V in [0.1,0.3,1.0]:
    Ca=Q['mu']*V/Q['sigma']; d0=0.643*0.5e-3*(3*Ca)**(2/3)
    ts=[Q['rho']*Q['hfg']*d0/q*1e3 for q in (1e4,5e4,1e5)]
    print(f"V={V}: Ca={Ca:.2e}, d0={d0*1e6:.1f} um, t_dry(10/50/100 kW/m2)= {ts[0]:.2f}/{ts[1]:.2f}/{ts[2]:.2f} ms, passage of 5 mm bubble={5e-3/V*1e3:.0f} ms, h_film=k/d0={Q['k']/d0:.0f} W/m2K")

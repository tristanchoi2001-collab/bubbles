"""힘 균형 분해(주제 3 지적 반영): -dP/dx = 12 mu j_L/H^2 + n F_b/H.
경로 A (Darcy 항력, 마찰 법칙 없음): n F_b/H = (12 mu/H^2) alpha (2U - V)
경로 B (메니스커스 법칙): n F_b/H = 0.5356 c sigma Ca_V^(2/3) Gamma/H, Gamma = 4 alpha/d
기포 속도: V/U = 2/(1 + 0.1785 c (H/d) Ca_V^(-1/3))  == Booth, Griffiths & Howell 2023 JFM 954:A21 (delta = 1.12 Ca^(1/3) d/H)
U는 j(혼합 속도)로 둔다(묽은 극한 근사).
"""
mu=1.002e-3; sig=0.0728
def V_over_U(U,H,d,c):
    V=U
    for _ in range(300):
        V=2*U/(1+0.1785*c*(H/d)*(mu*V/sig)**(-1/3))
    return V/U
print("| c | d/H | alpha | j (m/s) | C0 = V/j | 경로 A (Pa/m) | 경로 B (Pa/m) | 액체 12μj_L/H² (Pa/m) | φ_L² − 1 |")
print("|---|---|---|---|---|---|---|---|---|")
H=1e-3
for c in (5.01,12.63):
    for dH in (3,10,30):
        for alpha in (0.1,0.3):
            row=[]
            for j in (0.05,0.2,1.0):
                r=V_over_U(j,H,dH*H,c); V=r*j
                A=12*mu/H**2*alpha*(2*j-V)
                Ca=mu*V/sig; G=4*alpha/(dH*H)
                B=0.5356*c*sig*Ca**(2/3)*G/H
                jL=max(j-alpha*V,1e-9); L=12*mu*jL/H**2
                row.append((r,A,B,L,B/L))
            fmt=lambda k,f: " / ".join(f.format(x[k]) for x in row)
            print(f"| {c} | {dH} | {alpha} | 0.05 / 0.2 / 1.0 | {fmt(0,'{:.2f}')} | {fmt(1,'{:.0f}')} | {fmt(2,'{:.0f}')} | {fmt(3,'{:.0f}')} | {fmt(4,'{:.2f}')} |")

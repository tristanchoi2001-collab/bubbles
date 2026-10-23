import math
k=0.598; rho=998.2; cp=4182; mu=1.002e-3; aL=k/(rho*cp); Pr=mu*cp/k
print(f"water 20C alpha={aL:.3e} Pr={Pr:.2f}")
print("## 단상 층류 완전발달, 한쪽 벽 가열·반대쪽 단열 Nu_Dh=5.385")
for H in (0.3e-3,0.7e-3,1e-3,3e-3,7e-3):
    print(f"H={H*1e3:g} mm: h={5.385*k/(2*H):.0f} W/m2K")
print("## 열 입구 길이 0.05 Re Pr Dh (m)")
for H in (0.3e-3,0.7e-3,1e-3,3e-3,7e-3):
    print(f"H={H*1e3:g}: "+", ".join(f"U={U}: {0.05*rho*U*2*H/mu*Pr*2*H:.2f}" for U in (0.05,0.1,0.2)))
print("## Gnielinski (Dh=2H, 양쪽 가열 원관식 그대로, 참고)")
for H in (3e-3,7e-3):
    for U in (0.5,1.0):
        Re=rho*U*2*H/mu
        if Re<3000: print(f"H={H*1e3:g} U={U}: Re={Re:.0f} (전이)"); continue
        f=(0.79*math.log(Re)-1.64)**-2
        Nu=(f/8)*(Re-1000)*Pr/(1+12.7*math.sqrt(f/8)*(Pr**(2/3)-1))
        print(f"H={H*1e3:g} U={U}: Re={Re:.0f} Nu={Nu:.0f} h={Nu*k/(2*H):.0f}")
print("## 표면 갱신 상한 h=2k/sqrt(pi alpha t_c), t_c=1/f")
for f in (2,5,10,20,50):
    print(f"f={f} Hz: h={2*k/math.sqrt(math.pi*aL/f):.0f} W/m2K, 침투 sqrt(pi a t)={math.sqrt(math.pi*aL/f)*1e3:.2f} mm")
print("## 통과 빈도 f ~ alpha V/(pi d/4) (원형, 한 점 기준)")
for d in (3e-3,5e-3,10e-3):
    for V in (0.1,0.5):
        print(f"d={d*1e3:.0f} mm V={V}: f(alpha=0.3)={0.3*V/(math.pi*d/4):.1f} Hz")
print("## Cooper 풀 비등 (물 1 atm, Ra 1um)")
pr=101.325/22064; M=18.015
for q in (2e4,5e4,1e5,2e5):
    h=55*pr**0.12*(-math.log10(pr))**-0.55*M**-0.5*q**0.67
    print(f"q={q/1e3:.0f} kW/m2: h={h:.0f}")
print("## 열전대 응답: 침투 깊이 delta=sqrt(a/(pi f)), 깊이 z에서 진폭비 exp(-z/delta)")
mats={'탄소강(k50)':(50,7850,470),'스테인리스304(k14.9)':(14.9,7900,477),'구리(k401)':(401,8933,385)}
for name,(kk,r,c) in mats.items():
    a=kk/(r*c); e=math.sqrt(kk*r*c)
    row=[]
    for f in (0.1,1,10,50):
        d=math.sqrt(a/(math.pi*f))
        row.append(f"f={f}: d={d*1e3:.2f} mm, z=2mm {math.exp(-2e-3/d):.3f}")
    print(f"{name}: alpha={a:.2e}, 열침투율 e={e:.0f}; "+"; ".join(row))
print(f"물 열침투율 e={math.sqrt(k*rho*cp):.0f}")
print("## 1D 외삽: dT between TCs = q dz/k (dz=5 mm)")
for name,kk in (('탄소강',50),('스테인리스',14.9),('구리',401)):
    print(name, ", ".join(f"q={q/1e3:.0f}kW/m2: {q*5e-3/kk:.2f} K" for q in (1e4,5e4,1e5)))
print("## 투영 → 부피 기공률 비 (팬케이크: 1 - 0.429 H/d - 2delta/H; 구: 2d/(3H))")
for H in (0.3e-3,0.7e-3,1e-3,3e-3):
    for dH in (1.5,3,10,30):
        print(f"H={H*1e3:g} d/H={dH}: pancake ratio={1-0.429/dH-2*10e-6/H:.2f}")
for H in (3e-3,7e-3):
    for d in (1e-3,2e-3,3e-3):
        if d<=H: print(f"H={H*1e3:g} sphere d={d*1e3:.0f} mm: ratio={2*d/(3*H):.2f}")
print("puddle in 7 mm, e=4.5-5.5 mm: ratio ~", round(4.5/7*0.95,2),"-",round(5.5/7*0.95,2))
print("## 압력: 입출구 손실 K rho U^2/2 (K=1), 1도 기울기 중력 rho g L sin(1deg), L=0.1 m")
for U in (0.05,0.1,0.2,0.5,1.0):
    print(f"U={U}: minor={rho*U*U/2:.1f} Pa")
print(f"gravity 1deg over 0.1 m: {rho*9.81*0.1*math.sin(math.radians(1)):.1f} Pa; 0.1deg: {rho*9.81*0.1*math.sin(math.radians(0.1)):.1f} Pa")
print("## 비등 가속 항 G^2 x (1/rho_v - 1/rho_l), x_out")
for G in (50,100,300):
    print(f"G={G}: "+", ".join(f"x={x}: {G*G*x*(1/0.598-1/958.4):.0f} Pa" for x in (0.01,0.05,0.1)))

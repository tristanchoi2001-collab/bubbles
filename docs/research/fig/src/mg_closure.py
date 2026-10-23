"""속도 없이 시험하는 압력 폐합: Hele-Shaw 기포 = 2D 유효 매질(Clausius–Mossotti/Maxwell–Garnett).

Darcy(깊이 평균) 흐름 u = K·G, K = H^2/12, G = -dP/dx / mu.
원형 팬케이크 기포 k(면적 분율 a_k)는 속도 V_k로 움직이고, 바깥 흐름에는 쌍극자 (V_k - U_m) R^2로만 작용한다
(바깥 퍼텐셜 흐름의 경계조건이 u·n = V·n이므로 마찰 기구와 무관). U_m = K·G_m(기질 평균 장).
  S = sum a_k L_k, L_k = V_k/U_m - 1
  j = U_m (1 + S),  <G> = G_m (1 - S)  ->  K_eff/K = (1 + S)/(1 - S)
  beta = j_G/j = sum a_k V_k / j = (alpha + S)/(1 + S)  ->  S = (beta - alpha)/(1 - beta)
  phi_L^2 = [(12 mu j/H^2)(1 - S)/(1 + S)] / [12 mu j_L/H^2] = (1 + alpha - 2 beta)/((1 - alpha)(1 - beta))
  E = phi_L^2 - 1 = (2 alpha - beta - alpha beta)/((1 - alpha)(1 - beta))
-> 크기 분포와 무관하게 alpha(영상)와 beta(유량계)만으로 E가 정해진다. 1차(묽은) 근사는 (2 alpha - beta)/(1 - beta).
민감도: dE/dalpha = 2/(1 - alpha)^2, dE/dbeta = -1/(1 - beta)^2.
선행: Bławzdziewicz & Wajnryb 2008 Phys. Fluids 20:093303 (평행 벽 사이 입자 현탁액의 Clausius–Mossotti 투과율).

아래 표는 Booth et al. 2023 이동도(V/U_m = 2/(1 + 0.1785 c (H/d) Ca_V^(-1/3)))로 alpha, j, d/H에서 beta를 만든 뒤
E(유효 매질)와 E(묽은 근사, 기존 estimates 5.2절)를 비교하고, 측정 오차로 판별 가능한지 본다.
"""
import itertools
import math

mu = 1.002e-3
sig = 0.0728


def mobility(Um, dH, c):
    """Booth 2023: V/U_m, Ca_V = mu V / sigma (자기 일관)."""
    V = Um
    for _ in range(400):
        V = 2 * Um / (1 + 0.1785 * c / dH * (mu * V / sig) ** (-1 / 3))
    return V / Um


def solve(alpha, j, dH, c):
    """MG: U_m = j/(1 + alpha L), L = V/U_m - 1, 자기 일관."""
    Um = j
    for _ in range(400):
        L = mobility(Um, dH, c) - 1
        Um = j / (1 + alpha * L)
    V = Um * (1 + L)
    beta = alpha * V / j
    return L, V, beta


def E_mg(alpha, beta):
    return (2 * alpha - beta - alpha * beta) / ((1 - alpha) * (1 - beta))


def E_dilute(alpha, beta):
    return (2 * alpha - beta) / (1 - beta)


def check_algebra():
    # 1) 단분산: Lambda로 직접 계산한 phi_L^2와 alpha, beta 식이 같은가
    for alpha, L in [(0.1, 0.5), (0.3, -0.4), (0.25, 1.0), (0.2, -1.0)]:
        S = alpha * L
        beta = alpha * (1 + L) / (1 + S)
        phi2_direct = (1 / (1 - beta)) * (1 - S) / (1 + S)
        assert abs(phi2_direct - 1 - E_mg(alpha, beta)) < 1e-12
    # 2) 다분산: 크기 구분마다 Lambda가 달라도 총 alpha, beta만으로 같은 값
    ak = [0.05, 0.1, 0.08]
    Lk = [-0.3, 0.4, 0.9]
    S = sum(a * l for a, l in zip(ak, Lk))
    alpha = sum(ak)
    beta = sum(a * (1 + l) for a, l in zip(ak, Lk)) / (1 + S)
    phi2_direct = (1 / (1 - beta)) * (1 - S) / (1 + S)
    assert abs(phi2_direct - 1 - E_mg(alpha, beta)) < 1e-12
    # 3) 마찰 없는 기포(Taylor–Saffman, Lambda = 1) -> E = 0, 멈춘 기포(beta = 0) -> 2 alpha/(1 - alpha)
    for alpha in (0.1, 0.3):
        beta = 2 * alpha / (1 + alpha)
        assert abs(E_mg(alpha, beta)) < 1e-12
        assert abs(E_mg(alpha, 0) - 2 * alpha / (1 - alpha)) < 1e-12
    print("대수 검산 통과: 단분산 = alpha·beta 식, 다분산도 같은 식, Taylor–Saffman E = 0, 멈춘 기포 2a/(1-a)")


def table():
    # 측정 오차 가정: alpha 상대 5 %(경계 ±1 px, 부피 환산), beta 상대 2 %(유량계 둘), 측정 E 절대 0.02(차압계·j_L)
    ra, rb, dEm = 0.05, 0.02, 0.02
    print("| c | d/H | α | j (m/s) | C0 = V/j | β | E 유효 매질 | E 묽은 근사 | 예측 오차 ±δE | 판별 (E > 3σ) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for c, dH, alpha in itertools.product((5.01, 12.63), (3, 10, 30), (0.1, 0.2, 0.3)):
        cells = []
        for j in (0.05, 0.2, 1.0):
            L, V, beta = solve(alpha, j, dH, c)
            E = E_mg(alpha, beta)
            Ed = E_dilute(alpha, beta)
            dE_pred = math.hypot(2 / (1 - alpha) ** 2 * ra * alpha, 1 / (1 - beta) ** 2 * rb * beta)
            sigma = math.hypot(dE_pred, dEm)
            cells.append((V / j, beta, E, Ed, dE_pred, "O" if E > 3 * sigma else "x"))
        f = lambda k, fmt: " / ".join(fmt.format(x[k]) for x in cells)
        print(f"| {c} | {dH} | {alpha} | 0.05 / 0.2 / 1.0 | {f(0, '{:.2f}')} | {f(1, '{:.3f}')} | "
              f"{f(2, '{:.3f}')} | {f(3, '{:.3f}')} | {f(4, '{:.3f}')} | {f(5, '{}')} |")


def inverse_demo():
    # 속도를 못 잴 때: 측정 alpha, beta -> 평균 이동도 Lambda(질량 보존) -> c 역산(단분산 d 가정)
    print("\n역산 예: alpha, beta, d/H, j -> 평균 이동도 Lambda와 c")
    for c_true, dH, alpha, j in [(5.01, 10, 0.2, 0.2), (12.63, 10, 0.2, 0.2), (5.01, 3, 0.1, 0.05)]:
        L, V, beta = solve(alpha, j, dH, c_true)
        S = (beta - alpha) / (1 - beta)
        Lam = S / alpha
        # c를 이분법으로
        lo, hi = 0.5, 60.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            Lm, _, bm = solve(alpha, j, dH, mid)
            if bm > beta:
                lo = mid
            else:
                hi = mid
        # alpha 5 % 오차의 영향
        Lp, _, _ = solve(alpha, j, dH, c_true)
        lo2, hi2 = 0.5, 60.0
        a2 = alpha * 1.05
        for _ in range(80):
            mid = 0.5 * (lo2 + hi2)
            _, _, bm = solve(a2, j, dH, mid)
            if bm > beta:
                lo2 = mid
            else:
                hi2 = mid
        print(f"  c={c_true}, d/H={dH}, alpha={alpha}, j={j}: beta={beta:.3f}, Lambda={Lam:.3f}, "
              f"역산 c={0.5 * (lo + hi):.2f}, alpha +5 %면 c={0.5 * (lo2 + hi2):.2f}")


if __name__ == "__main__":
    check_algebra()
    table()
    inverse_demo()

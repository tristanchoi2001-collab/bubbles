"""I82 수치 실험 도구: 주기 상자 속 무작위(겹치지 않는) 원판 무리의 2차원 Darcy 흐름.

국소장의 s배로 움직이는 원 = 전도도 ε = s/(2 − s)인 원판(쌍극자 수준에서 같음, 독립 검토 3).
div(σ∇φ) = 0, φ = −Gx + φ'(주기). 덮임 비율은 화소 4 × 4 표본, 면 전도도는 조화 평균, 행렬 없는 CG + 야코비 전처리.
출력: α(원판 면적 비), E = G/j_L − 1, B = j_G/j_L(원판 안 플럭스 = 기체 유량), 원형 평균장 폐합 E_MG = 2α/(1 − α) − B.
격자 오차는 1/R에 비례한다(R 14화소에서 원판 하나 2~6%). 그래서 같은 R의 원판 하나로 유효 C를 정하고 비교한다.
배치 계수 Q(I74, 원 합 = Lorentz 기준)는 q_periodic()이 주기 상의 띠 합 + 연속체 보정으로 낸다(plane_from_csv.layout_q와 같은 꼴,
측벽 거울상 대신 상자 주기 상). 배치 보정 ΔE = [2λQ/(1 − α − λQ)]·α/(1 − α), λ = s − 1.
    python darcy_disks.py --sweep out.json     # α 0.05~0.4 × s 0.41/0.8/1.57 × 시드 2 (512², R 14, 약 9분, 배치마다 Q 포함)
    python darcy_disks.py                      # 원판 하나 점검
"""

import numpy as np, math, time

def make_disks(N, alpha, R, rng, max_try=200000, gap=1.0):
    """무작위 순차 추가(RSA). gap = 원판 사이 최소 간격(화소). 기본 1.0이 그림 r13의 계산."""
    L = N
    n = int(round(alpha * L * L / (math.pi * R * R)))
    pts = []
    tries = 0
    while len(pts) < n and tries < max_try:
        tries += 1
        p = rng.uniform(0, L, 2)
        ok = True
        for q in pts:
            d = p - q
            d -= L * np.round(d / L)
            if d[0] * d[0] + d[1] * d[1] < (2 * R + gap) ** 2:
                ok = False; break
        if ok:
            pts.append(p)
    return np.array(pts), n

def coverage(N, pts, R, sub=4):
    """화소마다 원판이 덮는 비율(sub×sub 표본, 주기)."""
    cov = np.zeros((N, N))
    o = (np.arange(sub) + 0.5) / sub
    for p in pts:
        x0, x1 = int(math.floor(p[0] - R - 1)), int(math.ceil(p[0] + R + 1))
        y0, y1 = int(math.floor(p[1] - R - 1)), int(math.ceil(p[1] + R + 1))
        xs = np.arange(x0, x1); ys = np.arange(y0, y1)
        X = xs[:, None, None, None] + o[None, None, :, None]
        Y = ys[None, :, None, None] + o[None, None, None, :]
        inside = ((X - p[0]) ** 2 + (Y - p[1]) ** 2 <= R * R).mean(axis=(2, 3))
        cov[np.ix_(xs % N, ys % N)] += inside
    return np.clip(cov, 0, 1)

def solve(sigma, G=1.0, tol=1e-9, maxit=20000):
    """주기 격자 (i: x, j: y). 면 전도도: 조화 평균. 미지수 φ' (평균 0)."""
    sx = 2 * sigma * np.roll(sigma, -1, 0) / (sigma + np.roll(sigma, -1, 0))   # i+1/2 면
    sy = 2 * sigma * np.roll(sigma, -1, 1) / (sigma + np.roll(sigma, -1, 1))
    def A(p):
        fx = sx * (np.roll(p, -1, 0) - p)
        fy = sy * (np.roll(p, -1, 1) - p)
        return -(fx - np.roll(fx, 1, 0) + fy - np.roll(fy, 1, 1))
    # 우변: 외부 구배 −G x가 만드는 발산. 면 x 플럭스의 외부 부분 = sx*(−G)
    fx0 = sx * (-G)
    b = (fx0 - np.roll(fx0, 1, 0))
    diag = sx + np.roll(sx, 1, 0) + sy + np.roll(sy, 1, 1)
    x = np.zeros_like(sigma)
    r = b - A(x); z = r / diag; p = z.copy(); rz = (r * z).sum()
    bn = math.sqrt((b * b).sum())
    if bn == 0:
        return x, sx * G, 0
    for it in range(maxit):
        Ap = A(p); al = rz / (p * Ap).sum()
        x += al * p; r -= al * Ap
        if math.sqrt((r * r).sum()) < tol * bn:
            break
        z = r / diag; rz2 = (r * z).sum(); p = z + (rz2 / rz) * p; rz = rz2
    fx = sx * (G - (np.roll(x, -1, 0) - x))                                    # 전체 면 플럭스(x 방향, 전류 = −σ∇V)
    return x, fx, it

def q_periodic(pts, N, a2, alpha, Kx=3, Ky=60):
    """주기 상자(한 변 N)의 배치 계수 Q: 원판마다 |Δx| ≤ L, |Δy| ≤ C 띠 안의 모든 상에서 a²cos 2θ/r²를 더하고
    연속체 보정 α[1 − (4/π)arctan(L/C)]을 더한 값의 평균(원판 크기가 같을 때). 반환 (평균, 원판별 표준편차)."""
    L = (Kx - 0.5) * N
    C = (Ky - 0.5) * N
    shifts = np.array([(k * N, l * N) for k in range(-Kx, Kx + 1) for l in range(-Ky, Ky + 1)], float)
    corr = alpha * (1 - 4 / math.pi * math.atan(L / C))
    qs = []
    for p in pts:
        d0 = pts - p
        d0 -= N * np.round(d0 / N)
        dd = (d0[:, None, :] + shifts[None, :, :]).reshape(-1, 2)
        dx, dy = dd[:, 0], dd[:, 1]
        r2 = dx * dx + dy * dy
        m = (r2 > 1e-9) & (np.abs(dx) <= L) & (np.abs(dy) <= C)
        qs.append(np.sum(a2 * (dx[m] ** 2 - dy[m] ** 2) / r2[m] ** 2) + corr)
    return float(np.mean(qs)), float(np.std(qs))


def run(N, alpha, R, s, seed, gap=1.0, layout=False):
    rng = np.random.default_rng(seed)
    pts, n_target = make_disks(N, alpha, R, rng, gap=gap)
    cov = coverage(N, pts, R)
    eps = s / (2 - s)
    sigma = 1 + (eps - 1) * cov
    phi, fx, it = solve(sigma)
    # 면 플럭스를 셀 중심으로(평균), 원판 안 플럭스 = 덮임 가중
    fc = 0.5 * (fx + np.roll(fx, 1, 0))
    a = cov.mean()
    j_tot = fc.mean()
    j_g = (fc * cov).mean()
    j_l = j_tot - j_g
    E = 1.0 / j_l - 1.0                      # G = 1, K = 1
    B = j_g / j_l
    E_mg = 2 * a / (1 - a) - B
    out = dict(alpha=a, n=len(pts), n_target=n_target, s=s, E=E, B=B, E_mg=E_mg, it=it, s_bar=B * (1 - a) / a, gap=gap)
    if layout and len(pts) > 1:
        out["Q"], out["Q_sd"] = q_periodic(pts, N, R * R, len(pts) * math.pi * R * R / N ** 2)
    return out



def sweep(path, N=512, R=14, alphas=(0.05, 0.1, 0.2, 0.3, 0.4), ss=(0.41, 0.8, 1.57), seeds=(1, 2)):
    import json
    out = {"N": N, "R": R, "calib": {}, "runs": []}
    for s in ss:
        r = run(N, 0.0024, R, s, 0)
        a, E, B = r["alpha"], r["E"], r["B"]
        y = E * (1 - a) / a; x = 1 - B * (1 - a) / a
        out["calib"][f"{s:g}"] = dict(alpha=a, E=E, B=B, C_eff=(y - 1) / x if abs(x) > 1e-3 else float("nan"))
    for alpha in alphas:
        for s in ss:
            for seed in seeds:
                out["runs"].append(run(N, alpha, R, s, seed, layout=True))
    json.dump(out, open(path, "w"), default=float, indent=1)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--sweep":
        sweep(sys.argv[2])
        raise SystemExit
    t0 = time.time()
    # 정밀도 점검: 단일 원판(묽음)에서 쌍극자 이론과 비교
    for s in (0.41, 1.57):
        r = run(256, 0.01, 14, s, 0)
        print("dilute check", {k: round(v, 5) if isinstance(v, float) else v for k, v in r.items()}, "time", round(time.time() - t0, 1))

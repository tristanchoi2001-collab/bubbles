"""2차원 부가질량 계수 C_A(흐름 방향 x)를 기포 윤곽에서 경계요소법으로 구한다 (아이디어 I81).

판별 평면 폐합의 모양 인자는 c = 1 + C_A다(원 1, 흐름 방향 반축 a·가로 반축 b 타원 b/a).
윤곽은 (N, 2) 배열(픽셀 좌표 가능, 반시계 방향이 아니면 자동으로 뒤집음). 흐름은 +x 방향으로 놓는다.
    python added_mass_bem.py          # 원·타원·총알 모양으로 스스로 점검

방법: 외부 Neumann 문제 ∂φ/∂n = n_x(기포 밖 법선), 상수 요소 + 8점 Gauss 적분, 자기 요소의 log 특이점은 해석 적분.
C_A = −∮ φ n_x ds / 면적. 요소 200~400개면 원·타원에서 상대 오차 1e-4 이하.
"""
import numpy as np


def added_mass_coefficient(xy, n_gauss=8):
    xy = np.asarray(xy, dtype=float)
    signed = 0.5 * np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - np.roll(xy[:, 0], -1) * xy[:, 1])
    if signed < 0:
        xy = xy[::-1]
    a = xy
    b = np.roll(xy, -1, axis=0)
    mid = 0.5 * (a + b)
    t = b - a
    L = np.linalg.norm(t, axis=1)
    tu = t / L[:, None]
    n = np.stack([tu[:, 1], -tu[:, 0]], axis=1)              # 기포 밖을 향하는 법선(반시계 윤곽)
    N = len(mid)
    G = np.zeros((N, N))
    H = np.zeros((N, N))
    gp, gw = np.polynomial.legendre.leggauss(n_gauss)
    s = 0.5 * (gp + 1)
    for j in range(N):
        q = a[j][None, :] + s[:, None] * t[j][None, :]
        w = 0.5 * gw * L[j]
        d = mid[:, None, :] - q[None, :, :]
        r2 = (d ** 2).sum(-1)
        G[:, j] = (-np.log(np.sqrt(r2)) / (2 * np.pi) * w).sum(1)
        H[:, j] = ((d * n[j][None, None, :]).sum(-1) / (2 * np.pi * r2) * w).sum(1)
        hl = L[j] / 2
        G[j, j] = -(1 / (2 * np.pi)) * 2 * (hl * np.log(hl) - hl)
        H[j, j] = 0.0
    phi = np.linalg.solve(0.5 * np.eye(N) - H, -(G @ n[:, 0]))
    area = 0.5 * np.abs(np.sum(a[:, 0] * b[:, 1] - b[:, 0] * a[:, 1]))
    return float(-(phi * n[:, 0] * L).sum() / area)


def _selftest():
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    for ax, bx in ((1, 1), (2, 1), (1, 2)):
        ca = added_mass_coefficient(np.stack([ax * np.cos(th), bx * np.sin(th)], 1))
        print(f"타원 a={ax}(흐름 방향) b={bx}: C_A = {ca:.4f} (이론 b/a = {bx / ax:.4f})")
    R = 1.0
    front = np.stack([R * np.cos(np.linspace(-np.pi / 2, np.pi / 2, 200)), R * np.sin(np.linspace(-np.pi / 2, np.pi / 2, 200))], 1)
    for L0 in (0.0, 0.5, 1.0):
        parts = [front]
        if L0 > 0:
            parts.append(np.stack([np.linspace(0, -L0, 50, endpoint=False), np.full(50, R)], 1)[1:])
        parts.append(np.stack([np.full(100, -L0), np.linspace(R, -R, 100, endpoint=False)], 1))
        if L0 > 0:
            parts.append(np.stack([np.linspace(-L0, 0, 50, endpoint=False), np.full(50, -R)], 1)[1:])
        ca = added_mass_coefficient(np.vstack(parts))
        print(f"총알(앞 반원 + 뒤 평면, 길이 {R + L0:.1f}, 폭 {2 * R:.1f}): C_A = {ca:.3f}, 같은 폭/길이 타원 {2 * R / (R + L0):.3f}")


if __name__ == "__main__":
    _selftest()

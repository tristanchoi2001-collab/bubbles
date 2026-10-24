"""2차원 부가질량 계수 C_A(흐름 방향 x)를 기포 윤곽에서 경계요소법으로 구한다 (아이디어 I81).

판별 평면 폐합의 모양 인자는 c = 1 + C_A다(원 1, 흐름 방향 반축 a·가로 반축 b 타원 b/a).
원거리 쌍극자의 세기는 (V − U)·A(1 + C_A)다(독립 검토 4가 임의 모양에서 0.1% 안으로 확인).
윤곽은 (N, 2) 배열(픽셀 좌표 가능, 반시계 방향이 아니면 자동으로 뒤집음, 끝점이 첫 점을 반복해도 됨).
흐름은 +x 방향으로 놓는다. 영상에서 흐름이 위·아래면 flow="up"/"down"으로 주면 돌려서 계산한다.
    python added_mass_bem.py          # 원·타원·총알·화소 원판으로 스스로 점검

방법: 외부 Neumann 문제 ∂φ/∂n = n_x(기포 밖 법선), 상수 요소 + 8점 Gauss 적분, 자기 요소의 log 특이점은 해석 적분.
C_A = −∮ φ n_x ds / 면적. 요소 200~400개면 원·타원에서 상대 오차 1e-4 이하.
시간(독립 검토 4): 요소 100/200/400개에 약 8/26/100 ms.
화소 윤곽은 C_A를 키운다(화소 중심 윤곽 R 5/10/20 px에서 +7/+3/+1.3%, 계단 윤곽은 그 두 배쯤).
마스크에서 구할 때는 added_mass_from_mask()가 marching squares(contourpy, matplotlib에 딸림) 윤곽을
같은 호 길이로 다시 뽑고 푸리에 평활(기본 12 모드, 192점)한 뒤 계산한다. 화소 원판에서 R ≥ 10 px면 0.4% 안,
R 5 px는 +3.6%. 날카로운 모서리(화소 반원판)는 2~4% 작게 나온다(모서리가 둥글어짐. 실제 기포 윤곽은 둥글다).
"""
import numpy as np


def clean_contour(xy, tol=1e-9):
    """연속으로 겹친 점(끝점이 첫 점을 반복하는 닫힌 윤곽 포함)을 지운다. 길이 0 요소는 NaN을 낸다."""
    xy = np.asarray(xy, dtype=float)
    keep = np.ones(len(xy), bool)
    d = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    keep[1:] = d > tol
    xy = xy[keep]
    while len(xy) > 3 and np.linalg.norm(xy[-1] - xy[0]) <= tol:
        xy = xy[:-1]
    return xy


def resample_contour(xy, n):
    """닫힌 윤곽을 호 길이가 같은 n개 점으로 다시 뽑는다."""
    xy = clean_contour(xy)
    closed = np.vstack([xy, xy[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0.0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])], axis=1)


def fourier_smooth(xy, modes, n=None):
    """호 길이로 고르게 뽑은 윤곽의 복소 푸리에 계수 중 |k| ≤ modes만 남긴다(화소 계단 제거)."""
    n = n or max(128, 8 * modes)
    z = resample_contour(xy, n)
    c = np.fft.fft(z[:, 0] + 1j * z[:, 1])
    k = np.fft.fftfreq(n, d=1.0 / n)
    c[np.abs(k) > modes] = 0.0
    zs = np.fft.ifft(c)
    return np.stack([zs.real, zs.imag], axis=1)


def orient_for_flow(xy, flow="right"):
    """흐름 방향이 +x가 되게 윤곽을 돌린다. C_A,xx는 흐름의 부호와 무관하므로 right=left, up=down."""
    xy = np.asarray(xy, dtype=float)
    if flow in ("up", "down"):
        return np.stack([xy[:, 1], xy[:, 0]], axis=1)
    return xy


def added_mass_coefficient(xy, n_gauss=8):
    xy = clean_contour(xy)
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


def mask_contour(mask):
    """이진 마스크(2차원 bool/0-1)의 가장 긴 닫힌 바깥 윤곽(marching squares, 0.5 등고선). 좌표는 (x = 열, y = 행)."""
    import contourpy
    m = np.pad(np.asarray(mask, dtype=float), 1)
    lines = contourpy.contour_generator(z=m).lines(0.5)
    if not lines:
        return None
    best = max(lines, key=len)
    return best - 1.0                                         # 패딩 1화소를 되돌림


def added_mass_from_mask(mask, flow="right", n=192, modes=12):
    """마스크 하나의 C_A(흐름 방향). 윤곽 → 고른 재표본 → 푸리에 평활(modes) → 흐름 방향 회전 → BEM."""
    xy = mask_contour(mask)
    if xy is None or len(xy) < 8:
        return float("nan")
    xy = fourier_smooth(xy, modes, n=max(n, 8 * modes)) if modes else resample_contour(xy, n)
    if len(xy) != n:
        xy = resample_contour(xy, n)
    return added_mass_coefficient(orient_for_flow(xy, flow))


def _selftest():
    import time
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    for ax, bx in ((1, 1), (2, 1), (1, 2)):
        ca = added_mass_coefficient(np.stack([ax * np.cos(th), bx * np.sin(th)], 1))
        print(f"타원 a={ax}(흐름 방향) b={bx}: C_A = {ca:.4f} (이론 b/a = {bx / ax:.4f})")
    e = np.stack([2 * np.cos(th), np.sin(th)], 1) @ np.array([[np.cos(np.pi / 4), np.sin(np.pi / 4)], [-np.sin(np.pi / 4), np.cos(np.pi / 4)]])
    print(f"45° 기울인 타원(a 2, b 1): C_A = {added_mass_coefficient(e):.4f} (이론 1.25)")
    closed = np.vstack([np.stack([np.cos(th), np.sin(th)], 1), [[1.0, 0.0]]])
    print(f"첫 점을 끝에 반복한 원: C_A = {added_mass_coefficient(closed):.4f} (전에는 NaN)")
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
    print("화소 원판(마스크 → marching squares 윤곽): 평활 없음 / 12 모드 평활")
    for Rp in (5, 10, 20):
        yy, xx = np.mgrid[-Rp - 3:Rp + 4, -Rp - 3:Rp + 4]
        m = (xx + 0.3) ** 2 + (yy - 0.2) ** 2 <= Rp * Rp
        raw = added_mass_coefficient(resample_contour(mask_contour(m), 128))
        sm = added_mass_from_mask(m)
        print(f"  R {Rp} px: {raw:.3f} / {sm:.3f} (이론 1)")
    yy, xx = np.mgrid[-25:26, -25:26]
    half = ((xx ** 2 + yy ** 2) <= 400) & (xx >= 0)
    print(f"화소 반원판(R 20 px, 평평한 면이 뒤): {added_mass_from_mask(half):.3f}, 같은 모양 해석 윤곽 2.11")
    ell_v = ((xx / 10.0) ** 2 + (yy / 20.0) ** 2) <= 1      # 영상 세로(y)로 긴 타원
    print(f"세로로 긴 타원(가로 10, 세로 20 px): flow=right {added_mass_from_mask(ell_v, 'right'):.3f}(이론 2), "
          f"flow=up {added_mass_from_mask(ell_v, 'up'):.3f}(이론 0.5)")
    for n in (100, 200, 400):
        z = np.stack([np.cos(np.linspace(0, 2 * np.pi, n, endpoint=False)), np.sin(np.linspace(0, 2 * np.pi, n, endpoint=False))], 1)
        t0 = time.perf_counter()
        added_mass_coefficient(z)
        print(f"요소 {n}개: {1e3 * (time.perf_counter() - t0):.0f} ms")


if __name__ == "__main__":
    _selftest()

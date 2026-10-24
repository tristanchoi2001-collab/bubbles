"""판별 평면(아이디어 I73, 추정 5.4절)을 운전점 표 + 추적 CSV에서 바로 그린다.

쓰는 법
    python plane_from_csv.py points.csv --out plane_out
    python plane_from_csv.py --demo --out plane_demo      # 합성 자료로 스스로 점검

points.csv (UTF-8, 운전점 한 줄씩. 열 이름은 영어)
    name          운전점 이름
    H_mm          유효 갭(단상 ΔP로 정한 값을 권장)
    jL, jG        액체·기체 겉보기 속도 (m/s, 시야 위치의 압력으로 환산한 값)
    dp_tp, dp_l   같은 탭 구간의 이상류 ΔP와 같은 j_L의 단상 ΔP (Pa)
    tracking_csv  2_bin_track.py / 2_steel_track.py 의 result_tracking.csv 경로
    roi_area_px   ROI 면적(px)
    px_mm         화소 크기(mm/px)
    fps           촬영 속도(frame/s)
    flow          영상에서 흐름 방향: up(투명 채널 기본, y가 줄어드는 쪽) / down / right(철 채널 기본) / left
    mu, rho       액체 점도(Pa·s)·밀도(kg/m³). 비우면 물 20 °C
    T_tp, T_l     (선택) 이상류·단상 측정 때 수온(°C). 둘 다 있으면 dp_l을 물 점도 비 μ(T_tp)/μ(T_l)로 보정
    wall_lo_px, wall_hi_px  (선택) 두 측벽의 가로 좌표(화소, 영상 밖이어도 됨). 흐름이 up/down이면 X, right/left면 Y.
                  비우면 모든 프레임의 기포 가로 끝(중심 ± 등가 반경)의 최소·최대로 추정하고 경고한다.
    q_radius_px   (선택) 배치 계수 Q를 더하는 흐름 방향 반폭 L(화소). 비우면 min(채널 폭, 시야 길이/3)
    masks_dir     (선택) 추적 프로그램의 SAVE_INSTANCE_MASKS 출력 폴더(OUTPUT_FOLDER/instances, 프레임마다 <파일 이름>.npz의
                  라벨 지도 inst). 있으면 기포 윤곽마다 경계요소법으로 C_A(I81)를 구해 b/a 추정기 대신 쓴다.
                  CSV 기포와는 중심 3 px·면적 비 0.8~1.25로 짝짓는다. ca_max_bubbles(기본 2000)개까지만 표본으로 계산한다.

계산 (모두 "갭을 채운 기포", 즉 등가직경 d > 2H만 쓴다)
    α        프레임마다 Σ ROI内面積 / ROI 면적의 평균
    b/a      화면 끝에 닿지 않은 기포마다 a = |중심 − 앞끝|(흐름 방향 반축), b = A/(π a) → b/a = A/(π a²), 면적 가중 평균
             앞끝은 윤곽 위쪽 5% 점의 평균이라 a가 조금 작게 나와 b/a가 몇 % 크게 나온다.
    s̄        B(1 − α)/α (B = jG/jL, 유량계), s̄_T = B_f(1 − α)/α (B_f = 영상 기체 유량 / jL, 추적)
    E        dp_tp/dp_l − 1,  y = E(1 − α)/α,  x = 1 − s̄
    예측     원형 폐합 y = 1 + x, 모양 폐합 y = 1 + (b/a)x, 분리류 y = 1, 균질류 y = 1 − x
             기포별 y_track = ΣA_i[1 + (b/a)_i(1 − s_i)]/ΣA_i, s_i = u_i(1 − α)/jL (추적 속도, 유량계 불필요)
    Re_B     ρH²u_B²/(μ w_B u_L) (Moriyama & Inoue 1993), Λ = ρ u_L H²/(10 μ d̄)
    Q        배치 계수(I74, 독립 검토 3). 기포 i에서 Q_i = Σ_j a_j²·cos 2θ_ij / r_ij²(a_j = 등가 반경, θ는 흐름 방향 기준,
             원 합 = Lorentz 기준). 측벽(불투과)의 거울상(같은 부호, 두 벽이라 2W 주기)과 기포 자신의 거울상을 넣고,
             흐름 방향 띠 |Δs| ≤ L에서 더한 뒤 연속체 보정으로 원 합으로 바꾼다(layout_q 설명). 띠가 시야 밖으로 나가지 않는
             기포만 대상으로 하고 면적 가중 평균한다. 진단용 Q_noimg = 거울상 없는 반경 L의 원 합(고른 배치에서 0과 α 사이).
    C_A      (masks_dir가 있을 때) 윤곽 → marching squares → 푸리에 평활 → 경계요소(added_mass_bem.py)의 면적 가중 평균.
             b/a 추정기(A/(πa²))는 D형·총알 모양에서 C_A를 17~40% 작게 낸다(독립 검토 4). 짝지은 같은 기포들의 두 값을 함께 낸다.
    예측 기울기  slope = C_A − 2Q/(1 − α)(C_A가 없으면 b/a), y_layout = 1 + C_A·x + 2λQ/(1 − α − λQ)(λ = s̄ − 1 = −x),
             y_track_layout = ΣA_i[1 + (C_i − 2Q_i/(1 − α))(1 − s_i)]/ΣA_i(Q_i를 구한 기포만. C_i = 그 기포의 C_A, 없으면 b/a)
쐐기 보정(β_f)은 넣지 않았다. Q는 쌍극자 수준(원 등가)이라 간격 < 2.5a의 줄에서는 몇 % 다를 수 있다.
숫자를 논문에 쓰기 전에 윤곽 규약(I48)과 기체 유량 폐합으로 α를 점검한다.
    python plane_from_csv.py --selftest-q   # 직사각 격자·한 줄·무작위 배치로 Q 계산 점검
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WATER = (1.0e-3, 998.0)
COLS = ["name", "H_mm", "jL", "jG", "dp_tp", "dp_l", "tracking_csv", "roi_area_px", "px_mm", "fps", "flow", "mu", "rho", "T_tp", "T_l",
        "wall_lo_px", "wall_hi_px", "q_radius_px", "masks_dir", "ca_max_bubbles"]


def mu_water(t_c):
    """물 점도(Pa·s), Vogel형 근사 A·10^(B/(T − C)). 비(ratio) 보정용."""
    return 2.414e-5 * 10 ** (247.8 / (t_c + 273.15 - 140.0))


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def read_tracking(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    speed_col = next((c for c in rows[0].keys() if "速度" in c), None) if rows else None
    return rows, speed_col


def axis_of(flow):
    # (좌표 열 이름 끝자, 앞으로 갈 때 좌표가 커지면 +1)
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def layout_q(bubbles, walls, L, s_range, alpha, K=30):
    """기포 배치 계수 Q(I74, 독립 검토 3). bubbles: [(s, c, a², target)] 한 프레임(s = 흐름 방향 좌표, c = 가로 좌표,
    a² = 등가 반경²). walls = (c_lo, c_hi). L = 흐름 방향 반폭. s_range = 시야의 흐름 방향 범위. alpha = 그 프레임의 기공률
    (연속체 보정용. 띠 안의 기포 수로 세면 띠 끝의 불연속 때문에 격자에서 8% 틀렸다).
    Q_i(원 합, Lorentz 기준)를 빨리 수렴하는 꼴로 낸다: 기포 i 둘레 |Δs| ≤ L의 띠에 든 실제 기포와 그 측벽 거울상
    (두 벽 → 2W 주기, k = −K..K, 자기 거울상 포함)을 |Δc| ≤ C = (2K − 1)W까지 더하고, 연속체 보정
    α·[1 − (4/π)·arctan(L/C)]을 더한다(cos 2θ/r²의 연속체 적분: 원 0, 가로로 무한한 띠 −π, 정사각 0).
    직사각 격자·한 줄에서 L = W면 해석값과 0.2% 안(--selftest-q). 진단용 Q_noimg는 거울상 없는 반경 L의 원 합이다.
    반환: [(i, Q_i, Q_noimg_i)] — |Δs| ≤ L의 띠가 시야 안에 드는 target 기포만."""
    if not bubbles:
        return []
    arr = np.array([(b[0], b[1], b[2]) for b in bubbles], dtype=float)
    lo, hi = walls
    W = hi - lo
    C = (2 * K - 1) * W
    corr = 1 - 4 / math.pi * math.atan(L / C)
    out = []
    for i, b in enumerate(bubbles):
        if not b[3] or b[0] - L < s_range[0] or b[0] + L > s_range[1]:
            continue
        sub = arr[np.abs(arr[:, 0] - b[0]) <= L]
        src = [sub]
        for k in range(-K, K + 1):
            if k != 0:
                src.append(np.column_stack([sub[:, 0], sub[:, 1] + 2 * k * W, sub[:, 2]]))
            src.append(np.column_stack([sub[:, 0], 2 * lo - sub[:, 1] + 2 * k * W, sub[:, 2]]))
        src = np.vstack(src)
        ds, dc = src[:, 0] - b[0], src[:, 1] - b[1]
        r2 = ds * ds + dc * dc
        m = (r2 > 1e-9) & (np.abs(dc) <= C)
        q_img = float(np.sum(src[m, 2] * (ds[m] ** 2 - dc[m] ** 2) / r2[m] ** 2)) + alpha * corr
        ds0, dc0 = sub[:, 0] - b[0], sub[:, 1] - b[1]
        r20 = ds0 * ds0 + dc0 * dc0
        m0 = (r20 > 1e-9) & (r20 <= L * L)
        q_no = float(np.sum(sub[m0, 2] * (ds0[m0] ** 2 - dc0[m0] ** 2) / r20[m0] ** 2))
        out.append((i, q_img, q_no))
    return out


def _selftest_q():
    """한 줄·직사각 격자(해석값 있음)와 무작위 배치(기대값 0)로 layout_q를 점검한다."""
    def exact(a, lx, ly):
        tail = sum(1 / math.sinh(math.pi * m * ly / lx) ** 2 for m in range(1, 60) if math.pi * m * ly / lx < 300)
        return (math.pi * a / lx) ** 2 * (1 / 3 - 2 * tail) - math.pi * a * a / (lx * ly)
    a = 1.0
    for lx, ly, nrow, name in ((3.0, 20.0, 1, "가운데 한 줄(간격 3a, 폭 20a)"), (3.0, 5.236, 4, "직사각 격자 3a × 5.24a, 4줄"),
                               (5.236, 3.0, 4, "가로로 촘촘한 격자 5.24a × 3a, 4줄")):
        W = nrow * ly
        bub = [(j * lx, ly / 2 + kr * ly, a * a, True) for kr in range(nrow) for j in range(-150, 151)]
        res = layout_q(bub, (0.0, W), W, (-150 * lx, 150 * lx), math.pi * a * a / (lx * ly))
        q = np.mean([r[1] for r in res])
        print(f"{name}: Q = {q:.4f}, 해석값 {exact(a, lx, ly):.4f}, 거울상 없는 원 합 {np.mean([r[2] for r in res]):.4f}")
    rng = np.random.default_rng(0)
    W, Ls, al = 20.0, 400.0, 0.1
    pts = []
    while len(pts) < int(al * W * Ls / math.pi):
        p = (rng.uniform(-Ls / 2, Ls / 2), rng.uniform(a, W - a))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= 4 * a * a for q in pts[-300:]):
            pts.append(p)
    res = layout_q([(x, y, a * a, True) for x, y in pts], (0.0, W), W, (-Ls / 2, Ls / 2), math.pi * a * a * len(pts) / (W * Ls))
    qi, qn = np.array([r[1] for r in res]), np.array([r[2] for r in res])
    print(f"고른 무작위(α {al}, {len(res)}개): Q = {qi.mean():.4f} ± {qi.std() / math.sqrt(len(qi)):.4f}(기대 0), "
          f"거울상 없는 원 합 {qn.mean():.4f}(띠 효과로 0과 α 사이)")


def contour_added_mass(per_bubble, pb_meta, masks_dir, flow, max_bubbles=2000, seed=0):
    """masks_dir의 라벨 지도에서 CSV 기포와 짝지은 윤곽의 C_A(I81). 반환: {per_bubble 번호: C_A}."""
    from added_mass_bem import added_mass_from_mask
    by_file = defaultdict(list)
    for k, (fname, cx, cy) in enumerate(pb_meta):
        if fname and cx == cx and cy == cy:
            by_file[os.path.splitext(fname)[0]].append(k)
    files = sorted(by_file)
    rng = np.random.default_rng(seed)
    rng.shuffle(files)
    out, n_try = {}, 0
    for stem in files:
        path = os.path.join(masks_dir, stem + ".npz")
        if not os.path.exists(path):
            continue
        inst = np.load(path)["inst"]
        lab = inst.ravel().astype(np.int64)
        cnt = np.bincount(lab)
        yy, xx = np.indices(inst.shape)
        sx = np.bincount(lab, weights=xx.ravel())
        sy = np.bincount(lab, weights=yy.ravel())
        ids = np.nonzero(cnt)[0]
        ids = ids[ids > 0]
        if not len(ids):
            continue
        cxs, cys = sx[ids] / cnt[ids], sy[ids] / cnt[ids]
        for k in by_file[stem]:
            A_csv = per_bubble[k][0]
            _, cx, cy = pb_meta[k]
            d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
            j = int(np.argmin(d2))
            if d2[j] > 9.0 or not 0.8 <= cnt[ids[j]] / A_csv <= 1.25:
                continue
            ys, xs = np.nonzero(inst == ids[j])
            crop = inst[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == ids[j]
            ca = added_mass_from_mask(crop, flow=flow)
            if ca == ca:
                out[k] = ca
            n_try += 1
        if n_try >= max_bubbles:
            break
    return out


def analyse_point(p):
    H = _f(p["H_mm"]) * 1e-3
    jl, jg = _f(p["jL"]), _f(p["jG"])
    px = _f(p["px_mm"]) * 1e-3
    fps = _f(p["fps"])
    roi = _f(p["roi_area_px"])
    mu = _f(p.get("mu"), float("nan"))
    if mu != mu:
        t0 = _f(p.get("T_tp"))
        mu = mu_water(t0) if t0 == t0 else WATER[0]
    rho = _f(p.get("rho"), WATER[1])
    ax, sgn = axis_of((p.get("flow") or "up").strip())
    rows, speed_col = read_tracking(p["tracking_csv"])

    frames = defaultdict(list)
    for r in rows:
        if r.get("イベント") == "気泡なし" or not r.get("トラックID"):
            frames[int(r["フレーム"])]
            continue
        frames[int(r["フレーム"])].append(r)

    alpha_t, flux_t = [], []
    w_area = w_ba = w_u = w_d = w_w = 0.0
    per_bubble = []                                         # (A, b/a, u) — 기포마다의 예측 y_track용
    pb_meta = []                                            # (파일 이름, 중심 X, 중심 Y) — 윤곽 C_A 짝짓기용
    cross = "X" if ax == "Y" else "Y"
    frame_bub = {}                                          # 프레임 → [(s, c, a², target, per_bubble 번호 또는 −1)]
    frame_alpha = {}
    for f, rs in frames.items():
        a_sum = flux = a_known = 0.0
        fb = frame_bub.setdefault(f, [])
        for r in rs:
            A_px = _f(r.get("面積(px)"), 0.0)
            A_roi = _f(r.get("ROI内面積(px)"), 0.0)
            d = math.sqrt(4 * A_px / math.pi) * px
            if d <= 2 * H or A_roi <= 0:
                continue
            s_c, c_c = _f(r.get(f"中心{ax}")), _f(r.get(f"中心{cross}"))
            k_fb = -1
            if s_c == s_c and c_c == c_c:
                fb.append([s_c, c_c, A_px / math.pi, r.get("フレーム接触") != "1", -1])
                k_fb = len(fb) - 1
            a_sum += A_roi
            v = _f(r.get(speed_col)) if speed_col else float("nan")
            if v == v:
                u = sgn * v * px * fps                       # m/s, 흐름 방향 +
                flux += A_roi * u
                a_known += A_roi
            if r.get("フレーム接触") == "1" or v != v:
                continue
            lead = _f(r.get(f"先端部{ax}"))
            cen = _f(r.get(f"中心{ax}"))
            a_px = abs(cen - lead)
            if not a_px > 0:
                continue
            ba = min(max(A_px / (math.pi * a_px * a_px), 0.2), 5.0)
            w_area += A_px
            w_ba += A_px * ba
            w_u += A_px * u
            w_d += A_px * d
            w_w += A_px * 2 * A_px / (math.pi * a_px) * px
            per_bubble.append((A_px, ba, u))
            pb_meta.append((r.get("ファイル名", ""), _f(r.get("中心X")), _f(r.get("中心Y"))))
            if k_fb >= 0:
                fb[k_fb][4] = len(per_bubble) - 1
        alpha_t.append(a_sum / roi)
        frame_alpha[f] = a_sum / roi
        flux_t.append(flux / roi * (a_sum / a_known) if a_known > 0 else float("nan"))

    # 배치 계수 Q (I74): 측벽 거울상 포함 / 없음
    allb = [b for fb in frame_bub.values() for b in fb]
    walls = (_f(p.get("wall_lo_px")), _f(p.get("wall_hi_px")))
    if not (walls[0] == walls[0] and walls[1] == walls[1]) and allb:
        walls = (min(b[1] - math.sqrt(b[2]) for b in allb), max(b[1] + math.sqrt(b[2]) for b in allb))
        print(f"  [{p['name']}] 경고: 측벽 위치가 없어 기포 가로 끝으로 추정({walls[0]:.0f}~{walls[1]:.0f} px). 시야가 측벽을 포함하지 않으면 Q가 틀린다.")
    q_rows = {"img": [], "noimg": []}
    q_of = {}
    if allb:
        s_rng = (min(b[0] - math.sqrt(b[2]) for b in allb), max(b[0] + math.sqrt(b[2]) for b in allb))
        W_px = walls[1] - walls[0]
        R = _f(p.get("q_radius_px"))
        if not R == R:
            R = min(W_px, (s_rng[1] - s_rng[0]) / 3)
        for f, fb in frame_bub.items():
            bl = [(b[0], b[1], b[2], b[3]) for b in fb]
            for i, q, qn in layout_q(bl, walls, R, s_rng, frame_alpha[f]):
                q_rows["img"].append((math.pi * fb[i][2], q))
                q_rows["noimg"].append((math.pi * fb[i][2], qn))
                if fb[i][4] >= 0:
                    q_of[fb[i][4]] = q
    def _wmean(v):
        return sum(A * q for A, q in v) / sum(A for A, _ in v) if v else float("nan")
    Q, Q_noimg = _wmean(q_rows["img"]), _wmean(q_rows["noimg"])

    alpha = float(np.mean(alpha_t)) if alpha_t else float("nan")
    jg_img = float(np.nanmean(flux_t)) if flux_t else float("nan")
    B = jg / jl
    B_f = jg_img / jl
    kappa = (1 - alpha) / alpha if alpha > 0 else float("nan")
    s_bar, s_bar_t = B * kappa, B_f * kappa
    dp_l = _f(p["dp_l"])
    t_tp, t_l = _f(p.get("T_tp")), _f(p.get("T_l"))
    if t_tp == t_tp and t_l == t_l:
        dp_l *= mu_water(t_tp) / mu_water(t_l)           # 수온 1 K 차이 = 약 2.4 %
    E = _f(p["dp_tp"]) / dp_l - 1
    y = E * kappa
    x = 1 - s_bar
    ba = w_ba / w_area if w_area else float("nan")
    u_b = w_u / w_area if w_area else float("nan")
    d_bar = w_d / w_area if w_area else float("nan")
    w_b = w_w / w_area if w_area else float("nan")
    u_l = jl / (1 - alpha)
    re_b = rho * H * H * u_b * u_b / (mu * w_b * u_l) if w_area else float("nan")
    lam = rho * u_l * H * H / (10 * mu * d_bar) if w_area else float("nan")
    # 기포마다: s_i = u_i/U_m(U_m = jL/(1 − α)), y_track = ΣA_i[1 + (b/a)_i(1 − s_i)]/ΣA_i (유량계 없이, 모양–이동도 상관 포함)
    y_track = (sum(A * (1 + ba_i * (1 - u / u_l)) for A, ba_i, u in per_bubble) / sum(A for A, _, _ in per_bubble)
               if per_bubble else float("nan"))
    # 윤곽 C_A(I81): masks_dir가 있으면 경계요소로, 같은 기포들의 b/a 추정기 값과 함께
    ca_of = {}
    mdir = (p.get("masks_dir") or "").strip()
    if mdir:
        mx = int(_f(p.get("ca_max_bubbles"), 2000))
        ca_of = contour_added_mass(per_bubble, pb_meta, mdir, (p.get("flow") or "up").strip(), max_bubbles=mx)
        if not ca_of:
            print(f"  [{p['name']}] 경고: {mdir}에서 CSV 기포와 짝지은 윤곽이 없다(파일 이름·좌표 확인).")
    wsum = sum(per_bubble[k][0] for k in ca_of)
    C_A = sum(per_bubble[k][0] * c for k, c in ca_of.items()) / wsum if ca_of else float("nan")
    ba_m = sum(per_bubble[k][0] * per_bubble[k][1] for k in ca_of) / wsum if ca_of else float("nan")
    shape = C_A if C_A == C_A else ba
    # 배치를 넣은 예측(I74): 기울기 C_A − 2Q/(1 − α), 평균 꼴은 λ = −x로 2λQ/(1 − α − λQ)
    slope = shape - 2 * Q / (1 - alpha)
    y_layout = 1 + shape * x + 2 * (-x) * Q / (1 - alpha + x * Q)
    qb = [(per_bubble[k], ca_of.get(k, per_bubble[k][1]), q) for k, q in q_of.items()]
    y_track_layout = (sum(A * (1 + (c_i - 2 * q / (1 - alpha)) * (1 - u / u_l)) for (A, _, u), c_i, q in qb) / sum(A for (A, _, _), _, _ in qb)
                      if qb else float("nan"))
    return {
        "name": p["name"], "H_mm": H * 1e3, "alpha": alpha, "B": B, "B_f": B_f, "s_bar": s_bar, "s_bar_T": s_bar_t,
        "E": E, "x": x, "y": y, "b_over_a": ba,
        "y_circle": 1 + x, "y_shape": 1 + ba * x, "y_track": y_track, "y_separated": 1.0, "y_homogeneous": 1 - x,
        "C_A": C_A, "b_over_a_matched": ba_m, "C_A_bubbles": len(ca_of), "y_shape_CA": 1 + C_A * x,
        "Q": Q, "Q_noimg": Q_noimg, "Q_bubbles": len(q_rows["img"]), "slope_pred": slope, "y_layout": y_layout,
        "y_track_layout": y_track_layout,
        "u_bubble": u_b, "d_bar_mm": d_bar * 1e3, "Re_B": re_b, "Lambda": lam, "frames": len(alpha_t),
    }


def plot(results, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink2, muted, grid, surf = "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
    s1, s2, s3 = "#2a78d6", "#eb6834", "#1baf7a"
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    fig.patch.set_facecolor(surf); ax.set_facecolor(surf)
    xs = np.linspace(-1.1, 1.1, 50)
    ax.plot(xs, 1 + xs, color=s1, lw=2, label="circular closure y = 1 + x")
    ax.plot(xs, np.ones_like(xs), color=s2, lw=2, label="separated model y = 1")
    ax.plot(xs, 1 - xs, color=s3, lw=2, label="homogeneous y = 1 − x")
    for r in results:
        ax.plot(r["x"], r["y"], "o", ms=8, color="#0b0b0b", mec=surf, mew=2, zorder=5)
        ax.plot(r["x"], r["y_shape"], "o", ms=7, color=surf, mec=s1, mew=1.6, zorder=4)
        ax.plot([r["x"], r["x"]], [r["y"], r["y_shape"]], color=muted, lw=0.8, zorder=3)
        ax.annotate(r["name"], (r["x"], r["y"]), xytext=(5, 4), textcoords="offset points", fontsize=7.5, color=ink2)
    ax.plot([], [], "o", ms=8, color="#0b0b0b", label="measured (pressure + imaged α)")
    ax.plot([], [], "o", ms=7, color=surf, mec=s1, mew=1.6, label="closure with imaged b/a")
    ax.set_xlabel("x = 1 − s̄  (s̄ = B(1 − α)/α)", color=ink2)
    ax.set_ylabel("y = E(1 − α)/α", color=ink2)
    ax.grid(color=grid, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_demo(out):
    """원형이 아닌 기포(b/a 1.5)가 s 1.5로 움직이는 합성 자료 3점. 계산이 입력을 되돌려 주는지 본다.
    기포는 겹치지 않게 고르게 놓아 배치 계수 Q ≈ 0이다(합성 E에는 배치 효과를 넣지 않았다).
    처음 6프레임은 라벨 지도(masks_k/f<프레임>.npz)도 써서 윤곽 C_A 경로를 점검한다(타원이라 C_A = b/a)."""
    rng = np.random.default_rng(1)
    os.makedirs(out, exist_ok=True)
    H, px, fps, W, Hpx = 0.3e-3, 0.02e-3, 500.0, 1000, 1000
    pts = []
    for k, (alpha_t, ba_t, s_t, jl) in enumerate(((0.10, 1.5, 1.5, 0.05), (0.15, 1.5, 1.2, 0.05), (0.20, 1.0, 0.8, 0.05))):
        rows = []
        u_l = jl / (1 - alpha_t)
        v_px = s_t * u_l / (px * fps)
        mdir = os.path.join(out, f"masks_{k}")
        os.makedirs(mdir, exist_ok=True)
        for f in range(60):
            area_sum = 0.0
            tid = 0
            placed = np.empty((0, 3))                       # 겹치지 않게(배치 계수 Q가 0 근처가 되도록) 놓는다
            inst = np.zeros((Hpx, W), np.int32) if f < 6 else None
            while area_sum < alpha_t * W * Hpx:
                a = rng.uniform(15, 30)                     # 흐름 방향 반축(px) → d > 2H(= 30 px)
                b = ba_t * a
                A = math.pi * a * b
                cx, cy = rng.uniform(b, W - b), rng.uniform(a, Hpx - a)
                rmax = max(a, b)
                if len(placed) and np.any(np.hypot(placed[:, 0] - cx, placed[:, 1] - cy) < placed[:, 2] + rmax):
                    continue
                placed = np.vstack([placed, (cx, cy, rmax)])
                if inst is not None:                        # 흐름(위) 방향 반축 a는 y, 가로 반축 b는 x
                    x0, x1 = int(max(cx - b - 1, 0)), int(min(cx + b + 2, W))
                    y0, y1 = int(max(cy - a - 1, 0)), int(min(cy + a + 2, Hpx))
                    yy, xx = np.mgrid[y0:y1, x0:x1]
                    m = ((xx - cx) / b) ** 2 + ((yy - cy) / a) ** 2 <= 1.0
                    inst[y0:y1, x0:x1][m] = tid + 1
                    A = float(m.sum())
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": tid, "イベント": "", "親トラックID": "",
                             "面積(px)": f"{A:.0f}", "ROI内面積(px)": f"{A:.0f}", "先端部X": f"{cx:.2f}", "先端部Y": f"{cy - a:.2f}",
                             "中心X": f"{cx:.2f}", "中心Y": f"{cy:.2f}", "上昇速度(px/frame)": f"{-v_px:.3f}",
                             "周長(px)": "", "フレーム接触": "0"})
                area_sum += A
                tid += 1
            if inst is not None:
                np.savez_compressed(os.path.join(mdir, f"f{f}.npz"), inst=inst)
        path = os.path.join(out, f"demo_tracking_{k}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        jg = s_t * alpha_t / (1 - alpha_t) * jl
        E = alpha_t / (1 - alpha_t) + ba_t * alpha_t * (1 - s_t) / (1 - alpha_t)
        pts.append({"name": f"demo{k} (b/a {ba_t}, s {s_t})", "H_mm": 0.3, "jL": jl, "jG": jg, "dp_tp": 100 * (1 + E), "dp_l": 100,
                    "tracking_csv": path, "roi_area_px": W * Hpx, "px_mm": px * 1e3, "fps": fps, "flow": "up", "mu": "", "rho": "",
                    "wall_lo_px": 0, "wall_hi_px": W, "masks_dir": mdir})
    pfile = os.path.join(out, "demo_points.csv")
    with open(pfile, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader(); w.writerows(pts)
    return pfile


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("points", nargs="?")
    ap.add_argument("--out", default="plane_out")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--selftest-q", action="store_true")
    a = ap.parse_args()
    if a.selftest_q:
        _selftest_q()
        return
    os.makedirs(a.out, exist_ok=True)
    pfile = make_demo(a.out) if a.demo else a.points
    with open(pfile, encoding="utf-8-sig", newline="") as fh:
        pts = list(csv.DictReader(fh))
    res = [analyse_point(p) for p in pts]
    keys = list(res[0].keys())
    with open(os.path.join(a.out, "plane_points.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in res:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})
    plot(res, os.path.join(a.out, "plane.png"))
    for r in res:
        print(f"{r['name']}: α {r['alpha']:.3f}, b/a {r['b_over_a']:.2f}, s̄ {r['s_bar']:.2f} (추적 {r['s_bar_T']:.2f}), "
              f"x {r['x']:.2f}, y {r['y']:.2f} (원형 {r['y_circle']:.2f}, 모양 {r['y_shape']:.2f}, 기포별 {r['y_track']:.2f}), Re_B {r['Re_B']:.2f}, Λ {r['Lambda']:.3f}")
        if r["C_A_bubbles"]:
            print(f"    윤곽 C_A {r['C_A']:.2f}(같은 {r['C_A_bubbles']}개 기포의 b/a 추정기 {r['b_over_a_matched']:.2f})")
        print(f"    배치 Q {r['Q']:.3f}(거울상 없음 {r['Q_noimg']:.3f}, 기포 {r['Q_bubbles']}개), 예측 기울기 {r['slope_pred']:.2f}, "
              f"배치 넣은 예측 y {r['y_layout']:.2f}(기포별 {r['y_track_layout']:.2f})")


if __name__ == "__main__":
    main()

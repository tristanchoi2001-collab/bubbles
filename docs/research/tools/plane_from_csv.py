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

계산 (모두 "갭을 채운 기포", 즉 등가직경 d > 2H만 쓴다)
    α        프레임마다 Σ ROI内面積 / ROI 면적의 평균
    b/a      화면 끝에 닿지 않은 기포마다 a = |중심 − 앞끝|(흐름 방향 반축), b = A/(π a) → b/a = A/(π a²), 면적 가중 평균
             앞끝은 윤곽 위쪽 5% 점의 평균이라 a가 조금 작게 나와 b/a가 몇 % 크게 나온다.
    s̄        B(1 − α)/α (B = jG/jL, 유량계), s̄_T = B_f(1 − α)/α (B_f = 영상 기체 유량 / jL, 추적)
    E        dp_tp/dp_l − 1,  y = E(1 − α)/α,  x = 1 − s̄
    예측     원형 폐합 y = 1 + x, 모양 폐합 y = 1 + (b/a)x, 분리류 y = 1, 균질류 y = 1 − x
             기포별 y_track = ΣA_i[1 + (b/a)_i(1 − s_i)]/ΣA_i, s_i = u_i(1 − α)/jL (추적 속도, 유량계 불필요)
    Re_B     ρH²u_B²/(μ w_B u_L) (Moriyama & Inoue 1993), Λ = ρ u_L H²/(10 μ d̄)
쐐기 보정(β_f)과 배치 보정(I74)은 넣지 않았다. 숫자를 논문에 쓰기 전에 윤곽 규약(I48)과 기체 유량 폐합으로 α를 점검한다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

WATER = (1.0e-3, 998.0)
COLS = ["name", "H_mm", "jL", "jG", "dp_tp", "dp_l", "tracking_csv", "roi_area_px", "px_mm", "fps", "flow", "mu", "rho"]


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


def analyse_point(p):
    H = _f(p["H_mm"]) * 1e-3
    jl, jg = _f(p["jL"]), _f(p["jG"])
    px = _f(p["px_mm"]) * 1e-3
    fps = _f(p["fps"])
    roi = _f(p["roi_area_px"])
    mu = _f(p.get("mu"), WATER[0])
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
    for f, rs in frames.items():
        a_sum = flux = a_known = 0.0
        for r in rs:
            A_px = _f(r.get("面積(px)"), 0.0)
            A_roi = _f(r.get("ROI内面積(px)"), 0.0)
            d = math.sqrt(4 * A_px / math.pi) * px
            if d <= 2 * H or A_roi <= 0:
                continue
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
        alpha_t.append(a_sum / roi)
        flux_t.append(flux / roi * (a_sum / a_known) if a_known > 0 else float("nan"))

    alpha = float(np.mean(alpha_t)) if alpha_t else float("nan")
    jg_img = float(np.nanmean(flux_t)) if flux_t else float("nan")
    B = jg / jl
    B_f = jg_img / jl
    kappa = (1 - alpha) / alpha if alpha > 0 else float("nan")
    s_bar, s_bar_t = B * kappa, B_f * kappa
    E = _f(p["dp_tp"]) / _f(p["dp_l"]) - 1
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
    return {
        "name": p["name"], "H_mm": H * 1e3, "alpha": alpha, "B": B, "B_f": B_f, "s_bar": s_bar, "s_bar_T": s_bar_t,
        "E": E, "x": x, "y": y, "b_over_a": ba,
        "y_circle": 1 + x, "y_shape": 1 + ba * x, "y_track": y_track, "y_separated": 1.0, "y_homogeneous": 1 - x,
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
    """원형이 아닌 기포(b/a 1.5)가 s 1.5로 움직이는 합성 자료 3점. 계산이 입력을 되돌려 주는지 본다."""
    rng = np.random.default_rng(1)
    os.makedirs(out, exist_ok=True)
    H, px, fps, W, Hpx = 0.3e-3, 0.02e-3, 500.0, 1000, 1000
    pts = []
    for k, (alpha_t, ba_t, s_t, jl) in enumerate(((0.10, 1.5, 1.5, 0.05), (0.15, 1.5, 1.2, 0.05), (0.20, 1.0, 0.8, 0.05))):
        rows = []
        u_l = jl / (1 - alpha_t)
        v_px = s_t * u_l / (px * fps)
        for f in range(60):
            area_sum = 0.0
            tid = 0
            while area_sum < alpha_t * W * Hpx:
                a = rng.uniform(15, 30)                     # 흐름 방향 반축(px) → d > 2H(= 30 px)
                b = ba_t * a
                A = math.pi * a * b
                cx, cy = rng.uniform(b, W - b), rng.uniform(a, Hpx - a)
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": tid, "イベント": "", "親トラックID": "",
                             "面積(px)": f"{A:.0f}", "ROI内面積(px)": f"{A:.0f}", "先端部X": f"{cx:.2f}", "先端部Y": f"{cy - a:.2f}",
                             "中心X": f"{cx:.2f}", "中心Y": f"{cy:.2f}", "上昇速度(px/frame)": f"{-v_px:.3f}",
                             "周長(px)": "", "フレーム接触": "0"})
                area_sum += A
                tid += 1
        path = os.path.join(out, f"demo_tracking_{k}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        jg = s_t * alpha_t / (1 - alpha_t) * jl
        E = alpha_t / (1 - alpha_t) + ba_t * alpha_t * (1 - s_t) / (1 - alpha_t)
        pts.append({"name": f"demo{k} (b/a {ba_t}, s {s_t})", "H_mm": 0.3, "jL": jl, "jG": jg, "dp_tp": 100 * (1 + E), "dp_l": 100,
                    "tracking_csv": path, "roi_area_px": W * Hpx, "px_mm": px * 1e3, "fps": fps, "flow": "up", "mu": "", "rho": ""})
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
    a = ap.parse_args()
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


if __name__ == "__main__":
    main()

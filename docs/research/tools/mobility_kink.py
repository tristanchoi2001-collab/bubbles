"""운전점(유속)마다 크기–속도 곡선이 Booth 곡선에서 아래로 꺾이는 크기 d_k를 찾아 (크기, 속도) 평면에 건조 경계를 그린다(아이디어 I112).

배경
    깨끗한(젖은) 팬케이크의 이동도 s = V/U는 Booth 관계 s^(2/3)/(2 − s) = δ_B/f, δ_B = 1.12·(d/H)·Ca_U^(1/3)(Ca_U = μU/σ)를 따라
    크기와 함께 매끈하게 오른다(I91·I104). f는 마찰 배율(오염). 발자국 일부가 마르면 접촉선 마찰이 생겨 그 크기부터 V가 이 곡선
    아래로 꺾인다. 꺾임 크기 d_k를 유속 4~6개에서 이으면 경계의 모양이 원인을 가른다(I112, 그림 r21).
      - 세로(유속 아래로 모든 크기가 마름): 거칠기 뚫음 V_c ∝ H^(−3/2) 또는 강제 풀림 V*(H 무관). 이때는 젖은 구간이 없어
        맞춘 f가 갑자기 커진다 → 운전점별 f의 계단으로 본다.
      - 기울어진 곡선 d_k ∝ V^(1.7~2): 늦은 터짐(막 배수·풀림). 가열에서 1/q로 움직이면 증발 얇아짐.

계산
    1. 트랙마다 흐름 방향 속도(중심 위치의 k프레임 차분 중앙값, 화면 끝 접촉·사건 프레임 제외)와 크기(온전한 프레임 면적의 중앙값 →
       등가 지름 d)를 낸다. 관측이 --min_obs 미만인 트랙은 뺀다.
    2. d/H 로그 구간별 중앙값 V(d)와 트랙 부트스트랩 구간.
    3. 작은 쪽 구간(아래 30%, 적어도 2개)을 젖었다고 보고 V(d) = U·s(δ_B(d; U)/f)에서 f를 맞춘다. **U는 운전표의 U_loc(m/s)으로
       고정한다**(I111의 U_loc = V̄/(1 + λ), 또는 j_L/(1 − α)). U와 f를 함께 맞추면 작은 기포(δ ≪ 1)에서 s ≈ (2δ)^(3/2)라
       V ∝ (U/f)^(3/2)·d^(3/2)로 U/f 한 묶음만 정해진다(자가 시험에서 U 0.002·f 0.28 같은 엉뚱한 해) → `--fit_U`일 때만 허용.
    4. 비 r(d) = V_측정/V_맞춤이 1 − --thr(기본 0.1) 아래로 내려가 다음 구간까지 이어지는 첫 구간의 중심 = d_k. 부트스트랩으로 구간.
    5. 운전점들의 (V_k = d_k에서 맞춘 곡선의 V, d_k)를 로그–로그로 맞춰 기울기 β를 낸다(β 1.7~2면 늦은 터짐, 꺾임 없이 f만 뛰면 세로).

쓰는 법
    python mobility_kink.py runs.csv --out mk_out
        runs.csv 열: name, tracking_csv, px_mm(mm/px), fps, H_mm, flow(up/down/right/left), [U_loc(m/s)], [q_Wcm2]
    python mobility_kink.py --demo --out mk_demo      # 합성: 늦은 터짐 경계(기울기 1.85)와 세로 경계를 되찾는지 점검
출력: mk_runs.csv(운전점별 U, f, d_k와 구간), mk_bins.csv(구간별 V·맞춤·비), mk_plane.png, 요약.
주의: 꺾임은 마름 말고도 폭 채움(I95), 겹침, 측벽, 홈 고정(I96)에서도 생긴다 → 같은 구분에서 R(I100·I111)·멈춘 이완(I107)·
      뒤 끌림(I109)이 함께 바뀌는지로 확인한다(velocity_links 7절). Booth 관계는 원형·깊이 평균 Darcy·깨끗한 막 꼴이다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

MU, SIG = 1.0e-3, 0.072


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def _s_table(n=4001):
    """s^(2/3)/(2 − s) = δ의 해를 log δ 격자에서 한 번 풀어 둔다(이분법)."""
    ld = np.linspace(np.log(1e-5), np.log(1e5), n)
    dl = np.exp(ld)
    lo, hi = np.full_like(dl, 1e-12), np.full_like(dl, 2 - 1e-12)
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        big = mid ** (2 / 3) / (2 - mid) > dl
        hi = np.where(big, mid, hi)
        lo = np.where(big, lo, mid)
    return ld, 0.5 * (lo + hi)


_LD, _ST = _s_table()


def s_booth(delta):
    """s^(2/3)/(2 − s) = delta(0 < s < 2). 미리 푼 표를 log δ로 보간(상대 오차 < 1e-4). 배열 가능."""
    return np.interp(np.log(np.clip(np.asarray(delta, float), 1e-5, 1e5)), _LD, _ST)


def v_model(d_over_H, U, f, mu=MU, sig=SIG):
    """젖은 막 Booth 곡선의 기포 속도 V = U·s(1.12·(d/H)·Ca_U^(1/3)/f)."""
    delta = 1.12 * np.asarray(d_over_H, float) * (mu * U / sig) ** (1 / 3) / f
    return U * s_booth(delta)


def read_tracks(path, flow, px_mm, fps, H_mm, k=2, min_obs=6, stop_rel=0.25):
    """트랙마다 (ID, 등가 지름/H, 흐름 방향 속도 m/s, 멈춤 비율, 한 프레임 이동의 변동 계수). 화면 끝 접촉·사건(new/merge/split)
    프레임과 merged_into 행은 뺀다. 멈춤 비율 = 한 프레임 이동이 그 트랙 중앙값의 stop_rel배 아래인 비율(I114: 마른 접촉선의
    멈춤–출발. 젖은 막은 매끈해 거의 0)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ax, sgn = axis_of(flow)
    px_m = px_mm * 1e-3
    H_px = H_mm / px_mm
    tr = defaultdict(dict)
    for r in rows:
        tid = r.get("トラックID")
        ev = r.get("イベント") or ""
        if not tid or ev == "気泡なし" or ev.startswith("merged_into"):
            continue
        A = _f(r.get("面積(px)"))
        c = _f(r.get(f"中心{ax}"))
        if not (A > 0 and c == c):
            continue
        tr[tid][int(r["フレーム"])] = (sgn * c, A, r.get("フレーム接触") == "1", ev in ("new", "merge", "split"))
    out = []
    for tid, fr in tr.items():
        fs = sorted(fr)
        vs = []
        for f in fs:
            if f - k in fr and f + k in fr and not any(fr[g][2] or fr[g][3] for g in (f - k, f, f + k)):
                vs.append((fr[f + k][0] - fr[f - k][0]) / (2 * k))
        areas = [fr[f][1] for f in fs if not fr[f][2]]
        if len(vs) < min_obs or not areas:
            continue
        d_px = math.sqrt(4 * float(np.median(areas)) / math.pi)
        dx = np.array([fr[f][0] - fr[f - 1][0] for f in fs if f - 1 in fr and not any(fr[g][2] or fr[g][3] for g in (f - 1, f))])
        if len(dx) >= min_obs and np.median(dx) > 0:
            md = float(np.median(dx))
            stop = float(np.mean(dx < stop_rel * md))
            cv = float(np.std(dx) / np.mean(dx)) if np.mean(dx) > 0 else float("nan")
        else:
            stop = cv = float("nan")
        out.append((tid, d_px / H_px, float(np.median(vs)) * px_m * fps, stop, cv))
    return out


def fit_wet(dH, V, U_fixed=None):
    """젖은 구간 중앙값 (dH, V)에 (U, f)를 로그 잔차 최소로 맞춘다(거친 격자 → 그 둘레 고운 격자, 벡터화). U_fixed면 f만."""
    dH = np.asarray(dH, float); V = np.asarray(V, float)
    lv = np.log(V)

    def search(Us, fs):
        Ug, fg = np.meshgrid(Us, fs, indexing="ij")
        delta = 1.12 * dH[None, None, :] * (MU * Ug[..., None] / SIG) ** (1 / 3) / fg[..., None]
        r = lv[None, None, :] - np.log(Ug[..., None] * s_booth(delta))
        sse = (r * r).sum(-1)
        i, j = np.unravel_index(int(np.argmin(sse)), sse.shape)
        return Us[i], fs[j]
    fs = np.exp(np.linspace(np.log(0.3), np.log(30), 61))
    Us = np.array([U_fixed]) if U_fixed else np.exp(np.linspace(np.log(max(V.min() * 0.2, 1e-4)), np.log(V.max() * 5), 61))
    U, f = search(Us, fs)
    fs2 = f * np.exp(np.linspace(-0.08, 0.08, 33))
    Us2 = np.array([U_fixed]) if U_fixed else U * np.exp(np.linspace(-0.08, 0.08, 33))
    U, f = search(Us2, fs2)
    return float(U), float(f)


def analyse_run(tracks, U, n_bins=10, thr=0.1, n_boot=200, seed=0, min_per_bin=5, s_max_fit=1.6):
    """구간 중앙값 → 구간마다 겉보기 마찰 배율 f_i(Booth 관계를 U로 거꾸로 풂) → 젖은 f는 f_i의 아래 포락선(가장 작은 셋의 중앙값,
    V가 f에 민감한 s < s_max_fit 구간만) → 비 V/V_맞춤 ≥ 1 − thr인 가장 긴 연속 구간이 젖은 창 → 창의 아래·위 끝이 꺾임 d_k1·d_k2.
    느린 작은 기포(얇은 막)와 긴 큰 기포(긴 머무름)가 둘 다 마를 수 있어 꺾임이 양쪽에 생길 수 있다."""
    rng = np.random.default_rng(seed)
    dh = np.array([t[1] for t in tracks]); v = np.array([t[2] for t in tracks])
    ok = v > 0
    dh, v = dh[ok], v[ok]
    if len(dh) < 3 * min_per_bin:
        return None
    edges = np.exp(np.linspace(np.log(dh.min()), np.log(dh.max() * 1.0001), n_bins + 1))
    cau = (MU * U / SIG) ** (1 / 3)

    def one(dh_, v_):
        cen, med = [], []
        for i in range(n_bins):
            m = (dh_ >= edges[i]) & (dh_ < edges[i + 1])
            if m.sum() >= min_per_bin:
                cen.append(float(np.exp(np.mean(np.log(dh_[m]))))); med.append(float(np.median(v_[m])))
        cen, med = np.array(cen), np.array(med)
        nan = float("nan")
        if len(cen) < 4:
            return nan, nan, nan, cen, med, np.full(len(cen), nan), np.full(len(cen), nan), False
        s_i = med / U
        fi = np.full(len(cen), np.inf)
        good = (s_i > 0) & (s_i < 2)
        dl = s_i[good] ** (2 / 3) / (2 - s_i[good])
        fi[good] = 1.12 * cen[good] * cau / dl
        cand = np.where(good & (s_i < s_max_fit))[0]
        if len(cand) < 2:
            cand = np.where(good)[0]
        if len(cand) == 0:
            return nan, nan, nan, cen, med, fi, np.full(len(cen), nan), True
        low = np.sort(fi[cand])[:max(2, min(3, len(cand)))]
        f_wet = float(np.median(low))
        ratio = med / v_model(cen, U, f_wet)
        wet = ratio >= 1 - thr
        best, cur, start = (0, -1, -1), 0, 0
        for i, w in enumerate(wet):
            if w:
                if cur == 0:
                    start = i
                cur += 1
                if cur > best[0]:
                    best = (cur, start, i)
            else:
                cur = 0
        if best[0] == 0:
            return f_wet, nan, nan, cen, med, fi, ratio, True
        _, a0, a1 = best
        dk1 = float(math.sqrt(cen[a0 - 1] * cen[a0])) if a0 > 0 else nan
        dk2 = float(math.sqrt(cen[a1] * cen[a1 + 1])) if a1 < len(cen) - 1 else nan
        return f_wet, dk1, dk2, cen, med, fi, ratio, False
    f_wet, dk1, dk2, cen, med, fi, ratio, all_dry = one(dh, v)
    st = np.array([t[3] for t in tracks])[ok]; cvs = np.array([t[4] for t in tracks])[ok]
    stop_b, cv_b = [], []
    for i in range(n_bins):                               # 구간별 간헐성(I114): 꺾임과 같은 구간에서 함께 커져야 마름
        m = (dh >= edges[i]) & (dh < edges[i + 1])
        if m.sum() >= min_per_bin:
            stop_b.append(float(np.nanmedian(st[m]))); cv_b.append(float(np.nanmedian(cvs[m])))
    b1, b2 = [], []
    for _ in range(n_boot):
        ii = rng.integers(0, len(dh), len(dh))
        r = one(dh[ii], v[ii])
        b1.append(r[1]); b2.append(r[2])

    def ci(b):
        b = np.array([x for x in b if x == x])
        return (tuple(np.percentile(b, [2.5, 97.5])) if len(b) > 10 else (float("nan"), float("nan"))), len(b) / max(n_boot, 1)
    (l1, h1), p1 = ci(b1)
    (l2, h2), p2 = ci(b2)
    return dict(U=U, f=f_wet, all_dry=all_dry, d_k1=dk1, d_k1_lo=float(l1), d_k1_hi=float(h1), p_k1=p1,
                d_k2=dk2, d_k2_lo=float(l2), d_k2_hi=float(h2), p_k2=p2, n_tracks=len(dh),
                bins=list(zip(cen.tolist(), med.tolist(), fi.tolist(), ratio.tolist(), stop_b, cv_b)))


def boundary_slope(points):
    """(V_k, d_k) 로그–로그 기울기와 부트스트랩 구간(운전점 다시 뽑기)."""
    p = [(vk, dk) for vk, dk in points if vk > 0 and dk > 0 and vk == vk and dk == dk]
    if len(p) < 3:
        return float("nan"), float("nan"), float("nan")
    x = np.log([q[0] for q in p]); y = np.log([q[1] for q in p])
    b = float(np.polyfit(x, y, 1)[0])
    rng = np.random.default_rng(1)
    bs = []
    for _ in range(500):
        ii = rng.integers(0, len(p), len(p))
        if np.ptp(x[ii]) > 0:
            bs.append(np.polyfit(x[ii], y[ii], 1)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (float("nan"), float("nan"))
    return b, float(lo), float(hi)


def make_demo(out, seed=7):
    """합성 운전점 5개 × 트랙 400개(1 mm 갭, 0.02 mm/px, 500 fps, 위치 잡음 0.3 px, 트랙마다 ±4%). 젖은 막: Booth 곡선(f 1.3).
    마른 기포는 접촉선 마찰로 V × 0.55. 마름 판정은 그 기포의 젖은 속도 V로 한다.
    (가) 늦은 터짐: d > d_w(V) = 20 mm·(V/0.05 m/s)^1.85 → 느린 작은 기포와 긴 큰 기포가 둘 다 마른다(양쪽 꺾임).
    (나) 세로 경계: V < V_c = 0.03 m/s → 느린 작은 기포만 마른다(아래 꺾임의 V_k가 모두 V_c).
    U_loc은 참값에 ±5% 오차를 넣어 준다(I111·유량계의 정밀도 수준)."""
    rng = np.random.default_rng(seed)
    H_mm, px_mm, fps = 1.0, 0.02, 500.0
    runs = []
    for case in ("late", "vertical"):
        for U in ((0.045, 0.05, 0.055, 0.065, 0.075) if case == "late" else (0.02, 0.03, 0.04, 0.06, 0.1)):
            rows = []
            for t in range(400):
                d_mm = math.exp(rng.uniform(math.log(2.0), math.log(60.0)))
                V = float(v_model([d_mm / H_mm], U, 1.3)[0])
                dry = d_mm > 20.0 * (V / 0.05) ** 1.85 if case == "late" else V < 0.03
                if dry:
                    V *= 0.55
                V *= 1 + 0.04 * rng.standard_normal()
                v_px = V / (px_mm * 1e-3 * fps)
                a_px = d_mm / px_mm / 2
                x = 100.0
                for kk in range(12):
                    if kk:                                    # 마른 기포는 멈춤–출발(프레임의 30% 멈춤, 평균 속도는 같게)
                        x += (0.0 if rng.random() < 0.3 else v_px / 0.7) if dry else v_px
                    xo = x + rng.normal(0, 0.3)
                    rows.append({"ファイル名": f"f{t}_{kk}.png", "フレーム": t * 20 + kk, "トラックID": f"{t + 1}",
                                 "イベント": "new" if kk == 0 else "normal", "面積(px)": f"{math.pi * a_px * a_px:.1f}",
                                 "中心X": f"{xo:.3f}", "中心Y": "500", "フレーム接触": "0"})
            sub = os.path.join(out, f"{case}_U{U:g}")
            os.makedirs(sub, exist_ok=True)
            path = os.path.join(sub, "result_tracking.csv")
            with open(path, "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
            runs.append(dict(name=f"{case}_U{U:g}", tracking_csv=path, px_mm=px_mm, fps=fps, H_mm=H_mm, flow="right", case=case, U_true=U,
                             U_loc=U * (1 + 0.05 * rng.uniform(-1, 1))))
    return runs


def run_table(runs, out, n_boot=200, fit_U=False):
    os.makedirs(out, exist_ok=True)
    res = []
    for r in runs:
        tracks = read_tracks(r["tracking_csv"], r.get("flow", "up"), float(r["px_mm"]), float(r["fps"]), float(r["H_mm"]))
        U = _f(r.get("U_loc"))
        if not U == U:
            if not fit_U:
                print(f"  {r['name']}: U_loc이 없다. 작은 기포에서는 U/f 한 묶음만 정해져 꺾임을 못 믿는다 → U_loc 열(I111의 V̄/(1 + λ) 또는"
                      " j_L/(1 − α), m/s)을 넣거나 --fit_U로 강제한다.")
                continue
            dh = np.array([t[1] for t in tracks]); vv = np.array([t[2] for t in tracks])
            U, _ = fit_wet(dh[vv > 0], vv[vv > 0])
        a = analyse_run(tracks, U, n_boot=n_boot)
        if a is None:
            print(f"  {r['name']}: 트랙이 너무 적다({len(tracks)}개)")
            continue
        H_mm = float(r["H_mm"])
        row = dict(name=r["name"], q_Wcm2=_f(r.get("q_Wcm2")), n_tracks=a["n_tracks"], U=a["U"], f_wet=a["f"], all_dry=a["all_dry"])
        for k in ("1", "2"):
            dk = a["d_k" + k]
            row["d_k%s_mm" % k] = dk * H_mm
            row["d_k%s_lo_mm" % k], row["d_k%s_hi_mm" % k] = a["d_k%s_lo" % k] * H_mm, a["d_k%s_hi" % k] * H_mm
            row["p_k" + k] = a["p_k" + k]
            row["V_k" + k] = float(v_model([dk], a["U"], a["f"])[0]) if dk == dk and a["f"] == a["f"] else float("nan")
        row["bins"] = a["bins"]
        res.append(row)
    return res


def flag_runs(res, tol=1.3):
    """같은 물·같은 날이면 젖은 f가 운전점마다 같아야 한다. 젖은 f가 운전점 중앙값의 tol배를 넘으면 젖은 창이 좁거나 없는 운전점
    (대부분 마름 → 아래 포락선이 마른 구간에서 나옴)으로 보고 경계 맞춤에서 뺀다."""
    fs = [r["f_wet"] for r in res if r["f_wet"] == r["f_wet"] and not r["all_dry"]]
    if len(fs) < 3:
        return set()
    fm = float(np.median(fs))
    return {r["name"] for r in res if r["all_dry"] or not r["f_wet"] == r["f_wet"] or r["f_wet"] > tol * fm}


def boundary_points(res, skip=frozenset()):
    pts = []
    for r in res:
        if r["name"] in skip:
            continue
        for k in ("1", "2"):
            if r["d_k%s_mm" % k] == r["d_k%s_mm" % k]:
                pts.append((r["V_k" + k], r["d_k%s_mm" % k], k))
    return pts


def report(res, out):
    if not res:
        print("결과 없음")
        return
    keys = [k for k in res[0] if k != "bins"]
    with open(os.path.join(out, "mk_runs.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in res:
            w.writerow({k: (f"{r[k]:.5g}" if isinstance(r[k], float) else r[k]) for k in keys})
    with open(os.path.join(out, "mk_bins.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(["name", "d_over_H", "V_median_mps", "f_apparent", "V_over_wet_fit", "stop_frac", "cv_dx"])
        for r in res:
            for c, m, fi, q, sf, cv in r["bins"]:
                w.writerow([r["name"], f"{c:.4g}", f"{m:.5g}", f"{fi:.4g}", f"{q:.4g}", f"{sf:.3g}", f"{cv:.3g}"])
    for r in res:
        if r["all_dry"]:
            print(f"  {r['name']}: 트랙 {r['n_tracks']}, U {r['U']:.3f} m/s — 젖은 구간 없음(모든 크기가 젖은 곡선 아래; 겉보기 f가 다른 운전점보다 크면 세로 경계 쪽)")
            continue
        parts = []
        for k, side in (("1", "작은 쪽"), ("2", "큰 쪽")):
            if r["d_k%s_mm" % k] == r["d_k%s_mm" % k]:
                parts.append(f"{side} 꺾임 {r['d_k%s_mm' % k]:.1f} mm [{r['d_k%s_lo_mm' % k]:.1f}~{r['d_k%s_hi_mm' % k]:.1f}]"
                             f"(부트스트랩 {r['p_k' + k]:.0%}), V_k {r['V_k' + k]:.3f} m/s")
        print(f"  {r['name']}: 트랙 {r['n_tracks']}, U {r['U']:.3f} m/s, 젖은 f {r['f_wet']:.2f}; " + ("; ".join(parts) if parts else "꺾임 없음(모두 젖음)"))
        sl = [(c, sf, q) for c, m, fi, q, sf, cv in r["bins"] if sf == sf]
        if sl:
            wet_sf = [sf for c, sf, q in sl if q == q and q >= 0.9]; dry_sf = [sf for c, sf, q in sl if q == q and q < 0.9]
            print(f"      멈춤 비율(I114) 중앙값: 젖은 구간 {np.median(wet_sf) if wet_sf else float('nan'):.2f}, 느린(꺾임) 구간 "
                  f"{np.median(dry_sf) if dry_sf else float('nan'):.2f} — 꺾임 구간에서 함께 커지면 접촉선(마름), 그대로면 다른 원인(폭 채움·측벽)")
    skip = flag_runs(res)
    if skip:
        print(f"경계 맞춤에서 뺀 운전점(젖은 f가 중앙값의 1.3배 초과이거나 젖은 구간 없음 → 대부분 마름): {', '.join(sorted(skip))}")
    pts = boundary_points(res, skip)
    b, lo, hi = boundary_slope([(p[0], p[1]) for p in pts])
    if b == b:
        print(f"경계 기울기 d ln d_k / d ln V_k = {b:.2f} [{lo:.2f}~{hi:.2f}](꺾임 {len(pts)}개, 양쪽 모두; 늦은 터짐이면 1.7~2, 증발이면 5/3이고 1/q로 움직임)")
    lowpts = [(p[1], p[0]) for p in pts if p[2] == "1"]
    if len(lowpts) >= 3:
        g, glo, ghi = boundary_slope(lowpts)                 # d ln V_k / d ln d_k (작은 쪽 꺾임만)
        vk = np.array([q[1] for q in lowpts])
        print(f"작은 쪽 꺾임 {len(lowpts)}개: d ln V_k / d ln d_k = {g:.2f} [{glo:.2f}~{ghi:.2f}], V_k 평균 {vk.mean():.3f} m/s. "
              "0이면(V_k가 크기와 무관) 세로 경계: 거칠기 뚫음 V_c 또는 강제 풀림 V*(갭 심으로 가름). 1/α ≈ 0.5~0.6이면 늦은 터짐·증발.")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.6, 4.2))
        for vk, dk, side in pts:
            ax.plot([vk], [dk], "o" if side == "1" else "s", color="#2a78d6" if side == "1" else "#eb6834", ms=6)
        ax.plot([], [], "o", color="#2a78d6", label="small-side kink (slow bubbles dry)")
        ax.plot([], [], "s", color="#eb6834", label="large-side kink (long bubbles dry)")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("wet-curve bubble speed at the kink V_k (m/s)"); ax.set_ylabel("kink size d_k (mm)")
        ax.legend(frameon=False, fontsize=7.5)
        ax.set_title("Drying boundary from mobility kinks (I112)", fontsize=9.5, loc="left")
        fig.tight_layout(); fig.savefig(os.path.join(out, "mk_plane.png"), dpi=150); plt.close(fig)
    except Exception as e:                                # 그림은 선택
        print(f"(그림 생략: {e})")


def _demo(out):
    runs = make_demo(out)
    fails = []
    for case in ("late", "vertical"):
        sub = [r for r in runs if r["case"] == case]
        print(f"[{case}]")
        res = run_table(sub, os.path.join(out, case), n_boot=100)
        report(res, os.path.join(out, case))
        pts = boundary_points(res, flag_runs(res))
        wet_sf = [sf for r in res for c, m, fi, q, sf, cv in r["bins"] if q == q and q >= 0.9 and sf == sf]
        dry_sf = [sf for r in res for c, m, fi, q, sf, cv in r["bins"] if q == q and q < 0.8 and sf == sf]
        ok_i = bool(wet_sf) and bool(dry_sf) and np.median(wet_sf) < 0.08 and np.median(dry_sf) > 0.15
        print(f"  {'통과' if ok_i else '실패'}  I114 간헐성: 멈춤 비율 중앙값 젖은 구간 {np.median(wet_sf) if wet_sf else float('nan'):.3f}(< 0.08), "
              f"느린 구간 {np.median(dry_sf) if dry_sf else float('nan'):.3f}(> 0.15; 참: 마른 기포는 프레임의 30% 멈춤)")
        if not ok_i:
            fails.append(f"{case} intermittency")
        if case == "late":
            b, lo, hi = boundary_slope([(p[0], p[1]) for p in pts])
            lowpts = [(p[1], p[0]) for p in pts if p[2] == "1"]
            g = boundary_slope(lowpts)[0] if len(lowpts) >= 3 else float("nan")
            ok = (b == b and abs(b - 1.85) < 0.35 and len(pts) >= 5 and any(p[2] == "1" for p in pts) and any(p[2] == "2" for p in pts)
                  and g > 0.3)                                # 늦은 터짐은 세로 경계와 구별돼야 한다(참 1/1.85 = 0.54)
            print(f"  {'통과' if ok else '실패'}  늦은 터짐: 양쪽 꺾임 {len(pts)}개가 한 곡선, 기울기 {b:.2f} [{lo:.2f}~{hi:.2f}](참 1.85, 허용 ±0.35),"
                  f" 작은 쪽 d ln V_k/d ln d_k {g:.2f}(참 0.54, > 0.3이어야 세로와 구별)")
            if not ok:
                fails.append("late")
        else:
            lowpts = [(p[1], p[0]) for p in pts if p[2] == "1"]
            g = boundary_slope(lowpts)[0] if len(lowpts) >= 3 else float("nan")
            vk = np.array([q[1] for q in lowpts]) if lowpts else np.array([float("nan")])
            ok = len(lowpts) >= 3 and abs(g) < 0.2 and abs(vk.mean() - 0.03) < 0.0075
            print(f"  {'통과' if ok else '실패'}  세로 경계: 작은 쪽 꺾임 {len(lowpts)}개, d ln V_k/d ln d_k {g:.2f}(|·| < 0.2), V_k 평균 {vk.mean():.3f} m/s(참 V_c 0.030)")
            if not ok:
                fails.append("vertical")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="?", help="운전표 CSV(name, tracking_csv, px_mm, fps, H_mm, flow, [U_loc], [q_Wcm2])")
    ap.add_argument("--out", default="mk_out"); ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--fit_U", action="store_true", help="U_loc 없이 U와 f를 함께 맞춘다(작은 기포만이면 U/f 한 묶음만 정해짐, 권하지 않음)")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not a.runs:
        ap.error("운전표 CSV가 필요하다(또는 --demo)")
    with open(a.runs, encoding="utf-8-sig", newline="") as fh:
        runs = list(csv.DictReader(fh))
    for r in runs:
        if _f(r.get("px_mm")) > 1:
            raise SystemExit(f"{r.get('name')}: px_mm은 화소 하나의 크기(mm/px)다(예 0.02). 1보다 크면 px/mm로 넣은 것 같다.")
    res = run_table(runs, a.out, a.n_boot, fit_U=a.fit_U)
    report(res, a.out)


if __name__ == "__main__":
    main()

"""합체 뒤 모양 이완으로 마찰 지수와 마른 발자국을 읽는다(아이디어 I107).

배경 (원형 근처의 2번 모드 r = a(1 + ε·cos 2θ), 깊이 평균 Darcy)
    되돌리는 힘은 평면 곡률 압력 (π/4)σκ_∥, 막는 힘은 바깥 Darcy 흐름과 메니스커스 마찰이다.
    마찰이 D ∝ V^m이고 마찰이 지배하면 ε̇ = −C·ε^q, q = 1/m이다(m 1: 지수 감쇠, m 2/3: q 1.5로 꼬리 t^(−2), m 1/3: q 3).
    접촉선이 붙은(마른) 발자국이면 남는 변형 ε_r에서 멈춘다: ε̇ = −C·(ε − ε_r)^q.
    Darcy만이면 시간 척도 τ₂ = 8μa³/(πσH²)(q = 1). 실제는 마찰 때문에 더 느리고 꼬리가 길다(I107의 Φ).

쓰는 법
    python merge_relax.py --csv result_tracking.csv --fps 500 --px_mm 0.02 --H_mm 0.3 [--masks_dir OUTPUT_FOLDER/instances] --out mr_out
        [--max_frames 40] [--dH_bins 2,5,15,50] [--quiet 10]
    python merge_relax.py --demo --out mr_demo      # 지수 감쇠 / 거듭제곱 꼬리 / 멈춤을 그린 합성 마스크로 스스로 점검

계산
    1. 합체 사건: イベント == "merge"인 행(합친 쪽 트랙). 그 트랙의 다음 프레임을 다른 사건(merge/split/new)·화면 끝 접촉·빠진
       프레임이 나올 때까지(최대 --max_frames) 따라간다.
    2. 변형 ε: masks_dir가 있으면 그 기포 라벨(중심 3 px·면적 비 0.8~1.25로 짝지음)의 2차 모멘트 고유값으로
       ε = (√λ₁ − √λ₂)/(√λ₁ + √λ₂)(타원이면 (장축 − 단축)/(장축 + 단축)). 없으면 둘레·면적에서 ε ≈ √((P²/(4πA) − 1)/1.5)
       (2번 모드의 등주 부족. 화소 둘레는 치우치므로 아래 기준선이 중요하다).
    3. 기준선: 같은 d/H 구간에서 앞뒤 --quiet 프레임 안에 사건이 없는 조용한 관측의 ε 중앙값(움직이는 기포의 정상 모양 + 화소 효과)을 뺀다.
    4. d/H 구간마다 사건 뒤 프레임별 중앙값 곡선 ε(t)를 3점 평활하고, 위상 평면에서 ln(−ε̇)를 ln(ε − ε_r)에 회귀한다.
       ε_r는 0 ~ 0.95·min ε에서 잔차가 가장 작은 값을 고른다. 기울기 q → m = 1/q, ε_r > 0.05(그리고 잡음의 3배)면 "멈춤".
       같은 곡선의 지수 맞춤 시간 τ와 τ₂(그 구간 평균 반경)의 비도 낸다.
출력: mr_events.csv(사건별 ε 계열), mr_classes.csv(구간별 요약), 요약 출력.
주의: 합체 직후 몇 프레임은 목(neck) 동역학과 관성이 섞인다 → --skip(기본 1)프레임은 맞춤에서 뺀다. 큰 기포는 시야를 빨리 떠난다.
      예상 크기(I107): 0.3 mm에서 τ₂는 d/H 10/20/30이면 1.3/10.6/36 ms라 500 fps에서 d/H ≳ 20만 이완이 몇 프레임 이상 보인다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def eps_from_mask(mask):
    """마스크의 2차 모멘트로 ε = (√λ₁ − √λ₂)/(√λ₁ + √λ₂)."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 5:
        return float("nan")
    x = xs - xs.mean(); y = ys - ys.mean()
    cov = np.array([[np.mean(x * x), np.mean(x * y)], [np.mean(x * y), np.mean(y * y)]])
    l2, l1 = np.linalg.eigvalsh(cov)
    if l2 <= 0:
        return float("nan")
    r1, r2 = math.sqrt(l1), math.sqrt(l2)
    return (r1 - r2) / (r1 + r2)


def eps_from_perimeter(P, A):
    """2번 모드의 등주 부족 P²/(4πA) − 1 ≈ 1.5ε²에서 ε."""
    if not (P > 0 and A > 0):
        return float("nan")
    return math.sqrt(max(P * P / (4 * math.pi * A) - 1.0, 0.0) / 1.5)


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


class MaskLookup:
    """masks_dir의 프레임별 라벨 지도에서 CSV 기포와 짝지은 마스크의 ε."""

    def __init__(self, masks_dir):
        self.dir = masks_dir
        self.cache = {}

    def _load(self, fname):
        stem = os.path.splitext(fname)[0]
        if stem not in self.cache:
            path = os.path.join(self.dir, stem + ".npz")
            if not os.path.exists(path):
                self.cache[stem] = None
            else:
                inst = np.load(path)["inst"]
                lab = inst.ravel().astype(np.int64)
                cnt = np.bincount(lab)
                yy, xx = np.indices(inst.shape)
                sx = np.bincount(lab, weights=xx.ravel()); sy = np.bincount(lab, weights=yy.ravel())
                ids = np.nonzero(cnt)[0]
                ids = ids[ids > 0]
                self.cache[stem] = (inst, ids, sx[ids] / cnt[ids], sy[ids] / cnt[ids], cnt[ids])
            if len(self.cache) > 64:                     # 메모리: 오래된 것을 버린다
                self.cache.pop(next(iter(self.cache)))
        return self.cache[stem]

    def eps(self, fname, cx, cy, A):
        d = self._load(fname)
        if d is None or not len(d[1]):
            return float("nan")
        inst, ids, cxs, cys, cnt = d
        d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
        j = int(np.argmin(d2))
        if d2[j] > 9.0 or not 0.8 <= cnt[j] / A <= 1.25:
            return float("nan")
        return eps_from_mask(inst == ids[j])


def collect(rows, H_px, masks=None, max_frames=40, quiet=10):
    """사건 뒤 ε 계열과 조용한 관측의 기준선 표본."""
    tracks = defaultdict(dict)
    for r in rows:
        tid = r.get("トラックID")
        if not tid or r.get("イベント") == "気泡なし":
            continue
        A = _f(r.get("面積(px)"))
        if not A > 0:
            continue
        tracks[tid][int(r["フレーム"])] = r
    ev_frames = defaultdict(set)
    for tid, fr in tracks.items():
        for f, r in fr.items():
            if r.get("イベント") in ("merge", "split", "new"):
                ev_frames[tid].add(f)

    def eps_of(r):
        """ε²(제곱으로 돌려준다: 기준선을 제곱으로 빼기 위해. 정상 변형·화소 효과와 이완 변형은 방향이 무작위라 평균적으로 제곱으로 더해진다)."""
        A = _f(r.get("面積(px)"))
        if masks is not None:
            e = masks.eps(r.get("ファイル名", ""), _f(r.get("中心X")), _f(r.get("中心Y")), A)
            return e * e if e == e else float("nan")
        P = _f(r.get("周長(px)"))
        return (P * P / (4 * math.pi * A) - 1.0) / 1.5 if P > 0 and A > 0 else float("nan")
    events, quiet_obs = [], []
    for tid, fr in tracks.items():
        evs = ev_frames[tid]
        for f, r in fr.items():
            if r.get("フレーム接触") == "1":
                continue
            dH = math.sqrt(4 * _f(r["面積(px)"]) / math.pi) / H_px
            if r.get("イベント") == "merge":
                ser = []
                for k in range(max_frames + 1):
                    g = f + k
                    q = fr.get(g)
                    if q is None or q.get("フレーム接触") == "1" or (k > 0 and g in evs):
                        break
                    ser.append(eps_of(q))                 # ε²
                if len(ser) >= 4:
                    events.append(dict(track=tid, frame=f, dH=dH, a_px=math.sqrt(_f(r["面積(px)"]) / math.pi), eps=ser))
            elif r.get("イベント") in ("normal", "") and not any(abs(f - e) <= quiet for e in evs):
                quiet_obs.append((dH, eps_of(r)))
    return events, quiet_obs


def phase_plane_fit(t, e, eps_r=0.0, skip=1, floor=0.01, min_pts=6):
    """ε̇ = −C(ε − ε_r)^q를 위상 평면에서 맞춘다(ε_r는 고정). 반환 (q, C, 잔차, 점 수)."""
    e = np.asarray(e, float)
    es = np.convolve(np.pad(e, 1, mode="edge"), np.ones(3) / 3, mode="valid") if len(e) >= 3 else e
    de = np.gradient(es, t)
    x = es - eps_r
    ok = (np.arange(len(es)) >= skip) & (x > floor) & (de < 0)
    if ok.sum() < min_pts:
        return float("nan"), float("nan"), float("nan"), int(ok.sum())
    lx, ly = np.log(x[ok]), np.log(-de[ok])
    A = np.vstack([lx, np.ones_like(lx)]).T
    sol = np.linalg.lstsq(A, ly, rcond=None)[0]
    rms = float(np.sqrt(np.mean((A @ sol - ly) ** 2)))
    return float(sol[0]), float(math.exp(sol[1])), rms, int(ok.sum())


def plateau(e, skip=1):
    """멈춤 판정: 마지막 1/3의 중앙값이 처음 값의 40% 이상이고 0.05 이상이며, 마지막 1/3의 기울기가 처음 1/3 기울기의 20% 미만."""
    e = np.asarray(e, float)
    n = len(e)
    if n < 6:
        return False, float("nan")
    k3 = max(n // 3, 2)
    early, late = e[skip:skip + k3], e[-k3:]
    s_e = abs(np.polyfit(np.arange(len(early)), early, 1)[0]) if len(early) >= 2 else 0.0
    s_l = abs(np.polyfit(np.arange(len(late)), late, 1)[0])
    lv = float(np.median(late))
    return bool(lv >= max(0.05, 0.4 * e[skip]) and s_l < 0.2 * max(s_e, 1e-9)), lv


def analyse(events, quiet_obs, bins, fps, H_m, px_m, mu=1e-3, sigma=0.072, skip=1):
    out = []
    for lo, hi in bins:
        base_v = [e for d, e in quiet_obs if lo <= d < hi and e == e]          # ε² 표본
        base = float(np.median(base_v)) if len(base_v) >= 10 else 0.0
        evs = [ev for ev in events if lo <= ev["dH"] < hi]
        if len(evs) < 3:
            continue
        T = max(len(ev["eps"]) for ev in evs)
        med, nk = [], []
        for k in range(T):
            v = [math.sqrt(max(ev["eps"][k] - base, 0.0)) for ev in evs if k < len(ev["eps"]) and ev["eps"][k] == ev["eps"][k]]
            if len(v) < 3:
                break
            med.append(float(np.median(v))); nk.append(len(v))
        if len(med) < 5:
            continue
        qe = np.sqrt(np.maximum(np.array(base_v) - base, 0.0)) if base_v else np.zeros(1)
        noise = float(max(np.percentile(qe, 75), 0.005) / math.sqrt(max(len(evs), 1)))
        t = np.arange(len(med)) / fps
        pinned, late = plateau(med, skip)
        er = late if pinned else 0.0
        floor = max(3 * noise, 0.02 * med[skip] if len(med) > skip else 0.0, 0.003)
        q, C, rms, npts = phase_plane_fit(t, med, eps_r=(er - 0.5 * floor) if pinned else 0.0, skip=skip, floor=floor)
        e1 = np.array(med[skip:]) - (er - 0.5 * floor if pinned else 0.0); tt = t[skip:]
        okk = e1 > floor
        tau = float(-1 / np.polyfit(tt[okk], np.log(e1[okk]), 1)[0]) if okk.sum() >= 3 else float("nan")
        a_m = float(np.median([ev["a_px"] for ev in evs])) * px_m
        tau2 = 8 * mu * a_m ** 3 / (math.pi * sigma * H_m * H_m)
        out.append(dict(dH_lo=lo, dH_hi=hi, n_events=len(evs), frames=len(med), baseline_eps=math.sqrt(max(base, 0.0)), noise=noise,
                        eps0=med[0], eps_end=med[-1], q=q, m=1 / q if q and q == q else float("nan"), eps_r=er, pinned=int(pinned),
                        fit_rms=rms, fit_points=npts, tau_exp_s=tau, tau2_s=tau2, tau_over_tau2=tau / tau2 if tau2 > 0 else float("nan"),
                        curve=";".join(f"{v:.4f}" for v in med)))
    return out


def make_demo(out, seed=11):
    """합성: 반경 30 px 기포의 합체 뒤 타원 모양 ε(t)를 세 법칙으로 그린 라벨 지도 + CSV.
    (가) 지수 ε = 0.3·e^(−t/6)(m 1), (나) ε̇ = −Cε^1.5(m 2/3, 6프레임에 반), (다) 멈춤 ε = 0.25 + 0.15·e^(−t/4).
    각 법칙 사건 6개(방향 무작위) + 같은 크기 조용한 원형 기포(기준선). d/H 구간을 법칙마다 달리 두어 구간별로 가린다."""
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(out, "instances"), exist_ok=True)
    Hpx = 6.0
    laws = [("exp", 30.0), ("pow", 45.0), ("pin", 70.0)]          # 반경 30/45/70 px → d/H 10/15/23
    rows = []
    frame = 0
    tid = 0

    def law_eps(kind, k):
        if kind == "exp":
            return 0.3 * math.exp(-k / 6)
        if kind == "pow":
            C = 0.828 / (6 * math.sqrt(0.3))
            return (0.3 ** -0.5 + C * k / 2) ** -2
        return 0.25 + 0.15 * math.exp(-k / 4)
    W, Hh = 520, 520
    yy, xx = np.indices((Hh, W))
    for kind, a in laws:
        for rep in range(6):
            tid += 1
            host = tid
            quiet_ids = [tid + 1, tid + 2]
            tid += 2
            ang = rng.uniform(0, math.pi)
            for k in range(0, 36):
                inst = np.zeros((Hh, W), np.uint16)
                fname = f"f{frame:05d}.png"
                e = law_eps(kind, k)
                A_ax = a * math.sqrt((1 + e) / (1 - e)); B_ax = a * math.sqrt((1 - e) / (1 + e))
                cx, cy = 260.0, 200.0
                xr = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
                yr = -(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)
                m = (xr / A_ax) ** 2 + (yr / B_ax) ** 2 <= 1
                inst[m] = 1
                area = int(m.sum())
                h = math.pi * (3 * (A_ax + B_ax) - math.sqrt((3 * A_ax + B_ax) * (A_ax + 3 * B_ax))) * 1.03   # 화소 둘레 치우침 3%
                rows.append({"ファイル名": fname, "フレーム": frame, "トラックID": host, "イベント": "merge" if k == 0 else "normal",
                             "親トラックID": "", "面積(px)": area, "中心X": f"{xx[m].mean():.3f}", "中心Y": f"{yy[m].mean():.3f}",
                             "周長(px)": f"{h:.2f}", "フレーム接触": "0"})
                for j, qid in enumerate(quiet_ids):
                    qx, qy = 130.0 + 260 * j, 420.0
                    mq = (xx - qx) ** 2 + (yy - qy) ** 2 <= (a * 0.999) ** 2
                    if mq.any():
                        inst[mq & (inst == 0)] = 2 + j
                        rows.append({"ファイル名": fname, "フレーム": frame, "トラックID": qid, "イベント": "normal",
                                     "親トラックID": "", "面積(px)": int(mq.sum()), "中心X": f"{xx[mq].mean():.3f}",
                                     "中心Y": f"{yy[mq].mean():.3f}", "周長(px)": f"{2 * math.pi * a * 1.03:.2f}", "フレーム接触": "0"})
                np.savez_compressed(os.path.join(out, "instances", fname.replace(".png", ".npz")), inst=inst)
                frame += 1
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path, Hpx


def _demo(out):
    path, Hpx = make_demo(out)
    rows = read_rows(path)
    bins = ((8, 12), (12, 20), (20, 30))
    fails = []
    for label, masks in (("마스크 2차 모멘트", MaskLookup(os.path.join(out, "instances"))), ("둘레·면적(마스크 없음)", None)):
        events, quiet = collect(rows, Hpx, masks, max_frames=35, quiet=0)
        res = analyse(events, quiet, bins, fps=500.0, H_m=Hpx * 2e-5, px_m=2e-5)
        print(f"[{label}] 사건 {len(events)}개")
        want = {(8, 12): ("지수(m 1)", 1.0, 0.0), (12, 20): ("거듭제곱 꼬리(m 2/3)", 1.5, 0.0), (20, 30): ("멈춤", None, 0.25)}
        for r in res:
            name, q_true, er_true = want[(r["dH_lo"], r["dH_hi"])]
            print(f"  d/H {r['dH_lo']:g}~{r['dH_hi']:g} {name}: 사건 {r['n_events']}, ε0 {r['eps0']:.3f} → 끝 {r['eps_end']:.3f}, "
                  f"q {r['q']:.2f}(m {r['m']:.2f}), ε_r {r['eps_r']:.3f}, 멈춤 {r['pinned']}, τ/τ₂ {r['tau_over_tau2']:.2f}, 맞춤 점 {r['fit_points']}")
            if masks is None:                            # 둘레·면적 경로는 화소 면적 잡음 때문에 ε ≲ 0.05를 못 가른다 → 멈춤 여부만 본다
                ok = (r["pinned"] == 1) == (q_true is None)
            elif q_true is not None:
                ok = abs(r["q"] - q_true) <= 0.3 and not r["pinned"]
            else:
                ok = r["pinned"] == 1 and abs(r["eps_r"] - er_true) <= 0.05
            print(f"  {'통과' if ok else '실패'}  {label}: {name} 판정")
            if not ok:
                fails.append(f"{label} {name}")
        if len(res) != 3:
            fails.append(f"{label}: 구간 {len(res)}개(3개여야 함)")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--px_mm", type=float); ap.add_argument("--H_mm", type=float)
    ap.add_argument("--masks_dir", default="")
    ap.add_argument("--max_frames", type=int, default=40)
    ap.add_argument("--quiet", type=int, default=10, help="기준선: 앞뒤 이 프레임 안에 사건이 없는 관측만")
    ap.add_argument("--skip", type=int, default=1, help="합체 직후 맞춤에서 뺄 프레임 수(목 동역학)")
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--mu", type=float, default=1.0e-3); ap.add_argument("--sigma", type=float, default=0.072)
    ap.add_argument("--out", default="mr_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm and a.H_mm):
        ap.error("--csv, --px_mm, --H_mm가 필요하다")
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    masks = MaskLookup(a.masks_dir) if a.masks_dir else None
    events, quiet = collect(read_rows(a.csv), H_px, masks, a.max_frames, a.quiet)
    edges = [float(v) for v in a.dH_bins.split(",")]
    res = analyse(events, quiet, list(zip(edges[:-1], edges[1:])), a.fps, a.H_mm * 1e-3, a.px_mm * 1e-3, a.mu, a.sigma, a.skip)
    with open(os.path.join(a.out, "mr_events.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["track", "frame", "dH", "eps_series"])
        for ev in events:
            w.writerow([ev["track"], ev["frame"], f"{ev['dH']:.2f}", ";".join(f"{math.sqrt(max(v, 0.0)):.4f}" if v == v else "" for v in ev["eps"])])
    if res:
        with open(os.path.join(a.out, "mr_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            for r in res:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    print(f"합체 사건 {len(events)}개, 기준선 관측 {len(quiet)}개({'마스크' if masks else '둘레·면적'})")
    for r in res:
        print(f"  d/H {r['dH_lo']:g}~{r['dH_hi']:g}: 사건 {r['n_events']}, ε {r['eps0']:.3f} → {r['eps_end']:.3f}({r['frames']}프레임), "
              f"q {r['q']:.2f} → m {r['m']:.2f}, ε_r {r['eps_r']:.3f}{' (멈춤: 접촉선 고정 후보)' if r['pinned'] else ''}, "
              f"τ {r['tau_exp_s'] * 1e3:.1f} ms = τ₂의 {r['tau_over_tau2']:.1f}배")
    print("읽는 법: q ≈ 1(지수)은 선형 마찰, q ≈ 1.5는 깨끗한 막(m 2/3), q 큰 값은 m 작음. ε_r > 0이면 원으로 돌아가지 않는다(마른 발자국, I107).")
    print("         τ/τ₂가 1보다 훨씬 크면 메니스커스 마찰이 지배한다(I107의 Φ). 사건이 적으면(< 10) 곡선이 시끄럽다.")


if __name__ == "__main__":
    main()

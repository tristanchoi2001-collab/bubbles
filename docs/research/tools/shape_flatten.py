"""움직이는 기포의 정상 납작함으로 마찰 배율 f와 지수 m을 읽는다(아이디어 I109). 압력·국소장 불필요.

배경 (원형 근처 r = R(1 + ε·cos 2θ), θ는 흐름 방향 기준, 깨끗한 막)
    앞(β₁ 3.88)·뒤(β₂ −1.13) 메니스커스의 동적 점프 (2σ/H)·β·(3Ca_V|cos θ|)^(2/3)의 2번 모드를 평면 곡률 (π/4)σκ가 받는다.
    → ε = −0.417·f·(R/H)·(3Ca_V)^(2/3)(음수 = 흐름 방향으로 눌림), Ca_V = μV/σ(그 기포의 속도).
    마찰이 D ∝ V^m이면 |ε| ∝ V^m.
    단, 이 식은 막 압력이 지배하는 작은 δ(Booth 매개변수 δ = 1.12·(d/H)·Ca^(1/3) ≲ 1.5)에서만 맞는다. Wu 외 2024(PRF 9:123603,
    저자 공개본)의 전체 이론·실험(실리콘유)은 모양이 δ에 대해 비단조다: 작은 기포는 눌리고(가로/길이 최소 약 1.06~1.09),
    큰 기포는 바깥 점성 압력 때문에 늘어나며, A = 1(원형)을 지나는 δ가 이론(ε 0.05)에서 약 2.5, 실험 그림에서 대략 2~3이다. → 이 도구는 기울기를 δ_V < --delta_max
    관측으로만 맞추고, ε_x가 음에서 양으로 바뀌는 δ_V(모양 영점)를 함께 낸다. 오염 배율 f는 막 항을 키우므로 모양 영점도 약 f배로 옮긴다(가설).

쓰는 법
    python shape_flatten.py --csv result_tracking.csv --masks_dir OUTPUT_FOLDER/instances --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --out sf_out
        [--k 2] [--dH_bins 5,10,20,50] [--quiet 3] [--min_gap 1.0] [--delta_max 1.5] [--mu 1e-3] [--sigma 0.072]
    python shape_flatten.py --demo --out sf_demo      # f 1.5, m 2/3로 그린 합성 타원 마스크로 스스로 점검

계산
    1. 트랙마다 중심 차분 속도 V(k프레임, 흐름 방향 성분). 화면 끝 접촉, 앞뒤 --quiet 프레임 안의 사건(merge/split/new), 면적 변화 20% 초과는 뺀다.
    2. 그 프레임 라벨 지도에서 기포 마스크(중심 3 px·면적 비 0.8~1.25로 짝지음)의 흐름 방향·가로 2차 모멘트 σ_ss, σ_cc로
       ε_x = (√σ_ss − √σ_cc)/(√σ_ss + √σ_cc)(정렬된 타원이면 (A − B)/(A + B)). 이웃 쌍극자 장의 변형은 방향이 무작위라 평균에서 빠진다.
       가장 가까운 이웃과의 틈이 --min_gap × 반경보다 좁은 관측은 뺀다(접촉 변형).
    3. δ_V = 1.12·(d/H)·Ca_V^(1/3)(국소장 대신 기포 속도로 잰 Booth 매개변수, δ보다 s^(1/3)배 큼)이 --delta_max 아래인 관측만으로
       X = (R/H)(3Ca_V)^(2/3)마다 ε_x의 중앙값을 내고, 원점을 지나는 기울기 c(ε_x = −c·X)를 맞춘다 → f = c/0.417.
       d/H 구간마다 ln|ε_x|를 ln V에 회귀한 기울기가 m이다(속도 범위가 2배 이상일 때만, 같은 δ 제한).
    4. 모든 관측을 δ_V 분위 구간으로 나눠 ε_x 중앙값이 음에서 양으로 바뀌는 δ_V(모양 영점)를 보간한다. 깨끗한 실리콘유(Wu 2024)는 대략 2~3.
출력: sf_obs.csv(관측별), sf_classes.csv(구간별 요약), 요약 출력.
주의: 관성(We = ρV²H/σ ≳ 0.1)도 기포를 누른다 → We가 큰 관측은 따로 본다(출력의 We 열). |ε| > 0.15는 선형 식 밖이다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

from merge_relax import MaskLookup, _f, read_rows

K_FLAT = 0.417          # ε = −K_FLAT·f·(R/H)(3Ca)^(2/3) (깨끗한 막, I109)


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def eps_x_from_mask(mask, flow, with_asym=False):
    """흐름 방향(s)·가로(c) 2차 모멘트로 ε_x = (√σ_ss − √σ_cc)/(√σ_ss + √σ_cc).
    with_asym이면 앞뒤 비대칭 (중심 − 흐름 방향 중점)/길이도 돌려준다(음수 = 뒤가 넓음, Wu 외 2024의 x_c − x_m)."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 5:
        return (float("nan"), float("nan")) if with_asym else float("nan")
    ax, sgn = axis_of(flow)
    s_, c_ = (ys, xs) if ax == "Y" else (xs, ys)
    vs, vc = float(np.var(s_)), float(np.var(c_))
    if vs <= 0 or vc <= 0:
        return (float("nan"), float("nan")) if with_asym else float("nan")
    e = (math.sqrt(vs) - math.sqrt(vc)) / (math.sqrt(vs) + math.sqrt(vc))
    if not with_asym:
        return e
    s = sgn * s_.astype(float)                         # 흐름 방향을 +로
    L = s.max() - s.min() + 1.0
    return e, (s.mean() - 0.5 * (s.max() + s.min())) / L


class FlowMasks(MaskLookup):
    def eps_x(self, fname, cx, cy, A, flow):
        """(ε_x, 앞뒤 비대칭)."""
        d = self._load(fname)
        if d is None or not len(d[1]):
            return float("nan"), float("nan")
        inst, ids, cxs, cys, cnt = d
        d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
        j = int(np.argmin(d2))
        if d2[j] > 9.0 or not 0.8 <= cnt[j] / A <= 1.25:
            return float("nan"), float("nan")
        return eps_x_from_mask(inst == ids[j], flow, with_asym=True)


def collect(rows, masks, flow, k, H_px, px_m, fps, mu, sigma, rho=998.0, quiet=3, min_gap=1.0):
    ax, sgn = axis_of(flow)
    tracks = defaultdict(dict)
    per_frame = defaultdict(list)
    for r in rows:
        tid = r.get("トラックID")
        A = _f(r.get("面積(px)"))
        if not tid or not A > 0 or r.get("イベント") == "気泡なし":
            continue
        f = int(r["フレーム"])
        tracks[tid][f] = r
        per_frame[f].append((_f(r.get("中心X")), _f(r.get("中心Y")), math.sqrt(A / math.pi)))
    obs = []
    for tid, fr in tracks.items():
        evs = {f for f, r in fr.items() if r.get("イベント") in ("merge", "split", "new")}
        for f, r in fr.items():
            if f - k not in fr or f + k not in fr or r.get("フレーム接触") == "1":
                continue
            if any(abs(f - e) <= quiet for e in evs):
                continue
            a = [_f(fr[g]["面積(px)"]) for g in (f - k, f, f + k)]
            if max(a) > 1.2 * min(a):
                continue
            c0 = (_f(fr[f - k][f"中心{ax}"]), _f(fr[f + k][f"中心{ax}"]))
            v_px = sgn * (c0[1] - c0[0]) / (2 * k)
            if not v_px > 0:
                continue
            x, y, R = _f(r["中心X"]), _f(r["中心Y"]), math.sqrt(a[1] / math.pi)
            gaps = [math.hypot(x - q[0], y - q[1]) - R - q[2] for q in per_frame[f] if not (q[0] == x and q[1] == y)]
            if gaps and min(gaps) < min_gap * R:
                continue
            e, asym = masks.eps_x(r.get("ファイル名", ""), x, y, a[1], flow)
            if e != e:
                continue
            V = v_px * px_m * fps
            Ca = mu * V / sigma
            obs.append(dict(track=tid, frame=f, dH=2 * R / H_px, R_over_H=R / H_px, V=V, Ca=Ca,
                            We=rho * V * V * (H_px * px_m) / sigma, X=(R / H_px) * (3 * Ca) ** (2 / 3),
                            delta_V=1.12 * (2 * R / H_px) * Ca ** (1 / 3), eps_x=e, asym=asym))
    return obs


def shape_zero(obs, n_d=10):
    """ε_x 중앙값이 음에서 양으로 바뀌는 δ_V(모양 영점). 없으면 nan."""
    if len(obs) < 30:
        return float("nan")
    d = np.array([o["delta_V"] for o in obs]); e = np.array([o["eps_x"] for o in obs])
    q = np.quantile(d, np.linspace(0, 1, n_d + 1))
    dm, em = [], []
    for i in range(n_d):
        m = (d >= q[i]) & (d <= q[i + 1])
        if m.sum() >= 5:
            dm.append(float(np.median(d[m]))); em.append(float(np.median(e[m])))
    for i in range(len(dm) - 1):
        if em[i] < 0 <= em[i + 1]:
            return dm[i] + (dm[i + 1] - dm[i]) * (-em[i]) / (em[i + 1] - em[i])
    return float("nan")


def analyse(obs_all, bins, n_x=8, delta_max=1.5):
    out = []
    obs = [o for o in obs_all if o["delta_V"] < delta_max]
    X = np.array([o["X"] for o in obs]); E = np.array([o["eps_x"] for o in obs])
    if len(X) >= 20:
        edges = np.quantile(X, np.linspace(0, 1, n_x + 1))
        xm, em = [], []
        for i in range(n_x):
            m = (X >= edges[i]) & (X <= edges[i + 1])
            if m.sum() >= 5:
                xm.append(float(np.median(X[m]))); em.append(float(np.median(E[m])))
        xm, em = np.array(xm), np.array(em)
        c = float(-(xm @ em) / (xm @ xm)) if len(xm) else float("nan")
        out.append(dict(cls="all", n=len(obs), slope_c=c, f=c / K_FLAT, m=float("nan"),
                        X_bins=";".join(f"{v:.4g}" for v in xm), eps_bins=";".join(f"{v:.4g}" for v in em),
                        delta_zero=shape_zero(obs_all), n_all=len(obs_all)))
    for lo, hi in bins:
        sel = [o for o in obs if lo <= o["dH"] < hi]
        if len(sel) < 20:
            continue
        x = np.array([o["X"] for o in sel]); e = np.array([o["eps_x"] for o in sel])
        c = float(-np.median(e / x)) if np.all(x > 0) else float("nan")
        v = np.array([o["V"] for o in sel])
        m = float("nan")
        if v.max() / v.min() >= 2:
            q = np.quantile(v, np.linspace(0, 1, 7))
            lv, le = [], []
            for i in range(6):
                mm = (v >= q[i]) & (v <= q[i + 1])
                if mm.sum() >= 5 and np.median(e[mm]) < 0:
                    lv.append(math.log(float(np.median(v[mm])))); le.append(math.log(-float(np.median(e[mm]))))
            if len(lv) >= 3:
                m = float(np.polyfit(lv, le, 1)[0])
        out.append(dict(cls=f"dH_{lo:g}_{hi:g}", n=len(sel), slope_c=c, f=c / K_FLAT, m=m,
                        X_bins="", eps_bins="", We_med=float(np.median([o["We"] for o in sel])),
                        asym_med=float(np.median([o["asym"] for o in sel]))))
    return out


def make_demo(out, f_true=1.5, m_true=2 / 3, seed=4):
    """합성: 원형 근처 타원(흐름 방향 +x로 눌림 ε = −K_FLAT·f·(R/H)(3Ca)^(2/3)·(V/V₀)^(m − 2/3) 꼴), 반경 25~70 px, 속도 넓게.
    한 프레임에 한 트랙, 각 트랙 5프레임(중심 차분 k = 2). 위치 잡음 0.1 px, 방향 흔들림 ±0.1 rad."""
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(out, "instances"), exist_ok=True)
    px_m, fps, H_px, mu, sigma = 2e-5, 500.0, 15.0, 1e-3, 0.072
    V0 = 0.05
    rows = []
    frame = 0
    tid = 0
    W, Hh = 420, 300
    yy, xx = np.indices((Hh, W))
    for _ in range(60):
        tid += 1
        R = rng.uniform(25, 70)
        V = 10 ** rng.uniform(math.log10(0.01), math.log10(0.2))      # m/s
        Ca = mu * V / sigma
        eps = -K_FLAT * f_true * (R / H_px) * (3 * Ca) ** (2 / 3) * (V / V0) ** (m_true - 2 / 3)
        A_ax, B_ax = R * math.sqrt((1 + eps) / (1 - eps)), R * math.sqrt((1 - eps) / (1 + eps))   # A: 흐름 방향
        ang = rng.normal(0, 0.1)
        v_px = V / (px_m * fps)
        for kk in range(5):
            cx = 120.0 + kk * v_px + rng.normal(0, 0.1); cy = 150.0 + rng.normal(0, 0.1)
            xr = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
            yr = -(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)
            m = (xr / A_ax) ** 2 + (yr / B_ax) ** 2 <= 1
            inst = np.zeros((Hh, W), np.uint16)
            inst[m] = 1
            fname = f"f{frame:05d}.png"
            np.savez_compressed(os.path.join(out, "instances", fname.replace(".png", ".npz")), inst=inst)
            rows.append({"ファイル名": fname, "フレーム": frame, "トラックID": tid, "イベント": "new" if kk == 0 else "normal",
                         "面積(px)": int(m.sum()), "中心X": f"{xx[m].mean():.3f}", "中心Y": f"{yy[m].mean():.3f}", "フレーム接触": "0"})
            frame += 1
        frame += 1                                     # 트랙 사이 빈 프레임
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path, dict(px_m=px_m, fps=fps, H_px=H_px, mu=mu, sigma=sigma, f=f_true, m=m_true)


def _demo(out):
    fails = []
    for f_true, m_true in ((1.0, 2 / 3), (1.5, 2 / 3), (1.0, 1 / 3)):
        sub = os.path.join(out, f"f{f_true:g}_m{m_true:.2f}")
        path, tr = make_demo(sub, f_true, m_true)
        obs = collect(read_rows(path), FlowMasks(os.path.join(sub, "instances")), "right", 2, tr["H_px"], tr["px_m"], tr["fps"],
                      tr["mu"], tr["sigma"], quiet=0, min_gap=0.0)
        res = analyse(obs, [(2, 100)])
        ra = [r for r in res if r["cls"] == "all"][0]
        rc = [r for r in res if r["cls"] != "all"][0]
        if abs(rc["asym_med"]) > 0.01:
            fails.append(f"f {f_true:g}: 대칭 타원의 앞뒤 비대칭 {rc['asym_med']:+.4f}(0이어야 함)")
        if abs(m_true - 2 / 3) < 1e-9:
            ok = abs(ra["f"] - f_true) <= 0.12 * f_true and abs(rc["m"] - m_true) <= 0.12
            print(f"  {'통과' if ok else '실패'}  f {f_true:g}, m {m_true:.2f}: 관측 {ra['n']}, 되찾은 f {ra['f']:.3f}, m {rc['m']:.3f}")
        else:
            ok = abs(rc["m"] - m_true) <= 0.12
            print(f"  {'통과' if ok else '실패'}  f {f_true:g}, m {m_true:.2f}: 관측 {ra['n']}, 되찾은 m {rc['m']:.3f}(f는 m 2/3 가정이라 비교 안 함)")
        if not ok:
            fails.append(f"f {f_true:g} m {m_true:.2f}")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--masks_dir"); ap.add_argument("--px_mm", type=float); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--H_mm", type=float); ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--quiet", type=int, default=3); ap.add_argument("--min_gap", type=float, default=1.0)
    ap.add_argument("--delta_max", type=float, default=1.5, help="막 압력이 지배하는 작은 δ만 기울기 맞춤에 쓴다(Wu 2024)")
    ap.add_argument("--dH_bins", default="5,10,20,50"); ap.add_argument("--mu", type=float, default=1.0e-3); ap.add_argument("--sigma", type=float, default=0.072)
    ap.add_argument("--out", default="sf_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.masks_dir and a.px_mm and a.H_mm):
        ap.error("--csv, --masks_dir, --px_mm, --H_mm가 필요하다")
    os.makedirs(a.out, exist_ok=True)
    obs = collect(read_rows(a.csv), FlowMasks(a.masks_dir), a.flow, a.k, a.H_mm / a.px_mm, a.px_mm * 1e-3, a.fps, a.mu, a.sigma,
                  quiet=a.quiet, min_gap=a.min_gap)
    edges = [float(v) for v in a.dH_bins.split(",")]
    res = analyse(obs, list(zip(edges[:-1], edges[1:])), delta_max=a.delta_max)
    if obs:
        with open(os.path.join(a.out, "sf_obs.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(obs[0].keys()))
            w.writeheader()
            for o in obs:
                w.writerow({kk: (f"{v:.5g}" if isinstance(v, float) else v) for kk, v in o.items()})
    if res:
        keys = sorted({kk for r in res for kk in r}, key=lambda kk: list(res[0].keys()).index(kk) if kk in res[0] else 99)
        with open(os.path.join(a.out, "sf_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in res:
                w.writerow({kk: (f"{v:.5g}" if isinstance(v, float) else v) for kk, v in r.items()})
    print(f"관측 {len(obs)}개")
    for r in res:
        print(f"  {r['cls']}: n {r['n']}(δ_V < {a.delta_max:g}), 기울기 c {r['slope_c']:.3f} → f {r['f']:.2f}" + (f", m {r['m']:.2f}" if r["m"] == r["m"] else "")
              + (f", We 중앙값 {r['We_med']:.3f}, 앞뒤 비대칭 {r['asym_med']:+.4f}" if "We_med" in r else "")
              + (f"; 모양 영점 δ_V {r['delta_zero']:.2f}(전체 {r['n_all']}개)" if "delta_zero" in r else ""))
    print("읽는 법: 깨끗한 막이면 f ≈ 1, m ≈ 2/3. 실험실 물은 f > 1(I90 k_fit/16.85, I104 d*와 비교). We ≳ 0.1이면 관성도 누른다(I109).")
    print("         모양 영점(눌림 → 늘어남)은 깨끗한 실리콘유에서 대략 δ 2~3(Wu 외 2024 그림). 더 크면 막 마찰이 큰 것(오염) 후보다.")
    print("         앞뒤 비대칭(음수 = 뒤가 넓음)은 깨끗한 막에서 작은 음수(Wu 2024). 크게 음수면 뒤 접촉선이 붙는(마른 발자국) 후보다.")


if __name__ == "__main__":
    main()

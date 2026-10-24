"""유량 변조 응답 분광(아이디어 I117): 액체 유량을 주파수 f로 조금 흔든 녹화에서 기포 속도를 위상 고정으로 모아 크기 구분별
응답을 내고, 마찰 지수 m과 막 기억 무게 w_r를 맞춘다.

배경
    힘 균형 2U = V(1 + Δ(V)), Δ ∝ V^(m−1)에서 (δV/V)/(δU/U) = R = (1 + Δ)/(1 + mΔ)(준정적)다. Δ = 2/s − 1, s = V̄/U_loc.
    젖은 막이면 뒤 메니스커스는 L/V̄ 전에 깔린 막을 거두므로(Yu 외 2018) 저항 변화에 지연 항이 붙는다:
        R(ω) = (1 + Δ)/(1 + mΔ·(1 − w_r + w_r·e^{−iωτ})),  τ = L/V̄(흐름 방향 길이 ÷ 평균 속도).
    마른 발자국(접촉선 마찰, 막 없음)은 w_r = 0이다. 국소 유속 진폭 ε를 모르면 응답은 ε·R로만 나오므로 ε도 함께 맞춘다
    (크기 구분 둘 이상 × 주파수 하나 이상이면 정해진다. 구분 사이 비는 ε 없이 m만의 함수).

계산
    1. 트랙을 빠진 프레임·합체·분열·화면 끝에서 자르고, 조각마다 중심 위치의 중심 차분 속도 v(t)를 그 조각 평균으로 나눈 y = v/V̄ − 1.
    2. 위상 θ = 2πf·frame + φ_ref(--ref 신호가 있으면 그 신호를 A·cos(2πf·frame + φ_ref)로 맞춘 φ_ref, 없으면 모든 기포의 프레임
       중앙 y로 맞춘 위상).
    3. 크기 구분마다 y = a·cos θ + b·sin θ를 최소제곱으로 맞춰 복소 응답 Z = a − i·b(진폭 |Z|, 위상 arg Z, 앞섬이 양수). 트랙 부트스트랩 구간.
    4. 맞춤: Δ_c(--U_loc가 있을 때 s = V̄_c/U_loc), τ_c(구분 중앙 L/V̄)를 넣고 모든 (구분, 주파수)의 Z를 ε·R(ω)로 맞춰 (ε, m, w_r)을 낸다.
       ε는 복소수(공통 진폭과 위상)다: 압력 신호와 국소 유속 사이의 관로 관성·순응 위상, 기준 신호의 지연을 흡수한다.
       --eps(국소 유속의 상대 진폭)를 주면 |ε|를 고정한다. 구분 사이 진폭 비만 쓰는 m(ε 불필요)도 따로 낸다.
쓰는 법
    python modulation_response.py --csv run_f01.csv,run_f03.csv --f_mod 0.1,0.3 --fps 100 --px_mm 0.01 --H_mm 1 --flow right
        --U_loc 0.03 [--eps 0.05] [--ref p_f01.csv,p_f03.csv] [--dH_bins 2,4,7,12,30] --out mr_out
    python modulation_response.py --demo --out mr_demo     # 합성(젖은 구분: m 2/3·w_r 0.3, 마른 구분: m 0.2·w_r 0)
    --ref 파일은 열 frame(또는 time_s)과 value(압력 등)를 가진 CSV다. 카메라와 같은 시계여야 한다.
출력: mr_classes.csv(구분 × 주파수의 진폭·위상·구간), 요약 출력.
주의: 1 mm 갭은 Womersley 수 1 아래(f ≲ 0.64 Hz)여야 갭 안 분포가 준정적이다. 주입기의 기포 크기·간격이 변조에 따라 흔들리면
      크기 구분 안에서만 비교한다. 같은 영상 안 트랙 부트스트랩 구간은 배치·관로 표류를 넣지 않아 좁다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

AXIS = {"right": ("X", +1), "left": ("X", -1), "down": ("Y", +1), "up": ("Y", -1)}
JUMP = ("merge", "split")


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def read_segments(path, flow, H_px, k=1):
    """CSV → 조각 목록. 조각 = (트랙, 프레임 배열, y = v/V̄ − 1 배열, V̄(px/frame), d/H 중앙값, L 중앙값(px)).
    L은 2·(先端部 − 中心)(흐름 방향), 없으면 등가 지름."""
    ax, sgn = AXIS[flow]
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    by = defaultdict(list)
    for r in rows:
        ev = r.get("イベント") or ""
        A = _f(r.get("面積(px)"))
        if not r.get("トラックID") or ev.startswith("merged_into") or ev == "気泡なし" or not A > 0:
            continue
        pos = sgn * _f(r.get(f"中心{ax}"))
        front = sgn * _f(r.get(f"先端部{ax}"))
        d = math.sqrt(4 * A / math.pi)
        L = 2 * (front - pos) if front == front and front > pos else d
        by[r["トラックID"]].append((int(r["フレーム"]), pos, d / H_px, L, ev, r.get("フレーム接触") == "1"))
    segs = []
    for tid, ts in by.items():
        ts.sort()
        cur = []
        for t in ts + [None]:
            if t is not None and cur and t[0] - cur[-1][0] == 1 and t[4] not in JUMP and not t[5]:
                cur.append(t)
                continue
            if len(cur) >= 2 * k + 8:
                fr = np.array([c[0] for c in cur]); x = np.array([c[1] for c in cur])
                v = (x[2 * k:] - x[:-2 * k]) / (2 * k)
                vb = float(v.mean())
                if vb > 0:
                    segs.append((tid, fr[k:-k], v / vb - 1, vb, float(np.median([c[2] for c in cur])),
                                 float(np.median([c[3] for c in cur]))))
            cur = [t] if t is not None and not t[5] else []
    return segs


def ref_phase(frames, values, f_cyc):
    """기준 신호를 A·cos(2πf·frame + φ)로 맞춘 φ(f는 주기/frame)."""
    th = 2 * np.pi * f_cyc * np.asarray(frames, float)
    X = np.column_stack([np.cos(th), np.sin(th), np.ones_like(th)])
    a, b, _ = np.linalg.lstsq(X, np.asarray(values, float), rcond=None)[0]
    return math.atan2(-b, a)


def lockin(segs, f_cyc, phi0, sel, n_boot=200, seed=0, k=1):
    """sel(조각 번호 배열)의 y를 θ = 2πf·frame + φ0에 맞춘 복소 응답과 트랙 부트스트랩 구간.
    중심 차분 (x(t + k) − x(t − k))/2k는 진폭을 sin(2πfk)/(2πfk)배 깎으므로(위상은 그대로) 나눠서 되돌린다."""
    rng = np.random.default_rng(seed)
    parts = [(segs[i][1], segs[i][2]) for i in sel]

    def fit(idx):
        fr = np.concatenate([parts[i][0] for i in idx]); y = np.concatenate([parts[i][1] for i in idx])
        th = 2 * np.pi * f_cyc * fr + phi0
        X = np.column_stack([np.cos(th), np.sin(th)])
        a, b = np.linalg.lstsq(X, y, rcond=None)[0]
        return complex(a, -b)
    att = math.sin(2 * math.pi * f_cyc * k) / (2 * math.pi * f_cyc * k) if f_cyc > 0 else 1.0
    z = fit(np.arange(len(parts))) / att
    zb = np.array([fit(rng.integers(0, len(parts), len(parts))) for _ in range(n_boot)]) / att if n_boot else np.zeros(0, complex)
    return z, zb


def model_R(Delta, m, w_r, wt):
    return (1 + Delta) / (1 + m * Delta * (1 - w_r + w_r * np.exp(-1j * wt)))


def fit_global(Z, Delta, wt, eps=None):
    """Z(관측 복소 응답) ≈ ε·R(Δ, m, w_r, ωτ)를 격자 + 닫힌 꼴 복소 ε로 맞춘다(eps를 주면 |ε| 고정, 위상만 맞춤).
    Delta·wt는 칸마다 구성 조각의 값 배열 목록이다(R이 Δ·ωτ에 비선형이라 칸 중앙값 하나로 넣으면 치우친다 → 칸 안에서 평균한 모형).
    반환 (ε(복소), m, w_r, 잔차)."""
    best = None
    for m in np.linspace(0.0, 1.5, 151):
        for w in np.linspace(0.0, 0.9, 46):
            R = np.array([np.mean(model_R(D, m, w, t)) for D, t in zip(Delta, wt)])
            e = complex(np.vdot(R, Z) / np.vdot(R, R))
            if eps:
                e = eps * e / abs(e) if abs(e) > 0 else complex(eps)
            res = float(np.sum(np.abs(Z - e * R) ** 2))
            if best is None or res < best[3]:
                best = (e, m, w, res)
    return best


def m_from_ratio(r12, D1, D2):
    """진폭 비 |R1/R2| = [(1 + D1)/(1 + mD1)]/[(1 + D2)/(1 + mD2)]를 m에 대해 푼다(준정적, w_r 무시)."""
    ms = np.linspace(-0.2, 2.0, 2201)
    g = ((1 + D1) / (1 + ms * D1)) / ((1 + D2) / (1 + ms * D2))
    k = int(np.argmin(np.abs(g - r12)))
    return float(ms[k]) if 0 < k < len(ms) - 1 else float("nan")


def analyse(runs, bins, H_px, px_mm, fps, U_loc=None, eps=None, n_boot=200):
    """runs = [(조각 목록, f(Hz), 기준 위상 φ0 또는 None)]. 구분 × 주파수 표와 전역 맞춤."""
    recs = []
    for segs, f_hz, phi0 in runs:
        f_cyc = f_hz / fps
        if phi0 is None:                                     # 모든 기포의 프레임 중앙 y로 기준 위상
            acc = defaultdict(list)
            for s in segs:
                for fr, y in zip(s[1], s[2]):
                    acc[int(fr)].append(y)
            fr = sorted(acc)
            phi0 = ref_phase(fr, [np.median(acc[q]) for q in fr], f_cyc)
        dh = np.array([s[4] for s in segs])
        for lo, hi in bins:
            sel = np.where((dh >= lo) & (dh < hi))[0]
            if len(sel) < 5:
                continue
            z, zb = lockin(segs, f_cyc, phi0, sel, n_boot=n_boot)
            Vb = float(np.median([segs[i][3] for i in sel])); L = float(np.median([segs[i][5] for i in sel]))
            rec = dict(f_hz=f_hz, dH_lo=lo, dH_hi=hi, n_seg=len(sel), V_px_per_frame=Vb, L_px=L,
                       wtau=2 * math.pi * f_cyc * L / Vb, amp=abs(z), phase_deg=math.degrees(math.atan2(z.imag, z.real)), z=z,
                       phi_ref=phi0)
            if len(zb):
                rec["amp_lo"], rec["amp_hi"] = (float(v) for v in np.percentile(np.abs(zb), [2.5, 97.5]))
            if U_loc:
                s = Vb * px_mm * 1e-3 * fps / U_loc
                rec["s"], rec["Delta"] = s, 2 / s - 1
                si = np.array([segs[i][3] for i in sel]) * px_mm * 1e-3 * fps / U_loc
                rec["Delta_i"] = 2 / si - 1                          # 칸 안 조각마다(모형 평균용)
                rec["wtau_i"] = np.array([2 * math.pi * f_cyc * segs[i][5] / segs[i][3] for i in sel])
            recs.append(rec)
    fit = None
    if U_loc and len(recs) >= 3:
        Z = np.array([r["z"] for r in recs])
        fit = fit_global(Z, [r["Delta_i"] for r in recs], [r["wtau_i"] for r in recs], eps)
    return recs, fit


def make_demo(out, f_list=(0.002, 0.02, 0.05), seed=5, nf=1500, n_per=40):
    """합성: 서로 독립인 기포(상호작용 없음). 크기 d/H 2.5~12(H 16/3 px), 국소장 U(t) = U0(1 + ε sin 2πft), U0 6 px/frame, ε 0.05.
    젖은 기포(d/H ≥ 4): 2U = V + Δ0·V0·[(1 − w_r)(V/V0)^m + w_r(V(t − τ)/V0)^m], m 2/3, w_r 0.3, τ = d/V0.
    마른 기포(d/H < 4): m 0.2, w_r 0. Δ0는 Booth 관계 s(d/H)에서. 위치 잡음 0.15 px. 주파수마다 CSV 하나(모든 기포를 한꺼번에 적분)."""
    rng = np.random.default_rng(seed)
    H_px, U0, eps, sub = 16.0 / 3, 6.0, 0.05, 4

    def s_booth(dH, U=0.05, mu=1e-3, sig=0.072):
        s = 1.0
        for _ in range(200):
            s = 0.5 * s + 0.5 * 2 / (1 + 1 / (1.12 * dH * (mu * s * U / sig) ** (1 / 3)))
        return s
    dH = np.concatenate([rng.uniform(2.5, 4.0, n_per), rng.uniform(4.0, 12.0, n_per)])
    nb = len(dH)
    s0 = np.array([s_booth(v) for v in dH]); V0 = s0 * U0; D0 = 2 / s0 - 1
    wet = dH >= 4.0
    m = np.where(wet, 2 / 3, 0.2); wr = np.where(wet, 0.3, 0.0)
    d_px = dH * H_px
    lag = np.maximum((d_px / V0 * sub).astype(int), 1)
    paths = []
    for f in f_list:
        nst = nf * sub
        Vh = np.empty((nst + lag.max() + 1, nb)); Vh[:lag.max() + 1] = V0
        x = rng.uniform(0, 200, nb); xs = np.empty((nf, nb))
        cols = np.arange(nb)
        for step in range(nst):
            if step % sub == 0:
                xs[step // sub] = x                          # 프레임 시각의 위치(이 프레임의 첫 단계 전)
            cur = lag.max() + step
            U = U0 * (1 + eps * math.sin(2 * math.pi * f * (step + 0.5) / sub))   # 단계 가운데 시각
            Vd = Vh[cur - lag, cols]
            V = Vh[cur].copy()
            for _ in range(40):
                Vn = 2 * U - D0 * V0 * ((1 - wr) * (np.maximum(V, 1e-6) / V0) ** m + wr * (Vd / V0) ** m)
                V = 0.5 * V + 0.5 * Vn
            Vh[cur + 1] = V
            x = x + V / sub
        rows = []
        for b in range(nb):
            for fr in range(nf):
                rows.append({"フレーム": fr, "トラックID": b + 1, "イベント": "", "面積(px)": f"{math.pi * (d_px[b] / 2) ** 2:.1f}",
                             "中心X": f"{xs[fr, b] + rng.normal(0, 0.15):.3f}", "中心Y": f"{30.0 * (b + 1):.1f}",
                             "先端部X": f"{xs[fr, b] + d_px[b] / 2 + rng.normal(0, 0.15):.3f}", "先端部Y": f"{30.0 * (b + 1):.1f}",
                             "フレーム接触": "0"})
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, f"mod_f{f:g}.csv")
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        paths.append(p)
    return paths, H_px, U0, eps


def _demo(out):
    f_list = (0.002, 0.02, 0.05)
    paths, H_px, U0, eps = make_demo(out, f_list)
    px_mm, fps = 0.02, 100.0                                 # U0 6 px/frame = 0.012 m/s
    U_m = U0 * px_mm * 1e-3 * fps
    runs = [(read_segments(p, "right", H_px), f * fps, -math.pi / 2) for p, f in zip(paths, f_list)]   # 강제 sin = cos(θ − π/2)
    bins_wet = ((4, 6), (6, 9), (9, 12.1))
    recs, fit = analyse(runs, bins_wet, H_px, px_mm, fps, U_loc=U_m, n_boot=0)
    recs_dry, fit_dry = analyse(runs, ((2.5, 3.2), (3.2, 4.0)), H_px, px_mm, fps, U_loc=U_m, n_boot=0)
    fails = []

    def check(ok, label, msg):
        print(f"  {'통과' if ok else '실패'}  {label}: {msg}")
        if not ok:
            fails.append(label)
    print(f"합성: 젖은 구분 m 0.667·w_r 0.3, 마른 구분 m 0.2·w_r 0, ε {eps}, f {f_list} 주기/프레임")
    for r in recs + recs_dry:
        print(f"  f {r['f_hz']:.2f} Hz d/H {r['dH_lo']:g}~{r['dH_hi']:g}: 진폭 {r['amp']:.4f}, 위상 {r['phase_deg']:+.1f}°, ωτ {r['wtau']:.2f}, Δ {r['Delta']:.2f}")
    e, m, w, _ = fit
    check(abs(m - 2 / 3) <= 0.07 and abs(w - 0.3) <= 0.1 and abs(abs(e) - eps) <= 0.005, "젖은 구분 전역 맞춤(ε 모름, 복소)",
          f"|ε| {abs(e):.4f}(참 0.05), arg ε {math.degrees(math.atan2(e.imag, e.real)):+.1f}°(참 0), m {m:.3f}(참 0.667), w_r {w:.2f}(참 0.3)")
    e2, m2, w2, _ = fit_dry
    check(abs(m2 - 0.2) <= 0.1 and w2 <= 0.1, "마른 구분 전역 맞춤", f"|ε| {abs(e2):.4f}, m {m2:.3f}(참 0.2), w_r {w2:.2f}(참 0)")
    lo = [r for r in recs if r["f_hz"] == f_list[0] * fps]
    if len(lo) >= 2:
        mr = m_from_ratio(lo[0]["amp"] / lo[-1]["amp"], lo[0]["Delta"], lo[-1]["Delta"])
        check(abs(mr - 2 / 3) <= 0.12, "낮은 주파수 구분 비로 m(ε 불필요)", f"{mr:.3f}(참 0.667, w_r 무시라 조금 치우칠 수 있음)")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", help="녹화마다 하나, 쉼표로"); ap.add_argument("--f_mod", help="녹화마다 변조 주파수(Hz), 쉼표로")
    ap.add_argument("--ref", default="", help="(선택) 녹화마다 기준 신호 CSV(frame 또는 time_s, value), 쉼표로")
    ap.add_argument("--fps", type=float, default=500.0); ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px)")
    ap.add_argument("--H_mm", type=float, default=1.0); ap.add_argument("--flow", default="right", choices=list(AXIS))
    ap.add_argument("--U_loc", type=float, default=float("nan"), help="국소장(m/s), 예 j_L/(1 − α). Δ와 m 맞춤에 필요")
    ap.add_argument("--eps", type=float, default=float("nan"), help="(선택) 국소 유속의 상대 변조 진폭. 없으면 함께 맞춤")
    ap.add_argument("--dH_bins", default="2,4,7,12,30"); ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--out", default="mr_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.f_mod and a.px_mm):
        ap.error("--csv, --f_mod, --px_mm가 필요하다")
    if a.px_mm > 1:
        ap.error("--px_mm은 화소 하나의 크기(mm/px)다(예 0.01).")
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    csvs = a.csv.split(","); fs = [float(v) for v in a.f_mod.split(",")]
    refs = a.ref.split(",") if a.ref else [None] * len(csvs)
    runs = []
    for c, f, rf in zip(csvs, fs, refs):
        phi0 = None
        if rf:
            with open(rf, encoding="utf-8-sig", newline="") as fh:
                rr = list(csv.DictReader(fh))
            fr = [(_f(r.get("frame")) if r.get("frame") else _f(r.get("time_s")) * a.fps) for r in rr]
            phi0 = ref_phase(fr, [_f(r.get("value")) for r in rr], f / a.fps)   # 기준 = A·cos(2πf·frame + φ0)
        runs.append((read_segments(c, a.flow, H_px), f, phi0))
    edges = [float(v) for v in a.dH_bins.split(",")]
    recs, fit = analyse(runs, list(zip(edges[:-1], edges[1:])), H_px, a.px_mm, a.fps,
                        U_loc=a.U_loc if a.U_loc == a.U_loc else None, eps=a.eps if a.eps == a.eps else None, n_boot=a.n_boot)
    if recs:
        keys = [k for k in recs[0] if k not in ("z", "Delta_i", "wtau_i")]
        with open(os.path.join(a.out, "mr_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys + [k for k in ("amp_lo", "amp_hi", "s", "Delta") if k not in keys], extrasaction="ignore")
            w.writeheader(); w.writerows(recs)
    for r in recs:
        print(f"f {r['f_hz']:g} Hz, d/H {r['dH_lo']:g}~{r['dH_hi']:g}: 조각 {r['n_seg']}, 진폭 {r['amp']:.4f} "
              f"[{r.get('amp_lo', float('nan')):.4f}~{r.get('amp_hi', float('nan')):.4f}], 위상 {r['phase_deg']:+.1f}°, ωτ = 2πfL/V̄ {r['wtau']:.2f}"
              + (f", s {r['s']:.2f}(Δ {r['Delta']:.2f})" if "s" in r else ""))
    if fit:
        e, m, w, _ = fit
        print(f"전역 맞춤 ε·(1 + Δ)/(1 + mΔ(1 − w_r + w_r e^(−iωτ))): |ε| {abs(e):.4f}(위상 {math.degrees(math.atan2(e.imag, e.real)):+.0f}°), m {m:.2f}, w_r {w:.2f}. "
              "w_r > 0이면 막 기억(젖은 막), 0이면 지연 없는 마찰(마름 쪽). 구분이 마름·젖음으로 섞이면 구분을 나눠 다시 맞춘다.")
    print("읽는 법: 낮은 주파수에서 구분 사이 진폭 비는 m만의 함수(ε 불필요). 진폭이 변조 세기에 비례하지 않으면(녹화 둘 이상) 고정 문턱(마름) 쪽.")


if __name__ == "__main__":
    main()

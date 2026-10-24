"""저유속 기포 표류 지도로 갭의 가로 분포(덮개 처짐)·기울기·액체 온도 기울기를 읽는다(아이디어 I105).

배경 (원형 팬케이크, 깊이 평균 Darcy)
    테두리 바깥 액체 압력 p_g − 2σ/H가 평면 안에서 기울면 기포는 Ψ = 2σ(T)/H − ρgζ가 낮은 쪽으로 밀린다.
    가로 표류각 tanφ = v_c/v_s = K(−∂_cΨ)/(2U), K = H²/(12μ). 크기·마찰과 무관하다(가로 응답은 할선 이동도, I102와 같은 이유).
    갭 항만 있으면 ∂_cH = 12μU·tanφ/σ다. 같은 H(c)가 국소장도 U_loc ∝ H²로 바꾼다(흐름 방향 속도의 가로 분포).
    → 가로 표류를 적분한 H(c)와 흐름 방향 속도 분포가 같은 H(c)를 말하면 갭 분포(덮개 처짐, 가공 휨)로 확인된다.
    온도 기울기(가열)가 있으면 같은 꼴로 더해진다: 갭 항 σ∂H ↔ 온도 항 H|dσ/dT|∂T(부호는 측정 대상, I105).

쓰는 법
    python drift_map.py --csv result_tracking.csv --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --U_loc 0.05 --out dm_out
        [--walls 120,980] [--nbins 12] [--dH_bins 2,5,15,50] [--k 2] [--sigma 0.072] [--mu 1e-3] [--wall_excl 1.0]
    python drift_map.py --demo --out dm_demo     # 덮개 처짐(가운데 3 µm) 합성 추적으로 스스로 점검

계산
    1. 트랙마다 중심 차분 속도 v = (x(t + k) − x(t − k))/(2k). 창 안에 화면 끝 접촉, 면적 변화 20% 초과, 빠진 프레임,
       다른 기포와의 접촉(틈 < 0.5 × 작은 쪽 반경)이 있으면 버린다(velocity_fluctuations.py와 같은 규칙). 흐름 방향 s, 가로 c 성분.
    2. 가로 위치 구간(nbins, --walls가 있으면 두 벽 사이, 없으면 관측의 1~99% 범위)과 d/H 구간마다
       기포별 tanφ_i = v_c/v_s의 중앙값(코시 꼬리에 강함)과 v_s의 중앙값. 트랙 단위 부트스트랩으로 95% 구간.
       --walls가 있으면 벽에서 wall_excl × 지름 안의 관측은 뺀다(측벽 거울상 I101과 섞임).
    3. 크기 무관 시험: 위치 구간마다 d/H 구간끼리 tanφ의 차이(가로 표류가 크기에 따라 다르면 이 그림 밖).
    4. 갭 분포: ∂_cH = 12μU(c)·tanφ(c)/σ(U(c) = U_loc × 그 구간 v_s / 전체 v_s)를 c로 적분하고 평균을 0으로 → ΔH(c).
       예측 흐름 방향 속도비 (1 + ΔH/H)²(평균 1로)와 측정 v_s(c)/평균을 나란히 낸다.
    5. 위치와 무관한 균일 성분(구간 평균 tanφ, 같은 무게)은 기울임(I102)이나 균일 갭 기울기(쐐기)다. 위치로는 못 가른다.
       같은 각을 내는 기울임 sinθ = 24μU·tanφ/(H²ρg), 갭 기울기 12μU·tanφ/σ를 낸다.
       흐름 방향 속도로 가른다: 쐐기면 U ∝ H²라 v_s에 가로 1차 경향이 생기고 기울임이면 없다. 4의 예측을 두 가정(균일 성분 = 갭 / = 기울임)으로
       내고 측정 v_s 분포와의 잔차를 비교한다.
    자가 시험(--demo): 덮개 처짐 3 µm + 가로 기울임 20 mrad, 크기 세 가지. 구간별 각(±2%), ΔH(c)(0.05 µm), 속도 분포(0.2%),
       균일 성분(20.8 대 20 mrad)과 "기울임" 판정을 되돌린다.
출력: dm_bins.csv(구간별 표), 요약 출력.
주의: 쌍극자 요동(I99)이 각의 잡음이다(코시 척도 약 α|λ|). 기포 수천 개면 수 mrad. 원형에 가까운 기포를 전제한다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

from velocity_fluctuations import _f, near_contact, read_tracks


def track_obs(tracks, k, near=frozenset()):
    """(트랙, 프레임, s, c, v_s, v_c, 등가 지름 px) 목록. 창 규칙은 velocity_fluctuations.track_velocities와 같다."""
    out = []
    for tid, fr in tracks.items():
        fset = set(fr)
        for f in sorted(fr):
            win = range(f - k, f + k + 1)
            if not all(g in fset for g in win):
                continue
            if any(fr[g][3] or (tid, g) in near for g in win):
                continue
            a = [fr[g][2] for g in win]
            if max(a) > 1.2 * min(a):
                continue
            out.append((tid, f, fr[f][0], fr[f][1], (fr[f + k][0] - fr[f - k][0]) / (2 * k),
                        (fr[f + k][1] - fr[f - k][1]) / (2 * k), math.sqrt(4 * float(np.median(a)) / math.pi)))
    return out


def _boot_median(vals, tids, n_boot, rng):
    """트랙 단위 부트스트랩 중앙값의 95% 구간."""
    if len(vals) < 5:
        return float("nan"), float("nan")
    by = defaultdict(list)
    for v, t in zip(vals, tids):
        by[t].append(v)
    groups = list(by.values())
    meds = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        meds.append(np.median(np.concatenate([groups[i] for i in pick])))
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def analyse(obs, H_px, px_m, fps, H_m, U_loc, sigma, mu, nbins, bins_dH, walls=None, wall_excl=1.0, n_boot=200, seed=0):
    rng = np.random.default_rng(seed)
    ob = [o for o in obs if o[4] > 0]
    if walls:
        lo, hi = walls
        ob = [o for o in ob if lo + wall_excl * o[6] <= o[3] <= hi - wall_excl * o[6]]
    elif ob:
        cs = np.array([o[3] for o in ob])
        lo, hi = float(np.percentile(cs, 1)), float(np.percentile(cs, 99))
    else:
        lo = hi = float("nan")
    rows = []
    if not ob:
        return rows, {"tanphi_uniform": float("nan"), "tilt_equiv_mrad": float("nan"), "gap_slope_equiv": float("nan"),
                      "n_obs": 0, "c_range_px": (lo, hi), "rms_uniform_as_gap": float("nan"), "rms_uniform_as_tilt": float("nan")}
    # 흐름 방향 속도는 크기마다 이동도가 달라 위치별 크기 구성에 끌린다 → d/H 구간마다 그 구간 중앙값으로 나눈 값을 쓴다
    cls = {}
    for o in ob:
        for j, (a, z) in enumerate(bins_dH):
            if a <= o[6] / H_px < z:
                cls.setdefault(j, []).append(o[4])
                break
    med_cls = {j: float(np.median(v)) for j, v in cls.items()}
    edges = np.linspace(lo, hi, nbins + 1)

    def vs_norm(o):
        for j, (a, z) in enumerate(bins_dH):
            if a <= o[6] / H_px < z:
                return o[4] / med_cls[j]
        return float("nan")
    for b in range(nbins):
        sel = [o for o in ob if edges[b] <= o[3] < edges[b + 1]]
        row = {"c_mid_px": 0.5 * (edges[b] + edges[b + 1]), "n": len(sel)}
        if len(sel) >= 5:
            tp = [o[5] / o[4] for o in sel]
            row["tanphi"] = float(np.median(tp))
            row["tanphi_lo"], row["tanphi_hi"] = _boot_median(tp, [o[0] for o in sel], n_boot, rng)
            vn = [vs_norm(o) for o in sel]
            vn = [v for v in vn if v == v]
            row["vs_ratio"] = float(np.median(vn)) if vn else float("nan")
            for (a, z) in bins_dH:
                ss = [o for o in sel if a <= o[6] / H_px < z]
                row[f"tanphi_dH_{a:g}_{z:g}"] = float(np.median([o[5] / o[4] for o in ss])) if len(ss) >= 5 else float("nan")
        rows.append(row)
    good = [r for r in rows if "tanphi" in r and r["tanphi"] == r["tanphi"] and r["vs_ratio"] == r["vs_ratio"]]
    rms_full = rms_anti = float("nan")
    if len(good) >= 3:
        c_m = np.array([r["c_mid_px"] for r in good]) * px_m
        tph = np.array([r["tanphi"] for r in good])
        Uc = U_loc * np.array([r["vs_ratio"] for r in good])
        w = np.array([r["n"] for r in good], float)
        uni = float(np.mean(tph))                      # 구간을 같은 무게로: 벽 사이 대칭 구간이면 반대칭(처짐) 몫이 지워진다
        meas = np.array([r["vs_ratio"] for r in good])
        meas = meas / (np.sum(w * meas) / np.sum(w))

        def profile(tp):
            dHdc = 12 * mu * Uc * tp / sigma
            Hc = np.concatenate([[0.0], np.cumsum(0.5 * (dHdc[1:] + dHdc[:-1]) * np.diff(c_m))])
            Hc -= np.sum(w * Hc) / np.sum(w)
            pr = (1 + Hc / H_m) ** 2
            return Hc, pr / (np.sum(w * pr) / np.sum(w))
        # 균일 성분은 위치로는 기울임과 균일 갭 기울기를 못 가른다. 흐름 방향 속도의 가로 기울기로 가른다:
        # 갭 쐐기면 U ∝ H²라 v_s에 1차 경향이 생기고, 기울임이면 없다. 두 가정의 예측을 함께 낸다.
        Hf, pf = profile(tph)
        Ha, pa = profile(tph - uni)
        rms_full = float(np.sqrt(np.sum(w * (pf - meas) ** 2) / np.sum(w)))
        rms_anti = float(np.sqrt(np.sum(w * (pa - meas) ** 2) / np.sum(w)))
        for r, h, pv, ha, pva, mv in zip(good, Hf, pf, Ha, pa, meas):
            r["dH_um"] = h * 1e6
            r["vs_pred_from_drift"] = pv
            r["dH_um_uniform_as_tilt"] = ha * 1e6
            r["vs_pred_uniform_as_tilt"] = pva
            r["vs_meas_norm"] = mv
    else:
        uni = float("nan")
    summ = {"tanphi_uniform": uni,
            "tilt_equiv_mrad": 24 * mu * U_loc * uni / (H_m * H_m * 998.0 * 9.81) * 1e3 if uni == uni else float("nan"),
            "gap_slope_equiv": 12 * mu * U_loc * uni / sigma if uni == uni else float("nan"),
            "n_obs": len(ob), "c_range_px": (lo, hi), "rms_uniform_as_gap": rms_full, "rms_uniform_as_tilt": rms_anti}
    return rows, summ


def write_rows(rows, path):
    keys = []
    for r in rows:
        for kk in r:
            if kk not in keys:
                keys.append(kk)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({kk: (f"{v:.6g}" if isinstance(v, float) else v) for kk, v in r.items()})


def make_demo(out, seed=5, w0_um=3.0, tilt_mrad=20.0):
    """합성: 폭 20 mm(1000 px, 0.02 mm/px), 갭 0.3 mm, 덮개 처짐 w(c) = w0(1 − (2c/W − 1)²)²(가운데 w0, 고정단).
    국소장 U(c) = U0·(H(c)/H̄)², 기포 흐름 방향 속도 s·U(c), 가로 속도 s·σ·∂_cH/(12μ)(I105, 원형). 크기 세 가지(s 0.4/1.0/1.5).
    가로 기울임 tilt_mrad를 더한다(가로 속도 s·H²ρg·sinθ/(24μ), I102). 위치 잡음 0.2 px. 쌍극자 요동은 넣지 않았다(경로 점검용)."""
    rng = np.random.default_rng(seed)
    px_m, fps, H, W_px, U0, sig, mu = 0.02e-3, 500.0, 0.3e-3, 1000, 0.05, 0.072, 1.0e-3
    w0 = w0_um * 1e-6
    W = W_px * px_m

    def wfun(c_m):
        x = 2 * c_m / W - 1
        return w0 * (1 - x * x) ** 2

    def dwdc(c_m):
        x = 2 * c_m / W - 1
        return w0 * 2 * (1 - x * x) * (-2 * x) * (2 / W)
    cs_m = np.linspace(0, W, 2001)
    Hbar = H + float(np.mean(wfun(cs_m)))
    rows = []
    classes = [(3.0, 0.4), (10.0, 1.0), (30.0, 1.5)]          # (d/H, s)
    tid = 0
    nf = 120
    for f0 in range(0, nf, 3):
        for dH, s in classes:
            for _ in range(4):
                tid += 1
                d_px = dH * H / px_m
                c = rng.uniform(0.08, 0.92) * W
                x = rng.uniform(0, 300) * px_m
                for f in range(f0, min(f0 + 40, nf)):
                    Hc = H + wfun(c)
                    vx = s * U0 * (Hc / Hbar) ** 2
                    vy = s * sig * dwdc(c) / (12 * mu) + s * Hc * Hc * 998.0 * 9.81 * math.sin(tilt_mrad * 1e-3) / (24 * mu)
                    rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": tid, "イベント": "",
                                 "面積(px)": f"{math.pi * d_px * d_px / 4:.3f}",
                                 "中心X": f"{x / px_m + rng.normal(0, 0.2):.3f}", "中心Y": f"{c / px_m + rng.normal(0, 0.2):.3f}",
                                 "フレーム接触": "0"})
                    x += vx / fps
                    c += vy / fps
                    if x / px_m > 4000:
                        break
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    truth = dict(wfun=wfun, dwdc=dwdc, Hbar=Hbar, U0=U0, sig=sig, mu=mu, H=H, px_m=px_m, fps=fps, W_px=W_px, tilt=tilt_mrad * 1e-3)
    return path, truth


def _demo(out):
    path, tr = make_demo(out)
    tracks = read_tracks(path, "right", tr["px_m"] * 1e3, tr["H"] * 1e3)
    obs = track_obs(tracks, 2)                          # 합성은 상호작용이 없어 겹쳐도 되므로 접촉 창을 빼지 않는다
    H_px = tr["H"] / tr["px_m"]
    rows, summ = analyse(obs, H_px, tr["px_m"], tr["fps"], tr["H"], tr["U0"], tr["sig"], tr["mu"], 10,
                         [(2, 5), (5, 15), (15, 50)], walls=(0, tr["W_px"]), wall_excl=0.0)
    write_rows(rows, os.path.join(out, "dm_bins.csv"))
    fails = []
    print("표류 지도 자가 시험(덮개 처짐 3 µm, 0.3 mm, U 0.05 m/s, 쌍극자 요동 없음)")
    edges = np.linspace(0, tr["W_px"], 11)
    for b, r in enumerate(rows):
        if not ("tanphi" in r and r["tanphi"] == r["tanphi"]):
            continue
        c_obs = np.array([o[3] for o in obs if edges[b] <= o[3] < edges[b + 1] and o[4] > 0]) * tr["px_m"]
        Uc = tr["U0"] * ((tr["H"] + tr["wfun"](c_obs)) / tr["Hbar"]) ** 2
        Hc_obs = tr["H"] + tr["wfun"](c_obs)
        want = float(np.median((tr["sig"] * tr["dwdc"](c_obs) / 12 + Hc_obs ** 2 * 998.0 * 9.81 * math.sin(tr["tilt"]) / 24)
                               / (tr["mu"] * Uc)))   # 그 구간 관측 위치에서의 정답(처짐 + 기울임)
        spread = max(abs(r[k_] - r["tanphi"]) for k_ in r if k_.startswith("tanphi_dH_") and r[k_] == r[k_])
        ok = abs(r["tanphi"] - want) <= 0.1 * abs(want) + 2e-3 and spread <= 0.1 * abs(want) + 2e-3
        print(f"  {'통과' if ok else '실패'}  c {r['c_mid_px']:6.0f} px: tanφ 도구 {r['tanphi']:+.4f}, 정답 {want:+.4f}, 크기 구간끼리 차 {spread:.4f}"
              f" | ΔH(균일 = 기울임) {r.get('dH_um_uniform_as_tilt', float('nan')):+.2f} µm, 속도비 예측 {r.get('vs_pred_uniform_as_tilt', float('nan')):.4f}"
              f" 측정 {r.get('vs_meas_norm', float('nan')):.4f}")
        if not ok:
            fails.append(r["c_mid_px"])
    good = [r for r in rows if "dH_um" in r]
    cm = np.array([r["c_mid_px"] * tr["px_m"] for r in good])
    w = np.array([r["n"] for r in good], float)
    true_dH = tr["wfun"](cm)
    true_dH = (true_dH - np.sum(w * true_dH) / np.sum(w)) * 1e6
    got = np.array([r["dH_um_uniform_as_tilt"] for r in good])
    err = float(np.max(np.abs(got - true_dH)))
    ok = err <= 0.15 * float(np.max(np.abs(true_dH)))
    print(f"  {'통과' if ok else '실패'}  ΔH(c) 최대 차 {err:.2f} µm(정답 범위 {true_dH.min():+.2f}~{true_dH.max():+.2f} µm, 구간 적분이라 몇 % 오차)")
    if not ok:
        fails.append("dH")
    pv = np.array([r["vs_pred_uniform_as_tilt"] for r in good]); mv = np.array([r["vs_meas_norm"] for r in good])
    ok = float(np.max(np.abs(pv - mv))) <= 0.01
    print(f"  {'통과' if ok else '실패'}  표류에서 예측한 흐름 방향 속도 분포 대 측정(균일 성분 = 기울임): 최대 차 {np.max(np.abs(pv - mv)):.4f}")
    if not ok:
        fails.append("vs")
    ok = summ["rms_uniform_as_tilt"] < summ["rms_uniform_as_gap"]
    print(f"  {'통과' if ok else '실패'}  균일 성분을 기울임으로 본 예측이 갭 쐐기로 본 예측보다 맞음: 잔차 {summ['rms_uniform_as_tilt']:.4f} 대 {summ['rms_uniform_as_gap']:.4f}")
    if not ok:
        fails.append("uniform")
    want_t = tr["H"] ** 2 * 998.0 * 9.81 * math.sin(tr["tilt"]) / (24 * tr["mu"] * tr["U0"])
    ok = abs(summ["tanphi_uniform"] - want_t) <= 0.15 * want_t
    print(f"  {'통과' if ok else '실패'}  균일 성분 tanφ {summ['tanphi_uniform']:+.4f}(정답 {want_t:+.4f}) → 기울임 {summ['tilt_equiv_mrad']:+.1f} mrad(정답 {tr['tilt'] * 1e3:.0f})")
    if not ok:
        fails.append("tilt")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건"))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv")
    ap.add_argument("--px_mm", type=float)
    ap.add_argument("--fps", type=float)
    ap.add_argument("--H_mm", type=float)
    ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--U_loc", type=float, help="국소장(m/s), 예: j_L/(1 − α)")
    ap.add_argument("--walls", help="두 측벽의 가로 좌표(px), 예: 120,980")
    ap.add_argument("--wall_excl", type=float, default=1.0)
    ap.add_argument("--nbins", type=int, default=12)
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--contact_gap", type=float, default=0.5)
    ap.add_argument("--sigma", type=float, default=0.072)
    ap.add_argument("--mu", type=float, default=1.0e-3)
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--out", default="dm_out")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm and a.fps and a.H_mm and a.U_loc):
        ap.error("--csv, --px_mm, --fps, --H_mm, --U_loc가 필요하다")
    os.makedirs(a.out, exist_ok=True)
    px_m = a.px_mm * 1e-3
    tracks = read_tracks(a.csv, a.flow, a.px_mm, a.H_mm)
    obs = track_obs(tracks, a.k, near_contact(tracks, a.contact_gap))
    edges = [float(x) for x in a.dH_bins.split(",")]
    bins = list(zip(edges[:-1], edges[1:]))
    walls = tuple(float(x) for x in a.walls.split(",")) if a.walls else None
    rows, summ = analyse(obs, a.H_mm / a.px_mm, px_m, a.fps, a.H_mm * 1e-3, a.U_loc, a.sigma, a.mu, a.nbins, bins,
                         walls=walls, wall_excl=a.wall_excl, n_boot=a.n_boot)
    write_rows(rows, os.path.join(a.out, "dm_bins.csv"))
    print(f"관측 {summ['n_obs']}개, 가로 범위 {summ['c_range_px'][0]:.0f}~{summ['c_range_px'][1]:.0f} px")
    if summ["n_obs"] == 0:
        print("쓸 관측이 없다: 트랙이 2k + 1 프레임보다 짧거나, 화면 끝·합체·접촉(--contact_gap) 창에 모두 걸렸다.")
        return
    for r in rows:
        if "tanphi" in r and r["tanphi"] == r["tanphi"]:
            print(f"  c {r['c_mid_px']:7.1f} px (n {r['n']:5d}): tanφ {r['tanphi']:+.4f} [{r['tanphi_lo']:+.4f}, {r['tanphi_hi']:+.4f}], "
                  f"v_s 비 {r['vs_ratio']:.3f} | ΔH {r.get('dH_um', float('nan')):+.2f} µm(균일 = 갭) / {r.get('dH_um_uniform_as_tilt', float('nan')):+.2f} µm(균일 = 기울임)"
                  f" → 예측 속도비 {r.get('vs_pred_from_drift', float('nan')):.3f} / {r.get('vs_pred_uniform_as_tilt', float('nan')):.3f}")
    print(f"균일 성분 tanφ {summ['tanphi_uniform']:+.4f}: 기울임이면 {summ['tilt_equiv_mrad']:+.2f} mrad, 균일 갭 기울기면 {summ['gap_slope_equiv']:+.2e}")
    print(f"  흐름 방향 속도 분포 잔차: 균일 성분을 갭 쐐기로 보면 {summ['rms_uniform_as_gap']:.4f}, 기울임으로 보면 {summ['rms_uniform_as_tilt']:.4f}(작은 쪽이 맞는 가정)")
    print("읽는 법: tanφ가 가운데를 향하는 반대칭이고 크기 구간끼리 같으며 1/U로 줄면 갭의 가로 분포(덮개 처짐)다(I105).")
    print("         ΔH(c)로 예측한 흐름 방향 속도비와 측정 v_s 비가 맞으면 같은 H(c)가 두 결과를 함께 설명한다.")


if __name__ == "__main__":
    main()

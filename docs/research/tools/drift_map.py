"""저유속 기포 표류 지도로 갭의 가로 분포(덮개 처짐)·기울기·액체 온도 기울기를 읽는다(아이디어 I105).

배경 (원형 팬케이크, 깊이 평균 Darcy)
    테두리 바깥 액체 압력 p_g − 2σ/H가 평면 안에서 기울면 기포는 Ψ = 2σ(T)/H − ρgζ가 낮은 쪽으로 밀린다.
    가로 표류각 tanφ = v_c/v_s = K(−∂_cΨ)/(2U), K = H²/(12μ). 크기·마찰과 무관하다(가로 응답은 할선 이동도, I102와 같은 이유).
    갭 항만 있으면 ∂_cH = 12μU·tanφ/σ다. 같은 H(c)가 국소장도 U_loc ∝ H²로 바꾼다(흐름 방향 속도의 가로 분포).
    → 가로 표류를 적분한 H(c)와 흐름 방향 속도 분포가 같은 H(c)를 말하면 갭 분포(덮개 처짐, 가공 휨)로 확인된다.
    온도 기울기(가열)가 있으면 같은 꼴로 더해진다: 갭 항 σ∂H ↔ 온도 항 H|dσ/dT|∂T(부호는 측정 대상, I105).

쓰는 법
    python drift_map.py --csv result_tracking.csv --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --U_loc 0.05 --walls 120,980 --out dm_out
        [--nbins 12] [--dH_bins 2,5,15,50] [--k 2] [--sigma 0.072] [--mu 1e-3] [--wall_excl 1.0] [--alpha 0.1 --jG 0.02] [--no_wall_image]
    python drift_map.py --demo --out dm_demo     # 덮개 처짐(가운데 3 µm) + 기울임 합성 추적으로 스스로 점검(기본 설정 그대로)

계산 (독립 검토 8 반영판, 2026-10-24)
    1. 트랙마다 중심 차분 속도 v = (x(t + k) − x(t − k))/(2k). 창 안에 화면 끝 접촉, 면적 변화 20% 초과, 빠진 프레임,
       다른 기포와의 접촉(틈 < 0.5 × 작은 쪽 반경)이 있으면 버린다(velocity_fluctuations.py와 같은 규칙). 흐름 방향 s, 가로 c 성분.
    2. 가로 위치 구간(nbins, --walls가 있으면 두 벽 사이, 없으면 관측의 1~99% 범위)마다 기포별 tanφ_i = v_c/v_s의 중앙값
       (코시 꼬리에 강함), 트랙 단위 부트스트랩 95% 구간(트랙 3개 미만이면 NaN). 구간 위치는 중점이 아니라 관측 c의 중앙값이다
       (가장자리 구간은 관측이 안쪽에 몰림, 검토 8 #2). --walls가 있으면 벽에서 wall_excl × 지름 안의 관측은 뺀다.
    3. 흐름 방향 속도 분포: 크기 구분 × 위치 구간의 2원 로그 가법 맞춤(번갈아 중앙값). 앞 판은 구분마다 그 구분 전체 중앙값으로 나눠,
       벽 제외 때문에 가운데에만 남는 큰 구분이 분포를 납작하게 만들었다(기본 설정에서 진폭 0.61배, 검토 8 #2).
       --walls가 있으면 측벽 자기 거울상(I101)을 먼저 뺀다: v_s/(1 − R(s − 1)G), G > 0.25인 관측은 분포에서 뺀다.
    4. 갭 분포: 가로 표류 V_c = s·σ∂_cH/(12μ)(I105, 할선 이동도)이므로 ∂_cH = 12μ·(V_s/s)·tanφ/σ(구간의 V_s/s 중앙값,
       s = 구분 중앙 v_s/U_loc)를 c로 적분하고 평균을 0으로 → ΔH(c). 무리 인자 (1 − α)/(1 + Σαλ)(Σαλ = j_G/U_loc − α, 검토 7·8)로 각을 나눈다.
       예측 흐름 방향 속도비 (1 + ΔH/H)^n_eff, n_eff = 크기별 2 + d ln s/d ln H(깨끗한 막, s 0.345/1/1.55에서 1.62/1.80/1.92)의 평균(검토 8 #7).
    5. 위치와 무관한 균일 성분은 기울임(I102)이나 균일 갭 기울기(쐐기)다. 벽이 있으면 tanφ = u + A·x(1 − x²)(고정단 처짐 꼴의 기울기,
       x = 2(c − 벽)/W − 1)로 맞춰 u를 낸다. 구간이 가운데에 대해 대칭이 아니면(시야가 폭 일부) 단순 평균에 처짐이 섞이므로 경고한다
       (3 µm 처짐·기울임 0·시야 70%에서 단순 평균은 기울임 26 mrad를 냈다, 검토 8 #6). 벽이 없으면 기울임 환산을 내지 않는다.
       기울임 sinθ = 24μU·tanφ/(H²ρg), 갭 기울기 12μU·tanφ/σ. 쐐기면 U ∝ H²라 v_s에 가로 1차 경향이 생기고 기울임이면 없으므로,
       4의 예측을 두 가정(균일 성분 = 갭 / = 기울임)으로 내고 측정 v_s 분포와의 잔차를 비교한다.
    6. 가열 운전이면 셋째 가설(가로 온도 기울기)을 따로 본다: v_s가 점성으로 약 +2.4%/K 바뀌는데 갭 환산 예측은 0.44%/K다.
       온도 항의 각은 테두리 마랑고니 경계층 때문에 (1 + 0.82H/d)배로 크기에 따라 다르다(검토 8 #4).
    자가 시험(--demo, 기본 wall_excl 1·접촉 필터 0.5, 크기별 지수와 측벽 거울상을 넣은 합성): 구간별 각, ΔH(c) 최대 차 0.08 µm,
       흐름 방향 분포 진폭 0.98(앞 판 0.61), 균일 성분 19.9 대 20 mrad, 시야 0~700 px면 처짐 꼴 맞춤 20.7 mrad(단순 평균 42.2)·경고,
       벽 없으면 기울임을 내지 않고 경고.
출력: dm_bins.csv(구간별 표), 요약 출력.
주의: 쌍극자 요동(I99)이 각의 잡음이다(코시 척도 약 α|λ|). 기포 수천 개면 수 mrad. 원형에 가까운 기포를 전제한다.
    덮개 처짐은 폭의 네제곱에 비례한다(아크릴 5 mm·50 kPa: 폭 50 mm 21 µm, 20 mm 0.55 µm, 검토 8 #9).
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
    if len(groups) < 3:                                  # 트랙이 셋 미만이면 구간을 낼 수 없다(한 트랙의 창끼리는 독립이 아님)
        return float("nan"), float("nan")
    meds = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        meds.append(np.median(np.concatenate([groups[i] for i in pick])))
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def mobility_exponent(s, m=2 / 3):
    """같은 지름에서 기포 속도의 갭 의존 지수 d ln V/d ln H = 2 + d ln s/d ln H(검토 8 #7가).
    국소장 U_loc ∝ H², Booth 매개변수 δ_B ∝ Ca_loc^(1/3)/H ∝ H^(−1/3), s^(2/3)/(2 − s) = δ_B(깨끗한 막)이라
    d ln s/d ln δ_B = 1/(2/3 + s/(2 − s)). s 0.345/1/1.55에서 1.62/1.80/1.92."""
    s = min(max(s, 0.05), 1.95)
    return 2.0 - (1.0 / 3.0) / (2.0 / 3.0 + s / (2.0 - s))


def R_tangent(s, m=2 / 3):
    dl = max(2 / s - 1, 0.0)
    return (1 + dl) / (1 + m * dl)


def two_way_log(vals, rows_j, cols_b, n_iter=60):
    """ln v ≈ A_j(크기 구분) + B_b(위치 구간)를 번갈아 중앙값으로 맞춘다(검토 8 #2). 구분마다 위치 분포가 달라도 B_b가 치우치지 않는다."""
    lv = np.log(vals)
    J = int(rows_j.max()) + 1 if len(rows_j) else 0
    Bn = int(cols_b.max()) + 1 if len(cols_b) else 0
    A = np.zeros(J); B = np.zeros(Bn)
    for _ in range(n_iter):
        for j in range(J):
            s_ = rows_j == j
            if s_.any():
                A[j] = float(np.median(lv[s_] - B[cols_b[s_]]))
        for b in range(Bn):
            s_ = cols_b == b
            if s_.any():
                B[b] = float(np.median(lv[s_] - A[rows_j[s_]]))
        cnt = np.bincount(cols_b, minlength=Bn).astype(float)
        if cnt.sum() > 0:
            shift = float(np.log(np.sum(cnt * np.exp(B)) / cnt.sum()))
            B -= shift; A += shift
    return A, B


def analyse(obs, H_px, px_m, fps, H_m, U_loc, sigma, mu, nbins, bins_dH, walls=None, wall_excl=1.0, n_boot=200, seed=0,
            alpha=None, jG=None, wall_image=True):
    """구간별 표류각·흐름 방향 속도 분포와 갭 분포 ΔH(c), 균일 성분. 검토 8 반영판:
    흐름 방향 속도는 크기 × 위치 2원 로그 맞춤, 구간 위치는 관측 c의 중앙값, 크기별 이동도 지수, 측벽 자기 거울상 보정,
    무리 인자 (1 − α)/(1 + Σαλ)(--alpha·--jG), 균일 성분은 벽이 있을 때 처짐 꼴과 함께 맞춘다."""
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
    nan = float("nan")
    empty = {"tanphi_uniform": nan, "tanphi_uniform_mean": nan, "tilt_equiv_mrad": nan, "gap_slope_equiv": nan, "n_obs": 0,
             "c_range_px": (lo, hi), "rms_uniform_as_gap": nan, "rms_uniform_as_tilt": nan, "swarm_factor": nan,
             "n_eff": nan, "uniform_reliable": False, "warnings": []}
    if not ob:
        return rows, empty
    warnings = []
    U_px = U_loc / (px_m * fps)                         # 국소장(px/frame)
    # 크기 구분과 그 이동도(무리·측벽 보정 전의 근사: s_j = 구분 중앙 v_s / U_loc)
    def cls_of(o):
        for j, (a, z) in enumerate(bins_dH):
            if a <= o[6] / H_px < z:
                return j
        return -1
    cj = np.array([cls_of(o) for o in ob])
    s_cls = {}
    for j in range(len(bins_dH)):
        v = [o[4] for o, c_ in zip(ob, cj) if c_ == j]
        if len(v) >= 5:
            s_cls[j] = float(np.median(v)) / U_px
    # 측벽 자기 거울상: v_s = s·U(1 − R(s − 1)G) → 나눠서 뺀다(G > 0.25면 흐름 방향 분포에서 뺌)
    W_side = (hi - lo) if walls else nan
    vs_corr = []
    for o, c_ in zip(ob, cj):
        v = o[4]
        if walls and wall_image and c_ in s_cls:
            G = (math.pi * (o[6] / 2) / (2 * W_side)) ** 2 * (1 / max(math.sin(math.pi * (o[3] - lo) / W_side), 1e-6) ** 2 + 1 / 3)
            s_ = s_cls[c_]
            if G > 0.25:
                v = nan
            else:
                v = v / (1 - R_tangent(s_) * (s_ - 1) * G)
        vs_corr.append(v)
    vs_corr = np.array(vs_corr)
    edges = np.linspace(lo, hi, nbins + 1)
    bidx = np.clip(np.searchsorted(edges, [o[3] for o in ob], side="right") - 1, 0, nbins - 1)
    # 흐름 방향 속도 분포: 크기 × 위치 2원 로그 가법 맞춤
    use = (cj >= 0) & np.isfinite(vs_corr) & (vs_corr > 0)
    vs_ratio = np.full(nbins, nan)
    n_eff = nan
    if use.sum() >= 10:
        A_, B_ = two_way_log(vs_corr[use], cj[use], bidx[use])
        cnt = np.bincount(bidx[use], minlength=nbins)
        for b in range(nbins):
            if b < len(B_) and cnt[b] >= 3:
                vs_ratio[b] = math.exp(B_[b])
        ws = np.array([mobility_exponent(s_cls[j]) for j in cj[use] if j in s_cls]) if s_cls else np.array([])
        n_eff = float(np.mean(ws)) if len(ws) else 2.0
    else:
        warnings.append("흐름 방향 속도 분포를 맞출 관측이 10개 미만이다.")
    # 무리 인자(가로 표류를 줄임): (1 − α)/(1 + Σαλ), Σαλ = j_G/U_loc − α(검토 7·8)
    F = 1.0
    if alpha is not None and jG is not None and alpha == alpha and jG == jG:
        sal = jG / U_loc - alpha
        F = (1 - alpha) / (1 + sal)
    for b in range(nbins):
        sel_i = np.nonzero(bidx == b)[0]
        sel = [ob[i] for i in sel_i]
        row = {"c_mid_px": 0.5 * (edges[b] + edges[b + 1]), "c_pos_px": float(np.median([o[3] for o in sel])) if sel else nan,
               "n": len(sel)}
        if len(sel) >= 5:
            tp = [o[5] / o[4] for o in sel]
            row["tanphi"] = float(np.median(tp))
            row["tanphi_lo"], row["tanphi_hi"] = _boot_median(tp, [o[0] for o in sel], n_boot, rng)
            row["n_tracks"] = len(set(o[0] for o in sel))
            row["vs_ratio"] = float(vs_ratio[b])
            ue = [o[4] / s_cls[cj[i]] for i, o in zip(sel_i, sel) if cj[i] in s_cls]
            row["U_eff_mps"] = float(np.median(ue)) * px_m * fps if ue else U_loc   # ∂H = 12μ·(V_s/s)·tanφ/σ에 쓰는 국소장
            for (a, z) in bins_dH:
                ss = [o for o in sel if a <= o[6] / H_px < z]
                row[f"tanphi_dH_{a:g}_{z:g}"] = float(np.median([o[5] / o[4] for o in ss])) if len(ss) >= 5 else nan
        rows.append(row)
    good = [r for r in rows if "tanphi" in r and r["tanphi"] == r["tanphi"] and r["vs_ratio"] == r["vs_ratio"]]
    rms_full = rms_anti = nan
    uni_mean = uni_fit = nan
    reliable = False
    if len(good) >= 3:
        c_pos = np.array([r["c_pos_px"] for r in good])
        c_m = c_pos * px_m
        tph = np.array([r["tanphi"] for r in good]) / F
        w = np.array([r["n"] for r in good], float)
        uni_mean = float(np.mean(tph))
        if walls:
            x = 2 * (c_pos - lo) / W_side - 1
            Xd = np.stack([np.ones_like(x), x * (1 - x * x)], 1)    # 균일 + 고정단 처짐 꼴 (1 − x²)²의 기울기 ∝ x(1 − x²)
            sw = np.sqrt(w)
            coef, *_ = np.linalg.lstsq(Xd * sw[:, None], tph * sw, rcond=None)
            uni_fit = float(coef[0])
            xm = float(np.sum(w * x) / np.sum(w))
            cover = (c_pos.max() - c_pos.min()) / W_side
            reliable = True
            if abs(xm) > 0.1 or cover < 0.7:
                warnings.append(f"구간이 채널 가운데에 대해 대칭이 아니다(무게 중심 x {xm:+.2f}, 덮은 폭 {cover:.0%}). 단순 평균 균일 성분은 처짐이 섞인다 → 처짐 꼴 맞춤 값을 쓴다(처짐 꼴이 고정단 (1 − x²)²라는 가정).")
        else:
            warnings.append("--walls가 없으면 균일 성분(기울임·쐐기)을 처짐과 가를 수 없다(시야 일부만 보면 처짐의 한쪽 날개가 균일 성분이 됨, 검토 8 #6). 기울임 환산을 내지 않는다.")
        uni = uni_fit if walls else uni_mean
        meas = np.array([r["vs_ratio"] for r in good])
        meas = meas / (np.sum(w * meas) / np.sum(w))
        U_eff = np.array([r["U_eff_mps"] for r in good])   # 구간의 V_s/s(가로 표류 V_c = s·σ∂H/(12μ)를 각으로 바꾼 분모)

        def profile(tp):
            dHdc = 12 * mu * U_eff * tp / sigma
            Hc = np.concatenate([[0.0], np.cumsum(0.5 * (dHdc[1:] + dHdc[:-1]) * np.diff(c_m))])
            Hc -= np.sum(w * Hc) / np.sum(w)
            pr = (1 + Hc / H_m) ** n_eff
            return Hc, pr / (np.sum(w * pr) / np.sum(w))
        Hf, pf = profile(tph)
        Ha, pa = profile(tph - (uni if uni == uni else uni_mean))
        rms_full = float(np.sqrt(np.sum(w * (pf - meas) ** 2) / np.sum(w)))
        rms_anti = float(np.sqrt(np.sum(w * (pa - meas) ** 2) / np.sum(w)))
        for r, h, pv, ha, pva, mv in zip(good, Hf, pf, Ha, pa, meas):
            r["dH_um"] = h * 1e6
            r["vs_pred_from_drift"] = pv
            r["dH_um_uniform_as_tilt"] = ha * 1e6
            r["vs_pred_uniform_as_tilt"] = pva
            r["vs_meas_norm"] = mv
    uni = uni_fit if walls else nan
    summ = {"tanphi_uniform": uni, "tanphi_uniform_mean": uni_mean,
            "tilt_equiv_mrad": 24 * mu * U_loc * uni / (H_m * H_m * 998.0 * 9.81) * 1e3 if uni == uni else nan,
            "gap_slope_equiv": 12 * mu * U_loc * uni / sigma if uni == uni else nan,
            "n_obs": len(ob), "c_range_px": (lo, hi), "rms_uniform_as_gap": rms_full, "rms_uniform_as_tilt": rms_anti,
            "swarm_factor": F, "n_eff": n_eff, "uniform_reliable": reliable, "warnings": warnings}
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


def make_demo(out, seed=5, w0_um=3.0, tilt_mrad=20.0, nf=360, wall_image=True):
    """합성: 폭 20 mm(1000 px, 0.02 mm/px), 갭 0.3 mm, 덮개 처짐 w(c) = w0(1 − (2c/W − 1)²)²(가운데 w0, 고정단).
    기포 흐름 방향 속도 s·U0·(H(c)/H̄)^n(s)·(1 − R(s − 1)G)(크기별 이동도 지수 n, 측벽 자기 거울상 G, 검토 8 #7),
    가로 속도 s·σ·∂_cH/(12μ)(I105) + s·H²ρg·sinθ/(24μ)(I102). 크기 세 가지(d/H 3/10/30, s 0.4/1.0/1.5).
    검토 8 #2: 기본 설정(wall_excl 1, 접촉 필터 0.5)으로 돌 수 있게 겹치지 않게 놓는다. 크기 구분마다 시간 구획을 따로 둬서
    앞지르기 접촉을 없앴다(같은 구분은 속도가 거의 같아 처음에 안 겹치면 계속 안 겹침). 위치 잡음 0.2 px, 쌍극자 요동 없음."""
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
    classes = [(3.0, 0.4), (10.0, 1.0), (30.0, 1.5)]          # (d/H, s)
    rows = []
    tid = 0
    block = nf // len(classes)
    for ci, (dH, s) in enumerate(classes):
        a_px = dH * H / px_m / 2
        n_exp = mobility_exponent(s)
        R = R_tangent(s)
        f0, f1 = ci * block, (ci + 1) * block
        placed = []
        target = {0: 60, 1: 20, 2: 6}[ci]
        tries = 0
        while len(placed) < target and tries < 50000:
            tries += 1
            c = rng.uniform(a_px + 1, W_px - a_px - 1)
            x = rng.uniform(0, 2500)
            if any(math.hypot(x - xx, c - cc) < 2 * a_px * 1.6 for xx, cc in placed):
                continue
            placed.append((x, c))
        for x_px, c_px in placed:
            tid += 1
            x, c = x_px * px_m, c_px * px_m
            for f in range(f0, f1):
                Hc = H + wfun(c)
                G = (math.pi * a_px / (2 * W_px)) ** 2 * (1 / math.sin(math.pi * c / W) ** 2 + 1 / 3) if wall_image else 0.0
                vx = s * U0 * (Hc / Hbar) ** n_exp * (1 - R * (s - 1) * G)
                vy = s * sig * dwdc(c) / (12 * mu) + s * Hc * Hc * 998.0 * 9.81 * math.sin(tilt_mrad * 1e-3) / (24 * mu)
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": tid, "イベント": "",
                             "面積(px)": f"{math.pi * a_px * a_px:.3f}",
                             "中心X": f"{x / px_m + rng.normal(0, 0.2):.3f}", "中心Y": f"{c / px_m + rng.normal(0, 0.2):.3f}",
                             "フレーム接触": "0"})
                x += vx / fps
                c += vy / fps
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    truth = dict(wfun=wfun, dwdc=dwdc, Hbar=Hbar, U0=U0, sig=sig, mu=mu, H=H, px_m=px_m, fps=fps, W_px=W_px, tilt=tilt_mrad * 1e-3,
                 classes=classes, wall_image=wall_image)
    return path, truth


def _truth_tanphi(tr, c_px, dH):
    """관측 하나(가로 위치, d/H)의 정답 tanφ = v_c/v_s."""
    s = dict(tr["classes"])[dH]
    c = c_px * tr["px_m"]; W = tr["W_px"] * tr["px_m"]
    Hc = tr["H"] + tr["wfun"](c)
    a_px = dH * tr["H"] / tr["px_m"] / 2
    G = (math.pi * a_px / (2 * tr["W_px"])) ** 2 * (1 / math.sin(math.pi * c / W) ** 2 + 1 / 3) if tr["wall_image"] else 0.0
    vx = s * tr["U0"] * (Hc / tr["Hbar"]) ** mobility_exponent(s) * (1 - R_tangent(s) * (s - 1) * G)
    vy = s * tr["sig"] * tr["dwdc"](c) / (12 * tr["mu"]) + s * Hc * Hc * 998.0 * 9.81 * math.sin(tr["tilt"]) / (24 * tr["mu"])
    return vy / vx


def _demo(out):
    path, tr = make_demo(out)
    tracks = read_tracks(path, "right", tr["px_m"] * 1e3, tr["H"] * 1e3)
    obs = track_obs(tracks, 2, near_contact(tracks, 0.5))          # 기본 설정: 접촉 필터 켬
    H_px = tr["H"] / tr["px_m"]
    bins = [(2, 5), (5, 15), (15, 50)]
    rows, summ = analyse(obs, H_px, tr["px_m"], tr["fps"], tr["H"], tr["U0"], tr["sig"], tr["mu"], 10, bins,
                         walls=(0, tr["W_px"]), wall_excl=1.0)          # 기본 wall_excl 1.0
    write_rows(rows, os.path.join(out, "dm_bins.csv"))
    fails = []
    print(f"표류 지도 자가 시험(덮개 처짐 3 µm + 기울임 20 mrad, 0.3 mm, U 0.05 m/s, 기본 설정 wall_excl 1·접촉 필터 0.5, 관측 {summ['n_obs']}개)")
    if summ["n_obs"] < 1000:
        print("  실패: 기본 설정에서 관측이 너무 적다"); return False
    edges = np.linspace(0, tr["W_px"], 11)
    dH_of = {}
    for o in obs:
        for a, z in bins:
            if a <= o[6] / H_px < z:
                dH_of[(o[0], o[1])] = {(2, 5): 3.0, (5, 15): 10.0, (15, 50): 30.0}[(a, z)]
    ob_ok = [o for o in obs if o[4] > 0 and o[6] * 1.0 <= o[3] <= tr["W_px"] - o[6] * 1.0]
    for b, r in enumerate(rows):
        if not ("tanphi" in r and r["tanphi"] == r["tanphi"]):
            continue
        sel = [o for o in ob_ok if edges[b] <= o[3] < edges[b + 1]]
        want = float(np.median([_truth_tanphi(tr, o[3], dH_of[(o[0], o[1])]) for o in sel]))
        if r.get("n_tracks", 0) < 3:
            print(f"  건너뜀  c {r['c_pos_px']:6.0f} px: 트랙 {r.get('n_tracks', 0)}개라 구간을 낼 수 없다(도구도 구간 NaN)")
            continue
        # 정답과의 차를 그 구간 부트스트랩 구간 폭(관측이 적은 가장자리 구간의 잡음)까지 허용한다
        tol = 0.1 * abs(want) + 2e-3 + 0.5 * (r["tanphi_hi"] - r["tanphi_lo"])
        ok = abs(r["tanphi"] - want) <= tol
        worst = 0.0                                          # 크기 구분마다 자기 정답과 비교(측벽 거울상 때문에 큰 기포의 각은 물리적으로 조금 다르다)
        for (lo_, hi_), dHv in zip(bins, (3.0, 10.0, 30.0)):
            ss = [o for o in sel if dH_of.get((o[0], o[1])) == dHv]
            if len(ss) >= 20:
                d_ = abs(float(np.median([o[5] / o[4] for o in ss])) - float(np.median([_truth_tanphi(tr, o[3], dHv) for o in ss])))
                worst = max(worst, d_ - (0.15 * abs(want) + 4e-3))
        ok = ok and worst <= 0
        print(f"  {'통과' if ok else '실패'}  c {r['c_pos_px']:6.0f} px(n {r['n']}): tanφ 도구 {r['tanphi']:+.4f} [{r['tanphi_lo']:+.4f}, {r['tanphi_hi']:+.4f}], 정답 {want:+.4f}")
        if not ok:
            fails.append(f"tanphi {b}")
    good = [r for r in rows if "dH_um" in r]
    cm = np.array([r["c_pos_px"] * tr["px_m"] for r in good])
    w = np.array([r["n"] for r in good], float)
    true_dH = tr["wfun"](cm)
    true_dH = (true_dH - np.sum(w * true_dH) / np.sum(w)) * 1e6
    got = np.array([r["dH_um_uniform_as_tilt"] for r in good])
    err = float(np.max(np.abs(got - true_dH)))
    ok = err <= 0.15 * float(np.max(np.abs(true_dH)))
    print(f"  {'통과' if ok else '실패'}  ΔH(c) 최대 차 {err:.2f} µm(정답 범위 {true_dH.min():+.2f}~{true_dH.max():+.2f} µm)")
    if not ok:
        fails.append("dH")
    # 흐름 방향 속도 분포의 진폭(검토 8 #2): 측정(2원 맞춤, 측벽 거울상 뺌) 대 정답(관측 위치의 (H/H̄)^n 평균)
    tv = []
    for b, r in enumerate(rows):
        if "dH_um" not in r:
            continue
        sel = [o for o in ob_ok if edges[b] <= o[3] < edges[b + 1]]
        tv.append(np.mean([((tr["H"] + tr["wfun"](o[3] * tr["px_m"])) / tr["Hbar"]) ** mobility_exponent(dict(tr["classes"])[dH_of[(o[0], o[1])]])
                           for o in sel]))
    tv = np.array(tv); tv = tv / (np.sum(w * tv) / np.sum(w))
    mv = np.array([r["vs_meas_norm"] for r in good])
    amp = (mv.max() - mv.min()) / (tv.max() - tv.min())
    ok = 0.85 <= amp <= 1.15 and float(np.max(np.abs(mv - tv))) <= 0.004
    print(f"  {'통과' if ok else '실패'}  흐름 방향 속도 분포: 측정/정답 진폭 {amp:.3f}, 최대 차 {np.max(np.abs(mv - tv)):.4f}(앞 판 기본 설정은 0.61)")
    if not ok:
        fails.append("amplitude")
    pv = np.array([r["vs_pred_uniform_as_tilt"] for r in good])
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
    print(f"  {'통과' if ok else '실패'}  균일 성분(처짐 꼴 함께 맞춤) tanφ {summ['tanphi_uniform']:+.4f}(정답 {want_t:+.4f}) → 기울임 {summ['tilt_equiv_mrad']:+.1f} mrad(정답 {tr['tilt'] * 1e3:.0f})")
    if not ok:
        fails.append("tilt")
    # 시야가 폭 일부(0~700 px)만 볼 때(검토 8 #6): 벽이 있으면 처짐 꼴 맞춤이 기울임을 되찾고, 벽이 없으면 기울임을 내지 않는다
    part = [o for o in obs if o[3] < 700]
    _, s_part = analyse(part, H_px, tr["px_m"], tr["fps"], tr["H"], tr["U0"], tr["sig"], tr["mu"], 7, bins, walls=(0, tr["W_px"]), wall_excl=1.0)
    ok = abs(s_part["tanphi_uniform"] - want_t) <= 0.25 * want_t and any("대칭이 아니다" in x for x in s_part["warnings"])
    print(f"  {'통과' if ok else '실패'}  시야 0~700 px + 벽: 처짐 꼴 맞춤 기울임 {s_part['tilt_equiv_mrad']:+.1f} mrad(단순 평균이면 "
          f"{24 * tr['mu'] * tr['U0'] * s_part['tanphi_uniform_mean'] / (tr['H'] ** 2 * 998.0 * 9.81) * 1e3:+.1f}), 비대칭 경고 {'있음' if s_part['warnings'] else '없음'}")
    if not ok:
        fails.append("partial")
    _, s_nw = analyse(part, H_px, tr["px_m"], tr["fps"], tr["H"], tr["U0"], tr["sig"], tr["mu"], 7, bins, walls=None)
    ok = s_nw["tilt_equiv_mrad"] != s_nw["tilt_equiv_mrad"] and any("--walls" in x for x in s_nw["warnings"])
    print(f"  {'통과' if ok else '실패'}  벽 없음: 기울임 환산을 내지 않고 경고(단순 평균 tanφ {s_nw['tanphi_uniform_mean']:+.4f}는 처짐이 섞임)")
    if not ok:
        fails.append("nowalls")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(map(str, fails))))
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
    ap.add_argument("--alpha", type=float, help="영상 기공률 α(무리 인자 (1 − α)/(1 + Σαλ)에 씀, --jG와 함께)")
    ap.add_argument("--jG", type=float, help="기체 겉보기 속도 j_G(m/s). Σαλ = j_G/U_loc − α")
    ap.add_argument("--no_wall_image", action="store_true", help="측벽 자기 거울상 보정을 끈다(--walls가 있을 때 기본으로 켬)")
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
                         walls=walls, wall_excl=a.wall_excl, n_boot=a.n_boot, alpha=a.alpha, jG=a.jG, wall_image=not a.no_wall_image)
    write_rows(rows, os.path.join(a.out, "dm_bins.csv"))
    print(f"관측 {summ['n_obs']}개, 가로 범위 {summ['c_range_px'][0]:.0f}~{summ['c_range_px'][1]:.0f} px")
    if summ["n_obs"] == 0:
        print("쓸 관측이 없다: 트랙이 2k + 1 프레임보다 짧거나, 화면 끝·합체·접촉(--contact_gap) 창에 모두 걸렸다.")
        return
    for wmsg in summ["warnings"]:
        print("  경고: " + wmsg)
    print(f"  무리 인자 {summ['swarm_factor']:.3f}(--alpha·--jG가 없으면 1), 흐름 방향 속도의 갭 지수 n_eff {summ['n_eff']:.2f}(크기별 2 + d ln s/d ln H의 평균)")
    for r in rows:
        if "tanphi" in r and r["tanphi"] == r["tanphi"]:
            print(f"  c {r['c_pos_px']:7.1f} px (n {r['n']:5d}, 트랙 {r.get('n_tracks', 0)}): tanφ {r['tanphi']:+.4f} [{r['tanphi_lo']:+.4f}, {r['tanphi_hi']:+.4f}], "
                  f"v_s 비 {r['vs_ratio']:.3f} | ΔH {r.get('dH_um', float('nan')):+.2f} µm(균일 = 갭) / {r.get('dH_um_uniform_as_tilt', float('nan')):+.2f} µm(균일 = 기울임)"
                  f" → 예측 속도비 {r.get('vs_pred_from_drift', float('nan')):.3f} / {r.get('vs_pred_uniform_as_tilt', float('nan')):.3f}")
    print(f"균일 성분 tanφ {summ['tanphi_uniform']:+.4f}(처짐 꼴과 함께 맞춤, 벽 필요; 단순 평균 {summ['tanphi_uniform_mean']:+.4f}): "
          f"기울임이면 {summ['tilt_equiv_mrad']:+.2f} mrad, 균일 갭 기울기면 {summ['gap_slope_equiv']:+.2e}")
    print(f"  흐름 방향 속도 분포 잔차: 균일 성분을 갭 쐐기로 보면 {summ['rms_uniform_as_gap']:.4f}, 기울임으로 보면 {summ['rms_uniform_as_tilt']:.4f}(작은 쪽이 맞는 가정)")
    print("읽는 법: tanφ가 가운데를 향하는 반대칭이고 크기 구간끼리 같으며 1/U로 줄면 갭의 가로 분포(덮개 처짐)다(I105).")
    print("         ΔH(c)로 예측한 흐름 방향 속도비와 측정 v_s 비가 맞으면 같은 H(c)가 두 결과를 함께 설명한다.")
    print("         가열 운전이면 셋째 가설(가로 온도 기울기)을 따로 본다: 점성 때문에 v_s가 약 +2.4%/K 바뀌는데, 같은 각을 갭으로 바꾼 예측은 0.44%/K라")
    print("         두 결과가 약 다섯 배 어긋나는 것 자체가 온도의 신호다(검토 8 #7라). 온도 항의 각은 크기에 따라 (1 + 0.82H/d)배다(테두리 마랑고니 경계층).")


if __name__ == "__main__":
    main()

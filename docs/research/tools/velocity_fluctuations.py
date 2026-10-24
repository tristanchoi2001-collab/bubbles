"""추적 속도 요동으로 쌍극자 세기 Σα|λ|(아이디어 I99)와 마찰 지수 m(I100)을 읽는다.

배경
    기포 i의 속도는 V_i = s_i·(U_loc + u'_i)이고, u'_i는 이웃의 2차원 쌍극자 장 λ_jU·a_j²(cos 2θ, sin 2θ)/r²의 합이다.
    무작위 배치에서 그 합은 코시 분포이고 척도는 U·Σα_j|λ_j|·g(α), g ≈ 1/(1 + 6.7α)(몬테카를로, 그림 r16)다. 흐름 방향과 가로가 같다.
    마찰이 D ∝ V^m이면 흐름 방향 요동은 접선 이동도 2/(1 + mΔ), 가로 요동은 할선 이동도 2/(1 + Δ)로 응답한다(원형).
    그래서 비 R = (흐름 방향 폭)/(가로 폭) = (1 + Δ)/(1 + mΔ), Δ = 2/s − 1이다.

쓰는 법
    python velocity_fluctuations.py --csv result_tracking.csv --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --out vf_out
        [--k 2] [--smooth 1] [--frame_area_px 452608] [--U_loc 0.05] [--dH_bins 2,5,15,50]
    python velocity_fluctuations.py --demo --out vf_demo      # 쌍극자 상호작용을 넣은 합성 추적으로 스스로 점검

계산
    1. 트랙마다 중심 좌표(中心X/Y)의 중심 차분 속도 v(t) = (x(t + k) − x(t − k))/(2k)(px/frame). 창 안에 화면 끝 접촉,
       면적 변화 20% 초과(합체·분열), 빠진 프레임, 다른 기포와의 틈 < contact_gap × 작은 쪽 반경(접촉·윤활)이 있으면 버린다. CSV의 앞끝 EMA 속도는 요동을 깎으므로 쓰지 않는다.
       --smooth N이면 같은 트랙에서 N프레임 이동 평균을 두 방향에 똑같이 건다(철 바닥 홈 주기를 지우는 데 쓴다, I96).
    2. 흐름 방향(s)·가로(c) 성분으로 돌리고 d/H 구분으로 나눈다.
    3. 프레임·구분마다 중앙값을 빼고 그 구분의 평균 흐름 방향 속도로 나눈다(펌프 맥동 같은 공통 요동 제거).
       같은 구분 안의 크기 의존은 ln d에 대한 1차 회귀로 뺀다(흐름 방향만 부풀리지 않게).
    4. 위치 잡음 σ_p = 1.4826·MAD(위치 2차 차분)/√6(흰 잡음 가정), 속도 잡음 σ_v = σ_p/(√2·k)/√smooth.
    5. 반사분위폭(half-IQR)을 코시(γ) ⊗ 정규(σ_v)의 반사분위폭에 맞춰 γ를 푼다(분위수 맞춤 디컨볼루션).
    6. 트랙 단위 부트스트랩(--n_boot)으로 γ와 R의 95% 구간.
    7. --frame_area_px가 있으면 α(프레임 면적 비)와 |λ|_eff = γ_c/(α·g(α))(단분산 보정, 섞이면 Σα|λ|/α).
       --U_loc(국소장, m/s)이 있으면 s = V̄/U_loc, Δ = 2/s − 1, m = ((1 + Δ)/R − 1)/Δ(원형, I100).
    8. --regress: 프레임마다 모든 기포의 쌍극자 장을 계산해(λ = 구분별 V̄/U_loc − 1, --walls면 측벽 거울상) 속도와 같은 창으로
       평균하고, 속도 잔차를 흐름 방향·가로로 따로 회귀한다. 기울기가 접선·할선 이동도이고 비 R_reg는 배치 비등방과 무관하다.
       합성 시험(331개 × 260프레임): 작은 기포 가로 기울기 0.347(정답 0.345), R_reg 1.299(이론 1.381, −6% → m +0.05),
       큰 기포 R_reg 1.082(정답 1.081). 폭의 비 R은 같은 자료에서 배치에 따라 장의 폭 비가 0.83~1.28로 흔들려 쓰기 어렵다.
출력: vf_classes.csv(구분별 표), 요약 출력.
주의: I100은 원형에 가까운 기포를 전제한다. 크기·모양 이질성, 홈, 측벽은 흐름 방향이나 가로 한쪽만 부풀린다(I99·I100 설계 참조).
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

Q75 = 0.6744897501960817


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


_YQ = np.linspace(-9.0, 9.0, 3601)
_WQ = np.exp(-_YQ ** 2 / 2)
_WQ /= _WQ.sum()


def voigt_hiqr(gamma, sigma):
    """코시(γ) ⊗ 정규(σ)의 반사분위폭. P(|X| < q) = ∫φ(y)[atan((q − y)/γ) − atan((−q − y)/γ)]/π dy = 1/2를 푼다."""
    if sigma <= 0:
        return gamma
    if gamma <= 0:
        return Q75 * sigma
    y = _YQ * sigma

    def p(q):
        return float(np.sum(_WQ * (np.arctan((q - y) / gamma) - np.arctan((-q - y) / gamma))) / math.pi)
    lo, hi = 0.0, gamma + 3 * sigma
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if p(mid) < 0.5:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def gamma_from_hiqr(h, sigma):
    """잰 반사분위폭 h와 잡음 σ에서 코시 척도 γ(잡음보다 좁으면 0)."""
    if not h > 0:
        return float("nan")
    if h <= Q75 * sigma:
        return 0.0
    lo, hi = 0.0, h
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if voigt_hiqr(mid, sigma) < h:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def hiqr(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) < 8:
        return float("nan")
    q1, q3 = np.percentile(v, [25, 75])
    return float((q3 - q1) / 2)


def read_tracks(path, flow, px_mm, H_mm):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ax, sgn = axis_of(flow)
    tracks = defaultdict(dict)                          # 트랙 → {프레임: (s, c, 면적, 끝 접촉)}
    for r in rows:
        tid = r.get("トラックID")
        if not tid or r.get("イベント") == "気泡なし":
            continue
        x, y, A = _f(r.get("中心X")), _f(r.get("中心Y")), _f(r.get("面積(px)"))
        if not (x == x and y == y and A > 0):
            continue
        s_, c_ = (sgn * y, x) if ax == "Y" else (sgn * x, y)
        tracks[tid][int(r["フレーム"])] = (s_, c_, A, r.get("フレーム接触") == "1")
    return tracks


def near_contact(tracks, gap_frac):
    """(트랙, 프레임) 가운데 다른 기포와의 틈이 gap_frac × (작은 쪽 반경)보다 좁은 것. 접촉·윤활 변위는 쌍극자 장이 아니다."""
    near = set()
    if not gap_frac > 0:
        return near
    per_frame = defaultdict(list)
    for tid, fr in tracks.items():
        for f, (s_, c_, A, _) in fr.items():
            per_frame[f].append((tid, s_, c_, math.sqrt(A / math.pi)))
    for f, lst in per_frame.items():
        if len(lst) < 2:
            continue
        arr = np.array([[x[1], x[2], x[3]] for x in lst])
        gap = np.hypot(arr[:, None, 0] - arr[None, :, 0], arr[:, None, 1] - arr[None, :, 1]) - (arr[:, None, 2] + arr[None, :, 2])
        np.fill_diagonal(gap, np.inf)
        bad = (gap < gap_frac * np.minimum(arr[:, None, 2], arr[None, :, 2])).any(1)
        near.update((x[0], f) for x, b in zip(lst, bad) if b)
    return near


def track_velocities(tracks, k, smooth, H_px, near=frozenset()):
    """(트랙, 프레임, v_s, v_c, d/H) 목록과 위치 2차 차분 표본. 창 안에 접촉 근처(near) 프레임이 있으면 버린다."""
    obs, dd = [], []
    for tid, fr in tracks.items():
        fs = sorted(fr)
        fset = set(fs)
        for f in fs:                                    # 위치 2차 차분(잡음 추정)
            if f - 1 in fset and f + 1 in fset and not (fr[f - 1][3] or fr[f][3] or fr[f + 1][3]):
                dd.append((fr[f + 1][0] - 2 * fr[f][0] + fr[f - 1][0], fr[f + 1][1] - 2 * fr[f][1] + fr[f - 1][1]))
        vel = {}
        for f in fs:
            win = range(f - k, f + k + 1)
            if not all(g in fset for g in win):
                continue
            if any(fr[g][3] or (tid, g) in near for g in win):
                continue
            a = [fr[g][2] for g in win]
            if max(a) > 1.2 * min(a):
                continue
            vel[f] = ((fr[f + k][0] - fr[f - k][0]) / (2 * k), (fr[f + k][1] - fr[f - k][1]) / (2 * k), float(np.median(a)))
        if smooth > 1:
            sm = {}
            for f in vel:
                win = [g for g in range(f - smooth // 2, f - smooth // 2 + smooth)]
                if all(g in vel for g in win):
                    sm[f] = (float(np.mean([vel[g][0] for g in win])), float(np.mean([vel[g][1] for g in win])), vel[f][2])
            vel = sm
        for f, (vs, vc, A) in vel.items():
            obs.append((tid, f, vs, vc, math.sqrt(4 * A / math.pi) / H_px))
    return obs, np.array(dd) if dd else np.zeros((0, 2))


def dipole_fields(tracks, lam_of, H_px, U_px, walls=None, periodic=None):
    """프레임마다 모든 기포(화면 끝 포함)를 원천으로 2차원 쌍극자 장 D_j(cos 2θ, sin 2θ)/r²을 각 기포 중심에서 더한다.
    D_j = λ_j·U·a_j²(λ_j = lam_of(d/H)). walls = (c_lo, c_hi)면 측벽 거울상(같은 부호, 2W 주기, n = −2…2)을 넣는다.
    periodic = (L_s, L_c)는 합성 시험용(최소 거울상, 반경 L_c/2에서 자름). 반환 {(트랙, 프레임): (u_s, u_c)}(px/frame)."""
    per_frame = defaultdict(list)
    for tid, fr in tracks.items():
        for f, (s_, c_, A, _) in fr.items():
            per_frame[f].append((tid, s_, c_, math.sqrt(A / math.pi)))
    out = {}
    for f, lst in per_frame.items():
        S = np.array([x[1] for x in lst]); C = np.array([x[2] for x in lst]); a = np.array([x[3] for x in lst])
        D = np.array([lam_of(2 * r / H_px) for r in a]) * U_px * a * a
        n0 = len(S)
        if periodic:
            S, C = S % periodic[0], C % periodic[1]
        SS, CC, DD = [S], [C], [D]
        if walls and not periodic:
            lo, hi = walls
            W = hi - lo
            for n in range(-2, 3):
                if n:
                    SS.append(S); CC.append(C + 2 * n * W); DD.append(D)
                SS.append(S); CC.append(2 * lo - C + 2 * n * W); DD.append(D)
        SS, CC, DD = np.concatenate(SS), np.concatenate(CC), np.concatenate(DD)
        ds = S[:, None] - SS[None, :]
        dc = C[:, None] - CC[None, :]
        if periodic:
            ds -= periodic[0] * np.round(ds / periodic[0]); dc -= periodic[1] * np.round(dc / periodic[1])
        r2 = ds * ds + dc * dc
        r2[np.arange(n0), np.arange(n0)] = np.inf
        if periodic:
            r2[r2 > (0.5 * min(periodic)) ** 2] = np.inf
        r4 = r2 * r2
        us = (DD[None, :] * (ds * ds - dc * dc) / r4).sum(1)
        uc = (DD[None, :] * 2 * ds * dc / r4).sum(1)
        for (tid, *_), u1, u2 in zip(lst, us, uc):
            out[(tid, f)] = (float(u1), float(u2))
    return out


def class_lambda(obs, bins, U_px):
    """d/H 구분별 λ = V̄/U_loc − 1(중앙값). 구분 밖은 0."""
    lam = []
    for lo, hi in bins:
        v = [o[2] for o in obs if lo <= o[4] < hi]
        lam.append((lo, hi, float(np.median(v)) / U_px - 1 if len(v) >= 10 else 0.0))

    def lam_of(dh):
        for lo, hi, l in lam:
            if lo <= dh < hi:
                return l
        return 0.0
    return lam_of


def window_fields(fields, obs, k, smooth):
    """속도와 같은 창(중심 차분 2k + 이동 평균 smooth)으로 장을 평균한다. 창 길이가 다르면 빠르게 변하는 성분의 기울기가 깎인다."""
    out = {}
    n = max(smooth, 1)
    for o in obs:
        w = defaultdict(float)                          # v(h)는 h − k … h + k − 1의 이동을 담는다
        for h in range(o[1] - n // 2, o[1] - n // 2 + n):
            for g in range(h - k, h + k):
                w[g] += 1.0
        vals = [(fields.get((o[0], g)), wt) for g, wt in w.items()]
        vals = [(v, wt) for v, wt in vals if v is not None]
        if vals:
            sw = sum(wt for _, wt in vals)
            out[(o[0], o[1])] = (sum(v[0] * wt for v, wt in vals) / sw, sum(v[1] * wt for v, wt in vals) / sw)
    return out


def analyse(obs, dd, k, smooth, bins, frame_alpha=None, U_loc_px=None, n_boot=200, seed=0, fields=None):
    sig_p = float(np.mean([1.4826 * np.median(np.abs(dd[:, j] - np.median(dd[:, j]))) for j in (0, 1)]) / math.sqrt(6)) if len(dd) > 20 else float("nan")
    sig_v = sig_p / (math.sqrt(2) * k) / math.sqrt(max(smooth, 1))
    rng = np.random.default_rng(seed)
    out = []
    for lo, hi in bins:
        sel = [o for o in obs if lo <= o[4] < hi]
        if len(sel) < 30:
            continue
        tid = np.array([o[0] for o in sel]); fr = np.array([o[1] for o in sel])
        vs = np.array([o[2] for o in sel]); vc = np.array([o[3] for o in sel]); dh = np.array([o[4] for o in sel])
        Vbar = float(np.median(vs))
        if not Vbar > 0:
            continue
        rs, rc = vs.copy(), vc.copy()
        for f in np.unique(fr):                         # 프레임·구분 중앙값(공통 요동) 빼기
            m = fr == f
            if m.sum() >= 3:
                rs[m] -= np.median(vs[m]) - Vbar
                rc[m] -= np.median(vc[m])
            else:
                rc[m] -= np.median(vc)
        rc = rc - np.median(rc)
        x = np.log(dh)                                  # 구분 안 크기 의존(흐름 방향) 빼기
        if x.std() > 1e-9:
            b = np.polyfit(x, rs, 1)[0]
            rs = rs - b * (x - x.mean())
        us, uc = (rs - np.median(rs)) / Vbar, rc / Vbar
        sv = sig_v / Vbar
        hs, hc = hiqr(us), hiqr(uc)
        gs, gc = gamma_from_hiqr(hs, sv), gamma_from_hiqr(hc, sv)
        tids = np.unique(tid)
        idx_of = {t: np.where(tid == t)[0] for t in tids}
        bs, bc, br = [], [], []
        for _ in range(n_boot):
            pick = rng.choice(tids, size=len(tids))
            ii = np.concatenate([idx_of[t] for t in pick])
            g1, g2 = gamma_from_hiqr(hiqr(us[ii]), sv), gamma_from_hiqr(hiqr(uc[ii]), sv)
            bs.append(g1); bc.append(g2)
            if g2 > 0:
                br.append(g1 / g2)
        ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) > 10 else (float("nan"),) * 2
        rec = dict(dH_lo=lo, dH_hi=hi, n_obs=len(sel), n_tracks=len(tids), V_px_per_frame=Vbar, noise_rel=sv,
                   hiqr_s=hs, hiqr_c=hc, gamma_s=gs, gamma_c=gc, R=gs / gc if gc > 0 else float("nan"))
        rec["gamma_s_lo"], rec["gamma_s_hi"] = ci(bs)
        rec["gamma_c_lo"], rec["gamma_c_hi"] = ci(bc)
        rec["R_lo"], rec["R_hi"] = ci(br)
        if fields is not None:                          # 회귀형(I100 보강): 계산한 쌍극자 장에 대한 기울기 = 접선·할선 이동도
            fu = np.array([fields.get((o[0], o[1]), (np.nan, np.nan)) for o in sel])
            ok = np.isfinite(fu).all(1)
            fx_, fy_ = fu[:, 0].copy(), fu[:, 1].copy()
            for f in np.unique(fr):
                mm = (fr == f) & ok
                if mm.sum() >= 3:
                    fx_[mm] -= np.median(fx_[mm]); fy_[mm] -= np.median(fy_[mm])
            ys, yc = rs - np.median(rs), rc

            def slope(xv, yv, idx):
                xv, yv = xv[idx], yv[idx]
                keep = np.abs(xv) <= np.percentile(np.abs(xv), 99)   # 가장 가까운 이웃(근접장) 1%는 뺀다
                return float((xv[keep] @ yv[keep]) / (xv[keep] @ xv[keep]))
            base = np.where(ok)[0]
            if len(base) > 30:
                b1, b2 = slope(fx_, ys, base), slope(fy_, yc, base)
                rec["b_s"], rec["b_c"], rec["R_reg"] = b1, b2, b1 / b2 if b2 else float("nan")
                okset = set(base.tolist())
                rr = []
                for _ in range(n_boot):
                    pick = rng.choice(tids, size=len(tids))
                    ii = np.array([j for t in pick for j in idx_of[t] if j in okset])
                    if len(ii) > 30:
                        q2 = slope(fy_, yc, ii)
                        if q2:
                            rr.append(slope(fx_, ys, ii) / q2)
                rec["R_reg_lo"], rec["R_reg_hi"] = ci(rr)
        if frame_alpha:
            al = float(np.mean([frame_alpha.get(f, float("nan")) for f in np.unique(fr)]))
            rec["alpha"] = al
            rec["abs_lambda_eff"] = gc * (1 + 6.7 * al) / al if al > 0 else float("nan")
        if U_loc_px:
            s = Vbar / U_loc_px
            Dl = 2 / s - 1
            rec["s"] = s
            rec["Delta"] = Dl
            rec["m"] = ((1 + Dl) / rec["R"] - 1) / Dl if Dl > 0 and rec["R"] == rec["R"] else float("nan")
            rec["m_lo"] = ((1 + Dl) / rec["R_hi"] - 1) / Dl if Dl > 0 and rec["R_hi"] == rec["R_hi"] else float("nan")
            rec["m_hi"] = ((1 + Dl) / rec["R_lo"] - 1) / Dl if Dl > 0 and rec["R_lo"] == rec["R_lo"] else float("nan")
            if "R_reg" in rec and Dl > 0:
                mf = lambda R: ((1 + Dl) / R - 1) / Dl if R == R and R > 0 else float("nan")
                rec["m_reg"], rec["m_reg_lo"], rec["m_reg_hi"] = mf(rec["R_reg"]), mf(rec.get("R_reg_hi", float("nan"))), mf(rec.get("R_reg_lo", float("nan")))
        out.append(rec)
    return out, sig_p


def make_demo(out, seed=3, push=False):
    """쌍극자 상호작용을 넣은 합성 추적(주기 상자, 두 크기). 정답(잡음 없는 위치)도 함께 돌려준다.
    작은 기포 a 8 px·Δ0 4.8(s 0.345), 큰 기포 a 24 px·Δ0 0.29(s 1.55), 각 α 0.03, m = 2/3, U = 6 px/frame,
    위치 잡음 0.15 px. 기포 속도는 벡터 힘 균형 2(U + u') = V(1 + Δ0(|V|/V0)^(m − 1))로 푼다.
    push=True면 겹친 쌍을 중심선 방향으로 밀어낸다. 이 접촉 변위는 가로 회귀 기울기를 약 18% 부풀렸다(작은 기포) →
    실제 자료에서는 접촉 근처(--contact_gap)를 넉넉히 뺀다. 기본(push=False)은 겹침을 허용하고 접촉 필터가 그 창을 뺀다."""
    rng = np.random.default_rng(seed)
    Lx, Ly, U, m, noise = 2000.0, 1000.0, 6.0, 2 / 3, 0.15
    specs = [(24.0, 0.29, 0.03), (8.0, 4.8, 0.03)]
    P, a, D0 = [], [], []
    for rad, dl, al in specs:
        n = int(al * Lx * Ly / (math.pi * rad * rad))
        tries = 0
        while n > 0 and tries < 200000:
            tries += 1
            p = rng.uniform((0, 0), (Lx, Ly))
            if P:
                q = np.array(P); dx = q - p
                dx[:, 0] -= Lx * np.round(dx[:, 0] / Lx); dx[:, 1] -= Ly * np.round(dx[:, 1] / Ly)
                if np.any(np.hypot(dx[:, 0], dx[:, 1]) < np.array(a) + rad + 1):
                    continue
            P.append(p); a.append(rad); D0.append(dl); n -= 1
    P = np.array(P); a = np.array(a); D0 = np.array(D0)
    V0 = 2 * U / (1 + D0)
    lam = V0 / U - 1
    Dip = lam * U * a * a
    N = len(P)
    unwrapped = P.copy()
    nf = 260
    rows, truth = [], []
    for f in range(nf):
        d = P[:, None, :] - P[None, :, :]
        d[..., 0] -= Lx * np.round(d[..., 0] / Lx); d[..., 1] -= Ly * np.round(d[..., 1] / Ly)
        r2 = (d ** 2).sum(-1); np.fill_diagonal(r2, np.inf)
        cut = r2 > (0.5 * Ly) ** 2
        r4 = r2 * r2
        ux = np.where(cut, 0.0, Dip[None, :] * (d[..., 0] ** 2 - d[..., 1] ** 2) / r4).sum(1)
        uy = np.where(cut, 0.0, Dip[None, :] * 2 * d[..., 0] * d[..., 1] / r4).sum(1)
        ux -= ux.mean(); uy -= uy.mean()
        Fx, Fy = 2 * (U + ux), 2 * uy
        V = np.stack([V0, np.zeros(N)], 1)
        for _ in range(60):
            sp = np.hypot(V[:, 0], V[:, 1])
            Dl = D0 * (sp / V0) ** (m - 1)
            Vn = np.stack([Fx, Fy], 1) / (1 + Dl)[:, None]
            V = 0.5 * V + 0.5 * Vn
        for i in range(N):
            rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": i + 1, "イベント": "",
                         "面積(px)": f"{math.pi * a[i] ** 2:.3f}", "ROI内面積(px)": f"{math.pi * a[i] ** 2:.3f}",
                         "中心X": f"{unwrapped[i, 0] + rng.normal(0, noise):.4f}", "中心Y": f"{unwrapped[i, 1] + rng.normal(0, noise):.4f}",
                         "フレーム接触": "0"})
        truth.append(unwrapped.copy())
        P = P + V; unwrapped = unwrapped + V
        for _ in range(3 if push else 0):               # 겹치면 중심선 방향으로 밀어낸다(합체 없음)
            d = P[:, None, :] - P[None, :, :]
            d[..., 0] -= Lx * np.round(d[..., 0] / Lx); d[..., 1] -= Ly * np.round(d[..., 1] / Ly)
            r = np.sqrt((d ** 2).sum(-1)); np.fill_diagonal(r, np.inf)
            ov = (a[:, None] + a[None, :]) - r
            ov[ov < 0] = 0
            if not ov.any():
                break
            push = (ov / np.where(r > 0, r, 1))[..., None] * d * 0.5
            dP = push.sum(1)
            P = P + dP; unwrapped = unwrapped + dP
        P[:, 0] %= Lx; P[:, 1] %= Ly
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    frame_alpha = {f: float(np.sum(math.pi * a * a) / (Lx * Ly)) for f in range(nf)}
    return path, np.array(truth), a, D0, m, U, noise, frame_alpha


def _demo(out, push=False):
    os.makedirs(out, exist_ok=True)
    path, truth, a, D0, m, U, noise, frame_alpha = make_demo(out, push=push)
    H_px, k = 16.0 / 3, 4                                # 작은 기포 d 16 px = d/H 3, 큰 기포 d 48 px = d/H 9. 느린 작은 기포는 k를 키워 잡음을 줄인다
    bins = ((2, 5), (5, 50))
    tracks = read_tracks(path, "right", 0.02, H_px * 0.02)
    near = near_contact(tracks, 0.5)
    obs, dd = track_velocities(tracks, k, 1, H_px, near)
    fields = window_fields(dipole_fields(tracks, class_lambda(obs, bins, U), H_px, U, periodic=(2000.0, 1000.0)), obs, k, 1)
    res, sig_p = analyse(obs, dd, k, 1, bins, frame_alpha=frame_alpha, U_loc_px=U, n_boot=100, fields=fields)
    # 정답: 잡음 없는 위치로 같은 계산을 하고 잡음 0으로 둔다
    tr_true = defaultdict(dict)
    for f in range(truth.shape[0]):
        for i in range(truth.shape[1]):
            tr_true[str(i + 1)][f] = (truth[f, i, 0], truth[f, i, 1], math.pi * a[i] ** 2, False)
    obs_t, _ = track_velocities(tr_true, k, 1, H_px, near)
    res_t, _ = analyse(obs_t, np.zeros((0, 2)), k, 1, bins, n_boot=0)
    fails = []

    def check(name, got, want, tol):
        ok = abs(got - want) <= tol * abs(want)
        print(f"  {'통과' if ok else '실패'}  {name}: 도구 {got:.4g}, 정답 {want:.4g} (허용 {tol:.0%})")
        if not ok:
            fails.append(name)
    print(f"합성 추적: 기포 {truth.shape[1]}개 × {truth.shape[0]}프레임, 위치 잡음 {noise} px, m = {m:.3f}")
    check("위치 잡음 σ_p", sig_p, noise, 0.15)
    for r, rt, dl in zip(res, res_t, (4.8, 0.29)):
        tag = f"d/H {r['dH_lo']:g}~{r['dH_hi']:g}"
        print(f"  {tag}: 관측 {r['n_obs']}, 상대 잡음 {r['noise_rel']:.3f}, 반IQR 흐름 {r['hiqr_s']:.4f}·가로 {r['hiqr_c']:.4f} → "
              f"γ {r['gamma_s']:.4f}·{r['gamma_c']:.4f}, 폭의 비 R {r['R']:.3f} [{r['R_lo']:.3f}~{r['R_hi']:.3f}](참고: 배치 비등방에 민감), "
              f"회귀 기울기 흐름 {r['b_s']:.3f}·가로 {r['b_c']:.3f} → R_reg {r['R_reg']:.3f} [{r['R_reg_lo']:.3f}~{r['R_reg_hi']:.3f}], m_reg {r.get('m_reg', float('nan')):.2f}")
        check(f"{tag} 가로 γ(잡음 뺀 값) 대 잡음 없는 폭", r["gamma_c"], rt["hiqr_c"], 0.15)
        check(f"{tag} 흐름 방향 γ 대 잡음 없는 폭", r["gamma_s"], rt["hiqr_s"], 0.15)
        want = (1 + dl) / (1 + m * dl)
        if r["n_tracks"] >= 100:
            check(f"{tag} 가로 회귀 기울기 대 할선 이동도 2/(1 + Δ)", r["b_c"], 2 / (1 + dl), 0.1)
            check(f"{tag} 회귀 비 R_reg 대 (1 + Δ)/(1 + mΔ)", r["R_reg"], want, 0.1)
        else:
            inside = r["R_reg_lo"] <= want <= r["R_reg_hi"]
            print(f"  {'통과' if inside else '실패'}  {tag}(트랙 {r['n_tracks']}개, 표본이 적어 구간만 봄): 정답 {want:.3f}이 R_reg 95% 구간 안")
            if not inside:
                fails.append(tag)
    check("작은 기포 회귀로 되찾은 m(±0.12)", res[0]["m_reg"], m, 0.18)
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--px_mm", type=float); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--H_mm", type=float); ap.add_argument("--flow", default="up")
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--smooth", type=int, default=1)
    ap.add_argument("--frame_area_px", type=float, default=float("nan"))
    ap.add_argument("--U_loc", type=float, default=float("nan"), help="국소장 U_loc(m/s). 원형이면 (U_P + J)/2(I91) 또는 I102")
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--contact_gap", type=float, default=0.5, help="틈이 이 값 × 작은 쪽 반경보다 좁은 관측은 뺀다(0이면 끔)")
    ap.add_argument("--regress", action="store_true", help="계산한 쌍극자 장에 회귀(배치 비등방에 강함). --U_loc 필요")
    ap.add_argument("--walls", default="", help="측벽의 가로 좌표 두 개(px, 영상 좌표), 예: 12,1060. 주면 거울상을 넣는다")
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--out", default="vf_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    edges = [float(v) for v in a.dH_bins.split(",")]
    bins = list(zip(edges[:-1], edges[1:]))
    tracks = read_tracks(a.csv, a.flow, a.px_mm, a.H_mm)
    obs, dd = track_velocities(tracks, a.k, a.smooth, H_px, near_contact(tracks, a.contact_gap))
    frame_alpha = None
    if a.frame_area_px == a.frame_area_px:
        tot = defaultdict(float)
        for fr in tracks.values():
            for f, (_, _, A, _) in fr.items():
                tot[f] += A
        frame_alpha = {f: v / a.frame_area_px for f, v in tot.items()}
    U_px = a.U_loc / (a.px_mm * 1e-3 * a.fps) if a.U_loc == a.U_loc else None
    fields = None
    if a.regress:
        if not U_px:
            raise SystemExit("--regress에는 --U_loc(국소장, m/s)이 필요하다(I91의 (U_P + J)/2 또는 I102의 기울임 편향).")
        walls = tuple(float(v) for v in a.walls.split(",")) if a.walls else None
        fields = window_fields(dipole_fields(tracks, class_lambda(obs, bins, U_px), H_px, U_px, walls=walls), obs, a.k, a.smooth)
    res, sig_p = analyse(obs, dd, a.k, a.smooth, bins, frame_alpha, U_px, a.n_boot, fields=fields)
    print(f"속도 표본 {len(obs)}개(트랙 {len(set(o[0] for o in obs))}개), 위치 잡음 σ_p ≈ {sig_p:.3f} px")
    if res:
        keys = sorted({k for r in res for k in r}, key=lambda k: list(res[0].keys()).index(k) if k in res[0] else 99)
        with open(os.path.join(a.out, "vf_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in res:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    for r in res:
        line = (f"d/H {r['dH_lo']:g}~{r['dH_hi']:g}: 관측 {r['n_obs']}(트랙 {r['n_tracks']}), V̄ {r['V_px_per_frame']:.2f} px/frame, "
                f"상대 잡음 {r['noise_rel']:.3f}, 코시 척도 흐름 {r['gamma_s']:.4f}·가로 {r['gamma_c']:.4f}, "
                f"R {r['R']:.3f} [{r['R_lo']:.3f}~{r['R_hi']:.3f}]")
        if "alpha" in r:
            line += f", α {r['alpha']:.3f} → |λ|_eff {r['abs_lambda_eff']:.2f}"
        if "m" in r:
            line += f", s {r['s']:.2f}(Δ {r['Delta']:.2f}) → m {r['m']:.2f} [{r['m_lo']:.2f}~{r['m_hi']:.2f}]"
        if "R_reg" in r:
            line += (f"; 회귀: 기울기 흐름 {r['b_s']:.3f}·가로 {r['b_c']:.3f}(가로 = 할선 이동도 s여야 함), "
                     f"R_reg {r['R_reg']:.3f} [{r['R_reg_lo']:.3f}~{r['R_reg_hi']:.3f}]")
            if "m_reg" in r:
                line += f" → m_reg {r['m_reg']:.2f} [{r['m_reg_lo']:.2f}~{r['m_reg_hi']:.2f}]"
        print(line)
    print("읽는 법: 가로 γ ≈ Σα|λ|·g(α)(I99, d/H ≈ 10에서 최소, 배치에 따라 ±10~30%). R = (1 + Δ)/(1 + mΔ)(I100): 깨끗한 막 m 2/3이면 "
          "d/H 3에서 약 1.4, 마른 접촉선 m ≈ 0이면 1 + Δ로 크다. 폭의 비 R은 배치 비등방(합성 시험에서 장의 폭 비 0.83~1.28)에 "
          "민감하므로 m은 --regress의 R_reg로 읽는다(합성 시험: 작은 기포 −6%, 큰 기포 0%). 홈·맥동·크기 이질성은 흐름 방향만, "
          "접촉 변위는 가로 기울기를 부풀린다.")


if __name__ == "__main__":
    main()

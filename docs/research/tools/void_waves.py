"""추적 위치의 밀도 무늬(공극률 파)가 기포보다 빠른지 느린지로 이동도 결손 λ의 부호·크기와 마찰 지수 비 R을 읽는다(아이디어 I110).

배경 (원형 팬케이크, 깊이 평균 Darcy, 묽은 극한, 긴 파장)
    기포 속도 V = F(U_loc)이고 국소장은 이웃 쌍극자 장으로 바뀐다. 파수 k(흐름과 각 θ)의 밀도 섭동 δα가 만드는 국소장 섭동은
    δu = −λU·δα·(cos 2θ, sin 2θ)다(쌍극자 장의 합에서 자기 칸을 뺀 값. 폭 평균 띠 θ = 0은 J = (1 − α)U_loc + αV에서 바로 나온다).
    흐름 방향은 접선 이동도 s_t = 2/(1 + mΔ), 가로는 할선 이동도 s = 2/(1 + Δ)로 응답하므로(I100) 연속 방정식을 선형화하면
        ω = k_x·V̄·{1 − αλ[1 + (R − 1)·cos 2θ]},   R = s_t/s = (1 + Δ)/(1 + mΔ),   λ = s − 1
    즉 밀도 무늬는 흐름 방향으로 c_x = V̄·{1 − αλ[1 + (R − 1)cos 2θ]}로 흐른다. 결손 D = 1 − c_x/V̄.
      - 선형 마찰(R = 1)이면 모든 방향에서 V̄(1 − αλ)다. Desreumaux 외 2013(PRL 111:118301, 액적, 실험과 맞음)의
        ω = ½μσρ₀q_x와 같다(그들의 σρ₀ = 2(1 − μ)v_Fφ/πR²·πR², μ = s).
      - 폭을 채운 띠(폭 평균 밀도, θ = 0)는 D = αλR. 단분산 평균장 정확식은 D = αλR/[1 + α(Rs − 1)].
      - 45°는 D = αλ → 두 결손의 비가 R이다(α·λ 없이 m의 판독, I100과 같은 양).
      - 빠른 큰 기포(λ > 0)는 무늬가 기포보다 느리고, 느린 작은 기포(λ < 0)는 빠르다. 이동도 1인 크기(I104의 d*)에서 같아진다.
      - 크기가 섞이면 구분마다 c_i/V_i − 1 ≈ −α_iλ_iR_i다(구분 속도가 서로 떨어져 있을 때, 자기 구분의 α_i만 들어간다).
      - 한 줄로 선 기포 열은 부호가 반대다. 압축파가 열보다 (2π²/3)·λR·(a/d)²·V̄만큼 앞서 간다
        (Booth, Griffiths & Howell 2023 "Hele-Shaw Newton's cradle"의 긴 파장 극한). 같은 구분이 한 줄(가로 퍼짐 < 2a)이면 경고한다.
      - 짧은 파장은 배제 영역 때문에 분산한다: ω ∝ J1(2ka)/(ka)(Desreumaux 식 8). 이 인자로 나눠 k → 0 값을 낸다.
    두 지점 상관으로 잰 "속도"(두 탐침, 큰 창의 긴 시간 상관)는 V̄가 아니라 c다(기포류 공극률 파의 고전 결과: Bernier 1982).

쓰는 법
    python void_waves.py --csv result_tracking.csv --px_mm 0.02 --H_mm 0.3 --flow up --out vw_out
        [--dH_bins 2,5,15,50] [--fov s0,s1,c0,c1] [--ka_max 0.3] [--theta] [--m 0.667] [--weight area|count] [--n_boot 200]
    python void_waves.py --demo --out vw_demo      # 평균장 입자 모의(세 경우)로 스스로 점검(약 2~3분)
    fov는 흐름 좌표(s = 흐름 방향, c = 가로; --flow up이면 s = −y, c = x)의 px 범위. 비우면 검출 위치의 0.5~99.5% 범위.

계산
    1. 프레임마다 화면 끝에 닿지 않은 검출로 밀도장의 푸리에 성분 ρ_k(t) = Σ_j q_j·w(r_j)·exp(−ik·r_j)(q = 면적, w = 시야 Hann 창).
       ID가 필요 없어서 추적 오연결의 영향을 받지 않는다. 띠(k_c = 0)는 가로로 창을 걸지 않는다(폭 평균). --theta면 가로에도 Hann 창.
    2. 집단 상관 C_c(k, τ) = Σ_t ρ_k(t + τ)·ρ_k*(t). 무늬가 c로 흐르면 위상이 −k_s·c·τ다.
    3. 같은 무게의 자기 기준 C_s(k, τ) = Σ_(t, j) q_j²·w(r_j)·w(r_j + v_jτ)·exp(−ik·v_jτ)(검출마다 그 순간 속도로 τ만큼 간다고 둔 것).
       창이 느린 기포를 오래 담는 치우침과 구분 안의 속도 퍼짐이 함께 들어간다. 위상 = −k_s·V_ref·τ. 상호작용이 없으면 D = 0.
    4. 결손 D(k, τ) = arg(C_c·C_s*)/(k_s·V_ref·τ) = 1 − c/V_ref. k_s·V̄·τ ≤ 3π인 짝만 쓰고, 무게 = 결맞음² × (k_s·V̄·τ)².
       k마다 J1 인자로 나눠 평균 → D₀. 시간 블록(시야 통과 시간) 부트스트랩으로 95% 구간.
    5. 해석: X = D₀/α(α = 시야 안 그 구분의 면적 비율) = λR(묽은 극한). m을 가정하면 s = 2(1 + mX)/(2 − (1 − m)X)
       (압력·유량계·국소장이 필요 없다). 단분산 평균장 정확식으로 푼 s도 낸다.
    6. --theta: (k_s, k_c) 격자의 D(θ) = A + B·cos 2θ를 맞춰 R = 1 + B/A(묽은 극한에서 A = αλ, B = αλ(R − 1)).
       측벽이 있으면 가로 모드가 cos(nπc/W)라 근사이고, 가로 창 Hann의 누설로 θ가 조금 뭉개진다(B를 작게 냄).
출력: vw_classes.csv(구분별), vw_k.csv(파수별), 요약 출력.
주의
    - 결손은 α|λ|R(몇~10%)라 긴 녹화가 필요하다(시야 통과 수십 번 이상). 짧으면 구간이 넓다.
    - 합체는 면적을 보존하므로 면적 무게(기본)가 낫다. 구분 경계를 넘나드는 기포(합체·분열)는 구분 밀도를 보존하지 않는다
      → "all" 행(모든 크기)을 함께 본다. 크기가 넓게 섞이면 "all"의 D는 구분별 값의 섞임이라 해석이 어렵다.
    - 평균장은 α ≲ 0.2의 묽은 극한이다. 합체가 잦거나 큰 기포가 시야보다 크면 쓰지 않는다.
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


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def j1(x):
    """1종 1차 베셀 함수(급수, 0 ≤ x ≲ 8). scipy 없이 쓴다."""
    x = np.asarray(x, float)
    term = x / 2
    out = term.copy()
    for n in range(1, 40):
        term = term * (-(x / 2) ** 2) / (n * (n + 1))
        out = out + term
    return out


def disp_factor(ka):
    """Desreumaux 외 2013 식 8의 배제 영역 분산 인자 J1(2ka)/(ka)(k → 0에서 1)."""
    ka = np.asarray(ka, float)
    return np.where(ka > 1e-9, j1(2 * ka) / np.maximum(ka, 1e-12), 1.0)


def hann(u):
    u = np.asarray(u, float)
    return np.where((u >= 0) & (u <= 1), np.sin(np.pi * u) ** 2, 0.0)


def read_frames(path, flow):
    """프레임 → [(트랙, s, c, 면적, 끝 접촉)]과 CSV에 나온 모든 프레임(기포 없는 프레임 포함)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ax, sgn = axis_of(flow)
    frames, allf = defaultdict(list), set()
    for r in rows:
        f = _f(r.get("フレーム"))
        if f != f:
            continue
        f = int(f)
        allf.add(f)
        tid = r.get("トラックID")
        if not tid or r.get("イベント") == "気泡なし":
            continue
        x, y, A = _f(r.get("中心X")), _f(r.get("中心Y")), _f(r.get("面積(px)"))
        if not (x == x and y == y and A > 0):
            continue
        s_, c_ = (sgn * y, x) if ax == "Y" else (sgn * x, y)
        frames[f].append((tid, s_, c_, A, r.get("フレーム接触") == "1"))
    return frames, sorted(allf)


def attach_velocities(frames, k=1):
    """검출마다 (s, c, 면적, 끝 접촉, v_s, v_c). 속도는 같은 트랙의 ±k 프레임 중심 차분(끝 접촉·면적 변화 20% 초과면 NaN)."""
    tr = defaultdict(dict)
    for f, lst in frames.items():
        for tid, s_, c_, A, e in lst:
            tr[tid][f] = (s_, c_, A, e)
    out = {}
    for f, lst in frames.items():
        arr = []
        for tid, s_, c_, A, e in lst:
            fr = tr[tid]
            vs = vc = float("nan")
            if not e and (f - k) in fr and (f + k) in fr:
                p, q = fr[f - k], fr[f + k]
                if not (p[3] or q[3]) and max(p[2], A, q[2]) <= 1.2 * min(p[2], A, q[2]):
                    vs, vc = (q[0] - p[0]) / (2 * k), (q[1] - p[1]) / (2 * k)
            arr.append((s_, c_, A, 1.0 if e else 0.0, vs, vc))
        out[f] = np.array(arr, float) if arr else np.zeros((0, 6))
    return out


def _lags(Vbar, Ls, nF):
    tau = sorted({max(1, int(round(r * Ls / abs(Vbar)))) for r in (0.1, 0.2, 0.3, 0.4, 0.5)})
    return [t for t in tau if t <= max(1, nF // 3)]


def class_series(frames_v, frame_list, lo, hi, H_px, fov):
    """구분 [lo, hi) d/H의 프레임별 배열(끝 접촉 제외)과 시야 안 면적 비율 α, 중앙 반경."""
    s0, s1, c0, c1 = fov
    per, tot, radii = [], [], []
    for f in frame_list:
        a = frames_v.get(f)
        if a is None or not len(a):
            per.append(np.zeros((0, 6))); tot.append(0.0)
            continue
        dH = np.sqrt(4 * a[:, 2] / np.pi) / H_px
        sel = (dH >= lo) & (dH < hi) & (a[:, 3] < 0.5)
        b = a[sel]
        per.append(b)
        inside = (b[:, 0] >= s0) & (b[:, 0] <= s1) & (b[:, 1] >= c0) & (b[:, 1] <= c1)
        tot.append(float(b[inside, 2].sum()))
        radii.extend(np.sqrt(b[inside, 2] / np.pi).tolist())
    alpha = float(np.mean(tot)) / ((s1 - s0) * (c1 - c0))
    a_med = float(np.median(radii)) if radii else float("nan")
    return per, alpha, a_med


def _weights(b, fov, theta, weight):
    s0, s1, c0, c1 = fov
    w = hann((b[:, 0] - s0) / (s1 - s0))
    if theta:
        w = w * hann((b[:, 1] - c0) / (c1 - c0))
    else:
        w = w * ((b[:, 1] >= c0) & (b[:, 1] <= c1))
    q = b[:, 2] if weight == "area" else np.ones(len(b))
    return q, w


def analyse_class(per, frame_list, fov, a_ref, theta=False, weight="area", ka_max=0.3, n_boot=200, seed=0, Vbar_hint=None):
    """한 구분의 결손 D₀(띠)과 --theta면 D(θ) 맞춤. per = 프레임별 배열(frame_list 순서)."""
    s0, s1, c0, c1 = fov
    Ls, Lc = s1 - s0, c1 - c0
    nF = len(frame_list)
    # 같은 무게((q·w)²)의 평균 흐름 방향 속도
    num = den = 0.0
    for b in per:
        if not len(b):
            continue
        ok = np.isfinite(b[:, 4])
        q, w = _weights(b[ok], fov, theta, weight)
        ww = (q * w) ** 2
        num += float((ww * b[ok, 4]).sum()); den += float(ww.sum())
    if den <= 0:
        return None
    Vbar = num / den if Vbar_hint is None else Vbar_hint
    if not abs(Vbar) > 1e-9:
        return None
    # 파수 격자
    m_max = int(math.floor(ka_max * Ls / (2 * math.pi * a_ref)))
    K = [(2 * math.pi * mm / Ls, 0.0) for mm in range(2, m_max + 1)]
    if theta:
        n_max = int(math.floor(ka_max * Lc / (2 * math.pi * a_ref)))
        for nn in range(2, n_max + 1):
            for mm in range(2, m_max + 1):
                ks, kc = 2 * math.pi * mm / Ls, 2 * math.pi * nn / Lc
                if math.hypot(ks, kc) * a_ref <= ka_max:
                    K += [(ks, kc), (ks, -kc)]
    if not K:
        return None
    K = np.array(K)
    nK = len(K)
    # 집단 성분 ρ_k(t)
    rho = np.zeros((nF, nK), complex)
    for i, b in enumerate(per):
        if not len(b):
            continue
        q, w = _weights(b, fov, theta, weight)
        good = w > 0
        if not good.any():
            continue
        ph = np.exp(-1j * (np.outer(b[good, 0], K[:, 0]) + np.outer(b[good, 1], K[:, 1])))
        rho[i] = (q[good] * w[good]) @ ph
    lags = _lags(Vbar, Ls, nF)
    if not lags:
        return None
    pos = {f: i for i, f in enumerate(frame_list)}
    blen = max(max(lags), int(round(Ls / abs(Vbar))))
    nb = max(1, nF // blen)
    blk = np.minimum(np.arange(nF) // blen, nb - 1)
    Cc = np.zeros((len(lags), nb, nK), complex); Cs = np.zeros_like(Cc)
    N1 = np.zeros((len(lags), nb, nK)); N0 = np.zeros_like(N1)
    for li, tau in enumerate(lags):
        for i, f in enumerate(frame_list):
            j = pos.get(f + tau)
            if j is None:
                continue
            bi = blk[i]
            Cc[li, bi] += rho[j] * np.conj(rho[i])
            N1[li, bi] += np.abs(rho[j]) ** 2; N0[li, bi] += np.abs(rho[i]) ** 2
            b = per[i]
            if not len(b):
                continue
            ok = np.isfinite(b[:, 4])
            if not ok.any():
                continue
            bb = b[ok]
            q, w = _weights(bb, fov, theta, weight)
            moved = bb.copy(); moved[:, 0] += bb[:, 4] * tau; moved[:, 1] += bb[:, 5] * tau
            _, w2 = _weights(moved, fov, theta, weight)
            ww = q * q * w * w2
            sel = ww > 0
            if not sel.any():
                continue
            ph = np.exp(-1j * tau * (np.outer(bb[sel, 4], K[:, 0]) + np.outer(bb[sel, 5], K[:, 1])))
            Cs[li, bi] += ww[sel] @ ph
    lag_arr = np.array(lags, float)
    ka = np.hypot(K[:, 0], K[:, 1]) * a_ref
    gk = disp_factor(ka)
    cos2 = (K[:, 0] ** 2 - K[:, 1] ** 2) / np.maximum(K[:, 0] ** 2 + K[:, 1] ** 2, 1e-30)
    band = K[:, 1] == 0

    def estimate(cnt):
        cc = np.tensordot(cnt, Cc, axes=([0], [1]))           # (lag, k)
        cs = np.tensordot(cnt, Cs, axes=([0], [1]))
        n1 = np.tensordot(cnt, N1, axes=([0], [1])); n0 = np.tensordot(cnt, N0, axes=([0], [1]))
        x = K[None, :, 0] * Vbar * lag_arr[:, None]           # k_s·V̄·τ
        vref = Vbar - np.angle(cs * np.exp(1j * x)) / (K[None, :, 0] * lag_arr[:, None])
        dphi = np.angle(cc * np.conj(cs))
        D = dphi / (K[None, :, 0] * vref * lag_arr[:, None])
        coh = np.abs(cc) / np.sqrt(np.maximum(n1 * n0, 1e-300))
        wgt = coh ** 2 * x ** 2 * (np.abs(x) <= 3 * math.pi) * (coh > 0.05)
        W = wgt.sum(0)
        Dk = np.where(W > 0, (wgt * D).sum(0) / np.maximum(W, 1e-300), np.nan)
        Dk0 = Dk / gk
        okb = band & (W > 0)
        D0 = float((W[okb] * Dk0[okb]).sum() / W[okb].sum()) if okb.any() else float("nan")
        A_ = B_ = float("nan")
        okt = W > 0
        if theta and okt.sum() >= 3 and np.ptp(cos2[okt]) > 0.3:
            Xd = np.stack([np.ones(okt.sum()), cos2[okt]], 1)
            sw = np.sqrt(W[okt])
            coef, *_ = np.linalg.lstsq(Xd * sw[:, None], Dk0[okt] * sw, rcond=None)
            A_, B_ = float(coef[0]), float(coef[1])
        return D0, A_, B_, Dk, W, float(np.median(vref[np.isfinite(vref)])) if np.isfinite(vref).any() else Vbar

    D0, A_, B_, Dk, Wk, Vref = estimate(np.ones(nb))
    rng = np.random.default_rng(seed)
    bs_D, bs_R = [], []
    if nb >= 4:
        for _ in range(n_boot):
            cnt = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype(float)
            d0, a_, b_, *_ = estimate(cnt)
            bs_D.append(d0)
            if theta and a_ == a_ and abs(a_) > 1e-9:
                bs_R.append(1 + b_ / a_)
    res = {"V_px_per_frame": Vbar, "V_ref": Vref, "D0": D0, "n_blocks": nb, "block_frames": blen, "lags": lags, "n_k_band": int(band.sum())}
    if len(bs_D) >= 20:
        lo, hi = np.nanpercentile(bs_D, [2.5, 97.5])
        res["D0_lo"], res["D0_hi"] = float(lo), float(hi)
    if theta:
        res["A"], res["B"] = A_, B_
        res["R_theta"] = 1 + B_ / A_ if A_ == A_ and abs(A_) > 1e-9 else float("nan")
        if len(bs_R) >= 20:
            lo, hi = np.nanpercentile(bs_R, [2.5, 97.5])
            res["R_theta_lo"], res["R_theta_hi"] = float(lo), float(hi)
    res["k_table"] = [(float(K[i, 0]), float(K[i, 1]), float(ka[i]), float(Dk[i]), float(Wk[i])) for i in range(nK)]
    return res


def R_of(s, m):
    return 2.0 / (s + m * (2.0 - s))


def s_from_X(X, m):
    """묽은 극한 X = λR = 2(s − 1)/(s + m(2 − s))을 s로 푼다."""
    den = 2.0 - (1.0 - m) * X
    return 2.0 * (1.0 + m * X) / den if den > 0 else float("nan")


def s_from_D_exact(D0, alpha, m):
    """단분산 평균장 띠 정확식 D = αλR/[1 + α(Rs − 1)]을 s ∈ (0.02, 1.98)에서 푼다(가장 가까운 해)."""
    ss = np.linspace(0.02, 1.98, 4000)
    R = R_of(ss, m)
    Dm = alpha * (ss - 1) * R / (1 + alpha * (R * ss - 1))
    i = int(np.argmin(np.abs(Dm - D0)))
    return float(ss[i]) if abs(Dm[i] - D0) < 0.02 else float("nan")


def lateral_spread(per, fov):
    s0, s1, c0, c1 = fov
    sd = []
    for b in per:
        if len(b) >= 3:
            ins = (b[:, 0] >= s0) & (b[:, 0] <= s1)
            if ins.sum() >= 3:
                sd.append(float(np.std(b[ins, 1])))
    return float(np.median(sd)) if sd else float("nan")


def analyse(frames_v, frame_list, H_px, bins, fov, theta=False, weight="area", ka_max=0.3, m=2 / 3, n_boot=200, seed=0):
    rows, krows = [], []
    for lo, hi, name in [(lo, hi, f"{lo:g}~{hi:g}") for lo, hi in bins] + [(0.0, float("inf"), "all")]:
        per, alpha, a_med = class_series(frames_v, frame_list, lo, hi, H_px, fov)
        if not (a_med == a_med) or alpha <= 0:
            continue
        r = analyse_class(per, frame_list, fov, a_med, theta=theta, weight=weight, ka_max=ka_max, n_boot=n_boot, seed=seed)
        if r is None:
            continue
        out = {"class": name, "alpha": alpha, "a_px": a_med, "lateral_sd_px": lateral_spread(per, fov)}
        out.update({k: v for k, v in r.items() if k != "k_table"})
        X = r["D0"] / alpha
        out["lamR"] = X
        out["s_dilute"] = s_from_X(X, m)
        out["s_exact"] = s_from_D_exact(r["D0"], alpha, m)
        if theta and r.get("R_theta", float("nan")) == r.get("R_theta", float("nan")):
            s_ = out["s_dilute"]
            if s_ == s_ and 0 < s_ < 2 and abs(s_ - 1) > 0.05:
                Dl = 2 / s_ - 1
                out["m_from_R"] = ((1 + Dl) / r["R_theta"] - 1) / Dl
        rows.append(out)
        for ks, kc, ka, Dk, W in r["k_table"]:
            krows.append({"class": name, "k_s": ks, "k_c": kc, "ka": ka, "D_k": Dk, "weight": W})
    return rows, krows


def _write(rows, path):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})


# ---------------------------------------------------------------- 합성 자가 시험
def simulate(seed, s, m, alpha, n_frames=3000, Lx=3200.0, Ly=640.0, a=8.0, Vbar=10.0, spread=0.03, noise=0.2, h=8.0,
             fov=(400.0, 2800.0), csv_path=None, csv_frames=150):
    """평균장 입자 모의(주기 상자). 기포마다 V = V̄_j·x̂ + diag(R·s, s)·δu, δu_k = −λU·δα_k·(cos 2θ, sin 2θ)·J1(2ka)/(ka).
    면적 비율장은 CIC로 만든다. 시야 [fov] 안의 검출만 내고, 시야에 다시 들어올 때마다 새 트랙 ID를 준다.
    돌려주는 것: frames_v(프레임 → 배열), frame_list, 참 α, R."""
    rng = np.random.default_rng(seed)
    N = int(round(alpha * Lx * Ly / (math.pi * a * a)))
    P = rng.uniform((0, 0), (Lx, Ly), size=(N, 2))
    lam = s - 1.0
    U = Vbar / s
    R = R_of(s, m)
    vj = Vbar * (1 + spread * rng.standard_normal(N))
    nx, ny = int(round(Lx / h)), int(round(Ly / h))
    kx = 2 * np.pi * np.fft.fftfreq(nx, d=h); ky = 2 * np.pi * np.fft.fftfreq(ny, d=h)
    KX, KY = np.meshgrid(kx, ky, indexing="ij")
    K2 = KX ** 2 + KY ** 2
    Kk = np.sqrt(K2)
    with np.errstate(invalid="ignore", divide="ignore"):
        c2 = np.where(K2 > 0, (KX ** 2 - KY ** 2) / K2, 0.0)
        s2 = np.where(K2 > 0, 2 * KX * KY / K2, 0.0)
    g = np.where(2 * Kk * a < 3.8317, disp_factor(Kk * a), 0.0)
    kern_x = -lam * U * g * c2
    kern_y = -lam * U * g * s2
    area = math.pi * a * a
    unw = P[:, 0].copy()
    frames_v, frame_list = {}, []
    hist = []                                           # 최근 세 프레임의 (프레임, {트랙: (x, y, 끝 접촉)})
    rows = []
    for f in range(n_frames + 1):
        gx, gy = P[:, 0] / h, P[:, 1] / h
        i0, j0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
        fx, fy = gx - i0, gy - j0
        grid = np.zeros((nx, ny))
        for di, dj, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            np.add.at(grid, ((i0 + di) % nx, (j0 + dj) % ny), wt * area / (h * h))
        Ak = np.fft.fft2(grid)
        ux = np.fft.ifft2(kern_x * Ak).real; uy = np.fft.ifft2(kern_y * Ak).real
        dux = dvy = 0.0
        for di, dj, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            ii, jj = (i0 + di) % nx, (j0 + dj) % ny
            dux = dux + wt * ux[ii, jj]; dvy = dvy + wt * uy[ii, jj]
        V = np.stack([vj + R * s * dux, s * dvy], 1)
        # 기록: 시야 안(가장자리 걸침 포함), 트랙 = (입자, 통과 번호)
        x_obs = P[:, 0] + rng.normal(0, noise, N); y_obs = P[:, 1] + rng.normal(0, noise, N)
        inside = (P[:, 0] + a >= fov[0]) & (P[:, 0] - a <= fov[1])
        edge = (P[:, 0] - a < fov[0]) | (P[:, 0] + a > fov[1]) | (P[:, 1] - a < 0) | (P[:, 1] + a > Ly)
        passes = np.floor(unw / Lx).astype(int)
        cur = {(int(i), int(passes[i])): (x_obs[i], y_obs[i], bool(edge[i])) for i in np.nonzero(inside)[0]}
        hist.append((f, cur))
        if len(hist) > 3:
            hist.pop(0)
        if len(hist) == 3:                              # 가운데 프레임을 앞뒤 프레임의 중심 차분으로 확정
            (_, before), (pf, here), (_, after) = hist
            arr = []
            for key, (x_, y_, e_) in here.items():
                vs = vc = float("nan")
                if not e_ and key in before and key in after and not before[key][2] and not after[key][2]:
                    vs, vc = (after[key][0] - before[key][0]) / 2, (after[key][1] - before[key][1]) / 2
                arr.append((x_, y_, area, 1.0 if e_ else 0.0, vs, vc))
                if csv_path and pf < csv_frames:
                    rows.append({"ファイル名": f"f{pf}.png", "フレーム": pf, "トラックID": key[0] * 1000 + key[1], "イベント": "",
                                 "面積(px)": f"{area:.3f}", "ROI内面積(px)": f"{area:.3f}", "中心X": f"{x_:.4f}", "中心Y": f"{y_:.4f}",
                                 "フレーム接触": "1" if e_ else "0"})
            frames_v[pf] = np.array(arr, float) if arr else np.zeros((0, 6))
            frame_list.append(pf)
        P = P + V
        unw = unw + V[:, 0]
        P[:, 0] %= Lx; P[:, 1] %= Ly
    if csv_path and rows:                               # CSV는 앞 csv_frames 프레임만(읽기 경로 점검용). 그 경계 프레임의 속도는 메모리 쪽과 다를 수 있다
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    return frames_v, frame_list, N * area / (Lx * Ly), R


def _demo(out):
    os.makedirs(out, exist_ok=True)
    fov = (400.0, 2800.0, 0.0, 640.0)
    cases = [("A 빠른 큰 기포(λ > 0)", 1.55, 0.10, 0.03, False),
             ("B 느린 작은 기포(λ < 0), 방향 의존", 0.35, 0.10, 0.03, True),
             ("C 상호작용 없음(λ = 0), 속도 퍼짐 10%", 1.0, 0.10, 0.10, False)]
    ok_all = True
    m = 2 / 3
    lines = []
    for ci, (name, s, alpha, spread, theta) in enumerate(cases):
        csv_path = os.path.join(out, f"demo_{ci}.csv") if ci == 0 else None
        fv, fl, a_true, R = simulate(seed=7 + ci, s=s, m=m, alpha=alpha, spread=spread, csv_path=csv_path)
        H_px = 1.6                                      # d 16 px → d/H 10(한 구분)
        rows, _ = analyse(fv, fl, H_px, [(2.0, 50.0)], fov, theta=theta, ka_max=0.4 if theta else 0.3, m=m, n_boot=100)
        r = [x for x in rows if x["class"] == "2~50"][0]
        lam = s - 1
        D_true = a_true * lam * R                       # 묽은 극한 띠 결손(모의의 커널이 쓰는 값)
        ci_txt = f"[{r.get('D0_lo', float('nan')):.4f}~{r.get('D0_hi', float('nan')):.4f}]"
        line = (f"{name}: α {r['alpha']:.3f}(참 {a_true:.3f}), V̄ {r['V_px_per_frame']:.2f} px/frame, "
                f"띠 결손 D₀ {r['D0']:+.4f} {ci_txt}, 참 αλR {D_true:+.4f}; s(묽은, m 2/3) {r['s_dilute']:.3f}(참 {s:.2f})")
        tol = 0.012 + 0.15 * abs(D_true)
        good = abs(r["D0"] - D_true) <= tol
        if theta:
            line += (f"; 방향 맞춤 A {r['A']:+.4f}(참 αλ {a_true * lam:+.4f}), B {r['B']:+.4f}(참 αλ(R − 1) {a_true * lam * (R - 1):+.4f}), "
                     f"R {r['R_theta']:.2f} [{r.get('R_theta_lo', float('nan')):.2f}~{r.get('R_theta_hi', float('nan')):.2f}](참 {R:.3f})")
            good = good and (r.get("R_theta_lo", -9) <= R <= r.get("R_theta_hi", 9) or abs(r["R_theta"] - R) < 0.25)
        line += "  → " + ("통과" if good else "실패")
        lines.append(line)
        ok_all = ok_all and good
        if ci == 0:                                     # CSV 읽기 경로가 메모리 경로와 같은 배열을 내는지
            frames, allf = read_frames(csv_path, "right")
            fv2 = attach_velocities(frames)
            f_chk = allf[len(allf) // 2]
            a1 = fv[f_chk]; a2 = fv2[f_chk]
            same = len(a1) == len(a2) and np.allclose(np.sort(a1[:, 0]), np.sort(a2[:, 0]), atol=1e-3)
            lines.append(f"  CSV 읽기 점검(프레임 {f_chk}, 검출 {len(a2)}개): " + ("같음" if same else "다름"))
            ok_all = ok_all and same
    for ln in lines:
        print(ln)
    print("자가 시험 " + ("통과" if ok_all else "실패"))
    return ok_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv"); ap.add_argument("--px_mm", type=float); ap.add_argument("--H_mm", type=float)
    ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--fov", default="", help="s0,s1,c0,c1(흐름 좌표 px). 비우면 검출 위치의 0.5~99.5% 범위")
    ap.add_argument("--ka_max", type=float, default=0.3)
    ap.add_argument("--theta", action="store_true", help="(k_s, k_c) 격자로 방향 의존 D(θ) = A + B cos 2θ를 맞춰 R을 낸다")
    ap.add_argument("--m", type=float, default=2 / 3, help="s를 풀 때 가정하는 마찰 지수(깨끗한 막 2/3)")
    ap.add_argument("--weight", default="area", choices=["area", "count"])
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--out", default="vw_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    edges = [float(v) for v in a.dH_bins.split(",")]
    bins = list(zip(edges[:-1], edges[1:]))
    frames, allf = read_frames(a.csv, a.flow)
    fv = attach_velocities(frames)
    if a.fov:
        fov = tuple(float(v) for v in a.fov.split(","))
    else:
        S = np.concatenate([b[:, 0] for b in fv.values() if len(b)]); C = np.concatenate([b[:, 1] for b in fv.values() if len(b)])
        fov = (float(np.percentile(S, 0.5)), float(np.percentile(S, 99.5)), float(np.percentile(C, 0.5)), float(np.percentile(C, 99.5)))
    rows, krows = analyse(fv, allf, H_px, bins, fov, theta=a.theta, weight=a.weight, ka_max=a.ka_max, m=a.m, n_boot=a.n_boot)
    _write(rows, os.path.join(a.out, "vw_classes.csv")); _write(krows, os.path.join(a.out, "vw_k.csv"))
    print(f"프레임 {len(allf)}개, 시야 s {fov[0]:.0f}~{fov[1]:.0f}, c {fov[2]:.0f}~{fov[3]:.0f} px")
    for r in rows:
        line = (f"{r['class']}: α {r['alpha']:.3f}, a {r['a_px']:.1f} px, V̄ {r['V_px_per_frame']:.2f} px/frame, "
                f"띠 결손 D₀ = 1 − c/V̄ {r['D0']:+.4f} [{r.get('D0_lo', float('nan')):+.4f}~{r.get('D0_hi', float('nan')):+.4f}] "
                f"(블록 {r['n_blocks']}개 × {r['block_frames']} 프레임) → λR {r['lamR']:+.2f}, s(묽은) {r['s_dilute']:.2f}, s(평균장 정확) {r['s_exact']:.2f}")
        if "R_theta" in r:
            line += f"; 방향 맞춤 R {r['R_theta']:.2f} [{r.get('R_theta_lo', float('nan')):.2f}~{r.get('R_theta_hi', float('nan')):.2f}]"
            if "m_from_R" in r:
                line += f" → m {r['m_from_R']:.2f}"
        print(line)
        if r["lateral_sd_px"] == r["lateral_sd_px"] and r["lateral_sd_px"] < 2 * r["a_px"]:
            print("  경고: 이 구분은 가로로 거의 한 줄이다(가로 표준편차 < 2a). 한 줄 기포 열은 결손의 부호가 반대다(Booth 외 2023). 2차원 해석을 쓰지 않는다.")
        if r.get("n_blocks", 0) < 10:
            print("  참고: 시야 통과 블록이 10개 미만이라 구간이 넓거나 없다. 더 긴 녹화(낮은 fps로도 됨)가 필요하다.")
    print("읽는 법: D₀ > 0이면 무늬가 기포보다 느리다(λ > 0, 빠른 기포), D₀ < 0이면 빠르다(λ < 0). 묽은 극한 D₀ = αλR(I110). "
          "s는 m을 가정해 푼 이동도로 압력·유량계가 필요 없다. I91(국소장으로 나눈 s)·I99(|λ|_fwd)와 같은 크기 구분에서 맞춰 본다. "
          "R(--theta)은 I100의 R_reg와 같은 양이다.")


if __name__ == "__main__":
    main()

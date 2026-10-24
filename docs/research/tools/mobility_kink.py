"""운전점(유속)마다 크기–속도 곡선이 Booth 곡선 아래로 꺾이는 크기 d_k를 찾아 (크기, 속도) 평면에 꺾임을 모은다(아이디어 I112·I114). 독립 검토 11 반영판.

배경
    깨끗한(젖은) 팬케이크의 이동도 s = V/U는 Booth 관계 s^(2/3)/(2 − s) = δ_B/f, δ_B = 1.12·(d/H)·Ca_U^(1/3)(Ca_U = μU/σ)를 따라
    크기와 함께 매끈하게 오른다(I91·I104). f는 마찰 배율(오염). 발자국 일부가 마르면 접촉선 마찰이 생겨 그 크기부터 V가 이 곡선
    아래로 꺾일 수 있다. 꺾임 크기 d_k를 유속 4~6개에서 이으면 (크기, 속도) 평면의 경계가 된다.
    검토 11: 경계의 모양만으로 원인을 가르지 못한다.
      - 옆 막(Burgess & Foster 1990, ∝ (H/d)^(2/5)Ca^(4/5))이 먼저 뚫리면 거칠기 경계도 d ∝ V²로 기울어 늦은 터짐(1.7~2)과 같은 꼴이다.
      - 마름이 없어도 속도에 따라 변하는 오염 마찰(Ratulowski & Chang 1990)이 세로에 가까운 꺾임을 만든다.
      - 그래서 꺾임은 "후보"다. 마름 판정에는 잡음 바닥을 넘는 멈춤(I114)과 운동학이 아닌 신호(I98 밝기, 위에서 본 마른 자리)를 함께 요구한다.
      - 접촉선 힘이 둘레에 비례하면(감속 ∝ H/d) 큰 쪽 꺾임은 거의 안 보인다. 큰 쪽 꺾임은 d < min(W/2, 0.7 × 흐름 방향 시야)에서만 읽는다.

계산
    1. 트랙마다 흐름 방향 속도(중심 위치의 k프레임 차분 중앙값, 화면 끝 접촉·사건 프레임 제외), 크기(온전한 프레임 면적의 중앙값 → 등가
       지름 d), 한 프레임 이동 dx, 위치 잡음 σ_p(위치 2차 차분의 MAD/√6), 처음–끝 순 이동. 관측이 --min_obs 미만이면 뺀다.
       속도가 0 이하인 트랙(정지)도 버리지 않는다(검토 11 #9). 先端部 열이 있으면 흐름 방향 길이 L_x ≈ 2·(先端部 − 中心)도 낸다.
    2. d/H 로그 구간(--n_bins)마다 속도 중앙값 V_i와 상대 표준오차 σ_i = 1.2533·1.4826·MAD(ln v)/√n. d/H < --min_dH_fit(3)은
       Booth 관계(d ≫ H 팬케이크) 밖이라 맞춤·판정에서 뺀다(검토 11 #21).
    3. 운전점마다 겉보기 마찰 배율 f_i(U_loc으로 Booth 관계를 거꾸로 풂)의 무게(트랙 수) 중앙값을 s < 1 구간에서 낸다. 유의하게 느린
       구간을 빼며 되풀이 → f_run(앞 판의 "가장 작은 셋"은 잡음과 U_loc 과소에서 낮게 치우쳐 가짜 꺾임을 냈다, 검토 11 #3·#4).
    4. 기준 f_ref: 빠른 쪽 절반 운전점 가운데 젖은 창이 구간의 절반 이상인 것들의 f_run 무게 중앙값(검토 11 #7). 모든 운전점을 f_ref로
       판정한다. f_run/f_ref > --f_tol(1.3)이면 "대부분 마름 또는 오염 변화"로 표시하고, 그런 운전점이 과반이면 경고한다.
    5. 마른 구간: 비 r_i = V_i/V_맞춤 < 1 − max(thr, 2σ_i). 가장 긴 젖은 연속 구간(창) 바깥으로 마른 구간이 2개 이상 이어지면 꺾임(끝 구간
       하나뿐이면 r < 1 − max(2thr, 3σ)일 때만). 꺾임 크기는 비가 1 − thr를 지나는 곳을 두 구간 중심 사이 ln d로 보간한다.
    6. 구간: 트랙 부트스트랩, 매번 구간 경계의 위상도 다시 뽑는다(앞 판은 구간 경계를 고정해 꺾임 구간이 참값을 52%만 품었다, 검토 11 #10).
       f_ref는 고정한다(운전점 사이 불확도는 넣지 않음).
    7. U 흔들기: U_loc × (1 ∓ --u_shift(0.03))로 3~5를 다시 해 꺾임이 세 경우 모두 남으면 "튼튼", 아니면 "U_loc 계통에 민감"이라
       경계 맞춤에서 뺀다(U_loc이 3% 작게 잡히면 앞 판은 운전점의 27%에 가짜 작은 쪽 꺾임을 냈다, 검토 11 #3).
    8. 튼튼한 작은 쪽 꺾임 (d_k, V_k = 그 운전점 젖은 곡선의 V(d_k))로 g = d ln V_k/d ln d_k를 낸다. 꺾임 크기 오차는 V_k를 그 운전점
       Booth 곡선을 따라 함께 옮기므로(오차-변수) OLS 기울기가 치우친다 → 꺾임 구간 폭으로 보정한 g를 판독에 쓰고 OLS 값도 함께 낸다.
       구간은 운전점 다시 뽑기에 운전점 안 d_k 구간을 함께 넣는다. 큰 쪽은 따로 낸다("양쪽 모두" 합친 기울기는 없앴다, 검토 11 #8).
    9. 간헐성(I114, 구간별): 멈춤 = 한 프레임 이동이 그 구간의 젖은 기준 이동(젖은 곡선 속도)의 --stop_rel(0.25)배 아래. 트랙마다 잡음만의
       기대 멈춤 Φ((stop_rel·v_wet − v̄)/(√2σ_p))를 내 초과분을 쓴다. 주 통계는 변동 계수에서 잡음 2σ_p²/v̄²를 뺀 멈춤–출발 비율 추정
       p_ss = CV_ex²/(1 + CV_ex²)(트랙 중앙값 문턱의 앞 판은 0.4 근처에서 포화했다, 검토 11 #5). 정지 트랙(처음–끝 순 이동 < 2√2σ_p)은 따로
       센다. 멈춤이 프레임보다 짧으면 안 보이므로 p_ss·초과분 ≈ 0은 "판정 못 함"이다(검토 11 #14).
합성 시험(검토 11의 조건, `--demo`와 같은 합성기: 1 mm, 0.02 mm/px, 500 fps, 위치 잡음 0.3 px, 트랙당 12 프레임)
    - 참 경계: 늦은 터짐 시드 10개에서 판정 범위 안 교차 40/40 검출, 크기 치우침 −3%(sd 5%), 꺾임 구간 적중 100%(앞 판 52%),
      g 0.552 ± 0.023(보정, 참 0.541; OLS 0.588). 세로 V_k 0.0299 ± 0.0023 m/s(참 0.030), g −0.02 ± 0.03.
    - 마름 없음(운전점 중 튼튼한 꺾임): U_loc 계통 −10~+15% 0/105, 트랙 60~400개·퍼짐 10~20% 0/100(앞 판 같은 조건 27~95%).
      f ∝ d^(−0.2) 0/5. f ∝ d^(+0.2)는 큰 쪽 4/5지만 "얕고 멈춤–출발 없음 → 오염 의심". f(V) 오염은 작은 쪽 4/5와 오염 의심.
    - 느린 운전점 다수가 마름(세로 V_c 0.03, U 0.012~0.06): f_ref 1.29(참 1.30), 과반 마름 경고.
판독(후보 좁히기, 기구를 정하지 않음)
    - 작은 쪽 g ≈ 0이고 V_k가 운전점마다 같음: 세로. 거칠기 뚫음·강제 풀림, 또는 속도 의존 오염 f(V)(갭 심, 멈춤, 밝기로 가름).
    - g ≈ 0.35~0.85: 기운 경계(d ∝ V^(1/g)). 늦은 터짐·증발, 또는 옆 막의 거칠기 뚫음.
    - g < 0이거나 V_k가 맞춘 선에서 흩어짐, 또는 얕은 꺾임(깊이 < 0.25)에 멈춤 초과분이 없음: 크기·속도 의존 마찰(오염) 의심.

쓰는 법
    python mobility_kink.py runs.csv --out mk_out [--thr 0.1] [--n_bins 10] [--min_obs 6] [--s_max_fit 1.6] [--min_dH_fit 3]
                                     [--u_shift 0.03] [--f_tol 1.3] [--noise_px 0.3] [--k 2] [--stop_rel 0.25]
        runs.csv 열: name, tracking_csv, px_mm(mm/px), fps, H_mm, flow(up/down/right/left), U_loc(m/s), [q_Wcm2], [W_mm], [fov_mm]
        U_loc은 j_L/(1 − α)(액체 유량계와 거품까지 넣은 영상 α)를 기본으로 권한다. I111의 U_loc은 기포가 프레임당 수십 개인 운전의 점검이다.
        W_mm(채널 폭)·fov_mm(흐름 방향 시야)이 있으면 큰 쪽 꺾임을 d < min(W/2, 0.7·fov)에서만 해석한다.
    python mobility_kink.py --demo --out mk_demo      # 참 경계(늦은 터짐·세로·덧셈형 감속)와 마름 없는 대조(U_loc −3%, 트랙 100개·퍼짐 10%,
                                                       # f(V) 오염)로 꺾임 검출과 거짓 양성률을 점검
출력: mk_runs.csv(운전점별), mk_bins.csv(구간별 V·비·간헐성), mk_plane.png, 요약.
주의: 꺾임은 마름 말고도 폭 채움(I95), 겹침, 측벽, 홈 고정(I96; 젖은 기포도 홈 깊이의 모세관 장벽 약 2σδ/H²에 걸릴 수 있음)에서도 생긴다.
      Booth 관계는 원형·깊이 평균 Darcy·깨끗한 막 꼴이다. 마름이 기포를 오히려 빠르게 하는 계(Keiser 외 2018, 방울)는 이 도구가 못 본다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

MU, SIG = 1.0e-3, 0.072
MED_SE = 1.2533 * 1.4826                                  # 중앙값 표준오차 ≈ 1.2533·σ/√n, σ ≈ 1.4826·MAD
NAN = float("nan")


def _f(v, default=NAN):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


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


def wmedian(x, w):
    x = np.asarray(x, float); w = np.asarray(w, float)
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, 0.5 * c[-1])])


def read_tracks(path, flow, px_mm, fps, H_mm, k=2, min_obs=6):
    """트랙마다 dict(tid, dH, V(m/s), dx(한 프레임 이동, px), sig_p(px), net(처음–끝 순 이동, px), Lx_d(흐름 방향 길이/등가 지름)).
    화면 끝 접촉·사건(new/merge/split) 프레임과 merged_into 행은 뺀다. 속도가 0 이하인 트랙도 남긴다."""
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
        lead = _f(r.get(f"先端部{ax}"))
        tr[tid][int(r["フレーム"])] = (sgn * c, A, r.get("フレーム接触") == "1", ev in ("new", "merge", "split"), sgn * lead)
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
        clean = [f for f in fs if not (fr[f][2] or fr[f][3])]
        dx = np.array([fr[f][0] - fr[f - 1][0] for f in clean if f - 1 in fr and not (fr[f - 1][2] or fr[f - 1][3])])
        d2 = np.array([fr[f + 1][0] - 2 * fr[f][0] + fr[f - 1][0] for f in clean
                       if f - 1 in fr and f + 1 in fr and not any(fr[g][2] or fr[g][3] for g in (f - 1, f + 1))])
        sig_p = float(1.4826 * np.median(np.abs(d2 - np.median(d2))) / math.sqrt(6)) if len(d2) >= 5 else NAN
        net = float(fr[clean[-1]][0] - fr[clean[0]][0]) if len(clean) >= 2 else NAN
        lx = [2 * (fr[f][4] - fr[f][0]) for f in clean if fr[f][4] == fr[f][4]]
        out.append(dict(tid=tid, dH=d_px / H_px, V=float(np.median(vs)) * px_m * fps, dx=dx, sig_p=sig_p, net=net,
                        Lx_d=float(np.median(lx)) / d_px if lx else NAN))
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


def bin_stats(dh, v, edges, min_per_bin):
    """구간마다 (중심 d/H, 속도 중앙값, 상대 표준오차, 트랙 수, 트랙 번호)."""
    cen, med, sig, cnt, idx = [], [], [], [], []
    for i in range(len(edges) - 1):
        m = np.where((dh >= edges[i]) & (dh < edges[i + 1]))[0]
        if len(m) < min_per_bin:
            continue
        vv = v[m]
        md = float(np.median(vv))
        pos = vv > 0
        if md > 0 and pos.sum() >= max(3, 0.8 * len(vv)):
            lv = np.log(vv[pos])
            s_ = MED_SE * float(np.median(np.abs(lv - np.median(lv)))) / math.sqrt(len(m))
        else:
            s_ = MED_SE * float(np.median(np.abs(vv - md))) / math.sqrt(len(m)) / max(abs(md), 1e-12)
        cen.append(float(np.exp(np.mean(np.log(dh[m]))))); med.append(md); sig.append(max(s_, 1e-4)); cnt.append(len(m)); idx.append(m)
    return np.array(cen), np.array(med), np.array(sig), np.array(cnt), idx


def f_apparent(cen, med, U):
    """구간마다 겉보기 마찰 배율 f_i(Booth 관계를 U로 거꾸로 풂). 0 < s < 2가 아니면 inf."""
    s = med / U
    fi = np.full(len(cen), np.inf)
    good = (s > 0) & (s < 2)
    fi[good] = 1.12 * cen[good] * (MU * U / SIG) ** (1 / 3) / (s[good] ** (2 / 3) / (2 - s[good]))
    return fi, s


def f_central(cen, med, sig, cnt, U, thr, valid, s_max_fit=1.6, iters=10):
    """운전점의 젖은 f: s < 1 구간(모자라면 s < s_max_fit)에서 f_i의 무게 중앙값, 유의하게 느린 구간을 빼며 되풀이."""
    fi, s = f_apparent(cen, med, U)
    good = valid & np.isfinite(fi)
    cand = good & (s < 1.0)
    if cand.sum() < 3:
        cand = good & (s < s_max_fit)
    if cand.sum() < 2:
        cand = good
    if not cand.any():
        return NAN, fi
    use = cand.copy()
    f = NAN
    for _ in range(iters):
        f = wmedian(fi[use], cnt[use])
        r = med / v_model(cen, U, f)
        lim = np.maximum(thr, 2 * sig)
        fast = cand & (r > 1 + lim)
        if fast.sum() >= 2:                               # 더 빠른 무리가 있으면 그쪽이 젖은 쪽이다(마름은 겉보기 f를 키우기만 함)
            new = fast
        else:
            new = cand & ~(r < 1 - lim)
        if new.sum() < 2 or (new == use).all():
            break
        use = new
    return f, fi


def judge(cen, med, sig, U, f, thr, valid):
    """판정 구간(valid)만 d 순서로 보고 비·마른 표시·가장 긴 젖은 창·꺾임(보간)을 낸다."""
    n = len(cen)
    out = dict(ratio=np.full(n, NAN), dry=np.zeros(n, bool), win=None, k1=NAN, k2=NAN, dep1=NAN, dep2=NAN, all_dry=False,
               win_frac=NAN, n_valid=int(valid.sum()), side1=[], side2=[], fast=0)
    vi = np.where(valid)[0]
    if len(vi) < 3 or not f == f:
        return out
    r = med[vi] / v_model(cen[vi], U, f)
    dry = r < 1 - np.maximum(thr, 2 * sig[vi])
    strong = r < 1 - np.maximum(2 * thr, 3 * sig[vi])
    out["ratio"][vi] = r
    out["dry"][vi] = dry
    out["fast"] = int(np.sum(r > 1 + np.maximum(thr, 2 * sig[vi])))     # f보다 유의하게 빠른 구간 수(운전점마다 f가 다르다는 신호)
    wet = r >= 1 - thr                                    # 마르지 않은 구간 가운데 비가 실제로 1 − thr 위인 것(잡음 큰 구간만으로 창을 만들지 않음)
    best, cur, st = (0, -1, -1), 0, 0
    for j, d_ in enumerate(dry):
        if not d_:
            if cur == 0:
                st = j
            cur += 1
            if wet[st:j + 1].any() and (cur > best[0]):
                best = (cur, st, j)
        else:
            cur = 0
    if best[0] == 0:
        out["all_dry"] = True
        return out
    _, a0, a1 = best
    out["win"] = (int(vi[a0]), int(vi[a1]))
    out["win_frac"] = best[0] / len(vi)
    lc = np.log(cen[vi])

    def cross(a, b):
        """젖은 구간 a와 바로 옆 마른 구간 b 사이에서 비가 반 깊이 (r_a + r_마른 쪽)/2를 지나는 곳을 ln d로 보간한다.
        r_마른 쪽 = b와 그 바깥 구간(마른 경우)의 중앙값. 구간 경계에 놓인 계단이면 치우침이 없다(1 − thr 수준은 젖은 쪽으로 치우침)."""
        b2 = b + (b - a)
        side = [r[b]] + ([r[b2]] if 0 <= b2 < len(r) and dry[b2] else [])
        lev = 0.5 * (r[a] + float(np.median(side)))
        t = float(np.clip((r[a] - lev) / (r[a] - r[b]), 0, 1)) if r[a] > r[b] else 0.5
        return float(np.exp(lc[a] + t * (lc[b] - lc[a])))
    m = 0
    while a0 - 1 - m >= 0 and dry[a0 - 1 - m]:
        m += 1
    if m >= 2 or (m == 1 and a0 - 1 == 0 and strong[0]):
        out["k1"] = cross(a0, a0 - 1)
        out["dep1"] = float(np.median(1 - r[max(a0 - 2, 0):a0]))
        out["side1"] = [int(vi[j]) for j in range(a0 - m, a0)]
    m = 0
    while a1 + 1 + m < len(vi) and dry[a1 + 1 + m]:
        m += 1
    if m >= 2 or (m == 1 and a1 + 1 == len(vi) - 1 and strong[-1]):
        out["k2"] = cross(a1, a1 + 1)
        out["dep2"] = float(np.median(1 - r[a1 + 1:a1 + 3]))
        out["side2"] = [int(vi[j]) for j in range(a1 + 1, a1 + 1 + m)]
    return out


class Params:
    def __init__(self, thr=0.1, n_bins=10, min_per_bin=5, s_max_fit=1.6, min_dH_fit=3.0, u_shift=0.03, f_tol=1.3, stop_rel=0.25,
                 noise_px=NAN):
        self.thr, self.n_bins, self.min_per_bin, self.s_max_fit = thr, n_bins, min_per_bin, s_max_fit
        self.min_dH_fit, self.u_shift, self.f_tol, self.stop_rel, self.noise_px = min_dH_fit, u_shift, f_tol, stop_rel, noise_px


def _bins_of(dh, v, P, phase=None):
    lo, hi = math.log(dh.min()), math.log(dh.max() * 1.0001)
    w = (hi - lo) / P.n_bins
    if phase is None:
        edges = np.exp(np.linspace(lo, hi, P.n_bins + 1))
    else:
        edges = np.exp(lo - phase * w + w * np.arange(P.n_bins + 2))
    cen, med, sig, cnt, idx = bin_stats(dh, v, edges, P.min_per_bin)
    return cen, med, sig, cnt, idx, cen >= P.min_dH_fit


def analyse_runs(data, P, U_scale=1.0, n_boot=0, seed=0):
    """두 단계 판정. (1) 운전점마다 f_run과 젖은 창, (2) 빠른 쪽 운전점들로 f_ref를 정하고 모든 운전점을 f_ref로 판정.
    n_boot > 0이면 꺾임 구간(트랙 다시 뽑기 + 구간 경계 위상 다시 뽑기, f_ref 고정)."""
    out = []
    for r in data:
        dh = np.array([t["dH"] for t in r["tracks"]]); v = np.array([t["V"] for t in r["tracks"]])
        o = dict(name=r["name"], U=r["U"] * U_scale, n_tracks=len(dh), dh=dh, v=v, ok=len(dh) >= 3 * P.min_per_bin, f_run=NAN, win1=NAN)
        if o["ok"]:
            cen, med, sig, cnt, idx, valid = _bins_of(dh, v, P)
            f_run, fi = f_central(cen, med, sig, cnt, o["U"], P.thr, valid, P.s_max_fit)
            j1 = judge(cen, med, sig, o["U"], f_run, P.thr, valid)
            o.update(cen=cen, med=med, sig=sig, cnt=cnt, idx=idx, valid=valid, f_run=f_run, win1=j1["win_frac"])
        out.append(o)
    ok = [o for o in out if o["ok"] and o["f_run"] == o["f_run"]]
    fast = sorted(ok, key=lambda o: -o["U"])[:max(1, (len(ok) + 1) // 2)]
    ref = [o for o in fast if o["win1"] == o["win1"] and o["win1"] >= 0.5]
    if not ref:
        ref = [o for o in ok if o["win1"] == o["win1"] and o["win1"] >= 0.5] or ok
    if ref:                                               # 가장 깨끗한 쪽 무리: 통째로 마른 운전점은 자기 f로 보면 "다 젖음"이라 기준을 끌어올린다
        fmin = min(o["f_run"] for o in ref)
        ref = [o for o in ref if o["f_run"] <= fmin * math.sqrt(P.f_tol)]
    f_ref = wmedian([o["f_run"] for o in ref], [o["n_tracks"] for o in ref]) if ref else NAN
    rng = np.random.default_rng(seed)
    for o in out:
        if not o["ok"]:
            continue
        j = judge(o["cen"], o["med"], o["sig"], o["U"], f_ref, P.thr, o["valid"])
        o.update(j)
        o["f_ref"] = f_ref
        o["V_k1"] = float(v_model([j["k1"]], o["U"], f_ref)[0]) if j["k1"] == j["k1"] else NAN
        o["V_k2"] = float(v_model([j["k2"]], o["U"], f_ref)[0]) if j["k2"] == j["k2"] else NAN
        if n_boot:
            b1, b2 = [], []
            for _ in range(n_boot):
                ii = rng.integers(0, len(o["dh"]), len(o["dh"]))
                cen, med, sig, cnt, idx, valid = _bins_of(o["dh"][ii], o["v"][ii], P, phase=rng.uniform())
                jb = judge(cen, med, sig, o["U"], f_ref, P.thr, valid)
                b1.append(jb["k1"]); b2.append(jb["k2"])
            for key, b in (("1", b1), ("2", b2)):
                bb = np.array([x for x in b if x == x])
                o["k%s_lo" % key], o["k%s_hi" % key] = (tuple(float(q) for q in np.percentile(bb, [2.5, 97.5])) if len(bb) > 10 else (NAN, NAN))
                o["p_k" + key] = len(bb) / n_boot
    return out, f_ref, [o["name"] for o in ref]


def intermittency(o, tracks, U, f_ref, px_m, fps, P):
    """구간별 간헐성(I114). 멈춤 문턱 = stop_rel × 그 구간 젖은 곡선 속도(px/frame). σ_p는 마르지 않은 구간 트랙의 중앙값(또는 --noise_px)."""
    nb = len(o["cen"])
    sp_all = [tracks[i]["sig_p"] for b in range(nb) if not o["dry"][b] for i in o["idx"][b] if tracks[i]["sig_p"] == tracks[i]["sig_p"]]
    if not sp_all:
        sp_all = [t["sig_p"] for t in tracks if t["sig_p"] == t["sig_p"]]
    sp = P.noise_px if P.noise_px == P.noise_px else (float(np.median(sp_all)) if sp_all else 0.0)
    v_wet = v_model(o["cen"], U, f_ref) / (px_m * fps)
    res = []
    for b in range(nb):
        sf, sn, cv, cvn, pss, nst, lxd = [], [], [], [], [], 0, []
        for i in o["idx"][b]:
            t = tracks[i]
            if t["Lx_d"] == t["Lx_d"]:
                lxd.append(t["Lx_d"])
            dx = t["dx"]
            if len(dx) < 3:
                continue
            vb = float(np.mean(dx))
            thr_px = P.stop_rel * v_wet[b]
            sf.append(float(np.mean(dx < thr_px)))
            sn.append(_phi((thr_px - vb) / (math.sqrt(2) * sp)) if sp > 0 else float(vb < thr_px))
            if (t["net"] == t["net"] and t["net"] < 2 * math.sqrt(2) * sp) or vb <= 0:
                nst += 1
                pss.append(1.0)
                continue
            c_ = float(np.std(dx) / vb)
            cn = math.sqrt(2) * sp / vb
            cv.append(c_); cvn.append(cn)
            ex2 = max(c_ * c_ - cn * cn, 0.0)
            pss.append(ex2 / (1 + ex2))
        nt = len(sf)
        res.append(dict(stop_frac=float(np.mean(sf)) if sf else NAN, stop_noise=float(np.mean(sn)) if sn else NAN,
                        stop_excess=float(np.mean(sf) - np.mean(sn)) if sf else NAN, cv=float(np.median(cv)) if cv else NAN,
                        cv_noise=float(np.median(cvn)) if cvn else NAN, p_ss=float(np.median(pss)) if pss else NAN,
                        n_stopped=nst, frac_stopped=nst / nt if nt else NAN, Lx_over_d=float(np.median(lxd)) if lxd else NAN))
    return res, sp


def kink_slope(pts, n_boot=500, seed=1):
    """pts = [(d_k(mm), V_k, d_lo, d_hi, U, f, H(mm))]. g = d ln V_k/d ln d_k(최소제곱), 구간(운전점 다시 뽑기 + 운전점 안 d_k를 그 구간에서
    다시 뽑아 젖은 곡선을 따라 V_k를 다시 냄), 맞춘 선 둘레 ln V_k의 흩어짐(rms), 오차-변수 보정 g_eiv.
    꺾임 크기의 오차 e는 그 운전점 젖은 곡선을 따라 V_k를 b = d ln V/d ln d(작은 기포 1.2~1.5)배로 함께 옮기므로 OLS 기울기가
    ĝ ≈ g + κ(b̄ − g), κ = 평균 σ_e²/var(ln d_k)만큼 치우친다 → g_eiv = (ĝ − κb̄)/(1 − κ)(σ_e는 꺾임 구간 폭/3.92, κ ≥ 0.5면 내지 않음).
    합성 늦은 터짐 시드 10개: OLS 0.588 ± 0.021, 보정 0.552 ± 0.023(참 0.541)."""
    p = [q for q in pts if q[0] > 0 and q[1] > 0]
    if len(p) < 3:
        return NAN, NAN, NAN, NAN, NAN
    x = np.log([q[0] for q in p]); y = np.log([q[1] for q in p])
    cf = np.polyfit(x, y, 1)
    g = float(cf[0])
    resid = float(np.sqrt(np.mean((y - np.polyval(cf, x)) ** 2)))
    sd_e = np.array([(math.log(q[3]) - math.log(q[2])) / 3.92 if q[2] == q[2] and q[3] == q[3] and q[3] > q[2] > 0 else 0.0 for q in p])
    bl = []
    for d, V, lo, hi, U, f, H in p:                       # 그 운전점 젖은 곡선의 국소 기울기 d ln V/d ln d
        bl.append((math.log(float(v_model([d / H * 1.01], U, f)[0])) - math.log(float(v_model([d / H / 1.01], U, f)[0]))) / (2 * math.log(1.01)))
    kap = float(np.mean(sd_e ** 2) / np.var(x)) if np.var(x) > 0 else NAN
    g_eiv = (g - kap * float(np.mean(bl))) / (1 - kap) if kap == kap and kap < 0.5 else NAN
    rng = np.random.default_rng(seed)
    gs = []
    for _ in range(n_boot):
        ii = rng.integers(0, len(p), len(p))
        xs, ys = [], []
        for i in ii:
            d, V, lo, hi, U, f, H = p[i]
            sd = (math.log(hi) - math.log(lo)) / 3.92 if lo == lo and hi == hi and hi > lo > 0 else 0.0
            dj = d * math.exp(rng.normal(0, sd)) if sd > 0 else d
            xs.append(math.log(dj)); ys.append(math.log(float(v_model([dj / H], U, f)[0])))
        if np.ptp(xs) > 1e-9:
            gs.append(np.polyfit(xs, ys, 1)[0])
    lo_, hi_ = (np.percentile(gs, [2.5, 97.5]) if len(gs) > 20 else (NAN, NAN))
    return g, float(lo_), float(hi_), resid, g_eiv


def run_table(runs, out, n_boot=200, fit_U=False, P=None, k=2, min_obs=6, verbose=True):
    """운전표 → 판정(U 흔들기 포함). 반환: 운전점 결과 목록과 요약 사전."""
    P = P or Params()
    os.makedirs(out, exist_ok=True)
    data = []
    for r in runs:
        tracks = read_tracks(r["tracking_csv"], r.get("flow", "up"), float(r["px_mm"]), float(r["fps"]), float(r["H_mm"]), k=k, min_obs=min_obs)
        U = _f(r.get("U_loc"))
        if not U == U:
            if not fit_U:
                if verbose:
                    print(f"  {r['name']}: U_loc이 없다. 작은 기포에서는 U/f 한 묶음만 정해져 꺾임을 못 믿는다 → U_loc 열(j_L/(1 − α), m/s)을"
                          " 넣거나 --fit_U로 강제한다.")
                continue
            dh = np.array([t["dH"] for t in tracks]); vv = np.array([t["V"] for t in tracks])
            U, _ = fit_wet(dh[vv > 0], vv[vv > 0])
        if len(tracks) < 3 * P.min_per_bin:
            if verbose:
                print(f"  {r['name']}: 트랙이 너무 적다({len(tracks)}개)")
            continue
        data.append(dict(name=r["name"], U=U, tracks=tracks, px_m=float(r["px_mm"]) * 1e-3, fps=float(r["fps"]), H_mm=float(r["H_mm"]),
                         q=_f(r.get("q_Wcm2")), W=_f(r.get("W_mm")), fov=_f(r.get("fov_mm"))))
    if not data:
        return [], {}
    base, f_ref, ref_names = analyse_runs(data, P, 1.0, n_boot=n_boot)
    lo_s, _, _ = analyse_runs(data, P, 1 - P.u_shift)
    hi_s, _, _ = analyse_runs(data, P, 1 + P.u_shift)
    res = []
    for d, o, ol, oh in zip(data, base, lo_s, hi_s):
        if not o["ok"]:
            continue
        H = d["H_mm"]
        row = dict(name=d["name"], q_Wcm2=d["q"], n_tracks=o["n_tracks"], H_mm=H, U=o["U"], f_run=o["f_run"], f_ref=f_ref,
                   f_ratio=o["f_run"] / f_ref if f_ref == f_ref and f_ref > 0 else NAN, win_frac=o["win_frac"], all_dry=o["all_dry"],
                   fast_bins=o["fast"])
        lim = NAN
        if d["W"] == d["W"] or d["fov"] == d["fov"]:
            lim = min(d["W"] / 2 if d["W"] == d["W"] else np.inf, 0.7 * d["fov"] if d["fov"] == d["fov"] else np.inf)
        row["large_limit_mm"] = lim
        for kk in ("1", "2"):
            dk = o["k" + kk]
            row[f"d_k{kk}_mm"] = dk * H
            row[f"d_k{kk}_lo_mm"], row[f"d_k{kk}_hi_mm"] = o.get(f"k{kk}_lo", NAN) * H, o.get(f"k{kk}_hi", NAN) * H
            row["p_k" + kk] = o.get("p_k" + kk, NAN)
            row["V_k" + kk] = o["V_k" + kk]
            row[f"depth{kk}"] = o["dep" + kk]
            alt = [ol["k" + kk] if ol["ok"] else NAN, oh["k" + kk] if oh["ok"] else NAN]
            row[f"robust{kk}"] = bool(dk == dk and all(a == a for a in alt))
            row[f"d_k{kk}_Ushift_mm"] = "/".join(f"{a * H:.2f}" if a == a else "-" for a in alt)
        row["large_outside"] = bool(row["d_k2_mm"] == row["d_k2_mm"] and lim == lim and row["d_k2_mm"] >= lim)
        bins_i, sp = intermittency(o, d["tracks"], o["U"], f_ref, d["px_m"], d["fps"], P)
        row["sigma_p_px"] = sp
        fi, _ = f_apparent(o["cen"], o["med"], o["U"])
        row["bins"] = []
        for b in range(len(o["cen"])):
            role = ("small_dry" if b in o["side1"] else "large_dry" if b in o["side2"] else
                    "out" if not o["valid"][b] else "wet" if o["win"] and o["win"][0] <= b <= o["win"][1] else "other")
            row["bins"].append(dict(d_over_H=float(o["cen"][b]), n=int(o["cnt"][b]), V_median=float(o["med"][b]), rel_se=float(o["sig"][b]),
                                    f_apparent=float(fi[b]), ratio=float(o["ratio"][b]), dry=bool(o["dry"][b]), role=role, **bins_i[b]))
        res.append(row)
    if verbose:
        write_outputs(res, out, P)
    summ = summarize(res, f_ref, ref_names, P, verbose=verbose)
    return res, summ


def summarize(res, f_ref, ref_names, P, verbose=True):
    """운전점 사이 판독: 기준 f, 대부분 마름 표시, U 민감 꺾임, 작은 쪽 g와 흩어짐, 큰 쪽(해석 범위 안), 판독 문구."""
    pr = print if verbose else (lambda *a, **k: None)
    summ = dict(f_ref=f_ref, ref=ref_names)
    pr(f"기준 f_ref {f_ref:.3f}(빠른 쪽 운전점 {', '.join(ref_names)}의 f_run 무게 중앙값; 모든 운전점을 이 f로 판정)")
    many = [r["name"] for r in res if r["all_dry"] or (r["f_ratio"] == r["f_ratio"] and r["f_ratio"] > P.f_tol)]
    summ["mostly_dry"] = many
    if many:
        pr(f"  f_run/f_ref > {P.f_tol:g}이거나 젖은 창 없음(대부분 마름 또는 오염 변화): {', '.join(many)}")
        if len(many) > len(res) / 2:
            pr("  경고: 운전점 과반이 대부분 마름이다. 기준 f가 마른 쪽에서 나왔을 수 있다 → 더 빠른 운전점을 더하거나 깨끗한 기준 운전을 따로 만든다.")
    nonrob = [(r["name"], s) for r in res for kk, s in (("1", "작은 쪽"), ("2", "큰 쪽")) if r[f"d_k{kk}_mm"] == r[f"d_k{kk}_mm"] and not r["robust" + kk]]
    summ["nonrobust"] = nonrob
    if nonrob:
        pr(f"  U_loc ±{P.u_shift:.0%}에서 사라지는 꺾임(U_loc 계통에 민감, 경계 맞춤에서 뺌): " + ", ".join(f"{n} {s}" for n, s in nonrob))
    small = [(r["d_k1_mm"], r["V_k1"], r["d_k1_lo_mm"], r["d_k1_hi_mm"], r["U"], r["f_ref"], r["H_mm"]) for r in res if r["robust1"]]
    summ["small_points"] = [(q[0], q[1]) for q in small]
    g_ols, glo, ghi, resid, g_eiv = kink_slope(small) if len(small) >= 3 else (NAN,) * 5
    g = g_eiv if g_eiv == g_eiv else g_ols                # 판독에는 오차-변수 보정값을 쓴다(구간은 OLS 구간을 같은 만큼 옮김)
    if g_eiv == g_eiv:
        glo, ghi = glo + (g_eiv - g_ols), ghi + (g_eiv - g_ols)
    summ.update(g=g, g_ols=g_ols, g_lo=glo, g_hi=ghi, resid=resid, n_small=len(small))
    deps = [r["depth1"] for r in res if r["robust1"] and r["depth1"] == r["depth1"]]
    pss_dry = [b["p_ss"] for r in res if r["robust1"] for b in r["bins"] if b["role"] == "small_dry" and b["p_ss"] == b["p_ss"]]
    pss_wet = [b["p_ss"] for r in res for b in r["bins"] if b["role"] == "wet" and b["p_ss"] == b["p_ss"]]
    summ["pss_small_dry"] = float(np.median(pss_dry)) if pss_dry else NAN
    summ["pss_wet"] = float(np.median(pss_wet)) if pss_wet else NAN
    summ["depth_small"] = float(np.median(deps)) if deps else NAN
    reasons = []
    cleaner = [r["name"] for r in res if r["fast_bins"] >= 2 and r["f_ratio"] == r["f_ratio"] and r["f_ratio"] < 1 / P.f_tol]
    if cleaner:                                           # 마름은 겉보기 f를 키우기만 하므로, f_ref보다 뚜렷이 깨끗한 운전점은 f 자체가 바뀐 것
        reasons.append(f"f_ref보다 뚜렷이 깨끗하고(f_run/f_ref < 1/{P.f_tol:g}) 유의하게 빠른 구간이 둘 이상인 운전점({', '.join(cleaner)}): 운전점마다 f가 다름")
    wet_base = [b["p_ss"] for r in res for b in r["bins"] if b["role"] == "wet" and b["p_ss"] == b["p_ss"]]
    wb = float(np.median(wet_base)) if wet_base else 0.0
    smooth_hi = []
    for r in res:                                         # f가 큰(대부분 마름으로 보이는) 운전점인데 느린 구간에 멈춤–출발이 없음
        if r["all_dry"] or (r["f_ratio"] == r["f_ratio"] and r["f_ratio"] > P.f_tol):
            ps = [b["p_ss"] for b in r["bins"] if b["dry"] and b["p_ss"] == b["p_ss"]]
            if ps and float(np.median(ps)) < wb + 0.05:
                smooth_hi.append(r["name"])
    if smooth_hi:
        reasons.append(f"f_run이 기준의 {P.f_tol:g}배를 넘는데 마른 구간에 멈춤–출발 초과분이 없는 운전점({', '.join(smooth_hi)}): 마름 대신 f 자체가 큼(오염) 가능")
    if len(small) >= 3:
        vk = np.array([q[1] for q in small])
        pr(f"작은 쪽 튼튼한 꺾임 {len(small)}개: g = d ln V_k/d ln d_k = {g:.2f} [{glo:.2f}~{ghi:.2f}](오차-변수 보정, OLS {g_ols:.2f})"
           + (f"(d_k ∝ V_k^{1 / g:.2f})" if g > 0.05 else "") + f", 맞춘 선 둘레 흩어짐 {resid:.2f}(ln), V_k {vk.min():.3f}~{vk.max():.3f} m/s, "
           f"꺾임 깊이 중앙값 {summ['depth_small']:.2f}, 멈춤–출발 p_ss 꺾임 구간 {summ['pss_small_dry']:.2f} 대 젖은 창 {summ['pss_wet']:.2f}")
        shallow = summ["depth_small"] == summ["depth_small"] and summ["depth_small"] < 0.25
        base_w = summ["pss_wet"] if summ["pss_wet"] == summ["pss_wet"] else 0.0
        no_stop = not (summ["pss_small_dry"] == summ["pss_small_dry"] and summ["pss_small_dry"] > base_w + 0.05)
        if g < -0.1:
            reasons.append(f"g {g:.2f} < 0")
        if resid > 0.2:
            reasons.append(f"V_k가 맞춘 선에서 흩어짐(rms {resid:.2f})")
        if shallow and no_stop:
            reasons.append("얕은 꺾임에 멈춤 초과분 없음")
        if reasons:
            pass
        elif abs(g) <= 0.2:
            pr("  판독: 세로에 가까움(V_k가 크기와 무관). 거칠기 뚫음·강제 풀림, 또는 속도 의존 오염 f(V) 후보 → 갭 심(H^(−3/2)), 멈춤 초과분, 밝기로 가름."
               " 모양만으로 기구를 정하지 않는다(검토 11 #1·#2).")
        elif 0.35 <= g <= 0.85:
            pr(f"  판독: 기운 경계(d_k ∝ V_k^{1 / g:.1f}). 늦은 터짐(1.7~2)·증발, 또는 옆 막(Burgess & Foster)의 거칠기 뚫음(d ∝ V²) 후보 → 모양만으로 기구를 정하지 않는다.")
        else:
            pr(f"  판독: g = {g:.2f}는 위 후보 범위 밖이다(점 수·구간 폭을 본다).")
        if no_stop and not reasons:
            pr("  참고: 꺾임 구간의 멈춤–출발 초과분이 잡음 바닥 안이다 → 운동학만으로는 마름 판정 불가(프레임보다 짧은 멈춤은 안 보임, 검토 11 #14).")
    else:
        pr(f"작은 쪽 튼튼한 꺾임 {len(small)}개(3개 미만이면 경계 모양을 말하지 않는다).")
    large_in = [(r["d_k2_mm"], r["V_k2"], r["d_k2_lo_mm"], r["d_k2_hi_mm"], r["U"], r["f_ref"], r["H_mm"]) for r in res
                if r["robust2"] and not r["large_outside"]]
    large_out = [r["name"] for r in res if r["robust2"] and r["large_outside"]]
    summ["n_large"] = len(large_in) + len(large_out)
    summ["n_large_in"] = len(large_in)
    dep2 = [r["depth2"] for r in res if r["robust2"] and r["depth2"] == r["depth2"]]
    pss2 = [b["p_ss"] for r in res if r["robust2"] for b in r["bins"] if b["role"] == "large_dry" and b["p_ss"] == b["p_ss"]]
    if dep2 and float(np.median(dep2)) < 0.25 and not (pss2 and float(np.median(pss2)) > wb + 0.05):
        reasons.append(f"큰 쪽 꺾임이 얕고(깊이 {float(np.median(dep2)):.2f}) 멈춤–출발 초과분이 없음: f가 크기에 따라 커짐(오염 분포·모양) 가능")
    if reasons:
        pr("  판독: g < 0이거나 V_k가 운전점마다 흩어짐(또는 얕은 꺾임에 멈춤 초과분 없음, 운전점마다 f가 다름) → 크기·속도 의존 마찰(오염,"
           " Ratulowski & Chang 1990형) 의심. 근거: " + "; ".join(reasons) + ". 마름이라고 하려면 멈춤 초과분과 운동학이 아닌 신호"
           "(I98 밝기, 위에서 본 마른 자리)가 필요하다.")
    summ["contamination_flag"] = bool(reasons)
    summ["contamination_reasons"] = reasons
    if not any(r["large_limit_mm"] == r["large_limit_mm"] for r in res) and any(r["robust2"] for r in res):
        pr("  큰 쪽 꺾임이 있으나 W_mm·fov_mm 열이 없어 해석 한계를 모른다(폭 채움 I95·시야 밖과 겹칠 수 있음, 검토 11 #8).")
    if large_out:
        pr(f"  큰 쪽 꺾임 중 d ≥ min(W/2, 0.7·시야)라 해석하지 않는 것: {', '.join(large_out)}")
    if len(large_in) >= 3:
        g2, g2lo, g2hi, _, _ = kink_slope(large_in)
        pr(f"큰 쪽 튼튼한 꺾임 {len(large_in)}개: d ln V_k/d ln d_k = {g2:.2f} [{g2lo:.2f}~{g2hi:.2f}](작은 쪽과 따로)")
    elif large_in:
        pr(f"큰 쪽 튼튼한 꺾임 {len(large_in)}개(3개 미만). 접촉선 힘이 둘레에 비례하면 큰 쪽 꺾임은 원래 드물다.")
    return summ


def write_outputs(res, out, P):
    keys = [k for k in res[0] if k != "bins"]
    with open(os.path.join(out, "mk_runs.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in res:
            w.writerow({k: (f"{r[k]:.5g}" if isinstance(r[k], float) else r[k]) for k in keys})
    bkeys = next((list(r["bins"][0].keys()) for r in res if r["bins"]), [])
    with open(os.path.join(out, "mk_bins.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(["name"] + bkeys)
        for r in res:
            for b in r["bins"]:
                w.writerow([r["name"]] + [f"{b[k]:.4g}" if isinstance(b[k], float) else b[k] for k in bkeys])
    for r in res:
        head = (f"  {r['name']}: 트랙 {r['n_tracks']}, U {r['U']:.3f} m/s, f_run {r['f_run']:.2f}(f_ref 대비 {r['f_ratio']:.2f}), "
                f"젖은 창 {r['win_frac']:.0%}" if not r["all_dry"] else f"  {r['name']}: 트랙 {r['n_tracks']}, U {r['U']:.3f} m/s — 젖은 구간 없음")
        parts = []
        for kk, side in (("1", "작은 쪽"), ("2", "큰 쪽")):
            if r[f"d_k{kk}_mm"] == r[f"d_k{kk}_mm"]:
                tag = "튼튼" if r["robust" + kk] else "U_loc에 민감"
                if kk == "2" and r["large_outside"]:
                    tag += ", 해석 밖"
                parts.append(f"{side} 꺾임 {r[f'd_k{kk}_mm']:.1f} mm [{r[f'd_k{kk}_lo_mm']:.1f}~{r[f'd_k{kk}_hi_mm']:.1f}]"
                             f"(부트스트랩 {r['p_k' + kk]:.0%}, U ∓{P.u_shift:.0%}에서 {r[f'd_k{kk}_Ushift_mm']} mm, {tag}), "
                             f"V_k {r['V_k' + kk]:.3f} m/s, 깊이 {r['depth' + kk]:.2f}")
        print(head + "; " + ("; ".join(parts) if parts else "꺾임 없음"))
        roles = defaultdict(list)
        for b in r["bins"]:
            roles[b["role"]].append(b)
        txt = []
        for role, lab in (("wet", "젖은 창"), ("small_dry", "작은 쪽 마른 구간"), ("large_dry", "큰 쪽 마른 구간")):
            bb = roles.get(role)
            if bb:
                pss = float(np.nanmedian([b["p_ss"] for b in bb])); ex = float(np.nanmedian([b["stop_excess"] for b in bb]))
                cvn = float(np.nanmedian([b["cv_noise"] for b in bb])) if any(b["cv_noise"] == b["cv_noise"] for b in bb) else NAN
                nst = sum(b["n_stopped"] for b in bb)
                flag = (" 판정 못 함(잡음 바닥이 큼)" if cvn == cvn and cvn > 0.7 else
                        (" 멈춤 안 보임(프레임보다 짧은 멈춤은 안 보임)" if pss < 0.05 and ex < 0.05 else ""))
                txt.append(f"{lab} p_ss {pss:.2f}·멈춤 초과 {ex:+.2f}·잡음 CV {cvn:.2f}·정지 트랙 {nst}{flag}")
        if txt:
            print(f"      간헐성(I114, σ_p {r['sigma_p_px']:.2f} px): " + "; ".join(txt))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.6, 4.2))
        for r in res:
            for kk, mk_, col in (("1", "o", "#2a78d6"), ("2", "s", "#eb6834")):
                if r[f"d_k{kk}_mm"] == r[f"d_k{kk}_mm"]:
                    filled = r["robust" + kk] and not (kk == "2" and r["large_outside"])
                    ax.plot([r["V_k" + kk]], [r[f"d_k{kk}_mm"]], mk_, ms=6, color=col, mfc=col if filled else "none")
        ax.plot([], [], "o", color="#2a78d6", label="small-side kink (robust)")
        ax.plot([], [], "s", color="#eb6834", label="large-side kink (robust)")
        ax.plot([], [], "o", color="#8a8986", mfc="none", label="open: U_loc-sensitive or outside min(W/2, 0.7 FOV)")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("wet-curve bubble speed at the kink V_k (m/s)"); ax.set_ylabel("kink size d_k (mm)")
        ax.legend(frameon=False, fontsize=7.2)
        ax.set_title("Mobility kinks (I112): candidates, not a mechanism", fontsize=9.5, loc="left")
        fig.tight_layout(); fig.savefig(os.path.join(out, "mk_plane.png"), dpi=150); plt.close(fig)
    except Exception as e:                                # 그림은 선택
        print(f"(그림 생략: {e})")


def _synth_run(path, U_true, U_loc, rng, n_tracks=400, d_range=(2.0, 60.0), H_mm=1.0, px_mm=0.02, fps=500.0, f_const=1.3, f_of_V=None,
               dry=None, dry_factor=0.55, dry_add=None, stop_p=0.3, spread=0.04, pos_noise=0.3, n_frames=12):
    """추적기 열 형식의 합성 CSV(1 mm 갭, 0.02 mm/px, 500 fps, 위치 잡음 0.3 px, 트랙당 12 프레임). 젖은 막은 Booth 곡선(f_const 또는
    속도 의존 f_of_V(V)를 자기 일관으로 풂). 마른 기포(dry(d, V_젖은))는 ×dry_factor 또는 V_젖은 − dry_add(d, V)로 늦추고 프레임의
    stop_p만큼 멈춘다(평균 속도는 그대로)."""
    rows = []
    for t in range(n_tracks):
        d_mm = math.exp(rng.uniform(math.log(d_range[0]), math.log(d_range[1])))
        if f_of_V is not None:
            V = float(v_model([d_mm / H_mm], U_true, 1.3)[0])
            for _ in range(60):
                Vn = float(v_model([d_mm / H_mm], U_true, f_of_V(V))[0])
                if abs(Vn - V) < 1e-10:
                    break
                V = 0.5 * (V + Vn)
        else:
            V = float(v_model([d_mm / H_mm], U_true, f_const)[0])
        isdry = bool(dry(d_mm, V)) if dry is not None else False
        if isdry:
            V = max(V - dry_add(d_mm, V), 0.0) if dry_add is not None else V * dry_factor
        V *= 1 + spread * rng.standard_normal()
        v_px = V / (px_mm * 1e-3 * fps)
        a_px = d_mm / px_mm / 2
        x = 100.0
        for kk in range(n_frames):
            if kk:
                x += ((0.0 if rng.random() < stop_p else v_px / (1 - stop_p)) if isdry and stop_p > 0 else v_px)
            rows.append({"ファイル名": f"f{t}_{kk}.png", "フレーム": t * (n_frames + 8) + kk, "トラックID": f"{t + 1}",
                         "イベント": "new" if kk == 0 else "normal", "面積(px)": f"{math.pi * a_px * a_px:.1f}",
                         "中心X": f"{x + rng.normal(0, pos_noise):.3f}", "中心Y": "500", "フレーム接触": "0"})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return dict(tracking_csv=path, px_mm=px_mm, fps=fps, H_mm=H_mm, flow="right", U_loc=U_loc, U_true=U_true)


LATE_U = (0.045, 0.05, 0.055, 0.065, 0.075)
VERT_U = (0.02, 0.03, 0.04, 0.06, 0.1)


def make_demo(out, seed=7):
    """자가 시험 운전점들. 참 경계: (가) 늦은 터짐 d > 20 mm·(V/0.05 m/s)^1.85(×0.55), (나) 세로 V < 0.03 m/s(×0.55),
    (다) 늦은 터짐 + 덧셈형 감속 0.02 m/s·H/d(접촉선 힘 ∝ 둘레). U_loc은 참값에 ±2% 무작위 오차. 마른 기포는 프레임의 30%에서 멈춤.
    마름 없는 대조(거짓 양성률): (라) U_loc −3% 계통, (마) 트랙 100개·퍼짐 10%, (바) 속도 의존 오염 f(V) = 1 + 1.5/(1 + (V/0.03)^4)."""
    rng = np.random.default_rng(seed)
    late = lambda d, V: d > 20.0 * (V / 0.05) ** 1.85
    cases = {
        "late": [dict(U=U, dry=late) for U in LATE_U],
        "vertical": [dict(U=U, dry=lambda d, V: V < 0.03) for U in VERT_U],
        "late_additive": [dict(U=U, dry=late, dry_add=lambda d, V: 0.02 * 1.0 / d) for U in LATE_U],
        "null_U-3%": [dict(U=U, U_err=-0.03, seed=s) for s in range(2) for U in VERT_U],
        "null_n100_spread10%": [dict(U=U, n_tracks=100, spread=0.10, U_err=0.0, seed=s) for s in range(2) for U in VERT_U],
        "null_f(V)": [dict(U=U, f_of_V=lambda V: 1.0 + 1.5 / (1 + (V / 0.03) ** 4), U_err=0.0) for U in VERT_U],
    }
    runs = {}
    for case, specs in cases.items():
        runs[case] = []
        for sp in specs:
            U = sp["U"]
            U_loc = U * (1 + sp["U_err"]) if "U_err" in sp else U * (1 + 0.02 * rng.uniform(-1, 1))
            name = f"{case}_U{U:g}" + (f"_s{sp['seed']}" if "seed" in sp else "")
            path = os.path.join(out, case, name, "result_tracking.csv")
            kw = {k: sp[k] for k in ("dry", "dry_add", "f_of_V", "n_tracks", "spread") if k in sp}
            r = _synth_run(path, U, U_loc, rng, **kw)
            r["name"] = name
            runs[case].append(r)
    return runs


def _true_late_cross(U, f=1.3, A=20.0, Vr=0.05, beta=1.85, H_mm=1.0):
    """합성 늦은 터짐 경계 d = A(V_젖은(d)/Vr)^β와 그 운전점 젖은 곡선의 두 교차(작은 쪽, 큰 쪽, mm)."""
    ds = np.exp(np.linspace(np.log(0.5), np.log(500), 20000))
    gg = ds - A * (v_model(ds / H_mm, U, f) / Vr) ** beta
    ii = np.where(np.sign(gg[:-1]) != np.sign(gg[1:]))[0]
    xs = [float(np.sqrt(ds[i] * ds[i + 1])) for i in ii]
    return (xs + [NAN, NAN])[:2]


def _demo(out):
    runs = make_demo(out)
    fails = []
    P = Params()

    def check(ok, msg):
        print(f"  {'통과' if ok else '실패'}  {msg}")
        if not ok:
            fails.append(msg.split(":")[0])
    for case, rr in runs.items():
        print(f"[{case}]")
        res, summ = run_table(rr, os.path.join(out, case), n_boot=60, P=P, verbose=True)
        n_run = len(res)
        k1 = sum(1 for r in res if r["robust1"]); k2 = sum(1 for r in res if r["robust2"])
        any_k = sum(1 for r in res if r["robust1"] or r["robust2"])
        raw_k = sum(1 for r in res if r["d_k1_mm"] == r["d_k1_mm"] or r["d_k2_mm"] == r["d_k2_mm"])
        if case == "late":
            g = summ.get("g", NAN)
            want, hit, cover, errs = 0, 0, 0, []
            for r in res:                                 # 참 교차가 판정 범위(d/H ≥ 3, 데이터 60 mm 안)에 있는 운전점만 센다
                U_t = float(r["name"].split("_U")[1])
                for side, dt in zip(("1", "2"), _true_late_cross(U_t)):
                    if not (P.min_dH_fit <= dt <= 60.0 / 1.6):     # 꺾임에는 바깥으로 마른 구간 둘(구간 폭 ×1.4)이 필요하다
                        continue
                    want += 1
                    dk = r[f"d_k{side}_mm"]
                    if dk == dk and r["robust" + side]:
                        hit += 1
                        errs.append(abs(math.log(dk / dt)))
                        cover += int(r[f"d_k{side}_lo_mm"] <= dt <= r[f"d_k{side}_hi_mm"])
            emax = max(errs) if errs else NAN
            check(hit == want and want >= 3 and emax < 0.15 and g == g and 0.35 <= g <= 0.8,
                  f"늦은 터짐: 판정 범위 안 참 교차 {want}개 중 {hit}개 검출, 크기 오차 최대 {emax:.1%}(허용 15%), 구간이 참값 품음 {cover}/{hit}, "
                  f"작은 쪽 g {g:.2f} [{summ.get('g_lo', NAN):.2f}~{summ.get('g_hi', NAN):.2f}](참 0.54, 허용 0.35~0.8)")
            pd_, pw = summ["pss_small_dry"], summ["pss_wet"]
            check(pd_ == pd_ and pw == pw and pd_ > 0.15 and pw < 0.08,
                  f"I114 간헐성: 멈춤–출발 p_ss 꺾임 구간 {pd_:.2f}(> 0.15; 참 0.30) 대 젖은 창 {pw:.2f}(< 0.08)")
        elif case == "vertical":
            g = summ.get("g", NAN)
            vk = np.array([q[1] for q in summ.get("small_points", [])]) if summ.get("small_points") else np.array([NAN])
            check(k1 >= 3 and g == g and abs(g) < 0.25 and abs(np.nanmean(vk) - 0.03) < 0.0075 and not summ["contamination_flag"],
                  f"세로 경계: 작은 쪽 튼튼한 꺾임 {k1}/{n_run}, g {g:.2f}(|·| < 0.25), V_k 평균 {np.nanmean(vk):.3f} m/s(참 V_c 0.030), "
                  f"오염 의심 {summ['contamination_flag']}")
        elif case == "late_additive":
            check(k2 == 0 and k1 >= 3, f"덧셈형 감속(∝ H/d): 큰 쪽 꺾임 {k2}개(0이 정상: 큰 기포는 10% 문턱을 못 넘음), 작은 쪽 {k1}/{n_run}")
        elif case.startswith("null_f"):
            check(summ["contamination_flag"],
                  f"속도 의존 오염 f(V)(마름 없음): 꺾임 운전점 {any_k}/{n_run}, 오염 의심 문구 {summ['contamination_flag']}(떠야 함)")
        else:
            rate = any_k / max(n_run, 1)
            check(rate <= 0.10, f"{case}(마름 없음): 거짓 양성 {any_k}/{n_run} = {rate:.0%}(허용 ≤ 10%; U 흔들기 전 {raw_k}/{n_run})")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="?", help="운전표 CSV(name, tracking_csv, px_mm, fps, H_mm, flow, U_loc, [q_Wcm2], [W_mm], [fov_mm])")
    ap.add_argument("--out", default="mk_out"); ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--fit_U", action="store_true", help="U_loc 없이 U와 f를 함께 맞춘다(작은 기포만이면 U/f 한 묶음만 정해짐, 권하지 않음)")
    ap.add_argument("--thr", type=float, default=0.1, help="꺾임 문턱: 비가 1 − max(thr, 2σ) 아래면 마른 구간")
    ap.add_argument("--n_bins", type=int, default=10); ap.add_argument("--min_obs", type=int, default=6, help="트랙당 최소 속도 관측 수")
    ap.add_argument("--min_per_bin", type=int, default=5)
    ap.add_argument("--s_max_fit", type=float, default=1.6, help="s < 1 구간이 셋 미만일 때 f에 쓸 s 상한")
    ap.add_argument("--min_dH_fit", type=float, default=3.0, help="이보다 작은 d/H 구간은 Booth 관계 밖이라 판정하지 않는다")
    ap.add_argument("--u_shift", type=float, default=0.03, help="U_loc을 이 비율만큼 흔들어 꺾임이 남는지 본다")
    ap.add_argument("--f_tol", type=float, default=1.3, help="f_run/f_ref가 이보다 크면 대부분 마름 또는 오염 변화로 표시")
    ap.add_argument("--stop_rel", type=float, default=0.25); ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--noise_px", type=float, default=NAN, help="위치 잡음(px)을 따로 잰 값으로 준다(정지 기포·표적). 비우면 젖은 구간 트랙의 2차 차분")
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
    P = Params(thr=a.thr, n_bins=a.n_bins, min_per_bin=a.min_per_bin, s_max_fit=a.s_max_fit, min_dH_fit=a.min_dH_fit, u_shift=a.u_shift,
               f_tol=a.f_tol, stop_rel=a.stop_rel, noise_px=a.noise_px)
    run_table(runs, a.out, a.n_boot, fit_U=a.fit_U, P=P, k=a.k, min_obs=a.min_obs)


if __name__ == "__main__":
    main()

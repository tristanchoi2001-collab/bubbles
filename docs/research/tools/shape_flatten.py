"""움직이는 기포의 정상 납작함으로 마찰 배율 f와 지수 m을 읽는다(아이디어 I109). 압력·국소장 불필요.

배경 (원형 근처 r = R(1 + ε·cos 2θ), θ는 흐름 방향 기준, 깨끗한 막)
    앞(β₁ 3.88)·뒤(β₂ −1.13) 메니스커스의 동적 점프 (2σ/H)·β·(Ca_V|cos θ|)^(2/3)(Wu 외 2024 식 3b 규약: β는 Ca^(2/3)에 곱한다,
    3Ca가 아님)의 2번 모드 ((β₁ + β₂)/2)·c₂ = 0.490(c₂ = 0.3566)을 평면 곡률 (π/4)σκ가 받는다.
    → ε = −0.416·f·(R/H)·Ca_V^(2/3)(음수 = 흐름 방향으로 눌림), Ca_V = μV/σ(그 기포의 속도). 바른 규약이면 Wu (A9) 첫 극한과 0.2% 안에서 같다(검토 9 #15).
    마찰이 D ∝ V^m이면 |ε| ∝ V^m.
    단, 이 식은 막 압력이 지배하는 작은 δ(Booth 매개변수 δ = 1.12·(d/H)·Ca^(1/3) ≲ 1.5)에서만 맞는다. Wu 외 2024(PRF 9:123603,
    저자 공개본)의 전체 이론·실험(실리콘유)은 모양이 δ에 대해 비단조다: 작은 기포는 눌리고(가로/길이 최소 약 1.06~1.09),
    큰 기포는 바깥 점성 압력 때문에 늘어나며, A = 1(원형)을 지나는 δ가 이론(ε 0.05)에서 약 2.5, 실험 그림에서 대략 2~3이다.
    Wu의 δ는 배경 유속 기준이고 이 도구의 δ_V = δ·s^(1/3)이라, δ 2~3은 δ_V 2.3~3.4이고 --delta_max 1.5(δ_V)는 δ 약 1.3이다(검토 9 #20).
    → 이 도구는 기울기를 δ_V < --delta_max 관측으로만 맞추고, ε_x가 음에서 양으로 바뀌는 δ_V(모양 영점)를 함께 낸다.
    오염 배율 f는 막 항을 키우므로 모양 영점도 약 f배로 옮긴다(가설).

쓰는 법
    python shape_flatten.py --csv result_tracking.csv --masks_dir OUTPUT_FOLDER/instances --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --out sf_out
        [--k 2] [--dH_bins 5,10,20,50] [--quiet 3] [--min_gap 1.0] [--delta_max 1.5] [--mu 1e-3] [--sigma 0.072] [--no_inv_r] [--n_boot 200]
    python shape_flatten.py --csv u02/result_tracking.csv,u05/result_tracking.csv,u10/result_tracking.csv
        --masks_dir u02/instances,u05/instances,u10/instances ...    # 유속이 다른 운전점 여럿(쉼표로, 같은 순서). m은 이때만 나온다
    python shape_flatten.py --demo --out sf_demo      # 합성 타원 마스크로 스스로 점검(f, m, 절편, 한쪽 윤곽 밀림, 한 운전점, 운전점별 f)

계산
    1. 트랙마다 중심 차분 속도 V(k프레임, 흐름 방향 성분). 화면 끝 접촉, 앞뒤 --quiet 프레임 안의 사건(merge/split/new), 면적 변화 20% 초과는 뺀다.
    2. 그 프레임 라벨 지도에서 기포 마스크(중심 3 px·면적 비 0.8~1.25로 짝지음)의 흐름 방향·가로 2차 모멘트 σ_ss, σ_cc로
       ε_x = (√σ_ss − √σ_cc)/(√σ_ss + √σ_cc)(정렬된 타원이면 (A − B)/(A + B)). 이웃 쌍극자 장의 변형은 방향이 무작위라 평균에서 빠진다.
       가장 가까운 이웃과의 틈이 --min_gap × 반경보다 좁은 관측은 뺀다(접촉 변형).
    3. δ_V = 1.12·(d/H)·Ca_V^(1/3)(국소장 대신 기포 속도로 잰 Booth 매개변수, δ보다 s^(1/3)배 큼)이 --delta_max 아래인 관측으로
       ε_x = b₀ + b₁/R − c·X를 최소 절대 편차(중앙값 회귀)로 맞춘다 → f = c/0.416. X = (R/H)·Ca_V^(2/3), R은 화소.
       b₀는 윤곽 비등방(화소 종횡비, 렌즈 왜곡, 분할 비등방)이 더하는 상수다(검토 9 #12).
       b₁/R은 한쪽 윤곽 밀림이다(검토 10 #12): 철 영상은 빛이 위에서 와 테두리 밝기가 방향마다 달라, 한쪽 윤곽이 δ px 밀리면
       ε = −δ/(4R)로 크기에 반비례한다. 이것은 X ∝ R과 상관해 상수 절편으로는 빠지지 않는다(한 운전점·0.5 px에서 상수 절편만이면
       f −13~−15%, b₁/R을 함께 맞추면 −5~+2%, 자가 시험).
       δ ≈ −4·b₁ px(+면 가로 쪽, −면 흐름 방향 쪽이 넓어짐)를 함께 낸다. --no_inv_r이면 b₁ 없이 맞춘다.
       크기 분포가 좁거나 몇 무리로 뭉치면 X와 1/R이 겹친다. 분산 팽창(X를 [1, 1/R]에 회귀한 1/(1 − R²))이 10을 넘으면 b₁을 맞추지 않는다
       (끝까지 시험 투명 CSV, 반경 8·20 px 두 무리: VIF 17, 참 f 0인데 b₁을 맞추면 f 0.92 [0.17~1.28], 상수 절편만이면 0.00).
       한 운전점은 VIF 약 6이라 맞추되 f 구간이 약 2배 넓어진다.
       비교용으로 상수 절편만(f_const)과 원점 통과(f0, X 분위 구간 중앙값)도 낸다. 원점 통과는 b₀가 f로 들어간다
       (바른 계수로 0.3 mm·0.05 m/s·d/H 10의 신호는 ε 0.016이라 0.003도 19%). f의 95% 구간은 트랙 단위 부트스트랩.
       이보다 복잡한 크기 의존 비등방은 못 잡는다 → 정지 기포(V → 0)나 철 영상은 기포를 180° 돌린 추론 비교로 크기별 b(R)을 따로 잰다.
    4. m: d/H 구간마다 ε_x = b₀' + b₁'/R − C·(R/H)·V^m을 m 격자로 맞춰 m과 그 구간의 절편 b₀'를 낸다(R/H를 곱해 크기 인자를 뺀다,
       검토 9 #21; 'all'의 b₀·b₁은 m 2/3 가정이라 m ≠ 2/3이면 속도 의존의 어긋남을 흡수하므로 빼지 않고 구간마다 다시 맞춘다;
       남길 관측은 m 2/3 맞춤에서 한 번 정해 고정한다, 검토 10 #21). 같은 까닭으로 m이 2/3과 크게 다르면 'all'의 f·δ도 치우친다.
       **한 운전점에서는 m이 식별되지 않는다**(검토 10 #11): 한 운전점 안의 속도 차는 크기 차(s(d))에서 오므로 V^m과 크기 의존이 섞인다.
       그래서 같은 크기에서의 속도 퍼짐(ln V를 ln R에 회귀한 잔차의 5~95% 범위)이 ln 2 이상일 때만 m을 낸다 = 유속이 다른 운전점을 묶었을 때.
       격자 끝(0.05, 1.5)에 붙은 m은 nan.
    5. 운전점을 묶기 전에 운전점마다 f를 따로 낸다(공통 b₁, 운전점별 b₀·c). 오염(계면활성제)이 유속·시간에 따라 바뀌면 f(U)의 변화가 m으로
       들어간다(검토 10 #13: f 1.0/1.3/1.6이면 참 m 2/3이 0.93~1.03). 운전점별 f(트랙 단위 부트스트랩 구간)가 가중 χ² 95%에서 같지 않고
       10% 넘게 다르면 m을 내지 않는다.
       단, 운전점별 f는 m 2/3을 가정한 값이라 "m ≠ 2/3"과 "f가 유속에 따라 바뀜"은 이 자료만으로는 가를 수 없다.
       f가 같을 때의 m은 2/3과의 일관성 확인이다. 유속 순서를 섞어(0.05 → 0.02 → 0.1 → 0.05) 같은 유속을 되풀이하면 시간 표류를 따로 본다.
    6. 모든 관측을 δ_V 분위 구간으로 나눠 ε_x − b₀ − b₁/R 중앙값이 음에서 양으로 바뀌는 δ_V(모양 영점)를 보간한다.
       양쪽 모두 중앙값이 0에서 문턱보다 멀리 떨어진 구간이 있어야 영점으로 본다(변형이 없으면 nan). 문턱은 트랙 단위 부트스트랩
       표준오차의 2배(같은 트랙 관측은 서로 상관한다, 검토 10 #20), 크기별 화소 잡음(부화소 중심이 무작위인 원판의 ε 산포
       ≈ 0.008·(8/R)^1.64, R 8/12/20/50 px에서 0.008/0.004/0.0015/0.0004), 0.002 중 큰 것(끝까지 시험 투명 CSV: 관측 단위 표준오차로는
       합체 꼬리·느린 작은 기포가 δ_V 0.30의 거짓 영점을 만들었고, 지금은 없음). 깨끗한 실리콘유(Wu 2024)는 δ 2~3 = δ_V 약 2.3~3.4.
출력: sf_obs.csv(관측별), sf_classes.csv(구간별 요약, 운전점별 f), 요약 출력.
주의: 관성(We = ρV²H/σ ≳ 0.1)도 기포를 누른다 → We가 큰 관측은 따로 본다(출력의 We 열). |ε| > 0.15는 선형 식 밖이다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

from merge_relax import MaskLookup, _f, read_rows

K_FLAT = 0.416          # ε = −K_FLAT·f·(R/H)·Ca_V^(2/3) (깨끗한 막, I109; 8·0.4903/(3π), Wu 2024 식 3b 규약)
M_GRID = np.linspace(0.05, 1.5, 146)
VIF_MAX = 10.0          # X(또는 m 맞춤의 Z)와 1/R의 분산 팽창이 이보다 크면 b₁/R을 맞추지 않는다(다중공선성의 흔한 기준)


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
        h = int(3 * math.sqrt(cnt[j] / math.pi)) + 6                 # 기포 둘레 창만 본다(전체 화상 비교는 느리다)
        y0, x0 = max(int(cys[j]) - h, 0), max(int(cxs[j]) - h, 0)
        win = inst[y0:int(cys[j]) + h + 1, x0:int(cxs[j]) + h + 1] == ids[j]
        if win.sum() != cnt[j]:                                      # 창 밖으로 뻗은 모양이면 전체 화상
            win = inst == ids[j]
        return eps_x_from_mask(win, flow, with_asym=True)


def collect(rows, masks, flow, k, H_px, px_m, fps, mu, sigma, rho=998.0, quiet=3, min_gap=1.0, op=1):
    """op는 운전점 번호(--csv를 여럿 주면 1, 2, ...)."""
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
    cand = []
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
            cand.append((f, tid, r, x, y, R, a[1], v_px))
    obs = []
    for f, tid, r, x, y, R, A, v_px in sorted(cand, key=lambda t: t[0]):     # 프레임 순서로(마스크 캐시가 맞도록)
        e, asym = masks.eps_x(r.get("ファイル名", ""), x, y, A, flow)
        if e != e:
            continue
        V = v_px * px_m * fps
        Ca = mu * V / sigma
        obs.append(dict(op=op, track=tid, frame=f, dH=2 * R / H_px, R_px=R, R_over_H=R / H_px, V=V, Ca=Ca,
                        We=rho * V * V * (H_px * px_m) / sigma, X=(R / H_px) * Ca ** (2 / 3),
                        delta_V=1.12 * (2 * R / H_px) * Ca ** (1 / 3), eps_x=e, asym=asym))
    return obs


def pix_floor(R):
    """화소화만으로 생기는 ε_x 산포(부화소 중심 무작위 원판, 검토 10 #20 측정 0.008/0.004/0.0015/0.0004 @ R 8/12/20/50 px의 맞춤)."""
    return 0.008 * (8.0 / max(R, 1.0)) ** 1.64


def _boot_idx(keys, strata, rng, n_boot):
    """트랙(keys) 단위 부트스트랩 표본 색인. 운전점(strata)마다 따로 뽑는다(운전점이 표본에서 빠지지 않게)."""
    groups = defaultdict(lambda: defaultdict(list))
    for i, (k, s) in enumerate(zip(keys, strata)):
        groups[s][k].append(i)
    per = [[np.array(v) for v in g.values()] for g in groups.values()]
    for _ in range(n_boot):
        yield np.concatenate([g[p] for g in per for p in rng.integers(0, len(g), len(g))])


def shape_zero(obs, b0=0.0, b1=0.0, n_d=10, eps_floor=0.002, n_boot=200, seed=0):
    """ε_x − b₀ − b₁/R 중앙값이 음에서 양으로 바뀌는 δ_V(모양 영점). 음·양 양쪽에 문턱을 넘는 구간이 없으면 nan.
    문턱 = max(2 × 트랙 단위 부트스트랩 표준오차, 그 구간 R 중앙값의 화소 잡음, eps_floor). 관측 단위 표준오차는 같은 트랙의
    관측이 서로 상관해 4~5배 작게 나오고(끝까지 시험 투명 CSV), 0.002는 작은 기포의 화소 수준보다 작다(검토 10 #20)."""
    if len(obs) < 30:
        return float("nan")
    rng = np.random.default_rng(seed)
    d = np.array([o["delta_V"] for o in obs]); R = np.array([o["R_px"] for o in obs])
    e = np.array([o["eps_x"] for o in obs]) - b0 - b1 / R
    keys = np.array([f"{o.get('op', 1)}|{o['track']}" for o in obs])
    q = np.quantile(d, np.linspace(0, 1, n_d + 1))
    dm, em, thr = [], [], []
    for i in range(n_d):
        m = (d >= q[i]) & (d <= q[i + 1])
        if m.sum() < 5:
            continue
        ei, ki = e[m], keys[m]
        bs = [np.median(ei[ix]) for ix in _boot_idx(ki, np.zeros(len(ki)), rng, n_boot)]
        se = float(np.std(bs)) if bs else 0.0
        dm.append(float(np.median(d[m]))); em.append(float(np.median(ei)))
        thr.append(max(2 * se, pix_floor(float(np.median(R[m]))), eps_floor))
    if not (any(v < -t for v, t in zip(em, thr)) and any(v > t for v, t in zip(em, thr))):
        return float("nan")
    for i in range(len(dm) - 1):
        if em[i] < 0 <= em[i + 1]:
            return dm[i] + (dm[i + 1] - dm[i]) * (-em[i]) / (em[i + 1] - em[i])
    return float("nan")


def fit_slope(X, E, n_x=8):
    """X 분위 구간의 중앙값으로 ε = b₀ − c·X(절편 있음)와 원점 통과 c₀를 맞춘다(표시·원점 통과 비교용)."""
    edges = np.quantile(X, np.linspace(0, 1, n_x + 1))
    xm, em = [], []
    for i in range(n_x):
        m = (X >= edges[i]) & (X <= edges[i + 1])
        if m.sum() >= 5:
            xm.append(float(np.median(X[m]))); em.append(float(np.median(E[m])))
    xm, em = np.array(xm), np.array(em)
    c0 = float(-(xm @ em) / (xm @ xm)) if len(xm) else float("nan")
    if len(xm) >= 3 and np.ptp(xm) > 0:
        k1, k0 = np.polyfit(xm, em, 1)
        c, b0 = float(-k1), float(k0)
    else:
        c, b0 = float("nan"), float("nan")
    return c, b0, c0, xm, em


def fit_l1(M, y, n_iter=60):
    """최소 절대 편차 회귀(중앙값 회귀, 가중 최소제곱 반복). 합체 뒤 늘어남·분할 실수 같은 꼬리에 강하다."""
    coef = np.linalg.lstsq(M, y, rcond=None)[0]
    for _ in range(n_iter):
        r = np.abs(y - M @ coef)
        sw = 1.0 / np.sqrt(np.maximum(r, 1e-3 * float(np.median(r)) + 1e-12))
        new = np.linalg.lstsq(M * sw[:, None], y * sw, rcond=None)[0]
        done = np.allclose(new, coef, rtol=1e-8, atol=1e-12)
        coef = new
        if done:
            break
    return coef


def vif_invr(X, R):
    """X를 [1, 1/R]에 회귀했을 때의 분산 팽창 1/(1 − R²). 크기 분포가 좁거나 몇 무리로 뭉치면 X와 1/R이 겹쳐 b₁과 c를 가를 수 없다
    (끝까지 시험 투명 CSV: 반경 8·20 px 두 무리, VIF 17에서 참 f 0인데 b₁/R을 맞추면 f 0.92 [0.17~1.28]). 합성 한 운전점 5.7, 묶음 1.3."""
    A = np.column_stack([np.ones_like(X), 1.0 / R])
    r = X - A @ np.linalg.lstsq(A, X, rcond=None)[0]
    return float(np.var(X) / max(float(np.var(r)), 1e-300))


def fit_flat(X, E, R=None):
    """ε = b₀ [+ b₁/R] − c·X를 중앙값 회귀로 맞춰 (c, b₀, b₁). R(px)을 주면 한쪽 윤곽 밀림 항 b₁/R을 함께 맞춘다(검토 10 #12)."""
    cols = [np.ones_like(X)] + ([1.0 / R] if R is not None else []) + [-X]
    coef = fit_l1(np.column_stack(cols), E)
    return float(coef[-1]), float(coef[0]), (float(coef[1]) if R is not None else 0.0)


def fit_ops(X, E, R, op, ops):
    """운전점마다 따로인 b₀·c와 공통 b₁/R(R이 None이면 없음)로 한꺼번에 맞춘다 → ({op: c}, {op: b₀})."""
    cols = [(op == o).astype(float) for o in ops] + ([1.0 / R] if R is not None else []) + [-X * (op == o) for o in ops]
    coef = fit_l1(np.column_stack(cols), E)
    n = len(ops)
    return dict(zip(ops, (float(v) for v in coef[-n:]))), dict(zip(ops, (float(v) for v in coef[:n])))


def speed_spread(v, rh):
    """같은 크기에서의 속도 퍼짐: ln V를 ln(R/H)에 직선 회귀한 잔차의 5~95% 범위(자연로그). 한 운전점이면 크기에서 오는 속도 차는 빠진다."""
    lv, lr = np.log(v), np.log(rh)
    r = lv - np.polyval(np.polyfit(lr, lv, 1), lr) if np.ptp(lr) > 0 else lv - lv.mean()
    return float(np.quantile(r, 0.95) - np.quantile(r, 0.05))


def fit_power(e, rh, v, R=None, m_grid=M_GRID):
    """ε = b₀ [+ b₁/R] − C·(R/H)·(V/V_med)^m를 m 격자마다 선형 최소제곱으로 맞춰 잔차가 가장 작은 m과 b₀, 격자 끝 여부.
    R/H를 곱해 크기 인자를 빼고(검토 9 #21), 구간 자신의 절편(과 R을 주면 한쪽 밀림 b₁/R)을 함께 맞춰 윤곽 비등방이 m으로
    들어가지 않게 한다(검토 9 #12, 검토 10 #12). 'all'의 b₀·b₁은 m 2/3 가정이라 m ≠ 2/3이면 속도 의존의 어긋남을 흡수하므로
    빼지 않는다(자가 시험 m 1/3: 'all' 절편을 빼면 0.81, 'all' b₁/R을 빼면 0.55, 함께 맞추면 0.29~0.34).
    남길 관측(잔차 3·MAD 안)은 m 2/3 맞춤에서 한 번 정해 모든 m에 같이 쓴다. m마다 남길 집합이 다르면 잔차 제곱 평균을
    서로 다른 표본으로 비교하게 된다(검토 10 #21: 운전점 3개·이상치 5%에서 m 평균 0.692 → 고정 0.672, 참 0.667)."""
    vn = v / np.median(v)
    if R is not None and vif_invr(rh * vn ** (2 / 3), R) > VIF_MAX:      # 이 구간에서는 1/R을 가를 수 없다
        R = None
    base = [np.ones_like(e)] + ([1.0 / R] if R is not None else [])
    M = np.column_stack(base + [-rh * vn ** (2 / 3)])
    r = e - M @ np.linalg.lstsq(M, e, rcond=None)[0]
    mad = float(np.median(np.abs(r - np.median(r)))) * 1.4826
    keep = np.abs(r - np.median(r)) <= 3 * mad if mad > 0 else np.ones_like(r, bool)
    if keep.sum() < 10:
        keep = np.ones_like(r, bool)
    best = (float("inf"), float("nan"), float("nan"))
    for m in m_grid:
        M = np.column_stack([b[keep] for b in base] + [-rh[keep] * vn[keep] ** m])
        coef = np.linalg.lstsq(M, e[keep], rcond=None)[0]
        sse = float(np.mean((e[keep] - M @ coef) ** 2))
        if coef[-1] > 0 and sse < best[0]:
            best = (sse, float(m), float(coef[0]))
    edge = best[1] == best[1] and (best[1] <= m_grid[0] + 1e-9 or best[1] >= m_grid[-1] - 1e-9)
    return best[1], best[2], edge


def _consistent(f, se, rel=0.10):
    """운전점별 f가 같다고 볼 수 있는가: 가중 평균 둘레 χ²가 95% 값(Wilson–Hilferty)을 넘고 동시에 최대/최소가 1 + rel을 넘으면 다르다."""
    f, se = np.asarray(f, float), np.asarray(se, float)
    if len(f) < 2 or np.any(~np.isfinite(f)):
        return True
    spread = f.max() / f.min() - 1 if f.min() > 0 else float("inf")
    if not np.all(np.isfinite(se) & (se > 0)):
        return spread <= rel
    w = 1 / se ** 2
    q = float(np.sum(w * (f - np.sum(w * f) / np.sum(w)) ** 2))
    k = len(f) - 1
    crit = k * (1 - 2 / (9 * k) + 1.645 * math.sqrt(2 / (9 * k))) ** 3
    return not (q > crit and spread > rel)


def analyse(obs_all, bins, n_x=8, delta_max=1.5, inv_r=True, n_boot=200, seed=0):
    rng = np.random.default_rng(seed)
    nan = float("nan")
    out = []
    obs = [o for o in obs_all if o["delta_V"] < delta_max]
    b0_all, b1_all, f_ok, use_r = 0.0, 0.0, True, inv_r
    if len(obs) >= 20:
        X, E, R, V = (np.array([o[k] for o in obs]) for k in ("X", "eps_x", "R_px", "V"))
        op = np.array([o.get("op", 1) for o in obs]); keys = [f"{o.get('op', 1)}|{o['track']}" for o in obs]
        vif = vif_invr(X, R)
        use_r = inv_r and vif <= VIF_MAX
        Rf = R if use_r else None
        c, b0, b1 = fit_flat(X, E, Rf)
        cc, bc, _ = fit_flat(X, E)
        _, _, c0, xm, em = fit_slope(X, E, n_x)
        bs = [fit_flat(X[i], E[i], None if Rf is None else Rf[i])[0] for i in _boot_idx(keys, op, rng, n_boot)]
        lo, hi = (np.percentile(bs, [2.5, 97.5]) / K_FLAT) if len(bs) >= 20 else (nan, nan)
        b0_all, b1_all = b0, b1
        out.append(dict(cls="all", n=len(obs), slope_c=c, f=c / K_FLAT, f_lo=float(lo), f_hi=float(hi), intercept=b0,
                        b1_invR=b1, shift_px=-4 * b1 if use_r else nan, inv_r_used=use_r, vif_invR=vif,
                        f_const=cc / K_FLAT, intercept_const=bc, slope_c0=c0, f0=c0 / K_FLAT, m=nan,
                        X_bins=";".join(f"{v:.4g}" for v in xm), eps_bins=";".join(f"{v:.4g}" for v in em),
                        X_med=float(np.median(X)), R_med=float(np.median(R)), V_med=float(np.median(V)),
                        delta_zero=shape_zero(obs_all, b0, b1), n_all=len(obs_all)))
        ops = sorted(set(op.tolist()))
        if len(ops) > 1:                                  # 운전점별 f(공통 b₁, 운전점별 b₀·c, 검토 10 #13)
            cs, b0s = fit_ops(X, E, Rf, op, ops)
            bo = defaultdict(list)
            for i in _boot_idx(keys, op, rng, n_boot):
                for o_, v in fit_ops(X[i], E[i], None if Rf is None else Rf[i], op[i], ops)[0].items():
                    bo[o_].append(v / K_FLAT)
            fs, ses = [], []
            for o_ in ops:
                sel = op == o_
                lo_, hi_ = np.percentile(bo[o_], [2.5, 97.5]) if len(bo[o_]) >= 20 else (nan, nan)
                fs.append(cs[o_] / K_FLAT); ses.append((hi_ - lo_) / 3.92)
                out.append(dict(cls=f"op{o_}", n=int(sel.sum()), slope_c=cs[o_], f=cs[o_] / K_FLAT, f_lo=float(lo_), f_hi=float(hi_),
                                intercept=b0s[o_], m=nan, V_med=float(np.median(V[sel])), X_bins="", eps_bins=""))
            f_ok = _consistent(fs, ses)
            out[0]["ops_f_consistent"] = f_ok
    for lo, hi in bins:
        sel = [o for o in obs if lo <= o["dH"] < hi]
        if len(sel) < 20:
            continue
        x, e, R = (np.array([o[k] for o in sel]) for k in ("X", "eps_x", "R_px"))
        c = float(-np.median((e - b0_all - b1_all / R) / x)) if np.all(x > 0) else nan
        v = np.array([o["V"] for o in sel]); rh = np.array([o["R_over_H"] for o in sel])
        spread = speed_spread(v, rh)
        m_raw, b0_m, edge = fit_power(e, rh, v, R if use_r else None)        # m_raw는 조건과 무관하게 맞춘 값(진단용)
        note = ("같은 크기의 속도 퍼짐 < 2배(한 운전점)" if spread < math.log(2) else "격자 끝" if edge
                else "운전점별 f가 다름" if not f_ok else "")
        out.append(dict(cls=f"dH_{lo:g}_{hi:g}", n=len(sel), slope_c=c, f=c / K_FLAT, m=m_raw if not note else nan, m_raw=m_raw,
                        m_note=note, v_spread=math.exp(spread), intercept_m=b0_m, X_bins="", eps_bins="",
                        We_med=float(np.median([o["We"] for o in sel])), asym_med=float(np.median([o["asym"] for o in sel]))))
    return out


def s_booth(dH, U, f=1.0, mu=1e-3, sigma=0.072):
    """한 운전점 합성용 이동도: Booth 관계 s^(2/3)/(2 − s) = δ_B/f, δ_B = 1.12·(d/H)·Ca_U^(1/3)(이분법)."""
    t = 1.12 * dH * (mu * U / sigma) ** (1 / 3) / f
    lo, hi = 1e-6, 2 - 1e-9
    for _ in range(60):
        s = 0.5 * (lo + hi)
        lo, hi = (s, hi) if s ** (2 / 3) / (2 - s) < t else (lo, s)
    return 0.5 * (lo + hi)


def make_demo(out, f_true=1.5, m_true=2 / 3, seed=4, b0_true=0.0, shift_px=0.0, U_op=None, n_tracks=90):
    """합성: 원형 근처 타원(흐름 방향 +x로 눌림 ε = −K_FLAT·f·(R/H)·Ca^(2/3)·(V/V₀)^(m − 2/3) + b₀ 꼴).
    U_op가 없으면 반경 25~70 px, 속도 0.01~0.2 m/s 로그 균등(운전점 여럿을 묶은 것과 같음, 크기와 무관).
    U_op(m/s)를 주면 한 운전점: 반경 22~100 px(d/H 2.9~13), V = s_Booth(d/H)·U_op·(1 + 0.03N)이라 속도 차가 크기에서만 온다.
    b₀는 윤곽 비등방(조명·분할)이 더하는 상수, shift_px는 화상 위쪽(가로 쪽) 윤곽만 그만큼 바깥으로 민 것(철 영상의 위쪽 조명, 검토 10 #12).
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
    for _ in range(n_tracks):
        tid += 1
        if U_op is None:
            R = rng.uniform(25, 70)
            V = 10 ** rng.uniform(math.log10(0.01), math.log10(0.2))      # m/s
        else:
            R = rng.uniform(22, 100)
            V = s_booth(2 * R / H_px, U_op, f_true, mu, sigma) * U_op * (1 + 0.03 * rng.standard_normal())
        Ca = mu * V / sigma
        eps = -K_FLAT * f_true * (R / H_px) * Ca ** (2 / 3) * (V / V0) ** (m_true - 2 / 3) + b0_true
        A_ax, B_ax = R * math.sqrt((1 + eps) / (1 - eps)), R * math.sqrt((1 - eps) / (1 + eps))   # A: 흐름 방향
        ang = rng.normal(0, 0.1)
        v_px = V / (px_m * fps)
        for kk in range(5):
            cx = 120.0 + kk * v_px + rng.normal(0, 0.1); cy = 150.0 + rng.normal(0, 0.1)
            xr = (xx - cx) * math.cos(ang) + (yy - cy) * math.sin(ang)
            yr = -(xx - cx) * math.sin(ang) + (yy - cy) * math.cos(ang)
            m = (xr / A_ax) ** 2 + (yr / B_ax) ** 2 <= 1
            if shift_px:
                m |= ((xr / A_ax) ** 2 + (yr / (B_ax + shift_px)) ** 2 <= 1) & (yy < cy)
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
    return path, dict(px_m=px_m, fps=fps, H_px=H_px, mu=mu, sigma=sigma, f=f_true, m=m_true, b0=b0_true)


def _demo_obs(out, name, op=1, **kw):
    sub = os.path.join(out, name)
    path, tr = make_demo(sub, **kw)
    return collect(read_rows(path), FlowMasks(os.path.join(sub, "instances")), "right", 2, tr["H_px"], tr["px_m"], tr["fps"],
                   tr["mu"], tr["sigma"], quiet=0, min_gap=0.0, op=op)


def _demo(out):
    fails = []

    def check(ok, label, msg):
        print(f"  {'통과' if ok else '실패'}  {label}: {msg}")
        if not ok:
            fails.append(label)

    def rows_of(res):
        return [r for r in res if r["cls"] == "all"][0], [r for r in res if r["cls"].startswith("dH")][0]

    for f_true, m_true, b0_true, shift in ((1.0, 2 / 3, 0.0, 0.0), (1.5, 2 / 3, 0.0, 0.0), (1.0, 1 / 3, 0.0, 0.0),
                                           (1.0, 2 / 3, 0.004, 0.0), (1.0, 2 / 3, 0.0, 0.5)):
        obs = _demo_obs(out, f"f{f_true:g}_m{m_true:.2f}_b{b0_true:g}_s{shift:g}", f_true=f_true, m_true=m_true, b0_true=b0_true,
                        shift_px=shift)
        ra, rc = rows_of(analyse(obs, [(2, 100)]))
        label = f"f {f_true:g}, m {m_true:.2f}, 절편 {b0_true:g}, 한쪽 밀림 {shift:g} px"
        if abs(rc["asym_med"]) > 0.01:
            fails.append(f"{label}: 대칭 타원의 앞뒤 비대칭 {rc['asym_med']:+.4f}(0이어야 함)")
        if abs(m_true - 2 / 3) < 1e-9:
            ok = abs(ra["f"] - f_true) <= 0.12 * f_true and abs(rc["m"] - m_true) <= 0.12
            want = b0_true - shift / (4 * ra["R_med"])                                          # 중앙 크기에서의 윤곽 비등방
            ok &= abs(ra["intercept"] + ra["b1_invR"] / ra["R_med"] - want) <= 0.0015
            if shift:
                ok &= abs(ra["shift_px"] - shift) <= 0.25
            check(ok, label, f"관측 {ra['n']}, 되찾은 f {ra['f']:.3f} [{ra['f_lo']:.3f}~{ra['f_hi']:.3f}](상수 절편만 {ra['f_const']:.3f}, "
                  f"원점 통과 {ra['f0']:.3f}), 절편 {ra['intercept']:+.4f}, 밀림 δ {ra['shift_px']:+.2f} px, m {rc['m']:.3f}")
        else:
            ok = abs(rc["m"] - m_true) <= 0.12
            check(ok, label, f"관측 {ra['n']}, 되찾은 m {rc['m']:.3f}(f는 m 2/3 가정이라 비교 안 함)")
    # 한 운전점: 속도 차가 크기에서만 오므로 m을 내면 안 된다(검토 10 #11). 한쪽 0.5 px 밀림은 상수 절편으로는 f를 약 −13% 치우친다(#12)
    for shift in (0.0, 0.5):
        obs = _demo_obs(out, f"single_op_U0.05_s{shift:g}", f_true=1.0, U_op=0.05, shift_px=shift, n_tracks=150)
        ra, rc = rows_of(analyse(obs, [(2, 100)]))
        ok = rc["m"] != rc["m"] and rc["m_note"].startswith("같은 크기") and abs(ra["f"] - 1.0) <= 0.12
        if shift:
            ok &= abs(ra["shift_px"] - shift) <= 0.25
        check(ok, f"한 운전점 U 0.05 m/s, 한쪽 밀림 {shift:g} px",
              f"m {rc['m']:.3f}({rc['m_note'] or '조건 통과'}; 같은 크기 속도 퍼짐 ×{rc['v_spread']:.2f}, 맞춘 값 {rc['m_raw']:.3f}), "
              f"f {ra['f']:.3f} [{ra['f_lo']:.3f}~{ra['f_hi']:.3f}](상수 절편만 {ra['f_const']:.3f}), 밀림 δ {ra['shift_px']:+.2f} px")
    # 운전점 셋(0.02/0.05/0.1 m/s): f가 같으면 m을 내고(2/3 근처), 유속마다 f가 바뀌면(1.0/1.3/1.6) m을 내지 않는다(검토 10 #13)
    for fs, want in (((1.0, 1.0, 1.0), True), ((1.0, 1.3, 1.6), False)):
        obs = []
        for i, (U, f_op) in enumerate(zip((0.02, 0.05, 0.1), fs), start=1):
            obs += _demo_obs(out, f"ops_U{U:g}_f{f_op:g}", op=i, seed=10 + i, f_true=f_op, U_op=U, n_tracks=120)
        res = analyse(obs, [(2, 100)])
        ra, rc = rows_of(res)
        fo = ", ".join(f"{r['f']:.2f} [{r['f_lo']:.2f}~{r['f_hi']:.2f}]" for r in res if r["cls"].startswith("op"))
        ok = ra["ops_f_consistent"] == want and ((abs(rc["m"] - 2 / 3) <= 0.12) if want else (rc["m"] != rc["m"]))
        check(ok, f"운전점 셋 f {'/'.join(f'{v:g}' for v in fs)}",
              f"운전점별 f {fo} → {'같음' if ra['ops_f_consistent'] else '다름'}, m {rc['m']:.3f}({rc['m_note'] or '조건 통과'}, 맞춘 값 {rc['m_raw']:.3f})")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", help="result_tracking.csv. 운전점이 여럿이면 쉼표로(--masks_dir도 같은 순서로)")
    ap.add_argument("--masks_dir")
    ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px), 예 0.02"); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--H_mm", type=float); ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--quiet", type=int, default=3); ap.add_argument("--min_gap", type=float, default=1.0)
    ap.add_argument("--delta_max", type=float, default=1.5, help="막 압력이 지배하는 작은 δ만 기울기 맞춤에 쓴다(Wu 2024)")
    ap.add_argument("--no_inv_r", action="store_true", help="한쪽 윤곽 밀림 항 b₁/R을 맞추지 않는다(상수 절편만)")
    ap.add_argument("--n_boot", type=int, default=200, help="트랙 단위 부트스트랩 횟수(f 구간, 운전점별 f 비교)")
    ap.add_argument("--dH_bins", default="5,10,20,50"); ap.add_argument("--mu", type=float, default=1.0e-3); ap.add_argument("--sigma", type=float, default=0.072)
    ap.add_argument("--out", default="sf_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.masks_dir and a.px_mm and a.H_mm):
        ap.error("--csv, --masks_dir, --px_mm, --H_mm가 필요하다")
    if a.px_mm > 1:
        ap.error("--px_mm은 화소 하나의 크기(mm/px)다(예 0.02). 1보다 크면 px/mm로 넣은 것 같다.")
    csvs, mdirs = a.csv.split(","), a.masks_dir.split(",")
    if len(csvs) != len(mdirs):
        ap.error(f"--csv {len(csvs)}개와 --masks_dir {len(mdirs)}개의 수가 다르다(운전점마다 하나씩, 같은 순서)")
    os.makedirs(a.out, exist_ok=True)
    obs = []
    for i, (cp, md) in enumerate(zip(csvs, mdirs), start=1):
        obs += collect(read_rows(cp), FlowMasks(md), a.flow, a.k, a.H_mm / a.px_mm, a.px_mm * 1e-3, a.fps, a.mu, a.sigma,
                       quiet=a.quiet, min_gap=a.min_gap, op=i)
    edges = [float(v) for v in a.dH_bins.split(",")]
    res = analyse(obs, list(zip(edges[:-1], edges[1:])), delta_max=a.delta_max, inv_r=not a.no_inv_r, n_boot=a.n_boot)
    if obs:
        with open(os.path.join(a.out, "sf_obs.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(obs[0].keys()))
            w.writeheader()
            for o in obs:
                w.writerow({kk: (f"{v:.5g}" if isinstance(v, float) else v) for kk, v in o.items()})
    if res:
        keys = list(dict.fromkeys(kk for r in res for kk in r))
        with open(os.path.join(a.out, "sf_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in res:
                w.writerow({kk: (f"{v:.5g}" if isinstance(v, float) else v) for kk, v in r.items()})
    print(f"관측 {len(obs)}개(운전점 {len(csvs)}개)")
    if not obs:
        H_px = a.H_mm / a.px_mm
        print(f"  쓸 관측이 없다. 마스크 짝(중심 3 px, 면적 비 0.8~1.25)·사건 앞뒤 {a.quiet} 프레임·틈 --min_gap·속도 > 0 조건을 확인한다"
              f"(H = {H_px:.1f} px, --flow {a.flow}).")
    for r in res:
        if r["cls"] == "all":
            print(f"  all: n {r['n']}(δ_V < {a.delta_max:g}), 기울기 c {r['slope_c']:.4f} → f {r['f']:.2f} [{r['f_lo']:.2f}~{r['f_hi']:.2f}]"
                  f"; 절편 {r['intercept']:+.4f}" + (f", 한쪽 윤곽 밀림 b₁ {r['b1_invR']:+.4f} → δ ≈ {r['shift_px']:+.2f} px" if r["inv_r_used"] else "")
                  + f"; 비교: 상수 절편만 f {r['f_const']:.2f}, 원점 통과 f {r['f0']:.2f}"
                  + (f"; 모양 영점 δ_V {r['delta_zero']:.2f}(전체 {r['n_all']}개)" if r["delta_zero"] == r["delta_zero"]
                     else f"; 모양 영점 없음(눌림·늘어남이 둘 다 문턱을 넘지 않음, 전체 {r['n_all']}개)"))
            if not a.no_inv_r and not r["inv_r_used"]:
                print(f"  참고: X와 1/R이 겹쳐(분산 팽창 {r['vif_invR']:.1f} > {VIF_MAX:g}, 크기 분포가 좁거나 몇 무리로 뭉침) 한쪽 윤곽 밀림 b₁/R을 "
                      "맞추지 않고 상수 절편만 썼다. 한쪽 밀림은 정지 기포나 180° 돌린 추론으로 따로 재야 한다(검토 10 #12).")
            sig = abs(r["slope_c"]) * r["X_med"]
            aniso = r["intercept"] + r["b1_invR"] / r["R_med"]
            if aniso == aniso and sig == sig and abs(aniso) > max(0.3 * sig, 0.0005):
                print(f"  경고: 중앙 크기(R {r['R_med']:.0f} px)의 윤곽 비등방 {aniso:+.4f}가 X 중앙값의 신호 {sig:.4f}의 30%를 넘는다. "
                      "상수 절편과 한쪽 밀림(1/R)은 맞춰 뺐지만, 그보다 복잡한 크기 의존 비등방(조명·화소·분할)은 못 잡는다 → "
                      "정지 기포나 180° 돌린 추론으로 크기별로 따로 재야 f를 믿을 수 있다(검토 9 #12, 검토 10 #12).")
        elif r["cls"].startswith("op"):
            print(f"  {r['cls']}: n {r['n']}, V 중앙값 {r['V_med']:.3f} m/s, f {r['f']:.2f} [{r['f_lo']:.2f}~{r['f_hi']:.2f}], 절편 {r['intercept']:+.4f}")
        else:
            print(f"  {r['cls']}: n {r['n']}(δ_V < {a.delta_max:g}), 기울기 c {r['slope_c']:.4f} → f {r['f']:.2f}"
                  + (f", m {r['m']:.2f}" if r["m"] == r["m"] else f", m 없음({r['m_note']})")
                  + f", We 중앙값 {r['We_med']:.3f}, 앞뒤 비대칭 {r['asym_med']:+.4f}")
    if res and "ops_f_consistent" in res[0]:
        print("  운전점별 f가 " + ("구간 안에서 같다 → 묶은 m은 m 2/3과의 일관성 확인이다." if res[0]["ops_f_consistent"] else
                                "다르다 → m을 내지 않는다. m ≠ 2/3이거나 오염이 유속·시간에 따라 바뀐 것이고, 이 자료만으로는 가를 수 없다"
                                "(검토 10 #13). 'all'의 f·δ도 운전점을 섞은 값이라 쓰지 않고 운전점별 f를 본다. "
                                "같은 유속을 순서를 섞어 되풀이해 시간 표류부터 본다."))
    elif len(csvs) == 1:
        print("  m: 운전점 하나에서는 속도 차가 크기 차에서 와 m이 식별되지 않는다(검토 10 #11). 유속이 다른 운전점을 --csv에 쉼표로 함께 준다.")
    print("읽는 법: 깨끗한 막이면 f ≈ 1, m ≈ 2/3. 실험실 물은 f > 1(I90 k_fit/16.85, I104 d*와 비교). We ≳ 0.1이면 관성도 누른다(I109).")
    print("         모양 영점(눌림 → 늘어남)은 깨끗한 실리콘유에서 대략 δ 2~3(Wu 외 2024 그림). 더 크면 막 마찰이 큰 것(오염) 후보다.")
    print("         앞뒤 비대칭(음수 = 뒤가 넓음)은 깨끗한 막에서 작은 음수(Wu 2024). 크게 음수면 뒤 접촉선이 붙는(마른 발자국) 후보다.")


if __name__ == "__main__":
    main()

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
      - 45°는 D = αλ. 두 결손의 비가 R인 것은 묽은 극한(α → 0)이다. 평균장 정확식은 D₄₅ = αλ(1 − αλR)/[1 − α²λ(Rs − 1)]이라
        D₀/D₄₅ = R[1 − α(R − 1)] + O(α²)다(α 0.1이면 m이 +0.03 치우친다, 검토 9 #8). 도구는 두 정확식을 함께 풀어 m을 가정하지 않고 낸다.
      - 빠른 큰 기포(λ > 0)는 무늬가 기포보다 느리고, 느린 작은 기포(λ < 0)는 빠르다. 이동도 1인 크기(I104의 d*)에서 같아진다.
      - 크기가 섞이면 구분마다 c_i/V_i − 1 ≈ −α_iλ_iR_i다(구분 속도가 서로 떨어져 있을 때, 자기 구분의 α_i만 들어간다).
      - 한 줄로 선 기포 열은 부호가 반대다. 압축파가 열보다 (2π²/3)·λR·(a/ℓ)²·V̄만큼 앞서 간다(ℓ = 중심 간격, 무한 셀·ℓ ≪ W/π;
        Booth, Griffiths & Howell 2023 "Hele-Shaw Newton's cradle"의 긴 파장 극한). 같은 구분이 한 줄(가로 퍼짐 < 2a)이면 경고한다.
      - 짧은 파장은 배제 영역 때문에 분산한다: ω ∝ J1(2ka)/(ka)(Desreumaux 식 8). 이 인자로 나눠 k → 0 값을 낸다.
    두 지점 상관으로 잰 "속도"(두 탐침, 큰 창의 긴 시간 상관)는 V̄가 아니라 c다(기포류 공극률 파의 고전 결과: Bernier 1982).

잴 수 있는 범위 (검토 9 #3)
    흐름 방향 모드 m ≥ 2가 ka ≤ ka_max에 들어와야 하므로 흐름 방향 시야 Ls ≥ 4πa/ka_max(ka_max 0.3이면 42a)인 구분만 잰다.
    흐름 방향 1080~1200 px·0.02 mm/px면 a ≤ 26~29 px, 즉 0.3 mm에서 d/H ≲ 3.5(λ < 0 쪽)뿐이다. 0.7·1 mm의 대부분, 큰 기포(D > 0),
    d* 영점, 철 영상(a ≥ 50 px)은 지금 시야로 잴 수 없다(이어 붙인 카메라·낮은 배율로 흐름 방향 시야를 넓힌다).
    --theta는 가로 시야도 Lc ≥ 4πa/ka_max여야 한다. 못 재는 구분은 빼되 이유와 필요한 시야(px)를 출력한다.

필요한 기록 (검토 9 #4b 모의)
    현실 시야(1080 × 416 px, a 20 px, 구분 α 0.05, 모드 1개, 시야 안 기포 약 18개)에서 통과 13번이면 D가 ±0.17로 흩어져 부호가
    절반 틀렸고, 통과 55번이면 sd 0.028이었다. 부호(3σ)만 보려면 시야 통과 약 200번(500 fps에서 약 4만 프레임), ±0.01(95%)이면
    약 1700번이 필요하다. "통과 10~30번이면 ±0.01"은 프레임당 760개·모드 8개인 데모 조건이다. 같은 운전을 여러 번 녹화해 통과 수를
    늘리거나 시야를 넓힌다. 통과당 10~20 프레임 이상이고 트랙이 이어지는 fps여야 한다(V_ref와 자기 기준이 같은 트랙의 ±1 프레임
    차분이라서). 트랙이 이어지지 않으면 --Vbar로 다른 녹화의 V̄를 준다.

쓰는 법
    python void_waves.py --csv result_tracking.csv --px_mm 0.02 --H_mm 0.3 --flow up --out vw_out
        [--dH_bins 2,5,15,50] [--fov s0,s1,c0,c1] [--ka_max 0.3] [--theta] [--m 0.667] [--weight area|count] [--n_boot 200] [--Vbar px/frame]
    python void_waves.py --demo --out vw_demo      # 평균장 입자 모의(세 경우)로 스스로 점검(약 3분)
    px_mm은 화소 하나의 크기(mm/px, 예 0.02)다. fov는 흐름 좌표(s = 흐름 방향, c = 가로)의 px 범위다. --flow up이면 s = −y, c = x라
    s0·s1이 음수다(예: 높이 1080 px 영상에서 위아래 20 px를 빼면 --fov -1060,-20,0,416). 비우면 검출 위치의 0.5~99.5% 범위.

계산
    1. 프레임마다 화면 끝에 닿지 않은 검출로 밀도장의 푸리에 성분 ρ_k(t) = Σ_j q_j·w(r_j)·exp(−ik·r_j)(q = 면적, w = 시야 Hann 창).
       무늬 속도 c는 ID가 필요 없다. 그러나 기준 V̄·V_ref는 같은 트랙의 ±1 프레임 차분으로 내므로 추적이 필요하다(V_ref가 0.5%
       치우치면 D 0.05의 10%가 틀린다, 검토 9 #9). 그래서 긴 트랙(≥ 10 표본)의 절사 평균 속도도 내 두 기준의 차를 보인다.
       띠(k_c = 0)는 가로로 창을 걸지 않는다(폭 평균). --theta면 가로에도 Hann 창.
    2. 집단 상관 C_c(k, τ) = Σ_t ρ_k(t + τ)·ρ_k*(t). 무늬가 c로 흐르면 위상이 −k_s·c·τ다.
    3. 같은 무게의 자기 기준 C_s(k, τ) = Σ_(t, j) q_j²·w(r_j)·w(r_j + v_jτ)·exp(−ik·v_jτ)(검출마다 그 순간 속도로 τ만큼 간다고 둔 것).
       창이 느린 기포를 오래 담는 치우침은 이것으로 빠진다. 위상 = −k_s·V_ref·τ. 상호작용이 없으면 퍼짐이 있어도 D = 0이다.
       구분 안의 속도 퍼짐은 빠지지 않는다: 상호작용이 있으면 퍼짐이 무늬의 집단 속도 자체를 바꾼다(운동론 효과. 모의에서 퍼짐 3%면
       D/αλR 1.03, 6% 1.06, 15~30% 1.17~1.28, 검토 9 #4). 그래서 구분마다 퍼짐 σ_V와 σ_V/|D·V̄|를 내고 0.5를 넘으면 경고한다.
       속도가 없고(트랙이 이어지지 않음) --Vbar를 주면 자기 기준 대신 exp(−ik_s·V̄τ)를 쓴다(창 머무름 치우침은 남는다).
    4. 결손 D(k, τ) = arg(C_c·C_s*)/(k_s·V_ref·τ) = 1 − c/V_ref. k_s·V̄·τ ≤ 3π인 짝만 쓰고, 무게 = 결맞음² × (k_s·V̄·τ)².
       k마다 J1 인자로 나눠 평균 → D₀. 95% 구간은 시간 블록(시야 통과 시간) 부트스트랩이다. 블록 사이에 최대 지연 τ_max만큼 간격을
       두고 두 프레임이 같은 블록에 든 짝만 블록에 넣어(이웃 블록 상관을 줄임) 그 퍼짐을 전체 추정에 옮긴다.
       시야 통과 블록이 3개 미만이면 D₀는 참고값(구간 없음)이고 s를 내지 않는다.
    5. 해석: X = D₀/α(α = 시야 안 그 구분의 면적 비율) = λR(묽은 극한). m을 가정하면 s = 2(1 + mX)/(2 − (1 − m)X)
       (압력·유량계·국소장이 필요 없다). 단분산 평균장 정확식으로 푼 s도 낸다. s가 (0, 2) 밖이거나 정확식이 풀리지 않으면
       "물리 범위 밖"으로 경고한다(잡음·배치 구조).
       α는 화면 끝에 닿은 검출까지 모든 검출(중심이 시야 안)의 보이는 면적(ROI内面積, 없으면 面積)으로 센다(끝 접촉을 빼면 2a/L만큼
       작다, 검토 9 #26). 잘린 검출의 구분은 같은 트랙의 끝에 닿지 않은 면적 중앙값으로 정한다.
    6. --theta: (k_s, k_c) 격자의 D를 D = A·g_A + B·g_B로 맞춘다. g_B = 창 전력 가중 평균 (k_s'/k_s)·cos 2θ'(흐름·가로 Hann 창의
       주 로브가 명목 모드에 이웃 모드를 섞는 것, 검토 9 #10), g_A = 같은 가중의 k_s'/k_s(≈ 1). 그러면 D₄₅ = A, D₀ = A + B다.
       두 평균장 정확식을 함께 풀어 λ, s = 1 + λ, R을 내고 m = ((1 + Δ)/R − 1)/Δ(Δ = 2/s − 1)를 낸다(m 가정 없음).
       측벽이 있으면 가로 모드가 cos(nπc/W)라 근사다. R 경로는 정밀도가 낮다(데모 조건에서도 m 구간이 0.6~0.85 정도) → I100 회귀의 점검용이다.
출력: vw_classes.csv(구분별, 뺀 구분은 이유와 필요한 시야), vw_k.csv(파수별), 요약 출력.
주의
    - 결손은 α|λ|R(몇 %)라 긴 녹화가 필요하다(위 "필요한 기록").
    - 합체는 면적을 보존하므로 면적 무게(기본)가 낫다. 구분 경계를 넘나드는 기포(합체·분열)는 구분 밀도를 보존하지 않는다
      → "all" 행(모든 크기)을 함께 본다. 크기가 넓게 섞이면 "all"의 D는 구분별 값의 섞임이고 퍼짐 경고가 난다.
    - 평균장은 α ≲ 0.2의 묽은 극한이다. 합체가 잦거나 큰 기포가 시야보다 크면 쓰지 않는다.
    - 자가 시험 모의는 속도 퍼짐 3%를 쓴다. 퍼짐 0은 쓰지 않는다(겹침 반발이 없어 비선형 뭉침이 생긴다. s 0.35에서 D/αλR 0.21까지, 검토 9 #25).
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

# 검출 배열의 열: s, c, 보이는 면적, 끝 접촉, v_s, v_c, 트랙 번호, 구분용 면적, α용 면적(ROI内面積)
NCOL = 9
LONG_TRACK = 10        # 긴 트랙 기준 속도에 쓰는 트랙의 최소 속도 표본 수(검토 9 #9)
SPREAD_WARN = 0.5      # σ_V/|D·V̄| 경고 문턱(검토 9 #4)
MIN_BLOCKS = 3         # 이보다 적은 시야 통과 블록이면 D₀는 참고값, s를 내지 않는다


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


def hann_leak_power(delta):
    """Hann 창의 푸리에 변환 전력(중심 1로 정규화). delta = 명목 파수에서 떨어진 칸 수(칸 = 2π/L).
    |W(δ)|/|W(0)| = |sin πδ/(πδ(1 − δ²))|이라 δ = ±1에서 전력 1/4, ±2에서 0(주 로브 끝)이다."""
    d = np.asarray(delta, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.sin(np.pi * d) / (np.pi * d * (1 - d * d))
    v = np.where(np.abs(d) < 1e-9, 1.0, v)
    v = np.where(np.abs(np.abs(d) - 1) < 1e-9, 0.5, v)
    return v * v


def leak_regressors(K, Ls, Lc, theta, half=2.0, n=161):
    """--theta 맞춤 회귀자 g_A = ⟨k_s'⟩/k_s, g_B = ⟨k_s'·cos 2θ'⟩/k_s(창 전력 가중, 주 로브 |δ| ≤ 2칸, 검토 9 #10).
    무늬 위상이 섞인 모드의 −k_s'·c'·τ 가중 평균이라 D_측정 = A·g_A + B·g_B다. 흐름 방향은 늘 Hann 창, 가로는 theta일 때만
    (띠 경로는 가로 창이 없어 g_A = g_B = 1)."""
    dd = np.linspace(-half, half, n)
    P = hann_leak_power(dd)
    gA, gB = np.ones(len(K)), np.ones(len(K))
    for i, (ks, kc) in enumerate(K):
        ks_ = ks + 2 * np.pi * dd / Ls
        if theta:
            KS, KC = np.meshgrid(ks_, kc + 2 * np.pi * dd / Lc, indexing="ij")
            W = np.outer(P, P)
        else:
            KS, KC = ks_[:, None], np.full((len(dd), 1), kc)
            W = P[:, None]
        k2 = KS ** 2 + KC ** 2
        c2 = np.where(k2 > 0, (KS ** 2 - KC ** 2) / np.maximum(k2, 1e-30), 0.0)
        gA[i] = float((W * KS).sum() / (W.sum() * ks))
        gB[i] = float((W * KS * c2).sum() / (W.sum() * ks))
    return gA, gB


def read_frames(path, flow):
    """프레임 → [(트랙, s, c, 보이는 면적, 끝 접촉, 구분용 면적, α용 면적)]과 CSV에 나온 모든 프레임(기포 없는 프레임 포함).
    구분용 면적: 화면 끝에 닿아 잘린 검출은 같은 트랙의 끝에 닿지 않은 프레임 면적 중앙값(없으면 보이는 면적).
    α용 면적: ROI内面積(없으면 面積)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ax, sgn = axis_of(flow)
    recs, allf, full = [], set(), defaultdict(list)
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
        A_roi = _f(r.get("ROI内面積(px)"))
        e = r.get("フレーム接触") == "1"
        s_, c_ = (sgn * y, x) if ax == "Y" else (sgn * x, y)
        recs.append((f, tid, s_, c_, A, e, A_roi if A_roi == A_roi and A_roi >= 0 else A))
        if not e:
            full[tid].append(A)
    med = {t: float(np.median(v)) for t, v in full.items()}
    frames = defaultdict(list)
    for f, tid, s_, c_, A, e, A_al in recs:
        frames[f].append((tid, s_, c_, A, e, med.get(tid, A) if e else A, A_al))
    return frames, sorted(allf)


def attach_velocities(frames, k=1):
    """검출마다 NCOL 열(s, c, 면적, 끝 접촉, v_s, v_c, 트랙 번호, 구분용 면적, α용 면적).
    속도는 같은 트랙의 ±k 프레임 중심 차분(끝 접촉·면적 변화 20% 초과면 NaN)."""
    tr = defaultdict(dict)
    for f, lst in frames.items():
        for tid, s_, c_, A, e, *_ in lst:
            tr[tid][f] = (s_, c_, A, e)
    idx = {t: i for i, t in enumerate(tr)}
    out = {}
    for f, lst in frames.items():
        arr = []
        for tid, s_, c_, A, e, A_cls, A_al in lst:
            fr = tr[tid]
            vs = vc = float("nan")
            if not e and (f - k) in fr and (f + k) in fr:
                p, q = fr[f - k], fr[f + k]
                if not (p[3] or q[3]) and max(p[2], A, q[2]) <= 1.2 * min(p[2], A, q[2]):
                    vs, vc = (q[0] - p[0]) / (2 * k), (q[1] - p[1]) / (2 * k)
            arr.append((s_, c_, A, 1.0 if e else 0.0, vs, vc, float(idx[tid]), A_cls, A_al))
        out[f] = np.array(arr, float) if arr else np.zeros((0, NCOL))
    return out


def _lags(Vbar, Ls, nF):
    tau = sorted({max(1, int(round(r * Ls / abs(Vbar)))) for r in (0.1, 0.2, 0.3, 0.4, 0.5)})
    return [t for t in tau if t <= max(1, nF // 3)]


def class_series(frames_v, frame_list, lo, hi, H_px, fov):
    """구분 [lo, hi) d/H의 프레임별 배열(끝 접촉 제외), 시야 안 면적 비율 α, 중앙 반경.
    구분은 구분용 면적으로 정한다. α는 끝 접촉을 포함한 모든 검출(중심이 시야 안)의 α용 면적으로 센다(검토 9 #26)."""
    s0, s1, c0, c1 = fov
    per, tot, radii = [], [], []
    for f in frame_list:
        a = frames_v.get(f)
        if a is None or not len(a):
            per.append(np.zeros((0, NCOL))); tot.append(0.0)
            continue
        dH = np.sqrt(4 * a[:, 7] / np.pi) / H_px
        incl = (dH >= lo) & (dH < hi)
        inside = (a[:, 0] >= s0) & (a[:, 0] <= s1) & (a[:, 1] >= c0) & (a[:, 1] <= c1)
        tot.append(float(a[incl & inside, 8].sum()))
        keep = incl & (a[:, 3] < 0.5)
        per.append(a[keep])
        radii.extend(np.sqrt(a[keep & inside, 2] / np.pi).tolist())
    alpha = float(np.mean(tot)) / ((s1 - s0) * (c1 - c0)) if tot else 0.0
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


def solve_band45(D0, D45, alpha, n_it=500):
    """띠·45° 평균장 정확식을 함께 풀어 (λ, R)을 낸다(검토 9 #8).
        D₀ = αλR/[1 + α(Rs − 1)],   D₄₅ = αλ(1 − αλR)/[1 − α²λ(Rs − 1)],   s = 1 + λ
    감쇠 고정점 반복(α 0.05~0.3, s 0.2~1.8에서 70번 안에 수렴). 못 풀면 1차 보정식 R ≈ ρ[1 + α(ρ − 1)](ρ = D₀/D₄₅),
    λ ≈ X/(1 − αXR)(X = D₄₅/α)을 쓴다."""
    nan = float("nan")
    if not (alpha > 0 and D0 == D0 and D45 == D45) or abs(D45) < 1e-9:
        return nan, nan
    lam, R = D45 / alpha, D0 / D45
    for _ in range(n_it):
        s = 1 + lam
        if abs(lam) < 1e-9:
            break
        R_new = D0 * (1 + alpha * (R * s - 1)) / (alpha * lam)
        den = alpha * (1 - alpha * lam * R_new)
        if den == 0:
            break
        lam_new = D45 * (1 - alpha ** 2 * lam * (R_new * s - 1)) / den
        if not (math.isfinite(R_new) and math.isfinite(lam_new)):
            break
        R2, lam2 = 0.5 * (R + R_new), 0.5 * (lam + lam_new)
        done = abs(R2 - R) < 1e-12 and abs(lam2 - lam) < 1e-12
        R, lam = R2, lam2
        if done:
            break
    ok = False
    if math.isfinite(lam) and math.isfinite(R) and -1 < lam < 1 and R > 0:
        s = 1 + lam
        r0 = alpha * lam * R / (1 + alpha * (R * s - 1)) - D0
        r45 = alpha * lam * (1 - alpha * lam * R) / (1 - alpha ** 2 * lam * (R * s - 1)) - D45
        ok = abs(r0) < 1e-7 + 1e-4 * abs(D0) and abs(r45) < 1e-7 + 1e-4 * abs(D45)
    if not ok:
        rho, X = D0 / D45, D45 / alpha
        R = rho * (1 + alpha * (rho - 1))
        den = 1 - alpha * X * R
        lam = X / den if den != 0 else nan
    return lam, R


def theta_readout(D0, D45, alpha):
    """(D₀, D₄₅, α) → λ, s, R, m(m 가정 없음). 해가 물리 범위(0 < s < 2, R > 0) 밖이면 s·R·m은 NaN이고 theta_in_range가 거짓.
    |λ| ≤ 0.05면 두 결손이 거의 영이라 m은 정해지지 않는다."""
    nan = float("nan")
    lam, R = solve_band45(D0, D45, alpha)
    s = 1 + lam if lam == lam else nan
    ok = bool(s == s and 0 < s < 2 and R == R and R > 0)
    m = nan
    if ok and abs(lam) > 0.05:
        Dl = 2 / s - 1
        m = ((1 + Dl) / R - 1) / Dl
    if not ok:
        s = R = nan
    return {"lam_theta": lam, "s_theta": s, "R_theta": R, "m_theta": m, "theta_in_range": ok}


def analyse_class(per, frame_list, fov, a_ref, theta=False, weight="area", ka_max=0.3, n_boot=200, seed=0, Vbar_hint=None,
                  alpha=float("nan")):
    """한 구분의 결손 D₀(띠)과 --theta면 D₄₅·D₀ 맞춤. per = 프레임별 배열(frame_list 순서).
    잴 수 없으면 {"skip": 이유, ...}를 돌려준다(조용히 빼지 않는다, 검토 9 #3)."""
    nan = float("nan")
    s0, s1, c0, c1 = fov
    Ls, Lc = s1 - s0, c1 - c0
    nF = len(frame_list)
    need_Ls = 4 * math.pi * a_ref / ka_max                 # 흐름 방향 모드 m = 2가 ka ≤ ka_max에 드는 시야
    # 같은 무게((q·w)²)의 평균 흐름 방향 속도·퍼짐과 트랙별 평균
    num = den = num2 = 0.0
    trk = defaultdict(lambda: [0.0, 0.0, 0])               # 트랙 → [Σ무게·v, Σ무게, 표본 수]
    for b in per:
        if not len(b):
            continue
        ok = np.isfinite(b[:, 4])
        if not ok.any():
            continue
        q, w = _weights(b[ok], fov, theta, weight)
        ww = (q * w) ** 2
        v = b[ok, 4]
        num += float((ww * v).sum()); den += float(ww.sum()); num2 += float((ww * v * v).sum())
        for t_, v_, w_ in zip(b[ok, 6], v, ww):
            if w_ > 0:
                e_ = trk[int(t_)]
                e_[0] += w_ * v_; e_[1] += w_; e_[2] += 1
    has_v = den > 0
    if not has_v and Vbar_hint is None:
        return {"skip": "속도 없음(트랙이 ±1 프레임으로 이어지지 않음): fps를 높이거나 --Vbar로 다른 녹화의 V̄를 준다"}
    V_meas = num / den if has_v else nan
    Vbar = V_meas if Vbar_hint is None else float(Vbar_hint)
    if not abs(Vbar) > 1e-9:
        return {"skip": "흐름 방향 평균 속도가 0이다"}
    sigV = math.sqrt(max(num2 / den - V_meas ** 2, 0.0)) if has_v else nan
    lt = [(e_[0] / e_[1], e_[1]) for e_ in trk.values() if e_[2] >= LONG_TRACK and e_[1] > 0]
    longv = np.array([v_ for v_, _ in lt]); longw = np.array([w_ for _, w_ in lt])
    V_long = sigV_trk = nan
    if len(longv) >= 5:                                    # 긴 트랙 평균 속도의 10~90% 절사 평균(검토 9 #9), V̄와 같은 무게
        o = np.argsort(longv)
        cw = np.cumsum(longw[o]) / longw.sum()
        mid = o[(cw >= 0.1) & (cw - longw[o] / longw.sum() <= 0.9)]
        if len(mid):
            V_long = float(np.average(longv[mid], weights=longw[mid]))
        Vw = float(np.average(longv, weights=longw))
        sigV_trk = float(math.sqrt(np.average((longv - Vw) ** 2, weights=longw)))
    # 파수 격자
    m_max = int(math.floor(ka_max * Ls / (2 * math.pi * a_ref)))
    if m_max < 2:
        return {"skip": f"흐름 방향 모드 없음: 시야 {Ls:.0f} px < 필요 {need_Ls:.0f} px(= 4πa/ka_max, a {a_ref:.1f} px, ka_max {ka_max:g})",
                "need_Ls_px": need_Ls}
    K = [(2 * math.pi * mm / Ls, 0.0) for mm in range(2, m_max + 1)]
    if theta:
        n_max = int(math.floor(ka_max * Lc / (2 * math.pi * a_ref)))
        for nn in range(2, n_max + 1):
            for mm in range(2, m_max + 1):
                ks, kc = 2 * math.pi * mm / Ls, 2 * math.pi * nn / Lc
                if math.hypot(ks, kc) * a_ref <= ka_max:
                    K += [(ks, kc), (ks, -kc)]
    K = np.array(K)
    nK = len(K)
    lags = _lags(Vbar, Ls, nF)
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
    pos = {f: i for i, f in enumerate(frame_list)}
    transit = Ls / abs(Vbar)                               # 시야 통과 시간(프레임)
    blen = max(max(lags), int(round(transit)))
    nb = max(1, nF // blen)                                # 시야 통과 블록 수
    gap = max(lags)                                        # 부트스트랩 블록 사이 간격 τ_max(검토 9 #19)
    period = blen + gap
    nbb = (nF + gap) // period
    nL = len(lags)
    Cc = np.zeros((nL, nK), complex); Cs = np.zeros_like(Cc)
    N1 = np.zeros((nL, nK)); N0 = np.zeros_like(N1)
    nB = max(nbb, 1)
    Ccb = np.zeros((nL, nB, nK), complex); Csb = np.zeros_like(Ccb)
    N1b = np.zeros((nL, nB, nK)); N0b = np.zeros_like(N1b)

    def gblock(i):
        bi = i // period
        return bi if (i % period) < blen and bi < nbb else -1

    for li, tau in enumerate(lags):
        for i, f in enumerate(frame_list):
            j = pos.get(f + tau)
            if j is None:
                continue
            cc_ = rho[j] * np.conj(rho[i])
            n1_, n0_ = np.abs(rho[j]) ** 2, np.abs(rho[i]) ** 2
            cs_ = None
            b = per[i]
            if has_v and len(b):
                ok = np.isfinite(b[:, 4])
                if ok.any():
                    bb = b[ok]
                    q, w = _weights(bb, fov, theta, weight)
                    moved = bb.copy(); moved[:, 0] += bb[:, 4] * tau; moved[:, 1] += bb[:, 5] * tau
                    _, w2 = _weights(moved, fov, theta, weight)
                    ww = q * q * w * w2
                    sel = ww > 0
                    if sel.any():
                        ph = np.exp(-1j * tau * (np.outer(bb[sel, 4], K[:, 0]) + np.outer(bb[sel, 5], K[:, 1])))
                        cs_ = ww[sel] @ ph
            Cc[li] += cc_; N1[li] += n1_; N0[li] += n0_
            if cs_ is not None:
                Cs[li] += cs_
            bi = gblock(i)
            if bi >= 0 and gblock(j) == bi:
                Ccb[li, bi] += cc_; N1b[li, bi] += n1_; N0b[li, bi] += n0_
                if cs_ is not None:
                    Csb[li, bi] += cs_
    lag_arr = np.array(lags, float)
    ka = np.hypot(K[:, 0], K[:, 1]) * a_ref
    gk = disp_factor(ka)
    band = K[:, 1] == 0
    gA, gB = leak_regressors(K, Ls, Lc, theta)
    ceff = gB / gA                                         # 창 누설을 넣은 유효 cos 2θ

    def estimate(cc, cs, n1, n0):
        kt = K[None, :, 0] * lag_arr[:, None]
        x = kt * Vbar                                      # k_s·V̄·τ
        if has_v:
            vref = Vbar - np.angle(cs * np.exp(1j * x)) / kt
            dphi = np.angle(cc * np.conj(cs))
        else:                                              # --Vbar만: 자기 기준 대신 V̄로 위상을 푼다
            vref = np.full(x.shape, Vbar)
            dphi = np.angle(cc * np.exp(1j * x))
        D = dphi / (kt * vref)
        coh = np.abs(cc) / np.sqrt(np.maximum(n1 * n0, 1e-300))
        wgt = coh ** 2 * x ** 2 * (np.abs(x) <= 3 * math.pi) * (coh > 0.05)
        W = wgt.sum(0)
        Dk = np.where(W > 0, (wgt * D).sum(0) / np.maximum(W, 1e-300), np.nan)
        Dk0 = Dk / gk
        okb = band & (W > 0)
        D0 = float((W[okb] * Dk0[okb]).sum() / W[okb].sum()) if okb.any() else nan
        A_ = B_ = nan
        okt = W > 0
        if theta and okt.sum() >= 3 and np.ptp(ceff[okt]) > 0.3:
            Xd = np.stack([gA[okt], gB[okt]], 1)
            sw = np.sqrt(W[okt])
            coef, *_ = np.linalg.lstsq(Xd * sw[:, None], Dk0[okt] * sw, rcond=None)
            A_, B_ = float(coef[0]), float(coef[1])
        fin = np.isfinite(vref)
        return D0, A_, B_, Dk, W, float(np.median(vref[fin])) if fin.any() else Vbar

    D0, A_, B_, Dk, Wk, Vref = estimate(Cc, Cs, N1, N0)
    res = {"V_px_per_frame": Vbar, "V_meas": V_meas, "V_ref": Vref, "V_long": V_long, "n_long_tracks": int(len(longv)),
           "sigma_V": sigV, "sigma_V_track": sigV_trk, "D0": D0, "n_blocks": nb, "block_frames": blen,
           "n_transit": nF / transit, "frames_per_transit": transit, "n_boot_blocks": nbb, "lags": lags,
           "n_k_band": int(band.sum()), "self_ref": bool(has_v)}
    sp = sigV_trk if sigV_trk == sigV_trk else sigV
    res["spread_ratio"] = sp / abs(D0 * Vbar) if (sp == sp and D0 == D0 and abs(D0 * Vbar) > 0) else nan
    if V_long == V_long and Vref == Vref and abs(Vref) > 0:
        res["dV_long_rel"] = (V_long - Vref) / Vref
    if theta:
        res["A"], res["B"] = A_, B_
        res["D45"], res["D0_theta"] = A_, A_ + B_
        res["R_ratio"] = (A_ + B_) / A_ if (A_ == A_ and abs(A_) > 1e-9) else nan
        res.update(theta_readout(A_ + B_, A_, alpha))
    if nbb >= 4:
        def est_cnt(cnt):
            return estimate(*(np.tensordot(cnt, X, axes=([0], [1])) for X in (Ccb, Csb, N1b, N0b)))
        g0 = est_cnt(np.ones(nbb))
        thg = theta_readout(g0[1] + g0[2], g0[1], alpha) if theta else None
        rng = np.random.default_rng(seed)
        bs = defaultdict(list)
        for _ in range(n_boot):
            cnt = np.bincount(rng.integers(0, nbb, nbb), minlength=nbb).astype(float)
            d0, a_, b_, *_ = est_cnt(cnt)
            bs["D0"].append(d0 - g0[0])
            if theta:
                t_ = theta_readout(a_ + b_, a_, alpha)
                for key in ("R_theta", "m_theta", "s_theta"):
                    bs[key].append(t_[key] - thg[key])
        for key, arr in bs.items():                        # 간격 둔 블록의 퍼짐을 전체 추정에 옮긴다
            arr = np.array(arr, float)
            arr = arr[np.isfinite(arr)]
            if len(arr) >= 20 and res.get(key) == res.get(key):
                lo, hi = np.percentile(arr, [2.5, 97.5])
                res[key + "_lo"], res[key + "_hi"] = res[key] + float(lo), res[key] + float(hi)
    res["k_table"] = [(float(K[i, 0]), float(K[i, 1]), float(ka[i]), float(ceff[i]), float(Dk[i]), float(Wk[i])) for i in range(nK)]
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


def analyse(frames_v, frame_list, H_px, bins, fov, theta=False, weight="area", ka_max=0.3, m=2 / 3, n_boot=200, seed=0, Vbar_hint=None):
    """구분별 결과 행(잴 수 없는 구분은 "skip" 이유와 함께)과 파수별 행."""
    rows, krows = [], []
    Lc = fov[3] - fov[2]
    for lo, hi, name in [(lo, hi, f"{lo:g}~{hi:g}") for lo, hi in bins] + [(0.0, float("inf"), "all")]:
        per, alpha, a_med = class_series(frames_v, frame_list, lo, hi, H_px, fov)
        if not (a_med == a_med) or not alpha > 0:
            rows.append({"class": name, "skip": "시야 안에 이 구분의 (화면 끝에 닿지 않은) 검출이 없다"})
            continue
        th_c, th_note = theta, ""
        if theta:
            need_Lc = 4 * math.pi * a_med / ka_max
            if Lc < need_Lc:
                th_c = False
                th_note = (f"--theta 안 함: 가로 시야 {Lc:.0f} px < 필요 {need_Lc:.0f} px(= 4πa/ka_max; ka_max 0.3이면 42a). "
                           "띠 결손만 낸다")
        r = analyse_class(per, frame_list, fov, a_med, theta=th_c, weight=weight, ka_max=ka_max, n_boot=n_boot, seed=seed,
                          Vbar_hint=Vbar_hint, alpha=alpha)
        out = {"class": name, "alpha": alpha, "a_px": a_med, "lateral_sd_px": lateral_spread(per, fov)}
        if "skip" in r:
            out.update(r)
            rows.append(out)
            continue
        out.update({k: v for k, v in r.items() if k != "k_table"})
        if th_note:
            out["theta_note"] = th_note
        X = r["D0"] / alpha
        out["lamR"] = X
        if r["n_blocks"] >= MIN_BLOCKS:
            sd = out["s_dilute"] = s_from_X(X, m)
            se = out["s_exact"] = s_from_D_exact(r["D0"], alpha, m)
            out["s_in_range"] = bool(sd == sd and 0 < sd < 2 and se == se)
        else:                                              # 블록 < 3: D₀는 참고값, s는 내지 않는다(검토 9 #4b)
            out["s_dilute"] = out["s_exact"] = float("nan")
            out["s_in_range"] = False
            for key in ("lam_theta", "s_theta", "R_theta", "m_theta"):
                if key in out:
                    out[key] = float("nan")
            if "theta_in_range" in out:
                out["theta_in_range"] = False
        rows.append(out)
        for ks, kc, ka, ce, Dk, W in r["k_table"]:
            krows.append({"class": name, "k_s": ks, "k_c": kc, "ka": ka, "cos2_eff": ce, "D_k": Dk, "weight": W})
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


def _ci(r, key, fmt):
    if key + "_lo" in r:
        return f" [{format(r[key + '_lo'], fmt)}~{format(r[key + '_hi'], fmt)}]"
    return ""


def report(rows, m, theta):
    """구분별 결과를 사람이 읽게 출력한다."""
    nan = float("nan")
    short = False
    for r in rows:
        if "skip" in r:
            extra = f" (a {r['a_px']:.1f} px, α {r['alpha']:.3f})" if "a_px" in r else ""
            print(f"{r['class']}: 뺌 — {r['skip']}{extra}")
            continue
        head = (f"{r['class']}: α {r['alpha']:.3f}, a {r['a_px']:.1f} px, V̄ {r['V_px_per_frame']:.2f} px/frame"
                f"(시야 통과 {r['n_transit']:.1f}번, 통과당 {r['frames_per_transit']:.0f} 프레임)")
        if r["n_blocks"] < MIN_BLOCKS:
            print(head + f", 띠 결손 D₀ {r['D0']:+.4f} — 참고값(구간 없음): 시야 통과 블록 {r['n_blocks']}개 < {MIN_BLOCKS}이라 s를 내지 않는다")
        else:
            ci = _ci(r, "D0", "+.4f") or " [구간 없음: 간격 둔 부트스트랩 블록 < 4]"
            print(head + f", 띠 결손 D₀ = 1 − c/V̄ {r['D0']:+.4f}{ci} (블록 {r['n_blocks']}개 × {r['block_frames']} 프레임)"
                         f" → λR {r['lamR']:+.2f}, s(묽은, m {m:.2f}) {r['s_dilute']:.2f}, s(평균장 정확) {r['s_exact']:.2f}")
            if not r["s_in_range"]:
                print("  경고: s가 물리 범위(0 < s < 2) 밖이거나 정확식이 풀리지 않는다 → 잡음·배치 구조(줄 배열, 짧은 기록, 크기 섞임) 탓일"
                      " 가능성이 크다. 이 구분의 s를 쓰지 않는다.")
        sp = r.get("spread_ratio", nan)
        if r["sigma_V"] == r["sigma_V"]:
            print(f"  구분 안 속도 퍼짐: 검출별 σ_V {r['sigma_V']:.3f} px/frame, 긴 트랙 평균 사이 {r['sigma_V_track']:.3f}"
                  f"(트랙 {r['n_long_tracks']}개) → σ_V/|D₀·V̄| {sp:.2f}")
        if sp == sp and sp > SPREAD_WARN:
            print(f"  경고: 퍼짐이 결손에 비해 크다(> {SPREAD_WARN}). 퍼짐은 무늬의 집단 속도 자체를 바꾼다(모의: 퍼짐 15~30%면 D가 αλR의"
                  " 1.17~1.28배, 검토 9 #4). 구간을 좁히거나 단분산 운전만 쓴다.")
        if "dV_long_rel" in r:
            dv = r["dV_long_rel"]
            print(f"  기준 속도: 자기 기준 V_ref {r['V_ref']:.3f}, 긴 트랙(≥ {LONG_TRACK} 표본) 무게 10~90% 절사 평균 {r['V_long']:.3f} px/frame"
                  f" → 차 {100 * dv:+.2f}%는 D를 약 {dv:+.4f} 옮긴다(δD ≈ δV/V̄). 무늬 속도 c는 ID가 필요 없지만 기준은 추적으로 낸다.")
        if not r["self_ref"]:
            print("  참고: 속도가 없어 --Vbar로 위상을 풀었다. 자기 기준이 없어 창이 느린 기포를 오래 담는 치우침은 빠지지 않는다.")
        if theta and "D45" in r:
            if not r["D45"] == r["D45"]:
                print("  방향 맞춤 못 함: 쓸 수 있는 비스듬한 모드가 부족하다(유효 cos 2θ 폭 < 0.3)")
            elif r["n_blocks"] < MIN_BLOCKS:
                print(f"  방향 맞춤: D₄₅ {r['D45']:+.4f}, D₀ {r['D0_theta']:+.4f} — 참고값(블록 < {MIN_BLOCKS}이라 λ·R·m을 내지 않는다)")
            elif not r.get("theta_in_range"):
                print(f"  방향 맞춤: D₄₅ {r['D45']:+.4f}, D₀ {r['D0_theta']:+.4f}, 비 {r['R_ratio']:.3f} → 평균장 정확식의 해가 물리 범위"
                      "(0 < s < 2, R > 0) 밖이다(잡음·배치 구조). λ·R·m을 쓰지 않는다.")
            else:
                print(f"  방향 맞춤(창 누설 회귀자): D₄₅ {r['D45']:+.4f}, D₀ {r['D0_theta']:+.4f}, 비 {r['R_ratio']:.3f} → 평균장 정확식으로"
                      f" λ {r['lam_theta']:+.3f}, s {r['s_theta']:.2f}{_ci(r, 's_theta', '.2f')}, R {r['R_theta']:.3f}{_ci(r, 'R_theta', '.3f')},"
                      f" m {r['m_theta']:.2f}{_ci(r, 'm_theta', '.2f')}(m 가정 없음, 정밀도가 낮아 I100 회귀의 점검용)")
                if r["R_theta"] < 1:
                    print("  참고: R < 1(m > 1)은 알려진 마찰(선형 m = 1 ~ 마른 접촉선 m ≈ 0) 밖이다 → 잡음이나 크기 섞임을 먼저 의심한다.")
        elif "theta_note" in r:
            print("  " + r["theta_note"])
        if r["lateral_sd_px"] == r["lateral_sd_px"] and r["lateral_sd_px"] < 2 * r["a_px"]:
            print("  경고: 이 구분은 가로로 거의 한 줄이다(가로 표준편차 < 2a). 한 줄 기포 열은 결손의 부호가 반대다(Booth 외 2023). 2차원 해석을 쓰지 않는다.")
        if r["frames_per_transit"] < 10:
            print("  경고: 통과당 프레임이 10 미만이라 지연이 몇 개뿐이다. 통과당 10~20 프레임 이상이고 트랙이 이어지는 fps로 찍는다.")
        short = short or r["n_transit"] < 200
    if short:
        print("참고: 시야 통과가 200번 미만인 구분이 있다. 현실 시야(흐름 방향 모드 1~2개, 시야 안 기포 수십 개)에서 부호를 3σ로 보려면 통과 약"
              " 200번, ±0.01(95%)이면 약 1700번이 필요하다(검토 9 #4b 모의). 통과 10~30번으로 충분한 것은 프레임당 760개·모드 8개인 데모 조건이다.")


# ---------------------------------------------------------------- 합성 자가 시험
def simulate(seed, s, m, alpha, n_frames=3000, Lx=3200.0, Ly=640.0, a=8.0, Vbar=10.0, spread=0.03, noise=0.2, h=8.0,
             fov=(400.0, 2800.0), csv_path=None, csv_frames=150):
    """평균장 입자 모의(주기 상자). 기포마다 V = V̄_j·x̂ + diag(R·s, s)·δu, δu_k = −λU·δα_k·(cos 2θ, sin 2θ)·J1(2ka)/(ka).
    면적 비율장은 CIC로 만든다. 시야 [fov] 안의 검출만 내고, 시야에 다시 들어올 때마다 새 트랙 ID를 준다.
    속도 퍼짐 0은 쓰지 않는다: 겹침 반발이 없어 비선형 뭉침이 생긴다(검토 9 #25).
    돌려주는 것: frames_v(프레임 → NCOL 열 배열), frame_list, 참 α, R."""
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
                arr.append((x_, y_, area, 1.0 if e_ else 0.0, vs, vc, float(key[0] * 1000 + key[1]), area, area))
                if csv_path and pf < csv_frames:
                    rows.append({"ファイル名": f"f{pf}.png", "フレーム": pf, "トラックID": key[0] * 1000 + key[1], "イベント": "",
                                 "面積(px)": f"{area:.3f}", "ROI内面積(px)": f"{area:.3f}", "中心X": f"{x_:.4f}", "中心Y": f"{y_:.4f}",
                                 "フレーム接触": "1" if e_ else "0"})
            frames_v[pf] = np.array(arr, float) if arr else np.zeros((0, NCOL))
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
    m = 2 / 3
    lines = []
    # 0. 대수 점검: 평균장 정확식으로 만든 (D₀, D₄₅)를 되풀어 λ, R, m이 나오는지(검토 9 #8)
    ok_all = True
    for s_, a_ in ((0.35, 0.1), (1.55, 0.1), (0.35, 0.2)):
        lam_ = s_ - 1; R_ = R_of(s_, m)
        D0e = a_ * lam_ * R_ / (1 + a_ * (R_ * s_ - 1))
        D45e = a_ * lam_ * (1 - a_ * lam_ * R_) / (1 - a_ * a_ * lam_ * (R_ * s_ - 1))
        t_ = theta_readout(D0e, D45e, a_)
        good = abs(t_["s_theta"] - s_) < 1e-6 and abs(t_["R_theta"] - R_) < 1e-6 and abs(t_["m_theta"] - m) < 1e-6
        Dl = 2 / s_ - 1
        m_naive = ((1 + Dl) / (D0e / D45e) - 1) / Dl
        lines.append(f"정확식 역산(s {s_}, α {a_}): 비 {D0e / D45e:.3f}(R {R_:.3f}) → s {t_['s_theta']:.4f}, R {t_['R_theta']:.4f},"
                     f" m {t_['m_theta']:.4f}(비를 R로 보면 m {m_naive:.3f})  → " + ("통과" if good else "실패"))
        ok_all = ok_all and good
    cases = [("A 빠른 큰 기포(λ > 0)", 1.55, 0.10, 0.03, False),
             ("B 느린 작은 기포(λ < 0), 방향 의존", 0.35, 0.10, 0.03, True),
             ("C 상호작용 없음(λ = 0), 속도 퍼짐 10%", 1.0, 0.10, 0.10, False)]
    for ci, (name, s, alpha, spread, theta) in enumerate(cases):
        csv_path = os.path.join(out, f"demo_{ci}.csv") if ci == 0 else None
        fv, fl, a_true, R = simulate(seed=7 + ci, s=s, m=m, alpha=alpha, spread=spread, csv_path=csv_path)
        H_px = 1.6                                      # d 16 px → d/H 10(한 구분)
        rows, _ = analyse(fv, fl, H_px, [(2.0, 50.0)], fov, theta=theta, ka_max=0.4 if theta else 0.3, m=m, n_boot=100)
        r = [x for x in rows if x["class"] == "2~50"][0]
        lam = s - 1
        D_true = a_true * lam * R                       # 묽은 극한 띠 결손(모의의 커널이 쓰는 값)
        ci_txt = f"[{r.get('D0_lo', float('nan')):.4f}~{r.get('D0_hi', float('nan')):.4f}]"
        line = (f"{name}: α {r['alpha']:.4f}(참 {a_true:.4f}), V̄ {r['V_px_per_frame']:.2f} px/frame, 퍼짐 비 {r['spread_ratio']:.2f}, "
                f"띠 결손 D₀ {r['D0']:+.4f} {ci_txt}, 참 αλR {D_true:+.4f}; s(묽은, m 2/3) {r['s_dilute']:.3f}(참 {s:.2f})")
        tol = 0.012 + 0.15 * abs(D_true)
        good = abs(r["D0"] - D_true) <= tol
        if theta:
            line += (f"; 방향 맞춤 D₄₅ {r['D45']:+.4f}(참 αλ {a_true * lam:+.4f}), D₀ {r['D0_theta']:+.4f}(참 αλR {D_true:+.4f}), "
                     f"→ s {r['s_theta']:.3f}{_ci(r, 's_theta', '.3f')}(참 {s:.2f}), R {r['R_theta']:.3f}{_ci(r, 'R_theta', '.3f')}(참 {R:.3f}), "
                     f"m {r['m_theta']:.3f}{_ci(r, 'm_theta', '.3f')}(참 {m:.3f})")
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
    ap.add_argument("--csv")
    ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px), 예 0.02(px/mm가 아님)")
    ap.add_argument("--H_mm", type=float, help="갭(mm)")
    ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--fov", default="", help="s0,s1,c0,c1(흐름 좌표 px). --flow up이면 s = −y라 s0·s1이 음수다"
                    "(예: 높이 1080 px에서 위아래 20 px를 빼면 -1060,-20,0,416). 비우면 검출 위치의 0.5~99.5%% 범위")
    ap.add_argument("--ka_max", type=float, default=0.3)
    ap.add_argument("--theta", action="store_true", help="(k_s, k_c) 격자로 D₄₅와 D₀를 함께 맞춰 λ·R·m을 낸다(가로 시야 ≥ 4πa/ka_max, 점검용)")
    ap.add_argument("--m", type=float, default=2 / 3, help="띠 결손에서 s를 풀 때 가정하는 마찰 지수(깨끗한 막 2/3)")
    ap.add_argument("--weight", default="area", choices=["area", "count"])
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--Vbar", type=float, default=None, help="흐름 방향 평균 기포 속도(px/frame, 흐름 방향이 양수). 다른 녹화의 값."
                    " 트랙이 이어지지 않아 속도가 없을 때 쓴다(추적기의 上昇速度는 음수라 부호를 바꿔 넣는다)")
    ap.add_argument("--out", default="vw_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm and a.H_mm):
        ap.error("--csv, --px_mm, --H_mm가 필요하다")
    if a.px_mm > 1:
        ap.error(f"--px_mm {a.px_mm:g}: 화소 하나의 크기(mm/px)를 넣는다(예 0.02). 1보다 크면 px/mm로 넣은 것이다(→ {1 / a.px_mm:.4g})")
    if a.Vbar is not None and not a.Vbar > 0:
        ap.error("--Vbar는 흐름 방향으로 양수(px/frame)로 준다")
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
    rows, krows = analyse(fv, allf, H_px, bins, fov, theta=a.theta, weight=a.weight, ka_max=a.ka_max, m=a.m, n_boot=a.n_boot,
                          Vbar_hint=a.Vbar)
    _write(rows, os.path.join(a.out, "vw_classes.csv")); _write(krows, os.path.join(a.out, "vw_k.csv"))
    print(f"프레임 {len(allf)}개, 시야 s {fov[0]:.0f}~{fov[1]:.0f}, c {fov[2]:.0f}~{fov[3]:.0f} px, H {H_px:.1f} px")
    report(rows, a.m, a.theta)
    print("읽는 법: D₀ > 0이면 무늬가 기포보다 느리다(λ > 0, 빠른 기포), D₀ < 0이면 빠르다(λ < 0). 묽은 극한 D₀ = αλR(I110). "
          "s는 m을 가정해 푼 이동도로 압력·유량계가 필요 없다. 무늬 속도 c는 ID가 필요 없지만 기준 V̄·V_ref는 추적으로 낸다"
          "(0.5% 치우침이 D 0.05의 10%). I91(국소장으로 나눈 s)·I99(|λ|_fwd)와 같은 크기 구분에서 맞춰 본다. "
          "--theta의 R·m은 두 평균장 정확식을 함께 푼 값(m 가정 없음)으로 I100 R_reg의 점검용이다.")


if __name__ == "__main__":
    main()

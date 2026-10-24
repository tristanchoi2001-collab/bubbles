"""추적 속도 요동으로 쌍극자 세기 Σα|λ|(아이디어 I99)와 마찰 지수 m(I100), 부호 있는 λ(d)와 국소장(I111)을 읽는다. 독립 검토 7·10 반영판.

배경
    기포 i의 속도는 V_i = s_i·(U_loc + u'_i)이고, u'_i는 이웃의 2차원 쌍극자 장 λ_jU·a_j²(cos 2θ, sin 2θ)/r²의 합이다.
    무작위 배치에서 그 합은 코시 분포이고 척도는 U·Σα_j|λ_j|이다(두 성분 같음). 이웃이 탐침에 겹치지 못하는 배제 영역 때문에
    중심부 폭이 g배로 준다. 묽은 극한에서 g = tan[(π/4)·e^(−Σα_j(1 + a_p/a_j)²)] ≈ 1 − 2πα(단분산)이고, 몬테카를로 맞춤
    1/(1 + 6.7α)와 맞는다(그림 r16). g는 α만이 아니라 탐침 크기(큰 탐침은 이웃이 덜 가까이 와서 훨씬 덜 봄)와 접촉 필터에 달린다.
    그래서 이 도구는 |λ|를 실제 배치로 환산한다(아래 7).
    마찰이 D ∝ V^m이면 흐름 방향 요동은 접선 이동도 2/(1 + mΔ), 가로 요동은 할선 이동도 2/(1 + Δ)로 응답한다(원형, 준정적).
    그래서 비 R = (흐름 방향 응답)/(가로 응답) = (1 + Δ)/(1 + mΔ), Δ = 2/s − 1이다. s = V̄/U_loc라 m에는 국소장이 필요하다.

쓰는 법
    python velocity_fluctuations.py --csv result_tracking.csv --px_mm 0.02 --fps 500 --H_mm 0.3 --flow up --out vf_out
        [--k 2] [--smooth 1] [--frame_area_px 452608] [--U_loc 0.05 --regress] [--walls 12,1060] [--dH_bins 2,5,15,50]
        [--noise_px 0.2] [--contact_gap 0.5] [--lam_nodes 2,3.5,6,10] [--r_offset_px 0.5] [--boot_block 200] [--jL 0.05 --jG 0.01]
    python velocity_fluctuations.py --demo --out vf_demo      # 쌍극자 상호작용을 넣은 합성 추적으로 스스로 점검(네 경우, 약 2~3분)

계산
    1. 트랙마다 중심 좌표(中心X/Y)의 중심 차분 속도 v(t) = (x(t + k) − x(t − k))/(2k)(px/frame). 창 안에 화면 끝 접촉,
       면적 변화 20% 초과(합체·분열), 빠진 프레임, 다른 기포와의 틈 < contact_gap × 작은 쪽 반경(접촉·윤활)이 있으면 버린다. CSV의 앞끝 EMA 속도는 요동을 깎으므로 쓰지 않는다.
       --smooth N이면 같은 트랙에서 N프레임 이동 평균을 두 방향에 똑같이 건다(철 바닥 홈 주기를 지우는 데 쓴다, I96).
    2. 흐름 방향(s)·가로(c) 성분으로 돌리고 d/H 구분으로 나눈다. 구분마다 V̄(흐름 방향 중앙값)로 나눈 상대 속도를 쓴다.
    3. 공통 요동(펌프 맥동 등), 폭(5~7)용: 프레임마다 모든 구분의 상대 편차 중앙값을 내고(관측 10개 이상인 프레임), 구분마다 그것에 대한
       회귀 기울기만큼 뺀다(두 쪽 모두 중심을 뺀 기울기). 앞 판은 프레임·구분 중앙값을 뺐는데, 그 구분이 프레임당 몇 개뿐이면 폭이 줄었다
       (n 3이면 0.58배, 검토 7 #7). 그다음 판은 중심을 빼지 않아 가로 표류가 있는 구분에서 기울기가 평균끼리의 곱으로 정해졌다(검토 10 #2).
       같은 구분 안의 크기 의존은 ln d에 대한 강건 회귀(Theil–Sen)로 뺀다.
       회귀(8·9)에는 이 단계를 쓰지 않는다: 고정효과((탐침 구분 × 프레임), (탐침 구분 × 위치 칸))의 평균을 속도와 장에서 똑같이 뺀다.
    4. 위치 잡음 σ_p = 1.4826·MAD(위치 2차 차분)/√6(흰 잡음 가정, 구분마다), 속도 잡음 σ_v = σ_p/(√2·k·√n)(smooth n ≤ 2k),
       σ_p/(√k·n)(n > 2k: 겹친 차분이 지워짐). 위치 잡음이 프레임 사이에 상관이 있으면(AR(1) 0.8) 2차 차분이 σ_p를 2.5배 작게
       내 γ가 23% 커진다 → 정지 기포나 표적으로 잰 값을 --noise_px로 준다.
    5. 반사분위폭(half-IQR)을 코시(γ) ⊗ 정규(σ_v)의 반사분위폭에 맞춰 γ를 푼다. 코시꼴(α ≲ 0.05)에서 잡음이 신호의 절반 이하면
       2~4% 안이다. α 0.3처럼 분포가 정규에 가까우면 같은 잡음에서 −15%라, 잡음/신호 > 0.5면 경고한다.
    6. 트랙 단위 부트스트랩(--n_boot)으로 γ와 R의 95% 구간. 같은 크기 기포는 배치가 거의 얼어 있어 이 구간은 배치 표본 오차를
       넣지 않는다(시드 사이 γ ±10%, R_reg ±0.2%). 운전점 안의 여러 영상으로 다시 뽑는 편이 낫다.
    7. 순방향 |λ| 환산(기본, 압력·국소장 불필요): 같은 관측·같은 창으로 λ = 1, U = 1의 쌍극자 장을 계산하고 그 가로 반사분위폭으로
       γ_c를 나눈다 → |λ|_fwd(이웃 |λ_j|의 가중 평균). 배제·탐침 크기·접촉 필터가 저절로 들어간다. 합성(참 0.603): 작은 0.59,
       큰 0.60~0.67. 옛 g 식 γ_c(1 + 6.7α)/α(--frame_area_px)는 작은 0.50~0.57, 큰 0.29~0.34로 큰 기포에서 절반쯤 틀린다.
       막 기억(아래)이 있으면 가로 응답이 빠른 요동에서 최대 약 0.78배라 |λ|_fwd도 그만큼 낮게 나올 수 있다.
    8. --regress(--U_loc 필요): 프레임마다 모든 기포의 쌍극자 장을 계산해(λ = 구분별 V̄/U_loc − 1, --walls면 측벽 거울상: 다른 기포는
       n = −4…4 대칭, 자기 거울상은 닫힌 식) 속도와 같은 창(사다리꼴 무게)으로 평균하고, 속도 잔차를 흐름 방향·가로로 따로 회귀한다.
       기울기가 접선·할선 이동도이고 비 R_reg는 배치 비등방과 무관하다. --walls면 자기 거울상을 뺀 회귀(R_reg_noself)도 낸다.
       합성 시험(331개 × 260프레임, 주기 경계를 넣은 접촉 필터): 작은 기포 R_reg 1.372(이론 1.381, −0.6%), m_reg 0.672(참 0.667),
       시드 다섯 개 1.369~1.375(검토 7). 앞 판의 "−6% → m +0.05"는 데모 접촉 필터가 주기 경계를 몰라 겹친 쌍을 넣은 버그였다.
       큰 기포는 트랙 30여 개라 구간만 본다(1.07~1.11, 이론 1.081). 큰 기포가 작은 기포를 따라잡아 닿는(밀어내는) 합성에서는
       큰 구분 R_reg가 0.91~0.95로 깎인다(작은 구분은 그대로) → 큰 기포의 m은 추월 접촉이 드문 운전에서 읽는다.
       막 기억: 뒤 메니스커스는 한 현 통과 시간 전에 깐 막을 걷는다. 막이 얼어 있는 극한에서 Δ 4.8의 두 기울기가 −21%·−22%지만
       R은 +1.8%(Δ 1에서 +3%)뿐이다(검토 7 #5) → R과 m은 튼튼하고, "가로 기울기 = s" 점검은 빠른 요동에서 20%까지 어긋날 수 있다.
       속도와 장 모두에서 (구분 안 프레임, 위치 칸) 고정효과를 똑같이 뺀다(검토 10 #2).
    9. I111(기본, --no_lamreg로 끔, 압력·국소장 불필요): 가로 속도를 자기 트랙 평균 속도로 나눈 yc = v_c/V̄_트랙을
       λ(d) = Σ_n β_n·h_n(ln d/H)(삼각 기저, 마디 --lam_nodes)인 원천의 단위 장 F_n에 회귀한다(모든 구분의 탐침을 한 회귀에).
       탐침 자신의 할선 이동도와 U가 지워진다. 국소장은 기포마다 U_i = V̄_i/(1 + λ(d_i))를 내 구분 안 중앙값을 쓴다.
       흐름 방향은 v_s/V_추세(d) − 1을 G = Σβ_n F_n,s에 회귀해 R_λ를 내고, m = ((1 + Δ)/R − 1)/Δ(Δ = 2/s − 1, s = 1 + λ).
       구분 지시 장 회귀(원천 구분마다 λ_k)는 점검용으로만 낸다: 교차 항 기울기는 λ_k·U_loc,k/U_loc,i이고 막 기억을 가장 크게 받는다.
       검토 10이 고친 것: 칸 빼기가 중앙값이라 기울기가 깎였다(합성 큰 구분 λ −10%, U_loc +4%), 공통 요동 회귀에 중심이 없어 철 영 시험에
       거짓 교차 항(−0.069)이 났다, 구분 중앙값 V̄로 나눠 구분 안 크기 퍼짐이 U_loc을 −8~−27% 치우쳤다.
       계통(출력과 함께 읽는다):
         - 회귀가 내는 것은 λ·(a_eff/a)²다(a = 검출 윤곽 반경). U_loc은 면적 규약 오차를 |1 − 1/s|배로 키운다
           (|δU/U| ≈ |1 − 1/s|·|δA/A|: s 0.35에서 1.9, 0.6에서 0.7, 1에서 0). --r_offset_px로 반경을 고쳐 다시 돌려 본다.
           s가 1에서 먼 구분, 링 경로(면적이 ×1.5~1.9 뛰는 작은 기포)가 섞인 구분의 U_loc은 정량으로 쓰지 않는다.
         - 막 기억(장이 현 통과 시간 2a/V 안에 바뀌는 원천: 속도가 다른 이웃)은 λ를 최대 약 20% 작게 낸다 → U_loc은 s 0.345에서
           −28%. 같은 속도 원천(좁은 크기 구간의 자기 항)에서 U_loc을 읽고, --k를 바꿔 λ의 주파수 의존을 같이 본다.
         - 구간은 트랙 단위로 다시 뽑아 배치 표본 오차를 덜 넣는다(시드 사이 산포가 1.5~2배). 기포가 시야를 지나가는 실제 영상은
           --boot_block(시야 통과 시간 이상의 프레임 블록)으로 다시 뽑는다. 여러 영상이면 영상 사이 산포를 본다.
         - 근접장: 장 크기 상위 1%는 뺀다(합성에서 영향 없음). 근접 짝 모형(Booth 외 2025)이 대안 커널이다.
         - 철 채널: 홈 고정이 방향마다 다르면 λ̂ × s_⊥/s가 되고, 관성 길이 ρUH²/(10μ)가 이웃 거리만 하면 Darcy 쌍극자 꼴이 보장되지 않는다
           → I88 조건부 평균으로 장의 꼴(앞뒤 대칭, 1/r²)을 먼저 확인한다(검토 10 #10).
       --jL·--jG(m/s)를 주면 I113의 탭 없는 압력 강하 E_U = (2U_loc − J)/j_L − 1을 구분마다 낸다(δE_U ≈ 2(δU_loc/U_loc)/(1 − α)).
출력: vf_classes.csv(구분별 표), vf_lamd.csv(I111 λ(d) 마디), 요약 출력.
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


def read_tracks(path, flow, px_mm, H_mm, r_offset=0.0):
    """r_offset(px)이면 면적을 반경이 그만큼 큰 원으로 고쳐 읽는다(윤곽 규약 보정: 검출 윤곽이 흰 테두리 바깥보다 0.5~1.3 px 안쪽)."""
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
        if r_offset:
            A = math.pi * max(math.sqrt(A / math.pi) + r_offset, 0.5) ** 2
        s_, c_ = (sgn * y, x) if ax == "Y" else (sgn * x, y)
        tracks[tid][int(r["フレーム"])] = (s_, c_, A, r.get("フレーム接触") == "1")
    return tracks


def near_contact(tracks, gap_frac, periodic=None):
    """(트랙, 프레임) 가운데 다른 기포와의 틈이 gap_frac × (작은 쪽 반경)보다 좁은 것. 접촉·윤활 변위는 쌍극자 장이 아니다.
    periodic = (L_s, L_c)면 최소 거울상 거리로 잰다(합성 시험의 주기 상자. 앞 판은 풀어 쓴 좌표의 단순 차라 상자 경계 너머
    겹친 쌍을 놓쳤고, 그것이 R_reg −6%의 원인이었다: 독립 검토 7 #1)."""
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
        dS = arr[:, None, 0] - arr[None, :, 0]
        dC = arr[:, None, 1] - arr[None, :, 1]
        if periodic:
            dS -= periodic[0] * np.round(dS / periodic[0]); dC -= periodic[1] * np.round(dC / periodic[1])
        gap = np.hypot(dS, dC) - (arr[:, None, 2] + arr[None, :, 2])
        np.fill_diagonal(gap, np.inf)
        bad = (gap < gap_frac * np.minimum(arr[:, None, 2], arr[None, :, 2])).any(1)
        near.update((x[0], f) for x, b in zip(lst, bad) if b)
    return near


def track_velocities(tracks, k, smooth, H_px, near=frozenset()):
    """(트랙, 프레임, v_s, v_c, d/H, s, c) 목록과 위치 2차 차분 표본. 창 안에 접촉 근처(near) 프레임이 있으면 버린다."""
    obs, dd = [], []
    for tid, fr in tracks.items():
        fs = sorted(fr)
        fset = set(fs)
        for f in fs:                                    # 위치 2차 차분(잡음 추정)
            if f - 1 in fset and f + 1 in fset and not (fr[f - 1][3] or fr[f][3] or fr[f + 1][3]):
                dd.append((fr[f + 1][0] - 2 * fr[f][0] + fr[f - 1][0], fr[f + 1][1] - 2 * fr[f][1] + fr[f - 1][1],
                           math.sqrt(4 * fr[f][2] / math.pi) / H_px))
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
            obs.append((tid, f, vs, vc, math.sqrt(4 * A / math.pi) / H_px, fr[f][0], fr[f][1]))
    return obs, np.array(dd) if dd else np.zeros((0, 3))


def dipole_fields(tracks, lam_of, H_px, U_px, walls=None, periodic=None, self_image=True, n_img=4):
    """프레임마다 모든 기포(화면 끝 포함)를 원천으로 2차원 쌍극자 장 D_j(cos 2θ, sin 2θ)/r²을 각 기포 중심에서 더한다.
    D_j = λ_j·U·a_j²(λ_j = lam_of(d/H)). lam_of가 배열(원천 무게 여러 개)을 돌려주면 쌍 기하를 한 번만 계산해 무게마다 장을 내고
    값은 배열 (2, 무게 수)다(I111 기저). walls = (c_lo, c_hi)면 측벽 거울상(불투과 벽: 같은 부호·같은 방향, 2W 주기)을 넣는다.
      - 다른 기포의 거울상은 두 가족 {c + 2nW}, {2c_lo − c + 2nW}를 n = −n_img…n_img로 대칭으로 자른다.
      - 자기 거울상은 닫힌 식으로 더한다: u_s = −D(π/2W)²[1/sin²(πy₀/W) + 1/3](y₀ = c − c_lo), u_c = 0(I101).
        앞 판은 n = −2…2로 한쪽에만 5W 항이 있어 채널 가운데서 약 12% 모자랐다(독립 검토 7 #12).
      - self_image=False면 자기 거울상을 뺀다. 자기 거울상은 가로 위치만의 함수라 국소장의 가로 분포와 섞이므로 회귀를 둘 다 낸다.
    periodic = (L_s, L_c)는 합성 시험용(최소 거울상, 반경 L_c/2에서 자름). 반환 {(트랙, 프레임): (u_s, u_c)}(px/frame)."""
    per_frame = defaultdict(list)
    for tid, fr in tracks.items():
        for f, (s_, c_, A, _) in fr.items():
            per_frame[f].append((tid, s_, c_, math.sqrt(A / math.pi)))
    out = {}
    for f, lst in per_frame.items():
        S = np.array([x[1] for x in lst]); C = np.array([x[2] for x in lst]); a = np.array([x[3] for x in lst])
        L = np.array([lam_of(2 * r / H_px) for r in a], float)
        D = L * (U_px * a * a if L.ndim == 1 else (U_px * a * a)[:, None])
        n0 = len(S)
        if periodic:
            S, C = S % periodic[0], C % periodic[1]
        SS, CC, DD, OWN = [S], [C], [D], [np.arange(n0)]
        if walls and not periodic:
            lo, hi = walls
            W = hi - lo
            for n in range(-n_img, n_img + 1):
                if n:
                    SS.append(S); CC.append(C + 2 * n * W); DD.append(D); OWN.append(np.arange(n0))
                SS.append(S); CC.append(2 * lo - C + 2 * n * W); DD.append(D); OWN.append(np.arange(n0))
        SS, CC, DD, OWN = np.concatenate(SS), np.concatenate(CC), np.concatenate(DD), np.concatenate(OWN)
        ds = S[:, None] - SS[None, :]
        dc = C[:, None] - CC[None, :]
        if periodic:
            ds -= periodic[0] * np.round(ds / periodic[0]); dc -= periodic[1] * np.round(dc / periodic[1])
        r2 = ds * ds + dc * dc
        r2[OWN[None, :] == np.arange(n0)[:, None]] = np.inf      # 자기 자신과 자기 거울상은 여기서 빼고 아래 닫힌 식으로
        if periodic:
            r2[r2 > (0.5 * min(periodic)) ** 2] = np.inf
        r4 = r2 * r2
        us = ((ds * ds - dc * dc) / r4) @ DD
        uc = (2 * ds * dc / r4) @ DD
        if walls and not periodic and self_image:
            y0 = np.clip(C - lo, 1e-6 * W, W * (1 - 1e-6))
            fac = (math.pi / (2 * W)) ** 2 * (1 / np.sin(math.pi * y0 / W) ** 2 + 1 / 3)
            us = us - (D * fac if D.ndim == 1 else D * fac[:, None])
        for i, (tid, *_) in enumerate(lst):
            out[(tid, f)] = (float(us[i]), float(uc[i])) if D.ndim == 1 else np.stack([us[i], uc[i]])
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


def window_fields(fields, obs, k, smooth, scheme="trapezoid"):
    """속도와 같은 창(중심 차분 2k + 이동 평균 smooth)으로 장을 평균한다. 창 길이가 다르면 빠르게 변하는 성분의 기울기가 깎인다.
    v(h)는 h − k … h + k의 이동을 담는다. scheme="trapezoid"(실제 궤적: 한 칸의 이동은 두 끝 프레임 장의 평균이 민다)는 양 끝
    무게 1/2, "euler"(합성 데모의 전진 오일러: g → g + 1 이동은 g의 장이 민다)는 h − k … h + k − 1을 같은 무게로 둔다."""
    out = {}
    n = max(smooth, 1)
    for o in obs:
        w = defaultdict(float)
        for h in range(o[1] - n // 2, o[1] - n // 2 + n):
            if scheme == "euler":
                for g in range(h - k, h + k):
                    w[g] += 1.0
            else:
                for g in range(h - k, h + k + 1):
                    w[g] += 0.5 if g in (h - k, h + k) else 1.0
        vals = [(fields.get((o[0], g)), wt) for g, wt in w.items()]
        vals = [(v, wt) for v, wt in vals if v is not None]
        if vals:
            sw = sum(wt for _, wt in vals)
            out[(o[0], o[1])] = (sum(v[0] * wt for v, wt in vals) / sw, sum(v[1] * wt for v, wt in vals) / sw)
    return out


def theil_sen(x, y, max_n=1500, seed=0):
    """두꺼운 꼬리에 강한 기울기(쌍 기울기의 중앙값). 표본이 많으면 max_n개를 뽑아 쓴다(검토 7 #12(가))."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) > max_n:
        ii = np.random.default_rng(seed).choice(len(x), max_n, replace=False)
        x, y = x[ii], y[ii]
    dx = x[:, None] - x[None, :]
    dy = y[:, None] - y[None, :]
    m = np.abs(dx) > 1e-12
    return float(np.median(dy[m] / dx[m])) if m.any() else 0.0


def _sigma_v(sig_p, k, smooth):
    """위치 잡음 σ_p가 속도 잡음이 되는 값. smooth n ≤ 2k면 σ_p/(√2·k·√n), n > 2k면 겹친 차분이 지워져 σ_p/(√k·n)(검토 7 #8)."""
    n = max(smooth, 1)
    return sig_p / (math.sqrt(2) * k * math.sqrt(n)) if n <= 2 * k else sig_p / (math.sqrt(k) * n)


def _mad_sigma(v):
    return float(1.4826 * np.median(np.abs(v - np.median(v))))


def cell_ids(s, c, n_s, n_c, periodic=None):
    """흐름 방향 s·가로 c 분위 칸 번호. periodic = (L_s, L_c)면 감은 좌표로 나눈다(합성 주기 상자)."""
    if periodic:
        s, c = np.mod(s, periodic[0]), np.mod(c, periodic[1])
    es = np.quantile(s, np.linspace(0, 1, n_s + 1)); ec = np.quantile(c, np.linspace(0, 1, n_c + 1))
    i = np.clip(np.searchsorted(es, s, "right") - 1, 0, n_s - 1); j = np.clip(np.searchsorted(ec, c, "right") - 1, 0, n_c - 1)
    return i * n_c + j


def detrend_cells(v, cid, ok=None, min_n=20):
    """폭(I99)용: 칸마다 시간 중앙값을 뺀다. 위치마다 다른 정상 표류(측벽 거울상의 평균장, 덮개 처짐·기울임의 I105 표류)는 쌍극자 요동이
    아니다. 관측이 min_n보다 적은 칸은 그대로 둔다. 회귀에는 쓰지 않는다(demean_fe: 중앙값을 속도와 장에서 따로 빼면 고정효과 투영이
    아니라 기울기가 깎인다, 검토 10 #1)."""
    out = v.copy()
    for q in np.unique(cid):
        m = cid == q
        mm = m & ok if ok is not None else m
        if mm.sum() >= min_n:
            out[m] -= np.median(v[mm])
    return out


def demean_fe(V, groups, ok=None, n_iter=200, tol=1e-9):
    """고정효과 빼기(검토 10 #1·#2): groups(정수 배열 목록)마다 묶음 평균을 번갈아 뺀다(두 갈래 이상이면 교대 투영으로 수렴할 때까지).
    평균은 ok 행으로만 내고 모든 행에서 뺀다. 속도와 장의 열을 한 번에 넣어 똑같이 빼야 기울기가 고정효과 회귀(Frisch–Waugh)와 같다."""
    V = np.array(V, float)
    one = V.ndim == 1
    if one:
        V = V[:, None]
    w = np.ones(len(V)) if ok is None else np.asarray(ok, float)
    codes = [np.unique(np.asarray(g), return_inverse=True)[1].ravel() for g in groups]
    scale = float(np.abs(V[w > 0]).max()) if (w > 0).any() and V.size else 0.0
    for _ in range(n_iter if len(codes) > 1 else 1):
        step = 0.0
        for c in codes:
            n = np.bincount(c, weights=w)
            Vw = np.where(w[:, None] > 0, V, 0.0) * w[:, None]
            mu = np.stack([np.bincount(c, weights=Vw[:, q], minlength=len(n)) for q in range(V.shape[1])], 1)
            mu = np.divide(mu, n[:, None], out=np.zeros_like(mu), where=n[:, None] > 0)
            V -= mu[c]
            step = max(step, float(np.abs(mu).max()) if mu.size else 0.0)
        if step <= tol * (scale + 1e-30):
            break
    return V[:, 0] if one else V


def _size_trend(tid, dh, v, seed=0):
    """구분 안 크기 추세 V(d)(행마다): 트랙 평균 속도의 ln V를 트랙 평균 ln d에 Theil–Sen으로 맞춘다."""
    _, inv = np.unique(tid, return_inverse=True)
    inv = inv.ravel()
    n = np.bincount(inv)
    lv = np.log(np.maximum(np.bincount(inv, weights=v) / n, 1e-12))
    ld = np.bincount(inv, weights=np.log(dh)) / n
    b = theil_sen(ld, lv, seed=seed) if np.ptp(ld) > 1e-9 else 0.0
    return np.exp(np.median(lv - b * ld) + b * np.log(dh))


def hat_weights(nodes):
    """ln(d/H)의 삼각(모자) 기저 무게: 마디 nodes(d/H)에서 1, 이웃 마디에서 0. 양 끝 밖은 끝 마디 값으로 평평하게 잇는다."""
    ln = np.log(np.asarray(nodes, float))

    def w(dh):
        x = math.log(max(dh, 1e-9))
        out = np.zeros(len(ln))
        if x <= ln[0]:
            out[0] = 1.0
        elif x >= ln[-1]:
            out[-1] = 1.0
        else:
            q = int(np.searchsorted(ln, x)) - 1
            t = (x - ln[q]) / (ln[q + 1] - ln[q])
            out[q], out[q + 1] = 1 - t, t
        return out
    return w


def auto_nodes(tracks, bins, H_px):
    """λ(d) 마디: 모든 검출 d/H의 2~98% 백분위 사이에 구분 수 + 1개를 기하 간격으로 둔다(범위가 좁으면 하나)."""
    dh = np.array([2 * math.sqrt(A / math.pi) / H_px for fr in tracks.values() for (_, _, A, _) in fr.values()])
    if not len(dh):
        return [1.0]
    lo, hi = (float(v) for v in np.percentile(dh, [2, 98]))
    return [lo] if hi <= 1.05 * lo else [float(v) for v in np.geomspace(lo, hi, len(bins) + 1)]


def lam_basis_fields(tracks, bins, nodes, H_px, obs, k, smooth, walls=None, periodic=None, scheme="trapezoid"):
    """I111 설명 변수를 한 번에 계산한다(쌍 기하 한 번): 열 = [구분 지시 장 K개(원천 구분 k만 λ = 1), ln(d/H) 삼각 기저 장 N개], U = 1,
    속도와 같은 창으로 평균. 반환 {(트랙, 프레임): (F_s 배열, F_c 배열)}."""
    hat = hat_weights(nodes)

    def w(dh):
        return np.concatenate([[1.0 if lo <= dh < hi else 0.0 for lo, hi in bins], hat(dh)])
    return window_fields(dipole_fields(tracks, w, H_px, 1.0, walls=walls, periodic=periodic), obs, k, smooth, scheme=scheme)


def lamreg_fit(obs, bins, basis, nodes, detrend=(4, 8), periodic=None, n_boot=200, seed=0, boot_block=0, near_pct=99.0,
               min_class_obs=30, r_gate=0.25):
    """I111 고친 판(검토 10 #1~#3·#7·#9·#19): U_loc 없이 부호 있는 λ(d), 구분별 국소장, R_λ, m을 낸다.
      - 탐침: yc = v_c/V̄_트랙(자기 트랙 평균 속도로 나눔)이라 탐침 자신의 할선 이동도와 U가 지워진다. 구분 중앙값으로 나누면
        구분 안 크기 퍼짐이 U_loc을 −8~−27% 치우친다(#3).
      - 원천: λ(d) = Σβ_n h_n(ln d/H)(모든 구분의 탐침을 한 회귀에). 구분 지시 장 회귀(탐침 구분마다 λ_k)는 점검용이다(#9).
      - 고정효과: (탐침 구분 × 프레임), (탐침 구분 × 위치 칸)의 평균을 속도와 모든 장에서 똑같이 뺀다(#1·#2).
      - U_loc: 트랙마다 V̄_트랙/(1 + λ(d))의 구분 안 중앙값. λ_자기도 구분 안 트랙의 λ(d) 중앙값.
      - R_λ: ys = v_s/V_추세(d) − 1을 G = Σβ_n F_n,s에 회귀. R 구간 폭이 r_gate·R보다 넓으면 m을 내지 않는다(#19).
      - 구간: 트랙 단위(기본) 또는 boot_block 프레임 블록 단위로 다시 뽑는다(고정효과를 뺀 자료로). 같은 영상 안이라 배치 표본 오차가
        덜 들어간다(#7).
    반환: ({구분 번호: 결과}, 마디 표 [(d/H, λ, 아래, 위)])."""
    rng = np.random.default_rng(seed)
    nc = len(bins)
    dh_o = np.array([o[4] for o in obs])
    cls = np.full(len(obs), -1)
    for j, (lo, hi) in enumerate(bins):
        cls[(dh_o >= lo) & (dh_o < hi) & (cls < 0)] = j
    cnt = np.bincount(cls[cls >= 0], minlength=nc) if (cls >= 0).any() else np.zeros(nc, int)
    vt, dt = defaultdict(list), defaultdict(list)
    for o in obs:
        vt[o[0]].append(o[2]); dt[o[0]].append(o[4])
    vtm = {t: float(np.mean(v)) for t, v in vt.items()}
    dtm = {t: float(np.median(v)) for t, v in dt.items()}
    rows = [i for i, o in enumerate(obs) if cls[i] >= 0 and cnt[cls[i]] >= min_class_obs and (o[0], o[1]) in basis and vtm[o[0]] > 0]
    if len(rows) < 30:
        return {}, []
    sel = [obs[i] for i in rows]
    cj = cls[rows]
    tid = np.array([o[0] for o in sel]); fr = np.array([o[1] for o in sel], np.int64)
    vs = np.array([o[2] for o in sel]); vc = np.array([o[3] for o in sel]); dh = np.array([o[4] for o in sel])
    FS = np.array([np.asarray(basis[(o[0], o[1])][0], float) for o in sel])
    FC = np.array([np.asarray(basis[(o[0], o[1])][1], float) for o in sel])
    nb = FS.shape[1]
    hcols = np.arange(nc, nb)
    ok = np.isfinite(FS).all(1) & np.isfinite(FC).all(1)
    tot = np.abs(np.nan_to_num(FC[:, hcols])).sum(1)
    for j in np.unique(cj):                              # 장 크기 상위 1%(가장 가까운 이웃, 근접장)는 뺀다
        m = ok & (cj == j)
        if near_pct < 100 and m.sum() > 30:
            ok &= ~(m & (tot > np.percentile(tot[m], near_pct)))
    yc = vc / np.array([vtm[t] for t in tid])
    vfit = np.ones(len(sel))
    for j in np.unique(cj):
        m = cj == j
        vfit[m] = _size_trend(tid[m], dh[m], vs[m], seed)
    ys = vs / vfit - 1
    groups = [fr * nc + cj]
    if detrend:
        cid = np.zeros(len(sel), np.int64)
        s_, c_ = np.array([o[5] for o in sel]), np.array([o[6] for o in sel])
        for j in np.unique(cj):
            m = cj == j
            cid[m] = cell_ids(s_[m], c_[m], detrend[0], detrend[1], periodic)
        groups.append(cid * nc + cj)
    Z = demean_fe(np.column_stack([ys, yc, FS, FC]), groups, ok)
    ys, yc, FS, FC = Z[:, 0], Z[:, 1], Z[:, 2:2 + nb], Z[:, 2 + nb:]
    okr = np.where(ok)[0]
    act = hcols[np.abs(FC[okr][:, hcols]).sum(0) > 1e-12]
    if not len(act):
        return {}, []
    hatw = hat_weights(nodes)
    tr_rows = defaultdict(list)
    for i in okr:
        tr_rows[tid[i]].append(i)
    t_cls = {t: int(np.bincount(cj[r]).argmax()) for t, r in tr_rows.items()}
    t_h = {t: hatw(dtm[t]) for t in tr_rows}

    lnn = np.log(np.asarray(nodes, float))
    on = act - nc

    def dstar(bf, tracks_used):
        """d*: λ(d) = 0인 크기(활성 마디 사이 ln d 선형 보간, 가장 작은 영점). 그 크기 기포는 s = 1이라 속도가 곧 국소장이고,
        윤곽 규약·막 기억처럼 λ에 곱해지는 오차가 영점을 옮기지 않는다(I84·I104). 영점 ±15% 안 트랙이 5개 이상일 때만 U*를 낸다."""
        lam_n = bf[on]
        for q in range(len(on) - 1):
            if lam_n[q] == 0 or lam_n[q] * lam_n[q + 1] < 0:
                x0, x1 = lnn[on[q]], lnn[on[q + 1]]
                xs = x0 + (x1 - x0) * lam_n[q] / (lam_n[q] - lam_n[q + 1])
                near = [vtm[t] / (1 + float(t_h[t] @ bf)) for t in tracks_used if abs(math.log(dtm[t]) - xs) < math.log(1.15)]
                return math.exp(xs), (float(np.median(near)) if len(near) >= 5 else float("nan")), len(near)
        return float("nan"), float("nan"), 0

    def fit(ii, tracks_used):
        beta, *_ = np.linalg.lstsq(FC[ii][:, act], yc[ii], rcond=None)
        bf = np.zeros(nb - nc)
        bf[act - nc] = beta
        G = FS[:, hcols] @ bf
        res = {"beta": bf}
        res["dstar"], res["U_dstar"], res["n_dstar"] = dstar(bf, tracks_used)
        ul = defaultdict(list)
        for t in tracks_used:
            lam_t = float(t_h[t] @ bf)
            if 1 + lam_t > 0.05:
                ul[t_cls[t]].append((vtm[t] / (1 + lam_t), lam_t))
        for j in range(nc):
            if len(ul[j]) >= 3:
                arr = np.array(ul[j])
                res[("U", j)], res[("lam", j)] = float(np.median(arr[:, 0])), float(np.median(arr[:, 1]))
            mj = ii[cj[ii] == j]
            if len(mj) > 10:
                gg = float(G[mj] @ G[mj])
                res[("R", j)] = float(G[mj] @ ys[mj]) / gg if gg > 0 else float("nan")
                ia = np.arange(nc)[np.abs(FC[mj][:, :nc]).sum(0) > 1e-12]
                if len(ia):
                    lk, *_ = np.linalg.lstsq(FC[mj][:, ia], yc[mj], rcond=None)
                    for q, kk in enumerate(ia):
                        res[("cross", j, int(kk))] = float(lk[q])
        return res
    base = fit(okr, list(tr_rows))
    clu = fr // boot_block if boot_block and boot_block > 0 else tid
    cl_rows = defaultdict(list)
    for i in okr:
        cl_rows[clu[i]].append(i)
    cl_keys = list(cl_rows)
    cl_tr = {c: list(dict.fromkeys(tid[r])) for c, r in cl_rows.items()}
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(len(cl_keys), size=len(cl_keys))
        ii = np.concatenate([cl_rows[cl_keys[p]] for p in pick])
        if len(ii) > 30:
            boots.append(fit(ii, [t for p in pick for t in cl_tr[cl_keys[p]]]))

    def ci(key):
        v = [b[key] for b in boots if key in b and b[key] == b[key]]
        return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) > 10 else (float("nan"),) * 2
    out = {}
    for j in range(nc):
        if ("U", j) not in base:
            continue
        r = {"lam_reg_self": base[("lam", j)], "s_lamreg": 1 + base[("lam", j)], "U_loc_lamreg": base[("U", j)],
             "lamreg_tracks": sum(1 for t in tr_rows if t_cls[t] == j),
             "dH_med_tracks": float(np.median([dtm[t] for t in tr_rows if t_cls[t] == j]))}
        r["lam_reg_self_lo"], r["lam_reg_self_hi"] = ci(("lam", j))
        r["U_loc_lamreg_lo"], r["U_loc_lamreg_hi"] = ci(("U", j))
        r["U_area_sens"] = abs(1 - 1 / r["s_lamreg"]) if r["s_lamreg"] > 0 else float("nan")   # |δU/U| ÷ |δA/A|(검토 10 #4)
        for kk in range(nc):
            if ("cross", j, kk) in base:
                lo_k, hi_k = bins[kk]
                key = f"lam_reg_src_{lo_k:g}_{hi_k:g}"
                r[key] = base[("cross", j, kk)]
                r[key + "_lo"], r[key + "_hi"] = ci(("cross", j, kk))
        Rr = base.get(("R", j), float("nan"))
        r["R_lamreg"] = Rr
        r["R_lamreg_lo"], r["R_lamreg_hi"] = ci(("R", j))
        s_self = r["s_lamreg"]
        Dl = 2 / s_self - 1 if s_self > 0 else float("nan")
        wide = not (r["R_lamreg_hi"] - r["R_lamreg_lo"] <= r_gate * abs(Rr)) if Rr == Rr else True
        r["R_lamreg_wide"] = wide
        if not wide and Dl == Dl and abs(Dl) > 1e-6:
            mf = lambda R: ((1 + Dl) / R - 1) / Dl if R == R and R > 0 else float("nan")
            r["m_lamreg"], r["m_lamreg_lo"], r["m_lamreg_hi"] = mf(Rr), mf(r["R_lamreg_hi"]), mf(r["R_lamreg_lo"])
        if base["dstar"] == base["dstar"] and bins[j][0] <= base["dstar"] < bins[j][1]:   # d*가 이 구분 안이면 붙인다
            r["dstar"], r["U_loc_dstar"], r["n_dstar"] = base["dstar"], base["U_dstar"], base["n_dstar"]
            r["dstar_lo"], r["dstar_hi"] = ci("dstar")
            r["U_loc_dstar_lo"], r["U_loc_dstar_hi"] = ci("U_dstar")
        out[j] = r
    tab = []
    for n, dn in enumerate(nodes):
        key_n = [b["beta"][n] for b in boots]
        lo_n, hi_n = (float(np.percentile(key_n, 2.5)), float(np.percentile(key_n, 97.5))) if len(key_n) > 10 else (float("nan"),) * 2
        tab.append((float(dn), float(base["beta"][n]) if (nc + n) in act else float("nan"), lo_n, hi_n))
    return out, tab


def analyse(obs, dd, k, smooth, bins, frame_alpha=None, U_loc_px=None, n_boot=200, seed=0, fields=None,
            unit_fields=None, fields_noself=None, noise_px=None, min_frame_obs=10, detrend=(4, 8), periodic=None,
            basis=None, nodes=None, boot_block=0):
    """구분별 요동 폭·응답 비·회귀 기울기. 폭의 공통 요동은 그 프레임의 모든 기포(모든 구분)에서 구한 상대 편차에 대한 회귀(중심을 뺀
    기울기)로 뺀다(앞 판의 프레임·구분 중앙값 빼기는 그 구분의 관측이 적은 프레임에서 폭을 줄였다: n 3이면 0.58배, 검토 7 #7).
    unit_fields(λ = 1, U = 1로 계산한 장)가 있으면 같은 관측·같은 창에서 그 장의 가로 폭으로 나눈 |λ|_fwd를 낸다(실제 배치·
    접촉 필터·탐침 크기를 모두 반영하는 순방향 환산, 검토 7 #2). fields_noself는 측벽 자기 거울상을 뺀 장(회귀를 하나 더 낸다).
    detrend = (n_s, n_c)면 구분마다 (s, c) 분위 칸을 쓴다: 폭은 칸 중앙값을 빼고, 회귀는 칸 고정효과를 속도와 장에서 똑같이 뺀다
    (위치마다 다른 정상 표류는 쌍극자 요동이 아니다). None이면 끈다.
    basis(lam_basis_fields)와 nodes가 있으면 I111(lamreg_fit)을 돌려 구분 표에 붙인다. 위치 잡음은 회귀 기울기를 치우치게 하지
    않는다(폭 방식의 잡음 바닥이 없다: 끝까지 시험의 상호작용 없는 자료에서 폭 방식 |λ|_fwd는 0.05·0.19였다. 부화소 위상이 천천히
    도는 중심 오차는 2차 차분 잡음 추정에 안 잡혀 디컨볼루션으로 빠지지 않는다). 반환 (구분 표, σ_p, I111 마디 표)."""
    if len(dd) > 20:
        sig_p_all = float(np.mean([_mad_sigma(dd[:, j]) for j in (0, 1)]) / math.sqrt(6))
    else:
        sig_p_all = float("nan")
    if noise_px is not None and noise_px == noise_px:
        sig_p_all = noise_px
    rng = np.random.default_rng(seed)
    out = []
    # 구분별 V̄와 프레임 공통 요동(모든 구분)
    cls_of = {}
    vbar = {}
    for j, (lo, hi) in enumerate(bins):
        v = [o[2] for o in obs if lo <= o[4] < hi]
        if len(v) >= 10 and np.median(v) > 0:
            vbar[j] = float(np.median(v))
    for o in obs:
        for j, (lo, hi) in enumerate(bins):
            if lo <= o[4] < hi and j in vbar:
                cls_of[(o[0], o[1])] = j
                break
    by_frame = defaultdict(list)
    for o in obs:
        j = cls_of.get((o[0], o[1]))
        if j is not None:
            by_frame[o[1]].append((o[2] / vbar[j] - 1, o[3] / vbar[j]))
    cm = {f: (float(np.median([x[0] for x in v])), float(np.median([x[1] for x in v])))
          for f, v in by_frame.items() if len(v) >= min_frame_obs}
    n_frame_med = float(np.median([len(v) for v in by_frame.values()])) if by_frame else float("nan")

    def frame_cm_fields(fl):
        if fl is None:
            return None
        acc = defaultdict(list)
        for o in obs:
            v = fl.get((o[0], o[1]))
            if v is not None and (o[0], o[1]) in cls_of:
                acc[o[1]].append(v)
        return {f: (float(np.median([x[0] for x in v])), float(np.median([x[1] for x in v])))
                for f, v in acc.items() if len(v) >= min_frame_obs}
    ucm = frame_cm_fields(unit_fields)
    lr, lam_tab = (lamreg_fit(obs, bins, basis, nodes, detrend=detrend, periodic=periodic, n_boot=n_boot, seed=seed,
                              boot_block=boot_block) if basis is not None else ({}, []))
    for j, (lo, hi) in enumerate(bins):
        sel = [o for o in obs if lo <= o[4] < hi]
        if len(sel) < 30 or j not in vbar:
            continue
        Vbar = vbar[j]
        tid = np.array([o[0] for o in sel]); fr = np.array([o[1] for o in sel])
        vs = np.array([o[2] for o in sel]); vc = np.array([o[3] for o in sel]); dh = np.array([o[4] for o in sel])
        # 구분별 위치 잡음(표본이 20개 이상이면), 아니면 전체 값
        if noise_px is None and len(dd) and dd.shape[1] >= 3:
            dsel = dd[(dd[:, 2] >= lo) & (dd[:, 2] < hi)]
            sig_p = float(np.mean([_mad_sigma(dsel[:, q]) for q in (0, 1)]) / math.sqrt(6)) if len(dsel) >= 20 else sig_p_all
        else:
            sig_p = sig_p_all
        ys = vs / Vbar - 1
        yc = vc / Vbar
        xs = np.array([cm.get(f, (0.0, 0.0))[0] for f in fr]); xc = np.array([cm.get(f, (0.0, 0.0))[1] for f in fr])
        for y, x in ((ys, xs), (yc, xc)):                # 공통 요동: 프레임 상대 편차에 대한 (중심을 뺀) 회귀 기울기만큼 뺀다
            xm = x - x.mean()
            if (xm @ xm) > 0:
                y -= (xm @ (y - y.mean())) / (xm @ xm) * xm
        cid = None
        if detrend and len(sel[0]) >= 7:                 # 위치별 정상 표류 빼기
            cid = cell_ids(np.array([o[5] for o in sel]), np.array([o[6] for o in sel]), detrend[0], detrend[1], periodic)
            ys = detrend_cells(ys, cid); yc = detrend_cells(yc, cid)
        yc -= np.median(yc)
        lx = np.log(dh)                                  # 구분 안 크기 의존(흐름 방향) 빼기: 강건 회귀
        if lx.std() > 1e-9:
            ys -= theil_sen(lx, ys, seed=seed) * (lx - lx.mean())
        ys -= np.median(ys)
        us, uc = ys, yc
        sv = _sigma_v(sig_p, k, smooth) / Vbar
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
        nper = np.bincount(np.unique(fr, return_inverse=True)[1])
        rec = dict(dH_lo=lo, dH_hi=hi, n_obs=len(sel), n_tracks=len(tids), n_per_frame_class=float(np.median(nper)),
                   n_per_frame_all=n_frame_med, V_px_per_frame=Vbar, sigma_p=sig_p, noise_rel=sv,
                   hiqr_s=hs, hiqr_c=hc, gamma_s=gs, gamma_c=gc, R=gs / gc if gc > 0 else float("nan"))
        rec["noise_over_signal"] = sv / hc if hc > 0 else float("nan")
        rec["gamma_s_lo"], rec["gamma_s_hi"] = ci(bs)
        rec["gamma_c_lo"], rec["gamma_c_hi"] = ci(bc)
        rec["R_lo"], rec["R_hi"] = ci(br)

        def field_xy(fl, fcmap):
            fu = np.array([fl.get((o[0], o[1]), (np.nan, np.nan)) for o in sel])
            ok = np.isfinite(fu).all(1)
            fx_, fy_ = fu[:, 0].copy(), fu[:, 1].copy()
            if fcmap:
                fx_ -= np.array([fcmap.get(f, (0.0, 0.0))[0] for f in fr]); fy_ -= np.array([fcmap.get(f, (0.0, 0.0))[1] for f in fr])
            if cid is not None:                          # 관측 속도와 같은 칸 빼기
                fx_ = detrend_cells(np.nan_to_num(fx_), cid, ok); fy_ = detrend_cells(np.nan_to_num(fy_), cid, ok)
            return fx_, fy_, ok
        if unit_fields is not None:                      # 순방향 |λ| 환산: 같은 관측·같은 창의 λ = 1 장 가로 폭
            ux_, uy_, ok_u = field_xy(unit_fields, ucm)
            if ok_u.sum() > 30:
                wu = hiqr(uy_[ok_u] - np.median(uy_[ok_u]))
                rec["unit_field_hiqr_c"] = wu
                rec["abs_lambda_fwd"] = gc / wu if wu > 0 else float("nan")
        rec.update(lr.get(j, {}))                       # I111(lamreg_fit): 부호 있는 λ(d), U_loc, R_λ, m
        if fields is not None:                          # 회귀형(I100 보강): 계산한 쌍극자 장에 대한 기울기 = 접선·할선 이동도
            vfit = _size_trend(tid, dh, vs, seed)       # 흐름 방향은 구분 안 크기 추세를 뺀 절대 편차(px/frame)
            grp = [fr] + ([cid] if cid is not None else [])

            def fe_pair(xv, yv, base_ok):               # 근접장 1% 자름 뒤 고정효과(프레임·칸)를 속도와 장에서 똑같이 뺀다(검토 10 #2)
                okq = base_ok & (np.abs(np.nan_to_num(xv)) <= np.percentile(np.abs(xv[base_ok]), 99))
                Z = demean_fe(np.column_stack([yv, xv]), grp, okq)
                return Z[:, 1], Z[:, 0], okq

            def slope(p, idx):
                xv, yv, okq = p
                idx = idx[okq[idx]]
                xx = float(xv[idx] @ xv[idx])
                return float(xv[idx] @ yv[idx]) / xx if xx > 0 else float("nan")
            for tag, fl in (("", fields), ("_noself", fields_noself)):
                if fl is None:
                    continue
                fu = np.array([fl.get((o[0], o[1]), (np.nan, np.nan)) for o in sel], float)
                ok = np.isfinite(fu).all(1)
                if ok.sum() <= 30:
                    continue
                ps, pc = fe_pair(fu[:, 0], vs - vfit, ok), fe_pair(fu[:, 1], vc, ok)
                allr = np.arange(len(sel))
                b1, b2 = slope(ps, allr), slope(pc, allr)
                rec["b_s" + tag], rec["b_c" + tag], rec["R_reg" + tag] = b1, b2, b1 / b2 if b2 else float("nan")
                if tag:
                    continue
                rr = []
                for _ in range(n_boot):
                    pick = rng.choice(tids, size=len(tids))
                    ii = np.concatenate([idx_of[t] for t in pick])
                    q2 = slope(pc, ii)
                    if q2:
                        rr.append(slope(ps, ii) / q2)
                rec["R_reg_lo"], rec["R_reg_hi"] = ci([r for r in rr if r == r])
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
    return out, sig_p_all, lam_tab


def _s_booth_demo(dH, U=0.05, mu=1e-3, sig=0.072):
    """다분산 합성의 s(d/H): 0.3 mm·물에서 s^(2/3)/(2 − s) = 1.12(d/H)Ca_U^(1/3)(f = 1)을 고정점 반복으로 푼다."""
    s = 1.0
    for _ in range(200):
        s = 0.5 * s + 0.5 * 2 / (1 + 1 / (1.12 * dH * (mu * s * U / sig) ** (1 / 3)))
    return s


def make_demo(out, seed=3, push=False, drift=(0.0, 0.0), poly=False, r_shift=0.0, name="demo_tracking.csv"):
    """쌍극자 상호작용을 넣은 합성 추적(주기 상자, 두 크기). 정답(잡음 없는 위치)도 함께 돌려준다.
    작은 기포 a 8 px·Δ0 4.8(s 0.345), 큰 기포 a 24 px·Δ0 0.29(s 1.55), 각 α 0.03, m = 2/3, U = 6 px/frame,
    위치 잡음 0.15 px. 기포 속도는 벡터 힘 균형 2(U + u') = V(1 + Δ0(|V|/V0)^(m − 1))로 푼다.
    push=True면 겹친 쌍을 중심선 방향으로 밀어낸다(접촉 변위). 앞 판은 이 경로가 변수 덮어쓰기로 멈췄고 "가로 기울기 +18%"는
    재현되지 않았다(검토 7 #10). 기본(push=False)은 겹침을 허용하고 접촉 필터(주기 경계)가 그 창을 뺀다.
    검토 10 #8의 경우: drift = (작은, 큰) 구분의 일정한 가로 표류(px/frame, 기울임·측벽 표류), poly면 구분 d/H 2~5·5~14에서 d를
    고르게 뽑고 s(d/H)를 _s_booth_demo로 준다(구분 안 크기 퍼짐), r_shift면 CSV에 반경을 그만큼 작게 적는다(윤곽이 안쪽)."""
    rng = np.random.default_rng(seed)
    Lx, Ly, U, m, noise = 2000.0, 1000.0, 6.0, 2 / 3, 0.15
    H_px = 16.0 / 3
    P, a, D0, big = [], [], [], []

    def free(p, rad):
        if not P:
            return True
        q = np.array(P); dx = q - p
        dx[:, 0] -= Lx * np.round(dx[:, 0] / Lx); dx[:, 1] -= Ly * np.round(dx[:, 1] / Ly)
        return not np.any(np.hypot(dx[:, 0], dx[:, 1]) < np.array(a) + rad + 1)
    if poly:
        for q, (lo, hi, al) in enumerate([(2.0, 5.0, 0.03), (5.0, 14.0, 0.03)]):
            acc = 0.0
            while acc < al * Lx * Ly:
                dH = rng.uniform(lo, hi)
                rad = dH * H_px / 2
                for _ in range(100000):
                    p = rng.uniform((0, 0), (Lx, Ly))
                    if free(p, rad):
                        break
                P.append(p); a.append(rad); D0.append(2 / _s_booth_demo(dH) - 1); big.append(q == 1); acc += math.pi * rad * rad
    else:
        for rad, dl, al in [(24.0, 0.29, 0.03), (8.0, 4.8, 0.03)]:
            n = int(al * Lx * Ly / (math.pi * rad * rad))
            tries = 0
            while n > 0 and tries < 200000:
                tries += 1
                p = rng.uniform((0, 0), (Lx, Ly))
                if not free(p, rad):
                    continue
                P.append(p); a.append(rad); D0.append(dl); big.append(rad > 12); n -= 1
    P = np.array(P); a = np.array(a); D0 = np.array(D0)
    dr = np.where(np.array(big), drift[1], drift[0])
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
        V[:, 1] += dr
        for i in range(N):
            ar = math.pi * max(a[i] - r_shift, 0.5) ** 2
            rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": i + 1, "イベント": "",
                         "面積(px)": f"{ar:.3f}", "ROI内面積(px)": f"{ar:.3f}",
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
            dpush = (ov / np.where(r > 0, r, 1))[..., None] * d * 0.5
            dP = dpush.sum(1)
            P = P + dP; unwrapped = unwrapped + dP
        P[:, 0] %= Lx; P[:, 1] %= Ly
    path = os.path.join(out, name)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    frame_alpha = {f: float(np.sum(math.pi * a * a) / (Lx * Ly)) for f in range(nf)}
    return path, np.array(truth), a, D0, m, U, noise, frame_alpha


def _i111_only(path, bins, H_px, k, per, n_boot=40, r_offset=0.0, nodes=None):
    """자가 시험의 추가 경우: I111만 돌린다(폭·R_reg 계산은 건너뜀)."""
    tracks = read_tracks(path, "right", 0.02, H_px * 0.02, r_offset=r_offset)
    obs, _ = track_velocities(tracks, k, 1, H_px, near_contact(tracks, 0.5, periodic=per))
    nodes = nodes or auto_nodes(tracks, bins, H_px)
    basis = lam_basis_fields(tracks, bins, nodes, H_px, obs, k, 1, periodic=per, scheme="euler")
    lr, tab = lamreg_fit(obs, bins, basis, nodes, periodic=per, n_boot=n_boot)
    return lr, tab


def _demo(out, push=False, seed=3, contact_gap=0.5):
    os.makedirs(out, exist_ok=True)
    path, truth, a, D0, m, U, noise, frame_alpha = make_demo(out, seed=seed, push=push)
    H_px, k = 16.0 / 3, 4                                # 작은 기포 d 16 px = d/H 3, 큰 기포 d 48 px = d/H 9. 느린 작은 기포는 k를 키워 잡음을 줄인다
    bins = ((2, 5), (5, 50))
    per = (2000.0, 1000.0)
    tracks = read_tracks(path, "right", 0.02, H_px * 0.02)
    near = near_contact(tracks, contact_gap, periodic=per)
    obs, dd = track_velocities(tracks, k, 1, H_px, near)
    fields = window_fields(dipole_fields(tracks, class_lambda(obs, bins, U), H_px, U, periodic=per), obs, k, 1, scheme="euler")
    unit = window_fields(dipole_fields(tracks, lambda dh: 1.0, H_px, 1.0, periodic=per), obs, k, 1, scheme="euler")
    nodes = auto_nodes(tracks, bins, H_px)
    basis = lam_basis_fields(tracks, bins, nodes, H_px, obs, k, 1, periodic=per, scheme="euler")
    res, sig_p, _ = analyse(obs, dd, k, 1, bins, frame_alpha=frame_alpha, U_loc_px=U, n_boot=100, fields=fields, unit_fields=unit,
                            periodic=per, basis=basis, nodes=nodes)
    # 정답: 잡음 없는 위치로 같은 계산을 하고 잡음 0으로 둔다
    tr_true = defaultdict(dict)
    for f in range(truth.shape[0]):
        for i in range(truth.shape[1]):
            tr_true[str(i + 1)][f] = (truth[f, i, 0], truth[f, i, 1], math.pi * a[i] ** 2, False)
    obs_t, _ = track_velocities(tr_true, k, 1, H_px, near)
    res_t, _, _ = analyse(obs_t, np.zeros((0, 3)), k, 1, bins, n_boot=0, noise_px=0.0, periodic=per)
    lam_true = float(np.sum(np.abs(2 / (1 + D0) - 1) * math.pi * a * a) / np.sum(math.pi * a * a))   # Σα|λ|/α
    fails = []

    def check(name, got, want, tol, absolute=False):
        ok = abs(got - want) <= (tol if absolute else tol * abs(want))
        lim = f"±{tol:g}" if absolute else f"{tol:.0%}"
        print(f"  {'통과' if ok else '실패'}  {name}: 도구 {got:.4g}, 정답 {want:.4g} (허용 {lim})")
        if not ok:
            fails.append(name)
    print(f"[1] 합성 추적: 기포 {truth.shape[1]}개 × {truth.shape[0]}프레임, 위치 잡음 {noise} px, m = {m:.3f}, 시드 {seed}")
    check("위치 잡음 σ_p", sig_p, noise, 0.15)
    for r, rt, dl in zip(res, res_t, (4.8, 0.29)):
        tag = f"d/H {r['dH_lo']:g}~{r['dH_hi']:g}"
        print(f"  {tag}: 관측 {r['n_obs']}(프레임당 이 구분 {r['n_per_frame_class']:.0f}, 전체 {r['n_per_frame_all']:.0f}), 상대 잡음 {r['noise_rel']:.3f}, "
              f"반IQR 흐름 {r['hiqr_s']:.4f}·가로 {r['hiqr_c']:.4f} → γ {r['gamma_s']:.4f}·{r['gamma_c']:.4f}, 폭의 비 R {r['R']:.3f} "
              f"[{r['R_lo']:.3f}~{r['R_hi']:.3f}](참고: 배치 비등방에 민감), 회귀 기울기 흐름 {r['b_s']:.3f}·가로 {r['b_c']:.3f} → "
              f"R_reg {r['R_reg']:.3f} [{r['R_reg_lo']:.3f}~{r['R_reg_hi']:.3f}], m_reg {r.get('m_reg', float('nan')):.3f}, "
              f"|λ|_fwd {r.get('abs_lambda_fwd', float('nan')):.3f}(g 식 {r.get('abs_lambda_eff', float('nan')):.3f})")
        check(f"{tag} 가로 γ(잡음 뺀 값) 대 잡음 없는 폭", r["gamma_c"], rt["hiqr_c"], 0.15)
        check(f"{tag} 흐름 방향 γ 대 잡음 없는 폭", r["gamma_s"], rt["hiqr_s"], 0.15)
        check(f"{tag} 순방향 |λ|_fwd 대 Σα|λ|/α", r["abs_lambda_fwd"], lam_true, 0.12)
        want = (1 + dl) / (1 + m * dl)
        if r["n_tracks"] >= 100:
            check(f"{tag} 가로 회귀 기울기 대 할선 이동도 2/(1 + Δ)", r["b_c"], 2 / (1 + dl), 0.03)
            check(f"{tag} 회귀 비 R_reg 대 (1 + Δ)/(1 + mΔ)", r["R_reg"], want, 0.02)
        else:
            inside = r["R_reg_lo"] <= want <= r["R_reg_hi"]
            print(f"  {'통과' if inside else '실패'}  {tag}(트랙 {r['n_tracks']}개, 표본이 적어 구간만 봄): 정답 {want:.3f}이 R_reg 95% 구간 안")
            if not inside:
                fails.append(tag)
    check("작은 기포 회귀로 되찾은 m", res[0]["m_reg"], m, 0.03, absolute=True)
    for r, dl in zip(res, (4.8, 0.29)):                  # I111: U_loc 없이 부호 있는 λ, 국소장, R, m(검토 10 #8의 허용)
        tag = f"d/H {r['dH_lo']:g}~{r['dH_hi']:g}"
        lam_t = 2 / (1 + dl) - 1
        print(f"  {tag}: I111 λ_자기 {r.get('lam_reg_self', float('nan')):+.4f}(참 {lam_t:+.4f}), U_loc {r.get('U_loc_lamreg', float('nan')):.3f}"
              f" [{r.get('U_loc_lamreg_lo', float('nan')):.3f}~{r.get('U_loc_lamreg_hi', float('nan')):.3f}](참 {U:.3f} px/frame), "
              f"R_λ {r.get('R_lamreg', float('nan')):.4f} [{r.get('R_lamreg_lo', float('nan')):.4f}~{r.get('R_lamreg_hi', float('nan')):.4f}], "
              f"m_λ {r.get('m_lamreg', float('nan')):.3f}")
        check(f"{tag} I111 λ_자기(U_loc 없음) 대 s − 1", r.get("lam_reg_self", float("nan")), lam_t, 0.015, absolute=True)
        check(f"{tag} I111 U_loc = 중앙값 V̄_i/(1 + λ(d_i))", r.get("U_loc_lamreg", float("nan")), U, 0.02)
        check(f"{tag} I111 R_λ 대 (1 + Δ)/(1 + mΔ)", r.get("R_lamreg", float("nan")), (1 + dl) / (1 + m * dl), 0.01)
    check("작은 기포 I111 m(U_loc 없음)", res[0].get("m_lamreg", float("nan")), m, 0.03, absolute=True)

    print("[2] 구분마다 일정한 가로 표류(작은 0.05, 큰 0.1 px/frame: 기울임·측벽 표류). 앞 판은 교차 항이 +0.023, 자기 항이 +0.005 움직였다")
    p2 = make_demo(out, seed=seed, drift=(0.05, 0.1), name="demo_drift.csv")[0]
    lr2, _ = _i111_only(p2, bins, H_px, k, per)
    lt = {0: 2 / (1 + 4.8) - 1, 1: 2 / (1 + 0.29) - 1}
    for j, (lo, hi) in enumerate(bins):
        r = lr2.get(j, {})
        check(f"표류 d/H {lo:g}~{hi:g} λ_자기", r.get("lam_reg_self", float("nan")), lt[j], 0.015, absolute=True)
        lo_k, hi_k = bins[1 - j]
        check(f"표류 d/H {lo:g}~{hi:g} 교차 항(원천 {lo_k:g}~{hi_k:g}, 점검용)", r.get(f"lam_reg_src_{lo_k:g}_{hi_k:g}", float("nan")),
              lt[1 - j], 0.03, absolute=True)

    print("[3] 다분산 구분(d/H 2~5·5~14에서 d 고르게, s(d/H)는 Booth 관계, s = 1인 d* = 10.1). 앞 판은 U_loc −19%·−9.5%였다(구분 중앙값으로 나눔)")
    p3, _, a3, D03, *_ = make_demo(out, seed=1, poly=True, name="demo_poly.csv")
    bins3 = ((2, 5), (5, 14))
    lr3, tab3 = _i111_only(p3, bins3, H_px, k, per, nodes=[2.0, 3.5, 6.0, 10.0, 14.0])
    for j, (lo, hi) in enumerate(bins3):
        check(f"다분산 d/H {lo:g}~{hi:g} U_loc", lr3.get(j, {}).get("U_loc_lamreg", float("nan")), U, 0.02)
    for dn, lam_n, _, _ in tab3:
        if 2.5 <= dn <= 12:                              # 원천이 양쪽에 있는 마디만
            check(f"다분산 λ(d/H = {dn:g})", lam_n, _s_booth_demo(dn) - 1, 0.02, absolute=True)
    r3 = lr3.get(1, {})
    d_true = next(x for x in np.linspace(5, 14, 9001) if _s_booth_demo(x) >= 1)
    print(f"  d* {r3.get('dstar', float('nan')):.2f} [{r3.get('dstar_lo', float('nan')):.2f}~{r3.get('dstar_hi', float('nan')):.2f}](참 {d_true:.2f}), "
          f"U_loc(d*) {r3.get('U_loc_dstar', float('nan')):.3f} [{r3.get('U_loc_dstar_lo', float('nan')):.3f}~{r3.get('U_loc_dstar_hi', float('nan')):.3f}]"
          f"(트랙 {r3.get('n_dstar', 0)}개)")
    check("다분산 d*(λ = 0인 크기)", r3.get("dstar", float("nan")), d_true, 0.08)
    check("다분산 U_loc(d*) = d* 근처 기포 속도", r3.get("U_loc_dstar", float("nan")), U, 0.02)

    print("[4] 윤곽 규약: CSV 반경이 0.5 px 작다(검출 윤곽이 안쪽). 회귀는 λ·(a_eff/a)²를 낸다")
    p4 = make_demo(out, seed=seed, r_shift=0.5, name="demo_contour.csv")[0]
    lr4, _ = _i111_only(p4, bins, H_px, k, per)
    lr4c, _ = _i111_only(p4, bins, H_px, k, per, r_offset=0.5)
    for j, (lo, hi) in enumerate(bins):
        r, rc = lr4.get(j, {}), lr4c.get(j, {})
        got = r.get("U_loc_lamreg", float("nan")) / rc.get("U_loc_lamreg", float("nan")) - 1
        a_img = (8.0 if j == 0 else 24.0) - 0.5
        pred = r.get("U_area_sens", float("nan")) * 2 * 0.5 / a_img
        print(f"  d/H {lo:g}~{hi:g}: 보정 없는 U_loc이 보정한 값보다 {got:+.1%}(1차 감도 |1 − 1/s|·δA/A로 ±{pred:.1%}), "
              f"--r_offset_px 0.5로 {rc.get('U_loc_lamreg', float('nan')):.3f} px/frame")
        ok = pred > 0 and 0.6 <= abs(got) / pred <= 1.6
        print(f"  {'통과' if ok else '실패'}  d/H {lo:g}~{hi:g} 보정 없는 U_loc 어긋남이 1차 감도의 0.6~1.6배")
        if not ok:
            fails.append(f"윤곽 감도 {lo:g}~{hi:g}")
        check(f"윤곽 보정 뒤 d/H {lo:g}~{hi:g} U_loc", rc.get("U_loc_lamreg", float("nan")), U, 0.02)
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px), 예 0.02")
    ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--detrend", default="4,8", help="위치별 정상 표류를 뺄 (흐름 방향, 가로) 분위 칸 수. none이면 끈다")
    ap.add_argument("--no_lamreg", action="store_true", help="U_loc 없는 부호 있는 λ(d) 회귀(I111)를 끈다(원천 기저마다 장을 한 번 더 계산)")
    ap.add_argument("--lam_nodes", default="auto", help="I111 λ(d) 삼각 기저의 마디(d/H, 쉼표). auto면 검출 d/H 2~98%% 사이 구분 수 + 1개")
    ap.add_argument("--r_offset_px", type=float, default=0.0,
                    help="검출 반경에 더할 값(px). 윤곽이 흰 테두리 바깥보다 안쪽이면 +(작은 기포 약 0.5, 큰 기포 약 1.3). I111 λ·U_loc 감도 시험용")
    ap.add_argument("--boot_block", type=int, default=0,
                    help="I111 구간을 프레임 블록 단위로 다시 뽑는다(시야 통과 시간 이상 권장). 0이면 트랙 단위(배치 표본 오차를 덜 넣음)")
    ap.add_argument("--jL", type=float, default=float("nan"), help="액체 겉보기 속도 j_L(m/s). --jG와 함께 주면 I113 E_U를 낸다")
    ap.add_argument("--jG", type=float, default=float("nan"), help="기체 겉보기 속도 j_G(m/s)")
    ap.add_argument("--H_mm", type=float); ap.add_argument("--flow", default="up")
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--smooth", type=int, default=1)
    ap.add_argument("--frame_area_px", type=float, default=float("nan"))
    ap.add_argument("--U_loc", type=float, default=float("nan"), help="국소장 U_loc(m/s). 원형이면 (U_P + J)/2(I91) 또는 I102")
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--contact_gap", type=float, default=0.5, help="틈이 이 값 × 작은 쪽 반경보다 좁은 관측은 뺀다(0이면 끔)")
    ap.add_argument("--regress", action="store_true", help="계산한 쌍극자 장에 회귀(배치 비등방에 강함). --U_loc 필요")
    ap.add_argument("--walls", default="", help="측벽의 가로 좌표 두 개(px, 영상 좌표), 예: 12,1060. 주면 거울상을 넣는다")
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--noise_px", type=float, default=float("nan"),
                    help="위치 잡음(px)을 따로 잰 값으로 준다(정지 기포·표적 영상). 비우면 2차 차분(흰 잡음 가정, 상관 잡음이면 과소)")
    ap.add_argument("--no_unit", action="store_true", help="순방향 |λ| 환산(λ = 1 장 계산)을 끈다(기포가 아주 많을 때 시간 절약)")
    ap.add_argument("--out", default="vf_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm and a.H_mm):
        ap.error("--csv, --px_mm, --H_mm가 필요하다")
    if a.px_mm > 1:
        ap.error("--px_mm은 화소 하나의 크기(mm/px)다(예 0.02). 1보다 크면 px/mm로 넣은 것 같다.")
    detrend = None if a.detrend.strip().lower() == "none" else tuple(int(v) for v in a.detrend.split(","))
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    edges = [float(v) for v in a.dH_bins.split(",")]
    bins = list(zip(edges[:-1], edges[1:]))
    tracks = read_tracks(a.csv, a.flow, a.px_mm, a.H_mm, r_offset=a.r_offset_px)
    obs, dd = track_velocities(tracks, a.k, a.smooth, H_px, near_contact(tracks, a.contact_gap))
    frame_alpha = None
    if a.frame_area_px == a.frame_area_px:
        tot = defaultdict(float)
        for fr in tracks.values():
            for f, (_, _, A, _) in fr.items():
                tot[f] += A
        frame_alpha = {f: v / a.frame_area_px for f, v in tot.items()}
    U_px = a.U_loc / (a.px_mm * 1e-3 * a.fps) if a.U_loc == a.U_loc else None
    walls = tuple(float(v) for v in a.walls.split(",")) if a.walls else None
    fields = fields_ns = unit = None
    if not a.no_unit:                                    # 순방향 |λ|: 압력·국소장 없이 된다(λ = 1, U = 1 장)
        unit = window_fields(dipole_fields(tracks, lambda dh: 1.0, H_px, 1.0, walls=walls), obs, a.k, a.smooth)
    if a.regress:
        if not U_px:
            raise SystemExit("--regress에는 --U_loc(국소장, m/s)이 필요하다(I91의 (U_P + J)/2, 영상 α와 유량계의 j_L/(1 − α), 또는 I102의 기울임 편향).")
        lam = class_lambda(obs, bins, U_px)
        fields = window_fields(dipole_fields(tracks, lam, H_px, U_px, walls=walls), obs, a.k, a.smooth)
        if walls:
            fields_ns = window_fields(dipole_fields(tracks, lam, H_px, U_px, walls=walls, self_image=False), obs, a.k, a.smooth)
    nodes = basis = None
    if not a.no_lamreg and obs:
        nodes = auto_nodes(tracks, bins, H_px) if a.lam_nodes.strip().lower() == "auto" else [float(v) for v in a.lam_nodes.split(",")]
        basis = lam_basis_fields(tracks, bins, nodes, H_px, obs, a.k, a.smooth, walls=walls)
    res, sig_p, lam_tab = analyse(obs, dd, a.k, a.smooth, bins, frame_alpha, U_px, a.n_boot, fields=fields, unit_fields=unit,
                                  fields_noself=fields_ns, noise_px=a.noise_px if a.noise_px == a.noise_px else None, detrend=detrend,
                                  basis=basis, nodes=nodes, boot_block=a.boot_block)
    px_s = a.px_mm * 1e-3 * a.fps                        # px/frame → m/s
    print(f"속도 표본 {len(obs)}개(트랙 {len(set(o[0] for o in obs))}개), 위치 잡음 σ_p ≈ {sig_p:.3f} px"
          + (f", 위치별 정상 표류 뺌({detrend[0]}×{detrend[1]} 칸)" if detrend else ""))
    if obs:
        dh_all = np.array([o[4] for o in obs])
        for lo, hi in bins:
            n_in = int(((dh_all >= lo) & (dh_all < hi)).sum())
            if n_in < 30:
                print(f"  d/H {lo:g}~{hi:g}: 관측 {n_in}개라 뺐다(30개 이상 필요)")
        if not res:
            print(f"  쓸 구분이 없다. 관측 d/H 범위 {np.percentile(dh_all, 1):.2f}~{np.percentile(dh_all, 99):.2f}(H = {H_px:.2f} px). "
                  "--dH_bins나 --px_mm(mm/px)·--H_mm를 확인한다.")
        if not walls:                                    # 측벽 거울상을 빠뜨리면 큰 기포 λ가 몇 % 깎인다(검토 10 #18)
            c_all = np.array([c_ for fr_ in tracks.values() for (_, c_, _, _) in fr_.values()])
            c_lo, c_hi = float(c_all.min()), float(c_all.max())
            for lo, hi in bins:
                m_ = [(o[6], o[4] * H_px / 2) for o in obs if lo <= o[4] < hi]
                if len(m_) >= 30:
                    near_w = np.mean([min(c_ - c_lo, c_hi - c_) < 3 * r_ for c_, r_ in m_])
                    if near_w > 0.2:
                        print(f"  참고: d/H {lo:g}~{hi:g} 관측의 {near_w:.0%}가 가로 끝(검출 범위) 3a 안이다. 그 끝이 측벽이면 --walls를 준다"
                              "(빠뜨리면 큰 기포 λ가 약 6% 깎인다, 검토 10 #18).")
    if res:
        keys = sorted({k for r in res for k in r}, key=lambda k: list(res[0].keys()).index(k) if k in res[0] else 99)
        with open(os.path.join(a.out, "vf_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in res:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    if lam_tab:
        with open(os.path.join(a.out, "vf_lamd.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dH_node", "lambda", "lambda_lo", "lambda_hi", "s"])
            for dn, ln_, lo_, hi_ in lam_tab:
                w.writerow([f"{dn:.4g}", f"{ln_:.5g}", f"{lo_:.5g}", f"{hi_:.5g}", f"{1 + ln_:.5g}"])
        print("I111 λ(d) 마디(U_loc 없음, λ·(a_eff/a)²): " + "; ".join(
            f"d/H {dn:.2f} λ {ln_:+.3f} [{lo_:+.3f}~{hi_:+.3f}]" if ln_ == ln_ else f"d/H {dn:.2f} 원천 없음" for dn, ln_, lo_, hi_ in lam_tab))
    for r in res:
        line = (f"d/H {r['dH_lo']:g}~{r['dH_hi']:g}: 관측 {r['n_obs']}(트랙 {r['n_tracks']}, 프레임당 이 구분 {r['n_per_frame_class']:.0f}), "
                f"V̄ {r['V_px_per_frame']:.2f} px/frame, σ_p {r['sigma_p']:.3f} px, 상대 잡음 {r['noise_rel']:.3f}, "
                f"코시 척도 흐름 {r['gamma_s']:.4f}·가로 {r['gamma_c']:.4f}(트랙 부트스트랩 구간은 배치 표본 오차를 넣지 않는다), "
                f"R {r['R']:.3f} [{r['R_lo']:.3f}~{r['R_hi']:.3f}]")
        if "abs_lambda_fwd" in r:
            line += f", |λ|_fwd {r['abs_lambda_fwd']:.2f}(같은 관측·창의 λ = 1 장 가로 폭으로 나눔)"
        if "alpha" in r:
            line += f", α {r['alpha']:.3f} → |λ|(g 식, 작은 탐침·단분산 근사) {r['abs_lambda_eff']:.2f}"
        if "m" in r:
            line += f", s {r['s']:.2f}(Δ {r['Delta']:.2f}) → m {r['m']:.2f} [{r['m_lo']:.2f}~{r['m_hi']:.2f}]"
        if "R_reg" in r:
            line += (f"; 회귀: 기울기 흐름 {r['b_s']:.3f}·가로 {r['b_c']:.3f}(가로 = 할선 이동도 s여야 함), "
                     f"R_reg {r['R_reg']:.3f} [{r['R_reg_lo']:.3f}~{r['R_reg_hi']:.3f}]")
            if "m_reg" in r:
                line += f" → m_reg {r['m_reg']:.2f} [{r['m_reg_lo']:.2f}~{r['m_reg_hi']:.2f}]"
            if "R_reg_noself" in r:
                line += f"; 측벽 자기 거울상 뺀 회귀 R_reg {r['R_reg_noself']:.3f}"
        print(line)
        if "U_loc_lamreg" in r:
            U_m = r["U_loc_lamreg"] * px_s
            a_px = r["dH_med_tracks"] * H_px / 2
            sens = r["U_area_sens"] * 2 * 0.5 / a_px if a_px > 0 else float("nan")   # 반경 0.5 px 어긋남의 1차 효과
            txt = (f"  I111(U_loc 없음): 이 구분 트랙 {r['lamreg_tracks']}개, λ_자기 {r['lam_reg_self']:+.3f} "
                   f"[{r['lam_reg_self_lo']:+.3f}~{r['lam_reg_self_hi']:+.3f}] → s {r['s_lamreg']:.3f}, "
                   f"U_loc = 중앙값 V̄_i/(1 + λ(d_i)) {r['U_loc_lamreg']:.3f} [{r['U_loc_lamreg_lo']:.3f}~{r['U_loc_lamreg_hi']:.3f}] px/frame"
                   f" = {U_m:.4g} m/s, R_λ {r['R_lamreg']:.3f} [{r['R_lamreg_lo']:.3f}~{r['R_lamreg_hi']:.3f}]")
            txt += (f" → m {r['m_lamreg']:.2f} [{r['m_lamreg_lo']:.2f}~{r['m_lamreg_hi']:.2f}]" if "m_lamreg" in r
                    else " (R 구간이 넓어 m은 읽지 않음)")
            srcs = [kk for kk in r if kk.startswith("lam_reg_src_") and not kk.endswith(("_lo", "_hi"))]
            if srcs:
                txt += "; 구분 지시 회귀(점검용, 교차 항 = λ_k·U_loc,k/U_loc,i): " + ", ".join(
                    f"원천 d/H {kk[12:].replace('_', '~')} {r[kk]:+.3f} [{r.get(kk + '_lo', float('nan')):+.3f}~{r.get(kk + '_hi', float('nan')):+.3f}]"
                    for kk in srcs)
            print(txt)
            print(f"    윤곽 감도: 반경이 0.5 px 어긋나면 U_loc 약 ±{sens:.1%}(|1 − 1/s| = {r['U_area_sens']:.2f} × δA/A). "
                  + ("s가 1에서 멀어 반경 보정(--r_offset_px로 다시 돌림) 없이는 U_loc을 정량으로 쓰지 않는다." if r["U_area_sens"] > 0.5
                     else "s가 1에 가까워 윤곽 규약에 둔하다."))
            if "U_loc_dstar" in r:
                print(f"    d*(λ = 0인 크기) {r['dstar']:.2f} [{r['dstar_lo']:.2f}~{r['dstar_hi']:.2f}]가 이 구분 안: U_loc(d*) = d* ±15% 기포 "
                      f"{r['n_dstar']}개의 속도 {r['U_loc_dstar']:.3f} [{r['U_loc_dstar_lo']:.3f}~{r['U_loc_dstar_hi']:.3f}] px/frame"
                      f" = {r['U_loc_dstar'] * px_s:.4g} m/s. s = 1이라 윤곽 규약·막 기억(λ에 곱해지는 오차)에 둔하다 → 국소장은 이 값을 먼저 쓴다.")
            if a.jL == a.jL and a.jG == a.jG and a.jL > 0:
                J = a.jL + a.jG
                for tag_u, key in (("구분 U_loc", "U_loc_lamreg"), ("U_loc(d*)", "U_loc_dstar")):
                    if r.get(key, float("nan")) != r.get(key, float("nan")):
                        continue
                    E = (2 * r[key] * px_s - J) / a.jL - 1
                    E_lo, E_hi = ((2 * r[key + q] * px_s - J) / a.jL - 1 for q in ("_lo", "_hi"))
                    note = (f"윤곽 0.5 px이면 ±{2 * sens * U_m / a.jL:.3f}, 반경 보정·좁은 구간·단분산 운전에서만 정량" if key == "U_loc_lamreg"
                            else "d*의 위치 오차만 남음")
                    print(f"    I113 탭 없는 압력 강하({tag_u}): E_U = (2U_loc − J)/j_L − 1 = {E:+.3f} [{E_lo:+.3f}~{E_hi:+.3f}] ({note}, 검토 10 #5).")
        if r.get("noise_over_signal", 0) > 0.5:
            print(f"  경고: 잡음이 가로 폭의 {r['noise_over_signal']:.0%}다. 디컨볼루션은 코시꼴(α ≲ 0.05)에서만 2~4% 안이고, 정규꼴이면 −15% 이상 치우친다(검토 7 #8).")
        if r.get("n_per_frame_class", 99) < 5:
            print("  참고: 이 구분은 프레임당 관측이 적다. 공통 요동은 모든 구분의 프레임 편차에 대한 회귀로 뺐다(구분 안 중앙값을 빼지 않음).")
    print("읽는 법: |λ|_fwd는 이웃의 이동도 결손 크기(부호 없음, I99)로 압력·국소장 없이 나온다(g 식은 작은 탐침·단분산 근사라 큰 기포에서 절반 아래로 틀림). "
          "R = (1 + Δ)/(1 + mΔ)(I100): 깨끗한 막 m 2/3이면 d/H 3에서 약 1.4, 마른 접촉선 m ≈ 0이면 1 + Δ로 크다. "
          "m에는 국소장 U_loc이 필요하다(Δ = 2U_loc/V̄ − 1, 회귀자 λ). 폭의 비 R은 배치 비등방에 민감하므로 m은 --regress의 R_reg로 읽는다"
          "(합성 시험: 작은 기포 −0.6%, m 0.672 대 0.667). 막 기억(뒤 메니스커스가 오래된 막을 걷음)이면 두 기울기가 각각 최대 약 −20% 바뀌지만 "
          "R은 +2~3%뿐이다 → 가로 기울기 = s 점검은 빠른 요동에서 맞지 않을 수 있다. 큰 기포가 작은 기포를 따라잡아 닿는 운전은 큰 구분 R_reg를 깎는다(합성 0.91~0.95 대 1.08). "
          "I111: 회귀 λ는 λ·(a_eff/a)²이고, U_loc은 면적 규약 오차를 |1 − 1/s|배로 키운다(위 윤곽 감도). 막 기억은 λ를 최대 약 20% 작게 내 "
          "U_loc을 s 0.345에서 −28% 치우치므로 같은 속도 원천(좁은 구간)에서 읽고 --k를 바꿔 본다. 구간은 같은 영상 안 다시 뽑기라 1.5~2배 좁다"
          "(--boot_block 또는 영상 사이 산포). 철 채널은 I88 조건부 평균으로 장의 꼴을 먼저 확인한다.")


if __name__ == "__main__":
    main()

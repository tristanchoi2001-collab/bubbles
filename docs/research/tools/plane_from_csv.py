"""판별 평면(아이디어 I73, 추정 5.4절)을 운전점 표 + 추적 CSV에서 바로 그린다.

쓰는 법
    python plane_from_csv.py points.csv --out plane_out
    python plane_from_csv.py --demo --out plane_demo      # 합성 자료로 스스로 점검

points.csv (UTF-8, 운전점 한 줄씩. 열 이름은 영어)
    name          운전점 이름
    H_mm          유효 갭(단상 ΔP로 정한 값을 권장)
    jL, jG        액체·기체 겉보기 속도 (m/s, 시야 위치의 압력으로 환산한 값)
    dp_tp, dp_l   같은 탭 구간의 이상류 ΔP와 같은 j_L의 단상 ΔP (Pa)
    tracking_csv  2_bin_track.py / 2_steel_track.py 의 result_tracking.csv 경로
    roi_area_px   ROI 면적(px)
    px_mm         화소 크기(mm/px)
    fps           촬영 속도(frame/s)
    flow          영상에서 흐름 방향: up(투명 채널 기본, y가 줄어드는 쪽) / down / right(철 채널 기본) / left
    mu, rho       액체 점도(Pa·s)·밀도(kg/m³). 비우면 물 20 °C
    T_tp, T_l     (선택) 이상류·단상 측정 때 수온(°C). 둘 다 있으면 dp_l을 물 점도 비 μ(T_tp)/μ(T_l)로 보정
    wall_lo_px, wall_hi_px  (선택) 두 측벽의 가로 좌표(화소, 영상 밖이어도 됨). 흐름이 up/down이면 X, right/left면 Y.
                  비우면 모든 프레임의 기포 가로 끝(중심 ± 등가 반경)의 최소·최대로 추정하고 경고한다.
    q_radius_px   (선택) 배치 계수 Q를 더하는 흐름 방향 반폭 L(화소). 비우면 min(채널 폭, 시야 길이/3)
    masks_dir     (선택) 추적 프로그램의 SAVE_INSTANCE_MASKS 출력 폴더(OUTPUT_FOLDER/instances, 프레임마다 <파일 이름>.npz의
                  라벨 지도 inst). 있으면 기포 윤곽마다 경계요소법으로 C_A(I81)를 구해 b/a 추정기 대신 쓴다.
                  CSV 기포와는 중심 3 px·면적 비 0.8~1.25로 짝짓는다. ca_max_bubbles(기본 2000)개까지만 표본으로 계산한다.
    dp_tp_se, dp_l_se  (선택) 두 ΔP의 표준오차(Pa). T_se(선택): 수온 차의 표준오차(K, 물 점도 2.4 %/K로 환산).
    B_rel_se      (선택) 유량계 비 B의 상대 표준오차(예: 0.02)
    sigma         (선택) 표면장력(N/m). 비우면 물 σ(T) = 0.0757 − 1.665×10⁻⁴·T(T_tp, 없으면 20 °C)
    friction_k    (선택) 힘 균형 예측의 마찰 계수 k(D = k·σ·a·Ca^(2/3)). 비우면 16.85(깨끗한 막)
    stuck_s       (선택) 멈춘 기포로 보는 이동도 문턱 s* = 2u/(U_P + J). 비우면 0.1
    shape_friction (선택) 0이면 마찰 합에 모양 배율 S(b/a)를 곱하지 않는다(원 공식). 비우면 곱한다(아래 속도 중심).

계산 (모두 "갭을 채운 기포", 즉 등가직경 d > 2H만 쓴다)
    α        프레임마다 Σ ROI内面積 / ROI 면적의 평균
    b/a      화면 끝에 닿지 않은 기포마다 a = |중심 − 앞끝|(흐름 방향 반축), b = A/(π a) → b/a = A/(π a²), 면적 가중 평균
             앞끝은 윤곽 위쪽 5% 점의 평균이라 a가 조금 작게 나와 b/a가 몇 % 크게 나온다.
    s̄        B(1 − α)/α (B = jG/jL, 유량계), s̄_T = B_f(1 − α)/α (B_f = 영상 기체 유량 / jL, 추적)
    E        dp_tp/dp_l − 1,  y = E(1 − α)/α,  x = 1 − s̄
    예측     원형 폐합 y = 1 + x, 모양 폐합 y = 1 + (b/a)x, 분리류 y = 1, 균질류 y = 1 − x
             기포별 y_track = ΣA_i[1 + (b/a)_i(1 − s_i)]/ΣA_i, s_i = u_i(1 − α)/jL (추적 속도, 유량계 불필요)
    Re_B     ρH²u_B²/(μ w_B u_L) (Moriyama & Inoue 1993), Λ = ρ u_L H²/(10 μ d̄)
    오차     α·B_f·Q는 프레임 블록 부트스트랩(블록 = 프레임 수/20, 400번)으로 표준오차를 낸다(프레임끼리 상관이 있어
             기포 수로 나누면 과소). E는 위 선택 열로, x·y는 그것을 전파한다. α 오차는 점을 (1, 0) 쪽으로, E 오차는 세로로 옮긴다.
    Q        배치 계수(I74, 독립 검토 3). 기포 i에서 Q_i = Σ_j a_j²·cos 2θ_ij / r_ij²(a_j = 등가 반경, θ는 흐름 방향 기준,
             원 합 = Lorentz 기준). 측벽(불투과)의 거울상(같은 부호, 두 벽이라 2W 주기)과 기포 자신의 거울상을 넣고,
             흐름 방향 띠 |Δs| ≤ L에서 더한 뒤 연속체 보정으로 원 합으로 바꾼다(layout_q 설명). 띠가 시야 밖으로 나가지 않는
             기포만 대상으로 하고 면적 가중 평균한다. 진단용 Q_noimg = 거울상 없는 반경 L의 원 합(고른 배치에서 0과 α 사이).
    C_A      (masks_dir가 있을 때) 윤곽 → marching squares → 푸리에 평활 → 경계요소(added_mass_bem.py)의 면적 가중 평균.
             b/a 추정기(A/(πa²))는 D형·총알 모양에서 C_A를 17~40% 작게 낸다(독립 검토 4). 짝지은 같은 기포들의 두 값을 함께 낸다.
    예측 기울기  쌍극자 수준 정확식(독립 검토 5): slope = (C(1 − α) − ε)/(1 − α + ε), ε = (1 + C)Q/2 + α(1 − C)/2
             (C = C_A, 없으면 b/a. 원형이면 ε = Q). Q는 기체 유량(A_i·u_i) 가중 평균(속도가 없으면 면적 가중).
             y_layout = 1 + slope·x(측정 x로 정확). 앞 판은 1차식 C − 2Q/(1 − α)와 측정 λ = −x를 넣은 식이라 큰 Q·큰 s에서 틀렸다.
             y_track_layout = ΣA_i[1 + (C_i − (1 + C_i)ε_i/(1 − α))(1 − s_i)]/ΣA_i(기포별 1차식, 진단용)
    속도 중심(I89~I91, 공극률 불필요. 독립 검토 6 반영판)
             시간 평균 힘 균형: 초과 압력 강하 = 움직이는 기포의 마찰 합 + 멈춘 기포의 Darcy 힘.
             E_vel = k·P_2/3 + E_stuck, P_m = (H/(12μ j_L))·σ·⟨Σ_i w_i·a_i·Ca_i^m⟩/A_ROI(a = 등가 반경, Ca = μu/σ, w = ROI 안 몫,
             프레임 평균, 기포 없는 프레임은 0). k = friction_k(기본 16.85 = 깨끗한 계면의 평면 Bretherton 앞·뒤 계수 3.88·1.13을
             둘레로 적분한 값 = Booth 2023의 δ_B = 1.12·Ca^(1/3)·d/H, 추정 5.1절의 경로 B와 같은 식).
             조건: 시간 평균, 모든 기체가 센 기포 안, Darcy(Λ ≪ 1), H/d ≪ 1, 측벽 탭, ROI가 탭 구간을 대표.
             멈춘 기포: s* = 2u/(U_P + J) < stuck_s. 마찰 법칙 대신 Darcy 힘을 받으므로 E_stuck = α_멈춤·(2 + E + B)(원형 국소장).
             잘린 기포(フレーム接触 = 1): 같은 트랙의 화면 끝에 닿지 않은 프레임 면적의 중앙값으로 크기를 정하고, ROI 안 몫으로 센다.
               (앞 판은 보이는 면적의 등가 반경이라 마찰을 1/√(보이는 비율)배 과대 계산했다. 검토 6: d 9~18 mm면 E_vel +9~24%.)
               온전한 프레임이 없는 트랙은 보이는 면적 그대로 세고 그 면적 비를 cut_noref_alpha로 낸다.
             갭보다 작은 기포(d ≤ 2H): 마찰 법칙이 다르므로 빼고 그 면적 비를 alpha_subgap으로 낸다.
             속도 없는 기포(새 트랙 등): 마찰 둘레 항은 둘레(Σw·a) 비로, 유량·멈춘 몫·면적 항은 면적 비로 채운다.
               모든 기포의 속도가 없는 프레임(영상 첫 프레임 등)은 P_m·α_멈춤 평균에서 빠지고 α 평균에는 들어간다(무작위 결측이면 무해, 검토 7 #17).
             k_fit = (E − E_stuck)/P_2/3는 측정 ΔP가 말하는 마찰 계수다(17 근처 깨끗, 21~43 잘 녹는 계면활성제).
             모양 배율(검토 6 #16d): 메니스커스 마찰은 둘레의 ∫|n_x|^(m+1)ds라 같은 면적이라도 가로로 넓은 기포가 더 크다.
               타원(흐름 방향 반축 a, 가로 반축 b)에서 등가 반경 원 대비 S(b/a) = 0.69(0.6), 0.86(0.8), 1.17(1.27), 1.30(1.5),
               1.56(2), 1.97(3)(m 2/3. m마다 따로 표로 만든다). 화면 끝에 닿지 않은 기포는 b/a = A/(πa²)로 S를 곱하고,
               잘린 기포는 1이다. 원 공식이면 b/a 1.27(0.3 mm d/H 10 근처)에서 마찰을 17% 작게 세어 k_fit이 17% 커진다
               (오염 신호 ×1.26과 같은 크기). k_fit_circle = 원 공식의 값(비교용). D형·총알 모양은 타원이 아니라 몇 % 다르다.
             P_area = (H/(12μ j_L))·σ·⟨Σ w·(a²/H)·Ca^(1/3)⟩/A_ROI는 굳은 막 미끄럼의 발자국 막 전단 항이다(계수 6.86).
             여러 운전점이면 friction_fit.csv(m 격자마다 로그 잔차)와 friction_fit_summary.csv를 낸다.
               모든 점에 se_E가 있으면(점 표의 dp_tp_se 등) 로그 공간에서 1/σ²_lnE로 가중한다(요약의 weighted).
               m = 2/3 고정 k(2점 이상), 지수 맞춤과 2항 맞춤 k1·P_2/3 + k2·P_area(5점 이상, 운전점 부트스트랩 95% 구간).
               m과 k는 거의 완전히 상관한다. "굳은 계면 = 지수 1/2"은 근거가 없어 지웠다(검토 6).
             측벽(I101, 검토 7): 폭 W 채널의 가로 위치 y₀에 있는 기포는 자기 거울상 때문에 국소장이 −λG(G = (πa/2W)²[1/sin²(πy₀/W) + 1/3])만큼
               바뀌고 접선 이동도로 응답한다 → s_starW_* = 그것을 뺀 이동도(m 2/3 가정). 폭 20 mm에서 d/H 30(0.3 mm) 기포는 가운데서도 약 −9%.
             이동도 붕괴: s* = 2u/(U_P + J)(원형), s*_C = u(1 + C)/(U_P + C·J)(모양 국소장, C = 기포의 b/a), U_P = j_L(1 + E),
               J = j_L + j_G. d/H 구간별 면적 가중 평균, 같은 구간의 V/J와 Booth 좌표 δ_B = 1.12·Ca_loc^(1/3)·d/H
               (Ca_loc = μ(U_P + J)/(2σ))를 함께 낸다. 깨끗한 막이면 s^(2/3)/(2 − s) = δ_B 한 곡선에 놓인다.
             frames_<이름>.csv: 프레임별 α, 멈춘 α, 순간 기체 유량 j_G,inst = Σ u·A_ROI / ROI 면적, E_D(t), 순간 식
               E_vel_frame = E_D(t) + (j_G − j_G,inst)/j_L(검토 6: 순간에는 기체 유량 요동 항이 남고 시간 평균에서 사라진다).
             자가 시험: python plane_from_csv.py --selftest-vel(정답을 아는 합성 6점으로 위 처리를 모두 점검).
쐐기 보정(β_f)은 넣지 않았다. Q는 쌍극자 수준(원 등가)이라 간격 < 2.5a의 줄에서는 몇 % 다를 수 있다.
힘 균형은 Darcy(Λ ≪ 1)에서 정확하고, 시야(ROI)가 탭 구간을 대표한다고 가정한다(통계적으로 균질).
숫자를 논문에 쓰기 전에 윤곽 규약(I48)과 기체 유량 폐합으로 α를 점검한다.
    python plane_from_csv.py --selftest-q   # 직사각 격자·한 줄·무작위 배치로 Q 계산 점검
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WATER = (1.0e-3, 998.0)
COLS = ["name", "H_mm", "jL", "jG", "dp_tp", "dp_l", "tracking_csv", "roi_area_px", "px_mm", "fps", "flow", "mu", "rho", "T_tp", "T_l",
        "wall_lo_px", "wall_hi_px", "q_radius_px", "masks_dir", "ca_max_bubbles", "dp_tp_se", "dp_l_se", "T_se", "B_rel_se",
        "sigma", "friction_k", "stuck_s", "shape_friction"]
M_GRID = sorted(set([round(0.05 * k, 2) for k in range(25)] + [1 / 3, 2 / 3]))   # 마찰 법칙의 속도 지수 후보(I90)
DH_BINS = ((2, 5), (5, 15), (15, 50), (50, 1e9))                # 이동도 붕괴 표의 d/H 구간
_SR = np.exp(np.linspace(np.log(0.2), np.log(5.0), 121))        # 모양 배율 표의 b/a 격자
EDGE_INSET_PX = 0.5   # 추적기의 先端部는 경계 화소 중심의 평균이라 면적 경계보다 약 0.5 px 안쪽이다(검토 8 #8). 반축에 더한다
_ST = None


def _shape_table():
    """타원(흐름 방향 반축 a, 가로 반축 b)의 앞 메니스커스 적분 ∫|n_x|^(m+1)ds를 등가 반경 원 대비로(검토 6 #16d).
    a = 1, b = r에서 ∫ r^(m+1)|cos t|^(m+1)(sin²t + r²cos²t)^(−m/2) dt / (원의 값 × √r). b/a 1.27에서 1.17, 1.5에서 1.30(m 2/3)."""
    global _ST
    if _ST is None:
        tt = np.linspace(-np.pi / 2, np.pi / 2, 4001)
        dt = tt[1] - tt[0]
        c = np.abs(np.cos(tt)); s2 = np.sin(tt) ** 2; c2 = np.cos(tt) ** 2

        def trap(y):
            return float(np.sum(y[1:] + y[:-1]) * dt / 2)
        rows = []
        for m in M_GRID:
            ref = trap(c ** (m + 1))
            rows.append([trap(r ** (m + 1) * c ** (m + 1) * (s2 + r * r * c2) ** (-m / 2)) / (ref * np.sqrt(r)) for r in _SR])
        _ST = np.array(rows)
    return _ST


def wall_G(a_px, y0_px, W_px):
    """두 측벽 사이 원형 기포의 자기 거울상 인자 G = (πa/2W)²[1/sin²(πy₀/W) + 1/3](I101, 거울상 직접 합과 일치).
    국소장 변화 u'_x/U = −λG(λ = s − 1). 벽 하나 극한(y₀ → 0)은 (a/2y₀)²."""
    y0 = min(max(y0_px, 1e-6 * W_px), W_px * (1 - 1e-6))
    return (math.pi * a_px / (2 * W_px)) ** 2 * (1 / math.sin(math.pi * y0 / W_px) ** 2 + 1 / 3)


def s_wall_correct(s_m, G, m=2 / 3, G_max=0.25):
    """측정 이동도 s_m에서 측벽 자기 거울상을 뺀 무한 폭 이동도 s를 푼다(검토 7 #13).
    s_m = s·(1 − R(s)·(s − 1)·G), R = (1 + Δ)/(1 + mΔ), Δ = 2/s − 1: 흐름 방향 국소장 변화에는 접선 이동도로 응답한다(I100).
    m은 깨끗한 막 2/3을 기본으로 둔다(R 1.08~1.4).
    풀지 않고 NaN을 돌려주는 경우(검토 8 #10): G > G_max(a/W ≳ 0.2이거나 벽 바로 옆), 보정이 95%를 넘음, 정방향 사상
    s → s_m의 기울기 1 − G[(2s − 1)R + s(s − 1)R′]가 0 이하(근이 둘이라 작은 근을 조용히 고를 수 있음), 수렴 안 함.
    G 0.5·참 s 1.6이면 1.357, G 0.7·참 1.5면 0.773(λ 부호가 뒤집힘)을 내던 경우다. 그 범위는 Booth 외 2023의 정확해를 써야 한다."""
    if not (G == G and s_m == s_m and s_m > 0):
        return s_m
    if G <= 1e-12:
        return s_m
    if G > G_max:
        return float("nan")

    def R_of(s):
        dl = max(2 / s - 1, 0.0)
        return (1 + dl) / (1 + m * dl)
    s = s_m
    for _ in range(400):
        den = 1 - R_of(s) * (s - 1) * G
        if den < 0.05:
            return float("nan")
        s_new = s_m / den
        if abs(s_new - s) < 1e-12:
            h = 1e-6 * s_new
            dR = (R_of(s_new + h) - R_of(s_new - h)) / (2 * h)
            slope = 1 - G * ((2 * s_new - 1) * R_of(s_new) + s_new * (s_new - 1) * dR)
            return s_new if slope > 0 else float("nan")
        s = 0.5 * s + 0.5 * s_new
    return float("nan")


def shape_factors(ba):
    """M_GRID 순서의 모양 배율 배열. b/a를 모르면 1."""
    if not (ba == ba and ba > 0):
        return np.ones(len(M_GRID))
    x = np.log(min(max(ba, 0.2), 5.0))
    lx = np.log(_SR)
    i = int(min(max(np.searchsorted(lx, x) - 1, 0), len(lx) - 2))
    w = (x - lx[i]) / (lx[i + 1] - lx[i])
    tab = _shape_table()
    return tab[:, i] * (1 - w) + tab[:, i + 1] * w


def block_bootstrap_se(series_list, stat, n_boot=400, seed=0):
    """프레임 순서의 여러 계열(같은 길이)을 블록째 다시 뽑아 stat(*계열)의 표준오차. 블록 길이 = max(5, n/20)."""
    n = len(series_list[0])
    if n < 10:
        return float("nan")
    L = max(5, n // 20)
    starts = np.arange(0, n - L + 1)
    rng = np.random.default_rng(seed)
    arrs = [np.asarray(sv, dtype=float) for sv in series_list]
    vals = []
    for _ in range(n_boot):
        idx = np.concatenate([np.arange(st, st + L) for st in rng.choice(starts, size=int(np.ceil(n / L)))])[:n]
        vals.append(stat(*[a[idx] for a in arrs]))
    vals = np.asarray(vals, dtype=float)
    return float(np.nanstd(vals, ddof=1))


def mu_water(t_c):
    """물 점도(Pa·s), Vogel형 근사 A·10^(B/(T − C)). 비(ratio) 보정용."""
    return 2.414e-5 * 10 ** (247.8 / (t_c + 273.15 - 140.0))


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def read_tracking(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    speed_col = next((c for c in rows[0].keys() if "速度" in c), None) if rows else None
    return rows, speed_col


def axis_of(flow):
    # (좌표 열 이름 끝자, 앞으로 갈 때 좌표가 커지면 +1)
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def layout_q(bubbles, walls, L, s_range, alpha, K=30):
    """기포 배치 계수 Q(I74, 독립 검토 3). bubbles: [(s, c, a², target)] 한 프레임(s = 흐름 방향 좌표, c = 가로 좌표,
    a² = 등가 반경²). walls = (c_lo, c_hi). L = 흐름 방향 반폭. s_range = 시야의 흐름 방향 범위. alpha = 그 프레임의 기공률
    (연속체 보정용. 띠 안의 기포 수로 세면 띠 끝의 불연속 때문에 격자에서 8% 틀렸다).
    Q_i(원 합, Lorentz 기준)를 빨리 수렴하는 꼴로 낸다: 기포 i 둘레 |Δs| ≤ L의 띠에 든 실제 기포와 그 측벽 거울상
    (두 벽 → 2W 주기, k = −K..K, 자기 거울상 포함)을 |Δc| ≤ C = (2K − 1)W까지 더하고, 연속체 보정
    α·[1 − (4/π)·arctan(L/C)]을 더한다(cos 2θ/r²의 연속체 적분: 원 0, 가로로 무한한 띠 −π, 정사각 0).
    직사각 격자·한 줄에서 L = W면 해석값과 0.2% 안(--selftest-q). 진단용 Q_noimg는 거울상 없는 반경 L의 원 합이다.
    반환: [(i, Q_i, Q_noimg_i)] — |Δs| ≤ L의 띠가 시야 안에 드는 target 기포만."""
    if not bubbles:
        return []
    arr = np.array([(b[0], b[1], b[2]) for b in bubbles], dtype=float)
    lo, hi = walls
    W = hi - lo
    C = (2 * K - 1) * W
    corr = 1 - 4 / math.pi * math.atan(L / C)
    out = []
    for i, b in enumerate(bubbles):
        if not b[3] or b[0] - L < s_range[0] or b[0] + L > s_range[1]:
            continue
        sub = arr[np.abs(arr[:, 0] - b[0]) <= L]
        src = [sub]
        for k in range(-K, K + 1):
            if k != 0:
                src.append(np.column_stack([sub[:, 0], sub[:, 1] + 2 * k * W, sub[:, 2]]))
            src.append(np.column_stack([sub[:, 0], 2 * lo - sub[:, 1] + 2 * k * W, sub[:, 2]]))
        src = np.vstack(src)
        ds, dc = src[:, 0] - b[0], src[:, 1] - b[1]
        r2 = ds * ds + dc * dc
        m = (r2 > 1e-9) & (np.abs(dc) <= C)
        q_img = float(np.sum(src[m, 2] * (ds[m] ** 2 - dc[m] ** 2) / r2[m] ** 2)) + alpha * corr
        ds0, dc0 = sub[:, 0] - b[0], sub[:, 1] - b[1]
        r20 = ds0 * ds0 + dc0 * dc0
        m0 = (r20 > 1e-9) & (r20 <= L * L)
        q_no = float(np.sum(sub[m0, 2] * (ds0[m0] ** 2 - dc0[m0] ** 2) / r20[m0] ** 2))
        out.append((i, q_img, q_no))
    return out


def _selftest_q():
    """한 줄·직사각 격자(해석값 있음)와 무작위 배치(기대값 0)로 layout_q를 점검한다."""
    def exact(a, lx, ly):
        tail = sum(1 / math.sinh(math.pi * m * ly / lx) ** 2 for m in range(1, 60) if math.pi * m * ly / lx < 300)
        return (math.pi * a / lx) ** 2 * (1 / 3 - 2 * tail) - math.pi * a * a / (lx * ly)
    a = 1.0
    for lx, ly, nrow, name in ((3.0, 20.0, 1, "가운데 한 줄(간격 3a, 폭 20a)"), (3.0, 5.236, 4, "직사각 격자 3a × 5.24a, 4줄"),
                               (5.236, 3.0, 4, "가로로 촘촘한 격자 5.24a × 3a, 4줄")):
        W = nrow * ly
        bub = [(j * lx, ly / 2 + kr * ly, a * a, True) for kr in range(nrow) for j in range(-150, 151)]
        res = layout_q(bub, (0.0, W), W, (-150 * lx, 150 * lx), math.pi * a * a / (lx * ly))
        q = np.mean([r[1] for r in res])
        print(f"{name}: Q = {q:.4f}, 해석값 {exact(a, lx, ly):.4f}, 거울상 없는 원 합 {np.mean([r[2] for r in res]):.4f}")
    # 판별 평면 기울기: 쌍극자 수준 정확식 대 1차식(검토 5의 Rayleigh 다중극 값과 비교)
    for lx, ly, ray in ((3.0, 10.47, 0.547), (3.0, 5.236, 0.661), (5.0, 3.0, 1.500)):
        al_l = math.pi * a * a / (lx * ly)
        q = exact(a, lx, ly)
        ex = ((1 - al_l) - q) / (1 - al_l + q)
        print(f"격자 {lx:g}a × {ly:g}a(α {al_l:.3f}, Q {q:+.3f}): 기울기 정확식 {ex:.3f}, 1차식 {1 - 2 * q / (1 - al_l):.3f}, Rayleigh(검토 5) {ray:.3f}")
    rng = np.random.default_rng(0)
    W, Ls, al = 20.0, 400.0, 0.1
    pts = []
    while len(pts) < int(al * W * Ls / math.pi):
        p = (rng.uniform(-Ls / 2, Ls / 2), rng.uniform(a, W - a))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= 4 * a * a for q in pts[-300:]):
            pts.append(p)
    res = layout_q([(x, y, a * a, True) for x, y in pts], (0.0, W), W, (-Ls / 2, Ls / 2), math.pi * a * a * len(pts) / (W * Ls))
    qi, qn = np.array([r[1] for r in res]), np.array([r[2] for r in res])
    print(f"고른 무작위(α {al}, {len(res)}개): Q = {qi.mean():.4f} ± {qi.std() / math.sqrt(len(qi)):.4f}(기대값은 0이 아니라 자기 거울상 때문에 약간 음수, 검토 5), "
          f"거울상 없는 원 합 {qn.mean():.4f}(띠 효과로 0과 α 사이)")


def contour_added_mass(per_bubble, pb_meta, masks_dir, flow, max_bubbles=2000, seed=0):
    """masks_dir의 라벨 지도에서 CSV 기포와 짝지은 윤곽의 C_A(I81). 반환: {per_bubble 번호: C_A}."""
    from added_mass_bem import added_mass_from_mask
    by_file = defaultdict(list)
    for k, (fname, cx, cy) in enumerate(pb_meta):
        if fname and cx == cx and cy == cy:
            by_file[os.path.splitext(fname)[0]].append(k)
    files = sorted(by_file)
    rng = np.random.default_rng(seed)
    rng.shuffle(files)
    out, n_try = {}, 0
    for stem in files:
        path = os.path.join(masks_dir, stem + ".npz")
        if not os.path.exists(path):
            continue
        inst = np.load(path)["inst"]
        lab = inst.ravel().astype(np.int64)
        cnt = np.bincount(lab)
        yy, xx = np.indices(inst.shape)
        sx = np.bincount(lab, weights=xx.ravel())
        sy = np.bincount(lab, weights=yy.ravel())
        ids = np.nonzero(cnt)[0]
        ids = ids[ids > 0]
        if not len(ids):
            continue
        cxs, cys = sx[ids] / cnt[ids], sy[ids] / cnt[ids]
        for k in by_file[stem]:
            A_csv = per_bubble[k][0]
            _, cx, cy = pb_meta[k]
            d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
            j = int(np.argmin(d2))
            if d2[j] > 9.0 or not 0.8 <= cnt[ids[j]] / A_csv <= 1.25:
                continue
            ys, xs = np.nonzero(inst == ids[j])
            crop = inst[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == ids[j]
            ca = added_mass_from_mask(crop, flow=flow)
            if ca == ca:
                out[k] = ca
            n_try += 1
        if n_try >= max_bubbles:
            break
    return out


def analyse_point(p, out_dir=None):
    H = _f(p["H_mm"]) * 1e-3
    jl, jg = _f(p["jL"]), _f(p["jG"])
    px = _f(p["px_mm"]) * 1e-3
    if px > 1e-3:
        raise SystemExit(f"{p.get('name', '')}: px_mm {px * 1e3:g}은 화소 하나의 크기(mm/px)여야 한다(예 0.02). 1보다 크면 px/mm로 넣은 것 같다.")
    fps = _f(p["fps"])
    roi = _f(p["roi_area_px"])
    mu = _f(p.get("mu"), float("nan"))
    if mu != mu:
        t0 = _f(p.get("T_tp"))
        mu = mu_water(t0) if t0 == t0 else WATER[0]
    rho = _f(p.get("rho"), WATER[1])
    sigma = _f(p.get("sigma"))
    if sigma != sigma:
        t0 = _f(p.get("T_tp"))
        sigma = 0.0757 - 1.665e-4 * (t0 if t0 == t0 else 20.0)
    k_fric = _f(p.get("friction_k"), 16.85)
    ax, sgn = axis_of((p.get("flow") or "up").strip())
    rows, speed_col = read_tracking(p["tracking_csv"])
    dp_l = _f(p["dp_l"])
    t_tp, t_l = _f(p.get("T_tp")), _f(p.get("T_l"))
    if t_tp == t_tp and t_l == t_l:
        dp_l *= mu_water(t_tp) / mu_water(t_l)           # 수온 1 K 차이 = 약 2.4 %
    E = _f(p["dp_tp"]) / dp_l - 1
    B = jg / jl
    U_P, J = jl * (1 + E), jl + jg                          # 압력이 말하는 Darcy 속도와 전체 플럭스(I91)
    s_stuck = _f(p.get("stuck_s"), 0.1)

    frames = defaultdict(list)
    a_ref = defaultdict(list)                               # 트랙별 화면 끝에 닿지 않은 프레임의 면적 → 잘린 기포의 참 크기(검토 6 #6)
    for r in rows:
        if r.get("イベント") == "気泡なし" or not r.get("トラックID"):
            frames[int(r["フレーム"])]
            continue
        frames[int(r["フレーム"])].append(r)
        if r.get("フレーム接触") != "1" and _f(r.get("面積(px)"), 0.0) > 0:
            a_ref[r["トラックID"]].append(_f(r.get("面積(px)")))
    a_ref = {tr: float(np.median(v)) for tr, v in a_ref.items()}

    alpha_t, flux_t = [], []
    fric_t = []                                             # 프레임별 {m: Σ (ROI 몫)·a·Ca^m}(I89·I90), 움직이는 기포만
    farea_t = []                                            # 프레임별 Σ (ROI 몫)·(a²/H)·Ca^(1/3): 굳은 막 미끄럼의 면적 항(검토 6)
    fricc_t = []                                            # 프레임별 원 공식(모양 배율 없음) 2/3 합
    use_shape = (p.get("shape_friction") or "1").strip() not in ("0", "no", "false")
    stuck_t, subgap_t = [], []                              # 멈춘 기포(s* < stuck_s)와 갭보다 작은 기포(d ≤ 2H)의 면적 비
    frame_rows = []
    vel_bub = []                                            # [A, d/H, u, b/a, 가로 위치] — 이동도 붕괴용(I91), 움직이고 잘리지 않은 기포
    n_cut = n_cut_fixed = 0
    cut_noref = 0.0
    w_area = w_ba = w_u = w_d = w_w = 0.0
    per_bubble = []                                         # (A, b/a, u) — 기포마다의 예측 y_track용
    pb_meta = []                                            # (파일 이름, 중심 X, 중심 Y) — 윤곽 C_A 짝짓기용
    cross = "X" if ax == "Y" else "Y"
    frame_bub = {}                                          # 프레임 → [(s, c, a², target, per_bubble 번호 또는 −1)]
    frame_alpha = {}
    for f, rs in frames.items():
        a_sum = flux = a_known = 0.0
        p_all = p_known = 0.0                               # Σ (ROI 몫)·a: 속도 없는 기포의 마찰 몫은 둘레 비로 채운다(검토 6 #16a)
        st_area = sub_area = 0.0
        fr = {m: 0.0 for m in M_GRID}
        fr_c = 0.0                                          # 모양 배율 없는(원) 2/3 합, 비교용
        fa = 0.0
        n_v = 0
        fb = frame_bub.setdefault(f, [])
        for r in rs:
            A_px = _f(r.get("面積(px)"), 0.0)
            A_roi = _f(r.get("ROI内面積(px)"), 0.0)
            cut = r.get("フレーム接触") == "1"
            A_true = A_px                                   # 잘린 기포는 같은 트랙의 온전한 면적(없으면 보이는 면적이라 마찰을 과대 계산)
            if cut:
                n_cut += 1
                ref = a_ref.get(r.get("トラックID"))
                if ref is None:
                    cut_noref += A_roi
                elif ref > A_px:
                    A_true = ref
                    n_cut_fixed += 1
            if A_roi <= 0:
                continue
            d = math.sqrt(4 * A_true / math.pi) * px
            if d <= 2 * H:
                sub_area += A_roi
                continue
            s_c, c_c = _f(r.get(f"中心{ax}")), _f(r.get(f"中心{cross}"))
            k_fb = -1
            if s_c == s_c and c_c == c_c:
                fb.append([s_c, c_c, A_true / math.pi, not cut, -1])
                k_fb = len(fb) - 1
            a_sum += A_roi
            a_r = math.sqrt(A_true / math.pi) * px
            w_roi = A_roi / A_true if A_true > 0 else 0.0
            p_all += w_roi * a_r
            v = _f(r.get(speed_col)) if speed_col else float("nan")
            ba_i = float("nan")                              # 잘리지 않은 기포의 b/a(마찰 모양 배율용)
            if not cut:
                ap0 = abs(_f(r.get(f"中心{ax}")) - _f(r.get(f"先端部{ax}"))) + EDGE_INSET_PX
                if ap0 > EDGE_INSET_PX:
                    ba_i = min(max(A_px / (math.pi * ap0 * ap0), 0.2), 5.0)
            moving = False
            if v == v:
                u = sgn * v * px * fps                       # m/s, 흐름 방향 +
                flux += A_roi * u
                a_known += A_roi
                p_known += w_roi * a_r
                if 2 * u / (U_P + J) < s_stuck:             # 멈춘(걸린) 기포: 마찰 법칙이 아니라 Darcy 힘을 받는다(I89)
                    st_area += A_roi
                else:
                    moving = True
                    ca = mu * u / sigma
                    sf = shape_factors(ba_i) if use_shape else None
                    for j, m in enumerate(M_GRID):
                        fr[m] += w_roi * a_r * ca ** m * (sf[j] if use_shape else 1.0)
                    fr_c += w_roi * a_r * ca ** (2 / 3)
                    fa += w_roi * a_r * a_r / H * ca ** (1 / 3)
                    n_v += 1
            if cut or v != v:
                continue
            kv = -1
            if moving:
                vel_bub.append([A_px, d / H, u, float("nan"), c_c])
                kv = len(vel_bub) - 1
            lead = _f(r.get(f"先端部{ax}"))
            cen = _f(r.get(f"中心{ax}"))
            a_px = abs(cen - lead) + EDGE_INSET_PX
            if not a_px > EDGE_INSET_PX:
                continue
            ba = min(max(A_px / (math.pi * a_px * a_px), 0.2), 5.0)
            w_area += A_px
            w_ba += A_px * ba
            w_u += A_px * u
            w_d += A_px * d
            w_w += A_px * 2 * A_px / (math.pi * a_px) * px
            per_bubble.append((A_px, ba, u))
            pb_meta.append((r.get("ファイル名", ""), _f(r.get("中心X")), _f(r.get("中心Y"))))
            if k_fb >= 0:
                fb[k_fb][4] = len(per_bubble) - 1
            if kv >= 0:
                vel_bub[kv][3] = ba
        alpha_t.append(a_sum / roi)
        frame_alpha[f] = a_sum / roi
        if a_sum == 0:                                      # 기포 없는 프레임은 0으로 센다(앞 판은 nan이 되어 평균에서 빠졌다)
            sc_a = sc_p = 1.0
        else:
            sc_a = a_sum / a_known if a_known > 0 else float("nan")   # 속도 없는 기포 몫: 면적 비(유량·멈춘 몫·면적 항)
            sc_p = p_all / p_known if p_known > 0 else float("nan")   # 마찰 둘레 항: 둘레 비(검토 6 #16a)
        flux_t.append(flux / roi * sc_a)
        fric_t.append({m: fr[m] * sc_p for m in M_GRID})
        fricc_t.append(fr_c * sc_p)
        farea_t.append(fa * sc_a)
        stuck_t.append(st_area / roi * sc_a)
        subgap_t.append(sub_area / roi)
        frame_rows.append((f, a_sum / roi, stuck_t[-1], flux_t[-1], fr[2 / 3] * sc_p, n_v))

    # 배치 계수 Q (I74): 측벽 거울상 포함 / 없음
    allb = [b for fb in frame_bub.values() for b in fb]
    walls = (_f(p.get("wall_lo_px")), _f(p.get("wall_hi_px")))
    if not (walls[0] == walls[0] and walls[1] == walls[1]) and allb:
        walls = (min(b[1] - math.sqrt(b[2]) for b in allb), max(b[1] + math.sqrt(b[2]) for b in allb))
        print(f"  [{p['name']}] 경고: 측벽 위치가 없어 기포 가로 끝으로 추정({walls[0]:.0f}~{walls[1]:.0f} px). 시야가 측벽을 포함하지 않으면 Q가 틀린다.")
    q_rows = {"img": [], "noimg": []}
    q_of = {}
    q_frame = {}
    if allb:
        s_rng = (min(b[0] - math.sqrt(b[2]) for b in allb), max(b[0] + math.sqrt(b[2]) for b in allb))
        W_px = walls[1] - walls[0]
        R = _f(p.get("q_radius_px"))
        if not R == R:
            R = min(W_px, (s_rng[1] - s_rng[0]) / 3)
        if R < W_px:
            print(f"  [{p['name']}] 경고: Q의 흐름 방향 반폭 L = {R:.0f} px < 채널 폭 {W_px:.0f} px. Q의 상대 오차는 약 "
                  f"0.6·e^(−2πL/W) = {0.6 * math.exp(-2 * math.pi * R / W_px):.1%}(검토 5의 격자 점검: L = W/3이면 7%, W/2면 2.5%). "
                  f"시야를 길게 찍거나 q_radius_px를 키운다.")
        for f, fb in frame_bub.items():
            bl = [(b[0], b[1], b[2], b[3]) for b in fb]
            for i, q, qn in layout_q(bl, walls, R, s_rng, frame_alpha[f]):
                qa, qw = q_frame.get(f, (0.0, 0.0))
                q_frame[f] = (qa + math.pi * fb[i][2] * q, qw + math.pi * fb[i][2])
                q_rows["img"].append((math.pi * fb[i][2], q))
                q_rows["noimg"].append((math.pi * fb[i][2], qn))
                if fb[i][4] >= 0:
                    q_of[fb[i][4]] = q
    def _wmean(v):
        return sum(A * q for A, q in v) / sum(A for A, _ in v) if v else float("nan")
    Q, Q_noimg = _wmean(q_rows["img"]), _wmean(q_rows["noimg"])

    alpha = float(np.mean(alpha_t)) if alpha_t else float("nan")
    jg_img = float(np.nanmean(flux_t)) if flux_t else float("nan")
    B_f = jg_img / jl
    kappa = (1 - alpha) / alpha if alpha > 0 else float("nan")
    s_bar, s_bar_t = B * kappa, B_f * kappa
    y = E * kappa
    x = 1 - s_bar
    # 표준오차: α·B_f·Q는 프레임 블록 부트스트랩, E는 입력 열, x·y는 전파
    fl = list(frames.keys())
    se_alpha = block_bootstrap_se([alpha_t], lambda a: a.mean())
    fx = np.array([v if v == v else 0.0 for v in flux_t])
    se_bf = block_bootstrap_se([fx], lambda v: v.mean()) / jl
    qa = np.array([q_frame.get(f, (0.0, 0.0))[0] for f in fl])
    qw = np.array([q_frame.get(f, (0.0, 0.0))[1] for f in fl])
    se_q = block_bootstrap_se([qa, qw], lambda u, w: u.sum() / w.sum() if w.sum() > 0 else np.nan) if qw.sum() > 0 else float("nan")
    rel2 = 0.0
    for col, ref in (("dp_tp_se", _f(p["dp_tp"])), ("dp_l_se", _f(p["dp_l"]))):
        v = _f(p.get(col))
        if v == v:
            rel2 += (v / ref) ** 2
    t_se = _f(p.get("T_se"))
    if t_se == t_se:
        rel2 += (0.024 * t_se) ** 2
    se_E = (1 + E) * math.sqrt(rel2) if rel2 > 0 else float("nan")
    b_rel = _f(p.get("B_rel_se"), 0.0)
    se_y = math.sqrt((kappa * (se_E if se_E == se_E else 0.0)) ** 2 + (E * se_alpha / alpha ** 2) ** 2) if se_alpha == se_alpha else float("nan")
    se_x = math.sqrt((B * se_alpha / alpha ** 2) ** 2 + (kappa * B * b_rel) ** 2) if se_alpha == se_alpha else float("nan")
    ba = w_ba / w_area if w_area else float("nan")
    u_b = w_u / w_area if w_area else float("nan")
    d_bar = w_d / w_area if w_area else float("nan")
    w_b = w_w / w_area if w_area else float("nan")
    u_l = jl / (1 - alpha)
    re_b = rho * H * H * u_b * u_b / (mu * w_b * u_l) if w_area else float("nan")
    lam = rho * u_l * H * H / (10 * mu * d_bar) if w_area else float("nan")
    # 기포마다: s_i = u_i/U_m(U_m = jL/(1 − α)), y_track = ΣA_i[1 + (b/a)_i(1 − s_i)]/ΣA_i (유량계 없이, 모양–이동도 상관 포함)
    y_track = (sum(A * (1 + ba_i * (1 - u / u_l)) for A, ba_i, u in per_bubble) / sum(A for A, _, _ in per_bubble)
               if per_bubble else float("nan"))
    # 윤곽 C_A(I81): masks_dir가 있으면 경계요소로, 같은 기포들의 b/a 추정기 값과 함께
    ca_of = {}
    mdir = (p.get("masks_dir") or "").strip()
    if mdir:
        mx = int(_f(p.get("ca_max_bubbles"), 2000))
        ca_of = contour_added_mass(per_bubble, pb_meta, mdir, (p.get("flow") or "up").strip(), max_bubbles=mx)
        if not ca_of:
            print(f"  [{p['name']}] 경고: {mdir}에서 CSV 기포와 짝지은 윤곽이 없다(파일 이름·좌표 확인).")
    wsum = sum(per_bubble[k][0] for k in ca_of)
    C_A = sum(per_bubble[k][0] * c for k, c in ca_of.items()) / wsum if ca_of else float("nan")
    ba_m = sum(per_bubble[k][0] * per_bubble[k][1] for k in ca_of) / wsum if ca_of else float("nan")
    shape = C_A if C_A == C_A else ba
    # 배치를 넣은 예측(I74, 독립 검토 5의 쌍극자 수준 정확식): ε = (1 + C)Q/2 + α(1 − C)/2,
    # 기울기 (C(1 − α) − ε)/(1 − α + ε), y = 1 + 기울기·x(측정 x로 정확). Q는 기체 유량 가중(속도가 없으면 면적 가중).
    qf = [(per_bubble[k][0] * per_bubble[k][2], q) for k, q in q_of.items() if per_bubble[k][2] == per_bubble[k][2]]
    Q_flux = (sum(w * q for w, q in qf) / sum(w for w, _ in qf)) if qf and sum(w for w, _ in qf) > 0 else float("nan")
    Q_s = Q_flux if Q_flux == Q_flux else Q
    eps = (1 + shape) * Q_s / 2 + alpha * (1 - shape) / 2
    slope = (shape * (1 - alpha) - eps) / (1 - alpha + eps)
    y_layout = 1 + slope * x
    qb = [(per_bubble[k], ca_of.get(k, per_bubble[k][1]), q) for k, q in q_of.items()]
    y_track_layout = (sum(A * (1 + (c_i - (1 + c_i) * ((1 + c_i) * q / 2 + alpha * (1 - c_i) / 2) / (1 - alpha)) * (1 - u / u_l))
                          for (A, _, u), c_i, q in qb) / sum(A for (A, _, _), _, _ in qb) if qb else float("nan"))
    # 속도 중심(I89~I91): 힘 균형 예측과 이동도 붕괴. 멈춘 기포는 Darcy 힘 α_멈춤·(2 + E + B)로 따로 센다(원형 국소장, 검토 6).
    roi_m2 = roi * px * px
    pref = (H / (12 * mu * jl)) * sigma / roi_m2
    P_m = {m: pref * float(np.nanmean([ft[m] for ft in fric_t])) if fric_t else float("nan") for m in M_GRID}
    P_area = pref * float(np.nanmean(farea_t)) if farea_t else float("nan")
    alpha_stuck = float(np.nanmean(stuck_t)) if stuck_t else float("nan")
    alpha_subgap = float(np.mean(subgap_t)) if subgap_t else float("nan")
    E_stuck = alpha_stuck * (2 + E + B)
    E_vel_moving = k_fric * P_m[2 / 3]
    E_vel = E_vel_moving + E_stuck
    k_fit = (E - E_stuck) / P_m[2 / 3] if P_m[2 / 3] > 0 else float("nan")
    P23_circle = pref * float(np.nanmean(fricc_t)) if fricc_t else float("nan")
    k_fit_circle = (E - E_stuck) / P23_circle if P23_circle > 0 else float("nan")
    ca_loc = mu * (U_P + J) / 2 / sigma
    W_side = walls[1] - walls[0] if walls[0] == walls[0] and walls[1] == walls[1] else float("nan")

    def s_wall(b):
        """측벽 자기 거울상을 뺀 이동도(I101 닫힌 식 + 접선 이동도, 검토 7 #13). 측벽 위치를 모르면 보정하지 않는다."""
        s_m = 2 * b[2] / (U_P + J)
        if not (W_side == W_side and W_side > 0 and b[4] == b[4]):
            return s_m
        return s_wall_correct(s_m, wall_G(math.sqrt(b[0] / math.pi), b[4] - walls[0], W_side))
    coll = {}
    for lo, hi in DH_BINS:
        tag = f"dH_{lo:g}_{hi:g}" if hi < 1e8 else f"dH_{lo:g}_up"
        sel = [b for b in vel_bub if lo <= b[1] < hi]
        wsel = sum(b[0] for b in sel)

        def _bin(fn):
            return sum(b[0] * fn(b) for b in sel) / wsel if wsel else float("nan")
        coll[f"s_star_{tag}"] = _bin(lambda b: 2 * b[2] / (U_P + J))
        # 모양 국소장(I91, 검토 6): U_loc = (U_P + C·J)/(1 + C), C = 기포의 b/a(없으면 원형 1)
        coll[f"s_starC_{tag}"] = _bin(lambda b: b[2] * (1 + (b[3] if b[3] == b[3] else 1.0)) / (U_P + (b[3] if b[3] == b[3] else 1.0) * J))
        coll[f"V_over_J_{tag}"] = _bin(lambda b: b[2] / J)
        coll[f"deltaB_{tag}"] = _bin(lambda b: 1.12 * ca_loc ** (1 / 3) * b[1])     # Booth 붕괴 좌표 δ_B
        sw = [(b[0], s_wall(b)) for b in sel]                                       # 측벽 자기 거울상을 뺀 이동도(I101)
        sw_ok = [(w_, v_) for w_, v_ in sw if v_ == v_]
        w_ok = sum(w_ for w_, _ in sw_ok)
        coll[f"s_starW_{tag}"] = sum(w_ * v_ for w_, v_ in sw_ok) / w_ok if w_ok else float("nan")
        coll[f"n_wall_skip_{tag}"] = len(sw) - len(sw_ok)                          # 벽에 너무 가깝거나 큰 기포(G > 0.25)라 뺀 수
    if out_dir and frame_rows:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in p["name"])
        with open(os.path.join(out_dir, f"frames_{safe}.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            # 순간 힘 균형(검토 6): E(t) = E_D(t) + (j_G − j_G,inst(t))/j_L, j_G,inst = ΣV_iA_i/(ROI 면적).
            # 시간 평균에서 둘째 항이 0이 된다(기체 보존). 멈춘 몫은 시간 평균 U_P로 근사했다.
            w.writerow(["frame", "alpha", "alpha_stuck", "j_G_inst", "sum_a_Ca23_m", "n_moving_with_speed", "E_D_frame", "E_vel_frame"])
            for f, al, ast, jgi, fs, nv in sorted(frame_rows):
                e_d = k_fric * pref * fs + ast * (2 + E + B)
                w.writerow([f, f"{al:.5f}", f"{ast:.5f}", f"{jgi:.6g}", f"{fs:.6g}", nv, f"{e_d:.6g}", f"{e_d + (jg - jgi) / jl:.6g}"])
    return {
        "name": p["name"], "H_mm": H * 1e3, "alpha": alpha, "B": B, "B_f": B_f, "s_bar": s_bar, "s_bar_T": s_bar_t,
        "E": E, "x": x, "y": y, "b_over_a": ba,
        "y_circle": 1 + x, "y_shape": 1 + ba * x, "y_track": y_track, "y_separated": 1.0, "y_homogeneous": 1 - x,
        "C_A": C_A, "b_over_a_matched": ba_m, "C_A_bubbles": len(ca_of), "y_shape_CA": 1 + C_A * x,
        "Q": Q, "Q_flux": Q_flux, "Q_noimg": Q_noimg, "Q_bubbles": len(q_rows["img"]), "eps": eps, "slope_pred": slope,
        "y_layout": y_layout, "y_track_layout": y_track_layout,
        "sigma": sigma, "friction_k": k_fric, "E_vel": E_vel, "E_vel_moving": E_vel_moving, "E_stuck": E_stuck, "k_fit": k_fit, "k_fit_circle": k_fit_circle,
        "alpha_stuck": alpha_stuck, "alpha_subgap": alpha_subgap, "P_area": P_area,
        "cut_obs": n_cut, "cut_fixed": n_cut_fixed, "cut_noref_alpha": cut_noref / (roi * len(alpha_t)) if alpha_t else float("nan"),
        "U_P": U_P, "J": J, **coll,
        **{f"P_m{m:.2f}": v for m, v in P_m.items()},
        "u_bubble": u_b, "d_bar_mm": d_bar * 1e3, "Re_B": re_b, "Lambda": lam, "frames": len(alpha_t),
        "se_alpha": se_alpha, "se_B_f": se_bf, "se_Q": se_q, "se_E": se_E, "se_x": se_x, "se_y": se_y,
    }


def plot(results, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink2, muted, grid, surf = "#52514e", "#8a8986", "#e6e5e1", "#fcfcfb"
    s1, s2, s3 = "#2a78d6", "#eb6834", "#1baf7a"
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    fig.patch.set_facecolor(surf); ax.set_facecolor(surf)
    xs = np.linspace(-1.1, 1.1, 50)
    ax.plot(xs, 1 + xs, color=s1, lw=2, label="circular closure y = 1 + x")
    ax.plot(xs, np.ones_like(xs), color=s2, lw=2, label="separated model y = 1")
    ax.plot(xs, 1 - xs, color=s3, lw=2, label="homogeneous y = 1 − x")
    for r in results:
        ax.plot(r["x"], r["y"], "o", ms=8, color="#0b0b0b", mec=surf, mew=2, zorder=5)
        ax.plot(r["x"], r["y_layout"], "o", ms=7, color=surf, mec=s1, mew=1.6, zorder=4)
        ax.plot([r["x"], r["x"]], [r["y"], r["y_layout"]], color=muted, lw=0.8, zorder=3)
        sa, se = r.get("se_alpha", float("nan")), r.get("se_E", float("nan"))
        a0, B, E = r["alpha"], r["B"], r["E"]
        if sa == sa and 0 < a0 - sa and a0 + sa < 1:              # α 오차: (1, 0)을 지나는 직선 위로
            k1, k2 = (1 - (a0 - sa)) / (a0 - sa), (1 - (a0 + sa)) / (a0 + sa)
            ax.plot([1 - B * k1, 1 - B * k2], [E * k1, E * k2], color=ink2, lw=1.1, zorder=4)
        if se == se:                                              # E 오차: 세로
            kap = (1 - a0) / a0
            ax.plot([r["x"], r["x"]], [r["y"] - se * kap, r["y"] + se * kap], color=ink2, lw=1.1, zorder=4)
        ax.annotate(r["name"], (r["x"], r["y"]), xytext=(5, 4), textcoords="offset points", fontsize=7.5, color=ink2)
    ax.plot([], [], "o", ms=8, color="#0b0b0b", label="measured (pressure + imaged α); bars: ±1 SE of E (vertical), α (toward (1, 0))")
    ax.plot([], [], "o", ms=7, color=surf, mec=s1, mew=1.6, label="closure with imaged shape (C_A or b/a) and layout Q")
    ax.set_xlabel("x = 1 − s̄  (s̄ = B(1 − α)/α)", color=ink2)
    ax.set_ylabel("y = E(1 − α)/α", color=ink2)
    ax.grid(color=grid, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_demo(out):
    """원형이 아닌 기포(b/a 1.5)가 s 1.5로 움직이는 합성 자료 3점. 계산이 입력을 되돌려 주는지 본다.
    기포는 겹치지 않게 고르게 놓아 배치 계수 Q ≈ 0이다(합성 E에는 배치 효과를 넣지 않았다).
    처음 6프레임은 라벨 지도(masks_k/f<프레임>.npz)도 써서 윤곽 C_A 경로를 점검한다(타원이라 C_A = b/a)."""
    rng = np.random.default_rng(1)
    os.makedirs(out, exist_ok=True)
    H, px, fps, W, Hpx = 0.3e-3, 0.02e-3, 500.0, 1000, 1000
    pts = []
    for k, (alpha_t, ba_t, s_t, jl) in enumerate(((0.10, 1.5, 1.5, 0.05), (0.15, 1.5, 1.2, 0.05), (0.20, 1.0, 0.8, 0.05))):
        rows = []
        u_l = jl / (1 - alpha_t)
        v_px = s_t * u_l / (px * fps)
        mdir = os.path.join(out, f"masks_{k}")
        os.makedirs(mdir, exist_ok=True)
        for f in range(60):
            area_sum = 0.0
            tid = 0
            placed = np.empty((0, 3))                       # 겹치지 않게(배치 계수 Q가 0 근처가 되도록) 놓는다
            inst = np.zeros((Hpx, W), np.int32) if f < 6 else None
            while area_sum < alpha_t * W * Hpx:
                a = rng.uniform(15, 30)                     # 흐름 방향 반축(px) → d > 2H(= 30 px)
                b = ba_t * a
                A = math.pi * a * b
                cx, cy = rng.uniform(b, W - b), rng.uniform(a, Hpx - a)
                rmax = max(a, b)
                if len(placed) and np.any(np.hypot(placed[:, 0] - cx, placed[:, 1] - cy) < placed[:, 2] + rmax):
                    continue
                placed = np.vstack([placed, (cx, cy, rmax)])
                if inst is not None:                        # 흐름(위) 방향 반축 a는 y, 가로 반축 b는 x
                    x0, x1 = int(max(cx - b - 1, 0)), int(min(cx + b + 2, W))
                    y0, y1 = int(max(cy - a - 1, 0)), int(min(cy + a + 2, Hpx))
                    yy, xx = np.mgrid[y0:y1, x0:x1]
                    m = ((xx - cx) / b) ** 2 + ((yy - cy) / a) ** 2 <= 1.0
                    inst[y0:y1, x0:x1][m] = tid + 1
                    A = float(m.sum())
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": tid, "イベント": "", "親トラックID": "",
                             "面積(px)": f"{A:.0f}", "ROI内面積(px)": f"{A:.0f}", "先端部X": f"{cx:.2f}", "先端部Y": f"{cy - a + EDGE_INSET_PX:.2f}",
                             "中心X": f"{cx:.2f}", "中心Y": f"{cy:.2f}", "上昇速度(px/frame)": f"{-v_px:.3f}",
                             "周長(px)": "", "フレーム接触": "0"})
                area_sum += A
                tid += 1
            if inst is not None:
                np.savez_compressed(os.path.join(mdir, f"f{f}.npz"), inst=inst)
        path = os.path.join(out, f"demo_tracking_{k}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        jg = s_t * alpha_t / (1 - alpha_t) * jl
        E = alpha_t / (1 - alpha_t) + ba_t * alpha_t * (1 - s_t) / (1 - alpha_t)
        pts.append({"name": f"demo{k} (b/a {ba_t}, s {s_t})", "H_mm": 0.3, "jL": jl, "jG": jg, "dp_tp": 100 * (1 + E), "dp_l": 100,
                    "tracking_csv": path, "roi_area_px": W * Hpx, "px_mm": px * 1e3, "fps": fps, "flow": "up", "mu": "", "rho": "",
                    "wall_lo_px": 0, "wall_hi_px": W, "masks_dir": mdir, "dp_tp_se": 1.0, "dp_l_se": 1.0, "T_se": 0.1, "B_rel_se": 0.02})
    pfile = os.path.join(out, "demo_points.csv")
    with open(pfile, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader(); w.writerows(pts)
    return pfile


def friction_fit(res, out_dir=None, n_boot=2000, seed=0):
    """운전점 여러 개로 마찰 법칙을 읽는다(I90, 독립 검토 6). 표적은 멈춘 기포 몫을 뺀 E_mov = E − E_stuck.
    (1) m = 2/3 고정(운전점 2개 이상): ln k = 평균(ln E_mov − ln P_2/3), 상대 표준오차 = 표준편차/√N.
    (2) 지수 맞춤(5개 이상): 격자의 m마다 로그 잔차 ln E_mov − ln P_m의 표준편차가 가장 작은 m. 운전점 부트스트랩으로 95% 구간.
    (3) 2항(5개 이상): E_mov = k1·P_2/3 + k2·P_area(둘레 항 + 굳은 막 미끄럼의 면적 항), 상대 잔차 최소, k ≥ 0, 부트스트랩 구간.
    m과 k는 거의 완전히 상관한다(검토 6: d/H 10·차압 ±13 Pa면 sd(m) 0.22, corr > 0.99).
    모든 운전점에 E의 표준오차(se_E, 점 표의 dp_tp_se·dp_l_se·T_se·B_rel_se에서)가 있으면 로그 공간에서 1/σ²_lnE로 가중한다
    (σ_lnE = se_E/E_mov). 하나라도 없으면 같은 무게다(검토 7 #17: 앞 판은 설명과 달리 가중하지 않았다). 요약의 weighted 열."""
    pts = [r for r in res if r.get("P_m0.67", float("nan")) > 0 and (r["E"] - r["E_stuck"]) > 0]
    n = len(pts)
    if n < 2:
        return None
    Em = np.array([r["E"] - r["E_stuck"] for r in pts])
    P = {m: np.array([r[f"P_m{m:.2f}"] for r in pts]) for m in M_GRID}
    S = np.array([r["P_area"] for r in pts])
    sig_ln = np.array([r.get("se_E", float("nan")) for r in pts], float) / Em
    weighted = bool(np.all(np.isfinite(sig_ln)) and np.all(sig_ln > 0))
    wts = 1 / sig_ln ** 2 if weighted else np.ones(n)

    def wstats(rr, w):
        mu_ = float(np.sum(w * rr) / np.sum(w))
        return mu_, float(math.sqrt(np.sum(w * (rr - mu_) ** 2) / np.sum(w)))
    r23 = np.log(Em) - np.log(P[2 / 3])
    mu23, _ = wstats(r23, wts)
    se23 = math.sqrt(float(np.sum(wts * (r23 - mu23) ** 2)) / ((n - 1) * float(np.sum(wts)))) if n > 1 else float("nan")
    out = {"n_points": n, "weighted": int(weighted), "k_m23": float(np.exp(mu23)), "k_m23_rel_se": se23}

    def best_m(idx):
        best = None
        for m in M_GRID:
            if np.any(P[m][idx] <= 0):
                continue
            rr = np.log(Em[idx]) - np.log(P[m][idx])
            mu_, sd = wstats(rr, wts[idx])
            if best is None or sd < best[1] - 1e-12:
                best = (m, sd, float(np.exp(mu_)))
        return best

    def two_term(idx):
        sw = np.sqrt(wts[idx])
        X = np.column_stack([P[2 / 3][idx] / Em[idx], S[idx] / Em[idx]]) * sw[:, None]
        y = sw.copy()
        sol = np.linalg.lstsq(X, y, rcond=None)[0]
        if sol[0] >= 0 and sol[1] >= 0:
            return float(sol[0]), float(sol[1])
        cands = []
        for j in (0, 1):
            xj = X[:, j]
            kk = [0.0, 0.0]
            kk[j] = max(float(xj @ y / (xj @ xj)), 0.0) if xj @ xj > 0 else 0.0
            cands.append((float(np.sum((y - X @ np.array(kk)) ** 2)), kk))
        return tuple(min(cands, key=lambda c: c[0])[1])

    grid = []
    for m in M_GRID:
        if np.all(P[m] > 0):
            rr = np.log(Em) - np.log(P[m])
            mu_, sd = wstats(rr, wts)
            grid.append((m, float(np.exp(mu_)), sd))
    if n >= 5:
        full = np.arange(n)
        mb = best_m(full)
        out.update(m_best=mb[0], k_at_m_best=mb[2], sd_log_at_m_best=mb[1])
        ok_s = bool(np.all(np.isfinite(S)))
        if ok_s:
            out["k1"], out["k2"] = two_term(full)
        rng = np.random.default_rng(seed)
        bm, b1, b2 = [], [], []
        for _ in range(n_boot):
            idx = rng.integers(0, n, n)
            if len(set(idx.tolist())) < 3:
                continue
            bb = best_m(idx)
            if bb:
                bm.append(bb[0])
            if ok_s:
                u1, u2 = two_term(idx)
                b1.append(u1)
                b2.append(u2)
        out["m_lo"], out["m_hi"] = (float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))) if bm else (float("nan"),) * 2
        if ok_s and b1:
            out["k1_lo"], out["k1_hi"] = float(np.percentile(b1, 2.5)), float(np.percentile(b1, 97.5))
            out["k2_lo"], out["k2_hi"] = float(np.percentile(b2, 2.5)), float(np.percentile(b2, 97.5))
    if out_dir:
        with open(os.path.join(out_dir, "friction_fit.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["m", "k", "sd_log_resid"])
            for m, k, sd in grid:
                w.writerow([f"{m:.3f}", f"{k:.5g}", f"{sd:.5f}"])
        with open(os.path.join(out_dir, "friction_fit_summary.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["key", "value"])
            for k, v in out.items():
                w.writerow([k, f"{v:.6g}" if isinstance(v, float) else v])
    return out


def _selftest_vel(out):
    """속도 경로 자가 시험(독립 검토 6 #16f). 정답을 아는 합성 추적 CSV 6점(j_L 0.02~0.2 m/s)으로 확인한다.
    (가) 잘린 기포는 같은 트랙의 온전한 크기로 센다  (나) 멈춘 기포는 마찰에서 빼고 α_멈춤·(2 + E + B)로 센다
    (다) 갭보다 작은 기포는 뺀다  (라) 기포 없는 프레임은 0으로 센다  (마) 프레임 CSV의 순간 식 평균 = E_vel
    (바) E를 16.85·P_2/3로 만들면 k_fit = 16.85, 지수 맞춤 2/3, 2항 (16.85, 0)
    (사) 30·P_0.5로 만들면 지수 맞춤 0.5  (아) 16.85·P_2/3 + 6.86·P_area로 만들면 2항 맞춤이 둘을 되돌린다
    (자) 타원 기포(b/a 1.5)의 마찰 합에 모양 배율이 들어간다(정답은 타원 다각형 직접 적분으로 따로 셈)
    (차) 측벽 자기 거울상 보정(I101)의 역산이 정확하다. 마찰 맞춤은 se_E가 있으면 가중한다."""
    os.makedirs(out, exist_ok=True)
    H, px, fps, mu, sig = 0.3e-3, 0.02e-3, 500.0, 1.0e-3, 0.072
    roi = 1000 * 1000
    pref0 = (H / (12 * mu)) * sig / (roi * px * px)
    nf = 10
    bubbles = [(0, 25.0, 0.5), (1, 40.0, 0.9), (2, 60.0, 1.2), (3, 90.0, 1.5), (4, 50.0, 1.0), (5, 35.0, 0.01), (6, 10.0, 1.0)]
    # 트랙 4는 첫 프레임에서 왼쪽 끝에 반만 보인다(잘림), 5는 멈춘 기포, 6은 갭보다 작다(d 20 px < 2H 30 px).
    truth = {}
    for jl in (0.02, 0.03, 0.05, 0.08, 0.12, 0.2):
        rows = []
        sums = {m: 0.0 for m in M_GRID}
        sarea = st = sub = 0.0
        jgi = []
        for f in range(nf + 1):
            if f == nf:
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": "", "イベント": "気泡なし"})
                jgi.append(0.0)
                continue
            flux = 0.0
            for k, r, s in bubbles:
                vis = 0.5 if (k == 4 and f == 0) else 1.0
                A_vis = math.pi * r * r * vis
                u = s * jl
                cx = 100.0 + 130.0 * k
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": k, "イベント": "", "面積(px)": f"{A_vis:.6f}",
                             "ROI内面積(px)": f"{A_vis:.6f}", "先端部X": f"{cx + r - EDGE_INSET_PX:.3f}", "先端部Y": "500", "中心X": f"{cx:.3f}",
                             "中心Y": "500", "速度X(px/frame)": f"{u / (px * fps):.9f}", "フレーム接触": "1" if vis < 1 else "0"})
                if 2 * r * px <= 2 * H:
                    sub += A_vis / roi
                    continue
                flux += A_vis * u
                if k == 5:
                    st += A_vis / roi
                    continue
                ca = mu * u / sig
                for m in M_GRID:
                    sums[m] += vis * r * px * ca ** m
                sarea += vis * (r * px) ** 2 / H * ca ** (1 / 3)
            jgi.append(flux / roi)
        path = os.path.join(out, f"selftest_tracking_{jl:g}.csv")
        keys = list(rows[0].keys())
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        nfr = nf + 1
        truth[jl] = dict(path=path, P={m: pref0 / jl * v / nfr for m, v in sums.items()}, Parea=pref0 / jl * sarea / nfr,
                         st=st / nfr, sub=sub / nfr, jg=float(np.mean(jgi)))
    fails = []

    def check(name, got, want, tol):
        ok = abs(got - want) <= tol * max(abs(want), 1e-12)
        print(f"  {'통과' if ok else '실패'}  {name}: 도구 {got:.6g}, 정답 {want:.6g}")
        if not ok:
            fails.append(name)

    def run(tag, emov):
        pts = []
        for jl, tr in truth.items():
            B = tr["jg"] / jl
            E = (emov(tr) + tr["st"] * (2 + B)) / (1 - tr["st"])
            pts.append({"name": f"{tag}_{jl:g}", "H_mm": H * 1e3, "jL": jl, "jG": tr["jg"], "dp_tp": 100 * (1 + E), "dp_l": 100,
                        "tracking_csv": tr["path"], "roi_area_px": roi, "px_mm": px * 1e3, "fps": fps, "flow": "right",
                        "mu": mu, "rho": 998.0, "sigma": sig, "wall_lo_px": 0, "wall_hi_px": 1000, "q_radius_px": 1000})
        return [analyse_point(q, out) for q in pts]

    print("속도 경로 자가 시험(합성 6점, 정답을 앎)")
    resA = run("A", lambda tr: 16.85 * tr["P"][2 / 3])
    for r, (jl, tr) in zip(resA, truth.items()):
        check(f"(가)(라) j_L {jl:g}: P_2/3(잘린 기포는 온전한 크기, 빈 프레임은 0)", r["P_m0.67"], tr["P"][2 / 3], 1e-6)
        check(f"(나) j_L {jl:g}: 멈춘 기포 α", r["alpha_stuck"], tr["st"], 1e-6)
        check(f"(다) j_L {jl:g}: 갭보다 작은 기포 α", r["alpha_subgap"], tr["sub"], 1e-6)
        check(f"(바) j_L {jl:g}: k_fit", r["k_fit"], 16.85, 1e-6)
        check(f"(바) j_L {jl:g}: E_vel = E", r["E_vel"], r["E"], 1e-6)
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in r["name"])
        with open(os.path.join(out, f"frames_{safe}.csv"), encoding="utf-8") as fh:
            ev = [float(q["E_vel_frame"]) for q in csv.DictReader(fh)]
        check(f"(마) j_L {jl:g}: 프레임 순간 식의 평균 = E_vel", float(np.mean(ev)), r["E_vel"], 1e-4)
    tr0 = truth[0.02]
    old = (math.sqrt(0.5) - 0.5) * 50 * px * (mu * 0.02 / sig) ** (2 / 3) * pref0 / 0.02 / (nf + 1)
    print(f"  참고: 앞 판(보이는 면적의 등가 반경)이면 j_L 0.02의 P_2/3이 {old / tr0['P'][2 / 3]:+.1%} 컸다(잘린 관측 1개).")
    fa = friction_fit(resA)
    check("(바) 지수 맞춤 m", fa["m_best"], 2 / 3, 1e-9)
    for s_true, a_px, y0 in ((0.4, 30.0, 500.0), (1.5, 200.0, 500.0), (1.5, 200.0, 260.0), (0.8, 60.0, 80.0)):
        G = wall_G(a_px, y0, 1000.0)
        dl = 2 / s_true - 1
        s_meas = s_true * (1 - (1 + dl) / (1 + 2 / 3 * dl) * (s_true - 1) * G)
        check(f"(차) 측벽 거울상 역산 s {s_true}, a {a_px:g} px, y₀ {y0:g}/1000 px(측정 {s_meas:.4f})", s_wall_correct(s_meas, G), s_true, 1e-9)
    for s_true, G in ((1.6, 0.5), (1.5, 0.7), (1.9, 0.4)):                 # 근이 둘인 영역은 NaN이어야 한다(검토 8 #10)
        dl = 2 / s_true - 1
        s_meas = s_true * (1 - (1 + dl) / (1 + 2 / 3 * dl) * (s_true - 1) * G)
        got = s_wall_correct(s_meas, G)
        check(f"(차) G {G:g}·참 s {s_true}: 풀지 않음(NaN)", 1.0 if got != got else 0.0, 1.0, 1e-12)
    fw = friction_fit([dict(r, se_E=0.02 * (1 + i) * r["E"]) for i, r in enumerate(resA)])
    check("(바) se_E가 있으면 가중 맞춤(weighted 1)", float(fw["weighted"]), 1.0, 1e-9)
    check("(바) 가중 맞춤의 지수 m", fw["m_best"], 2 / 3, 1e-9)
    check("(바) 가중 맞춤의 2항 k1", fw["k1"], 16.85, 1e-6)
    check("(바) 2항 k1", fa["k1"], 16.85, 1e-6)
    check("(바) 2항 k2(0이어야 함)", fa["k2"] + 1.0, 1.0, 1e-6)
    fb = friction_fit(run("B", lambda tr: 30.0 * tr["P"][0.5]))
    check("(사) 지수 맞춤 m", fb["m_best"], 0.5, 1e-9)
    check("(사) 그 m에서 k", fb["k_at_m_best"], 30.0, 1e-6)
    fc = friction_fit(run("C", lambda tr: 16.85 * tr["P"][2 / 3] + 6.86 * tr["Parea"]))
    check("(아) 2항 k1", fc["k1"], 16.85, 1e-5)
    check("(아) 2항 k2", fc["k2"], 6.86, 1e-5)
    # (자) 타원 기포: 흐름 방향 반축 a = |先端部 − 中心| + 0.5 px(추적기 규약), b/a = 면적/(πa²). 정답 배율은 표 대신 다각형에서 직접 적분한다.
    q = 1.5
    tt = np.linspace(0.0, 2 * np.pi, 20000, endpoint=False)
    ex, ey = np.cos(tt), q * np.sin(tt)
    dx, dy = np.roll(ex, -1) - ex, np.roll(ey, -1) - ey
    ds = np.hypot(dx, dy)
    tc = np.linspace(-np.pi / 2, np.pi / 2, 20001)
    cc = np.cos(tc) ** (5 / 3)
    S23 = float(np.sum(np.clip(dy / ds, 0.0, None) ** (5 / 3) * ds)) / (float(np.sum(cc[1:] + cc[:-1])) * (tc[1] - tc[0]) / 2 * math.sqrt(q))
    for jl in (0.03, 0.12):
        rows, s23, flux = [], 0.0, 0.0
        for f in range(nf):
            for k, r, s in bubbles[:4]:
                u = s * jl
                cx = 100.0 + 200.0 * k
                rows.append({"ファイル名": f"f{f}.png", "フレーム": f, "トラックID": k, "イベント": "", "面積(px)": f"{math.pi * r * r:.6f}",
                             "ROI内面積(px)": f"{math.pi * r * r:.6f}", "先端部X": f"{cx + r / math.sqrt(q) - EDGE_INSET_PX:.6f}", "先端部Y": "500",
                             "中心X": f"{cx:.3f}", "中心Y": "500", "速度X(px/frame)": f"{u / (px * fps):.9f}", "フレーム接触": "0"})
                s23 += r * px * (mu * u / sig) ** (2 / 3) * S23
                flux += math.pi * r * r * u
        path = os.path.join(out, f"selftest_ellipse_{jl:g}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        E = 16.85 * pref0 / jl * s23 / nf
        for sf in ("1", "0"):
            rr = analyse_point({"name": f"D_{jl:g}_{sf}", "H_mm": H * 1e3, "jL": jl, "jG": flux / roi / nf, "dp_tp": 100 * (1 + E),
                                "dp_l": 100, "tracking_csv": path, "roi_area_px": roi, "px_mm": px * 1e3, "fps": fps, "flow": "right",
                                "mu": mu, "rho": 998.0, "sigma": sig, "wall_lo_px": 0, "wall_hi_px": 1000, "q_radius_px": 1000,
                                "shape_friction": sf}, out)
            check(f"(자) j_L {jl:g}, b/a {q:g}: k_fit(모양 배율 {'켬' if sf == '1' else '끔'})", rr["k_fit"],
                  16.85 if sf == "1" else 16.85 * S23, 1e-3)
            check(f"(자) j_L {jl:g}: k_fit_circle = 16.85·S(1.5) = 16.85·{S23:.4f}", rr["k_fit_circle"], 16.85 * S23, 1e-3)
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("points", nargs="?")
    ap.add_argument("--out", default="plane_out")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--selftest-q", action="store_true")
    ap.add_argument("--selftest-vel", action="store_true")
    a = ap.parse_args()
    if a.selftest_q:
        _selftest_q()
        return
    if a.selftest_vel:
        raise SystemExit(0 if _selftest_vel(os.path.join(a.out, "selftest_vel")) else 1)
    os.makedirs(a.out, exist_ok=True)
    pfile = make_demo(a.out) if a.demo else a.points
    if a.demo:
        print("데모: 합성 ΔP는 공극률 폐합으로 만든 값이라 힘 균형의 k·지수 맞춤은 의미가 없다(경로 점검용).")
    with open(pfile, encoding="utf-8-sig", newline="") as fh:
        pts = list(csv.DictReader(fh))
    res = [analyse_point(p, a.out) for p in pts]
    keys = list(res[0].keys())
    with open(os.path.join(a.out, "plane_points.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in res:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})
    plot(res, os.path.join(a.out, "plane.png"))
    for r in res:
        print(f"{r['name']}: α {r['alpha']:.3f}, b/a {r['b_over_a']:.2f}, s̄ {r['s_bar']:.2f} (추적 {r['s_bar_T']:.2f}), "
              f"x {r['x']:.2f}, y {r['y']:.2f} (원형 {r['y_circle']:.2f}, 모양 {r['y_shape']:.2f}, 기포별 {r['y_track']:.2f}), Re_B {r['Re_B']:.2f}, Λ {r['Lambda']:.3f}")
        print(f"    표준오차: α {r['se_alpha']:.4f}, B_f {r['se_B_f']:.4f}, Q {r['se_Q']:.4f}, E {r['se_E']:.4f}, x {r['se_x']:.3f}, y {r['se_y']:.3f}")
        if r["C_A_bubbles"]:
            print(f"    윤곽 C_A {r['C_A']:.2f}(같은 {r['C_A_bubbles']}개 기포의 b/a 추정기 {r['b_over_a_matched']:.2f})")
        print(f"    배치 Q {r['Q']:.3f}(유량 가중 {r['Q_flux']:.3f}, 거울상 없음 {r['Q_noimg']:.3f}, 기포 {r['Q_bubbles']}개), "
              f"예측 기울기 {r['slope_pred']:.2f}(정확식), 배치 넣은 예측 y {r['y_layout']:.2f}(기포별 1차 {r['y_track_layout']:.2f})")
        sc = "  ".join(f"{k[10:]} {v:.2f}/{r['V_over_J' + k[6:]]:.2f}" for k, v in r.items() if k.startswith("s_star_") and v == v)
        print(f"    속도 중심: 힘 균형 예측 E_vel {r['E_vel']:.3f}(움직이는 기포 {r['E_vel_moving']:.3f}, k {r['friction_k']:.2f} + 멈춘 기포 {r['E_stuck']:.3f}) "
              f"대 측정 E {r['E']:.3f} → 압력이 말하는 k {r['k_fit']:.1f}. 이동도 붕괴 s* = 2u/(U_P + J) / V/J: {sc}")
        print(f"    계통(검토 6): 멈춘 기포 α {r['alpha_stuck']:.4f}, 갭보다 작은 기포(d ≤ 2H, 마찰에서 뺌) α {r['alpha_subgap']:.4f}, "
              f"화면 끝에서 잘린 관측 {r['cut_obs']}개 중 같은 트랙의 온전한 크기로 고친 것 {r['cut_fixed']}개, "
              f"온전한 크기가 없는 잘린 기포 α {r['cut_noref_alpha']:.4f}(마찰 과대)")
    fit = friction_fit(res, a.out)
    if fit:
        print(f"마찰 법칙(운전점 {fit['n_points']}개, 표적 E − E_stuck): m = 2/3 고정 k = {fit['k_m23']:.3g}(상대 표준오차 {fit['k_m23_rel_se']:.0%}). "
              "17 근처면 깨끗한 막, 21~43이면 잘 녹는 계면활성제(같은 지수, 1.26~2.52배). "
              "오염으로 읽기 전에 잘린·멈춘·작은 기포, 쐐기, 기울기를 먼저 본다(I90).")
        if "m_best" in fit:
            print(f"    지수 맞춤: m = {fit['m_best']:.2f} [95% {fit['m_lo']:.2f}~{fit['m_hi']:.2f}], k = {fit['k_at_m_best']:.3g}. "
                  "m과 k는 거의 완전히 상관한다. 2/3과 1/3을 가르려면 차압 ±2~5 Pa, d/H ≤ 10, 넓은 j_L이 필요하다(검토 6).")
            if "k1" in fit:
                print(f"    2항 맞춤: k1(둘레 a·Ca^(2/3)) = {fit['k1']:.3g} [{fit.get('k1_lo', float('nan')):.3g}~{fit.get('k1_hi', float('nan')):.3g}], "
                      f"k2(면적 a²/H·Ca^(1/3)) = {fit['k2']:.3g} [{fit.get('k2_lo', float('nan')):.3g}~{fit.get('k2_hi', float('nan')):.3g}]. "
                      "깨끗하면 k1 ≈ 16.85·k2 ≈ 0, 녹는 계면활성제면 k1 21~43·k2 ≈ 0, 굳은 막 미끄럼이면 k1 ≈ 23·k2 ≈ 6.9"
                      "(우리 유속에서는 기포가 거의 멈춘다).")
        else:
            print("    운전점이 5개 미만이라 지수·2항 맞춤은 하지 않았다(검토 6).")

if __name__ == "__main__":
    main()

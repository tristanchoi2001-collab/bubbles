# 주제 3: 압력 강하 예측과 영상 변수 (2026-10-23, 문헌 조사 에이전트 3)

범위: 갭 H = 0.3, 0.7, 1, 3, 7 mm 평평한 유로(공기-물로 가정). 확인 수준 표기는 공통 지침 4장(C+F, C+A, C, U).
계산 스크립트(세션 scratchpad, 저장소 밖): `lit3/scripts/bretherton.py`(Bretherton 상수 재계산), `lit3/scripts/q6_ratio.py`(6장 표).

## 0. 요약
1. **메니스커스 계수는 문헌으로 확정된다.** 평면(갭) 동적 메니스커스의 압력 점프 보정은 앞쪽 β1 = 3.88, 뒤쪽 β2 = −1.13이다(단위 (2σ/H)·Ca_n^(2/3), Ca_n = 법선 속도 기준) [P1 Booth 2023 C+F, P2 Cantat 2013 C+F]. 내가 Bretherton 식을 다시 풀어도 3.877 / 1.129였다.
   - Bretherton 초록의 "3.58(3Ca)^(2/3)σ/r"(원관)은 사실상 앞쪽만의 값이다. 뒤쪽까지 넣으면 원관 총합은 4.75~4.81이다 [P2].
   - 이전 세션이 적은 "뒤쪽 0.94"는 뒤쪽 계수가 아니다. 0.94는 Cantat의 굳은 계면 액막 항 계수 ζ다.
2. **계수 k(원형 팬케이크, 깨끗한 계면) = 2.68.** dP/dx_b = k·σ·Ca_V^(2/3)·Γ/H, k = (β1 − β2)·2·1.6827/(2π) [P1의 적분 √πΓ(4/3)/Γ(11/6) = 1.6827, P2의 "법선 속도 모델"]. "투영 길이 모델"을 쓰면 3.19 [P2]. 길쭉한 슬러그는 Γ 대신 |n_x|^(5/3)로 가중한 둘레 밀도를 써야 한다.
3. **계수의 불확실성이 크다.** 계면 오염(계면활성 물질)으로 압력 점프가 최대 4^(2/3) = 2.52배(β1 → 9.78, β2 → −2.85) [P3 Booth 2025, P4 Booth 학위논문 C+F]. 힘으로 계산한 Cantat는 1.26~1.38배 + 면적에 비례하는 액막 전단 항(Ca^(1/3))을 준다 [P2]. 폼·라멜라 실험은 이론의 2~4배, 지수 0.5~0.6을 자주 보인다 [P2, F3 Terriac 2006 C+F, F4 Raufaste 2009 C+A]. Taylor 흐름 실험도 깨끗한 CFD의 약 2.4배였다(a = 0.17 vs 0.07) [T6 Kreutzer 2005, 원문 수치는 T7 Warnier 2010 C+F 경유].
4. **"한 계수, 두 관측" 중 속도 쪽은 이미 발표됐다.** `estimates_microgap.md` 5장의 V/j = 2/(1 + 0.18c(H/d)Ca^(−1/3))는 Booth, Griffiths & Howell(2023 JFM)의 식 Ub^(2/3) = δ(2 − Ub), δ = 1.12·Ca^(1/3)/(H/d)와 같다 [P1]. Princeton 실험(실리콘유, Ca 3~7×10⁻⁴)과 맞았다 [P4]. Reichert 외(2019)도 같은 식(계수 1.20)을 냈다 [P4].
5. **새로움이 남는 곳: 기포 무리의 압력 강하와 운동학 폐합.** 위 Hele-Shaw 문헌은 기포 속도만 다루고, 유로 전체의 압력 강하는 계산하지 않았다(Booth 학위논문의 "pressure drop" 35회가 모두 메니스커스 단위, 4장 기록). 여기서 유도한 힘 균형(3장)은 다음을 준다.
   - −dP/dx = 12μ·j_L/H² + (1/(A·H))·ΣF_b (Hele-Shaw 극한, 정확한 운동량 균형).
   - 원형 팬케이크는 F_b = 12πμR²(2U − V)/H이므로 **증가분 = (12μ/H²)·α·(2U − V̄)**. 마찰 법칙 없이 영상(α, V̄)과 유량계로 압력 강하를 예측한다.
   - 같은 증가분을 메니스커스 법칙(k, Γ, Ca_V)으로도 계산할 수 있다. 두 경로와 측정 ΔP를 비교하는 것이 시험 가능한 주장이 된다.
6. **0.3·0.7 mm가 이 시험에 가장 알맞다.** Re_H·H/d가 1~100(0.3 mm, j ≤ 0.2 m/s에서 1~30)으로 작아 Darcy-Bretherton 근사가 가장 잘 맞는다. 3 mm는 5~1700, 7 mm는 양쪽 벽에 닿는 팬케이크가 거의 없다(Bo_H = 6.6).
7. **이전 추정의 비율 R은 분해 방식에 따라 다르다.** 같은 조건(1 mm, d/H = 3, α = 0.3, j = 0.05 m/s)에서 총 dP/dx는 873(에너지 분해, 이전 세션) vs 881 Pa/m(힘 분해)로 거의 같다. 그러나 "메니스커스 항/액체 마찰"은 0.13 vs 0.70이다. 비율 대신 φ_L² − 1(액체 단독 대비 증가분)로 말해야 한다(6장).
8. **상관식 쪽**: 좁은 직사각 갭의 직접 근거는 Lee & Lee(2001, 갭 0.4~4 mm, 폭 20 mm, 수평, 공기-물)다 [K3]. Mishima & Hibiki(1996)는 C = 21(1 − e^(−0.319D[mm]))(원관 1~4 mm) [K2, 2차 인용]. 갭이 좁을수록 C가 작아진다(5~100 µm 갭은 Chisholm보다 작은 배수) [K12]. 정확한 계수를 원문으로 확인하지 못한 식이 많다(1장 표).

## 1. 문헌 표

### 1-A. 가장 가까운 문헌: Hele-Shaw 기포 운동과 메니스커스 계수
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| P1 | Booth, Griffiths, Howell (2023) | Circular bubbles in a Hele-Shaw channel: a Hele-Shaw Newton's cradle | J Fluid Mech 954:A21 | 10.1017/jfm.2022.1008 | 이론, 팬케이크 원형 기포, Ca = O(ε³), ε = H/(2R) | 경계조건 p_b − p = 2σ/H + (2σ/H)β(Ca_n)Ca_n^(2/3) + (π/4)σκ, β1 ≈ 3.88(전진), β2 ≈ −1.13(후퇴). 힘 균형 → Ub^(2/3) = δ(2 − Ub), δ = 1.12·Ca^(1/3)/ε. δ > 1이면 액체보다 빠르고 δ < 1이면 느림. 여러 기포는 쌍을 이루며 뭉침 | 이전 세션의 C0 모델과 같은 식(선행). 기포 크기별 V/U에서 β를 거꾸로 구하는 근거. 채널 압력 강하는 다루지 않음 | C+F |
| P2 | Cantat (2013) | Liquid meniscus friction on a wet plate: Bubbles, lamellae, and foams | Phys Fluids 25(3):031303 | 10.1063/1.4793544 | 리뷰 + 이론, 메니스커스 1개당 힘 | 벽 1개, 단위 길이당 힘: 깨끗 f^f = 3.84γCa^(2/3), f^r = −1.1γCa^(2/3)(합 ξ = 4.94). 굳은 계면 미끄럼 ξ = 6.82 + 0.94γCa^(1/3)(ℓ/r_m), 구름 ξ = 6.22. 방향: 투영 길이(cosθ) vs 법선 속도((cosθ)^(5/3)) 모델, 실험으로 구별 못 함. 3D 폼 실험은 이론의 약 4배. Ca^(2/3)는 We ≈ 10까지 성립. 원관 1 mm, Ca 10⁻³에서 기포 1개 = 관 12 mm의 Poiseuille 손실 | k의 직접 근거(앞·뒤 계수, 투영, 계면 조건). 굳은 계면이면 면적 비례 항이 생김 | C+F (arXiv 1305.0569) |
| P3 | Booth, Griffiths, Howell (2025) | The motion of a surfactant-laden bubble in a channel or a Hele-Shaw cell | J Fluid Mech 1025:A12 | 10.1017/jfm.2025.10951 | 이론, 탄성 매개변수 1개 | 계면활성제가 있으면 앞·뒤 메니스커스 압력 강하가 최대 4^(2/3)배. 같은 조건에서 더 느리게 움직임 | 물(오염 가능)의 계수 상한 | C+A |
| P4 | Booth (2024) | The motion of bubbles in Hele-Shaw cells (DPhil thesis) | Univ. Oxford (ORA) | - | 이론 + Princeton 실험(K. Wu, 실리콘유) | 실험 Ca = 3.3~6.6×10⁻⁴, ε = 0.01~0.25에서 Ub(δ)와 잘 맞음(δ < 1 포함). 포화 계면 극한 h̃0 = 3.369, β1 = 9.78, β2 = −2.85. Reichert 외(2019)는 같은 식을 계수 1.20으로 얻음. "pressure drop" 언급 35회 모두 메니스커스 단위 | 선행 연구의 범위 확인(채널 ΔP 없음) | C+F (URL ora.ox.ac.uk uuid:2712a3fb-d5de-4899-8051-a9f42695b393) |
| P5 | Park, Homsy (1984) | Two-phase displacement in Hele Shaw cells: theory | J Fluid Mech 139:291-308 | 10.1017/s0022112084000367 | 정합 점근, 작은 Ca·ε | 유효 경계조건의 형태와 상수 결정(앞쪽 3.88은 P1 경유) | β1의 원출처 | C+A |
| P6 | Reinelt (1987) | The effect of thin film variations and transverse curvature on the shape of fingers in a Hele-Shaw cell | Phys Fluids 30(9):2617-2623 | 10.1063/1.866105 | 이론 | 경계조건이 μU_n/T(법선 속도)에 의존 | 투영(법선 속도) 가정의 근거 | C+A |
| P7 | Burgess, Foster (1990) | Analysis of the boundary conditions for a Hele-Shaw bubble | Phys Fluids A 2(7):1105-1117 | 10.1063/1.857610 | 이론 | 기포 옆면 작은 영역에서 막 ∝ ε^(2/5)Ca^(4/5)(나머지는 Ca^(2/3)). 뒤쪽 계수는 앞쪽이 깐 막에 따라 달라짐(F 함수) | 투영 모델의 한계(옆면), 비원형 기포의 뒤쪽 계수 | C+A |
| P8 | Reichert, Cantat, Jullien (2019) | Predicting droplet velocity in a Hele-Shaw cell | Phys Rev Fluids 4(11):113602 | 10.1103/physrevfluids.4.113602 | 실험 + 모델(액적) | P1과 같은 속도식(계수 1.20)을 소산 균형으로 얻음(P4 기준) | 운동학으로 마찰을 읽는 선례 | C |
| P9 | Reichert 외 (2018) | Topography of the lubrication film under a pancake droplet travelling in a Hele-Shaw cell | J Fluid Mech 850:708-732 | 10.1017/jfm.2018.457 | RICM 측정(nm 정밀도) | 앞쪽은 표면장력 구배 무시 가능, 뒤쪽은 계면활성제 축적으로 막이 두꺼워짐. 옆면에 골(ravine) | 앞·뒤 계수가 계면 상태에 따라 달라짐 | C+A |
| P10 | Baué 외 (2025) | Droplet velocity in both limits of low and high soluble surfactants in a Hele-Shaw cell | J Fluid Mech 1009:A23 | 10.1017/jfm.2025.167 | 실험 + 이론, 기름 액적 | 잘 녹는 계면활성제: 속도가 반지름에 따라 증가(응력 없는 극한). 덜 녹는 것: 감소(비압축 극한). 맞춤 없이 일치 | **크기별 V(d)의 기울기로 계면 상태 판별** 가능 | C+A |
| P11 | Park, Maruvada, Yoon (1994) | The influence of surfactant on the bubble motion in Hele-Shaw cells | Phys Fluids 6(10):3267-3275 | 10.1063/1.868059 | 실험 | 실리콘유 속 공기 기포는 Taylor-Saffman에 가까움. SDS 물방울은 속도가 10배 작음. Kopf-Sill & Homsy의 느린 기포는 오염 탓 | 물 실험에서 오염 위험 | C+A |
| P12 | Maruvada, Park (1996) | Retarded motion of bubbles in Hele-Shaw cells | Phys Fluids 8(12):3229-3233 | 10.1063/1.869113 | 이론, 굳은 계면 | 굳은 계면이면 속도가 한 자릿수 감소 가능 | 계면 상태가 C0를 크게 바꿈 | C+A |
| P13 | Kopf-Sill, Homsy (1988) | Bubble motion in a Hele-Shaw cell | Phys Fluids 31(1):18-26 | 10.1063/1.866566 | 실험 | 측정 속도가 이론과 안 맞음(뒤에 오염 탓으로 해석, P11). Maxworthy(1986, JFM 173:95, 10.1017/s002211208600109x)도 작은 기포에서 이탈 | 경고 사례 | C+A |
| P14 | Taylor, Saffman (1959) | A note on the motion of bubbles in a Hele-Shaw cell and porous medium | Q J Mech Appl Math 12(3):265-279 | 10.1093/qjmam/12.3.265 | 이론 | 마찰 없는 원형 기포는 2U로 움직임(P1, P4 경유) | 운동학 폐합의 기준(마찰 0) | C |
| P15 | Zhu, Gallaire (2016) | A pancake droplet translating in a Hele-Shaw cell: lubrication film and flow field | J Fluid Mech 798:955-969 | 10.1017/jfm.2016.357 | 경계적분, Stokes | 평균 막 두께는 확장 Bretherton 모델(맞춤 계수)로 예측. 교란 흐름은 쌍극자 1/r² | 쌍극자 상호작용(기포 무리) | C+A |
| P16 | Ling 외 (2016) | Droplet migration in a Hele-Shaw cell: effect of the lubrication film on the droplet dynamics | Phys Fluids 28(6):062001 | 10.1063/1.4952398 | 3D DNS | 팬케이크 액적은 평균 유입 속도보다 느림. 고전 Hele-Shaw 식은 막 효과를 못 잡음 | 막 마찰이 속도를 지배 | C+A |
| P17 | Booth, Griffiths, Howell (2026) | Dipole and pairwise models for the motion of bubbles in a Hele-Shaw cell | R Soc Open Sci 13(3):252426 | 10.1098/rsos.252426 | 이론, N개 기포 | 멀리 떨어진 기포는 쌍극자로 근사 가능, 쌍 상호작용 모델 | 기포 무리 계산 틀(같은 그룹: Wu 외 2024 PRF 9:123603, Booth 외 2025 JFM 1010:A19, RSPA 481:20240613) | C+A |
| P18 | Beatus, Bar-Ziv, Tlusty (2012) | The physics of 2D microfluidic droplet ensembles | Phys Rep 516(3):103-145 | 10.1016/j.physrep.2012.02.003 | 리뷰 | (원문 미확인) 준2차원 액적 집단의 마찰·쌍극자 상호작용 | 기포 무리의 선례 후보 | C |
| P19 | Okumura (2018) | Viscous dynamics of drops and bubbles in Hele-Shaw cells: drainage, drag friction, coalescence, and bursting | Adv Colloid Interface Sci 255:64-75 | 10.1016/j.cis.2017.07.021 | 리뷰(점성액) | 정지 액체 속 기포 F ≃ ηVR_T²/D(갭 소산), 액막 소산이 지배하면 F ≃ (ηV/γ)^(1/3)γR_TR_L/D(면적 비례). 접촉선이 생기면 접촉각 이력이 지배 | 면적 비례 마찰 대안. Eri & Okumura 2011(Soft Matter 7:5648)이 원 실험 | C+F (arXiv 1707.06049) |
| P20 | Yahashi, Kimoto, Okumura (2016) | Scaling crossover in thin-film drag dynamics of fluid drops in the Hele-Shaw cell | Sci Rep 6:31395 | 10.1038/srep31395 | 실험 | 막 소산 지배 영역과 액적 내부 소산 영역 사이 전환, 상 지도 | 마찰 법칙 전환 | C+A |
| P21 | Gallaire 외 (2014) | Marangoni induced force on a drop in a Hele Shaw cell | Phys Fluids 26(6):062105 | 10.1063/1.4878095 | Brinkman 깊이 평균 | 둘레 적분 힘의 닫힌 식, 이전 결과가 Marangoni 힘을 2배 과소평가 | 붙잡힌 기포의 힘(2U 인자) 교차 확인 | C+A |
| P22 | Aussillous, Quéré (2002) | Bubbles creeping in a viscous liquid along a slightly inclined plane | EPL 59(3):370-376 | 10.1209/epl/i2002-00204-2 | 실험(점성액) | (원문 미확인) 한쪽 벽을 미끄러지는 기포의 막 마찰 | 3·7 mm에서 위 덮개 밑 기포 | C |

### 1-B. 2D 폼·폼 벽 마찰 (계면 길이 × 길이당 힘)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| F1 | Cantat, Kern, Delannay (2004) | Dissipation in foam flowing through narrow channels | EPL 65(5):726-732 | 10.1209/epl/i2003-10169-0 | 2D 폼, 좁은 채널 | 압력 ∝ 속도^(2/3), Plateau border가 벽을 미끄러지는 소산. 길이당 힘 ληvCa^(−1/3)|u·n|, λ ≈ 10(측정)(F2 경유) | **"계면 길이 × 길이당 힘"의 가장 가까운 선례**(폼) | C (본문은 F2·P2 경유) |
| F2 | Cantat, Delannay (2005) | Dissipative flows of 2D foams | Eur Phys J E 18(1):55-67 | 10.1140/epje/i2004-10154-5 | 이론·수치, 2D 폼 | Plateau border 길이당 힘 f = −λη_w vCa^(−1/3)|u_v·n|, λ ~ 10, 지수 −1/3~−1/2 범위 보고 | 길이당 마찰 + 방향 인자의 모델 사례 | C+F (HAL hal-00007608 프리프린트) |
| F3 | Terriac, Etrillard, Cantat (2006) | Viscous force exerted on a foam at a solid boundary: influence of the liquid fraction and of the bubble size | EPL 74(5):909-915 | 10.1209/epl/i2005-10583-2 | mm 채널(1 cm², 0.12 cm²)의 기포 열, V 10⁻⁴~5×10⁻³ m/s, Re ≲ 10 | ΔP = Σ(Plateau border 길이 × f_v), 막 수를 세어 씀. f_v ∝ Ca^0.56±0.02(2/3 아님), 막 간격 L에 따라 2.5배 변화 → 메니스커스만의 소산 모델과 모순 | 영상 계수(막 수)를 압력 강하 입력으로 쓴 선례. 지수 < 2/3 경고 | C+F (HAL hal-00096588) |
| F4 | Raufaste, Foulon, Dollet (2009) | Dissipation in quasi-two-dimensional flowing foams | Phys Fluids 21(5):053102 | 10.1063/1.3142502 | 준2D 폼, Hele-Shaw, 이동 계면 | 기존 모델이 소산을 체계적으로 과소평가. 불일치 인자 ξ = 1.4(R_P/A^0.5)^(−0.5). P2 정리: f = 5.13γCa^(2/3)(√A_c/r_m)^0.48, 속도만 맞추면 Ca^0.58 | 실제 계수가 이론보다 큼 | C+A |
| F5 | Kern, Weaire, Martin, Hutzler, Cox (2004) | Two-dimensional viscous froth model for foam dynamics | Phys Rev E 70(4):041411 | 10.1103/physreve.70.041411 | 모델 | (원문 미확인) 막 길이당 비선형 항력으로 2D 폼 동역학 | 길이당 항력 모델의 원형 | C |
| F6 | Denkov, Subramanian, Gurovich, Lips (2005) | Wall slip and viscous dissipation in sheared foams: effect of surface mobility | Colloids Surf A 263(1-3):129-145 | 10.1016/j.colsurfa.2005.02.038 | 실험·모델 | 계면 이동성이 벽 마찰 지수를 바꿈(P2 경유: 이동 계면 Ca^(2/3), 비압축은 1/3~2/3 혼합). Denkov 외 2006(Colloids Surf A 282-283:329, 10.1016/j.colsurfa.2006.04.028)이 비압축 계면 막 형상 | 계면 상태에 따른 지수 | C |
| F7 | Dollet, Cantat (2010) | Deformation of soap films pushed through tubes at high velocity | J Fluid Mech 652:529-539 | 10.1017/s0022112010000935 | 비누막, 수 m/s | Bretherton 스케일이 Ca·We가 작지 않은 고속까지 성립 | 1 m/s 근처의 적용 근거 | C+A |
| F8 | Hirasaki, Lawson (1985) | Mechanisms of foam flow in porous media: apparent viscosity in smooth capillaries | SPE J 25(02):176-190 | 10.2118/12129-pa | 모세관 속 기포 열 | 겉보기 점도 = 슬러그 + 계면 변형 + 표면장력 구배. 기포 크기(라멜라 수/길이)가 핵심 변수 | "기포 수 밀도 → 압력 강하" 공학 선례(석유). 후속 개체수 균형 모델: Kovscek, Patzek, Radke 1995(Chem Eng Sci 50:3783, 10.1016/0009-2509(95)00199-f) | C+A |
| F9 | Marmottant, Raven (2009) | Microfluidics with foams | Soft Matter 5(18):3385 | 10.1039/b903276b | 리뷰 | (원문 미확인) 미세유로 폼 흐름. P2는 "흐름 수직 투영 길이만 기여" 근거로 인용 | 투영 길이 모델 근거 | C |

### 1-C. Taylor 흐름·미세유로의 기포·액적 저항 (1차원 유로)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| T1 | Bretherton (1961) | The motion of long bubbles in tubes | J Fluid Mech 10(2):166-188 | 10.1017/s0022112061000160 | 이론 + 실험, 원관, 낮은 Re | W ≃ 1.29(3Ca)^(2/3), P ≃ 3.58(3Ca)^(2/3)σ/r, Ca < 5×10⁻³에서 오차 10% 이내. 평판 사이 2차원에도 같은 이론 | 상수의 원출처. 3.58은 앞쪽 값(0장 1번) | C+A |
| T2 | Ratulowski, Chang (1989) | Transport of gas bubbles in capillaries | Phys Fluids A 1(10):1642-1655 | 10.1063/1.857530 | 수치, 원·정사각 관 | **기포 열의 기포 1개 압력 강하 = 고립 기포 값(낮은 Ca)**. 길이 > 관 폭이면 무한 긴 기포와 같음 | Γ로 더해도 된다는 근거(가산성) | C+A |
| T3 | Ratulowski, Chang (1990) | Marangoni effects of trace impurities on the motion of long gas bubbles in capillaries | J Fluid Mech 210:303-328 | 10.1017/s0022112090001306 | 점근 해석 | 불순물로 막이 최대 4^(2/3)배. 고속에서는 깨끗한 값으로 돌아감, 중간 속도에서 지수 < 2/3 | 오염 계수 범위 | C+A |
| T4 | Wong, Radke, Morris (1995) | The motion of long bubbles in polygonal capillaries. Part 2 | J Fluid Mech 292:95-110 | 10.1017/s0022112095001455 | 다각형 관 | 압력 강하 ∝ Ca^(2/3), 상수는 원관의 약 1/3. 모서리로 우회하는 흐름 때문에 Q < Q_c(≲10⁻⁶)에서 압력 구배가 Q에 선형 | 넓은 유로의 우회 흐름 비유 | C+A |
| T5 | Aussillous, Quéré (2000) | Quick deposition of a fluid on the wall of a tube | Phys Fluids 12(10):2367-2371 | 10.1063/1.1289396 | 실험, 저점성 액체 | 문턱 Ca 이상에서 막이 Taylor 법칙보다 두꺼워지고 고속에서 감소(관성). 두꺼운 막 보정 Ca^(2/3)/(1 + 3.34Ca^(2/3))(T7 경유) | Ca ≳ 10⁻²(1 m/s) 보정 | C+A |
| T6 | Kreutzer 외 (2005) | Inertial and interfacial effects on pressure drop of Taylor flow in capillaries | AIChE J 51(9):2428-2440 | 10.1002/aic.10495 | 원관, U 0.04~0.3 m/s, Ca 3×10⁻³~4×10⁻², Re 150~1400, We 1~15 | f = (16/Re)[1 + a(D/L_s)(Re/Ca)^0.33], a = 0.17(실험) / 0.07(CFD 깨끗). 차이는 불순물의 Marangoni 효과. 슬러그 < 10D면 마찰 급증 | Re ≫ 1에서 기포 항이 Re^(1/3)배로 커짐(6장). 공학 범위 Re와 겹침 | C+A (식·계수는 T7 C+F 경유) |
| T7 | Warnier 외 (2010) | Pressure drop of gas-liquid Taylor flow in round micro-capillaries for low to intermediate Reynolds numbers | Microfluid Nanofluid 8(1):33-45 | 10.1007/s10404-009-0448-z | 250 µm 원관, N₂-물, Ca_gl 2.3~8.8×10⁻³, Re 41~159 | dP/dz = (32μU_l/D²)[1 + (7.16·3^(2/3)/32)(D·f_b/U_l)/(Ca_b^(1/3) + 3.34Ca_b)], **기포 빈도 f_b와 기포 속도가 입력**, ±4% | 1차원 운동학 입력 모델의 가장 가까운 선례. 액체 항이 겉보기 속도 U_l로 정리됨(3장 결과와 같은 구조) | C+F |
| T8 | Walsh 외 (2009) | Pressure drop in two phase slug/bubble flows in mini scale capillaries | Int J Multiphase Flow 35(10):879-884 | 10.1016/j.ijmultiphaseflow.2009.06.007 | 미니 관, Re·Ca 3자릿수, 슬러그 길이 2자릿수 | Re와 Ca 묶음이 압력 강하를 맞게 스케일, 계면 추가 압력은 기존 보고보다 약 40% 작음 | 계수 a의 실험 편차 | C+A (UL 저장소 초록) |
| T9 | Fuerstman 외 (2007) | The pressure drop along rectangular microchannels containing bubbles | Lab Chip 7(11):1479-1489 | 10.1039/b706549c | 직사각 미세유로, 네 벽에 닿는 기포, 물(±계면활성제)·물-글리세롤, 간접 압력 산출 | 계면활성제가 적거나 많으면 **기포 수**가, 중간이면 **기포 총길이**가 압력 강하를 지배(모서리 홈 흐름) | 둘레(수) 대 면적(길이) 지배가 계면 상태로 바뀌는 직접 선례 | C+A |
| T10 | Vanapalli 외 (2009) | Hydrodynamic resistance of single confined moving drops in rectangular microchannels | Lab Chip 9(7):982-990 | 10.1039/b815002h | 직사각 미세유로, 계면활성제 없는 액적 1개, Ca 10⁻³~10⁻², 미세 비교기로 초과 압력 직접 측정 | 길이/폭 ≲ 4: 끝 캡 소산 지배, 그 이상: 캡 + 몸통 | 작은 팬케이크 = 캡 지배 | C+A |
| T11 | Labrot 외 (2009) | Extracting the hydrodynamic resistance of droplets from their behavior in microchannel networks | Biomicrofluidics 3(1):012804 | 10.1063/1.3109686 | 채널 500 µm × 300 µm, 기름 20 cP, 액적 48~95 nl, v 5~9 mm/s(Re ≈ 0.1, 계산) | **경로 선택·액적 간격(운동학)으로 저항 길이 L_d 추출**, 차압계(Validyne)와 비교: 부피·속도 의존은 일치, 점도 의존은 "mediocre", 간격 3 mm 이하에서 협동 효과로 과소 | 운동학 → 저항의 선례(1차원 네트워크, Re ≪ 1) | C+F (PMC2717590) |
| T12 | Sessoms 외 (2009) | Droplet motion in microfluidic networks: hydrodynamic interactions and pressure-drop measurements | Phys Rev E 80(1):016317 | 10.1103/physreve.80.016317 | 밀리·미세 비대칭 루프, 원·직사각 단면 | 액적 교통에서 초과 저항(저항 길이 L_d)과 이동도 β 측정, 압력 강하 직접 측정 병행 | 운동학 + 압력의 이중 측정 선례(1차원) | C+A |
| T13 | Jakiela 외 (2011) | Speed of flow of individual droplets in microfluidic channels as a function of the capillary number, volume of droplets and contrast of viscosities | Lab Chip 11(21):3603 | 10.1039/c1lc20534j | 정사각 360 µm, λ 0.3~33, Ca 10⁻⁴~10⁻¹, 길이 0.8~30w | 액적 속도가 길이와 점도비에 크게 의존(속도만 측정) | 속도 측정만으로는 저항이 안 나옴(1차원) | C+A |
| T14 | Garimella, Killion, Coleman (2002) | An experimentally validated model for two-phase pressure drop in the intermittent flow regime for circular microchannels | J Fluids Eng 124(1):205-214 | 10.1115/1.1428327 | R134a 응축, D 0.5~4.91 mm, G 150~750 | 단위 셀(슬러그 + 기포 + 막) 모델, 단위 셀 길이는 슬러그 Re 상관식, ±13.4% | 슬러그 빈도를 **상관식으로** 넣음(영상 입력과 구별) | C+A |
| T15 | Garimella, Killion, Coleman (2003) | ... noncircular microchannels | J Fluids Eng 125(5):887-894 | 10.1115/1.1601258 | D_h 0.42~0.84 mm, 여러 단면 | 90%가 ±28%, 평균 오차 16.5% | 비원형 확장 | C+A |
| T16 | Heil (2001) | Finite Reynolds number effects in the Bretherton problem | Phys Fluids 13(9):2517-2521 | 10.1063/1.1389861 | 2D 채널, 0.05 < Ca < 5, 0 < Re < 280 | 유한 Re에서 기포 앞 와류가 압력 상승을 눈에 띄게 키움 | 관성 보정 방향(증가) | C+A |
| T17 | de Lózar, Juel, Hazel (2008) | The steady propagation of an air finger into a rectangular tube | J Fluid Mech 614:173-195 | 10.1017/s0022112008003455 | 직사각 관, 종횡비 α | α ≥ 8이면 준2차원. 가로 중력 Bo > 1이면 기포가 아래 벽에서 떨어짐 | (주 세션 정정 2026-10-23: 원문의 Bo = ρgb²/σ는 반높이 b = H/2 기준이다. 우리 갭은 Bo_b = 0.003/0.016/0.034/0.30/1.65 → **7 mm만** > 1. 경계 H = 2Lc. 처음 판의 "3 mm(Bo_H 1.2)도 떨어짐"은 정의 차이) | C+F |
| T18 | Hazel, Heil (2002) | The steady propagation of a semi-infinite bubble into a tube of elliptical or rectangular cross-section | J Fluid Mech 470:91-114 | 10.1017/s0022112002001830 | 수치 | 직사각 관에서 낮은 Ca는 Wong 외와 일치, 큰 Ca는 Wong 외가 과소 | 직사각 보정 | C+A |
| T19 | Botticini 외 (2026) | Pressure drop-flow rate nonlinearity in bubble trains through a capillary bundle | Phys Rev Fluids 11(7):073601 | 10.1103/7z3l-zpzy | 이론, 모세관 다발 | 기포 수가 적으면 지수 2/3에서 2/3~1로 전환 | 지수 해석 | C+A (arXiv 2510.12588 초록) |
| T20 | Fries, Trachsel, von Rohr (2008) | Segmented gas-liquid flow characterization in rectangular microchannels | Int J Multiphase Flow 34(12):1108-1118 | 10.1016/j.ijmultiphaseflow.2008.07.002 | 직사각 미세유로 | (원문 미확인) 슬러그 흐름 특성과 압력 강하 | 직사각 Taylor 흐름 | C |
| T21 | Abadie 외 (2012) | Hydrodynamics of gas-liquid Taylor flow in rectangular microchannels | Microfluid Nanofluid 12(1-4):355-369 | 10.1007/s10404-011-0880-8 | 직사각 미세유로 | (원문 미확인) | 직사각 Taylor 흐름 | C |

### 1-D. 상관식과 좁은 직사각 유로 평가
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| K1 | Chisholm (1967) | A theoretical basis for the Lockhart-Martinelli correlation for two-phase flow | Int J Heat Mass Transfer 10(12):1767-1778 | 10.1016/0017-9310(67)90047-6 | 이론 | φ_L² = 1 + C/X + 1/X², C = 5~20(흐름 상태별)(2차 인용) | 기준 틀 | C |
| K2 | Mishima, Hibiki (1996) | Some characteristics of air-water two-phase flow in small diameter vertical tubes | Int J Multiphase Flow 22(4):703-712 | 10.1016/0301-9322(96)00010-9 | 수직 원관 1~4 mm, 공기-물 | C = 21(1 − e^(−319D)), D [m](= 0.319·D[mm])(2차 인용: Ali, Palm, Maqbool 2009, 0.781 mm R134a에서 MAD 19%) | D_h 의존 C의 기준식 | C |
| K3 | Lee, Lee (2001) | Pressure drop correlations for two-phase flow within horizontal rectangular channels with small heights | Int J Multiphase Flow 27(5):783-796 | 10.1016/s0301-9322(00)00050-1 | 수평, 폭 20 mm, 갭 0.4/1/2/4 mm, 공기-물, 305점 | L-M형, C가 갭과 유량에 의존, ±10%. X 0.303~79.4, Re_lo 175~17700(검색 요약 기준). λ = μ²/(ρσD), ψ = μj/σ, Re_lo의 거듭제곱 꼴이라는 기억은 **원문 미확인** | 0.4·1 mm 자료가 0.3·0.7·1 mm에 가장 가까움 | C |
| K4 | Sun, Mishima (2009) | Evaluation analysis of prediction methods for two-phase flow pressure drop in mini-channels | Int J Multiphase Flow 35(1):47-54 | 10.1016/j.ijmultiphaseflow.2008.08.003 | 평가, 미니 채널 | Chisholm 방식, Re_l·Re_v = 2000을 전환점으로 C를 나눔(2차 인용, 계수 미확인) | 평가 기준 | C |
| K5 | Zhang, Hibiki, Mishima (2010) | Correlations of two-phase frictional pressure drop and void fraction in mini-channel | Int J Heat Mass Transfer 53(1-3):453-465 | 10.1016/j.ijheatmasstransfer.2009.09.011 | ANN으로 지배 변수 탐색 | 무차원 Laplace 상수가 C와 C0를 지배(검색 요약). 계수 미확인 | 갇힘(Lc/D)을 C에 넣은 식 | C |
| K6 | Li, Wu (2010) | A general correlation for adiabatic two-phase pressure drop in micro/mini-channels | Int J Heat Mass Transfer 53(13-14):2732-2739 | 10.1016/j.ijheatmasstransfer.2010.02.029 | 데이터베이스 | Bo × Re_L^0.5를 정의해 C를 상관(2차 인용), 계수 미확인 | 표면장력·관성 묶음 | C |
| K7 | Kim, Mudawar (2012) | Universal approach to predicting two-phase frictional pressure drop for adiabatic and condensing mini/micro-channel flows | Int J Heat Mass Transfer 55(11-12):3246-3261 | 10.1016/j.ijheatmasstransfer.2012.02.047 | 7115점, 36출처 | 액·기 층류/난류 4조합별 C(Re_lo, Su_go, ρ 비) — 식 원문 미확인(저자 PDF 서버 503). 비등판 2013(IJHMT 58:718, 10.1016/j.ijheatmasstransfer.2012.11.045) | 범용 비교 기준 | C |
| K8 | Ali, Sadatomi, Kawaji (1993) | Adiabatic two-phase flow in narrow channels between two flat plates | Can J Chem Eng 71(5):657-666 | 10.1002/cjce.5450710502 | 갭 0.778·1.465 mm, 길이 240 mm, 방향 6가지 | 수직 평판 사이 수평 흐름을 빼면 갭·방향 효과 작음. 기공률·마찰 배수를 Martinelli X로 상관(검색 요약 기준) | 0.7·1 mm 직접 근거 | C |
| K9 | Moriyama, Inoue, Ohira (1992) | The thermohydraulic characteristics of two-phase flow in extremely narrow channels (frictional pressure drop and void fraction ...) | Trans JSME B 58(546):401-407 | 10.1299/kikaib.58.401 | 수평 평판 갭 5~100 µm, N₂-R113 | 마찰 배수가 Chisholm보다 작음, 좁을수록 기공률 감소, 경험식 제안 | 갭 감소 → C 감소 추세 | C+A |
| K10 | Ide, Fukano (2005) | Experimental research on the correlations of holdup and frictional pressure drop in air-water two-phase flow in a capillary rectangular channel | Exp Therm Fluid Sci 29(7):833-841 | 10.1016/j.expthermflusci.2005.03.010 | 9.9 × 1.1 mm, 수직·수평, 넓은 면 방향 2가지 | 종횡비 효과를 넣은 holdup·마찰 상관식(ICMM2004 판 초록, 10.1115/icmm2004-2358) | 1 mm 갭, 방향 효과 | C (+A: 학회판) |
| K11 | Kawahara, Chung, Kawaji (2002) | Investigation of two-phase flow pattern, void fraction and pressure drop in a microchannel | Int J Multiphase Flow 28(9):1411-1435 | 10.1016/s0301-9322(02)00037-x | 100 µm 원관 | (원문 미확인) | 미세 쪽 기준 | C |
| K12 | Chung, Kawaji (2004) | The effect of channel diameter on adiabatic two-phase flow characteristics in microchannels | Int J Multiphase Flow 30(7-8):735-761 | 10.1016/j.ijmultiphaseflow.2004.05.002 | 50~530 µm | (원문 미확인) 같은 그룹 학회판(10.1115/icmm2004-2359, 초록): 기공률 기준 미세/미니 경계가 100~251 µm | 0.3·0.7 mm는 "미니" 쪽 | C |
| K13 | Huang, Gao (2013) | Experimental and prediction methods investigation of two-phase frictional pressure drop in rectangular narrow channel | ICONE21 V004T09A101 | 10.1115/icone21-16562 | 수직 좁은 직사각, 증기-물 | 균질 모델 중 Cicchitti·Dukler 점도가 비교적 정확, 새 식 평균 편차 18.7% | 좁은 갭 평가 | C+A |
| K14 | Jin, Yan, Sun, Wang (2013) | Resistance characteristic and calculating method of two-phase flow in rectangular channel (원자력 과학 기술 47(5):740) | Atomic Energy Sci Technol | 10.7538/yzk.2013.47.05.0740 (미대조) | 종횡비 다른 직사각 2개, 공기-물 | 일반 채널 상관식은 좁은 직사각에서 나쁨. Lee-Lee는 잘 맞지만 일부 범위에서 오차. 종횡비·Re_lo·X를 넣은 C 수정식 | Lee-Lee 평가 | U (학술지 웹 초록) |
| K15 | Ronshin, Dementyev, Chinnov, Cheverda, Kabov (2019) | Experimental investigation of adiabatic gas-liquid flow regimes and pressure drop in slit microchannel | Microgravity Sci Technol 31(5):693-707 | 10.1007/s12217-019-09747-1 | 슬릿 미세유로(원문 미확인) | (원문 미확인) | 0.3 mm 이하 슬릿의 압력 강하 자료 | C |
| K16 | Ronshin, Chinnov (2019) | Experimental characterization of two-phase flow patterns in a slit microchannel | Exp Therm Fluid Sci 103:262-273 | 10.1016/j.expthermflusci.2019.01.022 | 50 µm × 10 mm | 국소 기공률, 위·아래 벽 액막 영역 크기, 기포 생성 빈도를 영상으로 측정해 유동 양식 경계 판정 | 슬릿 영상 계측 선례(ΔP 입력은 아님) | C+A |
| K17 | Liu, Cheng, Yan, Gu, Meng (2022) | Experimental study on length, liquid film thickness and pressure drop of slug flow in horizontal narrow rectangular channel | Chem Eng Res Des 182:502-516 | 10.1016/j.cherd.2022.04.010 | 수평 좁은 직사각 | (제목 기준) 슬러그 길이·액막·압력 강하 동시 측정 | mm 규모에서 영상 길이 + ΔP를 같이 쓴 후보 | C |
| K18 | Harirchian, Garimella (2012) | Flow regime-based modeling of heat transfer and pressure drop in microchannel flow boiling | Int J Heat Mass Transfer 55(4):1246-1260 | 10.1016/j.ijheatmasstransfer.2011.09.024 | 비등, 유동 양식별 모델 | (원문 미확인, Purdue e-Pubs 403) | 양식 기반 모델의 예(주제 2와 겹침) | C |
| K19 | English, Kandlikar (2006) | An experimental investigation into the effect of surfactants on air-water two-phase flow in minichannels | Heat Transfer Eng 27(4):99-109 | 10.1080/01457630500523980 | 미니 채널, 공기-물 | (원문 미확인) 계면활성제 영향 | 계면 상태가 공학 ΔP에 주는 영향 | C |

## 2. 핵심 질문에 대한 답

### Q1. 좁은 직사각·미니 채널 상관식
- 확인한 식(2차 인용 포함)
  - Chisholm: φ_L² = 1 + C/X + 1/X² [K1, C].
  - Mishima & Hibiki: C = 21(1 − e^(−0.319·D[mm])) [K2, 2차 인용]. D_h = 2H로 넣으면 0.3/0.7/1/3/7 mm에서 C = 3.6 / 7.3 / 9.6 / 18.3 / 20.9(계산).
  - Kreutzer(Taylor 흐름): f = (16/Re)[1 + a(D/L_s)(Re/Ca)^0.33], a = 0.17/0.07 [T6, T7 C+F].
  - Warnier: 기포 빈도 f_b를 쓰는 식(1-C 표) [T7, C+F].
- 확인하지 못한 식: Lee & Lee의 λ·ψ·Re_lo 거듭제곱 계수, Sun & Mishima, Zhang 외, Li & Wu, Kim & Mudawar의 계수. 원문(유료)·저자 PDF(Purdue 서버 503·TLS 실패) 모두 막혔다. **메인 세션은 이 계수를 기억으로 쓰지 말 것.**
- 어느 식이 1~5 mm 갭에 맞나
  - 직접 근거는 Lee & Lee(갭 0.4~4 mm, 폭 20 mm, 수평, 공기-물)다 [K3]. 중국 평가 연구도 "Lee-Lee가 잘 맞지만 일부 범위에서 오차"라고 했다 [K14, U].
  - 갭이 좁아질수록 C가 작아진다: Mishima-Hibiki의 D 의존 [K2], 5~100 µm 갭에서 Chisholm보다 작은 배수 [K9].
  - 0.3·0.7 mm(D_h 0.6·1.4 mm)는 기공률 기준으로 "미니" 쪽이다(미세/미니 경계 100~251 µm, 원관 결과) [K12 학회판, C+A].
- 물리적 해석(3장 결과에서): Hele-Shaw 극한에서 마찰 없는 기포는 φ_L² = 1이다. C/X 항이 곧 기포(메니스커스·막) 마찰이다. 그래서 C가 갭이 좁을수록 작아지는 것은 "기포 1개당 마찰은 σCa^(2/3) 꼴로 작고 액체 마찰은 1/H²로 크다"와 같은 방향이다(추정).

### Q2. 기포 수·길이가 들어가는 메커니즘 모델
- 1차원 유로에서는 정착된 방법이다: ΔP = 슬러그 Poiseuille + 기포 수 × 기포 1개 압력 강하 [T1, T6, T7, T8, T9].
  - 기포 열에서도 기포 1개의 압력 강하는 고립 기포와 같다(낮은 Ca) → 더해도 된다 [T2].
  - 입력은 슬러그 길이(Kreutzer, Walsh), 기포 빈도와 기포 속도(Warnier), 기포 수 또는 총길이(Fuerstman), 상관식으로 구한 단위 셀 길이(Garimella).
- 실험 계수는 깨끗한 이론보다 크다: a = 0.17 vs 0.07 [T6]. Walsh는 Kreutzer보다 약 40% 작게 봤다 [T8]. 같은 식에서도 2배 안팎이 흔들린다.
- Fuerstman: 계면 상태에 따라 "기포 수"(캡, 둘레형) 지배와 "기포 총길이"(몸통, 면적형) 지배가 바뀐다 [T9]. Vanapalli: 길이/폭 ≲ 4는 캡 지배 [T10]. → 영상에서 둘레(Γ)와 면적(α)을 둘 다 재야 한다.

### Q3. Hele-Shaw·2D 폼의 벽 마찰
- 길이당 힘(깨끗한 계면, 벽 1개): 앞 3.84γCa^(2/3), 뒤 1.1γCa^(2/3), 합 4.94 [P2]. 갭 두 벽의 압력 점프로 쓰면 β1 = 3.88, β2 = −1.13 [P1].
- 굳은 계면: Cantat는 구름 6.22, 미끄럼 6.82 + 0.94γCa^(1/3)(ℓ/r_m)(액막 전단, 면적 비례) [P2]. Booth는 압력 점프 최대 4^(2/3)배(β1 9.78, β2 −2.85) [P3, P4]. **두 접근의 굳은 계면 값이 다르다(힘 1.26~1.38배 vs 압력 점프 2.52배).** Cantat는 Ratulowski & Chang이 표면장력 변화를 빼서 값이 다르다고 지적했다 [P2]. 해결되지 않았으므로 범위로 둔다.
- 2D 폼: 압력 강하 = Plateau border 길이 × 길이당 힘 [F1, F2, F3]. 측정 λ ≈ 10 [F2], 지수 0.56 [F3], 이론 과소평가 [F4]. Denkov 그룹: 계면 이동성에 따라 지수가 바뀜(2/3 vs 1/3·1/2 혼합) [F6, P2].
- Okumura 그룹(점성 액체, 정지 액체 속 기포): 갭 소산 F ≃ ηVR²/D와 막 소산 F ∝ Ca^(1/3)·면적 사이의 전환 [P19, P20]. 접촉선이 생기면 접촉각 이력이 지배한다 [P19].

### Q4. 유동 양식 기반·슬러그 빈도 모델
- Garimella(단위 셀 + 슬러그 Re 상관식으로 빈도) [T14, T15], Harirchian & Garimella(양식별) [K18, 원문 미확인].
- 공통점: 기포 길이·빈도를 **상관식으로** 넣는다. 영상으로 잰 값을 직접 넣는 것은 Warnier(f_b)·Fuerstman(수)·Terriac(막 수)처럼 미세·폼 쪽뿐이다.

### Q5. "액체 마찰 + k·σ·Ca^(2/3)·Γ/H"가 물리적으로 맞는가
1. **0.3·0.7·1 mm(갇힌 팬케이크, d > 2H)**: 맞다. 단, 세 가지를 고쳐야 한다.
   - (a) Ca는 기포의 벽 기준 속도 V로 잰다(메니스커스가 벽에 대해 V로 움직임) [P1].
   - (b) Γ 대신 방향 가중 둘레를 쓴다. 앞쪽 Γ_f = (1/A)Σ∫_front |n_x|^(5/3) ds, 뒤쪽 Γ_r도 같이. dP/dx_b = (2σCa_V^(2/3)/H)(β1Γ_f + |β2|Γ_r) [P1, P2] (주 세션 정정 2026-10-23: 처음 판에 2가 빠져 있었다. 2가 있어야 원형에서 k = 2.68). 원형이면 Γ_f = Γ_r = 0.268Γ → k = 2.68. 투영 길이 모델이면 k = 3.19. 둘은 실험으로 구별된 적이 없다 [P2].
   - (c) 액체 항은 12μj_L/H²(액체 겉보기 속도)로 쓴다. 3장의 힘 균형에서 정확히 이 꼴이 나온다. j_L/(1−α)를 쓰면 마찰 없는 기포에서도 압력 강하가 1/(1−α)배로 커지는 모순이 생긴다.
2. **계수 k의 결론**
   - 이론(깨끗, 원형): k = 2.68(법선 속도 모델) ~ 3.19(투영 길이 모델).
   - 계면 오염: k ≈ 3.4~6.8(1.26~2.52배) + 굳은 계면이면 면적 항 dP/dx_film ≈ 1.88·α·σ·Ca^(1/3)/H²(Cantat ζ = 0.94에서 유도, 두 벽).
     면적 항/메니스커스 항 ≈ 0.13(d/H)Ca^(−1/3) → d/H = 3, Ca = 10⁻³에서 약 4배. 굳은 계면이면 면적 항이 지배할 수 있다.
   - 실험 계수는 이론의 1~4배, 지수 0.5~2/3로 흔들린다 [P2, F3, F4, T6, T8].
   - → **k는 맞춤값으로 두되, 이론값 2.7을 하한 기준으로 보고, 지수(2/3 vs 1/3)와 입력 변수(Γ vs α)를 데이터로 판별한다.** 더 좋은 방법은 4번(운동학 폐합)이다.
3. **적용 한계**
   - Ca: Bretherton 상수는 Ca < 5×10⁻³에서 10% 이내 [T1]. 우리 Ca_V = 1.6×10⁻⁴~2.3×10⁻²(6장 표). j ≈ 1 m/s는 한계를 넘는다 → 두꺼운 막 보정 1/(1 + 3.34Ca^(2/3)) [T5, T7]. 힘의 Ca^(2/3) 스케일은 We ≈ 10, 수 m/s까지 성립한 보고가 있다 [P2, F7].
   - 관성: Darcy(Hele-Shaw) 가정은 Re_H·H/d ≪ 1이 필요하다. 0.3 mm는 0.4~170, 1 mm는 1.4~560, 3 mm는 4~1700(6장). 유한 Re는 기포 앞 압력 상승을 키운다 [T16]. Taylor 흐름에서는 Re ≫ 1이면 계면 항이 (Re/Ca)^(1/3) 꼴(속도에 선형)로 바뀐다 [T6]. 이 꼴과 Bretherton의 비는 (0.15~0.37)·Re^(1/3) ≈ 0.7~3.7(Re 100~1000, 계산).
   - 젖음 막: 막이 끊기면 접촉선 마찰(접촉각 이력)이 지배한다 [P19]. δ < 1(작은 기포·낮은 Ca)은 막이 매우 얇아 실험에서 보통 계면활성제를 넣는다 [P1]. 철 바닥의 젖음성 확인이 필요하다.
   - 기포가 갭을 채우지 않는 경우(3·7 mm의 작은 기포): 두 벽 메니스커스가 없다. 수평이면 위 덮개 밑에서 한쪽 벽만 미끄러진다 [P22]. 가로 중력 Bo > 1이면 아래 벽에서 떨어진다 [T17]. Bo_H = ρgH²/σ = 0.012 / 0.066 / 0.13 / 1.2 / 6.6(주 세션 정정: T17의 Bo는 반높이 기준이라 Bo_b = Bo_H/4 = 0.003~0.30, 7 mm 1.65 → 떨어지는 것은 7 mm의 큰 기포). → 3 mm는 갭보다 작은 기포만 "위 벽만", 7 mm는 큰 기포도 "위 벽만"으로 제한한다.
   - 넓은 유로의 우회 흐름: 액체가 기포 옆으로 돌아간다. 이것이 기포 속도를 힘 균형으로 정하는 이유다(1차원 관과 다름) [P1]. 다각형 관의 모서리 우회는 낮은 유량에서 압력 구배를 선형으로 만든다 [T4]. 옆벽 근처에서는 기포 속도가 δ에 따라 빨라지거나 느려진다 [P1].
   - 비원형 기포: 뒤쪽 계수는 앞쪽이 깐 막에 따라 달라진다(F(cosθ+/cosθ−)) [P1, P7]. 슬러그 옆면은 Ca^(4/5) 막 [P7].
4. **같은 것을 누가 했나**
   - 2D 폼: "Plateau border 길이 × 길이당 힘"으로 압력 강하를 계산한 연구가 있다 [F1~F4, P2]. 차이: 폼은 기포가 빽빽하고(액체 분율 수 %), 계면활성제가 있고, Re ≲ 10이다. 우리는 묽은 기포류·슬러그(α 0.1~0.5), 액체가 흐르고(액체 마찰이 같은 크기), Re 10~1000, 물이다.
   - Hele-Shaw 기포: 같은 메니스커스 법칙으로 기포 **속도**를 예측한 연구는 있다 [P1, P4, P8, P10]. 기포 무리의 **유로 압력 강하**를 계산한 것은 찾지 못했다(4장 기록).
   - 1차원 Taylor 흐름: 기포 수·빈도로 압력 강하를 계산한 연구는 많다 [T6~T9]. 2차원(넓은 유로)으로 일반화한 것은 찾지 못했다.

### Q6. 크기 비 계산용 계수·식(6장에 표)

## 3. 아이디어와 시사점

### 3.1 힘 균형 분해 (여기서 유도, 검토 필요)
- 가정: Hele-Shaw 극한(깊이 평균 Darcy 흐름 u = −(H²/12μ)∇p), 기포는 갭을 채운 팬케이크, 막의 유량 무시, 관성 무시.
- 판 두께 H, 면적 A인 층의 x 방향 힘 균형: 압력 차가 벽 마찰과 같다. 액체 영역의 벽 마찰은 (12μ/H)u, 기포는 F_b(메니스커스 + 막).
  - **−dP/dx = 12μ·j_L/H² + (1/(A·H))·ΣF_b**. ∫_액체 u dA/A = j − j_G = j_L이 정확하므로 액체 항은 겉보기 액체 속도로 쓴다.
  - Warnier의 1차원 식도 액체 항이 겉보기 속도 U_l로 정리된다 [T7]. 같은 구조다.
- 원형 기포(반지름 R, 속도 V, 주변 액체 속도 U)의 Darcy 압력장: p = −(12μ/H²)[Ur + (U − V)R²/r]cosθ → 기포에 미는 힘 **F_b = 12πμR²(2U − V)/H**. 마찰 없으면 V = 2U [P14], 멈춘 기포는 F = 24πμR²U/H(Gallaire 외의 "2배" 지적과 같은 방향 [P21]).
  - 이것은 P1의 식(2.15)을 차원으로 쓴 것과 같다(Ub^(2/3) = δ(2 − Ub)의 오른쪽).
- 따라서 **증가분 = (12μ/H²)·Σ(a_b/A)(2U − V_b) = (12μ/H²)·α·(2U − V̄_a)**(V̄_a는 면적 가중 평균 기포 속도).
  - 묽은 근사 U ≈ j_L/(1−α)와 αV̄ = j_G를 쓰면 −dP/dx = (12μ/H²)[j_L(1+α)/(1−α) − j_G].
  - 점검: 마찰 0 → 12μj_L/H²(Maxwell 1차와 같음). 기포가 멈추면 (1+α)/(1−α)배(2D Maxwell-Garnett, 불투과 원판).
- 같은 증가분을 메니스커스 법칙으로: (σ/H)·k·Ca_V^(2/3)·Γ(원형). 두 식이 같다는 것이 곧 Booth 속도식이다.

### 3.2 운동학–동역학 폐합 (논문의 핵심 주장 후보)
- 경로 A(운동학): 영상 α, 크기별 V(d), 유량계 j_L·j_G → 증가분 = (12μ/H²)α(2U − V̄). **마찰 법칙과 계수 없이** 예측.
- 경로 B(동역학): 영상 Γ_f·Γ_r, V → (2σ/H)Ca_V^(2/3)(β1Γ_f + |β2|Γ_r)(주 세션 정정: 2 추가). β는 이론값 또는 V(d)/U를 P1 곡선에 맞춰 구한 값.
- 경로 C(측정): ΔP − 12μj_L/H²·L.
- 시험: A = C면 Hele-Shaw 그림이 맞다(계수와 무관). A = B면 Bretherton 법칙·투영 모델이 맞다. V(d)로 맞춘 β로 B를 계산해 C와 비교하면 "맞춤 없는 예측"이 된다.
- 크기별 V(d)의 기울기 부호로 계면 상태를 판별한다 [P10]: 클수록 빠름(이동 계면) / 클수록 느림(비압축 계면). 이 판정이 Γ형(Ca^(2/3)) vs α형(Ca^(1/3)) 마찰 선택의 근거가 된다 [T9, P2].
- 필요한 데이터: 0.3·0.7 mm 단열 실험의 j_L, j_G(유량계), ΔP(탭 위치, 입출구 제외), 영상의 기포별 면적·둘레·윤곽 방향·속도. 화소당 mm 보정. 흐름 방향 축이 영상 x와 맞는지.
- 실현성: 기존 파이프라인 출력(면적, 둘레, 속도)으로 대부분 계산된다. 윤곽 방향(|n_x|^(5/3) 가중)만 새로 계산하면 된다.
- 위험
  - 관성(Re_H·H/d가 0.3 mm에서도 j = 1 m/s면 ~100) → 경로 A의 Darcy 계수 12μ/H²가 틀어진다. 저속 조건부터 시험한다.
  - 기공률 α가 커지면(> 0.3) 묽은 근사 U = j_L/(1−α)가 흔들린다. 기포 간 쌍극자 상호작용 [P15, P17].
  - 작은 기포(d < 2H)는 팬케이크가 아니다. 크기 구분별로 따로 계산한다.
  - 공기 주입부 근처의 가속·팽창, 옆벽 효과 [P1].
  - 젖음 막이 끊기면(철 바닥, 가열) 법칙 자체가 바뀐다.

### 3.3 영상 기반 Chisholm C
- φ_L² − 1 = (경로 A 또는 B의 증가분)/(12μj_L/H²). C_img = X·(φ_L² − 1 − 1/X²). 갭별로 C_img와 Lee & Lee·Mishima-Hibiki C를 같이 그리면 "왜 좁은 갭에서 C가 작은가"를 기포 거동으로 설명할 수 있다(가설).

## 4. 새로움 판단 기록

### 4.1 검색 기록
- Crossref(query.bibliographic, 행 5~6, mailto 없음)
  - 서지 대조: 이 문서의 모든 DOI. K14(10.7538/…)만 Crossref에 없다(중국 DOI 등록처로 추정, U).
  - 새로움 검색 8건, 모두 관련 없음 또는 아래 후보만:
    "pressure drop bubbles Hele-Shaw cell meniscus friction"(6건, 채널 ΔP 없음), "pressure drop two-dimensional bubbly flow Hele-Shaw channel"(6, 없음), "pressure drop confined bubbles shallow wide microchannel lubrication film"(6, 없음), "interfacial perimeter pressure drop two-phase flow narrow gap image"(6, 없음), "bubble train pressure drop Hele-Shaw channel capillary number two-thirds"(6, Lawless 외 2024 PRF 등, ΔP 없음), "friction of confined bubbles in a Hele-Shaw cell pressure drop flow rate"(6, 없음), "pancake bubbles pressure drop quasi two-dimensional flow"(6, 없음), "two-phase flow narrow rectangular channel pressure drop model bubble length film thickness"(6, K17·K13 발견).
  - 그룹 검색: "Booth Griffiths Howell bubble Hele-Shaw"(6건 → P1, P3, P17과 같은 그룹 2024~2026 논문 3편), Hele-Shaw 속도 실험(P8, P10, P11, P12), 슬릿 미세유로(K15, K16, Chinnov 그룹 5건).
- Google Scholar(WebFetch, 6회 사용)
  1. "narrow rectangular channel" "two-phase" "frictional pressure drop" "Lee and Lee" ...: 4건(Kandlikar 2002 리뷰 등), 새로운 평가 없음.
  2. Lee & Lee 정확한 제목: 1건(인용 572), 무료 PDF 없음.
  3. Vanapalli 정확한 제목: 인용 문헌 18건만, 무료 PDF 없음.
  4. "Hele-Shaw" bubbles "pressure drop" "bubble velocity" Bretherton "thin film" experiment channel multiple bubbles: 27건. 상위 10건(Booth 2025 racing, Hilgenfeldt 외 2008 폼 리뷰, Schwartz 외 1986, Booth 학위논문, Ratulowski 1988, Park 1994, Balestra 2018, Booth 2025 계면활성제, Lu & Chang 1988, Ronshin & Chinnov 2019) 중 **여러 기포의 운동학으로 유로 ΔP를 예측한 것 없음**.
  5. "narrow rectangular channel" "bubble velocity" "pressure drop" "image processing" "interfacial area"/"bubble number density": 14건. Yan 외 2014(Prog Nucl Energy 73:64, 10.1016/j.pnucene.2014.01.003)와 Wang 외 2017(학회)이 영상 기포 변수와 ΔP를 같은 실험에서 쟀다(검색 요약 기준). 영상 변수를 ΔP 모델 입력으로 쓴 증거는 없음.
- WebSearch(standard, 7회): Lee & Lee 계수(2회, 없음), Kim & Mudawar 계수·PDF(2회, PDF 위치만, 서버 503), Walsh 초록(UL 저장소), Booth 학위논문 위치(ORA), Liu 2022 초록(못 찾음).
- 전문 확인: Booth 학위논문 전체에서 "pressure drop" 35회 = 모두 메니스커스 단위. "resistance", "hydraulic", "pumping", "pressure gradient"는 0회, "permeab"는 "impermeable wall"(경계조건)뿐. → 이 그룹은 유로 압력 강하를 다루지 않았다.

### 4.2 판단
1. 미세유로 액적 저항 추출(조정자 질문 1)
   - Labrot 2009: 1차원 네트워크(500 × 300 µm, 20 cP 기름, 5~9 mm/s, Re ≈ 0.1)에서 **운동학(경로 선택·간격)으로 저항 길이**를 뽑고 차압계와 비교. 부피·속도 의존은 일치, 점도 의존은 부정확, 좁은 간격에서 과소 [T11, C+F].
   - Sessoms 2009: 같은 루프 방식 + 압력 직접 측정, 밀리·미세, 원·직사각 [T12, C+A]. Vanapalli 2009: 비교기로 단일 액적 초과 ΔP 직접 측정, Ca 10⁻³~10⁻² [T10]. Jakiela 2011: 속도만(360 µm, Ca 10⁻⁴~10⁻¹) [T13]. Fuerstman 2007: 기포 수/길이와 ΔP(간접) [T9].
   - 공통 조건: 1차원 채널(기포·액적이 단면을 채움), Re ≪ 1, 대부분 액-액. 1차원에서는 기포 속도가 질량 보존(막 두께)으로 정해지고 힘 균형으로 정해지지 않는다. 그래서 "속도 → 마찰 계수 → ΔP"의 고리가 2차원과 다르다.
2. mm 규모 기액 좁은 유로(Re 10~1000, 기포 무리)에서 같은 일(질문 2): **찾지 못했다.** 가까운 것은 다음뿐이다.
   - Hele-Shaw 단일·2개 기포 속도(점성액, Re ≪ 1) [P1, P4, P8, P10, P11].
   - 2D 폼(빽빽, Re ≲ 10) [F1~F4].
   - 좁은 직사각 유로에서 영상 변수와 ΔP 동시 측정(모델 입력 아님, 원문 미확인) [K16, K17, Yan 2014].
3. 영상 계면 길이·수 밀도를 직접 입력으로 쓰는 공학 ΔP 모델(질문 3)
   - 1차원: 기포 빈도·속도(Warnier) [T7], 기포 수(Fuerstman) [T9], 슬러그 길이(Kreutzer·Walsh) [T6, T8], 막 수(Terriac, 폼) [F3]. 석유 폼: 라멜라 수 밀도(Hirasaki & Lawson, Kovscek) [F8]. Garimella는 빈도를 상관식으로 넣는다(영상 아님) [T14].
   - 2차원 계면 길이 밀도 Γ(방향 가중)를 넣은 공학 모델: **찾지 못했다.**
4. 결론
   - 가설 2(메니스커스 × Γ)의 **물리 자체는 새롭지 않다**(폼·Taylor 흐름에 선례). 이전 세션의 C0 모델도 Booth 외 2023과 같다.
   - **새로움 후보**: (i) mm 규모 공기-물 평평한 유로(Re 10~1000, 묽은 기포 무리)에서 (ii) 추적한 기포 속도로 Hele-Shaw 힘 균형을 닫아 압력 강하 증가분을 맞춤 없이 예측하고(경로 A), (iii) 영상 Γ·Ca_V로 메니스커스 법칙을 시험하며(경로 B), (iv) 0.3~7 mm로 갇힘이 풀리는 과정을 같은 틀로 보는 것. 넷을 함께 한 연구는 찾지 못했다.
   - 주의: 검색 범위가 영어권 DB 중심이다. 중국·일본·한국 학회지는 체계적으로 보지 못했다. K15·K17 원문을 못 봤다.

## 5. 남은 의문과 사용자에게 확인할 것
- 0.3·0.7 mm 단열 실험: 기포가 갭보다 큰 팬케이크였나(d/H)? 영상(속도 추적 가능한 fps)이 있나? 유량계로 j_L, j_G를 쟀나?
- 채널 방향(수평/수직), 압력 탭 위치(입출구 손실 포함 여부), 유로 폭 W와 길이.
- 물의 순도·계면활성 물질(수돗물, 증류수, 첨가제), 철 바닥의 젖음성(접촉각). 막이 유지되는지가 법칙을 정한다.
- 공기 주입 방식(기포 크기 분포를 정함).
- 확인 못 한 것: Lee & Lee·Kim & Mudawar·Zhang·Li & Wu·Sun & Mishima의 계수, Cantat 2004 원문(내용은 F2·P2 경유), Walsh 계수, K15·K17·P18·P22 원문, Taylor & Saffman 1959의 "다공질에서 기포의 저항" 부분, Cantat 대 Booth의 굳은 계면 값 차이의 원인.

## 6. Q6 계산용 표 (공기-물 20 °C: μ 1.002 mPa·s, σ 0.0728 N/m, ρ 998 kg/m³)

### 6.1 식과 계수
| 항목 | 식 | 계수·범위 | 근거 | 확인 수준 |
|---|---|---|---|---|
| 액체 마찰(층류, 넓은 평판) | dP/dx_L = 12μj_L/H² | 정확해(평행 평판). Re_Dh ≈ 2000 근처까지. 유한 폭 보정은 교과서(Shah & London) | 3.1 유도 + 표준 | 해석해 |
| 메니스커스 압력 점프 | p_b − p = (2σ/H)[1 + βCa_n^(2/3)] + (π/4)σκ | β1 = 3.88, β2 = −1.13 | P1, P5 | C+F |
| 길이당 힘(벽 1개) | f = ξγCa^(2/3) | 깨끗 앞 3.84 / 뒤 1.1(합 4.94), 구름 6.22, 미끄럼 6.82 + 0.94Ca^(1/3)ℓ/r_m | P2 | C+F |
| 원형 팬케이크 1개 마찰 | F_b = 2σR(β1 − β2)·1.6827·Ca_V^(2/3) | 1.6827 = √πΓ(4/3)/Γ(11/6) | P1 | C+F |
| 기포 항 | dP/dx_b = kσCa_V^(2/3)Γ/H | k = 2.68(원형, 법선 속도) / 3.19(투영 길이) | P1, P2 + 계산 | C+F + 계산 |
| 계면 오염 | β×(1~2.52) 또는 힘×(1.26~1.38) + 막 항 1.88ασCa^(1/3)/H² | 포화 β1 9.78, β2 −2.85 | P3, P4, P2 | C+F/C+A |
| 막 두께 | h = 1.337(H/2)Ca^(2/3)/(1 + 3.34Ca^(2/3)) | 굳은 계면 ×4^(2/3) = 3.37 | T1, T5, T7, T3, P4 | C+A/C+F |
| 기포 속도 | Ub^(2/3) = δ(2 − Ub), Ub = V/U | δ = 1.12Ca_U^(1/3)/(H/d), 원형 유지 조건 δ ≪ ε^(−1/3) | P1, P4 | C+F |
| 운동학 폐합 | −dP/dx = (12μ/H²)[j_L + α(2U − V̄)], U ≈ j_L/(1−α) | Hele-Shaw, 묽은 근사 | 3.1 유도 | 유도(검토 필요) |
| Taylor 흐름 관성형 | f = (16/Re)[1 + a(D/L_s)(Re/Ca)^0.33] | a 0.07(깨끗) / 0.17(실험), Ca 3×10⁻³~4×10⁻², Re 150~1400 | T6, T7 | C+F(T7) |
| 적용 한계 | Ca < 5×10⁻³(10%), We ≲ 10, Re_H·H/d ≪ 1, d/H ≳ 2, Bo_b = ρg(H/2)²/σ ≪ 1(대칭 막. 주 세션 정정: 3 mm는 0.30이라 바닥 막이 두껍고, 7 mm 1.65는 떨어짐) | | T1, P2, F7, T17 | C+A~C+F |
| Mishima-Hibiki C | C = 21(1 − e^(−0.319D_h[mm])) | 0.3/0.7/1/3/7 mm(D_h = 2H): 3.6/7.3/9.6/18.3/20.9 | K2 | C(2차) |

### 6.2 결과: 원형 팬케이크, 깨끗한 계면(β1 3.88, β2 1.13), 힘 분해
- R = (기포 항)/(12μj_L/H²) = φ_L² − 1. 같은 d/H, α, j면 H와 무관하다(모든 항 ∝ 1/H²).
- V/j: Booth 식, 배경 U = j_L/(1−α). "×2.52"는 β 둘 다 4^(2/3)배.

| d/H | α | j = 0.05 / 0.2 / 1 m/s: V/j | δ | R(깨끗) | R(×2.52) |
|---|---|---|---|---|---|
| 2 | 0.1 | 0.24 / 0.40 / 0.66 | 0.20 / 0.32 / 0.54 | 0.20 / 0.18 / 0.15 | 0.22 / 0.21 / 0.20 |
| 2 | 0.3 | 0.30 / 0.48 / 0.73 | 0.22 / 0.34 / 0.56 | 0.76 / 0.69 / 0.58 | 0.83 / 0.80 / 0.75 |
| 3 | 0.1 | 0.38 / 0.59 / 0.88 | 0.30 / 0.48 / 0.81 | 0.18 / 0.16 / 0.13 | 0.21 / 0.20 / 0.18 |
| 3 | 0.3 | 0.46 / 0.67 / 0.91 | 0.32 / 0.49 / 0.81 | 0.70 / 0.61 / 0.48 | 0.81 / 0.76 / 0.68 |
| 10 | 0.1 | 0.99 / 1.22 / 1.43 | 0.99 / 1.55 / 2.64 | 0.11 / 0.08 / 0.06 | 0.17 / 0.14 / 0.11 |
| 10 | 0.3 | 0.99 / 1.16 / 1.30 | 0.99 / 1.53 / 2.56 | 0.43 / 0.32 / 0.22 | 0.65 / 0.54 / 0.41 |
| 30 | 0.1 | 1.46 / 1.58 / 1.67 | 2.91 / 4.60 / 7.83 | 0.05 / 0.03 / 0.02 | 0.10 / 0.07 / 0.05 |
| 30 | 0.3 | 1.32 / 1.40 / 1.45 | 2.82 / 4.42 / 7.48 | 0.20 / 0.14 / 0.08 | 0.39 / 0.29 / 0.19 |

- Ca_V = 1.6×10⁻⁴(d/H 2, 0.05 m/s) ~ 2.3×10⁻²(d/H 30, 1 m/s).
- 액체 항 크기(j_L 기준): 0.3 mm 4~125 kPa/m, 0.7 mm 0.7~23 kPa/m, 1 mm 0.4~11 kPa/m, 3 mm 0.04~1.3 kPa/m.
- Re_H·H/d(α 0.1, j = 0.05/0.2/1 m/s)

| H | d/H = 2 | 3 | 10 | 30 |
|---|---|---|---|---|
| 0.3 mm | 8 / 32 / 155 | 5 / 21 / 101 | 1.5 / 6 / 29 | 0.5 / 1.9 / 9 |
| 0.7 mm | 19 / 74 / 362 | 12 / 49 / 236 | 3.5 / 14 / 66 | 1.1 / 4.3 / 22 |
| 1 mm | 27 / 106 / 517 | 18 / 69 / 336 | 5 / 19 / 95 | 1.6 / 6 / 31 |
| 3 mm | 81 / 319 / 1551 | 53 / 208 / 1009 | 15 / 58 / 285 | 4.7 / 19 / 92 |

### 6.3 이전 추정(`estimates_microgap.md` 5장)과의 차이
- 같은 조건(1 mm, d/H = 3, α = 0.3, j = 0.05): 총 dP/dx는 이전 770 + 103 = 873 Pa/m, 여기 518 + 363 = 881 Pa/m로 거의 같다.
- 비율 R은 0.13 vs 0.70이다. 이전 분해(에너지)는 기포 주위 흐름 교란의 소산을 "액체 항"에 넣었고, 힘 분해는 기포 항에 넣는다. **증가분을 말할 때는 φ_L² − 1(액체 단독 j_L 대비)을 쓰자.** 이 값은 분해 방식과 무관하다.
- 이전 추정의 c_r ≈ 1(가정)은 1.13으로 확인됐다. 굳은 계면 c = 12.6은 Booth의 포화 극한(9.78 + 2.85 = 12.63)과 같다. 단 Cantat의 힘 기반 값(6.2~6.8)과 다르다.
- 이전 추정의 속도 모델은 V/j(배경 = j)로 썼다. 묽은 극한에서는 같지만 α = 0.3이면 배경 U = j_L/(1−α)와 차이가 난다(V/j 0.34 vs 0.46).

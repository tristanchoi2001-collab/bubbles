# 주제 8: 계면 면적 수송(IATE)·인구 균형과 합체·분열 — 영상 추적으로 원천항을 직접 재기

작성: 2026-10-23, 문헌 조사 에이전트 8.
확인 수준: `C+F` Crossref + 전문, `C+A` Crossref + 초록, `C` Crossref만(내용은 2차 자료), `U` 미대조. 공통 지침 4장을 따른다.
범위: 갭 H = 0.3, 0.7, 1, 3, 7 mm. 합체·분열 "실험 자료" 자체는 주제 1이 본다. 여기서는 모델(IATE·인구 균형 커널)과 "영상으로 원천항을 직접 재는 일"을 본다.
작업 폴더(검색 원자료, 받은 원문): `<scratchpad>/lit8/` (세션이 끝나면 사라짐).

## 0. 요약
1. **가장 가까운 선행 연구는 Ruiz-Rus, Ern, Roig & Martínez-Bazán(2022, JFM, #B1)이다.** 1 mm 갭 세로 셀에서 갭보다 큰(팬케이크) 기포 무리를 250 fps로 찍고, 자체 알고리즘으로 추적·합체 판정을 해서 크기 쌍별 충돌 빈도 h(D_k, D_k′)와 합체 효율 λ를 직접 쟀다. λ ≈ 80%로 크기·기공률과 무관했다.
   → "얇은 갭에서 영상 추적으로 크기별 합체 커널을 잰다"는 것만으로는 새롭지 않다. 이 논문을 반드시 인용하고 차별점을 세워야 한다.
2. 그 논문에 없는 것: 갭을 바꾼 비교(1 mm 하나), 강제 흐름(정지 액체 속 부력 무리), IATE 원천항과의 대조, 분열(드물어서 안 다룸), 수평 유로, 압력 강하와의 연결, 판정 오차의 정량 보정. 이 조합을 다룬 연구는 찾지 못했다(4장 기록, Scholar 10회·Crossref·J-STAGE).
3. 갇힌 유로 IATE(Sun·Kim·Ishii·Beus 2004, 200×10 mm, #A1·A2)와 좁은 유로 IATE(Shen & Hibiki 2012·2013, 갭 0.993 mm, #A5·A6; 수평은 Liu 등 2023, #A8)는 있다.
   그러나 원천항 검증은 모두 **IAC(계면 면적 농도)의 축 방향 변화**(전도도 탐침 또는 영상)로 했다. 합체·분열 사건을 세어 원천항 하나하나를 맞댄 연구는 없다. 계수는 적분량에 맞춘 값이다(관 자료에서 기존 8개 모델 세트 중 최선 33.5%, 계수를 다시 맞춘 새 모델 17.1%의 IAC 평균 상대 오차, #C6).
4. 기존 IATE의 충돌·분열 항은 거의 모두 난류 소산율 ε^(1/3)에 비례한다(#C1, C2, A1). 0.3~1 mm 갭은 Re_Dh 30~2000의 층류라서 이 전제가 없다.
   얇은 갭의 강제 흐름에서는 **기포 속도가 크기에 따라 단조 증가**해서 쌍은 따라잡아 합체하거나 멀어진다(Keeler 2022, Lawless 2024, #D1·D2). 충돌 기구는 "크기별 속도 차"다 → 추적으로 잰 u(d)로 충돌 빈도를 계수 없이 예측하고, 실측 합체율과 나눠 효율을 구할 수 있다.
5. 팬케이크의 합체 효율은 갭이 들어간 막 모세관수로 정해진다는 이론·실험이 있다(Ohashi 2022: Ca_f = (ηṘ/σ)(R/D)², Chan 2010: Ca_f = (μv/σ)(R₀/h₀)^(3/2), #D3·D4). 같은 접근 속도면 0.3 mm는 3 mm보다 Ca_f가 약 100배 크다 → 갭이 작을수록 효율이 낮아질 수 있다(가설, 검증 대상).
6. **실현성의 핵심 위험은 사건 판정 오차다.** Kearney & Bewley(2020, #E1): 충돌을 90% 넘게 잡으려면 ξ = (프레임당 이동)/(최근접 간격) < 0.2가 필요하다. ξ ≈ 0.5에서는 맞게 잡은 수 = 거짓 검출 수, ξ = 0.4에서는 궤적 오류가 2%뿐인데도 충돌의 절반 넘게 놓친다.
   사용자 트래커의 촬영 조건 지표는 0.47~0.62다(평균 흐름을 빼지 않은 값). 예측 오차 기준(평균 흐름 보정)으로 다시 재고 0.2 아래가 되는 크기·조건만 사건 통계에 써야 한다.
7. 붙어 있지만 아직 합쳐지지 않은 쌍을 분할이 한 덩어리로 내면 "가짜 합체 → 가짜 분열"(flip-flop)이 생긴다. Ruiz-Rus는 "테두리를 공유하지만 안쪽 영역이 따로인 쌍"을 충돌 중으로 따로 분류했다. 사용자 U-Net의 3클래스(내부/경계)로 같은 분류를 할 수 있다. 그러면 효율 λ = 합체 수 / 충돌 수를 바로 얻는다.
8. 사람 표본 감사로 정밀도(PPV)와 재현율을 재면 Rogan–Gladen식(#E4)으로 보정할 수 있다: 참 사건률 ≈ 관측률 × PPV / 재현율. 재현율은 "사건이 아니라고 판정된 접촉 쌍"도 표본으로 봐야 잴 수 있다.

## 1. 문헌 표

### 1-A. 좁은·갇힌 유로의 IATE와 영상 IAC (가장 가까운 것부터)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3~7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| A1 | Sun, Kim, Ishii, Beus (2004) | Modeling of bubble coalescence and disintegration in confined upward two-phase flow | Nucl. Eng. Des. 230(1-3):3-26 | 10.1016/j.nucengdes.2003.10.008 | 수직 상향, 공기-물, 200×10 mm(갭 10 mm), 0.1 MPa | 2그룹 IATE, 5기구(RC 무작위 충돌, WE 후류 포착, TI 난류 충돌 분열, SO 가장자리 떨어짐, SI 표면 불안정). 그룹 2 = 갭 방향으로 눌린 캡 기포. 2그룹 항에 갭 G, 최대 가로 반경 R_t,max2, 폭 W가 들어감. 예: Φ_RC^(2) ∝ ε^(1/3)α₂²R_t,max2^(4/3)/(W²G), Φ_WE^(12,2) ∝ √(gC_D2 G)·α₂a_i1/R_t,max2(2차 인용, Chen 2021 표 5) | 갇힌 유로 IATE의 원조. 갭 10 mm·난류 조건. 0.3~1 mm에서는 거의 모든 기포가 그룹 2가 되고 ε 항의 전제가 깨짐 | C |
| A2 | Sun, Kim, Ishii, Beus (2004) | Model evaluation of two-group interfacial area transport equation for confined upward flow | Nucl. Eng. Des. 230(1-3):27-47 | 10.1016/j.nucengdes.2003.10.014 | A1과 같은 유로, 기포류 11세트 + 캡·처언 난류 13세트 | 1차원 정상 2그룹 IATE + 그룹 2 기공률 수송식. 총 IAC의 평균 상대 차이 7% 이내(초록 기준) | 검증 대상이 IAC 적분값이다(사건 수가 아님) | C+A |
| A3 | Kim, Sun, Ishii, Beus, Lincoln (2003) | Interfacial area transport and evaluation of source and sink terms for confined air–water bubbly flow | Nucl. Eng. Des. 219(1):61-75 | 10.1016/s0029-5493(02)00289-3 | 200×10 mm 기포류 | 측정 IAC의 축 방향 변화로 원천·소멸항 평가(제목 기준, 초록 미확인) | 같은 유로에서 원천항을 자료로 가른 시도 | C |
| A4 | Kim, Ishii, Wu, McCreary, Beus (2002) | Interfacial structures of confined air–water two-phase bubbly flow | Exp. Therm. Fluid Sci. 26(5):461-472 | 10.1016/s0894-1777(02)00152-8 | 단열 직사각 수직 유로, 공기-물 기포류 | **이중 센서 전도도 탐침**으로 국소 기공률·IAC. 벽 피크. IAC 축 방향 발달을 IAT 관점에서 해석. 드리프트 플럭스 C0 = 1.35와 비교(초록 기준, Penn State Pure) | 갇힌 유로 원천항 검증 자료가 탐침 자료임을 확인 | C+A |
| A5 | Shen, Hibiki, Ono, Sato, Mishima (2012) | One-dimensional interfacial area transport of vertical upward bubbly flow in narrow rectangular channel | Int. J. Heat Fluid Flow 36:72-82 | 10.1016/j.ijheatfluidflow.2012.04.007 | 수직 상향, **갭 0.993 mm × 폭 40.0 mm**, 축 방향 7곳, 화상 처리 | 발달 중인 흐름에서 국소 변수 변화가 큼. 기존 IAC 모델을 고쳐 IAC·Sauter 평균 직경 예측(검색 요약 기준) | **1 mm 갭 영상 IAT의 가장 가까운 선행**. 사건 계수는 없음 | C |
| A6 | Shen, Hibiki (2013) | One-group interfacial area transport equation and its sink and source terms in narrow rectangular channel | Int. J. Heat Fluid Flow 44:312-326 | 10.1016/j.ijheatfluidflow.2013.06.010 | 좁은 직사각 유로(A5 자료) | 눌린(crushed) 기포 특성을 넣은 1그룹 IATE. 합체 = 무작위 충돌, 분열 = 난류 에디 충돌로 모델링. 기공률·IAC·직경 자료로 "신뢰할 만함" 평가(KAKEN 23561011 보고서 요약 기준) | 좁은 유로 원천항의 가장 직접적 선행. 층류 갭에서도 난류 기구를 씀 | C |
| A7 | Shen, Hibiki (2025) | Advanced Prediction Method of Interfacial Area Concentration in Gas-Liquid Two-Phase Flow Analysis | JSME 関西支部講演会 2025.100:20304 | 10.1299/jsmekansai.2025.100.20304 | 4센서 탐침(대구경관·봉다발) + **고속 카메라·화상 처리(연구로용 좁은 유로)** | 두 자료로 IAC 구성식 시리즈를 만듦(초록 기준, J-STAGE) | 같은 그룹이 지금도 좁은 유로 영상 자료를 IAC 상관에만 씀 → 경쟁·협력 후보 | C+A |
| A8 | Liu, Cheng, Yan, Gu, Meng (2023) | Characteristics of one-dimensional bubbly flow interfacial area transport in horizontal narrow rectangular channel | Chem. Eng. Res. Des. 189:30-45 | 10.1016/j.cherd.2022.10.039 | **수평** 좁은 직사각 유로 기포류 | 1차원 IAT 특성(초록 미확인) | 수평 좁은 유로 IAT의 유일한 문헌(이번 검색 기준). 갭·계측법 확인 필요 | C |
| A9 | Wilmarth, Ishii (1997) | Interfacial Area Concentration and Void Fraction of Two-Phase Flow in Narrow Rectangular Vertical Channels | J. Fluids Eng. 119(4):916-922 | 10.1115/1.2819517 | 수직, 공기-물, 갭 **1·2 mm** | CCD 영상 + 화상 처리로 국소 평균 기공률·IAC. 양식별 C0·Vgj(초록 기준) | 1 mm 갭 영상 IAC의 가장 오래된 선례. 합체·분열 없음 | C+A |
| A10 | Fu, Liu (2016) | Development of a robust image processing technique for bubbly flow measurement in a narrow rectangular channel | Int. J. Multiphase Flow 84:217-228 | 10.1016/j.ijmultiphaseflow.2016.04.011 | 좁은 직사각 유로 기포류 | 겹친 기포 분리·윤곽 복원, IAC·수 밀도 자동 계산(학위논문 Fu 2018의 Scholar 요약 기준) | 좁은 유로 영상 계측 방법론의 선행 | C |

### 1-B. 일반 IATE·커널 (원천항의 꼴과 계수)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| C1 | Wu, Kim, Ishii, Beus (1998) | One-group interfacial area transport in vertical bubbly flow | Int. J. Heat Mass Transfer 41(8-9):1103-1112 | 10.1016/s0017-9310(97)00167-1 | 수직관 50.8 mm 공기-물 | RC 충돌 빈도 ∝ nε^(1/3)D^(2/3)·6α/(πα_max^(1/3)(α_max^(1/3)−α^(1/3)))·[1−exp(−C…)], C = 3.0, α_max = 0.75, 효율 C_RC = 0.004. TI: We_cr = 6.0, C_TI = 0.085(2차 인용, Chen 2021 표 4) | 1그룹 IATE의 표준형. ε 기반 | C |
| C2 | Hibiki, Ishii (2002) | Development of one-group interfacial area transport equation in bubbly flow systems | Int. J. Heat Mass Transfer 45(11):2351-2372 | 10.1016/s0017-9310(01)00327-1 | 25.4/50.8 mm 관 | 효율 = (C_RC/2)exp(−K_c√(We/2)), C_RC = 0.0314, K_c = 1.29, α_RC,max = 0.741. TI: K_TI = 6.0, C_TI = 0.021(2차 인용, Chen 2021 표 4). 같은 저자의 2000년 관 모델(IJHMT 43:2711-2726, 10.1016/s0017-9310(99)00325-7)이 #C7 비교에서 2위 | 액막 배수형 효율을 넣은 판 | C |
| C3 | Hibiki, Ishii (2000) | Two-group interfacial area transport equations at bubbly-to-slug flow transition | Nucl. Eng. Des. 202(1):39-76 | 10.1016/s0029-5493(00)00286-7 | 관 | 2그룹 IATE 틀. 시작 문헌 목록의 "Hibiki & Ishii 2000 IJHMT(2그룹)"은 실제로 NED에 실림 | 2그룹 틀 | C |
| C4 | Ishii, Hibiki (2011) | Thermo-Fluid Dynamics of Two-Phase Flow (2nd ed.) | Springer (책) | 10.1007/978-1-4419-7985-8 | 교과서 | 10장 IAT(217-242쪽), 11장 IAT 구성식(243-313쪽) | 표준 참고서 | C |
| C5 | Chen, Wei, Ding, Wei, Li, Saxén 외 (2021) | Interfacial Area Transport Equation for Bubble Coalescence and Breakup: Developments and Comparisons | Entropy 23(9):1106 | 10.3390/e23091106 | 리뷰(오픈액세스, Europe PMC PMC8465106) | 1그룹 5종과 2그룹 3유로형(좁은 갇힌 유로 = Sun 2004)의 식·계수 표. "2그룹 IATE 성능은 유로 크기·모양에 강하게 의존" | 원천항 꼴의 1차 정리 자료(C1, C2, A1의 식 출처) | C+F |
| C6 | Shen, Hibiki (2018) | Bubble coalescence and breakup model evaluation and development for two-phase bubbly flows | Int. J. Multiphase Flow 109:131-149 | 10.1016/j.ijmultiphaseflow.2018.07.008 | 수직관 50.8~200 mm, 8개 모델 세트 | IAC 예측 평균 절대 상대 오차: Sun 2004(A1) 33.5%(1위), Hibiki & Ishii 2000 61.7%. 후류 포착을 더하고 계수를 다시 맞춘 새 모델 17.1%(초록 기준) | 원천항 계수가 IAC 적분값에 맞춰지며, 같은 IAC를 다른 기구 조합으로 맞출 수 있음을 보여 줌 → 사건 직접 계측의 필요성 | C+A |
| C7 | Takamasa, Iguchi, Hazuku, Hibiki, Ishii (2003) | Interfacial area transport of bubbly flow under microgravity environment | Int. J. Multiphase Flow 29(2):291-304 | 10.1016/s0301-9322(02)00129-5 | 미소중력, 질소-물, 9 mm 관, 축 방향 4곳 | **화상 처리**로 기공률·수 밀도·IAC·Sauter 직경의 축 방향 발달 측정(학회판 초록 기준, 10.1115/fedsm2003-45160) | 영상 기반 IAT도 "축 방향 발달" 방식이었음을 보여 주는 예 | C |
| C8 | Prince, Blanch (1990) | Bubble coalescence and break-up in air-sparged bubble columns | AIChE J. 36(10):1485-1499 | 10.1002/aic.690361004 | 기포탑 | 합체 = 난류·부력·**층류 전단** 충돌 × 효율. 합체·분열 사건을 추적 기체 혼합 + 몬테카를로로 측정(초록 기준) | 층류 전단 충돌항이 이미 있음 → 층류 갭의 출발점. 사건 측정이 영상이 아님 | C+A |
| C9 | Liao, Lucas (2010) | A literature review on mechanisms and models for the coalescence process of fluid particles | Chem. Eng. Sci. 65(10):2851-2864 | 10.1016/j.ces.2010.02.020 | 리뷰 | 합체 기구·효율 모델 정리(내용 미확인) | 커널 표준 리뷰 | C |
| C10 | Liao, Lucas (2009) | A literature review of theoretical models for drop and bubble breakup in turbulent dispersions | Chem. Eng. Sci. 64(15):3389-3406 | 10.1016/j.ces.2009.04.026 | 리뷰 | 난류 분열 커널 정리(내용 미확인) | 커널 표준 리뷰. 층류 갭에는 직접 못 씀 | C |

### 1-C. 합체·분열을 영상으로 센 연구 (좁은 유로·2차원·기타)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| B1 | Ruiz-Rus, Ern, Roig, Martínez-Bazán (2022) | Coalescence of bubbles in a high Reynolds number confined swarm | J. Fluid Mech. 944:A13 (오픈액세스) | 10.1017/jfm.2022.492 | 세로 셀 800×400 mm, **갭 1 mm**, 증류수 정지, 기공률 2.4~6.7%, δ₀ = 갭/D₀ = 0.24~0.29, Ar₀ 630~850, 250 fps, 1024×512 px, 350 µm/px, 25 s 영상 | 위치당 기포 기록 2만~7.5만. 검출 기포의 99% 넘게 추적. 충돌 = 테두리 공유 + 안쪽 영역 분리로 판정. 크기 쌍별 h(D_k, D_k′)와 λ 측정. **λ∞ ≈ 80%, 크기 쌍 간 차이 < 5%, 기공률·위치와 무관**. h는 2 영역(작은 쌍: D_p에 비례하는 교반 지배, 큰 쌍: 변형 지배로 감소). D_p = 2D_kD_k′/(D_k+D_k′), D_V90, α가 지배. 분열은 드묾. 기포가 주입 크기의 10배까지 자람. IATE 언급 없음 | **가장 가까운 선행.** 같은 측정을 했지만 갭 1개, 정지 액체, 부력 무리, 분열 없음 | C+F |
| B2 | Zhang, Liu, Liu, Chen (2022) | Prediction of sliding bubble coalescence rate during subcooled flow boiling in narrow rectangular channel | Int. J. Heat Mass Transfer 196:123244 | 10.1016/j.ijheatmasstransfer.2022.123244 | 좁은 직사각 유로, 과냉 흐름 비등, 4면 가시화 | 합체 순간 접촉 속도가 미끄럼 중 크기 변화로 커짐. 충돌은 부력 차이·난류에서. 좁은 유로용 충돌 빈도 상관식 + 임계 속도 모델로 합체율 ±25%(SSRN판 초록 기준, 10.2139/ssrn.4113805) | 좁은 유로 + 영상 + 합체율 모델. 단 비등 미끄럼 기포, 수직, 분열 없음 | C+A |
| B3 | Zhang, Liu, Liu, Zhou, Chen (2021) | Experimental investigation on sliding bubble coalescence of subcooled flow boiling in rectangular narrow channel | Int. J. Heat Mass Transfer 165:120681 | 10.1016/j.ijheatmasstransfer.2020.120681 | B2와 같은 장치 | 합체 뒤 환상파 → 2차 기포 생성. 2차 기포가 생기는 초기 평균 직경 약 0.87 mm. 합체 뒤 진동 조정 구간(격렬·완화 두 단계, 길이 비슷)(초록 기준) | 합체 직후 짧은 분열(2차 기포)이 있음 → 판정 규칙에 영향 | C+A |
| B4 | Ren, Zhu, Zhang, Shi, Yan (2020) | Visualization Experiment of Bubble Coalescence in a Narrow Vertical Rectangular Channel | Front. Energy Res. 8:96 | 10.3389/fenrg.2020.00096 | 700×40×**2 mm**, 과냉 흐름 비등, 4300 fps, 시야 10.28×10.28 mm | 합체 4단계(접근·병합·조정·안정). 기포는 가열면을 따라 미끄러지며 떨어지지 않음. 합체 중 새 작은 기포 생성 | 2 mm 갭 단일 사건 형태. 빈도 없음 | C+F |
| B5 | Kurimoto, Ito, Hayashi, Tomiyama (2026) | Breakup of single planar bubbles rising through stagnant liquids | Multiphase Sci. Technol. 38(1):1-20 | 10.1615/multscientechn.2026063937 | 두 평판 사이 평면(팬케이크) 기포, 정지 액체 | 분열 2유형: 표면장력파형(지그재그 운동) / 동압형(직진 운동, 앞머리 섭동). 둘 다 Morton 수가 크면 확률 감소. **갭이 작을수록 동압형 확률 감소**(종단 속도 감소). 섭동 파장 > Rayleigh–Taylor 임계 파장(초록 기준) | 갇힌 기포 분열 기구와 갭 의존의 직접 근거 | C+A |
| B6 | Hlawitschka, Schleiffer, Schurr, Winkler, Danner (2025) | Coalescence investigations in a small-scale continuously operated setup for bubble column design | Can. J. Chem. Eng. 103(4):1902-1916 | 10.1002/cjce.25458 | 연속 운전 마이크로 채널 합체 셀, 알코올·전해질 수용액·실리콘유 | 합체 데이터베이스용 장치. **AI로 자료 생성 자동화**(초록 기준). StarDist 분할 + 추적으로 합체 판정(Scholar 요약 기준) | "AI + 합체 계측" 선행. 단 두 기포 합체 확률 셀이지 흐름 속 커널이 아님 | C+A |
| B7 | Laari, Turunen (2003) | Experimental Determination of Bubble Coalescence and Break-up Rates in a Bubble Column Reactor | Can. J. Chem. Eng. 81(3-4):395-401 | 10.1002/cjce.5450810309 | 기포탑 | 여러 높이의 사진 기포 크기 분포 → 인구 균형 역산으로 커널 계수 추정(초록 기준) | 분포 변화로 역산하는 간접법의 예 | C+A |
| B8 | Liu, Wang, Wu, Fu, Duan, Zhou (2026) | Bubble dynamics in bubbling fluidized beds of porous particles based on semantic segmentation | Chem. Eng. Sci. 331:124008 | 10.1016/j.ces.2026.124008 | 2차원 기포 유동층 | 의미 분할 + 추적 변화로 기포 사건을 검출하고 합체·분열 사건 수를 셈(Scholar 요약 기준) | 다른 분야(기고 유동층)에서는 AI 사건 계수가 이미 쓰임 | C |

### 1-D. 얇은 갭(Hele-Shaw) 팬케이크 기포·방울의 상호작용과 합체, 2차원 폼
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| D1 | Keeler, Gaillard, Lawless, Thompson, Juel, Hazel (2022) | The interaction of multiple bubbles in a Hele-Shaw channel | J. Fluid Mech. 946 | 10.1017/jfm.2022.618 | 점성 액체 흐름으로 밀리는 Hele-Shaw 채널, 두 기포, 실험 + 깊이 평균 모델 | 단일 기포 속도는 부피에 따라 단조 증가 → 크기가 다른 두 기포는 유한 시간에 합체하거나 멀어짐. 불안정한 두 기포 정상 상태가 결과를 가름(초록 기준) | **압력 구동 갭 흐름의 충돌 기구 = 크기별 속도 차**의 직접 근거 | C+A |
| D2 | Lawless, Keeler, Hazel, Juel (2024) | Stable bubble formations in a depth-perturbed Hele-Shaw channel | Phys. Rev. Fluids 9(9):093605 | 10.1103/physrevfluids.9.093605 | 다분산 기포, 일정 유량 Hele-Shaw 채널 | 평평한 채널에서는 이웃 쌍이 반드시 멀어지거나 합체. 무리는 크기 순으로 재배열되고 안정한 다기포 상태가 없음. 깊이의 1% 정도 턱이 있으면 안정 상태가 생김(초록 기준) | 갭 균일도(덮개 처짐, 홈 있는 철 바닥)가 합체율을 바꿀 수 있음 | C+A |
| D3 | Ohashi, Toramaru, Namiki (2022) | Coalescence of two growing bubbles in a Hele–Shaw cell | Sci. Rep. 12 | 10.1038/s41598-022-05252-5 | Hele-Shaw, 감압으로 자라는 두 기포, 점도·감압률·갭 변화 | 막 모세관수 Ca_f = (ηṘ/σ)(R/D)²가 합체 직전 변형을 정함. 공칭 Ca_f가 임계값보다 작을 때만 합체(초록 기준) | 갭 D가 (R/D)²로 들어감 → 갭별 효율 차이의 근거 | C+A |
| D4 | Chan, Klaseboer, Manica (2010) | Dynamic interactions between deformable drops in the Hele–Shaw geometry | Soft Matter 6(8):1809 | 10.1039/b918933e | Hele-Shaw 속 두 변형 방울 충돌 모델 | 막 모세관수 Ca_f = (μv/σ)(R₀/h₀)^(3/2). 합체 여부는 상호작용의 전체 이력에 의존. 간격 측정으로 힘을 역산할 수 있음(초록 기준, arXiv 0912.5136) | 접근 이력(속도)이 효율을 정함 → 크기별 상대 속도 측정이 필요 | C+A |
| D5 | Yokota, Okumura (2011) | Dimensional crossover in the coalescence dynamics of viscous drops confined in between two plates | PNAS 108(16):6395-6398 | 10.1073/pnas.1017112108 | 두 판 사이 점성 방울 | 목 폭이 처음엔 시간에 선형, 뒤에 느려짐. 3D(구) → 준2D(원판) 교차(초록 기준) | 팬케이크 합체 시간의 갭 의존 | C+A |
| D6 | Okumura (2018) | Viscous dynamics of drops and bubbles in Hele-Shaw cells: Drainage, drag friction, coalescence, and bursting | Adv. Colloid Interface Sci. 255:64-75 | 10.1016/j.cis.2017.07.021 | 리뷰 | 갇힘이 3D와 다른 스케일링 영역을 만든다. 배수·항력·합체·파열의 스케일링 정리(초록 기준) | Q3 개관 | C+A |
| D7 | Lai, Bremond, Stone (2009) | Separation-driven coalescence of droplets: an analytical criterion for the approach to contact | J. Fluid Mech. 632:97-107 | 10.1017/s0022112009007320 | 미세유로 2차원 모델 | 분리할 때 합체. 무차원수 A = 4CμR²α^(1/2)/(πγ h₀(0)^(3/2)), 임계 A_crit = 16/3^(3/2) ≈ 3.08 아래에서는 분리가 합체를 돕기 어려움(초록 기준) | 판정 규칙: 접촉 직후가 아니라 떨어질 때 합체하는 경우도 셈 | C+A |
| D8 | Bremond, Thiam, Bibette (2008) | Decompressing Emulsion Droplets Favors Coalescence | Phys. Rev. Lett. 100(2):024501 | 10.1103/physrevlett.100.024501 | 미세유로 방울 쌍 열 | 합체는 충돌 때가 아니라 **분리 단계**에서 일어남. 분리 때 마주 보는 돌기가 생겨 연결. 밀집계에서 합체 연쇄(초록 기준, HAL) | D7과 같음. 연쇄 → 사건이 독립이 아님 | C+A |
| D9 | Biance, Delbos, Pitois (2011) | How Topological Rearrangements and Liquid Fraction Control Liquid Foam Stability | Phys. Rev. Lett. 106(6):068301 | 10.1103/physrevlett.106.068301 | 폼, 두 기포 실험 포함 | 위상 재배열(T1)과 막 망의 액체량이 임계값보다 적을 때 합체. 재배열 중 일시적 두꺼운 막이 생기고, 국소 액체가 부족하면 파열(초록 기준, HAL API) | 밀집 팬케이크(거품 무리)에서는 충돌이 아니라 재배열이 합체를 부름 | C+A |
| D10 | Ritacco, Kiefer, Langevin (2007) | Lifetime of Bubble Rafts: Cooperativity and Avalanches | Phys. Rev. Lett. 98(24):244501 | 10.1103/physrevlett.98.244501 | 준2차원 기포 뗏목 | 첫 파열 뒤 파열 연쇄(사태). 어떤 점도 범위에서 사태 크기 분포가 거듭제곱 법칙(초록 기준, HAL API) | 사건이 무리 지어 일어나면 포아송 오차가 과소평가됨 | C+A |

### 1-E. 추적 오차·사건 판정·표본 감사 (Q5)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| E1 | Kearney, Bewley (2020) | Lagrangian tracking of colliding droplets | Exp. Fluids 61(7) | 10.1007/s00348-020-02991-x | 3차원 입자 추적 + 충돌(합체)·분열 검출, DNS 합성 자료로 검증 | 추적 난이도 ξ = δx/δd(프레임당 이동/최근접 간격). **충돌 검출 95%는 ξ < 0.2에서만**. ξ ≈ 0.5에서 맞게 잡은 충돌 수 = 거짓 충돌 수. ξ = 1에서 C_g ≈ 0.01. ξ = 0.4에서 불완전 궤적은 2%인데 충돌은 절반 넘게 놓침. E_track < 0.1은 ξ < 0.7, C_g > 0.9는 ξ < 0.2 필요(arXiv 2006.06593 전문) | **사건률 측정의 촬영 조건 기준.** 궤적 품질보다 사건 검출이 훨씬 엄격 | C+F |
| E2 | Ouellette, Xu, Bodenschatz (2006) | A quantitative study of three-dimensional Lagrangian particle tracking algorithms | Exp. Fluids 40(2):301-313 | 10.1007/s00348-005-0068-7 | 추적 알고리즘 비교(DNS 궤적) | 새 4프레임 예측 알고리즘이 가장 좋음(초록 기준). 최근접 이웃이 가장 나쁨(E1 본문의 요약). E1이 같은 오차 지표(불완전 궤적 비율)를 씀 | 예측(속도) 기반 추적의 필요성 | C+A |
| E3 | Jaqaman 외 (2008) | Robust single-particle tracking in live-cell time-lapse sequences | Nat. Methods 5(8):695-702 | 10.1038/nmeth.1237 | 세포 내 입자 | 프레임 간 연결 → 궤적 조각 연결을 전역 조합 최적화로 풀며, 고밀도·일시 소실·**합체·분열**을 함께 다룸(초록 기준) | 합체·분열을 LAP 틀 안에서 판정하는 표준 참고 | C+A |
| E4 | Rogan, Gladen (1978) | Estimating prevalence from the results of a screening test | Am. J. Epidemiol. 107(1):71-76 | 10.1093/oxfordjournals.aje.a112510 | 역학 | 민감도·특이도를 알면 관측 양성률에서 참 비율을 보정(교과서적 식, 원문 미확인) | 사람 표본 감사로 잰 정밀도·재현율로 사건 수를 보정하는 근거 | C |

## 2. 핵심 질문에 대한 답

### Q1. 좁은 직사각 유로 IATE의 원천항 꼴과 계수, 갭 < 기포(팬케이크)에서의 변화
- **표준 1그룹형**(C1, C2; C5 표 4, 확인 수준 C)
  - 합체 = 충돌 빈도 × 효율. 충돌 빈도는 난류 관성 영역의 에디 속도((εD)^(1/3))를 충돌 속도로 쓴다. Chen 2021 표 4의 정규화로 f_coll/(n(εD²)^(1/3)) = 6α/(πα_max^(1/3)(α_max^(1/3)−α^(1/3)))·[1−exp(…)](Wu 1998), α/(α_RC,max−α)(Hibiki & Ishii 2002). 최대 충전율 α_max 0.741~0.75.
  - 효율은 상수(Wu 1998: 0.004) 또는 액막 배수형 exp(−K_c√(We/2))(Hibiki & Ishii 2002: C_RC 0.0314, K_c 1.29).
  - 분열(TI) = 에디 충돌 × exp(−We_cr/We), We_cr = 6.0, C_TI = 0.085(Wu) 또는 0.021(H&I).
  - 후류 포착(WE, 그룹 1) = −0.27·C_WE·C_D^(1/3)·v_r·a_i²(Sun 2004의 그룹 1 항, Chen 2021 표 5).
- **갇힌 유로 2그룹형**(A1, 갭 G = 10 mm, 폭 W = 200 mm; C5 표 5에서 식 확인, C)
  - 그룹 1 = 갭보다 작은 구·변형 기포, 그룹 2 = 갭 방향으로 눌린 캡 기포. 2그룹 항에 G, R_t,max2(그룹 2의 최대 가로 반경), W가 들어간다.
  - 갭은 그룹 2 기포의 부피(≈ 투영 면적 × G)와 상승 속도 척도 √(gC_D G)에 들어간다(해석). RC, TI, SI 항은 여전히 ε^(1/3) 기반이다.
  - 평가: 24세트에서 총 IAC 평균 차이 7% 이내(A2, C+A). 다른 자료(관)에서는 33.5% 오차(C6, C+A).
- **좁은 유로(갭 약 1 mm) 1그룹형**(A6, Shen & Hibiki 2013, C): 눌린 기포 특성을 넣었지만 합체 = 무작위 충돌, 분열 = 난류 에디 충돌로 그대로 썼다(KAKEN 요약 기준).
- **수평 좁은 유로**는 Liu 등(2023, A8)뿐이다. 식과 갭은 확인하지 못했다.
- **0.3~1 mm 갭에서 바뀌는 것**(문헌 근거 + 이 조사의 해석)
  1. 난류가 없다. Re_Dh 30~2000(estimates 3장)이라 ε 기반 RC·TI 항의 전제가 성립하지 않는다. 기존 계수(C_RC, C_TI)를 그대로 옮길 근거가 없다.
  2. 충돌 기구는 **크기별 속도 차(따라잡기)**가 된다. 압력 구동 Hele-Shaw 채널에서 기포 속도는 부피에 따라 단조 증가하고, 쌍은 합체하거나 멀어진다(D1·D2, C+A). Prince & Blanch(C8)의 층류 전단 충돌항도 같은 계열이다.
     - 2차원에서는 충돌 단면이 넓이가 아니라 길이다. 제안: h_ij ≈ (d_i + d_j)·|u_i − u_j|·(접근 확률). u(d)는 추적으로 잰다(유도, 문헌 아님).
  3. 효율은 갭이 들어간 막 모세관수로 정해진다(D3: (R/D)², D4: (R₀/h₀)^(3/2), C+A). 부력 무리의 1 mm 갭에서는 λ ≈ 0.8로 높고 일정했다(B1, C+F).
  4. 분열은 난류 충돌이 아니라 앞머리 섭동(동압)과 표면장력파로 일어난다. 갭이 작으면 동압형이 줄어든다(B5, C+A). 1 mm 갭 무리에서는 분열이 드물었다(B1).
  5. **계면 면적 자체가 합체에 둔해진다**(이 조사의 계산). 팬케이크(반지름 R, 갭 H, 가장자리를 반원으로 근사)의 계면은 위아래 면 2πR² + 가장자리 π²HR이다.
     같은 크기 둘이 합쳐져도 면 넓이는 보존되고 가장자리만 줄어든다. 줄어드는 비율은 0.586πH/(4R + 2πH)로, R/H = 2·5에서 13%·7%다. 구 두 개가 합쳐질 때는 21%다.
     → 얇은 갭에서는 IAC보다 **수 밀도 n과 가장자리(둘레) 길이 밀도 Γ**가 합체·분열에 민감하다. 영상은 사건마다 Δn, ΔΓ를 바로 준다. 둘레 기반 수송식을 다룬 문헌은 찾지 못했다(4장).

### Q2. 원천항 검증에 무엇을 쟀나, 영상으로 빈도를 직접 잰 연구가 있나
- **갇힌·좁은 유로 IATE의 검증은 IAC 축 방향 변화였다.**
  - 같은 갇힌 유로의 자료는 전도도 탐침(Kim 2002: 이중 센서)으로 잰 국소 IAC·기공률이다(A2, A4, C+A). Sun 2004b는 그 24세트의 총 IAC로 평가했다.
  - Shen 등 2012·2013(갭 0.993 mm)과 Shen & Hibiki 2025는 고속 카메라 + 화상 처리로 축 방향 7곳의 IAC·직경을 쟀다(A5·A7, C/C+A). 영상이지만 사건 수가 아니라 적분량이다.
  - 미소중력 IAT(C7)도 화상 처리로 축 방향 4곳의 발달을 쟀다.
- **사건을 직접 센 연구**
  - 기포탑: Prince & Blanch 1990은 추적 기체 혼합(C8). Laari & Turunen 2003은 크기 분포 역산(B7).
  - 얇은 갭: Ruiz-Rus 2022가 추적으로 충돌·합체를 세어 h, λ를 크기 쌍별로 냈다(B1, C+F). **유일한 직접 사례**(이번 검색 기준).
  - 좁은 유로 비등: Zhang 2021·2022가 미끄럼 기포 합체를 영상으로 보고 합체율 모델(±25%)을 냈다(B2·B3, C+A).
  - 다른 분야: 기포 유동층에서 의미 분할 + 추적으로 합체·분열 수를 센다(B8, C). 합체 셀에서 AI로 자료를 자동 생성한다(B6, C+A).
- **결론**: 영상 추적으로 센 합체·분열률을 **IATE 원천항(특히 갇힌 유로 항)과 직접 맞댄 연구는 찾지 못했다.** Ruiz-Rus도 IATE가 아니라 인구 균형 커널(h, λ)로 정리했다.

### Q3. 얇은 갭 팬케이크의 합체: 배수 시간, 접촉 시간, 효율
- 팬케이크 사이 액막의 배수는 갭에 묶인다. 막 모세관수가 임계값보다 작을 때만 합체한다(D3, C+A).
  - 크기 감: 물(η = 1 mPa·s, σ = 0.073 N/m), R = 2 mm, 접근 속도 0.01~0.1 m/s이면 Ca_f = (ηv/σ)(R/H)²는 H = 0.3 mm에서 0.006~0.06, 1 mm에서 0.0006~0.006, 3 mm에서 0.00006~0.0006이다(직접 계산).
  - 임계값은 초록에 없다. 성장형 접근(마그마 모사, 점성 액체) 실험이라 물 흐름에 그대로 옮기는 것은 가설이다.
- 합체 여부는 접근 이력에 달려 있다(D4). 갇힌 방울은 충돌할 때보다 **떨어질 때** 합체하는 경우가 있다(D7·D8, A_crit ≈ 3.08).
- 목(neck)의 성장은 3D → 준2D로 바뀌며 느려진다(D5). 물에서 관성-모세관 시간 √(ρR³/σ)은 R = 1 mm에서 약 3.7 ms, 5 mm에서 약 41 ms다(직접 계산).
- 1 mm 갭 부력 무리의 측정 효율은 λ ≈ 0.8, 크기·기공률과 무관했다(B1). 이전 같은 장치에서는 합체가 억제되어 있었다(B1이 Bouche 2012·2014를 인용) → 물의 순도·첨가물이 효율을 크게 바꾼다.
- 2차원 폼·뗏목: 재배열(T1)과 액체량이 합체를 정하고(D9), 파열은 사태로 연쇄된다(D10). 사용자의 5~8 px 미세 거품 무리에 해당한다. 이 무리는 개별 추적이 안 되므로(CLAUDE.md, 간격 약 10 px·이동 약 50 px/프레임) 사건 통계에서 빼야 한다.

### Q4. 새로움 판단
- **주장 그대로("AI 추적으로 0.3~7 mm 갭의 합체·분열률을 크기별로 직접 재고, 좁은 유로 IATE 원천항(갇힘 효과)을 검증·보정")는 새로움 "중간"이다.**
  - 낮아지는 이유: 얇은 갭에서 영상 추적으로 크기 쌍별 충돌 빈도·효율을 잰 직접 선례가 있다(B1). 다른 분야에는 AI 사건 계수도 있다(B6, B8). 좁은 유로 영상 IAT 자료도 있다(A5, A7, A9, A10).
  - 남는 새로움(찾지 못한 것)
    1. **갭 묶음(0.3~7 mm, Co = 9.1 → 0.39)에서 h, λ, 분열률의 갭 의존**: 선례는 갭 1개(1 mm)뿐이다.
    2. **압력 구동(강제) 흐름, 수평 유로**: 선례는 정지 액체 속 부력 무리다. 강제 흐름의 충돌 기구(크기별 속도 차, D1·D2)로 h를 계수 없이 예측하고 실측과 비교한 연구는 없다.
    3. **IATE 원천항과의 직접 대조**: Sun 2004(A1)의 G 의존 항, Shen & Hibiki 2013(A6)의 항을 사건 단위 측정으로 하나씩 시험한 연구는 없다. 기존 검증은 IAC 적분값뿐이다(A2, C6).
    4. **둘레(Γ)·수 밀도 기반 원천항**: 팬케이크에서는 IAC가 합체에 둔하다(Q1-5). 사건마다 ΔΓ를 재서 압력 강하 가설(estimates 5장, 메니스커스 마찰 ∝ Γ)과 같은 변수로 묶는 틀은 찾지 못했다.
    5. **사건 판정 오차의 정량 보정**: 사람 표본 감사로 PPV·재현율을 재고 사건률을 보정한 기포 연구는 찾지 못했다. Kearney & Bewley(E1)는 합성 자료로만 오차를 쟀다.
  - 정리: "갭이 갇힘 → 자유를 가로지를 때 합체·분열 커널이 어떻게 바뀌는가"를 **강제 흐름에서, 오차 보정된 사건 수로** 보여 주고 IATE 갇힘 항을 시험하면 새로움 "중간~높음"이다. 1~4 중 둘 이상을 갖춰야 한다.
- **가장 가까운 선행 5편**
  1. Ruiz-Rus 외 2022(B1): 같음 = 얇은 갭, 팬케이크, 추적·합체 판정, 크기별 h·λ. 다름 = 갭 1개, 정지 액체·부력, 분열 없음, IATE 없음, AI 아님, 압력 강하 없음.
  2. Sun 외 2004(A1·A2): 같음 = 갇힌 유로 2그룹 IATE, 갭이 들어간 원천항. 다름 = 갭 10 mm·난류, 탐침 IAC로만 검증.
  3. Shen & Hibiki 2012·2013(A5·A6): 같음 = 약 1 mm 갭, 영상, IATE. 다름 = 수직, 사건 수 없음, 난류 기구.
  4. Zhang 외 2021·2022(B2·B3): 같음 = 좁은 유로, 영상, 합체율 모델. 다름 = 비등 미끄럼 기포, 수직, 분열 없음, 갭 변화 없음.
  5. Keeler 2022 / Lawless 2024(D1·D2): 같음 = 강제 흐름 Hele-Shaw의 크기별 속도 → 합체/분리. 다름 = 두세 기포 이론·실험, 통계·커널 없음.
- 새로움 판단에 쓴 검색은 4장에 있다.

### Q5. 실현성: 판정 오차 민감도, 프레임 속도·표본 수, 사람 감사
- **판정 오차 민감도**(E1, C+F)
  - 사건 검출은 궤적보다 훨씬 엄격하다. C_g > 0.9에는 ξ < 0.2, 궤적 E_track < 0.1에는 ξ < 0.7이면 된다. ξ ≈ 0.5에서는 거짓 충돌 = 참 충돌이다.
  - 사용자 트래커 기록(옛 투명 채널 자료, CLAUDE.md): 촬영 조건 지표(다음 프레임 최근접 ÷ 같은 프레임 최근접) 0.47~0.62. 이것은 평균 흐름을 빼지 않은 ξ에 해당한다.
    속도 예측을 쓰면 실효 ξ는 더 작다(예: large 예측 위치 오차 중앙값 4.6 px). 그러나 tiny/small은 예측 오차 기준 초과가 74%/42%였다.
  - 권장: 크기 구분별로 **ξ_res = (예측 위치 오차)/(최근접 간격)**의 분포를 보고, ξ_res < 0.2인 크기·조건만 커널 추정에 쓴다. 나머지는 "검출 한계 밖"으로 보고한다.
  - 프레임 속도: ξ_res < 0.2가 되도록 f ≥ 5·Δu/s(Δu = 이웃과의 상대 속도 또는 예측 오차 속도, s = 최근접 간격). 예: Δu = 0.1 m/s, s = 5 mm이면 100 fps 이상(직접 계산). B1은 부력 무리에 250 fps를 썼다.
- **가짜 합체·분열(flip-flop)**: 붙은 쌍을 분할이 하나로 내면 합체 → 분열이 연달아 기록된다(합성 자료에서 붙은 쌍 융합 28~39%, CLAUDE.md).
  - 대책 1: B1처럼 "경계 공유 + 안쪽 영역 2개"를 충돌 중으로 분류한다. U-Net의 내부/경계 클래스가 그대로 쓰인다. 그러면 λ = 합체/충돌을 직접 얻는다.
  - 대책 2: 합체는 합친 기포가 N 프레임 이상 유지되고 면적이 보존될 때만 인정한다(팬케이크는 면적 ∝ 부피). 합체 직후 2차 기포 생성(B3)과 분리 때 합체(D7·D8)도 규칙에 넣는다.
- **표본 수**: 사건 수가 포아송이면 상대 오차 ≈ 1/√N. 크기 4구분 → 쌍 10개, 쌍마다 100건이면 약 1000건(±10%).
  - 옛 투명 채널 실데이터의 합체는 프레임당 1.7~3.9건이었다(CLAUDE.md 리서치 메모). 같은 수준이면 300~600 프레임이면 된다. 철 채널 값은 아직 모른다.
  - 사건이 사태처럼 몰리면(D10) 포아송 오차가 과소평가된다. 시간 블록 부트스트랩으로 구간을 낸다.
- **사람 표본 감사로 보정**
  - 관측 사건 중 무작위 표본으로 PPV(맞은 비율)를 잰다. 재현율은 "사건 아님"으로 판정된 접촉·근접 쌍과 끊긴 궤적 쌍을 표본으로 봐야 잴 수 있다.
  - 보정: 참 사건률 ≈ 관측률 × PPV / 재현율(Rogan–Gladen 계열, E4). 비율 구간은 이미 감사 도구가 쓰는 Wilson 구간을 쓴다.
  - 독립 점검: 두 창 사이 수 밀도·둘레의 변화(오일러)와 그 사이에서 센 사건의 합(라그랑주)이 맞아야 한다(수지 맞추기). 안 맞는 양이 미검출·오검출의 상한을 준다. B1도 개체군 변화율을 사건과 함께 보였다.
  - 합성 자료(정답 ID가 있는 old/sim_*)에 합체·분열을 넣어 C_g, C_b를 ξ_res별로 재는 E1 방식의 검증도 할 수 있다.

## 3. 아이디어와 시사점
- **추천 틀**: "갭이 모세관 길이를 가로지를 때 팬케이크 합체·분열 커널의 변화 — 강제 흐름, 오차 보정된 사건 수, IATE 갇힘 항 시험".
  - 측정: 크기별 속도 u(d/H), 충돌 수(경계 공유 쌍), 합체 수, 분열 수, 사건마다 Δn·ΔA·ΔΓ.
  - 모델: h_ij = (d_i + d_j)|u_i − u_j|(2차원 따라잡기) → λ_ij = 실측 합체율/h_ij. 갭별 λ를 막 모세관수 Ca_f(D3·D4)로 정리해 본다.
  - IATE 시험: Sun 2004 항(G 의존)과 Shen & Hibiki 2013 항을 같은 조건으로 계산해 사건 단위 실측과 비교한다. 0.3~1 mm에서 ε 기반 항이 틀리는 것을 보이는 것만으로도 결과가 된다.
  - 압력 강하·열전달과 연결: 같은 Γ가 메니스커스 마찰 항(estimates 5장)에 들어간다. "사건이 Γ를 바꾸고, Γ가 ΔP를 바꾼다"는 고리를 보일 수 있다.
- **필요한 자료**: 갭별 영상(유량 여러 점), 화소당 mm, 물의 성분(수돗물/증류수, 계면활성 오염), 유로 방향, 기포 주입 방식(공기 주입 노즐 크기 → 초기 크기 분포).
- **위험**
  - 0.3·0.7 mm에서는 거의 모든 기포가 양쪽 벽에 닿는다. 접촉선 고정(철 바닥의 홈, 젖음성)이 합체를 바꿀 수 있다. 갭 균일도(1% 턱도 영향, D2)도 변수다.
  - 7 mm에서는 기포가 덮개 밑에 떠서 겹쳐 보일 수 있다. 투영 영상에서 합체와 겹침을 가르기 어렵다.
  - 물의 순도에 따라 효율이 크게 바뀐다(B1, C8). 실험 사이 물 관리가 필요하다.
  - 미세 거품 무리(5~8 px)는 추적 불가 → 커널은 일정 크기 이상만 낸다.

## 4. 새로움 판단 기록
| 도구 | 검색어 | 결과 수 | 메모 |
|---|---|---|---|
| Scholar S1 | "interfacial area transport" "narrow rectangular channel" coalescence breakup (2010~) | 18 | IATE 적용·IAC 측정·CFD뿐. 영상으로 합체·분열 빈도를 센 연구 없음 |
| Scholar S2 | "coalescence frequency" "breakup frequency" "interfacial area transport" "high-speed" images bubbles | 6 | Smith 2002 학위논문, Lehr 2002 등. 좁은 유로 없음 |
| Scholar S3 | "Hele-Shaw" OR "thin gap" bubbles "coalescence rate" OR "coalescence frequency" tracking population balance | 7 | 관련 없음 |
| Scholar S4 | bubble tracking "coalescence and breakup" events "deep learning" OR "neural network" image statistics (2019~), 2쪽까지 | 53 | 유동층 AI 사건 계수(B8 등), 합체 셀 AI(B6), GNN 추적. 좁은 갭 기액 흐름 없음 |
| Scholar S5 | "narrow channel" OR "Hele-Shaw" OR "narrow gap" bubbles "coalescence rate" OR "breakup rate" "image processing" "interfacial area" (2015~) | 14 | **B1 발견**, B2, Kumar 2026(난류 덕트, 갭 아님) |
| Scholar S6 | B1 제목 → 인용 38(목록 34~37), 3쪽 모두 확인 | 34 | B5, D2, Yeo & Park 2024(2차원 기포 사슬), 얇은 갭 광생물반응기 등. 갭 변화 커널·IATE 시험은 없음 |
| Crossref | 주제 질의 약 25개(예: interfacial area transport narrow rectangular channel bubbly flow / bubble coalescence frequency narrow rectangular channel adiabatic air-water image processing / interfacial area transport Hele-Shaw cell bubbly flow / pancake bubble coalescence film drainage confined), 상위 3~8건 확인 + 서지 대조 약 50건 | 관련도순(총수는 의미 없음) | A5~A10, B2~B4, B7, D1~D8 발견. 둘레(Γ) 수송식, 팬케이크 IAC 분해 질의는 관련 결과 없음 |
| J-STAGE API | 제목 "気泡合体" / 전문 "気泡合体 狭隘 画像処理" | 5 / 1 | 단일 합체 가시화(1994~2020), A7(Shen & Hibiki 2025). 좁은 갭 합체율 없음 |
| KAKEN | 23561011(Shen, 2011~2013) | 1 | 좁은 유로 영상 + 4센서 탐침 → 눌린 기포 IATE(RC + TI) |
- 찾지 못한 것: (1) 갭을 바꿔 합체 커널을 잰 연구, (2) 강제 흐름 Hele-Shaw 다기포 계의 커널 측정, (3) 갇힌 유로 IATE 원천항을 사건 수로 시험한 연구, (4) 둘레 기반 수송식, (5) 표본 감사로 사건률을 보정한 기포 연구.
- 한계: 중국어 DB(CNKI)와 한국어 DB(KCI, KoreaScience)는 보지 못했다. ScienceDirect가 막혀 A3, A5, A6, A8의 초록·본문을 못 봤다. Scholar는 10회만 썼다(공용 한도).

## 5. 남은 의문과 사용자에게 확인할 것
- 물의 종류(수돗물/증류수/첨가물)와 실험 사이 관리: 합체 효율이 크게 달라진다.
- 기포 주입 방식과 초기 크기(노즐), 유량 범위: 크기별 상대 속도 Δu와 필요한 fps를 정한다.
- 0.3·0.7 mm 단열 영상의 fps와 화소당 mm: ξ_res를 계산해 사건 통계가 가능한 크기 하한을 정한다.
- 유로 방향(수평이면 부력이 갭 방향 → 7 mm에서 덮개 밑 기포, 겹침 문제).
- 철 바닥의 홈 방향·깊이: 갭 균일도와 접촉선 고정이 합체를 바꿀 수 있다(D2).
- 확인하지 못한 문헌 내용: A3(Kim 2003)의 원천항 평가 방법, A6의 식·계수, A8(수평)의 갭·계측법, C9·C10의 커널 목록. 대학 도서관 접속으로 읽어야 한다.

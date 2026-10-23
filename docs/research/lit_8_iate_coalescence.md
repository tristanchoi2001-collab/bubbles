# 주제 8: 계면 면적 수송(IATE)·인구 균형과 합체·분열 — 영상 추적으로 원천항을 직접 재기

작성: 2026-10-23, 문헌 조사 에이전트 8. **초안(작성 중)**.
확인 수준: `C+F` Crossref + 전문, `C+A` Crossref + 초록, `C` Crossref만(내용은 2차 자료), `U` 미대조. 공통 지침 4장을 따른다.
범위: 갭 H = 0.3, 0.7, 1, 3, 7 mm. 합체·분열 "실험 자료" 자체는 주제 1이 본다. 여기서는 모델(IATE·인구 균형 커널)과 "영상으로 원천항을 직접 재는 일"을 본다.

## 0. 요약 (작성 중)
1. 좁은 직사각 유로 IATE의 원조는 Sun·Kim·Ishii·Beus(2004, 200×10 mm)다(#A1~A4). 갭(G)은 "갭보다 큰 기포 = 갇힌 캡 기포(2그룹)"의 모양·부피·후류에만 들어간다.
   모든 충돌·분열 항이 난류 소산율 ε에 비례한다. 0.3~1 mm 갭(Re_Dh 30~2000, 층류)에는 ε 기반 항의 전제가 없다.
2. 그 원천항의 검증은 거의 전부 전도도(다중 센서) 탐침으로 잰 IAC·기공률의 **축 방향 변화**로 했다. 합체·분열 빈도 자체를 센 것이 아니다(#A3, #A5~A7, #C1).
   좁은 유로에서도 Shen·Hibiki(2012, 2013), Liu 등(2023, 수평)이 같은 방식이다.
3. 합체 사건을 영상으로 직접 센 연구는 대부분 단일 사건(형태·접촉 속도) 연구다(Ren 2020, Zhang 2022 비등 미끄럼 기포, #B1~B2). 빈도·커널을 크기별로 재서 IATE 원천항과 맞댄 연구는 이번 검색에서 찾지 못했다(4장 기록).
4. 얇은 갭 팬케이크 기포의 합체는 액막 배수가 갭 두께에 묶인다(Hele-Shaw: Ohashi 2022의 막 모세관수 Ca_f = (ηṘ/σ)(R/D)², Yokota & Okumura 2011의 3D→2D 교차, #D1~D3).
5. 추적 오차는 합체·분열률을 직접 흔든다. 오연결 1건이 가짜 "분열+합체" 쌍을 만든다. 표본 감사로 정밀도·재현율을 재고 Rogan–Gladen식으로 보정하는 길이 있다(#E1~E5).

## 1. 문헌 표 (작성 중)

### 1-A. 좁은·갇힌 유로의 IATE (가장 가까운 것부터)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3~7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| A1 | Sun, Kim, Ishii, Beus (2004) | Modeling of bubble coalescence and disintegration in confined upward two-phase flow | Nucl. Eng. Des. 230(1-3):3-26 | 10.1016/j.nucengdes.2003.10.008 | 수직 상향, 공기-물, 200×10 mm(갭 10 mm), 0.1 MPa | 2그룹 IATE. 5기구(RC 무작위 충돌, WE 후류 포착, TI 난류 충돌 분열, SO 전단 떨어짐, SI 표면 불안정). 2그룹 항에 갭 G, 최대 가로 반경 R_t,max2, 폭 W가 들어감. 예: Φ_RC^(2) ∝ ε^(1/3)α₂²R_t,max2^(4/3)/(W²G), Φ_WE^(12,2) ∝ √(gC_D2 G)·α₂a_i1/R_t,max2(2차 인용, Chen 2021 표 5) | 갇힌 유로 IATE의 원조. 단 갭 10 mm·난류. 0.3~1 mm는 거의 모든 기포가 "2그룹 갇힌 기포"가 되고 ε 항의 전제가 깨짐 | C |
| A2 | Sun, Kim, Ishii, Beus (2004) | Model evaluation of two-group interfacial area transport equation for confined upward flow | Nucl. Eng. Des. 230(1-3):27-47 | 10.1016/j.nucengdes.2003.10.014 | A1과 같은 유로 | A1 모델을 다중 센서 탐침 자료(축 방향 IAC 변화)로 평가(2차 인용, Chen 2021) | "무엇으로 검증했나"(Q2)의 기준점 | C |
| A3 | Kim, Sun, Ishii, Beus, Lincoln (2003) | Interfacial area transport and evaluation of source and sink terms for confined air–water bubbly flow | Nucl. Eng. Des. 219(1):61-75 | 10.1016/s0029-5493(02)00289-3 | 200×10 mm 기포류 | 원천·소멸항을 측정 IAC 변화로부터 "평가"(초록 미확인) | 같은 유로에서 원천항을 자료로 나눠 본 시도. 직접 빈도 측정인지 미확인 | C |
| A4 | Kim, Ishii, Wu, McCreary, Beus (2002) | Interfacial structures of confined air–water two-phase bubbly flow | Exp. Therm. Fluid Sci. 26(5):461-472 | 10.1016/s0894-1777(02)00152-8 | 200×10 mm | 갇힌 유로의 국소 계면 구조(측정 방법은 미확인) | 갇힌 유로 계측 자료 | C |
| A5 | Shen, Hibiki, Ono, Sato, Mishima (2012) | One-dimensional interfacial area transport of vertical upward bubbly flow in narrow rectangular channel | Int. J. Heat Fluid Flow 36:72-82 | 10.1016/j.ijheatfluidflow.2012.04.007 | 수직 상향 좁은 직사각 유로 기포류 | 1차원 IAT 자료(세부 미확인) | 좁은 유로 IAT 자료의 일본 계열 | C |
| A6 | Shen, Hibiki (2013) | One-group interfacial area transport equation and its sink and source terms in narrow rectangular channel | Int. J. Heat Fluid Flow 44:312-326 | 10.1016/j.ijheatfluidflow.2013.06.010 | 좁은 직사각 유로 | 1그룹 IATE와 원천·소멸항(세부 미확인) | 좁은 유로 원천항의 가장 직접적 선행 | C |
| A7 | Liu, Cheng, Yan, Gu, Meng (2023) | Characteristics of one-dimensional bubbly flow interfacial area transport in horizontal narrow rectangular channel | Chem. Eng. Res. Des. 189:30-45 | 10.1016/j.cherd.2022.10.039 | **수평** 좁은 직사각 유로 기포류 | 1차원 IAT 특성(세부 미확인) | 사용자 장치(수평 가능성)와 방향이 같은 유일한 IAT 문헌 | C |
| A8 | Cheng, Gu, Zhang, Zhu, Yu, Meng (2023) | An experimental study on interfacial parameters in a narrow rectangular channel under different flow regimes | Prog. Nucl. Energy 159:104644 | 10.1016/j.pnucene.2023.104644 | 좁은 직사각 유로, 여러 유동 양식 | 큰 기포 합체가 IAC를 줄임(Scholar 요약 기준) | A7과 같은 그룹(하얼빈공정대) | C |
| A9 | Wilmarth, Ishii (1997) | Interfacial Area Concentration and Void Fraction of Two-Phase Flow in Narrow Rectangular Vertical Channels | J. Fluids Eng. 119(4):916-922 | 10.1115/1.2819517 | 수직, 공기-물, 갭 **1·2 mm** | CCD 영상 + 화상 처리로 국소 평균 기공률·IAC. 기공률로 양식별 C0·Vgj(초록 기준) | 1 mm 갭에서 영상 IAC의 가장 오래된 선례. 합체·분열은 다루지 않음 | C+A |
| A10 | Fu, Liu (2016) | Development of a robust image processing technique for bubbly flow measurement in a narrow rectangular channel | Int. J. Multiphase Flow 84:217-228 | 10.1016/j.ijmultiphaseflow.2016.04.011 | 좁은 직사각 유로 기포류 | 겹친 기포를 나누는 화상 처리(세부 미확인) | 좁은 유로 영상 계측의 방법론 선행. 합체·분열 빈도는 다루지 않은 것으로 보임(미확인) | C |
| A11 | Yang, Xiong (2023) | Unified two-component interfacial area concentration model for narrow channel two-phase flow | Int. J. Multiphase Flow 163:104428 | 10.1016/j.ijmultiphaseflow.2023.104428 | 좁은 유로 | IAC 모델 | 좁은 유로 IAC 상관 | C |

### 1-B. 일반 IATE·커널 (원천항의 꼴과 계수)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| C1 | Wu, Kim, Ishii, Beus (1998) | One-group interfacial area transport in vertical bubbly flow | Int. J. Heat Mass Transfer 41(8-9):1103-1112 | 10.1016/s0017-9310(97)00167-1 | 수직관 50.8 mm 공기-물 | RC: f_coll ∝ nε^(1/3)D^(2/3)·6α/(πα_max^(1/3)(α_max^(1/3)−α^(1/3)))·[1−exp(−C…)], C = 3.0, α_max = 0.75, 효율 C_RC = 0.004. TI: We_cr = 6.0, C_TI = 0.085(2차 인용, Chen 2021 표 4) | 1그룹 IATE의 표준형. ε 기반 | C |
| C2 | Hibiki, Ishii (2002) | Development of one-group interfacial area transport equation in bubbly flow systems | Int. J. Heat Mass Transfer 45(11):2351-2372 | 10.1016/s0017-9310(01)00327-1 | 25.4/50.8 mm 관 | 충돌 효율 = (C_RC/2)exp(−K_c√(We/2)), C_RC = 0.0314, K_c = 1.29, α_RC,max = 0.741. TI: K_TI = 6.0, C_TI = 0.021(2차 인용, Chen 2021 표 4) | 액막 배수형 효율을 넣은 판 | C |
| C3 | Hibiki, Ishii (2000) | Two-group interfacial area transport equations at bubbly-to-slug flow transition | Nucl. Eng. Des. 202(1):39-76 | 10.1016/s0029-5493(00)00286-7 | 관 | 2그룹 IATE(시작 문헌 목록의 "2000 IJHMT 2그룹"은 실제로 NED) | 2그룹 틀 | C |
| C4 | Ishii, Hibiki (2011) | Thermo-Fluid Dynamics of Two-Phase Flow (2nd ed.) | Springer (책) | 10.1007/978-1-4419-7985-8 | 교과서 | 10장 IAT(217-242쪽), 11장 IAT 구성식(243-313쪽) | 표준 참고서 | C |
| C5 | Ishii, Kim (2004) | Development of One-Group and Two-Group Interfacial Area Transport Equation | Nucl. Sci. Eng. 146(3):257-273 | 10.13182/nse01-69 | 리뷰 | 1·2그룹 IATE 정리 | 개관 | C |
| C6 | Kim, Ishii, Kong, Wang (2021) | Progress in two-phase flow modeling: Interfacial area transport | Nucl. Eng. Des. 373:111019 | 10.1016/j.nucengdes.2020.111019 | 리뷰 | IATE 30년 정리(세부 미확인) | 최신 개관 | C |
| C7 | Chen, Wei, Ding, Wei, Li, Saxén 외 (2021) | Interfacial Area Transport Equation for Bubble Coalescence and Breakup: Developments and Comparisons | Entropy 23(9):1106 | 10.3390/e23091106 | 리뷰(오픈액세스, Europe PMC PMC8465106) | 1그룹 5종·2그룹 3유로형(좁은 갇힌 유로 = Sun 2004) 식과 계수 표. "2그룹 IATE 성능은 유로 크기·모양에 강하게 의존" | 원천항 꼴의 1차 정리 자료(이 표의 C1·C2·A1 식 출처) | C+F |
| C8 | Prince, Blanch (1990) | Bubble coalescence and break-up in air-sparged bubble columns | AIChE J. 36(10):1485-1499 | 10.1002/aic.690361004 | 기포탑 | 합체 = 난류·부력·**층류 전단** 충돌 × 효율. 합체·분열 "사건"을 추적 기체 혼합 + 몬테카를로로 측정(초록 기준) | 층류 전단 충돌항이 이미 있음 → 0.3~1 mm 층류 갭의 출발점. 사건 측정이 영상이 아님 | C+A |
| C9 | Liao, Lucas (2009) | A literature review of theoretical models for drop and bubble breakup in turbulent dispersions | Chem. Eng. Sci. 64(15):3389-3406 | 10.1016/j.ces.2009.04.026 | 리뷰 | 분열 커널 정리 | 커널 표준 리뷰 | C |
| C10 | Liao, Lucas (2010) | A literature review on mechanisms and models for the coalescence process of fluid particles | Chem. Eng. Sci. 65(10):2851-2864 | 10.1016/j.ces.2010.02.020 | 리뷰 | 합체 기구(난류·부력 차이·전단·후류 등)와 효율 모델 정리 | 커널 표준 리뷰 | C |
| C11 | Lehr, Millies, Mewes (2002) | Bubble-size distributions and flow fields in bubble columns | AIChE J. 48(11):2426-2443 | 10.1002/aic.690481103 | 기포탑 CFD | 평균 기포 부피 수송식 + 물리 기반 분열·합체율(초록 기준). 고속 영상으로 분열·합체를 관찰했다는 서술(Scholar 요약 기준) | 영상 관찰로 커널을 만든 대표 예 | C+A |

### 1-C. 합체·분열을 영상으로 센 연구 (좁은 유로·2차원·기포탑)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| B1 | Zhang, Liu, Liu, Chen (2022) | Prediction of sliding bubble coalescence rate during subcooled flow boiling in narrow rectangular channel | Int. J. Heat Mass Transfer 196:123244 | 10.1016/j.ijheatmasstransfer.2022.123244 | 좁은 직사각 유로, 과냉 흐름 비등, 4면 가시화 | 합체 순간 접촉 속도가 미끄럼 중 크기 변화로 커짐. 충돌은 부력 차이·난류에서. 좁은 유로용 충돌 빈도 상관식 + 임계 속도 모델로 합체율 ±25%(초록 기준, SSRN 판 10.2139/ssrn.4113805) | **가장 가까운 선행**(좁은 유로 + 영상 + 합체율). 단 비등 미끄럼 기포, 수직, 분열 없음, 크기별 커널 아님 | C+A |
| B2 | Ren, Zhu, Zhang, Shi, Yan (2020) | Visualization Experiment of Bubble Coalescence in a Narrow Vertical Rectangular Channel | Front. Energy Res. 8:96 | 10.3389/fenrg.2020.00096 | 700×40×2 mm, 과냉 흐름 비등, 4300 fps, 시야 10.28×10.28 mm | 합체 4단계(접근·병합·조정·안정). 기포는 가열면을 따라 미끄러지며 떨어지지 않음. 합체 중 새 작은 기포 생성 | 2 mm 갭 단일 사건 형태. 빈도 없음 | C+F |
| B3 | Laari, Turunen (2003) | Experimental Determination of Bubble Coalescence and Break-up Rates in a Bubble Column Reactor | Can. J. Chem. Eng. 81(3-4):395-401 | 10.1002/cjce.5450810309 | 기포탑 | 여러 높이의 사진 기포 크기 분포 → 인구 균형 역산으로 커널 계수 추정(초록 기준) | "분포 변화로 역산"하는 간접법의 예. 사건 직접 계수 아님 | C+A |
| B4 | Karn, Shao, Arndt, Hong (2016) | Bubble coalescence and breakup in turbulent bubbly wake of a ventilated hydrofoil | Exp. Therm. Fluid Sci. 70:397-407 | 10.1016/j.expthermflusci.2015.10.003 | 환기 수중익 후류 | 영상으로 합체·분열(세부 미확인) | 영상 기반 합체·분열 통계의 예 | C |

### 1-D. 얇은 갭(Hele-Shaw) 팬케이크 기포·방울의 합체, 2차원 폼
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| D1 | Ohashi, Toramaru, Namiki (2022) | Coalescence of two growing bubbles in a Hele–Shaw cell | Sci. Rep. 12:? | 10.1038/s41598-022-05252-5 | Hele-Shaw, 감압으로 자라는 두 기포, 점도·감압률·갭 변화 | 막 모세관수 Ca_f = (ηṘ/σ)(R/D)²가 합체 직전 변형을 정함. 공칭 Ca_f가 임계값보다 작을 때만 합체(초록 기준) | 갭 D가 배수 속도에 (R/D)²로 들어감 → 갭별 합체 효율 차이의 근거 | C+A |
| D2 | Yokota, Okumura (2011) | Dimensional crossover in the coalescence dynamics of viscous drops confined in between two plates | PNAS 108(16):6395-6398 | 10.1073/pnas.1017112108 | 두 판 사이 점성 방울 | 목 폭이 초기 선형 → 뒤에 느려짐. 3D(구) → 준2D(원판) 교차(초록 기준) | 팬케이크 합체 시간의 갭 의존 | C+A |
| D3 | Okumura (2018) | Viscous dynamics of drops and bubbles in Hele-Shaw cells: Drainage, drag friction, coalescence, and bursting | Adv. Colloid Interface Sci. 255:64-75 | 10.1016/j.cis.2017.07.021 | 리뷰 | Hele-Shaw 배수·항력·합체·파열 스케일링(세부 미확인) | Q3 개관 | C |
| D4 | Biance, Delbos, Pitois (2011) | How Topological Rearrangements and Liquid Fraction Control Liquid Foam Stability | Phys. Rev. Lett. 106(6):068301 | 10.1103/physrevlett.106.068301 | 폼 | 위상 재배열(T1)이 막 파열(합체)을 일으킴(세부 미확인) | 밀집 팬케이크 무리에서 "충돌"이 아니라 재배열이 합체를 부를 수 있음 | C |
| D5 | Ritacco, Kiefer, Langevin (2007) | Lifetime of Bubble Rafts: Cooperativity and Avalanches | Phys. Rev. Lett. 98(24):244501 | 10.1103/physrevlett.98.244501 | 2차원 기포 뗏목 | 파열이 연쇄(사태)로 일어남(세부 미확인) | 합체 사건이 독립 포아송이 아닐 수 있음 → 통계 오차 계산에 영향 | C |
| D6 | Durand, Stone (2006) | Relaxation Time of the Topological T1 Process in a Two-Dimensional Foam | Phys. Rev. Lett. 97(22):226101 | 10.1103/physrevlett.97.226101 | 2D 폼 | T1 이완 시간(세부 미확인) | 2D 재배열 시간 척도 | C |
| D7 | Bremond, Thiam, Bibette (2008) | Decompressing Emulsion Droplets Favors Coalescence | Phys. Rev. Lett. 100(2):024501 | 10.1103/physrevlett.100.024501 | 미세유로 갇힌 방울 | 갇힌 방울은 다가갈 때가 아니라 **떨어질 때** 합체(2차 인용) | 판정 규칙: 접촉 직후 아닌 분리 시점 합체도 셀 것 | C |
| D8 | Beatus, Bar-Ziv, Tlusty (2012) | The physics of 2D microfluidic droplet ensembles | Phys. Rep. 516(3):103-145 | 10.1016/j.physrep.2012.02.003 | 리뷰 | 갇힌 방울의 쌍극자 유체역학 상호작용(2차 인용) | 층류 갭에서 "충돌"을 정하는 장거리 상호작용 | C |

### 1-E. 추적 오차·사건 판정·표본 감사 (Q5)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| E1 | Ouellette, Xu, Bodenschatz (2006) | A quantitative study of three-dimensional Lagrangian particle tracking algorithms | Exp. Fluids 40(2):301-313 | 10.1007/s00348-005-0068-7 | 입자 추적 알고리즘 비교 | 오류율이 "프레임당 변위 / 입자 간격" 비에 따라 급증(2차 인용) | 사용자 트래커의 촬영 조건 지표(0.47~0.62)와 같은 변수 | C |
| E2 | Jaqaman 외 (2008) | Robust single-particle tracking in live-cell time-lapse sequences | Nat. Methods 5(8):695-702 | 10.1038/nmeth.1237 | 세포 내 입자 추적 | LAP 틀에서 간극 잇기·**합체·분열**을 함께 판정(2차 인용) | 합체·분열 사건 판정 알고리즘의 표준 참고 | C |
| E3 | Chenouard 외 (2014) | Objective comparison of particle tracking methods | Nat. Methods 11(3):281-289 | 10.1038/nmeth.2808 | 14개 팀 비교 | 밀도·SNR에 따른 추적 성능 지표(2차 인용) | 오차 정량화 방식 | C |
| E4 | Rogan, Gladen (1978) | Estimating prevalence from the results of a screening test | Am. J. Epidemiol. 107(1):71-76 | 10.1093/oxfordjournals.aje.a112510 | 역학 | 민감도·특이도를 알면 관측 비율에서 참 비율을 보정 | 사람 표본 감사로 잰 정밀도·재현율로 합체·분열 수를 보정하는 식의 근거 | C |

## 2. 핵심 질문에 대한 답 (작성 중)
- Q1~Q5: 작성 중.

## 4. 새로움 판단 기록 (작성 중)
| 도구 | 검색어 | 결과 수 | 메모 |
|---|---|---|---|
| Scholar | "interfacial area transport" "narrow rectangular channel" coalescence breakup (2010~) | 18 | IATE 적용·IAC 측정·CFD뿐. 영상으로 합체·분열 빈도를 센 연구 없음 |
| Scholar | "coalescence frequency" "breakup frequency" "interfacial area transport" "high-speed" images bubbles | 6 | Smith 2002 학위논문(고속 영상 관찰), Lehr 2002(C11) 등. 좁은 유로 없음 |

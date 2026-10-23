# 주제 6: 계측·자료 처리 (0.3/0.7/1/3/7 mm 마이크로갭, 2026-10-23)

조사 담당: 주제 6 서브 에이전트. 범위 변경(갭 0.3·0.7 mm 추가)을 반영했다.
문헌 번호 [n]은 이 파일 안의 번호다. 확인 수준은 공통 지침 4장(C+F / C+A / C / U)을 따른다.
"(추정)"은 이 보고서가 직접 계산한 값이다. 계산 스크립트는 세션 scratchpad(lit6/calc/est6.py)에만 있다.
물성은 `estimates_microgap.md`와 같다(물 20 °C, μ = 1.002 mPa·s, σ = 0.0728 N/m).

## 0. 요약
1. **영상 기공률은 처리법에 따라 수십 % 달라진다.** U-Net 마스크의 면적비와 3D 부피 재구성은 평균 약 80%, 낮은 기공률에서 최대 약 700% 차이가 났다 [1, C+F]. → 갭별 모양 모델(팬케이크/구/웅덩이)이 필수다.
2. **0.3~1 mm에서는 영상 기공률이 가장 믿을 만하다.** 팬케이크 보정(가장자리 메니스커스 + 액막)은 d/H ≥ 3이면 5~20%다 (추정, [2][16]). 7 mm는 구·웅덩이 보정으로 0.1~0.75배가 된다(`estimates_microgap.md` 10장).
3. **좁은 갭에서 영상 기공률을 독립 기준법과 직접 비교한 연구는 드물다.** 대부분 상관식이나 다른 영상 처리법과 비교했다 [1][11][12]. 기준법 후보는 임피던스(±0.02, 0.778/1.465 mm) [5], 정전용량(수평·아래 가열 4 mm) [9], 중성자 [6][8]다.
4. **0.3 mm는 갭 오차가 압력 강하를 지배한다.** 같은 유량에서 ΔP ∝ 1/H³라 10 µm 오차가 10%다(추정). 단상 층류 ΔP로 수력 갭을 역산하면 ±2 µm 수준이다(추정). 평탄도 편차는 2차 효과다: h_H³ ≈ ⟨h⟩³(1 − 1.5σ²/⟨h⟩²) [27, C+F].
5. **덮개 휨은 운전 압력에 따라 갭을 바꾼다.** 0.778/1.465 mm 장치는 게이지압 96 kPa까지 올라 판으로 보강했다 [5, C+F]. 얕은 채널은 변형으로 같은 ΔP에서 유량이 크게 달라진다 [28][29].
6. **입출구 손실은 0.3 mm에서 마찰의 1~6%뿐이지만, 1 mm 고속과 3·7 mm에서는 마찰과 같거나 크다**(추정). 이상류 입출구 손실 모델은 2배까지 틀린다 [32][33]. → 압력 탭은 채널 안, 발달 길이 뒤에 3개 이상 둔다 [30][33][34].
7. **철 바닥에서 기포 내부가 어두운 이유는 단순 반사율로 설명되지 않는다.** 철의 반사율은 공기 접촉 0.51 > 물 접촉 0.42다 [19] (계산). "젖으면 어둡다" 문헌 [21]도 반대 부호를 예측한다. 덮개–액층에 전반사로 갇힌 빛이 기포 밑에 들어가지 못한다는 가설이 덧셈형 −40과 맞는다(원리 [22][23]). 가시광 밝기로 액막 유무를 판정할 근거는 없다.
8. **매립 열전대는 시간 평균만 본다.** 벽은 15 Hz 변동을 거의 지운다 [39]. 철은 k가 낮아 외삽 보정, 2D 공액 전도, 열전대 구멍 교란이 크다 [41][42]. → 단상 기준 시험으로 열손실과 외삽을 함께 보정한다 [44][45].

## 1. 문헌 표

### 1-1. 기공률·기포 부피·액막 (Q1, 0.3/0.7 mm 부피 보정)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 1 | Passoni, Mereu, Bucci (2024) | Integrating machine learning and image processing for void fraction estimation in two-phase flow through corrugated channels | IJMF 177:104871 | 10.1016/j.ijmultiphaseflow.2024.104871 | 판형 열교환기 주름 채널(깊이 2.5 mm), 역광 정면 고속 영상, U-Net 분할 | 분할 지표 > 0.9(재현율 91.7%). 작은 기포(등가직경 < 국소 깊이)는 회전 타원체, 큰 기포는 깊이 지도로 돌출 + 가장자리 곡률 평활. 면적비와 평활 부피비의 평균 차 약 80%, 낮은 α에서 최대 약 700%. 평활 유무 차 20~40%(평균 32%). 액막은 무시. 독립 기준법 비교 없음 | 같은 U-Net 파이프라인. 부피 모델 선택만으로 α가 수십 % 바뀐다. 7 mm(구·웅덩이)에서 특히 크다 | C+F |
| 2 | Musterd, van Steijn, Kleijn, Kreutzer (2015) | Calculating the volume of elongated bubbles and droplets in microchannels from a top view image | RSC Adv 5(21):16042-16049 | 10.1039/c4ra15163a | 직사각·사다리꼴 마이크로채널, H/W ≤ 1, Surface Evolver로 검증 | 단순 V = A·L보다 오차가 최대 10배 작다. L ≥ 3W에서 5% 이내, 전체 10% 이내, W < L < 2W는 12%. 짧은 기포는 팬케이크 V = πHL²/4, 구 πL³/6. 액막: Ca < 10⁻³이면 무시(2.5%), Ca = 10⁻²에서 12% → W−2δ, H−2δ로 보정 | 윗면 영상 → 부피 변환의 기하(가장자리 (4−π) 항). 우리 Ca 7×10⁻⁴~1.4×10⁻²라 0.07 m/s 이상에서 막 보정 필요 | C+F |
| 3 | Ito, Prasser (2012) | Measurement of Two-Phase Flow Structure in a Narrow Rectangular Channel | InTech, Flow Measurement(장) | 10.5772/37721 | 수직 상향 공기-물, 갭 1.5 mm, 폭 32 mm. 양쪽 벽에 액막 센서(2×2 mm², 600 µm 이하 측정) | 전도도로 "기공률 100%"여도 양쪽 액막 150 µm면 실제 80%(20% 차). 처언 흐름에서도 100%에 도달하지 않음. 기체 두께 = 갭 − 막으로 재구성. Ali et al.의 α ≈ 0.8β, Kawahara 식과 비교 | 0.7~1.5 mm에서 막 항이 Bretherton 예측보다 클 수 있다(고 jL). 영상은 막 두께를 못 본다 | C+F |
| 4 | Shikazono, Han (2011) (+ Han, Shikazono, Kasagi 2011, IJMF 37(1):36-45) | Liquid Film Thickness in Micro-Scale Two-Phase Flow | InTech(장) | 10.5772/22394 (Han 2011: 10.1016/j.ijmultiphaseflow.2010.08.010) | 레이저 공초점 변위계(오차 1%, 분해능 0.01 µm)와 간섭계. 평판형 채널 H = 0.116/0.309/0.504 mm(종횡비 4~10) 포함 | 초기 막 두께 δ0/Dh = 0.670Ca^(2/3)/(1 + 3.13Ca^(2/3) + 0.504Ca^0.672·Re^0.589 − 0.352We^0.629) (Ca < 0.3, Re < 2000)가 평판형 데이터도 잘 맞춤. 같은 장에서 Utaka 2007의 0.5/0.3/0.15 mm 갭 막 2~30 µm 인용 | 0.3 mm(H = 0.309 mm 시험)의 막 두께 추정. 공초점 변위계는 덮개 너머 갭 높이 측정에도 쓸 수 있다 | C+F (Han 2011은 C) |
| 5 | Sadatomi, Ali, Kawaji (1992) (+ Ali, Sadatomi, Kawaji 1993, Can J Chem Eng 71(5):657-666) | 狭い平行平板間の気液二相流に及ぼすすきま寸法と流動方向の影響 | 日本機械学会論文集B 58(546):408-415 | 10.1299/kikaib.58.408 (Ali 1993: 10.1002/cjce.5450710502) | 공기-물(소금 0.2 g/kg), 갭 0.778/1.465 mm, 폭 80, 길이 240 mm, 아크릴 12 mm, 6방향 | 기공률: 벽 매립 금도금 전극 쌍(12.5×76 mm, 120 mm 간격), 2 kHz·3 s, 오차 ±0.02. 고유량에서 게이지압 최대 96 kPa → 갭 확대를 막으려고 알루미늄 12.7 mm + 아크릴 25.4 mm로 보강. Chisholm C = 10~25(1.465 mm 수직), jL > 1 m/s에서 C = 20 | 0.7·1 mm의 기준 기공률 측정 설계와 덮개 보강의 직접 사례 | C+F (Ali 1993은 C) |
| 6 | Mishima, Hibiki, Nishihara (1993) (+ Hibiki et al. 1995 Nucl Technol 110(3):422-435; Mishima & Hibiki 1998 NED 184(2-3):183-201) | Some characteristics of gas-liquid flow in narrow rectangular ducts | IJMF 19(1):115-124 | 10.1016/0301-9322(93)90027-r (10.13182/nt95-a35111; 10.1016/s0029-5493(98)00196-4) | 수직, 갭 1.07/2.45/5.0 mm(2차 인용), 중성자 투과 기공률 | 중성자 투과가 좁은 금속 덕트의 기공률 기준법(1995: 금속 직사각 덕트 고속 중성자 영상, 1998: 정량 측정법) | 1·3 mm 비교 기준. 철 벽도 중성자는 투과한다 | C |
| 7 | Mishima, Fujine, Yoneda, Yonebayashi, Kanda, Nishihara (1988) | A study of air-water flow in a narrow rectangular duct using an image processing technique | Proc. Dynamics of Two-Phase Flows 141-160 | 10.1615/0-8493-9925-4.70 | 학회 1988-07(오쓰). Crossref 출판연도는 2023(디지털화) | 중성자 투과·광학 영상 처리로 기공률. 전도도 탐침 자료·드리프트 플럭스 식과 일치(검색 요약) | 좁은 갭 영상 기공률의 초기 검증 사례 | C |
| 8 | Ito, Odaira, Ito, Saito, Kurita, Iikura (2023) | Measurements of gas-liquid two-phase flow dynamics using high-speed neutron imaging | J Phys Conf Ser 2605(1):012024 | 10.1088/1742-6596/2605/1/012024 | 갭 2.8 mm × 폭 66.5 mm, 1000 fps, 160 µm/px, 화소·프레임당 중성자 약 26개 | 회전 스테인리스 교정 원판으로 흐림·잡음 복원법 확립. 2D 기공률 분포와 갭 방향 액막 거동을 얻음 | 독립 기준법의 현재 수준. 시설이 필요해 이 실험에 바로 쓰긴 어렵다 | C+F |
| 9 | Liu, Asano (2026, 프리프린트) | Void Fraction of Subcooled Flow Boiling within Horizontal Narrow Channel Measured by Capacitance Sensor | SSRN | 10.2139/ssrn.6753968 | **수평** 채널 높이 4 mm, 바닥 중앙 가열면 20×50 mm², HFC245fa, 정전용량 센서 | 열유속에 따라 기공률 증가, 막비등 천이에서 급감. 표면 처리별 차이 | 수평 + 아래 가열 + 수 mm 갭이라 3 mm와 가장 비슷한 배치의 기준법. 동료 심사 전 | C+A |
| 10 | Keinath, Garimella (2014) | Measurement and Modeling of Void Fraction in High Pressure Condensing Flows through Microchannels | 4th Micro and Nano Flows Conf. (UCL) | DOI 없음 | R404A 응축, 관 0.508/1/3 mm, 1000 fps, 3 mm에서 45 px/mm | 2D 영상 + 단면 모양 가정(원/부분 원)으로 기공률. 가정은 수직 방향 두 번째 시점(위에서 본 영상)으로 검증. 드리프트 모델이 92.3%를 ±25% 안에서 예측 | 3·7 mm의 기포 두께 가정을 옆 시점 영상으로 검증하는 방법 | U (전문 읽음) |
| 11 | Chu, Liu, Pan, Zhu, Yang (2021) | Study on Measure Approach of Void Fraction in Narrow Channel Based on Fully Convolutional Neural Network | Front Energy Res 9:636813 | 10.3389/fenrg.2021.636813 | 30×1.5 mm 유리 채널, 투명 가열막, 비등, 1000 fps | FCN 화소 정확도 0.991, MIoU 0.982. 이진 마스크로 기공률. 출구 건도로 계산한 상관식과 ±11%. 독립 측정 없음 | 1.5 mm 영상 기공률의 흔한 검증 수준(약함) | C+F |
| 12 | Masiukiewicz, Anweiler (2021) | Precise Evaluation of Gas–Liquid Two-Phase Flow Pattern in a Narrow Rectangular Channel with Stereology Method | Energies 14(11):3180 | 10.3390/en14113180 | 50×1200×5 mm 수직, jG 0.006~0.044, jL 0.011~1.111 m/s | 입체해석학 지표(V_V, 계면 S_V, 수 N_V, 평균 현 길이, 자유 거리)로 양식 판별 | 영상 기반 계면 면적 농도. 독립 검증 없음 | C+A |
| 13 | Piasecka (2013) (+ Piasecka, Piasecki, Maciejewska 2025, Energies 18(4):940) | Determination of the Temperature Field Using Liquid Crystal Thermography and Analysis of Two-Phase Flow Structures in Research on Boiling Heat Transfer in a Minichannel | Metrol Meas Syst 20(2):205-216 | 10.2478/mms-2013-0018 (10.3390/en18040940) | 한쪽이 얇은 가열 박막인 평판 미니채널. 액정 열화상 + 흐름 영상 | 이진화 영상으로 단면 기공률 계산, 오차 추정. 2025: 액정·적외선 열화상의 h 차이 15% 미만 | 국소 h 지도 + 영상 기공률을 함께 얻는 대안 장치 | C+A |
| 14 | Kawahara, Chung, Kawaji (2002) | Investigation of two-phase flow pattern, void fraction and pressure drop in a microchannel | IJMF 28(9):1411-1435 | 10.1016/s0301-9322(02)00037-x | 100 µm 관, 질소-물 | 상관식 α = 0.03β^0.5/(1 − 0.97β^0.5)(Ito & Prasser [3]의 인용, 2차). 마이크로 규모의 강한 미끄럼 | 0.3 mm 기공률 비교선(마이크로 쪽 끝) | C |
| 15 | Park, Homsy (1984) | Two-phase displacement in Hele Shaw cells: theory | JFM 139:291-308 | 10.1017/s0022112084000367 | Hele-Shaw, 작은 Ca·작은 ε | Bretherton을 확장한 메니스커스·막 이론(정합 점근 전개) | 팬케이크 막 두께와 가장자리 형상의 이론 근거 | C+A |
| 16 | Aussillous, Quéré (2000) | Quick deposition of a fluid on the wall of a tube | Phys Fluids 12(10):2367-2371 | 10.1063/1.1289396 | 저점성 액체, 모세관 | 임계 Ca 위에서 관성으로 막이 Taylor 법칙보다 두꺼워지고, 아주 빠르면 감소 | 막 두께 식 δ/b = 1.34Ca^(2/3)/(1 + 3.35Ca^(2/3))의 출처(estimates 4장) | C+A |
| 17 | Reichert, Huerre, Theodoly, Valignat, Cantat, Jullien (2018) (+ Huerre et al. 2015 PRL 115(6)) | Topography of the lubrication film under a pancake droplet travelling in a Hele-Shaw cell | JFM 850:708-732 | 10.1017/jfm.2018.457 (10.1103/physrevlett.115.064501) | 반사 간섭 대비 현미경(RICM)으로 nm 정밀도 막 지도 | 막은 3D 지형. 뒤쪽은 계면활성제 축적으로 두꺼워지고 옆에 "골"이 생김. 2015: 낮은 Ca는 분리압이 막을 정하고, 임계 Ca 위는 점성 거동 | 팬케이크 막이 균일하지 않다 → 부피 보정 불확도. 물이 오염되면 막이 두꺼워진다 | C+A |
| 18 | de Gennes, Brochard-Wyart, Quéré (2004) | Capillarity and Wetting Phenomena | Springer(책) | 10.1007/978-0-387-21656-0 | 교과서 | 웅덩이 두께 e = 2Lc·sin(θ/2) | 7 mm에서 위 덮개 밑 큰 기포 두께 ≈ 4.5~5.5 mm → 부피 = A·e | C |

### 1-2. 불투명 바닥 위 가시화의 광학 (Q2)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 19 | Johnson, Christy (1974) | Optical constants of transition metals: Ti, V, Cr, Mn, Fe, Co, Ni, and Pd | PRB 9(12):5056-5070 | 10.1103/physrevb.9.5056 | 순철 n, k(표 값은 refractiveindex.info) | (계산) 550 nm에서 n = 2.95, k = 2.93 → 수직 반사율 공기 접촉 0.512, 물 접촉 0.416(비 0.81). 450~660 nm 모두 비 0.81~0.82 | 기체가 철에 직접 닿으면 더 밝아야 한다 → 관찰(어두움)과 반대 | C+F (데이터) |
| 20 | Hale, Querry (1973) | Optical Constants of Water in the 200-nm to 200-μm Wavelength Region | Appl Opt 12(3):555 | 10.1364/ao.12.000555 | 물 25 °C(표 값은 refractiveindex.info, 격자 거침) | (계산) 흡수 계수 550 nm 4.5×10⁻⁴ /cm, 1.4 µm 12 /cm, 2.0 µm 69 /cm. 왕복 투과율: 1.4 µm에서 막 20 µm 0.95, 0.3 mm 액층 0.48 / 2.0 µm에서 0.76, 0.016 | 가시광은 막을 못 본다. 근적외(1.4~2 µm) 흡수 영상은 막 두께·기공률을 직접 잴 수 있다(카메라 비용) | C+F (데이터) |
| 21 | Lekner, Dorf (1988) (+ Twomey, Bohren, Mergenthaler 1986, Appl Opt 25(3):431-437) | Why some things are darker when wet | Appl Opt 27(7):1278-1280 | 10.1364/ao.27.001278 (10.1364/ao.25.000431) | 거친 흡수성 표면 | 물막 안 전반사로 빛이 표면에 다시 돌아와 흡수가 늘고, 굴절률 대비가 줄어 젖은 표면이 어둡다. 1986: 앞쪽 산란 증가가 원인 | "젖으면 어둡다" → 액체 쪽이 어둡다는 예측. 우리 관찰은 반대라 다른 기구가 필요 | C+A |
| 22 | Hurlburt, Newell (1996) | Optical measurement of liquid film thickness and wave velocity in liquid film flows | Exp Fluids 21(5):357-362 | 10.1007/bf00189056 | 투명 벽 위 액막 | 액체–기체 계면의 전반사로 생긴 반사광 위치가 막 두께에 선형(검색 요약) | 덮개 쪽 액막을 덮개 바깥에서 재는 원리. 갇힌 빛 가설의 근거 | C |
| 23 | Shedd, Newell (1998) | Automated optical liquid film thickness measurement method | Rev Sci Instrum 69(12):4205-4213 | 10.1063/1.1149232 | 투명 벽 위 막, CCD 자동화 | 막 약 0.01 mm까지, 정지 액체에서 바늘 접촉법과 2.2% 이내 | 0.3~1 mm 팬케이크 위쪽 막(2~30 µm)에는 정밀도가 경계선 | C+A |
| 24 | Grasso, Petrov, Manera (2024) | Accuracy and error analysis of optical liquid film thickness measurement with total internal reflection method (TIRM) | Exp Fluids 65(6) | 10.1007/s00348-024-03820-1 | 전반사법(TIRM) 오차 분석, 광선 추적 | 굴절률 변화, 보정 범위 확장, 물결 표면의 영향을 정량화. 정확도 한계를 다시 정의 | 전반사 기반 막 측정을 쓸 때의 오차 목록 | C+A |
| 25 | Utaka, Okuda, Tasaki (2009) | Configuration of the micro-layer and characteristics of heat transfer in a narrow gap mini/micro-channel boiling system | IJHMT 52(9-10):2205-2214 | 10.1016/j.ijheatmasstransfer.2008.11.020 | 좁은 갭 비등, 레이저 소광법(물이 흡수하는 적외선) | 같은 그룹 2007: 0.5/0.3/0.15 mm 갭에서 막 2~30 µm(Shikazono & Han [4]의 인용, 2차) | 0.3 mm 비등 시 막 두께 범위. 흡수 원리는 [20]과 같다 | C |
| 26 | Chu, No, Song (2011) | Observation of High Heat Flux Boiling Structures in a Horizontal Pool by a Total Reflection Technique | NURETH-14, Proc. Canadian Nuclear Society | DOI 없음 | 투명 ITO 가열면, 전반사 + 비스듬한 시점 동기 | 임계 열유속 근처 큰 기포 밑이 대부분 건조, 일부 액체 갇힘 | 전반사는 투명 가열면이 필요하다 → 불투명 철 바닥에는 그대로 못 쓴다 | U (초록) |

### 1-3. 갭 높이 실측·평탄도·덮개 변형 (범위 변경으로 추가)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 27 | Zimmerman, Bodvarsson (1994 보고서; 1996 학술지) (+ Witherspoon et al. 1980, Water Resour Res 16(6):1016-1024) | Hydraulic conductivity of rock fractures | LBL-35976 보고서; Transp Porous Media 23(1) | 10.2172/60784 (학술지 10.1007/bf00145263; 10.1029/wr016i006p01016) | 거친 벽 틈의 윤활(Hele-Shaw) 흐름 | 3승 법칙. 유효 수력 간극은 항상 평균 간극보다 작다: h_H³ ≈ ⟨h⟩³[1 − 1.5σ²/⟨h⟩²](식 57). 접촉 면적 보정식 별도 | 수력 보정 갭의 정의와, 평탄도(σ)가 2차 효과라는 근거 | C+F (보고서 스캔 쪽 직접 읽음) |
| 28 | Gervais, El-Ali, Günther, Jensen (2006) | Flow-induced deformation of shallow microfluidic channels | Lab Chip 6(4):500 | 10.1039/b513524a | PDMS 얕은 채널, 공초점 현미경 | 낮은 종횡비 채널일수록 변형이 중요. 변형이 압력을 따라 흐름 방향으로 가늘어짐. 같은 ΔP에서 유량이 변형 없는 경우의 수 배 | 덮개 휨 → 갭이 흐름 방향으로 변한다. 수력 보정은 같은 압력에서 | C+A |
| 29 | Hardy, Uechi, Zhen, Kavehpour (2009) | The deformation of flexible PDMS microchannels under a pressure driven flow | Lab Chip 9(7):935-938 | 10.1039/b813061b | 형광 염료 층 두께 ∝ 세기로 변형 측정, 5개 위치 압력 | 압력과 변형이 선형. ΔP가 강체 채널보다 최대 35% 작음. 벽이 얇을수록 영향 큼 | 염료 1회 단상 시험으로 갭 지도를 만드는 방법(염료 사용 가능 여부는 사용자 확인) | C+A |

### 1-4. 압력 강하 측정·분해·변동·동기 (Q4)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 30 | Kohl, Abdel-Khalik, Jeter, Sadowski (2005) | An experimental investigation of microchannel flow with internal pressure measurements | IJHMT 48(8):1518-1533 | 10.1016/j.ijheatmasstransfer.2004.10.030 | Dh 24.9~99.8 µm, 채널 안 압력 센서 8개 + 입출구 2개, 물 Re 4.9~2068 | 내부 압력으로 외부 손실 모델을 검증하면 층류 이론(Shah & London)과 일치. 문헌의 일관된 편차는 외부 손실·입구 영역 미보정 때문으로 봄. Re 2067까지 조기 천이 없음 | 0.3 mm 단상 수력 보정과 이상류 ΔP 모두 탭을 채널 안에 둬야 하는 근거 | C (같은 저자 2004 학위논문 전문 확인) |
| 31 | Steinke, Kandlikar (2006) | Single-phase liquid friction factors in microchannels | IJTS 45(11):1073-1083 | 10.1016/j.ijthermalsci.2006.01.016 | 문헌 자료 데이터베이스 | 입출구·발달 구간 등 ΔP 성분을 분리하면 종래 Stokes/Poiseuille 이론이 맞음(검색 요약). 편차 원인으로 형상 측정 오차, 입출구 손실 미보정이 꼽힘(2차) | 갭 실측 오차와 입출구 처리가 결과를 좌우 | C |
| 32 | Abdelall, Hahn, Ghiaasiaan, Abdel-Khalik, Jeter, Yoda, Sadowski (2005) | Pressure drop caused by abrupt flow area changes in small channels | ETFS 29(4):425-434 | 10.1016/j.expthermflusci.2004.05.001 | 1.6↔0.84 mm 급확대·급축소, 공기-물 | 이상류 손실이 균질 모델보다 크게 작고, 미끄럼비 S = (ρL/ρG)^(1/3)이면 비교적 잘 맞음(Chalfi 2007 학위논문의 인용, 2차) | 입출구(플리넘 ↔ 갭) 이상류 손실의 불확도 | C |
| 33 | Chalfi, Ghiaasiaan (2008) (+ Chalfi 2007 석사논문, 조지아공대) | Pressure drop caused by flow area changes in capillaries under low flow conditions | IJMF 34(1):2-12 (지시서의 ETFS는 오기) | 10.1016/j.ijmultiphaseflow.2007.09.004 | 0.84/1.6 mm 모세관, 탭 여러 개, 공기-물 | (학위논문) 탭 여러 개의 직선 압력 분포를 외삽해 국소 손실 산출. 측정 전 배관에 기포가 없음을 확인. 균질 모델은 완전히 부적합. 급확대에서 Zivi·Premoli 미끄럼 모델이 약 2배 과소 예측. 축소부 vena contracta 없음 | 이상류 입출구 손실은 2배 수준 불확실 → 측정 구간에서 빼야 한다 | C (논문) / U (학위논문 전문) |
| 34 | Durst, Ray, Ünsal, Bayoumi (2005) (+ Ray, Durst, Ray 2020, J Fluids Eng 142(4), arXiv 1707.04947) | The Development Lengths of Laminar Pipe and Channel Flows | J Fluids Eng 127(6):1154-1160 | 10.1115/1.2063088 (10.1115/1.4045610) | 층류 발달 길이 수치 상관 | 채널: L_fd/Dh = [(0.3155)^1.6 + (0.01105Re)^1.6]^(1/1.6)(Ray et al.이 Dh 기준으로 옮긴 식) | 0.3 mm는 0.3~4 mm로 짧고, 7 mm 저속은 100 mm 이상 → 7 mm는 거의 전 구간이 발달 중(추정) | C (식은 Ray 2020 arXiv 공개본에서 C+F) |
| 35 | Matsui (1984) | Identification of flow regimes in vertical gas-liquid two-phase flow using differential pressure fluctuations | IJMF 10(6):711-719 | 10.1016/0301-9322(84)90007-7 | 수직관, 질소-물, 네 위치 | 차압 변동의 확률밀도함수 모양이 유동 양식마다 다름(검색 요약) | 차압 변동 통계로 양식 판별하는 고전 | C |
| 36 | Drahoš, Čermák (1989) | Diagnostics of gas—liquid flow patterns in chemical engineering systems | Chem Eng Process 26(2):147-164 | 10.1016/0255-2701(89)90007-x | 리뷰 | 변동 신호 기반 유동 양식 진단 정리(제목 수준) | 압력 스펙트럼 해석의 배경 | C |
| 37 | Li, Zhou, Hou, Sun, Yang (2014) | Flow pattern map and time–frequency spectrum characteristics of nitrogen–water two-phase flow in small vertical upward noncircular channels | ETFS 54:47-60 | 10.1016/j.expthermflusci.2014.01.017 | 작은 수직 직사각 채널, 고속 영상 + 차압 시간-주파수 | 같은 그룹의 2 mm × 0.81 mm 채널에서 압력 시간-주파수로 양식 인식률 92~100%(검색 요약, 이 논문의 수치인지 미확인) | 0.7~1 mm에 가까운 갭의 압력 스펙트럼 사례 | C |
| 38 | Kingston, Weibel, Garimella (2018) | High-frequency thermal-fluidic characterization of dynamic microchannel flow boiling instabilities: Part 1 | IJMF 106:179-188 | 10.1016/j.ijmultiphaseflow.2018.05.007 | 500 µm 유리관, HFE-7100 | 저장조·입출구 압력, 차압, 질량유속, 유체·벽 온도를 고속 영상과 동기해 측정 | 압력–영상 동기 측정의 표준 사례 | C+A |
| 39 | Kingston, Olson, Weibel, Garimella (2021) | Transient Flow Boiling and Maldistribution Characteristics in Heated Parallel Channels Induced by Flow Regime Oscillations | IEEE TCPMT 11(10):1615-1624 | 10.1109/tcpmt.2021.3106226 | 평행 채널 2개, 63/60 kW/m² | 평행 채널 불안정 15 Hz에서 ΔP·유량은 진동했지만 벽 온도 진동은 "사실상 없음". 빠른 가열 변동은 벽이 감쇠 | 매립 열전대로 기포 통과(수십 Hz)를 볼 수 없다는 실험 근거 | C+A |
| 40 | Clark, Weibel, Garimella (2021) | Impact of Pressure Drop Oscillations on Surface Temperature and Critical Heat Flux During Flow Boiling in a Microchannel | IEEE TCPMT 11(10):1634-1644 | 10.1109/tcpmt.2021.3094767 | 구리 히트싱크의 정사각 채널 폭 0.5/0.75/1 mm, 길이 20 mm | 고주파 압력 신호를 고속 영상과 동기해 압력 강하 진동의 영향을 분리 | 구리 블록 + 동기 측정 설계 예(철 블록과 비교) | C+A |

### 1-5. 철 블록 열전대로 h 구하기 (Q3)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 41 | Maranzana, Perry, Maillet (2004) | Mini- and micro-channels: influence of axial conduction in the walls | IJHMT 47(17-18):3993-4004 | 10.1016/j.ijheatmasstransfer.2004.04.016 | 평행 평판 채널 해석 모델 | 낮은 Re에서 벽 열유속이 입구 쪽에 몰려 매우 불균일. 낮은 유량에서 1D 모델로 실험값을 역산하면 h를 과소평가. 축방향 전도 무차원수 제안(M < 0.01이면 무시 가능은 2차 인용) | 0.3 mm 저속(Re 30~120)일수록 1D 외삽 h가 위험 | C+A (IIR 초록) |
| 42 | Beck (1962) | Thermocouple Temperature Disturbances in Low Conductivity Materials | J Heat Transfer 84(2):124-131 | 10.1115/1.3684310 | 저열전도 재료 속 열전대 | 구멍과 선이 온도장을 교란(제목 수준) | 철(k 15~50)은 구리(400)보다 설치 오차가 크다 | C |
| 43 | Golobič, Bergles (1997) | Effects of heater-side factors on the saturated pool boiling critical heat flux | ETFS 15(1):43-51 | 10.1016/s0894-1777(96)00170-7 | FC-72, 리본 가열체, 50개 자료 + 문헌 | 가열체 물성·두께가 CHF에 영향. 전도·열용량 효과 없는 가열체 크기 기준(검색 요약) | 비등 실험이면 철 블록 두께·물성이 결과에 들어간다 | C |
| 44 | Fernández-Seara, Uhía, Sieres, Campo (2007) | A general review of the Wilson plot method and its modifications to determine convection coefficients in heat exchange devices | ATE 27(17-18):2745-2757 | 10.1016/j.applthermaleng.2007.04.004 | 리뷰 | 윌슨 도표와 변형법 정리 | 접촉·전도 저항을 단상 시험으로 분리할 때 | C |
| 45 | Rose (2004) | Heat-transfer coefficients, Wilson plots and accuracy of thermal measurements | ETFS 28(2-3):77-86 | 10.1016/s0894-1777(03)00025-6 | 방법 비판 | 윌슨 도표의 가정과 정확도 문제(제목 수준) | 윌슨 도표만으로 보정하면 안 된다는 주의 | C |
| 46 | Woodbury, Najafi, de Monte, Beck (2023) | Inverse Heat Conduction | Wiley(책) | 10.1002/9781119840220 | 역열전도 교과서 | 역문제 추정 절차(정규화, 잡음 증폭) | 과도 운전(가열 계단)에서 표면 열유속을 구할 때 | C |

### 1-6. 불확도·영상 계측 (Q5)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 47 | JCGM (2008) | Evaluation of measurement data — Guide to the expression of uncertainty in measurement (GUM) | JCGM 100:2008 | 10.59161/jcgm100-2008e | 국제 표준 | 표준 불확도, 감도 계수 전파, 확장 불확도. 보충 1(몬테카를로, 10.59161/jcgm101-2008) | 모든 측정량의 불확도 표기 | C |
| 48 | Kline, McClintock (1953) | Describing uncertainties in single-sample experiments | Mech Eng 75(1):3-8 | DOI 없음 | 고전 | 단일 표본 실험의 오차 전파(2차 인용) | 열전달계수·마찰계수 오차 전파 | U |
| 49 | Moffat (1988) | Describing the uncertainties in experimental results | ETFS 1(1):3-17 | 10.1016/0894-1777(88)90043-x | 고전 | 실험 결과 불확도 기술법(제목 수준) | 같음 | C |
| 50 | Coleman, Steele (2018) | Experimentation, Validation, and Uncertainty Analysis for Engineers (4판) | Wiley(책) | 10.1002/9781119417989 | 교과서 | 계통·무작위 불확도, 회귀 불확도 | 열전대 기울기 회귀의 T_w, q 공분산 | C |
| 51 | Raffel, Willert, Scarano, Kähler, Wereley, Kompenhans (2018) | Particle Image Velocimetry (3판) | Springer(책) | 10.1007/978-3-319-68852-7 | 교과서 | 영상 교정, 피사계 심도, 노출·흐림 | 영상 속도·크기 불확도 예산의 틀 | C |

## 2. 핵심 질문에 대한 답

### Q1. 투영 면적 → 기공률 (0.3/0.7 mm 보강)
- **면적비는 과대평가한다.** 같은 U-Net 마스크에서 면적비와 부피 재구성은 평균 약 80% 다르다. 낮은 α에서는 최대 약 700% 다르다 [1, C+F]. 가장자리 곡률을 넣느냐만으로도 20~40% 차이가 난다 [1].
- **팬케이크(양쪽 벽에 닿는 기포).** 가장자리 단면을 반원(반지름 H/2)으로 보면 둘레 길이당 (4−π)H²/8 ≈ 0.107H²만큼 부피가 빈다. 같은 기하가 Musterd et al.의 (4−π) 항이다 [2, C+F]. 막까지 넣으면 다음과 같다(`estimates_microgap.md` 10장과 같은 식).
  - α_vol/α_p = 1 − 0.429·H/d − δ/b, δ/b = 1.34Ca^(2/3)/(1 + 3.35Ca^(2/3)) [16], b = H/2.
  - δ/b는 Ca에만 의존한다: 0.05 / 0.2 / 1 m/s에서 1.0% / 2.5% / 6.5% (추정).

  | H (mm) | d (mm) | d/H | α_vol/α_p (0.05 / 0.2 / 1 m/s) | 막 두께 δ (0.2 / 1 m/s) |
  |---|---|---|---|---|
  | 0.3 | 1 | 3.3 | 0.86 / 0.85 / 0.81 | 3.7 / 9.7 µm |
  | 0.3 | 3 | 10 | 0.95 / 0.93 / 0.89 | 3.7 / 9.7 µm |
  | 0.3 | 10 | 33 | 0.98 / 0.96 / 0.92 | 3.7 / 9.7 µm |
  | 0.7 | 1 | 1.4 | 0.69 / 0.68 / 0.64 | 8.6 / 22.6 µm |
  | 0.7 | 3 | 4.3 | 0.89 / 0.88 / 0.84 | 8.6 / 22.6 µm |
  | 1.0 | 3 | 3 | 0.85 / 0.83 / 0.79 | 12.3 / 32.3 µm |
  | 1.0 | 10 | 10 | 0.95 / 0.93 / 0.89 | 12.3 / 32.3 µm |
  | 3.0 | 10 | 3.3 | 0.86 / 0.85 / 0.81 | 37 / 97 µm |
  (추정. 막은 Aussillous & Quéré 식 [16]. Shikazono 식 [4]은 관성 보정이 더 붙는다.)
- **0.3·0.7 mm의 특징.**
  - 같은 물리 크기(mm)라면 가장자리 항(0.429H/d)이 작다. 그래서 다섯 갭 중 영상 기공률이 가장 정확하다(보정 5~20%).
  - 대신 가장자리 폭(약 H/2 = 0.15~0.35 mm)이 몇 화소뿐이다. 경계를 흰 띠의 안쪽/바깥쪽 어디에 두는지가 보정만큼 크다. → 경계 규약을 정하고 보고한다.
  - 막은 계면 오염에 민감하다. 뒤쪽이 두꺼워지고 옆에 골이 생긴다 [17]. 0.3 mm 막 2~30 µm는 비등 실측 범위와 맞는다 [4][25].
  - 1.5 mm 수직 슬러그·처언에서는 막이 커서 "100%"가 실제 80%였다 [3, C+F]. 고 jL에서는 Bretherton 예측보다 막이 클 수 있다.
  - 0.3 mm에서는 ΔP가 커서 기체가 채널을 따라 팽창한다. 출구 대기압이고 ΔP가 13/30/60 kPa면 출구 jG가 입구의 1.13/1.30/1.59배다(추정). → C0 = u_B/j의 j는 그 위치의 압력으로 계산한다.
- **7 mm(갭보다 작은 기포·웅덩이).** 구는 α_vol/α_p = 2d/(3H), 위 덮개 밑 웅덩이는 두께 e = 2Lc·sin(θ/2) ≈ 4.5~5.5 mm [18] → 0.61~0.75 (`estimates_microgap.md` 10장). 깊이 방향 겹침이 있으면 면적비는 더 틀린다. 3 mm는 두 경우가 섞인다.
  - 기포 두께 가정은 옆 시점 영상으로 검증할 수 있다 [10, U].
- **기준 측정법.**
  - 중성자 투과: 좁은 금속 덕트의 표준 [6][7][8]. 철 벽도 투과하지만 원자로·가속기 시설이 필요하다.
  - 임피던스(벽 매립 전극): 0.778/1.465 mm에서 ±0.02 [5, C+F]. 물에 소금 0.2 g/kg을 넣어 전도도를 맞췄다. 철 바닥은 그 자체가 전극이 될 수 있다(덮개 쪽 절연 전극 + 철 바닥, 아이디어).
  - 정전용량: 수평·아래 가열 4 mm 채널에서 비등 기공률을 쟀다 [9, 프리프린트].
  - 급폐쇄 밸브: 0.3 mm에서는 갇히는 부피가 작아 정밀도가 떨어진다(추정, 문헌 미확인).
- **영상 계면 면적 농도.** 입체해석학 지표 S_V를 쓴 예 [12], 막 센서로 재구성한 예 [3]가 있다. 영상의 둘레 길이 밀도 Γ는 팬케이크에서 계면의 "가장자리" 면적만 센다. 위아래 넓은 면(2A)은 별도로 더해야 한다(추정).

### Q2. 불투명 철 바닥 위 가시화의 광학
- **관찰(CLAUDE.md 철 블록 절).** 기포 내부 −25~−45 계조(덧셈형, 배경 밝기 110~166에서 일정), 빛 쪽 테두리 +30~+85, 반대쪽 바깥 그림자, 거대 슬러그 중심은 거의 0.
- **후보 기구 평가.**
  1. 철 표면 반사율(프레넬): 공기 접촉 0.51, 물 접촉 0.42 [19 계산]. 기체가 철에 직접 닿으면 약 20% 밝아져야 한다 → 부호가 반대다.
  2. 기포 밑에 막이 남으면 철의 반사율은 그대로다. 덮개/기체(PMMA 3.9%), 기체/막(2.0%) 계면이 늘어 왕복 약 12% 어두워진다(곱셈형, 회색 134에서 약 −16) → 크기와 형태(덧셈형)가 맞지 않는다(계산).
  3. "젖으면 어둡다" [21]: 액체 쪽이 어둡다는 예측 → 반대다.
  4. **갇힌 빛(가설).** 액체 영역에서 철이 흩뿌린 빛 중 물 속 각도 > 48.6°인 것은 덮개 윗면에서 전반사되어 다시 철로 돌아온다. 이 빛은 덮개 두께의 몇 배 거리로 퍼져 덧셈형 "베일"을 만든다. 기포 영역에서는 덮개 속 n·sinθ = 1~1.333 빛이 덮개/기체(또는 막/기체) 계면에서 전반사되어 철까지 못 내려간다. → 기포 밑만 베일이 빠져 일정량 어둡다. 덧셈형이라는 관찰과 맞는다. 원리는 전반사 막 측정법과 같다 [22][23][24].
  5. 굴곡 메니스커스의 굴절·반사: 빛 쪽 테두리 밝음, 반대쪽 그림자를 설명한다(기하 광학).
  - 거대 슬러그 중심이 거의 0인 것은 4번과 충돌한다. 7 mm처럼 슬러그 밑에 액층이 남으면 그 액층 안에 다시 빛이 갇혀 베일이 생긴다. → **예측: 0.3~1 mm 슬러그는 균일하게 어둡고, 7 mm 웅덩이 중심은 액체와 비슷하다.** 갭별 영상으로 검증할 수 있다.
- **밝기로 기포 밑 액막 유무를 판정할 수 있나.**
  - 가시광에서 물의 흡수는 무시할 만하다(550 nm 4.5×10⁻⁴ /cm) [20 계산]. 막 두께 정보가 밝기에 실리지 않는다.
  - 전반사 기반 판정은 "기체가 있다"를 알려줄 뿐 "막이 있다"는 구분하지 못한다. 평행 층에서는 n·sinθ가 보존되어, 막이 소멸파 깊이(약 0.1 µm)보다 두꺼우면 막/기체 계면에서도 똑같이 전반사된다(추정 해석). 투명 가열면 연구 [26]도 이 한계 안에서 "건조"를 판정했다.
  - 근적외 흡수(1.4~2.0 µm)는 원리상 가능하다. 왕복 투과율이 막 20 µm에서 0.95(1.4 µm)/0.76(2.0 µm), 0.3 mm 액층에서 0.48/0.016이다 [20 계산]. 레이저 소광법 [25]과 같은 원리다. InGaAs 카메라가 필요해 **비용이 든다**(사용자 판단 사항).
- **바로 할 수 있는 확인.**
  - 덮개 윗면에 무광 흑색 띠나 반사 방지 처리를 일부만 하고 기포 대비를 비교 → 4번 가설 검증.
  - 조명 방향을 바꾸거나 확산 돔 조명으로 테두리 비대칭이 바뀌는지 본다.
  - 편광판을 교차시켜 정반사 번쩍임을 줄인다(일반 기법).
  - 갭별로 기포 크기와 대비의 관계를 잰다(위 예측 검증).

### Q3. 철 블록 열전대로 h 구하기
- **시간 응답.** 탄소강 2 mm 깊이에서 10 Hz 진폭 5%, 50 Hz 0.1%다(`estimates_microgap.md` 9장). 실험으로도 15 Hz 진동에서 벽 온도 진동은 사실상 없었다 [39, C+A]. → h는 운전점별 시간 평균으로만 영상 지표와 연결한다.
- **외삽 보정.** 깊이 z의 보정량 qz/k와 위치 오차의 영향(추정):

  | k (W/m·K) | q (kW/m²) | z = 2 mm 보정 | 위치 오차 0.2 mm |
  |---|---|---|---|
  | 15(스테인리스) | 20 / 100 | 2.7 / 13.3 K | 0.27 / 1.33 K |
  | 50(탄소강) | 20 / 100 | 0.8 / 4.0 K | 0.08 / 0.40 K |
  - k 자체의 불확도(±5~10%)가 보정량에 그대로 곱해진다. 철 종류(탄소강/주철/스테인리스)와 k(T)를 확인한다.
  - 깊이가 다른 열전대 3개 이상으로 기울기를 회귀하면 q와 T_w를 공분산과 함께 얻는다 [47][50].
- **설치 교란.** 저열전도 재료에서 구멍과 선이 온도장을 바꾼다 [42]. 가는 피복 열전대(0.25~0.5 mm), 등온면을 따라 뚫은 구멍, 열전도 페이스트를 쓴다(일반 권고).
- **2D/3D 공액 전도.** 낮은 유량에서 1D 역산은 h를 과소평가한다 [41]. 비오 수 h·t/k(t = 5 mm)는 탄소강 0.2~1.0, 스테인리스 0.7~3.3이다(h = 2~10 kW/m²K, 추정). 기포가 만드는 불균일 h를 철이 옆으로 고르게 퍼뜨리지 못한다. → 블록 3D 전도 모델로 열전대 값을 해석하거나, 최소한 단상 시험으로 검증한다.
- **열손실·기준 시험.** 단상 가열 시험에서 전기 입력과 ṁc_pΔT의 차이를 블록–주위 온도차에 대해 맞춘다. 같은 시험으로 외삽 T_w의 h가 층류 이론(주제 4)과 맞는지 본다. 미지 저항이 있으면 윌슨 도표 [44]를 쓰되 정확도 주의 [45].
- **정상 상태 시간.** τ ≈ L²/α: 두께 20 mm 탄소강 29 s, 스테인리스 101 s(추정). 운전점마다 3~5τ를 기다린다. 과도 운전이면 역열전도 [46].
- **가열체 두께·열용량.** 비등이면 가열체 물성이 CHF에 들어간다 [43]. 빠른 가열 변동은 벽이 감쇠한다 [39].
- **좁은 갭 가열 블록 사례.** 구리 히트싱크 + 동기 측정 [40], 얇은 가열 박막 + 액정/적외선 열화상 [13]이 있다. 구리는 외삽 보정이 작고 철은 기울기(열유속)를 재기 쉽다. 철 블록 자체의 체계적 비교 문헌은 이번에 찾지 못했다(4장).

### Q4. 압력 강하 측정·분해 (0.3 mm 탭·입출구 손실 보강)
- **성분.** 마찰 + 입출구(급축소·급확대) + 가속 + 중력(수평이면 0) + 0.3 mm에서는 기체 팽창.
- **입출구 손실의 상대 크기**(L = 0.1 m, 층류 마찰, K = 1.5, 추정):

  | H (mm) | 0.05 m/s 마찰 / 입출구 | 0.2 m/s | 1 m/s | 발달 길이 L_fd (0.05 / 0.2 / 1 m/s) [34] |
  |---|---|---|---|---|
  | 0.3 | 668 / 1.9 Pa (0.3%) | 2672 / 30 Pa (1.1%) | 13360 / 749 Pa (5.6%) | 0.3 / 0.8 / 4.0 mm |
  | 0.7 | 123 / 1.9 (1.5%) | 491 / 30 (6.1%) | 2454 / 749 (31%) | 1.2 / 4.4 / 22 mm |
  | 1 | 60 / 1.9 (3.1%) | 241 / 30 (12%) | 1202 / 749 (62%) | 2.4 / 8.9 / 44 mm |
  | 3 | 6.7 / 1.9 (28%) | 27 / 30 (112%) | 난류 | 20 / 79 mm / - |
  | 7 | 1.2 / 1.9 (153%) | 난류 근처 | 난류 | 108 mm / - / - |
  - 0.3 mm에서는 입출구 손실이 작다. 이상류에서 2배 틀려도 ±3% 이내다(추정).
  - 1 mm 고속과 3·7 mm에서는 입출구 손실이 마찰과 같거나 크다. 이상류 모델은 균질 모델이 완전히 틀리고 미끄럼 모델도 2배 틀린다 [32][33].
- **탭 설계.**
  - 채널 안, 입구에서 발달 길이 뒤에 탭 3개 이상 → 직선 분포를 확인하고 기울기만 쓴다 [30][33].
  - 0.3 mm에서는 탭 구멍(0.5~1 mm)이 갭보다 크다. 구멍에 기포가 갇히면 오프셋과 감쇠가 생긴다. 측정 전 배관에 기포가 없게 한다 [33]. 탭을 투명 덮개에 내면 갇힌 기포를 볼 수 있다(제안).
  - 무유동 영점으로 기울기·정수압을 보정한다(1° 기울기면 0.1 m에서 17 Pa, `estimates_microgap.md` 7장).
- **가속 항.** 비등이면 크다(estimates 7장). 공기-물 0.3 mm는 기체 팽창이 가속 항이 된다. 국소 압력으로 jG를 구한다.
- **압력 변동과 기포 통과 빈도.** 차압 변동의 확률밀도·스펙트럼으로 양식을 판별한 연구가 고전이다 [35][36]. 작은 직사각 채널에서도 시간-주파수 해석 사례가 있다 [37]. 고속 영상과 고주파 압력의 동기 측정은 마이크로채널 비등에서 표준이 됐다 [38][40].
  - 영상으로 각 탭 위치의 기포 통과 빈도를 세고, 압력 스펙트럼 봉우리와 비교할 수 있다. 두 탭 신호의 상호상관 지연으로 구한 속도를 추적 속도와 비교할 수도 있다(제안).
- **카메라–DAQ 동기(권고).**
  1. 카메라의 프레임 TTL 출력을 DAQ 아날로그 채널에 압력과 함께 기록한다(프레임마다 DAQ 시간).
  2. 화면 구석 LED를 DAQ 디지털 출력으로 무작위 부호 점멸 → 절대 정렬과 프레임 누락 검사.
  3. 시작 때 밸브를 한 번 두드려 압력·영상 사건의 상호상관으로 확인한다.
  - 기대 정밀도는 1 프레임 이하다(추정). 압력 표본은 2 kHz 이상(임피던스 기공률도 2 kHz였다 [5]). 짧고 단단한 배관으로 공진 주파수를 기포 통과 빈도(4~60 Hz)보다 충분히 높인다.

### Q5. 영상 계측의 불확도 예산
| 요인 | 크기(추정) | 갭 의존 | 대책 |
|---|---|---|---|
| 경계 ±1 px | 면적 오차 ≈ 4/d_px: 8 px 50%, 20 px 20%, 100 px 4%, 230 px 1.7% | 0.3 mm에서 가장자리 폭과 비슷 | 5~8 px 거품은 개수만 보고. 경계 규약 명시 |
| 화소 보정 px/mm | 0.1~0.5%(정밀 격자판) | 7 mm는 높이에 따라 배율 차 | 철 표면 위치와 덮개 안쪽 위치 두 곳에서 교정 |
| 깊이에 따른 배율 | 7 mm 물층의 겉보기 깊이 5.25 mm → 작업거리 150/300/500 mm에서 3.5/1.75/1.05% | 0.3~1 mm는 0.5% 이하 | 텔레센트릭 렌즈 또는 높이별 보정 |
| 덮개 굴절 | 초점면 이동 t(1 − 1/n) | 덮개 두께 의존 | 물을 채우고 덮개 너머로 교정 |
| 피사계 심도 | 7 mm에서 겉보기 5.25 mm 필요 | 7 mm만 문제 | 조리개를 줄이고 조명을 키움 |
| 움직임 흐림 | 프레임당 50 px 이동 → 흐림 ≤ 1 px이려면 노출 ≤ 프레임 간격의 2% | 공통 | 노출 시간 기록·확인 |
| 검출·추적 오차 | QC 플래그, 연결 감사(사람 판정) | 공통 | 크기별 놓침·오연결률을 α, f, C0로 전파(몬테카를로 [47]) |
| 시간 | 프레임 간격(카메라 내부 시계) | 공통 | 동기 TTL로 확인 |

- 속도: 중심 위치 정밀도 0.1~0.5 px면 50 px/프레임에서 0.2~1%다(추정). 큰 기포는 변형 때문에 앞끝/중심 선택이 편향을 만든다.

### Q6. 이 실험에 맞는 권고 (1920×1200, 위에서 철 바닥, 갭 0.3/0.7/1/3/7 mm)
1. **갭 실측(최우선, 0.3·0.7 mm).**
   - 단상 층류 ΔP–유량으로 수력 갭 H_h = (12μQL/(WΔP))^(1/3)을 갭마다 구한다. ΔP·Q·μ 각 1%, W·L 0.5%면 H_h ±0.6%(0.3 mm에서 ±1.9 µm)다(추정).
   - 물의 점도는 20 °C 근처에서 2.2%/K 바뀐다. 액체 온도를 ±0.2 K로 잰다(추정).
   - 같은 장치를 운전 게이지압 범위에서 보정한다(덮개 휨). 평탄도 편차 σ는 2차 효과다: σ = 30 µm라도 0.3 mm에서 H_h −0.5% [27].
   - 기계적 측정(간극 게이지, 레이저 공초점 변위계 [4])으로 한두 점을 교차 확인한다. 7 mm는 단상 ΔP가 작아 수력 보정이 부정확하니 기계 측정을 쓴다.
2. **덮개 강성.** 긴 판 근사(클램프/단순지지) 휨(추정):

   | 덮개 | 두께 | 무지지 폭 | 10 kPa | 100 kPa |
   |---|---|---|---|---|
   | PMMA | 10 mm | 40 mm | 0.2~1.2 µm | 2.3~12 µm |
   | PMMA | 10 mm | 80 mm | 3.7~18 µm | 37~184 µm |
   | PMMA | 20 mm | 80 mm | 0.5~2.3 µm | 4.6~23 µm |
   | 유리 | 10 mm | 80 mm | 0.2~0.9 µm | 1.7~8.7 µm |
   - Sadatomi et al.의 조건(아크릴 12 mm, 폭 80 mm, 96 kPa)이면 20~100 µm로, 0.778 mm 갭의 3~13%다(추정). 그래서 보강했다 [5].
   - 가열 실험에서는 PMMA의 열팽창(약 7×10⁻⁵ /K)과 휨도 갭을 바꿀 수 있다(추정).
3. **압력 탭.** 채널 안 3개 이상, 첫 탭은 입구에서 발달 길이(0.3 mm: 수 mm, 1 mm: 수십 mm, 7 mm: 100 mm 이상) 뒤. 배관 기포 제거, 무유동 영점, 차압계 범위를 갭마다 바꾼다.
4. **기공률.** 갭별 모양 모델 + 경계 규약 + 막 보정. 7 mm는 옆 시점 영상(또는 프리즘)으로 기포 두께를 일부 조건에서 확인한다 [10].
   - **기체 유량 닫힘 검사**(장비 추가 없음): 영상의 Σ(부피 × 속도)/창 길이를 계량 기체 유량(국소 압력 보정)과 비교한다. 갭별 부피 모델의 직접 검증이다(제안).
5. **열.** 단상 가열 기준 시험(열손실, 외삽 검증), 열전대 3개 이상/위치, 철의 k 확인, 블록 3D 전도 모델.
6. **동기.** TTL 기록 + LED 부호 + 사건 상호상관. 노출 시간과 프레임 속도를 운전점마다 기록.
7. **영상 교정.** 정밀 격자판을 철 표면 높이와 덮개 안쪽 높이에 두고, 물을 채운 상태로 덮개 너머에서 찍는다. 렌즈 왜곡도 같은 영상으로 보정.

## 3. 아이디어와 시사점
| 아이디어 | 새로움 | 필요한 데이터 | 실현성 | 위험 |
|---|---|---|---|---|
| A. 기체 유량 닫힘 검사로 갭별 부피 모델 검증 | 좁은 갭 영상 기공률 논문에서 이 검사를 본 적 없음(검색 미확인, 4장) | 계량 기체 유량, 채널 압력 분포, 추적 결과 | 높음(이미 있는 자료) | 창 밖으로 나가는 기포, 압축성, 합체·분열 시 부피 보존 |
| B. 수력 갭 + 평탄도 통계로 0.3 mm 갭 불확도 정량 | 암석 균열 문헌에선 표준 [27], 마이크로갭 이상류에선 드묾 | 단상 ΔP–Q, 온도, 간극 게이지 몇 점 | 높음 | 덮개 휨이 압력에 따라 변함 [28][29] |
| C. 갭별 기포 대비 측정으로 광학 기구 판별 | 불투명 금속 위 기포 밝기 기구를 다룬 문헌 못 찾음 | 같은 조명에서 갭별 영상, 덮개 일부 무광 처리 | 높음 | 조명·덮개가 갭마다 다르면 비교 불가 |
| D. 근적외 흡수 영상으로 막·기공률 직접 측정 | 레이저 소광의 영상판 [25] | InGaAs 카메라, 1.45 µm 광원 | 낮음(**비용**) | 덮개(PMMA)의 근적외 흡수, 고속 InGaAs 가격 |
| E. 압력 스펙트럼 봉우리 ↔ 영상 통과 빈도, 두 탭 상호상관 속도 ↔ 추적 속도 | 일대일 대응을 좁은 갭 단열에서 한 연구 못 찾음 | 고주파 차압 2개 이상, 동기 영상 | 중간 | 배관 공진, 0.3 mm에서 탭 구멍 기포 |
| F. 검출·추적 오차를 α, f, C0로 전파 | 영상 이상류 논문에서 드묾(주제 5와 겹침) | QC·연결 감사 결과 | 높음 | 표본 수, 크기별 편향 |

## 4. 새로움 판단 기록 (검색어와 결과 수)
- **Crossref**(query.bibliographic, rows 3~8, 약 45회): 시작 문헌 12편 모두 대조(Kline & McClintock 1953은 DOI 없음). 주요 주제 검색:
  - "void fraction image processing comparison quick closing valves two-phase flow small channel"(6건: 영상 vs QCV 좁은 갭 직접 비교 없음).
  - "interfacial area concentration image processing narrow rectangular channel bubbly flow"(6건: Fu & Liu 2016, Shen 2012, Liu 2023 등. 독립 비교는 확인 못 함).
  - "pressure drop fluctuation spectrum dominant frequency bubble passing frequency high-speed video narrow rectangular channel"(8건: 비등 기포 빈도·압력 강하 학회 논문뿐, 일대일 대응 없음).
  - "Taylor bubble frequency from pressure signal compared with high speed imaging minichannel slug flow"(6건: 관련 없음).
  - "conductance electrode void fraction sensor narrow rectangular channel"(8건: Liu & Asano 2026, Asano 2018, Jin 2014 등).
  - "effect of wall material thermal conductivity on measured heat transfer coefficient conjugate minichannel stainless steel copper"(8건: 관련 없음) → 철 블록 열전대의 체계적 비교 문헌은 못 찾음.
  - "synchronization high-speed camera data acquisition two-phase flow pressure signal trigger LED"(6건: 관련 없음) → 동기 방법만 다룬 문헌은 없고, 응용 논문 [38][40]이 방법을 기술.
- **Google Scholar(WebFetch 2회)**
  - `"pressure fluctuation" "narrow rectangular channel" "high-speed camera" frequency spectrum bubble` → 약 33건. Li et al. 2014 [37], Park et al. 2026(비등 양식 판별) 외에 영상 통과 빈도와 스펙트럼을 일대일로 맞춘 단열 연구는 첫 쪽에 없음.
  - `"void fraction" "image processing" "narrow rectangular channel" "quick closing valve" OR "neutron radiography" OR "capacitance" comparison` → 약 59건. Hibiki et al. 1992(중성자+영상), Kureta 2001, Jin 2014, Zhang 2023(수평 미니관, QCV 오차 언급) 등. 0.3~1 mm 수평 갭에서 영상 기공률을 기준법과 비교한 결과는 첫 쪽에서 확인 못 함.
- **WebSearch(standard, 약 15회)**: Mishima 1993 상세(갭 값 미확인), Kawahara 2002 방법(미확인), Musterd 공개본, Passoni 공개본, Abdelall 결과(미확인), Matsui 내용, Hurlburt & Newell 원리, Steinke & Kandlikar, Maranzana M 정의(2차), Golobič 내용, Nishio & Tanaka(방법 미확인), 평행 평판 K(∞) 값(미확인), Duan 2013 동기 방법(저장소 429로 미확인).
- **OpenAlex·Semantic Scholar**: Elsevier 초록을 주지 않아 쓸모가 적었다(5회 정도).
- **"없다"의 범위**: 위 검색어·첫 쪽 결과 기준이다. 중국어·일본어 학회 논문은 거의 보지 못했다.

## 5. 남은 의문과 사용자에게 확인할 것
- **갭**: 갭을 무엇으로 정했나(가공 단차/스페이서/개스킷)? 갭별 실측값과 측정법? 0.3·0.7 mm 단열 실험 때 단상 ΔP–유량 자료가 있나(있으면 수력 갭을 바로 역산할 수 있다)?
- **덮개**: 재질(PMMA/유리/폴리카보네이트), 두께, 채널 폭(무지지 폭), 운전 게이지압.
- **압력**: 탭 위치·개수·구멍 지름, 차압계 종류·범위·표본 주파수, 배관 길이.
- **유량**: 기체 유량계 종류(닫힘 검사 가능 여부), 액체 온도 측정 위치.
- **카메라**: 프레임 속도, 노출 시간, 렌즈(텔레센트릭 여부), 작업 거리, px/mm, 조명 방향·종류, 덮개 윗면 처리.
- **열**: 철 종류(k), 열전대 종류·지름·깊이·개수, 히터 전력 측정법, 블록 크기, 단상 가열 시험 여부.
- **염료**: 단상 보정용으로 형광·흡광 염료를 한 번 쓸 수 있나(갭 지도 [29])?
- **확인하지 못한 것**
  - Mishima 1993의 C0 값과 정확한 갭 값(원문 미확인).
  - Abdelall 2005의 원문 수치(학위논문의 인용으로만 확인).
  - Shah & London의 평행 평판 K(∞) 값(인용하지 않음).
  - Nishio & Tanaka 2004(IJHMT 47:4559)의 방법 세부, Bröder & Sommerfeld 2007의 초점 기준, Duan et al. 2013의 동기 방식(접속 제한).
  - 갇힌 빛 가설은 문헌 원리에서 세운 추정이다. 실험으로만 확인된다.

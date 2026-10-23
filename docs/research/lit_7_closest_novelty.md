# 주제 7. 가장 가까운 선행 연구와 새로움 점검 (갭 0.3·0.7·1·3·7 mm)

작성: 문헌 조사 에이전트 7, 2026-10-23. 범위 변경(갭 다섯 개)과 우선순위 변경(신규성 우선, Huang et al. 2024 대비)을 반영했다.
확인 수준: `C+F` 원문 확인, `C+A` 초록 확인, `C` Crossref 대조만(내용은 2차 자료), `U` 대조 못 함. 서지는 `refs_7_closest_novelty.tsv`.
Co = Lc/H, Lc = √(σ/(gΔρ)). 물 20 °C Lc = 2.73 mm, 100 °C 2.50 mm(`estimates_microgap.md`).

## 0. 요약
1. 찾은 범위에서 **"한 장치에서 서브 mm~7 mm로 갭을 바꾸고, ΔP + 벽 온도/h + 위에서 본 영상의 정량 지표(추적 포함)를 함께 잰 연구"는 없다.** 조건 세 개를 모두 만족하는 결과가 Scholar 13건, WebSearch 4회 모두 0건이었다(4장).
   - 단, **측정 구성 자체는 새롭지 않다.** Shinmoto et al. 2017(규슈대 오타 그룹)이 수평 채널, 아래 금속 블록 가열(깊이 1.5/8.5/15.5 mm 열전대로 1차원 외삽), 가열 구간 ΔP, 위 유리 너머 고속 촬영을 갭 2/1/0.5 mm에서 함께 했다(본문 확인). 그들의 영상은 정성뿐이다.
   - → 새로운 것은 "정량 영상·추적 지표"와 "Co 9.1→0.39 갭 범위", 그리고 그것으로 하는 검증(주장 10·11)이다.
2. 가장 가까운 연구 5편(1-1표 A1~A5): Shinmoto 2017(배치·측정 구성이 같음), Alam 2012(갭 10개 + ΔP + h + 영상), Lee & Lee 2001(수평 0.4~4 mm, ΔP·h), Albahloul & Hollingsworth 2015(공기 주입 + 영상 → 열전달 모델), Zhu 2023(물, 0.5/1/2 mm, 영상 + ΔP + h).
3. **갭 범위**: 우리 묶음은 H 23배(1.37자릿수), Co 9.1→0.39다. Co = 1과 2Lc(위 덮개 밑 웅덩이 두께)를 모두 가로지른다. 강제 흐름 연구 중 가장 넓은 것은 Alam 2012(12.5배, 모두 Co > 2.5)와 Lee & Lee 2001(10배, 2Lc 미도달)이다. 더 넓은 것은 풀 비등 두 편(Cardoso 2011 130배, Fujita 1988 33배)뿐이다(1-2표).
4. **Huang et al. 2024(IJMF)와 Chang et al. 2023(IJHMT, BubbleMask)이 "영상 특징 → h·CHF 상관식/모델 개선"을 이미 했다.** 그래서 "영상 지표로 상관식을 개선했다"는 주장만으로는 신규성이 약하다(메인 초안과 같은 판단).
5. **추천 주장 1순위: (10) 운동학–동역학 폐합.** 추적한 크기별 C0로 메니스커스 마찰 계수를 정하고, 그 값으로 ΔP 증가분을 맞춤 없이 예측한다. 0.3·0.7 mm 단열 자료로 바로 시작할 수 있다. 새로움 **중~높음**, 실현성 높음.
6. **2순위: (11) 기하가 정하는 영상 변수 φ_c + 갭 하나 빼기 검증**(가열 실험 후). 새로움 중~높음. 두 주장 모두 (13) 오차 전파를 붙이면 심사 대응력이 커진다.
7. 새로움이 낮은 것: 갇힘 틀 자체(H1의 틀), 성능 지도(H5), 영상 빈도 + 3구역 모델(H8), 압력 스펙트럼(H9). 공기 주입 + 영상 + 열전달(메인 초안 G7)은 Albahloul 2014/2015가 이미 했다.
8. 메인 초안(`novelty_analysis.md`)과 다른 판정: N1은 "높음"이 아니라 "중~높음"(미세유체·폼에 개념 선례), G6·G7은 지상 선례가 있다(3-3절).

## 1. 문헌 표

### 1-1. 가장 가까운 선행 연구 (Q1: 한 장치에서 갭을 바꾼 연구, 배치가 같은 연구)
가장 가까운 것을 위에 두었다.

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| A1 | Shinmoto, Yamamoto, Fujii, Ohta (2017) | Heat Transfer Characteristics during Boiling of Immiscible Liquids Flowing in Narrow Rectangular Heated Channels | Front. Mech. Eng. 3:16 | 10.3389/fmech.2017.00016 | 수평, **아래 벽 가열**(알루미늄 블록 7개, 그 밑 구리 블록의 카트리지 히터), **블록 속 깊이 1.5/8.5/15.5 mm 열전대로 표면 온도·열유속 외삽**, **가열 구간 ΔP(Validyne P55D)**, 위 유리판 너머 **고속 촬영**(≤1000 fps). 30 × 175 mm, H = 2/1/0.5 mm. FC72·물·혼합. 유량 0.5/0.25/0.13 L/min, G 137~450 kg/m²s, 출구 0.1 MPa | FC72 CHF: 2 mm 약 1.4~1.5×10⁵, 1 mm 1.2~1.3×10⁵(하류 6.6×10⁴), 0.5 mm 0.8~1.1×10⁵(하류 6.2×10⁴) W/m². 납작한 기포의 박막 증발(증진)과 건조 반점(저하)이 경쟁 | **배치와 측정 구성(ΔP + 매립 열전대 + 위에서 촬영)이 우리와 같다.** 다른 점: 갭 3개(0.6자릿수, 모두 Co > 1), 영상은 정성(기포 크기·기공률·건조 면적 정량 없음), 비등만 | C+F(본문 HTML 앞부분) |
| A2 | Alam, Lee, Yap, Jin, Balasubramanian (2012) | Experimental investigation and flow visualization to determine the optimum dimension range of microgap heat sinks | IJHMT 55(25-26):7623-7634 | 10.1016/j.ijheatmasstransfer.2012.07.080 | 실리콘 마이크로갭 10종(80~1000 µm), 물 흐름 비등, 고속 가시화 | ≤ 500 µm는 갇힘(갇힌 슬러그·환상류), ≥ 700 µm는 비갇힘(기포류). ΔP와 변동은 갭이 클수록 작아지고, 벽 온도와 변동은 커진다. h는 ≤ 500 µm에서 갭에 강하게 의존하고 ≥ 700 µm에서 무관. < 100 µm는 조기 부분 건조 | "갭 스윕 + ΔP + h + 영상"이라는 구성이 같다. 모두 Co > 2.5, 영상은 정성, 공기-물 없음 | C+A |
| A3 | Lee HJ, Lee SY (2001a) | Pressure drop correlations for two-phase flow within horizontal rectangular channels with small heights | IJMF 27(5):783-796 | 10.1016/s0301-9322(00)00050-1 | 수평, 폭 20 mm, 갭 0.4~4 mm, 공기-물 | L-M형, Chisholm C가 질량유속·갭의 함수, ±10%(메모). 갭이 줄면 plug 영역이 늘고 bubbly가 줄며, plug-slug·slug-annular 천이는 갭 영향이 작다(KAIST 학위논문 요약) | 우리 0.3~3 mm와 거의 같은 수평 범위. 영상 지표·7 mm·가열 없음 | C |
| A4 | Lee HJ, Lee SY (2001b) | Heat transfer correlation for boiling flows in small rectangular horizontal channels with low aspect ratios | IJMF 27(12):2043-2062 | 10.1016/s0301-9322(01)00054-4 | 수평, R113 흐름 비등, 갭 0.4~2 mm | 작은 갭·낮은 유량에서 열전달은 액막 두께가 지배(검색 요약) | 같은 장치 계열의 h. 영상 지표 없음 | C |
| A5 | Lee SY, Lee HJ (2001c) | 미세 수평 사각 유로 내에서의 비등 유동 압력강하 | 대한기계학회논문집 B 25(9):1219-1226 | KISTI DOI(표 참고) | R113, 갭 0.4~2 mm, G 50~200, q ≤ 15 kW/m² | Lee(2001) 승수가 ±20%로 맞음 | 한국의 기준 연구 | U |
| A6 | Albahloul, Hollingsworth (2015) | Observations of bubble shape and confinement in diabatic two-phase flow in a minichannel | IJHMT 83:200-211 | 10.1016/j.ijheatmasstransfer.2014.09.029 | 수평 1.29~1.48 mm, 폭 23 mm, Novec 649 층류에 **공기 주입**. **위 벽 가열**, 아래 투명 벽으로 평면 영상, 액정 열화상(학위논문 A7) | 모양: 구 → 비대칭 회전타원 → 채널을 가로지르는 마름모(d ≥ 1.5H). 막힘 보정 액체 속도로 속도비가 거의 일정. 증진 원인 = 후류 혼합 + 막힘에 의한 액체 가속. 단상 대비 최대 3.5배, 후류 전도 모델 ±18%(A7) | 공기 주입 + 영상 → 열전달 모델의 가장 가까운 선례. 갭 1개, ΔP 없음, 가열면이 기포 쪽(위) | C+A |
| A7 | Albahloul (2014) | Heat transfer enhancement caused by sliding noncondensable gas bubbles in a minichannel (PhD, UAH) | 학위논문 | - | A6과 같음 | A6 참고 | | U |
| A8 | Zhu, Li, Liu, Mubarak, Wang (2023) | Experimental study of flow boiling characteristics in minigap channels over a wide heat flux range | IJHMT 201:123567 | 10.1016/j.ijheatmasstransfer.2022.123567 | 물, 갭 0.5/1/2 mm, G 200~400 kg/m²s | G = 400에서 ΔP 최대 12.2/3.8/1.6 kPa, h 최대 7.3/6.9/5.8 W/cm²K(0.5/1/2 mm). CHF는 G·갭과 함께 증가. 새 ΔP 상관식 10.8% | 물·다중 갭·영상 + ΔP + h. 방향·가열면은 초록에 없음. 0.6자릿수 | C+A |
| A9 | Xu, Cheng, Zhao (1999); Xu (1999) | Gas–liquid two-phase flow regimes in rectangular channels with mini/micro gaps; …with mini gaps | IJMF 25(3):411-432; IJHFF 20(4):422-428 | 10.1016/s0301-9322(98)00057-3; 10.1016/s0142-727x(99)00002-8 | 수직, 공기-물, 갭 0.3/0.6/1.0 mm | 0.3 mm에서는 기포류가 없고 cap-bubbly, slug-droplet, churn, annular-droplet. 갭이 줄면 천이선이 낮은 j_G 쪽으로 | **사용자의 0.3·0.7 mm 단열 실험과 같은 갭.** 수직·가열·추적 없음 | C; C+A |
| A10 | Mishima, Hibiki, Nishihara (1993) | Some characteristics of gas-liquid flow in narrow rectangular ducts | IJMF 19(1):115-124 | 10.1016/0301-9322(93)90027-r | 수직, 공기-물, 갭 1.0~5.0 mm(2차 인용) | 유동 양식, 기공률(분포 계수 약 1.35, 2차 인용), 슬러그 속도, 마찰 손실 | 1·3 mm에 해당. 수직·가열 없음 | C |
| A11 | Kim YH et al. (2005) | Visualization of boiling phenomena in inclined rectangular gap | IJMF 31(5):618-642 | 10.1016/j.ijmultiphaseflow.2005.01.002 | 포화수 풀 비등, 갭 1/2/5/10 mm, 90~180° | CHF는 기울기와 갭 감소에 따라 줄고, 아래 향 면에서는 갭이 좁을수록 늘었다(메모) | 1~10 mm + 가시화. 흐름·ΔP 없음 | C |
| A12 | Fujita, Ohta, Uchida, Nishikawa (1988) | Nucleate boiling heat transfer and critical heat flux in narrow space between rectangular surfaces | IJHMT 31(2):229-239 | 10.1016/0017-9310(88)90004-x | 포화수 1 atm, 갭 5/2/0.6/0.15 mm, 수직~거의 수평 아래 향, 가장자리 조건 3종 | 초록에 수치 없음 | 서브 mm~5 mm. 풀 비등 | C+A |
| A13 | Cardoso, Kannengieser, Stutz, Passos (2011) | FC72 and FC87 nucleate boiling inside a narrow horizontal space | ETFS 35(6):1038-1045 | 10.1016/j.expthermflusci.2011.02.006 | 위 향 가열 원판(지름 12 mm) + 위 덮개, s = 0.1/0.2/0.3/0.4/0.5/1/13 mm, FC72(Lc 0.73 mm), FC87(0.98 mm) | 낮은 열유속에서 갭이 줄면 비등이 증진되고 건조 열유속은 줄어든다. Bo < 1이면 얇은 막 영역 | 수평·아래 가열·위 덮개(풀). 1~13 mm 사이 점이 없다 | C+F(부분) |
| A14 | Klugmann, Dąbrowski, Mikielewicz (2019) | Flow Boiling in Minigap in the Reversed Two-Phase Thermosiphon Loop | Energies 12(17):3368 | 10.3390/en12173368 | 증발기 0.1 × 0.2 m, minigap 1/2/3 mm, 물·에탄올 | 유동 구조 영상 + 압력 변화 | 물·1~3 mm | C+A |
| A15 | Lee J, Chae, Chang (2013) | Flow instability during subcooled boiling for a downward flow at low pressure in a vertical narrow rectangular channel | IJHMT 67:1170-1180 | 10.1016/j.ijheatmasstransfer.2013.08.049 | 수직 하향, 양면 가열, 갭 2.5/3.3/4.1 mm, 폭 40 mm, 길이 350 mm | 맞은편 가열면의 기포가 합쳐질 때 유동 일탈. 갭을 넣은 새 상관식 | 한국 다중 갭 + 고속 영상 | C+A |
| A16 | Willingham, Mudawar (1992) | Channel height effects on forced-convection boiling and critical heat flux from a linear array of discrete heat sources | IJHMT 35(8):1865-1880 | 10.1016/0017-9310(92)90190-4 | FC-72, 채널 높이 2/5/10 mm(검색 요약) | 원문 미확인(Purdue PDF 503) | 채널 높이 비교의 고전 | C |
| A17 | Chinnov, Ron'shin, Kabov (2016) | Two-phase flow patterns in short horizontal rectangular microchannels | IJMF 80:57-68 | 10.1016/j.ijmultiphaseflow.2015.11.006 | 수평, 높이 100~500 µm, 폭 9~40 mm, 슐리렌·형광 | 채널이 얇을수록 churn 영역이 크게 넓어짐 | 0.3 mm 부근 수평 단열 | C+A |
| A18 | Liu A, Cheng, Yan, Gu, Meng (2022) | Experimental study on length, liquid film thickness and pressure drop of slug flow in horizontal narrow rectangular channel | ChERD 182:502-516 | 10.1016/j.cherd.2022.04.010 | 수평 68 × 1.9 mm, 가시화 + PCB 액막 센서 + ΔP | 슬러그 속도 ∝ 혼합 속도. 액막은 기포 Re < 3100에서 Ca와 함께 증가. Lee 상관식(표면장력 영역)·Chisholm(관성 영역)이 최선 | 수평 한 갭에서 영상 길이·액막·ΔP를 함께 잼. 추적 기반 모델은 없음 | C+A |
| A19 | Ide, Fukano (2005) | Experimental research on the correlations of holdup and frictional pressure drop in air–water two-phase flow in a capillary rectangular channel | ETFS 29(7):833-841 | 10.1016/j.expthermflusci.2005.03.010 | 9.9 × 1.1 mm, 수직·수평(넓은 면 수직/수평) | 액괴 통과 빈도·속도, 홀드업, 마찰 ΔP. 종횡비·Re·Ca를 넣은 상관식 | 1 mm 수평 공기-물 | C+A |
| A20 | Omisanya, Chen, Utaka (2024) | Enhanced flow boiling heat transfer in narrow gap with different widths using different-mode-interacting boiling | IJHMT 226:125471 | 10.1016/j.ijheatmasstransfer.2024.125471 | 물(과냉 2~30 K), 갭 1/2/5 mm, 폭 10/80 mm, G 100~400 | CHF 3.59/3.66 MW/m², h 1261/2027 kW/m²K(폭 10/80 mm). 갭별 결과는 초록에 없음 | 일본 다중 갭 흐름 비등 | C+A |
| A21 | Kharangate et al. (2015) | Flow boiling and critical heat flux in horizontal channel with one-sided and double-sided heating | IJHMT 90:323-338 | 10.1016/j.ijheatmasstransfer.2015.06.073 | 수평 2.5 × 5 mm, FC-72, 위/아래 한쪽 가열·양쪽 가열, 고속 영상 | 가열 벽 위치에 따라 계면 거동이 다르다(검색 요약) | "기체가 가열면에 닿는가"의 중력 효과 선례 | C |
| A22 | Zhang K et al. (2021) | Experimental investigation on flow regimes and transitions of steam-water two-phase flow in narrow rectangular horizontal channels | PNE 131:103601 | 10.1016/j.pnucene.2020.103601 | 수평 1 × 20, 2 × 20 mm, 대기압, J_f 0.007~0.27, J_g 0.05~65.2 m/s | 유동 양식(초록 일부) | 수평 1·2 mm | C+A |
| A23 | He Q et al. (2022) | Research on frictional pressure drop of air-water co-current upward flow in vertical rectangular channels with different sizes | PNE 152:104377 | 10.1016/j.pnucene.2022.104377 | 수직, 4/6/8/10 mm(× 66, × 100) | Chisholm C가 D_h와 함께 28까지 증가. 새 모델 오차 < 15~24% | 3·7 mm 근처 다중 갭 ΔP | C+A |
| A24 | Bonjour, Lallemand (1998) | Flow patterns during boiling in a narrow space between two vertical surfaces | IJMF 24(6):947-960 | 10.1016/s0301-9322(98)00017-2 | 수직, R-113, 갭 0.5~2 mm | 3영역(고립 변형 기포·합쳐진 기포·부분 건조), Bond 수·환산 열유속 지도 | 갇힘 지도의 선례 | C+A |
| A25 | Liu S, Asano (2026, 프리프린트) | Void Fraction of Subcooled Flow Boiling within Horizontal Narrow Channel Measured by Capacitance Sensor | SSRN | 10.2139/ssrn.6753968 | 수평, 높이 4 mm, 바닥 가열면 20 × 50 mm, HFC245fa | 기공률은 열유속과 함께 증가, 막비등 전이에서 급감 | 일본(고베대) 수평·바닥 가열 좁은 채널 | C+A |

### 1-2. 갭 범위 비교 (Co = Lc/H)
- Lc 가정: 물 20 °C 2.73 mm, 포화수 2.50 mm, FC-72 0.73 mm·FC-87 0.98 mm(Cardoso 2011 표 1), R-113 포화 약 1.0 mm(σ = 0.0147 N/m, ρ_l = 1507 kg/m³로 계산, 추정), Novec 649 약 0.83 mm(σ = 0.0108, ρ = 1600으로 계산, 추정).
- "2Lc 넘음"은 수평 채널에서 위 덮개 밑 웅덩이(두께 약 2Lc)가 아래 벽에 닿지 않게 되는 갭이 있느냐다. 수직 채널에는 이 논리가 해당하지 않는다.

| 연구 | 흐름·방향 | 유체 | 갭 (mm) | Hmax/Hmin (자릿수) | Co 범위 | Co = 1 가로지름 | 2Lc 넘음 | ΔP / h / 영상 정량 |
|---|---|---|---|---|---|---|---|---|
| **우리** | 강제 흐름, 수평(추정)·아래 가열 | 물(공기 주입 또는 비등) | 0.3, 0.7, 1, 3, 7 | 23.3 (1.37) | 9.1 → 0.39 (비등 8.3 → 0.36) | 예 | 예(7 mm) | 예 / 예 / 예(추적 포함) |
| Cardoso 2011 (A13) | 풀, 수평 위 향 | FC72·FC87 | 0.1~1, 13 | 130 (2.11) | 7.3 → 0.056 | 예 | 예 | 아니오 / 예 / 정성 |
| Fujita 1988 (A12) | 풀, 기울기 | 포화수 | 0.15~5 | 33 (1.52) | 16.7 → 0.50 | 예 | 경계(5 mm ≈ 2Lc) | 아니오 / 예 / 정성 |
| Alam 2012 (A2) | 강제, 실리콘 | 물 비등 | 0.08~1.0 | 12.5 (1.10) | 31 → 2.5 | 아니오 | 아니오 | 예 / 예 / 정성 |
| Lee & Lee 2001a (A3) | 강제, 수평 | 공기-물 | 0.4~4 | 10 (1.00) | 6.8 → 0.68 | 예 | 아니오 | 예 / 아니오 / 아니오 |
| Kim YH 2005 (A11) | 풀, 기울기 | 포화수 | 1~10 | 10 (1.00) | 2.5 → 0.25 | 예 | 예 | 아니오 / CHF / 정성 |
| Lee & Lee 2001b (A4) | 강제, 수평 | R113 비등 | 0.4~2 | 5 (0.70) | 2.5 → 0.50 | 예 | 경계 | 예(A5) / 예 / 아니오 |
| Mishima 1993 (A10) | 강제, 수직 | 공기-물 | 1.0~5.0 | 5 (0.70) | 2.7 → 0.55 | 예 | (수직) | 예 / 아니오 / 중성자 영상 |
| Willingham 1992 (A16) | 강제 | FC-72 비등 | 2~10 | 5 (0.70) | 0.36 → 0.073 | 아니오 | 예 | 미확인 / 예 / 미확인 |
| Chinnov 2016 (A17) | 강제, 수평 | 기체-액체 | 0.1~0.5 | 5 (0.70) | 27 → 5.5 | 아니오 | 아니오 | 아니오 / 아니오 / 정성 |
| Omisanya 2024 (A20) | 강제 | 물 과냉 비등 | 1~5 | 5 (0.70) | 2.5 → 0.5 | 예 | 경계 | 미확인 / 예 / 미확인 |
| Zhu 2023 (A8) | 강제 | 물 비등 | 0.5~2 | 4 (0.60) | 5.0 → 1.25 | 아니오 | 아니오 | 예 / 예 / 정성 |
| Shinmoto 2017 (A1) | 강제, 수평 아래 가열 | FC72·물 | 0.5~2 | 4 (0.60) | 물 5.0 → 1.25 | 아니오 | 아니오 | 예 / 예 / 정성 |
| Bonjour 1998 (A24) | 자연 대류 비등, 수직 | R-113 | 0.5~2 | 4 (0.60) | 2.0 → 0.5 | 예 | (수직) | 아니오 / 예 / 정성 |
| Xu 1999 (A9) | 강제, 수직 | 공기-물 | 0.3~1.0 | 3.3 (0.52) | 9.1 → 2.7 | 아니오 | (수직) | 아니오 / 아니오 / 정성 |
| Klugmann 2019 (A14) | 열사이펀 | 물·에탄올 | 1~3 | 3 (0.48) | 물 2.5 → 0.83 | 예 | 아니오 | 압력 / 미확인 / 정성 |
| Lee J 2013 (A15) | 강제, 수직 하향 | 물(추정) | 2.5~4.1 | 1.6 (0.21) | 1.0 → 0.61 | 경계 | (수직) | 미확인 / 아니오 / 정성 |
| He 2022 (A23) | 강제, 수직 | 공기-물 | 4~10 | 2.5 (0.40) | 0.68 → 0.27 | 아니오 | (수직) | 예 / 아니오 / 아니오 |
| Albahloul 2015 (A6) | 강제, 수평 | 공기-Novec 649 | 1.29~1.48 | 1.1 (0.06) | 0.64 → 0.56 | 아니오 | 아니오 | 아니오 / 예 / 예(모양·속도) |
| 참고: Hibiki & Mishima 2001 | 여러 장치 자료 모음, 수직 | 공기-물 등 | 0.3~17 | 57 | — | — | — | 천이 기준 비교용(한 장치 아님, 검색 요약) |

- 해석: **강제 흐름에서 Co = 1과 2Lc를 함께 넘는 다중 갭 연구는 찾지 못했다.** 이 점이 1장 표의 "가장 가까운 연구"와 우리 자료를 가르는 가장 분명한 차이다.
- 단, "가장 넓은 범위"를 주장하려면 Ishibashi & Nishikawa 1969, Geisler & Bar-Cohen 2009, Satitchaicharoen & Wongwises 2004의 갭 값(초록에 없음)을 원문으로 확인해야 한다.

### 1-3. 가설별 판정에 쓴 선행 연구 (Q2 근거)
| # | 저자(연도) | 학술지 권(호):쪽 | DOI | 내용(숫자) | 관련 가설 | 확인 수준 |
|---|---|---|---|---|---|---|
| B1 | Huang, Chang, Suh, Mudawar, Won, Kharangate (2024) Machine learning boiling prediction: From autonomous vision of flow visualization data to performance parameter theoretical modeling | IJMF 179:104928 | 10.1016/j.ijmultiphaseflow.2024.104928 | 미세중력 흐름 비등 영상에서 ML 비전으로 기공률·계면 거동·젖은 벽 면적을 뽑음 → 기공률을 해석 모델로 검증 → 기공률과 젖음 전선 면적으로 h 상관식 개선, "공식 발견 가속"을 주장. 형상 변화·일반화·비전 불확도는 초록에 없음(본문 미확인) | 기준점(3, 8, 11, 13) | C+A |
| B2 | Chang et al. (2023) BubbleMask | IJHMT 217:124656 | 10.1016/j.ijheatmasstransfer.2023.124656 | 미세중력 흐름 비등 영상의 기포 특징 → CHF 모델 입력(메인 초안 기준) | 기준점 | C |
| B3 | Suh, Bostanabad, Won (2021) Deep learning predicts boiling heat transfer | Sci Rep 11:5622 | 10.1038/s41598-021-85150-4 | 영상 → 열유속 예측(같은 그룹의 앞선 연구) | 11 | C |
| B4 | Zhou, Garg, Qiu, Kim, Mudawar, Kharangate (2020) | IJHMT 162:120351 | 10.1016/j.ijheatmasstransfer.2020.120351 | 모은 자료로 만든 ML 상관식, 보지 못한 자료로 일반화 시험(검색 요약) | 11 | C |
| B5 | Fuerstman et al. (2007) The pressure drop along rectangular microchannels containing bubbles | Lab Chip 7(11):1479 | 10.1039/b706549c | ΔP는 기포 수가 지배(계면활성제 농도가 낮거나 높을 때), 중간 농도에서는 총 기포 길이. 기여 = 액체 슬러그 + 모서리 홈 + 끝 캡 | 2, 10 | C+A |
| B6 | Vanapalli et al. (2009) Hydrodynamic resistance of single confined moving drops in rectangular microchannels | Lab Chip 9(7):982-990 | 10.1039/b815002h | Ca 10⁻³~10⁻²에서 단일 액적 초과 ΔP, 크기에 따른 두 영역, 끝 캡 소산이 지배 | 2, 10 | C+A |
| B7 | Labrot et al. (2009) Extracting the hydrodynamic resistance of droplets from their behavior in microchannel networks | Biomicrofluidics 3:012804 | 10.1063/1.3109686 | **관측한 액적 거동(분기 선택, 간격 시계열)에서 액적 저항을 추출**, 표준 측정과 비교 | 10 | C+A |
| B8 | Sessoms et al. (2009) Droplet motion in microfluidic networks: hydrodynamic interactions and pressure-drop measurements | PRE 80:016317 | 10.1103/physreve.80.016317 | 액적 흐름으로 액적이 찬 채널의 초과 저항을 재는 방법 | 10 | C+A |
| B9 | Cantat (2013) Liquid meniscus friction on a wet plate: bubbles, lamellae, and foams | Phys Fluids 25(3):031303 | 10.1063/1.4793544 | 메니스커스 마찰 리뷰. 굳은 계면은 Ca^(1/3)과 Ca^(2/3)의 합. 폼이 젖은 벽을 미끄러질 때 응력 예측 | 2, 10 | C+A |
| B10 | Raufaste, Foulon, Dollet (2009) Dissipation in quasi-two-dimensional flowing foams | Phys Fluids 21(5):053102 | 10.1063/1.3142502 | Hele-Shaw 폼 소산. 기존 모델은 과소 예측, 불일치 ξ = 1.4(R_P/A)^(−0.5) | 2, 10 | C+A |
| B11 | Raufaste, Rose, Santucci, Dollet (2025) Friction-induced bubble edge curvature in flowing two-dimensional confined foams | PRF 10(2):023301 | 10.1103/physrevfluids.10.023301 | **영상의 기포 가장자리 곡률을 판 마찰과 연결**, 모델이 정량 일치(HAL 초록) | 10 | C+A |
| B12 | Booth, Wu, Griffiths, Howell, Nunes, Stone (2025) Bubble racing in a Hele-Shaw cell | JFM 1010:A19 | 10.1017/jfm.2025.322 | 배경 흐름에서 큰 팬케이크 기포가 작은 기포를 추월. Bretherton 매개변수 임계값 위에서는 충돌하지 않음 | 4, 6, 12 | C+A |
| B13 | Wu, Booth, Griffiths, Howell, Nunes, Stone (2024) Motion and deformation of a bubble in a Hele-Shaw cell | PRF 9(12):123603 | 10.1103/physrevfluids.9.123603 | 저 Re에서 이론과 속도 측정 일치, 문헌 속도 자료가 이론 척도로 모임(검색 요약) | 6, 10 | C |
| B14 | Monnet, John Soundar Jerome, Vidal, Joubaud (2024) Bubble dynamics in an inclined Hele-Shaw cell | PRF 9(7):073601 | 10.1103/physrevfluids.9.073601 | 부력이 기포를 위 벽으로 밀면 위 막만 Bretherton 척도, 속도가 Taylor–Saffman보다 크게 줄어듦(arXiv 초록) | 2, 3, 6 | C+A |
| B15 | Taylor, Saffman (1959) | QJMAM 12(3):265-279 | 10.1093/qjmam/12.3.265 | 원형 팬케이크 기포 속도 = 평균 유속의 2배(2차 인용) | 6 | C |
| B16 | Maxworthy (1986) Bubble formation, motion and interaction in a Hele-Shaw cell | JFM 173:95-114 | 10.1017/s002211208600109x | 기울어진 Hele-Shaw의 기포 모양·상승 속도, 이론은 α → 0·큰 기포에서만 맞음 | 6 | C+A |
| B17 | Kreutzer et al. (2005) | AIChE J 51(9):2428-2440 | 10.1002/aic.10495 | Taylor 흐름 ΔP = 슬러그 마찰 + 계면 항, 관성 보정 | 2, 10 | C |
| B18 | Balestra, Zhu, Gallaire (2018) Viscous Taylor droplets in axisymmetric and planar tubes | Microfluid Nanofluid 22(6):67 | 10.1007/s10404-018-2084-y | 평면 관 액적의 ΔP, Bretherton 막 결과를 고친 경험 계수(Scholar 스니펫) | 10 | C |
| B19 | Huisman, Ern, Roig (2012) Interaction and coalescence of large bubbles rising in a thin gap | PRE 85(2):027302 | 10.1103/physreve.85.027302 | 얇은 갭에서 뒤 기포가 앞 기포 후류로 가속해 따라잡고 합체(arXiv 초록) | 4, 12 | C+A |
| B20 | Bouche, Roig, Risso, Billet (2012) Homogeneous swarm of high-Reynolds-number bubbles rising within a thin gap. Part 1 | JFM 704:211-231 | 10.1017/jfm.2012.233 | 얇은 갭 기포 무리 | 4 | C |
| B21 | Cheng L et al. (2023) An experimental study on interfacial parameters in a narrow rectangular channel under different flow regimes | PNE 159:104644 | 10.1016/j.pnucene.2023.104644 | 수직 65 × 2 mm, 고속 영상(겹치지 않는 기포 이용)으로 기공률·IAC·기포 수 밀도, 42조건, "IATE 검증용 자료". 원천항 직접 평가는 초록에 없음 | 12 | C+A |
| B22 | Shen, Hibiki, Ono, Sato, Mishima (2012) | IJHFF 36:72-82 | 10.1016/j.ijheatfluidflow.2012.04.007 | 좁은 직사각 채널 1차원 IATE | 12 | C |
| B23 | Sun, Kim, Ishii, Beus (2004) Modeling of bubble coalescence and disintegration in confined upward two-phase flow | NED 230(1-3):3-26 | 10.1016/j.nucengdes.2003.10.008 | 갇힌 유로 2군 IATE의 합체·분열 모델 | 12 | C |
| B24 | Khandelwal, Tsoukalas, Zhao, Ishii (2026) Two Phase Flows in Narrow Rectangular Channels | Nucl Technol (온라인) | 10.1080/00295450.2026.2619821 | Ishii 그룹 최신 연구(내용 미확인) | 12 | C |
| B25 | Zhang H, Hibiki (2026) Single bubble rising behavior in narrow rectangular channels with finite channel width | Phys Fluids 38(8):083342 | 10.1063/5.0342482 | 단일 기포 상승 속도·모양 상관식, Sauter 직경 → 두께의 3배 | 6 | C+A |
| B26 | Shen, Yamamoto, Nakajima, Hibiki (2024) | IJTS 202:109086 | 10.1016/j.ijthermalsci.2024.109086 | 좁은 직사각 채널 전 범위 드리프트 플럭스(채널 평균) | 6 | C |
| B27 | Agostini, Revellin, Thome (2008) Part I; Revellin, Agostini, Thome (2008) Part II | IJMF 34(6):590-601; 602-613 | 10.1016/j.ijmultiphaseflow.2007.07.007; .006 | 미세유로 긴 기포 속도 모델, 기포 충돌(합체) 모델 | 4, 6, 12 | C |
| B28 | Feng, Zhong, Lei, Jia (2024) | CSITE 54:104016 | 10.1016/j.csite.2024.104016 | 영상으로 잰 기포 빈도·속도를 3구역 모델과 비교(1 mm 미세채널, SSRN판 스니펫) | 8 | C |
| B29 | Shiferaw, Karayiannis, Kenning (2009) | IJTS 48(2):331-341 | 10.1016/j.ijthermalsci.2008.02.009 | 3구역 모델의 기포 빈도 등 3개 매개변수를 맞춤(스니펫) | 8 | C |
| B30 | Thome, Dupont, Jacobi (2004); Magnini, Thome (2017) | IJHMT 47:3375-3385; IJMF 91:296-314 | 10.1016/j.ijheatmasstransfer.2004.01.006; 10.1016/j.ijmultiphaseflow.2017.01.015 | 3구역 모델과 개정판 | 8 | C |
| B31 | Harirchian, Garimella (2009; 2010; 2012) | IJMF 35:904; IJHMT 53:2694; IJHMT 55:1246 | 10.1016/j.ijmultiphaseflow.2009.06.005 등 | 단면적의 결정적 역할, 정량 천이 기준 유동 양식 지도, 유동 양식 기반 h·ΔP 모델 | 1, 8 | C |
| B32 | Kew, Cornwell (1997) | ATE 17(8-10):705-715 | 10.1016/s1359-4311(96)00071-3 | 갇힘 수 Co | 1 | C |
| B33 | Kingston, Weibel, Garimella (2018) Part 1 | IJMF 106:179-188 | 10.1016/j.ijmultiphaseflow.2018.05.007 | 단일 500 µm 유리 미세유로, 고속 영상 + 고주파 압력·온도 동기, 급성장 불안정의 과열·압력 스파이크 정량(검색 요약) | 9 | C |
| B34 | Barber, Brutin, Sefiane, Tadrist (2010); Brutin, Topin, Tadrist (2003) | ETFS 34:1375; IJHMT 46:2957 | 10.1016/j.expthermflusci.2010.06.011; 10.1016/s0017-9310(03)00093-0 | 높은 종횡비 미세유로의 기포 갇힘과 압력 변동, 미니채널 비정상 비등 | 9 | C |
| B35 | Chalgeri, Jeong (2019) Flow regime identification … void fraction and differential pressure | IJHMT 132:802-816 | 10.1016/j.ijheatmasstransfer.2018.12.015 | 좁은 직사각 채널, 기공률·차압 신호로 유동 양식 분류 | 9 | C |
| B36 | Park, Addad, Jo (2026) | Ann Nucl Energy 228:112039 | 10.1016/j.anucene.2025.112039 | 좁은 직사각 채널, 게이지 압력 의사 음향 분석(PSD)으로 유동 양식 검출(스니펫) | 9 | C |
| B37 | Maduabuchi, Jossou, Bucci (2024) MSEG-VCUQ | arXiv:2411.07463 | - | 비등 영상 분할 + 화소 단위 UQ(건조 면적 비율, 접촉선 밀도) | 3, 13 | U |
| B38 | Seong et al. (2023); Kim, Park (2021); Dunlap et al. (2024) | IJMF 159:104336; Sci Rep 11:8940; J Appl Phys 136:014902 | 표 참고 | U-Net + 광류 기포 분석, 범용 기포 마스크, Mask R-CNN + SORT(BubbleID) | 13 | C |
| B39 | Sciacchitano (2019) Uncertainty quantification in PIV | MST 30(9):092001 | 10.1088/1361-6501/ab1db8 | PIV 불확도 정량 리뷰 | 13 | C |
| B40 | Ghajar, Tang (2010); Walsh, Walsh, Muzychka (2010); Betz, Attinger (2010) | HTE 31:711; IJHMT 53:3193; IJHMT 53:3683 | 표 참고 | 비비등 이상류 h((1−α) 인자), 슬러그 흐름 열전달 모델, 분절 흐름의 열전달·펌프 동력 | 5, 8 | C |

### 1-4. 학술지와 논문 구성의 본보기 (Q3)
| 논문 | 학술지 | 구성(그림 순서) | 주장 방식 | 확인 수준 |
|---|---|---|---|---|
| Shinmoto 2017 (A1) | Front. Mech. Eng. | 그림 15장: 동기·지도 → 장치·시험부 사진 → 상태도 → 에너지 균형 검증 → 열 분담 → 온도 분포 → H = 1 mm에서 유체별 Tw–q, h–q, 영상(그림 8~11) → 갭별 Tw–q, h–q(그림 12~14) → 갭 효과 요약(그림 15) | 갭마다 같은 형식의 그림을 반복하고 마지막에 요약 그림 한 장 | C+F |
| Cardoso 2011 (A13) | ETFS | 장치·갇힘 요소(그림 1~2) → 갭별 Bond 수 표 → 갭별 부분 비등 곡선(그림 3~6) → 갭별 영상(그림 7~8) → Bond 수에 대한 건조 열유속(그림 9) | 무차원수 표 → 곡선 → 영상 → 무차원수 요약 | C+F(부분) |
| Alam 2012 (A2) | IJHMT | 초록의 결과 순서: 갭별 갇힘 영상 → ΔP·변동 → 벽 온도·변동 → h → 최적 갭 범위 | "영상으로 본 갇힘 전이가 ΔP·Tw·h의 갭 의존을 설명" | C+A |
| Zhu 2023 (A8) | IJHMT | 초록 순서: 유동 양식 순서 → ΔP 세 영역과 갭별 최댓값 → h의 갭 효과 → CHF → 상관식 평가 + 새 ΔP 상관식 | 갭별 표준 측정 + 상관식 비교 | C+A |
| Albahloul & Hollingsworth 2015 (A6) | IJHMT | 초록 순서: 크기별 모양 → 속도비 척도 → 증진 기구 → 증기 기포 자료와 합친 상관식 | 영상 운동학 → 물리 기구 → 모델 | C+A |
| Huang 2024 (B1) | IJMF | 초록 순서: ML 비전 특징 추출 → 기공률을 해석 모델로 검증 → 기공률·젖음 면적으로 h 상관식 개선 | 데이터 기반 특징 → 상관식 | C+A |
| Liu A 2022 (A18) | ChERD | 초록 순서: 슬러그 속도·길이·액막 → ΔP 상관식 평가 | 영상 길이 척도 → ΔP | C+A |

- 학술지 맞춤(제안)
  - 단열 논문(주장 10 + 6 + 13): **IJMF**(물리 + 모델 + 실험). 0.3·0.7 mm의 Hele-Shaw 물리만 떼면 Phys Fluids·PRF도 후보.
  - 가열 논문(주장 11 + 3 + 13): **IJHMT**(갭 효과 + 모델, A2·A8·A6과 같은 학술지) 또는 ETFS(실험 중심).
  - 방법(검출·추적 QC + 사람 감사 + 오차 전파): Exp Fluids 또는 MST(B39가 MST).
- 학위논문 범위(제안): 석사 = 단열 논문 1편(0.3·0.7·1 mm, 주장 10). 박사 = 단열 + 가열 2편 + 방법 1편. Albahloul 2014(A7, 박사 1편 = 갭 1개·공기 주입·열전달 모델)가 범위의 참고가 된다.
- 위 구성 중 원문으로 확인한 것은 Shinmoto 2017과 Cardoso 2011뿐이다. 나머지는 초록의 결과 순서다.

### 1-5. 최근 리뷰 (Q4)
| 리뷰 | 학술지 권:쪽 | DOI | 범위 | 확인 수준 |
|---|---|---|---|---|
| Han, Fedorov, Joshi (2016) Flow boiling in microgaps for thermal management of high heat flux microsystems | J Electron Packag 138(4):040801 | 10.1115/1.4034317 | 평면·표면 강화 마이크로갭 흐름 비등 실험 리뷰 + 200 µm 핀 마이크로갭 결과 | C+A |
| Balasubramanian, Peter, Krishnan (2022) Recent hypotheses on the parameters of microchannel flow boiling: a comprehensive overview | Microfluid Nanofluid 26(10):80 | 10.1007/s10404-022-02587-3 | 미세유로 흐름 비등, 마이크로갭 절 포함(스니펫) | C |
| Cheng, Xia (2017) Fundamental issues, mechanisms and models of flow boiling heat transfer in microscale channels | IJHMT 108:97-127 | 10.1016/j.ijheatmasstransfer.2016.12.003 | 미세 규모 흐름 비등 기구·모델 | C |
| Karayiannis, Mahmoud (2017) Flow boiling in microchannels: fundamentals and applications | ATE 115:1372-1397 | 10.1016/j.applthermaleng.2016.08.063 | 미세유로 흐름 비등 | C |
| Kadam, Hassan, Kumar, Rahman (2021) Bubble dynamics in microchannel: an overview of the state-of-the-art | Meccanica 56(3):481-513 | 10.1007/s11012-020-01300-4 | 미세유로 기포 동역학 | C |
| Liu, Zhao, Chong (2025) Review of flow regime transition criteria for adiabatic co-current upward gas-liquid flow in vertical multi-scale channels | Measurement: Energy 8:100066 | 10.1016/j.meaene.2025.100066 | 여러 규모 채널(좁은 직사각 포함) 천이 기준 | C |
| Okumura (2018) Viscous dynamics of drops and bubbles in Hele-Shaw cells | Adv Colloid Interface Sci 255:64-75 | 10.1016/j.cis.2017.07.021 | Hele-Shaw 액적·기포 마찰·합체 | C |
| Sciacchitano (2019) Uncertainty quantification in PIV | MST 30(9):092001 | 10.1088/1361-6501/ab1db8 | 영상 계측 불확도 | C |

- 2018년 이후 **좁은 직사각 채널(수 mm) 이상류만** 다룬 리뷰는 찾지 못했다(Scholar 188건 1쪽, WebSearch 1회). 영상·ML 리뷰는 주제 5가 맡는다.

## 2. 핵심 질문에 대한 답

### Q1. 가장 가까운 연구
- 조건 다섯 개(수평·한쪽 아래 가열·서브 mm~7 mm 다중 갭·ΔP + h + 위에서 본 영상 정량)를 모두 갖춘 연구는 없다(4장 검색 기록).
- 가장 가까운 5편과 같은 점·다른 점
  1. **Shinmoto 2017 (A1, C+F)**: 같음 = 수평, 아래 금속 블록 가열 + 매립 열전대 1차원 외삽, 가열 구간 ΔP, 위 유리 너머로 가열면 촬영, 갭 비교(2/1/0.5 mm), Tw·h·CHF. 다름 = 영상은 정성, 갭 0.5~2 mm뿐(3·7 mm 없음, 모두 Co > 1), 비등(FC72·물·비혼합 혼합)만, 공기 주입 없음. → **사용자 장치의 가장 가까운 선례로 반드시 인용**하고, "정량 영상·추적 + 넓은 갭 범위"로 차별화한다.
  2. **Alam 2012 (A2, C+A)**: 같음 = 한 장치 갭 10개, 물, ΔP + Tw + h + 고속 영상, 갇힘 전이로 갭 효과 설명. 다름 = 80~1000 µm(모두 Co > 2.5), 영상 정성, 공기-물 없음.
  3. **Lee & Lee 2001a,b + KSME 2001 (A3~A5, C/U)**: 같음 = 수평, 0.4~4 mm(우리 0.3~3 mm와 겹침), 공기-물 ΔP와 R113 비등 h·ΔP. 다름 = 영상 지표 없음, 7 mm 없음, 경험 상관식(C가 갭의 함수).
  4. **Albahloul & Hollingsworth 2015 + 2014 (A6~A7, C+A/U)**: 같음 = 수평 좁은 채널, 공기 주입, 평면 영상(모양·속도비), 액정 열화상, 영상 운동학 → 열전달 기구·모델. 다름 = 갭 1개(1.3~1.5 mm), **위 벽 가열**(기포가 가열면에 붙음), ΔP 없음, Novec 649.
  5. **Zhu 2023 (A8, C+A)**: 같음 = 물, 다중 갭(0.5/1/2 mm), 영상 + ΔP + h + CHF. 다름 = 범위 0.6자릿수, 방향·가열면 미확인, 정량 영상 지표 없음.
- 그다음: 사용자의 0.3·0.7 mm 단열 자료에는 **Xu 1999(A9)**가, 3~7 mm 자유 쪽에는 **Kim YH 2005(A11)**와 **He 2022(A23)**가 가깝다.
- 지역별
  - 한국: Lee & Lee(KAIST, A3~A5), Lee·Chae·Chang 2013(KAIST, A15), Chalgeri & Jeong 2019(부산대, B35), Park·Addad·Jo 2026(경북대, B36).
  - 일본: 오타·신모토(규슈대, A1, A12, Shinmoto 2007 2·5 mm CHF), 아사노(고베대, A25, Asano 2009 2·4 mm), 우타카(요코하마국립대, A20).
  - 중국: 대부분 갭 하나(수직·한쪽 가열 원자력 채널). 다중 갭은 He 2022(A23, 4~10 mm)와 Zhu 2023(A8). 수평은 Zhang K 2021(A22)과 Liu A 2022(A18).

### Q2. 가설별 새로움 → 3장 표

### Q3. 학술지와 구성 → 1-4표
- 구성의 공통 형식: (1) 장치와 무차원수 표(갭별 Co·Bo) → (2) 갭마다 같은 형식의 그림 반복 → (3) 무차원수에 대한 요약 그림 한 장 → (4) 모델·상관식 비교.
- 우리 논문은 (3)을 "갭 다섯 개가 한 곡선에 모이는가(또는 어디서 갈라지는가)"로 만들면 A1·A2·A13보다 한 단계 정량적이다.

### Q4. 리뷰 → 1-5표

### Q5 (추가). Huang 2024류가 이미 있으면 무엇을 해야 하나
- Huang 2024(B1)와 Chang 2023(B2)은 같은 그룹이고, 미세중력 흐름 비등에서 "영상 특징 → 상관식/모델 개선"을 했다. 초록에는 형상(갭) 변화, 보지 못한 조건으로의 일반화, 비전 측정 불확도 전파가 언급되지 않는다(본문은 확인 못 함).
- 그래서 우리는 다음 네 가지로 차별화한다.
  1. **맞춤 없는 폐합(주장 10)**: 영상(운동학)과 압력계(동역학)라는 서로 다른 측정이 같은 계수를 가리키는지 시험한다. 상관식 맞춤이 아니라 반증 가능한 예측이다.
  2. **기하가 정하는 영상 변수와 갭 일반화(주장 11)**: φ_c는 H, Lc, 2Lc에서 미리 정해진다(7 mm에서 0). 갭 하나를 빼고 맞춘 모델로 남은 갭을 예측한다. Huang의 회귀 특징(기공률 등)과 같은 자료에서 일반화 성능을 비교해 보인다.
  3. **오차 전파(주장 13)**: 자동 QC + 사람 표본 감사로 잰 검출·추적 오차를 계수까지 전파한다.
  4. **한 장치에서 Co 9.1→0.39(1-2표)**: 강제 흐름에서 Co = 1과 2Lc를 함께 넘는 다중 갭 자료는 찾지 못했다.
- 논문에서는 Huang 2024·Chang 2023을 "데이터 기반 특징" 선례로 분명히 인용하고, 우리 주장을 그 다음 단계(물리 제약 + 형상 일반화 + 불확도)로 놓는다.

## 3. 아이디어와 시사점

### 3-1. 가설별 새로움 판정표 (H1~H9 + 추가 후보 10~13)
"Huang류" = Huang 2024(B1)·Chang 2023(B2). "범위 효과" = 갭을 0.3~7 mm로 넓힌 효과.

| # | 가설 | 가장 가까운 선행 연구 | 차이 | Huang류와의 차이 | 새로움 | 범위 효과 | 근거(검색어·결과 수) |
|---|---|---|---|---|---|---|---|
| H1 | 갇힘 틀 + "갇힌 기체 면적 비율" 지표 | Alam 2012(A2), Harirchian & Garimella 2009·2010(B31), Kew & Cornwell 1997(B32), Bonjour 1998(A24)·Cardoso 2011(A13)의 Bond 수 지도, Albahloul 2015(A6, d ≥ 1.5H이면 가로지름) | 선례는 채널 단위 분류(Co, Bo)나 정성 영상. 운전점마다 연속 지표를 재서 갭 사이 변수로 쓴 예와, 수평에서 2Lc 경계를 쓴 예는 못 찾음 | Huang류는 한 장치 회귀 특징. 우리 지표는 기하로 미리 정해짐 | 틀: **낮음**, 지표: **중** | Co 9.1→0.39로 강한 갇힘~자유를 한 장치에서 덮음(1-2표) → 틀의 설득력이 크게 오름. 0.3·0.7 mm에서는 거의 모든 기포가 팬케이크라 지표 ≈ 투영 기공률(정보는 1~7 mm에서 나옴) | WebSearch "fraction of confined bubbles measured by image processing narrow gap…" 10건 중 해당 0. Scholar "gap height … image processing … void fraction … pressure drop … heat transfer"(2015~) 13건 중 해당 0 |
| H2 | ΔP 메니스커스 항 = c·σCa^(2/3)·Γ/H | Fuerstman 2007(B5), Vanapalli 2009(B6), Cantat 2004·2013(B9), Raufaste 2009(B10), Kreutzer 2005(B17), Liu A 2022(A18), Ide & Fukano 2005(A19, Ca 포함 상관식) | 개념(기포 수·메니스커스 길이 × 마찰)은 미세유체·폼에 있음. 영상으로 잰 Γ로 기체-액체 mm 갭 흐름의 ΔP 증가분을 나눈 예는 못 찾음 | Huang류는 ΔP를 다루지 않음(초록) | **중~높음** | 0.3·0.7 mm에서 항이 크고(∝ 1/H) Re가 낮아 Hele-Shaw 가정에 가장 가까움. 7 mm는 항이 0인 대조군 → 검증력이 커짐 | Scholar `"pressure drop" bubbles "Hele-Shaw" "Bretherton" "perimeter" gas-liquid channel` 16건, 기체-액체 다기포 둘레 공식 0 |
| H3 | 가열면을 덮는 기포/액막 비율 → h | Albahloul 2014·2015(A6~A7, 위 벽 가열), Hollingsworth 2009, Kharangate 2015(A21, 위/아래 가열), Shinmoto 2017(A1), Cardoso 2011(A13), Huang 2024(B1, 젖음 전선 면적), MSEG-VCUQ(B37) | 아래 가열에서 접촉 비율이 갭에 따라 1 → 일부 → 0으로 바뀌는 축을 정량화한 예는 못 찾음 | Huang류는 젖은 면적을 직접 봄(미세중력). 우리는 위에서 보므로 접촉을 기하로 추정 → 차이는 "중력이 정하는 접촉"과 "갭 일반화" | **중** | 0.3·0.7·1 mm는 φ_c ≈ α_p(모두 접촉), 3 mm 일부, 7 mm 0 → 축의 양 끝이 생김 | WebSearch "heated wall contact area fraction bubbles image horizontal channel bottom heated…" 10건 중 해당 0 |
| H4 | 합체·분열 빈도, 크기별 드리프트 플럭스 | Booth 2025(B12), Huisman 2012(B19), Revellin 2008(B27), Cheng 2023(B21), Shen 2012(B22), Sun 2004(B23), Shen 2024(B26, 채널 평균) | 다수 기포 흐름에서 추적으로 크기별 사건 빈도를 센 예는 못 찾음 | Huang류에 사건 통계 없음(초록) | **중**(12로 구체화하면 중~높음) | 0.3·0.7 mm는 팬케이크 추월 합체(B12 영역), 7 mm는 3차원 기포 → 기구가 바뀌는 것을 한 장치에서 봄 | WebSearch "bubble coalescence frequency measured by bubble tracking … thin gap Hele-Shaw…" 9건 중 빈도 측정 0 |
| H5 | 성능 지도(h vs 펌프 동력) | Alam 2012(A2), Zhu 2023(A8), Willingham 1992(A16), Betz & Attinger 2010(B40) | 갭 최적화 자체는 흔함 | 무관 | **낮음** | 0.3 mm의 큰 ΔP(층류 6.7~133 kPa/m)로 대비는 커지지만, 펌프 동력이 열유속의 약 1% 이하라 결정적이지 않다(메인 추정) | A2·A8 초록 |
| H6 | 크기별 C0(d/H) 주곡선 | Taylor & Saffman 1959(B15), Maxworthy 1986(B16), Wu 2024(B13)·Booth 2025(B12), Monnet 2024(B14), Albahloul 2015(A6, 속도비 일정), Agostini 2008(B27), Zhang & Hibiki 2026(B25) | 저 Re 단일·두 기포 이론은 있음. 공학 유량(관성)·다수 기포·여러 갭에서 크기별 C0를 추적으로 잰 예는 못 찾음 | Huang류에 개별 기포 속도 통계 없음(초록) | **중** | 0.3·0.7 mm가 Hele-Shaw 이론의 기준점, 3·7 mm에서 관성·부력(벽 근처) 가지로 갈라짐 → "어디까지 한 곡선인가"를 시험 | Scholar `"distribution parameter" "bubble size" "narrow rectangular channel" drift-flux` 23건 중 크기별 C0 0. WebSearch(Hele-Shaw 속도) 9건 |
| H7 | 검출·추적 오차 → 물리량·계수 불확도 | = 13 | | | | | |
| H8 | 영상 빈도 → 3구역(비등) / 영상 기공률 → 액체 가속(공기) | 비등: Feng 2024(B28), Shiferaw 2009(B29), Jige 2019, Magnini & Thome 2017(B30), Harirchian & Garimella 2012(B31). 공기: Albahloul 2015(A6, 막힘 가속 + 후류), Ghajar & Tang 2010·Walsh 2010(B40) | 미세유로·한 갭에서는 이미 함 | **Huang류와 가장 많이 겹침**(기공률로 h 상관식 개선) | **낮음~중** | 0.3·0.7 mm 비등은 3구역 모델의 적용 영역에 들어감 → 적용성은 오르나 새로움은 그대로 | Scholar `"three-zone model" "bubble frequency" "high-speed" measured…` 30건 중 측정 빈도 사용 1~2건. WebSearch(공기 주입 열전달) 9건 |
| H9 | 압력 변동 스펙트럼 ↔ 영상 통과 빈도 | Kingston 2018(B33), Barber 2010·Brutin 2003(B34), Chalgeri & Jeong 2019(B35), Park 2026(B36), Ide & Fukano 2005(A19, 액괴 통과 빈도) | 단일 유로 동기 측정은 있음. 갭별 비교는 못 찾음 | 무관 | **낮음~중** | 0.3·0.7 mm는 기포 하나의 압력 펄스가 커서 잘 보이고, 7 mm는 ΔP가 작아 못 볼 수 있음 | Scholar `"pressure fluctuation" "narrow rectangular channel" "high-speed" "frequency" bubbles PSD` 6건, 해당 0 |
| **10** | **운동학–동역학 폐합**: 추적한 크기별 C0로 메니스커스 마찰 계수 c를 정하고, 그 c로 ΔP 증가분을 맞춤 없이 예측해 측정 ΔP − 액체 마찰과 비교 | Labrot 2009(B7)·Sessoms 2009(B8)(관측 액적 거동 → 저항), Vanapalli 2009(B6), Fuerstman 2007(B5), Raufaste 2025(B11, 영상 곡률 ↔ 판 마찰), Wu 2024·Booth 2025(B12~13, 속도 ↔ Bretherton 이론), Kreutzer 2005(B17) | 기체-액체 mm 갭 흐름에서 "속도로 정한 계수 → ΔP 예측 → 독립 측정과 비교"를 한 예는 못 찾음. 단, "관측 운동학에서 저항을 추정"하는 개념은 미세유체·폼에 있음 | Huang류는 영상 특징을 상관식에 넣어 맞춤. 우리는 두 독립 측정의 일관성을 시험(반증 가능) | **중~높음**("mm 갭 기체-액체·관성·다중 갭·ΔP 독립 검증"으로 한정하면 높음) | 0.3·0.7 mm(저 Re, 강한 갇힘)가 가장 깨끗한 검증 무대, 1·3 mm에서 관성 보정 시험, 7 mm는 항이 0인 대조군 | Scholar `"bubble velocity" "pressure drop" "Hele-Shaw" OR "flat channel" OR "narrow channel" friction … "Bretherton"` 34건, 명시적 역추정 0(가장 가까운 것: Hele-Shaw 폼 학위논문, 평면 액적 B18). Europe PMC 초록 4편 |
| **11** | **φ_c(가열면 접촉 기체 비율) + 갭 하나 빼기 검증** | Huang 2024(B1), Chang 2023(B2), Zhou 2020(B4, 보지 못한 자료 시험), Albahloul 2015(A6, 물리 변수), Kharangate 2015(A21) | 기하에서 미리 정해지는 영상 변수로 갭을 빼고 예측한 예는 못 찾음 | Huang류는 한 장치 회귀 특징. 우리는 물리 변수 + 형상 밖 예측 | **중~높음** | 다섯 갭이라 "넷으로 맞추고 하나 예측"이 가능하고 φ_c가 0~α_p를 모두 덮음 | WebSearch "two-phase heat transfer correlation generalization unseen channel size leave-one-out…" 9건 중 해당 0 |
| **12** | **추적 합체·분열률 → 좁은 유로 IATE 원천항 검증** | Cheng 2023(B21, 영상 IAC·BND), Shen 2012(B22), Sun 2004(B23), Khandelwal 2026(B24), Huisman 2012(B19), Booth 2025(B12) | 사건을 추적으로 직접 세어 원천항(빈도 커널)을 검증한 예는 못 찾음 | 무관(Huang류에 없음) | **중~높음**(위험 큼) | 0.3·0.7 mm 팬케이크 추월, 7 mm 3차원 → 커널 형태 변화를 한 장치에서 | Scholar `"interfacial area transport" "narrow rectangular" coalescence breakup "high-speed" image tracking source terms` 14건, 사건 계수 0 |
| **13** | **검출·추적 오차를 계수까지 전파한 불확도** | MSEG-VCUQ(B37, 화소 UQ), Seong 2023·Kim & Park 2021·BubbleID(B38), Sciacchitano 2019(B39) | 사람 표본 감사 + 자동 QC → C0·Γ·φ_c·모델 계수까지 전파한 예는 못 찾음 | Huang류 초록에 비전 불확도 언급 없음(본문 미확인) | **중~높음**(방법론). 단독 논문으로는 약함 | 7 mm는 깊이 방향 겹침, 0.3 mm는 대비가 약한 얇은 기포 → 갭마다 오차가 달라 공정한 비교에 꼭 필요 | WebSearch "uncertainty propagation bubble segmentation tracking errors to void fraction… human annotation audit" 10건 중 전체 사슬 0 |

### 3-2. 추천: 신규성이 가장 높고 실현 가능한 주장
1. **1순위: 주장 10 + 13 (+ H6)** — "하나의 계면 마찰 계수가 기포 속도(영상)와 ΔP 증가분(압력계)을 함께 설명한다."
   - 왜: 맞춤이 아니라 두 독립 측정의 일관성 시험이라 Huang류와 성격이 다르다. 개념 선례(B7·B8·B11)는 미세유체·폼에 한정된다.
   - 실현성: 0.3·0.7 mm 단열 자료(ΔP, 기포 수·크기)에 추적 속도, 혼합 속도 j(유량계), 같은 채널의 액체만 ΔP 기준선을 더하면 된다. 0.3·0.7 mm는 Re가 낮아 모델 가정에 가장 가깝다.
   - 위험: 관성(Re_H·H/d > 1), 젖음 막 파열(접촉선 마찰), 기체 팽창(0.3 mm는 ΔP가 커서 길이 방향 j가 변함), 계면 오염. c를 C0에서 정하므로 오염에 따른 c 변화는 자동으로 들어간다. 그래도 두 관측이 어긋나면 그것도 결과다(어느 가정이 깨졌는지 알려 줌).
2. **2순위: 주장 11 + 13** — "갭 효과는 H/Lc·H/2Lc가 정하는 φ_c와 통과 빈도로 설명되고, 갭 하나를 빼도 예측된다."
   - 실현성: 가열 실험(갭 3개 이상) 후. 열전대 위치의 국소 φ_c가 필요하다.
3. 보조: 12는 자료가 되면 별도 장(또는 후속 논문). H1·H3는 주장이 아니라 해석의 축으로 쓴다. H5·H8·H9는 부록·논의 수준.

### 3-3. 메인 초안(`novelty_analysis.md`)과 다른 판정
| 항목 | 메인 초안 | 이 조사 | 근거 |
|---|---|---|---|
| N1(= 10) 새로움 | 높음(추정) | **중~높음**. 범위를 한정하면 높음 | 관측 운동학으로 저항·마찰을 추정한 선례가 미세유체(B7 Labrot 2009, B8 Sessoms 2009)와 폼(B11 Raufaste 2025)에 있다. 기체-액체 mm 갭 + ΔP 독립 검증은 못 찾았다(Scholar 34건) |
| G6 "중력이 정하는 접촉(미세중력에는 없음)" | 기준점에 없는 것 | 지상 선례가 있다 | Kharangate 2015(A21, 위/아래 가열), Albahloul 2014(A7, 위 벽 가열), Shinmoto 2017(A1, 아래 가열). 새로운 부분은 "접촉 비율을 갭별로 정량화한 것"이다 |
| G7 "비등이 아닌 공기 주입 + 영상" | 기준점에 없는 것 | 이미 있다 | Albahloul 2014·2015(A6~A7): 공기 주입, 평면 영상, 열전달 모델. 단 갭 1개, 위 벽 가열, ΔP 없음 |
| N4(= 12) | 조사 중 | 중~높음(위험 큼) | 사건 직접 계수 검증 0건(Scholar 14건) |
| 1장 "한 가지 형상" | 단정 | 미확인 | Huang 2024 초록에 형상 정보가 없다. 본문(Purdue PDF 503, escholarship 403)을 못 읽었다 |

### 3-4. 필요한 데이터와 실현성 메모
- 주장 10: 크기별 기포 속도(추적), j, Γ(둘레 합/면적), ΔP, 액체만 ΔP. 프레임당 이동이 이웃 간격의 1/3 이하가 되는 fps. 연결 감사 크기별 100건.
- 주장 11: 갭 3개 이상의 가열 자료, 열전대 위치의 국소 영상 창, 단상 기준 h.
- 주장 12: 합체·분열 판정의 정확도(감사로 확인), 높은 fps.
- 주장 13: QC 보고서, `4_link_audit.py` 판정, 경계 ±1 px 섭동, 부트스트랩.

## 4. 새로움 판단 기록 (검색어와 결과 수)
- **인용 추적(Semantic Scholar citations API, 키 없음)**: 고전 10편(Mishima 1993, Lee & Lee 2001a·b, Wilmarth 1994, Kim YH 2005, Hibiki 2001, Moriyama 1996, Alam 2012, Bar-Cohen & Rahim 2009, Geisler 2009) → 1453건, 중복 제거 1147건, 2015년 이후 523건. 제목 키워드·공동 인용으로 순위를 매겨 상위 160건을 검토했다. 다섯 조건을 모두 갖춘 것은 0건이었다.
- **Google Scholar(WebFetch, 12회, CAPTCHA 없음)**
  1. `"slug flow in horizontal narrow rectangular channel"` → 15건(Liu 2022, 인용 30).
  2. `"rectangular channel" "gap" horizontal "heated from below" OR … "gap height"`(2015~) → 0건(조건 과다).
  3. `"pressure drop" bubbles "Hele-Shaw" "Bretherton" "perimeter" gas-liquid channel` → 16건, 기체-액체 다기포 둘레 공식 0.
  4. `"distribution parameter" "bubble size" "narrow rectangular channel" drift-flux` → 23건, 크기별 C0 0.
  5. `"three-zone model" "bubble frequency" "high-speed" measured "heat transfer coefficient" boiling channel` → 30건, 측정 빈도 사용 1~2건(B28).
  6. `"pressure fluctuation" "narrow rectangular channel" "high-speed" "frequency" bubbles "power spectral density"` → 6건, 갭별 비교 0.
  7. `review "narrow rectangular channel(s)" two-phase flow boiling heat transfer`(2018~) → 약 188건, 1쪽에 좁은 직사각 전용 리뷰 0.
  8. `microgap OR "micro-gap" flow boiling review OR "state-of-the-art" OR overview`(2018~) → 약 442건, 리뷰 3건(1-5표).
  9. `"Friction-induced bubble edge curvature"` → 1건(B11).
  10. `"bubble velocity" "pressure drop" "Hele-Shaw" OR "flat channel" OR "narrow channel" friction coefficient inferred OR predicted "gas-liquid" "Bretherton"` → 34건, 명시적 역추정 0.
  11. `"interfacial area transport" "narrow rectangular" coalescence breakup "high-speed" image tracking source terms` → 14건, 사건 계수 0.
  12. `"gap height" OR "gap size" "image processing" OR "image analysis" "void fraction" "pressure drop" "heat transfer" microgap OR minigap OR "narrow gap"`(2015~) → 13건, 세 조건 동시 0.
- **WebSearch(standard)**: 수평·아래 가열·다중 갭(3회, 해당 0), Piasecka 그룹(갭 하나씩), minigap 0.5/1/2 mm(그단스크 1/2/3 mm 발견), 공기-물 좁은 채널 열전달(해당 0), "effect of gap size" 좁은 채널(Shinmoto 2017 발견), 갇힌 기포 비율(0), 가열면 접촉 비율(0, Albahloul 학위논문 발견), 오차 전파(0), 공기 주입 열전달(0), Hele-Shaw 속도(이론만), 합체 추적(0), 갭 일반화(0), 한국어(Lee & Lee 계열), 중국어(갭 하나 위주), Huang 2024 계열(같은 그룹 BubbleMask·VISION-iT).
- **J-STAGE**: `narrow gap flow boiling gap size visualization heat transfer` → 첫 쪽 20건 중 관련 14건(오타·신모토, 아사노, Fujita 등).
- **Crossref**: 모든 DOI 대조(73건 이상). KSME B 2001(KISTI DOI)은 Crossref에 없어 U.
- **초록 출처**: CoLab 미러(Elsevier 초록), Europe PMC(Lab Chip·PRE·Biomicrofluidics), HAL API(B11), arXiv API(B14, B19, B37), KoreaScience(A5).
- **막힌 곳**: ScienceDirect·MDPI(403), Purdue Mudawar PDF(503), Purdue e-Pubs·UAH·escholarship 본문(403), KAIST 저장소(연결 끊김), 그단스크 저장소(DNS). OpenAlex는 429라 쓰지 않았다.

## 5. 남은 의문과 사용자에게 확인할 것
- **사용자 확인**
  1. 0.3·0.7 mm 단열 실험: 채널 방향(수평?), 공기 주입 방식(점·다공판), 유량 범위, ΔP 탭 위치, 프레임률(개별 기포 속도가 나오는가), 채널 바닥이 철인지 투명인지. → 주장 10의 실현성을 정한다.
  2. 가열 실험이 공기 주입인지 비등인지. → H3·H8·주장 11의 모델이 갈린다.
  3. 열전대 위치와 영상 창의 관계(국소 φ_c를 짝지을 수 있는가).
  4. 같은 채널에서 액체만 흘린 ΔP 자료가 있는가(유효 갭 보정과 주장 10의 기준선).
- **확인하지 못한 것**
  - Huang 2024 본문(상관식 형태, 정확도, 형상 일반화 여부, 비전 불확도 처리).
  - Shinmoto 2017의 결론부(본문 뒤 28k자). ΔP·매립 열전대·정성 영상은 확인했다.
  - 갭 값: Geisler & Bar-Cohen 2009, Ishibashi & Nishikawa 1969, Satitchaicharoen & Wongwises 2004(IJMF 30:225), Mishima 1993 원문 값(1.07/2.45/5.0 여부).
  - Willingham & Mudawar 1992 본문, Gasanov 2026(J Eng Thermophys 35:175, 갭 효과 과냉 비등)과 Khandelwal 2026의 내용.
  - Zhu 2023의 채널 방향·가열면·시야.

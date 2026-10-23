# 주제 1: 좁은 직사각 유로·얇은 갭의 단열 기액 이상류 (갭 0.3~10 mm)

- 작성: 2026-10-23, 문헌 조사 에이전트 1. 범위는 갭 H = 0.3, 0.7, 1, 3, 7 mm(2026-10-23 범위 변경 반영).
- 확인 수준: `C+F` Crossref + 전문, `C+A` Crossref + 초록, `C` Crossref만(내용은 2차 자료·검색 요약), `U` 미대조. 공통 지침 4장을 따른다.
- 초록 출처가 Crossref가 아닐 때는 괄호에 적었다(CityU·HKUST 연구 포털, HAL, OSTI, Semantic Scholar, EPFL infoscience).
- 물성·무차원수는 직접 계산(20 °C 물-공기, σ = 0.072 N/m, Lc = √(σ/ρg) ≈ 2.7 mm). 주 세션의 `estimates_microgap.md`와 같은 값을 쓴다.

| H (mm) | 0.3 | 0.7 | 1 | 3 | 7 |
|---|---|---|---|---|---|
| Co = Lc/H | 9.1 | 3.9 | 2.7 | 0.9 | 0.39 |
| Co(D_h = 2H 기준) | 4.5 | 1.9 | 1.36 | 0.45 | 0.19 |
| Bo_H = (H/Lc)² | 0.012 | 0.067 | 0.14 | 1.2 | 6.7 |
| Re_H = ρUH/μ (U = 0.1 m/s) | 30 | 70 | 100 | 300 | 700 |
| Re_H·H/d (d/H = 10, U = 0.1 m/s) | 3 | 7 | 10 | 30 | 70 |

## 0. 요약
1. 갭을 바꾼 단열 실험의 직접 선례는 수직 채널에 몰려 있다. Mishima 외(1993, 약 1/2.4/5 mm)[A1], Xu 외(1999, 0.3/0.6/1.0 mm)[A2], Sadatomi·Ali·Kawaji(1992/93, 0.78/1.47 mm, 6방향)[A5, A6]가 핵심이다. 수평 좁은 갭은 Wilmarth & Ishii(1994, 1·2 mm)[A4], Lee & Lee(2001, 0.4~4 mm)[A7], Wambsganss 외(1991/92, 3.18 mm)[A8]가 거의 전부다.
2. 0.3 mm에서는 양식이 바뀐다. Xu 외는 0.3 mm에서 기포류가 전혀 없고, 벽에 붙은 액적을 기체가 미는 양식(cap-bubbly, slug-droplet, annular-droplet)을 봤다(초록 기준)[A2]. 0.6~1.0 mm는 큰 채널과 같은 4양식이다.
3. 1.5 mm 이하에서는 방향(수직·수평판 수평류) 영향이 작다. 수직판 사이 수평류만 다르다(원문)[A5]. 그래서 0.3~1 mm 수평 실험은 수직 문헌과 바로 비교할 수 있다. 3·7 mm 수평은 그렇지 않다.
4. 드리프트 플럭스의 "직사각 C0 = 1.35"는 Ishii(1977)가 가로세로비 2.8~9.4의 비등 자료로 정한 값이다(원문)[C1, C2]. Mishima 외(1993)는 기공률로는 C0 ≈ 1.35, 슬러그 기포 속도로는 1.0~1.2를 얻었다(초록 기준)[A1] — 이전 메모의 "1.35 대 1.0~1.2" 충돌은 측정 대상이 다른 것이었다. 최신 상관식은 C∞를 가로세로비로 나누거나(1.35/1.20)[C3], 갭·폭을 넣는다[C4]. 크기별로는 작은 기포 C∞ = 1.00, 큰 기포 1.45라는 2군 결과가 있다(초록 기준)[C5].
5. 압력 구동 Hele-Shaw의 팬케이크 기포 속도는 Taylor–Saffman의 2배가 상한이다. 실제로는 막·메니스커스 소산 때문에 작은 기포일수록, Ca가 작을수록 느리다[D3~D5, D12]. Reichert 외(2019)는 계면 활성제 없는 기포에서 이동도 1.0~1.65를 쟀다(d/H ≈ 11~23, Ca = 0.5~5×10⁻³, 원문 그림)[D12]. 주 세션의 C0 모델(c = 5)은 이 값과 거의 맞는다(직접 계산, 2장 Q3).
6. 오염(계면 활성제)은 이동도를 크게 낮추고, 크기 의존의 부호까지 바꿀 수 있다[D12, D13]. 물-공기 실험에서 C0(d/H)의 절댓값은 물의 청결도에 좌우될 수 있다.
7. 수평 갭에서 부력이 기포를 위 벽으로 밀면 위·아래 막이 비대칭이 되고 속도가 준다(기울인 Hele-Shaw 실험)[D14]. 3·7 mm 수평의 "위 덮개 밑 기포"에 맞는 근거다. 다만 압력 구동 + 관성(Re_H ≫ 1) 조건의 자료는 찾지 못했다.
8. 새로움: "영상 추적으로 기포마다 잰 C0를 d/H(연속 곡선)와 갭(0.3~7 mm)에 대해 그린 연구"는 찾지 못했다(4장 기록). 가장 가까운 것은 2군 드리프트 플럭스[C5], 미세 유로 기포 이동도[D12], 점성 Hele-Shaw 채널의 "속도는 크기와 함께 단조 증가"(Juel 그룹)[G1~G3], 1 mm 갭 영상 계측[C7, F1]이다.
9. 합체·분열: 좁은 갭에서 빈도를 직접 센 단열 자료는 찾지 못했다. 쌍 실험[E7, E8, G1], 비등 합체의 정성 기술[G11], 계면 면적 수송 원천항의 간접 평가[C7, C9, G12]뿐이다. 크기별 속도 차가 따라잡기 합체를 만든다는 기구[G1, G2]는 추적 자료로 바로 검증할 수 있다.

## 1. 문헌 표
표의 "관련성"은 0.3/0.7/1/3/7 mm 연구와의 관련성이다.

### 1-A. 갭을 바꾼 단열 실험 (유동 양식·기공률·마찰)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| A1 | Mishima, Hibiki & Nishihara (1993) | Some characteristics of gas-liquid flow in narrow rectangular ducts | Int. J. Multiphase Flow 19(1):115-124 | 10.1016/0301-9322(93)90027-r | 좁은 갭·큰 가로세로비 직사각 덕트, 공기-물, 중성자 투과 영상 + 영상 처리로 기공률. 갭 약 1.0/2.4/5.0 mm·수직 상향은 2차 인용 | (초록 기준) 기공률은 기존 C0 상관식(약 1.35)의 드리프트 플럭스로 잘 맞음. 슬러그 기포 속도의 C0는 1.0~1.2. 마찰 손실은 Chisholm–Laird로 맞지만 Chisholm C가 갭이 줄면 21 → 0 | 1~5 mm 갭 비교의 가장 가까운 선례. C0·Chisholm C가 갭에 따라 바뀜 | C+A (CityU 포털 초록) |
| A2 | Xu, Cheng & Zhao (1999) | Gas–liquid two-phase flow regimes in rectangular channels with mini/micro gaps | Int. J. Multiphase Flow 25(3):411-432 | 10.1016/s0301-9322(98)00057-3 | 수직 상향 공기-물, 12 × 260 mm, 갭 0.3/0.6/1.0 mm, CCD 영상 | (초록 기준) 1.0·0.6 mm: 기포류·슬러그·처언·환상류. 갭이 줄수록 천이가 낮은 기체 유량에서 일어남. 0.3 mm: 아주 낮은 기체 유량에서도 기포류 없음. 표면장력·벽 마찰 때문에 벽에 붙은 액적을 기체가 밂 → cap-bubbly, slug-droplet, churn, annular-droplet. 천이 모델은 0.6 mm 이상만 비교, 0.3 mm 이하는 새 이론 필요 | 0.3·0.7·1 mm 양식 비교의 기준. 사용자 0.3 mm 단열 자료와 직접 비교 | C+A (HKUST 포털 초록) |
| A3 | Xu (1999) | Experimental study on gas–liquid two-phase flow regimes in rectangular channels with mini gaps | Int. J. Heat Fluid Flow 20(4):422-428 | 10.1016/s0142-727x(99)00002-8 | 미니 갭 직사각 유로(세부 미확인) | 갭이 커질수록 천이선이 높은 j_g 쪽(검색 요약 기준) | A2 보완 | C |
| A4 | Wilmarth & Ishii (1994) | Two-phase flow regimes in narrow rectangular vertical and horizontal channels | Int. J. Heat Mass Transfer 37(12):1749-1758 | 10.1016/0017-9310(94)90064-7 | 공기-물 단열, 수직·수평, 갭 1·2 mm, CCD 영상(검색 요약 기준) | 수평: 매끄러운 층상, plug, slug, 분산 기포, 파상 환상류(이전 메모, 검색 요약 기준). 후속 연구가 수직 자료와 가장 잘 맞는 지도로 평가(2차) | 수평 1 mm 갭 양식 지도의 유일한 고전. 판 방향(갭이 수직인지)은 원문 확인 필요 | C |
| A5 | Sadatomi, Ali & Kawaji (1992) | 狭い平行平板間の気液二相流に及ぼすすきま寸法と流動方向の影響 (Effects of gap width and orientation on two-phase flow in a narrow passage between two-flat plates) | Trans. JSME Ser. B 58(546):408-415 | 10.1299/kikaib.58.408 | 공기-물 단열, 폭 80 mm, 길이 240 mm, 갭 1.465·0.778 mm. 6방향: 수직 상·하향, 45° 상·하향, 수평판 사이 수평류(H-H), 수직판 사이 수평류(H-V) | (원문) H-V를 뺀 5방향은 양식·기공률·마찰이 비슷하고 갭 영향도 작음. 기공률은 Martinelli χ의 Chisholm–Laird형 식(C = 20)으로 상관. 마찰은 Beattie–Whalley 식과 분리류 모델이 가장 좋고 균질 모델은 평균 75% 과대. 단상 층류 f·Re = 95(0.778 mm), 94(1.465 mm). H-V는 질량 속도 영향이 강하고 층상-파상류가 생김 | 0.7·1 mm 수평(판 수평) 조건과 같은 기하. "1.5 mm 이하에서는 방향 영향이 작다"는 근거 | C+F (J-STAGE 원문, 일본어) |
| A6 | Ali, Sadatomi & Kawaji (1993) | Adiabatic two-phase flow in narrow channels between two flat plates | Can. J. Chem. Eng. 71(5):657-666 | 10.1002/cjce.5450710502 | A5와 같은 장치(갭 0.778·1.465 mm, 6방향) | A5와 같은 결론: 수직판 사이 수평류를 빼면 갭·방향 영향이 작고, 기공률·마찰 배수가 Martinelli χ로 상관(이전 메모, 검색 요약 기준) | A5의 영문판. 인용은 이쪽 | C |
| A7 | Lee & Lee (2001) | Pressure drop correlations for two-phase flow within horizontal rectangular channels with small heights | Int. J. Multiphase Flow 27(5):783-796 | 10.1016/s0301-9322(00)00050-1 | 수평, 공기-물, 폭 20 mm, 갭 0.4~4 mm, 305점 | Lockhart–Martinelli형, Chisholm C를 질량 유속·갭에 따라 바꿔 ±10%. X 0.303~79.4, Re_Lo 175~17,700(이전 메모, 검색 요약 기준) | 0.4~4 mm 수평. 0.7·1·3 mm 압력 강하의 기준 상관식(주제 3과 겹침) | C (Crossref 첫 저자 표기 "Ju Lee Han", 성·이름 뒤바뀜) |
| A8 | Wambsganss, Jendrzejczyk & France (1991); Wambsganss 외 (1992) | Two-phase flow patterns and transitions in a small, horizontal, rectangular channel / Frictional pressure gradients in two-phase flow in a small horizontal rectangular channel | Int. J. Multiphase Flow 17(3):327-342 / Exp. Therm. Fluid Sci. 5(1):40-56 | 10.1016/0301-9322(91)90003-l / 10.1016/0894-1777(92)90055-a | 수평, 공기-물 단열, 19.05 × 3.18 mm(판 방향은 미확인) | (ANL-90/19 보고서 초록, OSTI 7067684) 압력 신호로 plug/기포 → 슬러그 천이를 객관적으로 판정. 원관·모세관·큰 직사각 채널 지도는 정성적으로만 맞음. 기존 마찰 상관식 2개는 전 범위에서 맞지 않아 반경험식을 새로 만듦 | 3 mm 수평과 가장 가까운 기하. 차압 변동으로 양식 판정 | C+A (보고서 초록) |
| A9 | Sadatomi, Sato & Saruwatari (1982) | Two-phase flow in vertical noncircular channels | Int. J. Multiphase Flow 8(6):641-655 (일본어판 Trans. JSME B 48(434):1893-1900, 10.1299/kikaib.48.1893) | 10.1016/0301-9322(82)90068-4 | 수직 상향 공기-물. 직사각 7×50, 10×50, 17×50, 7×20.6 mm, 삼각, 환형, 원관 26 mm. 급속 차단 밸브로 기공률 | (일본어판 원문) 원관용 Smith 기공률 식이 비원형에도 맞음(j_L = 0.1 m/s 제외). 유동 양식 천이는 형상 영향이 작고, 단면적 약 200 mm² 이하에서 크기 영향이 나타남. Chisholm–Laird 마찰 식은 원관 수준 정확도 | 7 mm 갭(7×50 mm)의 수직 기준 자료. 7 mm는 원관식이 대체로 통함 | C+F (일본어판) |
| A10 | Hibiki & Mishima (2001) | Flow regime transition criteria for upward two-phase flow in vertical narrow rectangular channels | Nucl. Eng. Des. 203(2-3):117-131 | 10.1016/s0029-5493(00)00306-x | 천이 모델. 공기-물 갭 0.3~17 mm 자료, 고압 증기-물과 비교 | (초록 기준) Mishima–Ishii 원관 모델을 좁은 직사각 유로로 확장. 갭 0.3~17 mm 자료와 만족스럽게 일치, 비등에도 적용. Scholar 조각: 갭이 줄면 C0가 바뀔 수 있음 | 0.3~7 mm를 한 틀로 다룬 천이 기준(수직) | C+A (CityU 포털 초록) |
| A11 | Satitchaicharoen & Wongwises (2004) | Two-phase flow pattern maps for vertical upward gas–liquid flow in mini-gap channels | Int. J. Multiphase Flow 30(2):225-236 | 10.1016/j.ijmultiphaseflow.2003.11.006 | 수직 상향 미니 갭(세부 미확인) | 제목·Scholar 조각 수준 | 1~3 mm대 수직 양식 지도 후보 | C |
| A12 | Chalgeri & Jeong (2019a) | Flow patterns of vertically upward and downward air-water two-phase flow in a narrow rectangular channel | Int. J. Heat Mass Transfer 128:934-953 | 10.1016/j.ijheatmasstransfer.2018.09.047 | 수직 상·하향 좁은 직사각 유로(연구로 판형 연료 냉각 유로 배경) | 제목 수준 | 하향류 포함 양식 비교 | C |
| A13 | Chalgeri & Jeong (2019b) | Flow regime identification and classification based on void fraction and differential pressure of vertical two-phase flow in rectangular channel | Int. J. Heat Mass Transfer 132:802-816 | 10.1016/j.ijheatmasstransfer.2018.12.015 | 수직 직사각 유로, 기공률·차압 신호로 양식 판별 | 제목·Scholar 조각 수준 | 차압 변동 + 영상 양식 판정(주제 6과 연결) | C |
| A14 | Yuan 외 (2021) | Air-water two-phase flow regime and transition criteria in vertical upward narrow rectangular channels | Prog. Nucl. Energy 136:103750 | 10.1016/j.pnucene.2021.103750 | 수직 상향 좁은 직사각 유로, 1 mm 갭 포함(검색 요약) | 1 mm 갭에서 측벽이 합체 확률을 높임(이전 메모, 검색 요약 기준) | 1 mm 합체 빈도 해석 | C |
| A15 | Ide & Fukano (2005) | Experimental research on the correlations of holdup and frictional pressure drop in air–water two-phase flow in a capillary rectangular channel | Exp. Therm. Fluid Sci. 29(7):833-841 | 10.1016/j.expthermflusci.2005.03.010 | 납작한 모세관 직사각 유로, 공기-물(세부 미확인). 같은 그룹의 학회 발표: 수평 납작 모세관 유로(ICMM2003), 수평 납작 미세 유로(ICNMM2011) | 제목 수준 | 0.3~1 mm 수평 납작 유로의 holdup·마찰 자료 후보(원문 확인 필요) | C |
| A16 | Ide, Kariyasaki & Fukano (2007) | Fundamental data on the gas–liquid two-phase flow in minichannels | Int. J. Therm. Sci. 46(6):519-530 | 10.1016/j.ijthermalsci.2006.07.012 | 미니 채널 기초 자료(원관·직사각, 세부 미확인) | 제목 수준 | 같은 그룹의 종합 자료 | C |
| A17 | Fourar & Bories (1995) | Experimental study of air-water two-phase flow through a fracture (narrow channel) | Int. J. Multiphase Flow 21(4):621-637 | 10.1016/0301-9322(95)00005-i | 매끄러운 평행 유리판 "균열"(얇은 갭) 공기-물(세부 미확인) | 제목 수준 | 수평 Hele-Shaw형 공기-물 흐름의 지구과학 쪽 선례 | C |

### 1-B. 갇힘의 기준과 긴 기포 (모세관 길이 근처에서 바뀌는 것)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| B1 | Ong & Thome (2011) | Macro-to-microchannel transition in two-phase flow: Part 1 – Two-phase flow patterns and film thickness measurements | Exp. Therm. Fluid Sci. 35(1):37-47 | 10.1016/j.expthermflusci.2010.08.004 | R134a·R236fa·R245fa, 원관 1.03/2.20/3.04 mm, 수평 | (EPFL infoscience 초록) 대규모 슬러그/플러그 흐름으로의 천이는 Co ≈ 0.3~0.4. Co → 1이면 중력이 표면장력·전단에 완전히 눌려 막이 대칭 | 갇힘의 문턱값. H 기준이면 7 mm(0.39)는 경계, 3 mm(0.9)는 거의 대칭 | C+A |
| B2 | Kew & Cornwell (1997) | Correlations for the prediction of boiling heat transfer in small-diameter channels | Appl. Therm. Eng. 17(8-10):705-715 | 10.1016/s1359-4311(96)00071-3 | 작은 관 비등 | 갇힘 수 Co = √(σ/(gΔρ))/D_h를 쓴 원조(널리 인용). 문턱값 0.5는 이번에 원문·2차 자료로 확인 못 함 | D_h = 2H로 쓰면 Co가 반으로 줄어 3 mm가 "비갇힘"이 됨 → 길이 척도 선택이 결론을 바꿈 | C |
| B3 | Triplett 외 (1999) | Gas–liquid two-phase flow in microchannels Part I: two-phase flow patterns | Int. J. Multiphase Flow 25(3):377-394 | 10.1016/s0301-9322(98)00054-8 | 미세 유로(원관·반삼각, 약 1 mm대) 공기-물 | 제목 수준(내용 미확인) | 1 mm대 양식 지도의 표준 비교 대상 | C |
| B4 | Kawahara, Chung & Kawaji (2002) | Investigation of two-phase flow pattern, void fraction and pressure drop in a microchannel | Int. J. Multiphase Flow 28(9):1411-1435 | 10.1016/s0301-9322(02)00037-x | 100 µm대 원관(검색 요약) | 지름 > 0.1 mm에서는 기공률이 체적 건도에 거의 선형, 그 아래는 벗어남(같은 그룹 결과에 대한 리뷰 서술, 검색 요약 기준) | 0.3 mm는 "선형 쪽"일 가능성 | C |
| B5 | Chung & Kawaji (2004) | The effect of channel diameter on adiabatic two-phase flow characteristics in microchannels | Int. J. Multiphase Flow 30(7-8):735-761 | 10.1016/j.ijmultiphaseflow.2004.05.002 | 지름을 바꾼 미세 원관(세부 미확인) | 제목 수준 | 크기에 따른 미세 유로 거동 변화 | C |
| B6 | Brauner & Moalem Maron (1992) | Identification of the range of 'small diameters' conduits, regarding two-phase flow pattern transitions | Int. Commun. Heat Mass Transfer 19(1):29-39 | 10.1016/0735-1933(92)90061-l | 이론(관) | 표면장력이 천이를 지배하는 "작은 관" 범위를 Eötvös 수로 정의(제목·2차 수준, 식은 원문 확인 필요) | 층상류가 사라지는 크기 기준 | C |
| B7 | Bretherton (1961) | The motion of long bubbles in tubes | J. Fluid Mech. 10(2):166-188 | 10.1017/s0022112061000160 | 이론 + 실험, 저 Re | (초록 기준) 기포가 평균 액체 속도보다 U·W만큼 빠름, W ≈ 1.29(3Ca)^(2/3). 기포 앞뒤 압력 강하 ≈ 3.58(3Ca)^(2/3)σ/r. 평행판 사이 2차원 메니스커스에도 같은 이론이 적용됨. 수직관에서 ρgr²/σ < 0.842면 기포가 뜨지 않음 | 0.3~1 mm 팬케이크의 막·마찰 기본식(주제 3과 겹침) | C+A |
| B8 | Zukoski (1966) | Influence of viscosity, surface tension, and inclination angle on motion of long bubbles in closed tubes | J. Fluid Mech. 25(4):821-837 | 10.1017/s0022112066000442 | 실험, 닫힌 관 긴 기포, 경사 포함 | (초록 기준) 점성·표면장력이 기포 속도에 주는 영향 정리, 경사각 영향 제시 | 수평·경사 긴 기포 드리프트가 표면장력에 따라 줄어듦 | C+A |
| B9 | Couët & Strumolo (1987) | The effects of surface tension and tube inclination on a two-dimensional rising bubble | J. Fluid Mech. 184:1-14 | 10.1017/s0022112087002787 | 이론, 2차원 덕트(평행판) 속 큰 기포, 표면장력·경사 | (초록 기준) 2차원 덕트에서 큰 기포의 Froude 수를 σ·경사각의 함수로 구함. 실험·이론과 잘 맞음 | 3·7 mm 수평 갭에서 긴 기포(슬러그)의 드리프트(Vgj ≠ 0 가능성)를 다룰 수 있는 유일한 2차원 이론 | C+A |
| B10 | Weber (1981) | Drift in intermittent two-phase flow in horizontal pipes | Can. J. Chem. Eng. 59(3):398-399 | 10.1002/cjce.5450590322 | 수평관 간헐류 드리프트 | 제목 수준(Bond 수에 따른 수평 드리프트 상관식으로 알려짐, 원문 미확인) | 수평 긴 기포 드리프트 | C |
| B11 | Benjamin (1968) | Gravity currents and related phenomena | J. Fluid Mech. 31(2):209-248 | 10.1017/s0022112068000133 | 이론 | 제목 수준(수평 관·채널의 빈 공동이 액체 속으로 나아가는 속도, "Benjamin 기포"로 인용) | 7 mm 수평 슬러그의 드리프트 상한 | C |

### 1-C. 드리프트 플럭스 (C0, Vgj)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| C1 | Ishii (1977) | One-dimensional drift-flux model and constitutive equations for relative motion between phases in various two-phase flow regimes | ANL-77-47 (Argonne National Laboratory 보고서) | 10.2172/6871478 | 이론 + 자료 비교 | (원문, Eq. 68) 완전 발달 난류 기포류: C0 = 1.2 − 0.2√(ρg/ρf)(원관), 1.35 − 0.35√(ρg/ρf)(직사각, "실험 자료가 약 1.35를 보임"). 층류 극한 C∞ = 2(원관) | 직사각 1.35의 출처. 갇힌 팬케이크는 대상 밖 | C+F (OSTI 원문) |
| C2 | Hibiki (2019) | One-dimensional drift-flux correlations for two-phase flow in medium-size channels | Exp. Comput. Multiph. Flow 1(2):85-100 | 10.1007/s42757-019-0009-y | 리뷰(오픈 액세스) | (원문) 직사각 C0 식은 비등수·R-11·질소–NaK, ρg/ρf ≤ 0.04, 가로세로비 2.8~9.4에서 검증. "직사각 유로의 단열 기포류 C0 상관식은 없다." 수평 유로는 부력이 흐름에 수직이라 Vgj = 0으로 둠 | 수평이면 Vgj = 0, C0만 남음. 넓은 갭 단열 C0는 빈칸 | C+F |
| C3 | Rassame & Hibiki (2024) | Drift-flux model for dispersed adiabatic and boiling two-phase flows in rectangular channels | Int. J. Heat Mass Transfer 224:125270 | 10.1016/j.ijheatmasstransfer.2024.125270 | 직사각 유로 분산류 자료 모음 | (초록 기준) Vgj의 길이 척도는 D_h가 적절. C∞ = 1.35(가로세로비 < 0.25), 1.20(> 0.33), 사이는 선형 보간. 기공률 오차 ±13.9%(단열), ±8.72%(비등) | 넓은 갭(가로세로비 ≪ 0.25)이면 1.35 | C+A (CityU 포털 초록) |
| C4 | Shen, Yamamoto, Nakajima & Hibiki (2024) | A full-flow-range drift-flux model for adiabatic and boiling two-phase flows in vertical narrow rectangular flow channels | Int. J. Therm. Sci. 202:109086 | 10.1016/j.ijthermalsci.2024.109086 | 수직 좁은 직사각, 13개 자료 1758점 | (초록 기준) 기존 상관식 7개가 불만족. C0·Vgj를 밀도비, 갭, 폭, 국소 유동 조건의 함수로 새로 만듦. 상대 오차 13.1% | 갭이 들어간 최신 식. 수직이면 0.3~7 mm 비교의 기준 | C+A (CityU 포털 초록) |
| C5 | Khunsrimek, Rassame & Hibiki (2024) | Two-group drift-flux model for dispersed gas-liquid flow in rectangular channel | Int. J. Heat Mass Transfer 235:126207 | 10.1016/j.ijheatmasstransfer.2024.126207 | 직사각 유로(치수 미공개), 모양·크기로 1군/2군 | (초록 기준) C∞ = 1.00(1군, 작은 기포), 1.45(2군, 큰 기포). 기공률·기체 속도 오차 11.6·11.5%(1군), 13.6·15.0%(2군) | 크기별 C0가 다르다는 가장 가까운 근거. 다만 2구간이고 연속 곡선 C0(d/H)는 아님 | C+A (CityU 포털 초록) |
| C6 | Rassame & Hibiki (2018) | Drift-flux correlation for gas-liquid two-phase flow in a horizontal pipe | Int. J. Heat Fluid Flow 69:33-42 | 10.1016/j.ijheatfluidflow.2017.11.002 | 수평관 12개 자료 566점(관경 19~77.9 mm는 C2) | (초록 기준) Vgj = 0, C0 = f(j_g⁺/j⁺). 평균 절대 상대 편차 0.206. 회귀로 구한 Vgj에는 C0와의 보상 오차가 큼 | 수평 기준 틀. 좁은 갭 자료는 없음 | C+A (CityU 포털 초록). 정오표 10.1016/j.ijheatfluidflow.2021.108884 |
| C7 | Shen 외 (2012) | One-dimensional interfacial area transport of vertical upward bubbly flow in narrow rectangular channel | Int. J. Heat Fluid Flow 36:72-82 | 10.1016/j.ijheatfluidflow.2012.04.007 | 수직 상향 공기-물, 갭 0.993 mm × 폭 40.0 mm, 7개 높이에서 영상 처리, 차압계로 마찰 구배. j_L = 0.214~2.08 m/s, 기공률 3.92~42.6%(INIS 초록, 검색 요약) | 국소 변수의 축 방향 변화가 크고 원인은 합체·분열. Ishii(1977) 직사각 C0와 기존 Vgj 식이 측정 기공률·기체 속도와 잘 맞음. 계면 면적 농도·Sauter 직경 모델 수정(검색 요약 기준) | 1 mm 갭에서 영상으로 기포 변수를 잰 직접 선례 | C |
| C8 | Kim, Sun, Ishii, Beus & Lincoln (2002) | Interfacial structures of confined air–water two-phase bubbly flow | Exp. Therm. Fluid Sci. 26(5):461-472 | 10.1016/s0894-1777(02)00152-8 | Purdue 수직 "갇힌" 직사각 덕트, 이중 전도도 탐침 | (2000년 학회판 OSTI 774251 초록) 기공률·계면 면적 농도가 벽 쪽 봉우리. 드리프트 플럭스(C0 = 1.35)와 비교 | 갇힌 채널의 국소 분포. 벽 봉우리면 작은 기포 C0 < 1.35 | C |
| C9 | Sun, Kim, Ishii & Beus (2004a) | Modeling of bubble coalescence and disintegration in confined upward two-phase flow | Nucl. Eng. Des. 230(1-3):3-26 | 10.1016/j.nucengdes.2003.10.008 | Purdue 갇힌 채널, 2군 계면 면적 수송 | 제목 수준 | 갇힌 채널의 합체·분열 원천항 → 추적한 합체·분열 빈도와 비교 대상 | C |
| C10 | Sun, Kim, Ishii & Beus (2004b) | Model evaluation of two-group interfacial area transport equation for confined upward flow | Nucl. Eng. Des. 230(1-3):27-47 | 10.1016/j.nucengdes.2003.10.014 | 같은 채널 | 제목 수준 | 같음 | C |
| C11 | Bois, Barbera & Amate-Vignon (2025) | Void drift in narrow rectangular channels for highly advective bubbly flows: A macroscopic drift-flux model derived from two-fluid local simulations | Int. J. Multiphase Flow 182:105038 | 10.1016/j.ijmultiphaseflow.2024.105038 | 수치(국소 2유체 계산), 고압 물-증기 단분산 기포, 64조건 | (HAL 초록) 평평한 직사각 유로의 기공률 분산 모델을 드리프트 플럭스에 넣음. 기공률·Re·Eötvös 수 공간을 고르게 덮음 | 갭 방향 기공률 분포가 C0를 정한다는 틀. 실험 아님 | C+A (HAL) |
| C12 | Bhusan, Ghosh, Das & Das (2009) | Rise of Taylor bubbles through narrow rectangular channels | Chem. Eng. J. 155(1-2):326-332 | 10.1016/j.cej.2009.07.006 | 수직 좁은 직사각 유로의 Taylor 기포 | Scholar 조각: Mishima·Hibiki의 슬러그 속도 분포 계수 ≈ 1.1을 인용 | 슬러그 Vgj(수직) | C |
| C13 | Jones & Zuber (1975) | The interrelation between void fraction fluctuations and flow patterns in two-phase flow | Int. J. Multiphase Flow 2(3):273-306 | 10.1016/0301-9322(75)90015-4 | 직사각 채널 기공률 요동(X선)과 유동 양식 | 제목 수준. 직사각 채널 C0의 근거 자료로 자주 인용됨(이번에 원문 수치 미확인) | 직사각 C0 역사의 출발점 | C |

### 1-D. 갇힌(팬케이크) 기포의 속도: 압력 구동 Hele-Shaw

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| D1 | Taylor & Saffman (1959) | A note on the motion of bubbles in a Hele-Shaw cell and porous medium | Q. J. Mech. Appl. Math. 12(3):265-279 | 10.1093/qjmam/12.3.265 | 이론(깊이 평균, 막 무시) | 원형 팬케이크 기포 속도 = 주변 평균 속도의 2배(D12의 서술로 확인) | 0.3~1 mm 큰 팬케이크 C0의 상한 2 | C |
| D2 | Park & Homsy (1984) | Two-phase displacement in Hele Shaw cells: theory | J. Fluid Mech. 139:291-308 | 10.1017/s0022112084000367 | 이론, 젖은 벽, 작은 Ca·작은 ε(갭/가로 길이) | (초록 기준) ε와 Ca^(1/3)의 이중 점근 전개로 Bretherton을 넓히고 유효 경계 조건의 꼴과 상수를 정함 | 팬케이크 테두리 압력 점프 계수(주 세션 c_f ≈ 3.8)의 출처 | C+A |
| D3 | Maxworthy (1986) | Bubble formation, motion and interaction in a Hele-Shaw cell | J. Fluid Mech. 173:95-114 | 10.1017/s002211208600109x | 실험, 기울인 Hele-Shaw, 점성 액체에 공기 주입 | (초록 기준) Taylor–Saffman·Tanveer 이론은 경사 → 0이고 기포 폭이 클 때만 맞음. 작은 기포의 벗어남은 기포 표면 근처 흐름(막)으로 설명 | 작은 팬케이크일수록 이론보다 느림 | C+A |
| D4 | Kopf-Sill & Homsy (1988) | Bubble motion in a Hele–Shaw cell | Phys. Fluids 31(1):18-26 | 10.1063/1.866566 | 실험, 주변 액체 흐름으로 밀리는 기포(압력 구동) | (초록 기준) 정상 모양 6종, 다중 정상 상태·이력. 측정 병진 속도가 기존 이론과 맞지 않음 | 압력 구동 Hele-Shaw 기포 속도가 2배 이론과 다르다는 고전 근거 | C+A |
| D5 | Meiburg (1989) | Bubbles in a Hele–Shaw cell: numerical simulation of three-dimensional effects | Phys. Fluids A 1(6):938-946 | 10.1063/1.857404 | 수치, 막의 3차원 압력 점프 포함 | (초록 기준) 2차원 계산은 액체보다 빠른 기포만 줌. 3차원 압력 점프를 넣으면 넓고 짧은 기포, 액체보다 느린 기포가 나옴 | C0 < 1 가능성의 이론 근거 | C+A |
| D6 | Burgess & Foster (1990) | Analysis of the boundary conditions for a Hele–Shaw bubble | Phys. Fluids A 2(7):1105-1117 | 10.1063/1.857610 | 이론, 유효 경계 조건 | (초록 기준) 기포 옆 작은 영역의 막 두께는 Ca^(2/3)이 아니라 ε^(2/5)Ca^(4/5) | 측면 메니스커스 보정 | C+A |
| D7 | Gallaire, Meliga, Laure & Baroud (2014) | Marangoni induced force on a drop in a Hele Shaw cell | Phys. Fluids 26(6):062105 | 10.1063/1.4878095 | 깊이 평균(Brinkman) 이론 + 3차원 계산 | (초록 기준) 갇힌 액적의 힘을 닫힌 식으로 구함. D12의 서술: 점성 액적 이동도 2/(1 + η_i/η_o) | 기포(η_i → 0)면 2 | C+A |
| D8 | Huerre 외 (2015) | Droplets in Microchannels: Dynamical Properties of the Lubrication Film | Phys. Rev. Lett. 115(6):064501 | 10.1103/physrevlett.115.064501 | 실험, 미세 유로 액적 막 지형(간섭 현미경) | (HAL 초록) 낮은 Ca에서는 막 두께가 분리압으로 정해져 일정, 임계 Ca 이상에서 점성(Bretherton형) 거동 | 0.3 mm 저속에서도 막은 수 µm 이상이라 분리압 영역은 아님(직접 계산) | C+A (HAL) |
| D9 | Ling, Fullana, Popinet & Josserand (2016) | Droplet migration in a Hele–Shaw cell: Effect of the lubrication film on the droplet dynamics | Phys. Fluids 28(6):062001 | 10.1063/1.4952398 | 3차원 DNS, 낮은 Ca, 액적 | (초록 기준) 반지름 > 갭/2면 팬케이크. 팬케이크 속도는 평균 유입 속도보다 낮음(실험과 일치). 막 전단과 3차원 흐름이 원인. 속도·막 두께가 Ca와 함께 감소. 깊이 평균 Hele-Shaw 식은 이를 못 잡음 | C0 < 1 수치 근거(액적) | C+A |
| D10 | Zhu & Gallaire (2016) | A pancake droplet translating in a Hele-Shaw cell: lubrication film and flow field | J. Fluid Mech. 798:955-969 | 10.1017/jfm.2016.357 | 경계 적분, 같은 점성 액적, Stokes | (초록 기준) 평균 막 두께는 확장 Bretherton 모델로 예측. 벽 평행면의 교란은 쌍극자, 1/r²로 감쇠 | 팬케이크 사이 상호작용 거리 | C+A |
| D11 | Reichert 외 (2018) | Topography of the lubrication film under a pancake droplet travelling in a Hele-Shaw cell | J. Fluid Mech. 850:708-732 | 10.1017/jfm.2018.457 | 실험(간섭 현미경), 기름 액적 | (초록 기준) 막 지형은 3차원. 앞쪽은 표면장력 구배 무시 가능, 뒤쪽은 계면 활성제 축적으로 막이 두꺼워짐 | 오염이 뒤쪽 막을 바꿈 | C+A |
| D12 | Reichert, Cantat & Jullien (2019) | Predicting droplet velocity in a Hele-Shaw cell | Phys. Rev. Fluids 4(11):113602 | 10.1103/physrevfluids.4.113602 | 실험 + 모델. 계면 활성제 없는 공기 기포(불소 기름 η = 4.5 mPa·s, γ = 15 mN/m), 셀 두께 14 µm, R = 77/100/160 µm(d/H ≈ 11/14/23), Ca = 5×10⁻⁴~5×10⁻³ | (원문) 이동도 U_d/U_f는 Ca와 R이 클수록 커지고 Taylor–Saffman의 2보다 작음. 그림 읽기: R = 77 µm 약 1.0~1.3, 100 µm 약 1.2~1.45, 160 µm 약 1.35~1.65. 보정 소산은 둘레(∝R), 기준 소산은 면적(∝R²)에 비례 → 큰 기포일수록 2에 가까움. 계면 활성제 액적은 0.55~1.05. 뒤쪽 굳은 영역(막 면적의 수 %)이 속도를 크게 바꿈 | 0.3·0.7 mm 팬케이크 C0(d/H, Ca)의 가장 직접적인 무차원 근거. 주 세션 C0 모델 검증에 씀(2장 Q3) | C+F (HAL 원문) |
| D13 | Baué 외 (2025) | Droplet velocity in both limits of low and high soluble surfactants in a Hele-Shaw cell: experimental and analytical results | J. Fluid Mech. 1009:A23 | 10.1017/jfm.2025.167 | 실험 + 이론, 기름 액적, 계면 활성제 용해도 두 극한 | (초록 기준) 잘 녹는 계면 활성제: 속도가 반지름과 함께 증가. 잘 안 녹는 계면 활성제: 반지름과 함께 감소. 두 극한이 이동도의 상·하한 | 물-공기의 오염 정도가 C0(d/H) 기울기 부호까지 바꿀 수 있음 | C+A |
| D14 | Monnet, Soundar Jerome, Vidal & Joubaud (2024) | Bubble dynamics in an inclined Hele-Shaw cell | Phys. Rev. Fluids 9(7):073601 | 10.1103/physrevfluids.9.073601 | 실험, 기울인 Hele-Shaw, 정지한 물/UCON 혼합액(저 Re), 셀 3종 | (HAL 초록) 상승 속도는 Taylor–Saffman 극한(∝ h²·g_eff/η)을 따르지만, 많이 기울일수록 부력이 기포를 위 벽으로 밀어 위·아래 막이 비대칭이 되고 속도가 크게 줆. 위 막은 Bretherton 법칙(Ca^(2/3)), 아래 막은 아님. 마찰 항을 넣은 일률 균형 모델이 모든 자료와 맞음 | 수평 3·7 mm에서 위 덮개로 밀린 기포의 직접 근거(부력 구동이라 압력 구동과는 다름) | C+A (HAL) |
| D15 | Shen, Leman, Reyssat & Tabeling (2014) | Dynamics of a small number of droplets in microfluidic Hele–Shaw cells | Exp. Fluids 55(5):1728 | 10.1007/s00348-014-1728-2 | 미세 유로 Hele-Shaw 액적 몇 개 | 제목 수준 | 팬케이크 사이 상호작용 | C |

### 1-E. 얇은 갭에서 떠오르는 기포·기포군 (수직, 부력 구동)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| E1 | Hashida, Hayashi & Tomiyama (2019) | Rise velocities of single bubbles in a narrow channel between parallel flat plates | Int. J. Multiphase Flow 111:285-293 | 10.1016/j.ijmultiphaseflow.2018.09.015 | 실험, 갭 3 mm, d_B = 7~20 mm, 깨끗한 물·글리세린 수용액(0.9~65.7 mPa·s) | (S2 초록) 지그재그 → 직선 운동 천이가 임계 d_B에서 갑자기 일어나 V_B가 계단식 증가. 앞머리 곡률이 V_B를 크게 좌우(저점도에서 산포 불가피). Filella 식은 힘 균형에서 유도되고, 항력 계수는 Morton 수와 갭/직경 비로 표현 | 3 mm 갭 단일 기포 속도·항력. 수직이면 Vgj 모델 | C+A (고베대 저장소 원문 있음) |
| E2 | Filella, Ern & Roig (2015) | Oscillatory motion and wake of a bubble rising in a thin-gap cell | J. Fluid Mech. 778:60-88 | 10.1017/jfm.2015.355 | 실험, 갭 3.1 mm, 물 | (초록 기준) 평균 상승 속도 V_b ∝ (h/d)^(1/6)√(gd). 1200 < Re < 3000, h/d < 0.4에서 축 방향 속도 비 0.92, Strouhal 0.27 | 3 mm 갭과 같은 갭 | C+A |
| E3 | Roig, Roudet, Risso & Billet (2012) | Dynamics of a high-Reynolds-number bubble rising within a thin gap | J. Fluid Mech. 707:444-466 | 10.1017/jfm.2012.289 | 실험, 물 속 공기, 수직 Hele-Shaw, h/d < 1, 10 ≤ Ar ≤ 10⁴, 6×10⁻³ ≤ Bo ≤ 140 | (초록 기준) Re = 0.5Ar가 넓은 범위에서 성립 → 벽 액막이 항력에 크게 기여하지 않음. 모양은 원 → 타원 → 비대칭 → 반원 모자 | 3·7 mm(관성 영역)에서는 막 마찰보다 관성이 지배할 수 있음 | C+A |
| E4 | Monnet, Madec, Vidal & Joubaud (2022) | Bubble rise in a Hele-Shaw cell: bridging the gap between viscous and inertial regimes | J. Fluid Mech. 942:R3 | 10.1017/jfm.2022.361 | 실험, 수직 Hele-Shaw, 점성 → 관성 | (초록 기준) 일률 균형 모델이 점성~관성 천이의 속도를 맞춤. 점성 영역 기포는 진행 방향으로 길쭉, 관성 영역은 옆으로 납작 | 0.3 mm(점성 쪽)~3·7 mm(관성 쪽) 해석의 다리 | C+A |
| E5 | Bouche, Roig, Risso & Billet (2012) | Homogeneous swarm of high-Reynolds-number bubbles rising within a thin gap. Part 1. Bubble dynamics | J. Fluid Mech. 704:211-231 | 10.1017/jfm.2012.233 | 실험, 얇은 갭 균질 기포군 | (초록 기준) 수직 방향 속도 분산·분산 계수는 기공률에 거의 선형으로 증가(후류 끌림). 수평 방향은 경로 진동이 지배해 분산 일정 | 추적한 기포 속도 요동과 비교 | C+A |
| E6 | Bouche 외 (2014) | Part 2. Liquid dynamics | J. Fluid Mech. 758:508-521 | 10.1017/jfm.2014.544 | 같은 장치, 액체 | 제목 수준 | | C |
| E7 | Filella, Ern & Roig (2020) | Interaction of two oscillating bubbles rising in a thin-gap cell: vertical entrainment and interaction with vortices | J. Fluid Mech. 888:A13 | 10.1017/jfm.2020.4 | 두 기포 상호작용 | 제목 수준 | 앞 기포 후류의 끌림 → 합체 해석 | C |
| E8 | Huisman, Ern & Roig (2012) | Interaction and coalescence of large bubbles rising in a thin gap | Phys. Rev. E 85(2):027302 | 10.1103/physreve.85.027302 | 얇은 갭 큰 기포 | 제목 수준 | 합체 | C |
| E9 | Zhang & Hibiki (2026) | Single bubble rising behavior in narrow rectangular channels with finite channel width | Phys. Fluids 38(8):083342 | 10.1063/5.0342482 | 실험, 유한 폭 좁은 직사각 유로 단일 기포 | (초록 기준) d ≈ 0.4W에서 상승 속도가 점근값(폭·갭과 함께 증가). 큰 기포 폭 → 0.86W. Sauter 직경 → 갭의 3배로 점근. 속도·모양·항력 새 상관식 | 폭이 유한한 실제 채널의 보정 | C+A (CityU·S2 초록) |
| E10 | Pavlov 외 (2021) | Kinematics of a bubble freely rising in a thin-gap cell with additional in-plane confinement | Phys. Rev. Fluids 6(9):093605 | 10.1103/physrevfluids.6.093605 | 측벽으로 폭을 줄인 얇은 갭, 관성 | (S2 초록) 폭 갇힘이 속도·모양 결합을 바꿈, 영역별 크기 법칙 | | C+A |
| E11 | Wang 외 (2014) | Experimental and numerical study of buoyancy-driven single bubble dynamics in a vertical Hele-Shaw cell | Phys. Fluids 26(12):123303 | 10.1063/1.4903488 | 수직 Hele-Shaw 단일 기포 실험 + 수치 | 제목 수준 | | C |
| E12 | Piedra, Ramos & Herrera (2015) | Dynamics of two-dimensional bubbles | Phys. Rev. E 91(6):063013 | 10.1103/physreve.91.063013 | 2차원 기포 | 제목 수준 | | C |

### 1-F. 영상 기반 측정과 수평 채널

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| F1 | Fu & Liu (2016a) | Development of a robust image processing technique for bubbly flow measurement in a narrow rectangular channel | Int. J. Multiphase Flow 84:217-228 | 10.1016/j.ijmultiphaseflow.2016.04.011 | 좁은 직사각 유로 기포류 영상 처리 | Scholar 조각: 개별 기포 분리가 변수 측정에 필수 | 겹친 기포 분리 = 우리 파이프라인과 같은 문제 | C |
| F2 | Fu & Liu (2016b) | Experimental study of bubbly flow using image processing techniques | Nucl. Eng. Des. 310:570-579 | 10.1016/j.nucengdes.2016.10.044 | 영상 처리 기포류 실험 | 제목 수준 | | C |
| F3 | Liu, Cheng, Yan, Gu & Meng (2023) | Characteristics of one-dimensional bubbly flow interfacial area transport in horizontal narrow rectangular channel | Chem. Eng. Res. Des. 189:30-45 | 10.1016/j.cherd.2022.10.039 | 수평 좁은 직사각 유로 기포류, 고속 영상 처리 | Scholar 조각: 고속 영상으로 기포 크기·난류를 정량화 | 수평 좁은 갭에서 영상으로 계면 면적 수송을 다룬 최근 선례 | C |
| F4 | Han 외 (2025) | Two-group bubble interfacial area concentration correlation for two-phase flows in narrow rectangular flow channels | Int. J. Heat Mass Transfer 252:127453 | 10.1016/j.ijheatmasstransfer.2025.127453 | 좁은 직사각 유로 2군 계면 면적 농도 | 제목 수준 | 작은/갇힌 기포 2군 분류 | C |
| F5 | Chen 외 (2024) | Experimental study on turbulent characteristics of dispersed bubbly flow in a narrow rectangular channel by two-phase PIV | Int. J. Heat Mass Transfer 219:124887 | 10.1016/j.ijheatmasstransfer.2023.124887 | 좁은 직사각 유로 분산 기포류, 2상 PIV | Scholar 조각: 기포 크기 분포가 Weibull, 기포 직경 분포와 기포 속도 측정 | 크기 분포 + 속도를 함께 잰 최근 예 | C |
| F6 | Ito, Prasser 외 (2011) | Micro wire-mesh sensor for two-phase flow measurement in a rectangular narrow channel | Flow Meas. Instrum. 22(5):377-382 | 10.1016/j.flowmeasinst.2011.06.001 | 좁은 직사각 유로용 미세 와이어메시 | 제목 수준 | 영상 외 독립 검증 수단 | C |
| F7 | Bentley & Ruggles (1992) | Phase distribution measurements in narrow rectangular channels using image-processing techniques | ORNL/TM-12011 (보고서) | 10.2172/5349611 | 공기-물, 좁은 직사각 유로, 물에 잉크 | (OSTI 초록) 회색값을 보정 장치로 액층 두께로 바꿔 시공간 평균 액체 분율을 구함. 기체 유속 0의 압력 구배 예측과 잘 맞음 | 투영 영상에서 갭 방향 두께를 얻는 방법(주제 6) | C+A |
| F8 | Murai, Fukuda, Oishi, Kodama & Yamamoto (2007) | Skin friction reduction by large air bubbles in a horizontal channel flow | Int. J. Multiphase Flow 33(2):147-163 | 10.1016/j.ijmultiphaseflow.2006.08.008 | 수평 채널 위 벽의 큰 기포, 벽 전단 응력계 | 경계층 두께 정도의 변형 기포가 지날 때 국소 벽 전단 응력이 크게 줆(리뷰 서술, 검색 요약 기준) | 수평 7 mm에서 위 덮개 밑 기포의 영향 | C |

### 1-G. 새로움 판단용: 크기별 기포 속도·합체 자료 (2026-10-23 우선순위 변경 후 추가)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| G1 | Keeler, Gaillard, Lawless, Thompson, Juel 외 (2022) | The interaction of multiple bubbles in a Hele-Shaw channel | J. Fluid Mech. 946:A40 | 10.1017/jfm.2022.618 | 실험 + 깊이 평균 모델. 점성 액체로 미는 Hele-Shaw 채널(가운데 얕은 돌기), 기포 2개 | (arXiv 초록) 단일 기포의 전파 속도는 부피와 함께 단조 증가 → 크기가 다른 두 기포는 상호작용이 없으면 유한 시간 안에 합체하거나 멀어짐. 실제로는 불안정한 2기포 상태가 결과(합체/분리)를 정함 | "큰 기포가 더 빠르다 → 따라잡아 합체"라는 합체 기구의 직접 근거(점성 영역) | C+A (arXiv 2112.11053) |
| G2 | Lawless, Keeler, Hazel & Juel (2024) | Stable bubble formations in a depth-perturbed Hele-Shaw channel | Phys. Rev. Fluids 9(9):093605 | 10.1103/physrevfluids.9.093605 | 같은 계열 실험 + 모델 | (arXiv 초록) 깊이가 고른 채널에서는 속도가 크기와 함께 단조 증가해, 기포 무리는 결국 크기 순으로 재배열되고 모두 떨어짐. 깊이 섭동이 있으면 안정한 대형이 생김 | 0.3·0.7 mm에서 크기별 속도 차가 기포 간격·합체를 정한다는 틀 | C+A (arXiv 2302.01038, 제목이 학술지판과 다름) |
| G3 | Gaillard, Keeler, Le Lay, Lemoult 외 (2021) | The life and fate of a bubble in a geometrically perturbed Hele-Shaw channel | J. Fluid Mech. 914:A34 | 10.1017/jfm.2020.844 | 실험 + 수치, 점성 액체로 미는 기포, 깊이 섭동 채널 | (arXiv 초록) 분열·응집·합체가 나타나고, 최종 상태는 속도가 커지는 순서로 늘어선 기포들. Scholar 조각: 기포 속도는 크기와 함께 체계적으로 증가 | 분열 후 크기별 속도 차로 분리되는 과정 | C+A (arXiv 2005.13959) |
| G4 | Saffman & Tanveer (1989) | Prediction of bubble velocity in a Hele–Shaw cell: Thin film and contact angle effects | Phys. Fluids A 1(2):219-223 | 10.1063/1.857492 | 이론 | (초록 기준) 작은 Ca의 막 보정만으로는 Kopf-Sill & Homsy 실험의 느린 기포를 설명 못 함. 계면–판 접촉각이 위치마다 다르다고 두면 정성적으로 설명됨 | 철 바닥의 젖음성(부분 젖음)이 C0를 크게 낮출 수 있음 | C+A |
| G5 | Cantat, Poloni & Delannay (2006) | Experimental evidence of flow destabilization in a two-dimensional bidisperse foam | Phys. Rev. E 73(1):011505 | 10.1103/physreve.73.011505 | 실험, Hele-Shaw 속 2차원 거품(foam) 흐름 | (HAL 초록) 평균보다 10배 이상 큰 기포는 크기에 따른 속도 문턱을 넘으면 평균 흐름보다 빨리 이동. 큰 기포끼리 끌려 흐름 방향 열을 이룸 | 기공률이 높은 0.3 mm 흐름에서 크기별 속도·뭉침 | C+A (HAL) |
| G6 | Agostini, Revellin & Thome (2008) | Elongated bubbles in microchannels. Part I: Experimental study and modeling of elongated bubble velocity | Int. J. Multiphase Flow 34(6):590-601 | 10.1016/j.ijmultiphaseflow.2007.07.007 | 미세 원관 긴 기포(냉매) | 제목 수준(긴 기포 속도의 실험·모델) | 공학 조건에서 기포별 속도를 길이에 대해 잰 가장 가까운 예(원관) | C |
| G7 | Revellin, Agostini & Thome (2008) | Elongated bubbles in microchannels. Part II: Experimental study and modeling of bubble collisions | Int. J. Multiphase Flow 34(6):602-613 | 10.1016/j.ijmultiphaseflow.2007.07.006 | 같은 장치 | 제목 수준(속도 차에 의한 기포 충돌의 실험·모델) | 크기별 속도 → 충돌(합체) 빈도 모델의 원관 선례 | C |
| G8 | Sathe, Thaker, Strand & Joshi (2010) | Advanced PIV/LIF and shadowgraphy system to visualize flow structure in two-phase bubbly flows | Chem. Eng. Sci. 65(8):2431-2442 | 10.1016/j.ces.2009.11.014 | 좁은 직사각 기포탑, 기체 홀드업 약 5%, 기포 0.1~15 mm | 걸러낸 액체 속도장에서 기포마다 슬립 속도를 구해 단일 기포 상관식과 비교, 기포군과 단일 기포가 다름(검색 요약 기준) | 크기별 슬립 속도를 영상으로 잰 예(부력 구동, 평균 흐름 없음) | C |
| G9 | Almani, Blel, Gadoin & Gentric (2021) | Investigation of single bubbles rising in Newtonian and non-Newtonian fluids inside a thin-gap bubble column intended for microalgae cultivation | Chem. Eng. Res. Des. 167:218-230 | 10.1016/j.cherd.2021.01.010 | 두께 4 mm 기포탑, d = 1.34~3.36 mm(d/e = 0.34~0.84), 물·전단 묽어짐 액체 | (S2 초록) 갇힘이 벽 마찰을 키움. d/e 0.34~0.84의 갇힌 항력 상관식 | 3·7 mm에서 갭보다 작은 기포(d < H)의 벽 마찰 | C+A |
| G10 | Zehara, Si-Ahmed, Legrand & Salhi (2026) | Bubble Hydrodynamics in Rectangular Columns: Effects of Confinement and Co-Current/Counter-Current Liquid Flow | Fluids 11(9):217 | 10.3390/fluids11090217 | 직사각 기포탑, 갇힘비 λ = 3.7/11/18.5, 공류·향류 액체, 고속 영상 | (초록 기준) 갇힘이 기포 생성·성장·속도·모양을 크게 바꿈. 액체 흐름 방식은 약한 갇힘에서만 속도에 영향. 강한 갇힘에서 기존 지도가 균질류라 해도 비균질 구조가 생김 | 흐르는 액체 + 갇힘 + 크기별 속도를 함께 다룬 최신 예(기포탑 규모) | C+A |
| G11 | Ren, Zhu, Zhang, Shi & Yan (2020) | Visualization Experiment of Bubble Coalescence in a Narrow Vertical Rectangular Channel | Front. Energy Res. 8:96 | 10.3389/fenrg.2020.00096 | 수직 과냉 비등, 700 × 40 × 2 mm, 0.4 MPa, 4300 fps | (원문) 합체를 접근·병합(약 0.5 ms)·조정(약 7~8.5 ms)·안정 4단계로 기술. 합체 빈도·효율은 재지 않음("정량 분석은 앞으로"). 쌍 안에서 큰 기포가 더 빨리 미끄러짐 | 좁은 갭 합체 자료가 정성 수준임을 보여 줌 | C+F (Frontiers 원문) |
| G12 | Kim, Sun, Ishii, Beus & Lincoln (2003) | Interfacial area transport and evaluation of source and sink terms for confined air–water bubbly flow | Nucl. Eng. Des. 219(1):61-75 | 10.1016/s0029-5493(02)00289-3 | Purdue 갇힌 채널, 이중 탐침 | 제목 수준(계면 면적 수송의 합체·분열 원천항을 자료로 평가) | 합체·분열률의 간접(계면 면적 변화) 추정 선례 | C |
| G13 | Cubaud & Ho (2004) | Transport of bubbles in square microchannels | Phys. Fluids 16(12):4575-4585 | 10.1063/1.1813871 | 정사각 미세 유로 200·525 µm, 유리·실리콘 | (초록 기준) 유동 지도, 기포 속도와 슬립비 측정, 부분 젖음 벽의 건조, 2상 압력 강하 식 | 0.3 mm급 미세 유로에서 기포 속도·슬립비를 잰 예 | C+A |
| G14 | Vanapalli 외 (2009) | Hydrodynamic resistance of single confined moving drops in rectangular microchannels | Lab Chip 9(7):982-990 | 10.1039/b815002h | 미세 유로 액적 | 제목 수준 | 갇힌 액적 속도·저항의 크기 의존(미세 유로) | C |
| G15 | Jakiela, Makulska, Korczyk & Garstecki (2011) | Speed of flow of individual droplets in microfluidic channels as a function of the capillary number, volume of droplets and contrast of viscosities | Lab Chip 11(21):3603 | 10.1039/c1lc20534j | 미세 유로 액적 | 제목 수준(액적 속도를 Ca·부피·점도비의 함수로) | 개별 속도를 크기에 대해 잰 미세 유로 선례 | C |
| G16 | Sessoms 외 (2009) | Droplet motion in microfluidic networks: Hydrodynamic interactions and pressure-drop measurements | Phys. Rev. E 80(1):016317 | 10.1103/physreve.80.016317 | 미세 유로 액적 | 제목 수준 | 액적 수와 압력 강하 | C |
| G17 | Lundin & McCready (2009) | Modeling of bubble coalescence in bubbly co-current flows restricted by confined geometry | Chem. Eng. Sci. 64(18):4060-4067 | 10.1016/j.ces.2009.06.020 | 모델 | 제목 수준 | 갇힌 기하의 합체 모델 | C |
| G18 | (Crossref 저자 정보 없음) (2026) | Bubble dynamics in a Hele-Shaw channel and velocity selection without surface tension | Phys. Rev. Fluids (권·쪽 미기재) | 10.1103/pm4m-18nt | 이론(깊이 평균), Hele-Shaw 채널 | 같은 제목의 arXiv 1910.04327로 보임(미확인). 검색 요약: 기포의 무차원 속도가 크기와 함께 단조 증가, 크기 0에서는 유체 속도(추적자 극한), 큰 크기에서 포화 | 예상 C0(d) 곡선의 꼴(1에서 시작해 포화)을 지지하는 이론 | C (서지 일부만) |

## 2. 핵심 질문에 대한 답

### Q1. 유동 양식과 천이 — 갭별, 그리고 Lc 근처에서 바뀌는 것
- **0.3 mm**: 수직 자료뿐이다. 기포류가 없고 cap-bubbly, slug-droplet, churn, annular-droplet이 나타난다. 벽에 붙은 액적을 기체가 민다[A2, C+A]. 기존 천이 모델은 0.3 mm 이하에서 검증되지 않았다[A2]. Hibiki & Mishima(2001)의 기준은 0.3~17 mm 자료와 비교했다[A10, C+A].
- **0.6~1 mm**: 큰 채널과 같은 4양식(기포·슬러그·처언·환상)이다. 갭이 줄수록 천이가 낮은 기체 유량에서 일어난다[A2, C+A]. 1·2 mm 수평도 양식 지도가 있다(매끄러운 층상, plug, slug, 분산 기포, 파상 환상)[A4, C, 판 방향 미확인].
- **방향 영향**: 0.78·1.47 mm에서는 수직판 사이 수평류(H-V)를 빼면 방향 영향이 작다. 판이 수평인 수평류(H-H, 우리 경우)는 수직 상향과 비슷했다[A5, C+F]. → 0.3/0.7/1 mm 수평 실험은 수직 문헌과 비교해도 된다. H-V에서만 층상-파상류가 생겼다[A5].
- **3 mm**: 수평 3.18 mm(19.05 mm 폭)에서 원관·모세관·큰 직사각 채널 지도는 정성적으로만 맞았다[A8, C+A]. 수직 3 mm는 단일 기포 자료가 많다[E1, E2].
- **7 mm**: 수직 7 × 50 mm에서는 원관 상관식(Smith 기공률, Chisholm–Laird)이 대체로 통했다[A9, C+F].
- **갇힘 기준**: Ong & Thome(2011)은 Co ≈ 0.3~0.4 아래를 대규모, Co ≈ 1 이상을 막이 대칭인 미세 규모로 봤다(원관)[B1, C+A]. H 기준 Co는 9.1/3.9/2.7/0.9/0.39라서 0.3~1 mm는 확실히 갇힘, 3 mm는 대칭 문턱 근처, 7 mm는 대규모 경계다. D_h = 2H 기준이면 3 mm가 0.45, 7 mm가 0.19가 되어 분류가 한 단계씩 내려간다(직접 계산). 넓은 납작 유로에서 어느 길이를 써야 하는지 정한 문헌은 찾지 못했다. Rassame & Hibiki(2024)는 직사각 유로 Vgj의 길이로 D_h가 낫다고 했다(수직 분산류)[C3, C+A].
- **수평에서 Lc를 지날 때 바뀌는 것**: 문헌으로 직접 확인한 것은 둘이다. (1) 기울인 Hele-Shaw에서 부력이 기포를 위 벽으로 밀어 위·아래 막이 비대칭이 되고 속도가 준다[D14, C+A]. (2) 2차원 덕트 속 큰 기포의 드리프트는 표면장력과 경사에 따라 정해진다[B9, C+A]. 큰 기포가 위 덮개 밑 "웅덩이"(두께 ≈ 2Lc ≈ 5 mm)가 되어 7 mm에서 바닥에 닿지 않는다는 점은 주 세션의 추정(`estimates_microgap.md` 2장)이고, 수평 납작 유로에서 이를 잰 문헌은 찾지 못했다.
- **층상류**: 판이 수평인 0.78·1.47 mm에서는 층상류가 보고되지 않았다[A5]. 3·7 mm 수평(판 수평)의 층상류 자료는 찾지 못했다.

### Q2. 기공률·드리프트 플럭스 (C0, Vgj)
- 직사각 C0 = 1.35 − 0.35√(ρg/ρf)는 Ishii(1977)가 직사각 채널 자료로 정했다(원문 Eq. 68)[C1, C+F]. 검증 범위는 가로세로비 2.8~9.4의 비등수·R-11·질소–NaK다[C2, C+F].
- Mishima 외(1993, 약 1~5 mm): 기공률로는 C0 ≈ 1.35, 슬러그 기포 속도로는 1.0~1.2다[A1, C+A]. **이전 메모의 "1.35 대 1.0~1.2" 충돌은 측정 대상이 달라서 생긴 것이다.** 2차 문헌의 1.1(Bhusan 2009)·1.2(Sowiński 2009)은 슬러그 속도 쪽 값으로 보인다[C12].
- 최신 상관식: C∞ = 1.35(가로세로비 < 0.25)/1.20(> 0.33)[C3, C+A]. 갭·폭이 들어간 전 범위 식(1758점, 오차 13.1%)[C4, C+A]. 2군: 작은 기포 1.00, 큰 기포 1.45[C5, C+A].
- 1 mm 갭(0.993 × 40 mm, 수직)에서 영상으로 잰 기공률·기체 속도는 Ishii의 직사각 C0로 잘 예측됐다[C7, C(검색 요약)].
- 수평 유로는 부력이 흐름에 수직이라 Vgj = 0으로 둔다[C2, C+F; C6, C+A]. 수평 좁은 갭의 C0 자료는 찾지 못했다.
- Hibiki(2019): "직사각 유로의 단열 기포류 C0 상관식은 없다"(2019년 기준)[C2, C+F]. 이후 C3·C4·C5가 나왔지만 모두 수직이다.
- 0.3·0.7 mm: 드리프트 플럭스 자료는 찾지 못했다. 0.78 mm 기공률은 Martinelli χ 상관(Chisholm–Laird형, C = 20)으로 정리됐다[A5, C+F].

### Q3. 갇힌(팬케이크) 기포의 속도 — 0.3·0.7 mm에서 가장 중요
- **이론 상한**: 원형 팬케이크는 평균 속도의 2배(Taylor & Saffman)[D1, C; D12, C+F]. 점성 액적은 2/(1 + η_i/η_o)[D7, C+A].
- **실제는 더 느리다**: 압력 구동 실험의 속도가 이론과 맞지 않았다[D4, C+A]. 막 보정만으로는 설명이 안 되고, 접촉각 변화로 정성적 설명이 된다[G4, C+A]. 작은 기포일수록 이론에서 벗어난다[D3, C+A]. 막의 3차원 압력 점프를 넣으면 액체보다 느린 기포가 나온다[D5, C+A]. DNS에서도 팬케이크 액적은 평균 유입 속도보다 느렸다[D9, C+A].
- **정량 자료(가장 가까움)**: Reichert 외(2019)는 계면 활성제 없는 공기 기포(셀 14 µm, d/H ≈ 11~23, Ca = 0.5~5×10⁻³)의 이동도를 쟀다. 약 1.0~1.65이고 Ca와 크기가 클수록 커진다. 보정 소산이 둘레에, 기준 소산이 면적에 비례하기 때문이다[D12, C+F]. 계면 활성제 액적은 0.55~1.05로 훨씬 낮다[D12]. 계면 활성제 용해도에 따라 크기 의존의 부호가 바뀐다[D13, C+A].
- **주 세션 모델과의 대조(직접 계산)**: C0 = 2/(1 + 0.1785·c·(H/d)·Ca^(−1/3)), c = 5.
  - d/H = 11: Ca = 1×10⁻³에서 1.10, 3×10⁻³에서 1.28. Reichert 그림 값은 약 1.1, 1.3.
  - d/H = 23: Ca = 1×10⁻³에서 1.44, 4×10⁻³에서 1.61. 그림 값은 약 1.45, 1.6.
  - 그림 읽기 기준으로 ±0.05 안에서 맞는다. 단, Stokes 영역·깨끗한 계면·불소 기름이다. 물-공기 0.3 mm는 Re_H·H/d = 1.5~30이고, 물이 오염되면 더 느릴 것이다.
- **크기에 따른 단조 증가**: 고른 깊이의 Hele-Shaw 채널에서 기포 속도는 크기와 함께 단조 증가한다(점성 영역, Juel 그룹)[G1, G2, G3, C+A]. 거품 속 큰 기포도 평균보다 빨리 간다[G5, C+A].
- **갭보다 작은 기포(3·7 mm 수평)**: 위 벽으로 밀린 기포는 막이 비대칭이 되어 느려진다(부력 구동 실험)[D14, C+A]. 압력 구동 흐름에서 위 벽 밑 작은 기포의 C0를 잰 문헌은 찾지 못했다. 층류 속도 분포로 본 추정(C0 ≈ 6(y/H)(1 − y/H), y = d/2)은 주 세션의 계산이다.
- **예상되는 C0(d/H) 곡선(문헌 + 직접 추론)**
  - 0.3·0.7 mm: 거의 모든 기포가 팬케이크다. C0는 작은 팬케이크에서 1 근처(또는 1 미만)로 시작해 d/H·Ca와 함께 2를 향해 오른다[D3~D5, D9, D12]. 오염·부분 젖음이면 전체가 내려간다[D12, D13, G4]. Darcy–Bretherton 근사가 다섯 갭 중 가장 잘 맞는 곳이다(Re_H·H/d가 가장 작음).
  - 1 mm: 같은 가지지만 관성이 크다(Re_H·H/d = 2~300). 관성 영역에서는 막이 항력에 덜 기여한다는 보고가 있다(부력 상승)[E3, C+A] → C0가 Stokes 모델보다 높을 수 있다(추론).
  - 3 mm: 두 가지가 섞인다. d < 3 mm는 위 벽 근처 가지(C0 < 1 가능), d > 3 mm는 양쪽 벽에 닿는 팬케이크 가지.
  - 7 mm: 대부분 위 벽 근처 가지. 큰 기포는 위 덮개 밑 웅덩이가 되어 밑으로 액체가 흐른다. 수평 긴 기포의 드리프트 이론[B9, B11]이 필요할 수 있다.
- **이 곡선을 공학 조건에서 잰 연구**: 찾지 못했다(4장). 가장 가까운 것은 2군 C0(1.00/1.45, 수직, 탐침)[C5], 미세 유로 이동도[D12, D13, G13~G15], 점성 Hele-Shaw의 정성적 단조 증가[G1~G3]다.

### Q4. 얇은 갭의 기포·기포군 (수직, 부력 구동)
- 단일 기포 상승 속도: 3.1 mm 갭에서 V_b ∝ (h/d)^(1/6)√(gd)[E2, C+A]. 3 mm 갭에서 지그재그 → 직선 천이로 V_b가 계단식으로 늘고, 항력은 Morton 수와 갭/직경 비로 표현된다[E1, C+A]. 관성 영역에서는 Re = 0.5Ar이고 막이 항력에 크게 기여하지 않는다[E3, C+A]. 점성 → 관성 천이는 일률 균형 모델로 맞는다[E4, C+A]. 유한 폭 보정(큰 기포 폭 0.86W, Sauter 직경 → 갭의 3배)[E9, C+A]. 갭보다 작은 기포(d/e = 0.34~0.84)의 갇힌 항력 식[G9, C+A].
- 기포군: 속도 요동·분산이 기공률에 거의 선형으로 는다[E5, C+A].
- 합체·분열: 쌍 상호작용(후류 끌림, 와류)[E7, E8, C]과 점성 채널의 크기 순 분리·합체[G1~G3, C+A]가 있다. 좁은 직사각 유로에서는 비등 합체의 정성 기술[G11, C+F], 측벽이 합체 확률을 높인다는 보고[A14, C(검색 요약)], 1 mm 갭에서 국소 변수의 축 방향 변화를 합체·분열로 해석한 계측[C7, C(검색 요약)], 계면 면적 수송의 원천항 평가[G12, C9, C10, C]뿐이다. **갭별 합체·분열 빈도를 직접 센 단열 자료는 찾지 못했다.**

### Q5. 갭에 따른 압력 강하 실험 자료 (주제 3과 겹침, 조건만)
- Mishima 외(1993, 약 1~5 mm, 수직): Chisholm–Laird로 맞지만 C가 갭이 줄면 21 → 0[A1, C+A].
- Lee & Lee(2001, 수평, 폭 20 mm, 0.4~4 mm, 305점): C = f(질량 유속, 갭), ±10%[A7, C].
- Sadatomi·Ali·Kawaji(1992/93, 0.78·1.47 mm, 6방향): Beattie–Whalley·분리류 모델이 가장 좋음[A5, C+F; A6, C].
- Wambsganss 외(1991/92, 수평 3.18 mm): 기존 식 불일치 → 수정식[A8, C+A].
- Sadatomi 외(1982, 수직 7 × 50 mm 등): Chisholm–Laird가 원관 수준으로 맞음[A9, C+F].
- Ide & Fukano(2005), Ide 외(2007): 납작 모세관 직사각 유로의 holdup·마찰(원문 미확인)[A15, A16, C].
- Lowry & Kawaji(1988): Crossref에서 찾지 못함(U, DOI 없음으로 추정).
- → 0.3 mm 수평 판의 압력 강하 자료는 Lee & Lee(0.4 mm부터)가 가장 가깝다. 0.3·0.7 mm 자료는 그 자체로 기존 범위를 넓힌다.

### Q6. 새로움
- 4장 표 참고. 요약: "영상 추적으로 기포마다 잰 C0를 d/H의 연속 함수로, 갭 0.3~7 mm에 걸쳐 압력 구동 물-공기 흐름에서" 낸 연구는 찾지 못했다. "갇힌 기포 비율"이라는 영상 지표도 찾지 못했다(가장 가까운 것은 2군 분류[C5, F4, C9]). "갭별 합체·분열 빈도"의 직접 측정도 찾지 못했다.
- 좁은 직사각 유로에서 영상으로 기포 크기 분포·계면 면적 농도를 낸 연구는 있다: Fu & Liu(2016, 영상 처리 기법)[F1, F2, C], Shen 외(2012, 1 mm 갭 7개 높이)[C7, C], Liu 외(2023, 수평)[F3, C], Chen 외(2024, 2상 PIV + 크기 분포)[F5, C], Bentley & Ruggles(1992, 잉크 흡광으로 액층 두께)[F7, C+A]. 이들은 계면 면적 수송·Sauter 직경이 주 출력이고, 크기별 속도(C0)는 주 출력이 아니다(초록·조각 기준).

## 3. 아이디어와 시사점

| # | 아이디어 | 새로움 | 필요한 데이터 | 실현성 | 위험 |
|---|---|---|---|---|---|
| 1 | **갭별 크기 분해 C0(d/H) 곡선** (0.3~7 mm, 압력 구동 물-공기) | 높음. 공학 조건의 연속 곡선은 못 찾음. 미세 유로(Stokes)와 부력 상승(관성) 사이의 빈칸 | 기포별 속도(추적), 투영 면적 → d, j_L·j_G(유량계), H 실측값, 수온(μ, σ), 화소당 mm | 높음. 파이프라인이 기포별 속도·크기를 이미 낸다 | 화소당 mm·j 오차, 물 오염(계면 활성제), 철 바닥 부분 젖음[G4], 입구 효과, 기포 간 상호작용(높은 기공률), 작은 기포 검출 편향 |
| 2 | **한 계수 두 관측**: C0 곡선에서 맞춘 메니스커스 계수 c로 기포 압력 강하 항을 예측해 측정 ΔP와 비교 | 중~높음(주제 3과 함께 판단). Reichert(2019)는 미세 유로에서 일률 균형으로 속도를 예측했지만 압력 강하와 같은 계수로 묶지는 않음 | 1의 자료 + ΔP(탭 위치·입출구 보정) | 0.3·0.7 mm에서 가장 좋음(Darcy 근사가 가장 맞고 ΔP가 큼) | 관성 보정, 오염으로 c가 운전점마다 바뀔 수 있음 |
| 3 | **갇힌 기포 비율 α_trap**(d > H인 기포의 기체 면적 비율)을 갭·유량 지도로 | 중간. 2군 분류[C5, C9, F4]와 개념이 겹치므로 반드시 인용·비교 | 1과 같음 | 높음 | 기준(d > H인지 d > 2H인지) 선택. 투영 면적 → 부피 보정(주제 6) |
| 4 | **크기별 속도 차가 만드는 합체 빈도**: 쌍의 상대 속도(1의 곡선에서) × 접근 빈도 × 합체 효율 | 높음. 점성 채널의 쌍 실험[G1~G3]과 비등 정성 관찰[G11]만 있음 | 추적의 합체·분열 이벤트, 쌍별 상대 속도·간격 | 중간. 이벤트 판정 오류를 연결 감사로 재야 함 | 트래커의 가짜 합체·분열, 화면 밖 합체 |
| 5 | **판이 수평인 0.3~7 mm 유동 양식 지도**(영상 지표 포함) | 중간. 0.3 mm 수평 판 지도는 못 찾음(Xu는 수직) | 영상 + 유량 | 높음 | 양식 판정의 주관성 → 지표(α_trap, 크기 분포)로 정량화 |

- 관성의 위치: 0.3 mm(Re_H·H/d ≈ 1~30)는 미세 유로 Stokes 이론[D12]과 가장 가깝고, 3·7 mm는 관성 상승 기포 문헌[E1~E4]과 가깝다. 다섯 갭이 이 두 문헌군을 잇는 것이 논문의 줄기가 될 수 있다(직접 추론).
- 물-공기에서 깨끗한 계면을 가정하기 어렵다. 같은 장치에서 계면 활성제를 조금 넣은 대조 조건(또는 물 교체 직후/장시간 후 비교)이 있으면 C0 해석의 위험이 크게 준다[D12, D13].

## 4. 새로움 판단 기록

### 4.1 한 것 / 안 한 것
| 주제 | 이미 한 것 (누가, 조건, 결과) | 찾지 못한 것 |
|---|---|---|
| 팬케이크 기포 속도의 크기·Ca 의존 | Reichert 외 2019(공기 기포, 셀 14 µm, Stokes, 이동도 1.0~1.65)[D12]. 액적: Ling 2016 DNS[D9], Baué 2025[D13], Jakiela 2011·Vanapalli 2009(제목)[G14, G15]. 점성 Hele-Shaw 채널에서 크기와 함께 속도 단조 증가(Juel 그룹)[G1~G3]. 고전: Kopf-Sill & Homsy 1988, Maxworthy 1986, Saffman & Tanveer 1989[D3, D4, G4] | 물-공기, mm 갭, Re_H > 1, 압력 구동에서 C0(d/H) 연속 곡선 |
| 크기별 드리프트 플럭스(공학 조건) | 2군 C∞ 1.00/1.45(직사각, 수직)[C5]. Purdue 갇힌 채널 2군 모델[C9, C10]. 슬러그 속도 C0 1.0~1.2 vs 기공률 C0 1.35[A1]. 원관 미세 유로 긴 기포 속도(제목)[G6] | 연속 크기 분해, 영상 추적 기반, 수평, 0.3~7 mm 갭 비교 |
| 크기별 슬립 속도(부력 구동, 갇힘) | 3·3.1 mm 갭 단일 기포[E1, E2], 4 mm 갭 d/e 0.34~0.84[G9], 좁은 기포탑 기포군 슬립(0.1~15 mm)[G8], 갇힘비 3.7~18.5 + 액체 흐름[G10] | 평균 액체 흐름이 지배하는 채널 흐름(수평)에서의 같은 측정 |
| 합체·분열 빈도 | 쌍 상호작용(얇은 갭 상승)[E7, E8], 점성 채널 2기포[G1], 비등 합체 단계(정성)[G11], 원관 미세 유로 충돌(제목)[G7], 원천항의 간접 평가[G12], 측벽 효과(검색 요약)[A14] | 갭별 단위 면적·시간당 합체·분열 빈도를 영상 추적으로 직접 센 단열 자료 |
| 갇힌 기포 비율 | 2군 분류(모양·크기)[C5], 2군 계면 면적 농도 식(제목)[F4] | d > H 면적 비율이라는 영상 지표의 갭별 비교 |
| 수평 좁은 갭 양식 | 1·2 mm[A4], 0.78·1.47 mm 6방향[A5, A6], 3.18 mm[A8], 0.4~4 mm 압력 강하[A7] | 0.3 mm 판 수평 양식 지도, 3·7 mm 판 수평의 층상류·웅덩이 기포 자료 |

### 4.2 검색 기록 (2026-10-23)
- Crossref(제목·키워드, rows 3~10): 시작 문헌 16편과 후보 약 70편 대조. 새로움용 키워드 검색은 다음과 같다(결과 상위 6~10건을 모두 확인).
  - "bubble velocity as a function of bubble size narrow rectangular channel experiment" → 10건: 비등·흔들림 조건 영상 연구(Li 2014, Ren 2020, Yan 2018, Hong 2011, Lv 2023), Zhang & Hibiki 2026. 흐르는 액체에서 크기별 C0는 없음.
  - "confined bubble velocity Hele-Shaw cell pressure-driven flow experiment bubble size" → 10건: Saffman & Tanveer 1989, Haudin 2016, Booth 2025(발표), PRF 2026(이론). 공학 조건 자료 없음.
  - "bubble coalescence breakup frequency narrow rectangular channel adiabatic air-water experiment" → 10건: Ren 2020(비등, 정성), Zhang 2022(비등 미끄럼 기포 합체율), 나머지 CFD. 단열 빈도 자료 없음.
  - "bubble coalescence Hele-Shaw cell experiment frequency bubbly flow confined" → 8건: Lundin 2009(모델), Ramadugu 2023(스펙트럼), 액적 합체 1건. 빈도 자료 없음.
  - "bubble interaction coalescence two-dimensional bubbly flow thin gap statistics" → 6건: 모델 논문뿐.
  - "drift-flux model narrow rectangular channel distribution parameter" → 10건: Bois 2025, Shen 2024, Khunsrimek 2024 등(모두 수직 또는 수치).
  - "bubbly flow horizontal narrow rectangular channel void fraction drift flux" → 8건: Bois 2025, Jin 2014(흔들림), Liu 2023(수평 계면 면적). 수평 C0 자료 없음.
- Google Scholar(WebFetch, 첫 페이지만, 5회)
  - "Some characteristics of gas-liquid flow in narrow rectangular ducts" → 약 65건, 1쪽에 대상 없음.
  - Mishima Hibiki Nishihara "narrow rectangular ducts" "distribution parameter" → 16건. C0 ≈ 1.35·슬러그 1.0~1.2 조각.
  - "narrow rectangular channel" bubble velocity "bubble size" image processing distribution parameter(2010~) → 약 167건, 1쪽 10건이 모두 영상 계측(크기 분포·속도·수밀도)이고 크기별 C0는 조각에 없음.
  - Hele-Shaw bubbles "bubble velocity" "bubble size" mean/imposed/pressure-driven flow mobility → 26건: Gaillard 2021, Cantat 2006, Huerre 2014(리뷰), Gangloff 2014(복합재 수지 속 공극, 압력 구동 Hele-Shaw 셀에서 기포 크기·수지 속도에 따른 기포 속도; Crossref 대조, 원문 미확인이라 표에는 넣지 않음), 거품 흐름 연구들.
  - narrow/mini/thin gap air-water "bubble velocity" bubble length/diameter "liquid velocity" → 35건: Almani 2021, Zehara 2026, Bouche 2012, Shikazono & Han 2011(미세관 기포/평균 속도비, 미대조), Zenit 2004(경사 채널 기포 현탁, 미대조).
- WebSearch(standard, 11회): 아래 9회 + 추가 2회. (10) Shen 2012 세부 → INIS 초록(0.993 mm, j_L 0.214~2.08 m/s, 기공률 3.92~42.6%, 합체·분열로 축 방향 변화), 크기별 속도 언급 없음. (11) 압력 구동 Hele-Shaw + 물 + 관성 + 기포 속도/평균 액체 속도 → 맞는 실험 없음. 찾은 것은 점성 영역(축소 Re ≤ 0.2) 채널 실험, 부력 상승(Monnet 2022: 점성 액체는 d/h > 8에서 무차원 속도가 약 1로 포화, 물은 더 낮음), 이론 G18.
- WebSearch 앞 9회: Wilmarth & Ishii 조건, Xu 1999 양식, Ide·Fukano(세부 못 찾음), Murai 2007, 수평 좁은 갭 계면 면적(대신 Shen 2012 세부), Ong & Thome 문턱값, Chung & Kawaji(일부), 좁은 직사각 2상 PIV(→ Sathe 2010), Agostini/Revellin(서지만).
- 초록 출처: CityU·HKUST·HIT 연구 포털, HAL API, OSTI API, arXiv API, Semantic Scholar, EPFL infoscience(서지만), Frontiers(원문).
- **한계**: Scholar는 첫 페이지만 봤다. ScienceDirect 등 출판사 페이지가 막혀 Elsevier 논문 상당수는 제목·검색 요약 수준이다. OpenAlex는 하루 예산 소진으로 못 썼다. 중국어(CNKI)·일본어 학회 논문집은 J-STAGE 일부만 봤다. → "찾지 못했다"는 "이 범위에서 찾지 못했다"는 뜻이다.

## 5. 남은 의문과 사용자에게 확인할 것
- 실험 조건(새로움 주장의 범위를 정함)
  - 채널 방향(판이 수평인지), 폭 W, 길이, 입구 구조(공기 주입 방식: T자, 다공판, 바늘 등).
  - 0.3·0.7 mm 갭의 실측값과 공차. 층류 ΔP ∝ 1/H²(같은 평균 속도), 같은 유량이면 1/H³이라 0.3 mm에서 10 µm 오차도 결과를 크게 바꾼다(직접 계산).
  - 물의 종류(수돗물·증류수), 실험 중 물 교체 주기, 계면 활성제 유무 — C0 해석에 직접 영향[D12, D13].
  - 철 바닥·덮개 재질과 젖음성(접촉각). 부분 젖음이면 접촉선 마찰로 C0가 크게 줄 수 있다[G4].
  - 화소당 mm, 촬영 fps, j_L·j_G 범위, 압력 탭 위치.
- 문헌 쪽 미확인(원문을 못 봄)
  - Wilmarth & Ishii(1994)의 수평 채널 판 방향, Lee & Lee(2001)의 C 식, Ide & Fukano(2005)의 갭, Fourar & Bories(1995)의 개구 폭.
  - Kew & Cornwell의 Co 문턱 0.5, Brauner & Moalem Maron의 기준식, Benjamin·Weber의 수평 드리프트 수치.
  - Lowry & Kawaji(1988): Crossref에 없음.
  - Agostini(2008)·Revellin(2008)의 크기별 속도·충돌 결과(제목만), Chen(2024)·Shen(2012)이 크기별 속도를 냈는지.
  - 고베대 저장소의 Hashida(2019) 원고, Hibiki 2019 외 CityU 포털 초록은 읽었지만 원문 표·그림은 일부만 봤다.

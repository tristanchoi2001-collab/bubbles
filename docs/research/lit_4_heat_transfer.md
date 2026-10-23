# 주제 4: 열전달 모델과 영상 변수 (2026-10-23, 조사 에이전트 4)

대상: 갭 H = 0.3, 0.7, 1, 3, 7 mm(범위 변경 반영). 물, 철 블록 바닥 가열(매립 열전대), 위 투명 덮개, 고속 영상(위에서 봄).
"공기 주입이면 / 비등이면", "수평이면 / 수직이면"으로 나눠 쓴다. 확인 수준 규칙은 `agent_brief.md` 4장.
크기 추정은 메인 세션의 `estimates_microgap.md`와 같은 물성(물 20 °C, 포화수 100 °C)을 썼다. 계산 스크립트는 세션 scratchpad(`lit4/scripts/est4.py`)에만 있다.

## 0. 요약
1. **가장 가까운 선행 연구는 일본 사가대 Monde 그룹(1987~1995)이다** [1–6]. 좁은 수직 직사각 유로(폭 20 mm, 갭 s = 1~7 mm)에 기포를 정해진 주기로 통과시키고, 얇은 박(50 µm) 가열면의 h를 기포 통과 주기 T0와 기포 길이 l로 정리했다.
   - 포화 비등(s = 2, 3, 4, 7 mm): 같은 기포 길이면 h는 갭에 거의 무관(±15%)하고, l과 T0가 지배한다 [1](C+F).
   - 공기 기포 + 서브쿨 물(s = 2 mm): h는 T0만의 함수다. 기포가 없을 때의 약 5배 [2](C+F).
   - 해석 모델(증발 없음): 잔류 액막 x*와 T0로 h를 주는 닫힌 해. 두 극한이 "표면 갱신(Higbie형)"과 "액막 전도(k/x*)"다 [3](C+F). 잰 잔류막 x* = 70 µm(s = 2 mm), 56 µm(s = 1~1.5 mm) [5](C+F).
   - → "갭 효과는 기포 통과 주기와 기포 길이(영상 변수)로 설명된다"는 주장의 직접 선례다. 다만 기포를 인위적으로 일정 주기로 넣었고, 수직 유로였으며, 영상 통계(자동 검출·추적)는 없었다.
2. **수평 미니채널(1.2~1.5 mm)에서 주입 공기 기포 vs 증기 기포의 열전달 강화를 영상 + 액정 열화상으로 비교한 연구** [8](C+A): 공기 기포가 Nu를 120~350% 올렸고, 강화가 기포 직경과 빈도의 무차원군으로 잘 정리됐다. 주된 기구는 증발이 아니라 기포 뒤의 혼합(단상 대류)이라고 결론냈다. 가열 벽이 **위**라 사용자 장치(아래 가열)와 기포-가열면 관계가 반대다.
3. **0.3 mm에서는 단상 층류 기준선이 이미 높다.** 완전발달 층류 h ≈ 5.4 kW/m²K(Nu_Dh = 5.385 가정)이고, 표면 갱신 상한(Higbie형)이 이를 넘으려면 통과 빈도가 약 9 Hz 이상이어야 한다(0.7 mm 1.7 Hz, 1 mm 0.8 Hz, 3 mm 0.1 Hz; 본 조사 계산). 공기 주입에서는 기포 밑 얇은 막이 1 ms 안에 열적으로 포화돼 덮인 면적이 **단열**처럼 작동할 수 있다. → 0.3~0.7 mm에서는 강화가 작거나 오히려 h가 떨어질 수 있다. 1~3 mm가 공기 주입 강화에 가장 유리한 갭일 가능성이 있다(가설).
4. **비등이면 0.3~1 mm의 핵심은 팬케이크 밑 액막 증발이다.** 3구역 모델(Thome 2004) [14]의 입력 중 기포 빈도·길이·속도는 영상으로 바로 잴 수 있고, 초기 막 두께는 상관식(Moriyama & Inoue, Zhang & Utaka 0.15~0.5 mm 갭, Han & Shikazono)으로 준다 [20, 21, 23]. 원 모델의 막 두께 계수 C_δ0는 연구마다 0.29 → 0.81 → 3.48로 10배 넘게 달라졌다 [19](C+F) → 측정 빈도를 넣으면 맞춤 자유도가 줄어든다는 점이 논문 기여가 될 수 있다.
5. **0.2~0.5 mm 갭 비등은 낮은 건도에서 h가 높다가 건도에 따라 단조 감소한다(조기 부분 건조)** [10](C+A). 실리콘 마이크로갭 80~500 µm에서는 갭이 작을수록 h가 컸다 [11](C+A).
6. **매립 열전대는 기포 하나의 통과를 보지 못한다.** 탄소강의 열 침투 깊이는 10 Hz에서 0.66 mm, 50 Hz에서 0.29 mm다. 기포 통과에 따른 벽 온도 변동은 얇은 박에서도 1 K 수준이다(Monde: ΔTw/qw = 1.65×10⁻⁴·T0^0.75) [4](C+F). → 영상 통계와 h는 운전점별 **시간 평균**으로 연결해야 한다. 순간 동기화는 얇은 박 + IR/액정이 필요하다 [8, 41, 42, 73].
7. **새로움 판단(잠정)**: "좁은 갭에서 기포 통과 주기·길이와 h"는 Monde [1–5]가 이미 했다(수직, 인위 주입, 1~7 mm). "자동 영상 통계(검출·추적)로 자연 발생 기포류의 접촉 면적 비율·통과 빈도·슬러그 길이를 재고, 0.3~7 mm 다섯 갭의 측정 h를 기구별 모델로 설명"하는 연구는 찾지 못했다(4장 검색 기록). 수평 + 아래 가열 + 불투명 금속 가열면 조합도 찾지 못했다.

## 1. 문헌 표
열 이름: `| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |`

### 1.1 가장 가까운 문헌: 좁은 갭을 지나는 기포와 열전달
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 1 | Monde, Mihara, Noma (1988) | The enhancement of heat transfer due to bubbles passing through a narrow vertical rectangular channel (The effect of bubble length and clearance of channel on heat transfer) | Trans JSME B 54(507):3214–3218 | 10.1299/kikaib.54.3214 | 수직, 폭 20 mm, 길이 200 mm, 갭 s = 2/3/4/7 mm, 물·R113 포화, 1 atm. 가열면 10×20 mm 스테인리스 박 50 µm. 기포를 주기 T0 = 0.033~1.0 s로 강제 통과, 기포 길이 l = 10/20/30 mm | 같은 l이면 s = 2~7 mm의 h가 ±15% 안(2~3점 제외). h는 l이 길수록, T0가 짧을수록 크다. 포화 상한 h̄ = 2.3×10⁴λ(물 1.57×10⁴ W/m²K, aT0 < 6×10⁻⁹ m²). 좁은 갭에서 h가 큰 것은 갭 자체가 아니라 기포 발생 주기 감소와 기포 길이 증가 때문이라고 해석 | 3·7 mm를 포함한 거의 같은 갭 범위. "갭 효과 = 영상 변수(T0, l) 효과"의 직접 선례. 수직·인위 주입이라는 차이 | C+F (J-STAGE 원문) |
| 2 | Monde, Mihara, Noma (1989) | Enhancement of heat transfer due to a bubble passing through a narrow vertical rectangular channel (Effect of subcooling on heat transfer) | Trans JSME B 55(510):483–487 | 10.1299/kikaib.55.483 | 같은 장치, s = 2 mm. **공기 기포**, 물 서브쿨 70/40/20/10 K, 에탄올 60/30 K. T0 = 0.1~10 s, l = 10/20/30 mm | ΔTsub ≥ 40 K에서 h는 T0만의 함수(열유속·l 무관) → 기포가 열경계층을 쓸어 내는 현열 수송이 기구. 기포 없을 때 h0 = 1300(ΔTsub 70 K)~1700 W/m²K(20 K, q = 3.7×10⁴ W/m²), 기포 있으면 약 5배(T0 = 0.1 s), 흐름만 고려한 추정의 약 2배 | 공기 주입 + 좁은 갭의 h를 통과 주기 하나로 정리한 실험. 0.3~3 mm 공기 주입 해석의 출발점 | C+F |
| 3 | Monde, Mitsutake (1989) | Enhancement of heat transfer due to bubbles passing through a narrow vertical rectangular channel (Theoretical analysis without evaporation on an interface) | Trans JSME B 55(515):2030–2034 | 10.1299/kikaib.55.2030 | 1차원 비정상 전도 모델(Kusuda 외 1980 기반). 기포 통과 때 과열 액층 제거 → 기포 밑 잔류 액막(증발 없음) → 통과 뒤 벌크 액 유입. 등열유속·등온 가열 모두 해석 | 무차원 h̄√(aT0)/λ = f(δ = x*/√(aT0)). δ < 0.01: 등열유속 √π, 등온 2/√π(= Higbie). δ > 7: h̄x*/λ = 1(등열유속), 2/3(등온). 잔류막 x* = 71.7 µm(60~80 µm). 짧은 가열면 실험은 모델의 2~3배(다음 기포가 일으키는 흐름 때문) | 표면 갱신 상한과 액막 극한을 한 식으로 준다. 영상 변수 T0(=1/f)와 덮는 시간이 입력. 가열 벽 열용량 변수 B2 포함 → 철 블록이면 등온 극한 쪽 | C+F |
| 4 | Monde, Mihara (1987) | Boiling heat transfer in a narrow vertical rectangular channel (Relationship between heat transfer coefficient and period of passing bubble) | Trans JSME B 53(490):1788–1792 | 10.1299/kikaib.53.1788 | s = 2 mm, 물·R113 포화. T0 = 0.033~1.0 s | aT0 > 6×10⁻⁹ m²이면 기포 통과로 h 증가(열유속 클수록 큼). aT0 < 6×10⁻⁹ m²이면 h가 T0·q에 무관한 포화값. 벽 온도 변동 폭 ΔTw/qw = 1.65×10⁻⁴·T0^0.75(물; q = 3.5×10⁴, T0 = 0.1 s에서 ΔTw = 1.2 K) | 통과 빈도로 h가 포화되는 한계 주기. 벽 온도 변동 크기(Q3) | C+F |
| 5 | Monde, Mihara, Okafuji (1991) | Measurement of liquid film thickness during pass of bubble in a vertical rectangular channel | Trans JSME B 57(542):3499–3504 | 10.1299/kikaib.57.3499 | 공기 기포 상승(약 0.33 m/s), s = 1.0/1.5/2.0 mm, l = 10~30 mm, T0 = 0.25~2 s. 가열 박 온도 상승에서 막 두께 역산 | x* = 70.3 µm(s = 2 mm), 56.0 µm(s = 1.0·1.5 mm). l과 T0의 영향은 거의 없음. 56 µm는 Street & Tek의 전단-부력 균형 막과 가깝다 | 갇힌 기포 밑 막의 실측값(수직, 부력 구동). 수평 강제 흐름의 Bretherton형 막(0.3 mm에서 2~10 µm)과 비교 기준 | C+F |
| 6 | Monde, Mitsutake (1989); Monde (1988, 1990); Monde, Mitsutake (1995) | 영문판: Enhancement of heat transfer due to bubbles passing through a narrow vertical rectangular channel / Characteristic of heat transfer enhancement… / Measurement of liquid film thickness… / (Change in heat transfer along flow) | IJMF 15(5):803–814; J Heat Transfer 110(4a):1016–1019; 112(1):255–258; Heat Mass Transfer 31(1-2):77–82 | 10.1016/0301-9322(89)90042-6; 10.1115/1.3250576; 10.1115/1.2910357; 10.1007/bf02537424 | [1–5]의 국제 학술지판 | 내용은 일본어판[1–5]으로 확인(영문판 원문은 못 봄) | 논문에서 인용할 판 | C |
| 7 | Kusuda, Monde, Uehara, Otsubo (1980) | Bubble influence on boiling heat transfer in a narrow space: About low heat-flux region | Trans JSME B 46(408):1555–1562 | 10.1299/kikaib.46.1555 | 좁은 유로, 낮은 열유속 비등 | (원문 미확인) [3]의 모델 바탕(현열 수송 모델) | 모델 계보 | C |
| 8 | Albahloul, Hollingsworth, Witte, Ozer (2013) | Comparing the enhancement of heat transfer caused by sliding gas bubbles and by sliding vapor bubbles in subcooled flow in a minichannel | ASME HT2013, V002T07A042 | 10.1115/ht2013-17070 | 수평 직사각 미니채널, 간격 1.21~1.484 mm, **위 벽** 금속 가열, 아래 투명 벽. Novec 649 강한 서브쿨 층류. 공기 주입(한 점 또는 소결 플러그) vs 핵생성 증기 기포. 고속 영상 + 액정 열화상(시간 평균) | 공기 기포 Nu 강화 120~350%. 단일 공기 기포 통과 뒤 벽 온도 2~5 °C 하강. 공기·증기 모두 기포 직경·빈도 무차원군으로 잘 정리. 기구는 기포 뒤 혼합(단상 대류) | 1 mm 근처 수평 갭에서 "영상 변수 → Nu"를 한 가장 가까운 사례. 가열면 위치(위)가 반대 | C+A (Crossref 초록) |
| 9 | Ozer, Oncel, Hollingsworth, Witte (2011); Ozer, Hollingsworth, Witte (2012) | The effect of sliding bubbles on nucleate boiling of a subcooled liquid flowing in a narrow channel; Highly subcooled flow boiling: a model for estimating heat transfer behind sliding bubbles in a narrow channel | IJHMT 54(9-10):1930–1940; ASME HT2012-58031 | 10.1016/j.ijheatmasstransfer.2011.01.010; 10.1115/ht2012-58031 | 1.2×23 mm 수평 채널, 한쪽 넓은 벽 균일 발열, 반대쪽 광학 창, Novec 649, 서브쿨 15~50 °C, 액정 열화상 | 2012: 기포 뒤 "잘 섞인 액체 영역" + 1차원 비정상 전도(quenching/diffusion) 모델. 핵비등·마이크로층 증발 없이 17조건의 벽 온도·열유속을 ±15%로 예측(초록 기준) | 갇힌 미끄럼 기포의 단상 혼합 모델. Monde 모델과 같은 계열(통과 후 전도) | 2011 C, 2012 C+A |
| 10 | Yang, Fujita (2004) | Flow boiling heat transfer and flow pattern in rectangular channel of mini-gap | ASME ICMM2004-2383, 573–580 | 10.1115/icmm2004-2383 | 직사각 좁은 유로, 갭 2/1/0.5/0.2 mm, 폭 20 mm, 길이 100 mm | 유동 양식이 갭에 강하게 의존. 작은 갭은 기포류가 사라짐. 2·1 mm는 관과 비슷한 열전달. 0.5·0.2 mm는 낮은 건도에서 h가 높고 건도에 따라 단조 감소(구석 미세 기포 + 얇은 막의 조기 부분 건조) | 0.3/0.7/1 mm 비등의 갭 경계(0.5~1 mm 사이)를 시사 | C+A |
| 11 | Alam, Lee, Yap, Jin (2012, IMECE); Alam, Lee, Yap, Jin, Balasubramanian (2012, IJHMT) | Experimental study and high speed visualization of flow boiling characteristics in silicon microgap heat sink; Experimental investigation and flow visualization to determine the optimum dimension range of microgap heat sinks | IMECE2012-86669; IJHMT 55(25-26):7623–7634 | 10.1115/imece2012-86669; 10.1016/j.ijheatmasstransfer.2012.07.080 | 실리콘 마이크로갭, 갭 깊이 80~500 µm, 물 10 °C 서브쿨, G = 400~1000 kg/m²s, q ≤ 100 W/cm², 고속 영상 동시 | 주 기구는 갇힌 슬러그 비등과 환상류. 갭이 작을수록 h가 크다(IMECE 초록). IJHMT판은 최적 갭 범위(원문 미확인) | 0.3 mm 비등의 직접 비교 대상(갭별 h + 영상) | C+A / C |
| 12 | Kitagawa, Kobayashi, Denissenko, Murai (2023) | Natural convection heat transfer enhancement using bubble injection between vertical parallel plates | IJHMT 202:123658 | 10.1016/j.ijheatmasstransfer.2022.123658 | 수직 가열판 + 평행 유도판, 물, 기포 주입, 자연대류 | 기포 주입만으로 h가 3배 이상. 유도판을 더하면 최대 12% 추가(벽 수직 변동 속도는 줄었지만 벽 평행 평균 속도 증가). 벽 평행 평균 속도의 기여가 판이 있으면 최대 30% 커짐 | 판 간격이 기포 강화에 미치는 영향의 근거(자연대류) | C+A (Warwick 저장소 초록) |
| 13 | Narayanan, Lakehal (2008) | Two-phase convective heat transfer in miniature pipes under normal and microgravity conditions | J Heat Transfer 130(7):074502 | 10.1115/1.2909076 | 소직경관 비비등 기액 수치해석, 중력 방향 비교 | 기포·슬러그·슬러그 열이 물 단상보다 3~4배 열 수송. 기포가 막아 생기는 순환 흐름이 원인. 방향 영향 작음. **기포 빈도와 길이 척도 기반 기구 모델** 제시 | 영상 변수(빈도·길이) 기반 열전달 모델의 선례 | C+A |

### 1.2 비등: 3구역 모델과 액막 (0.1~1 mm 포함)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 14 | Thome, Dupont, Jacobi (2004); Dupont, Thome, Jacobi (2004) | Heat transfer model for evaporation in microchannels. Part I: presentation of the model / Part II: comparison with the database | IJHMT 47(14-16):3375–3385; 3387–3401 | 10.1016/j.ijheatmasstransfer.2004.01.006; 10.1016/j.ijheatmasstransfer.2004.01.007 | 원형 미세관 증발, 액체 슬러그–긴 기포(증발 막)–증기 슬러그 3구역의 시간 평균 h | 맞춤 매개변수 3개: 기포(핵생성) 빈도, 초기 막 두께(Moriyama & Inoue 식 × C_δ0), 건조 막 두께 δ_min(2차 인용 [19]). 원 모델은 이 셋에 강하게 의존(검색 요약). Part II: 1591점, 7유체, 67%가 ±30%(이전 세션 메모, 미확인) | 0.3~1 mm 비등의 기본 모델. 빈도·기포 길이·속도를 영상으로 대체할 수 있음 | C |
| 15 | Jacobi, Thome (2002) | Heat transfer model for evaporation of elongated bubble flows in microchannels | J Heat Transfer 124(6):1131–1136 | 10.1115/1.1517274 | 2구역 전신 모델 | 미세관 h가 건도에 거의 무관, 질량유속에 약하게, 열유속에 강하게 의존 → 긴 기포 밑 얇은 막 증발이 주 기구라는 가설로 설명 | 3구역 모델의 출발점 | C+A |
| 16 | Magnini, Thome (2017) | An updated three-zone heat transfer model for slug flow boiling in microchannels | IJMF 91:296–314 | 10.1016/j.ijmultiphaseflow.2017.01.015 | 수평 원형 미세관, 833점(R134a/R245fa/R236fa, d < 1 mm) | 기포 속도는 모세관 흐름 이론, 막 두께는 기포 근접 효과 포함, 건조 막 = 벽 거칠기, 액막 열관성·슬러그 내 순환 반영. 80% 이상이 ±30%. 원 모델보다 액체 슬러그 기여가 크고 막 증발 기여가 작다 | 맞춤 매개변수를 물리 모델로 바꾼 갱신판. 영상으로 기포 속도·길이를 주면 검증 가능 | C+A (EPFL 메타데이터 초록) |
| 17 | Consolini, Thome (2010) | A heat transfer model for evaporation of coalescing bubbles in micro-channel flow | IJHFF 31(1):115–125 | 10.1016/j.ijheatfluidflow.2009.10.005 | 갇힌 합체 기포류의 1차원 모델 | 합체로 기포-슬러그 쌍의 통과 빈도가 줄고 액체가 재분배됨을 반영. 83%가 ±30%. 열유속 지수 0.74를 재현(막 증발이 지배) | **추적의 합체 이벤트 빈도를 직접 입력으로 쓸 수 있는 모델** | C+A (EPFL 메타데이터 초록) |
| 18 | Dupont, Thome (2004) | Evaporation in microchannels: influence of the channel diameter on heat transfer | ASME ICMM2004-2369, 461–468 | 10.1115/icmm2004-2369 | 3구역 모델로 직경 효과 분석 | 미세 영역에서 낮은 건도는 d가 작을수록 h 증가, 높은 건도는 감소. 슬러그 뒤에 주기적으로 남는 막 두께 때문 | 갭(직경) 효과를 막 두께로 설명한 예. 0.3/0.7/1 mm 비교의 틀 | C+A |
| 19 | Jain, Jayaramu, Gedupudi (2019) | Modeling of pressure drop and heat transfer for flow boiling in a mini/micro-channel of rectangular cross-section | IJHMT 140:1029–1054 (arXiv:1902.00264) | 10.1016/j.ijheatmasstransfer.2019.05.089 | 직사각 미세채널 5구역 모델(부분 갇힘·완전 갇힘·건조 포함), 물 | 초기 막 δ/D_h = C_δ·(3√(ν/(U·D_h)))^0.84·[(0.07·(ρD_hU²/σ)^0.41)^−8 + 0.1^−8]^(−1/8), h = k/δ. C_δ: Thome 0.29(냉매, 수 µm), Wang 0.8117(물, D_h 0.137 mm, 1~2 µm), 이 연구 3.48(물, D_h 0.324·0.658 mm, 10~30 µm). Sun 외 물 실측 25·31 µm, 건조 2~3 µm | 막 두께 계수가 연구마다 10배 차이 → 영상 측정으로 다른 입력을 고정하면 C_δ를 물리적으로 좁힐 수 있음 | C+F (arXiv 원문; 학술지판은 C) |
| 20 | Moriyama, Inoue (1996) | Thickness of the liquid film formed by a growing bubble in a narrow gap between two horizontal plates | J Heat Transfer 118(1):132–139 | 10.1115/1.2824026 | **두 수평 평판** 사이 갭 0.1~0.4 mm, 성장하는 납작한 기포, 고속 사진 | 막 두께는 Bond 수(계면 가속도 기반) > 2이면 점성 경계층 두께, < 2이면 Ca가 지배 | 0.3 mm 수평 갭 비등 막 두께의 직접 근거. 3구역 모델의 막 식 원전 | C+A |
| 21 | Zhang, Utaka (2015) | Characteristics of a liquid microlayer formed by a confined vapor bubble in micro gap boiling between two parallel plates | IJHMT 84:475–485 | 10.1016/j.ijheatmasstransfer.2015.01.013 | 평행 석영판 갭 s = 0.15/0.30/0.50 mm, 물·에탄올·톨루엔·HFE7200, 레이저 소광법, VOF | 초기 마이크로층 δ0는 갭과 기포 앞끝 속도가 주로 정함. 저속은 속도와 함께 증가, 고속은 약간 감소(점성 경계층). δ0 최대 약 50 µm(0.5 mm), 30 µm(0.15 mm). 상관식 δ0/s = {[0.32Ca^0.95We^0.45Bo^−0.5]^−3 + [0.44Ca^0.53We^0.03Bo^−0.5]^−3}^(−1/3) | 0.3 mm 갭 비등 막 두께를 바로 줄 수 있는 상관식 | C+F (YNU 저장소 원고) |
| 22 | Utaka, Okuda, Tasaki (2009) | Configuration of the micro-layer and characteristics of heat transfer in a narrow gap mini/micro-channel boiling system | IJHMT 52(9-10):2205–2214 | 10.1016/j.ijheatmasstransfer.2008.11.020 | 좁은 갭 미니/마이크로 채널 비등, 레이저 소광 | (원문 미확인) 마이크로층 형상과 열전달 관계 | 좁은 갭에서 막 증발 기여를 잰 계열 | C |
| 23 | Han, Shikazono (2009); Youn, Muramatsu, Han, Shikazono (2015) | Measurement of the liquid film thickness in micro tube slug flow; The effect of initial flow velocity on the liquid film thickness in micro tube accelerated slug flow | IJHFF 30(5):842–853; IJMF 73:108–117 | 10.1016/j.ijheatfluidflow.2009.02.019; 10.1016/j.ijmultiphaseflow.2015.03.006 | 단열 슬러그류, 관경 0.3/0.5/0.7/1.0/1.3 mm, 레이저 초점 변위계 | 작은 Ca에서 막은 Ca만으로 정해지고, Ca가 크면 관성 영향. Ca, Re, We 상관식(2차 인용 [21]). 가속 흐름은 경계층이 막 두께를 제한 | 0.3~1 mm 막 두께(단열·비등 공통) | C |
| 24 | Han, Shikazono, Kasagi (2012) | The effect of liquid film evaporation on flow boiling heat transfer in a micro tube | IJHMT 55(4):547–555 | 10.1016/j.ijheatmasstransfer.2011.11.005 | 미세관 흐름 비등, 막 두께 측정 + 열전달 | (원문 미확인) 막 증발과 h의 관계 | "잰 막 두께 → h" 연결의 선례 | C |
| 25 | Revellin, Dupont, Ursenbacher, Thome, Zun (2006); Agostini, Revellin, Thome (2008); Arcanjo, Tibiriçá, Ribatski (2010) | Characterization of diabatic two-phase flows in microchannels…R-134a in a 0.5 mm channel; Elongated bubbles in microchannels. Part I…bubble velocity; Evaluation of flow patterns and elongated bubble characteristics… | IJMF 32(7):755–774; IJMF 34(6):590–601; ETFS 34(6):766–775 | 10.1016/j.ijmultiphaseflow.2006.02.016; 10.1016/j.ijmultiphaseflow.2007.07.007; 10.1016/j.expthermflusci.2010.01.006 | 미세관 비등의 기포 빈도·길이·속도 광학(레이저-포토다이오드) 또는 고속 영상 측정 | (원문 미확인) 3구역 모델 입력(빈도·길이·속도)을 광학으로 잰 대표 연구 | Q1 "입력을 측정으로 바꾼 연구"의 예. 다만 h와 결합한 정량 검증은 미확인 | C |
| 26 | Harirchian, Garimella (2009, 2012) | The critical role of channel cross-sectional area in microchannel flow boiling heat transfer; Flow regime-based modeling of heat transfer and pressure drop in microchannel flow boiling | IJMF 35(10):904–913; IJHMT 55(4):1246–1260 | 10.1016/j.ijmultiphaseflow.2009.06.005; 10.1016/j.ijheatmasstransfer.2011.09.024 | 미세채널(폭·깊이 변화), 고속 영상으로 유동 양식 판별 | (원문 미확인) 단면적이 비등 기구를 가른다. 영상으로 정한 유동 양식별 모델 선택 | 갭(단면) 크기 → 기구 전환 → 모델 전환의 틀. Purdue e-Pubs 공개본 있음(미열람) | C |
| 27 | Lee, Lee (2001) | Heat transfer correlation for boiling flows in small rectangular horizontal channels with low aspect ratios | IJMF 27(12):2043–2062 | 10.1016/s0301-9322(01)00054-4 | 수평 직사각 소형 채널(높이 0.4~2 mm급), 비등 | 낮은 질량유속·작은 갭에서는 열전달이 액막 두께에 지배됨(이전 세션 검색 요약) | 수평 좁은 갭 비등 상관식 | C |
| 28 | Bar-Cohen, Rahim (2007); Bar-Cohen, Sheehan, Rahim (2011) | Modeling and prediction of two-phase refrigerant flow regimes and heat transfer characteristics in microgap channels; Two-phase thermal transport in microgap channels—theory, experimental results, and predictive relations | ASME ICNMM2007-30216; Microgravity Sci Technol 24(1):1–15 | 10.1115/icnmm2007-30216; 10.1007/s12217-011-9284-3 | 마이크로갭 냉매·유전액 비등 자료 정리 | Taitel–Dukler 지도 적용 시 환상류 지배. 낮은 건도 환상류 h는 미세관 상관식으로 예측, 건도 증가 시 감소 구간 전환이 빨리 옴(초록 기준) | 마이크로갭 비등의 유동 양식 기반 해석 | C+A / C |
| 29 | Ishibashi, Nishikawa (1969) | Saturated boiling heat transfer in narrow spaces | IJHMT 12(8):863–893 | 10.1016/0017-9310(69)90153-7 | 수직 환형 좁은 공간 포화 비등 | (주제 2 담당) 고립 기포 / 합체 기포 영역. Monde [3]이 비교에 쓴 계산식 h̄ΔR/λ = 0.800(ΔR²/aT0)^(2/3)(2차 인용 [3]) | 좁은 갭 비등 고전. 짧게만 다룸 | C |

### 1.3 비등: 열유속 분배 모델과 영상·IR 입력
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 30 | Kurul, Podowski (1990) | Multidimensional effects in forced convection subcooled boiling | Proc. 9th IHTC, 21–26 | 10.1615/ihtc9.40 | 서브쿨 흐름 비등 다차원 모델 | (원문 미확인) 벽 열유속 = 대류 + 급랭(quenching) + 증발의 분배 모델 | 3·7 mm 핵비등 분배의 원형. 입력 N_a, f, D_d | C |
| 31 | Mikic, Rohsenow (1969) | A new correlation of pool-boiling data including the effect of heating surface characteristics | J Heat Transfer 91(2):245–250 | 10.1115/1.3580136 | 풀 비등 | (원문 미확인) 기포 이탈 뒤 영향 면적의 비정상 전도(급랭) 항 — 표면 갱신과 같은 √(kρc·f) 꼴 | 비등의 "통과 빈도 → h" 항의 원형. Monde [3]과 같은 물리 | C |
| 32 | Del Valle, Kenning (1985) | Subcooled flow boiling at high heat flux | IJHMT 28(10):1907–1920 | 10.1016/0017-9310(85)90213-3 | 서브쿨 흐름 비등, 고속 사진 | (원문 미확인) 사진으로 잰 핵생성 밀도·기포 크기·수명을 분배 모델에 넣은 초기 연구 | "영상 측정값 → 분배 모델"의 고전 | C |
| 33 | Basu, Warrier, Dhir (2005) | Wall heat flux partitioning during subcooled flow boiling: Part 1—model development; Part II—model validation | J Heat Transfer 127(2):131–140; 141–148 | 10.1115/1.1842784; 10.1115/1.1842785 | 수직 상향 서브쿨 흐름 비등, 1.03~3.2 bar, G = 124~926 kg/m²s, q = 2.5~90 W/cm², 접촉각 30~90° | 모든 열이 먼저 과열 액층으로 간다고 보고, 강제대류·비정상 전도·증기 생성을 핵생성 밀도, 이탈·부상 직경, 방출 빈도로 정량화. 높은 과열도에서 비정상 전도가 지배. 수직 상향에만 적용(초록 기준) | 입력이 영상 측정 대상. 수평 아래 가열에는 그대로 못 씀 | C+A |
| 34 | Gilman, Baglietto (2017) | A self-consistent, physics-based boiling heat transfer modeling framework for use in computational fluid dynamics | IJMF 95:35–53 | 10.1016/j.ijmultiphaseflow.2017.04.018 | CFD용 분배 모델 | (원문 미확인) 미끄럼 기포, 핵생성 사이트 상호작용 포함(Kommajosyula [35]가 확장) | 최신 분배 모델 | C |
| 35 | Kommajosyula (2020) | Development and assessment of a physics-based model for subcooled flow boiling with application to CFD | MIT PhD thesis (DSpace handle 1721.1/129051) | DOI 없음 | Gilman & Baglietto 확장 | 미끄럼 기포·사이트 상호작용·마이크로층 증발 추가, 이탈 직경·빈도 모델. 비등 곡선 80% 이상을 20% 안(검색 요약 기준) | 분배 모델 최신판 | U |
| 36 | Richenderfer, Kossolapov, Seong, … Bucci (2018) | Investigation of subcooled flow boiling and CHF using high-resolution diagnostics | ETFS 99:35–58 | 10.1016/j.expthermflusci.2018.07.017 | 직사각 채널 3×1 cm², 물, 1 atm, 10 K 서브쿨, G = 500/750/1000 kg/m²s. 고속 영상 + 고속 IR 동기 | 핵생성 밀도·성장/대기 시간·이탈 직경을 CHF까지 측정. 분배 항을 직접 추정. 마이크로층 증발 기여는 열유속과 함께 커지지만 CHF 직전에도 50%를 겨우 넘음(초록 기준) | "영상·IR 측정 → 분배 모델 검증"의 최신 표준. 투명 가열체(ITO) 필요 → 철 블록에는 못 씀 | C+A |
| 37 | Gerardi, Buongiorno, Hu, McKrell (2010) | Study of bubble growth in water pool boiling through synchronized, infrared thermometry and high-speed video | IJHMT 53(19-20):4185–4192 | 10.1016/j.ijheatmasstransfer.2010.05.041 | 풀 비등, IR + 고속 영상 동기 | (원문 미확인) 동기 측정 방법의 예 | Q3 동기 측정 사례 | C |

### 1.4 미끄러지는 기포의 열전달
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 38 | Cornwell (1990); Houston, Cornwell (1996) | The influence of bubbly flow on boiling from a tube in a bundle; Heat transfer to sliding bubbles on a tube under evaporating and non-evaporating conditions | IJHMT 33(12):2579–2584; 39(1):211–214 | 10.1016/0017-9310(90)90193-x; 10.1016/s0017-9310(96)85017-4 | 관군 비등, 관 표면을 미끄러지는 기포(증발·비증발 비교) | (원문 미확인) 미끄럼 기포 밑 막 증발과 기포 교란이 관군 비등 h를 지배한다는 계열 | 증발/비증발(공기) 미끄럼 기포 비교의 선례 | C |
| 39 | Thorncroft, Klausner (1999) | The influence of vapor bubble sliding on forced convection boiling heat transfer | J Heat Transfer 121(1):73–79 | 10.1115/1.2825969 | FC-87 수직 상향·하향 흐름 비등 + 단상 상향류에 공기 주입 | 상향류(기포가 벽에 붙어 미끄러짐)가 하향류보다 h가 크게 높음. 공기 주입 실험은 미끄럼 기포가 벽 근처 난류를 키워 거시 열전달에 크게 기여함을 시사(초록 기준) | 공기 주입으로 비등 기구 일부를 분리한 방법 — 사용자 실험 설계에 참고 | C+A |
| 40 | Bayazit, Hollingsworth, Witte (2003) | Heat transfer enhancement caused by sliding bubbles | J Heat Transfer 125(3):503–509 | 10.1115/1.1565090 | 기울어진 얇은 박(아래면 FC-87), 윗면 액정, 카메라 2대(액정 + 기포) | 미끄럼 기포 밑 마이크로층과 후류가 모두 국소 h에 크게 기여. 추정 마이크로층 40~50 µm(12°)(초록 기준) | 영상-벽 온도 동기 방법(Q3) | C+A |
| 41 | Hollingsworth, Witte, Figueroa (2009) | Enhancement of heat transfer behind sliding bubbles | J Heat Transfer 131(12):121005 | 10.1115/1.3216039 | 기울어진 얇은 박 + 액정 카메라 + 기포 카메라(아래) | 후류 h 최대 약 2500 W/m²K(뾰족한 분포). 최대 냉각점은 기포 길이와, 최대 h 위치는 기포 폭과 상관. 기포 폭 기준 Nu는 포화값에 도달(초록 기준) | 기포 크기(영상) → 후류 h. 큰 기포에서 h가 떨어지는 크기 의존 | C+A |
| 42 | Kenning, Kao (1972) | Convective heat transfer to water containing bubbles: enhancement not dependent on thermocapillarity | IJHMT 15(9):1709–1717 | 10.1016/0017-9310(72)90099-3 | 기포를 포함한 물의 대류 열전달 | (원문 미확인) 기포에 의한 강화가 열모세관 효과에 의존하지 않음 | 비비등 기포 강화의 고전 | C |
| 43 | Donnelly, O'Reilly Meehan, Nolan, Murray (2015) | The dynamics of sliding air bubbles and the effects on surface heat transfer | IJHMT 91:532–542 | 10.1016/j.ijheatmasstransfer.2015.07.133 | 기울어진 가열면 밑 미끄럼 공기 기포 | (원문 미확인) 공기 기포 동역학과 표면 열전달(열화상) | 공기 기포 후류 강화 | C |
| 44 | Yoo, Estrada-Perez, Hassan (2016) | Experimental study on bubble dynamics and wall heat transfer arising from a single nucleation site at subcooled flow boiling conditions – Part 2 | IJMF 84:292–314 | 10.1016/j.ijmultiphaseflow.2016.04.019 | 단일 핵생성 사이트, 서브쿨 흐름 비등 | (원문 미확인) 미끄럼 기포 특성과 벽 열전달 | 미끄럼 기포 영향 면적 | C |

### 1.5 비비등 기액 열전달 상관식 (관 중심)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 45 | Ghajar (2004 ENCIT 강연; 2005 학술지판) | Non-boiling heat transfer in gas-liquid flow in pipes – a tutorial | ENCIT 2004 CIT04-IL10 (abcm.org.br 공개); J Braz Soc Mech Sci Eng 27(1):46–73 | 10.1590/s1678-58782005000100004 | 비비등 기액 열전달 상관식 총정리 | Kim 외(2000) 일반식 h_TP = (1−α)·h_L·[1 + C(x/(1−x))^m(α/(1−α))^n(Pr_G/Pr_L)^p(μ_G/μ_L)^q], h_L은 Sieder–Tate + 현장 액체 Re_L = 4ṁ_L/(π√(1−α)μ_L D). 수직 255점: C = 0.27, m = −0.04, n = 1.21, p = 0.66, q = −0.72, 96%가 ±30%. 권장 상관식의 공통 변수는 Re_SL, Pr_L, μ_B/μ_W와 **기공률 α 또는 u_SG/u_SL** | α가 입력 → 영상 기공률(부피 보정 후)을 직접 넣을 수 있음. (1−α)와 √(1−α)가 "액체 가속"을 표현 | C+F (ENCIT 원문; 학술지판 DOI는 Crossref 대조) |
| 46 | Kim, Ghajar (2002) | Heat transfer measurements and correlations for air–water flow of different flow patterns in a horizontal pipe | ETFS 25(8):659–676 | 10.1016/s0894-1777(01)00120-0 | 수평 25.4 mm 스테인리스관, L/D = 100, 공기-물, 150점, Re_SL 636~35503 | 유동 양식별 상수: 슬러그·기포/슬러그·기포/슬러그/환상(89점) C = 2.86, m = 0.42, n = 0.35, p = 0.66, q = −0.72. 93%가 ±20%. 원주 방향 벽 온도 차가 커서 둘레 평균 h를 씀. 낮은 유량(층상·플러그)은 건조·국소 비등 위험으로 자료 없음 [45] | 수평 기액 h의 기준 자료. 위/아래 비대칭의 증거. 저유량 플러그 영역은 공백 | C (내용은 [45] 원문으로 확인) |
| 47 | Kim, Ghajar (2006); Tang, Ghajar (2007) | A general heat transfer correlation for non-boiling gas–liquid flow with different flow patterns in horizontal pipes; Validation of a general heat transfer correlation for non-boiling two-phase flow with different flow patterns and pipe inclination angles | IJMF 32(4):447–465; ASME HT2007-32219 | 10.1016/j.ijmultiphaseflow.2006.01.002; 10.1115/ht2007-32219 | 수평·약간 기운 관, 공기-물. 2007: 27.9 mm 스테인리스관, 763점, q = 1800~10900 W/m² | 2006: 유동 양식 인자(= **유효 젖음 둘레**)를 상관식에 도입(검색 요약 기준, 식 미확인). 2007: 여러 기공률 상관식으로 바꿔 넣어 성능 비교(초록 기준) | "가열면 젖음 비율"을 상관식 변수로 쓴 선례 → 영상 접촉 면적 비율과 직접 대응 | C / C+A |
| 48 | Shah (1981); Shah (2018) | Generalized prediction of heat transfer during two component gas-liquid flow in tubes and other channels; General correlation for heat transfer during two-component gas-liquid flow in horizontal pipes; A correlation… in vertical channels | AIChE Symp Ser 77(208):140–151; ASME IMECE2018-86589, -86590 | 1981: DOI 없음; 10.1115/imece2018-86589; 10.1115/imece2018-86590 | 1981: 여러 유체, 수평·수직. 2018 수평: d 4.3~57 mm, 946점·18출처. 2018 수직: 직사각 채널 포함 1022점·19출처 | 1981: h_TP/h_L = (1 + u_SG/u_SL)^(1/4), 층류 기준 Re 170([45] 원문). 2018: 수평 MAD 19.2%, 수직 MAD 18.1%(초록 기준) | 직사각 채널 자료를 포함한 가장 넓은 상관식. 기준선 비교용 | 1981 U(서지는 [45]에서), 2018 C+A |
| 49 | Kim, Ghajar, Dougherty, Ryali (1999); Ghajar, Tang (2010) | Comparison of 20 two-phase heat transfer correlations with seven sets of experimental data…; Importance of non-boiling two-phase flow heat transfer in pipes for industrial applications | HTE 20(1):15–40; HTE 31(9):711–732 | 10.1080/014576399271691; 10.1080/01457630903500833 | 상관식 비교·검토 | (원문 미확인) | 상관식 선택 근거 | C |
| 50 | Dong, Hibiki (2018) | Heat transfer correlation for two-component two-phase slug flow in horizontal pipes | Appl Therm Eng 141:866–876 (정정 143:909) | 10.1016/j.applthermaleng.2018.06.029 | 수평관 슬러그류 비비등 | (원문 미확인) 슬러그류 전용 h 상관식 | 수평 슬러그의 비교 기준 | C |
| 51 | Hetsroni, Hu, Yi, Mosyak, Yarin, Ziskind (1998) | Heat transfer in intermittent air–water flows—Part I (horizontal) / Part II (upward inclined) | IJMF 24(2):165–188; 189–212 | 10.1016/s0301-9322(97)00055-4; 10.1016/s0301-9322(97)00056-6 | 49.2 mm 관, 가열 벽 IR 열화상(온도장 가시화 + 국소 벽 온도), Part II 2°·5° | Part II: 액·기체 Froude 수와 **무차원 기포 출현 빈도**가 좋은 상관 변수(검색 요약 기준). Part I 내용 미확인 | 빈도(영상 변수)로 간헐류 h를 정리한 선례. IR 벽 온도 | C |
| 52 | Sato, Sadatomi, Sekoguchi (1981) | Momentum and heat transfer in two-phase bubble flow—I. Theory / II | IJMF 7(2):167–177; 179–190 | 10.1016/0301-9322(81)90003-3; 10.1016/0301-9322(81)90004-5 | 기포류 운동량·열전달 이론 | (원문 미확인) 기포 유도 난류 확산을 더한 모델 | 7 mm 기포류(벽에 안 닿는 기포)의 교란 항 | C |

### 1.6 Taylor 흐름 열전달 (비비등, 0.1~2 mm)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 53 | Walsh, Walsh, Muzychka (2010) | Heat transfer model for gas–liquid slug flows under constant flux | IJHMT 53(15-16):3193–3201 | 10.1016/j.ijheatmasstransfer.2010.03.007 | 미니채널, 등열유속, 국소 Nu를 IR 열화상으로 측정(입구·완전발달) | 최적 슬러그 형상이면 최대 한 자릿수(약 10배) 강화. 물리에 근거한 열전달 모델 제시(초록 기준) | 0.3~1 mm 공기 주입의 핵심 모델 후보. 영상 변수 = 슬러그 길이 | C+A (UL Pure 초록) |
| 54 | Muzychka, Walsh, Walsh (2011) | Heat transfer enhancement using laminar gas-liquid segmented plug flows | J Heat Transfer 133(4):041902 | 10.1115/1.4002807 | 층류 분절 흐름, 등온 벽 | 액체 플러그 내부 순환이 유효 열 길이를 줄여 강화. 축척한 Graetz 이론 모델, 무차원 관 길이 L* < 0.1에서 유효(초록 기준) | 슬러그 길이(영상) → Graetz형 h. 0.3~1 mm 층류에 맞음 | C+A |
| 55 | Howard, Walsh, Walsh (2011) | Prandtl and capillary effects on heat transfer performance within laminar liquid–gas slug flows | IJHMT 54(21-22):4752–4761 | 10.1016/j.ijheatmasstransfer.2011.05.029 | 층류 슬러그류, Pr·Ca 영향 | (원문 미확인) | 물(Pr 7)과 다른 유체 비교 | C |
| 56 | Leung, Liu, Fletcher, Haynes (2010); Leung, Gupta, Fletcher, Haynes (2011, 2012) | Heat transfer in well-characterised Taylor flow; Effect of flow characteristics on Taylor flow heat transfer; Gravitational effect on Taylor flow in horizontal microchannels | CES 65(24):6379–6388; IECR 51(4):2010–2020; CES 69(1):553–564 | 10.1016/j.ces.2010.09.014; 10.1021/ie200610k; 10.1016/j.ces.2011.11.016 | 미세채널 Taylor 흐름, 슬러그·기포 길이를 잰 실험. 수평 미세채널의 중력 효과 | (원문·초록 미확인) | 수평 미세채널에서 중력이 막·기포를 비대칭으로 만드는지(아래 가열 해석에 필요) | C |
| 57 | Asadolahi, Gupta, Leung, Fletcher, Haynes (2012); Dai, Guo, Fletcher, Haynes (2015) | Validation of a CFD model of Taylor flow hydrodynamics and heat transfer; Taylor flow heat transfer in microchannels—Unification of liquid–liquid and gas–liquid results | CES 69(1):541–552; CES 138:140–152 | 10.1016/j.ces.2011.11.017; 10.1016/j.ces.2015.08.012 | CFD 검증, 액-액·기-액 통합 상관 | (원문 미확인) | 슬러그 길이·기공률로 Nu를 통합하는 상관식 후보 | C |
| 58 | Bandara, Nguyen, Rosengarten (2015) | Slug flow heat transfer without phase change in microchannels: A review | CES 126:283–295 | 10.1016/j.ces.2014.12.007 | 리뷰 | 내부 순환으로 열전달이 크게 증가. 보고된 상관식 사이 Nu가 500% 넘게 엇갈림 — 흐름 조건 기술 부족 탓(검색 요약 기준) | **영상으로 슬러그 길이·빈도를 같이 보고하면 이 엇갈림을 줄일 수 있다**는 논거 | C |
| 59 | Betz, Attinger (2010) | Can segmented flow enhance heat transfer in microchannel heat sinks? | IJHMT 53(19-20):3683–3691 | 10.1016/j.ijheatmasstransfer.2010.04.016 | 500 µm 정사각 미세채널 7개, T 접합 주기적 공기 주입, 물 | 액체 질량유속 330~2000 kg/m²s 범위에서만 층류 Nu가 100% 넘게 증가(검색 요약 기준) | 0.3~0.7 mm 공기 주입 강화의 크기와 조건 의존 | C |
| 60 | Mehta, Khandekar (2014) | Measurement of local heat transfer coefficient during gas–liquid Taylor bubble train flow by infra-red thermography | IJHFF 45:41–52 | 10.1016/j.ijheatfluidflow.2013.12.001 | 정사각 미니채널, IR 열화상 + 흐름 가시화 | (원문 미확인) | 국소 h와 기포열 동기 측정 예 | C |

### 1.7 기포 주입 강화와 표면 갱신 모델
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 61 | Kitagawa, Denissenko, Murai (2017) | Effect of heated wall inclination on natural convection heat transfer in water with near-wall injection of millimeter-sized bubbles | IJHMT 113:1200–1211 | 10.1016/j.ijheatmasstransfer.2017.06.009 | 가열 벽 0~40°(수직 기준), 벽 근처 mm 기포 주입, 속도·온도 측정 | h 최대 한 자릿수 증가. 강화 비는 벽 기울기와 함께 증가. 기구: ① 기포 구동 벽 평행 흐름이 찬 액체를 열경계층으로 운반, ② 벽 수직 혼합(기포 상승·와류 방출·경계층 와류)(초록 기준) | 기포가 가열 벽 쪽으로 붙을수록 강화가 큼 → 수평 아래 가열에서 기포가 위로 뜨는 7 mm는 불리 | C+A (Warwick 저장소 초록) |
| 62 | Kitagawa 외 (2008, 2010); Kitagawa, Murai (2013); Tokuhiro, Lykoudis (1994) | Heat transfer enhancement for laminar natural convection along a vertical plate due to sub-millimeter-bubble injection; Experimental study on turbulent natural convection… with sub-millimeter-bubble injection; Natural convection heat transfer from a vertical heated plate in water with microbubble injection; Natural convection heat transfer from a vertical plate—I. Enhancement with gas injection | Exp Fluids 45(3):473–484; 49(3):613–622; CES 99:215–224; IJHMT 37(6):997–1003 | 10.1007/s00348-008-0490-8; 10.1007/s00348-010-0838-8; 10.1016/j.ces.2013.05.027; 10.1016/0017-9310(94)90224-0 | 수직 가열판 + 기포 주입(자연대류) | (원문 미확인) 기포 주입 강화의 계열 | 기포 크기·수 밀도(영상 변수) 의존성의 선례 | C |
| 63 | Gvozdić, Alméras, Mathai, Zhu, van Gils, Verzicco, Huisman, Sun, Lohse (2018) | Experimental investigation of heat transport in homogeneous bubbly flow | JFM 845:226–244 | 10.1017/jfm.2018.213 | 수직 채널 균일 기포류(측벽 가열) | (원문 미확인) 기공률에 따른 열 수송 증가 | 7 mm에서 기포류가 벽 열전달에 주는 효과의 상한 감 | C |
| 64 | Deckwer (1980) | On the mechanism of heat transfer in bubble column reactors | CES 35(6):1341–1346 | 10.1016/0009-2509(80)85127-x | 기포탑 벽 열전달 | (원문 미확인) 표면 갱신 + 등방 난류(Kolmogorov) 접촉 시간 모델 | 표면 갱신 모델을 기포류 벽 열전달에 쓴 대표 예 | C |
| 65 | Higbie (1935); Danckwerts (1951) | The rate of absorption of a pure gas into a still liquid during short periods of exposure; Significance of liquid-film coefficients in gas absorption | Trans AIChE 31:365–389; Ind Eng Chem 43(6):1460–1467 | Higbie DOI 없음; 10.1021/ie50498a055 | 표면 갱신 이론 | 접촉 시간 t의 비정상 전도: 시간 평균 계수 = 2√(D/(πt))(열은 2k/√(παt)). 같은 꼴이 [3]의 등온 극한 h̄√(aT0)/λ = 2/√π로 확인됨 | 통과 빈도 f → h = 2k√f/√(πα). 물 20 °C에서 h ≈ 1.78 kW/m²K × √(f/Hz) | Higbie U, Danckwerts C |

### 1.8 수평 흐름·젖음 둘레(건조각)를 넣은 열전달 모델
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 66 | Kattan, Thome, Favrat (1998) | Flow boiling in horizontal tubes: Part 3—Development of a new heat transfer model based on flow pattern | J Heat Transfer 120(1):156–165 | 10.1115/1.2830039 | 수평관 흐름 비등 | (원문 미확인) 건조각으로 둘레를 젖은 부분·마른 부분으로 나누어 h를 가중 평균하는 유동 양식 기반 모델 | "가열면 덮음 비율 → h 가중 평균"의 원형 | C |
| 67 | Ursenbacher, Wojtan, Thome (2004); Wojtan, Ursenbacher, Thome (2005) | Interfacial measurements in stratified types of flow. Part I: new optical measurement technique and dry angle measurements; Investigation of flow boiling in horizontal tubes: Part I (diabatic flow pattern map) / Part II (heat transfer model for stratified-wavy, dryout and mist) | IJMF 30(2):107–124; IJHMT 48(14):2955–2969; 2970–2985 | 10.1016/j.ijmultiphaseflow.2003.11.010; 10.1016/j.ijheatmasstransfer.2004.12.012; 10.1016/j.ijheatmasstransfer.2004.12.013 | 수평관, 광학(영상)으로 건조각 측정 → 열전달 모델 | (원문 미확인) **광학으로 잰 건조각을 열전달 모델에 넣은 선례**(이전 세션 메모·검색 요약) | Q4·Q1의 "영상 측정 → 모델 입력" 직접 선례. 사용자의 접촉 면적 비율과 같은 역할 | C |

### 1.9 벽 온도 측정과 영상 동기화
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 68 | Sheehan, Kim, Bar-Cohen (2009) | Thermal imaging of two-phase cooled microgap channel wall | ASME InterPACK2009-89238, 491–499 | 10.1115/interpack2009-89238 | 마이크로갭 260 µm × 30 mm × 34 mm, 반대쪽 사파이어 창으로 가열면 IR 촬영, FC-72 | IR 반사·흡수 보정. q = 3.2 W/cm², G = 35 kg/m²s에서 가열면 온도 변동 최대 약 20 K(국소 건조 증거 가능)(초록 기준) | **투명 덮개 너머 가열면 IR** — 사용자 장치(위 덮개)와 같은 배치. 철 블록 표면 IR이면 방사율 보정 필요 | C+A |
| 69 | Kim, Kommer, Dessiatoun, Kim (2012) | Measurement of two-phase flow and heat transfer parameters using infrared thermometry | IJMF 40:56–67 | 10.1016/j.ijmultiphaseflow.2011.11.012 | IR 열측정으로 이상류 변수와 열전달 동시 측정 | (원문 미확인) | 동기 측정 방법 | C |
| 70 | Carslaw, Jaeger (1959) | Conduction of Heat in Solids, 2nd ed. | Oxford Univ. Press (책) | DOI 없음(ISBN 0198533683) | 주기 표면 온도의 반무한체 해 | 진폭 감쇠 exp(−z/δ), δ = √(α/(πf)) | 매립 열전대 응답 한계(Q3) | U (책, 식은 표준 결과) |

## 2. 핵심 질문에 대한 답

### Q1. 비등: 3구역 모델의 입력과 영상 측정으로 바꾼 연구
- 3구역 모델은 액체 슬러그–증발 막이 있는 긴 기포–증기 슬러그가 차례로 지나가는 동안의 h를 시간 평균한다 [14](C). 증발 막 구역의 국소 h = k/δ(t)이고, 막은 증발로 얇아진다 [19](C+F).
- 원 모델의 맞춤 매개변수는 세 개다: 기포 빈도, 초기 막 두께 계수 C_δ0, 건조 막 두께 δ_min [14, 19](C, 2차 인용).
  - 초기 막: Moriyama & Inoue(두 수평 평판 사이 0.1~0.4 mm 갭)의 식을 C_δ0로 보정 [20](C+A), [19](C+F).
  - C_δ0는 0.29(Thome, 냉매) → 0.8117(Wang, 물, D_h 0.137 mm) → 3.48(Jain 외, 물, D_h 0.32~0.66 mm)로 연구마다 크게 달랐다 [19](C+F).
  - 갱신판(Magnini & Thome 2017)은 기포 속도를 모세관 흐름 이론으로, δ_min을 벽 거칠기로 바꿔 맞춤을 줄였다 [16](C+A).
- **입력을 영상으로 바꾼 연구**
  - 기포 빈도·길이·속도를 광학으로 잰 연구는 많다 [25](C). 이 값으로 3구역 모델을 검증했는지는 원문을 못 봐 확인하지 못했다.
  - 막 두께를 직접 재고 h와 연결한 연구: Han, Shikazono, Kasagi(2012) [24](C), Utaka 계열(레이저 소광) [21, 22].
  - 좁은 갭에서 기포 통과 주기와 h를 직접 연결: Monde 계열 [1, 3, 4](C+F). 단 기포를 인위적으로 일정 주기로 넣었다.
  - 합체 기포 모델(Consolini & Thome) [17](C+A)은 통과 빈도 감소와 액체 재분배를 넣는다 → 추적의 합체 빈도를 입력으로 쓸 수 있다.
- **사용자 장치에 적용할 때**: 위에서 보는 영상은 막 두께를 못 잰다. 빈도 f, 기포 길이 L_b, 속도 u_b, 덮는 시간 L_b/u_b, 합체 빈도는 잰다. 막 두께는 상관식([20, 21, 23], 0.3 mm는 Zhang & Utaka가 가장 가깝다)으로 주고, C_δ0 하나만 남겨 다섯 갭에 공통으로 맞추는 것이 깨끗한 설계다.
- 열유속 분배(Kurul & Podowski, Basu, Gilman & Baglietto, Kommajosyula) [30, 33–35]의 입력(핵생성 밀도, 이탈 빈도·직경, 미끄럼 길이)은 Richenderfer 외처럼 투명 가열체 + IR이 있어야 제대로 잰다 [36](C+A). 위에서 보는 영상은 기포가 위 덮개 밑에 모이는 3·7 mm에서 핵생성 사이트를 가릴 수 있다. → 분배 모델은 7 mm의 "기준 비등" 비교용으로만 쓰는 것이 현실적이다.

### Q2. 비비등(공기 주입) 기액 열전달
- 관 상관식: Kim 외(2000)/Kim & Ghajar(2002) 일반식은 h_TP = (1−α)h_L[1 + …]이고 h_L에 현장 액체 Re(∝1/√(1−α))를 쓴다 [45, 46](C+F). Shah(1981)는 h_TP/h_L = (1 + u_SG/u_SL)^(1/4) [45](C+F, 원 논문 U). 권장 상관식의 공통 변수는 α 또는 u_SG/u_SL이다 [45].
- 수평에서는 원주 방향 벽 온도 차가 커서 둘레 평균 h를 쓴다 [45, 46](C+F). Kim & Ghajar(2006)는 유효 젖음 둘레를 인자로 넣었다 [47](C, 식 미확인).
- Taylor 흐름(0.1~2 mm): 액체 슬러그 내부 순환이 유효 열 길이를 줄인다 [54](C+A). 슬러그 형상에 따라 최대 약 10배 [53](C+A), 500 µm 채널에서 조건부 100% 이상 [59](C). 상관식끼리 Nu가 500% 넘게 엇갈린다 [58](C).
- 기포 주입 강화(자연대류): 3배 이상 [12], 기울기에 따라 최대 10배 [61](C+A). 기포가 가열 벽 쪽에 붙을수록 강화가 크다 [61].
- 표면 갱신: Higbie/Danckwerts [65]의 h = 2k/√(παt)를 좁은 갭 기포 통과에 쓴 것이 Monde 모델이다 [3](C+F). 기포 탑에서는 Deckwer가 같은 틀을 썼다 [64](C).
- **좁은 갭 공기 주입에서 h를 기포 통과 주기 하나로 정리한 실험**: Monde 외(1989), 2 mm, ΔTsub ≥ 40 K [2](C+F). 1.2~1.5 mm 수평에서 기포 직경과 빈도로 정리: Albahloul 외(2013) [8](C+A).

### Q3. 벽 온도와 고속 영상의 동기 측정, 열전대 응답 한계
- 동기 측정 사례는 모두 **얇은 가열체**(박 50 µm, ITO 막, 얇은 금속 박 + 액정/IR)를 쓴다 [1–5, 8, 36, 40, 41, 68](C+F/C+A). 얇아야 표면 온도가 기포에 따라 움직인다.
- 반무한체의 주기 온도 변동은 깊이 z에서 exp(−z/δ), δ = √(α/(πf))로 줄어든다 [70](U, 표준 해).
  - 탄소강(α = 1.36×10⁻⁵ m²/s): δ = 6.6 / 2.1 / 0.66 / 0.29 mm(0.1 / 1 / 10 / 50 Hz). 스테인리스 304: 3.6 / 1.1 / 0.35 / 0.16 mm(본 조사 계산, 메인 세션 추정과 같음).
  - 기포 통과(수~수십 Hz) 신호는 깊이 1~2 mm 열전대에서 수 % 이하로 준다.
- 얇은 박에서도 기포 통과에 따른 벽 온도 변동은 1 K 수준이다(ΔTw/qw = 1.65×10⁻⁴·T0^0.75 m²K/W, 물, 2 mm 갭) [4](C+F). 철 블록 표면은 열 활동도(√kρc ≈ 13600, 물 1580)가 커서 이보다 더 작다. 
- 같은 이유로 철 블록 가열면은 기포 한 번 지나가는 동안 **거의 등온**이다. 그러면 표면 갱신 식은 등열유속형(√π)보다 등온형(2/√π, Higbie)이 맞다. Monde 모델은 벽 열용량 변수 B2 = √((ρcλ)_s/(ρcλ)_l)·(δ_s/√(a_sT0))를 갖고 B2 → ∞가 등온 극한이다 [3](C+F).
- 결론: 이 장치로는 운전점마다 **시간 평균 h ↔ 시간 평균 영상 통계**로만 연결한다. 기포 단위 동기 해석이 필요하면 별도 얇은 박 가열 시험편 + IR(투명 덮개 너머, Sheehan 외처럼) [68]이 필요하다.

### Q4. 수평 + 아래 가열에서 기체가 위 벽에 모일 때의 바닥 h
- 갭별 기포-가열면 관계(메인 세션 추정 `estimates_microgap.md` 2·8장과 일치):
  - 0.3 / 0.7 / 1 mm: 갭보다 큰 기포는 모두 팬케이크로 양쪽 벽에 닿는다. 가열면과 기포 사이에 얇은 막(수평 강제 흐름의 Aussillous–Quéré 추정 0.3 mm 2~10 µm, 1 mm 5~32 µm; 수직 부력 상승 실측 56~70 µm [5]).
  - 3 mm: d > 3 mm 기포와 위 덮개 밑 웅덩이(두께 약 2Lc ≈ 5 mm)가 바닥에 닿는다.
  - 7 mm: 부력 기포는 바닥에 닿지 못한다. 웅덩이 밑 액층이 남는다.
- 문헌의 틀
  - 젖음 둘레 가중: 비등은 Kattan/Wojtan의 건조각 모델 [66, 67](C), 공기-물은 Kim & Ghajar의 유효 젖음 둘레 인자 [47](C). 건조각을 **광학으로 재서** 모델에 넣은 선례가 Ursenbacher/Wojtan이다 [67](C).
  - 액체 가속: Kim 외 일반식의 (1−α)와 현장 Re_L ∝ 1/√(1−α) [45](C+F). 난류 Dittus–Boelter에 실제 액체 속도를 넣으면 h ∝ (1−α)^−0.8(본 조사의 유도). 층류 완전발달 액층은 h ∝ 1/(액층 두께) ∝ 1/(1−α_local)(본 조사의 유도, 문헌 계수 미확인).
  - 상하 비대칭: 수평관은 원주 벽 온도 차가 크고, 저유량 층상·플러그 영역은 건조 위험 때문에 자료가 없다 [45, 46](C+F).
  - 가열 벽이 위인 미니채널(Albahloul, Ozer)은 부력이 기포를 가열면으로 민다 [8, 9]. 사용자 장치는 반대라서, 0.3~1 mm에서는 같은 접촉(갇힘 때문), 3·7 mm에서는 접촉이 줄어든다. 이 차이를 "갭에 따른 접촉 비율"로 정량화하는 것이 새로운 부분이다.
  - 기포가 가열 벽 쪽으로 기울수록 강화가 커진다(Kitagawa 2017) [61](C+A) → 7 mm 아래 가열은 기포 강화가 가장 작을 것이다.

### Q5. 갭이 바뀔 때 h 변화를 설명할 영상 변수 (핵심)
아래 표의 크기는 본 조사 계산(물 20 °C; 비등은 포화수 100 °C). 문헌 식의 확인 수준은 해당 문헌 번호를 따른다.

**(b) 공기 주입(수평, 아래 가열)**
| 기구 | 식(근거) | 필요한 영상 변수 | 0.3 mm | 0.7 mm | 1 mm | 3 mm | 7 mm |
|---|---|---|---|---|---|---|---|
| 단상 기준선(층류 완전발달, 한쪽 가열) | h0 = 5.385·k/D_h(Shah & London 값, 원문 미확인) | 없음 | 5.4 kW/m²K, 열 입구 길이 약 13 mm(0.1 m/s) → 거의 완전발달 | 2.3, 입구 약 70 mm | 1.6, 입구 약 140 mm | 0.54, 발달 중(실제 h는 더 큼) | 0.23, 발달 중; 1 m/s면 난류(Re 1.4만) |
| 표면 갱신(통과 빈도) | h_sr = 2k√f/√(πα)(등온; Higbie [65], Monde 극한 [3]). 물 20 °C: 1.78 kW/m²K·√(f/Hz). 등열유속이면 ×π/2 [3] | 가열면 한 점의 기포 통과 빈도 f(= 접촉 기포 투영 면적 비율 × u_b / L_b 근사), 접촉 면적 비율 φ_c | h_sr이 h0를 넘으려면 f > 9 Hz | f > 1.7 Hz | f > 0.8 Hz | f > 0.1 Hz(닿는 큰 기포만) | 해당 없음(바닥 접촉 없음) |
| 잔류막 + 갱신(Monde) | h̄√(aT0)/λ = F(x*/√(aT0)); 두꺼운 막 극한 h = k/x*(등열유속) [3] | T0 = 1/f, 덮는 시간 L_b/u_b; x*는 상관식 | x* 2~10 µm(AQ 추정) → 막 열시간 0.03~0.7 ms ≪ 덮는 시간 → 막이 금방 포화, 갱신 극한에 가까움 | x* 4~23 µm | x* 5~32 µm(수직 실측 56 µm [5]) | x* 15~97 µm | 해당 없음 |
| 가열면 덮음(단열) | h ≈ (1−φ_c)·h_wet + φ_c·h_under; 공기면 h_under ≪ h_wet(막이 ms 안에 포화)(본 조사 정리; 젖음 둘레 인자 [47], 건조각 모델 [66, 67]과 같은 꼴) | φ_c(바닥 접촉 면적 비율), 덮는 시간 분포 | φ_c ≈ 투영 기공률(모든 기포가 닿음) → 저빈도에서 h가 단상보다 **낮아질** 수 있음 | 같음 | 같음 | 일부(큰 기포·웅덩이) | ≈ 0 |
| Taylor 슬러그 순환 | Nu는 슬러그 길이 L_s에 의존(축척 Graetz, L* < 0.1) [54], 최적 형상 최대 10배 [53] | L_s, L_b, u_b, f | 적용(층류, 팬케이크가 갭을 채움) | 적용 | 적용 | 부분(갭 채우는 큰 기포만) | 미적용 |
| 액체 가속(얇아진 액층) | 난류 h ∝ (1−α)^−0.8, 층류 h ∝ 1/(1−α_local)(본 조사 유도); Kim 외 (1−α), 현장 Re [45] | 부피 기공률 α(투영 → 부피 보정, `estimates_microgap.md` 10장), 웅덩이 덮음 | 작음(막이 아주 얇아 액층 개념이 약함) | 작음 | 작음 | 중간 | **주 기구**: 웅덩이 덮음 30%면 +20~30%(메인 추정) |
| 기포 후류·교란 | 실험 상관(기포 직경·빈도 무차원군 [8]; 후류 h 최대 2.5 kW/m²K [41]; 자연대류 3~10배 [12, 61]) | 기포 직경 분포, 수 밀도, 슬립 속도 | 갭 채운 기포 뒤 혼합 [8, 9] | 같음 | 같음 | 혼합 | 위에 뜬 기포의 원거리 교란(작음) |

**(a) 비등(수평, 아래 가열)**
| 기구 | 식(근거) | 필요한 영상 변수 | 0.3 mm | 0.7 mm | 1 mm | 3 mm | 7 mm |
|---|---|---|---|---|---|---|---|
| 팬케이크 밑 막 증발(3구역) | h_film = k/δ(t), δ0 = 상관식 [19–21, 23]; 시간 평균은 f, L_b/u_b, 건조 시간 ρh_fgδ0/q [14, 16] | f, L_b, u_b, 합체 빈도(→ Consolini [17]) | δ0 작음(Zhang & Utaka 0.3 mm 실측 수~30 µm) → k/δ0 수십~수백 kW/m²K, 대신 건조가 빠름(δ0 = 5 µm면 100 kW/m²에서 108 ms) | 중간 | δ0 5~30 µm급 → 23~136 kW/m²K | 큰 기포 밑만 | 미적용 |
| 건조(부분 건조) | 건조 면적 비율 A_dry: h = (1−A_dry)h_wet + A_dry·h_v(건조각 모델과 같은 꼴 [66, 67]) | 덮는 시간 > 건조 시간인 기포 비율, (가능하면) 건조 패치의 밝기 | 0.2·0.5 mm에서 건도 따라 h 단조 감소(조기 부분 건조) [10](C+A) | 같은 경향 예상 | 1~2 mm는 관과 비슷 [10] | 작음 | 작음 |
| 통과 기포에 의한 갱신·혼합 | Monde 모델 [3], 포화 상한 h̄ = 2.3×10⁴λ(물 약 1.6×10⁴ W/m²K) [1, 4] | T0(= 1/f), 기포 길이 l | 적용 | 적용 | 적용 | **s = 2~7 mm에서 같은 l이면 h 차 ±15%** [1] | 적용(기포가 바닥을 쓸 때만) |
| 핵비등 + 분배 | q = q_fc + q_quench + q_evap [30, 33] | N_a, f_d, D_d, 미끄럼 길이(위에서 보이면) | 갇힘이 지배 | 갇힘 | 전이 | 혼합 | **주 기구**(Cooper 6~10 kW/m²K at 50~100 kW/m², 메인 추정) |

- 갭별 요약(가설): 0.3·0.7 mm는 "막 두께와 덮음/건조", 1·3 mm는 "통과 빈도(갱신)와 기포 길이", 7 mm는 "액체 가속(공기)과 핵비등(비등)"이 지배할 것이다. 한 장의 그림에 "기구별 기여 비율 vs 갭"을 그리는 것이 논문의 중심 그림 후보다.

### Q6. 새로움 판단
- 영상 통계 ↔ 측정 h를 연결한 연구는 있다.
  - 좁은 갭(수직, 1~7 mm)에서 **인위적으로 넣은 기포열**의 주기·길이 ↔ h: Monde 계열 [1–5](C+F). 갭 2~7 mm 비교까지 했다.
  - 수평 미니채널(1.2~1.5 mm, 위 가열)에서 고속 영상의 기포 직경·빈도 ↔ Nu: Albahloul 외 [8](C+A).
  - 미세관 비등의 광학 빈도 측정 [25], 마이크로갭 비등의 영상 + h(갭 80~500 µm) [11], 간헐류의 기포 출현 빈도 ↔ h(IR) [51].
- 찾지 못한 것(4장 검색 기록 근거):
  - 자연 발생 기포류에서 **자동 검출·추적**으로 얻은 통계(접촉 면적 비율, 통과 빈도, 슬러그 길이, 합체 빈도)를 측정 h와 기구 모델로 연결한 연구.
  - 0.3~7 mm처럼 갇힘(Co ≈ 9)부터 자유(Co ≈ 0.4)까지 한 장치에서 가로지르는 갭 비교 + 아래 가열 + 불투명 금속 가열면.
  - 공기 주입과 비등을 같은 장치·같은 영상 지표로 비교한 좁은 갭 연구(Albahloul [8]이 가장 가깝지만 한 갭, 위 가열).
- 따라서 새로움은 "영상 통계 ↔ h" 자체가 아니라, **(i) 갭이 기구를 바꾸는 범위 전체, (ii) 자동 영상 지표(특히 가열면 접촉 비율), (iii) 기구 모델의 입력을 측정으로 고정하고 남은 계수 하나로 다섯 갭을 함께 설명**하는 데 있다.

## 3. 아이디어와 시사점
1. **"접촉 비율 + 통과 빈도"로 갭별 h를 설명하는 2변수 모델** (공기 주입)
   - 식: h_TP/h0 = (1 − φ_c) + φ_c·(h_sr(f)/h0)·g(L_b/u_b, x*) 꼴(본 조사 제안, 문헌 [3]의 두 극한을 묶음).
   - 필요 데이터: 운전점별 시간 평균 h, φ_c(가열 구간 위), f, L_b, u_b. 갭 다섯 개.
   - 새로움: Monde [3]은 단일 기포열·수직·인위 주입. 자연 기포류의 분포(크기·간격)를 영상으로 넣는 것이 새롭다.
   - 위험: φ_c 판정(위에서 보면 기포가 바닥에 닿는지 구분이 어렵다. 0.3~1 mm는 거의 1, 3 mm는 크기 기준 근사). 기포 밑 막이 실제로 단열인지(공기-물 계면으로의 증발·수증기 확산은 무시).
2. **0.3 mm의 "강화 역전" 검증**
   - 예측: 0.3 mm는 h0가 높아(5.4 kW/m²K) 통과 빈도가 약 9 Hz 미만이면 공기 주입이 h를 높이지 못하고 덮음 때문에 낮출 수 있다. 1~3 mm는 f > 1 Hz면 강화.
   - 필요 데이터: 같은 액체 유량에서 단상/이상 h 비교, 기포 빈도 분포.
   - 실현성: 높음(이미 0.3·0.7 mm 단열 실험이 있어 기포 통계부터 낼 수 있음). 위험: 열 입구 효과(0.7 mm 이상은 발달 중)로 h0가 모호하다 → 가열 길이·위치를 확인해야 한다.
3. **비등은 막 두께 계수 하나로 다섯 갭 설명** (3구역 모델)
   - 영상으로 f, L_b, u_b, 합체 빈도를 넣고 δ0 상관식(Zhang & Utaka [21] 또는 Moriyama & Inoue [20])의 계수 C_δ0 하나만 공통으로 맞춘다. C_δ0가 0.29~3.48로 흩어진 문헌 [19]과 대비해 "측정 입력으로 계수의 범위를 좁혔다"고 주장할 수 있다.
   - 위험: 사용자 실험이 비등인지 미확인. 3·7 mm에서는 3구역 모델의 가정(갇힌 긴 기포)이 깨진다.
4. **합체 이벤트 → Consolini 모델** [17]: 추적이 내는 합체 빈도는 다른 연구가 거의 쓰지 않은 변수다. 0.3~1 mm 비등에서 h 감소(건도 증가)와 합체 빈도를 같이 보이면 새로운 증거가 된다.
5. **측정 쪽 시사점**: 매립 열전대로는 시간 평균만 가능하다(Q3). 리뷰어가 "기포 단위 동기화"를 요구하면, 얇은 박 시험편 + IR(투명 덮개 너머) 보조 실험을 제안한다 [68]. 철 블록 h는 1D 외삽 보정(주제 6)이 필요하다.

## 4. 새로움 판단 기록 (검색어와 결과)
- Crossref(query.bibliographic, 행 4~10개 확인)
  - "gas injection heat transfer enhancement narrow channel bubbles gap size" → Monde 1988 JHT, Monde & Mitsutake 1989 IJMF, 1995 HMT, Ozer 2012 HT conf, Janssen 2013 HT conf. 이것이 Monde 계열 발견의 출발.
  - J-STAGE(prefix 10.1299) "Monde bubbles narrow vertical rectangular channel heat transfer enhancement" → 18072건 중 상위 10개에 Monde 일본어판 6편.
  - "heat transfer air-water two-phase flow narrow rectangular channel experimental" → Chalgeri & Jeong 2019(유동 양식, 열전달 없음), Huang 2011(와류 발생기, 증기) 등. 공기-물 좁은 갭 **열전달** 실험은 상위에 없음.
  - "Ozer Hollingsworth Witte … narrow channel sliding bubbles" → Ozer 2011 IJHMT, Albahloul 2013, Li 2006/Hollingsworth 2008(마이크로층 두께), Willard & Hollingsworth 2018(수치), Yan 2019(좁은 직사각 채널 미끄럼 기포, 자연순환).
- WebSearch(standard)·Google Scholar 기록은 아래에 추가한다(작성 중).

## 5. 남은 의문과 사용자에게 확인할 것
- 공기 주입인가 비등인가? 0.3·0.7 mm 단열 실험은 공기-물이 맞는가? 가열 실험에서도 공기를 넣는가?
- 가열 구간 길이와 위치(입구에서 거리). 0.7 mm 이상은 열 입구 효과가 커서 h0 기준선이 달라진다.
- 열전대 깊이·간격과 블록 재질(탄소강/스테인리스). 표면 외삽 오차와 시간 응답을 정한다.
- 가열면(철) 표면 젖음성(접촉각). 기포 밑 막이 끊기면(부분 젖음) 공기 주입에서도 건조 패치가 생긴다.
- 영상에서 "바닥 접촉" 판정이 가능한가? 기포 내부가 25~45 계조 어두운 이유가 바닥 접촉(막/건조)과 관련 있는지 확인하면 φ_c를 직접 잴 수 있다(주제 6과 공동).
- 미확인 문헌 내용: Kim & Ghajar(2006) 젖음 둘레 인자 식, Leung(2010, 2012) 결과, Dai(2015) 상관식, Wojtan(2005)의 건조각 사용 방식, Del Valle & Kenning(1985) 수치, Shah & London의 Nu = 5.385.

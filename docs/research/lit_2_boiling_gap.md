# 주제 2: 좁은 갭의 (풀·흐름) 비등 — 갭 0.1~10 mm

- 담당: 문헌 조사 에이전트 2 (2026-10-23). 확인 수준은 `agent_brief.md` 4장(C+F / C+A / C / U)을 따른다.
- 범위 변경(2026-10-23 사용자 지시) 반영: 갭 H = **0.3, 0.7, 1, 3, 7 mm**. 관련성 열은 "0.3/0.7/1/3/7 mm 연구와의 관련성"이다.
- Bond 수 표기가 문헌마다 다르다. 이 문서에서는 두 가지를 구분해 쓴다.
  - **Bo_s = s/Lc** (Yao & Chang 1983 이후 좁은 공간 비등 문헌의 관례, s = 갭)
  - **Bo = (H/Lc)²** (보통의 Bond 수. Bo < 0.1 ⇔ H < 0.32 Lc ≈ 0.8 mm)

| H (mm) | Bo_s 포화수(Lc 2.50 mm) | Bo_s 25 °C(Lc 2.71 mm) | Bo = (H/Lc)² 포화 | Co = Lc/H 포화 | D_h ≈ 2H (mm, 폭 ≫ H) | Lc/D_h (Kew–Cornwell Co) |
|---|---|---|---|---|---|---|
| 0.3 | 0.12 | 0.11 | 0.014 | 8.3 | 0.6 | 4.2 |
| 0.7 | 0.28 | 0.26 | 0.078 | 3.6 | 1.4 | 1.8 |
| 1 | 0.40 | 0.37 | 0.16 | 2.5 | 2 | 1.25 |
| 3 | 1.20 | 1.11 | 1.44 | 0.83 | 6 | 0.42 |
| 7 | 2.80 | 2.58 | 7.84 | 0.36 | 14 | 0.18 |

(물성은 표준 값으로 계산. 폭 W를 모르므로 D_h는 W ≫ H 근사.)

## 0. 요약
1. 좁은 공간 **풀 비등**에서 갭 효과는 50년 넘게 같은 그림이다. 갭이 기포 이탈 크기(≈ Lc) 아래로 줄면 납작한 기포 밑 얇은 액막 증발로 h가 오르고, 더 줄면 건조 영역이 생겨 h가 떨어진다. CHF는 갭이 줄수록 거의 단조 감소한다(#15, #19, #22, #23, #6, #18). 경계는 **Bo_s = s/Lc ≈ 1**이고(#17, #22, #23), 건조 열유속이 최대인 갭은 Bo_s ≈ 0.4(#23)다.
2. 이 틀을 다섯 갭에 대면: **7 mm(Bo_s 2.8)** 는 증기가 위 덮개 밑에 층을 이루고 가열면은 젖어 있어 비갇힘 비등과 비슷하다(#23, #4, #9). **3 mm(1.2)** 는 전이 구간, **1 mm(0.4)** 는 강화 최적 부근(#23, #24, #6), **0.7 mm(0.28)·0.3 mm(0.12)** 는 액 공급이 지배하는 강한 갇힘으로 조기 건조·CHF 저하·불안정 위험이 크다(#23 Bo_s < 0.3, #6 0.5 mm 저하, #15 0.1~0.2 mm 건조, #26 간헐 비등).
3. 0.1~1 mm **마이크로갭 흐름 비등**은 갇힌 슬러그·환상류가 지배하고, h는 건도에 대해 M자 모양이며 IR에서 국소 건조로 인한 약 20 K 온도 변동이 보인다(#34, #35). 단면이 작을수록 h가 오르다가 조기 건조가 온다(#41).
4. 수평 + 아래 가열 좁은 유로에서 큰 합체 기포가 유로 위쪽을 차지한다는 직접 관찰이 있다(#9, 에탄올). 수평 가열면(아래·위 가열 모두)은 불안정·역류에 가장 취약하다(#3, 0.5 mm 높이).
5. **덮개 젖음성**이 숨은 변수다. 1 mm보다 큰 갭에서는 친수/소수 덮개에 따라 기포가 덮개에 붙거나 가열면 위 슬러그가 되어 h와 CHF가 갈린다(#4, #5). 사용자 실험은 덮개 재질과 접촉각을 기록해야 한다.
6. **가장 가까운 선행 연구**: Gasanov 2026(#1, 물 아냉 흐름 비등, 갭 0.3/0.6/3 mm, 세 양식 가시화), Zhu et al. 2023(#2, 물 흐름 비등, 0.5~2 mm, h·ΔP·CHF·양식), Koizumi 계열(#8, #9, 에탄올, 수평 아래 가열, 높이 0.5~8 mm), Daoud et al. 2026(#11, ML 추적 + 벽 온도, 0.5~15 mm 풀 비등), Karim et al. 2021(#12, 스테인리스 마이크로갭 + 물 + ANN).
7. **새로움 판단**: "물 흐름 비등 + 0.3~7 mm 다섯 갭(서브 mm와 > 2Lc를 함께) + 위에서 본 고속 영상의 AI 기포 통계 + h + ΔP"를 함께 한 연구는 찾지 못했다(4장 검색 기록). 서브 mm와 mm를 한 실험에서 다룬 흐름 비등은 #1(0.3/0.6/3 mm)과 #2(0.5~2 mm) 정도이고, 7 mm(자유 영역)까지는 없다.
8. 위험: 위에서 본 영상만으로는 3·7 mm에서 기포가 **가열면에 닿았는지, 덮개에 붙었는지** 구분하기 어렵다(#4, #23). 가설 3(피복 비율 → h)에는 검증 수단이 필요하다. 기포가 공기 주입이면 이 주제의 핵심 기구(마이크로층 증발)는 해당하지 않는다(#52 같은 공기 기포 문헌으로 바꿔야 함).

## 1. 문헌 표
번호는 소주제를 가로질러 이어진다. 각 표 안에서는 가장 가까운 문헌을 위에 두었다.

### 1-A. 가장 가까운 문헌 (물·여러 갭·수평 아래 가열·영상/ML·스테인리스)
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 1 | Gasanov (2026) | Experimental Investigation into Influence of Channel Gap Size on Heat Transfer during Boiling of Subcooled Water Flow | J. Eng. Thermophys. 35(1):175-191 | 10.1134/s1810232826010169 | 물 아냉 흐름 비등, 1 atm. 폭 14 mm·길이 50 mm 직사각 유로 중앙의 지름 7 mm 원형 가열면. 갭 0.3/0.6/3 mm. G 127~370 kg/m²s, q 50~4800 kW/m², 입구 25/50/70 °C | 갭에 따라 세 양식을 가시화: 변형 기포 / 변형+고립 혼합 / 고립 기포. 상관식 8개 비교에서 Lee–Mudawar식이 MAE 5.6%로 가장 정확(초록 기준) | 다섯 갭 중 0.3·(0.7)·3 mm와 거의 같은 갭 묶음 + 물 + 가시화. 가장 가까운 선행 연구. 차이: 작은 원판 가열면(가장자리는 아냉 액체), 7 mm 없음, ΔP·기포 통계·AI 없음(초록 기준). SSRN 사전판 10.2139/ssrn.4781058 | C+A |
| 2 | Zhu, Li, Liu, Mubarak, Wang (2023) | Experimental study of flow boiling characteristics in minigap channels over a wide heat flux range | IJHMT 201:123567 | 10.1016/j.ijheatmasstransfer.2022.123567 | 탈이온수 흐름 비등, 미니갭 높이 0.5~2 mm, G 200~400 kg/m²s | 양식: 기포류 → sweeping → churn → churn-환상(q 증가 순). sweeping에서 불안정. ΔP는 양식과 연결된 세 구간. 갭이 h에 주는 효과는 q가 커지면 처음에 증가했다가 감소. CHF는 G·갭이 클수록 증가. 새 ΔP 상관식 오차 10.8%. 아냉 h는 Liu–Winterton·Shah, 포화 h는 Sun–Mishima·Kandlikar가 가장 정확(초록 기준) | 0.7/1 mm와 겹치는 물 흐름 비등에서 h·ΔP·CHF·양식을 함께 잰 연구. 갭별 상관식 평가의 비교 대상. 방향·가열 방식은 확인 못 함. 초록은 SSRN 사전판 10.2139/ssrn.4220685 | C+A |
| 3 | Vermaak, Orejon, Dirker, Sefiane, Meyer (2023) | Pressure and thermal characterisation of dynamic instabilities during flow boiling in micro/mini-channels at different azimuth orientations | ATE 218:119292 | 10.1016/j.applthermaleng.2022.119292 | FC-72, 수평 납작 유로 5 × 0.5 mm(AR 10, D_h 909 µm), 한쪽 가열, 방위각 0°(아래 가열)~180°(위 가열) 30° 간격, G 10/20/40 kg/m²s, Tsat 56 °C. 고속 영상 + IR + 압력 | 불안정을 이상 혼합 / 약한 역류 / 강한 역류로 분류. 가열면이 수평(0°, 180°)일 때 가장 취약, 중간 각(30~90°)은 최고 G에서만 불안정. G↑ → 불안정이 잦고 심함. q↑ → 불안정 조건은 늘지만 주파수는 낮아짐. 불안정 중 h가 오히려 높음(180°·최고 G: 단상 영역 +77%, 이상 영역 +275%)(초록 기준) | 0.3/0.7 mm 수평 아래 가열과 가장 비슷한 형상의 역류·불안정 연구. 영상 + 압력 + 벽 온도 동기화의 선례. SSRN 사전판 10.2139/ssrn.4044510에서 초록 확인 | C+A |
| 4 | Rukhsar, Fadda, Wang, Lee, You (2024) | Effects of cover plate wettability on pool boiling heat transfer in a narrow gap | IJHMT 221:125130 | 10.1016/j.ijheatmasstransfer.2023.125130 | 수평 좁은 갭 0.64~5 mm, 친수/소수 덮개, 풀 비등(유체는 물로 추정. 후속 #5는 증류수) | 갭 > 1 mm에서 덮개 젖음성이 중요. 소수성 덮개: 기포가 가열면을 떠나 덮개에 붙고 가열면은 젖은 상태 → 핵비등 h는 거의 같고, 증기가 갭을 채워 CHF 저하. 친수성 덮개(갭 > 1 mm): 가열면 위 증기 슬러그 → q < 약 250 kW/m²에서 h 증가, 그 이상에서 슬러그 운동으로 부분 건조 → h·CHF 저하 | 0.7/1/3 mm와 겹치는 수평·아래 가열 갭. 덮개(유리·아크릴) 접촉각이 숨은 변수. 위 영상의 기포가 "덮개에 붙은 것"일 수 있다는 근거 | C (검색 요약: Ajou 저장소 초록) |
| 5 | Rukhsar, Fadda, Lee, You (2025) | Boiling heat transfer with a microporous heating surface in a narrow gap with cover plates of different wettability | IJHMT 244:126956 | 10.1016/j.ijheatmasstransfer.2025.126956 | 증류수, 미세다공 구리 코팅, 갭 0.64/1/2/3/5 mm | 소수성 덮개에서는 CHF 감소가 작고, 친수성 덮개에서는 크게 감소. 소수성 덮개는 갭 안 성층류, 친수성 덮개는 옆으로 자라는 기포 | #4와 같음. 같은 그룹 2026 ICHMT 171:110119(방향 의존성, 제목만 확인) | C (검색 요약) |
| 6 | Kim JS, Shin, Kim Y, You, Lee (2020) | Bubble Behavior in Pool Boiling Heat Transfer between Two Plates with a Narrow Gap | JHT 142(3) | 10.1115/1.4046116 | 증류수 1 atm, 수직, 구리판 80×80 mm, 뒷면 10×10 mm 히터, 갭 3 → 0.5 mm | 갭이 줄면 기포가 옆으로 퍼짐. 3·1 mm: 납작한 기포 밑 얇은 액막 증발로 열전달 향상. 0.5 mm: 건조 영역 증가로 비등 열전달 저하 | 물에서 1·3 mm 강화, 0.5 mm 저하 → 0.7 mm가 강화–저하 경계 근처일 수 있음 | C+A |
| 7 | Kim JS, Shin, You, Lee (2020) | Pool boiling heat transfer on bare and microporous surfaces confined in a narrow gap | IJHMT 162:120329 | 10.1016/j.ijheatmasstransfer.2020.120329 | 포화 증류수 1 atm, 10×10 mm 히터 + 두께 0.2 mm 구리판, 앞쪽 유리창 너머 관찰, 갭 0.5 mm~무한 | CHF 근처에서 건조 영역과 액체 하층(liquid sublayer)이 뚜렷이 보임. 다공 표면은 1 mm까지 h 유지 | 투명 창 너머로 가열면을 보는 같은 관찰 배치. "건조 영역 면적"을 영상 지표로 쓸 근거 | C+A |
| 8 | Oshikawa, Sakurai, Koizumi, Ohtake (2008) | Study on Boiling Heat Transfer in Narrow and Flat Space | Proc. ICONE16, Vol. 2:619-622 | 10.1115/icone16-48123 | 에탄올 0.1 MPa, 가열면은 바닥. (a) 수평 직사각 유로 폭 1~2 mm·높이 0.5~8 mm·길이 30 mm(양끝 개방), (b) 20×20/30×30 mm 평판 공간 중앙 지름 3 mm 가열면, 간격 0.5~8 mm | 유로: 큰 기포가 주기적으로 가열면을 떠나 양끝으로 이동. 높이가 줄수록 CHF 감소, 높이가 크면 풀 비등 CHF에 가까움. 평판 공간: 넓으면 풀 비등과 비슷, 좁으면 큰 기포가 가열면에 앉아 CHF, 아주 좁으면 비등 시작이 곧 CHF | 수평·아래 가열·높이 0.5~8 mm로 다섯 갭 범위 전체를 한 계열에서 다룬 거의 유일한 예. 단 에탄올·작은 가열면·풀 조건 | C+A |
| 9 | Koizumi, Ohtake, Oshikawa (2009) | Study on Boiling Heat Transfer in Narrow Channel and Horizontal-Narrow-Flat Space | Proc. ICNMM2009:53-57 | 10.1115/icnmm2009-82113 | 에탄올 0.1 MPa, 수평 유로 높이 1.0~4.0 mm·폭 1.0~3.0 mm·길이 30/60 mm, 바닥 중앙 가열면, 양끝 개방. 지름 1~20 mm 가열면 풀 비등 비교 | 같은 가열면 크기의 풀 비등과 비등 곡선이 같음. 높이가 줄수록 CHF 저하. **큰 합체 기포가 유로 위쪽을 차지**. 기포가 한쪽 출구로만 빠지는 순환 흐름이 생김. CHF는 "액 공급 = 증기 생성" 질량 균형만으로 정해지지 않음 | 수평 아래 가열에서 "증기가 위 벽에 모인다"는 가정의 직접 근거(1·3 mm 범위) | C+A |
| 10 | Kim YH, Kim SJ, Kim JJ, Noh, Suh, Rempe, Cheung, Kim SB (2005) | Visualization of boiling phenomena in inclined rectangular gap | IJMF 31(5):618-642 | 10.1016/j.ijmultiphaseflow.2005.01.002 | 포화수 1 atm, 구리 히터, 갭 1/2/5/10 mm, 경사 90°(수직)~180°(아래 향함), 고속 카메라, 진공 단열 | CHF는 경사각이 커지고 갭이 줄수록 감소. 단 180°(아래 향함)에서는 갭이 줄수록 CHF 증가(갭이 증기 이동을 도움). CHF가 급변하는 전이 각이 있음 | 물 + 1·5·10 mm(3·7 mm를 감쌈). 방향이 바뀌면 갭 효과의 부호가 바뀔 수 있음. 후속 Kim YH et al. 2006 Nucl. Technol. 154(1):13-40, 10.13182/nt06-a3715(CHF, 제목만 확인. 첫 저자는 Rempe가 아니라 Kim YH) | C+A (Penn State 기관 페이지 초록) |
| 11 | Daoud, Baudin, Roux, Bellettre (2026, 사전공개) | Experimental Investigation of Bubble Dynamics in Confined Pool Boiling Using Machine-Learning-Based Tracking | SSRN | 10.2139/ssrn.7225772 | Novec 7000, 수직 갇힌 풀 비등, 갭 0.5~15 mm, 2000 fps + 벽 온도·열유속 | 공개 BubbleFinder를 고쳐 검출·추적, 손 라벨 프레임과 IoU로 정확도 평가. 궤적에서 등가직경, 수직 속도, 3D 재구성 기공률(시간·높이별). 앞면만 갇힘: 갇힘이 기포를 가속, 합체 없이 성장. U자 측판 추가: 평평한 속도 분포, 높이별 직경 발산, 비등 곡선 저하 | 방법론이 가장 가까움(ML 추적 + IoU 검증 + 열 측정 + 넓은 갭 범위). 차이: 풀 비등·유전 유체·수직·ΔP 없음. Crossref 저자 표기는 "Jérôme, Bellettre"로 이름·성이 뒤바뀜 | C+A |
| 12 | Karim, Kim YJ, Kim JH (2021) | Two-Dimensional Flow Boiling Characteristics With Wettability Surface in Microgap Heat Sink and Heat Transfer Prediction Using Artificial Neural Network | JHT 143(9) | 10.1115/1.4051602 | DI 물(실온 입구), **스테인리스 판**, 마이크로갭 깊이 170 µm, 국소 히터(핫스폿), 친수 코팅(부분/채널형) | 친수 표면에서 증기막·슬러그가 빨리 씻겨 h 증가, 채널형 친수가 냉각·압력 안정에 가장 좋음. 기포 형상·h·ΔP 함께 측정. ANN의 h 예측 평균 ±5% | 스테인리스 가열판 + 물 + 마이크로갭 + 가시화 + ΔP + ML. 단일 갭(0.3 mm보다 작음). 선행 학회판 Karim & Kim 2019 IMECE(깊이 254 µm, 10.1115/imece2019-11015, C+A) | C+A |
| 13 | Robinson, Bar-Cohen (2019) | Orientation Effects in Two-Phase Microgap Flow | JEP 141(3) | 10.1115/1.4043483 | HFE7100, 마이크로갭 높이 1.01 × 폭 13.0 × 길이 12.7 mm, 증발기 방향·G·q 변화 | G ≥ 400 kg/m²s(Fr ≈ 0.8)에서 CHF·h·양식이 방향과 무관 | 1 mm 갭도 저유량이면 방향(중력) 효과가 남음. 3·7 mm는 더 강할 것 | C+A |
| 14 | Soffer, Aharon, Ziskind (2023) | Experimental investigation on incipient boiling in narrow closed gaps with water | IJTS 191:108333 | 10.1016/j.ijthermalsci.2023.108333 | 아냉수 1 atm, 정지 액체, 수직 구리판 두 장(가열/냉각), 닫힌 갭 5/3/0.9/0.5 mm | 0.5 mm는 단상에서 물을 통한 전도, 0.9 mm는 "전이" 열전달 영역. ONB는 h 거동이 급변하는 점으로 검출(가시화로 확인). 문헌식 기반 모델은 ONB 열유속은 잘 맞추지만 ONB 과열도는 과대 예측(0.5 mm 제외) | 물 + 0.5~5 mm. 0.3/0.7 mm에서는 단상 열전달부터 전도 지배일 수 있다는 점(흐름이 있으면 다름) | C (검색 요약: CRIS 초록) |

### 1-B. 좁은 공간 풀 비등: 갭 효과·Bo 기준·CHF
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 15 | Katto, Yokoya, Teraoka (1977) | Nucleate and Transition Boiling in a Narrow Space between Two Horizontal, Parallel Disk-Surfaces | Bull. JSME 20(143):638-643 | 10.1299/jsme1958.20.638 | 포화수 1 atm, 위로 향한 지름 11 mm 구리 가열면 + 같은 지름 유리 원판(덮개), s = ∞~0.1 mm, 고속 촬영 | 같은 q에서 s가 줄면 과열도가 줄다가(h 증가) s ≈ 0.2 mm에서 최소, 0.1 mm에서 급반전. CHF는 s가 줄수록 감소(그림 11에서 읽은 대략값: 자유 비등 약 1.9 MW/m² → s = 0.1 mm 약 0.5 MW/m²). s ≥ 2 mm는 소실 기구가 자유 비등과 같음. s = 0.5~0.2 mm는 핵비등 중에도 건조 부분 존재. s = 0.1 mm는 뚜렷한 CHF가 없음 | 물·수평·위로 향한 가열면·투명 덮개 = 사용자 형상의 풀 비등판. 다섯 갭 모두 범위 안. 같은 장치의 핵비등 결과: Katto & Yokoya 1966 Trans. JSME 32(238):948-958, 10.1299/kikai1938.32.948(일본어, C) | C+F (J-STAGE 스캔본) |
| 16 | Ishibashi, Nishikawa (1969) | Saturated boiling heat transfer in narrow spaces | IJHMT 12(8):863-893 | 10.1016/0017-9310(69)90153-7 | 수직 개방 환형 갭(가열 봉 + 비가열 관) | 저열유속에서 고립 기포 영역과 합체 기포 영역을 구분. 합체 영역의 강화된 h를 경험식으로 정리 | "고립 vs 합체" 두 영역 구분의 원조. 영상의 "합체 기포 면적 비율"로 영역을 판정하는 근거 | C (2차 인용: #18, #21) |
| 17 | Yao, Chang (1983) | Pool boiling heat transfer in a confined space | IJHMT 26(6):841-848 | 10.1016/s0017-9310(83)80108-2 | R-113·물·아세톤, 바닥이 막힌 수직 환형 갭 0.32/0.80/2.58 mm, 높이 25.4/76.4 mm | Bo_s = s/Lc 도입. Bo_s와 수정 비등수(갭 안 기포 체류 시간 / 증기 생성 시간)로 세 영역 지도. 영역은 Bo_s가 1보다 작은지, 비슷한지, 큰지에 크게 좌우 | 갭 기준 Bond 수의 원조. 물 포함. 같은 그룹 Chang & Yao 1983 JHT 105(1):192-195(바닥 막힌 환형 CHF, 10.1115/1.3245542, C) | C (2차 인용: #21, #19, DTIC 보고서 요약) |
| 18 | Hung, Yao (1985) | Pool Boiling Heat Transfer in Narrow Horizontal Annular Crevices | JHT 107(3):656-662 | 10.1115/1.3247474 | 수평 좁은 환형 틈, 유체 물성·아냉·틈 길이·갭 변화 | CHF는 갭이 줄거나 길이가 길수록 감소. 얇은 액막 증발로 설명. 수평 갇힌 공간 CHF 반경험식 | 수평 좁은 공간에서 CHF 저하와 "가열 길이" 효과(길수록 증기 배출이 어려움) | C+A |
| 19 | Fujita, Ohta, Uchida (1988) | Heat Transfer in Nucleate Boiling within a Vertical Narrow Space | JSME Int. J. Ser. II 31(3):513-519 | 10.1299/jsmeb1988.31.3_513 | 물 1 atm, 수직, 가열면–유리판 갭 5 → 0.15 mm(4단계), 가열면 높이 2종, 주변 개방/폐쇄 | 갭이 줄면 h가 최대값까지 증가(특히 중간 q), 더 줄면 전 q 범위에서 저하. 갭 크기로 세 무리. s = 0.15 mm: 젖은 영역(폭 W)과 건조 영역으로 나눈 모델에서 W = 2.5 mm, α_w = 15,000 W/m²K일 때 개방 주변 실험과 일치 | 물 + 0.15~5 mm. **관찰한 젖은 폭으로 비등 곡선을 예측한 "영상 → h" 모델의 고전 예**(가설 3). 같은 그룹 Fujita, Ohta, Uchida, Nishikawa 1988 IJHMT 31(2):229-239, 10.1016/0017-9310(88)90004-x(직사각 면 사이 좁은 공간 핵비등·CHF, 원문 미확인, C) | C+F (J-STAGE 스캔본) |
| 20 | Bonjour, Lallemand (1998) | Flow patterns during boiling in a narrow space between two vertical surfaces | IJMF 24(6):947-960 | 10.1016/s0301-9322(98)00017-2 | R-113, 수직, 높이 120 mm, 갭 0.5~2 mm, 열선 풍속계 | 세 영역: 변형된 고립 기포 / 합체 기포 / 부분 건조. 앞의 둘은 강화, 건조는 저하. 기포 빈도·통과 시간·기공률을 재서 천이 기준과 Bo–환산 열유속 지도 | 갭별 양식 지도의 표준. 기포 빈도·통과 시간은 영상 지표와 직접 비교 가능 | C (검색 요약: Scholar 스니펫) |
| 21 | Passos, Hirata, Possamai, Balsamo, Misale (2004) | Confined boiling of FC72 and FC87 on a downward facing heating copper disk | IJHFF 25(2):313-319 | 10.1016/j.ijheatfluidflow.2003.11.016 | FC72/FC87, 아래 향한 지름 12 mm·두께 2 mm 구리 원판, 간격 0.2~13 mm, 포화·아냉 | 포화·저열유속(≤ 45 kW/m²)에서는 간격이 줄면 강화. 아냉에서는 간격이 줄면 h 감소 | 아냉 조건이면 갇힘 효과의 부호가 바뀔 수 있음(흐름 비등이 아냉이면 주의) | C+F |
| 22 | Stutz, Lallemand, Raimbault, Passos (2009) | Nucleate and transition boiling in narrow horizontal spaces | Heat Mass Transfer 45(7):929-935 | 10.1007/s00231-007-0325-9 | n-펜탄 포화(Lc = 1.6 mm), 위로 향한 지름 30 mm 구리, 플렉시글라스 덮개, s = 0.2~90 mm, 내시경 + 250 fps, 역전도 해석 | CHF는 s가 줄수록 감소, **s ≈ Lc에서 크게 변함**. Bo_s < 1: 납작한 기포 밑 얇은 액막 증발로 저열유속 h 증가, 비등 곡선의 오목성 변화. 저열유속에서 비등이 켜졌다 꺼지는 약 0.01 Hz 불안정. 천이 비등에서 덮개의 액막이 약 15 Hz로 건조 가열면에 닿음. s ≈ 0.2 mm(Bo_s ≈ 0.13)에서 CHF 개념이 흐려짐 | 수평·위로 향한 가열면·투명 덮개. 전이가 s ≈ Lc(물 ≈ 2.5 mm, 즉 3 mm 근처)에서 일어난다는 직접 근거 | C+F |
| 23 | Cardoso, Kannengieser, Stutz, Passos (2011) | FC72 and FC87 nucleate boiling inside a narrow horizontal space | ETFS 35(6):1038-1045 | 10.1016/j.expthermflusci.2011.02.006 | FC72/FC87 포화, 지름 12 mm 구리 원판, 위/아래 향함, s = 0.1~13 mm, 덮개 2종, q ≤ 40 kW/m² | 위로 향한 가열면, Bo_s > 1: 기포가 떨어져 덮개 밑에 증기층(두께는 중력이 제한)을 만들고 **가열면과 상호작용하지 않아 비갇힘 비등과 비슷**. Bo_s < 1: 가열면과 증기층 사이에 액체 마이크로층. 강화 기구: 수평·매우 좁은 공간은 마이크로층 증발, 수직은 합체·미끄럼에 의한 액 교반. 건조 열유속(DHF)은 대부분 Bo_s ≈ 0.4에서 최대. Bo_s < 0.3이면 DHF가 주변 조건(액 공급)에 크게 좌우, Bo_s > 0.5면 무관 | 7 mm(2.8)는 "덮개 증기층 + 젖은 가열면", 1 mm(0.4)는 최적 부근, 0.3/0.7 mm(0.12/0.28)는 액 공급 지배라는 예측(유체·풀 조건 차이 주의) | C+F |
| 24 | Nunes, Souza, Rodrigues, Safaei, Cardoso (2020) | Influence of coated surfaces and gap size on boiling heat transfer of deionized water | JBSMSE 42(3) | 10.1007/s40430-020-2223-8 | 포화 탈이온수 1 atm, 구리(Ra 0.33 µm), Al2O3 나노코팅, 갭 1.0 mm(Bo_s = 0.4) vs 비갇힘 | 코팅은 오염 저항으로 h 약 29% 저하. 코팅 + 갇힘에서 DHF +28%(재젖음 향상). h는 코팅보다 갭 영향이 큼. ImageJ로 기포 변형 측정 | 물·1 mm·Bo_s 0.4로 사용자 1 mm와 같은 조건 | C+A |
| 25 | Geisler, Bar-Cohen (2009) | Confinement effects on nucleate boiling and critical heat flux in buoyancy-driven microchannels | IJHMT 52(11-12):2427-2436 | 10.1016/j.ijheatmasstransfer.2009.02.001 | FC-72, 수직 평행판 채널(간격 약 0.3~1.6 mm, 2차 인용) | 간격이 줄면 핵비등 강화(정도는 히터 종류에 따라 다름). CHF는 간격이 줄면 저하하며 표면과 무관, 기존 상관식으로 잘 예측(학회판 HT2005-72666 초록 기준) | CHF 저하는 표면보다 형상이 지배한다는 근거 | C (학회판 10.1115/ht2005-72666 C+A, #21 2차 인용) |
| 26 | Kapitz, Schmiedinghoff, Lüling, aus der Wiesche (2019) | Impact of surface parameters on confined boiling heat transfer in a Hele-Shaw cell | Heat Mass Transfer 55(9):2533-2544 | 10.1007/s00231-019-02604-2 | 순수 물 1 atm, Hele-Shaw 셀(판 간격 작음, 여러 값), 구리/알루미나·매끈/거침, 인공 핵생성점 1개, 고속 카메라 | 저열유속에서 갇힌 비등이 셀 침수로 끊기는 간헐 비등 → 열전달 큰 요동. 인공 핵생성점 하나로 안정. 중간 열유속에서는 작은 간격에서 거칠기 영향 작음. 영상 후처리로 마이크로층 증발을 주 기구로 판단. 수정 모세관수 모델 | 0.3 mm처럼 아주 작은 갭(물)의 간헐 비등과 영상 분석의 선례 | C+A |
| 27 | Chauhan, Kandlikar (2020) | Transforming pool boiling into self-sustained flow boiling through bubble squeezing mechanism in tapered microgaps | APL 116(8) | 10.1063/1.5141357 | 물, 10 mm 정사각 히터, 입구 갭 1.27 mm, 테이퍼 10°/15° | 15° 테이퍼: CHF 288 W/cm², h 119 kW/m²K(평면 127 W/cm², 52.5 kW/m²K). 눌린 기포가 넓어지는 쪽으로 팽창해 펌프 없는 흐름을 만듦. 고속 영상 | 갇힌 기포의 팽창 방향이 흐름·역류를 좌우(0.3~1 mm 역류 문제와 연결). 후속 2022 IJHMT 183:122165(C) | C+A |

### 1-C. 얇은 액막(마이크로층)과 0.1~0.5 mm 갭
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 28 | Moriyama, Inoue (1996) | Thickness of the Liquid Film Formed by a Growing Bubble in a Narrow Gap Between Two Horizontal Plates | JHT 118(1):132-139 | 10.1115/1.2824026 | 수평 두 판, 갭 0.1~0.4 mm, 고속 사진 | 액막 두께는 (이 논문의) Bond 수가 2보다 크면 점성 경계층 두께, 작으면 모세관수가 지배 | 0.3 mm 갭에서 납작 기포 밑 초기 액막 두께 추정 | C+A |
| 29 | Utaka, Okuda, Tasaki (2009) | Configuration of the micro-layer and characteristics of heat transfer in a narrow gap mini/micro-channel boiling system | IJHMT 52(9-10):2205-2214 | 10.1016/j.ijheatmasstransfer.2008.11.020 | 평행판 미니/마이크로 채널, 갭 0.5·0.25 mm(계산), 레이저 소광법 | 기포 주기를 마이크로층 기간과 액 포화 기간으로 나누고 1차원 과도 전도로 과열도를 계산 → 실험과 일치, 마이크로층 증발이 강화 원인 | 0.3 mm 갭 열전달 기구 모델. 같은 그룹의 좁은 갭 흐름 비등 CHF·h 강화: Omisanya, Chen, Utaka 2022 IJHMT 182:121982, 10.1016/j.ijheatmasstransfer.2021.121982 / 2024 IJHMT 226:125471, 10.1016/j.ijheatmasstransfer.2024.125471(제목만, C) | C (2차 인용: #30) |
| 30 | Zhang, Utaka (2012) | Characteristics of microlayer formation and heat transfer in mini/microchannel boiling systems: a review | Front. Heat Mass Transfer 3(1):013003 | 10.5098/hmt.v3.1.3003 | 리뷰(갭 0.1~0.5 mm 자료) | 물·평행 석영판(TiO2 친수 코팅)의 비등 곡선은 마이크로층 증발 구간과 건조 구간으로 나뉘고, 마이크로층 증발 구간이 최대 열유속의 약 70~80%를 차지(Tasaki & Utaka 2003 인용) | 0.3/0.7 mm에서 "강화 구간 → 건조 구간" 전환 예상 | C+F |
| 31 | Zhang, Utaka (2015) | Characteristics of a liquid microlayer formed by a confined vapor bubble in micro gap boiling between two parallel plates | IJHMT 84:475-485 | 10.1016/j.ijheatmasstransfer.2015.01.013 | 물·에탄올·톨루엔·HFE7200, 갭 0.15/0.30/0.50 mm, 레이저 소광 + VOF | 초기 마이크로층 두께는 주로 갭과 기포 앞끝 속도로 결정. 저속 구간은 속도↑ → 두께↑, 고속 구간은 약간 감소. Ca·We·Bo의 경험식 | 0.3 mm 갭 액막 두께 → 3구역 모델(주제 4) 입력 | C+F (YNU 저장소 수정 원고) |
| 32 | Jagirdar, Lee PS (2020) | Quasi-steady and transient study of heat transfer during sub-cooled flow boiling in a small aspect ratio microchannel | IJMF 133:103446 | 10.1016/j.ijmultiphaseflow.2020.103446 | 탈이온수 아냉 흐름 비등, 단일 채널 높이 0.14/0.28/0.42 mm(폭 2.54 mm, 2015 학회판), G 200~1000 kg/m²s | 대부분 슬러그류. 고주파 벽 온도를 역전도 해석(IHCP)해 젖은 면의 과도 열유속·h를 구하고 영상과 동기. 얇은 액막 증발이 주 기구. 열전달 변수와 비등 현상의 양방향 결합 | 0.3 mm 물 흐름 비등 + 벽 온도–영상 동기화 = 사용자 방법에 가장 가까운 열측정 선례. 2016 IJMF 83:254-266(동기 가시화, 10.1016/j.ijmultiphaseflow.2016.04.004, C) | C+A |
| 33 | Zaitsev, Kabov (2009) | Microgap Cooling Technique Based on Evaporation of Thin Liquid Films | Proc. InterPACK2009, Vol. 2:545-551 | 10.1115/interpack2009-89318 | 물, 납작 채널 높이 1.2~2.0 mm, 기체 흐름이 미는 얇은 액막(성층·환상) | 넓은 유량 범위에서 액막 안정. 열모세관 효과가 중요. 전단 액막의 CHF가 낙하 액막의 10배, 물에서 400 W/cm² 초과 | 증기가 위에 모인 수평 갭의 "아래 액막 + 위 증기" 성층 양식의 상한 참고. Kabov et al. 2011 ETFS 35(5):825-831(10.1016/j.expthermflusci.2010.08.001, C) | C+A |

### 1-D. 마이크로갭(0.01~1 mm) 흐름 비등
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 34 | Bar-Cohen, Sheehan, Rahim (2012) | Two-Phase Thermal Transport in Microgap Channels—Theory, Experimental Results, and Predictive Relations | Microgravity Sci. Technol. 24(1):1-15 | 10.1007/s12217-011-9284-3 | 리뷰 + 냉매·유전 유체 자료 + IR 영상 역해석 | 양식 진행은 기존 양식 지도로 예측됨. 환상류가 지배적이고 채널이 작을수록 더 중요. h는 건도(또는 겉보기 속도)에 대해 **M자 모양**, 변곡점 = 냉각 방식 전환. 환상류에서는 Chen 상관식이 거시 채널만큼 맞음. IR에서 환상류 중 큰 표면 온도 변동 → 얇은 액막 증발 종료 | 0.3/0.7 mm에서 h–건도 곡선 모양과 국소 건조 예측. 앞선 Bar-Cohen & Rahim 2009 HTE 30(8):601-625(10.1080/01457630802656678, 문헌 자료를 Taitel–Dukler 지도로 분류, C) | C+A |
| 35 | Sheehan, Kim DW, Bar-Cohen (2009) | Thermal Imaging of Two-Phase Coooled Microgap Channel Wall | Proc. InterPACK2009, Vol. 2:491-499 | 10.1115/interpack2009-89238 | FC-72, 마이크로갭 260 µm × 30 × 34 mm, 반대쪽 사파이어 창 너머 IR, G 35 kg/m²s, q 3.2 W/cm² | 공간·시간 온도 변동이 약 20 K에 이름. 고건도 환상류의 국소 건조 증거 | 투명 창 너머로 불투명 가열벽을 보는 같은 배치(IR). 영상 지표 ↔ 벽 온도 요동 비교의 선례 | C+A |
| 36 | Alam, Lee PS, Yap, Jin, Balasubramanian (2012) | Experimental investigation and flow visualization to determine the optimum dimension range of microgap heat sinks | IJHMT 55(25-26):7623-7634 | 10.1016/j.ijheatmasstransfer.2012.07.080 | 실리콘 마이크로갭, 채널 높이 110~500 µm, 고속 가시화(Scholar 스니펫) | 갭 높이 최적화. 최적 범위의 수치는 확인 못 함 | "최적 갭" 개념의 마이크로갭 쪽 근거. 0.3 mm는 이 범위 안 | C (검색 요약) |
| 37 | Alam, Lee PS, Jin (2013) | Flow Boiling in Microgap Channels: Experiment, Visualization and Analysis | SpringerBriefs in Applied Sciences and Technology | 10.1007/978-1-4614-7190-5 | 책(장 초록). 3·5장: 3종·10종 치수 마이크로갭, Harirchian–Garimella 갇힘 기준으로 자료 정리 | 7장: 같은 바닥 면적·G·유효 q에서 마이크로갭이 직선 마이크로채널보다 불안정·역류가 적음. 5장: 치수·운전 조건 최적화 | 0.3 mm 단일 넓은 갭이 병렬 채널보다 역류에 강할 수 있다는 근거. 관련 논문: Alam et al. 2012 IJMF 42:164-174(10.1016/j.ijmultiphaseflow.2012.02.007), 2013 IJHMT 58(1-2):335-347(10.1016/j.ijheatmasstransfer.2012.11.020), Alam & Lee 2015 IJHMT 89:390-405(확장 마이크로갭 불안정, 10.1016/j.ijheatmasstransfer.2015.05.057; Crossref 저자 표기 "Tamanna, Alam") — 모두 C | C+A (장 초록) |
| 38 | Han, Fedorov, Joshi (2016) | Flow Boiling in Microgaps for Thermal Management of High Heat Flux Microsystems | JEP 138(4) | 10.1115/1.4034317 | 마이크로갭 흐름 비등 리뷰 + 높이 200 µm 마이크로 핀핀, 물, 출구 24~36 kPa, G 1351~1784 kg/m²s, q 198~444 W/cm² | 이상 h가 q와 함께 감소. 핵생성 뒤 삼각형 후류. 흐름 진동 관찰 | 마이크로갭(평면·핀핀) 리뷰. 물 마이크로갭의 진동 | C+A |
| 39 | Nasr et al. (2017) | Hotspot Thermal Management With Flow Boiling of Refrigerant in Ultrasmall Microgaps | JEP 139(1) | 10.1115/1.4035387 | R134a, 갭 10 µm(빈 갭/핀핀), 실리콘 아래 저항 히터 + 위 유리 덮개, q 최대 약 5 kW/cm², G ≤ 3000 kg/m²s, p ≤ 1.5 MPa | 벽 온도·열저항·ΔP를 관찰한 양식에 대응 | 극소 갭의 상한. "아래 가열 + 위 유리 덮개 + 위에서 관찰" 배치 | C+A |
| 40 | Lee HJ, Lee SY (2001) | Heat transfer correlation for boiling flows in small rectangular horizontal channels with low aspect ratios | IJMF 27(12):2043-2062 | 10.1016/s0301-9322(01)00054-4 | R-113, 수평, 폭 20 mm, 갭 0.4~2 mm, G 50~200 kg/m²s, q ≤ 15 kW/m², x 0.15~0.75, 환상류 | 저 G(작은 갭)에서는 액막 두께가 열전달을 지배. Re_LF ≤ 200용 수정 증강계수 F로 ±20%, Re_LF > 200은 Kandlikar식(평균 편차 10.7%) | 0.3~1 mm 넓은 수평 갭 h 상관식의 직접 후보. 같은 저자의 ΔP 상관식은 주제 3 | C+A (KAIST DSpace 초록, 검색 요약 경유) |
| 41 | Harirchian, Garimella (2009) | The critical role of channel cross-sectional area in microchannel flow boiling heat transfer | IJMF 35(10):904-913 | 10.1016/j.ijmultiphaseflow.2009.06.005 | FC-77, 실리콘 병렬 채널, 폭 100~5850 µm·깊이 400 µm(앞 연구) + 깊이 100·250 µm, 고속 가시화 + 국소 h·ΔP | 단면적이 지배 변수. 기준값보다 크면 핵비등 지배·h가 치수와 무관(폭 ≥ 400 µm). 작으면 모든 q에서 증기 갇힘, 단면이 작을수록 h 증가하다가 갇힘으로 **조기 건조** | 0.3/0.7 mm에서 "갇힘 → h 증가 → 조기 건조" 순서의 근거. 앞 연구 2009 IJMF 35(4):349-362(10.1016/j.ijmultiphaseflow.2009.01.003, C) | C+A |
| 42 | Harirchian, Garimella (2010) | A comprehensive flow regime map for microchannel flow boiling with quantitative transition criteria | IJHMT 53(13-14):2694-2702 | 10.1016/j.ijheatmasstransfer.2010.02.039 | 위 자료 | 질량유속·단면적·물성을 넣은 "대류 갇힘 수" 제안(Bo^0.5·Re < 160이면 갇힘: 학위논문 초록의 2차 인용). 무차원 비등 변수로 천이 기준이 있는 양식 지도 | 갇힘을 D_h만이 아니라 G까지 넣어 판정 → 다섯 갭의 갇힘 판정 후보 | C+A (160은 2차 인용) |
| 43 | Harirchian, Garimella (2012) | Flow regime-based modeling of heat transfer and pressure drop in microchannel flow boiling | IJHMT 55(4):1246-1260 | 10.1016/j.ijheatmasstransfer.2011.09.024 | FC-77 | 지도 4영역(기포류, 슬러그, 갇힌 환상, 교대 churn/환상/wispy-환상). 슬러그·환상 h 모델. 길이 방향 양식별 ΔP 합산 | "양식별 모델 + 영상으로 양식 판정"의 선례(영상 지표로 양식 구간 길이를 잴 수 있음) | C+A |
| 44 | Kim SM, Mudawar (2013) | Universal approach to predicting saturated flow boiling heat transfer in mini/micro-channels – Part II. Two-phase heat transfer coefficient | IJHMT 64:1239-1256 | 10.1016/j.ijheatmasstransfer.2013.04.014 | 31개 출처 10,805점(건조 전), 18개 유체, D_h 0.19~6.5 mm | 핵비등 + 대류 비등 결합식, MAE 20.3%(±30% 안 79.9%). 직사각 채널 3면 가열 등 가열 둘레 처리 언급(세부 미확인) | 비교 기준식. 한쪽 가열 넓은 갭에 그대로 쓸 수 있는지는 원문 확인 필요. Part I 10.1016/j.ijheatmasstransfer.2013.04.016(건조 시작 건도) | C (검색 요약) |
| 45 | Kew, Cornwell (1997) | Correlations for the prediction of boiling heat transfer in small-diameter channels | ATE 17(8-10):705-715 | 10.1016/s1359-4311(96)00071-3 | 작은 관 비등 | 갇힘수 Co = Lc/D_h > 0.5면 소구경 거동(널리 인용, 2차 인용) | 넓은 갭은 D_h ≈ 2H라서 D_h 기준 Co가 H 기준의 절반이 됨 → 3 mm가 "거시"로 분류됨(2장 Q1) | C |

### 1-E. mm급 직사각 유로 흐름 비등: 한쪽 가열·방향·수평 아래 가열
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 46 | Zhang H, Mudawar, Hasan (2004) | A Method for Assessing the Importance of Body Force on Flow Boiling CHF | JHT 126(2):161-168 | 10.1115/1.1651532 | FC-72, 투명 직사각 유로의 한 벽 가열, 여러 방향, 고속 영상 | CHF 양식 6종(파동 증기층, 풀 비등, 성층, 증기 역류, 증기 정체, 분리 병류). 유속 < 0.2 m/s에서 CHF가 방향에 매우 민감, 아래로 향한 가열벽·하향류에서 매우 낮음. 고유속이면 방향 효과가 거의 사라짐. 중력 무시 조건 무차원 기준 3개 | 수평 + 아래 가열(가열면이 위를 향함)은 유리한 쪽이지만 저유속에서는 방향 효과가 남음. 앞 연구 2002 IJHMT 45(20):4079-4095(10.1016/s0017-9310(02)00133-3, C) | C+A |
| 47 | Sudo (1996) | Study on Critical Heat Flux in Rectangular Channels Heated From One or Both Sides at Pressures Ranging From 0.1 to 14 MPa | JHT 118(3):680-688 | 10.1115/1.2822686 | 물, 0.1~14 MPa, G 3.9~28,000 kg/m²s, 입구 아냉 0~328 K, 기존 자료 800여 점 | 저속·출구 아냉 0: 완전 분리 이상류 + 거시 액 하층 모델. 고아냉·고속: 아냉 비등 + 액 하층 모델. 한쪽/양쪽 가열 직사각 유로 CHF 예측 | 한쪽 가열 좁은 직사각 유로 CHF의 표준(원자로 판형 연료) | C+A |
| 48 | Yan, Pan, Ma, Lee PS (2024) | A comprehensive analysis of the gap size influence on boiling crisis in narrow rectangular channels | IJHMT 233:126025 | 10.1016/j.ijheatmasstransfer.2024.126025 | 한쪽 가열 좁은 직사각 유로, 이상류 가시화, 흐름 비등 모델(Scholar 스니펫) | 갭 크기가 비등 위기에 주는 영향 분석(수치 미확인) | 갭별 CHF의 최신 정리. 같은 그룹: 2022 NED 389:111687(가시화 + CHF 상관식, 10.1016/j.nucengdes.2022.111687), 2024 IJHMT 218:124800(CHF 기구 모델, 10.1016/j.ijheatmasstransfer.2023.124800) — 모두 C | C (검색 요약) |
| 49 | Shuai, Kulenovic, Groll (2003) | Heat Transfer and Pressure Drop for Flow Boiling of Water in Narrow Vertical Rectangular Channels | Proc. ICMM2003:667-673 | 10.1115/icmm2003-1084 | 물, 출구 대기압, 2.0×4.0 mm(D_h 2.67)·0.5×2.0 mm(D_h 0.8) | q·G·입구 아냉이 h·ΔP에 주는 영향. 기포류·슬러그·환상류 구분, 예비 양식 지도 | 물 + 0.5 mm급 좁은 유로의 h·ΔP·가시화 | C+A |
| 50 | Mancin, Diani, Rossetto (2016) | Flow boiling heat transfer, dewetting-rewetting, and dryout visualization of HFOs in an asymmetrically heated rectangular plain channel | ATE 107:960-974 | 10.1016/j.applthermaleng.2016.07.020 | R1234ze(E)/R1234yf, 한쪽 가열 직사각 유로, G 50~200 kg/m²s, x 0.2~1, q 50~100 kW/m², Tsat 30 °C | 핵비등 지배. 건조 시작 건도 추정, 직접 관찰로 젖음 상실·재젖음 분석 | 한쪽 가열 유로에서 영상으로 건조·재젖음을 본 선례. 같은 그룹 Diani et al. 2017 HTE 39(3):198-207 "heated from the bottom"(10.1080/01457632.2017.1295733, C) | C (검색 요약) |
| 51 | Liu S, Asano (2026, 사전공개) | Void Fraction of Subcooled Flow Boiling within Horizontal Narrow Channel Measured by Capacitance Sensor | SSRN | 10.2139/ssrn.6753968 | HFC245fa, Tsat 40 °C, 수평 유로 높이 4 mm, 바닥 중앙 가열면 20×50 mm, 표면 처리(용사 코팅, V홈) | 기공률은 q와 함께 증가, 막비등 전이에서 급감. 처리 표면은 응축 덕에 기공률이 낮음. 입구 아냉↑ → 기공률↓ | 수평 + 아래 가열 + 높이 4 mm(3 mm와 비슷). 정전용량 기공률로 영상 투영 기공률을 검증하는 아이디어. 같은 그룹: Liu, Asano, Sugimoto 2026 ExHT 39(6):781-799(10.1080/08916152.2026.2633425, C), Asano et al. 2014 IHTC15(10.1615/ihtc15.fbl.009840, C) | C+A |
| 52 | Monde, Mitsutake (1995) | Enhancement of heat transfer due to bubbles passing through a narrow vertical rectangular channel (Change in heat transfer along flow) | Heat Mass Transfer 31(1-2):77-82 | 10.1007/bf02537424 | 아냉수(40~80 K), 1 atm, 수직 유로 20 × 2 × 450 mm, 공기 기포를 0.125~1.0 s 주기로 주입, 기포 길이 0.01~0.03 m | h는 흐름 방향으로 감소하다 일정해짐. 완전 발달 영역 h는 대류항·계면 증발을 무시한 이론으로 예측 | **공기 주입이라면**: 기포 통과 주기·길이(영상 지표)로 h를 예측한 선례(주제 4와 겹침) | C+A |

### 1-F. 불안정·압력 변동
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 53 | Tadrist (2007) | Review on two-phase flow instabilities in narrow spaces | IJHFF 28(1):54-62 | 10.1016/j.ijheatfluidflow.2006.06.004 | 리뷰(풀·흐름 비등), D_h > 10 mm 채널 요약 후 좁은 공간 | 좁은 공간 불안정은 실험 보고가 많지만 이론은 부족. 이상류의 특성 시간과 모세관 속 기포 성장 시간으로 해석 | 불안정 분석의 틀(특성 시간 비교) | C (INIS 초록 검색 요약) |
| 54 | Wu, Cheng (2003) | Visualization and measurements of periodic boiling in silicon microchannels | IJHMT 46(14):2603-2614 | 10.1016/s0017-9310(03)00039-5 | 물, 실리콘 마이크로채널(학회판 HT2003-47463 초록) | 불안정 3모드: LTAF(저 q·고 G, 중간 진폭 온도·압력 진동, 기포류 지배), CTF(중간, 작은 진폭), LTVAF(고 q·저 G, 큰 진폭) | 0.3/0.7 mm 물 실험의 압력·온도 진동을 양식과 함께 분류하는 틀 | C (학회판 10.1115/ht2003-47463 C+A) |
| 55 | Kandlikar (2006) | Nucleation characteristics and stability considerations during flow boiling in microchannels | ETFS 30(5):441-447 | 10.1016/j.expthermflusci.2005.10.001 | 미세 채널 핵생성·불안정(원문 미확인) | 역류·불안정 대책(입구 제한 등)의 표준 인용 | 0.3 mm 갭 역류 대책 검토용 | C |
| 56 | Lee J, Chae, Chang (2013) | Flow instability during subcooled boiling for a downward flow at low pressure in a vertical narrow rectangular channel | IJHMT 67:1170-1180 | 10.1016/j.ijheatmasstransfer.2013.08.049 | 저압 하향 아냉 비등, 좁은 직사각 유로(Scholar 스니펫: 저 G에서 비등과 flow excursion 가시화) | 좁은 유로 흐름 이탈(OFI) 관찰(수치 미확인) | 좁은 유로의 정적 불안정(흐름 이탈) 사례. Lee J et al. 2015 ETFS 69:86-98(조기·안정 CHF, 10.1016/j.expthermflusci.2015.07.015, C) | C (검색 요약) |

### 1-G. 가시화와 영상–열/압력 측정 연결
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 57 | Matsuda, Kawanami, Orimo, Uete, Watanabe, Egami, Yamaguchi, Niimi (2020) | Simultaneous measurement of gas-liquid interface motion and temperature distribution on heated surface using temperature-sensitive paint | IJHMT 153:119567 | 10.1016/j.ijheatmasstransfer.2020.119567 | 감온 도료(TSP)로 가열면 온도 분포와 계면 운동을 동시 측정(제목 기준). 같은 그룹 학회판: 좁은 유로 흐름 비등 기포 둘레 온도·열유속(IHTC16 2018, 10.1615/ihtc16.bae.021918), 마이크로갭 흐름 비등(IHTC15 2014, 10.1615/ihtc15.fbl.009930) | 내용 미확인 | 불투명 가열면에서 영상과 벽 온도를 같은 시야로 얻는 방법 후보(철 블록 표면에 도포 가능성) | C |
| 58 | Lv, Zhou, Chen, Gao (2023) | Experimental investigation on the evolution of bubble behavior in subcooled flow boiling in narrow rectangular channel based on bubble tracking algorithm | Front. Energy Res. 11:1224306 | 10.3389/fenrg.2023.1224306 | 아냉 흐름 비등, 전체 투명 좁은 직사각 유로, 여러 압력 | 기포 추적 알고리즘으로 이탈 기포 직경·위치 → 핵생성점 밀도·이탈 빈도. 이탈 직경을 기존 모델과 비교, 핵생성점 밀도·이탈 빈도 모델 제안 | 추적 기반 기포 통계를 비등 모델 입력으로 쓴 예(갭 하나). 비슷한 연구: Chen Y et al. 2022 ICONE29(10.1115/icone29-93516, 석영·사파이어 유로, G 400~1500, q 50~300 kW/m², 0.1~0.7 MPa, 이탈 빈도는 Cole 모델과 일치, C+A) | C+A |
| 59 | Lee Haeun, Lee G, Kim K, Kong D, Lee Hyoungsoon (2024) | Multimodal machine learning for predicting heat transfer characteristics in micro-pin fin heat sinks | CSTE 57:104331 | 10.1016/j.csite.2024.104331 | 마이크로 핀핀 흐름 비등(Scholar 스니펫) | 출구 건도·ΔP와 영상 기반 기포 인식을 함께 넣어 h 예측 | 영상 + ΔP → h ML의 선례(갭 효과 없음, 주제 5와 겹침) | C (검색 요약) |

### 1-H. 가열면 재질·두께
| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 60 | Raghupathi, Kandlikar (2017) | Effect of Thermophysical Properties of the Heater Substrate on Critical Heat Flux in Pool Boiling | JHT 139(11) | 10.1115/1.4036653 | 알루미늄·황동·구리·**탄소강**·모넬 400·은·실리콘, 두꺼운 히터 + 문헌 자료 | 점근 두께보다 두꺼우면 표면 온도 요동이 고르게 되어 CHF가 두께와 무관. 그 영역에서는 ρc_p가 중요하고 k는 중요하지 않음. Kandlikar CHF 모델 수정으로 ±15% | 두꺼운 철 블록은 CHF 점근 영역일 가능성(탄소강 ρc_p ≈ 3.6 MJ/m³K, 구리 ≈ 3.4 MJ/m³K, 물성 대략값) | C+A |
| 61 | Golobič, Bergles (1997) | Effects of heater-side factors on the saturated pool boiling critical heat flux | ETFS 15(1):43-51 | 10.1016/s0894-1777(96)00170-7 | 풀 비등 CHF의 가열체 쪽 인자(두께·물성) | 얇거나 열활성이 작은 가열체는 CHF가 낮고, 일정 값 이상이면 점근(2차 인용: #60의 "점근 두께") | 같은 흐름. 열침투율 기반 CHF 상관식: Arik & Bar-Cohen 2003 IJHMT 46(20):3755-3764(10.1016/s0017-9310(03)00215-1, 원문 미확인, C) | C |
| 62 | Magrini, Nannei (1975) | On the Influence of the Thickness and Thermal Properties of Heating Walls on the Heat Transfer Coefficients in Nucleate Pool Boiling | JHT 97(2):173-178 | 10.1115/1.3450337 | 포화수 1 atm, 비금속 봉에 구리·은·아연·니켈·주석 도금(두께 5~250 µm) | 조건에 따라 벽 두께가 h에 영향. 열전도도가 낮을수록 두께 영향이 큼. ΔT = (q/A)^n f(κd, √(κρc))로 ±15% | 낮은 k의 벽(철)에서는 h 자체가 벽 물성에 민감할 수 있음(두꺼운 블록이면 영향 작음) | C+A |
| 63 | Kenning, Yan (1996) | Pool boiling heat transfer on a thin plate: features revealed by liquid crystal thermography | IJHMT 39(15):3117-3137 | 10.1016/0017-9310(96)00006-3 | 얇은 판 + 액정 열화상(원문 미확인) | 낮은 열전도 얇은 벽의 국소 온도 요동(제목 기준) | 국소 벽 온도 요동 측정 방법. 같은 저자 2001 ChERD 79(4):425-436 "Saturated flow boiling of water in a narrow channel"(10.1205/026387601750282553, C) | C |

### 1-I. 서지만 대조한 관련 문헌(내용 미확인, 표에 넣지 않음)
- Bonjour & Lallemand 1997 ICHMT 24(2):191-200, 10.1016/s0735-1933(97)00005-5 (갇힘·압력이 CHF에 주는 영향)
- Misale, Guglielmini, Priarone 2009 IJR 32(2):235-245, 10.1016/j.ijrefrig.2008.06.003 / 2011 ETFS 35(5):772-779, 10.1016/j.expthermflusci.2010.06.009 (HFE-7100 경사·수평 좁은 공간)
- Rops et al. 2009 IJHFF 30(4):751-760, 10.1016/j.ijheatfluidflow.2009.03.007 (갇힌 풀 비등 강화)
- Fujita & Uchida 1990 IHTC9 pp. 153-158, 10.1615/ihtc9.260 (갭·경사·주변 조건)
- Cheng L 2013 HTE 34(13):1016-1043, 10.1080/01457632.2013.763538 (미세 채널 CHF와 갇힌 풀 비등 리뷰)
- Kapitz & aus der Wiesche 2016 HTE 38(3):290-302, 10.1080/01457632.2016.1189258 (Hele-Shaw 셀 갇힌 비등·양식)
- Vermaak et al. 2020 IJHMT 158:119948, 10.1016/j.ijheatmasstransfer.2020.119948 (회전 방향별 불균일 가열 흐름 비등)
- Al-Yahia & Jo 2018 IJHMT 116:136-151, 10.1016/j.ijheatmasstransfer.2017.09.011 (한쪽 가열 좁은 직사각 유로 ONB·OSV·OFI)
- Kureta & Akimoto 2002 IJHMT 45(20):4107-4115, 10.1016/s0017-9310(02)00129-1 (좁은 유로 아냉 CHF 상관식)
- Hetsroni et al. 2005 IJMF 31(4):371-392, 10.1016/j.ijmultiphaseflow.2005.01.003 (병렬 마이크로채널 물의 폭발적 비등)
- Kandlikar 2010 IJTS 49(7):1073-1085, 10.1016/j.ijthermalsci.2009.12.016 (미세 채널 비등의 크기 효과)
- Tachibana, Akiyama, Kawamura 1968 JNST 5(3):117-126, 10.3327/jnst.5.117 / Guglielmini & Nannei 1976 IJHMT 19(9):1073-1075, 10.1016/0017-9310(76)90191-5 (가열체 열활성·두께와 CHF)

## 2. 핵심 질문에 대한 답

### Q1. 갭 높이 효과와 경계 기준
- **현상** (풀 비등, 여러 유체·방향에서 같은 경향)
  - 갭이 기포 이탈 크기 아래로 줄면 h가 오르고, 더 줄면 떨어진다. 물: Katto(#15) 수평 위 향함에서 s ≈ 0.2 mm까지 과열도 감소 후 0.1 mm에서 급반전(C+F). Fujita(#19) 수직에서 중간 갭에 h 최대, 0.15 mm에서 저하(C+F). Kim JS(#6) 수직에서 3·1 mm 강화, 0.5 mm 저하(C+A).
  - CHF는 갭이 줄수록 감소한다(#15, #18, #22, #8, #9, #25). 예외: 아래로 향한 가열면에서는 갭이 줄수록 CHF가 오른다(#10, 물 1~10 mm, C+A).
  - 아냉이면 갇힘이 h를 떨어뜨릴 수 있다(#21, C+F).
- **기구**: 수평·매우 좁은 공간은 납작한 기포 밑 **마이크로층 증발**(#15, #22, #29, #26), 수직은 합체·미끄럼에 의한 **액 교반**(#16, #19). 이 구분은 Cardoso et al.(#23, C+F)의 정리다.
- **경계 기준**
  - Bo_s = s/Lc ≈ 1: Yao & Chang(#17)이 영역이 Bo_s <, ≈, > 1에 따라 달라짐을 보였다(C, 2차 인용). Stutz(#22)는 CHF가 s ≈ Lc에서 크게 변함을 보였다(C+F). Cardoso(#23)는 Bo_s > 1이면 증기층이 덮개에 붙어 가열면과 상호작용하지 않고, Bo_s < 1이면 마이크로층이 생긴다고 정리했다(C+F).
  - 최적: DHF 최대 Bo_s ≈ 0.4(#23, FC72·작은 원판, C+F). 물 1 mm가 Bo_s 0.4에 해당하고 #24가 이 조건에서 측정했다(C+A).
  - 저하 쪽 경계: Bo_s < 0.3이면 DHF가 주변 액 공급에 지배된다(#23). 물에서 저하가 보인 갭은 0.5 mm(#6, Bo_s 0.2), 0.15 mm(#19), 0.1~0.2 mm(#15, Bo_s 0.04~0.08). (H/Lc)² 표기로는 저하 위험이 Bo ≲ 0.04~0.1 → **0.3 mm(0.014)는 저하 위험권, 0.7 mm(0.078)는 경계**.
  - 고립 기포 영역 vs 합체 기포 영역: Ishibashi & Nishikawa(#16)가 처음 구분했고, Bonjour & Lallemand(#20)가 Bo–환산 열유속 지도로 세 영역(고립 변형 기포 / 합체 / 부분 건조)을 정리했다(C, 검색 요약).
- **D_h 기준과 H 기준의 차이**(가설 1과 직접 관련): 넓은 갭은 D_h ≈ 2H라서 Kew–Cornwell Co = Lc/D_h(#45)로는 3 mm가 0.42(< 0.5, "거시")로 분류된다. 그러나 H 기준 Bo_s = 1.2로 전이 구간이다. 좁은 공간 비등 문헌은 처음부터 D_h가 아니라 **갭 s 자체**를 썼다(#17, #22, #23). Harirchian & Garimella(#42)는 갇힘에 G도 넣었다.

### Q2. 한쪽 가열(특히 아래 가열) 좁은 유로의 흐름 비등
- **다섯 갭에 대한 문헌상의 예상** (수평 + 아래 가열 + 위 투명 덮개, 비등일 때)
  - 7 mm: 증기가 덮개 밑에 모여 층을 이루고 가열면은 젖어 있다(#23 Bo_s > 1, #9 큰 합체 기포가 위쪽 차지, #4 소수성 덮개). h는 비갇힘 흐름 비등과 비슷하고, 증기가 갭을 채우면 CHF가 떨어진다(#4, #8).
  - 3 mm: 전이 구간(#22). 큰 기포만 가열면에 닿는다. 덮개 젖음성이 결과를 가른다(#4: 갭 > 1 mm에서 중요).
  - 1 mm: 강화 최적 부근(#23, #24, #6). 그래도 저유량이면 방향 효과가 남는다(#13: G ≥ 400 kg/m²s, Fr ≈ 0.8에서야 방향 무관).
  - 0.3·0.7 mm: 갇힌 슬러그·환상류(#34, #41, #32). h는 오를 수 있지만 조기 건조·CHF 저하(#41, #30), 역류·압력 진동(#3, #2, #37, #54).
- **마이크로갭(0.01~1 mm)**: 환상류 지배, h–건도 M자 곡선, Chen식이 환상류에서 맞음, IR에서 약 20 K 변동(#34, #35, C+A). 극소 갭 10 µm·약 5 kW/cm²(#39). 마이크로갭은 병렬 마이크로채널보다 역류가 적다(#37, C+A).
- **넓은 수평 갭의 상관식**: Lee & Lee(#40, R-113, 0.4~2 mm)는 작은 갭·저 G에서 액막 두께가 지배한다고 보고 수정 F를 냈다(C+A). 물 0.3/0.6/3 mm에서는 Lee–Mudawar식이 MAE 5.6%로 가장 정확했다(#1, C+A). 물 0.5~2 mm에서는 Liu–Winterton·Shah(아냉), Sun–Mishima·Kandlikar(포화)가 가장 정확했다(#2, C+A). 범용식 Kim & Mudawar(#44)는 가열 둘레 처리가 있지만 세부는 미확인(C).
- **원자력 좁은 직사각 유로**: 한쪽/양쪽 가열 CHF는 Sudo(#47) 모델이 표준(C+A). 최근 중국 연구가 갭 크기와 비등 위기를 정리했다(#48, C). 국내 KAIST의 저압 하향류 불안정(#56, C). 수평 아래 가열 물 흐름 비등을 갭별로 다룬 원자력 연구는 찾지 못했다.
- **방향**: 한 벽 가열 FC-72에서 유속 < 0.2 m/s면 CHF가 방향에 매우 민감하고, 아래로 향한 가열벽에서 매우 낮다(#46, C+A). 사용자의 아래 가열(가열면이 위를 향함)은 유리한 쪽이다. 단 수평 가열면은 아래·위 가열 모두 불안정에 가장 취약했다(#3, C+A).

### Q3. 불안정·압력 변동
- 좁은 공간 특유의 불안정
  - 저열유속에서 비등이 켜졌다 꺼지는 약 0.01 Hz 진동(#22, 펜탄), 셀 침수로 끊기는 간헐 비등(#26, 물 Hele-Shaw). 인공 핵생성점 하나로 안정(#26).
  - 천이 비등에서 덮개 액막이 약 15 Hz로 건조 가열면을 적심(#22).
  - 수평 양끝 개방 유로에서 기포가 한쪽 출구로만 빠지는 순환 흐름(#9).
- 흐름 비등
  - 0.5 mm 높이 수평 유로에서 이상 혼합 / 약한 역류 / 강한 역류. 수평 가열면이 가장 취약. G가 클수록 심함(#3, C+A).
  - 물 미니갭 0.5~2 mm의 sweeping flow 구간에서 불안정. ΔP가 양식에 따라 세 구간(#2, C+A).
  - 물 마이크로채널의 3모드(LTAF/CTF/LTVAF): 모드별 온도·압력 진동 진폭이 다름(#54, C+A 학회판).
  - 마이크로갭은 병렬 채널보다 불안정이 적음(#37). 갭이 작을수록 진동이 억제됐다는 학위논문 스니펫도 있다(Zhao 2020 학위논문, U: DOI 없음).
- 측정법: 대부분 고속 영상과 압력·벽 온도 동기 측정(#3, #54, #32). 특성 시간(기포 성장 vs 이상류 통과)으로 해석하는 틀(#53, C).

### Q4. 가시화 방식과 정량 지표
- **투명 덮개 너머로 불투명 가열면을 위(또는 앞)에서 본 연구**: #15(유리 원판), #22(플렉시글라스 + 내시경 250 fps), #7·#6(유리창), #4·#5(덮개), #39(유리 덮개 + 실리콘 아래 가열), #35(사파이어 창 너머 IR), #26(Hele-Shaw), #11(2000 fps), #1(양식 가시화).
- **뽑은 정량 지표**
  - 양식 분류(대부분), 젖은 폭/건조 영역(#19 W = 2.5 mm, #7 건조 영역과 액체 하층), 액막 접촉 빈도(#22 15 Hz), 기포 빈도·통과 시간·기공률(#20, 열선), 이탈 직경·이탈 빈도·핵생성점 밀도(#58 추적 알고리즘), 등가직경·속도·3D 기공률(#11, ML 추적 + IoU), 기포 변형(#24, ImageJ), 젖음 상실·재젖음(#50).
- **영상 지표를 h·ΔP와 연결한 시도**
  - 가장 강한 예: Jagirdar & Lee(#32). 고주파 벽 온도 역해석으로 과도 h를 구해 영상과 동기했다(0.14~0.42 mm, 물, C+A).
  - 고전: Fujita(#19)의 젖은 폭 기반 비등 곡선 모델(C+F).
  - IR·TSP: #35, #34(벽 온도 변동 ↔ 국소 건조), #57(TSP로 계면 운동 + 온도 동시).
  - ML: #59(영상 + ΔP + 건도 → h), #12(ANN, 입력 미확인), #11(ML 추적 + 벽 온도, 상관 분석은 사전공개 초록 수준).
  - **찾지 못한 것**: 기포별 통계(투영 기공률, 계면 길이 밀도, 피복 비율, 갇힌 기포 비율)를 여러 갭에서 h·ΔP에 회귀한 연구.

### Q5. 가열면 재질(철·스테인리스)과 두께
- CHF: 얇거나 열활성이 작은 가열체는 CHF가 낮다(#61, C). 점근 두께 이상이면 두께와 무관하고 ρc_p가 중요하며 k는 중요하지 않다(#60, 탄소강 포함 7종, C+A). 두꺼운 철 블록이면 CHF는 점근 영역일 가능성이 크다.
- h: 얇은 벽에서는 두께·물성이 h에 영향을 주고, k가 낮을수록 두께 영향이 크다(#62, 물, C+A).
- 국소 온도 요동: 낮은 열침투율 벽은 기포 밑 국소 온도 요동이 크다(#63 C, #35 약 20 K, #34). 열침투율 대략값: 구리 ≈ 37, 탄소강 ≈ 13, 스테인리스 ≈ 8 kJ/(m²·K·s^0.5)(물성 대략값).
- 사용자 실험에 주는 뜻
  - (1) 블록 속 열전대는 시간·공간 평균 온도를 본다. 기포 주기의 요동은 보지 못한다.
  - (2) k가 낮아 표면까지 외삽 오차가 크고 측면 전도·공액 효과가 크다(주제 6).
  - (3) 갭마다 같은 블록을 쓰면 재질 효과는 상쇄되지만, 0.3 mm처럼 국소 건조가 생기면 철 표면의 국소 과열이 구리보다 크다.
  - 스테인리스 가열판 + 물 + 마이크로갭의 선례는 #12다.

### Q6. 새로움 판단
- 다섯 요소를 모두 한 연구는 찾지 못했다(4장 기록): 물, 0.3~7 mm 다섯 갭(서브 mm와 > 2Lc 포함), 위에서 본 고속 영상 + AI 기포 통계, h, ΔP.
- 부분적으로 겹치는 연구
  - 갭 묶음: #1(물 흐름, 0.3/0.6/3 mm), #2(물 흐름, 0.5~2 mm), #8(에탄올 수평 아래 가열, 0.5~8 mm, 풀), #15(물 수평, 0.1~10 mm, 풀), #4·#5(물 수평 0.64~5 mm, 풀), #6(물 수직 0.5~3 mm), #10(물 1~10 mm, 풀), #14(물 0.5~5 mm, 닫힌 갭).
  - 방법: #11(ML 추적 + IoU + 벽 온도, 0.5~15 mm 풀), #32(벽 온도–영상 동기, 0.14~0.42 mm 물 흐름), #12(스테인리스 + 물 + 마이크로갭 + ΔP + ANN), #59(영상 + ΔP → h).
- 판단: "서브 mm부터 7 mm까지 갇힘 전이를 가로지르는 물 흐름 비등에서, AI 기포 통계로 갇힘·피복을 정량화해 h·ΔP 변화를 설명"하는 조합은 새롭다고 볼 수 있다. 단 풀 비등에서 Bo_s 기준 전이는 고전이므로(#17, #22, #23), 기여는 **흐름 조건 + 영상 정량화 + ΔP를 함께**에 있다고 써야 한다.

## 3. 아이디어와 시사점
- **A. 다섯 갭을 세 기구 구간으로 묶는 틀** (가설 1 보강)
  - 0.3·0.7 mm(Bo_s ≤ 0.28): 마이크로층·액 공급 지배. 1 mm(0.4): 강화 최적 부근. 3 mm(1.2): 전이. 7 mm(2.8): 덮개 증기층 + 젖은 가열면.
  - 문헌이 예측하는 순서를 흐름 비등에서 확인하고, 경계를 영상 지표로 정량화하는 것이 논문의 줄기가 될 수 있다.
  - 필요한 것: 같은 G·q·아냉에서 다섯 갭 비교, 갭마다 같은 철 블록.
- **B. 영상 지표**
  - "갇힌 기포 면적 비율"(등가직경 > 2H 등)과 "합체 기포 비율"(#16, #20).
  - 0.3/0.7 mm는 "건조 패치 면적 비율"(#7, #19).
  - 3·7 mm는 기포가 가열면에 닿는지 판정이 핵심이다(#4, #23). 위 영상만으로는 구분이 어렵다. 검증 수단 후보:
    - (i) 옆에서 보는 보조 카메라.
    - (ii) 덮개를 바꿔 기포가 덮개에 붙는 정도를 바꾸는 대조 실험(#4).
    - (iii) 기포 내부가 어둡게 보이는 원인이 "가열면 접촉"인지 확인하는 실험. 예: 7 mm에서 덮개에 붙은 기포와 0.3 mm 갇힌 기포의 밝기 분포 비교.
- **C. 덮개 젖음성을 기록·고정**(#4, #5): 접촉각을 재서 보고한다. 실험 중 오염으로 바뀌지 않게 관리한다. 친수 덮개면 1 mm 넘는 갭에서 가열면 위 증기 슬러그가 생긴다.
- **D. 불안정** (#3, #2, #54)
  - 고주파 압력(≥ 1 kHz 권장)과 카메라 시간을 맞춘다. 영상의 기포 통과 빈도와 ΔP 스펙트럼을 대응시킨다.
  - 0.3 mm에서는 역류 사례를 영상 추적의 "역방향 속도"로 자동 검출할 수 있다(추적 파이프라인의 장점).
- **E. 상관식 평가 + 오차 설명**
  - 다섯 갭 자료로 #40·#44·#1의 Lee–Mudawar·#2의 Liu–Winterton/Shah/Sun–Mishima/Kandlikar를 평가한다.
  - 갭별 오차를 영상 지표(갇힌 기포 비율, 피복 비율)로 설명하면 "D_h 상관식이 놓치는 갇힘"(가설 1)의 정량 근거가 된다.
- **F. 열측정**
  - #32처럼 블록 속 열전대 응답으로 과도 해석을 하기는 철에서 어렵다(낮은 k). 시간 평균 h를 주 지표로 하고, 국소 요동은 박막 열전대·TSP(#57)를 선택지로 둔다.
- **위험**
  - 공기 주입이면 마이크로층 증발 기구가 해당하지 않는다(#52, 주제 4 문헌으로 바꿈).
  - 가열면이 바닥 일부(작은 원판)면 가장자리 액 공급이 결과를 바꾼다(#1, #23: Bo_s < 0.3에서 주변 조건 지배).
  - 아냉 조건이면 갇힘 효과의 부호가 바뀔 수 있다(#21).

## 4. 새로움 판단 기록 (검색어와 결과)
- Google Scholar(WebFetch, 총 7회)
  1. `"narrow gap" OR "microgap" flow boiling water "gap height" high-speed visualization heat transfer coefficient pressure drop` → 약 77건 중 1쪽 10건. 갭 여러 개 + 물 + AI 통계 조합 없음. 마이크로갭 흐름 비등(Han 2016, Lorenzini 2019 학위논문, Moreira 2023 테이퍼, 공기 주입 기포로 마이크로갭 핵생성을 흉내 낸 Green 2022 학위논문).
  2. `Bonjour Lallemand "flow patterns during boiling in a narrow space" Bond number regimes` → 1건(#20).
  3. `"flow boiling" "narrow gap" OR "narrow channel" OR "microgap" bubble "deep learning" OR "U-Net" OR "convolutional" "heat transfer coefficient" "pressure drop"`(2015~) → 9건. 가까운 것: #11, #12, #59.
  4. `"horizontal" "narrow rectangular channel" flow boiling "heated from below" OR "bottom heated" OR "one-side heated" flow pattern visualization` → 28건 중 10건(#48, #50, #56 등).
  5. `Alam Lee Yap Jin microgap heat sinks "optimum" gap height` → 약 33건(#36의 110~500 µm, Lorenzini & Joshi 2016이 인용한 80~1000 µm).
  6. `"flow boiling" water "gap" "0.3 mm" "1 mm" "3 mm" "7 mm" rectangular channel` → 4건. 관련은 #1뿐.
  7. `"confined boiling" OR "narrow gap" OR "microgap" boiling bubble "image processing" OR "machine learning" OR "deep learning" "gap size" heat transfer`(2018~) → 25건 중 10건(#11, #24, Tang et al. 2024 좁은 유로 기포 운동 영상 처리, 원자력 CCFL).
- WebSearch(standard)
  - 갇힌 풀 비등 리뷰, Asano 수평 좁은 유로, Soffer, Rops, Geisler, Alam(2회), Lee & Lee, Kim & Mudawar, Tadrist, Mancin, Yan 2024, Rukhsar, Zhu 2023.
  - `boiling narrow gap "0.3 mm" "0.7 mm" "1 mm" "3 mm" water` → 정확히 이 갭 묶음의 비등 연구 없음. 가까운 것: #14(5/3/0.9/0.5 mm), #5(0.64/1/2/3/5 mm), #10(1/2/5/10 mm).
- Crossref(query.bibliographic, 약 40회): narrow gap boiling, confined boiling review, microgap flow boiling, gap height effect water, horizontal narrow rectangular channel bottom heated, minigap, Hele-Shaw boiling, 일본어(狭隘流路 沸騰) 등.
  - 새로 찾은 것: #1, #2, #3, #8, #9, #26, #33, #51.
- 결론
  - "물 + 흐름 비등 + 0.3~7 mm + 위 영상 AI 통계 + h + ΔP"는 0건.
  - "물 + 흐름 비등 + 서브 mm와 mm 갭 동시"는 #1(0.3/0.6/3 mm), #2(0.5~2 mm)뿐이다.
  - "7 mm(> 2Lc)까지 포함한 흐름 비등 갭 비교"는 찾지 못했다.
- 한계
  - ScienceDirect·ASME·T&F·SSRN·Purdue 엔지니어링 서버·DTIC·MDPI가 막혀 Elsevier 논문은 초록을 거의 못 봤다.
  - OpenAlex는 429였다. 중국어·한국어 학술지(원자력 좁은 유로)는 거의 보지 못했다.

## 5. 남은 의문과 사용자에게 확인할 것
- **사용자에게 확인**
  1. 기포가 비등(증기)인가 공기 주입인가. 공기면 이 주제의 기구는 대부분 해당하지 않는다.
  2. 채널 방향. 수평 + 아래 가열인가.
  3. 가열 면적. 바닥 전체인가 일부인가. 일부면 가장자리 액 공급 효과(#1, #23).
  4. 덮개 재질과 접촉각(#4, #5).
  5. 입구 아냉도(#21: 아냉이면 갇힘 효과가 반대일 수 있음).
  6. 유량 범위. 저유량이면 방향 효과가 남는다(#13, #46).
  7. 압력 센서 응답 주파수와 카메라 동기 여부.
  8. 0.3·0.7 mm 단열 실험에서 본 양식이 비등에서도 유지될지. 가열하면 0.3 mm에서 역류·간헐 비등 가능(#3, #26).
- **확인 못 한 것**
  - #36 최적 갭 범위의 수치, #37 계열 논문들의 수치(물 여부 포함).
  - #44의 한쪽 가열 처리 방식, #25의 수치, #48의 갭별 CHF 수치.
  - #2의 방향·가열 방식, #4의 유체(물로 추정).
  - Fujita et al. 1988 IJHMT(#19 비고)·Bonjour & Lallemand 1998(#20)·Ishibashi & Nishikawa 1969(#16)·Yao & Chang 1983(#17) 원문.
  - Rops 2009, Misale 2009/2011 내용.
  - DTIC 보고서 ADA543244(실리콘 마이크로갭 190/285/380 µm, 물, NUS 계열로 추정): 403으로 못 읽음.

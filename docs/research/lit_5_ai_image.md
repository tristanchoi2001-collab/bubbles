# 주제 5: AI 영상 분석과 데이터 기반 예측 (2026-10-23)

범위: 갭 H = 0.3/0.7/1/3/7 mm. 최우선 질문은 "영상으로 상관식을 개선한 선행 연구가 이미 있다면 우리는 무엇이 새로운가"다.
확인 수준: C+F(Crossref + 원문), C+A(Crossref + 초록), C(Crossref만, 내용은 2차 자료), U(Crossref 대조 못 함·DOI 없음).
문헌 번호 [n]은 1장 표의 번호다. 서지는 `refs_5_ai_image.tsv`.

## 0. 요약
- **"영상 지표로 h·CHF 모델을 개선"은 이미 있다.** Huang et al. 2024 IJMF [1]이 대표다(같은 그룹 Chang 2023 [2], 박사논문 [3]). 다만 범위가 좁다.
  - 자료: FC-72, 2.5 × 5 mm 직사각 채널 하나, 미소중력 포물선 비행, 한쪽 가열, 10개 사례. 옆에서 찍었다.
  - h: 젖음 전선/증기 덩어리 길이로 시간 가중 h를 만들었다. 상관식 13개 중 5개는 MAE가 크게 줄었지만 8개는 나빠졌다. 가장 좋은 MAE는 15.9% → 28.2%로 오히려 커졌다. 개선은 주로 "하류로 갈수록 h가 준다"는 경향이다(원문 Table 2) [1].
  - 상(相) 속도는 측정하지 않고 기공률과 에너지 균형으로 계산했다. ΔP는 쟀지만 모델링하지 않았다. 오차 전파·조건 밖 검증·자료 공개가 없다 [1].
- **영상(이벤트 카메라) 지표 → ΔP**는 박사논문 1편 [3]뿐이다. 통계 모델(MLP)이고 비등, 채널 하나다(운전 조건만 쓴 모델보다 RMSE 33.8% 감소).
- 비AI 영상으로 잰 기포 길이·수를 ΔP 모델에 넣는 것은 미세채널 Taylor 흐름에서 오래된 방법이다(Kurimoto 2019 [13], Fuerstman 2007 [14]).
  얇은 갭 2D 거품에서는 "압력 구배 = 경계선 길이당 마찰 × 경계선 길이 밀도" 꼴의 식이 이미 쓰인다(Raufaste 2025 [15], h = 0.9 mm). → 가설 2의 "둘레당 마찰" 틀 자체는 새롭지 않다.
- **찾지 못한 것(새로움 후보)**: (a) 넓고 납작한 갭 여러 개(서브 mm ~ mm)에서, (b) 자동 검출·추적으로 잰 개별 기포 운동학(기포별 속도 → Ca)과 둘레·개수를, (c) 같은 장치의 측정 ΔP(와 이후 h)에 물리 모델로 연결하고, (d) 검출·추적 오차를 실데이터 표본 감사로 재서 모델 계수까지 전파한 연구. 검색 기록은 4장.
- 0.3·0.7 mm 단열 실험은 ΔP 쪽이라 [1]~[3]과 겹치지 않는다. 가장 가까운 것은 [13], [15], [3]이다.
- 불투명 강철 바닥 + 투명 뚜껑 + 위에서 촬영 + U-Net은 Schepperle 2024 [8]이 있다(0.5 mm 깊이 단일 미세채널, 비등). 갭을 바꾸거나 추적한 연구는 아니다.
- 검출·분할 오차가 물리량으로 가는 양은 합성 영상으로만 일부 정량화됐다(기공률 오차 약 12%, Hessenkemper 2022 [28]; 둘레 이산화 오차 최대 13.8%, [55]). 실데이터 추적 오류를 사람 표본으로 재고 신뢰구간을 낸 기포 연구는 찾지 못했다.

## 1. 문헌 표

### 1-A. 영상 지표 → 상관식·모델(h, ΔP, CHF) — 신규성 판단의 핵심

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 1 | Huang, Chang, Suh, Mudawar, Won, Kharangate (2024) | Machine learning boiling prediction: From autonomous vision of flow visualization data to performance parameter theoretical modeling | IJMF 179:104928 | 10.1016/j.ijmultiphaseflow.2024.104928 | Purdue 자료(Konishi 2015). FC-72, 2.5×5 mm 직사각, 가열 길이 약 80 mm 분석, 한쪽 가열, 미소중력(포물선 비행), 10, 20, 40 g/s, 10개 사례, 옆에서 2000 fps | Mask R-CNN 지표(재현율·정밀도·F1 > 87%). 기공률 모델: 분리류 MAE 3.8%, HEM 59.3%. h: 상관식 13개 중 5개 개선(예: Lazarek 233.6→28.2%), 8개 악화(예: Kim·Mudawar 24.9→70.4%, Hamdar 15.9→64.5%). CHF: Tong 오차 26.8~54.3% → 1.2~38.2%, 개정 수력학 불안정 모델 10/7/11% | 가장 가까운 "영상→h" 선행. 채널 하나·비등·옆 촬영. 상 속도 계산값(측정 아님), ΔP 모델 없음, UQ 없음, 자료 비공개 명시. 같은 내용의 학회판: Huang et al. 2024 ITherm, 10.1109/itherm55375.2024.10709607 | C+F (Suh 연구실 공개 PDF) |
| 2 | Chang, Suh, Shingote, Huang, Mudawar, Kharangate, Won (2023) | BubbleMask: Autonomous visualization of digital flow bubbles for predicting critical heat flux | IJHMT 217:124656 | 10.1016/j.ijheatmasstransfer.2023.124656 | [1]과 같은 자료(가열 길이 114.6 mm). 30,000장, 기포 155,000개, 특징 10개 | 계면 이탈(ILM) 모델의 b를 영상값(0.14/0.20/0.46)으로 바꿔 CHF 오차 39/22/1%. 잘린 기포 16~35% 제외. 다중 선형회귀(사례 약 10개)로 특징 중요도: 파장이 h·열유속에 가장 큼. 추적으로 기포 속도 측정(평균 약 0.5/0.9/1.8 m/s) | 추적 속도를 쟀지만 모델에는 회귀 특징으로만 썼다. "창(window) 효과"를 한계로 명시 → 우리 시야와 압력 탭 구간 문제와 같다. 같은 자료인데 [1] Table 3의 ILM 개정값(8.5/15.3/35.1 vs 실측 28.8/34.2/40.6 W/cm²)은 오차 약 70/55/14%로 다르다(내가 계산, 입력 정의에 민감) | C+F (Suh 연구실 공개 PDF) |
| 3 | Chang, S. (2026) | Boiling Intelligence: Vision-Based and Event-Driven Flow Boiling Analysis (박사논문, UC Irvine) | - | DOI 없음 (escholarship.org/uc/item/8gx8t5td) | 3장 = [1] 재서술. 4장: 지상 비등, Flutec PP1, 2.5×5 mm(Dh 3.33 mm) 폴리카보네이트, 구리 히터 100 mm, 이벤트 카메라. 12/15/18 g/s × 열유속 8단계 = 24 조건 | 이벤트 지표(상대 변동 F, 스펙트럼 엔트로피 H) + 운전 조건 → MLP로 평균 ΔP. LOOCV: RMSE 0.1419→0.0940 kPa(−33.8%), R² 0.978→0.9915. Ridge는 −7.3%. 저자: "ΔP 측정을 대신하지 않는다" | 유일하게 찾은 "영상계 지표 → ΔP". 통계 모델, 비등, 채널 하나, 개별 기포 아님. 3장은 [1]보다 h 개선을 강하게 서술(논문 Table 2와 차이) | U (원문 읽음) |
| 4 | Naderi et al. (2026) | Large-scale vision-based interfacial characterization for heat transfer prediction in horizontal mini-channel flow boiling | ATE 303:132079 | 10.1016/j.applthermaleng.2026.132079 | 지상 수평 미니채널 흐름 비등(제목 기준). SSRN 6505385 선행판 | 원문·초록 확인 못 함 | 수평 + 영상→h. 내용 확인이 꼭 필요한 최근 경쟁 문헌 | C |
| 5 | Kharangate, Naderi, Ji, Narayanan et al. (2025) | Applying Computer Vision to Flow Boiling Analysis: Feature Extraction and Data-Driven Heat Transfer Coefficient Prediction | SSRN (posted content) | 10.2139/ssrn.5914773 | 흐름 비등, 미니·미세채널(검색 요약) | Scholar 요약: 기공률 α가 h 예측에 들어가고 길쭉한 기포가 있는 미니·미세채널에서 민감도가 크다 | [4]와 같은 계열로 보인다. 데이터 기반 h 예측 | C (검색 요약 기준) |
| 6 | Sun, Cheng, Wang, Xie, Zhang et al. (2026) | Deep learning-enhanced investigation of R134a/R245fa flow boiling in microchannels | ICHMT 172:110611 | 10.1016/j.icheatmasstransfer.2026.110611 | 미세채널 흐름 비등, R134a/R245fa | Scholar 요약: 기포 성장 억제 계수(BGSF)로 미시 기포 거동을 h에 연결, 기존 상관식 부적합 | 미세채널 영상→h의 또 다른 예. 수치 미확인 | C (검색 요약 기준) |
| 7 | Zhang, Chang, Suh, Won (2026) | Multi-modality fusion: Illuminating the complexity of two-phase flow | AI Thermal Fluids 5:100028 | 10.1016/j.aitf.2026.100028 | 광학 + 움직임 정보 융합 분할(미세흐름·흐름·풀 비등) | 기준 모델보다 20~40% 개선, 기포 면적·종횡비 오차 약 20%. 서론에서 "기공률·젖음 전선이 h 상관식을 개선"의 근거로 [1]만 인용 | 이 분야가 [1]을 대표 사례로 본다는 근거 | C+F (본문 일부) |
| 8 | Schepperle, Junaid, Woias (2024) | Computer-Vision- and Deep-Learning-Based Determination of Flow Regimes, Void Fraction, and Resistance Sensor Data in Microchannel Flow Boiling | Sensors 24(11):3363 | 10.3390/s24113363 | 물, 미세채널 깊이 0.5 × 폭 1.5 × 길이 65 mm를 **스테인리스 블록**에 가공, 박막 Pt 측온저항(RTD)이 붙은 **Pyrex 뚜껑 위에서** 2000 fps, 카메라–RTD 동기 | U-Net Dice 99.1%, 유동 양식 분류 91%, 영상으로 RTD 값 예측 MSE < 10⁻⁶ | 촬영 형상(불투명 강철 + 투명 뚜껑 + 위)이 우리와 가장 비슷하다. 갭 하나, 추적·ΔP 없음 | C+F (Europe PMC) |
| 9 | Suh, Bostanabad, Won (2021) | Deep learning predicts boiling heat transfer | Sci Rep 11:5622 | 10.1038/s41598-021-85150-4 | 풀 비등, 평판 구리, 연속 실험 4회 | VGG16 + Mask R-CNN 기포 통계(크기는 열유속에 선형, 개수는 지수 감소) → 열유속 평균 오차 6% | 영상→열유속 회귀. 형상 고정 | C+F |
| 10 | Hobold, da Silva (2019) | Visualization-based nucleate boiling heat flux quantification using machine learning | IJHMT 134:511-520 | 10.1016/j.ijheatmasstransfer.2018.12.170 | 풀 비등(직·간접 가시화) | 신경망 열유속 오차 최소 7%(초록) | 영상→열유속 초기 사례 | C+A |
| 11 | Zhang L., Wang, Su, Kossolapov, Aguiar, Seong, Chavagnat, Phillips, Rahman, Bucci (2023) | A unifying criterion of the boiling crisis | Nat Commun 14:2321 | 10.1038/s41467-023-37899-7 | 적외선(투명 히터) 기포 통계, 여러 표면·풀/흐름 비등·물/액체질소 | 핵생성 밀도, 평균 발자국 반경, 성장시간×이탈빈도 3개로 CHF 임계면(초록) | 영상 통계 → 물리 기준식 + **조건 밖 일반화**의 모범. 우리 검증 설계의 기준 | C+A |
| 12 | Khodakarami et al. (2022) | Machine learning enabled condensation heat transfer measurement | IJHMT 194:123016 | 10.1016/j.ijheatmasstransfer.2022.123016 | 액적 응축 | 원문 미확인 | 영상→열전달(응축) 사례 | C |

### 1-B. 비AI 영상 측정 + ΔP·h (다중 크기, 갇힌 기포)

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 13 | Kurimoto, Tsubouchi, Minagawa, Yasuda (2019) | Pressure drop of gas–liquid Taylor flow in square microchannels | Microfluid Nanofluid 24(1):5 | 10.1007/s10404-019-2307-x | N2–물/글리세린 수용액, 정사각 미세채널 Dh 190/298/505 µm, 2.0×10⁻³ < Ca_T < 0.132 | 고속 영상으로 기포 속도·기포 길이·액체 슬러그 길이 → 단위 셀 모델. 기존 모델과 큰 차이 → 액막 두께 기반 기포당 ΔP 모델 새로 제안 | 서브 mm, 크기 3종, 영상 지표→ΔP(물리). 단 일렬 Taylor 기포, 수동·고전 영상 처리 | C+F (고베대 저장소) |
| 14 | Fuerstman, Lai, Thurlow, Shevkoplyas, Stone, Whitesides (2007) | The pressure drop along rectangular microchannels containing bubbles | Lab Chip 7(11):1479 | 10.1039/b706549c | 네 벽에 닿는 기포, 계면활성제 농도 변화 | ΔP는 주로 **기포 개수**로 정해진다. 중간 농도에서는 기포 총길이가 지배(초록) | "기포 수 → ΔP"의 원형. 0.3 mm 갇힌 기포에 직접 비교 대상 | C+A |
| 15 | Raufaste, Rose, Santucci, Dollet (2025) | Friction-induced bubble edge curvature in flowing 2D confined foams | PRF 10(2):023301 | 10.1103/physrevfluids.10.023301 | 2D 거품 단층, Hele-Shaw h = 0.9 mm, 폭 15 cm, 길이 46 cm, V0 3.5~20 mm/s, 기포 면적 9.5~39.7 mm² | 힘 균형 ∇P·L·w·h = 2 f_v ℓ_proj N_bub, f_v ∝ γCa^(2/3)(K_f 5.1→8.2로 맞춤). 영상의 경계 곡률이 모델과 일치. Plateau 경계 반경 91~143 µm는 수동 측정 | 가설 2의 "둘레당 마찰 × 둘레 밀도" 틀이 이미 있다. 단 ΔP는 측정이 아닌 추정, 건조 거품, 갭 하나. 마찰 법칙 출처: Raufaste et al. 2009 PoF 21:053102 (10.1063/1.3142502, C) | C+F (HAL) |
| 16 | Chung, Kawaji (2004) | The effect of channel diameter on adiabatic two-phase flow characteristics in microchannels | IJMF 30(7-8):735-761 | 10.1016/j.ijmultiphaseflow.2004.05.002 | 단열, 여러 직경 미세채널(제목) | 원문·초록 확인 못 함 | 크기를 바꾼 단열 영상 + ΔP 선행(고전) | C |
| 17 | Alam, Lee, Yap, Jin, Balasubramanian (2012) | Experimental investigation and flow visualization to determine the optimum dimension range of microgap heat sinks | IJHMT 55(25-26):7623-7634 | 10.1016/j.ijheatmasstransfer.2012.07.080 | 마이크로갭 비등, 갭 치수 변화(제목) | 원문 확인 못 함(주제 2 참고) | 여러 갭 + 가시화 + h·ΔP의 가장 가까운 비등 선행. 영상은 정성적으로 보인다(미확인) | C |
| 18 | Harirchian, Garimella (2012) | Flow regime-based modeling of heat transfer and pressure drop in microchannel flow boiling | IJHMT 55(4):1246-1260 | 10.1016/j.ijheatmasstransfer.2011.09.024 | 여러 크기 미세채널 비등(제목) | 원문 확인 못 함 | 유동 양식(범주)별 h·ΔP 모델. 연속 영상 통계가 아니라 양식 판정 수준 | C |

### 1-C. 마이크로채널·얇은 갭·불투명 배경의 영상 처리

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 19 | Jegorovs, Birjukovs, et al. (2024) | Optical imaging of MHD bubble flow in Hele-Shaw liquid metal cells | Exp Fluids 65(8):113 | 10.1007/s00348-024-03856-3 | 불투명 액체금속, Hele-Shaw 160×88×3 mm³ | 한쪽 벽에 닿은 기포의 윤곽을 옆 조명으로 밝혀 찍음. 고전 임계값 분할 + 조각난 윤곽을 관계 그래프로 묶음 | 불투명 매질 + 한쪽에서 촬영 + 밝은 테두리라는 점이 우리와 비슷 | C+F (arXiv 2311.06288) |
| 20 | Bouche, Roig, Risso, Billet (2012) | Homogeneous swarm of high-Reynolds-number bubbles rising within a thin gap. Part 1. Bubble dynamics | JFM 704:211-231 | 10.1017/jfm.2012.233 | 얇은 갭 기포군(갭 값은 초록에 없음) | 영상 추적으로 속도 분산·분산계수가 기공률에 거의 선형(초록) | 얇은 갭에서 개별 기포 추적 → 통계의 고전 선례(주제 1 참고) | C+A |
| 21 | Fu, Liu (2016) | Development of a robust image processing technique for bubbly flow measurement in a narrow rectangular channel | IJMF 84:217-228 | 10.1016/j.ijmultiphaseflow.2016.04.011 | 좁은 직사각 채널 기포류 | 원문 미확인. 같은 저자 학위논문(2018)은 겹친 기포 분할 → 기공률·계면 면적·수 밀도·속도 | 좁은 채널 고전 영상 처리. 과제문의 "Fu & Liu 2018 IJMF"는 Crossref에 없고 IJMF는 2016년이다 | C |
| 22 | Zhang H., Yang, Lin, Pu, Wang, Chang et al. (2026) | A computer-vision approach for bulk flow parameters and Lagrangian bubble motion in millimeter-scale tubes | PoF 38(10):103324 | 10.1063/5.0336482 | mm 관, 기포류·슬러그류, 30 fps 역광 | Attention-UNet(Dice 0.9736) + 마스크 겹침·관성 연속 조건 매칭. 합성 변위 시험 오프셋 0.95%, 기포 속도 B형 불확도 0.47% | 우리와 가장 비슷한 "마스크 겹침 추적 + 불확도 보고". 관 하나, ΔP·h 없음 | C+A |
| 23 | Durve et al. (2022) | DropTrack—Automatic droplet tracking with YOLOv5 and DeepSORT for microfluidic applications | PoF 34(8):082003 | 10.1063/5.0097597 | 미세유체 이중 에멀전 | 실제 40% + 합성 60% 학습이 최고, 라벨 작업 60% 절감, 약 30 fps | 미세유로 DL 추적. 지표는 검출 mAP·개수 MSE뿐 | C+A |
| 24 | Zvejnieks, Birjukovs, Klevs, Akashi, Eckert, Jakovics (2022) | MHT-X: offline multiple hypothesis tracking with algorithm X | Exp Fluids 63(3):55 | 10.1007/s00348-022-03399-5 | 기포·입자 추적 코드 | 합체·분열을 질량·운동량 보존을 통계 함수로 바꿔 판정(초록) | 우리 마스크 겹침 합체·분열과 같은 계열의 선행 | C+A |
| 25 | Graner, Dollet, Raufaste, Marmottant (2008) | Discrete rearranging disordered patterns, part I: Robust statistical tools in two or three dimensions | EPJE 25(4):349-369 | 10.1140/epje/i2007-10298-8 | 2D 거품 등 영상 통계 도구 | 이웃 연결 기반 텍스처 텐서 등 6개 도구(초록) | 0.3 mm에서 기포가 맞닿아 거품처럼 되면 쓸 통계 틀 | C+A |

### 1-D. 기포 검출·분할·추적 일반

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 26 | Seong, Ravichandran, Su, Phillips, Bucci (2023) | Automated bubble analysis of high-speed subcooled flow boiling images using U-net transfer learning and global optical flow | IJMF 159:104336 | 10.1016/j.ijmultiphaseflow.2022.104336 | 과냉 흐름 비등(MIT) | 학습 영상 약 10장, GT 100장 대비 정확도·정밀도 > 90%, 광류로 생애 단계 판정 | U-Net 전이학습 + 광류. 우리 PIV 사전과 비슷한 발상 | C (검색 요약 기준) |
| 27 | Kim, Park (2021) | Deep learning-based automated and universal bubble detection and mask extraction in complex two-phase flows | Sci Rep 11:8940 | 10.1038/s41598-021-88334-0 | Mask R-CNN(BubMask), 실험 + BubGAN 합성 | AP50 98%, α ≤ 1%에서 92% 이상, 2%에서 87% 이상 검출. 크기별 AP. 추적은 보충 영상으로만 | 크기별 지표 보고의 예 | C+F |
| 28 | Hessenkemper, Starke, Atassi, Ziegenhein, Lucas (2022) | Bubble identification from images with machine learning methods | IJMF 155:104169 | 10.1016/j.ijmultiphaseflow.2022.104169 | 기포탑, U-Net/StarDist/Mask R-CNN, 합성 시험 | 합성 영상에서 분할 오차가 기공률 오차로: 이상적 분할 약 9%, SD+UNet 약 12% 과소. 기공률 5% 초과에서는 오차가 받아들일 수 없는 수준 | 분할 오차 → 물리량 전파의 대표 사례 | C+F (arXiv 판) |
| 29 | Wang, Hessenkemper, et al. (2025) | A contribution to 3D tracking of deformable bubbles in swarms using temporal information | Exp Fluids 66(2):34 | 10.1007/s00348-025-03963-9 | 실제 단일 기포 실험을 겹친 인공(반합성) 시퀀스 12개 | MOTA 0.28~0.94, 정확 궤적 비율 0.30~0.99, 평균 상승 속도 오차 0.09~12.7 mm/s | Exp Fluids가 받은 추적 검증 수준의 예. 선행판 Hessenkemper et al. 2024 IJMF 179:104932 (10.1016/j.ijmultiphaseflow.2024.104932, C) | C+F |
| 30 | Haas, Schubert, Schlüter, Hampel (2020) | BubCNN: Bubble detection using Faster RCNN and shape regression network | CES 216:115467 | 10.1016/j.ces.2019.115467 | 기포탑 | Faster R-CNN + 형상 회귀, 전이학습 모듈 공개(초록) | 일반 검출기 | C+A |
| 31 | Cerqueira, Paladino (2021) | Development of a deep learning-based image processing technique for bubble pattern recognition and shape reconstruction in dense bubbly flows | CES 230:116163 | 10.1016/j.ces.2020.116163 | 조밀 기포류, 물·글리세린 수용액 | 앵커 점 + 타원 후보를 CNN이 선택, 다른 액체에 일반화(초록) | 일반 검출기 | C+A |
| 32 | Poletaev, Tokarev, Pervunin (2020) | Bubble patterns recognition using neural networks: Application to the analysis of a two-phase bubbly jet | IJMF 126:103194 | 10.1016/j.ijmultiphaseflow.2019.103194 | 기포 제트 | 합성 영상으로 학습한 신경망 앙상블. 영상 기공률이 적분 기공률과 일치(초록) | 독립 적분량과 대조하는 검증 방식 | C+A |
| 33 | Fu, Liu (2019) | BubGAN: Bubble generative adversarial networks for synthesizing realistic bubbly flow images | CES 204:35-47 | 10.1016/j.ces.2019.04.004 | 1만 개 기포로 학습, 100만 개 생성 | 라벨 붙은 합성 영상으로 학습·벤치마크 | 합성 GT 생성법 | C+F (arXiv 판) |
| 34 | Dunlap, Li, Pandey, Le, Hu (2024) | BubbleID: A deep learning framework for bubble interface dynamics analysis | JAP 136(1):014902 | 10.1063/5.0207546 | 풀 비등 | Mask R-CNN + SORT 추적, 이탈 등 사건 검출. 추적 지표 수치는 초록에 없음 | 공개 도구. 추적 정확도 보고가 약한 전형 | C+A (NSF PAR 초록) |
| 35 | Suh, Chang, Simadiris, et al. (2024) | VISION-iT: A framework for digitizing bubbles and droplets | Energy and AI 15:100309 | 10.1016/j.egyai.2023.100309 | 검출·추적·후처리 모듈 | [1][2]의 기반 도구(2차 인용, [43]) | [1][2]의 지표가 나온 경로 | C |
| 36 | Choi, Kim, Park (2022) | Bubble velocimetry using the conventional and CNN-based optical flow algorithms | Sci Rep 12:11879 | 10.1038/s41598-022-16145-y | 기포 플룸 | 미세조정 CNN 광류가 변동 속도에서 PTV와 가장 가까움, 기공률 > 10%에서 PTV 실패(초록) | 속도 검증을 독립 방법(PTV)과 대조 | C+A |
| 37 | Caicedo et al. (2019) | Evaluation of Deep Learning Strategies for Nucleus Segmentation in Fluorescence Images | Cytometry A 95(9):952-965 | 10.1002/cyto.a.23863 | 세포핵 23,165개 | 배경/내부/경계 3클래스 U-Net, 경계 가중치 10배. 병합·분할 오류를 따로 셈 | 우리 3클래스 U-Net(경계 가중 6)의 직접 선례 → 이 부분은 새롭지 않다 | C+F (Europe PMC) |
| 38 | Jaqaman et al. (2008) | Robust single-particle tracking in live-cell time-lapse sequences | Nat Methods 5(8):695-702 | 10.1038/nmeth.1237 | u-track | 전역 조합 최적화로 연결 + 합체·분열(초록) | 헝가리안 + 합체·분열의 선례 | C+A |

### 1-E. 영상 → 열유속·CHF(그 밖) + 리뷰

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 39 | Hobold, da Silva (2018) | Machine learning classification of boiling regimes with low speed, direct and indirect visualization | IJHMT 125:1296-1309 | 10.1016/j.ijheatmasstransfer.2018.04.156 | 선 히터 풀 비등 | SVM·신경망 비등 양식 분류 정확도 > 93%(초록) | 영상→양식 | C+A |
| 40 | Rassoulinejad-Mousavi et al. (2021) | Deep learning strategies for critical heat flux detection in pool boiling | ATE 190:116849 | 10.1016/j.applthermaleng.2021.116849 | 공개 자료 2개 + 자체 1개 | 새 자료 1%로 전이학습 시 정확도 94.79%(CNN 85.10%)(초록). 영역 일반화 후속: Al-Hindawi et al. 2023 ESWA 227:120265 (10.1016/j.eswa.2023.120265, C+A) | 다른 장치로 옮길 때 소량 재학습이 필요하다는 근거 | C+A |
| 41 | Rokoni et al. (2022) | Learning new physical descriptors from reduced-order analysis of bubble dynamics in boiling heat transfer | IJHMT 186:122501 | 10.1016/j.ijheatmasstransfer.2021.122501 | 풀 비등 | 초록 못 봄. 후속: Zhang L. et al. 2026 IJHMT 255:127894 (10.1016/j.ijheatmasstransfer.2025.127894, C) 비지도 영상 서술자 | 영상에서 물리 서술자를 뽑는 계열 | C |
| 42 | Ravichandran, Bucci (2019) | Online, quasi-real-time analysis of high-resolution, infrared, boiling heat transfer investigations using artificial neural networks | ATE 163:114357 | 10.1016/j.applthermaleng.2019.114357 | 적외선, 풀 비등 | 성장시간·주기·핵생성 밀도를 수 초 안에, 기존 처리 대비 회귀계수 ≥ 0.95(초록) | 영상 통계 자동화 | C+A |
| 43 | Dunlap, Olabiyi, Al-Hindawi, Pandey, et al. (2026) | Open datasets and machine learning for two-phase heat transfer: a review following a spatial-temporal taxonomy | Transport Phenomena 1(3):20260081 | 10.1515/tp-2026-0081 | 리뷰 | 영상→h 예로 [1]만 든다. 영상 지표→ΔP 연구는 없다. "인접 프레임이 아니라 실험 단위로 train/test를 나눠라" 권고 | 부재 근거 + 검증 권고 | C+F (arXiv 2605.23037v2) |
| 44 | Suh, Chang, Won (2024) | Recent progress of artificial intelligence for liquid-vapor phase change heat transfer | npj Comput Mater 10:65 | 10.1038/s41524-024-01223-8 | 리뷰 | 메타분석·데이터 추출·데이터 흐름 분석 정리(초록) | 배경 리뷰 | C+A |

### 1-F. ML 상관식과 해석 가능한 ML

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 45 | Zhang W., Hibiki, Mishima (2010) | Correlations of two-phase frictional pressure drop and void fraction in mini-channel | IJHMT 53(1-3):453-465 | 10.1016/j.ijheatmasstransfer.2009.09.011 | 미니채널 | 신경망으로 지배 변수 탐색, 무차원 Laplace 상수가 C와 C0를 지배(2차 인용) | "ML로 지배 무차원수 찾기"의 선례. 우리 갭(Co) 축과 직결 | C |
| 46 | Qiu, Garimella, Kharangate, Mudawar et al. (2020) | An artificial neural network model to predict mini/micro-channels saturated flow boiling heat transfer coefficient based on universal consolidated data | IJHMT 149:119211 | 10.1016/j.ijheatmasstransfer.2019.119211 | 통합 데이터베이스 | 원문 미확인. 같은 그룹 응축 h: Zhou et al. 2020 IJHMT 162:120351 (10.1016/j.ijheatmasstransfer.2020.120351, C), Bard et al. 2022 ATE 210:118305 (10.1016/j.applthermaleng.2022.118305, C) | 표 형식(운전 조건) ML. 영상 입력 없음 | C |
| 47 | Qiu et al. (2021) | Machine learning algorithms to predict flow boiling pressure drop in mini/micro-channels based on universal consolidated data | IJHMT 178:121607 | 10.1016/j.ijheatmasstransfer.2021.121607 | 통합 데이터베이스 | 원문 미확인 | ΔP ML 기준선 | C |
| 48 | Sajjad et al. (2024) | On the prediction and optimization of the flow boiling heat transfer in mini and micro channel heat sinks | PNE 177:105466 | 10.1016/j.pnucene.2024.105466 | 표 형식 | SHAP로 h 예측 해석(Scholar 요약) | SHAP 사례. 영상 특징 없음 | C (검색 요약 기준) |
| 49 | Hussain et al. (2024) | A physics-informed, data-driven framework for estimation and optimization of two-phase pressure drop of refrigerants in mini- and macro channels | Results Eng 23:102538 | 10.1016/j.rineng.2024.102538 | 표 형식 | 물리 + Pearson·SHAP로 ΔP 핵심 변수(Scholar 요약) | ΔP SHAP 사례 | C (검색 요약 기준) |
| 50 | Xie, Samaei, Guo, Liu, Gan (2022) | Data-driven discovery of dimensionless numbers and governing laws from scarce measurements | Nat Commun 13:7562 | 10.1038/s41467-022-35084-w | 적은 실측 자료 | 차원 불변성을 넣은 2단계 학습으로 지배 무차원수·법칙 발견(초록) | 갭 5종 × 유량의 적은 자료에서 무차원 법칙 찾기에 맞다 | C+A |
| 51 | Bakarji, Callaham, Brunton, Kutz (2022) | Dimensionally consistent learning with Buckingham Pi | Nat Comput Sci 2(12):834-844 | 10.1038/s43588-022-00355-5 | 예제 3종 | Pi 정리 제약 하의 무차원군 탐색(BuckiNet, SINDy 포함)(초록) | 같은 용도 | C+A |
| 52 | Brunton, Proctor, Kutz (2016) | Discovering governing equations from data by sparse identification of nonlinear dynamical systems | PNAS 113(15):3932-3937 | 10.1073/pnas.1517384113 | SINDy | 희소 회귀로 식 발견(제목) | 후보 항(σCa^(2/3)·둘레 밀도 등) 선택에 쓸 수 있다 | C |
| 53 | Shi et al. (2025) | Hybrid symbolic regression for data-driven discovery: Governing dimensionless numbers in supercritical heat transfer | Energy 338:138752 | 10.1016/j.energy.2025.138752 | 초임계 열전달 | 원문 미확인 | 기호 회귀 + 무차원수, 열전달 응용 | C |
| 54 | Cranmer (2023) | Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl | arXiv 2305.01582 | DOI 없음 | 도구 | 기호 회귀 도구 | 상관식 형태 탐색 | U |

### 1-G. 검증·오차 전파·지표

| # | 저자(연도) | 제목 | 학술지 권(호):쪽 | DOI | 조건 | 핵심 결과(숫자) | 0.3/0.7/1/3/7 mm 연구와의 관련성 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|
| 55 | Maduabuchi, Jossou, Bucci (2024, v5 2026) | MSEG-VCUQ: Multimodal SEGmentation with Enhanced Vision Foundation Models, Convolutional Neural Networks, and Uncertainty Quantification for High-Speed Video Phase Detection Data | arXiv 2411.07463 | DOI 없음 | 위상 검출 HSV, 여러 유체 | 전문가 5명 GT 대비 건조 면적 비율 < 2%, 접촉선 밀도 < 8%. 둘레는 화소 이산화에 민감(PRE 13.8% → 팽창 후 6.6%, LN2 −8.4%), 면적은 안정 | **둘레 길이 밀도(가설 2의 입력)는 화소 크기 보정이 필요하다**는 근거 | U (원문 읽음) |
| 56 | Sciacchitano (2019) | Uncertainty quantification in particle image velocimetry | MST 30(9):092001 | 10.1088/1361-6501/ab1db8 | PIV UQ 리뷰 | 사전·사후 UQ, 유도량으로의 전파(초록) | UQ 보고 형식의 기준 | C+A |
| 57 | Villegas et al. (2019) | Image processing for the experimental investigation of dense dispersed flows: Application to bubbly flows | IJMF 111:16-30 | 10.1016/j.ijmultiphaseflow.2018.10.017 | 합성 + 실제 영상 | 검출 기포 수 40% 이상 증가(초록) | 합성 검증의 고전 예 | C+A |
| 58 | Luiten et al. (2021) | HOTA: A Higher Order Metric for Evaluating Multi-object Tracking | IJCV 129(2):548-578 | 10.1007/s11263-020-01375-2 | 지표 | 검출·연관 균형 지표 | 1:1 가정이라 합체를 못 다룸 → 보조 지표 | C |
| 59 | Bernardin, Stiefelhagen (2008) | Evaluating Multiple Object Tracking Performance: The CLEAR MOT Metrics | EURASIP JIVP 2008:246309 | 10.1155/2008/246309 | 지표 | MOTA/MOTP | 기포 추적 논문이 주로 쓰는 지표([29]) | C |
| 60 | Ristani, Solera, Zou, Cucchiara, Tomasi (2016) | Performance Measures and a Data Set for Multi-target, Multi-camera Tracking | ECCV 2016 Workshops (LNCS) 17-35 | 10.1007/978-3-319-48881-3_2 | 지표 | IDF1 | 같은 한계 | C |
| 61 | Maška et al. (2023) | The Cell Tracking Challenge: 10 years of objective benchmarking | Nat Methods 20(7):1010-1020 | 10.1038/s41592-023-01879-y | 벤치마크 | DET/SEG/TRA 등 | 부모 1개 형식이라 합체 표현 불가 | C |
| 62 | Maier-Hein et al. (2024) | Metrics reloaded: recommendations for image analysis validation | Nat Methods 21(2):195-212 | 10.1038/s41592-023-02151-z | 지침 | 과제별 지표 선택 권고 | 크기별·사례별 지표 선택 근거 | C |
| 63 | Kapoor, Narayanan (2023) | Leakage and the reproducibility crisis in machine-learning-based science | Patterns 4(9):100804 | 10.1016/j.patter.2023.100804 | 지침 | 정보 누설 유형 | 인접 프레임 분할 누설 점검 근거 | C |
| 64 | Olofsson, Foody, Herold, Stehman, Woodcock, Wulder (2014) | Good practices for estimating area and assessing accuracy of land change | RSE 148:42-57 | 10.1016/j.rse.2014.02.015 | 원격탐사 | 확률 표본의 참값으로 면적을 추정해 지도 오차를 보정하고, 정확도·면적에 신뢰구간을 보고(초록). 층화 추정: Olofsson et al. 2013 RSE 129:122-131 (10.1016/j.rse.2012.10.031, C) | **사람 표본 감사로 물리량(개수·면적)을 보정하고 CI를 내는 틀**. 우리 4_link_audit의 통계 근거 | C+A |
| 65 | Brown, Cai, DasGupta (2001) | Interval Estimation for a Binomial Proportion | Stat Sci 16(2):101-133 | 10.1214/ss/1009213286 | 통계 | 이항 비율 구간 비교(Wilson 구간 권장 근거로 흔히 인용). Wilson 1927 JASA 22(158):209-212 (10.1080/01621459.1927.10502953, C) | 감사 신뢰구간 방법 근거 | C |

## 2. 핵심 질문에 대한 답

### 신규성(최우선): 영상으로 상관식을 개선한 논문이 있는데 우리는 무엇이 새로운가

**선행 연구가 한 것 / 안 한 것** (✓ 했다, ✗ 안 했다, △ 부분, ? 확인 못 함)

| 항목 | Huang 2024 [1] | BubbleMask 2023 [2] | Chang 2026 ΔP [3] | Naderi 2026 [4] | Schepperle 2024 [8] | Kurimoto 2019 [13] | Raufaste 2025 [15] | Zhang 2023 [11] | **우리(계획)** |
|---|---|---|---|---|---|---|---|---|---|
| 채널·갭 크기를 여러 개로 | ✗ (2.5×5 mm 1개) | ✗ | ✗ (2.5×5 mm 1개) | ? | ✗ | ✓ (Dh 3종) | ✗ (0.9 mm) | △ (표면 여러 개) | ✓ (0.3~7 mm 5종, Co 0.39~9.1) |
| 서브 mm 갭 | ✗ | ✗ | ✗ | ? | ✓ (깊이 0.5 mm) | ✓ | ✓ | – | ✓ (0.3, 0.7 mm) |
| 넓고 납작한 갭에서 여러 기포 | ✗ | ✗ | ✗ | ? | ✗ | ✗ (일렬 기포) | ✓ (거품 단층) | – | ✓ |
| 가열면을 정면(위)에서 촬영 | ✗ (옆; 저자가 "투명 히터로 벽 위상 분포를 봐야" 한계로 명시) | ✗ (옆) | ? | ? | ✓ (강철 바닥 + Pyrex 뚜껑) | – (비가열) | – | ✓ (투명 히터 IR) | ✓ (불투명 철 바닥, 위) |
| 개별 기포 추적으로 속도 측정 | ✗ (속도는 기공률·에너지 균형으로 계산) | ✓ (평균 0.5~1.8 m/s) | ✗ (이벤트 통계) | ? | ✗ | △ (수동·고전) | ✗ | – | ✓ (헝가리안, 합체·분열) |
| 측정 운동학을 모델 입력으로 | ✗ | △ (회귀 특징만) | ✗ | ? | ✗ | ✓ (단위 셀) | △ (평균 속도 V0) | – | ✓ (기포별 Ca) |
| 영상 지표로 ΔP 모델링 | ✗ (ΔP는 측정만) | ✗ | ✓ (MLP, 통계) | ? | ✗ | ✓ (물리) | △ (ΔP 추정, 미측정) | ✗ | ✓ (물리 + ML 기준선) |
| 영상 지표로 h 모델링 | ✓ (시간 가중) | △ (회귀 중요도) | – (3장은 [1]과 같음) | ✓ (제목) | △ (RTD 값 예측) | ✗ | ✗ | – (CHF) | ✓ (가열 실험 후) |
| ΔP와 h를 같은 영상 지표로 함께 | ✗ | ✗ | ✗ | ? | ✗ | ✗ | ✗ | ✗ | ✓ |
| 모델 형태 | 물리(기존 상관식 + 시간 가중) | 물리(ILM) + 선형회귀 | 통계(MLP, Ridge) | ? | 통계(CNN) | 물리 | 물리 | 물리 기준식 | 물리 + ML 비교 |
| 조건 밖 검증 | ✗ (같은 10사례) | ✗ | △ (LOOCV, 같은 장치) | ? | ✗ | ✗ (같은 자료로 맞춤) | – | ✓ (표면·유체·풀/흐름) | 갭 하나 빼기(leave-one-gap-out) |
| 영상 지표 오차를 결과로 전파 | ✗ (검출 지표 > 87%만) | ✗ (잘린 기포 16~35% 제외, 편차 막대만) | △ (모델 구조 변동만) | ? | ✗ | ✗ | ✗ | ? | ✓ (QC + 사람 표본 감사 → 몬테카를로) |
| 실데이터 검출·추적의 사람 표본 감사(CI) | ✗ | ✗ | ✗ | ? | ✗ | ✗ | ✗ | ✗ | ✓ (크기별 Wilson CI) |
| 단열(공기–물) | ✗ (비등) | ✗ | ✗ | ✗ | ✗ | ✓ (N2–액) | ✓ (거품) | ✗ | ✓ (0.3·0.7 mm 먼저) |
| 자료 공개 | ✗ ("공유 권한 없음") | ? | ? | ? | 코드 공개 | ? | 영상 보충자료 | ? | 가능하면 공개 |

**판단**
1. "영상 지표로 h 상관식을 개선"만으로는 새롭지 않다([1], [4], [5], [6]).
2. 그러나 [1]의 실제 개선은 약하다: 상관식 13개 중 8개가 나빠졌고, 가장 좋은 MAE는 15.9% → 28.2%다. 저자도 "예비적"이라 했다. 같은 자료로 [2]와 [1]의 ILM 개정 결과가 다르다(입력 정의에 민감). → **측정 정의와 오차를 엄밀히 다루는 것 자체가 차별점이 된다.**
3. 0.3·0.7 mm 단열 실험(ΔP, 기포 수, 크기, 가능하면 개별 속도)에서 새로울 수 있는 조합:
   - 넓은 갭의 여러 기포 + 측정 ΔP + 자동 추적으로 잰 **기포별 Ca**(속도) + 둘레·개수 → 물리 마찰 항([14][15]의 틀)을 실측 ΔP로 검증. [13]은 일렬 Taylor 기포, [15]는 ΔP 미측정·건조 거품, [3]은 통계 모델이다.
   - 갭 축(Co 9.1~0.39)을 따라 이 항이 사라지는지 보이는 것. 이미지→상관식 연구 중 형상을 바꾼 것은 찾지 못했다.
   - 검출·추적 오차를 사람 표본 감사로 재서 ΔP 항의 계수 불확도까지 전파. 어느 선행도 하지 않았다.
4. 가열 실험에서 새로울 수 있는 것: 위에서 본 가열면 화소마다 "기포 덮임 시간 / 액체 시간"을 추적으로 **직접** 재서 시간 가중 h에 넣기. [1]은 옆 촬영이라 이 값을 기공률로 계산했고, 저자가 이것을 한계로 적었다. 단, 불투명 철에서 위로 보면 기포 아래 액막이 말랐는지는 안 보인다(덮임 ≠ 건조).

### Q1. 딥러닝 기포 검출·분할·추적 (좁은 유로·불투명 배경·마이크로갭)
- 일반 검출기: Mask R-CNN [27][34], Faster R-CNN [30], U-Net 전이학습 [26], StarDist + U-Net [28], 앵커 + CNN [31], 합성 학습 [32][33]. 대부분 기포탑·풀 비등이고 옆(투과광) 촬영이다.
- 추적: SORT [34], DeepSORT([23]), 광류 [26][36], 마스크 겹침 + 관성 조건 [22], MHT(합체·분열) [24], u-track [38].
- 좁은 유로·불투명 배경 사례는 적다.
  - [8]: 0.5 mm 깊이 강철 미세채널을 Pyrex 뚜껑 위에서 U-Net(Dice 99.1%). 추적 없음.
  - [19]: 불투명 액체금속 3 mm Hele-Shaw. 벽에 닿은 기포 윤곽을 옆 조명으로 밝힘. 고전 처리.
  - [20][15]: 얇은 갭 기포군·거품을 고전 영상 처리로 추적·측정.
  - 0.1~1 mm 넓은 갭에서 DL로 기포를 추적한 연구는 찾지 못했다(검색 4, 7, 20, 21, 24).
- 얇은 갭 윤곽: 메니스커스(벽 Plateau 경계)가 테두리 선으로 보인다. [15]에서 그 반경은 91~143 µm(h = 0.9 mm)이고 수동으로 쟀다. 0.3 mm에서는 테두리가 화소 몇 개로 얇아질 것이다(추정). 라벨 규약("흰 테두리 바깥쪽")과 화소 크기를 먼저 정해야 둘레·면적이 일관된다([55]).
- 추적 지표: HOTA [58], MOTA [59], IDF1 [60], CTC [61]. 모두 1:1 또는 부모 1개 가정이라 합체를 표현하지 못한다. 기포 논문은 대개 검출 AP·F1만 내고([27][23][34]), 추적 지표는 반합성 GT에서만 냈다([29]).

### Q2. 영상 → 열유속·h·CHF
- 풀 비등: 열유속 회귀 오차 6~7% [9][10], 양식 분류 > 93% [39], CHF 검출 전이학습 [40], 적외선 통계 [42], 영상 서술자 [41].
- 흐름 비등: h 시간 가중 [1], CHF(ILM) [2], h 예측 [4][5][6], RTD 값 예측 [8].
- 일반화의 모범은 [11]이다. 영상(IR) 통계 3개로 만든 물리 기준을 여러 표면·유체·풀/흐름 비등에서 확인했다.
- 공기 주입이면 영상→h 문헌은 거의 없다(검색 12). 가열 실험이 비등이면 [1][4]와 직접 비교된다.

### Q3. ML 상관식과 해석 가능한 ML
- Mudawar 그룹은 통합 데이터베이스로 h·ΔP를 ANN으로 예측했다 [46][47]. 입력은 운전 조건·물성이다.
- SHAP 해석은 2024~2026년에 흔하다 [48][49]. 모두 표 형식 입력이고 영상 특징은 없다(검색 14).
- 무차원 법칙 발견: [50][51], 희소 회귀 [52], 기호 회귀 [53][54]. ML로 지배 무차원수를 찾은 이상류 선례는 [45]다.
- 권고: 영상 지표를 무차원으로 만들어(예: 갇힌 기포 면적 비율, 둘레 밀도 × H, 기포별 Ca) 운전 조건 무차원수와 함께 희소 회귀·기호 회귀에 넣는다. 검증은 갭 하나 빼기로 한다. 영상 특징을 넣은 해석 가능한 상관식은 찾지 못했다.

### Q4. 영상 기포 통계 ↔ 측정 h·ΔP (갭 높이별)
- h: [1](채널 1개, 비등), [4][6](제목·요약 수준). 갭을 바꾼 것은 없다.
- ΔP: AI 영상으로는 [3]만 있다(이벤트 지표, MLP, 채널 1개). 비AI 영상으로는 [13](크기 3종, 일렬 기포), [14], [15](ΔP 미측정), [16](크기 여러 개, 내용 미확인).
- 여러 갭 + 가시화 + h·ΔP는 비등 마이크로갭 [17]과 미세채널 [18]이 있지만 영상은 양식 판정 수준으로 보인다(원문 미확인).
- 결론: "자동 추적한 개별 기포 통계를 여러 갭(서브 mm ~ mm)의 측정 ΔP·h에 직접 연결"한 연구는 찾지 못했다(4장 검색 1, 2, 7, 9, 12, 24, 30, 31). 리뷰 [43]에도 영상→ΔP 연구가 없다.

### Q5. 검출·추적 오차 → 물리량 전파, 그리고 심사 요구 수준
- 정량화한 예
  - 분할 → 기공률: 합성 영상에서 약 9~12% 과소, 5% 초과에서 실패 [28].
  - 검출 → 개수: 기공률별 검출 비율 [27].
  - 화소 이산화 → 둘레·면적: 둘레 PRE 13.8%(팽창 후 6.6%), 면적은 안정 [55].
  - 추적 → 평균 속도: 반합성 시퀀스에서 0.09~12.7 mm/s [29]. 합성 변위로 오프셋 0.95%, 속도 B형 불확도 0.47% [22].
  - 상관식 쪽: [1][2]는 영상 지표의 불확도를 h·CHF로 전파하지 않았다.
- 게재 논문들이 실제로 한 검증(심사 요구 수준의 추정)
  - 사람 GT 시험 세트(예: 100장 [26], 전문가 5명 [55]).
  - 알려진 GT의 합성·반합성 자료([28][29][32][33]).
  - 독립 측정과 대조(적분 기공률 [32], PTV [36]).
  - 크기별 지표 [27][62], 실험 단위 분할로 누설 방지 [43][63].
  - 유도량의 불확도 보고 [56][22].
- 사람 표본 감사 + 신뢰구간: 기포 연구에서는 찾지 못했다(검색 33). 원격탐사의 표본 기반 정확도·면적 보정 [64]과 이항 구간 [65]이 통계 근거다.

### Q6. 우리 파이프라인의 새로운 점과 부족한 점
- 새롭지 않은 부분: 3클래스 U-Net [37], 헝가리안 + 합체·분열 [38][24], 마스크 겹침 매칭 [22]. PIV로 입자 추적을 돕는 방식도 오래됐다(Keane et al. 1995 MST 6(6):754-768, 10.1088/0957-0233/6/6/013, C, 원문 미확인).
- 새로울 수 있는 부분(찾은 범위 안에서)
  - 크기 구분별 PIV로 새 트랙의 초속을 주는 것. 비슷한 선행을 찾지 못했다(별도 검색은 하지 않았다).
  - QC 플래그 + 크기별 층화 무작위 사람 감사(Wilson CI, 모집단 가중)로 실데이터 추적 정확도를 수치로 내는 것.
  - 위의 오차를 ΔP·h 모델 입력의 불확도로 전파하는 것(계획).
  - 불투명 철 가열면 + 위 촬영 + 여러 갭 적용.
- 부족한 점
  - 실데이터 추적 GT가 없다. 합성 GT는 실제보다 쉽다(잔차 2.2 vs 4.8 px, CLAUDE.md).
  - 합체를 다루는 표준 지표가 없다 → 사건(합체·분열) 정밀도·재현율을 따로 내야 한다.
  - 둘레 길이는 화소 크기 보정이 필요하다 [55]. 라벨 경계 규약이 측정 정의를 바꾼다.
  - 인접 프레임 누설 방지(실험 단위 분할)를 아직 문서로 보이지 않았다 [43][63].
  - 시야가 압력 탭 구간보다 짧으면 [2]의 "창 효과"가 생긴다(잘린 기포 16~35%).

## 3. 아이디어와 시사점

1. **0.3·0.7 mm 단열: ΔP의 물리 분해 + 영상 입력 + 오차 전파** (가장 유력)
   - 입력: 프레임별 기포 수 N, 둘레 합 ΣP_i, 면적, 추적 속도 U_i → 기포별 Ca_i = μU_i/σ.
   - 모델: ΔP = 액체 마찰(층류 12μU_L/H²) + Σ c·σ·Ca_i^(2/3)·P_i/(W·H)류 항 + 기포 앞뒤 메니스커스 압력 항. 정확한 항은 주제 3의 크기 추정에 맡긴다.
   - 비교: (i) 운전 조건만 쓴 ML, (ii) 영상 지표를 더한 ML([3]의 방식), (iii) 물리 항. 갭 하나 빼기로 검증.
   - 오차: 감사로 잰 놓침·오연결 비율, 둘레 이산화 오차([55])를 부트스트랩·몬테카를로로 계수 CI에 넣는다.
   - 새로움: [13](일렬 기포·수동), [15](ΔP 미측정), [3](통계·비등)과 다르다.
   - 필요한 자료: 화소 크기 보정, 압력 탭 위치와 시야의 관계, 영상–압력 시간 동기, fps(이동량/이웃 간격 ≤ 0.5).
   - 위험: 0.3 mm에서는 액체 층류 ΔP가 커서(6.7~133 kPa/m) 기포 항이 묻힐 수 있다. 크기 추정이 먼저다.
2. **시간 분해 상관**: ΔP 시계열과 프레임별 N·ΣP의 상호상관·스펙트럼. [3]은 이벤트 지표의 변동이 ΔP 예측을 돕는다고 했다. 기포별 지표로 같은 질문을 하면 물리 해석이 가능하다.
3. **가열 실험**: 화소별 기포 덮임 시간 분율을 추적으로 직접 재서 [1]의 시간 가중 h에 넣는다. [1]의 결과(13개 중 8개 악화)를 같은 방식으로 재현·비교하면 차이가 분명해진다.
4. **해석 가능한 상관식**: 무차원 영상 지표 + 운전 조건 → 희소/기호 회귀([50]~[54]). 갭 축에서 계수가 Co에 따라 어떻게 바뀌는지 보인다.
5. **방법론 절(또는 별도 논문)**: 검출·추적 오차 → ΔP·h 계수 불확도 전파 + 사람 표본 감사. 비교 기준은 [28][29][55][56][64].

## 4. 새로움 판단 기록
| # | 도구 | 검색어 | 결과 | 찾은 것 / 못 찾은 것 |
|---|---|---|---|---|
| 1 | WebSearch | high-speed image bubble statistics correlated with measured heat transfer coefficient narrow rectangular channel gap height | 10 | 미니갭 비등 1개 갭(MIT), 좁은 채널 기포 추적(h 없음). 여러 갭 영상→h 없음 |
| 2 | Scholar | "void fraction" "wetting front" machine learning vision flow boiling heat transfer coefficient correlation (2015~) | 9 | [1] 인용 22, [7], [43], [5], Chang 박사논문 |
| 4 | Scholar | "deep learning" bubble segmentation tracking "narrow rectangular channel" OR minichannel OR microchannel OR "Hele-Shaw" (2018~) | 약 454 | [34], 갇힌 풀 비등 ML 추적(SSRN, 내용 미확인), [22]. 마이크로갭 DL 추적 없음 |
| 5 | WebSearch | bubble detection tracking Hele-Shaw cell neural network ... liquid metal radiography | 9 | 고전 처리만([19], MHT-X [24]) |
| 7 | Scholar | microgap OR "micro-gap" OR "mini-gap" flow boiling visualization "machine learning" OR "deep learning" OR "neural network" bubble (2016~) | 20 | 마이크로갭 영상에 ML을 쓴 논문 없음 |
| 9 | Scholar | "pressure drop" "image processing" "bubble number" OR "number of bubbles" OR "interfacial length" "narrow gap" OR "Hele-Shaw" OR "narrow rectangular" | 약 85 | 좁은 직사각 채널 영상 측정 + ΔP(고전), Torisaki & Miwa 2020(25.4 mm 관, YOLOv3, ΔP 연결 없음 — J-STAGE 원문 확인) |
| 12 | Scholar | "bubble injection" OR "gas injection" "heat transfer enhancement" "narrow channel" OR "Hele-Shaw" OR "thin gap" "image processing" "void fraction" Nusselt | 2 | 학위논문 2편. 얇은 갭 영상 통계→h 없음 |
| 14 | Scholar | "symbolic regression" OR "SINDy" OR "SHAP" "two-phase" "pressure drop" OR "heat transfer coefficient" OR "void fraction" correlation minichannel OR microchannel (2019~) | 약 113 | SHAP·표 형식만([48][49] 등). 영상 특징 입력 없음 |
| 16 | WebSearch | bubble image processing segmentation error propagation to void fraction bubble size distribution velocity uncertainty synthetic images validation deep learning | 10 | 체계적 전파 연구 없음. [36], 합성 생성기 학회 초록 |
| 20 | Scholar | microchannel "Taylor flow" OR "slug flow" bubble "deep learning" OR CNN OR YOLO detection tracking "bubble length" (2017~) | 3 | 관련 없음 |
| 21 | WebSearch | deep learning bubble detection microchannel images segmentation tracking microfluidic gas-liquid slug flow U-Net YOLO bubble length velocity | 9 | [8] |
| 24 | Scholar | "Hele-Shaw" bubble OR foam OR droplet "deep learning" OR "U-Net" OR CNN segmentation tracking (2018~) | 37 | 거품 CNN 분할 1건(Skrypnik 계열), YOLOv11+DeepSORT. Hele-Shaw DL 추적 → ΔP·h 없음 |
| 30 | Scholar | "flow boiling" "heat transfer coefficient" prediction from images OR "vision-based" OR "computer vision" bubble features mini-channel OR microchannel (2022~) | 약 305 | [5][6], Chang 박사논문 2편, 리뷰 2편. 모두 비등·채널 1개 |
| 31 | Crossref | CNN images narrow rectangular channel gap / DL image void fraction narrow gap different gap thickness / ML HS images minichannel different channel sizes pressure drop | 각 6 | 여러 갭 두께 영상 통계→ΔP·h 없음 |
| 33 | WebSearch | bubble tracking accuracy estimated by manual inspection of randomly sampled links confidence interval experimental two-phase flow no ground truth | 10 | 없음(시뮬레이션 도구 arXiv 2011.07243만) |
| – | 원문 | [1][2][7](Suh 연구실 공개 PDF), [3](eScholarship PDF), [43](arXiv) | – | [1]: 속도 계산값, ΔP 미모델, UQ 없음, 자료 비공개. [3]: 이벤트→ΔP MLP. [43]: 영상→ΔP 연구 없음 |
| – | 기타 | Crossref 서지 대조 약 70건, Semantic Scholar 초록, NASA NTRS(0건), SSRN(403) | – | – |

- Google Scholar는 11회 썼다(제목·버전 확인 2회 포함). CAPTCHA는 없었다.
- [1]의 수치는 원문 Table 1~3에서 직접 옮겼다. h 개선 13개 대응: 개선 5개(Tran 125.1→35.8, Lazarek 233.6→28.2, Agostini 147.5→37.1, Yu 234.5→28.2, Sun·Mishima 108.4→36.1%), 악화 8개(Kim·Mudawar 24.9→70.4, Li·Wu 23.4→57.5, Oh·Son 89.9→97.7, Gopinath 36.6→55.9, Liu·Winterton 23.1→69.9, Kenning·Cooper 67.2→89.9, Cooper 22.0→68.2, Hamdar 15.9→64.5%).
- 못 찾은 것: Naderi 2026 [4] 원문(ScienceDirect 막힘, Suh 연구실 목록에 없음), [5][6]의 수치, Seong 2023 원문, Alam 2012·Harirchian 2012·Chung & Kawaji 2004 초록.

## 5. 남은 의문과 사용자에게 확인할 것
- **[4] Naderi 2026(수평 미니채널, 영상→h)의 내용**: 가장 최근의 직접 경쟁 문헌이다. 학교 도서관 접속으로 원문을 받아 채널 크기·지표·개선 폭을 확인해 주면 신규성 표를 확정할 수 있다.
- 0.3·0.7 mm 단열 실험
  - 압력 탭 사이 길이와 카메라 시야의 관계(시야가 탭 구간 전체인지). 아니면 [2]의 창 효과가 생긴다.
  - 화소당 mm, fps, 노출 시간. 기포 속도와 이웃 간격 대비 이동량이 추적 가능 범위인지.
  - 영상과 압력 신호의 시간 동기 여부(시간 분해 상관을 하려면 필요).
  - 0.3 mm 영상에서 기포 테두리가 몇 화소로 보이는지(라벨 규약, 둘레 보정).
- 가열 실험이 비등인지 공기 주입인지. 비등이면 [1][4][6]과 직접 비교된다.
- 자료 공개가 가능한지([1]은 공개 불가였다. 공개하면 차별점이 된다).
- 미확인 문헌(논문에 쓰기 전에 원문 확인): [4][5][6][12][16][17][18][21][26][35][41][46][47][53], 갇힌 풀 비등 ML 추적(Daoud et al., SSRN 7225772, 10.2139/ssrn.7225772, 내용 미확인).

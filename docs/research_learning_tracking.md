# 기포 추적에 학습과 트랜스포머를 더 쓸 것인가: 근거와 로드맵

이 보고서는 연구 주제 8개와 각 주제의 검증 결과를 합친 것이다. 비판 검토에서 지적된 과장과 누락을 이번 판에서 고쳤다. 수치는 이 프로젝트에서 직접 잰 것이다. 출처는 사용자 CSV(750·144·112프레임), 731~790 저장 마스크, 17·31번 원본, 합성 시뮬레이터다. 이번 분석에서는 신경망을 돌리지 않았다.

인용 검증에는 한계가 있다. 이번 판에서 새로 넣은 문헌은 원문을 열지 못했다. 웹 검색 예산이 소진됐고 DOI·Crossref·출판사 호스트가 프록시에서 막혔기 때문이다. 해당 문헌은 PIV로 PTV를 돕는 고전 기법, 열유체 분야의 딥러닝 기포 추적, 반인공 GT 두 번째 기록이다. 모두 "미검증"으로 따로 표시했다.

## 한눈에 보는 답

**Q1. 추적 자체를 학습하면 안 되나? 학습할 수는 있다. 하지만 지금 쓸 수 있는 정답으로 학습하면 주로 시뮬레이터를 배운다. 측정과 학습 없는 수정이 먼저다.**
- 정답의 현황
  - 실데이터에는 트랙 ID도, 합체의 부모 정보도 없다. 라벨은 전부 단일 프레임 폴리곤이다.
  - 합성 데이터에는 정답이 있다. `old/sim_compare.py`와 `old/sim_piv.py`가 정답 ID와 합체·분열 이벤트를 낸다. 이것으로 연결기를 사전학습할 수는 있다.
  - 하지만 시뮬레이터는 실제보다 쉽다.
    - 예측 잔차 중앙값은 2.2 px다(실제 4.8 px). tiny POS_JUMP는 10%다(실제 49%).
    - 시뮬레이터의 검출 누락은 프레임마다 독립(i.i.d.)이다. 실제 누락은 같은 기포에서 연달아 생기고, 슬러그 접촉이나 붙은 쌍 같은 상황에 묶여 있다.
    - 따라서 시뮬레이터로 학습하면 주로 시뮬레이터의 통계를 배운다.
  - 더 현실적인 정답은 반인공 GT다(Hessenkemper 방식, 로드맵 5). 실제 영상에서 확신 높은 트랙 조각을 서로 다른 시간대에서 가져와 한 시퀀스에 겹친다. 학습에 쓰기 전에 평가용으로 먼저 쓴다.
- 정답 없이 돌릴 수 있는 것도 있다. 사전학습 Trackastra(general_2d)는 zero-shot 추론만 하면 된다.
  - 다만 토큰 특징에 밝기 평균·최대·최소가 들어 있다(`wrfeat.py`의 `_PROPERTIES`).
  - 이진화 B에서는 모든 기포 내부가 검정이라 이 특징에 정보가 없다. 원본 프레임에서 돌려야 한다.
- 구조적 한계가 있다. Trackastra의 ILP와 CTC 형식은 부모를 하나만 허용한다(코드에서 `MaxParents(1)`, `MaxChildren(2 if divisions else 1)` 확인). 그래서 합체를 표현하지 못한다. 우리 영상에는 합체가 프레임당 1.7~3.9건, 분열이 0.8~2.8건 있다.
- 자기지도 학습과 의사 라벨도 맞지 않는다.
  - 기포가 모두 같은 모양이라 외형 기반 자기지도 학습은 배울 신호가 없다.
  - tracker3의 확신 링크로 의사 라벨을 만들면 쉬운 링크만 배운다.
  - 정방향/역방향 일치율 96%(대형 1:1 링크)는 이벤트 라벨을 무시한 값이다.
    - 같은 쌍이 한 방향에서는 일반 링크로, 반대 방향에서는 합체·분열로 처리되는 일이 많다. 그러면 속도가 실측값과 hold 값 사이에서 바뀐다.
    - 합체·분열 행의 링크를 빼면 일치율은 화면 안 87%, 화면 끝 76%다.
    - 슬러그 옆 합체·분열 판정은 36%만 일치한다.
- 학습 없이 고칠 수 있는 오류가 많다.
  - 작은 점 누락: tiny/small 검출 실패의 59%는 입력에 또렷이 보이는 점을 U-Net이 ≈0으로 놓친 경우였다(검출 실패 분석). 라벨 누락 가설과 맞으므로 라벨 보충으로 다룬다.
  - 트래커 로직:
    - 합체 직후 기포를 '분열'이 아니라 '신규'로 처리한다.
    - 화면 끝 처리에 문제가 있다.
    - 자동 게이트가 tiny 이웃 간격과 같은 폭이다(로드맵 6).
- 먼저 할 일은 측정이다. 무작위 링크 감사(조건당 30~40분)로 정확도를 잰다. 그리고 추적이 u_B와 C0를 얼마나 흔드는지 잰다.

**Q2. 트랜스포머를 더 큰 층에 넣어 큰 기포를 잡게 하면? '더 큰 층'의 두 뜻 모두 지금 데이터로는 아니오.**
- 뜻 1: 더 고해상도 층(1/16, 1/8)으로 옮기기
  - 1/32가 이미 큰 물체용 스케일이다.
    - 1088×416에서 1/32 토큰은 442개다. 토큰 하나가 32 px이고, 전체가 프레임을 덮는다.
    - ResNet34의 이론 수용야는 1/32에서 899 px, 1/16에서 547 px다. 거대 슬러그 반두께 중앙값은 84 px다.
  - 1/16·1/8로 내리면 작은 구조에 유리해진다. 큰 기포를 잡으려는 목적과 반대 방향이다.
  - 비용도 커진다. 토큰은 1768개(1/16), 7072개(1/8)로 4배·16배가 되고, 어텐션 비용은 16배·256배가 된다.
  - 고해상도 스킵에 가까워져 tiny 재현율이 흔들릴 위험도 커진다. B는 대응되지 않은 tiny 예측이 27개 있었다.
- 뜻 2: 같은 1/32에서 더 깊거나 넓게(ViT-B급)
  - 무작위 초기화 파라미터만 늘어난다. 학습량(약 1760스텝), 데이터(약 530장), 거대 슬러그 실패 사례가 거의 없는 학습셋이라는 조건은 그대로다.
  - TransUNet이 통하는 것은 ImageNet-21k로 사전학습한 ViT를 쓰기 때문이다(참고문헌).
- 1/16 토큰도 벽이 어디 있는지는 담는다. 전체 해상도 입력에서 CNN이 계산한 특징이기 때문이다. 진짜 장애는 두 가지다.
  - 적은 예에서 안/밖(홀짝)을 배워야 한다.
  - 학습셋에 지금 모델이 틀리는 사례가 거의 없다.
- 지금의 1/32 블록
  - ctx.out을 0으로 만든 절제와 같은 epoch(last.pt) 비교에서 거대 슬러그 결과는 같았다. 작은 기포 검출 카운터만 조금 달랐다.
  - 가중치 크기(ctx_w 0.0013)는 '고칠 신호가 없었다'는 해석과 '과소학습'이라는 해석에 모두 맞는다. 가중치만으로는 둘을 가르지 못한다.
- 화면 끝에 닿는다고 해서 한 프레임으로 풀 수 없는 문제가 되지는 않는다.
  - 731~790의 거대 기포 82개 중 72개가 화면 끝에 닿는다.
  - 그런데 17번 프레임에서는 화면 끝 슬러그도 영역 전체 p_in 투표로 98.9%, 부호 검증 홀짝으로 약 100% 맞았다.
  - 액체 쪽 기준점이나 닫힌 영역이 화면에 보이지 않을 때만 한 프레임으로 안/밖이 정해지지 않는다.
- 먼저 거대 슬러그 val/test와 조각 지표가 있어야 한다(로드맵 7). 지금 test에서는 모든 모델이 large 21/21이라 차이가 보이지 않는다.

**Q3. 트랜스포머를 추적에 쓰면? 지금은 아니오. 학습 없는 비교선으로만 쓴다.**
- 맞는 형태는 검출 토큰 위에서 동작하는 연결기(Trackastra형)다. 하지만 트랙 GT가 필요하고(합성 GT의 한계는 Q1 참고), 합체를 다루지 못한다.
- 대형 기포에서 '애매한 선택'은 드물다. 속도를 아는 대형 링크의 97.8~99.5%는 2위 후보와 넉넉히 구분된다. 다만 두 가지를 주의해야 한다.
  - 이 수치에는 생존 편향이 있다. 마진을 계산하려면 앞선 관측이 2개 필요하므로 모든 트랙의 첫 링크가 빠진다. 트랙 길이 중앙값은 2~5에 불과하다.
  - 대형 내부 소실 270건 중 39건은 바로 다음 프레임에 비슷한 크기의 검출이 있었는데도 잇지 못했다.
  - 즉 대형의 문제는 후보 사이의 선택이 아니라 후보를 아예 잇지 못하는 것(게이트, 이벤트 처리)이다. 이것은 트래커 로직 점검(로드맵 8)의 대상이다.
- 이득이 생긴다면 tiny/small에서다.
  - 면적 가중 평균 u_B와 C0에는 영향이 작다.
  - 크기별 슬립비·C0나 기포 수·크기 분포를 보고하면, tiny/small 연관 오류가 그 값에 직접 들어간다('논문 관점' 참고).
- 학습 없이 해 볼 수 있는 것은 두 가지다.
  - 사전학습 Trackastra를 PC에서 **원본 프레임**에 추론만 돌려 tracker3와 비교한다.
  - SAM 2 비디오 전파를 거대 슬러그 몇 개의 라벨 초안 도구로 쓴다.
- 픽셀 단위 end-to-end MOT 트랜스포머(TrackFormer, MOTR)는 ID가 붙은 영상과 다중 GPU가 필요해서 맞지 않는다.

**Q4. TAU / Trans-UNet을 더 잘 쓰려면?**
- 시간 정보는 입력 채널이 아니라 결정 단계에서 쓰는 것이 맞다. 각 프레임의 분할 후보 중에서, 속도로 옮긴 t±1 마스크와 가장 잘 맞는 것을 고르는 방식이다. 그런데 지금 코드에는 그런 후보가 없다.
  - `_rescue_leaked`는 어떤 기포에도 속하지 않은 심에서만 돌고, 기존 기포의 화소는 바꾸지 않는다(docstring: '既にある気泡の画素は変えない').
    - 그래서 wall과 RESCUE_SCHEDULE 단계별 결과에는 '조각을 합친' 후보가 없다.
    - 대형 소실 끝의 30%는 면적 0.55배 미만의 조각으로 이어진다. 이것을 고치려면 조각 합집합 후보나 약한 벽을 지운 후보를 따로 만들어야 한다.
  - `main()`은 3채널 ckpt를 `main_single`로 보낸다. 다중 패스의 `detect_pass`는 패스마다 `detector.prob`을 다시 계산한다. 그래서 디스패치와 확률맵 캐시도 바꿔야 한다.
  - 규모는 150~300줄로 본다(학습 없음).
  - 637~641처럼 이웃 프레임도 똑같이 틀리면 효과가 없다. 그래서 조건부 항목으로 둔다.
- 추가 입력이나 모듈은 그것 없이는 풀 수 없는 학습 사례가 있어야 쓰인다. 재학습하기 전에 추론만으로 먼저 확인한다. 화면 끝 잘림이나 얼룩을 붙인 val에서 best.pt가 실제로 틀리는지 본다.
- 트랜스포머를 다시 시도한다면 세 가지가 필요하다.
  - 새 모듈 전용 학습률. 지금은 AdamW가 모든 파라미터에 미세조정과 같은 1e-4를 쓴다.
  - 거대 슬러그 학습 프레임.
  - 같은 epoch(last.pt)끼리 시드 2~3개로 비교하는 것.
  - LayerScale을 1e-4로 초기화하는 것은 Adam에서 0 초기화와 사실상 같아서 해결책이 아니다.
- 원래 뜻대로 "큰 기포만 잡는 트랜스포머"를 만든다면, best.pt를 고정하고 별도 분기를 붙이는 것이 안전하다.
  - 손실에서는 작은 기포 화소와 그 둘레 몇 px만 IGNORE로 둔다. 배경·액체 화소와 큰 기포는 그대로 감독한다.
  - 배경까지 IGNORE로 두면 분기가 전부 기체라고 내도 손실이 줄어든다. 그러면 학습이 무너진다.
  - 출력은 큰 기포 판정에만 쓰고, 작은 기포는 기존 출력을 쓴다. 이렇게 하면 미세조정 때 tiny 재현율이 무너진 일(A: 0.53→0.20)을 피할 수 있다.
  - 이것도 학습셋에 거대 슬러그 실패 프레임이 먼저 있어야 한다.

**Q5. 더 잘 추적할 새 방법은? 새 모델보다 측정과 작은 수정이 먼저다.**
- 먼저 측정할 것 4가지
  - (a) 추적 민감도
    - 112·750프레임 영상에서 정방향/역방향과 파라미터 변형을 돌리고, 트랙 단위 부트스트랩으로 신뢰구간을 낸다.
    - 731~790(느린 60프레임)의 정방향/역방향 차이는 인용하지 않는다. 공통 링크 130개의 평균은 −25.7로 같고, 차이는 18~48k px 거대 링크 약 6개에서 나왔다(로드맵 1).
  - (b) 무작위 링크 감사.
  - (c) 키모그래프로 슬러그 속도와 길이를 추적과 독립적으로 확인.
  - (d) 거대 슬러그 평가 프레임.
- 학습 없는 수정
  - 이미 구현한 EDGE_TOUCH_PX / MAX_AGE_NEW_LARGE를 사용자 데이터로 실행한다.
  - 게이트를 보정한다.
    - B 실행의 POS_GATE 20.4 px와 PIV_GATE 23.9 px는 tiny 이웃 간격 21.5 px와 거의 같다.
    - 부트스트랩 예측기 불일치를 고치고, tiny/small에만 간격 상한을 둔다.
  - 대형 끊김 39/270건을 디버그하고, 합체 직후 '신규' 처리와 면적 히스테리시스를 고친다.
  - 대형 영역 판정을 25 px 띠 대신 영역 전체 p_in으로 바꾸는 안은 저장된 확률맵에서 오프라인으로 먼저 시험한다.
  - 수정의 효과는 QC 플래그가 아니라 의사 GT(솎은 실영상, 반인공 GT)로 판정한다.
- 거대 슬러그는 다음 순서로 간다.
  1. 영역 전체 판정(오프라인 시험).
  2. 실패하면 부호 검증 벽 + 소프트 홀짝.
  3. 조건이 맞을 때만 시간 후보 선택.
- 작은 점은 진행 중인 라벨 보충으로 다룬다. 재촬영 때 프레임률을 올리면 tiny 이동/간격 비(지금 0.72)가 줄어든다. 대신 해상도나 시야가 줄어드는 대가가 있다(로드맵 10).

## 지금까지 왜 안 됐나

### 공통 원인
- **필요한 학습 사례가 없었다.**
  - 추가한 입력과 용량은 학습 데이터에 "그것 없이는 틀리는 화소"가 있을 때만 쓰인다.
  - TAU 사전 채널(약 0.002), ctx(0.0013), DK/DB(0.0015/0.002)가 모두 0 초기화 잡음 수준에 머물렀다. 영상 채널 가중치는 0.073이다.
  - 다만 가중치 크기만으로 "안 쓴다"고 할 수는 없다. 특히 ctx와 DK/DB는 과소학습이나 데이터 구성 때문에도 같은 크기가 나올 수 있다(예전 데이터가 표본의 50%이고 거기서는 DK = B, DB = 0).
  - best.pt, tau_best, tau480은 train_hw가 [1080, 416]이다. 그래서 1200×480 조건의 화면 끝 거대 슬러그와 얼룩은 거의 배우지 않았다.
  - raw A/B/C의 train_hw(새 원본 50장의 최빈 크기)는 기록되어 있지 않다. 이 원인을 트랜스포머와 DK/DB 결과에 적용하는 것은 미확인이다.
- **평가가 실패를 보지 못했다.**
  - large 클래스(≥ 500 px, IoU ≥ 0.3)는 조각남을 잡지 못한다. 시작 모델, A, B, C 모두 21/21이었다.
  - val이 약 8장이라 best epoch 선택은 운에 좌우된다. A와 B의 test 차이도 트랜스포머보다 epoch 선택(4 vs 23) 탓일 가능성이 크다.
  - test 객체 집계는 wall `extract_instances`만 쓴다. 실제 파이프라인(hybrid)과 다르다.

### TAU (사전 마스크 채널)
- 1차(160장): 사전 효과가 경계 IoU ≤ +0.0002였다. best는 epoch 3, 사전 가중치는 0.0007이었다.
- 2차(480장 + 화상 망가뜨리기): 효과는 +0.0004, 가중치는 0.0021이었다.
  - 화상을 망가뜨려도 사전 없이 경계 IoU가 0.573→0.569로 거의 떨어지지 않았다. U-Net이 윤곽의 틈을 스스로 메운 것이다.
- raw C(USE_PRIOR=True): 사전 가중치가 ep1의 0.0017/0.0029에서 거의 변하지 않았다. 정답으로 만든 사전(상한)을 넣어도 tiny는 4개만 늘었다.
- 이유
  - MaskTrack에서는 마스크가 "어느 물체를 분할하라"는 정보라서 반드시 쓰인다. 우리 3클래스 분할에서는 영상만으로 거의 모든 학습 화소가 풀린다. 그래서 흐트러뜨린 사전(영상보다 부정확)은 무시하는 것이 최적이 된다.
  - 추론 때의 사전은 이웃 프레임 검출에서 온다. 그런데 사전이 정말 필요한 프레임에서는 이웃 프레임도 똑같이 애매하다. 637~641의 세로 띠는 4프레임 모두 누락이다.
  - 교훈: 학습하기 전에 best.pt로 망가뜨린 val을 평가했다면 학습 없이 알 수 있었다.

### 트랜스포머 (1/32, 2층, 출구 0 초기화)
- ctx_w는 0.00051(ep1) → 0.00124(ep23) → 0.00128(ep80)로 변했다.
  - 일관된 신호가 없을 때 Adam이 만드는 random walk의 예측치(약 0.0017~0.0021)와 같은 크기다. cosine LR을 따라 평탄해진다.
- 해석은 두 가지가 모두 가능하고, 가중치만으로는 가르지 못한다.
  - 해석 1: 이 블록이 고칠 오류 신호가 학습 데이터에 없었다.
  - 해석 2: 과소학습이다.
    - 무작위 초기화 블록을 모든 파라미터 공통 lr 1e-4(AdamW, train.py 571행)로 학습했다.
    - batch는 4, 에폭당 약 22스텝이다. B의 best(ep23)까지 약 500스텝, 전체는 약 1760스텝이다.
    - 이런 조건에서는 블록 안 특징이 쓸모 있어지기 전이라 출구 기울기의 평균이 0에 가깝다. 그래서 같은 random walk가 보인다.
    - "일관된 신호가 있었다면 스텝당 약 lr씩, 최대 약 0.05까지 움직였을 것"이라는 계산은 블록 안 특징이 이미 쓸모 있을 때만 맞는다.
- 학습량 비교
  - TransUNet 공식 코드는 ImageNet-21k로 사전학습한 R50+ViT-B/16을 batch 24로 약 14k iter 학습한다(trainer.py가 train.py의 30000을 덮어씀). 우리가 본 샘플 수의 약 48배다.
  - 우리 블록은 무작위 초기화였다. ControlNet의 0 초기화가 통하는 것은 새 가지가 사전학습 모델의 복사본이기 때문이다.
- 효과
  - ctx.out을 0으로 만든 절제에서도, A(last) vs B(last) 비교에서도 거대 슬러그 결과는 같았다.
  - 객체 F1은 B 0.819, 시작 모델 0.828이다. B에는 대응되지 않은 tiny 예측이 27개 있었다.
  - QC on/off 차이(트랙 2262 vs 1966, 평균 길이 6.33 vs 7.35)는 근거로 쓸 수 없다. 두 실행은 ROI([0,1,432,1109] vs [0,3,432,1107])와 자동 게이트(POS_GATE 20.4 vs 27.0, PIV_GATE 23.9 vs 27.0, AREA_RATIO_GATE 1.78 vs 1.74)가 다르다.
  - 게이트와 무관한 검출 카운터도 조금 달랐다(pair_split 105/125, only_wall 477/550, nested 41/44). ROI가 위아래로 2 px 다르므로 엄밀한 비교는 아니다. 그래도 그 차이만으로 설명하기에는 큰 차이다.
  - 결론: 거대 슬러그에는 보이는 효과가 없고, 작은 기포 검출만 조금 바뀌었다.

### 부호 입력 (DK = 어두워진 분, DB = 밝아진 분)
- 첫 conv 가중치가 0.0015/0.002였다. 학습 표본의 50%는 예전 이진화 데이터(DK = B, DB = 0)라서 그 절반에는 부호 정보가 아예 없었다.
- 측정(27/28/31번 원본)
  - 닫힌 기포 내부는 액체보다 3.8~5 계조 어둡다(15/15).
  - 거대 슬러그 경계 양쪽의 밝기 프로파일은 대칭이다. 차이는 −0.24 계조이고, 기체 쪽이 더 어두운 열은 57%로 동전 던지기 수준이다. 깊은 내부는 +2~+3이다.
  - 얼룩은 +17이다. 가짜 벽은 +9~+16, 진짜 메니스커스는 −40~−100이다.
- 해석: 부호 정보로 얼룩이 만드는 가짜 벽을 국소적으로 가려낼 수 있다. 하지만 그런 사례가 학습셋에 거의 없었다. 거대 슬러그 깊은 내부에는 단서 자체가 없다.
- 유용성은 아직 모른다. 추론 때 DK/DB 가중치를 0으로 만드는 절제(추론만)가 필요하다.
- 1200×480 조건은 화소의 92%가 포화(255)되어 원본에도 단서가 없다.

### 거대 슬러그 실패의 실제 구성 (측정)
- **얼룩**: 국소 질감 문제이고 부호 정보로 풀린다. 원본과 배경이 있어야 한다.
- **L자(638)**
  - thr 0.2·closing 5로 다시 닫으면 L 영역(4.1만 px, 심 비율 0.57)이 이미 분리된다. 25 px 띠 판정(13195 < 17691)에서만 떨어진다.
  - 640/641은 (0.1, 7)로 닫아도 액체와 이어진다.
- **화면 끝 슬러그**
  - 731~790에서 대형(≥ 2000 px) 인스턴스의 69%가 화면 끝에 닿고, 이들이 대형 면적의 86%를 차지한다.
  - 750프레임 CSV에서는 검출 기체 면적의 57%가 2만 px 이상 검출에, 55%가 화면 끝 접촉 검출에 있다.
  - 화면 끝 접촉 자체가 판정을 불가능하게 만들지는 않는다. 17번의 화면 끝 슬러그는 영역 방법으로 풀렸다. 액체 기준점이나 닫힌 영역이 화면 안에 보이지 않을 때만 한 프레임으로 안/밖이 정해지지 않는다.
- **이웃 기포와의 접촉**: 거대 기포의 63%(52/82)가 2 px 안에서 다른 기포와 닿는다. 기체와 기체 사이의 막도 벽이 되므로, 홀짝은 엄격한 2색 칠하기가 아니라 p_in과 섞는 소프트 제약이어야 한다.
- **17번 프레임 프로토타입**
  - 단순한 영역 전체 p_in 투표만으로 슬러그 98.9%, 얼룩 구역 96.4%다. 부호 검증 홀짝의 추가 이득은 +1.1 / +3.6 pt뿐이었다.
  - 아래 오른쪽 누출 기포는 영역 방법 모두 0%였다.
  - 프레임 1장의 결과이고, 정답이 아니라 같은 p_edge로 만든 참조와 비교한 값이다.

## 추천 로드맵

공통 조건
- 학습은 사용자 PC에서 한다. 클라우드 학습은 금지다.
- 새 규칙은 전부 플래그로 켜고 끌 수 있게 한다.
- 측정용 스크립트는 저장소 밖 일회용으로 둔다.
- 사용자 데이터로 검증하는 실행은 사용자가 요청할 때 한다.

| # | 방법 | 무엇을 고치나 (오류 종류) | 필요한 것 | 기대 효과 | 첫 실험 | 위험 |
|---|---|---|---|---|---|---|
| 1 | **추적 민감도 측정**: tracker3를 정방향/역방향, PIV off, AREA_RELAX off, 게이트 ±로 돌려 u_B·C0·슬러그 길이의 퍼짐을 잰다 | 직접 고치지 않는다. 추적이 연구 출력을 얼마나 흔드는지 수치로 만든다 | 라벨·GPU 없음. 일회용 스크립트 30~50줄. 저장 마스크가 있으면 클라우드에서도 가능 | 추적 개선이 필요한지 판단할 근거. 논문의 '추적 불확도' | 112·750프레임 영상에서 부트스트랩을 끄고 게이트를 고정해 반복한다. 트랙 단위 부트스트랩 CI를 낸다. 731~790의 −24.9 vs −29.9 px/frame은 쓰지 않는다. 대형 1:1 링크 150/146개 중 공통 130개(평균 −25.7)는 같고, 차이는 거대 링크 약 6개가 만든 표본 잡음이다(링크별 중앙값 −22 vs −19) | 퍼짐은 오류가 아니라 불확도다. 합체/분열 규칙이 방향에 따라 달라 과대평가될 수 있다. 거대 링크 몇 개가 면적 가중 값을 좌우하므로 CI 없이 % 하나로 보고하지 않는다 |
| 2 | **이미 구현한 수정을 실행** + 게이트를 고정해 재비교 | 화면 끝 진입·이탈의 ID 변경, 대형 새 트랙의 2프레임 누락 | 코드 0줄. PC에서 재실행 | 144프레임 CSV(6cddd5bd)의 화면 끝 문제(약 30행이 touch = 0) 제거. ctx on/off를 공정하게 비교 | 144프레임 영상을 EDGE_TOUCH_PX = 3, MAX_AGE_NEW_LARGE = 3으로 재실행해 대형 내부 신규/소실을 비교한다. ctx on/off는 같은 ROI·게이트로 비교 | 낮음 |
| 3 | **무작위 링크 감사 + 대형 속도 감사** | 정확도 미측정. 지금 논문에는 실데이터 정확도 수치가 없다 | 조건당 사람 25~40분(+ 판정 시간 확인용 10분 시험). y/n 창 약 100줄(dot_labels의 Review 클래스 재사용) | 크기별 링크 정밀도·재현율. 대형 30개 트랙의 선단 변위로 속도 오차 | 144프레임 CSV에서 크기별 100/100/100 링크 + 60/60/60 재현 표본. 확신 링크도 표본에 넣는다 | CI를 링크 독립으로 계산하면 좁게 나온다. 오류는 트랙·합체 이벤트 단위로 몰린다(대형은 100프레임에 약 145트랙, 길이 중앙값 3). CI는 트랙·이벤트 단위 클러스터 부트스트랩으로 낸다. 장거리 ID 일관성은 못 본다. tiny는 'unsure'를 따로 보고하고, 검출 누락과 연관 오류를 분리한다 |
| 4 | **추적과 독립된 검증**: 키모그래프(공간-시간 단면)로 선단·후단 속도와 슬러그 길이, 크기별 PIV 기체 속도 | 면적 가중 출력(대형 u_B·길이)을 독립적으로 확인. 화면 끝에 잘린 슬러그는 중심 속도가 편향된다 | 수십 줄, CPU, 라벨 없음. 기존 프레임 + CSV로 클라우드에서도 가능. 기체 연속 검사에는 측정 기체 유량 | 열유체 리뷰어가 요구할 물리적 확인. 프레임보다 긴 슬러그의 길이 | 대형 슬러그 10개의 키모그래프 기울기 vs CSV 속도 | 슬러그가 겹치는 열에서는 기울기가 섞인다. 기체 연속(j_G = ⟨α u_G⟩)은 약 1 mm 간극·액막·화면 끝 때문에 참고용으로만 쓴다 |
| 5 | **의사 GT 3종**: (a) 솎은 실영상, (b) 반인공 GT(Hessenkemper 방식), (c) 시뮬레이터를 현재 코드로 재실행 | 고속 조건, 게이트·이벤트 규칙, QC 플래그의 정밀도가 검증되지 않은 문제 | (a) 731~790을 2·3프레임 간격으로 솎아 추적하고, 원래 속도에서 감사한 링크와 비교. 약 50줄. (b) 확신 높은 트랙 조각(고립, 정·역방향 일치, 이벤트 없음)을 다른 시간대에서 가져와 겹치지 않게 한 시퀀스에 넣는다. 약 100줄, CPU, 학습 없음. (c) tests/bundles.py로 sim_compare/sim_piv를 2_bin_track에 연결 | 이동/간격 비 0.5→1.0~1.5에서 크기별 오연결·끊김 곡선. (b)는 실제 모양·궤적과 연달아 생기는 실제 누락을 가진 ID 정답. (c)로 QC 플래그의 정밀도·재현율 | stride 2/3. 731~790 조각을 겹쳐 밀도를 1.5배·2배로 만든 시퀀스(저장 마스크를 그대로 검출로 사용) | (a)는 합의 오류를 물려받는다(이벤트 포함 대형 불일치 13~24%). (b)는 확신 조각만 써서 쉬운 기포로 치우치고, 겹친 기포 사이 상호작용이 없어 합체 평가는 못 한다. (c)는 실제보다 쉽다(잔차 2.2 vs 4.8 px, tiny POS_JUMP 10 vs 49%, 누락 i.i.d.) |
| 6 | **게이트 보정**: ① 부트스트랩 예측기 불일치 수정, ② tiny/small에만 간격 상한 | 게이트가 tiny 이웃 간격과 같은 폭이라 이웃을 가로챈다(B 실행 POS_GATE 20.4, PIV_GATE 23.9 vs tiny 이웃 간격 21.5 px). CLAUDE.md 2장의 원인 2 | ① 부트스트랩은 직전 변위 차 \|d2 − d1\|로 POS_GATE를 정하는데, 트래커는 EMA 예측 잔차에 게이트를 건다. 부트스트랩도 같은 EMA 잔차로 재게 고친다(버그 수준). ② v2의 SPACING_GATE_FRAC = 0.7 × 같은 프레임 최근접 이웃 거리(화면 끝 제외)를 tiny/small에만. large는 넣지 않는다(v2에서 슬러그 옆 작은 기포 때문에 슬러그 게이트가 좁아진 실패). 수십 줄, 플래그 | tracker3에는 간격 게이트가 없다. v2(흐름 prior + 간격 게이트 등의 묶음)는 합성에서 tiny 오연결을 15.4→1.3%(중속), 20.3→2.9%(고속)로 줄였다. 간격 게이트 단독 효과는 재지 않았다 | 5번 의사 GT에서 크기별 오연결·끊김 곡선. 112프레임 영상 QC | 끊김이 늘 수 있다(v2는 고속 실데이터에서 프레임당 약 73개 내부 신규). 합성 9배 개선(tiny 44.1→4.9%)은 극단적 깜빡임에서 부트스트랩이 무너진 경우(POS_GATE 90~118 px)라 일반화하지 않는다. POS_JUMP가 게이트와 같은 잔차로 정의되어 있어 QC 플래그로는 판정하지 못한다 |
| 7 | **거대 슬러그 val/test + 조각 지표** | 분할 변경(트랜스포머, 홀짝, 학습 데이터)을 평가할 수 없는 문제 | 12장(6 val + 6 test, 에피소드별, 영상 2개 이상). 0_prelabel 초안으로 대형만 라벨: 1~4시간. 지표 30~60줄(tools/raw_parts → build_raw) | best 선택이 운에서 벗어난다. 논문의 '슬러그 조각률' | 학습 없이 시작 모델·A·B의 last.pt를 6장에서 채점(SEG > 50% hit, 조각 수, 최대 조각 IoU). 차이가 없으면 구조 변경은 순위에서 뺀다 | 680~696의 31만 px 검출처럼 오검출일 수 있는 것은 화상으로 확인한다. 6장은 작으므로 장별 값을 보고한다. 포화된 1200×480보다 노출이 적당한 영상에서 라벨한다 |
| 8 | **트래커 로직 점검 (학습 없음)** | 대형 끊김 39/270건, 합체 직후 '신규' 처리, tiny 면적 경계 깜빡임 | 항목당 수 줄~40줄, 플래그 | 대형 소실 끝 최대 14% 감소. 합체 인접 신규의 초과분(small/large +11~18 pt) 감소 | 39건을 리뷰 화상으로 원인 분류(AREA_RATIO_GATE 1.78, MAX_AGE_NEW, 4b 단계). 면적 히스테리시스: 기존 트랙은 5 px까지 유지, 신규는 10 px 이상 | 끊김과 오연결의 trade-off는 QC 플래그로 판정할 수 없다. 3번이나 5번으로 판정한다 |
| 9 | **대형 영역 판정 교체**: 면적 ≥ 2000 영역만 25 px 띠 대신 영역 전체 Σ(log p_in − log p_bg)로 판정. 실패할 때만 부호 검증 벽 + 소프트 홀짝 | 638류 L자 누락. raw 입력에서는 얼룩이 만드는 가짜 벽 | 먼저 저장된 확률맵(731~790, 637~641; 없으면 PC에서 SAVE_PROB_MAPS=True로 한 번 저장)에서 신경망 없이 오프라인 시험(클라우드 가능). 통과하면 약 10줄 플래그로 저장소에 넣는다. 홀짝은 200~300줄이라 나중에. 부호는 원본 + 배경 필요 | 17번에서 영역 투표만으로 98.9 / 96.4%. 638 회수 가능성(미검증) | 오프라인에서 638 회수 여부. 731~790 회귀(wall이 맞힌 대형 15건 포함 60/60 동일) | 영역 전체 합은 25 px 띠보다 seed 실패와 같은 함정(대형 깊은 내부 p_in < 0.5)에 더 노출된다. 지금 맞는 대형 영역을 버릴 수 있다. 638 효과는 시험하지 않았다. 640/641 같은 틈 누출은 못 고친다 |
| 10 | **작은 점 라벨 보충** + 재촬영 시 **프레임률 상향** | tiny 깜빡임. 검출 실패의 59%가 또렷한 점에 U-Net ≈0 | 사용자 y/n(후보당 약 2초), PC 재학습. 프레임률은 코드 0줄. 이미 진행 중(사용자 작업 순서 1번)이라 순위와 무관하게 계속한다 | tiny 재현율과 끊김 개선. 프레임률 2배면 이동/간격 비 0.72 → 약 0.36 | 이미 계획됨(dot_labels → 1_bin_train, ignore 사용) | 점이 늘면 연관이 더 애매해진다. 적은 새 라벨로 미세조정하다 tiny가 무너진 이력(A 0.53→0.20)이 있으므로 ignore와 OLD_VAL_TOL을 유지한다. 대부분의 고속 카메라는 fps를 올리면 해상도나 시야(ROI)를 줄여야 한다. 시야가 줄면 화면 끝에 잘리는 슬러그가 는다(이미 대형 면적의 55~86%가 화면 끝 접촉). 해상도가 줄면 tiny 점의 화소가 줄어 검출이 더 어렵다. 재촬영 계획에서 fps·해상도·시야·노출(배경 약 200~220)을 함께 정한다 |
| 11 | (선택) **사전학습 모델 추론만**: SAM 2 비디오(거대 슬러그만), DINOv2 PCA 탐침, Trackastra zero-shot | 거대 슬러그 마스크 초안, 독립 비교선 | PC 추론, 새 의존성, 일회용 스크립트 | 통과하면 라벨 초안과 비교 기준선. 통과 못 하면 중단 | DINOv2 ViT-S/14로 27.jpg(원본)의 패치 토큰 PCA를 보고 기체·액체·얼룩이 갈리는지 확인. SAM 2는 638~641을 좋은 프레임에서 전파. Trackastra는 원본 프레임 + 우리 마스크로 | 이진화 입력에서는 기체와 액체가 같은 검정이라 실패 가능성이 크다. Trackastra의 밝기 특징도 이진화 B에서는 쓸모없다. 의존성이 는다. 우리 데이터에서 검증하기 전에는 논문에 쓰지 않는다 |

**조건부 (지금은 보류하고, 조건이 생기면 시도)**
- **시간 일관성으로 분할 후보 선택**(Ultrack 아이디어의 자작판)
  - 조건: 7번 평가에서 "이웃 프레임은 맞고 해당 프레임만 조각난" 사례가 충분히 나올 때.
  - 필요한 것
    - 조각 합집합 후보와 약한 벽을 지운 후보를 새로 만든다. 지금의 wall과 RESCUE_SCHEDULE에는 이런 후보가 없다.
    - 3채널 ckpt의 디스패치(`main()` → `main_single`)를 바꾼다.
    - 확률맵을 캐시한다(`detect_pass`가 패스마다 다시 계산하므로).
    - 규모는 150~300줄로 본다.
  - 위험: 진짜 합체·분열을 숨길 수 있다. 637~641처럼 이웃 프레임도 틀리면 효과가 없다.
- **오프라인 gap closing / stitching**
  - MAX_AGE = 3과 4b 단계와 겹친다.
  - tracker3 게이트를 통과하는 고유 후보는 tiny 23%, small 33%, large 48%뿐이다. 대형은 프레임당 0.12건이다.
  - CSV만으로 시험할 수 있으니 트래커 코드는 고치지 않는다.
- **ByteTrack식 낮은 임계값 복구**
  - 지금 근거는 약하다. "놓친 위치에서 p_in < 0.05가 93~97%, 0.2~0.5 대역은 2%로 대조군과 같다"는 값은 예전 best.pt로 느린 731~790에서, 고립된 내부 트랙 끝의 예측 위치를 잰 것이다.
  - 그 위치에서 p ≈ 0인 것은 기포가 실제로 나갔거나 합쳐졌거나 예측이 빗나가도 생긴다. 그 끝의 22%는 이웃에 흡수됐다.
  - 조건: B 모델 고속 영상에서 SAVE_PROB_MAPS로 같은 측정을 다시 해서 0.2~0.5 대역이 대조군보다 뚜렷이 많을 때.
- **부호 검증 벽 + 소프트 홀짝**: 9번의 영역 판정이 실패할 때만 시도한다. raw 프레임이 있어야 한다.
- **정지 벽 거부**(5프레임 이상 움직이지 않는 흰 구조 제거)
  - 부호 정보가 없을 때의 보조 검사다. 731~790에서는 효과가 0이다.
  - 6cddd5bd의 144프레임 내내 정지한 물체 3개(500 px 이상 면적의 6%)가 고정 기포인지 화상으로 확인한 뒤 판단한다.
- **대형 전용 분기 / DINOv2 동결 특징 융합**
  - 조건: 7번 평가셋과 거대 실패 학습 프레임이 생기고, DINOv2라면 PCA 탐침까지 통과했을 때.
  - 대형 전용 분기는 작은 기포 화소와 그 둘레만 IGNORE로 둔다(Q4).
- **4프레임 look-ahead**: 112프레임 영상에서 게이트 안 후보가 2개 이상인 할당이 tiny/small 링크의 10%를 넘을 때. 느린 영상에서는 0~8%였다.
- **학습형 연결기**: 3번 감사나 5번 GT에서 고전적 수정 뒤에도 오연결이 약 2%를 넘고, 논문이 크기별 출력을 보고할 때.
- **시간 일관성 손실 학습**(라벨 없는 연속 프레임, 입력 채널 없음): 라벨 보충 뒤에도 한 프레임만 p ≈ 0으로 꺼지는 깜빡임이 남을 때.

## 비추천

| 방법 | 이유 |
|---|---|
| 트랜스포머를 1/16·1/8로 옮기기 | 1/32가 이미 큰 물체용 스케일이다. 내리면 작은 구조 쪽으로 가서 목적과 반대다. 토큰은 4·16배, 어텐션 비용은 16·256배가 된다. 무작위 초기화, 약 1760스텝, 실패 사례 없는 학습셋이라는 문제는 그대로다. 고해상도 스킵 근처는 tiny 재현율이 흔들릴 위험이 더 크다(B에서 대응 안 된 tiny 예측 27개) |
| 같은 위치에서 트랜스포머를 깊거나 넓게 만들기 | 무작위 초기화 파라미터만 는다. TransUNet은 사전학습 ViT에 기대고 있다. 같은 데이터·학습량으로는 배울 것이 늘지 않는다 |
| 데이터는 그대로 두고 1/32 블록의 학습 조건만 손보기(LR, LayerScale, 보조 헤드) | 학습셋에 실패 사례가 없으면 학습률을 바꿔도 배울 것이 없다. LayerScale 1e-4는 Adam에서 0 초기화와 같다. 기체 비율 보조 헤드는 CNN이 이미 맞히는 것을 가르친다. 실패 프레임(7번)이 생기면 Q4의 조건으로 다시 본다 |
| 사전학습 TransUNet / Swin-UNETR로 교체 | best.pt와 미세조정 이력을 버리고, tiny와 경계를 약 530장으로 다시 배워야 한다. 코드가 크게 는다. Matsoukas의 근거는 분류 연구다 |
| 축방향·윈도·변형 어텐션, PSP, 큰 커널, ASPP, non-local | 모두 무작위 초기화 모듈이라 '실패 사례 없는 학습셋' 문제가 같다 |
| 거리·흐름·레벨셋 표현(Omnipose, StarDist, Deep Watershed, Chan–Vese, DALS) | 정보를 더하지 않는다. 화면 끝에서 잘린 물체는 거리가 정의되지 않는다. StarDist는 별-볼록이라 L/U자를 표현할 수 없다. 슬러그 내부와 액체의 D 중앙값이 둘 다 0이라 Chan–Vese가 쓸 평균 밝기 차가 없다 |
| 위상 손실(clDice, Betti matching) | 닫힌 곡선의 어느 쪽이 기체인지 정해 주지 않는다. 학습이 느리고, 붙은 쌍 융합(28~39%)이 나빠질 수 있다 |
| 순환 coloring 모듈(hGRU, Deep Thinking, FFN류) | 경로 추적·insideness류 과제를 겨냥한 구조지만 연구 과제 규모다. 규칙 홀짝이 어디서 실패하는지 세기 전에는 착수할 이유가 없다 |
| TAU 재학습(화면 끝 잘림 crop, 얼룩 붙이기, 입력 dropout), 다중 프레임 입력 채널, ConvLSTM / 3D U-Net | TAU 보류는 사용자와 합의했다. 사전이 필요한 프레임에서는 이웃 프레임도 똑같이 애매하다. 예전 480장에는 이웃 프레임이 없다. '무시되는 추가 입력' 패턴이 반복된다 |
| 내부 밝기 무작위화 합성 증강 | 데이터에 실제로 있는 유일한 국소 단서(닫힌 기포 −3.8~−5)를 학습에서 지운다 |
| 학습형 연결기 학습(Trackastra fine-tune, MPN/GNN, MAGIK, EmbedTrack, linajea) | 실데이터 트랙 GT가 없다. 합성 GT로는 시뮬레이터를 배운다. 부모를 하나만 허용해 합체를 표현하지 못한다. 이득은 tiny/small에서 생기므로 크기별 출력을 보고할 때만 의미가 있고, 그때도 GT 문제가 먼저다 |
| 자기지도 대응 학습(CRW, TimeCycle, Walker, cross-input), tracker3 의사 라벨 자기학습 | 외형이 똑같아 배울 신호가 없다. 의사 라벨은 쉬운 링크뿐이라 확증 편향이 생긴다 |
| End-to-end MOT 트랜스포머(TrackFormer, MOTR/MOTRv2, Cell-TRACTR) | ID 라벨이 붙은 영상과 다중 GPU가 필요하다(TrackFormer 7 × 32 GB는 기억에 근거한 값, 미확인). 2 px 점과 합체에 약하고, 동작하는 U-Net을 버리게 된다 |
| 학습형 PTV(GotFlow3D, DeepPTV, zero-divergence) | 발산 0 가정은 크기에 따라 슬립이 다른 기포에 맞지 않는다. 3D→2D 이식이 필요하다. 주 대상인 tiny는 면적 가중 결과에 기여가 작고, 크기별 출력에서는 GT 없이 효과를 확인할 수 없다 |
| 전역 min-cost flow / ILP 연관, IMM | 같은 검출 사이에서 링크 순서만 바꾼다. 코드가 300~600줄이고 솔버가 필요하다. 지금 좋은 대형 추적(484스텝 중 SWAP 6, POS_JUMP 17)을 해칠 위험이 있다. 대형의 실제 문제는 선택보다 잇지 못하는 쪽이다(Q3) |
| Ultrack 패키지를 그대로 사용 | ILP가 합체를 금지한다('single incoming node (no fusion)', 코드 확인). Windows에서 CBC 설치가 어렵다. 기본 max_distance 15 px가 대형 이동 중앙값 18.8 px보다 작다 |
| 크기 기반(drift-flux) 운동 사전 | 크기는 공간 이웃 정보에 아무것도 더하지 않았다. 그리고 측정한 C0가 순환 논리가 된다 |
| 운동만으로 분할(motion grouping), known-warp 합성쌍 | 이진화 내부에는 질감이 없고, 병진은 벽 양쪽에 대칭이다. known-warp은 트래커의 등속 모델과 같아서 새로 재는 것이 없다 |
| 기성 트랙 편집기로 모든 크기의 GT 작성 | napari-track-edit/funtracks는 두 번째 부모를 거부한다. Fiji 도구는 변환기가 필요하다. 처음부터 하면 100프레임에 4.5~7시간이 든다. 반인공 GT(5번)가 더 싸다 |
| 정방향/역방향 합의를 GT로 삼아 tracker3 채점 | 순환 논리다. 합의는 감사 대상을 고르는 데만 쓴다 |
| RTS 평활 | 연관을 바꾸지 않는다. 평균 u_B는 구간 직선 맞춤으로 충분하다 |

## 논문 관점

**출력의 성격을 먼저 밝힌다**
- CSV는 기포별 행이다(면적, 선단·중심 위치, 상승 속도, 화면 끝 접촉).
- 면적 가중 평균 u_B·C0와 슬러그 길이는 대형이 지배한다. 그래서 대형의 검출·추적 정확도가 핵심이다.
- 다음 출력은 tiny/small의 연관·검출 오류에 직접 민감하다. 이것을 보고한다면 3번 감사의 tiny/small 정밀도·재현율을 같이 쓴다.
  - 크기별 슬립비·C0
  - 기포 수 밀도와 크기 분포(result_area_count의 개수 포함)

**새롭다고 주장할 수 있는 것(범위를 좁혀서)**
1. **대상 영역**
   - 약 1 mm 마이크로갭에서 2 px 점부터 화면을 넘는 슬러그까지, 합체를 포함해 하나의 인스턴스 분할 + 추적 파이프라인으로 다룬다.
   - 검색한 범위에서는 마이크로갭/Hele-Shaw 이상류의 딥러닝 인스턴스 추적 논문을 찾지 못했다.
   - 하지만 확인하지 못한 후보가 있다(전부 미검증).
     - Zhou et al. 2024, IJHMT 222:125188: 과냉 비등에서 기포 검출·추적. 대상 청중의 학술지다.
     - VFNet(2026): 미니채널 시공간 네트워크.
     - Homan et al. 2024, *Deep Learning Bubble Segmentation on a Shoestring*.
     - BubSAM.
   - VFNet이 미니채널 추적이라면 "좁은 유로 딥러닝 추적이 없다"는 주장은 틀린다. 원문을 확인하기 전에는 "최초"라고 쓰지 않는다.
   - 좁은 간극 연구는 고전 영상처리나 X선/중성자 영상(MHT-X 등)이 주류다.
2. **크기별로 분리한 PIV로 새 트랙의 초기 속도를 주는 것**
   - PIV 결과로 PTV 대응을 돕는 것 자체는 고전 기법이다. Keane, Adrian & Zhang 1995(super-resolution PIV)와 Cowen & Monismith 1997(hybrid PTV)이 있다(기억에 근거, 미검증). 유체 분야 리뷰어는 이 논문들을 안다.
   - 그래서 주장을 "인스턴스 마스크로 크기별 영상을 분리해 PIV를 구한 것"으로 좁힌다.
   - 근거(합성 고속): 전체 영상 상관은 피크가 큰 기포를 따라가 tiny 초기 속도 오차가 10.6 px/frame이다. 크기별로 분리하면 1.6 px/frame이다.
   - 느린 실데이터에서 on/off 차이가 없었다는 사실도 함께 쓴다.
3. **정직한 부정적 결과**
   - 정적 라벨로 미세조정했을 때 사전 마스크 채널은 효과가 없었다. 정답으로 만든 사전을 넣어도 tiny는 4개만 늘었다.
   - 0 초기화 트랜스포머 블록은 거대 슬러그에 보이는 효과가 없었고, 작은 기포 검출만 조금 바꿨다.
   - 같은 epoch 비교와 절제 결과로 보고한다. 가중치 크기는 '쓰지 않았다'의 근거로 쓰지 않는다.
   - 열유체 청중에게 "왜 더 큰 모델이 아닌가"에 대한 답이 된다.
4. (9번을 구현하고 검증했을 때만) "계면은 서로 교차하지 않는다"는 물리 규칙에 기반한 영역 판정.

**기여가 아니라 진단 도구로 제시할 것**
- 정답 없는 QC 플래그를 크기별·면적 가중으로 보고하는 것(개수 기준 22%, 면적 기준 1.2%).
- 합성 GT에서 잰 플래그 정밀도가 낮다. POS_JUMP-tiny 0~17%, SWAP_LIKELY-tiny 6~8%다.
- 실제 오연결을 잡는 재현율은 3~36%다. 트랙의 첫 스텝은 점검하지 못한다.
- 그래서 플래그 비율을 오류율로 읽으면 안 된다. 비율을 보고할 때는 이 정밀도·재현율을 바로 옆에 쓴다.

**새롭지 않은 것**
- U-Net + 헝가리안 법.
- 마스크 겹침 기반 합체·분열 처리. u-track과 LapTrack(`merging_cutoff`/`splitting_cutoff`, 코드 확인)에 이미 있다. TrackMate의 LAP tracker에도 있다고 알려져 있지만 이번에 확인하지 못했다.
- 합성 데이터로 검증하는 것.

**기준선**
- 고전 기준선: 임계값/watershed + LAP(LapTrack 또는 TrackMate), 또는 trackpy.
- 내부 비교: tracker2 vs tracker3, wall vs hybrid.
- 선택: 사전학습 Trackastra zero-shot. 원본 프레임에서 돌리고, 합체를 표현하지 못한다는 한계를 명시한다.

**지표**
- **실데이터 정확도**(3번)
  - 크기별 링크 정밀도·재현율.
  - CI는 트랙·이벤트 단위 클러스터 부트스트랩으로 낸다. 링크 단위 Wilson CI는 너무 좁다.
  - 검출 누락과 연관 오류를 따로 세고, unsure 비율도 보고한다.
- **의사 GT**(5번)
  - 솎은 실영상, 반인공 GT, 합성(sim_compare / sim_piv를 현재 코드로 재실행)에서 크기별·면적 가중 오연결률, 끊김률, 합체/분열 발견률을 낸다.
  - 합성은 반드시 '합성'으로 표기하고, 실제보다 쉽다는 점(잔차 2.2 vs 4.8 px, 누락 i.i.d.)을 적는다.
- **QC 플래그**: 비율과 함께 합성 GT로 잰 플래그 정밀도·재현율을 쓴다.
- **이벤트**: 합체·분열의 정밀도/재현율(±1프레임 허용).
- **물리량**
  - u_B, 슬립비, C0, 슬러그 길이의 편향(의사 GT 대비).
  - 정방향/역방향과 파라미터 변형에 따른 퍼짐(추적 불확도). 112·750프레임에서 부트스트랩 CI로 낸다.
  - 화면 끝에 잘린 슬러그는 속도 통계에서 빼거나 표시한다.
- **거대 슬러그**: 슬러그당 조각 수, 최대 조각 IoU, SEG > 50% hit.
- **선택**: traccuracy의 AOGM. 합체 그래프를 받지만 division 지표는 거부한다. HOTA/IDF1/MOTA는 1:1 대응을 가정하므로 보조로만 쓴다.
- **독립 확인**: 키모그래프 선단 속도, 크기별 PIV, 기체 연속(참고용), 문헌의 C0 범위와 비교(drift-flux를 예측기로 쓰지는 않는다).

**통계 설계**
- 학습 비교는 시드 2~3개로 하고, last.pt끼리(또는 k-fold) 비교한다. 잡음 바닥으로는 C−A의 val sd 0.0007을 쓴다.
- val 8장에서 고른 best epoch 하나는 근거가 되지 않는다.
- 링크·화소 단위 통계는 트랙·이벤트·프레임 단위로 묶어 재표본한다.

**논문에 쓰지 말 것**(확인되지 않았거나 표본 잡음인 수치)
- BubbleID MOTA 87.4 vs 66.5, SAM2 크기별 F1(소형 0.58), HOCT의 59% / 400 annotation, Taylor bubble 논문의 1.1% / 6%, TrackFormer 7 × 32 GB.
- 731~790의 정방향/역방향 속도 차 "20%".
- 정밀도·재현율 없이 단독으로 쓴 QC 플래그 비율.

## 참고문헌

검증 한계
- 이번 실행에서 웹 검색 예산이 소진됐고, arXiv·DOI·Crossref·출판사·CVF·PubMed 호스트는 프록시에서 열리지 않았다.
- 아래 "확인됨"은 공식 GitHub 저장소·코드·README나 초록에서 제목·저자·핵심 주장을 확인했다는 뜻이다. 논문 본문의 세부 수치는 따로 표시했다.

### 확인됨: 추적·연결
- Gallusser, Weigert. *Trackastra: Transformer-based cell tracking for live-cell microscopy*. ECCV 2024. https://github.com/weigertlab/trackastra
  - ilp.py의 `MaxParents(1)`, `MaxChildren(2 if divisions else 1)`.
  - 사전학습 모델 general_2d. 학습에는 CTC TRA가 필요하다.
  - `trackastra/data/wrfeat.py`의 `_PROPERTIES`에 intensity_mean/max/min이 있다(코드 사본으로 확인).
- Bragantini, Lange, Royer. *Large-Scale Multi-Hypotheses Cell Tracking Using Ultrametric Contours Maps* (Ultrack). ECCV 2024, arXiv 2308.04526. https://github.com/royerlab/ultrack
  - mip_solver의 'single incoming node (no fusion)'. CBC는 Windows 설치가 어렵다는 주석. 기본 max_distance 15.
- Jaqaman et al. *Robust single-particle tracking in live-cell time-lapse sequences* (u-track). Nature Methods 5:695-702, 2008. https://github.com/DanuserLab/u-track
- Fukai, Kawaguchi. *LapTrack: linear assignment particle tracking with tunable metrics*. Bioinformatics 2022, doi 10.1093/bioinformatics/btac799. https://github.com/yfukai/laptrack
  - `gap_closing_cutoff`(기본 15**2), `merging_cutoff`, `splitting_cutoff`(기본 False). 정답 링크 보존(connected_edges).
- Tinevez et al. *TrackMate: An open and extensible platform for single-particle tracking*. Methods 2017. https://github.com/trackmate-sc/TrackMate
  - LAP merge/split 기능은 README에 없다(미확인).
- trackpy `predict.py`(NearestVelocityPredict, ChannelPredict). https://github.com/soft-matter/trackpy/blob/master/trackpy/predict.py
- Lambert et al. *motile*. https://github.com/funkelab/motile (연도 미확인)
- napari-track-edit / funtracks(합체 간선 거부). https://github.com/funkelab/motile_tracker
- Zhang, Li, Nevatia. *Global data association for multi-object tracking using network flows*. CVPR 2008. https://github.com/nwojke/mcf-tracker
- Ouellette, Xu, Bodenschatz. 4프레임 best estimate. Exp. Fluids 2006, doi 10.1007/s00348-005-0068-7. MyPTV 코드로 DOI만 확인. https://github.com/ronshnapp/MyPTV
- Tan et al. OpenLPT / *3D Lagrangian tracking of polydispersed bubbles at high image densities*. Exp. Fluids 2020/2023. https://github.com/JHU-NI-LAB/OpenLPT_GUI
- Zhang et al. *ByteTrack*. ECCV 2022. https://github.com/ifzhang/ByteTrack
- Brasó, Leal-Taixé. *Learning a Neural Solver for Multiple Object Tracking*. CVPR 2020. https://github.com/dvl-tum/mot_neural_solver
- Zvejnieks et al. *MHT-X: Offline Multiple Hypothesis Tracking with Algorithm X*. arXiv 2101.05202. https://github.com/Peteris-Zvejnieks/MHT-X (Exp. Fluids 게재 정보는 미확인)
- Conservation tracking(Schiegg et al., ICCV 2013). ilastik 문서에서 merger 처리와 "누락 물체는 복구 못 함"을 확인. 논문 본문은 미확인. https://github.com/ilastik/ilastik.github.io/blob/main/documentation/tracking/tracking.md
- Lu et al. *Self-Supervised Multi-Object Tracking with Path Consistency*. CVPR 2024. https://openaccess.thecvf.com/content/CVPR2024/papers/Lu_Self-Supervised_Multi-Object_Tracking_with_Path_Consistency_CVPR_2024_paper.pdf (공식 저장소가 링크)
- Bastani, He, Madden. *Self-Supervised Multi-Object Tracking with Cross-Input Consistency*. NeurIPS 2021. https://github.com/favyen/uns20 ("cycle-consistency가 퇴화한다"는 문장은 미확인)
- Doersch et al. *BootsTAP*. ACCV 2024. https://github.com/google-deepmind/tapnet
- Karaev et al. *CoTracker3* (arXiv 2410.11831). https://github.com/facebookresearch/co-tracker (ICCV 2025 게재는 미확인)
- Sugawara, Çevrim, Averof. *ELEPHANT*. eLife 2022. https://github.com/elephant-track/elephant-server
- Bragantini, Theodoro, Royer. *Higher-Order Cell Tracking Transformer* (HOCT). arXiv 2607.11754. https://github.com/royerlab/hoct (저장소는 있다. 59% / 400 annotation 수치는 페이지에 없어 미확인)
- Kalal, Mikolajczyk, Matas. *Forward-Backward Error: Automatic Detection of Tracking Failures*. ICPR 2010. opencv_contrib tracking.bib에서 서지만 확인.

### 확인됨: 지표
- traccuracy. https://github.com/live-image-tracking-tools/traccuracy (CTC 오류가 합체 간선을 받고, division 지표는 합체 그래프를 거부, v0.4.3 코드)
- Kaiser et al. *CHOTA* (arXiv 2408.11571) / py-ctcmetrics. https://github.com/CellTrackingChallenge/py-ctcmetrics (SEG 규칙 |R∩S| > 0.5|R|)
- CTC measures(AOGM, TRA/SEG/DET). https://github.com/celltrackingchallenge/measures
- Luiten et al. *HOTA*. IJCV 2021. https://arxiv.org/abs/2009.07736 (TrackEval README로 확인)

### 확인됨: 분할·트랜스포머·사전학습 모델
- Chen et al. *TransUNet* (arXiv 2102.04306, MedIA 2024 확장판). https://github.com/Beckschen/TransUNet
  - trainer.py가 약 14k iter로 덮어쓴다. 격자는 14×14. 'small organ' ablation은 CNN 스킵 수에 관한 것이다.
- Zhang, Rao, Agrawala. *ControlNet*. ICCV 2023. https://github.com/lllyasviel/ControlNet
- Bachlechner et al. *ReZero*. UAI 2021. https://github.com/majumderb/rezero
- Oquab et al. *DINOv2*. https://github.com/facebookresearch/dinov2 (ViT-S/14 21M, Apache 2.0)
- Segment Anything predictor(저해상도 마스크 256×256). https://raw.githubusercontent.com/facebookresearch/segment-anything/main/segment_anything/predictor.py
- Ravi et al. *SAM 2: Segment Anything in Images and Videos* (arXiv 2408.00714). https://github.com/facebookresearch/sam2 (propagate_in_video, Apache 2.0)
- Ke et al. *Segment Anything in High Quality*. NeurIPS 2023. https://github.com/SysCV/sam-hq
- Isensee et al. *nnU-Net Revisited* (arXiv 2404.09556); ResEnc 문서. https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/resenc_presets.md (ACDC는 예외)
- Matsoukas et al. *Is it Time to Replace CNNs with Transformers for Medical Images?* https://arxiv.org/abs/2108.09038 (분류 연구)
- Tay et al. *Long Range Arena*. ICLR 2021. https://github.com/google-research/long-range-arena
  - 원 논문 결과표에서는 모든 트랜스포머가 Path-X에서 실패했다.
  - 이후 모델(S4 등)이 풀었다고 알려져 있어 지금은 오래된 논거다. 이 보고서의 근거로 쓰지 않는다.
- Gu, Goel, Ré. *S4*. ICLR 2022. https://arxiv.org/pdf/2111.00396 (저장소로 확인. Path-X 수치는 이 보고서에서 미확인)
- Amos, Berant, Gupta. *Never Train from Scratch: Fair Comparison of Long-Sequence Models Requires Data-Driven Priors*. https://github.com/IdoAmos/not-from-scratch
  - README에는 LRA Image 과제 실험만 있고 Path-X 언급은 없다(이번에 확인).
  - 자기사전학습으로 Path-X를 풀었다는 주장과 학회 정보는 미확인.
- Ding et al. *RepLKNet*. CVPR 2022. https://github.com/DingXiaoH/RepLKNet-pytorch
- Villalobos et al. *Do Neural Networks for Segmentation Understand Insideness?* https://github.com/xboix/insideness
  - README에서 제목·저자·CBMM Memo 105v2만 확인했다. 결론과 연도는 미확인이다.
  - 대상은 CNN·순환망이고 트랜스포머가 아니다. 이 보고서의 근거로 쓰지 않는다.
- Linsley et al. hGRU / Pathfinder(NeurIPS 2018); Schwarzschild et al.(NeurIPS 2021); Bansal et al. *End-to-end Algorithm Synthesis with Recurrent Networks: Logical Extrapolation Without Overthinking*(NeurIPS 2022). https://github.com/aks2203/deep-thinking ; Januszewski et al. Flood-Filling Networks. https://github.com/google/ffn
- Schmidt et al. *StarDist*. MICCAI 2018. https://arxiv.org/pdf/1806.03535
- Liu et al. *Efficient Semantic Video Segmentation with Per-frame Inference*. ECCV 2020. https://www.ecva.net/papers/eccv_2020/papers_ECCV/html/1094_ECCV_2020_paper.php (공식 저장소로 확인)
- Arazo et al. *Pseudo-Labeling and Confirmation Bias in Deep Semi-Supervised Learning*. IJCNN 2020. https://github.com/EricArazo/PseudoLabeling

### 확인됨: 기포·이상류 분야
- Küçük, Della Santina, Laskari. *Segmenting the Complex and Irregular in Two-Phase Flows: A Real-World Empirical Study with SAM2*. arXiv 2508.05227. https://arxiv.org/abs/2508.05227
  - 이전 실행에서 초록으로 SAM 2.1 미세조정, 약 100장, air lubrication을 확인했다. 이번에는 arXiv 접속이 막혀 다시 확인하지 못했다. 크기별 F1과 IJMF 게재는 미확인.
- Hessenkemper, Starke, Atassi, Ziegenhein, Lucas. *Bubble identification from images with machine learning methods*. IJMF 155, 2022. https://arxiv.org/abs/2202.03107
- Hessenkemper et al. *3D detection and tracking of deformable bubbles in swarms with the aid of deep learning models*. IJMF 179:104932, 2024 (서지 확인).
  - 반인공 GT 데이터(서로 다른 시간의 실제 궤적을 한 시퀀스에 겹친 것): https://rodare.hzdr.de/record/2809/export/dcite4
  - RODARE 2811은 미확인.
- Ma, Hessenkemper, Lucas, Bragg. *Fate of bubble clusters rising in a quiescent liquid*. arXiv 2306.02101 (존재만 확인. MPN 학습 데이터는 미확인)
- Dunlap et al. *BubbleID*. J. Appl. Phys. 136:014902, 2024. https://github.com/cldunlap73/BubbleID (MOTA 수치는 미확인)
- Durve et al. *DropTrack*. Physics of Fluids 2022. https://arxiv.org/pdf/2205.02568
- Fu, Liu. *BubGAN*. Chem. Eng. Sci. 2019. https://github.com/ycfu/BubGAN
- Soibam et al. IJMF 169:104589, 2023; Seong et al. IJMF 159:104336, 2023; Schepperle et al. Sensors 24:3363, 2024 (https://www.mdpi.com/1424-8220/24/11/3363). 서지만 확인했고 본문 수치는 미확인.
- Choi, Kim, Park. *Bubble velocimetry using the conventional and CNN-based optical flow algorithms*. Sci. Rep. 2022. https://link.springer.com/article/10.1038/s41598-022-16145-y (제목만 확인. 비교 결과는 미확인)
- BubbleML. NeurIPS 2023 D&B. https://github.com/HPCForge/BubbleML
- Maduabuchi, Jossou, Bucci. *MSEG-VCUQ* (arXiv 2411.07463). https://github.com/chikap421/mseg_vcuq
- Chan et al. *Identifying and tracking bubbles and drops in simulations*. https://arxiv.org/pdf/2011.07243
- Ahire et al. *Deep Learning-Based Tracking and Lineage Reconstruction of Ligament Breakup*. https://arxiv.org/abs/2604.08711 (합성 데이터는 검출기용이고, 연결기는 기하 특징 MLP)
- GOTrack+(TCSVT 2026). https://github.com/wuwuwuas/GOTrack ; Zhang et al. FluidMotionNet(NeurIPS 2024). https://github.com/Forrest-110/FluidMotionNet

### 미검증 (인용 전에 원문 확인 필요, 또는 쓰지 말 것)
- 이번 판에서 새로 넣었지만 열지 못한 문헌
  - Keane, Adrian, Zhang. *Super-resolution particle imaging velocimetry*. Meas. Sci. Technol. 1995(기억).
  - Cowen, Monismith. *A hybrid digital particle tracking velocimetry technique*. Exp. Fluids 1997(기억).
  - Zhou et al. 2024, IJHMT 222:125188(과냉 비등 기포 검출·추적).
  - VFNet 2026(미니채널 시공간 네트워크). 같은 약칭의 검출기 VarifocalNet과 다르다.
  - Homan et al. 2024, *Deep Learning Bubble Segmentation on a Shoestring*(IECR). 이전 조사의 검색 결과에서 https://pubs.acs.org/doi/10.1021/acs.iecr.3c04059 가 나왔다. 저화량 영상에서 겹치지 않은 기포를 떼어 무작위로 합성하는 방식이라는 요약만 있다.
  - RODARE 2811.
- 존재 자체를 확인하지 못한 문헌
  - BubSAM(AIChE J 2024, "+30%, 약 90%"라는 요약만 있음).
  - Taylor bubble YOLOv8 + optical flow(Flow Meas. Instrum. 2025), URAFT-PIV(ISPIV 2021), FTGM(Appl. Sci. 2025), Wang et al. Exp. Fluids 2025.
  - Fu 학위논문, 라트비아대 학위논문, HZDR MHT-X 기록.
  - *Optical imaging of MHD bubble flow in Hele-Shaw liquid metal cells*(arXiv 2311.06288).
  - Exp. Fluids 2024의 SAM 활용 논문, ScienceDirect S0955598625000998(기포 분할 모델 비교), JAEA Swin 기포 검출(Uesawa 2024).
  - Superpixel Transformers(2309.16889), FMOX 벤치마크(2512.09633), Organoid Tracker(2509.11063), Segment Anything for Cell Tracking(2509.09943).
  - ReSCU-Nets의 JCB 세부, VideoSAM이 U-Net보다 낫다는 주장, pith.science 요약.
- 존재는 그럴듯하나 세부가 의심되는 문헌: Huisman, Ern, Roig의 좁은 간극 합체 논문(연도 2019가 틀렸을 수 있음).
- 기억에만 근거한 문헌: Zuber & Findlay 1965(drift flux), Schanz 2016(Shake-The-Box), Blom & Bar-Shalom 1988(IMM), Padfield 2011, Davey 2008(track-before-detect), Varoquaux 2018(작은 검증셋의 오차 막대), Ren/Fowlkes/Malik 2006, LazyBrush 2009, Stauffer & Grimson 1999, MaskTrack(Perazzi et al. 2017), TrackFormer의 GPU 요구량.
- 바로잡은 오인용
  - Naive-Student는 시간 일관성을 쓰지 않는다.
  - OGM-GE는 우리처럼 첫 conv에서 채널을 합치는 구조(early fusion)에는 적용되지 않는다.
  - DAM4SAM은 '비슷한 근접 물체'만 뒷받침하고 '작은 물체'는 뒷받침하지 않는다.
  - Matsoukas는 분류 연구다.
  - TransUNet의 'small organ' 결과는 CNN 스킵 수에 관한 것이다.
  - 리가먼트 논문의 합성 데이터는 검출기 학습용이다.
  - Villalobos와 LRA Path-X는 "트랜스포머가 insideness를 배우지 못한다"는 근거가 아니다.
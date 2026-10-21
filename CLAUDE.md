# 마이크로갭 기포 추적 (bubbles)

## 배경 — old/docs/PIV_TASK.md 1~4장 요약

원문은 `old/docs/PIV_TASK.md`(claude.ai 채팅에서 진행한 진단·설계를 넘겨받은 작업 지시서). 아래는 1~4장 요약이다.

### 1. 프로젝트 개요
- 마이크로갭(약 1 mm) 안의 기액 이상류에서 기포를 고속 촬영 영상으로 검출·추적한다.
- 파이프라인: 배경차분 이진화 → U-Net(배경/기포 내부/기포 경계 3클래스) → 경계를 벽으로 삼아 영역 분할 → 기포 인스턴스 마스크
  → `LeadingEdgeLapTracker`(헝가리안법 1:1 대응 + 마스크 겹침 기반 합체·분열 판정)
  → `result_tracking.csv` / `result_area_count.csv` / 오버레이 / `qc_report.json` → `3_tracking_qc.py`(추적 정확도 자동 점검).
- 연구상 중요한 출력: 기포별 속도(슬립비, 드리프트 플럭스 C0 = u_B / j)와 기포 길이. 면적 가중이므로 큰 기포(슬러그)가 결과를 지배한다.

### 2. 진단 (실제 데이터 QC, 느린 유속 조건)
- large: 예측 위치 오차 중앙값 4.6 px, 기준 초과 4.8% → 안정. tiny / small: 기준 초과 74% / 42% → 불안정.
- 촬영 조건 지표(다음 프레임 최근접 거리 ÷ 같은 프레임 최근접 거리) 0.47~0.62.
  기포가 프레임당 이웃 간격의 약 절반을 이동하므로 최근접 선택만으로는 애매하지만, 속도를 알면 추적 가능한 범위다.
- 부트스트랩 게이트 85 px > 이웃 간격 31 px.
- 원인
  1. 작은 기포가 검출에서 자주 깜빡이고, 다시 나타날 때마다 속도 0으로 새 트랙을 시작해 그 자리에 들어온 이웃을 잡는다.
  2. 게이트가 이웃 간격보다 훨씬 넓다. 부트스트랩은 "이동량"으로 게이트를 정하는데 게이트는 "예측 오차"에 적용된다(설계 결함).
  3. 작은 기포는 모양이 다 비슷해서 형상 IoU가 구분에 도움이 안 된다.

### 3. 이미 적용한 개선 (트래커 v2)
지시서의 `tracker.py`(v2)는 이 저장소의 `tracker2.py`에 해당한다.
- `USE_FLOW_PRIOR`: 새 트랙의 초기 vy = 반경 150 px 안에서 추적 중인 트랙(hits ≥ 3)의 vy 중앙값.
- `SPACING_GATE_FRAC = 0.7`: 예측 위치–검출 거리 ≤ 0.7 × (그 검출의 같은 프레임 최근접 이웃 거리)일 때만 대응. 화면 끝에 닿은 검출은 제외.
- `COAST_GATE_GROWTH = 0.5`, `SHAPE_AREA_REF = 300`(작은 기포는 형상 IoU 가중치를 면적에 비례해 축소).
- CSV 속도 열의 EMA 초기값 편향 수정(첫 값을 0이 아닌 첫 실측 이동량으로).
- 정답 ID가 있는 합성 데이터에서 잘못 연결 비율: 중속 tiny 15.4% → 1.3%, small 4.2% → 0.8%(끊김은 같은 수준), 고속 tiny 20.3% → 2.9%, small 10.5% → 1.6%.

### 4. 남은 문제
- 고속 조건 실데이터에서 프레임당 약 73개 트랙이 화면 내부에서 새로 시작한다(과도한 끊김). 큰 기포의 끊김도 늘었다.
- 추정 원인
  - (a) 간격 게이트의 최근접 이웃을 크기와 무관하게 계산 → 슬러그 옆 작은 기포 때문에 슬러그의 게이트가 좁아진다.
  - (b) 주변 중앙값 prior가 크기별 속도 차이를 무시한다(고속에서는 슬러그가 작은 기포보다 훨씬 빠르다).
- 새 기포의 초기 속도 추정 오차(고속 합성, 실제 이동 tiny 25 / small 30 / large 42 px/frame, 중앙값 px/frame):

  | 방법 | tiny | small | large |
  |---|---|---|---|
  | 속도 0 | 24.1 | 30.2 | 42.5 |
  | 주변 트랙 중앙값 (v2, 이상적 경우) | 4.0 | 3.3 | 15.2 |
  | 상호상관, 전체 영상 | 10.6 | 3.2 | 0.3 |
  | 상호상관, 크기별 분리 | 1.6 | 1.0 | 0.3 |

- 전체 영상 상관은 창의 피크가 픽셀이 많은 큰 기포를 따라가므로 크기별로 분리해야 한다.
  → 지시서 5장 작업: U-Net 인스턴스 마스크로 만든 크기별 영상에서 PIV(상호상관) 속도장을 구해 새 트랙의 초기 속도로 쓴다.

## PIV 초기 속도 추정 구현 현황 (지시서 5장)
v2가 아니라 `tracker3.py`에 통합했다. 지시서 5-2의 간격 게이트 항목은 tracker3에 간격 게이트가 없으므로 해당 없음.
x 방향 예측도 tracker3에 이미 있어서 PIV의 dx를 그대로 쓴다.
- `piv_field.py`: 크기 구분별 PIV.
  - `mode="faithful"`은 `reference/piv_prior.py`와 비트 단위로 같다.
  - 기본값 `"improved"`는 다음을 추가한 버전이다: 주 로브 밖에서 2위 피크 찾기, |d| ≤ 창/4 제한, 고립 벡터 검사, 오프셋 창 clamp, 가장자리 창, 유효성 반환.
- tracker3 플래그(전부 끌 수 있음): `USE_PIV_PRIOR`, `PIV_GATE`(부트스트랩 자동), `PIV_GATE_HARD` + `PIV_STATIC_SPEED`, `W_PIV_OUTSIDE`, `PIV_KEEP_STATIC`, `PIV_USE_DX`, `PIV_MODE`, `PIV_RASTER`, `PIV_WINDOWS`, `PRIOR_AREA_RATIO`, `SAVE_PIV_DEBUG`.
- 근거가 있는 결정
  - 래스터는 마스크 **윤곽**을 쓴다. 채운 마스크는 large 클래스의 유효 창이 0%였다(합성·실제 모두).
  - PIV 게이트는 하이브리드다. PIV가 "움직임"을 가리키는 곳은 단단한 게이트, ≈정지를 가리키는 곳은 패널티를 붙인 넓은 게이트.
    정지 기포가 다수인 창에서는 소수의 빠른 기포가 상관에 나타나지 않는다. 그래서 단단한 게이트만 쓰면 끊김만 늘었다.
  - tiny 창을 키우면 합성(균일 흐름)에서는 좋아졌다. 하지만 실제 프레임(공간적으로 변하는 흐름)에서는 나빠져서 기본값은 256/128→128/64를 유지한다.
- 검증 도구
  - `sim_piv.py`: 6-1/6-2 합성 벤치마크.
  - `fake_detector.py`: 정답 마스크로 확률맵을 만들어 `extract_instances`에 넣는다.
  - `tests/test_events.py`: 6-3 회귀 테스트, PIV on/off 판정이 동일한지 확인.
  - `tests/test_qc.py`.
  - `qc_compare.py`: 실데이터 QC 전후 표.
- 실데이터(60프레임 731~790, 사용자 U-Net npz): tracker3는 tracker2 대비 내부 신규 1030→479, 내부 소실 941→413. PIV on/off는 이 (느린) 데이터에서 차이가 없었다(기준 초과 tiny 35.4/35.5%, small 21.6/21.1%). 고속 데이터 검증은 아직.
- `IGNORE_PARTICLE_AREA = 4`: 면적 ≤ 4 px 검출은 입자로 보고 집계·추적·PIV·오버레이·CSV 전부에서 제외(교수님 요청). npz는 원본 저장.
- `AREA_RELAX_RATIO = 4.0` / `AREA_RELAX_POS = 6.0`: 면적 게이트 완화. U-Net이 같은 기포를 안쪽/바깥쪽 윤곽으로 번갈아 잡아
  면적만 크게 바뀌면 "소실 + 같은 자리 신규"가 된다. 그래서 합체·분열 판정(3, 4단계)이 끝난 뒤 남은 "속도 기지 트랙"과 "검출" 중
  다음을 모두 만족하는 쌍만 면적비 4까지 1:1로 잇는다(`update`의 4b 단계, 속도는 hold).
  - 예측 위치 오차 ≤ 6 + 0.25 × 작은 쪽 등가직경.
  - 서로 유일한 후보.
  - 다른 트랙의 예측 마스크나 다른 검출이 겹치지 않음.
  - 화면 끝 기포는 제외.
  - 결과: 합체·분열 판정은 바뀌지 않는다. 실데이터에서 33건을 이었고 내부 소실 413→397, 내부 신규 479→464, SWAP 146→139.
    AREA_JUMP는 늘어난다(이은 쌍이 그대로 플래그됨).
  - 회귀 테스트는 `tests/test_events.py`의 h. 0이면 무효.
- 사용자 환경 사실 (2026-10 확인)
  - 실제 전처리 값: Noise Cut 15 / Brightness 4 / Median 0 (슬라이더). 예전 분석은 30/3/0을 가정했으니 주의.
  - 라벨: Roboflow COCO 폴리곤을 기포의 흰 테두리 **바깥쪽**에 그림. `1_unet_train.py`(사용자 PC)가 3클래스 마스크로 변환한다.
    경계 = 폴리곤 선 위 두께 EDGE_PX=4(작은 기포 1~3) 띠. 손실 CE(경계 가중치 6) + Dice.
    Copy-Paste 증강은 500 px 미만만, 밝기 증강은 꺼져 있음.
  - 사용자는 아주 작은 점을 꼼꼼히 라벨링하지 못했다고 함.
  - **클라우드에서 U-Net 학습 금지**(토큰 비용). 학습은 사용자가 PC에서 한다.
- 검출 실패 분석 (60프레임, scratchpad/faint2, 결론만)
  - tiny/small 실패의 주원인은 희미한·끊긴 윤곽이 아니다(6% 이하).
    입력에 또렷이 보이는 점을 U-Net이 놓치는 것(59%, 같은 입력에서 1프레임만 깜빡임 포함), 슬러그 접촉(15%), 붙은 쌍 융합이 주원인이다.
  - `extract_instances`의 링 기포 윤곽 전환
    - 구멍 ≤ 29 px이면 tiny 경로(바깥 윤곽 전체), ≥ 40 px이면 주 경로(내부 + 벽 안쪽 절반). 면적이 ×1.5~1.9로 점프한다(AREA_JUMP의 원인).
    - 검출 윤곽은 흰 테두리 바깥 가장자리(G>15)보다 large 약 1.3 px, small 약 0.5 px 안쪽에 있다.
    - 확률맵으로 확인한 뒤 수정할 것. 패치 후보: scratchpad/faint2/C.
  - 사용자가 보고한 문제: 윤곽이 희미한 **대형 기포가 통째로 미검출**되어 추적이 끊긴다. 731~790에는 해당 사례가 없다.
- `SAVE_PROB_MAPS = False`: True면 OUTPUT_FOLDER/prob/*.npz에 p_in, p_edge(uint8), u_input 저장(실패 원인 분석용).
- `UNET_INSTANCE_MODE = "wall"`(기본, 종래) / `"seed"`: `extract_instances_seed`.
  - 방식: 내부 확률의 심(내부 > `UNET_SEED_THR` 그리고 경계 ≤ EDGE_THR)과 배경을 씨앗으로 쓰고, 경계 확률로 watershed를 한다.
  - 윤곽이 끊겨도 기포가 배경으로 새지 않는다. 심에 wall의 closing과 같은 횟수의 opening을 걸어 작은 기포의 면적 규약을 맞췄다.
  - 회귀 테스트: `tests/test_instances.py`.
  - 합성 결과(scratchpad/verify/eval_seed.log)
    - 열화 없음: wall과 완전히 같다.
    - 열화 있음: 정답률 small 78→98%, large 90→97.5%, tiny 82→94%.
    - 대가: 붙은 쌍 융합 28→39%, 오검출 0.03→0.07/프레임.
    - 합성에서는 끊긴 곳에서도 내부 확률이 높게 유지되므로 낙관적이다.
  - 실제 효과는 사용자 PC에서 확인이 필요하다.
- `UNET_INSTANCE_MODE = "hybrid"` (권장, watershed.py 기본값): `extract_instances_hybrid`.
  - 방식
    - wall 결과는 그대로 쓴다.
    - 벽 틈으로 배경에 새어 사라진 기포만 되살린다. 어떤 기포에도 속하지 않은 심(≥ `UNET_RESCUE_CORE_MIN` = 100 px)을 대상으로,
      `RESCUE_SCHEDULE`((0.5,5)…(0.1,7))로 벽을 점점 강하게 다시 닫는다.
    - 심 비율 ≥ `UNET_RESCUE_CORE_FRAC` = 0.5이고 wall의 띠 판정을 통과하는 첫 단계의 영역을 기포로 삼는다.
      경계 화소는 wall과 같은 능선 분배로 나눈다.
    - 순서는 주 경로 → 구제 → 작은 기포 경로.
  - 실데이터(best.pt, 60프레임, scratchpad/real)
    - 구제는 742, 752, 753, 762에서 각 1개뿐이다. 모두 눈으로 보고 옳다고 판정했다.
    - 나머지 56프레임은 wall과 완전히 같다. 리팩터 전 wall과도 60/60 일치한다.
    - QC 차이는 작다: 대형 내부 신규 0.52→0.50/프레임, 기준 초과 3.4→2.5%, large SWAP 1→2.
    - 원래 설계자의 추적 분석: 구제 4건 중 2건은 트랙이 이어지고, 2건은 트래커 약점 때문에 오연결·애매해졌다.
  - `"seed"`는 실데이터에서 결함이 확인됐다. 대형 기포 안쪽 깊은 곳은 p_in < 0.5라서 wall이 맞힌 대형 15건을 들쭉날쭉하게 자른다.
    사용자가 PC에서 본 "이상한 판정"이 이것이다. 비교용으로만 남긴다.
  - 이번 카탈로그(scratchpad/hybrid/A) 결과: wall이 대형 기포를 통째로 잃는 경우는 60프레임 중 4건뿐이고, 원인은 전부 벽 틈이다(띠 판정 실패는 0).
    → 대형 트랙 끊김의 주원인은 검출이 아니라 추적(슬러그와의 합체·분열 등) 쪽일 가능성이 높다. 다음 분석 후보.
  - wall의 작은 기포 경로는 고리가 열린(C자) 작은 기포를 덜 채운다(92건).
    seed가 흰 윤곽에 더 가까웠다(84/85). 작은 기포 면적 규약은 별도 개선 후보.
  - 회귀 테스트: `tests/test_instances.py`의 c, d(U-Net에 가까운 3px 벽 + 약한 틈).
- `watershed.py` = tracker3.py의 기본값만 다른 사본. 사용자 요청으로 따로 저장했다. (2026-10-21 정리 후 둘 다 old/에 보관. 지금은 binarized/2_bin_track.py를 직접 고친다.)
  - 다른 기본값: hybrid, SAVE_PROB_MAPS=True, COMPARE_INSTANCE_MODES=True, OUTPUT_FOLDER=...\output_watershed.
  - 실행 시 `실행 중인 파일: ...`과 설정값을 로그에 출력한다.
  - 사용자가 PC에서 직접 만든 이전 watershed.py는 코드가 빠져 있어 동작하지 않았다.
  - `COMPARE_INSTANCE_MODES`: 매 프레임 다른 방식(쓰는 방식이 wall이 아니면 wall, wall이면 hybrid)과 비교한다.
    차이 수를 로그와 mode_diff/*.png에 출력한다. hybrid는 구제 수도 출력한다.
  - SAVE_PROB_MAPS는 npz와 함께 확인용 png(입력 | 내부 | 경계)도 저장한다.
  - 슬라이더 오류(OpenCV 4.11은 createTrackbar 때 콜백 호출 → getTrackbarPos 오류)는 ready 플래그로 수정했다.
- 사용자의 best.pt(2026-10-06, resnet34, epoch 65, train 480 / val 46, val IoU 배경 0.982 / 내부 0.944 / 경계 0.578)
  - 이 세션 scratchpad/ckpt/best.pt에 있다. 세션이 끝나면 없어진다.
  - 추론만 허용(학습 금지). CPU에서 60프레임 33초.
- `shrink_ckpt.py`: best.pt 분할(`--split MB`, 내용 그대로) / float16 변환(`--fp16`, 절반 크기, 확률이 최대 0.1 정도 달라짐).
  업로드 크기 제한 대책.
- 실데이터 검증(6-4)은 U-Net 가중치(`best.pt`, 사용자 PC에 있음)가 필요하다. 클라우드 세션에서는 업로드받아야 실행할 수 있다(torch는 설치 가능).

## Tracking-aware U-Net (TAU) — 2026-10 시작
후처리(wall/hybrid)로는 한계라는 판단에서 사용자가 "완전히 새롭게" 개발하자고 했다. 코드는 클라우드에서 쓰고 배관만 확인했다. **학습은 사용자가 PC에서 한다.**
- 구성
  - `tau_unet.py`: 공통 부품. 5채널 입력 = 그레이 ×3(best.pt와 같은 정규화) + 사전 마스크 2장(내부 채움, 기포별 안쪽 윤곽 `PRIOR_EDGE_PX`=2).
    출력은 3클래스 그대로라서 hybrid와 tracker3을 그대로 쓴다.
    - `expand_state_dict`: 3ch 가중치의 첫 conv에 사전 마스크용 가중치를 0으로 추가 → 학습 전에는 best.pt와 같은 확률.
    - `synth_prior`(`PriorAug`): 정답 라벨을 망가뜨려 학습용 사전 마스크를 만든다(MaskTrack 방식, 연속 프레임 라벨 불필요).
      비움 0.15, 기포별 삭제 0.2, 위치 σ=1+0.05·등가직경(10%는 ×4), 크기 ×0.85~1.15, 팽창/수축 ±2, 일부 잘림 0.1,
      접한 쌍 융합 0.3, 큰 기포 쪼개기 0.05, 빈 곳의 가짜 기포 평균 2개/장.
    - `TauDetector.prob(gray, prior)`: UNetDetector와 같은 전후처리(32 패딩, train_hw 리사이즈). 3ch ckpt면 사전 마스크를 무시한다.
  - `1_tau_unet_train.py`: 사용자의 `1_unet_train.py`(한국어 주석, 저장소에는 없음)를 바탕으로 했다.
    - 데이터셋에 기포별 라벨맵 `instances/*.png`(uint16)를 추가.
    - FINETUNE_FROM=best.pt에서 3→5ch로 시작, 80 epoch, lr 1e-4.
    - val은 사전 없음 / 사전 있음(이미지별 고정 시드) 둘 다 평가하고 평균 점수(0.4·내부 IoU + 0.6·경계 IoU)로 best를 고른다.
      "写し"(사전 마스크에 있지만 정답은 배경인 화소를 기포로 낸 비율)도 출력한다.
    - CROP은 기존과 같은 (1088,416)(= 전체 이미지). "사전 마스크만 다르다"는 비교를 유지하려는 것.
    - test는 시작 모델 / 새 모델 사전 없음 / 새 모델 사전 있음 3열.
  - `tau_tracker.py`: tracker3을 import해서 오프라인 다중 패스로 돈다.
    - 패스0은 사전 없음 → 부트스트랩 → 추적.
    - 패스k에서 프레임 t의 사전 = 패스k-1 트랙의 예측. t±1 둘 다 있으면 t-1 마스크를 변위의 절반만큼 옮기고(내삽),
      한쪽만 있으면 t∓2와의 변위로 외삽한다(합체·분열·hold_v 직후는 0).
    - **t 자신의 검출은 쓰지 않는다.** t를 뺀 관측 수 < `PRIOR_MIN_HITS`(2)인 트랙도 쓰지 않는다(1프레임 오검출 확산 방지).
    - `PRIOR_PASSES`=2. 검출이 이전 패스와 같으면 조기 종료. 연속 누락은 패스마다 양 끝에서 1프레임씩 복구된다.
    - 패스별 CSV/qc_report → `passes/pass<k>/`, 3_tracking_qc 항목 비교표 → `pass_summary.json`.
      검출이 바뀐 프레임은 `prior_debug/*.png`로 남긴다. 마지막 패스는 tracker3과 같은 형식으로 출력한다.
    - `PRIOR_FROM="forward"`는 온라인과 같은 정보만 쓰는 비교용.
  - tracker3.py / watershed.py: `main()`의 used_params 딕셔너리를 `used_params(roi_rect, preprocess_params)` 함수로 분리했다(출력 동일).
- 검증 (배관만, 실제 학습 없음)
  - `tests/test_tau.py`
    - a: 3→5ch 변환 시 사전 마스크와 무관하게 확률 차 < 1e-5.
    - b: 3ch ckpt면 TauDetector = tracker3.UNetDetector(완전 일치, 리사이즈 경로 포함).
    - c: render_prior. d: synth_prior.
    - e: 가짜 검출기로 4프레임 누락 대형 기포가 패스 2개로 복구되어 트랙 1개가 된다.
      사전 마스크를 그대로 베끼는 최악의 검출기에서도 1프레임 오검출은 MIN_HITS=2면 퍼지지 않고, 1이면 퍼진다.
    - f: 가짜 COCO 96×128로 학습 스크립트 1 epoch(2 step)가 끝까지 돈다.
  - 실데이터 60프레임(731~790)에 best.pt(3ch)로 tau_tracker.main 실행 → 패스1에서 "같음"으로 끝난다.
    result_tracking.csv / result_area_count.csv가 watershed.py(hybrid) 출력과 바이트 단위로 같다.
  - 실데이터에서 만든 사전 마스크의 품질(패스0 = best.pt hybrid, scratchpad/tau/prior_stats.py)

    | | tiny | small | large |
    |---|---|---|---|
    | 검출 중 사전이 50% 이상 덮는 비율 | 42% | 73% | 87.5% |
    | 사전 없음(<10%) | 37% | 14% | 5% |
    | 사전 IoU 중앙값 | 0.35 | 0.55 | 0.73 |
    | 중심 오차/등가직경 중앙값 | 0.26 | 0.17 | 0.06 |

    synth의 위치 σ를 이 값에 맞춰 2→1 px, 큰 이동 5→10%로 조정했다(조정 후 IoU 중앙값 0.37 / 0.53 / 0.77).
- **1차 학습 결과 (2026-10-19, 사용자 PC)**: train 160장(best.pt 때는 480장), 80 epoch. 사전 마스크를 전혀 쓰지 않게 학습됐다.
  - 모든 epoch에서 사전 효과(경계 IoU, 있음−없음)가 ≤ +0.0002였다.
  - best = epoch 3. 사전 가중치 평균 0.0007(영상 가중치 0.073).
  - val 경계 IoU는 0.5754→0.5681로 계속 떨어졌다(과적합).
  - 사용자의 새 영상에서도 패스별 차이가 거의 없었다.
  - 원인: 학습 화상은 윤곽이 또렷해서 영상만으로 정답이 나온다. 흐트러뜨린 사전 마스크는 영상보다 부정확하므로 무시하는 쪽이 최적이 된다.
- 대책 (구현됨)
  - `BEST_BY='prior'`: 망가뜨린 화상 + 사전 있음 점수로 best를 고른다.
    단, 원래 화상 + 사전 없음 점수가 시작보다 `BEST_EMPTY_TOL`=0.01 넘게 떨어진 epoch는 제외한다.
  - epoch마다 사전 효과와 사전 가중치 크기를 표시한다.
  - **화상 망가뜨리기 `DEGRADE_*`**(`tau_unet.degrade_image` / `ImageDegrade`)
    - 대상: 면적 ≥ 300인 기포 1~4개, 확률 0.5.
    - 방식: 윤곽 띠의 일부(둘레의 10~35%, 1~2곳)를 지우거나, 30% 확률로 화소를 25~60%만 남겨 끊긴 윤곽을 만든다.
    - 정답 라벨은 그대로 둔다. 그 기포는 사전 마스크에서 지우지 않는다(`synth_prior(keep_ids=)`, 사전 없음 처리도 하지 않음).
    - val은 3가지로 평가한다: 원래 화상·사전 없음 / 망가뜨린 화상·사전 없음 / 망가뜨린 화상·사전 있음.
  - 재학습할 때 학습 데이터는 best.pt와 같은 480장을 권장한다.
- **2차 학습 결과 (2026-10-20, 480장, 화상 망가뜨리기 포함, best = epoch 14)**: 이번에도 사전 마스크를 거의 쓰지 않았다.
  - 사전 효과는 경계 IoU +0.0004, 사전 가중치 0.0021(영상 가중치 0.073).
  - 망가뜨린 화상에서도 사전 없이 경계 IoU가 0.573→0.569로 거의 떨어지지 않았다. U-Net이 윤곽의 틈을 스스로 메우므로 사전이 필요한 상황이 생기지 않는다.
  - 637~641의 L자 기포는 이전 best.pt와 결과가 거의 같다(아래 "큰 복잡한 기포" 참고).
  - 교훈: 재학습 전에 "기존 best.pt로 망가뜨린 val을 평가해서 성능이 실제로 떨어지는지"부터 확인했어야 했다. 학습 없이 확인할 수 있었다.
- **결정 (2026-10-20, 사용자와 합의): TAU는 보류한다.** 이진화 입력에서는 효과가 없다. 검출·학습은 3ch(USE_PRIOR=False)로 한다.
  - 다른 작업에서 다시 쓰는 부품: 채널 확장(expand_state_dict, 가중치 0 초기화) → 비이진화 입력에 차분 채널을 더할 때 쓴다.
  - 학습 스크립트의 ignore / 3ch 모드 / 평가 표도 계속 쓴다.
- 남은 일 (보류)
  - 사용자가 PC에서 학습한 TAU best.pt를 받아 731~790과 637~641(1200×480, L자 기포)에서 패스별 비교.
    지표: 대형 내부 신규/소실, large 合体直後の分裂(flip-flop), 637~641 검출.
  - 637~641은 앞뒤 프레임도 누락이면 사전이 없어서 도움이 안 된다(그 전후 프레임 확인 필요).

## 검출 병목 분석 (2026-10, 60프레임 731~790, scratchpad/dataq, 학습 없음)
- 이진화(Noise Cut 15)가 버리는 정보
  - 배경 노이즈: raw diff p99 = 7, σ≈3이라서 15는 약 5σ.
  - 윤곽(링)은 잃지 않는다. 검출된 기포 둘레의 99~100%에서 링이 ≥15로 보인다.
  - 대형 기포 **내부**는 액체보다 약 5 계조 어둡다(85%의 대형).
    raw diff 5×5 평균으로 내부와 액체를 구분하면 AUC 0.91, 이진화 입력으로는 0.53. 이 단서를 이진화가 지운다.
    → L자 띠(637~641), 누출 실패와 관련된다. raw diff를 **채널로 추가**(가중치 0 초기화)하는 것이 후보.
    기존 3채널을 바꿔 쓰면 ImageNet 정규화 때문에 출력이 바뀌므로 안 된다(확인함).
  - 프레임의 먼 액체 화소 43%가 ≥250으로 포화돼 있다. 대형 내부 오판 화소의 54%가 포화 영역이라 차분 정보가 없다 → 촬영 노출 문제.
  - 사용자가 보낸 1200×480 조건의 원본 프레임(images/15.jpg): 화소의 92%가 255다.
    배경과 대형 기포 내부가 모두 포화돼 있고(대형 5개 모두 내부·외부 중앙값 255), 정보는 윤곽(중앙값 176)에만 있다.
    → 이 조건에서는 원본 입력도 내부 단서가 없다. 노출을 낮춰 배경이 약 200~220이 되게 찍어야 내부 단서를 쓸 수 있다.
  - 누출 4건의 원인
    - 742: 링이 또렷한데 네트워크가 실패.
    - 752, 753: 임계값 근처의 희미한 링.
    - 762: 화면 끝이라 정보 없음.
- 눈에 또렷한 5~20 px 점(밝기 중앙값 43) 17.3개/프레임에 네트워크 출력이 거의 0이다 → 작은 점 라벨 누락 가설과 일치(가설).
- **후처리 버그 → `UNET_RING_RESCUE = True`로 수정** (wall/hybrid 공통, `_ring_path` + `_tiny_path` 분할, False면 종래 동작)
  - 증상: 또렷한 링 기포를 wall과 hybrid 모두 버렸다(U-Net 확률 ≈1).
    - 원인 ①: 붙은 쌍의 채움 면적이 TINY_MAX 300을 넘는다.
    - 원인 ②: 다른 기포와 2 px 이내라서 작은 기포 경로가 건너뛴다.
    - 공통 배경: 주 경로 closing으로 링의 작은 구멍이 메워진다.
  - 방식
    - 아직 기포가 아닌 경계 덩어리가 감싸는 구멍 중 "링의 구멍"을 씨앗으로 삼는다.
      링의 구멍 = 화소 절반 이상이 심(p_in > 0.5 & p_edge ≤ 0.5)이고, 기존 기포도 closing 뒤 남은 영역(띠 판정 결과)도 포함하지 않는 구멍.
    - `RING_MERGE_GAP` = 2 px 이하의 선으로 나뉜 구멍은 하나로 합친다.
    - 경계 화소는 가장 가까운 구멍에 준다. 단, 구멍에서 `UNET_RING_REACH` = 8 px보다 멀거나 기존 기포가 더 가까우면 제외한다.
    - 면적 규약은 작은 기포 경로와 같은 윤곽 바깥쪽까지다.
    - 줍지 않는 것
      - 약한 씨앗(심 ≤ `RING_WEAK_CORE` = 4 px)인데 면적 > 45.
      - 화면 끝 2 px에 걸친 것.
      - 면적 > `UNET_RING_MAX` = 600.
    - 작은 기포 경로에서 강한 구멍(심 > 4 px)이 2개 이상인 덩어리(붙은 쌍)는 구멍마다 나눈다. 이때만 기존 기포가 바뀐다.
  - 실데이터 60프레임 결과
    - 227개를 추가하고 14쌍을 분할했다.
    - 1차판 243개는 독립 육안 검증에서 정답 88.5%, 모양 불량 7.4%, 오검출 2.5%였다.
      규칙 추가 후 오검출 6건은 모두 사라졌고, 정답 211개는 그대로 남았다.
      남은 모양 불량 13건은 U-Net이 붙은 점 2~3개를 구멍 하나로 낸 경우와 슬러그 밑의 물방울(줄기 포함)이다.
    - 분할 14쌍은 눈으로 보고 모두 옳다고 판정했다.
    - 기존 기포는 분할 외에 바뀌지 않는다.
  - QC(watershed=hybrid, best.pt)
    - small 관측 1885→2070.
    - small 내부 신규/관측 10.9→10.5%, 내부 소실 9.4→8.8%, SWAP 4.0→4.6%.
    - large는 거의 같다.
    - 처리 시간 +0.09 s/프레임.
  - 회귀 테스트: `tests/test_instances.py` e~m.
  - fake_detector / sim_*는 `extract_instances`를 ring 없이(기본 ring_max=0) 부르므로 합성 벤치마크 수치는 종래 그대로다.
  - `1_tau_unet_train.py`의 test 평가용 wall 사본에도 ring이 없다.
- **기포 안의 기포 → `UNET_DROP_NESTED = True`** (`drop_nested`, unet_instances 마지막 단계, wall/hybrid/seed 공통)
  - 사용자 방침: 큰 기포 안에 보이는 링(액적 등)도 모양이 같으니 라벨·U-Net 모두 bubble로 다루고, 후처리에서 뺀다.
    라벨은 폴리곤 안의 폴리곤 그대로 두면 된다(변환 스크립트 변경 없음).
  - 판정: 바깥 2 px 고리 화소의 `UNET_NESTED_SURROUND` = 0.9 이상이 자기보다 큰 기포 1개면 "기체 안" → 제거한다.
    바깥 기포는 그대로 두고 구멍도 남긴다(기체 면적에서 빠짐). 화면 끝 기포는 대상이 아니다.
  - 액체 섬(슬러그로 둘러싸인 액체 영역, 이진화로는 기체와 구별 불가 / 차분 영상에서는 액체와 같은 회색)
    안의 진짜 기포는 둘레가 배경이므로 남는다.
    - 731~790에서 "큰 기포 안"으로 잡힌 6건은 모두 이 경우였다(781~787, 물방울 모양 액체 섬).
    - 실데이터에서 둘레 비율 최대 0.76(액체 섬 기포), 접촉만 하는 기포 ≤ 0.5 → 제거 0건, 출력 변화 없음.
  - 구멍이 작은 기체 안 링(구멍 ≲ 3 px)은 주 경로 closing에 이미 흡수되어 별도 기포로 나오지 않는다.
  - 회귀 테스트: `tests/test_instances.py` n.
- 조사 결론 (workflow 조사 + 검증)
  - CNN을 고른 진짜 이유는 데이터 양이 아니다. 다음이 이유다.
    - 정적 라벨로 학습할 수 있다.
    - best.pt에서 그대로 이어서 시작한다.
    - 전체 해상도로 1~4 px 경계와 2~8 px 기포를 다룬다.
    - 같은 모양 기포가 프레임당 약 80개이고 계속 바뀐다.
    - GPU 1대.
  - 사전학습 트랜스포머(SAM 2 미세조정)는 큰 기포에서는 적은 데이터로도 된다는 보고가 있다(Küçük et al., arXiv 2508.05227, 수치는 미검증).
  - 대안 평가
    - StarDist, Mask R-CNN, YOLO-seg, SAM 2를 주 검출기로 쓰는 것은 비추천.
    - Omnipose류 거리/흐름 표현(또는 U-Net에 거리 헤드 추가)은 누출에 강하다. 후순위 후보.
    - 트래킹 AI는 Trackastra(ECCV 2024)형 연관 학습이 맞다.
  - 데이터
    - 분할 누설 점검(연속 프레임 무작위 분할).
    - 라벨 감사 + ignore 마스크(CE·Dice 모두 ignore_index 지원).
    - 동결 테스트 세트 30~40프레임.
    - 작은 점 후보 자동 생성 → Roboflow에서 수락/삭제.
    - QC 플래그 기반 어려운 프레임 50~100장.
    - 인접 원본 프레임으로 실제 사전 마스크 만들기.
    - 추적 GT: 연속 약 100프레임 × 2. CTC 형식은 부모가 하나뿐이라 합체를 표현하지 못하므로 따로 평가한다.

## 대형 기포 트랙 끊김 (2026-10, 사용자 새 영상 144프레임 CSV, 480×1200)
- 사용자 CSV(6cddd5bd, TAU 패스 결과)에서 대형(≥ 2000 px) 트랙이 화면 내부에서 끝나는 12건을 분류했다.
  - 7건: 화면 끝으로 들어오거나 나가는 기포.
    - 위로 들어옴: 509→511, 1109→1110, 1557→1564. 아래로 나감: 216→1368, 438→1470. 왼쪽으로 나감: 709→833, 764→944.
    - 원인: 검출이 화면 끝 **1~2 px 앞에서 멈춘다**. 면적 ≥ 300이고 위끝 y = 1~2인 검출 약 30행이 フレーム接触 = 0이었다.
      그래서 "잘린 기포"로 판정되지 않았다. 잘린 기포 처리가 꺼진 상태라 다음이 적용됐다.
      - 면적 게이트가 3.6이 아니라 1.8이었고, 작은 쪽이 잘렸을 때 면적 게이트를 끄는 처리도 적용되지 않았다.
      - 위치를 반대쪽 끝이 아니라 중심으로 비교했다.
      - 결과: 들어오는 동안 면적이 ×2가 되면 매번 새 ID가 붙었다.
  - 1건: 새 트랙(속도 미지) 6이 f0에서 35099 px였는데 2프레임 동안 검출되지 않았다. f3에 159(34394 px)로 돌아왔지만 MAX_AGE_NEW = 1이라 끊겼다.
  - 1건(1202): 진짜 검출 실패. 사용자 이미지의 흰 윤곽만 보이는 대형 기포가 이 경우다. 2프레임만 검출됐다. 트래커로는 고칠 수 없다.
  - 나머지: 화면을 나가는 잔해(1368→1376 등)와 245→289(소형에 가까움).
  - 1110(26k px)처럼 속도 기지 트랙이 1프레임 빠지는 것은 MAX_AGE로 이미 이어진다.
- 수정 (tracker3/watershed 공통, 전부 플래그)
  - `EDGE_TOUCH_PX = 3`: 외접 사각형이 화면 끝에서 3 px 이내면 touch로 본다. 0이면 종래 동작(정확히 0/H/W일 때만).
    CSV의 フレーム接触 열에도 반영되므로 3_tracking_qc의 내부 신규/소실 집계에서 화면 끝 기포가 더 정확히 빠진다.
  - `MAX_AGE_NEW_LARGE = 3`, `LARGE_NEW_AREA = 2000`: 속도 미지 트랙이라도 면적이 2000 이상이고 화면 끝에 닿지 않았으면 3프레임까지 기다린다.
    화면 끝 조각은 다른 기포를 뺏을 위험이 있어 대상에서 뺐다. MAX_AGE_NEW 이하로 두면 무효. 판정 함수는 `_max_age(t)`.
  - 회귀 테스트: `tests/test_events.py`의 i(2 px 앞에서 멈추는 입장), j(대형 새 트랙 2프레임 소실, 소형은 종래대로 끊김).
  - 합성 벤치마크(sim_*)의 수치는 다시 돌리지 않았다. 화면 끝 3 px 이내 기포가 touch가 되므로 약간 달라질 수 있다.
  - 사용자 데이터로 효과를 확인하는 실행은 아직 하지 않았다(사용자 요청 전에는 검증 실행 금지).

## 작은 점 라벨 보충 (2026-10, 진행 순서 1번)
- 근거
  - 작은 기포 검출 실패의 주원인은 라벨 누락으로 본다. U-Net은 또렷한 점에 대해 약한 출력이 아니라 거의 0(확실한 배경)을 낸다.
  - 문헌 조사 결론
    - 체계적인 라벨 누락은 어떤 모델로 바꿔도 그대로 학습된다.
    - 자기 예측으로 다시 학습(self-training)하는 방법이나 손실 가중치 조정은 통하지 않는다(모델 출력이 ≈0이라 건질 신호가 없다).
    - 가장 효율적인 방법: U-Net과 독립적인 방식으로 후보를 만들고 사람은 y/n만 확인한다(후보당 약 2초). 확인하지 않은 후보는 ignore로 둔다.
- `dot_labels.py` (사용자 PC에서 실행. 설정은 파일 맨 위)
  - [1] 후보
    - Roboflow 학습 화상에서 `CAND_LOW`=30 이상인 화소의 8-연결 덩어리를 찾는다.
    - 조건: 광화소 ≥ `CAND_MIN_AREA`=5, 최대 밝기 ≥ `CAND_PEAK`=60, 채운 면적 ≤ `CAND_MAX_AREA`=600, 라벨된 기포에서 `LABEL_GAP`=2 px 안쪽에 걸치지 않음.
    - 채우기 `fill_dot`: radius-2 팽창 → fill holes → 수축 → 볼록 껍질 안쪽으로 제한한다.
      - closing 뒤에 채우면 1 px 굵기 링은 1~2 px 틈도 안 채워졌다(점검에서 발견).
      - 화상 끝에 닿은 쪽은 화상 끝을 링의 일부로 보고 채운다.
    - 붙은 링 분리 `split_pairs`: 진짜 구멍(≥ `PAIR_MIN_HOLE`=3 px)이 2개 이상인 덩어리는 가장 가까운 구멍 기준으로 링마다 나눠 후보로 만든다(타일에 "pair" 표시).
      하나로 받아들이면 "붙은 쌍 = 1개"를 학습시키기 때문이다. 실프레임 60장에서는 0건이었다.
    - U-Net은 쓰지 않는다.
  - [2] 확인 GUI (OpenCV, 문자열은 ASCII)
    - 5×4 타일. 좌클릭 = n, 우클릭 = u, 다시 클릭하면 취소, Enter/Space = 페이지의 나머지를 y로 하고 다음 페이지, b = 이전 페이지, q = 저장 후 종료.
    - TILE=140이라 창은 708×618 px다. 화면 밖으로 나간 타일까지 Enter로 y가 되는 것을 막으려고 줄였다.
    - 페이지가 바뀐 뒤 0.4초 동안은 Enter를 무시한다(누르고 있거나 두 번 누른 경우).
    - 순서: split(test → valid → train) 안에서 밝은 후보부터.
    - 판정은 `OUT/decisions.json`에 저장한다. 키는 후보 ID `split/file@x0,y0,wxh,광화소수`라서 다시 찾거나 채우는 방식을 바꿔도 같은 덩어리면 같은 ID가 된다.
    - 상태와 그리기는 `Review` 클래스에 있어 GUI 없이 테스트할 수 있다.
  - [3] 내보내기
    - `OUT/coco/<split>/`: 원래 라벨 + y. 화소 중심을 지나는 외곽 폴리곤, category는 기존 다수값, `"source": "dot_labels"`.
    - `OUT/ignore/<split>/<stem>.png`: u와 미확인 후보를 `IGNORE_PAD`=2 px만큼 넓힌 영역(255).
    - n은 아무것도 하지 않는다(배경으로 학습).
    - ignore 폴더는 비어 있어도 만든다.
    - 화상 파일이 없는 항목은 건너뛴다.
    - SRC와 OUT이 서로 포함하는 관계면 실행을 멈춘다. 예: `SRC=OUT\coco`로 두면 원본이 지워진다(점검에서 발견).
  - 폴리곤은 학습 변환(make_target)을 거치면 원래 마스크로 돌아온다.
    - bbox가 12 px 미만이면 정확히 같다.
    - 그보다 크면 경계선 두께 3~4 px의 바깥 절반만큼 넓어진다. 사용자 라벨과 같은 규약이다.
  - 실제 프레임 60장(731~790, hybrid 검출을 "라벨"로 대신 사용): 후보 프레임당 19개. 최대 밝기 ≥160이 66%, 100~160이 31%.
- `1_tau_unet_train.py`
  - `IGNORE_SRC`
    - 데이터셋 변환에서 ignore 화소 중 라벨이 배경인 곳만 255(`IGNORE_LABEL`)로 만든다(`apply_ignore`).
    - CE와 Dice에 ignore_index를 준다. ignore 화소가 없으면 값은 종래와 같다(테스트로 확인).
    - evaluate는 255를 세지 않는다.
    - test의 크기별 매칭은 ignore에 절반 이상 걸친 예측 기포를 세지 않는다.
    - copy-paste 재료는 m ∈ {1,2}로 만든다. 붙일 자리 판정은 ignore도 점유로 본다.
  - `USE_PRIOR = False`: 3채널 U-Net으로 학습한다.
    - 사전 마스크, 화상 망가뜨리기, BEST_BY를 쓰지 않는다. best는 val 점수로 고르고, test는 열 2개다.
    - 출력은 `in_channels`=3, `tau`=False라서 tracker3/watershed의 UNET_CKPT에 그대로 쓸 수 있다.
    - 라벨 보충의 효과만 비교할 때 이것을 권장한다.
  - 3ch 출력도 meta에 `prior_edge_px`를 숫자로 기록한다. TauDetector는 None도 허용한다. 예전에는 tau_tracker에서 int(None)로 실패했다.
  - test의 `n_pred`도 ignore에 걸친 예측을 뺀다. 손실은 `make_losses(dev)`로 만든다.
  - 기본값(USE_PRIOR=True, IGNORE_SRC=None)의 동작은 변하지 않는다.
- 회귀 테스트: `tests/test_dots.py` a~g + a2.
  - a 후보와 LABEL_GAP, a2 끊긴 링·끝에서 잘린 링·붙은 링, b 폴리곤 왕복, c 내보내기→데이터셋(IGNORE_PAD, valid→val, 빈 ignore, 없는 화상, SRC 보호)
  - d 학습 손실·평가·test 매칭·paste 재료의 ignore, e 3ch+ignore 학습 스모크 + UNetDetector·TauDetector 읽기 + 평가로 ignore가 전달되는지, f 확인 GUI 상태, g ID와 저장
  - 독립 점검(리뷰 4방향 + 회의적 검증) 결과는 위의 수정에 반영했다.
  - 변이 20종 중 19종을 잡는다. 남은 1종(prior_edge None)은 TauDetector를 고쳐서 생긴 이중 방어다.
- 사용자 작업 순서
  1. `python dot_labels.py`: test를 전부 확인하고, 이어서 train도 가능한 만큼 확인한다(목표 100~150장).
  2. `1_tau_unet_train.py`를 `SRC=dot_labels\coco`, `IGNORE_SRC=dot_labels\ignore`, `USE_PRIOR=False`로 학습한다.
  3. test 표에서 tiny 재현율을 시작 모델과 비교한다.

## 이진화 버전 2파일 (binarized/, 2026-10)
- 사용자 요청: 이진화 입력용 코드는 나중에 이진화하지 않는 입력과 따로 쓰게 되므로 "학습 1개 + 검출·추적 1개"로 정리한다.
- `binarized/1_bin_train.py` (원본: tau_unet + dot_labels + 1_tau_unet_train)
  - `STEP = 'dots'`: 작은 점 라벨 보충. 결과는 `DOT_OUT`에 저장한다.
  - `STEP = 'train'`: 학습. `USE_DOT_LABELS=True`면 DOT_OUT/coco와 DOT_OUT/ignore를 자동으로 쓴다.
  - 원본과 기본값이 다른 것: STEP='dots', USE_PRIOR=False, DST=dataset_bin, OUT=runs/bin. dot의 OUT과 REVIEW는 DOT_OUT과 DOT_REVIEW로 바꿨다.
- `binarized/2_bin_track.py` (원본: watershed + piv_field + tau_unet + tau_tracker)
  - 기본값은 watershed와 같다(hybrid 등). 출력 폴더만 output_bin이다.
  - `main()`은 UNET_CKPT가 5ch이고 PRIOR_PASSES > 0이면 `main_tau`(원본 tau_tracker), 아니면 `main_single`(원본 watershed)을 실행한다.
- `tools/build_binarized.py`가 원본 모듈에서 기계적으로 만든다.
  - 하는 일: 설정을 맨 앞에 모으고, import를 합치고, `T3.` / `tau_unet.` / `piv_field.` 참조를 같은 파일 안의 이름으로 바꾼다.
  - 이름이 겹치는 것은 이름을 바꾼다: main → main_single/main_tau/main_dots/main_train. 쓰이지 않는 tau_tracker의 size_class는 지운다(남기면 PIV의 size_class를 덮어써 오류가 났다).
  - 치환 횟수를 고정해 두었다. 원본이 바뀌면 생성이 멈춘다.
  - 이름을 바꾼 결과 함수 안에서 지역 변수와 겹치는지 AST로 검사한다.
  - (2026-10-21 정리) 원본 모듈과 이 생성기는 old/에 보관했다. **이제 binarized/ 파일이 기준이고 직접 고친다.** old/tools/build_binarized.py는 다시 돌리지 않는다.
- 검증
  - `tests/test_binarized.py`
    - a: 파일이 최신인지 확인한다.
    - b: 2_bin_track을 tracker3/piv_field/tau_unet/tau_tracker로 바꿔 끼워 test_events, test_instances, test_tau를 그대로 통과한다.
    - c: 점 후보와 내보내기가 원본과 같다. 학습(TAU, 3ch+ignore)의 가중치, log.json, test_report.json이 원본과 완전히 같다.
    - d: STEP 연결.
    - e: 3ch/5ch에 따라 main_single/main_tau를 고른다.
  - pyflakes에서 정의되지 않은 이름이 0이다.
  - 실데이터 60프레임(731~790, scratchpad/bundle_e2e)
    - best.pt: watershed.main과 2_bin_track의 출력 247개가 같다(JSON은 시간 항목만 빼고 비교).
    - 사용자 TAU ckpt: tau_tracker.main과 2_bin_track의 출력 151개가 같다. 단 pass_summary.json의 qc만 다르다.
      binarized/에 3_tracking_qc.py가 없어서 None이 됐기 때문이다. 입력인 패스별 CSV는 같다.
- 3_tracking_qc.py는 입력과 상관없이 CSV만 다루므로 그대로 둔다(두 파일과 같은 폴더에 있으면 TAU 패스별 비교표도 나온다).
- `binarized/0_prelabel.py` (손으로 쓴 파일, 생성 대상 아님): 라벨 초안 만들기.
  - 처리: 원본 + 배경 → 2_bin_track의 전처리와 U-Net(TauDetector, 3/5ch 모두, 사전 마스크 없음)과 unet_instances.
  - 마스크 보정: `GROW_PX`=1만큼 배경 쪽으로만 넓힌다. 검출 윤곽이 흰 링 바깥 가장자리보다 안쪽에 있기 때문이다.
  - 폴리곤: 화소 중심을 지나는 외곽선이다. `SIMPLIFY_PX`=0.7로 점을 줄이되, 점이 24개 이하인 작은 기포는 그대로 둔다.
  - 출력: OUT_FOLDER에 화상 + _annotations.coco.json(Roboflow Upload용)과 preview/를 만든다. EXPORT_IMAGE='raw'면 원본, 'binarized'면 이진화 png다.
  - 한계: drop_nested로 지운 기포 안 링은 초안에 없다. 구멍은 외곽선만 내보낸다.
  - 테스트 `tests/test_prelabel.py`
    - a: 점을 줄이지 않은 폴리곤은 fillPoly+polylines로 원래 마스크가 된다(L자, 선, 화면 끝 포함).
    - b: grow는 배경 쪽으로만 넓힌다.
    - c: 가짜 ckpt로 main을 끝까지 돌리고, 결과를 학습 스크립트의 load_coco가 읽는다.

## 큰 복잡한 기포 (2026-10-20, 637~641 + 사용자 새 영상 750프레임 CSV 63eac985)
- 637~641(1200×480)의 L자 슬러그(위쪽 띠 + 오른쪽 끝을 따라 내려가는 세로 띠)
  - 이전 best.pt와 새 TAU(tau480) 모두 같은 결과다. 638은 전부 누락, 639~641은 위쪽 띠만 검출, 세로 띠는 4프레임 모두 누락.
- 원인
  - p_edge(윤곽)는 끊김 없이 정확하다. 문제는 **어느 쪽이 기체인지**다.
    - 이진화 영상에서는 기체 내부와 액체가 같은 검정이라, U-Net이 윤곽의 곡률로 추측한다.
    - L자 안쪽 모서리처럼 곡률이 반대인 곳에서는 **액체 쪽에 p_in을 낸다**(640: x=441 액체 쪽 p_in>0.8, 기체 띠 x 450~479는 낮음).
  - 학습 화상은 전부 1080×416이다(best.pt, tau_best, tau480 모두 train_hw [1080,416]). 1200×480 조건의 화면 끝 거대 슬러그는 거의 배운 적이 없다고 본다.
  - 후처리
    - 638: thr 0.2·closing 5로 다시 닫으면 L 영역(4.1만 px)이 분리되고 심 비율 0.57로 구제 조건을 통과한다.
      그러나 띠 판정(벽 25 px 띠에서 Σp_in > Σp_bg)에서 13195 < 17691로 떨어진다. 세로 띠의 폭(30~40 px)이 띠 판정 범위 안에 다 들어가기 때문이다.
    - 640, 641: (0.1, 7)로 닫아도 액체와 이어진다.
- 새 CSV: 2만 px 이상 검출이 1275건(화면 끝 접촉 844건)이다. 프레임 680~696에 약 31만 px(화면의 55%) 검출이 있다. 실제 슬러그인지 오검출인지는 화상이 없어서 확인하지 못했다.
- 결정: **근본 해결로 간다** — 노출을 낮춰 새로 촬영하고 비이진화(차분) 입력을 쓴다.
  - 기체 내부가 액체보다 어둡게 남으면 안/밖을 국소적으로 구분할 수 있다(731~790에서 raw diff AUC 0.91, 이진화 0.53).
  - 후처리 규칙(다른 기포를 품지 않은 닫힌 영역 = 기체 등)은 보조 후보로만 둔다.

## 비이진화 버전 2파일 (raw/, 2026-10-20)
- 사용자가 배경이 남은 원본 약 50장을 Roboflow에서 라벨링했다(옛 46~47 조건처럼 노출이 적당한 영상). "학습용과 검출용 둘 다" 요청.
- 입력: 원본 + 배경 → B(지금과 같은 이진화) + D(Noise Cut만 뺀 차분, 기포 내부가 액체보다 약간 어두운 정보가 남음). `bin_diff`.
  - `INPUT_MODE`: `'bin+diff'`(권장, 4ch = B×3 + D, best.pt에서 D 가중치 0으로 시작 → 학습 전에는 best.pt와 같은 결과) / `'diff'`(D×3) / `'bin'`(대조군).
  - ckpt에 `input: {mode, preproc}`를 기록하고, 검출 쪽 `RawDetector`가 그것으로 같은 입력을 다시 만든다. 기록 없는 ckpt(지금 best.pt)는 'bin' + PREPROC_FIXED(기본 (15,4,0)).
- `raw/1_raw_train.py`
  - SRC = Roboflow 내보내기(원본 화상). 배경은 `BACKGROUNDS`(원래 파일명 앞부분 → 배경 경로, 가장 길게 일치하는 것). 원래 이름은 `extra.name` 또는 `<name>_jpg.rf.<hash>`에서 복원. 배경을 못 정한 화상이 있으면 목록을 내고 멈춘다.
  - DST/{bin,diff,masks}/<split>/. valid가 없으면 train의 10%를 val로. `meta.json`에 train_hw(새 train 화상의 최빈 크기)와 preproc.
  - `OLD_BIN_SRC`: 예전 이진화 내보내기(480장, train/valid/test)를 쓴다. D = B(원본이 없으므로).
    - train → split 'old', 학습에 섞는다. `OLD_SHARE`=0.5로 WeightedRandomSampler.
    - valid → 'old_val', best 선택 점수 = (1 − `OLD_VAL_WEIGHT`) × 새 val + `OLD_VAL_WEIGHT`(0.5) × 예전 val (2026-10-21 사용자 질문으로 추가).
      가중 평균만으로는 새 val 개선이 예전 val 악화를 상쇄하므로, 예전 val 점수가 시작 모델보다 `OLD_VAL_TOL`(0.01)을 넘게 떨어진 epoch는 best로 고르지 않는다(log의 old_val_drop).
    - 예전 데이터를 쓸지는 DST 폴더가 아니라 `OLD_BIN_SRC` 설정으로 정한다. meta.json에 layout/src/old_src/preproc를 기록하고, REBUILD_DATASET=False라도 다르면 다시 만든다(리뷰에서 발견).
    - test → 'old_test', [3]에서 별도 표(시작 모델 vs 새 모델, test_report.json의 `old_test`). 예전 best.pt도 이 test는 학습·선택에 안 썼으므로 공정한 비교.
  - FINETUNE_FROM=best.pt, epoch 0(시작 모델)을 기준으로 best를 고른다. 'bin+diff'는 epoch마다 D 가중치 크기 표시.
  - test: 시작 모델(그 ckpt의 입력) vs 새 모델의 화소 IoU + 크기별 재현율/적합율, test_preview(배경 D).
  - dot 라벨/ignore, TAU는 넣지 않았다.
- `raw/2_raw_track.py`: binarized/2_bin_track.py에서 TAU(설정, [B] 부품, [D] 다중 패스, 디스패처)를 빼고 UNetDetector를 RawDetector로 바꾼 것.
  - 전처리 값은 ckpt 기록을 쓰고 슬라이더는 안 띄운다. 배경 화상은 필수. 오버레이/확률맵 png 배경은 B. qc_report의 used_params.UNET.detection.input에 입력 기록.
- 생성: `python tools/build_raw.py`(`--check`). 재료는 `tools/raw_parts/`(train.py 본체, raw_input.py, raw_detector.py) + binarized/1_bin_train.py의 공통 부품(AST로 복사) + binarized/2_bin_track.py + binarized/3_tracking_qc.py(그대로 복사). **binarized/나 tools/raw_parts/를 고치면 다시 만든다.**
- 테스트 `tests/test_raw.py` a~e
  - a 최신, b bin_diff의 B = preprocess_image, c RawDetector = UNetDetector(완전 일치, 리사이즈 포함)·4ch 0 초기화 = 3ch·채널 불일치 오류
  - d 학습 스모크(3모드, Roboflow 이름, OLD_BIN_SRC의 train/valid/test 사용과 합산 점수(가중치 0.3으로 뒤바뀜 검출)·OLD_VAL_TOL·REBUILD_DATASET=False 재사용/재생성, 배경 누락 오류, 학습한 4ch에서 이어 학습), e 기록 없는 3ch ckpt면 2_bin_track과 CSV 바이트 동일 + 학습한 bin+diff ckpt로 끝까지 실행.
- 실데이터 학습·검증은 하지 않았다(사용자 PC에서).

## 저장소 구성 (2026-10-21 정리, 사용자 요청: "앞으로 쓸 것만 모으고 옛날 파일은 old/에 보존")
- 사용자용 안내는 `README.md`(한국어). 폴더 하나만 PC에 복사하면 동작하게 했다.
- `raw/` — 비이진화 버전(앞으로 주로 사용). `1_raw_train.py`, `2_raw_track.py`, `3_tracking_qc.py`. 전부 `tools/build_raw.py`가 생성(직접 고치지 않음).
- `binarized/` — 이진화 버전. `0_prelabel.py`(손으로 씀), `1_bin_train.py`, `2_bin_track.py`, `3_tracking_qc.py`. **이 폴더가 이진화 코드의 기준이며 직접 고친다.** 고친 뒤 `python tools/build_raw.py`.
  - `3_tracking_qc.py`의 기준은 `binarized/3_tracking_qc.py`(raw/는 복사본).
- `tools/` — `build_raw.py`, `raw_parts/`(raw 생성 재료), `shrink_ckpt.py`(best.pt 분할/fp16).
- `tests/` — 지금 코드의 테스트.
  - `bundles.py`: binarized/의 1파일 버전을 원래 모듈 이름(tracker3, piv_field, tau_unet, tau_tracker, watershed, dot_labels)으로 import하게 한다. `importlib.reload`가 되도록 binarized/를 sys.path에 넣고 이름으로 import.
  - `test_events.py`, `test_instances.py`, `test_tau.py`, `test_dots.py`: 원래 테스트를 bundles 경유로 binarized/에 대해 돈다. 바꾼 곳: import 경로, 학습 스크립트 경로(`bundles.TRAIN_PATH`), dot의 OUT/REVIEW/main → DOT_OUT/DOT_REVIEW/main_dots, 학습 main → main_train, test_tau f는 USE_PRIOR=True(번들 기본값 False).
  - `test_qc.py`(binarized/3_tracking_qc.py), `test_prelabel.py`, `test_binarized.py`(번들 전용 d STEP 연결, e 3ch/5ch 디스패치만 남김), `test_raw.py`, `fake_detector.py`(테스트용 사본).
- `old/` — 보관(`old/README.md`에 목록). tracker2/3, watershed, piv_field, tau_unet, tau_tracker, 1_tau_unet_train, dot_labels, 3_tracking_qc(정리 시점 사본), fake_detector, sim_compare, sim_piv, qc_compare, reference/piv_prior.py, docs/PIV_TASK.md, tools/build_binarized.py, tests/.
  - `cd old && python -B tests/test_events.py` 등으로 예전 테스트가 그대로 돈다(정리 시점에 events 11, instances 14, qc 12, tau 7, dots 8 모두 통과). old/tests/test_binarized.py와 old/tools/build_binarized.py는 old/binarized/를 찾으므로 동작하지 않는다.
  - 위의 각 절에 나오는 `tracker3.py`, `docs/PIV_TASK.md`, `reference/piv_prior.py` 등은 이제 old/ 아래 경로다.
- 테스트 실행 (루트에서): `python -B tests/test_events.py`, `tests/test_qc.py`, `tests/test_instances.py`, `tests/test_tau.py`, `tests/test_dots.py`,
  `tests/test_binarized.py`, `tests/test_prelabel.py`, `tests/test_raw.py` (pytest로도 실행 가능).

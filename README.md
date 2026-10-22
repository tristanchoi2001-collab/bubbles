# 마이크로갭 기포 검출·추적

고속 촬영 영상에서 기포를 U-Net으로 검출하고(배경 / 기포 내부 / 기포 경계), 기포마다 ID를 붙여 추적한다.

## 폴더

| 폴더 | 내용 | 언제 쓰나 |
|---|---|---|
| `raw/` | **비이진화 버전** (원본 + 배경 → 이진화 B + 차분 D) | 앞으로 주로 사용. 배경이 남은(포화되지 않은) 영상 |
| `binarized/` | **이진화 버전** (지금까지의 방식, 지금 best.pt) | 이진화 데이터 학습, 작은 점 라벨 보충, 라벨 초안 |
| `steel/` | **철(불투명) 배경 채널용** (raw/를 2026-10-22에 떼어 낸 고정 사본 + 배경 밝기 맞춤) | 배경이 금속인 채널. 투명 채널은 raw/ |
| `old/` | 예전 파일 보관 (tracker2/3, watershed, TAU, PIV 원본, 비교 스크립트, 지시서) | 쓰지 않음. 기록용 |
| `tools/`, `tests/` | 개발용 (생성 스크립트, 테스트), `tools/shrink_ckpt.py` (best.pt 분할) | 안 봐도 됨 |

`raw/`, `binarized/`, `steel/`은 **그 폴더만 PC에 복사하면 동작**한다. 설정은 각 파일 맨 위에 모여 있다.
각 폴더의 `3_tracking_qc.py`와 `4_link_audit.py`는 같은 파일이다.

## raw/ — 비이진화 (앞으로)

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `1_raw_train.py` | 학습. `SRC`(새 원본 라벨), `BACKGROUNDS`(파일명 앞부분 → 배경), `FINETUNE_FROM = best.pt`, `OLD_BIN_SRC`(예전 이진화 480장) 설정 → `runs/raw/best.pt`. 마지막에 test 표 2개 (새 원본 / 예전 이진화) |
| 2 | `2_raw_track.py` | 검출·추적. `UNET_CKPT`, `IMAGE_FOLDER`, `BACKGROUND_PATH`, `OUTPUT_FOLDER` → `result_tracking.csv` 등 |
| 3 | `3_tracking_qc.py` | 추적 점검. `TRACKING_CSV` = 2의 `result_tracking.csv` |
| (선택) | `4_link_audit.py` | **연결 감사**: 기포를 무작위로 골라 다음 프레임 연결이 맞는지 y/n으로 판정 → 크기별 연결 정확도·끊김 비율(95% 구간). 논문용 실데이터 추적 정확도 |

- `INPUT_MODE`: `'bin+sign'`(기본, 이진화 + 어두워진 분 + 밝아진 분) / `'bin+diff'` / `'diff'` / `'bin'`(비교용).
- 추가 부품 (on/off): `CTX_LAYERS`(작은 트랜스포머, 0 = 끔, 시도 2), `USE_PRIOR`(TAU, 앞뒤 프레임의 검출을 함께 입력).
  새로 붙인 부분의 가중치는 0에서 시작하므로 학습 전에는 시작 모델과 같은 결과다. 학습 로그의 `入口の重み` / `トランスフォーマー出口`가 0 근처에 머물면 그 부품은 쓰이지 않은 것이다.
- 입력 방식·부품·전처리 값은 best.pt에 기록되어 `2_raw_track.py`가 자동으로 맞춘다. TAU 모델이면 `2_raw_track.py`가 여러 번 다시 검출한다(`PRIOR_PASSES`).
- 지금 이진화 best.pt를 `2_raw_track.py`에 넣으면 `binarized/2_bin_track.py`와 같은 결과가 나온다.

## steel/ — 철(불투명) 배경 채널

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `1_steel_train.py` | 학습. 설정은 `1_raw_train.py`와 같고 `BG_MATCH`만 더 있다 → `runs/steel/best.pt` |
| 2 | `2_steel_track.py` | 검출·추적. best.pt에 기록된 `BG_MATCH`를 자동으로 쓴다 |
| 3 | `3_tracking_qc.py` | 추적 점검 (raw/와 같은 파일) |
| (선택) | `4_link_audit.py` | 연결 감사 (raw/와 같은 파일) |

- raw/를 떼어 낸 **고정 사본**이다. 앞으로 투명 채널용으로 raw/·binarized/를 고쳐도(parity 구제 등) steel/은 바뀌지 않는다. 고칠 때는 steel/ 파일을 직접 고친다.
- raw/와 다른 점은 `BG_MATCH`(기본 `'offset'`) 하나다. 매 프레임 배경 화상의 밝기를 원본에 맞춘 뒤 B / DK / DB를 만든다. 촬영 중 조명이 조금 바뀌어도 DB(밝아진 분)가 화면 전체에 깔리지 않게 하려는 것이다.
  - 기포가 화면의 대부분을 덮어 맞춘 값이 이상하면(직전 프레임에서 5 계조 넘게 급변, 또는 15 계조 넘는 보정) 그 프레임은 직전 값을 쓰고 경고를 낸다. 결과는 `qc_report.json`의 `bg_fit`에 남는다.
  - steel/에서 학습한 best.pt는 raw/·binarized/의 검출 파일에 넣으면 오류로 멈춘다(입력을 만드는 방법이 달라서). `2_steel_track.py`에서 쓴다.
- 철 채널에서는 기포 **내부**가 액체보다 약 40 계조 어둡다(시험 촬영 1장, 기포 1개). 그래서 이진화 화상 B에서도 기포가 흰 링이 아니라 **흰 원판**으로 보인다. 투명 채널의 예전 이진화 데이터(`OLD_BIN_SRC`)는 섞지 않는다.
- 라벨은 지금처럼 기포 윤곽의 바깥쪽에 폴리곤을 그린다. 배경 화상은 기포가 없는 프레임을 **같은 노출·조명**으로 찍고, 가능하면 PNG처럼 압축하지 않은 형식으로 저장한다.

## binarized/ — 이진화

| 순서 | 파일 | 하는 일 |
|---|---|---|
| (선택) | `0_prelabel.py` | 지금 모델의 검출 결과로 라벨 초안(COCO) → Roboflow에 올려 틀린 것만 고친다 |
| 1 | `1_bin_train.py` | `STEP = 'dots'`: 작은 점 후보를 y/n으로 확인 → `STEP = 'train'`: 학습 |
| 2 | `2_bin_track.py` | 검출·추적 (이진화 입력) |
| 3 | `3_tracking_qc.py` | 추적 점검 |
| (선택) | `4_link_audit.py` | 연결 감사 (위와 같은 파일) |

## 연결 감사 (`4_link_audit.py`) 사용법

1. 맨 위의 `TRACKING_CSV`를 `2_*_track.py`가 만든 `result_tracking.csv`로 바꾼다. 표시 화상은 기본으로 같은 폴더의 `_cache_processed`(이진화 화상)를 쓴다.
   - `2_*_track.py`를 `SAVE_INSTANCE_MASKS = True`로 돌려 두면 원 대신 검출 윤곽 그대로 그려서 큰 기포를 판정하기 쉽다.
2. `python 4_link_audit.py` → 창에 한 건씩 t-1, t, t+1, t+2가 나온다(**영문 입력 상태**에서 키를 누른다).
   - 노랑 = 확인할 기포, 초록 = 트래커가 같은 ID로 이은 기포, 주황 = 합체 상대, 하늘 = 분열 자식, 마젠타 = 다른 검출, 빨간 × = 예측 위치.
   - `y` 맞음 / `n` 틀림 / `m` 놓침(끝냈지만 t+1에 검출이 있음) / `d` t+1에 보이는데 검출이 없음 / `u` 모르겠음 / `b` 뒤로 / `q` 저장 후 종료(다시 실행하면 이어서).
   - "LOST then re-linked"(끊겼다 다시 이음) 건은 초록이 같은 기포인지만 보면 된다.
3. 끝나면 `link_audit/link_audit_report_<지문>.json`과 화면에 크기별 표가 나온다(연결 정확도, 놓침률, 트래커 오류율, 95% 구간). 크기별 100건이면 300건, 15~30분 정도.
4. 설정을 바꾼 두 실행을 비교할 때는 `2_*_track.py`의 `OUTPUT_FOLDER`를 다르게 해서 돌리고, 각각의 CSV로 감사한다.
   - 예: 게이트 보정 끔 = `SPACING_GATE_FRAC = 0`, `BOOTSTRAP_CHAIN_FRAMES = 3` / 켬 = 기본값.

## 개발 메모

- `raw/`의 파일은 `tools/build_raw.py`가 `binarized/` + `tools/raw_parts/`로 만든다. `binarized/`나 `tools/raw_parts/`를 고치면 `python tools/build_raw.py`.
- `steel/`은 생성하지 않는다(고정 사본, 직접 고침). 테스트는 `tests/test_steel.py`.
- 테스트: `python -B tests/test_raw.py` 등 (`tests/` 안의 `test_*.py`), 또는 루트에서 `python -m pytest`.
- 자세한 경위와 결정 사항은 `CLAUDE.md`.

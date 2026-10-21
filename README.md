# 마이크로갭 기포 검출·추적

고속 촬영 영상에서 기포를 U-Net으로 검출하고(배경 / 기포 내부 / 기포 경계), 기포마다 ID를 붙여 추적한다.

## 폴더

| 폴더 | 내용 | 언제 쓰나 |
|---|---|---|
| `raw/` | **비이진화 버전** (원본 + 배경 → 이진화 B + 차분 D) | 앞으로 주로 사용. 배경이 남은(포화되지 않은) 영상 |
| `binarized/` | **이진화 버전** (지금까지의 방식, 지금 best.pt) | 이진화 데이터 학습, 작은 점 라벨 보충, 라벨 초안 |
| `old/` | 예전 파일 보관 (tracker2/3, watershed, TAU, PIV 원본, 비교 스크립트, 지시서) | 쓰지 않음. 기록용 |
| `tools/`, `tests/` | 개발용 (생성 스크립트, 테스트), `tools/shrink_ckpt.py` (best.pt 분할) | 안 봐도 됨 |

`raw/`와 `binarized/`는 **그 폴더만 PC에 복사하면 동작**한다. 설정은 각 파일 맨 위에 모여 있다.
각 폴더의 `3_tracking_qc.py`는 같은 파일이다.

## raw/ — 비이진화 (앞으로)

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `1_raw_train.py` | 학습. `SRC`(새 원본 라벨), `BACKGROUNDS`(파일명 앞부분 → 배경), `FINETUNE_FROM = best.pt`, `OLD_BIN_SRC`(예전 이진화 480장) 설정 → `runs/raw/best.pt`. 마지막에 test 표 2개 (새 원본 / 예전 이진화) |
| 2 | `2_raw_track.py` | 검출·추적. `UNET_CKPT`, `IMAGE_FOLDER`, `BACKGROUND_PATH`, `OUTPUT_FOLDER` → `result_tracking.csv` 등 |
| 3 | `3_tracking_qc.py` | 추적 점검. `TRACKING_CSV` = 2의 `result_tracking.csv` |

- `INPUT_MODE`: `'bin+sign'`(기본, 이진화 + 어두워진 분 + 밝아진 분) / `'bin+diff'` / `'diff'` / `'bin'`(비교용).
- 추가 부품 (on/off): `CTX_LAYERS`(작은 트랜스포머, 0 = 끔, 시도 2), `USE_PRIOR`(TAU, 앞뒤 프레임의 검출을 함께 입력).
  새로 붙인 부분의 가중치는 0에서 시작하므로 학습 전에는 시작 모델과 같은 결과다. 학습 로그의 `入口の重み` / `トランスフォーマー出口`가 0 근처에 머물면 그 부품은 쓰이지 않은 것이다.
- 입력 방식·부품·전처리 값은 best.pt에 기록되어 `2_raw_track.py`가 자동으로 맞춘다. TAU 모델이면 `2_raw_track.py`가 여러 번 다시 검출한다(`PRIOR_PASSES`).
- 지금 이진화 best.pt를 `2_raw_track.py`에 넣으면 `binarized/2_bin_track.py`와 같은 결과가 나온다.

## binarized/ — 이진화

| 순서 | 파일 | 하는 일 |
|---|---|---|
| (선택) | `0_prelabel.py` | 지금 모델의 검출 결과로 라벨 초안(COCO) → Roboflow에 올려 틀린 것만 고친다 |
| 1 | `1_bin_train.py` | `STEP = 'dots'`: 작은 점 후보를 y/n으로 확인 → `STEP = 'train'`: 학습 |
| 2 | `2_bin_track.py` | 검출·추적 (이진화 입력) |
| 3 | `3_tracking_qc.py` | 추적 점검 |

## 개발 메모

- `raw/`의 파일은 `tools/build_raw.py`가 `binarized/` + `tools/raw_parts/`로 만든다. `binarized/`나 `tools/raw_parts/`를 고치면 `python tools/build_raw.py`.
- 테스트: `python -B tests/test_raw.py` 등 (`tests/` 안의 `test_*.py`), 또는 루트에서 `python -m pytest`.
- 자세한 경위와 결정 사항은 `CLAUDE.md`.

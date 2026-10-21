# old/ — 예전 파일 보관 (2026-10-21 정리)

지금은 쓰지 않는 파일. 내용은 정리 전 그대로다(수정하지 않음).
지금 쓰는 코드는 저장소 루트의 `raw/`(비이진화)와 `binarized/`(이진화)에 있다.

| 파일 | 내용 | 지금은 |
|---|---|---|
| `tracker2.py` | 트래커 v2 (지시서의 tracker.py) | — |
| `tracker3.py`, `watershed.py` | 트래커 v3 (watershed는 기본값만 다른 사본) | `binarized/2_bin_track.py`에 들어 있음 |
| `piv_field.py` | 크기별 PIV | `binarized/2_bin_track.py` [A] |
| `tau_unet.py`, `tau_tracker.py`, `1_tau_unet_train.py` | Tracking-aware U-Net (보류) | `binarized/1_bin_train.py`, `2_bin_track.py` |
| `dot_labels.py` | 작은 점 라벨 보충 | `binarized/1_bin_train.py` (`STEP = 'dots'`) |
| `3_tracking_qc.py` | 추적 점검 (정리 시점의 사본) | `binarized/3_tracking_qc.py`, `raw/3_tracking_qc.py` |
| `fake_detector.py`, `sim_compare.py`, `sim_piv.py`, `qc_compare.py` | 합성 벤치마크·비교 스크립트 | `tests/fake_detector.py`(테스트용 사본) |
| `reference/piv_prior.py`, `docs/PIV_TASK.md` | PIV 참고 구현, 작업 지시서 원문 | — |
| `tools/build_binarized.py` | 위 모듈들로 `binarized/`를 만들던 스크립트 | 더 이상 쓰지 않음 (`binarized/`를 직접 고친다) |
| `tests/` | 위 모듈들의 테스트 | — |

- `old/` 안에서 예전 테스트를 돌릴 수 있다: `cd old && python -B tests/test_events.py` (test_events, test_instances, test_qc, test_tau, test_dots는 정리 시점에 모두 통과).
- `tests/test_binarized.py`와 `tools/build_binarized.py`는 `old/binarized/`를 찾으므로 여기서는 동작하지 않는다(기록용).

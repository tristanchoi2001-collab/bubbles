"""
Microgap Bubble Tracking - Tracking-aware U-Net 版 (tau_tracker)
=====================================================================
U-Net に「このフレームに気泡がどこにあるはずか」(前のパスのトラックから予測した気泡マスク) を一緒に入力し、
見落とし・ちらつき・くっついた気泡の境目の揺れを、前後のフレームの情報で直す。
モデルは 1_tau_unet_train.py で作る (入力 5チャンネル: 画像 ×3 + 事前マスクの 内部・輪郭。tau_unet.py)。
前処理・気泡の分け方・トラッキング・CSV/オーバーレイ/QC は tracker3.py をそのまま使う (tracker3.py を import する)。

処理の流れ (オフライン。動画を何回か通す):
  パス0 : 事前マスクなし (= 普通の U-Net) で全フレームを検出 -> ブートストラップ -> トラッキング
  パス1 : フレーム t の事前マスク = パス0 のトラックから予測した t の気泡マスク
            t-1 と t+1 の両方にいるトラック -> t-1 のマスクを「t-1 -> t+1 の移動量の半分」だけ動かす (内挿)
            t-1 だけ                       -> t-1 のマスクを「t-2 -> t-1 の移動量」だけ前へ (分からなければ動かさない)
            t+1 だけ                       -> t+1 のマスクを「t+1 -> t+2 の移動量」だけ後ろへ
          t 自身の検出は使わない (誤検出が自分自身を支えないように)。
          観測が PRIOR_MIN_HITS 回未満 (t を除く) のトラックも使わない (1フレームだけの誤検出を広げないように)
          -> 事前マスク付きで全フレームを検出し直す -> 同じゲートでトラッキング
  パス2.. : PRIOR_PASSES まで繰り返す (検出が前のパスと同じになったら終了)。
            何フレームも続けて見落とした気泡は、両端のフレームから 1パスごとに1フレームずつ取り戻す
  最後のパスの結果を tracker3.py と同じ形式で出力する (result_tracking.csv / result_area_count.csv / オーバーレイ / qc_report.json)
  パスごとの CSV (OUTPUT_FOLDER/passes/pass<k>/) と QC の比較表 (pass_summary.json) も出す

best.pt (3チャンネルのモデル) を UNET_CKPT に入れると事前マスクは使われず、全パスが tracker3.py と同じ検出になる
(パス1 で「前のパスと同じ」になって終了する)。動作確認用。
tau_unet.py, tracker3.py, piv_field.py を同じフォルダに置いて実行すること。
"""

# ------------------------------------------------------------
# パスの設定 (自分の環境に合わせて変更すること)
# ------------------------------------------------------------
UNET_CKPT = r"C:\Users\inoue-2024-01\Desktop\U-net\runs\tau\best.pt"   # 1_tau_unet_train.py の出力
IMAGE_FOLDER = None       # 分析する画像があるフォルダ。None なら tracker3.py の IMAGE_FOLDER
BACKGROUND_PATH = None    # 背景画像のパス。None なら tracker3.py の BACKGROUND_PATH
OUTPUT_FOLDER = r"C:\Users\inoue-2024-01\Desktop\U-net\output_tau"   # 結果を保存するフォルダ (tracker3.py の結果を上書きしない)

# ------------------------------------------------------------
# Tracking-aware の設定
# ------------------------------------------------------------
UNET_INSTANCE_MODE = "hybrid"  # 確率マップ -> 気泡の分け方 (tracker3.py の UNET_INSTANCE_MODE と同じ。"wall" / "hybrid")
PRIOR_PASSES = 2          # 事前マスク付きで検出し直す回数 (0 なら tracker3.py と同じ 1回だけ)
PRIOR_FROM = "both"       # "both" = 前後のフレームから予測 / "forward" = 前のフレームだけ (オンライン処理と同じ情報。比較用)
PRIOR_MIN_HITS = 2        # 事前マスクに入れるトラックの観測回数の下限 (そのフレーム自身を除く)
SAVE_PASS_RESULTS = True  # パスごとの result_tracking.csv / qc_report.json を OUTPUT_FOLDER/passes/pass<k>/ に保存
SAVE_PRIOR_DEBUG = True   # 前のパスと検出が変わったフレームの確認画像を OUTPUT_FOLDER/prior_debug/ に保存
PRIOR_DEBUG_MAX = 30      # 確認画像の上限 (パスごと)

import glob
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from typing import Callable, Dict, List, Optional

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import tau_unet           # noqa: E402
import tracker3 as T3     # noqa: E402

SIZE_CLASSES = (("tiny", 0, 50), ("small", 50, 500), ("large", 500, float("inf")))   # QC と同じ (面積 px)


def size_class(area: float) -> str:
    return next(n for n, lo, hi in SIZE_CLASSES if lo <= area < hi)


# ==============================================================
# 1. 前のパスのトラック -> 事前マスク
# ==============================================================
class TrackObservations:
    """パスの結果 (検出 + トラッキングの行) を「フレーム -> {トラックID: (検出, 行)}」に並べ替えたもの"""

    def __init__(self, dets_per_frame: List[List[T3.Detection]], rows_by_frame: Dict[int, List[dict]]):
        self.obs: Dict[int, Dict[int, tuple]] = defaultdict(dict)
        self.count: Counter = Counter()
        for f, rows in rows_by_frame.items():
            for r in rows:
                di = r["det_index"]
                if di is None:   # 合体で吸収された記録 (merged_into_...)
                    continue
                tid = r["track_id"]
                if tid not in self.obs[f]:
                    self.count[tid] += 1
                self.obs[f][tid] = (dets_per_frame[f][di], r)

    @staticmethod
    def _steady(row) -> bool:
        """この観測の直前からの移動量を気泡の速度として使ってよいか (合体/分裂・輪郭の付け替えの直後は使わない)"""
        return row["event"] == "normal" and not row.get("hold_v")

    def prior_shapes(self, t: int, mode: str = "both", min_hits: int = 2) -> List[T3.Shape]:
        """フレーム t の事前マスク用の気泡マスク (t 自身の検出は使わない)"""
        prev, nxt = self.obs.get(t - 1, {}), (self.obs.get(t + 1, {}) if mode == "both" else {})
        here = self.obs.get(t, {})
        shapes = []
        for tid in sorted(set(prev) | set(nxt)):
            if self.count[tid] - (1 if tid in here else 0) < min_hits:
                continue
            a, b = prev.get(tid), nxt.get(tid)
            if a and b:
                dx, dy, _ = T3.displacement(a[0], b[0])
                shapes.append(T3.shift_shape(a[0].shape, dx / 2, dy / 2))
            elif a:
                p2 = self.obs.get(t - 2, {}).get(tid)
                dx, dy = (T3.displacement(p2[0], a[0])[:2] if p2 and self._steady(a[1]) else (0.0, 0.0))
                shapes.append(T3.shift_shape(a[0].shape, dx, dy))
            else:
                n2 = self.obs.get(t + 2, {}).get(tid)
                dx, dy = (T3.displacement(b[0], n2[0])[:2] if n2 and self._steady(n2[1]) else (0.0, 0.0))
                shapes.append(T3.shift_shape(b[0].shape, -dx, -dy))
        return shapes


# ==============================================================
# 2. パスの実行
# ==============================================================
def inst_from_dets(dets: List[T3.Detection], H: int, W: int) -> np.ndarray:
    """検出の一覧 -> 気泡ラベルマップ (比較用)"""
    inst = np.zeros((H, W), np.int32)
    for k, d in enumerate(dets, start=1):
        m, x0, y0 = d.shape
        inst[y0:y0 + m.shape[0], x0:x0 + m.shape[1]][m] = k
    return inst


def same_detections(a: List[T3.Detection], b: List[T3.Detection]) -> bool:
    if len(a) != len(b):
        return False
    return all(da.shape[1:] == db.shape[1:] and da.shape[0].shape == db.shape[0].shape
               and np.array_equal(da.shape[0], db.shape[0]) for da, db in zip(a, b))


def save_prior_debug(path: str, gray: np.ndarray, prior: np.ndarray, prev_inst: np.ndarray, inst: np.ndarray,
                     only_prev: List[int], only_now: List[int], k: int):
    """左: 入力 + 事前マスク (青 = 内部, 黄 = 輪郭) / 右: 検出 (灰 = 全気泡, 赤 = 前のパスだけ, 緑 = このパスだけ)"""
    left = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    if prior is not None:
        tint = left.copy()
        tint[prior[0] > 0.5] = (255, 120, 0)
        left = cv2.addWeighted(left, 0.6, tint, 0.4, 0)
        left[prior[1] > 0.5] = (0, 255, 255)
    right = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cs, _ = cv2.findContours((inst > 0).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(right, cs, -1, (128, 128, 128), 1)
    for lab, ids, col in ((prev_inst, only_prev, (0, 0, 255)), (inst, only_now, (0, 255, 0))):
        if ids:
            cs, _ = cv2.findContours(np.isin(lab, ids).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(right, cs, -1, col, 2)
    cv2.putText(left, f"pass{k} prior", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(right, f"red: pass{k - 1} only {len(only_prev)}  green: pass{k} only {len(only_now)}", (6, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.imwrite(path, np.hstack([left, np.full((gray.shape[0], 4, 3), 128, np.uint8), right]))


def detect_pass(k: int, n_frames: int, gray_of: Callable[[int], np.ndarray], detector, roi_bool,
                prev: Optional[TrackObservations] = None, prev_dets=None, names=None, debug_dir=None,
                on_frame=None, log=print):
    """パス k の検出。prev (前のパスの結果) があれば事前マスクを作って入れる。
    戻り値: (フレームごとの検出, 集計)"""
    dets_all: List[List[T3.Detection]] = []
    st = {"pass": k, "prior_shapes": 0, "changed_frames": 0, "only_prev": 0, "only_now": 0, "debug_saved": 0}
    inst_stats: Dict[str, int] = {}
    for f in range(n_frames):
        gray = gray_of(f)
        H, W = gray.shape
        prior = None
        if prev is not None:
            shapes = prev.prior_shapes(f, PRIOR_FROM, PRIOR_MIN_HITS)
            st["prior_shapes"] += len(shapes)
            prior = tau_unet.render_prior(shapes, H, W, getattr(detector, "edge_px", tau_unet.PRIOR_EDGE_PX))
        prob = detector.prob(gray, prior)
        n_res0 = inst_stats.get("rescued", 0)
        inst = T3.unet_instances(prob, stats=inst_stats)
        dets = T3.instances_to_detections(inst, roi_bool)
        dets_all.append(dets)
        msg = ""
        if prev_dets is not None:
            pinst = inst_from_dets(prev_dets[f], H, W)
            cinst = inst_from_dets(dets, H, W)
            only_prev, only_now = T3.unmatched_instances(pinst, cinst), T3.unmatched_instances(cinst, pinst)
            st["only_prev"] += len(only_prev)
            st["only_now"] += len(only_now)
            if only_prev or only_now:
                st["changed_frames"] += 1
                msg = f"  | パス{k - 1}だけ {len(only_prev)}個, パス{k}だけ {len(only_now)}個"
                if debug_dir and st["debug_saved"] < PRIOR_DEBUG_MAX:
                    stem = os.path.splitext(names[f])[0] if names else f"{f:06d}"
                    save_prior_debug(os.path.join(debug_dir, f"{stem}_pass{k}.png"), gray, prior, pinst, cinst,
                                     only_prev, only_now, k)
                    st["debug_saved"] += 1
        n_res = inst_stats.get("rescued", 0) - n_res0
        if on_frame is not None:
            on_frame(f, gray, prob, inst, dets)
        name = names[f] if names else str(f)
        log(f"  [パス{k} {name}] 検出{len(dets)}個" + (f", 事前マスクの気泡 {len(shapes)}個" if prev is not None else "")
            + (f"  | 救済 {n_res}個" if n_res else "") + msg)
    st["rescued"] = inst_stats.get("rescued", 0)
    return dets_all, st


def run_passes(n_frames: int, gray_of: Callable[[int], np.ndarray], detector, roi_bool, image_size,
               passes: int = PRIOR_PASSES, names=None, debug_dir=None, after_pass0=None, on_frame0=None,
               log=print):
    """全パスを実行する。detector は prob(gray, prior) を持つもの (TauDetector など)。
    after_pass0(dets): パス0 の検出のあと、トラッキングの前に呼ぶ (ブートストラップ用)。
    戻り値: [(検出, トラッキングの行, 集計) ...] パス0 から順に"""
    results = []
    log("\n[パス0] 事前マスクなしで検出")
    dets, st = detect_pass(0, n_frames, gray_of, detector, roi_bool, names=names, on_frame=on_frame0, log=log)
    if after_pass0 is not None:
        after_pass0(dets)
    log("\n[パス0] トラッキング")
    rows = T3.run_laptrack(dets, image_size)
    results.append((dets, rows, st))
    if passes > 0 and not getattr(detector, "uses_prior", True):
        log("  ※ このモデルは事前マスクを入力しない (3チャンネル) ので、パス1 以降もパス0 と同じ検出になります")
    for k in range(1, passes + 1):
        log(f"\n[パス{k}] パス{k - 1} のトラックから事前マスクを作って検出し直す")
        prev = TrackObservations(dets, rows)
        dets_k, st = detect_pass(k, n_frames, gray_of, detector, roi_bool, prev, dets, names, debug_dir, log=log)
        log(f"  パス{k - 1} と違う気泡: パス{k - 1}だけ {st['only_prev']}個, パス{k}だけ {st['only_now']}個 "
            f"({st['changed_frames']} フレーム)")
        same = all(same_detections(a, b) for a, b in zip(dets, dets_k))
        if same:
            log(f"  パス{k} の検出がパス{k - 1} と全く同じなので、ここで終了します")
            break
        log(f"\n[パス{k}] トラッキング")
        dets, rows = dets_k, T3.run_laptrack(dets_k, image_size)
        results.append((dets, rows, st))
    return results


# ==============================================================
# 3. パスごとの比較 (3_tracking_qc.py の項目)
# ==============================================================
def load_qc_module():
    import importlib.util
    path = os.path.join(HERE, "3_tracking_qc.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("tracking_qc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pass_qc(Q, csv_path: str, roi, n_frames: int) -> dict:
    """パスの CSV に 3_tracking_qc.py の解析をかけ、比較表の項目だけ取り出す"""
    rows, frame_files, has_touch = Q.load_tracking_csv(csv_path)
    flags, info = Q.analyze(rows, frame_files, has_touch, None, max_age=T3.MAX_AGE)
    s = Q.summarize(flags, info, roi)
    nf = max(1, n_frames)
    c = s["counts"]
    dev = s["deviation_from_prediction"]
    return {
        "observations_per_frame": {k: round(v / nf, 2) for k, v in s["observations_by_size"].items()},
        "n_tracks": s["n_tracks"],
        "interior_new_per_frame": {k: round(v / nf, 3) for k, v in c["INTERIOR_NEW"].items()},
        "interior_lost_per_frame": {k: round(v / nf, 3) for k, v in c["INTERIOR_LOST"].items()},
        "swap_likely": dict(c["SWAP_LIKELY"]),
        "merge_split": dict(c["MERGE_SPLIT"]),
        "area_jump": dict(c["AREA_JUMP"]),
        "frac_over_threshold": {k: v["frac_over_threshold"] for k, v in dev.items()},
        "suspicious_ratio_by_area": s["suspicious_ratio_by_area"],
    }


def print_pass_table(summ: List[dict], log=print):
    keys = [("observations_per_frame", "検出/フレーム", "{:.1f}"), ("interior_new_per_frame", "内部新規/フレーム", "{:.2f}"),
            ("interior_lost_per_frame", "内部消失/フレーム", "{:.2f}"), ("swap_likely", "ID乗り移り", "{}"),
            ("merge_split", "合体直後の分裂", "{}"), ("frac_over_threshold", "基準超え", "{:.1%}")]
    log("\n=== パスごとの比較 (3_tracking_qc.py の項目) ===")
    log(f"{'項目':<16}{'大きさ':<8}" + "".join(f"{'パス' + str(s['pass']):>10}" for s in summ))
    for key, label, fmt in keys:
        for cls in ("tiny", "small", "large"):
            vals = [s["qc"].get(key, {}).get(cls) for s in summ]
            log(f"{label:<16}{cls:<8}" + "".join(f"{(fmt.format(v) if v is not None else '-'):>10}" for v in vals))
    log(f"{'トラック数':<24}" + "".join(f"{s['qc']['n_tracks']:>10}" for s in summ))
    log(f"{'疑わしい割合(面積)':<20}" + "".join(f"{s['qc']['suspicious_ratio_by_area']:>10.2%}" for s in summ))


# ==============================================================
# 4. メイン
# ==============================================================
def set_detection_stats(st: dict):
    """qc_report.json の used_params.UNET.detection に入れる集計"""
    T3.DETECTION_STATS.clear()
    T3.DETECTION_STATS["mode"] = UNET_INSTANCE_MODE
    if UNET_INSTANCE_MODE == "hybrid":
        T3.DETECTION_STATS["rescued"] = st.get("rescued", 0)
    T3.DETECTION_STATS["pass"] = st["pass"]



def main():
    print(f"実行中のファイル: {os.path.abspath(__file__)}")
    T3.UNET_CKPT = UNET_CKPT
    T3.OUTPUT_FOLDER = OUTPUT_FOLDER
    T3.UNET_INSTANCE_MODE = UNET_INSTANCE_MODE
    image_folder = IMAGE_FOLDER or T3.IMAGE_FOLDER
    bg_path = BACKGROUND_PATH or T3.BACKGROUND_PATH
    T3.IMAGE_FOLDER, T3.BACKGROUND_PATH = image_folder, bg_path
    print(f"  モデル {UNET_CKPT}, 気泡の分け方 \"{UNET_INSTANCE_MODE}\", 事前マスク付きの検出 {PRIOR_PASSES}回 "
          f"(予測元 {PRIOR_FROM}, 観測回数 >= {PRIOR_MIN_HITS}), 出力先 {OUTPUT_FOLDER}")
    if PRIOR_FROM not in ("both", "forward"):
        raise ValueError(f'PRIOR_FROM は "both" / "forward": {PRIOR_FROM!r}')
    T3.unet_instances(np.zeros((3, 8, 8), np.float32))   # 分け方の綴りを最初に確認
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    cache_dir = os.path.join(OUTPUT_FOLDER, "_cache_processed")
    os.makedirs(cache_dir, exist_ok=True)

    print("U-Netモデルをロード中...")
    detector = tau_unet.TauDetector(UNET_CKPT, T3.TRAIN_IMAGE_HW)

    bg_img = cv2.imread(bg_path)
    if bg_img is None and T3.ENABLE_PREPROCESSING:
        raise FileNotFoundError(f"背景画像が見つかりません: {bg_path}")
    image_files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff'):
        image_files.extend(glob.glob(os.path.join(image_folder, ext)))
    image_files = sorted(p for p in set(image_files)
                         if os.path.normcase(os.path.abspath(p)) != os.path.normcase(os.path.abspath(bg_path)))
    if not image_files:
        raise FileNotFoundError(f"'{image_folder}' フォルダに画像がありません。")

    # 前処理の値を最初の1枚で決める (tracker3.py と同じ UI)。読めない画像は除く
    tv, bv, mv = T3.PREPROC_FIXED if T3.PREPROC_FIXED else T3.PREPROC_DEFAULT
    use_ui = T3.ENABLE_PREPROCESSING and T3.PREPROC_FIXED is None
    files, first = [], None
    for p in image_files:
        if cv2.imread(p) is None:
            print(f"  -> {os.path.basename(p)}: 画像の読み込みに失敗、スキップ")
            continue
        if first is None:
            _, first, tv, bv, mv = T3.preprocess_image(p, bg_img, filename=os.path.basename(p), show_ui=use_ui,
                                                       current_thresh_val=tv, current_bright_val=bv,
                                                       current_median_val=mv)
        files.append(p)
    print(f"合計{len(files)}枚の画像。前処理: Noise={tv}, Brightness={bv}, Median={mv}")
    roi_rect = T3.ROI_RECT
    if T3.ENABLE_ROI and roi_rect is None:
        roi_rect = T3.resolve_roi(first)
    h, w = first.shape[:2]
    image_size = (h, w)
    roi_bool = T3.make_roi_mask(h, w, roi_rect if T3.ENABLE_ROI else None).astype(bool)
    names = [os.path.basename(p) for p in files]

    def gray_of(f):
        _, proc, _, _, _ = T3.preprocess_image(files[f], bg_img, show_ui=False, current_thresh_val=tv,
                                               current_bright_val=bv, current_median_val=mv)
        if proc.shape[:2] != image_size:
            raise ValueError(f"{names[f]}: 画像サイズ {proc.shape[:2]} が最初の画像 {image_size} と違います")
        return cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)

    def on_frame0(f, gray, prob, inst, dets):   # パス0: オーバーレイ用の前処理画像を保存、最初のフレームは入力チェック
        cv2.imwrite(os.path.join(cache_dir, names[f]), cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
        if f == 0:
            T3.check_unet_input(gray, prob, inst, detector, names[f])

    def after_pass0(dets):
        if T3.ENABLE_BOOTSTRAP:
            T3.run_bootstrap_calibration(dets, names, cache_dir, image_size)

    debug_dir = os.path.join(OUTPUT_FOLDER, "prior_debug") if SAVE_PRIOR_DEBUG else None
    for d in ("prior_debug", "passes"):   # 前回の実行の残り (パスの数が違うと混ざる) を消す
        shutil.rmtree(os.path.join(OUTPUT_FOLDER, d), ignore_errors=True)
    if debug_dir:
        os.makedirs(debug_dir)
    results = run_passes(len(files), gray_of, detector, roi_bool, image_size, PRIOR_PASSES, names, debug_dir,
                         after_pass0, on_frame0)

    # パスごとの CSV と比較
    pp = {"preprocess": {"noise_cut": tv, "brightness": bv, "median": mv}}
    tau_params = {"UNET_CKPT": UNET_CKPT, "uses_prior": detector.uses_prior, "PRIOR_PASSES": PRIOR_PASSES,
                  "PRIOR_FROM": PRIOR_FROM, "PRIOR_MIN_HITS": PRIOR_MIN_HITS, "prior_edge_px": detector.edge_px,
                  "passes_run": len(results)}
    Q = load_qc_module() if SAVE_PASS_RESULTS else None
    summ = []
    n = len(files)
    roi_q = tuple(roi_rect) if (T3.ENABLE_ROI and roi_rect is not None) else None
    for dets, rows, st in results:
        rows = T3.compute_velocity_ema(rows, n)
        entry = {"pass": st["pass"], "detection": st}
        if SAVE_PASS_RESULTS:
            d = os.path.join(OUTPUT_FOLDER, "passes", f"pass{st['pass']}")
            os.makedirs(d, exist_ok=True)
            T3.write_tracking_csv(os.path.join(d, "result_tracking.csv"), rows, names, dets)
            rep = T3.qc_report(rows, n)
            set_detection_stats(st)
            rep["used_params"] = dict(T3.used_params(roi_rect, pp["preprocess"]), TAU={**tau_params, "pass": st["pass"]})
            with open(os.path.join(d, "qc_report.json"), "w", encoding="utf-8") as fp:
                json.dump(rep, fp, ensure_ascii=False, indent=2)
            if Q is not None:
                entry["qc"] = pass_qc(Q, os.path.join(d, "result_tracking.csv"), roi_q, n)
        summ.append(entry)
    if summ and all("qc" in s for s in summ):
        print_pass_table(summ)
    with open(os.path.join(OUTPUT_FOLDER, "pass_summary.json"), "w", encoding="utf-8") as fp:
        json.dump(summ, fp, ensure_ascii=False, indent=2)

    # 最後のパスを tracker3.py と同じ形式で出力
    dets, rows, st = results[-1]
    total_areas = [float(sum(d.area_in_roi for d in ds)) for ds in dets]
    roi_counts = [sum(1 for d in ds if d.in_roi) for ds in dets]
    tracking_csv_path = os.path.join(OUTPUT_FOLDER, "result_tracking.csv")
    area_csv_path = os.path.join(OUTPUT_FOLDER, "result_area_count.csv")
    T3.write_tracking_csv(tracking_csv_path, rows, names, dets)
    T3.write_area_count_csv(area_csv_path, names, total_areas, roi_counts)
    T3.draw_overlays(cache_dir, OUTPUT_FOLDER, rows, dets, names, total_areas, roi_counts,
                     roi_rect=(roi_rect if T3.ENABLE_ROI else None))
    set_detection_stats(st)
    report = T3.qc_report(rows, n)
    report["used_params"] = dict(T3.used_params(roi_rect, pp["preprocess"]), TAU=tau_params)
    with open(os.path.join(OUTPUT_FOLDER, "qc_report.json"), "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)

    print(f"\n最後のパス (パス{st['pass']}) の結果を保存しました:")
    print(f"  - トラッキング: {tracking_csv_path}")
    print(f"  - 面積・個数:   {area_csv_path}")
    print(f"  - オーバーレイ / qc_report.json: {OUTPUT_FOLDER}")
    if SAVE_PASS_RESULTS:
        print(f"  - パスごとの結果: {os.path.join(OUTPUT_FOLDER, 'passes')}  (3_tracking_qc.py でそれぞれ確認できる)")
    if debug_dir and any(s["detection"].get("debug_saved") for s in summ):
        print(f"  - 検出が変わったフレームの確認画像: {debug_dir}  (左: 事前マスク / 右: 赤 = 前のパスだけ, 緑 = このパスだけ)")
    print("\n全ての処理が完了しました!")


if __name__ == "__main__":
    main()

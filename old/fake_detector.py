"""
偽検出器 (docs/PIV_TASK.md 6-1): U-Net の代わりに、正解ラベル画像から 3クラス確率マップを作る
=====================================================================
  正解ラベル画像 (0=背景, 1..N=気泡) -> fake_prob() -> (3,H,W) 確率 [0 背景 / 1 内部 / 2 境界]
  -> トラッカーの extract_instances (トラッカーの既定値) -> instances_to_detections

U-Net の出力の代わりなので、トラッカー側の「境界を壁として領域分割する」後処理はそのまま通る。
合成データ (sim_piv.py) と回帰テスト (tests/test_events.py) で使う。

確率マップの作り方 (正解ラベルを全件復元できるように調べた結果):
  - 境界 (ch2=1): 各ラベルの内側 1px のリング
      watershed 経路の気泡 (内部が closing 後も残る) : 4近傍に別ラベル/背景がある画素 (8連結リング)。画面端には置かない
      境界の塊経路の小気泡 (内部が closing で消える)  : 8近傍で判定 (4連結リング)。画面端にも置く (fill_holes で閉じるため)
  - 内部 (ch1=1): リング以外のラベル画素
  - 背景: ch0=0.98, ch2=0.02 (内部の ch2=0 より少し高くして、watershed で内部が先にリングを取るようにする)
  - 平滑化なし (平滑化すると watershed の順番が崩れ、小気泡の面積が 1割ほど欠ける)
復元できない (extract_instances 自体の制約):
  - 別の気泡に接している / 1px しか離れていない tiny (r<=4px 程度) -> 消える、または tiny 同士がくっつく
  - 画面端の厚さ 2〜7px の切れ端で面積 > UNET_TINY_MAX -> 消える
"""
import numpy as np
from scipy import ndimage

EPS_BG = 0.02


def _ring(gt: np.ndarray, frame_ring: bool, conn: int) -> np.ndarray:
    """ラベル内の画素で、conn 近傍に別ラベル (背景、frame_ring なら画面外も) がある画素"""
    pad = np.pad(gt, 1, mode="constant", constant_values=-1) if frame_ring else np.pad(gt, 1, mode="edge")
    c = pad[1:-1, 1:-1]
    diff = (pad[:-2, 1:-1] != c) | (pad[2:, 1:-1] != c) | (pad[1:-1, :-2] != c) | (pad[1:-1, 2:] != c)
    if conn == 8:
        diff |= (pad[:-2, :-2] != c) | (pad[:-2, 2:] != c) | (pad[2:, :-2] != c) | (pad[2:, 2:] != c)
    return (gt > 0) & diff


def _main_path_labels(gt: np.ndarray, ring4: np.ndarray, close_it: int) -> np.ndarray:
    """extract_instances の closing (close_it+1 回) の後も内部が残るラベル = watershed 経路"""
    core = ndimage.binary_erosion((gt > 0) & ~ring4, iterations=close_it + 1)
    is_main = np.zeros(int(gt.max()) + 1, bool)
    is_main[np.unique(gt[core])] = True
    is_main[0] = False
    return is_main


def fake_prob(gt: np.ndarray, close_it: int = 2) -> np.ndarray:
    """正解ラベル画像 -> (3,H,W) float32 確率マップ"""
    gt = gt.astype(np.int32)
    inside = gt > 0
    r4 = _ring(gt, False, 4)
    r8 = _ring(gt, True, 8)
    is_main = _main_path_labels(gt, r4, close_it)
    ring = np.where(is_main[gt], r4, r8) & inside
    p = np.zeros((3,) + gt.shape, np.float32)
    bg = ~inside
    p[0][bg] = 1.0 - EPS_BG
    p[2][bg] = EPS_BG
    p[1][inside & ~ring] = 1.0
    p[2][ring] = 1.0
    return p


def overlap_table(gt: np.ndarray, inst: np.ndarray) -> np.ndarray:
    """[正解ラベル, 検出ラベル] の重なり画素数"""
    ng, ni = int(gt.max()), int(inst.max())
    return np.bincount((gt.astype(np.int64) * (ni + 1) + inst).ravel(),
                       minlength=(ng + 1) * (ni + 1)).reshape(ng + 1, ni + 1)


def fake_detect(T, gt: np.ndarray, roi_bool=None):
    """正解ラベル画像 -> (検出リスト, 各検出の正解ラベル, 各検出が含む正解ラベル数)
    T はトラッカーのモジュール (tracker2 / tracker3。extract_instances と instances_to_detections を使う)。
    正解ラベル = 重なり最大の正解。含む正解数 >= 2 は接触した小気泡がくっついた検出。
    検出の欠落は、この関数に渡す前に gt からそのラベルを消して作ること。"""
    p = fake_prob(gt, T.UNET_CLOSE)
    inst = T.extract_instances(p, T.UNET_MIN_AREA, T.UNET_BAND, T.UNET_EDGE_THR, T.UNET_CLOSE, T.UNET_TINY_MAX)
    roi = np.ones(gt.shape, bool) if roi_bool is None else roi_bool
    dets = T.instances_to_detections(inst, roi)
    ov = overlap_table(gt, inst)
    ag = np.maximum(ov.sum(1), 1)
    gt_ids, n_gt = [], []
    for d in dets:
        m, x0, y0 = d.shape
        ys, xs = m.nonzero()
        r = int(inst[y0 + ys[0], x0 + xs[0]])
        col = ov[1:, r]
        gt_ids.append(int(np.argmax(col)) + 1 if col.any() else -1)
        n_gt.append(int(np.sum(col / ag[1:] >= 0.5)))
    return dets, gt_ids, n_gt

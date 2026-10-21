"""
Microgap Bubble Tracking - U-Net版
=====================================================================
microgaptracker3.py の検出部(YOLO)を、1_unet_train.py で学習した U-Net に置き換えたもの。
前処理・ROI・ブートストラップ・CSV/オーバーレイ出力は microgaptracker3.py の構成を引き継ぐ。

処理の流れ:
  1) 前処理(2値化) : 背景差分 -> Median -> Noise Cut -> 明度増幅   ※学習画像と同じ処理
  2) 検出(U-Net)   : 画素ごとに 背景/気泡内部/気泡境界 の確率を出力
                     -> 境界を壁として領域分割 -> 壁で囲まれた領域 = 気泡1個 (画素マスク)
  3) トラッキング   : LeadingEdgeLapTracker
       同一気泡 : 先端部移動・中心X移動・面積変化・形状IoU のコストでハンガリアン法により1対1対応
       合体     : 対応の取れなかったトラックの予測マスクが検出と重なり、
                  「トラックA∪B ≈ 検出X」が Union IoU で確認できた場合
       分裂     : 対応の取れなかった検出が親トラックの予測マスクの中にあり、
                  「親X ≈ 検出A'∪B'」が Union IoU で確認できた場合
  4) 後処理       : 速度(EMA) -> CSV -> オーバーレイ画像 -> QCレポート

microgaptracker3.py からの変更点:
  - ultralytics(YOLO) 不要。torch + segmentation_models_pytorch を使用
  - 形状比較(IoU)をポリゴンではなく画素マスクで計算
  - 合体/分裂の候補探索を「先端部ゲート」から「マスクの重なり」に変更
      前後に並んだ気泡の合体/分裂では、両者の先端部が気泡長だけ離れているため先端部ゲートを通らない。
      旧方式では、合体は後方気泡が見失われてゲートが広がった後に遅れて検出され
      (気泡長が約160pxを超えると検出不可)、前後方向の分裂は「new」と判定されていた
  - 分裂にも合体と同じ Union IoU 検証を追加 (近くに新しく現れた気泡を分裂と誤判定しない)
  - 合体メンバーは直前フレームで観測されたトラックに限定 (同じ気泡の重複トラックを合体と誤判定しない)
  - 3個以上の同時合体・同時分裂に対応
  - 生まれたばかりのトラック(速度未知)は初回のみ先端部ゲートを NEW_TRACK_GATE_SCALE 倍に拡大
  - ブートストラップの位置ゲートに下限 BOOTSTRAP_MIN_JUMP を設定
  - トラッキングCSVの末尾に 周長(px)・フレーム接触 の列を追加
"""

# ------------------------------------------------------------
# パスの設定 (自分の環境に合わせて変更すること)
# ------------------------------------------------------------
UNET_CKPT = r"C:\Users\inoue-2024-01\Desktop\U-net\best.pt"   # U-Netの学習結果 (best.pt)
IMAGE_FOLDER = r"C:\Users\inoue-2024-01\Desktop\U-net\test w0.7 a0.5"                          # 分析する画像があるフォルダ
BACKGROUND_PATH = r"C:\Users\inoue-2024-01\Desktop\U-net\bg2real\image0000000.jpg"  # 背景画像のパス
OUTPUT_FOLDER = r"C:\Users\inoue-2024-01\Desktop\U-net\output"                   # 結果を保存するフォルダ

# 前処理(背景差分 + Noise Cut + Median + 明度増幅)を有効にするか。
# U-Netは2値化済み画像で学習しているので、基本は True のまま。
ENABLE_PREPROCESSING = True

# 前処理パラメータ (Noise Cut, Brightness, Median)。学習画像を作ったときと同じ値にすること。
#   None : 最初のフレームでスライダー調整 (初期値は PREPROC_DEFAULT)
#   固定 : 例) PREPROC_FIXED = (40, 3, 1)  -> スライダーを出さずにこの値を使う (再現性のため推奨)
PREPROC_FIXED = None
PREPROC_DEFAULT = (30, 3, 0)

# 入力チェック: 前処理後の画像は学習画像と同じく「ほぼ黒い背景 + 白い輪郭」でなければならない
MIN_BLACK_FRACTION = 0.7   # 黒画素(<15)の割合がこれ未満なら警告 (学習画像は約0.94)
SAVE_DEBUG_FIRST_FRAME = True   # 最初のフレームの U-Net 入力画像と確率マップを OUTPUT_FOLDER/debug に保存

# ------------------------------------------------------------
# U-Net 検出パラメータ (1_unet_train.py の [3] と同じ値にすること)
# ------------------------------------------------------------
UNET_MIN_AREA = 4       # これより小さい気泡は捨てる (px)
UNET_BAND = 25          # 壁近傍の判定帯の幅 (px)
UNET_EDGE_THR = 0.5     # 境界確率のしきい値
UNET_CLOSE = 2          # 境界の途切れを塞ぐ closing 回数
UNET_TINY_MAX = 300     # 境界の塊として拾う小気泡の最大面積 (px)
TRAIN_IMAGE_HW = None   # 学習画像のサイズ (H, W)。best.pt に記録があればそちらを使う。
                        # 古い best.pt で、撮影画像と学習画像のサイズが違う場合のみ指定。例: (1080, 416)
SAVE_INSTANCE_MASKS = False  # True ならフレームごとの気泡ラベルマップを OUTPUT_FOLDER/instances/*.npz に保存

# ------------------------------------------------------------
# ROI (関心領域) 設定
#   - 検出とトラッキングは画面全体で実行
#   - 「合計面積」は各気泡マスクがROIと重なる部分のピクセルのみ合算
#   - 「個数」はROIに少しでもかかった気泡を1個としてカウント
# ------------------------------------------------------------
ENABLE_ROI = True    # Falseなら画面全体基準
ROI_RECT = None      # Noneなら最初のフレームでマウスドラッグで選択。
                     # 再現性が必要なら (x, y, w, h) タプルで固定。例: ROI_RECT = (100, 200, 400, 600)
ROI_SAVE_PATH = None # 選択したROIを保存/再利用するファイルパス。NoneならOUTPUT_FOLDER/roi_saved.jsonを使用

# ------------------------------------------------------------
# トラッキングパラメータ（気泡のスケール・撮影fpsに合わせて調整すること）
# ------------------------------------------------------------
LEADING_EDGE_PERCENTILE = 5.0
MAX_LEADING_EDGE_JUMP = 40.0
MAX_CENTER_X_JUMP = 30.0
AREA_RATIO_GATE = 3.0
MAX_AGE = 3
VELOCITY_EMA_ALPHA = 0.5
IOU_COST_WEIGHT = 20.0           # 形状IoU項の重み
MERGE_UNION_IOU_THRESHOLD = 0.6  # 合体の確定しきい値: Union(合体前のトラック群) と 合体後の検出 のIoU
SPLIT_UNION_IOU_THRESHOLD = 0.6  # 分裂の確定しきい値: 分裂前の親 と Union(分裂後の検出群) のIoU
EVENT_OVERLAP_MIN = 0.3          # 合体/分裂の候補条件: 小さい側の面積のうち、相手と重なっている割合の下限
NEW_TRACK_GATE_SCALE = 2.0       # 生まれたばかりのトラック(速度未知)の先端部ゲート倍率。1.0なら microgaptracker3.py と同じ

# --- 追跡の改良 (小さい気泡が隣へ乗り移るのを防ぐ) ---
USE_FLOW_PRIOR = True        # 新しく現れた気泡の初速度を、周りで追跡中の気泡の速度(中央値)から推定する (False なら 0 から開始)
FLOW_PRIOR_RADIUS = 150.0    # 「周り」とみなす半径 (px)
SPACING_GATE_FRAC = 0.7      # 予測位置と検出の距離が「その検出から一番近い別の気泡までの距離 × この値」以下のときだけ対応させる
                             # = 隣の気泡より確実に近いときだけつなぐ。曖昧なら乗り移らずに途切れさせる。0 で無効
COAST_GATE_GROWTH = 0.5      # 見失っている間、1フレームごとにゲートを何倍ずつ広げるか (旧版は 1.0)
SHAPE_AREA_REF = 300.0       # 面積がこれより小さい気泡では形状IoUの重みを面積に比例して下げる (小さい気泡は形がどれも似ているため)

# ------------------------------------------------------------
# 自動ブートストラップキャリブレーション設定
# ------------------------------------------------------------
ENABLE_BOOTSTRAP = True       # Trueなら本トラッキング前にパラメータ自動算出 + ユーザー承認ステップを経る
BOOTSTRAP_NUM_SEGMENTS = 20   # 映像全体を何等分して均等サンプリングするか
BOOTSTRAP_PERCENTILE = 90    # 移動量/面積比分布の何パーセンタイルを基準にゲートを決めるか(外れ値防御)
BOOTSTRAP_JUMP_MARGIN = 1.2  # 位置ゲートの安全係数 (パーセンタイル値 × この値)
BOOTSTRAP_AREA_MARGIN = 1.1  # 面積比ゲートの安全係数
BOOTSTRAP_MIN_JUMP = 5.0     # 位置ゲートの下限(px)。移動が非常に安定していてもゲートが0近くに潰れないように
BOOTSTRAP_LOOSE_Y_GATE = 120.0  # 仮マッチング用の緩い初期ゲート(本ゲートより広め → 循環問題の回避)
BOOTSTRAP_LOOSE_X_GATE = 100.0
BOOTSTRAP_LOOSE_AREA_GATE = 6.0
BOOTSTRAP_PREVIEW_FRAMES = 4  # 承認画面に表示するサンプルオーバーレイのフレーム数


import cv2
import math
import numpy as np
import os
import glob
import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import watershed

Shape = Tuple[np.ndarray, int, int]   # (bboxで切り出したboolマスク, x0, y0)


# ==============================================================
# 1. 前処理 (microgaptracker3.py と同一。UI調整は最初の1枚のみ)
# ==============================================================
def preprocess_image(img_path, bg_img, filename="Image", show_ui=False,
                      current_thresh_val=30, current_bright_val=3, current_median_val=0):
    img = cv2.imread(img_path)
    if img is None:
        return None, None, current_thresh_val, current_bright_val, current_median_val

    if not ENABLE_PREPROCESSING:
        return img, img.copy(), current_thresh_val, current_bright_val, current_median_val

    if img.shape != bg_img.shape:
        bg_img_resized = cv2.resize(bg_img, (img.shape[1], img.shape[0]))
    else:
        bg_img_resized = bg_img

    diff = cv2.absdiff(img, bg_img_resized)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    final_thresh = current_thresh_val
    final_bright = current_bright_val
    final_median = current_median_val

    if show_ui:
        hist = cv2.calcHist([gray_diff], [0], None, [256], [0, 256])
        hist_img_base = np.zeros((256, 256, 3), dtype=np.uint8)
        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
        for x, y in enumerate(hist):
            cv2.line(hist_img_base, (x, 256), (x, 256 - int(y.item())), (200, 200, 200), 1)

        window_name = f"Preview - {filename} (Adjust Sliders & Press ENTER)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        def update_preview(*args):
            th = cv2.getTrackbarPos("Noise Cut", window_name)
            br = cv2.getTrackbarPos("Brightness", window_name)
            md = cv2.getTrackbarPos("Median Filter", window_name)
            if br < 1:
                br = 1
            ksize = md * 2 + 1
            preview_blur = cv2.medianBlur(gray_diff, ksize)
            _, preview_clean = cv2.threshold(preview_blur, th, 255, cv2.THRESH_TOZERO)
            preview_bright = cv2.convertScaleAbs(preview_clean, alpha=br, beta=0)
            temp_hist = hist_img_base.copy()
            cv2.line(temp_hist, (th, 0), (th, 256), (0, 0, 255), 2)
            cv2.imshow("Histogram", temp_hist)
            preview_bgr = cv2.cvtColor(preview_bright, cv2.COLOR_GRAY2BGR)
            cv2.imshow(window_name, preview_bgr)

        cv2.createTrackbar("Noise Cut", window_name, current_thresh_val, 100, update_preview)
        cv2.createTrackbar("Brightness", window_name, current_bright_val, 10, update_preview)
        cv2.createTrackbar("Median Filter", window_name, current_median_val, 5, update_preview)
        update_preview()
        print(f"{filename}: ヒストグラム, 明るさ, Medianフィルターを調整してENTERを押してください.")

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key in [13, 32]:
                break

        final_thresh = cv2.getTrackbarPos("Noise Cut", window_name)
        final_bright = cv2.getTrackbarPos("Brightness", window_name)
        final_median = cv2.getTrackbarPos("Median Filter", window_name)
        if final_bright < 1:
            final_bright = 1
        cv2.destroyWindow(window_name)
        try:
            cv2.destroyWindow("Histogram")
        except Exception:
            pass

    ksize_final = final_median * 2 + 1
    blur_diff = cv2.medianBlur(gray_diff, ksize_final)
    _, clean_diff = cv2.threshold(blur_diff, final_thresh, 255, cv2.THRESH_TOZERO)
    bright_diff = cv2.convertScaleAbs(clean_diff, alpha=final_bright, beta=0)
    processed_img = cv2.cvtColor(bright_diff, cv2.COLOR_GRAY2BGR)

    return img, processed_img, final_thresh, final_bright, final_median


# ==============================================================
# 2. U-Net 検出
# ==============================================================
class UNetDetector:
    """best.pt を読み込み、画素ごとの 背景/内部/境界 確率 (3, H, W) を返す。"""

    def __init__(self, ckpt_path, train_hw=None):
        import torch
        import segmentation_models_pytorch as smp
        self.torch = torch
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        ck = torch.load(ckpt_path, map_location=self.dev)
        self.model = smp.Unet(ck["encoder"], encoder_weights=None,
                              in_channels=3, classes=ck["classes"]).to(self.dev)
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()
        self.mean = np.array(ck["mean"], np.float32)
        self.std = np.array(ck["std"], np.float32)
        hw = ck.get("train_hw") or train_hw
        self.train_hw = (int(hw[0]), int(hw[1])) if hw else None
        self._resize_notice = False
        print(f"  U-Net: {ckpt_path}  (epoch {ck.get('epoch')}, device {self.dev}, "
              f"学習画像サイズ {self.train_hw if self.train_hw else '記録なし'})")
        if self.dev == "cpu":
            print("  ※ GPUが見つかりません。CPUでも動きますが遅くなります。")

    def _forward(self, gray):
        torch = self.torch
        H, W = gray.shape
        ph, pw = (-H) % 32, (-W) % 32
        g = cv2.copyMakeBorder(gray, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
        x = np.stack([g] * 3, -1).astype(np.float32) / 255.0
        x = (x - self.mean) / self.std
        x = torch.from_numpy(x).permute(2, 0, 1)[None].to(self.dev)
        with torch.no_grad():
            p = self.model(x).softmax(1)[0].cpu().numpy()
        return p[:, :H, :W]

    def prob(self, gray):
        H, W = gray.shape
        if self.train_hw is None or (H, W) == self.train_hw:
            return self._forward(gray)
        # 撮影画像と学習画像のサイズが違う → 学習サイズに合わせて推論し、確率マップを元のサイズに戻す
        th, tw = self.train_hw
        if not self._resize_notice:
            print(f"  ※ 画像サイズ {H}x{W} が学習画像 {th}x{tw} と異なるため、学習サイズに合わせて推論します")
            self._resize_notice = True
        interp = cv2.INTER_AREA if th * tw < H * W else cv2.INTER_LINEAR
        p = self._forward(cv2.resize(gray, (tw, th), interpolation=interp))
        return np.stack([cv2.resize(c, (W, H), interpolation=cv2.INTER_LINEAR) for c in p])


def extract_instances(prob, min_area=4, band=25, edge_thr=0.5, close_it=2, tiny_max=300):
    """確率マップ (3,H,W) -> 気泡ラベルマップ (0=なし, 1..N=気泡)
    1) 境界(class 2)を壁として領域分割。フレーム端も壁とする -> 画面で切れた気泡の領域も閉じる
    2) 領域の判定: 壁近傍の帯で 内部確率 > 背景確率 なら気泡
    3) watershed で境界画素を隣接領域に配分
    4) 内部画素が残らなかった小気泡: 閉じた境界の塊を塗りつぶして気泡とする
    """
    H, W = prob.shape[1:]
    edge_raw = prob[2] > edge_thr

    p = close_it + 3                                       # closing がフレーム端の壁を削らないよう余白
    ep = np.pad(edge_raw, p, constant_values=True)
    if close_it > 0:
        ep = ndimage.binary_closing(ep, iterations=close_it + 1)
    ep = ep[p - 1:-(p - 1), p - 1:-(p - 1)]                # 1px の外枠だけ残す
    ep[0, :] = ep[-1, :] = ep[:, 0] = ep[:, -1] = True
    lab, n = ndimage.label(~ep)
    lab = lab[1:-1, 1:-1]
    edge = ep[1:-1, 1:-1]

    inst = np.zeros((H, W), np.int32)
    k = 0
    if n > 0:
        wall_band = ndimage.binary_dilation(edge, iterations=band)
        size = np.bincount(lab.ravel(), minlength=n + 1)
        lb = lab[wall_band]
        cnt = np.bincount(lb, minlength=n + 1)
        s_in = np.bincount(lb, weights=prob[1][wall_band].astype(np.float64), minlength=n + 1)
        s_bg = np.bincount(lb, weights=prob[0][wall_band].astype(np.float64), minlength=n + 1)
        ok = (size >= min_area) & (cnt > 0) & (s_in > s_bg)
        ok[0] = False
        keep = np.nonzero(ok)[0]
        if keep.size:
            ws = watershed(prob[2], markers=lab)
            lut = np.zeros(n + 1, np.int32)
            lut[keep] = np.arange(1, keep.size + 1, dtype=np.int32)
            inst = lut[ws]
            k = int(keep.size)

    assigned = inst > 0
    near_assigned = ndimage.binary_dilation(assigned, iterations=2)
    comp, nc = ndimage.label(edge_raw & ~assigned)         # closing 前の境界を使う (角の残骸を拾わない)
    for ci, sl in enumerate(ndimage.find_objects(comp), start=1):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, H)
        x0, x1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, W)
        c = comp[y0:y1, x0:x1] == ci
        if (c & near_assigned[y0:y1, x0:x1]).any():         # 大きい気泡のリングの外側半分 -> 除外
            continue
        filled = ndimage.binary_fill_holes(c)
        a = int(filled.sum())
        if a < min_area or a > tiny_max:
            continue
        k += 1
        inst[y0:y1, x0:x1][filled] = k
    return inst


# ==============================================================
# 3. 検出データ構造
# ==============================================================
@dataclass
class Detection:
    shape: Shape              # (boolマスク, x0, y0)。形状IoU・合体/分裂判定用
    contours: list            # 画像座標の輪郭 (描画用。成分ごとに別々に描く)
    area: float               # 全体面積 (トラッキングのゲート/コスト用 - ROIと無関係に維持)
    cx: float
    cy: float
    leading_x: float
    leading_y: float
    perimeter: float = 0.0    # 輪郭長 (px)
    touches_frame: bool = False  # 画面端に接している (切れた気泡: 面積・周長は不完全)
    conf: float = 1.0
    area_in_roi: float = 0.0  # ROIと重なる部分の面積 (統計用)
    in_roi: bool = True       # ROIに少しでもかかっているか (個数カウント用)


def leading_edge_from_points(pts: np.ndarray, percentile: float = LEADING_EDGE_PERCENTILE):
    """輪郭点のうち上側(yが小さい)percentile%の平均 = 先端部"""
    n = max(3, int(len(pts) * percentile / 100.0))
    top = pts[np.argsort(pts[:, 1])[:n]]
    return float(np.mean(top[:, 0])), float(np.mean(top[:, 1]))


def instances_to_detections(inst: np.ndarray, roi_bool: np.ndarray) -> List[Detection]:
    H, W = inst.shape
    dets: List[Detection] = []
    for k, sl in enumerate(ndimage.find_objects(inst), start=1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        m = inst[y0:y1, x0:x1] == k
        area = int(np.count_nonzero(m))
        if area == 0:
            continue
        ys, xs = np.nonzero(m)
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,
                                 offset=(x0, y0))
        pts = np.vstack([c.reshape(-1, 2) for c in cs]).astype(np.float64)
        lx, ly = leading_edge_from_points(pts)
        per = float(sum(cv2.arcLength(c, True) for c in cs))
        a_roi = float(np.count_nonzero(m & roi_bool[y0:y1, x0:x1]))
        dets.append(Detection(
            shape=(m, x0, y0), contours=cs, area=float(area),
            cx=float(xs.mean() + x0), cy=float(ys.mean() + y0),
            leading_x=lx, leading_y=ly, perimeter=per,
            touches_frame=bool(y0 == 0 or x0 == 0 or y1 == H or x1 == W),
            area_in_roi=a_roi, in_roi=a_roi > 0,
        ))
    return dets


# ==============================================================
# 4. 形状比較 (画素マスク)
# ==============================================================
def overlap_px(a: Shape, b: Shape) -> int:
    """2つのマスクの重なり画素数"""
    ma, ax, ay = a
    mb, bx, by = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1 = min(ax + ma.shape[1], bx + mb.shape[1])
    y1 = min(ay + ma.shape[0], by + mb.shape[0])
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(np.count_nonzero(ma[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & mb[y0 - by:y1 - by, x0 - bx:x1 - bx]))


def group_iou(shapes_a: List[Shape], shift: Tuple[float, float], shapes_b: List[Shape]) -> float:
    """「shapes_a の和集合を shift だけ平行移動したもの」と「shapes_b の和集合」の IoU。
    1対1 (形状維持の確認)、多対1 (合体の確認)、1対多 (分裂の確認) をすべてこれで計算する。
    2つの和集合を囲む小さなキャンバスだけで計算するので軽い。"""
    if not shapes_a or not shapes_b:
        return 0.0
    sx, sy = int(round(shift[0])), int(round(shift[1]))
    a_list = [(m, x + sx, y + sy) for m, x, y in shapes_a]
    allsh = a_list + list(shapes_b)
    X0 = min(x for _, x, _ in allsh)
    Y0 = min(y for _, _, y in allsh)
    X1 = max(x + m.shape[1] for m, x, _ in allsh)
    Y1 = max(y + m.shape[0] for m, _, y in allsh)
    W, H = X1 - X0, Y1 - Y0
    if W <= 0 or H <= 0 or W > 4000 or H > 4000:
        return 0.0
    ua = np.zeros((H, W), bool)
    ub = np.zeros((H, W), bool)
    for m, x, y in a_list:
        ua[y - Y0:y - Y0 + m.shape[0], x - X0:x - X0 + m.shape[1]] |= m
    for m, x, y in shapes_b:
        ub[y - Y0:y - Y0 + m.shape[0], x - X0:x - X0 + m.shape[1]] |= m
    inter = int(np.count_nonzero(ua & ub))
    union = int(np.count_nonzero(ua | ub))
    return inter / union if union else 0.0


def compute_motion_compensated_iou(prev_shape: Optional[Shape], curr_shape: Optional[Shape],
                                   shift_x: float, shift_y: float) -> float:
    """トラックの前回マスクを「この検出が正解と仮定した実測移動量」(検出中心 - 前回中心)だけ平行移動して IoU を計算。
    予測移動量を使わないのは、予測が外れると同一物体でも形がずれて見え、形状比較が汚れるため。
    形を保ったまま移動しただけなら IoU は高く、合体/分裂のように形自体が急変すると低くなる。"""
    if prev_shape is None or curr_shape is None:
        return 0.5  # 履歴のないトラックにはペナルティもボーナスも与えない(中立値)
    return group_iou([prev_shape], (shift_x, shift_y), [curr_shape])


def _weighted_center(items):
    """[(面積, cx, cy), ...] の面積加重中心"""
    tot = sum(a for a, _, _ in items)
    if tot <= 0:
        return items[0][1], items[0][2]
    return (sum(a * x for a, x, _ in items) / tot, sum(a * y for a, _, y in items) / tot)


def merge_union_iou(tracks, det) -> float:
    """合体の検証: Union(トラック群の前回マスク) ≈ 合体後の検出 か。
    各トラックを個別に検出中心へ合わせると元の相対配置(並んで接した状態)が崩れるので、
    トラック群の面積加重中心 -> 検出中心 の「共通移動量ひとつ」を全体に適用する。"""
    gx, gy = _weighted_center([(t.area, t.cx, t.cy) for t in tracks])
    return group_iou([t.shape for t in tracks], (det.cx - gx, det.cy - gy), [det.shape])


def split_union_iou(parent, child_dets) -> float:
    """分裂の検証: 親の前回マスク ≈ Union(分裂後の検出群) か (合体の逆)。"""
    gx, gy = _weighted_center([(d.area, d.cx, d.cy) for d in child_dets])
    return group_iou([parent.shape], (gx - parent.cx, gy - parent.cy), [d.shape for d in child_dets])


# ==============================================================
# 5. LAPトラッカー (ハンガリアン法 + 合体/分裂)
# ==============================================================
@dataclass
class Track:
    track_id: int
    leading_x: float
    leading_y: float
    cx: float
    cy: float
    area: float
    shape: Optional[Shape] = None  # 直近でマッチした検出のマスク
    vy: float = 0.0
    hits: int = 1
    time_since_update: int = 0
    first_frame: int = 0
    last_frame: int = 0
    parent_ids: List[int] = field(default_factory=list)

    def predict_leading_y(self) -> float:
        return self.leading_y + self.vy * (self.time_since_update + 1)

    def predicted_shape(self) -> Optional[Shape]:
        """前回マスクを先端部速度で y 方向に移動した予測マスク (合体/分裂の候補探索用)"""
        if self.shape is None:
            return None
        m, x0, y0 = self.shape
        return (m, x0, y0 + int(round(self.vy * (self.time_since_update + 1))))


def _overlap_frac(a: Shape, area_a: float, b: Shape, area_b: float) -> float:
    """小さい側の面積のうち、相手と重なっている割合"""
    if a is None or b is None:
        return 0.0
    ov = overlap_px(a, b)
    return ov / max(1.0, min(area_a, area_b)) if ov else 0.0


class LeadingEdgeLapTracker:
    """フレーム間対応付け。
      同一気泡 : ハンガリアン法 (コスト = 先端部移動 + 中心X移動 + 面積変化 + 形状IoU、ゲート付き)
      合体     : 対応なしトラックの予測マスクが検出と重なる -> Union IoU で「A∪B ≈ X」を確認
      分裂     : 対応なし検出が親トラックの予測マスク内にある -> Union IoU で「X ≈ A'∪B'」を確認
    """

    def __init__(self):
        self.tracks: List[Track] = []
        self._next_id = 1

    def _new_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def update(self, detections: List[Detection], frame_idx: int) -> List[dict]:
        active = [t for t in self.tracks if t.time_since_update <= MAX_AGE]
        n_t, n_d = len(active), len(detections)

        # ---- 1) 同一気泡: コスト行列 + ハンガリアン法 (microgaptracker3.py と同じ) ----
        valid = np.zeros((n_t, n_d), dtype=bool)
        cost = np.full((n_t, n_d), 1e6)

        # 各検出から、同じフレームで一番近い別の気泡までの距離 (中心間)
        nn_dist = np.full(n_d, np.inf)
        if n_d >= 2:
            dxy = np.array([[d.cx, d.cy] for d in detections])
            dm = np.hypot(dxy[:, None, 0] - dxy[None, :, 0], dxy[:, None, 1] - dxy[None, :, 1])
            np.fill_diagonal(dm, np.inf)
            nn_dist = dm.min(axis=1)

        for i, t in enumerate(active):
            pred_y = t.predict_leading_y()
            gate = MAX_LEADING_EDGE_JUMP * (1 + COAST_GATE_GROWTH * t.time_since_update)
            if t.hits == 1 and not t.parent_ids:   # 速度がまだ実測されていない -> 初回だけゲートを広げる
                gate *= NEW_TRACK_GATE_SCALE
            for j, d in enumerate(detections):
                dy = abs(pred_y - d.leading_y)
                dx = abs(t.cx - d.cx)
                area_ratio = max(t.area, d.area) / max(1.0, min(t.area, d.area))
                if dy > gate or dx > MAX_CENTER_X_JUMP or area_ratio > AREA_RATIO_GATE:
                    continue
                if SPACING_GATE_FRAC > 0 and np.isfinite(nn_dist[j]) and not d.touches_frame:
                    # 隣の気泡より確実に近いときだけ: 予測位置がこの検出と隣の気泡の中間より手前にあること
                    # (画面端で切れている気泡は見えている部分の中心が不規則に動くので対象外。計測範囲外でもある)
                    if math.hypot(dx, dy) > max(3.0, SPACING_GATE_FRAC * nn_dist[j]):
                        continue
                valid[i, j] = True
                iou = compute_motion_compensated_iou(t.shape, d.shape, d.cx - t.cx, d.cy - t.cy)
                w_shape = IOU_COST_WEIGHT * min(1.0, min(t.area, d.area) / SHAPE_AREA_REF)
                cost[i, j] = (dy + 0.5 * dx
                              + 5.0 * abs(t.area - d.area) / max(t.area, d.area, 1.0)
                              + w_shape * (1.0 - iou))

        det_to_track: Dict[int, int] = {}
        if n_t and n_d:
            row_ind, col_ind = linear_sum_assignment(cost)
            for i, j in zip(row_ind, col_ind):
                if valid[i, j]:
                    det_to_track[j] = i
        primary_t = set(det_to_track.values())

        # ---- 2) 合体: 対応なしトラック i の予測マスクが、どの検出に最も重なるか ----
        # 合体の構成メンバーは全員「直前フレームで観測されたトラック」に限る。
        # 同じフレームの検出同士は重ならない = 確実に別々の気泡なので、
        # 同じ気泡の古い重複トラック(ID途切れの残り)を「合体」と誤判定しない。
        cand_by_det: Dict[int, List[Tuple[float, int]]] = defaultdict(list)
        for i, t in enumerate(active):
            if i in primary_t or t.time_since_update != 0:
                continue
            ps = t.predicted_shape()
            best = None
            for j, d in enumerate(detections):
                f = _overlap_frac(ps, t.area, d.shape, d.area)
                if f >= EVENT_OVERLAP_MIN and (best is None or f > best[0]):
                    best = (f, j)
            if best:
                cand_by_det[best[1]].append((best[0], i))   # 検出j -> [(重なり割合, トラックi), ...]

        merge_map: Dict[int, List[int]] = {}   # 検出j -> 吸収されたトラックの index
        for j, cands in cand_by_det.items():
            d = detections[j]
            if j in det_to_track and active[det_to_track[j]].time_since_update != 0:
                continue   # 主トラックが直前フレームで未観測 -> 位置の時刻が揃わないので判定しない
            cands.sort(reverse=True)
            group = [det_to_track[j]] if j in det_to_track else []
            base = merge_union_iou([active[k] for k in group], d) if group else 0.0
            for _, i in cands:
                trial = group + [i]
                v = merge_union_iou([active[k] for k in trial], d)
                # 主トラックがない検出では最初の1個は無条件に仮採用 (1個だけでは合体ではないので最後に2個以上を要求)
                if not group or v > base:
                    group, base = trial, v
            if len(group) >= 2 and base >= MERGE_UNION_IOU_THRESHOLD:
                if j in det_to_track:
                    primary = det_to_track[j]
                else:   # ハンガリアン法で対応しなかった合体塊 -> 最大のトラックのIDを継承
                    primary = max(group, key=lambda k: active[k].area)
                    det_to_track[j] = primary
                merge_map[j] = [k for k in group if k != primary]

        absorbed_t = {k for ks in merge_map.values() for k in ks}
        merge_primary_t = {det_to_track[j] for j in merge_map}

        # ---- 3) 分裂: 対応なし検出 j が、どの親トラックの予測マスクの中にあるか ----
        claimed_d = set(det_to_track.keys())
        parents_ok = [i for i in range(n_t)
                      if i not in absorbed_t and i not in merge_primary_t]
        cand_by_parent: Dict[int, List[Tuple[float, int]]] = defaultdict(list)
        for j, d in enumerate(detections):
            if j in claimed_d:
                continue
            best = None
            for i in parents_ok:
                t = active[i]
                f = _overlap_frac(t.predicted_shape(), t.area, d.shape, d.area)
                if f >= EVENT_OVERLAP_MIN and (best is None or f > best[0]):
                    best = (f, i)
            if best:
                cand_by_parent[best[1]].append((best[0], j))

        track_to_det = {i: j for j, i in det_to_track.items()}
        split_map: Dict[int, int] = {}        # 新しい検出j -> 親トラックの index
        hold_v_d = set()                      # 速度更新を保留する検出 (親が1対1対応しなかった分裂の継承側)
        for i, cands in cand_by_parent.items():
            t = active[i]
            cands.sort(reverse=True)
            primary_j = track_to_det.get(i)
            children = [primary_j] if primary_j is not None else []
            base = split_union_iou(t, [detections[c] for c in children]) if children else 0.0
            for _, j in cands:
                trial = children + [j]
                v = split_union_iou(t, [detections[c] for c in trial])
                if not children or v > base:
                    children, base = trial, v
            if len(children) >= 2 and base >= SPLIT_UNION_IOU_THRESHOLD:
                if primary_j is None:   # 親がハンガリアン法で対応しなかった -> 最大の子が親のIDを継承
                    heir = max(children, key=lambda c: detections[c].area)
                    det_to_track[heir] = i
                    hold_v_d.add(heir)
                    primary_j = heir
                for c in children:
                    if c != primary_j:
                        split_map[c] = i

        # ---- 4) 結果の記録・トラック更新 ----
        frame_rows: List[dict] = []

        for j, i in det_to_track.items():
            t = active[i]
            d = detections[j]
            absorbed = merge_map.get(j, [])
            event = "merge" if absorbed else "normal"
            parent_ids = [active[k].track_id for k in absorbed]
            hold_v = bool(absorbed) or (j in hold_v_d)

            new_vy = t.vy   # 合体直後などは速度更新を保留 (形状の過渡期)
            if not hold_v:
                new_vy = VELOCITY_EMA_ALPHA * t.vy + (1 - VELOCITY_EMA_ALPHA) * (d.leading_y - t.leading_y)

            t.leading_x, t.leading_y = d.leading_x, d.leading_y
            t.cx, t.cy = d.cx, d.cy
            t.area = d.area
            t.shape = d.shape
            t.vy = new_vy
            t.hits += 1
            t.time_since_update = 0
            t.last_frame = frame_idx

            frame_rows.append({
                "det_index": j, "track_id": t.track_id, "event": event,
                "parent_ids": parent_ids, "leading_x": t.leading_x, "leading_y": t.leading_y,
                "cx": t.cx, "cy": t.cy, "area": t.area, "vy": t.vy, "hold_v": j in hold_v_d,
            })

        merged_away_ids = set()
        for j, absorbed in merge_map.items():
            primary_id = active[det_to_track[j]].track_id
            for i in absorbed:
                t = active[i]
                merged_away_ids.add(t.track_id)
                frame_rows.append({
                    "det_index": None, "track_id": t.track_id, "event": f"merged_into_{primary_id}",
                    "parent_ids": [], "leading_x": t.leading_x, "leading_y": t.leading_y,
                    "cx": t.cx, "cy": t.cy, "area": 0.0, "vy": float("nan"),
                })

        for j, i in split_map.items():
            parent = active[i]
            d = detections[j]
            new_track = Track(
                track_id=self._new_id(), leading_x=d.leading_x, leading_y=d.leading_y,
                cx=d.cx, cy=d.cy, area=d.area, shape=d.shape, vy=parent.vy,
                hits=1, time_since_update=0, first_frame=frame_idx, last_frame=frame_idx,
                parent_ids=[parent.track_id],
            )
            self.tracks.append(new_track)
            frame_rows.append({
                "det_index": j, "track_id": new_track.track_id, "event": "split",
                "parent_ids": [parent.track_id], "leading_x": new_track.leading_x,
                "leading_y": new_track.leading_y, "cx": new_track.cx, "cy": new_track.cy,
                "area": new_track.area, "vy": new_track.vy,
            })

        # 周りで追跡中の気泡の速度 (今フレームで対応が取れ、3回以上観測されたトラック)
        est = [(t.cx, t.cy, t.vy) for t in self.tracks if t.time_since_update == 0 and t.hits >= 3]

        def flow_prior(x, y):
            if not USE_FLOW_PRIOR or not est:
                return 0.0
            near = [vy for (ex, ey, vy) in est if math.hypot(ex - x, ey - y) <= FLOW_PRIOR_RADIUS]
            return float(np.median(near if near else [vy for _, _, vy in est]))

        claimed_d = set(det_to_track.keys()) | set(split_map.keys())
        for j, d in enumerate(detections):
            if j in claimed_d:
                continue
            new_track = Track(
                track_id=self._new_id(), leading_x=d.leading_x, leading_y=d.leading_y,
                cx=d.cx, cy=d.cy, area=d.area, shape=d.shape, vy=flow_prior(d.cx, d.cy),
                hits=1, time_since_update=0, first_frame=frame_idx, last_frame=frame_idx,
                parent_ids=[],
            )
            self.tracks.append(new_track)
            frame_rows.append({
                "det_index": j, "track_id": new_track.track_id, "event": "new",
                "parent_ids": [], "leading_x": new_track.leading_x, "leading_y": new_track.leading_y,
                "cx": new_track.cx, "cy": new_track.cy, "area": new_track.area, "vy": new_track.vy,
            })

        consumed_t = set(det_to_track.values()) | absorbed_t
        for i in range(n_t):
            if i not in consumed_t:
                active[i].time_since_update += 1

        self.tracks = [
            t for t in self.tracks
            if t.track_id not in merged_away_ids and t.time_since_update <= MAX_AGE
        ]
        return frame_rows


def run_laptrack(detections_per_frame: List[List[Detection]]) -> Dict[int, List[dict]]:
    tracker = LeadingEdgeLapTracker()
    rows_by_frame: Dict[int, List[dict]] = {}
    for frame_idx, dets in enumerate(detections_per_frame):
        rows_by_frame[frame_idx] = tracker.update(dets, frame_idx)
    return rows_by_frame


# ==============================================================
# 6. 速度計算(EMA)
# ==============================================================
def compute_velocity_ema(rows_by_frame: Dict[int, List[dict]], total_frames: int) -> Dict[int, List[dict]]:
    track_history: Dict[int, List[Tuple[int, dict]]] = defaultdict(list)
    for f in range(total_frames):
        for row in rows_by_frame.get(f, []):
            if row["det_index"] is None:
                continue
            track_history[row["track_id"]].append((f, row))

    for track_id, hist in track_history.items():
        hist.sort(key=lambda x: x[0])
        prev_vy = None       # 旧版は 0 から始めていたため、最初の数フレームの速度が小さく出ていた
        prev_leading_y = None
        prev_frame = None
        for f, row in hist:
            if prev_leading_y is None:
                row["vy"] = float("nan")
            elif row["event"] in ("merge", "split") or row.get("hold_v"):
                row["vy"] = prev_vy if prev_vy is not None else float("nan")  # 合体/分裂直後は速度更新を保留
            else:
                dt = max(f - prev_frame, 1)
                raw_v = (row["leading_y"] - prev_leading_y) / dt
                row["vy"] = raw_v if prev_vy is None else VELOCITY_EMA_ALPHA * prev_vy + (1 - VELOCITY_EMA_ALPHA) * raw_v
            if row["vy"] == row["vy"]:
                prev_vy = row["vy"]
            prev_leading_y = row["leading_y"]
            prev_frame = f
    return rows_by_frame


# ==============================================================
# 7. QCレポート (今回の実行結果の健全性チェック用)
# ==============================================================
def qc_report(rows_by_frame: Dict[int, List[dict]], total_frames: int) -> dict:
    track_history: Dict[int, List[Tuple[int, dict]]] = defaultdict(list)
    for f in range(total_frames):
        for row in rows_by_frame.get(f, []):
            if row["det_index"] is None:
                continue
            track_history[row["track_id"]].append((f, row))

    num_tracks = len(track_history)
    lengths = [len(h) for h in track_history.values()]
    avg_track_length = float(np.mean(lengths)) if lengths else 0.0
    all_rows = [r for f in range(total_frames) for r in rows_by_frame.get(f, [])]
    return {
        "num_tracks": num_tracks,
        "avg_track_length_frames": round(avg_track_length, 2),
        "merge_events": sum(1 for r in all_rows if r["event"] == "merge"),
        "split_events": sum(1 for r in all_rows if r["event"] == "split"),
        "new_events": sum(1 for r in all_rows if r["event"] == "new"),
    }


# ==============================================================
# 8. 出力(CSV / オーバーレイ画像)
# ==============================================================
EVENT_COLORS = {
    "normal": (0, 255, 0), "new": (0, 255, 255),
    "merge": (0, 128, 255), "split": (255, 128, 0),
}


def write_tracking_csv(csv_path: str, rows_by_frame: Dict[int, List[dict]], filenames: List[str],
                        detections_per_frame: List[List[Detection]]):
    """トラッキング専用CSV: 気泡ごとのID/イベント/位置/速度。
    列は microgaptracker3.py と同じ順で、末尾に 周長(px)・フレーム接触 を追加。"""
    out_dir = os.path.dirname(csv_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["ファイル名", "フレーム", "トラックID", "イベント", "親トラックID",
                    "面積(px)", "ROI内面積(px)", "先端部X", "先端部Y", "中心X", "中心Y",
                    "上昇速度(px/frame)", "周長(px)", "フレーム接触"])
        for frame_idx, filename in enumerate(filenames):
            rows = rows_by_frame.get(frame_idx, [])
            dets = detections_per_frame[frame_idx] if frame_idx < len(detections_per_frame) else []
            if rows:
                for row in rows:
                    vy = row["vy"]
                    vy_str = "" if vy != vy else f"{vy:.3f}"
                    parent_str = ";".join(str(p) for p in row["parent_ids"])
                    di = row["det_index"]
                    roi_area_str = per_str = touch_str = ""
                    if di is not None and di < len(dets):
                        roi_area_str = f"{dets[di].area_in_roi:.0f}"
                        per_str = f"{dets[di].perimeter:.1f}"
                        touch_str = "1" if dets[di].touches_frame else "0"
                    w.writerow([filename, frame_idx, row["track_id"], row["event"], parent_str,
                                row["area"], roi_area_str,
                                f"{row['leading_x']:.2f}", f"{row['leading_y']:.2f}",
                                f"{row['cx']:.2f}", f"{row['cy']:.2f}", vy_str, per_str, touch_str])
            else:
                w.writerow([filename, frame_idx, "", "気泡なし", "", 0, "", "", "", "", "", "", "", ""])


def write_area_count_csv(csv_path: str, filenames: List[str],
                          total_areas: List[float], roi_counts: List[int]):
    """面積・個数専用CSV: フレームごとのROI内気泡数と合計面積。"""
    out_dir = os.path.dirname(csv_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["ファイル名", "フレーム", "ROI内気泡数", "ROI内合計面積(px)"])
        for frame_idx, filename in enumerate(filenames):
            w.writerow([filename, frame_idx, roi_counts[frame_idx], total_areas[frame_idx]])


def _draw_detection(img, det, color, label=None, thickness=2):
    cv2.drawContours(img, det.contours, -1, color, thickness)   # 輪郭は成分ごとに別々に描く(直線で繋がない)
    cv2.circle(img, (int(det.leading_x), int(det.leading_y)), 4, (0, 0, 255), -1)
    if label:
        cv2.putText(img, label, (int(det.leading_x), max(0, int(det.leading_y) - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def draw_overlays(cache_dir: str, output_dir: str, rows_by_frame: Dict[int, List[dict]],
                   detections_per_frame: List[List[Detection]], filenames: List[str],
                   total_areas: List[float], roi_counts: List[int], roi_rect=None):
    os.makedirs(output_dir, exist_ok=True)
    for frame_idx, filename in enumerate(filenames):
        img = cv2.imread(os.path.join(cache_dir, filename))
        if img is None:
            continue

        if roi_rect is not None:   # ROI矩形 (マゼンタ)
            rx, ry, rw2, rh2 = roi_rect
            cv2.rectangle(img, (rx, ry), (rx + rw2, ry + rh2), (255, 0, 255), 2)

        row_by_det_index = {r["det_index"]: r for r in rows_by_frame.get(frame_idx, []) if r["det_index"] is not None}
        for idx, det in enumerate(detections_per_frame[frame_idx]):
            row = row_by_det_index.get(idx)
            event = row["event"] if row else "normal"
            color = EVENT_COLORS.get(event, (0, 255, 0))
            if not det.in_roi:   # ROI外の気泡はグレーの細線 (検出はされるが統計には含まれない)
                cv2.drawContours(img, det.contours, -1, (128, 128, 128), 1)
                continue
            label = f"ID{row['track_id']} {int(det.area_in_roi)}px" if row else None
            _draw_detection(img, det, color, label)

        cv2.putText(img, f"ROI Area: {total_areas[frame_idx]:.0f} px  Count: {roi_counts[frame_idx]}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.imwrite(os.path.join(output_dir, filename), img)


# ==============================================================
# 9. 自動ブートストラップキャリブレーション
# ==============================================================
def _bootstrap_collect_stats(detections_per_frame: List[List[Detection]]):
    """映像全体から均等に抽出した隣接フレームペアに対し、「緩いゲート + 形状(IoU)最優先」で
    仮マッチングを実行し、マッチしたペアの実際の移動量/面積比を収集する。
    戻り値: dy_list, dx_list, area_ratio_list, quality(dict)"""
    total_frames = len(detections_per_frame)
    if total_frames < 2:
        return [], [], [], {"pairs": 0, "iou_mean": 0.0, "match_fail_rate": 0.0}

    n_seg = min(BOOTSTRAP_NUM_SEGMENTS, total_frames - 1)
    sample_frames = sorted(set(
        int(round(k * (total_frames - 2) / max(1, n_seg - 1))) for k in range(n_seg)
    ))

    dy_list, dx_list, area_ratio_list, iou_list = [], [], [], []
    total_candidates, total_matched = 0, 0

    for f in sample_frames:
        dets_a = detections_per_frame[f]
        dets_b = detections_per_frame[f + 1]
        if not dets_a or not dets_b:
            continue
        n_a, n_b = len(dets_a), len(dets_b)
        cost = np.full((n_a, n_b), 1e6)
        valid = np.zeros((n_a, n_b), dtype=bool)
        ious = np.zeros((n_a, n_b))
        for i, a in enumerate(dets_a):
            total_candidates += 1
            for j, b in enumerate(dets_b):
                dy = abs(a.leading_y - b.leading_y)
                dx = abs(a.cx - b.cx)
                area_ratio = max(a.area, b.area) / max(1.0, min(a.area, b.area))
                if dy > BOOTSTRAP_LOOSE_Y_GATE or dx > BOOTSTRAP_LOOSE_X_GATE or area_ratio > BOOTSTRAP_LOOSE_AREA_GATE:
                    continue
                iou = compute_motion_compensated_iou(a.shape, b.shape, b.cx - a.cx, b.cy - a.cy)
                valid[i, j] = True
                ious[i, j] = iou
                cost[i, j] = (1.0 - iou) * 100.0 + dy * 0.1  # 形状(IoU)最優先、位置は弱い補助

        if not valid.any():
            continue
        row_ind, col_ind = linear_sum_assignment(cost)
        for i, j in zip(row_ind, col_ind):
            if not valid[i, j] or ious[i, j] < 0.3:   # 確実なマッチング(IoUが一定以上)のみ統計に反映
                continue
            a, b = dets_a[i], dets_b[j]
            dy_list.append(abs(a.leading_y - b.leading_y))
            dx_list.append(abs(a.cx - b.cx))
            area_ratio_list.append(max(a.area, b.area) / max(1.0, min(a.area, b.area)))
            iou_list.append(ious[i, j])
            total_matched += 1

    quality = {
        "pairs": total_matched,
        "iou_mean": float(np.mean(iou_list)) if iou_list else 0.0,
        "match_fail_rate": (1.0 - total_matched / total_candidates) if total_candidates else 0.0,
    }
    return dy_list, dx_list, area_ratio_list, quality


def _bootstrap_compute_params(dy_list, dx_list, area_ratio_list):
    """収集した分布からゲートパラメータを算出する(パーセンタイル × 安全係数)。"""
    if not dy_list:
        return None
    y_jump = float(np.percentile(dy_list, BOOTSTRAP_PERCENTILE)) * BOOTSTRAP_JUMP_MARGIN
    x_jump = float(np.percentile(dx_list, BOOTSTRAP_PERCENTILE)) * BOOTSTRAP_JUMP_MARGIN
    area_gate = float(np.percentile(area_ratio_list, BOOTSTRAP_PERCENTILE)) * BOOTSTRAP_AREA_MARGIN
    return {
        "MAX_LEADING_EDGE_JUMP": round(max(BOOTSTRAP_MIN_JUMP, y_jump), 1),
        "MAX_CENTER_X_JUMP": round(max(BOOTSTRAP_MIN_JUMP, x_jump), 1),
        "AREA_RATIO_GATE": round(max(1.5, area_gate), 2),
    }


def _bootstrap_preview_overlays(detections_per_frame, filenames, cache_dir, auto_params):
    """自動パラメータでサンプル区間を実際にトラッキングし、オーバーレイ画像数枚を返す。"""
    global MAX_LEADING_EDGE_JUMP, MAX_CENTER_X_JUMP, AREA_RATIO_GATE
    saved = (MAX_LEADING_EDGE_JUMP, MAX_CENTER_X_JUMP, AREA_RATIO_GATE)
    MAX_LEADING_EDGE_JUMP = auto_params["MAX_LEADING_EDGE_JUMP"]
    MAX_CENTER_X_JUMP = auto_params["MAX_CENTER_X_JUMP"]
    AREA_RATIO_GATE = auto_params["AREA_RATIO_GATE"]

    total_frames = len(detections_per_frame)
    start = max(0, total_frames // 2 - BOOTSTRAP_PREVIEW_FRAMES // 2)
    preview_range = list(range(start, min(total_frames, start + BOOTSTRAP_PREVIEW_FRAMES)))

    try:
        tracker = LeadingEdgeLapTracker()
        overlays = []
        warmup_start = max(0, start - 3)   # 少し手前からウォームアップしてIDを安定させる
        for f in range(warmup_start, min(total_frames, start + BOOTSTRAP_PREVIEW_FRAMES)):
            rows = tracker.update(detections_per_frame[f], f)
            if f not in preview_range:
                continue
            img = cv2.imread(os.path.join(cache_dir, filenames[f]))
            if img is None:
                continue
            row_by_det = {r["det_index"]: r for r in rows if r["det_index"] is not None}
            for idx, det in enumerate(detections_per_frame[f]):
                row = row_by_det.get(idx)
                event = row["event"] if row else "normal"
                _draw_detection(img, det, EVENT_COLORS.get(event, (0, 255, 0)),
                                f"ID{row['track_id']}" if row else None)
            cv2.putText(img, f"frame {f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            overlays.append((f, img))
        return overlays
    finally:
        MAX_LEADING_EDGE_JUMP, MAX_CENTER_X_JUMP, AREA_RATIO_GATE = saved


def _bootstrap_show_approval_window(dy_list, dx_list, area_ratio_list, auto_params, quality, overlays):
    """ヒストグラム + サンプルオーバーレイを一つのウィンドウにまとめて表示する。
    matplotlibがない、またはGUIが使えない環境ではコンソール出力にフォールバックする。"""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("  [bootstrap] matplotlibを読み込めないためグラフプレビューをスキップします(コンソール値のみ表示)。")
        return

    fig = plt.figure(figsize=(19, 10))
    fig.suptitle("Bootstrap Calibration - Review (close window to continue)", fontsize=14)
    gs = fig.add_gridspec(3, 3, width_ratios=[0.7, 1.4, 1.4], hspace=0.45, wspace=0.15)

    specs = [
        ("Leading-edge jump (dy)", dy_list, auto_params["MAX_LEADING_EDGE_JUMP"]),
        ("Center-X jump (dx)", dx_list, auto_params["MAX_CENTER_X_JUMP"]),
        ("Area ratio", area_ratio_list, auto_params["AREA_RATIO_GATE"]),
    ]
    for k, (title, data, cutoff) in enumerate(specs):
        ax = fig.add_subplot(gs[k, 0])
        if data:
            ax.hist(data, bins=30, color="#5B8FF9", edgecolor="white")
            ax.axvline(cutoff, color="#E24B4A", linestyle="--", linewidth=2, label=f"gate = {cutoff}")
            ax.legend(fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.tick_params(labelsize=8)

    sub = gs[0:3, 1:3].subgridspec(2, 2, hspace=0.15, wspace=0.08)
    for k, (f_idx, img) in enumerate(overlays[:4]):
        ax = fig.add_subplot(sub[k // 2, k % 2])
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(f"frame {f_idx}", fontsize=11)
        ax.axis("off")

    q_txt = (f"pairs={quality['pairs']}   "
             f"IoU mean={quality['iou_mean']:.2f}   "
             f"match fail={quality['match_fail_rate']*100:.0f}%")
    fig.text(0.05, 0.02, q_txt, fontsize=10, color="#444")

    print("  [bootstrap] 確認ウィンドウを表示しました。確認後ウィンドウを閉じるとコンソールで承認ステップに進みます。")
    plt.show()


def run_bootstrap_calibration(detections_per_frame, filenames, cache_dir):
    """統計収集 -> パラメータ算出 -> 確認ウィンドウ -> コンソール承認/修正 -> 確定パラメータをグローバルに反映。"""
    global MAX_LEADING_EDGE_JUMP, MAX_CENTER_X_JUMP, AREA_RATIO_GATE

    print("\n[ブートストラップ] 映像全体の均等サンプルから移動量/面積比の統計を収集します...")
    dy_list, dx_list, area_ratio_list, quality = _bootstrap_collect_stats(detections_per_frame)
    auto_params = _bootstrap_compute_params(dy_list, dx_list, area_ratio_list)

    if auto_params is None:
        print("  [ブートストラップ] 有効なマッチングサンプルがないため自動算出をスキップします。現在の手動値を維持します。")
        return

    print(f"  収集されたマッチングペア: {quality['pairs']}個, IoU平均: {quality['iou_mean']:.2f}, "
          f"マッチング失敗率: {quality['match_fail_rate']*100:.0f}%")

    while True:
        current = {
            "MAX_LEADING_EDGE_JUMP": MAX_LEADING_EDGE_JUMP,
            "MAX_CENTER_X_JUMP": MAX_CENTER_X_JUMP,
            "AREA_RATIO_GATE": AREA_RATIO_GATE,
        }
        print("\n=== 自動ブートストラップ結果 ===")
        print(f"{'パラメータ':<26}{'現在の手動値':>12}{'自動計算値':>14}")
        for name in ("MAX_LEADING_EDGE_JUMP", "MAX_CENTER_X_JUMP", "AREA_RATIO_GATE"):
            print(f"{name:<26}{current[name]:>12}{auto_params[name]:>14}")

        overlays = _bootstrap_preview_overlays(detections_per_frame, filenames, cache_dir, auto_params)
        _bootstrap_show_approval_window(dy_list, dx_list, area_ratio_list, auto_params, quality, overlays)

        choice = input("\n[Enter] 自動値を使用 / [m] 手動値を維持 / [e] 直接入力 / [r] プレビューを再表示: ").strip().lower()
        if choice == "":
            MAX_LEADING_EDGE_JUMP = auto_params["MAX_LEADING_EDGE_JUMP"]
            MAX_CENTER_X_JUMP = auto_params["MAX_CENTER_X_JUMP"]
            AREA_RATIO_GATE = auto_params["AREA_RATIO_GATE"]
            print("  -> 自動値を適用しました。")
            break
        elif choice == "m":
            print("  -> 現在の手動値を維持します。")
            break
        elif choice == "e":
            try:
                v1 = input(f"  MAX_LEADING_EDGE_JUMP (Enter=自動 {auto_params['MAX_LEADING_EDGE_JUMP']}): ").strip()
                v2 = input(f"  MAX_CENTER_X_JUMP (Enter=自動 {auto_params['MAX_CENTER_X_JUMP']}): ").strip()
                v3 = input(f"  AREA_RATIO_GATE (Enter=自動 {auto_params['AREA_RATIO_GATE']}): ").strip()
                MAX_LEADING_EDGE_JUMP = float(v1) if v1 else auto_params["MAX_LEADING_EDGE_JUMP"]
                MAX_CENTER_X_JUMP = float(v2) if v2 else auto_params["MAX_CENTER_X_JUMP"]
                AREA_RATIO_GATE = float(v3) if v3 else auto_params["AREA_RATIO_GATE"]
                print("  -> 入力値を適用しました。")
                break
            except ValueError:
                print("  -> 数値形式ではありません。もう一度お試しください。")
                continue
        elif choice == "r":
            continue
        else:
            print("  -> 不明な入力です。もう一度選択してください。")
            continue

    print(f"  [ブートストラップ] 確定ゲート: JUMP={MAX_LEADING_EDGE_JUMP}, "
          f"X={MAX_CENTER_X_JUMP}, AREA={AREA_RATIO_GATE}\n")


# ==============================================================
# 10. ROI
# ==============================================================
def _roi_save_path() -> str:
    return ROI_SAVE_PATH if ROI_SAVE_PATH else os.path.join(OUTPUT_FOLDER, "roi_saved.json")


def load_saved_roi():
    """保存済みROIがあれば(x, y, w, h)タプルで返す。なければ、または破損していればNone。"""
    path = _roi_save_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rect = data.get("roi_rect")
        if isinstance(rect, list) and len(rect) == 4:
            return tuple(int(v) for v in rect)
    except Exception as e:
        print(f"  [ROI] 保存ファイルを読み込めませんでした({e})。新規に選択します。")
    return None


def save_roi(rect):
    """選択したROIをファイルに保存し、次回実行時に再利用できるようにする。"""
    if rect is None:
        return
    path = _roi_save_path()
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"roi_rect": list(rect)}, f, ensure_ascii=False, indent=2)
    print(f"  [ROI] 選択領域を保存しました: {path}")


def resolve_roi(sample_img: np.ndarray):
    """ROI決定: コード固定値 -> 保存済みROIの再利用確認 -> マウス選択+保存"""
    if ROI_RECT is not None:
        print(f"  [ROI] コードに固定されたROI_RECTを使用: {ROI_RECT}")
        return tuple(ROI_RECT)

    saved = load_saved_roi()
    if saved is not None:
        x, y, rw, rh = saved
        choice = input(f"\n[ROI] 保存済みROIがあります: x={x}, y={y}, w={rw}, h={rh}\n"
                       f"      [Enter] 再利用 / [n] 新規選択: ").strip().lower()
        if choice != "n":
            print("  [ROI] 保存済みROIを再利用します。")
            return saved

    rect = select_roi_interactive(sample_img)
    save_roi(rect)
    return rect


def select_roi_interactive(sample_img: np.ndarray):
    """最初のフレームでマウスドラッグによりROIを選択。ENTER/SPACEで確定、cでキャンセル(画面全体)。"""
    print("\n[ROI] マウスで関心領域をドラッグしてからENTERまたはSPACEを押してください。(c=キャンセル、キャンセル時は画面全体)")
    rect = cv2.selectROI("Select ROI (ENTER=OK, c=cancel)", sample_img, showCrosshair=True)
    cv2.destroyWindow("Select ROI (ENTER=OK, c=cancel)")
    x, y, rw, rh = [int(v) for v in rect]
    if rw <= 0 or rh <= 0:
        print("  [ROI] 選択がキャンセルされたため画面全体をROIとして使用します。")
        return None
    print(f"  [ROI] 選択されました: x={x}, y={y}, w={rw}, h={rh}")
    print(f"  [ROI] 再現するにはコード上部で ROI_RECT = ({x}, {y}, {rw}, {rh}) と固定できます。")
    return (x, y, rw, rh)


def make_roi_mask(image_h: int, image_w: int, roi_rect):
    """ROI矩形を0/1マスクに変換。roi_rectがNoneなら画面全体。"""
    mask = np.zeros((image_h, image_w), dtype=np.uint8)
    if roi_rect is None:
        mask[:, :] = 1
        return mask
    x, y, rw, rh = roi_rect
    x2, y2 = min(image_w, x + rw), min(image_h, y + rh)
    x, y = max(0, x), max(0, y)
    mask[y:y2, x:x2] = 1
    return mask


# ==============================================================
# 11. 検出ステップ (前処理 -> U-Net)
# ==============================================================
def check_unet_input(gray, prob, inst, detector, filename):
    """最初のフレームで「U-Netに入る画像が学習画像と同じ種類か」を確認し、デバッグ画像を保存する。"""
    h, w = gray.shape
    black = float((gray < 15).mean())
    cover = float((inst > 0).mean())
    print(f"  [入力チェック] {filename}: サイズ {h}x{w}, 黒画素 {black:.0%}, 気泡判定の画素 {cover:.0%}")
    if black < MIN_BLACK_FRACTION:
        print("  !!! 警告: 前処理後の背景が黒くなっていません (学習画像は約94%が黒)。")
        print("      U-Netは「黒い背景 + 白い輪郭」の2値化画像で学習しているため、このままでは正しく検出できません。")
        print("      -> Noise Cut を上げる / 背景画像(BACKGROUND_PATH)が同じ撮影条件か確認 /")
        print("         学習画像を作ったときの値を PREPROC_FIXED に設定")
    if cover > 0.5:
        print("  !!! 警告: 画面の半分以上が気泡と判定されています。背景そのものを気泡と誤認している可能性が高いです。")
    if getattr(detector, "train_hw", None) is None:
        print("  ※ best.pt に学習画像サイズの記録がありません。学習画像とサイズが違う場合は TRAIN_IMAGE_HW を指定してください。")
    if SAVE_DEBUG_FIRST_FRAME:
        d = os.path.join(OUTPUT_FOLDER, "debug")
        os.makedirs(d, exist_ok=True)
        cv2.imwrite(os.path.join(d, "unet_input.png"), gray)                          # U-Netが実際に見た画像
        cv2.imwrite(os.path.join(d, "prob_in.png"), (prob[1] * 255).astype(np.uint8))  # 内部確率 (白=1)
        cv2.imwrite(os.path.join(d, "prob_edge.png"), (prob[2] * 255).astype(np.uint8))  # 境界確率 (白=1)
        print(f"  [入力チェック] U-Net入力と確率マップを保存: {d}")


def run_detection_phase(cache_dir: str):
    print("U-Netモデルをロード中...")
    detector = UNetDetector(UNET_CKPT, TRAIN_IMAGE_HW)

    bg_img = cv2.imread(BACKGROUND_PATH)
    if bg_img is None and ENABLE_PREPROCESSING:
        raise FileNotFoundError(f"背景画像が見つかりません: {BACKGROUND_PATH}")
    if not ENABLE_PREPROCESSING:
        print("  [前処理OFF] 元画像をそのままU-Netに入力します (2値化画像で学習したモデルには非推奨)。")

    image_files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff'):
        image_files.extend(glob.glob(os.path.join(IMAGE_FOLDER, ext)))
    image_files = sorted(set(image_files))
    image_files = [p for p in image_files if os.path.normcase(os.path.abspath(p))
                   != os.path.normcase(os.path.abspath(BACKGROUND_PATH))]
    if not image_files:
        raise FileNotFoundError(f"'{IMAGE_FOLDER}' フォルダに画像がありません。")

    print(f"合計{len(image_files)}枚の画像が見つかりました。検出ステップを開始します。\n")
    os.makedirs(cache_dir, exist_ok=True)
    inst_dir = os.path.join(OUTPUT_FOLDER, "instances")
    if SAVE_INSTANCE_MASKS:
        os.makedirs(inst_dir, exist_ok=True)

    is_first = True
    thresh_val, bright_val, median_val = PREPROC_FIXED if PREPROC_FIXED else PREPROC_DEFAULT
    use_ui = ENABLE_PREPROCESSING and PREPROC_FIXED is None
    detections_per_frame: List[List[Detection]] = []
    filenames: List[str] = []
    total_areas: List[float] = []   # ROI使用時: ROI内面積の合計。未使用時: 全体面積の合計
    roi_counts: List[int] = []      # フレームごとのROIにかかった気泡数
    image_size = None
    roi_rect = ROI_RECT
    roi_bool = None

    for img_path in image_files:
        filename = os.path.basename(img_path)
        img, processed_img, thresh_val, bright_val, median_val = preprocess_image(
            img_path, bg_img, filename=filename, show_ui=(is_first and use_ui),
            current_thresh_val=thresh_val, current_bright_val=bright_val, current_median_val=median_val,
        )
        if img is None:
            print(f"  -> {filename}: 画像の読み込みに失敗、スキップ")
            continue
        if is_first:
            print(f"  -> 設定値: Noise={thresh_val}, Brightness={bright_val}, Median={median_val}")
            if ENABLE_ROI and roi_rect is None:
                roi_rect = resolve_roi(processed_img)
            is_first = False

        cv2.imwrite(os.path.join(cache_dir, filename), processed_img)
        h, w = processed_img.shape[:2]
        image_size = (h, w)
        if roi_bool is None or roi_bool.shape != (h, w):
            roi_bool = make_roi_mask(h, w, roi_rect if ENABLE_ROI else None).astype(bool)

        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        prob = detector.prob(gray)
        inst = extract_instances(prob, UNET_MIN_AREA, UNET_BAND, UNET_EDGE_THR, UNET_CLOSE, UNET_TINY_MAX)
        if not filenames:   # 最初のフレームだけ入力の健全性チェック
            check_unet_input(gray, prob, inst, detector, filename)
        if SAVE_INSTANCE_MASKS:
            np.savez_compressed(os.path.join(inst_dir, os.path.splitext(filename)[0] + ".npz"), inst=inst)

        dets = instances_to_detections(inst, roi_bool)
        total_area = float(sum(d.area_in_roi for d in dets))
        roi_count = sum(1 for d in dets if d.in_roi)

        detections_per_frame.append(dets)
        filenames.append(filename)
        total_areas.append(total_area)
        roi_counts.append(roi_count)
        print(f"  [{filename}] 検出{len(dets)}個 (ROI内{roi_count}個), ROI内合計面積 {total_area:.0f}px")

    preprocess_params = {"noise_cut": thresh_val, "brightness": bright_val, "median": median_val}
    return detections_per_frame, filenames, total_areas, roi_counts, image_size, roi_rect, preprocess_params


# ==============================================================
# 12. メインパイプライン
# ==============================================================
def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    cache_dir = os.path.join(OUTPUT_FOLDER, "_cache_processed")

    (detections_per_frame, filenames, total_areas, roi_counts,
     image_size, roi_rect, preprocess_params) = run_detection_phase(cache_dir)
    total_frames = len(filenames)

    if ENABLE_BOOTSTRAP:
        run_bootstrap_calibration(detections_per_frame, filenames, cache_dir)

    print("\n[LAPトラッカー] 実行中...")
    rows = run_laptrack(detections_per_frame)
    rows = compute_velocity_ema(rows, total_frames)

    tracking_csv_path = os.path.join(OUTPUT_FOLDER, "result_tracking.csv")
    area_csv_path = os.path.join(OUTPUT_FOLDER, "result_area_count.csv")
    write_tracking_csv(tracking_csv_path, rows, filenames, detections_per_frame)
    write_area_count_csv(area_csv_path, filenames, total_areas, roi_counts)
    draw_overlays(cache_dir, OUTPUT_FOLDER, rows, detections_per_frame, filenames,
                  total_areas, roi_counts, roi_rect=(roi_rect if ENABLE_ROI else None))

    report = qc_report(rows, total_frames)
    report["used_params"] = {
        "UNET_CKPT": UNET_CKPT,
        "UNET": {"min_area": UNET_MIN_AREA, "band": UNET_BAND, "edge_thr": UNET_EDGE_THR,
                 "close": UNET_CLOSE, "tiny_max": UNET_TINY_MAX},
        "preprocess": preprocess_params if ENABLE_PREPROCESSING else None,
        "MAX_LEADING_EDGE_JUMP": MAX_LEADING_EDGE_JUMP,
        "MAX_CENTER_X_JUMP": MAX_CENTER_X_JUMP,
        "AREA_RATIO_GATE": AREA_RATIO_GATE,
        "MERGE_UNION_IOU_THRESHOLD": MERGE_UNION_IOU_THRESHOLD,
        "SPLIT_UNION_IOU_THRESHOLD": SPLIT_UNION_IOU_THRESHOLD,
        "EVENT_OVERLAP_MIN": EVENT_OVERLAP_MIN,
        "USE_FLOW_PRIOR": USE_FLOW_PRIOR, "SPACING_GATE_FRAC": SPACING_GATE_FRAC,
        "COAST_GATE_GROWTH": COAST_GATE_GROWTH, "SHAPE_AREA_REF": SHAPE_AREA_REF,
        "bootstrap_enabled": ENABLE_BOOTSTRAP,
        "roi_enabled": ENABLE_ROI,
        "roi_rect": list(roi_rect) if (ENABLE_ROI and roi_rect is not None) else None,
    }
    report_path = os.path.join(OUTPUT_FOLDER, "qc_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nCSV保存完了:")
    print(f"  - トラッキング(移動距離): {tracking_csv_path}")
    print(f"  - 面積・個数:            {area_csv_path}")
    print(f"オーバーレイ画像の保存完了: {OUTPUT_FOLDER}")
    print(f"QCレポート: {json.dumps(report, ensure_ascii=False, indent=2)}")
    print("\n全ての処理が完了しました!")


if __name__ == "__main__":
    main()

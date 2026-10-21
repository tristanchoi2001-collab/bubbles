#!/usr/bin/env python
"""
二値化画像版 — U-Net の学習 (1ファイル)
=====================================================================
    python 1_bin_train.py

STEP で何をするか選ぶ (設定はこの下):
  STEP = 'dots'  : 小さい点のラベル補充。ラベルされていない小さい点の候補を探し、確認の画面で選ぶ
                     左クリック = 気泡でない   右クリック = 分からない (くっついた2個も)   もう一度 = 取り消し
                     Enter/Space = このページの残りを「気泡」にして次へ   b = 前のページ   q / Esc = 保存して終了
                   -> DOT_OUT/coco (点を足したラベル) と DOT_OUT/ignore (確認していない候補 = 学習しない所)
                   途中でやめても次は続きから (DOT_OUT/decisions.json)
  STEP = 'train' : U-Net を学習する。USE_DOT_LABELS = True なら STEP = 'dots' の結果を自動で使う
                     USE_PRIOR = False -> 普通の U-Net (3チャンネル)。ラベル補充の効果だけを比べるときはこちら
                     USE_PRIOR = True  -> TAU (画像 + 事前マスクの 5チャンネル)
                   -> OUT/best.pt を 2_bin_track.py の UNET_CKPT に入れる (どちらのモデルも自動で見分ける)

中身 (元は old/ のファイルを old/tools/build_binarized.py でまとめたもの。今はこのファイルを直接直す。直したら python tools/build_raw.py):
  [A] TAU の部品 (モデル・入力・学習用の事前マスク・画像を崩す増強)   元 tau_unet.py
  [B] 小さい点のラベル補充 (STEP = 'dots')                           元 dot_labels.py
  [C] 学習 (STEP = 'train')                                           元 1_tau_unet_train.py
  [D] 起動
"""

# ======================================================================
#  何をするか — ここを選んで  python 1_bin_train.py  で実行。Windows のパスは r'...' で囲む
# ======================================================================
STEP = 'dots'                 # 'dots' = 小さい点のラベル補充 (確認の画面) / 'train' = 学習
USE_DOT_LABELS = True         # STEP = 'train' のとき STEP = 'dots' の結果 (DOT_OUT/coco と DOT_OUT/ignore) を使う。
                              # False なら SRC (Roboflow の書き出し) と IGNORE_SRC をそのまま使う
DOT_OUT = r'dot_labels'       # STEP = 'dots' の作業・出力フォルダ (SRC の外に置く)


# ======================================================================
# STEP = 'train' (学習) の設定 (元 1_tau_unet_train.py)
# ======================================================================
SRC = r'C:\Users\Tristan\Desktop\ams\unet\cocosegmentation'   # Roboflow の書き出しフォルダ (train/ valid/ test/ を含む)
DST = r'dataset_bin'          # 変換したデータセットのフォルダ (images/ masks/ instances/ preview/ は毎回作り直す)
OUT = r'runs/bin'             # 結果のフォルダ。既にあれば runs/bin2, bin3 ... を自動で作る

REBUILD_DATASET = True        # True : 毎回 SRC から変換し直す (Roboflow のラベル修正が反映される)
                              # False: DST に変換済みのデータがあればそのまま使う (instances/ が無ければ作り直す)
IGNORE_SRC = None             # 学習しない画素のマスク (USE_DOT_LABELS = True なら DOT_OUT/ignore を自動で使う)。None なら使わない。
                              # <split>/<画像名>.png の白い所 (ラベルされていない点の候補) を、背景としても気泡としても学習しない。
                              # val/test の評価でもその画素と、そこに出た気泡は数えない。変えたら REBUILD_DATASET = True で
USE_PRIOR = False             # True : TAU (画像 + 事前マスクの 5チャンネル) を学習 → 2_bin_track.py で使う
                              # False: 事前マスクなしの普通の U-Net (3チャンネル) を学習 → 2_bin_track.py で
                              #        そのまま使える。ラベル補充 (STEP = 'dots') の効果だけを比べたいときはこちら。
                              #        FINETUNE_FROM は 3チャンネルの best.pt。画像を崩す増強・事前マスクの設定は使わない

# [1] ラベル変換 (1_unet_train.py と同じ)
EDGE_PX   = 4                 # 大きい気泡の境界の太さ (px)。小さい気泡は自動で 1〜3px
N_PREVIEW = 8                 # ラベル確認用のプレビュー枚数 (DST/preview/)

# [2] 学習
FINETUNE_FROM = r'best.pt'    # 今の best.pt (1_unet_train.py の出力, 3チャンネル)。ここから始める (推奨)。
                              # None なら ImageNet の重みから 5チャンネルで学習 (EPOCHS, LR を使う。時間がかかる)
FINETUNE_LR = 1e-4            # 学習率
FINETUNE_EPOCHS = 80          # epoch 数
EPOCHS  = 549                 # FINETUNE_FROM = None のときの epoch 数
LR      = 3e-4                # FINETUNE_FROM = None のときの学習率
BS      = 4                   # VRAM が足りなければ 2
CROP    = (1088, 416)         # (高さ, 幅)。32 の倍数。画像より大きければ反射パディング (= 画像全体で学習。1_unet_train.py と同じ)
EDGE_W  = 6.0                 # 境界クラスの損失の重み
ENCODER = 'resnet34'          # FINETUNE_FROM = None のときのエンコーダ (FINETUNE_FROM があればその値を使う)
WORKERS = 0                   # Windows では 0 のまま
SEED    = 0                   # 再現用の乱数シード
FREEZE_ENCODER_EPOCHS = 0     # 最初の何 epoch エンコーダを固定するか (最初の畳み込み = 事前マスクの入口は固定しない)
BEST_BY = 'prior'             # best.pt の選び方: 'prior' = 崩した画像・事前マスクありの点数が最高の epoch (ただし元の画像・
                              #   事前マスクなしの点数が開始モデルより BEST_EMPTY_TOL 以上下がった epoch は除く) / 'mean' = 両方の平均
BEST_EMPTY_TOL = 0.01         # 'prior' のとき、事前マスクなしの点数 (0.4×内部 IoU + 0.6×境界 IoU) の低下の許容

# [2-0] 学習中の増強 (1_unet_train.py と同じ。Roboflow で増強したなら切っておく)
AUG_RANDOM_CROP = True        # CROP の大きさを無作為な位置で切り出す
AUG_FLIP = False              # 左右反転
AUG_ROTATE = False            # ±5° 回転
AUG_BRIGHTNESS = False        # 明るさ・コントラスト

# [2-1] Copy-Paste 増強 (1_unet_train.py と同じ。貼った気泡も事前マスクの対象になる)
COPY_PASTE = True
CP_PROB = 0.5                 # 学習サンプルごとに貼り付けをする確率
CP_MAX = 15                   # 1枚に貼る最大個数
CP_MAX_AREA = 500             # この面積 (px) 未満の気泡だけ材料にする
CP_ALPHA = (0.35, 1.0)        # 貼るときの明るさの倍率 (薄い小気泡を真似る)
CP_SAVE_PREVIEW = 6           # 増強結果の確認画像の枚数 (OUT/cp_preview/。事前マスクも重ねて描く)

# [2-2] 画像を崩す (事前マスクがないと正しく出せない状況を作る。値の意味は tau_unet.ImageDegrade を参照)
DEGRADE_P = 0.5               # 学習サンプルごとに画像を崩す確率 (0 なら崩さない = 1回目の学習と同じ)
DEGRADE_N_MAX = 4             # 1枚で崩す気泡の最大数
DEGRADE_MIN_AREA = 300        # 崩す気泡の最小面積 (px)。大きい気泡の切れ目・薄い輪郭を真似る
DEGRADE_P_FADE = 0.3          # 崩す気泡のうち「輪郭全体を途切れ途切れにする」割合 (残りは「輪郭の一部を消す」)
DEGRADE_GAP = (0.1, 0.35)     # 消す輪郭の割合 (周の何割)
DEGRADE_FADE_KEEP = (0.25, 0.6)  # 途切れ途切れにするとき残す画素の割合

# [2-3] 事前マスクの作り方 (正解ラベルを崩す。値の意味は tau_unet.PriorAug を参照)
PRIOR_P_EMPTY = 0.15          # 事前マスクなし (1パス目と同じ状況) の割合
PRIOR_P_DROP = 0.2            # 気泡ごとに消す確率 (前のパスの見落とし)
PRIOR_SHIFT_PX = 1.0          # 位置ずれの標準偏差 = この値 + 等価直径 × PRIOR_SHIFT_SIZE (px)。
PRIOR_SHIFT_SIZE = 0.05       #   実データの前後フレームからの予測のずれ (大きさ別の中央値) に合わせた値
PRIOR_P_BIG_SHIFT = 0.1       # 位置ずれを4倍にする確率 (速度の予測の外れ・大きい気泡の変形)
PRIOR_SCALE = (0.85, 1.15)    # 大きさの変化 (前後のフレームでの変形)
PRIOR_MORPH_PX = 2            # 膨張/収縮の最大幅 (px)
PRIOR_P_TRUNC = 0.1           # 一部が欠ける確率
PRIOR_P_MERGE = 0.3           # 接している2個を1個にまとめる確率 (前のパスの融合)
PRIOR_P_SPLIT = 0.05          # 面積 500px 以上の気泡を2つに割る確率
PRIOR_PHANTOM_RATE = 2.0      # 1枚あたりの「何も無い所の気泡」の平均個数 (事前マスクをそのまま写さないように)

# [3] test 確認用の後処理 — tracker3.py の UNET_* と同じにしておく
MIN_AREA = 4
BAND     = 25
EDGE_THR = 0.5
CLOSE    = 2
TINY_MAX = 300
IOU_MATCH = 0.3               # 大きさ別の再現率で、予測と正解を同じ気泡とみなす IoU の下限

# ======================================================================
#  STEP = 'dots' (小さい点のラベル補充) の設定
# ======================================================================
DOT_REVIEW = True                 # True: 確認の画面を開く / False: 開かずに書き出すだけ (未確認の候補はすべて ignore)
SPLIT_ORDER = ('test', 'valid', 'train')   # 確認する順 (Roboflow のフォルダ名)

# [1] 候補の条件 (学習画像は二値化済み: 背景差分が Noise Cut 未満は 0、それ以上は ×Brightness)
CAND_LOW = 30                 # この明るさ以上を「光っている」画素とする (0 以外。JPEG のにじみ (〜20) は除く)
CAND_PEAK = 60                # 塊の一番明るい画素がこれ以上 (Noise Cut 15 × Brightness 4 = 60)
CAND_MIN_AREA = 5             # 光っている画素の数の下限 (tracker3 の IGNORE_PARTICLE_AREA = 4 より大きい)
CAND_MAX_AREA = 600           # 塗りつぶした面積の上限 (これより大きい塊は小さい点ではないので候補にしない)
LABEL_GAP = 2                 # ラベル済みの気泡からこの px 以内に掛かる塊は候補にしない (その気泡の輪郭の一部のことが多い)
PAIR_MIN_HOLE = 3             # 穴がこの px 以上の輪を「輪」とみなす。輪を 2つ以上含む塊 (くっついた輪) は輪ごとの候補に分ける
                              # (1つのラベルにすると「くっついた2個 = 1個」を教えてしまう)。0 なら分けない

# [3] 書き出し
IGNORE_PAD = 2                # 無視する範囲を候補の周りにこの px 広げる (点のぼやけた縁も背景として教えない)
GROW_PX = 0                   # 「気泡」にした点のマスクを広げる px。0 = 光っている画素の外側の縁まで
                              # (= 白い輪の外側にポリゴンを描く今のラベルの描き方)

# [2] 確認画面
GRID = (5, 4)                 # 1ページのタイルの数 (横, 縦)
TILE = 140                    # タイル1枚の大きさ (画面の px)。窓は 横 GRID[0]×(TILE+2) / 縦 52 + GRID[1]×(TILE+2) px
                              # (既定 708×618)。下の段が画面からはみ出すなら小さくする (見えないタイルも Enter で「気泡」になる)
MIN_CROP = 33                 # タイルに映す範囲の最小 (元画像の px)。点の周りの様子も見えるように


# ======================================================================
# import
# ======================================================================
import json
import random
import shutil
import time
from collections import Counter, OrderedDict
from dataclasses import replace, dataclass
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp
import os
import math
from typing import List, Optional, Sequence, Tuple


# ======================================================================
# [A] TAU の部品 — 元 tau_unet.py
# ======================================================================
# 元 tau_unet.py の説明:
# Tracking-aware U-Net (TAU) の共通部品
# =====================================================================
# U-Net の入力に「このフレームに気泡がどこにあるはずか」(トラッカーが前後のフレームから予測した気泡マスク) を足す。
#   ch 0-2 : 前処理画像 (グレーを3回。best.pt と同じ正規化)
#   ch 3   : 事前マスク・内部 (予測した気泡の塗りつぶし 0/1)
#   ch 4   : 事前マスク・輪郭 (予測した気泡ごとの内側の輪郭 PRIOR_EDGE_PX 幅 0/1。くっついた気泡の境目が分かる)
# 出力は best.pt と同じ 3クラス (背景/内部/境界) なので、気泡の分け方 (wall / hybrid) とトラッカーはそのまま使う。
#
# best.pt (3チャンネル) から学習を始めるときは、最初の畳み込みの事前マスク用の重みを 0 で足す (expand_state_dict)。
# 学習前のモデルは事前マスクに関係なく best.pt と同じ確率を出す (tests/test_tau.py の a で確認)。
# 事前マスクが全部 0 のときは、学習後のモデルも事前マスクなしの検出器として働く (学習で PriorAug.p_empty の割合だけ練習する)。
#
# 学習用の事前マスクは、正解ラベルの気泡を崩して作る (synth_prior。MaskTrack, Perazzi et al., CVPR 2017 と同じ考え方)。
# 連続フレームのラベルは要らない。崩し方 = 前のパスの検出・トラッカーの予測で起きる誤り:
#   見落とし (消す) / 位置ずれ / 変形 (拡大縮小・膨張収縮) / 一部欠け / 隣と融合 / 割れ / 何も無い所の気泡
#
# 1_tau_unet_train.py (学習) と tau_tracker.py (推論) の両方が使う。2つと同じフォルダに置くこと。

PRIOR_CHANNELS = 2       # 事前マスクのチャンネル数 (内部, 輪郭)
PRIOR_EDGE_PX = 2        # 事前マスクの輪郭の幅 (px)。学習と推論で同じ値を使う (ckpt の prior_edge_px に記録)
IMAGE_CHANNELS = 3       # 画像のチャンネル数 (グレーを3回。best.pt と同じ)

Shape = Tuple[np.ndarray, int, int]   # (bbox で切り出した bool マスク, x0, y0)。tracker3.py と同じ


# ==============================================================
# 1. モデル
# ==============================================================
def build_model(encoder: str, classes: int = 3, in_channels: int = IMAGE_CHANNELS + PRIOR_CHANNELS,
                encoder_weights=None):
    import segmentation_models_pytorch as smp
    return smp.Unet(encoder, encoder_weights=encoder_weights, in_channels=in_channels, classes=classes)


def state_in_channels(sd) -> int:
    """state_dict の入力チャンネル数 (最初の畳み込みの重みの2番目の次元)"""
    for k, v in sd.items():
        if k.startswith("encoder.") and v.ndim == 4:
            return int(v.shape[1])
    raise ValueError("state_dict にエンコーダの畳み込みが見つかりません")


def expand_state_dict(sd, model):
    """3チャンネルの state_dict を model (5チャンネル) に合わせる。
    入力チャンネル数だけが違う重み (最初の畳み込み) は、足りないチャンネルを 0 で埋める
    -> 足したチャンネル (事前マスク) は出力に全く影響しない (学習で少しずつ使い始める)"""
    import torch
    target = model.state_dict()
    out = {}
    for k, v in sd.items():
        t = target.get(k)
        if t is not None and v.ndim == 4 and t.ndim == 4 and v.shape[1] < t.shape[1] \
                and v.shape[0] == t.shape[0] and v.shape[2:] == t.shape[2:]:
            w = torch.zeros(t.shape, dtype=v.dtype)
            w[:, :v.shape[1]] = v
            out[k] = w
        else:
            out[k] = v
    return out


def load_tau_model(ckpt_path: str, dev: str = "cpu", force_prior: bool = False):
    """ckpt を読み込む。戻り値 (model, ck, uses_prior)
    5チャンネルの ckpt (1_tau_unet_train.py の出力) -> そのまま。uses_prior = True
    3チャンネルの ckpt (best.pt)
        force_prior = False -> 3チャンネルのまま (事前マスクは無視。tracker3.py の UNetDetector と完全に同じ確率)
        force_prior = True  -> 5チャンネルにして事前マスクの重みを 0 で足す (学習の開始点)"""
    import torch
    ck = torch.load(ckpt_path, map_location="cpu")
    sd = {k: (v.float() if v.is_floating_point() else v) for k, v in ck["state_dict"].items()}  # fp16 版も読める
    inp = ck.get("input") or {}
    if inp.get("mode", "bin") != "bin" or ck.get("ctx"):   # raw/1_raw_train.py の ckpt (差分の入力・トランスフォーマー)
        raise ValueError(f"{ckpt_path}: raw/1_raw_train.py の ckpt です (入力 {inp.get('mode')!r}"
                         f"{', トランスフォーマー付き' if ck.get('ctx') else ''})。raw/2_raw_track.py で使ってください")
    src_ch = state_in_channels(sd)
    in_ch = src_ch if (src_ch > IMAGE_CHANNELS or not force_prior) else IMAGE_CHANNELS + PRIOR_CHANNELS
    if in_ch not in (IMAGE_CHANNELS, IMAGE_CHANNELS + PRIOR_CHANNELS):
        raise ValueError(f"{ckpt_path}: 入力チャンネル数 {in_ch} には対応していません (3 か {IMAGE_CHANNELS + PRIOR_CHANNELS})")
    model = build_model(ck["encoder"], ck.get("classes", 3), in_ch)
    model.load_state_dict(expand_state_dict(sd, model) if in_ch > src_ch else sd)
    return model.to(dev).eval(), ck, in_ch > IMAGE_CHANNELS


# ==============================================================
# 2. 入力
# ==============================================================
def make_input(gray: np.ndarray, prior: Optional[np.ndarray], mean, std, uses_prior: bool = True) -> np.ndarray:
    """(H, W) uint8 + 事前マスク (2, H, W) -> ネットワーク入力 (C, H, W) float32。prior が None なら 0 (事前情報なし)"""
    g = gray.astype(np.float32) / 255.0
    x = [(g - float(m)) / float(s) for m, s in zip(mean, std)]
    if uses_prior:
        if prior is None:
            x += [np.zeros_like(g)] * PRIOR_CHANNELS
        else:
            if prior.shape != (PRIOR_CHANNELS,) + gray.shape:
                raise ValueError(f"事前マスクの形 {prior.shape} が画像 {gray.shape} と合いません")
            x += [prior[c].astype(np.float32) for c in range(PRIOR_CHANNELS)]
    return np.stack(x)


def _paste_or(canvas: np.ndarray, m: np.ndarray, x0: int, y0: int):
    """canvas[y0:, x0:] |= m (画面からはみ出す部分は切る)"""
    H, W = canvas.shape
    h, w = m.shape
    ya, yb, xa, xb = max(y0, 0), min(y0 + h, H), max(x0, 0), min(x0 + w, W)
    if ya < yb and xa < xb:
        canvas[ya:yb, xa:xb] |= m[ya - y0:yb - y0, xa - x0:xb - x0]


def render_prior(shapes: Sequence[Shape], H: int, W: int, edge_px: int = PRIOR_EDGE_PX) -> np.ndarray:
    """気泡マスクの一覧 -> 事前マスク (2, H, W) float32 [内部(塗りつぶし), 輪郭(気泡ごとの内側 edge_px 幅)]
    画面からはみ出す部分は切ってから輪郭を取る (画面端で切れた気泡は画面端にも輪郭が付く。学習と推論で同じ)"""
    fill = np.zeros((H, W), bool)
    ring = np.zeros((H, W), bool)
    for m, x0, y0 in shapes:
        if m is None or not m.any():
            continue
        h, w = m.shape
        ya, yb, xa, xb = max(y0, 0), min(y0 + h, H), max(x0, 0), min(x0 + w, W)
        if ya >= yb or xa >= xb:
            continue
        c = m[ya - y0:yb - y0, xa - x0:xb - x0]
        if not c.any():
            continue
        fill[ya:yb, xa:xb] |= c
        inner = ndimage.binary_erosion(np.pad(c, 1), iterations=edge_px)[1:-1, 1:-1] if edge_px > 0 else c
        ring[ya:yb, xa:xb] |= c & ~inner
    return np.stack([fill, ring]).astype(np.float32)


def label_shapes(ins: np.ndarray) -> List[Shape]:
    """気泡ラベルマップ (0 = 背景, 1..N) -> 気泡マスクの一覧"""
    out = []
    for k, sl in enumerate(ndimage.find_objects(ins), start=1):
        if sl is None:
            continue
        m = ins[sl] == k
        if m.any():
            out.append((m, sl[1].start, sl[0].start))
    return out


# ==============================================================
# 3. 学習用の事前マスク (正解ラベルを崩して作る)
# ==============================================================
@dataclass
class PriorAug:
    p_empty: float = 0.15          # 事前マスクを全部 0 にする割合 (1パス目・事前情報なしでも検出できるように)
    p_drop: float = 0.2            # 気泡ごとに事前マスクから消す確率 (前のパスで見落とした気泡)
    shift_px: float = 1.0          # 位置ずれの標準偏差 (px, x・y それぞれ) = shift_px + 等価直径 × shift_size
    shift_size: float = 0.05       #   実データ (731〜790) の前後フレームからの予測と合わせた値 (CLAUDE.md 参照)
    p_big_shift: float = 0.1       # 位置ずれを big_shift_mult 倍にする確率 (速度の予測の外れ・大きい気泡の変形)
    big_shift_mult: float = 4.0
    scale: Tuple[float, float] = (0.85, 1.15)   # 大きさの変化 (前後のフレームでの変形)
    morph_px: int = 2              # 膨張/収縮の最大幅 (px)。輪郭の取り方の違い (正解ラベルは白い縁の外側、検出は少し内側)
    p_trunc: float = 0.1           # 一部が欠ける確率 (前のパスで一部しか取れなかった気泡)
    trunc_keep: Tuple[float, float] = (0.4, 0.9)  # 欠けたときに残す面積の割合
    p_merge: float = 0.3           # 接している2個を1個にまとめる確率 (前のパスで融合していた)
    p_split: float = 0.05          # 大きい気泡を2つに割る確率 (前のパスで割れていた)
    split_min_area: int = 500      # 割るのはこの面積 (px) 以上の気泡だけ
    phantom_rate: float = 2.0      # 1枚あたりの「何も無い所の気泡」の平均個数 (前のパスの誤検出・予測の外れ)。
                                   #   形は正解の気泡からランダムに写すので、ほとんど tiny / small になる
    touch_px: int = 2              # この距離 (px) 以内なら「接している」とみなす (融合の候補)

    def as_dict(self):
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


def _deform(m: np.ndarray, x0: int, y0: int, rng, aug: PriorAug) -> Optional[Shape]:
    """1個の気泡マスクを崩す (拡大縮小 -> 膨張/収縮 -> 一部欠け -> 位置ずれ)"""
    area = int(m.sum())
    if area == 0:
        return None
    eqd = 2.0 * math.sqrt(area / math.pi)
    h, w = m.shape
    s = float(rng.uniform(*aug.scale))
    if abs(s - 1.0) > 0.02 and min(h, w) * s >= 2:
        nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
        m2 = cv2.resize(m.astype(np.uint8), (nw, nh), interpolation=cv2.INTER_NEAREST).astype(bool)
        if m2.any():
            x0, y0 = x0 + int(round((w - nw) / 2)), y0 + int(round((h - nh) / 2))
            m = m2
    r = int(rng.integers(-aug.morph_px, aug.morph_px + 1)) if aug.morph_px > 0 else 0
    if r > 0:
        m = ndimage.binary_dilation(np.pad(m, r), iterations=r)
        x0, y0 = x0 - r, y0 - r
    elif r < 0:
        e = ndimage.binary_erosion(np.pad(m, 1), iterations=-r)[1:-1, 1:-1]
        if e.sum() >= max(4, area // 4):
            m = e
    if rng.random() < aug.p_trunc and m.sum() >= 20:
        ys, xs = np.nonzero(m)
        th = rng.uniform(0, 2 * math.pi)
        proj = xs * math.cos(th) + ys * math.sin(th)
        keep = proj <= np.quantile(proj, rng.uniform(*aug.trunc_keep))
        mt = np.zeros_like(m)
        mt[ys[keep], xs[keep]] = True
        m = mt
    sig = aug.shift_px + aug.shift_size * eqd
    if rng.random() < aug.p_big_shift:
        sig *= aug.big_shift_mult
    dx, dy = rng.normal(0.0, sig, 2)
    return m, x0 + int(round(dx)), y0 + int(round(dy))


def _split(m: np.ndarray, rng) -> List[np.ndarray]:
    """重心を通る直線で2つに割る (間に 2px の隙間)"""
    ys, xs = np.nonzero(m)
    th = rng.uniform(0, math.pi)
    proj = (xs - xs.mean()) * math.cos(th) + (ys - ys.mean()) * math.sin(th)
    out = []
    for sel in (proj < -1.0, proj > 1.0):
        p = np.zeros_like(m)
        p[ys[sel], xs[sel]] = True
        if p.sum() >= 10:
            out.append(p)
    return out if len(out) == 2 else [m]


def _touching_pairs(ins: np.ndarray, shapes: List[Shape], touch_px: int) -> List[Tuple[int, int]]:
    pairs = set()
    H, W = ins.shape
    for i, (m, x0, y0) in enumerate(shapes):
        r = touch_px + 1
        d = ndimage.binary_dilation(np.pad(m, r), iterations=r)
        ya, xa = y0 - r, x0 - r
        yb, xb = ya + d.shape[0], xa + d.shape[1]
        ca, cb, ra, rb = max(ya, 0), min(yb, H), max(xa, 0), min(xb, W)
        sub = ins[ca:cb, ra:rb][d[ca - ya:cb - ya, ra - xa:rb - xa]]
        for j in np.unique(sub):
            if j > 0 and j - 1 != i:
                pairs.add((min(i, j - 1), max(i, j - 1)))
    return sorted(pairs)


def synth_prior(ins: np.ndarray, rng, aug: Optional[PriorAug] = None, edge_px: int = PRIOR_EDGE_PX,
                keep_ids=()) -> np.ndarray:
    """正解の気泡ラベルマップ (0 = 背景, 1..N の連番) を崩して学習用の事前マスク (2, H, W) を作る。
    rng = np.random.default_rng(...) (同じ rng の状態なら同じ結果)。
    keep_ids の気泡は消さない (degrade_image で画像を崩した気泡。事前マスクで補えるようにする)"""
    aug = aug or PriorAug()
    H, W = ins.shape
    if rng.random() < aug.p_empty:
        return np.zeros((PRIOR_CHANNELS, H, W), np.float32)
    ins = ins.astype(np.int32)
    ids = np.unique(ins)
    ids = ids[ids > 0]
    keep = {int(k) for k in keep_ids}
    if ids.size and (ids[-1] != ids.size):     # 連番に詰める (_touching_pairs が番号 = 位置 + 1 を使うため)
        lut = np.zeros(int(ids[-1]) + 1, np.int32)
        lut[ids] = np.arange(1, ids.size + 1)
        ins = lut[ins]
        keep = {int(lut[k]) for k in keep if 0 < k < lut.size}
    shapes = label_shapes(ins)
    # 接している2個を1個に (前のパスの融合)
    groups = [[i] for i in range(len(shapes))]
    if aug.p_merge > 0 and len(shapes) > 1:
        pairs = _touching_pairs(ins, shapes, aug.touch_px)
        used = set()
        for k in rng.permutation(len(pairs)) if pairs else []:
            i, j = pairs[k]
            if i in used or j in used or rng.random() >= aug.p_merge:
                continue
            used.update((i, j))
            groups[i] = [i, j]
            groups[j] = []
    objs: List[Shape] = []
    for g in groups:
        if not g:
            continue
        if len(g) == 1:
            m, x0, y0 = shapes[g[0]]
        else:
            (ma, xa, ya), (mb, xb, yb) = shapes[g[0]], shapes[g[1]]
            x0, y0 = min(xa, xb), min(ya, yb)
            x1, y1 = max(xa + ma.shape[1], xb + mb.shape[1]), max(ya + ma.shape[0], yb + mb.shape[0])
            p = aug.touch_px + 1
            m = np.zeros((y1 - y0 + 2 * p, x1 - x0 + 2 * p), bool)
            m[ya - y0 + p:ya - y0 + p + ma.shape[0], xa - x0 + p:xa - x0 + p + ma.shape[1]] |= ma
            m[yb - y0 + p:yb - y0 + p + mb.shape[0], xb - x0 + p:xb - x0 + p + mb.shape[1]] |= mb
            m = ndimage.binary_closing(m, iterations=p)
            x0, y0 = x0 - p, y0 - p
        if rng.random() < aug.p_drop and not any(i + 1 in keep for i in g):
            continue
        pieces = [m]
        if m.sum() >= aug.split_min_area and rng.random() < aug.p_split:
            pieces = _split(m, rng)
        for pc in pieces:
            d = _deform(pc, x0, y0, rng, aug)
            if d is not None:
                objs.append(d)
    # 何も無い所の気泡 (正解の気泡の形を写すか、無ければ楕円)
    occ = ndimage.binary_dilation(ins > 0, iterations=3)
    for _ in range(int(rng.poisson(aug.phantom_rate)) if aug.phantom_rate > 0 else 0):
        if shapes:
            m = shapes[int(rng.integers(len(shapes)))][0]
        else:
            a, b = rng.uniform(2, 12, 2)
            yy, xx = np.mgrid[-int(b) - 1:int(b) + 2, -int(a) - 1:int(a) + 2]
            m = (xx / a) ** 2 + (yy / b) ** 2 <= 1.0
        h, w = m.shape
        for _try in range(10):
            x0 = int(rng.integers(-(w // 2), max(1, W - w // 2)))
            y0 = int(rng.integers(-(h // 2), max(1, H - h // 2)))
            ya, yb, xa, xb = max(y0, 0), min(y0 + h, H), max(x0, 0), min(x0 + w, W)
            if ya >= yb or xa >= xb:
                continue
            sub = m[ya - y0:yb - y0, xa - x0:xb - x0]
            if sub.any() and (occ[ya:yb, xa:xb] & sub).sum() <= 0.2 * sub.sum():
                d = _deform(m, x0, y0, rng, aug)
                if d is not None:
                    objs.append(d)
                break
    return render_prior(objs, H, W, edge_px)


@dataclass
class ImageDegrade:
    """学習画像の崩し方 (degrade_image)。前のフレームでは見えていたが このフレームでは輪郭が切れた/薄い 気泡を真似る"""
    n_max: int = 4                 # 1枚で崩す気泡の最大数
    min_area: int = 300            # 崩す気泡の最小面積 (px)。小さい点は崩さない
    p_fade: float = 0.3            # 崩す気泡のうち「輪郭全体を薄くする」の割合 (残りは「輪郭の一部を消す」)
    gap_frac: Tuple[float, float] = (0.1, 0.35)   # 消す輪郭の割合 (周の何割。1〜2か所に分ける)
    fade_keep: Tuple[float, float] = (0.25, 0.6)  # 薄くするとき残す画素の割合 (2値化画像では薄い輪郭は途切れ途切れになる)

    def as_dict(self):
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


def degrade_image(g: np.ndarray, ins: np.ndarray, rng, cfg: Optional[ImageDegrade] = None):
    """画像 g (2値化画像: 輪郭が明るい) のうち、面積 cfg.min_area 以上の気泡を 1〜cfg.n_max 個選んで輪郭を崩す。
    輪郭の帯 (気泡のマスクの縁から内側 6px・外側 2px の明るい画素) の一部を 0 にする (切れ目) か、
    全体を途切れ途切れにする (薄い輪郭)。正解ラベルは変えない。
    戻り値: (崩した画像, 崩した気泡のラベルの組) -> synth_prior(keep_ids=...) に渡して事前マスクには残す"""
    cfg = cfg or ImageDegrade()
    ins = ins.astype(np.int32)
    ids, area = np.unique(ins[ins > 0], return_counts=True)
    cand = ids[area >= cfg.min_area]
    if cand.size == 0:
        return g, ()
    chosen = rng.choice(cand, int(rng.integers(1, min(cfg.n_max, cand.size) + 1)), replace=False)
    g = g.copy()
    H, W = g.shape
    objs = ndimage.find_objects(ins)
    done = []
    for k in chosen:
        sl = objs[int(k) - 1]
        y0, y1, x0, x1 = max(sl[0].start - 3, 0), min(sl[0].stop + 3, H), max(sl[1].start - 3, 0), min(sl[1].stop + 3, W)
        m = ins[y0:y1, x0:x1] == k
        sub = g[y0:y1, x0:x1]
        band = ndimage.binary_dilation(m, iterations=2) & ~ndimage.binary_erosion(m, iterations=6) & (sub > 0)
        if band.sum() < 10:
            continue
        if rng.random() < cfg.p_fade:
            band &= rng.random(band.shape) >= rng.uniform(*cfg.fade_keep)
            sub[band] = 0
        else:
            ys, xs = np.nonzero(m)
            by, bx = np.nonzero(band)
            ang = np.arctan2(by - ys.mean(), bx - xs.mean())
            n_gap = int(rng.integers(1, 3))
            total = rng.uniform(*cfg.gap_frac)
            for _ in range(n_gap):
                d = (ang - rng.uniform(-math.pi, math.pi)) % (2 * math.pi)
                sel = d < 2 * math.pi * total / n_gap
                sub[by[sel], bx[sel]] = 0
        done.append(int(k))
    return g, tuple(done)


# ==============================================================
# 4. 推論
# ==============================================================
class TauDetector:
    """ckpt を読み込み、prob(gray, prior) で 背景/内部/境界 の確率 (3, H, W) を返す。
    tracker3.py の UNetDetector と同じ前後処理 (32 の倍数への反射パディング、学習画像サイズへの拡大縮小)。
    3チャンネルの ckpt (best.pt) なら事前マスクは無視する (UNetDetector と全く同じ結果)。"""

    def __init__(self, ckpt_path, train_hw=None, dev=None):
        import torch
        self.torch = torch
        self.dev = dev or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, ck, self.uses_prior = load_tau_model(ckpt_path, self.dev)
        self.mean = np.array(ck["mean"], np.float32)
        self.std = np.array(ck["std"], np.float32)
        self.edge_px = int(ck.get("prior_edge_px") or PRIOR_EDGE_PX)   # 3チャンネルの ckpt には無い/None のことがある
        hw = ck.get("train_hw") or train_hw
        self.train_hw = (int(hw[0]), int(hw[1])) if hw else None
        self.epoch = ck.get("epoch")
        self._resize_notice = False
        print(f"  U-Net: {ckpt_path}  (epoch {ck.get('epoch')}, device {self.dev}, "
              f"学習画像サイズ {self.train_hw if self.train_hw else '記録なし'}, "
              f"事前マスク入力 {'あり' if self.uses_prior else 'なし (3チャンネルのモデル)'})")
        if self.dev == "cpu":
            print("  ※ GPUが見つかりません。CPUでも動きますが遅くなります。")

    def _forward(self, gray, prior):
        torch = self.torch
        H, W = gray.shape
        ph, pw = (-H) % 32, (-W) % 32
        g = cv2.copyMakeBorder(gray, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
        p = None
        if self.uses_prior and prior is not None:
            p = np.pad(prior.astype(np.float32), ((0, 0), (0, ph), (0, pw)))   # 事前マスクのパディングは 0 (学習と同じ)
        x = make_input(g, p, self.mean, self.std, self.uses_prior)
        x = torch.from_numpy(x)[None].to(self.dev)
        with torch.no_grad():
            out = self.model(x).softmax(1)[0].cpu().numpy()
        return out[:, :H, :W]

    def prob(self, gray, prior=None):
        H, W = gray.shape
        if self.train_hw is None or (H, W) == self.train_hw:
            return self._forward(gray, prior)
        th, tw = self.train_hw
        if not self._resize_notice:
            print(f"  ※ 画像サイズ {H}x{W} が学習画像 {th}x{tw} と異なるため、学習サイズに合わせて推論します")
            self._resize_notice = True
        interp = cv2.INTER_AREA if th * tw < H * W else cv2.INTER_LINEAR
        pr = None
        if self.uses_prior and prior is not None:
            pr = np.stack([cv2.resize(c.astype(np.float32), (tw, th), interpolation=interp) for c in prior])
        p = self._forward(cv2.resize(gray, (tw, th), interpolation=interp), pr)
        return np.stack([cv2.resize(c, (W, H), interpolation=cv2.INTER_LINEAR) for c in p])


# ======================================================================
# [B] 小さい点のラベル補充 (STEP = 'dots') — 元 dot_labels.py
# ======================================================================
# 元 dot_labels.py の説明 (OUT -> DOT_OUT, REVIEW -> DOT_REVIEW):
# 小さい点のラベル補充 — ラベルされていない小さい点を自動で探し、人が確認して、学習データに足す
#
#     python dot_labels.py
#
# なぜ必要か
#   U-Net は画像にはっきり見える小さい点 (731〜790 で 面積 5〜20 px の点が 1フレーム約17個) を「確実に背景」と出す。
#   学習ラベルで小さい点の多くが描かれていない (= 背景だと教えた) ためと考えられる。ラベルが背景だと教える限り、
#   どのモデル (CNN・トランスフォーマー・TAU) に変えても同じように見落とす。そこでラベルを補う。
#
# 流れ
#   [1] 候補: Roboflow の書き出し (SRC) の画像から「光っている小さい塊で、ラベル済みの気泡から離れているもの」を探す。
#       U-Net は使わない (U-Net が見落とす点を探すため。U-Net の出力を見せると判断がそれに引きずられる)
#   [2] 確認: 候補を拡大したタイルで 1ページ GRID 個ずつ表示する。split ごとに明るい候補から順に並ぶ
#       (途中でやめると、残るのは暗い候補 = 無視になる)。タイルの文字は 面積 px / 一番明るい画素の値
#         左クリック   = 気泡でない (n)        右クリック = 分からない (u)       同じクリックをもう一度 = 取り消し
#         Enter/Space  = このページの残りを「気泡」(y) にして次のページ
#         b = 前のページ      q / Esc = 保存して終了 (ウィンドウを閉じても保存される)
#       タイルの色: 黄の輪郭 = この候補 (輪郭は点の外側に描くので点そのものは隠れない), 緑の輪郭 = ラベル済みの気泡,
#                  水色の輪郭 = ほかの候補。枠: 灰 = 未確認, 緑 = 気泡, 赤 (×) = 気泡でない, 橙 (?) = 分からない
#       判定は OUT/decisions.json に保存される。途中でやめても、次に実行すると続きから
#   [3] 書き出し (終了すると自動):
#       OUT/coco/<split>/              元のラベル + 「気泡」(y) にした点を足した COCO (画像もコピー)。
#                                      → 1_tau_unet_train.py の SRC にする
#       OUT/ignore/<split>/<名前>.png  「分からない」(u) と まだ確認していない候補の範囲 (白 = 255)。
#                                      → 1_tau_unet_train.py の IGNORE_SRC にする (学習・評価でその画素を使わない)
#       「気泡でない」(n) は何もしない (今までどおり背景として学習する)
#   確認は test → valid → train の順。test を最後まで確認すると、評価用の test がもれなくラベルされた状態になる
#   (点の再現率を正しく測れるのはこの状態のときだけ)。
#   確認しなかった候補は無視 (ignore) になるので、確認せずに書き出すだけ (REVIEW = False) でも
#   「見えている点を背景だと教える」ことは止められる (点を気泡だと教えることにはならない)。
#
# 相対パスは「このファイルがあるフォルダ」基準。SRC は読むだけで変更しない。

ANN_NAME = '_annotations.coco.json'
IGNORE_VALUE = 255
DECISIONS = ('y', 'n', 'u')   # 気泡 / 気泡でない / 分からない


def _disk(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


# ======================================================================
# [1] 候補
# ======================================================================
def load_split(sdir):
    with open(Path(sdir) / ANN_NAME, encoding='utf-8') as f:
        return json.load(f)


def polygons_of(ann):
    """COCO の注釈 -> ポリゴン (N, 2) のリスト (RLE は 1_tau_unet_train.py と同じく使わない)"""
    seg = ann.get('segmentation')
    if not isinstance(seg, list):
        return []
    return [np.array(s, np.float32).reshape(-1, 2) for s in seg if len(s) >= 6]


def labelled_mask(anns, H, W):
    """ラベル済み気泡の画素 (1_tau_unet_train.py と同じ: ポリゴンの塗りつぶし + 輪郭線)"""
    m = np.zeros((H, W), np.uint8)
    for a in anns:
        for p in polygons_of(a):
            q = p.astype(np.int32)
            cv2.fillPoly(m, [q], 1)
            cv2.polylines(m, [q], True, 1, thickness=1)
    return m > 0


def fill_dot(cm, closed=(False, False, False, False)):
    """光っている画素の塊 (bool) -> 気泡の範囲。輪の穴と、切れた輪 (C 字、切れ目 約4px まで) を埋める。
    膨張 -> 穴埋め -> 収縮 の順 (膨張で切れ目をふさいでから穴を埋める)。埋めるのは塊の凸包の中だけ (小さい気泡はほぼ円)。
    closed: 塊が画像の (上, 下, 左, 右) の端に接しているか。接している側は画像の端を輪の一部とみなす (端で切れた輪)"""
    r = 2
    e = r + 1
    p = np.pad(cm, e).astype(np.uint8)
    d = cv2.dilate(p, _disk(r))
    for side, on in zip(((slice(0, e), slice(None)), (slice(-e, None), slice(None)),
                         (slice(None), slice(0, e)), (slice(None), slice(-e, None))), closed):
        if on:
            d[side] = 1
    d = ndimage.binary_fill_holes(d).astype(np.uint8)
    c = cv2.erode(d, _disk(r), borderType=cv2.BORDER_CONSTANT, borderValue=0)
    hull = np.zeros_like(p)
    cv2.fillConvexPoly(hull, cv2.convexHull(cv2.findNonZero(p)), 1)
    f = ((c > 0) & (hull > 0)) | (p > 0)
    return f[e:-e, e:-e]


def split_pairs(cm, f, min_hole=PAIR_MIN_HOLE):
    """くっついた輪 (穴が min_hole px 以上の輪を 2つ以上含む塊) を、輪ごとに分ける (画素は一番近い穴の輪へ)。
    戻り値: [(範囲, 光っている画素)]。分けないときは [(f, cm)]"""
    if min_hole <= 0:
        return [(f, cm)]
    holes = ndimage.binary_fill_holes(cm) & ~cm
    lab, n = ndimage.label(holes)
    if n < 2:
        return [(f, cm)]
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    strong = [k + 1 for k, sz in enumerate(sizes) if sz >= min_hole]
    if len(strong) < 2:
        return [(f, cm)]
    seeds = np.where(np.isin(lab, strong), lab, 0)
    _, (iy, ix) = ndimage.distance_transform_edt(seeds == 0, return_indices=True)
    owner = seeds[iy, ix]
    return [(f & (owner == k), cm & (owner == k)) for k in strong]


class Cand:
    """候補1つ。mask は (y0, x0) から始まる切り出し (bool)"""
    __slots__ = ('split', 'file', 'x0', 'y0', 'mask', 'lit', 'peak', 'ring', 'pair')

    def __init__(self, split, file, x0, y0, mask, lit, peak, ring, pair=False):
        self.split, self.file, self.x0, self.y0 = split, file, int(x0), int(y0)
        self.mask, self.lit, self.peak, self.ring = mask, int(lit), int(peak), bool(ring)
        self.pair = bool(pair)          # くっついた輪を分けた片方

    @property
    def area(self):
        return int(self.mask.sum())

    @property
    def id(self):
        """判定の保存に使う名前。条件を変えて探し直しても、同じ塊なら同じ名前になる
        (位置・大きさ・光っている画素の数。埋め方を変えても変わらない)"""
        h, w = self.mask.shape
        return f'{self.split}/{self.file}@{self.x0},{self.y0},{w}x{h},{self.lit}'


def find_candidates(gray, labelled, split='', file='', low=CAND_LOW, peak=CAND_PEAK, min_area=CAND_MIN_AREA,
                    max_area=CAND_MAX_AREA, label_gap=LABEL_GAP, pair_min_hole=PAIR_MIN_HOLE):
    """学習画像 1枚の候補。gray: uint8, labelled: ラベル済み気泡の画素 (bool)"""
    H, W = gray.shape
    near = labelled
    if label_gap > 0:
        near = cv2.dilate(labelled.astype(np.uint8), _disk(label_gap)) > 0
    n, lab, st, _ = cv2.connectedComponentsWithStats((gray >= low).astype(np.uint8), connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = (int(v) for v in st[i])
        if a < min_area:
            continue
        cm = lab[y:y + h, x:x + w] == i
        if near[y:y + h, x:x + w][cm].any():
            continue
        f = fill_dot(cm, (y == 0, y + h == H, x == 0, x + w == W))
        parts = split_pairs(cm, f, pair_min_hole)
        for pf, pc in parts:
            lit = int(pc.sum())
            if lit < min_area or pf.sum() > max_area:
                continue
            ys, xs = np.nonzero(pf)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            pk = int(gray[y:y + h, x:x + w][pc].max())
            if pk < peak:
                continue
            out.append(Cand(split, file, x + x0, y + y0, pf[y0:y1, x0:x1], lit, pk, pf.sum() > lit, len(parts) > 1))
    out.sort(key=lambda c: (c.y0, c.x0))
    return out


def scan(src, splits):
    """SRC の各 split の候補。戻り値: (候補のリスト (SPLIT_ORDER の順), {split: COCO の dict})"""
    cands, cocos = [], {}
    for split in splits:
        sdir = Path(src) / split
        if not (sdir / ANN_NAME).exists():
            continue
        d = load_split(sdir)
        cocos[split] = d
        by_img = {}
        for a in d['annotations']:
            by_img.setdefault(a['image_id'], []).append(a)
        n0 = len(cands)
        n_img = 0
        for im in sorted(d['images'], key=lambda m: m['file_name']):
            g = cv2.imread(str(sdir / im['file_name']), cv2.IMREAD_GRAYSCALE)
            if g is None:
                print(f'    読み込み失敗: {sdir / im["file_name"]}')
                continue
            n_img += 1
            lm = labelled_mask(by_img.get(im['id'], []), *g.shape)
            cands += find_candidates(g, lm, split, im['file_name'])
        k = len(cands) - n0
        cands[n0:] = sorted(cands[n0:], key=lambda c: (-c.peak, -c.area, c.file, c.y0, c.x0))   # 明るい順
        print(f'  [{split}] 画像 {n_img}枚  候補 {k}個 (1枚あたり {k / max(n_img, 1):.1f}個)')
    return cands, cocos


# ======================================================================
# 判定の保存
# ======================================================================
def load_decisions(path):
    if not path.exists():
        return {}
    d = json.loads(path.read_text(encoding='utf-8'))
    return {k: v for k, v in d.get('decisions', {}).items() if v in DECISIONS}


def save_decisions(path, dec):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps({'saved': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'decisions': dec},
                              ensure_ascii=False, indent=0), encoding='utf-8')
    os.replace(tmp, path)


# ======================================================================
# [2] 確認画面 (状態と描画は GUI と分けてある: 描画は画像を返すだけ)
# ======================================================================
STATE_COLOR = {None: (110, 110, 110), 'y': (0, 200, 0), 'n': (0, 0, 255), 'u': (0, 165, 255)}
BAR_H = 52


class Review:
    def __init__(self, cands, dec, src, grid=GRID, tile=TILE, min_crop=MIN_CROP):
        self.cands, self.dec, self.src = cands, dec, Path(src)
        self.cols, self.rows = grid
        self.tile, self.min_crop = tile, min_crop
        self.per_page = self.cols * self.rows
        self.n_pages = max(1, -(-len(cands) // self.per_page))
        self.by_img = {}
        for c in cands:
            self.by_img.setdefault((c.split, c.file), []).append(c)
        self._cache = OrderedDict()
        self.anns = {}
        self.page = self.first_open_page()

    # --- 状態 ---
    def page_cands(self, page=None):
        p = self.page if page is None else page
        return self.cands[p * self.per_page:(p + 1) * self.per_page]

    def first_open_page(self):
        for i, c in enumerate(self.cands):
            if c.id not in self.dec:
                return i // self.per_page
        return self.n_pages - 1

    def click(self, k, button):
        """k: ページ内のタイル番号, button: 'left' = 気泡でない / 'right' = 分からない。同じものをもう一度で取り消し"""
        pc = self.page_cands()
        if not 0 <= k < len(pc):
            return
        want = 'n' if button == 'left' else 'u'
        cid = pc[k].id
        if self.dec.get(cid) == want:
            del self.dec[cid]
        else:
            self.dec[cid] = want

    def confirm(self):
        """このページの未確認を「気泡」にして次のページへ。最後のページなら True"""
        for c in self.page_cands():
            self.dec.setdefault(c.id, 'y')
        if self.page >= self.n_pages - 1:
            return True
        self.page += 1
        return False

    def back(self):
        self.page = max(0, self.page - 1)

    def counts(self):
        ids = {c.id for c in self.cands}
        cnt = Counter(v for k, v in self.dec.items() if k in ids)
        return sum(cnt.values()), cnt

    # --- 描画 ---
    def image(self, split, file):
        key = (split, file)
        if key not in self._cache:
            g = cv2.imread(str(self.src / split / file), cv2.IMREAD_GRAYSCALE)
            if g is None:
                raise FileNotFoundError(self.src / split / file)
            self._cache[key] = (g, labelled_mask(self.anns.get(key, []), *g.shape))
            while len(self._cache) > 40:
                self._cache.popitem(last=False)
        return self._cache[key]

    def tile_image(self, c):
        g, lm = self.image(c.split, c.file)
        H, W = g.shape
        h, w = c.mask.shape
        side = max(self.min_crop, max(h, w) + 12)
        cy, cx = c.y0 + h // 2, c.x0 + w // 2
        y0, x0 = cy - side // 2, cx - side // 2
        crop = np.full((side, side), 40, np.uint8)           # 画像の外は暗い灰色
        ya, yb, xa, xb = max(y0, 0), min(y0 + side, H), max(x0, 0), min(x0 + side, W)
        crop[ya - y0:yb - y0, xa - x0:xb - x0] = g[ya:yb, xa:xb]
        t = self.tile
        out = cv2.cvtColor(cv2.resize(crop, (t, t), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR)

        def local(mask, mx0, my0):
            m = np.zeros((side, side), np.uint8)
            mh, mw = mask.shape
            ya2, yb2 = max(my0, y0), min(my0 + mh, y0 + side)
            xa2, xb2 = max(mx0, x0), min(mx0 + mw, x0 + side)
            if yb2 > ya2 and xb2 > xa2:
                m[ya2 - y0:yb2 - y0, xa2 - x0:xb2 - x0] = mask[ya2 - my0:yb2 - my0, xa2 - mx0:xb2 - mx0]
            return m

        def outline(m, color):
            mu = cv2.resize(m, (t, t), interpolation=cv2.INTER_NEAREST)
            ring = (cv2.dilate(mu, np.ones((3, 3), np.uint8)) > 0) & (mu == 0)   # 点の外側に描く
            out[ring] = color

        lab_local = local(lm.astype(np.uint8), 0, 0)
        if lab_local.any():
            outline(lab_local, (0, 200, 0))
        for o in self.by_img.get((c.split, c.file), []):
            if o is not c:
                lo = local(o.mask.astype(np.uint8), o.x0, o.y0)
                if lo.any():
                    outline(lo, (220, 200, 0))
        outline(local(c.mask.astype(np.uint8), c.x0, c.y0), (0, 255, 255))
        st = self.dec.get(c.id)
        col = STATE_COLOR[st]
        cv2.rectangle(out, (0, 0), (t - 1, t - 1), col, 4 if st else 2)
        if st == 'n':
            cv2.line(out, (8, 8), (t - 9, t - 9), col, 3)
            cv2.line(out, (t - 9, 8), (8, t - 9), col, 3)
        elif st == 'u':
            cv2.putText(out, '?', (t - 30, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, col, 3)
        cv2.putText(out, f'{c.area}px / {c.peak}' + (' pair' if c.pair else ''), (6, t - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        return out

    def render(self, note=''):
        t, gap = self.tile, 2
        W = self.cols * (t + gap) - gap
        H = BAR_H + self.rows * (t + gap) - gap
        canvas = np.full((H, W, 3), 30, np.uint8)
        pc = self.page_cands()
        for k, c in enumerate(pc):
            r, q = divmod(k, self.cols)
            y, x = BAR_H + r * (t + gap), q * (t + gap)
            canvas[y:y + t, x:x + t] = self.tile_image(c)
        done, cnt = self.counts()
        head = pc[0] if pc else None
        line1 = (f'{head.split if head else "-"}  {Path(head.file).name if head else ""}   page {self.page + 1}/{self.n_pages}'
                 f'   checked {done}/{len(self.cands)} (y {cnt["y"]} / n {cnt["n"]} / u {cnt["u"]})  {note}')
        line2 = 'L: NOT bubble  R: unsure (2 dots in 1 outline too)  Enter/Space: rest = bubble, next  b: back  q: quit'
        cv2.putText(canvas, line1, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(canvas, line2, (6, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 220, 255), 1)
        return canvas

    def tile_at(self, x, y):
        """画面の座標 -> ページ内のタイル番号 (タイルの外なら -1)"""
        t, gap = self.tile, 2
        if y < BAR_H:
            return -1
        r, q = (y - BAR_H) // (t + gap), x // (t + gap)
        if (y - BAR_H) % (t + gap) >= t or x % (t + gap) >= t or not (0 <= q < self.cols and 0 <= r < self.rows):
            return -1
        return int(r * self.cols + q)


ENTER_GUARD_S = 0.4            # ページが変わってからこの秒数の Enter/Space は無視 (押しっぱなし・二度押しで次のページを見ずに確定しない)


def run_review(rv, dec_path):
    """確認の画面 (OpenCV のウィンドウ)。終わったら判定を保存する"""
    win = 'dot review'
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    h0, w0 = rv.render().shape[:2]
    print(f'  確認の窓 {w0}×{h0} px (下の段が画面に入らなければ GRID / TILE を小さくしてください)')
    state = {'dirty': True, 'shown': 0.0}

    def on_mouse(event, x, y, flags, param):
        if event in (cv2.EVENT_LBUTTONDOWN, cv2.EVENT_RBUTTONDOWN):
            k = rv.tile_at(x, y)
            if k >= 0:
                rv.click(k, 'left' if event == cv2.EVENT_LBUTTONDOWN else 'right')
                state['dirty'] = True

    cv2.setMouseCallback(win, on_mouse)
    note = ''
    try:
        while True:
            if state['dirty']:
                cv2.imshow(win, rv.render(note))
                state['dirty'] = False
            key = cv2.waitKey(30) & 0xFF
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key in (10, 13, 32):
                if time.monotonic() - state['shown'] < ENTER_GUARD_S:
                    continue
                last = rv.confirm()
                state['shown'] = time.monotonic()
                save_decisions(dec_path, rv.dec)
                if last:
                    print('  最後のページまで確認しました')
                    break
                note, state['dirty'] = '', True
            elif key == ord('b'):
                rv.back()
                save_decisions(dec_path, rv.dec)
                state['dirty'], state['shown'] = True, time.monotonic()
            elif key in (ord('q'), 27):
                break
    finally:
        save_decisions(dec_path, rv.dec)
        cv2.destroyAllWindows()


# ======================================================================
# [3] 書き出し
# ======================================================================
def grow(mask, x0, y0, r, H, W):
    """切り出しのマスクを r px 広げる (画像の外は切る)。戻り値 (mask, x0, y0)"""
    if r <= 0:
        return mask, x0, y0
    m = cv2.dilate(np.pad(mask, r).astype(np.uint8), _disk(r)) > 0
    x0, y0 = x0 - r, y0 - r
    ya, xa = max(0, -y0), max(0, -x0)
    yb, xb = min(m.shape[0], H - y0), min(m.shape[1], W - x0)
    return m[ya:yb, xa:xb], x0 + xa, y0 + ya


def mask_to_polygon(mask, x0, y0):
    """マスクの外周 (画素の中心を通る) -> COCO のポリゴン [x1, y1, x2, y2, ...]。
    1_tau_unet_train.py の変換 (fillPoly + polylines) で元のマスクに戻る"""
    cs, _ = cv2.findContours(np.pad(mask, 1).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len).reshape(-1, 2) - 1 + np.array([x0, y0])
    if len(c) < 3:                                       # 1〜2画素 (CAND_MIN_AREA を下げたとき): 3点にする
        c = np.vstack([c, c[-1:], c[:1]])[:3]
    return c.astype(float).ravel().tolist()


def export(src, out, cands, cocos, dec, grow_px=GROW_PX, ignore_pad=IGNORE_PAD):
    """DOT_OUT/coco (元のラベル + y の点) と DOT_OUT/ignore (u と未確認の候補) を作り直す。戻り値: 集計"""
    src, out = Path(src), Path(out)
    for sub in ('coco', 'ignore'):
        t = (out / sub).resolve()
        if t == src.resolve() or t in src.resolve().parents:
            raise ValueError(f'{t} は SRC ({src}) を含むので消せません。DOT_OUT を別のフォルダにしてください')
        if (out / sub).exists():
            shutil.rmtree(out / sub)
    by_img = {}
    for c in cands:
        by_img.setdefault((c.split, c.file), []).append(c)
    summary = {}
    for split, d in cocos.items():
        cdir, idir = out / 'coco' / split, out / 'ignore' / split
        cdir.mkdir(parents=True, exist_ok=True)
        idir.mkdir(parents=True, exist_ok=True)       # 無視する所が無くても作る (IGNORE_SRC に指定しても止まらない)
        anns = list(d['annotations'])
        next_id = max((int(a.get('id', 0)) for a in anns), default=0) + 1
        cat_count = Counter(a.get('category_id') for a in anns)
        cat = cat_count.most_common(1)[0][0] if cat_count else (d.get('categories') or [{'id': 1}])[-1]['id']
        s = Counter()
        for im in d['images']:
            fn = im['file_name']
            if not (src / split / fn).exists():           # 学習スクリプトと同じく飛ばす (COCO の記載はそのまま)
                print(f'    画像がありません (飛ばします): {src / split / fn}')
                s['missing_images'] += 1
                continue
            (cdir / fn).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / split / fn, cdir / fn)
            H, W = int(im['height']), int(im['width'])
            ign = np.zeros((H, W), np.uint8)
            for c in by_img.get((split, fn), []):
                st = dec.get(c.id)
                s[st or 'unchecked'] += 1
                if st == 'y':
                    m, x0, y0 = grow(c.mask, c.x0, c.y0, grow_px, H, W)
                    poly = mask_to_polygon(m, x0, y0)
                    xs, ys = poly[0::2], poly[1::2]
                    anns.append({'id': next_id, 'image_id': im['id'], 'category_id': cat, 'segmentation': [poly],
                                 'area': float(m.sum()),
                                 'bbox': [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)],
                                 'iscrowd': 0, 'source': 'dot_labels'})
                    next_id += 1
                elif st != 'n':                          # 分からない / 未確認 -> 無視
                    m, x0, y0 = grow(c.mask, c.x0, c.y0, ignore_pad, H, W)
                    h, w = m.shape
                    ign[y0:y0 + h, x0:x0 + w][m] = IGNORE_VALUE
            if ign.any():
                cv2.imwrite(str(idir / (Path(fn).stem + '.png')), ign)
                s['ignore_images'] += 1
        nd = dict(d)
        nd['annotations'] = anns
        (cdir / ANN_NAME).write_text(json.dumps(nd, ensure_ascii=False), encoding='utf-8')
        summary[split] = dict(s)
        print(f'  [{split}] 気泡として追加 {s["y"]}個 / 気泡でない {s["n"]}個 / 無視 (分からない {s["u"]}個 + '
              f'未確認 {s["unchecked"]}個, 画像 {s["ignore_images"]}枚)')
    (out / 'export_summary.json').write_text(json.dumps(
        {'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'src': str(src), 'per_split': summary,
         'params': params()}, ensure_ascii=False, indent=1), encoding='utf-8')
    return summary


def params():
    return {'CAND_LOW': CAND_LOW, 'CAND_PEAK': CAND_PEAK, 'CAND_MIN_AREA': CAND_MIN_AREA,
            'CAND_MAX_AREA': CAND_MAX_AREA, 'LABEL_GAP': LABEL_GAP, 'IGNORE_PAD': IGNORE_PAD, 'GROW_PX': GROW_PX}


# ======================================================================
def main_dots():
    src, out = resolve(SRC), resolve(DOT_OUT)
    if not src.exists():
        raise FileNotFoundError(f'SRC フォルダがありません: {src}')
    rs, ro = src.resolve(), out.resolve()
    if rs == ro or rs in ro.parents or ro in rs.parents:
        raise ValueError('DOT_OUT と SRC は、片方がもう片方の中に入らない別のフォルダにしてください '
                         '(書き出しで DOT_OUT/coco, DOT_OUT/ignore を作り直すので、SRC が DOT_OUT の中にあると消えてしまう)')
    splits = [s for s in SPLIT_ORDER if (src / s / ANN_NAME).exists()]
    others = sorted(p.name for p in src.iterdir() if p.is_dir() and (p / ANN_NAME).exists() and p.name not in splits)
    splits += others
    if not splits:
        raise FileNotFoundError(f'{src} の中に {ANN_NAME} のあるフォルダ (train/ valid/ test/) がありません')

    print('\n[1] 候補を探す')
    cands, cocos = scan(src, splits)
    dec_path = out / 'decisions.json'
    dec = load_decisions(dec_path)
    ids = {c.id for c in cands}
    old = sum(1 for k in dec if k not in ids)
    print(f'  候補 合計 {len(cands)}個。保存済みの判定 {len(dec) - old}個'
          + (f' (今の候補に無い判定 {old}個は使わない: 条件を変えた?)' if old else ''))

    if DOT_REVIEW and cands:
        print('\n[2] 確認 (左クリック = 気泡でない, 右クリック = 分からない, Enter = 残りを気泡にして次, q = 終了)')
        rv = Review(cands, dec, src)
        for split, d in cocos.items():
            files = {m['id']: m['file_name'] for m in d['images']}
            for a in d['annotations']:
                rv.anns.setdefault((split, files.get(a['image_id'])), []).append(a)
        run_review(rv, dec_path)
        dec = rv.dec
        done, cnt = rv.counts()
        print(f'  確認済み {done}/{len(cands)} (気泡 {cnt["y"]} / 気泡でない {cnt["n"]} / 分からない {cnt["u"]})')
    else:
        save_decisions(dec_path, dec)

    print('\n[3] 書き出し')
    summary = export(src, out, cands, cocos, dec)
    t = summary.get('test', {})
    if t.get('unchecked'):
        print(f'  ※ test に未確認の候補が {t["unchecked"]}個あります。test は評価に使うので、最後まで確認するのがおすすめです')
    print("\n次は STEP = 'train' で学習 (USE_DOT_LABELS = True ならこの結果を自動で使う。"
          "ラベル補充の効果だけを比べるなら USE_PRIOR = False)")


# ======================================================================
# [C] 学習 (STEP = 'train') — 元 1_tau_unet_train.py
# ======================================================================
# 元 1_tau_unet_train.py の説明:
# Tracking-aware U-Net (TAU) の学習 — 1_unet_train.py に「事前マスク」の入力を足したもの
#
#     python 1_tau_unet_train.py
#
# 1_unet_train.py との違い
#   - 入力が 5チャンネル: 画像 ×3 (今までと同じ) + 事前マスク 2枚 (このフレームに気泡がどこにあるはずか: 内部・輪郭)
#     推論 (tau_tracker.py) では、前のパスのトラッカーが前後のフレームから予測した気泡マスクが入る
#   - 学習用の事前マスクは、正解ラベルの気泡を崩して作る (tau_unet.synth_prior)。連続フレームのラベルは要らない
#       見落とし (消す) / 位置ずれ / 変形 / 一部欠け / 隣と融合 / 割れ / 何も無い所の気泡 / 事前マスクなし
#     -> 「事前マスクを参考にするが、画像に無いものは出さない・画像にあるものは事前マスクに無くても出す」を学ぶ
#   - FINETUNE_FROM (今の best.pt) から始める。最初の畳み込みに事前マスク用の重みを 0 で足すので、
#     学習前は best.pt と全く同じ結果 = 「今より悪くならない所」から始まる
#   - val は「事前マスクなし」と「事前マスクあり (正解から作ったもの。毎 epoch 同じ)」の両方で評価する。
#     best は BEST_BY で選ぶ (既定: 崩した画像・事前マスクありの点数が最高の epoch。ただし元の画像・事前マスクなしの点数が
#     開始モデルより BEST_EMPTY_TOL 以上下がった epoch は選ばない)。毎 epoch「事前の効果」(崩した画像での ありとなしの
#     境界 IoU の差) と事前マスク用の重みの大きさも表示する (0 のままなら事前マスクを使っていない)
#     「写し」= 事前マスクにあって正解では背景の画素を、気泡と出した割合 (事前マスクをそのまま写していないかの目安。低いほどよい)
#   - 正解の気泡ごとのラベルマップ (instances/) もデータセットに保存する (事前マスクを作るため)
#   - 画像を崩す増強 (DEGRADE_*): 学習画像の気泡の輪郭を一部消す / 途切れ途切れにし、その気泡は事前マスクに必ず残す
#     (正解ラベルはそのまま)。学習画像は輪郭がはっきりしていて画像だけで正解が分かるため、崩さないと事前マスクを全く使わない
#     ことが 1回目の学習 (80 epoch で事前の効果 +0.0001) で分かった。val も「崩した画像」で事前なし/ありを比べる
#   - 小さい点のラベル補充 (dot_labels.py) の結果を使える: SRC = dot_labels の coco/ (点を足したラベル)、
#     IGNORE_SRC = dot_labels の ignore/ (確認していない点の候補 = 学習しない画素)
#   - USE_PRIOR = False で事前マスクなしの普通の U-Net (3チャンネル) も学習できる (tracker3.py / watershed.py でそのまま使える)。
#     ラベル補充の効果だけを比べるときはこちら
#
# 流れ
#   [1] Roboflow の COCO-segmentation 書き出し → 3クラスのマスク (0=背景, 1=気泡内部, 2=気泡境界) + 気泡ごとのラベルマップ (DST)
#   [2] 学習 → OUT/best.pt (tau_tracker.py の UNET_CKPT に入れる)
#   [3] test で確認 → 画素 IoU、気泡の大きさ別の再現率・適合率 (事前マスクなし / あり, FINETUNE_FROM との比較)
#
# tau_unet.py を同じフォルダに置くこと。相対パスは「このファイルがあるフォルダ」基準。
# OUT が既にあれば runs/tau2, runs/tau3 ... を新しく作る (前の結果を上書きしない)。

HERE = Path(__file__).resolve().parent

MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
SPLIT_MAP = {'train': 'train', 'valid': 'val', 'val': 'val', 'test': 'test'}
IGNORE_LABEL = 255            # マスクの「学習しない」画素 (IGNORE_SRC)。損失・評価で除く


def prior_aug():
    return PriorAug(
        p_empty=PRIOR_P_EMPTY, p_drop=PRIOR_P_DROP, shift_px=PRIOR_SHIFT_PX, shift_size=PRIOR_SHIFT_SIZE,
        p_big_shift=PRIOR_P_BIG_SHIFT, scale=tuple(PRIOR_SCALE), morph_px=PRIOR_MORPH_PX, p_trunc=PRIOR_P_TRUNC,
        p_merge=PRIOR_P_MERGE, p_split=PRIOR_P_SPLIT, phantom_rate=PRIOR_PHANTOM_RATE)


def degrade_cfg():
    return ImageDegrade(n_max=DEGRADE_N_MAX, min_area=DEGRADE_MIN_AREA, p_fade=DEGRADE_P_FADE,
                                 gap_frac=tuple(DEGRADE_GAP), fade_keep=tuple(DEGRADE_FADE_KEEP))


def resolve(p):
    """相対パスはこのファイルがあるフォルダ基準"""
    p = Path(p)
    return p if p.is_absolute() else HERE / p


def list_images(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def unique_dir(base):
    """base が既にあれば base2, base3 ... (前の結果を守る)"""
    base = Path(base)
    if not base.exists():
        return base
    i = 2
    while Path(f'{base}{i}').exists():
        i += 1
    return Path(f'{base}{i}')


# ======================================================================
# [1] COCO ポリゴン → 3クラスのマスク + 気泡ごとのラベルマップ
# ======================================================================
def edge_thickness(w, h, base):
    """小さい気泡は境界を細く (境界が内部を覆って気泡が消えないように)"""
    s = min(w, h)
    if s < 12:
        return 1
    if s < 24:
        return max(1, base - 1)
    return base


def make_target(anns, H, W, base_px):
    """anns: [(polys, bbox_w, bbox_h), ...] → (3クラスのラベル uint8 (0/1/2), 気泡ごとのラベルマップ uint16 (0 = 背景, 1..N))
    3クラスのラベルは 1_unet_train.py と全く同じ"""
    lbl = np.zeros((H, W), np.uint8)
    ins = np.zeros((H, W), np.uint16)
    fills = []
    for k, (polys, bw, bh) in enumerate(anns, start=1):            # 1) 内部を全部塗る
        f = np.zeros((H, W), np.uint8)
        for p in polys:
            cv2.fillPoly(f, [p.astype(np.int32)], 1)
        fills.append(f)
        lbl[f > 0] = 1
        ins[f > 0] = k                                             #    気泡ごと (重なりは後の気泡)
    for (polys, bw, bh), f in zip(anns, fills):                    # 2) 境界を上書き (くっついた気泡の間 = 壁)
        t = edge_thickness(bw, bh, base_px)
        for p in polys:
            cv2.polylines(lbl, [p.astype(np.int32)], True, 2, thickness=t)
    for f in fills:                                                # 3) 気泡ごとに内部を最低1画素
        inside = f > 0
        if inside.sum() == 0:
            continue
        if not np.any(lbl[inside] == 1):
            d = cv2.distanceTransform(f, cv2.DIST_L2, 3)
            y, x = np.unravel_index(np.argmax(d), d.shape)
            lbl[y, x] = 1
    return lbl, ins


def label_preview(gray, lbl, prior=None):
    """緑 = 内部, 赤 = 境界, 青 = 学習しない (IGNORE_SRC)。prior があれば 黄 = 事前マスクの輪郭"""
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    ov = bgr.copy()
    ov[lbl == 1] = (0, 160, 0)
    ov[lbl == 2] = (0, 0, 255)
    ov[lbl == IGNORE_LABEL] = (255, 120, 0)
    out = cv2.addWeighted(bgr, 0.5, ov, 0.5, 0)
    if prior is not None:
        out[prior[1] > 0.5] = (0, 255, 255)
    return out


def load_coco(json_path):
    with open(json_path, encoding='utf-8') as f:
        d = json.load(f)
    by_img = {}
    for a in d['annotations']:
        seg = a.get('segmentation')
        if not isinstance(seg, list):                 # RLE は未対応
            continue
        polys = [np.array(s, np.float32).reshape(-1, 2) for s in seg if len(s) >= 6]
        if not polys:
            continue
        bw, bh = a['bbox'][2], a['bbox'][3]
        by_img.setdefault(a['image_id'], []).append((polys, bw, bh))
    return d['images'], by_img


def apply_ignore(lbl, ign):
    """IGNORE_SRC の白い所のうち、ラベルが背景の画素だけを IGNORE_LABEL にする (ラベル済みの気泡はそのまま)"""
    if ign.shape != lbl.shape:
        raise ValueError(f'ignore マスクの大きさ {ign.shape} が画像 {lbl.shape} と違います')
    lbl[(ign > 0) & (lbl == 0)] = IGNORE_LABEL
    return lbl


def build_dataset(src, dst, edge_px, n_preview, ignore_src=None):
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise FileNotFoundError(f'SRC フォルダがありません: {src}')
    if ignore_src is not None and not Path(ignore_src).exists():
        raise FileNotFoundError(f'IGNORE_SRC フォルダがありません: {ignore_src}')
    for sub in ('images', 'masks', 'instances', 'preview'):
        if (dst / sub).exists():
            shutil.rmtree(dst / sub)
    gt_counts = {}
    found = False
    for sdir in sorted(src.iterdir()):
        if not sdir.is_dir() or sdir.name not in SPLIT_MAP:
            continue
        jp = sdir / '_annotations.coco.json'
        if not jp.exists():
            print(f'  [{sdir.name}] _annotations.coco.json なし — 飛ばす')
            continue
        found = True
        split = SPLIT_MAP[sdir.name]
        outs = {s: dst / s / split for s in ('images', 'masks', 'instances', 'preview')}
        for p in outs.values():
            p.mkdir(parents=True, exist_ok=True)
        images, by_img = load_coco(jp)
        stats = np.zeros(3, np.int64)
        n_inst = n_tiny = n_ok = n_ign_img = n_ign_px = 0
        for i, im in enumerate(images):
            ip = sdir / im['file_name']
            gray = cv2.imread(str(ip), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                print(f'    読み込み失敗: {ip}')
                continue
            H, W = gray.shape
            anns = by_img.get(im['id'], [])
            if len(anns) > 65535:
                raise RuntimeError(f'{ip}: 気泡が多すぎます ({len(anns)}個)')
            lbl, ins = make_target(anns, H, W, edge_px)
            stem = Path(im['file_name']).stem
            if ignore_src is not None:
                ign = cv2.imread(str(Path(ignore_src) / sdir.name / (stem + '.png')), cv2.IMREAD_GRAYSCALE)
                if ign is not None:
                    lbl = apply_ignore(lbl, ign)
                    n_ign_img += 1
                    n_ign_px += int((lbl == IGNORE_LABEL).sum())
            shutil.copy2(ip, outs['images'] / (stem + ip.suffix))
            cv2.imwrite(str(outs['masks'] / (stem + '.png')), lbl)
            cv2.imwrite(str(outs['instances'] / (stem + '.png')), ins)      # uint16 PNG
            gt_counts[f'{split}/{stem}'] = len(anns)
            stats += np.bincount(lbl.ravel(), minlength=3)[:3]
            n_inst += len(anns)
            n_tiny += sum(1 for _, bw, bh in anns if min(bw, bh) < 12)
            n_ok += 1
            if i < n_preview:
                cv2.imwrite(str(outs['preview'] / (stem + '.png')), label_preview(gray, lbl))
        frac = stats / max(stats.sum(), 1)
        print(f'  [{sdir.name} -> {split}] 画像 {n_ok}枚  気泡 {n_inst}個 (一辺 12px 未満 {n_tiny}個)'
              f'   画素の割合 背景 {frac[0]:.3f} 内部 {frac[1]:.3f} 境界 {frac[2]:.4f}'
              + (f'   学習しない画素 {n_ign_px}個 ({n_ign_img}枚)' if ignore_src is not None else ''))
    if not found:
        raise FileNotFoundError(f'{src} の中に train/ valid/ test/ と _annotations.coco.json がありません')

    # valid が無ければ train の 10% を val に (ファイル名順。毎回同じ分け方)
    if not list_images(dst / 'images' / 'val'):
        tr = list_images(dst / 'images' / 'train')
        mv = tr[::10]
        for sub in ('images', 'masks', 'instances'):
            (dst / sub / 'val').mkdir(parents=True, exist_ok=True)
        for p in mv:
            shutil.move(str(p), str(dst / 'images' / 'val' / p.name))
            for sub in ('masks', 'instances'):
                shutil.move(str(dst / sub / 'train' / (p.stem + '.png')), str(dst / sub / 'val' / (p.stem + '.png')))
            gt_counts[f'val/{p.stem}'] = gt_counts.pop(f'train/{p.stem}', 0)
        print(f'  valid フォルダが無いので train の {len(mv)}枚を val に分けました')
    (dst / 'gt_counts.json').write_text(json.dumps(gt_counts, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'  → {dst}   (ラベル確認: {dst / "preview"}  — くっついた気泡の間に赤い境界線があること)')


# ======================================================================
# [2] 学習
# ======================================================================
def build_paste_bank(imgs, mask_dir, max_area):
    """学習画像から「離れて1個だけある小さい気泡」をマスクごと切り出して集める → Copy-Paste の材料"""
    bank = []
    for ip in imgs:
        g = cv2.imread(str(ip), cv2.IMREAD_GRAYSCALE)
        m = cv2.imread(str(Path(mask_dir) / (ip.stem + '.png')), cv2.IMREAD_GRAYSCALE)
        if g is None or m is None:
            continue
        H, W = m.shape
        n, lab, st, _ = cv2.connectedComponentsWithStats(((m == 1) | (m == 2)).astype(np.uint8), 8)
        for i in range(1, n):
            x, y, w, h, a = st[i]
            if a < 4 or a >= max_area:
                continue
            if x == 0 or y == 0 or x + w >= W or y + h >= H:           # 画面端で切れた気泡は除く
                continue
            comp = lab[y:y + h, x:x + w] == i
            lp = m[y:y + h, x:x + w].copy()
            lp[~comp] = 0
            if ndimage.label(lp == 1)[1] != 1:                         # 内部がちょうど1つ = 気泡1個
                continue
            bank.append((g[y:y + h, x:x + w].copy(), lp, comp))
    return bank


class BubbleDS(Dataset):
    """(入力 5チャンネル, 3クラスのラベル) を返す。増強は cv2/numpy だけ。
    prior_mode: "synth" = 正解から事前マスクを作る / "empty" = 事前マスクなし (全部 0)
    学習 (train=True) は毎回違う事前マスク、val/test は画像ごとに毎回同じ事前マスク"""

    def __init__(self, root, split, crop_h, crop_w, train, prior_mode='synth', aug=None):
        self.imgs = list_images(Path(root) / 'images' / split)
        self.mask_dir = Path(root) / 'masks' / split
        self.ins_dir = Path(root) / 'instances' / split
        self.ch, self.cw, self.train = crop_h, crop_w, train
        self.prior_mode = prior_mode
        self.val_degrade = False      # val/test で画像を崩して評価するか (毎回同じ崩し方)
        self.aug = aug or prior_aug()
        for d, what in ((self.mask_dir, 'マスク'), (self.ins_dir, '気泡ごとのラベルマップ')):
            missing = [p.name for p in self.imgs if not (d / (p.stem + '.png')).exists()]
            if missing:
                raise FileNotFoundError(f'{what}がありません ({len(missing)}枚)。例: {missing[:3]}  '
                                        '→ REBUILD_DATASET = True で作り直してください')
        self.mean = np.array(MEAN, np.float32)
        self.std = np.array(STD, np.float32)
        self.bank = build_paste_bank(self.imgs, self.mask_dir, CP_MAX_AREA) if (train and COPY_PASTE) else []

    def __len__(self):
        return len(self.imgs)

    def _copy_paste(self, g, m, ins):
        """材料の気泡を、今ある気泡と重ならない空いた所に貼る。ラベルと気泡ごとのラベルも一緒に"""
        if not self.bank or np.random.rand() >= CP_PROB:
            return g, m, ins
        g, m, ins = g.copy(), m.copy(), ins.copy()
        H, W = g.shape
        nxt = int(ins.max()) + 1
        occ = cv2.dilate((m >= 1).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # 今ある気泡・学習しない所 + 2px の余裕
        for _ in range(np.random.randint(1, CP_MAX + 1)):
            gp, lp, cp = self.bank[np.random.randint(len(self.bank))]
            if np.random.rand() < 0.5:
                gp, lp, cp = gp[:, ::-1], lp[:, ::-1], cp[:, ::-1]
            h, w = cp.shape
            if h + 2 >= H or w + 2 >= W or nxt >= 65535:
                continue
            for _try in range(10):
                y = np.random.randint(1, H - h - 1)
                x = np.random.randint(1, W - w - 1)
                if not occ[y:y + h, x:x + w][cp].any():
                    break
            else:
                continue
            a = np.random.uniform(*CP_ALPHA)
            rg, rm, ri = g[y:y + h, x:x + w], m[y:y + h, x:x + w], ins[y:y + h, x:x + w]
            rg[cp] = np.clip(gp[cp].astype(np.float32) * a, 0, 255).astype(np.uint8)
            rm[cp] = lp[cp]
            ri[cp] = nxt
            nxt += 1
            occ[y - 1:y + h + 1, x - 1:x + w + 1] |= cv2.dilate(
                np.pad(cp, 1).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        return g, m, ins

    def _pad(self, g, m, ins, ph, pw):
        if ph or pw:
            g = cv2.copyMakeBorder(g, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
            m = cv2.copyMakeBorder(m, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
            ins = np.pad(ins, ((0, ph), (0, pw)))        # 気泡ごとのラベルは 0 で埋める (鏡像の気泡は事前マスクに入れない)
        return g, m, ins

    def _pad32(self, g, m, ins):
        H, W = g.shape
        return self._pad(g, m, ins, (-H) % 32, (-W) % 32)

    def _augment(self, g, m, ins):
        if AUG_RANDOM_CROP:
            H, W = g.shape
            g, m, ins = self._pad(g, m, ins, max(0, self.ch - H), max(0, self.cw - W))
            H, W = g.shape
            y = np.random.randint(0, H - self.ch + 1)
            x = np.random.randint(0, W - self.cw + 1)
            g, m, ins = g[y:y + self.ch, x:x + self.cw], m[y:y + self.ch, x:x + self.cw], ins[y:y + self.ch, x:x + self.cw]
        else:
            g, m, ins = self._pad32(g, m, ins)
        g, m, ins = self._copy_paste(np.ascontiguousarray(g), np.ascontiguousarray(m), np.ascontiguousarray(ins))
        H, W = g.shape
        if AUG_FLIP and np.random.rand() < 0.5:                        # 左右反転 (上下は流れの向きがあるのでしない)
            g, m, ins = g[:, ::-1], m[:, ::-1], ins[:, ::-1]
        if AUG_ROTATE and np.random.rand() < 0.5:                      # ±5° 回転
            ang = np.random.uniform(-5, 5)
            M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, 1.0)
            g = cv2.warpAffine(np.ascontiguousarray(g), M, (W, H), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REFLECT_101)
            m = cv2.warpAffine(np.ascontiguousarray(m), M, (W, H), flags=cv2.INTER_NEAREST,
                               borderMode=cv2.BORDER_REFLECT_101)
            ins = cv2.warpAffine(np.ascontiguousarray(ins), M, (W, H), flags=cv2.INTER_NEAREST,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if AUG_BRIGHTNESS and np.random.rand() < 0.7:
            alpha = np.random.uniform(0.8, 1.2)
            beta = np.random.uniform(-0.2, 0.2) * 255
            g = np.clip(g.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)
        return np.ascontiguousarray(g), np.ascontiguousarray(m), np.ascontiguousarray(ins)

    def load(self, i):
        ip = self.imgs[i]
        g = cv2.imread(str(ip), cv2.IMREAD_GRAYSCALE)
        m = cv2.imread(str(self.mask_dir / (ip.stem + '.png')), cv2.IMREAD_GRAYSCALE)
        ins = cv2.imread(str(self.ins_dir / (ip.stem + '.png')), cv2.IMREAD_UNCHANGED)
        if ins is None or ins.shape != m.shape:
            raise RuntimeError(f'{ip.stem}: 気泡ごとのラベルマップが読めないか大きさが違います')
        return g, m, ins

    def prior_for(self, i, ins, keep=()):
        """事前マスク。keep (画像を崩した気泡) は消さず、事前マスクなしにもしない"""
        if self.prior_mode == 'empty' or not USE_PRIOR:
            return None
        rng = np.random.default_rng(np.random.randint(0, 2 ** 31 - 1)) if self.train else np.random.default_rng((SEED, i))
        aug = replace(self.aug, p_empty=0.0) if keep else self.aug
        return synth_prior(ins, rng, aug, keep_ids=keep)

    def sample(self, i, force_degrade=False):
        """(画像, 3クラスのラベル, 気泡ごとのラベル, 崩した気泡, 事前マスク)"""
        g, m, ins = self.load(i)
        g, m, ins = self._augment(g, m, ins) if self.train else self._pad32(g, m, ins)
        keep = ()
        if not USE_PRIOR:             # 3チャンネル: 画像を崩さない (事前マスクで補えないので、正解と画像が合わなくなるだけ)
            pass
        elif self.train and (force_degrade or (DEGRADE_P > 0 and np.random.rand() < DEGRADE_P)):
            g, keep = degrade_image(g, ins, np.random.default_rng(np.random.randint(0, 2 ** 31 - 1)), degrade_cfg())
        elif not self.train and self.val_degrade:
            g, keep = degrade_image(g, ins, np.random.default_rng((SEED, i, 7)), degrade_cfg())
        return g, m, ins, keep, self.prior_for(i, ins, keep)

    def __getitem__(self, i):
        g, m, ins, keep, prior = self.sample(i)
        x = make_input(g, prior, self.mean, self.std, uses_prior=USE_PRIOR)
        return torch.from_numpy(x), torch.from_numpy(m.astype(np.int64))


def save_cp_preview(ds, folder, n):
    """増強の確認: 左 = 元の画像とラベル, 右 = 増強後 (画像を崩したもの) + 事前マスクの輪郭 (黄)"""
    if n <= 0 or not ds.imgs:
        return
    folder.mkdir(parents=True, exist_ok=True)
    state = np.random.get_state()
    for k in range(n):
        i = k % len(ds.imgs)
        g, m, ins = ds.load(i)
        ag, am, ai, keep, prior = ds.sample(i, force_degrade=DEGRADE_P > 0)
        H = min(g.shape[0], ag.shape[0])
        left = label_preview(g[:H], m[:H])
        right = label_preview(ag[:H], am[:H], None if prior is None else prior[:, :H])
        if left.shape[1] != right.shape[1]:
            right = cv2.resize(right, (int(right.shape[1] * H / right.shape[0]), H))
        cv2.imwrite(str(folder / f'aug_{k:02d}.png'), np.hstack([left, np.full((H, 6, 3), 255, np.uint8), right]))
    np.random.set_state(state)
    print(f'  増強・事前マスクの確認画像 → {folder}  (左: 元, 右: 増強後 + 事前マスクの輪郭 = 黄。'
          f'輪郭の一部が消えた/途切れた気泡にも黄の輪郭があれば正常)')


@torch.no_grad()
def evaluate(model, dl, dev, n_cls=3):
    """クラスごとの画素 IoU [背景, 内部, 境界] と「写し」(事前マスクにあって正解は背景の画素を気泡と出した割合)。
    学習しない画素 (IGNORE_LABEL) は数えない"""
    model.eval()
    conf = torch.zeros(n_cls, n_cls, dtype=torch.long)
    copy_hit = copy_all = 0
    for x, y in dl:
        p = model(x.to(dev)).argmax(1).cpu()
        ok = y.view(-1) != IGNORE_LABEL
        idx = y.view(-1)[ok] * n_cls + p.view(-1)[ok]
        conf += torch.bincount(idx, minlength=n_cls ** 2).view(n_cls, n_cls)
        if x.shape[1] > IMAGE_CHANNELS:
            ph = (x[:, IMAGE_CHANNELS] > 0.5) & (y == 0)
            copy_all += int(ph.sum())
            copy_hit += int((ph & (p > 0)).sum())
    tp = conf.diag().float()
    iou = tp / (conf.sum(0) + conf.sum(1) - tp).float().clamp(min=1)
    return {'iou': iou.tolist(), 'copy': copy_hit / copy_all if copy_all else None}


def score_of(ev):
    return 0.4 * ev['iou'][1] + 0.6 * ev['iou'][2]   # 境界 IoU を重く (気泡の分け方を決める)


def evaluate_both(model, ds, dev):
    """val を3通りで評価: empty = 元の画像・事前なし (今までどおり出せているか) /
    deg_empty = 崩した画像・事前なし / deg_synth = 崩した画像・事前あり (事前マスクで補えているか)。
    USE_PRIOR = False なら empty だけ"""
    if not USE_PRIOR:
        ds.prior_mode, ds.val_degrade = 'empty', False
        ev = evaluate(model, DataLoader(ds, 1, shuffle=False, num_workers=WORKERS), dev)
        return {'empty': ev, 'score': score_of(ev)}
    out = {}
    for name, mode, deg in (('empty', 'empty', False), ('deg_empty', 'empty', True), ('deg_synth', 'synth', True)):
        ds.prior_mode, ds.val_degrade = mode, deg
        out[name] = evaluate(model, DataLoader(ds, 1, shuffle=False, num_workers=WORKERS), dev)
    ds.prior_mode, ds.val_degrade = 'synth', False
    out['score'] = (score_of(out['deg_synth']) if BEST_BY == 'prior'
                    else 0.5 * (score_of(out['empty']) + score_of(out['deg_synth'])))
    return out


def make_losses(dev):
    """(CE, Dice)。どちらも学習しない画素 (IGNORE_LABEL) を除く。学習しない画素が無ければ今までと同じ値"""
    w = torch.tensor([1.0, 1.0, EDGE_W], device=dev)
    return nn.CrossEntropyLoss(weight=w, ignore_index=IGNORE_LABEL), make_dice()


def make_dice():
    """Dice 損失。学習しない画素 (IGNORE_LABEL) を除く (学習しない画素が無ければ今までと同じ値)"""
    try:
        return smp.losses.DiceLoss(mode='multiclass', ignore_index=IGNORE_LABEL)
    except TypeError:             # 古い segmentation_models_pytorch
        if IGNORE_SRC:
            raise SystemExit('この segmentation_models_pytorch は DiceLoss の ignore_index に対応していません。'
                             'pip install -U segmentation-models-pytorch で更新してください')
        return smp.losses.DiceLoss(mode='multiclass')


def prior_weight(first_conv):
    """最初の畳み込みの事前マスク用の重みの大きさ (平均, 最大)。開始時は 0。小さいままなら事前マスクを使っていない"""
    w = first_conv.detach()[:, IMAGE_CHANNELS:].abs()
    return (float(w.mean()), float(w.max())) if w.numel() else (0.0, 0.0)


def fmt_eval(ev):
    if 'deg_synth' not in ev:     # USE_PRIOR = False
        e = ev['empty']['iou']
        return f'[val] 内部 {e[1]:.3f} 境界 {e[2]:.3f}'
    e, de, ds_ = ev['empty']['iou'], ev['deg_empty']['iou'], ev['deg_synth']['iou']
    cp = ev['deg_synth']['copy']
    return (f'[元の画像・事前なし] 内部 {e[1]:.3f} 境界 {e[2]:.3f} | [崩した画像] 境界 事前なし {de[2]:.3f} -> '
            f'事前あり {ds_[2]:.3f} (事前の効果 {ds_[2] - de[2]:+.4f}) 写し {"-" if cp is None else f"{100 * cp:.1f}%"}')


def make_model(dev):
    """FINETUNE_FROM (3チャンネル) から 5チャンネルのモデルを作る (事前マスクの重み = 0)。None なら ImageNet から。
    USE_PRIOR = False なら 3チャンネルのまま"""
    in_ch = IMAGE_CHANNELS + (PRIOR_CHANNELS if USE_PRIOR else 0)
    if FINETUNE_FROM:
        path = resolve(FINETUNE_FROM)
        if not path.exists():
            raise FileNotFoundError(f'FINETUNE_FROM が見つかりません: {path}  (今の best.pt のパスを入れてください)')
        if not USE_PRIOR:
            model, ck0, uses = load_tau_model(str(path), dev, force_prior=False)
            if uses:
                raise ValueError(f'USE_PRIOR = False には 3チャンネルの ckpt が要ります ({path} は事前マスク付きの TAU)')
            print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]}) — 3チャンネル (事前マスクなし)')
            return model.train(), ck0['encoder'], FINETUNE_EPOCHS, FINETUNE_LR
        model, ck0, _ = load_tau_model(str(path), dev, force_prior=True)
        print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]})'
              f' — 事前マスクの重みを 0 で足した 5チャンネル版 (学習前は元のモデルと同じ結果)')
        return model.train(), ck0['encoder'], FINETUNE_EPOCHS, FINETUNE_LR
    model = build_model(ENCODER, 3, in_ch, 'imagenet')
    return model.to(dev).train(), ENCODER, EPOCHS, LR


def train(root, out, dev):
    aug = prior_aug()
    tr = BubbleDS(root, 'train', *CROP, train=True, aug=aug)
    va = BubbleDS(root, 'val', *CROP, train=False, aug=aug)
    if len(tr) < BS:
        raise RuntimeError(f'train の画像が {len(tr)}枚しかありません (BS={BS} 以上必要)')
    g = torch.Generator()
    g.manual_seed(SEED)
    dl_tr = DataLoader(tr, BS, shuffle=True, num_workers=WORKERS, drop_last=True, generator=g)

    shapes = Counter(cv2.imread(str(p), cv2.IMREAD_GRAYSCALE).shape for p in tr.imgs)
    train_hw = [int(v) for v in shapes.most_common(1)[0][0]]
    print(f'  train {len(tr)}枚  val {len(va)}枚  画像サイズ {train_hw[0]}x{train_hw[1]}  device {dev}')
    if dev == 'cpu':
        print('  ※ GPU が見つかりません。CPU での学習はとても遅いです (torch の CUDA 版を確認)')
    on = [n for n, f in (('ランダムクロップ', AUG_RANDOM_CROP), ('左右反転', AUG_FLIP), ('回転', AUG_ROTATE),
                         ('明るさ', AUG_BRIGHTNESS), ('Copy-Paste', COPY_PASTE)) if f]
    if USE_PRIOR:
        print(f'  学習中の増強: {", ".join(on) if on else "なし"}  + 事前マスク {aug.as_dict()}')
        print(f'  画像を崩す: 確率 {DEGRADE_P}, {degrade_cfg().as_dict()}')
    else:
        print(f'  学習中の増強: {", ".join(on) if on else "なし"}  (USE_PRIOR = False: 事前マスクなしの 3チャンネル)')
    if COPY_PASTE:
        print(f'  Copy-Paste の材料: 小さい気泡 {len(tr.bank)}個')
    save_cp_preview(tr, out / 'aug_preview', CP_SAVE_PREVIEW)

    model, encoder, epochs, lr = make_model(dev)
    ce, dice = make_losses(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    first_conv = next(p for n, p in model.encoder.named_parameters() if p.ndim == 4)

    meta = {'encoder': encoder, 'classes': 3, 'mean': MEAN, 'std': STD,
            'in_channels': IMAGE_CHANNELS + (PRIOR_CHANNELS if USE_PRIOR else 0), 'tau': USE_PRIOR,
            'prior_channels': ['interior', 'outline'] if USE_PRIOR else [],
            'prior_edge_px': PRIOR_EDGE_PX,
            'prior_aug': aug.as_dict() if USE_PRIOR else None,
            'degrade': dict(degrade_cfg().as_dict(), p=DEGRADE_P) if USE_PRIOR else None,
            'ignore_src': str(IGNORE_SRC) if IGNORE_SRC else None,
            'edge_px': EDGE_PX, 'edge_w': EDGE_W, 'crop': list(CROP), 'seed': SEED,
            'train_hw': train_hw, 'n_train': len(tr), 'n_val': len(va),
            'src': str(SRC), 'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'finetuned_from': str(FINETUNE_FROM) if FINETUNE_FROM else None,
            'online_aug': {'random_crop': AUG_RANDOM_CROP, 'flip': AUG_FLIP, 'rotate': AUG_ROTATE,
                           'brightness': AUG_BRIGHTNESS},
            'copy_paste': {'on': COPY_PASTE, 'prob': CP_PROB, 'max': CP_MAX,
                           'max_area': CP_MAX_AREA, 'alpha': list(CP_ALPHA)} if COPY_PASTE else None}

    meta['best_by'] = BEST_BY if USE_PRIOR else 'val'
    best, best_ep, empty_floor = -1.0, 0, None
    if FINETUNE_FROM:      # 開始モデル自体を基準にする → 学習で悪くなったら best.pt は開始モデルのまま
        ev0 = evaluate_both(model, va, dev)
        best = ev0['score']
        if USE_PRIOR and BEST_BY == 'prior':
            empty_floor = score_of(ev0['empty']) - BEST_EMPTY_TOL
        torch.save(dict(meta, state_dict=model.state_dict(), epoch=0, val=ev0), out / 'best.pt')
        print(f'  開始モデル val {fmt_eval(ev0)} (score {best:.4f}) — これより良くなったときだけ best を更新'
              + (f'\n  best の選び方: 事前マスクありの点数 (事前マスクなしの点数が {empty_floor:.4f} 未満の epoch は除く)'
                 if empty_floor is not None else ''))
    log = []
    for ep in range(1, epochs + 1):
        frozen = ep <= FREEZE_ENCODER_EPOCHS
        for prm in model.encoder.parameters():
            prm.requires_grad = not frozen
        if USE_PRIOR:
            first_conv.requires_grad = True          # 事前マスクの入口は固定しない
        model.train()
        tl, t0 = 0.0, time.time()
        for x, y in dl_tr:
            x, y = x.to(dev), y.to(dev)
            lg = model(x)
            loss = ce(lg, y) + dice(lg, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tl += loss.item()
        sched.step()
        ev = evaluate_both(model, va, dev)
        ok_empty = empty_floor is None or score_of(ev['empty']) >= empty_floor
        entry = {'ep': ep, 'loss': tl / len(dl_tr), 'score': ev['score'], 'empty_iou': ev['empty']['iou'],
                 'empty_ok': ok_empty}
        pw_txt = ''
        if USE_PRIOR:
            pw_mean, pw_max = prior_weight(first_conv)
            entry.update({'deg_empty_iou': ev['deg_empty']['iou'], 'deg_synth_iou': ev['deg_synth']['iou'],
                          'copy': ev['deg_synth']['copy'],
                          'prior_effect_edge': ev['deg_synth']['iou'][2] - ev['deg_empty']['iou'][2],
                          'prior_w_mean': pw_mean, 'prior_w_max': pw_max})
            pw_txt = f'  事前の重み {pw_mean:.4f}/{pw_max:.4f}'
        log.append(entry)
        mark = '' if ok_empty else '  (事前なしの点数が下がりすぎ: best の候補外)'
        ck = dict(meta, state_dict=model.state_dict(), epoch=ep, val=ev)
        torch.save(ck, out / 'last.pt')
        if ok_empty and ev['score'] > best:
            best, best_ep = ev['score'], ep
            torch.save(ck, out / 'best.pt')
            mark = '  ← best'
        print(f'  ep {ep:3d}/{epochs}{" (エンコーダ固定)" if frozen else ""}  loss {tl / len(dl_tr):.4f}  '
              f'{fmt_eval(ev)}{pw_txt}   {time.time() - t0:.0f}s{mark}')
        (out / 'log.json').write_text(json.dumps(log, indent=1), encoding='utf-8')
    print(f'  学習完了。best = epoch {best_ep} (score {best:.4f})'
          + ('  ※ 開始モデルより良くならなかったので、best.pt は開始モデル' + (' (事前マスクを使わない)' if USE_PRIOR else '')
             + ' のまま' if FINETUNE_FROM and best_ep == 0 else ''))
    return out / 'best.pt'


# ======================================================================
# [3] test 確認 — tracker3.py と同じ後処理 ("wall") で気泡の個数まで確認
# ======================================================================
def extract_instances(prob, min_area=4, band=25, edge_thr=0.5, close_it=2, tiny_max=300):
    """確率マップ (3,H,W) → 気泡ラベルマップ (0=なし, 1..N=気泡)。1_unet_train.py と同じ"""
    H, W = prob.shape[1:]
    edge_raw = prob[2] > edge_thr
    p = close_it + 3
    ep = np.pad(edge_raw, p, constant_values=True)
    if close_it > 0:
        ep = ndimage.binary_closing(ep, iterations=close_it + 1)
    ep = ep[p - 1:-(p - 1), p - 1:-(p - 1)]
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
    comp, nc = ndimage.label(edge_raw & ~assigned)
    for ci, sl in enumerate(ndimage.find_objects(comp), start=1):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, H)
        x0, x1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, W)
        c = comp[y0:y1, x0:x1] == ci
        if (c & near_assigned[y0:y1, x0:x1]).any():
            continue
        filled = ndimage.binary_fill_holes(c)
        a = int(filled.sum())
        if a < min_area or a > tiny_max:
            continue
        k += 1
        inst[y0:y1, x0:x1][filled] = k
    return inst


@torch.no_grad()
def predict_prob(model, gray, dev, prior=None, uses_prior=True):
    H, W = gray.shape
    ph, pw = (-H) % 32, (-W) % 32
    g = cv2.copyMakeBorder(gray, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
    pr = None if prior is None else np.pad(prior, ((0, 0), (0, ph), (0, pw)))
    x = make_input(g, pr, MEAN, STD, uses_prior)
    x = torch.from_numpy(x)[None].to(dev)
    return model(x).softmax(1)[0].cpu().numpy()[:, :H, :W]


def instance_overlay(gray, inst, text, prior=None):
    rng = np.random.default_rng(0)
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    col = bgr.copy()
    n = int(inst.max())
    colors = rng.integers(60, 255, (n + 1, 3))
    for i in range(1, n + 1):
        col[inst == i] = colors[i]
    out = cv2.addWeighted(bgr, 0.45, col, 0.55, 0)
    for i in range(1, n + 1):
        cs, _ = cv2.findContours((inst == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cs, -1, (255, 255, 255), 1)
    if prior is not None:
        out[prior[1] > 0.5] = (0, 255, 255)
    cv2.putText(out, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    return out


SIZE_CLASSES = (('tiny', 0, 50), ('small', 50, 500), ('large', 500, float('inf')))   # 面積 px (QC と同じ)


def _size_cls(a):
    return next(n for n, lo, hi in SIZE_CLASSES if lo <= a < hi)


def load_gt_instances(src):
    """COCO の test の正解ポリゴン → {ファイル名の stem: [気泡マスク, ...]}"""
    jp = Path(src) / 'test' / '_annotations.coco.json'
    if not jp.exists():
        return {}
    images, by_img = load_coco(jp)
    out = {}
    for im in images:
        H, W = im['height'], im['width']
        masks = []
        for polys, _, _ in by_img.get(im['id'], []):
            mk = np.zeros((H, W), np.uint8)
            for p in polys:
                cv2.fillPoly(mk, [p.astype(np.int32)], 1)
            if mk.any():
                masks.append(mk.astype(bool))
        out[Path(im['file_name']).stem] = masks
    return out


def match_by_size(gt_masks, inst, thr, ignore=None):
    """正解と予測の気泡を IoU で1対1に対応 → 大きさごとに [正解数, 見つけた正解数, 予測数, 当たった予測数]。
    ignore (学習しない画素) があれば、画素の半分以上がそこにある予測の気泡は数えない (ラベルされていない点の候補)"""
    from scipy.optimize import linear_sum_assignment
    pred = [q for q in (inst == i for i in range(1, int(inst.max()) + 1)) if q.any()]
    if ignore is not None and ignore.any():
        pred = [q for q in pred if np.count_nonzero(q & ignore) * 2 < np.count_nonzero(q)]
    st = {n: [0, 0, 0, 0] for n, _, _ in SIZE_CLASSES}
    gcls = [_size_cls(int(g.sum())) for g in gt_masks]
    pcls = [_size_cls(int(q.sum())) for q in pred]
    for c in gcls:
        st[c][0] += 1
    for c in pcls:
        st[c][2] += 1
    if not gt_masks or not pred:
        return st

    def bbox(mk):
        ys, xs = np.nonzero(mk)
        return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    gb, pb = [bbox(g) for g in gt_masks], [bbox(q) for q in pred]
    iou = np.zeros((len(gt_masks), len(pred)))
    for a, (g, (gy0, gy1, gx0, gx1)) in enumerate(zip(gt_masks, gb)):
        for b, (q, (py0, py1, px0, px1)) in enumerate(zip(pred, pb)):
            y0, y1, x0, x1 = max(gy0, py0), min(gy1, py1), max(gx0, px0), min(gx1, px1)
            if y1 <= y0 or x1 <= x0:
                continue
            inter = np.count_nonzero(g[y0:y1, x0:x1] & q[y0:y1, x0:x1])
            if inter:
                iou[a, b] = inter / (g.sum() + q.sum() - inter)
    r, c = linear_sum_assignment(-iou)
    for a, b in zip(r, c):
        if iou[a, b] >= thr:
            st[gcls[a]][1] += 1
            st[pcls[b]][3] += 1
    return st


def eval_ckpt(ckpt_path, root, dev, gt_inst, prior_mode, preview_dir=None):
    """test で評価。prior_mode: "empty" (事前マスクなし) / "synth" (正解から作った事前マスク。val と同じ作り方)"""
    model, ck, uses_prior = load_tau_model(str(ckpt_path), dev)
    te = BubbleDS(root, 'test', *CROP, train=False, prior_mode=prior_mode if uses_prior else 'empty')
    ev = evaluate(model if uses_prior else _ThreeCh(model),   # 3チャンネルのモデルには画像だけ入れる
                  DataLoader(te, 1, shuffle=False, num_workers=WORKERS), dev)
    per = {n: [0, 0, 0, 0] for n, _, _ in SIZE_CLASSES}
    n_gt = n_pred = 0
    for i, ip in enumerate(te.imgs):
        g, m, ins = te.load(i)
        prior = te.prior_for(i, ins) if uses_prior else None
        inst = extract_instances(predict_prob(model, g, dev, prior, uses_prior), MIN_AREA, BAND, EDGE_THR, CLOSE,
                                 TINY_MAX)
        gts = gt_inst.get(ip.stem)
        if gts is not None:
            st = match_by_size(gts, inst, IOU_MATCH, m == IGNORE_LABEL)
            for k in per:
                per[k] = [u + v for u, v in zip(per[k], st[k])]
            n_gt += len(gts)
        ign = m == IGNORE_LABEL                       # 学習しない画素に半分以上ある予測は数えない (match_by_size と同じ)
        n_pred += sum(1 for k in np.unique(inst) if k > 0
                      and not (ign.any() and np.count_nonzero((inst == k) & ign) * 2 >= np.count_nonzero(inst == k)))
        if preview_dir is not None:
            preview_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(preview_dir / f'{ip.stem}_{prior_mode}.png'), instance_overlay(
                g, inst, f'pred N={int(inst.max())}  GT N={"-" if gts is None else len(gts)}  prior={prior_mode}',
                prior))
    return {'ckpt': str(ckpt_path), 'epoch': ck.get('epoch'), 'prior': prior_mode if uses_prior else 'none (3ch)',
            'pixel_iou': {'bg': ev['iou'][0], 'in': ev['iou'][1], 'edge': ev['iou'][2]}, 'copy': ev['copy'],
            'n_gt': n_gt, 'n_pred': n_pred,
            'per_size': {k: {'gt': v[0], 'found': v[1], 'pred': v[2], 'correct': v[3],
                             'recall': v[1] / v[0] if v[0] else None,
                             'precision': v[3] / v[2] if v[2] else None} for k, v in per.items()}}


class _ThreeCh(nn.Module):
    """5チャンネルの入力から画像の3チャンネルだけを3チャンネルのモデルに渡す (評価用)"""

    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, x):
        return self.m(x[:, :IMAGE_CHANNELS])


def test_check(ckpt_path, root, out, dev):
    if not list_images(Path(root) / 'images' / 'test'):
        print('  test の画像が無いので飛ばします')
        return
    gt_inst = load_gt_instances(resolve(SRC))
    if not gt_inst:
        print('  ※ SRC/test の COCO の正解が無いので、大きさ別の再現率は省略します')
    cols = []
    if FINETUNE_FROM:
        cols.append(('開始モデル', eval_ckpt(resolve(FINETUNE_FROM), root, dev, gt_inst, 'empty')))
    cols.append(('新 事前なし' if USE_PRIOR else '新',
                 eval_ckpt(ckpt_path, root, dev, gt_inst, 'empty', out / 'test_preview')))
    if USE_PRIOR:
        cols.append(('新 事前あり', eval_ckpt(ckpt_path, root, dev, gt_inst, 'synth', out / 'test_preview')))

    def fmt(x):
        return '   -  ' if x is None else f'{100 * x:5.1f}%'
    new = cols[-1][1]
    print(f'  test の気泡 {new["n_gt"]}個 (正解ポリゴンと IoU ≥ {IOU_MATCH} なら同じ気泡とみなす)')
    print('  ' + f'{"大きさ":<8}' + ''.join(f'{name:>20}' for name, _ in cols))
    print('  ' + f'{"":<8}' + ''.join(f'{"再現率":>10}{"適合率":>10}' for _ in cols))
    for k, _, _ in SIZE_CLASSES:
        line = f'{k:<8}'
        for _, r in cols:
            d = r['per_size'][k]
            line += f'{fmt(d["recall"]):>10}{fmt(d["precision"]):>10}'
        print('  ' + line + f'   (正解 {new["per_size"][k]["gt"]}個)')
    for name, r in cols:
        pi = r['pixel_iou']
        cp = '' if r['copy'] is None else f', 写し {100 * r["copy"]:.1f}%'
        print(f'  [{name}] 予測 {r["n_pred"]}個 / 正解 {r["n_gt"]}個, 画素 IoU 内部 {pi["in"]:.3f} 境界 {pi["edge"]:.3f}{cp}')
    if USE_PRIOR:
        print('  「事前あり」は正解から作った事前マスクなので甘めの評価。本当の効果は 2_bin_track.py の動画で確認すること')
    if IGNORE_SRC:
        print('  学習しない画素 (IGNORE_SRC) に半分以上ある予測の気泡は数えていない。test の点の候補を STEP = "dots" で'
              '全部確認してあれば、tiny の再現率はラベルし直した点も含めた値')
    report = {'columns': {name: r for name, r in cols}, 'iou_match': IOU_MATCH,
              'postprocess': {'min_area': MIN_AREA, 'band': BAND, 'edge_thr': EDGE_THR,
                              'close': CLOSE, 'tiny_max': TINY_MAX}}
    (out / 'test_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'  オーバーレイ → {out / "test_preview"}  (黄 = 事前マスクの輪郭)')


# ======================================================================
def main_train():
    set_seed(SEED)
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    dst = resolve(DST)

    print('\n[1] データセットの変換')
    have = list_images(dst / 'images' / 'train') and (dst / 'instances' / 'train').exists()
    if REBUILD_DATASET or not have:
        build_dataset(resolve(SRC), dst, EDGE_PX, N_PREVIEW, resolve(IGNORE_SRC) if IGNORE_SRC else None)
    else:
        print(f'  変換済みのデータセットを使います: {dst}')

    out = unique_dir(resolve(OUT))
    out.mkdir(parents=True)
    print(f'\n[2] 学習 → {out}')
    best = train(dst, out, dev)

    print('\n[3] test で確認')
    test_check(best, dst, out, dev)

    print('\n完了。' + '2_bin_track.py'
          + ' の設定をこう変えてください:')
    print(f"  UNET_CKPT = r'{best}'")


# ======================================================================
# [D] 起動
# ======================================================================
def main():
    """STEP = 'dots' -> main_dots (元 dot_labels.py) / 'train' -> main_train (元 1_tau_unet_train.py)"""
    global SRC, IGNORE_SRC
    if STEP == 'dots':
        return main_dots()
    if STEP != 'train':
        raise ValueError(f"STEP は 'dots' か 'train': {STEP!r}")
    if USE_DOT_LABELS:
        d = resolve(DOT_OUT)
        if not (d / 'coco').exists():
            raise FileNotFoundError(f"{d / 'coco'} がありません。先に STEP = 'dots' で実行するか、USE_DOT_LABELS = False に")
        SRC, IGNORE_SRC = str(d / 'coco'), str(d / 'ignore')
        print(f'  小さい点のラベル補充の結果を使います: SRC = {SRC}, IGNORE_SRC = {IGNORE_SRC}')
    return main_train()


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
鉄 (不透明) の流路用 — U-Net の学習 (1ファイル)
=====================================================================
    python 1_steel_train.py

steel/ は raw/ (commit bb568f7) から分けた固定コピー。raw/ と binarized/ をこの先 (parity 救済など) 直しても、ここは変わらない。
tools/build_raw.py では作らない (直すときはこのファイルを直接直す)。raw/ との違いは次の 3つだけ:
  - BG_MATCH: 背景画像の明るさを元画像に合わせてから B / DK / DB を作る (ckpt の input.bg_match に記録 -> 2_steel_track.py も同じ)
  - 既定の DST / OUT の名前 (dataset_steel, runs/steel)
  - 説明文
鉄の流路の実測 (2026-10-22, 元画像 1枚に気泡 1個, 直径 約 115 px): 気泡の中は液体より約 40 階調暗い (ばらつき 3.2 の約 12倍)。
透明な流路 (中は -5、巨大スラグは 0 前後) と違い、気泡の中そのものが手がかりになる -> 'bin+sign' の DK に中が出る。
B (二値化) では気泡が「白く塗りつぶした円」になり、今までの二値化画像 (白い輪で中は黒) と見た目が違う。
そのため OLD_BIN_SRC (透明な流路の二値化画像) は混ぜない方がよい (既定 None)。

元画像 (背景の残った画像) と背景画像から画像を作って U-Net に入れる:
  B  = 二値化画像 (今と同じ: 背景差分 -> Noise Cut 未満を 0 -> ×Brightness。白い輪郭)
  D  = 差分画像   (B から Noise Cut だけを外したもの)
  DK = 背景より暗くなった分 / DB = 明るくなった分 (D を向きで2つに分けたもの)
       気液の界面 (メニスカス) は必ず暗い。大きい気泡の中の液膜のむら (乾いた所) は明るい。
       B と D は絶対値なので両方とも「白」になり、むらを輪郭と間違える (実測: 界面 -40〜-100, むら +9〜+16)
INPUT_MODE で入れ方を選ぶ (同じデータで学習して test で比べられる):
  'bin+sign' : B + DK + DB (5チャンネル)。おすすめ
  'bin+diff' : B + D (4チャンネル)
  'diff'     : D だけ (3チャンネル)。best.pt から始めるが、入力の見た目が変わるので最初は今より悪い
  'bin'      : B だけ (今と同じ入力)。「比較の基準」
  B 以外の画像の重みは 0 から始まる -> 学習前は今の best.pt と全く同じ結果
追加の部品 (どれも ON/OFF。OFF なら付けない):
  CTX_LAYERS > 0 : U-Net の一番深い所 (画像の 1/32) に小さいトランスフォーマー (画面全体の関係を見る)。出口の重みは 0 から
  USE_PRIOR      : TAU。事前マスク (前後のフレームの検出結果) も入力する。学習では正解ラベルを崩して作る
ラベルは Roboflow で元画像に描いたもの (座標は B・D と同じ)。背景画像は画像の名前の先頭で選ぶ (BACKGROUNDS)。
今までの二値化画像の学習データ (OLD_BIN_SRC) も使える (D は作れないので B と同じもの、DK = B, DB = 0 を入れる =
「気泡の中の情報が無い画像」として学ぶ):
  train -> 学習に混ぜる / valid -> best.pt の選び方にも使う / test -> 今までの画像で悪くなっていないかを別の表で確認

流れ
  [1] Roboflow の書き出し (SRC) -> B, D, DK, DB, 3クラスのマスク, 気泡ごとのラベル (DST)
  [2] 学習 -> OUT/best.pt (2_steel_track.py の UNET_CKPT に入れる。入力の作り方・部品も ckpt に記録)
  [3] test で確認 -> 「開始モデル (今の best.pt)」と「新しいモデル」の 画素 IoU と 大きさ別の再現率・適合率
                    (新しい test と、OLD_BIN_SRC の test の 2つの表)
相対パスは「このファイルがあるフォルダ」基準。OUT が既にあれば runs/steel2, steel3 ... を新しく作る。
"""

# ======================================================================
#  設定 — ここだけ直して  python 1_steel_train.py  で実行。Windows のパスは r'...' で囲む
# ======================================================================
SRC = r'C:\Users\Tristan\Desktop\steel\coco'     # Roboflow の書き出し (元画像にラベル。train/ valid/ test/ を含む)。
                                                # 書き出すときは Augmentation も Resize も無しで (背景画像と画素がずれると入力が壊れる)
BACKGROUNDS = {                                 # 画像の元の名前の先頭 -> その動画の背景画像 (先頭が長く一致するものが優先)
    'test': r'C:\Users\Tristan\Desktop\steel\bg_test.jpg',
}
DEFAULT_BACKGROUND = None     # BACKGROUNDS のどれにも当てはまらない画像の背景。None なら当てはまらない画像の一覧を出して止まる
INPUT_MODE = 'bin+sign'       # 'bin+sign' (おすすめ) / 'bin+diff' / 'diff' / 'bin'
PREPROC = (15, 4, 0)          # 前処理 (Noise Cut, Brightness, Median)。今の二値化と同じ値 (B はこの値で作る)
BG_MATCH = 'offset'           # 背景画像の明るさを元画像に合わせる: 'offset' (おすすめ) / 'gain' (模様のはっきりした背景だけ) / None (raw/ と同じ)
                              # 照明が撮影中に少し変わっても DB (明るくなった分) が液体全体に出ないようにする。ckpt に記録される
OLD_BIN_SRC = None            # 鉄の流路では None のまま (透明な流路の二値化画像は気泡の中が黒、鉄の流路は中が白で、見た目が違う)。
                              # 今までの二値化画像の Roboflow 書き出し (例 480枚。train/ valid/ test/ を含む)。None なら使わない。
                              #   train/ -> 学習に混ぜる
                              #   valid/ -> best.pt の選び方にも使う (OLD_VAL_WEIGHT と OLD_VAL_TOL)
                              #   test/  -> [3] で別の表 (今までの画像で今の best.pt より悪くなっていないか)
                              # 新しいデータが少ないうちは使うのがおすすめ (小さい気泡などの今の力を保つ)
OLD_SHARE = 0.5               # 1 epoch で OLD_BIN_SRC の train の画像が占める割合 (新しい画像は 1 epoch に平均1回ずつ出る)
OLD_VAL_WEIGHT = 0.5          # best.pt を選ぶ点数 = (1 - この値) × 新しい val の点数 + この値 × OLD_BIN_SRC の val の点数。
                              # 0 なら新しい val だけで選ぶ (今までの val は表示だけ)
OLD_VAL_TOL = 0.01            # OLD_BIN_SRC の val の点数 (0.4×内部 IoU + 0.6×境界 IoU) が開始モデルよりこの値を超えて下がった epoch は
                              # best.pt に選ばない (新しい val で良くなっても、今までの画像で悪くなったものは使わない)。None なら確認しない
DST = r'dataset_steel'        # 変換したデータセットのフォルダ (毎回作り直す)
OUT = r'runs/steel'           # 結果のフォルダ。既にあれば runs/steel2, steel3 ... を自動で作る
REBUILD_DATASET = True        # True: 毎回 SRC から作り直す / False: DST に変換済みがあればそのまま使う
                              # (SRC / OLD_BIN_SRC / PREPROC / BG_MATCH が前と違えば作り直す)

# [1] ラベル変換 (今の学習と同じ)
EDGE_PX   = 4                 # 大きい気泡の境界の太さ (px)。小さい気泡は自動で 1〜3px
N_PREVIEW = 8                 # 確認用のプレビュー枚数 (DST/preview/。左から B, DK, DB, ラベル)

# [2] 学習
FINETUNE_FROM = r'best.pt'    # 開始モデル (今の best.pt / TAU の best.pt / 1_steel_train.py の best.pt)。足りない入力・部品の重みは 0 から。
                              # None なら ImageNet から (EPOCHS を増やす)
LR      = 1e-4                # 学習率
EPOCHS  = 80                  # epoch 数
BS      = 4                   # VRAM が足りなければ 2
CROP    = (1088, 416)         # (高さ, 幅)。32 の倍数。画像の中から無作為な位置で切り出す (画像が小さければ反射で足す)
EDGE_W  = 6.0                 # 境界クラスの損失の重み
WORKERS = 0                   # Windows では 0 のまま
SEED    = 0
AUG_FLIP = False              # 左右反転
AUG_ROTATE = False            # ±5° 回転
COPY_PASTE = True             # 小さい気泡 (画像・ラベルごと) を空いた所に貼る (今の学習と同じ)
CP_PROB = 0.5
CP_MAX = 15
CP_MAX_AREA = 500
CP_ALPHA = (0.35, 1.0)

# [2b] 追加の部品 (ON/OFF)
CTX_LAYERS = 0                # 小さいトランスフォーマーの層数 (U-Net の一番深い所 = 画像の 1/32 に足す)。0 = 使わない。試すなら 2。
                              # 出口の重みは 0 から (学習前は足す前と同じ結果)。1088×416 で 34×13 = 442 個の位置しかないので軽い
CTX_HEADS = 8                 # トランスフォーマーのヘッド数 (resnet34 の 512 チャンネルを割り切れる数)
USE_PRIOR = False             # True: TAU。事前マスク (内部, 輪郭) も入力する (2_steel_track.py が前後のフレームから作る)。
                              # 学習では正解ラベルを崩して作る (下の PRIOR_*。1_bin_train.py と同じ)。事前マスクの重みは 0 から
PRIOR_P_EMPTY = 0.15          # 事前マスクなし (1パス目と同じ状況) の割合
PRIOR_P_DROP = 0.2            # 気泡ごとに消す確率 (前のパスの見落とし)
PRIOR_SHIFT_PX = 1.0          # 位置ずれの標準偏差 = この値 + 等価直径 × PRIOR_SHIFT_SIZE (px)
PRIOR_SHIFT_SIZE = 0.05
PRIOR_P_BIG_SHIFT = 0.1       # 位置ずれを4倍にする確率
PRIOR_SCALE = (0.85, 1.15)    # 大きさの変化
PRIOR_MORPH_PX = 2            # 膨張/収縮の最大幅 (px)
PRIOR_P_TRUNC = 0.1           # 一部が欠ける確率
PRIOR_P_MERGE = 0.3           # 接している2個を1個にまとめる確率
PRIOR_P_SPLIT = 0.05          # 面積 500px 以上の気泡を2つに割る確率
PRIOR_PHANTOM_RATE = 2.0      # 1枚あたりの「何も無い所の気泡」の平均個数

# [3] test 確認用の後処理 (今の学習と同じ)
MIN_AREA = 4
BAND     = 25
EDGE_THR = 0.5
CLOSE    = 2
TINY_MAX = 300
IOU_MATCH = 0.3
# ======================================================================

import json
import math
import random
import re
import shutil
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import segmentation_models_pytorch as smp

HERE = Path(__file__).resolve().parent
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
SPLIT_MAP = {'train': 'train', 'valid': 'val', 'val': 'val', 'test': 'test'}
IGNORE_LABEL = 255
ANN_NAME = '_annotations.coco.json'
OLD_SPLIT = {'train': 'old', 'val': 'old_val', 'test': 'old_test'}   # OLD_BIN_SRC の split -> DST の中の名前
OLD_PREFIX = 'old_'                                                 # OLD_BIN_SRC の画像の名前の頭 (SRC と重ならないように)
DATASET_LAYOUT = 'steel-3'    # DST の作り方の版 (変わったら REBUILD_DATASET = False でも作り直す)。raw/ の 3 と分けて、
                              # 同じ DST を指しても raw/1_raw_train.py が明るさを合わせた画像を使い回さないようにする
SUBDIRS = ('bin', 'diff', 'dark', 'bright', 'masks', 'instances')

# ======================================================================
# 入力の作り方とモデルの形 — 1_steel_train.py と 2_steel_track.py で同じ (両方を一緒に直す)
# ======================================================================
INPUT_MODES = ('bin', 'diff', 'bin+diff', 'bin+sign')
PLANES = {                      # INPUT_MODE -> 使う画像 (B = 二値化, D = |差分|, DK = 暗くなった分, DB = 明るくなった分)
    'bin': ('B',),
    'diff': ('D',),
    'bin+diff': ('B', 'D'),
    'bin+sign': ('B', 'DK', 'DB'),
}
PLANE_DIRS = {'B': 'bin', 'D': 'diff', 'DK': 'dark', 'DB': 'bright'}   # 学習データセットのフォルダ名


def bin_diff(raw_bgr, bg_bgr, preproc):
    """元画像 + 背景画像 (どちらも BGR) -> (二値化画像 B, 差分画像 D)。どちらも uint8 (H, W)
    B: 二値化版の前処理と同じ (背景差分 -> グレー -> Median -> Noise Cut 未満を 0 -> ×Brightness)
    D: B から Noise Cut だけを外したもの。輪郭は B と同じように明るく、気泡の中の薄い差 (液体より少し暗い) も残る"""
    thr, bright, median = (int(v) for v in preproc)
    if bg_bgr.shape != raw_bgr.shape:
        bg_bgr = cv2.resize(bg_bgr, (raw_bgr.shape[1], raw_bgr.shape[0]))
    g = cv2.cvtColor(cv2.absdiff(raw_bgr, bg_bgr), cv2.COLOR_BGR2GRAY)
    g = cv2.medianBlur(g, median * 2 + 1)
    _, cut = cv2.threshold(g, thr, 255, cv2.THRESH_TOZERO)
    return cv2.convertScaleAbs(cut, alpha=bright), cv2.convertScaleAbs(g, alpha=bright)


BG_MATCH_MODES = (None, 'offset', 'gain')
BG_MATCH_MAX = 15.0            # これより大きく明るさを直す当てはめは信用しない (気泡の中は -40。照明の変化は実測 +4.9)
BG_MATCH_JUMP = 5.0            # 検出 (2_steel_track.py) で、直前に信用したフレームからこれより大きく変わる当てはめは信用しない
                               # (照明はゆっくり変わる。気泡が画面の半分を超えると液体でなく気泡の明るさに合わせてしまうため)。
                               # 同じくらいの値に BG_MATCH_JUMP_FRAMES フレーム続けて変わったら、本当に照明が変わったとみなして受け入れる
BG_MATCH_JUMP_FRAMES = 5


def fit_background(raw_bgr, bg_bgr, mode='offset', max_shift=BG_MATCH_MAX):
    """背景画像の明るさを元画像に合わせる式 元画像 ≈ a × 背景 + b を求める (グレーで)。戻り値 (a, b)、信用できなければ None。
    撮影中に照明が少し変わる対策。鉄の流路の実測 (images/44 と 45) では元画像が全体に +4.9 階調明るく、
    そのままだと DB (明るくなった分) が液体の 92% の画素で 0 でなくなった (×4 で約 20)。
      'offset': a = 1。b は (元画像 - 背景) のヒストグラムの山 (いちばん多い値 = 液体) から始め、山のばらつき σ を山の近く
                (±15 階調) だけで求め、|差 - b| ≤ max(3σ, 3) の画素の平均で 3回 求め直す。
                気泡がいくら暗くても、液体の画素が一番多い値である限り正しい (中央値から始めると、画面の 45% が暗い気泡で
                b が -13 になった。レビューで確認)
      'gain'  : 'offset' で選んだ液体の画素で a, b を最小二乗。背景の模様が弱いと a が小さく出る (回帰の希釈) ので、
                a が 0.5〜2 の外なら 'offset' の値にする (a = 1)
    直す量 (背景の明るさの中央値での a × g + b - g) が max_shift を超えたら None (液体より気泡の画素が多いフレームなど)"""
    if mode is None:
        return 1.0, 0.0
    if mode not in BG_MATCH_MODES:
        raise ValueError(f'BG_MATCH は {BG_MATCH_MODES} のどれか: {mode!r}')
    if bg_bgr.shape != raw_bgr.shape:
        bg_bgr = cv2.resize(bg_bgr, (raw_bgr.shape[1], raw_bgr.shape[0]))
    r = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    g = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    step = max(1, int(np.sqrt(r.size / 200000)))          # 20万〜80万画素に間引いて当てはめる (結果はほぼ同じで速い)
    r, g = r[::step, ::step].ravel(), g[::step, ::step].ravel()
    d = r - g
    h = np.bincount(np.clip(np.rint(d).astype(np.int64) + 255, 0, 510), minlength=511).astype(np.float64)
    h = np.convolve(h, np.ones(5) / 5, 'same')
    b = float(np.argmax(h) - 255)                          # いちばん多い差 = 液体
    near = np.abs(d - b) < 15
    if near.sum() < 100:
        return None
    tol = max(3.0 * 1.4826 * float(np.median(np.abs(d[near] - b))), 3.0)
    for _ in range(3):
        keep = np.abs(d - b) <= tol                        # 液体の画素 (気泡・輪郭は外れる)
        b = float(np.mean(d[keep]))
    a = 1.0
    if mode == 'gain':
        ka, kb = a, b
        for _ in range(3):
            keep = np.abs(r - (ka * g + kb)) <= tol
            if keep.sum() < 100:
                break
            A = np.stack([g[keep], np.ones(int(keep.sum()))], 1)
            ka, kb = (float(v) for v in np.linalg.lstsq(A, r[keep], rcond=None)[0])
        if 0.5 <= ka <= 2.0 and np.isfinite(kb):
            a, b = ka, kb
    if not np.isfinite(b) or abs((a - 1.0) * float(np.median(g)) + b) > max_shift:
        return None
    return a, b


def apply_background(bg_bgr, a, b, shape=None):
    """背景画像 (BGR) に a × 背景 + b をかける (shape = 元画像の (H, W) に大きさを合わせてから)"""
    if shape is not None and bg_bgr.shape[:2] != tuple(shape[:2]):
        bg_bgr = cv2.resize(bg_bgr, (shape[1], shape[0]))
    if a == 1.0 and b == 0.0:
        return bg_bgr
    return np.clip(np.rint(bg_bgr.astype(np.float64) * a + b), 0, 255).astype(np.uint8)


def match_background(raw_bgr, bg_bgr, mode='offset'):
    """fit_background + apply_background。戻り値 (合わせた背景画像 uint8 BGR, (a, b), 当てはめが使えたか)。
    当てはめが信用できなければ背景はそのまま ((1.0, 0.0), False)。mode が None なら そのまま ((1.0, 0.0), True)"""
    fit = fit_background(raw_bgr, bg_bgr, mode)
    ok = fit is not None
    a, b = fit if ok else (1.0, 0.0)
    return apply_background(bg_bgr, a, b, raw_bgr.shape), (a, b), ok


def make_planes(raw_bgr, bg_bgr, preproc, bg_match=None):
    """元画像 + 背景画像 -> {'B', 'D', 'DK', 'DB'} (どれも uint8 (H, W))
    DK / DB: 背景より暗くなった分 / 明るくなった分 (×Brightness)。
    鉄の流路の実測 (images/44, 気泡 1個): 気泡の中 (気体) は液体より約 40 階調暗い -> B では「白く塗りつぶした円」、DK でも中が白い。
    輪郭 (メニスカス) の明暗は向きで変わる: 光の来る側 (画像の上) は明るく (DB)、反対側は暗く (DK)、その外に約 10 px の影 (DK)。
    (透明な流路では界面はいつも暗く、液膜のむらが明るかった。raw/ の説明はそちらの話)
    bg_match ('offset' / 'gain'): 先に背景画像の明るさを元画像に合わせる (match_background)。None なら raw/ と同じ"""
    if bg_match is not None:
        bg_bgr = match_background(raw_bgr, bg_bgr, bg_match)[0]
    B, D = bin_diff(raw_bgr, bg_bgr, preproc)
    _, bright, median = (int(v) for v in preproc)
    if bg_bgr.shape != raw_bgr.shape:
        bg_bgr = cv2.resize(bg_bgr, (raw_bgr.shape[1], raw_bgr.shape[0]))
    s = (cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16)
         - cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16))
    out = {'B': B, 'D': D}
    for k, v in (('DK', -s), ('DB', s)):
        v = cv2.medianBlur(np.clip(v, 0, 255).astype(np.uint8), median * 2 + 1)
        out[k] = cv2.convertScaleAbs(v, alpha=bright)
    return out


def input_channels(mode, prior=False):
    """INPUT_MODE (+ 事前マスク) -> ネットワークの入力チャンネル数"""
    return len(channel_names(mode, prior))


def channel_names(mode, prior=False):
    """入力チャンネルの名前 (重みの引き継ぎに使う)。最初の画像は 3回 (best.pt と同じ)、ほかの画像は 1回ずつ、
    事前マスク (TAU) は 内部 / 輪郭 の 2チャンネル"""
    if mode not in INPUT_MODES:
        raise ValueError(f'INPUT_MODE は {INPUT_MODES} のどれか: {mode!r}')
    p = PLANES[mode]
    names = [f'{p[0]}{i}' for i in range(3)] + list(p[1:])
    return names + (['P_IN', 'P_EDGE'] if prior else [])


def make_input_raw(planes, mode, mean, std, prior=None, uses_prior=False):
    """画像 {'B', 'D', ...} (+ 事前マスク (2, H, W)) -> ネットワーク入力 (C, H, W) float32
    最初の画像を 3回 (best.pt と同じ正規化)、ほかの画像は1回ずつ (1チャンネル目と同じ正規化)。
    uses_prior なら事前マスク 2チャンネルを足す (prior が None なら 0 = 事前情報なし)"""
    names = PLANES[mode]
    base = planes[names[0]].astype(np.float32) / 255.0
    x = [(base - float(m)) / float(s) for m, s in zip(mean, std)]
    for n in names[1:]:
        x.append((planes[n].astype(np.float32) / 255.0 - float(mean[0])) / float(std[0]))
    if uses_prior:
        if prior is None:
            x += [np.zeros_like(base)] * 2
        else:
            if prior.shape != (2,) + base.shape:
                raise ValueError(f'事前マスクの形 {prior.shape} が画像 {base.shape} と合いません')
            x += [prior[c].astype(np.float32) for c in range(2)]
    return np.stack(x)


def ckpt_layout(ck, sd):
    """ckpt -> (INPUT_MODE, 事前マスクを使うか, 入力チャンネルの名前)。
    記録 (input) の無い ckpt はチャンネル数から: 3 = 二値化の best.pt ('bin')、5 = TAU ('bin' + 事前マスク)"""
    k0 = next(k for k, v in sd.items() if k.startswith('encoder.') and v.ndim == 4)
    in_ch = int(sd[k0].shape[1])
    inp = ck.get('input') or {}
    if inp:
        mode, prior = inp.get('mode', 'bin'), bool(inp.get('prior', False))
    else:
        mode, prior = 'bin', in_ch == 5
    names = channel_names(mode, prior)
    if len(names) != in_ch:
        raise ValueError(f'ckpt の入力チャンネル数 {in_ch} が記録 ({mode!r}, 事前マスク {prior}) と合いません')
    return mode, prior, names


def remap_first_conv(sd, src_names, dst_names):
    """最初の畳み込みの重みを、入力チャンネルの名前で並べ替える。無いチャンネルは 0 (= 学習前は出力に影響しない)。
    'diff' (D×3) と B×3 の入れ替えだけは、もう一方の重みをそのまま使う (B0 <-> D0 ...)"""
    import torch
    k0 = next(k for k, v in sd.items() if k.startswith('encoder.') and v.ndim == 4)
    w = sd[k0]
    out = torch.zeros((w.shape[0], len(dst_names)) + tuple(w.shape[2:]), dtype=w.dtype)
    for j, n in enumerate(dst_names):
        if n in src_names:
            out[:, j] = w[:, src_names.index(n)]
        elif n[:1] in 'BD' and n[1:] in ('0', '1', '2') and {'B': 'D', 'D': 'B'}[n[0]] + n[1] in src_names:
            out[:, j] = w[:, src_names.index({'B': 'D', 'D': 'B'}[n[0]] + n[1])]
    sd = dict(sd)
    sd[k0] = out
    return sd


def _pos2d(h, w, dim, device, oy=0, ox=0):
    """2次元の位置 (sin / cos)。画像の大きさが学習と違っても同じ式で作れる。oy, ox = 位置のずらし (学習の切り出し用)"""
    import torch
    d = dim // 4
    omega = 1.0 / (10000 ** (torch.arange(d, device=device, dtype=torch.float32) / max(1, d)))
    ys = (torch.arange(h, device=device, dtype=torch.float32) + oy)[:, None] * omega[None]
    xs = (torch.arange(w, device=device, dtype=torch.float32) + ox)[:, None] * omega[None]
    pe = torch.cat([torch.sin(ys)[:, None].expand(h, w, d), torch.cos(ys)[:, None].expand(h, w, d),
                    torch.sin(xs)[None].expand(h, w, d), torch.cos(xs)[None].expand(h, w, d)], -1)
    pe = pe.reshape(h * w, 4 * d)
    if 4 * d < dim:
        pe = torch.cat([pe, pe.new_zeros(h * w, dim - 4 * d)], 1)
    return pe[None]


CTX_POS_JITTER = 8     # 学習中は位置を 0〜この値 (1/32 の格子の数) だけずらす: 切り出し (例 34×13) で学習しても、
                       # 画像全体 (例 38×15) で推論するときの位置まで見たことがあるように


def _context_block(dim, layers, heads):
    """小さいトランスフォーマー (画面全体の関係を見る)。出口の重みは 0 -> 学習前は何もしない (足す前と同じ結果)"""
    import torch
    import torch.nn as nn

    class ContextBlock(nn.Module):
        def __init__(self):
            super().__init__()
            layer = nn.TransformerEncoderLayer(dim, heads, dim_feedforward=2 * dim, dropout=0.1,
                                               batch_first=True, norm_first=True)
            try:
                self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
            except TypeError:      # 古い torch
                self.enc = nn.TransformerEncoder(layer, layers)
            self.norm = nn.LayerNorm(dim)
            self.out = nn.Linear(dim, dim)
            nn.init.zeros_(self.out.weight)
            nn.init.zeros_(self.out.bias)

        def forward(self, f):
            b, c, h, w = f.shape
            oy, ox = (torch.randint(0, CTX_POS_JITTER + 1, (2,)).tolist() if self.training else (0, 0))
            t = f.flatten(2).transpose(1, 2) + _pos2d(h, w, c, f.device, oy, ox).to(f.dtype)
            t = self.out(self.norm(self.enc(t)))
            return f + t.transpose(1, 2).reshape(b, c, h, w)

    return ContextBlock()


def build_unet(encoder, classes, in_ch, ctx_layers=0, ctx_heads=8, encoder_weights=None):
    """smp.Unet。ctx_layers > 0 ならエンコーダの一番深い特徴 (画像の 1/32) に小さいトランスフォーマーを足す
    (model.ctx。小さい点と輪郭は今までどおり U-Net が見て、トランスフォーマーは画面全体の関係だけを見る)"""
    import segmentation_models_pytorch as smp
    model = smp.Unet(encoder, encoder_weights=encoder_weights, in_channels=in_ch, classes=classes)
    if ctx_layers > 0:
        model.ctx = _context_block(model.encoder.out_channels[-1], int(ctx_layers), int(ctx_heads))
        model.encoder.register_forward_hook(lambda m, i, out: list(out[:-1]) + [model.ctx(out[-1])])
    return model


def predict_planes(model, planes, mode, mean, std, dev, prior=None, uses_prior=False, train_hw=None):
    """画像 {'B', ...} (+ 事前マスク) -> 確率 (3, H, W)。2_steel_track.py と 1_steel_train.py の test で同じ計算:
    学習画像の大きさ (train_hw) と違えば その大きさにしてから推論して元に戻す、32 の倍数に反射で足す (事前マスクは 0 で足す)"""
    import torch
    H, W = next(iter(planes.values())).shape
    if train_hw is not None and (H, W) != tuple(train_hw):
        th, tw = (int(v) for v in train_hw)
        interp = cv2.INTER_AREA if th * tw < H * W else cv2.INTER_LINEAR
        planes = {k: cv2.resize(v, (tw, th), interpolation=interp) for k, v in planes.items()}
        if uses_prior and prior is not None:
            prior = np.stack([cv2.resize(c.astype(np.float32), (tw, th), interpolation=interp) for c in prior])
        p = predict_planes(model, planes, mode, mean, std, dev, prior, uses_prior)
        return np.stack([cv2.resize(c, (W, H), interpolation=cv2.INTER_LINEAR) for c in p])
    ph, pw = (-H) % 32, (-W) % 32
    planes = {k: cv2.copyMakeBorder(v, 0, ph, 0, pw, cv2.BORDER_REFLECT_101) for k, v in planes.items()}
    pr = None
    if uses_prior and prior is not None:
        pr = np.pad(prior.astype(np.float32), ((0, 0), (0, ph), (0, pw)))   # 事前マスクのパディングは 0 (学習と同じ)
    x = torch.from_numpy(make_input_raw(planes, mode, mean, std, pr, uses_prior))[None].to(dev)
    with torch.no_grad():
        out = model(x).softmax(1)[0].cpu().numpy()
    return out[:, :H, :W]

# ======================================================================
# 共通の部品 — binarized/1_bin_train.py から写したもの (commit bb568f7 の時点)
# ======================================================================

def resolve(p):
    """相対パスはこのファイルがあるフォルダ基準"""
    p = Path(p)
    return p if p.is_absolute() else HERE / p


def list_images(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)


def unique_dir(base):
    """base が既にあれば base2, base3 ... (前の結果を守る)"""
    base = Path(base)
    if not base.exists():
        return base
    i = 2
    while Path(f'{base}{i}').exists():
        i += 1
    return Path(f'{base}{i}')


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


def score_of(ev):
    return 0.4 * ev['iou'][1] + 0.6 * ev['iou'][2]   # 境界 IoU を重く (気泡の分け方を決める)


def state_in_channels(sd) -> int:
    """state_dict の入力チャンネル数 (最初の畳み込みの重みの2番目の次元)"""
    for k, v in sd.items():
        if k.startswith("encoder.") and v.ndim == 4:
            return int(v.shape[1])
    raise ValueError("state_dict にエンコーダの畳み込みが見つかりません")


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


PRIOR_CHANNELS = 2       # 事前マスクのチャンネル数 (内部, 輪郭)


PRIOR_EDGE_PX = 2        # 事前マスクの輪郭の幅 (px)。学習と推論で同じ値を使う (ckpt の prior_edge_px に記録)


Shape = Tuple[np.ndarray, int, int]   # (bbox で切り出した bool マスク, x0, y0)。tracker3.py と同じ


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


def prior_aug():
    return PriorAug(
        p_empty=PRIOR_P_EMPTY, p_drop=PRIOR_P_DROP, shift_px=PRIOR_SHIFT_PX, shift_size=PRIOR_SHIFT_SIZE,
        p_big_shift=PRIOR_P_BIG_SHIFT, scale=tuple(PRIOR_SCALE), morph_px=PRIOR_MORPH_PX, p_trunc=PRIOR_P_TRUNC,
        p_merge=PRIOR_P_MERGE, p_split=PRIOR_P_SPLIT, phantom_rate=PRIOR_PHANTOM_RATE)


# ======================================================================
# [1] Roboflow の書き出し -> B, D, DK, DB, マスク, 気泡ごとのラベル
# ======================================================================
def original_name(im):
    """COCO の画像 -> 元のファイル名 (Roboflow は 'name_jpg.rf.<hash>.jpg' に変える。extra.name があればそれ)"""
    ex = im.get('extra') or {}
    if ex.get('name'):
        return Path(ex['name']).name
    fn = Path(im['file_name']).name
    m = re.match(r'(.+?)_(jpg|jpeg|png|bmp|tif|tiff)\.rf\.[0-9A-Za-z]+\.\w+$', fn, flags=re.I)
    return f'{m.group(1)}.{m.group(2)}' if m else fn


def background_for(name, backgrounds=None, default=None):
    """元の名前 -> 背景画像のパス (BACKGROUNDS の先頭が一番長く一致するもの)。無ければ default"""
    backgrounds = BACKGROUNDS if backgrounds is None else backgrounds
    keys = sorted((k for k in backgrounds if name.startswith(k)), key=len, reverse=True)
    if keys:
        return backgrounds[keys[0]]
    return DEFAULT_BACKGROUND if default is None else default


def _split_dirs(src):
    return [d for d in sorted(Path(src).iterdir()) if d.is_dir() and d.name in SPLIT_MAP and (d / ANN_NAME).exists()]


def _preview(pl, lbl):
    c = lambda a: cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    sep = np.full((lbl.shape[0], 4, 3), 128, np.uint8)
    return np.hstack([c(pl['B']), sep, c(pl['DK']), sep, c(pl['DB']), sep, label_preview(pl['B'], lbl)])


def _save(dst, split, stem, pl, lbl, ins):
    for sub, a in ((PLANE_DIRS[k], v) for k, v in pl.items()):
        (dst / sub / split).mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst / sub / split / (stem + '.png')), a)
    for sub, a in (('masks', lbl), ('instances', ins.astype(np.uint16))):
        (dst / sub / split).mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst / sub / split / (stem + '.png')), a)


def dataset_key(src, old_src, train_hw=None):
    """DST/meta.json に書く「何から作ったか」。REBUILD_DATASET = False のとき、今の設定と違えば作り直す"""
    k = {'layout': DATASET_LAYOUT, 'src': str(Path(src).resolve()),
         'old_src': str(Path(old_src).resolve()) if old_src else None, 'preproc': list(PREPROC), 'bg_match': BG_MATCH}
    if train_hw is not None:
        k['train_hw'] = train_hw
    return k


def build_dataset(src, dst, old_src=None):
    """SRC (元画像) -> DST/{bin,diff,dark,bright,masks,instances}/<split>/。OLD_BIN_SRC があればその train / valid / test を
    DST/*/old/, old_val/, old_test/ に (D = DK = B, DB = 0)。
    戻り値: 新しい train 画像の大きさで一番多いもの (推論で画像の大きさをそろえる基準)"""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise FileNotFoundError(f'SRC フォルダがありません: {src}')
    (dst / 'meta.json').unlink(missing_ok=True)      # 途中で止まったときに古い meta.json で使い回さないように
    for sub in SUBDIRS + ('preview',):
        if (dst / sub).exists():
            shutil.rmtree(dst / sub)
    dirs = _split_dirs(src)
    if not dirs:
        raise FileNotFoundError(f'{src} の中に train/ valid/ test/ と {ANN_NAME} がありません')
    # 背景の割り当てを先に全部確認 (足りなければ一覧を出して止まる)
    missing, plan = [], []
    for sdir in dirs:
        images, by_img = load_coco(sdir / ANN_NAME)
        for im in images:
            name = original_name(im)
            bgp = background_for(name)
            if bgp is None:
                missing.append(f'{sdir.name}/{name}')
            plan.append((sdir, im, by_img.get(im['id'], []), bgp, name))
    if missing:
        raise SystemExit(f'背景画像が決まらない画像が {len(missing)}枚あります (BACKGROUNDS か DEFAULT_BACKGROUND を設定):\n  '
                         + '\n  '.join(missing[:20]) + ('\n  ...' if len(missing) > 20 else ''))
    names = Counter(name for _, _, _, _, name in plan)
    dup = sorted(n for n, c in names.items() if c > 1)
    if dup:       # Roboflow の Augmentation (同じ元画像の反転・明るさ違いのコピー) は背景画像と合わない
        raise SystemExit(f'同じ元画像から作られた画像が {len(dup)}組あります (例: {dup[:3]})。Roboflow の Augmentation を'
                         '付けて書き出していませんか? 背景画像と画素が合わなくなるので、Augmentation 無しで書き出し直してください '
                         '(このファイルの AUG_FLIP / AUG_ROTATE / COPY_PASTE を使う)')
    bg_cache, shapes = {}, Counter()
    stats = Counter()
    for sdir, im, anns, bgp, name in plan:
        split = SPLIT_MAP[sdir.name]
        raw = cv2.imread(str(sdir / im['file_name']))
        if raw is None:
            print(f'    読み込み失敗 (飛ばします): {sdir / im["file_name"]}')
            continue
        if (cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY) < 15).mean() > 0.5:
            raise SystemExit(f'SRC の画像が二値化画像に見えます (黒い画素が半分以上): {sdir.name}/{im["file_name"]}\n'
                             '  SRC には背景の残った元画像の書き出しを、今までの二値化画像は OLD_BIN_SRC に指定してください')
        if bgp not in bg_cache:
            bg = cv2.imread(str(resolve(bgp)))
            if bg is None:
                raise FileNotFoundError(f'背景画像が読めません: {bgp}')
            bg_cache[bgp] = bg
        if raw.shape != bg_cache[bgp].shape:
            raise SystemExit(f'{sdir.name}/{name}: 画像の大きさ {raw.shape[:2]} が背景画像 {bg_cache[bgp].shape[:2]} と違います。'
                             'Roboflow で Resize を付けて書き出していませんか? (Resize 無しで書き出し直す / 背景画像を確認)')
        bg_m, _, ok = match_background(raw, bg_cache[bgp], BG_MATCH)
        if not ok:
            stats['bg_rejected'] += 1
            if stats['bg_rejected'] <= 5:
                print(f'    ※ {sdir.name}/{name}: 背景の明るさ合わせの当てはめが不自然 (直す量が {BG_MATCH_MAX} 階調を超える) なので'
                      '合わせません (気泡が画面の大半? 背景画像が別の日?)')
        pl = make_planes(raw, bg_m, PREPROC)
        H, W = pl['B'].shape
        if (pl['B'] > 0).mean() > 0.3:
            stats['bright_frames'] += 1
            if stats['bright_frames'] <= 5:
                print(f'    ※ {sdir.name}/{name}: 二値化画像の {100 * (pl["B"] > 0).mean():.0f}% が光っています。'
                      '背景画像が合っていない (別の日・明るさが違う) かもしれません。DST/preview で確認')
        lbl, ins = make_target(anns, H, W, EDGE_PX)
        stem = Path(im['file_name']).stem
        _save(dst, split, stem, pl, lbl, ins)
        if stats[split + '_preview'] < N_PREVIEW:
            (dst / 'preview' / split).mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dst / 'preview' / split / (stem + '.png')), _preview(pl, lbl))
            stats[split + '_preview'] += 1
        stats[split] += 1
        stats[split + '_bubbles'] += len(anns)
        if split == 'train':
            shapes[(H, W)] += 1
    if not stats['val'] and stats['train']:          # valid が無ければ train の 10% を val に
        tr = list_images(dst / 'bin' / 'train')
        for p in tr[::10]:
            for sub in SUBDIRS:
                (dst / sub / 'val').mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst / sub / 'train' / p.name), str(dst / sub / 'val' / p.name))
            stats['val'] += 1
            stats['train'] -= 1
        print(f'  valid が無いので train の {stats["val"]}枚を val に分けました')
    for split in ('train', 'val', 'test'):
        print(f'  [{split}] 画像 {stats[split]}枚  気泡 {stats[split + "_bubbles"]}個')
    if not stats['test']:
        print('  ※ 新しい画像の test がありません。元画像での比較 [3] ができないので、Roboflow で test を分けてください')
    if old_src:
        if Path(old_src).resolve() == src.resolve():
            raise SystemExit(f'OLD_BIN_SRC が SRC と同じフォルダです: {old_src}\n'
                             '  OLD_BIN_SRC には今までの「二値化画像」の書き出し (best.pt を学習したときの 480枚) を指定してください')
        n_old = Counter()
        not_bin = []
        for sdir in _split_dirs(old_src):
            split = OLD_SPLIT[SPLIT_MAP[sdir.name]]
            images, by_img = load_coco(sdir / ANN_NAME)
            for im in images:
                g = cv2.imread(str(sdir / im['file_name']), cv2.IMREAD_GRAYSCALE)
                if g is None:
                    continue
                if (g < 15).mean() < 0.5:          # 二値化画像は 9割以上が黒。元画像 (背景が灰色) なら黒はほぼ 0
                    not_bin.append(f'{sdir.name}/{im["file_name"]}')
                lbl, ins = make_target(by_img.get(im['id'], []), *g.shape, EDGE_PX)
                # 差分は作れないので D = B。輪郭は界面 (暗い) とみなして DK = B, DB = 0
                pl = {'B': g, 'D': g, 'DK': g, 'DB': np.zeros_like(g)}
                _save(dst, split, OLD_PREFIX + Path(im['file_name']).stem, pl, lbl, ins)
                n_old[split] += 1
        if not_bin:
            raise SystemExit(f'OLD_BIN_SRC に二値化画像に見えない画像が {len(not_bin)}枚あります (黒い画素が半分未満):\n  '
                             + '\n  '.join(not_bin[:10]) + ('\n  ...' if len(not_bin) > 10 else '')
                             + '\n  OLD_BIN_SRC は今までの二値化画像の書き出し、SRC は元画像の書き出しです')
        print(f'  [old] 今までの二値化画像 (D = DK = B, DB = 0): train {n_old["old"]}枚 (学習に混ぜる), '
              f'valid {n_old["old_val"]}枚 (best の選び方), test {n_old["old_test"]}枚 (悪くなっていないかの確認)')
    hw = [int(v) for v in shapes.most_common(1)[0][0]] if shapes else None
    (dst / 'meta.json').write_text(json.dumps(dataset_key(src, old_src, train_hw=hw)), encoding='utf-8')
    print(f'  -> {dst}   (確認: {dst / "preview"}  左から B, DK (暗くなった分), DB (明るくなった分), ラベル)')
    return hw


# ======================================================================
# [2] 学習
# ======================================================================
class RawDS(Dataset):
    """(入力 (C, H, W), 3クラスのラベル) を返す。
    prior (TAU): 事前マスクも入れる。prior_mode = 'train' (毎回崩し方を変える) / 'empty' (全部 0) / 'synth' (画像ごとに固定)"""

    def __init__(self, root, splits, train, mode=None, prior=False, prior_mode=None):
        self.root = Path(root)
        self.items = [(s, p.stem) for s in splits for p in list_images(self.root / 'bin' / s)]
        self.train = train
        self.mode = mode or INPUT_MODE
        self.names = PLANES[self.mode]
        self.prior = prior
        self.prior_mode = prior_mode or ('train' if train else 'empty')
        self.aug = prior_aug()
        self.ch, self.cw = CROP
        self.bank = self._paste_bank() if (train and COPY_PASTE) else []

    def __len__(self):
        return len(self.items)

    def load(self, i):
        """-> (画像 [PLANES の順], ラベル, 気泡ごとのラベル)"""
        s, stem = self.items[i]
        r = lambda sub, flag=cv2.IMREAD_GRAYSCALE: cv2.imread(str(self.root / sub / s / (stem + '.png')), flag)
        planes = [r(PLANE_DIRS[n]) for n in self.names]
        m, ins = r('masks'), r('instances', cv2.IMREAD_UNCHANGED)
        if any(a is None for a in planes + [m, ins]):
            raise RuntimeError(f'{s}/{stem}: 画像 / マスクが読めません (REBUILD_DATASET = True で作り直す)')
        return planes, m, ins.astype(np.int32)

    def _paste_bank(self):
        """学習画像から「離れて1個だけある小さい気泡」を (画像, ラベル) ごと切り出す"""
        bank = []
        for i in range(len(self.items)):
            planes, m, _ = self.load(i)
            H, W = m.shape
            n, lab, st, _ = cv2.connectedComponentsWithStats(((m == 1) | (m == 2)).astype(np.uint8), 8)
            for k in range(1, n):
                x, y, w, h, a = st[k]
                if a < 4 or a >= CP_MAX_AREA or x == 0 or y == 0 or x + w >= W or y + h >= H:
                    continue
                comp = lab[y:y + h, x:x + w] == k
                lp = m[y:y + h, x:x + w].copy()
                lp[~comp] = 0
                if ndimage.label(lp == 1)[1] != 1:
                    continue
                bank.append(([p[y:y + h, x:x + w].copy() for p in planes], lp, comp))
        return bank

    def _copy_paste(self, planes, m, ins):
        if not self.bank or np.random.rand() >= CP_PROB:
            return planes, m, ins
        planes, m, ins = [p.copy() for p in planes], m.copy(), ins.copy()
        H, W = m.shape
        occ = cv2.dilate((m >= 1).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        nid = int(ins.max()) + 1
        for _ in range(np.random.randint(1, CP_MAX + 1)):
            pps, lp, cp = self.bank[np.random.randint(len(self.bank))]
            if np.random.rand() < 0.5:
                pps, lp, cp = [p[:, ::-1] for p in pps], lp[:, ::-1], cp[:, ::-1]
            h, w = cp.shape
            if h + 2 >= H or w + 2 >= W:
                continue
            for _try in range(10):
                y, x = np.random.randint(1, H - h - 1), np.random.randint(1, W - w - 1)
                if not occ[y:y + h, x:x + w][cp].any():
                    break
            else:
                continue
            a = np.random.uniform(*CP_ALPHA)
            for dst_img, src_img in zip(planes, pps):
                r = dst_img[y:y + h, x:x + w]
                r[cp] = np.clip(src_img[cp].astype(np.float32) * a, 0, 255).astype(np.uint8)
            m[y:y + h, x:x + w][cp] = lp[cp]
            ins[y:y + h, x:x + w][cp] = nid
            nid += 1
            occ[y - 1:y + h + 1, x - 1:x + w + 1] |= cv2.dilate(np.pad(cp, 1).astype(np.uint8),
                                                                 np.ones((5, 5), np.uint8)) > 0
        return planes, m, ins

    @staticmethod
    def _pad(arrs, ph, pw, border=cv2.BORDER_REFLECT_101):
        return [cv2.copyMakeBorder(a, 0, ph, 0, pw, border) if (ph or pw) else a for a in arrs]

    def sample(self, i):
        """-> (画像のリスト, ラベル, 気泡ごとのラベル)。気泡ごとのラベルは反射で足さない (0 で足す)"""
        planes, m, ins = self.load(i)
        H, W = m.shape
        if not self.train:
            ph, pw = (-H) % 32, (-W) % 32
            return self._pad(planes, ph, pw), self._pad([m], ph, pw)[0], self._pad([ins], ph, pw, cv2.BORDER_CONSTANT)[0]
        ph, pw = max(0, self.ch - H), max(0, self.cw - W)
        planes, m = self._pad(planes, ph, pw), self._pad([m], ph, pw)[0]
        ins = self._pad([ins], ph, pw, cv2.BORDER_CONSTANT)[0]
        H, W = m.shape
        y, x = np.random.randint(0, H - self.ch + 1), np.random.randint(0, W - self.cw + 1)
        cut = lambda a: np.ascontiguousarray(a[y:y + self.ch, x:x + self.cw])
        planes, m, ins = [cut(p) for p in planes], cut(m), cut(ins)
        planes, m, ins = self._copy_paste(planes, m, ins)
        if AUG_FLIP and np.random.rand() < 0.5:
            planes, m, ins = [p[:, ::-1] for p in planes], m[:, ::-1], ins[:, ::-1]
        if AUG_ROTATE and np.random.rand() < 0.5:
            M = cv2.getRotationMatrix2D((self.cw / 2, self.ch / 2), np.random.uniform(-5, 5), 1.0)
            warp = lambda a, f, b=cv2.BORDER_REFLECT_101: cv2.warpAffine(np.ascontiguousarray(a), M, (self.cw, self.ch),
                                                                         flags=f, borderMode=b)
            planes = [warp(p, cv2.INTER_LINEAR) for p in planes]
            m = warp(m, cv2.INTER_NEAREST)
            ins = warp(ins.astype(np.float32), cv2.INTER_NEAREST, cv2.BORDER_CONSTANT).astype(np.int32)
        return [np.ascontiguousarray(p) for p in planes], np.ascontiguousarray(m), np.ascontiguousarray(ins)

    def prior_for(self, i, ins):
        if not self.prior or self.prior_mode == 'empty':
            return None
        if self.prior_mode == 'synth':                    # 画像ごとに固定 (epoch で変わらない)
            rng = np.random.default_rng(SEED * 100003 + i)
        else:
            rng = np.random.default_rng(np.random.randint(2 ** 31))
        return synth_prior(ins, rng, self.aug)

    def __getitem__(self, i):
        planes, m, ins = self.sample(i)
        x = make_input_raw(dict(zip(self.names, planes)), self.mode, MEAN, STD, self.prior_for(i, ins), self.prior)
        return torch.from_numpy(x), torch.from_numpy(m.astype(np.int64))


@torch.no_grad()
def evaluate(model, dl, dev, n_cls=3):
    """クラスごとの画素 IoU [背景, 内部, 境界] (学習しない画素は数えない)"""
    model.eval()
    conf = torch.zeros(n_cls, n_cls, dtype=torch.long)
    for x, y in dl:
        p = model(x.to(dev)).argmax(1).cpu()
        ok = y.view(-1) != IGNORE_LABEL
        conf += torch.bincount(y.view(-1)[ok] * n_cls + p.view(-1)[ok], minlength=n_cls ** 2).view(n_cls, n_cls)
    tp = conf.diag().float()
    return {'iou': (tp / (conf.sum(0) + conf.sum(1) - tp).float().clamp(min=1)).tolist()}


def make_losses(dev):
    w = torch.tensor([1.0, 1.0, EDGE_W], device=dev)
    return (nn.CrossEntropyLoss(weight=w, ignore_index=IGNORE_LABEL),
            smp.losses.DiceLoss(mode='multiclass', ignore_index=IGNORE_LABEL))


def load_model(path, mode=None, prior=None, ctx_layers=None, dev='cpu'):
    """ckpt -> モデル。mode / prior / ctx_layers を指定するとその形にする (無い入力・部品の重みは 0 から =
    学習前は ckpt と同じ結果)。None なら ckpt のまま。
    TAU の ckpt を prior=False で読むと事前マスクの重みは捨てる (事前マスクなしの TAU と同じ結果)。
    戻り値: (モデル, ckpt, 形の情報)"""
    ck = torch.load(str(path), map_location='cpu')
    sd = {k: (v.float() if v.is_floating_point() else v) for k, v in ck['state_dict'].items()}
    src_mode, src_prior, src_names = ckpt_layout(ck, sd)
    mode = src_mode if mode is None else mode
    prior = src_prior if prior is None else prior
    c0 = ck.get('ctx') or {}
    layers = int(c0.get('layers', 0) if ctx_layers is None else ctx_layers)
    if c0.get('layers') and layers != c0['layers']:
        raise ValueError(f'{path}: トランスフォーマー {c0["layers"]}層の ckpt を CTX_LAYERS = {layers} では読めません')
    heads = int(c0.get('heads', CTX_HEADS))
    dst_names = channel_names(mode, prior)
    model = build_unet(ck['encoder'], ck.get('classes', 3), len(dst_names), layers, heads)
    missing, unexpected = model.load_state_dict(remap_first_conv(sd, src_names, dst_names), strict=False)
    bad = [k for k in missing if not k.startswith('ctx.')] + list(unexpected)
    if bad:
        raise ValueError(f'{path}: 重みが合いません: {bad[:5]}')
    copied = lambda n: n in src_names or (n in ('D0', 'D1', 'D2') and 'B' + n[1] in src_names)   # remap_first_conv と同じ
    info = {'mode': mode, 'prior': prior, 'ctx_layers': layers, 'ctx_heads': heads,
            'new_channels': [n for n in dst_names if not copied(n)],
            'dropped': [n for n in src_names if n not in dst_names], 'new_ctx': bool(layers and not c0.get('layers'))}
    return model.to(dev), ck, info


def make_model(dev):
    if FINETUNE_FROM:
        path = resolve(FINETUNE_FROM)
        if not path.exists():
            raise FileNotFoundError(f'FINETUNE_FROM が見つかりません: {path}')
        model, ck0, info = load_model(path, INPUT_MODE, USE_PRIOR, CTX_LAYERS, dev)
        notes = []
        if info['new_channels']:
            notes.append(f'{"/".join(info["new_channels"])} の重みを 0 で足した')
        if info['dropped']:
            notes.append(f'{"/".join(info["dropped"])} の重みは使わない')
        if info['new_ctx']:
            notes.append(f'トランスフォーマー {CTX_LAYERS}層を足した (出口の重み 0)')
        lost = [n for n in info['dropped'] if not n.startswith('P_')]   # 事前マスクは捨てても「事前マスクなし」と同じ
        print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]})'
              + (f'  — {"、".join(notes)}' if notes else '')
              + ('  (学習前は開始モデルと同じ結果)' if notes and not lost else ''))
        if lost:
            print(f'  ※ 開始モデルの入力 {"/".join(lost)} を使わないので、学習前でも開始モデルとは少し違う結果になります '
                  '(epoch 0 の基準もこの形のモデル)')
        return model.train(), ck0['encoder'], info['ctx_heads']
    model = build_unet('resnet34', 3, input_channels(INPUT_MODE, USE_PRIOR), CTX_LAYERS, CTX_HEADS, 'imagenet')
    return model.to(dev).train(), 'resnet34', CTX_HEADS


def input_weights(model):
    """入口 (最初の畳み込み) の重みの大きさ (入力の名前ごと)。0 のままの入力は使われていない"""
    w = next(p for p in model.encoder.parameters() if p.ndim == 4).detach().abs()
    names = channel_names(INPUT_MODE, USE_PRIOR)
    out = {}
    for j, n in enumerate(names):
        key = n.rstrip('012') if n[-1:] in '012' and n[:-1] in ('B', 'D') else n
        out.setdefault(key, []).append(float(w[:, j].mean()))
    return {k: sum(v) / len(v) for k, v in out.items()}


def old_val_ok(ev_old, ev0_old, tol=None):
    """今までの val (OLD_BIN_SRC の valid) が開始モデルから tol (OLD_VAL_TOL) を超えて下がっていないか"""
    tol = OLD_VAL_TOL if tol is None else tol
    if tol is None or ev_old is None or ev0_old is None:
        return True
    return score_of(ev_old) >= score_of(ev0_old) - tol


def train(root, out, dev, train_hw):
    root = Path(root)
    use_old = bool(OLD_BIN_SRC)        # test_check と同じ条件 (DST に残っている古いフォルダは使わない)
    has_old = use_old and bool(list_images(root / 'bin' / 'old'))
    tr = RawDS(root, ['train'] + (['old'] if has_old else []), True, prior=USE_PRIOR)
    # val: 事前マスクなし (TAU なら 事前マスクあり も。best の点数は両方の平均)
    vals = {'new': [RawDS(root, ['val'], False, prior=USE_PRIOR, prior_mode='empty')],
            'old': [RawDS(root, ['old_val'] if use_old else [], False, prior=USE_PRIOR, prior_mode='empty')]}
    if USE_PRIOR:
        vals['new'].append(RawDS(root, ['val'], False, prior=True, prior_mode='synth'))
        vals['old'].append(RawDS(root, ['old_val'] if use_old else [], False, prior=True, prior_mode='synth'))
    n_va, n_va_old = len(vals['new'][0]), len(vals['old'][0])
    w_old = OLD_VAL_WEIGHT if n_va_old else 0.0
    n_new = sum(1 for s, _ in tr.items if s == 'train')
    n_old = len(tr) - n_new
    if n_new < 1 or n_va < 1:
        raise RuntimeError(f'train {n_new}枚 / val {n_va}枚: 足りません')
    g = torch.Generator()
    g.manual_seed(SEED)
    if n_old:
        w = [(1 - OLD_SHARE) / n_new if s == 'train' else OLD_SHARE / n_old for s, _ in tr.items]
        n_epoch = max(BS, int(round(n_new / max(1e-6, 1 - OLD_SHARE))))
        dl_tr = DataLoader(tr, BS, sampler=WeightedRandomSampler(w, n_epoch, replacement=True, generator=g),
                           num_workers=WORKERS, drop_last=True)
    else:
        if n_new < BS:
            raise RuntimeError(f'train の画像が {n_new}枚しかありません (BS={BS} 以上必要)')
        dl_tr = DataLoader(tr, BS, shuffle=True, num_workers=WORKERS, drop_last=True, generator=g)
    extras = (f'  トランスフォーマー {CTX_LAYERS}層' if CTX_LAYERS else '') + ('  TAU (事前マスク)' if USE_PRIOR else '')
    print(f'  入力 {INPUT_MODE!r}{extras}  train 新 {n_new}枚 + 今までの二値化 {n_old}枚 (1 epoch {len(dl_tr) * BS}サンプル)  '
          f'val 新 {n_va}枚' + (f' + 今までの {n_va_old}枚 (点数の重み {w_old})' if n_va_old else '') + f'  device {dev}')
    if dev == 'cpu':
        print('  ※ GPU が見つかりません。CPU での学習はとても遅いです')
    if COPY_PASTE:
        print(f'  Copy-Paste の材料: 小さい気泡 {len(tr.bank)}個')

    model, encoder, heads = make_model(dev)
    ce, dice = make_losses(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    meta = {'encoder': encoder, 'classes': 3, 'mean': MEAN, 'std': STD,
            'in_channels': input_channels(INPUT_MODE, USE_PRIOR),
            'input': {'mode': INPUT_MODE, 'preproc': list(PREPROC), 'prior': bool(USE_PRIOR), 'prior_edge_px': PRIOR_EDGE_PX,
                      'bg_match': BG_MATCH},
            'ctx': {'layers': CTX_LAYERS, 'heads': heads} if CTX_LAYERS else None,
            'prior_aug': prior_aug().as_dict() if USE_PRIOR else None, 'prior_edge_px': PRIOR_EDGE_PX,
            'train_hw': train_hw, 'edge_px': EDGE_PX, 'edge_w': EDGE_W, 'crop': list(CROP), 'seed': SEED,
            'n_train': n_new, 'n_train_old': n_old, 'old_share': OLD_SHARE if n_old else None, 'n_val': n_va,
            'n_val_old': n_va_old, 'old_val_weight': w_old, 'old_val_tol': OLD_VAL_TOL if n_va_old else None,
            'src': str(SRC), 'old_src': str(OLD_BIN_SRC) if OLD_BIN_SRC else None,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'finetuned_from': str(FINETUNE_FROM) if FINETUNE_FROM else None}
    dls = {k: [DataLoader(d, 1, shuffle=False, num_workers=WORKERS) for d in v] if len(v[0]) else None
           for k, v in vals.items()}

    def eval_set(key):
        """(点数, 事前マスクなしの評価, 事前マスクありの評価 (TAU でなければ None))。val が無ければ None"""
        if dls[key] is None:
            return None
        evs = [evaluate(model, dl, dev) for dl in dls[key]]
        return sum(score_of(e) for e in evs) / len(evs), evs[0], (evs[1] if len(evs) > 1 else None)

    def validate():
        """(best を選ぶ点数, 新しい val, 今までの val (無ければ None), 新しい val の事前マスクあり (TAU 以外は None))"""
        sn, ev, ev_p = eval_set('new')
        o = eval_set('old')
        sc = sn if o is None else (1 - w_old) * sn + w_old * o[0]
        return sc, ev, (o[1] if o else None), ev_p

    def msg(ev_old, ev_p):
        s = '' if ev_old is None else f'  | 今までの val 内部 {ev_old["iou"][1]:.3f} 境界 {ev_old["iou"][2]:.3f}'
        if ev_p is not None:
            s += f'  | 事前マスクあり 境界 {ev_p["iou"][2]:.3f}'
        return s

    best, best_ep, ev0_old = -1.0, 0, None
    if FINETUNE_FROM:      # 開始モデル自体を基準にする -> 悪くなったら best.pt は開始モデルのまま
        best, ev0, ev0_old, ev0_p = validate()
        torch.save(dict(meta, state_dict=model.state_dict(), epoch=0, val=ev0, val_old=ev0_old), out / 'best.pt')
        print(f'  開始モデル val 内部 {ev0["iou"][1]:.3f} 境界 {ev0["iou"][2]:.3f}{msg(ev0_old, ev0_p)} (score {best:.4f})')
    log = []
    for ep in range(1, EPOCHS + 1):
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
        sc, ev, ev_old, ev_p = validate()
        entry = {'ep': ep, 'loss': tl / max(1, len(dl_tr)), 'score': sc, 'iou': ev['iou'],
                 'iou_old': ev_old['iou'] if ev_old else None, 'iou_prior': ev_p['iou'] if ev_p else None,
                 'input_w': input_weights(model)}
        if CTX_LAYERS:             # トランスフォーマーの出口の重みの大きさ (0 のままなら使っていない)
            entry['ctx_w'] = float(model.ctx.out.weight.detach().abs().mean())
        log.append(entry)
        ck = dict(meta, state_dict=model.state_dict(), epoch=ep, val=ev, val_old=ev_old, val_prior=ev_p)
        torch.save(ck, out / 'last.pt')
        mark = ''
        if not old_val_ok(ev_old, ev0_old):
            entry['old_val_drop'] = True
            if sc > best:
                mark = '  (今までの val で悪くなったので best にしない)'
        elif sc > best:
            best, best_ep = sc, ep
            torch.save(ck, out / 'best.pt')
            mark = '  <- best'
        iw = entry['input_w']
        ws = '  入口の重み ' + ' '.join(f'{k} {v:.4f}' for k, v in iw.items()) if len(iw) > 1 else ''
        cw = f'  トランスフォーマー出口 {entry["ctx_w"]:.4f}' if 'ctx_w' in entry else ''
        print(f'  ep {ep:3d}/{EPOCHS}  loss {entry["loss"]:.4f}  val 内部 {ev["iou"][1]:.3f} 境界 {ev["iou"][2]:.3f}'
              f'{msg(ev_old, ev_p)}{ws}{cw}   {time.time() - t0:.0f}s{mark}')
        (out / 'log.json').write_text(json.dumps(log, indent=1), encoding='utf-8')
    print(f'  学習完了。best = epoch {best_ep} (score {best:.4f})'
          + ('  ※ 開始モデルより良くならなかったので best.pt は開始モデルのまま' if FINETUNE_FROM and best_ep == 0 else ''))
    print('  入口の重み・トランスフォーマー出口が 0 に近いままなら、その入力・部品はほとんど使われていない')
    return out / 'best.pt'


# ======================================================================
# [3] test — 開始モデル (今の best.pt) と新しいモデルの比較
# ======================================================================
@torch.no_grad()
def eval_on_test(model, layout, root, dev, gt_inst, preview_dir=None, tag='', split='test', train_hw=None):
    """layout = (INPUT_MODE, 事前マスクを入れるか, 事前マスクの作り方 'empty' / 'synth')。
    2_steel_track.py と同じ計算 (predict_planes: 画像が学習画像の大きさ train_hw と違えばその大きさにして推論)"""
    mode, prior, prior_mode = layout
    model.eval()
    te = RawDS(root, [split], False, mode=mode, prior=prior, prior_mode=prior_mode)
    per = {n: [0, 0, 0, 0] for n, _, _ in SIZE_CLASSES}
    conf = np.zeros((3, 3), np.int64)
    n_gt = n_pred = 0
    for i in range(len(te)):
        stem = te.items[i][1]
        planes, m, ins = te.load(i)
        prob = predict_planes(model, dict(zip(te.names, planes)), mode, MEAN, STD, dev, te.prior_for(i, ins), prior,
                              train_hw)
        ok = m != IGNORE_LABEL
        conf += np.bincount(m[ok].astype(np.int64) * 3 + prob.argmax(0)[ok], minlength=9).reshape(3, 3)
        inst = extract_instances(prob, MIN_AREA, BAND, EDGE_THR, CLOSE, TINY_MAX)
        n_pred += int(len(np.unique(inst)) - (1 if (inst == 0).any() else 0))
        gts = gt_inst.get(stem)
        if gts is not None:
            st = match_by_size(gts, inst, IOU_MATCH)
            for k in per:
                per[k] = [u + v for u, v in zip(per[k], st[k])]
            n_gt += len(gts)
        if preview_dir is not None:
            preview_dir.mkdir(parents=True, exist_ok=True)
            D = cv2.imread(str(Path(root) / 'diff' / te.items[i][0] / (stem + '.png')), cv2.IMREAD_GRAYSCALE)
            cv2.imwrite(str(preview_dir / f'{stem}_{tag}.png'),
                        instance_overlay(D, inst, f'{tag} pred N={int(inst.max())}  GT N={"-" if gts is None else len(gts)}'))
    tp = np.diag(conf).astype(np.float64)
    iou = (tp / np.maximum(conf.sum(0) + conf.sum(1) - tp, 1)).tolist()
    return {'pixel_iou': {'bg': iou[0], 'in': iou[1], 'edge': iou[2]}, 'n_gt': n_gt, 'n_pred': n_pred,
            'train_hw': list(train_hw) if train_hw else None,
            'per_size': {k: {'gt': v[0], 'found': v[1], 'pred': v[2], 'correct': v[3],
                             'recall': v[1] / v[0] if v[0] else None,
                             'precision': v[3] / v[2] if v[2] else None} for k, v in per.items()}}


def print_table(title, cols):
    fmt = lambda v: '   -  ' if v is None else f'{100 * v:5.1f}%'
    print(f'\n  {title}: 気泡 {cols[-1][1]["n_gt"]}個 (正解と IoU >= {IOU_MATCH} なら同じ気泡)')
    print('  ' + f'{"大きさ":<8}' + ''.join(f'{n:>24}' for n, _ in cols))
    print('  ' + f'{"":<8}' + ''.join(f'{"再現率":>12}{"適合率":>12}' for _ in cols))
    for k, _, _ in SIZE_CLASSES:
        print('  ' + f'{k:<8}' + ''.join(f'{fmt(r["per_size"][k]["recall"]):>12}{fmt(r["per_size"][k]["precision"]):>12}'
                                         for _, r in cols) + f'   (正解 {cols[-1][1]["per_size"][k]["gt"]}個)')
    for n, r in cols:
        pi = r['pixel_iou']
        print(f'  [{n}] 予測 {r["n_pred"]}個 / 正解 {r["n_gt"]}個, 画素 IoU 内部 {pi["in"]:.3f} 境界 {pi["edge"]:.3f}')


def test_check(best_path, root, out, dev):
    """新しい test (SRC) と、OLD_BIN_SRC の test (今までの二値化画像) で 開始モデル と 新しいモデル を比べる。
    TAU なら新しいモデルは 事前マスクなし / あり (正解を崩したもの) の 2列"""
    root = Path(root)
    sets = []
    if list_images(root / 'bin' / 'test'):
        sets.append(('test', '新しい test (元画像)', load_gt_instances(resolve(SRC))))
    if OLD_BIN_SRC and list_images(root / 'bin' / 'old_test'):
        gt_old = {OLD_PREFIX + k: v for k, v in load_gt_instances(resolve(OLD_BIN_SRC)).items()}
        sets.append(('old_test', '今までの二値化画像の test (D = B。今の best.pt より悪くなっていないか)', gt_old))
    if not sets:
        print('  test の画像が無いので飛ばします')
        return
    models = []
    if FINETUNE_FROM:      # 開始モデルはそれ自身の入力で (今の best.pt なら 'bin'。事前マスクを使うモデルなら事前マスクなしで)
        m0, ck0, info0 = load_model(resolve(FINETUNE_FROM), dev=dev)
        name0 = f'開始モデル ({info0["mode"]})'
        models.append((name0, m0.eval(), (info0['mode'], info0['prior'], 'empty'), 'now', ck0.get('train_hw')))
    m1, ck1, _ = load_model(best_path, dev=dev)
    hw1 = ck1.get('train_hw')
    name1 = f'新 ({INPUT_MODE}' + (f', 変換{CTX_LAYERS}層' if CTX_LAYERS else '') + ')'
    if USE_PRIOR:
        models.append((name1[:-1] + ', 事前なし)', m1.eval(), (INPUT_MODE, True, 'empty'), 'new', hw1))
        models.append((name1[:-1] + ', 事前あり)', m1, (INPUT_MODE, True, 'synth'), 'new_prior', hw1))
    else:
        models.append((name1, m1.eval(), (INPUT_MODE, False, 'empty'), 'new', hw1))
    report = {'columns': None, 'iou_match': IOU_MATCH, 'input_mode': INPUT_MODE, 'ctx_layers': CTX_LAYERS,
              'use_prior': bool(USE_PRIOR)}
    for split, title, gt in sets:
        cols = [(name, eval_on_test(m, layout, root, dev, gt, out / f'{split}_preview', tag, split, hw))
                for name, m, layout, tag, hw in models]
        print_table(title, cols)
        report['columns' if split == 'test' else split] = dict(cols)
    (out / 'test_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print('  (2_steel_track.py と同じ計算: 画像の大きさが各モデルの学習画像と違えば、その大きさにして推論)')
    if BG_MATCH:
        print(f'  ※ 開始モデルも、このデータセットの画像 (背景の明るさ合わせ {BG_MATCH!r}) で評価しています。'
              '記録の無い開始モデル (best.pt) を 2_steel_track.py で使うと明るさを合わせないので、少し違う結果になります')
    print(f'\n  オーバーレイ -> {out}/' + ', '.join(f'{s}_preview' for s, _, _ in sets)
          + '  (背景は D。now = 開始モデル, new = 新しいモデル' + (', new_prior = 事前マスクあり' if USE_PRIOR else '') + ')')


# ======================================================================
def main():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    input_channels(INPUT_MODE)
    if not 0 <= OLD_SHARE < 1:
        raise ValueError(f'OLD_SHARE は 0 以上 1 未満: {OLD_SHARE}')
    if not 0 <= OLD_VAL_WEIGHT <= 1:
        raise ValueError(f'OLD_VAL_WEIGHT は 0 以上 1 以下: {OLD_VAL_WEIGHT}')
    if CTX_LAYERS and 512 % CTX_HEADS:
        raise ValueError(f'CTX_HEADS は 512 を割り切れる数に: {CTX_HEADS}')
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    dst = resolve(DST)
    if BG_MATCH not in BG_MATCH_MODES:
        raise ValueError(f'BG_MATCH は {BG_MATCH_MODES} のどれか: {BG_MATCH!r}')
    print('\n[1] データセットの変換 (B = 二値化, D = 差分, DK / DB = 暗く / 明るくなった分'
          + (f', 背景の明るさ合わせ {BG_MATCH!r})' if BG_MATCH else ')'))
    src, old_src = resolve(SRC), (resolve(OLD_BIN_SRC) if OLD_BIN_SRC else None)
    meta = json.loads((dst / 'meta.json').read_text(encoding='utf-8')) if (dst / 'meta.json').exists() else None
    same = meta is not None and {k: meta.get(k) for k in ('layout', 'src', 'old_src', 'preproc', 'bg_match')} == dataset_key(src, old_src)
    if REBUILD_DATASET or not same:     # SRC / OLD_BIN_SRC / PREPROC / BG_MATCH / 作り方の版 のどれかが変わったら作り直す
        if not REBUILD_DATASET and meta is not None:
            print('  変換済みのデータセットが今の設定 (SRC / OLD_BIN_SRC / PREPROC / BG_MATCH) と違うので作り直します')
        train_hw = build_dataset(src, dst, old_src)
    else:
        train_hw = meta['train_hw']
        print(f'  変換済みのデータセットを使います: {dst}')
    out = unique_dir(resolve(OUT))
    out.mkdir(parents=True)
    print(f'\n[2] 学習 -> {out}')
    best = train(dst, out, dev, train_hw)
    print('\n[3] test で確認')
    test_check(best, dst, out, dev)
    print('\n完了。2_steel_track.py の設定をこう変えてください:')
    print(f"  UNET_CKPT = r'{best}'")


if __name__ == '__main__':
    main()

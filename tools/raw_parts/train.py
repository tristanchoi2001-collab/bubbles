#!/usr/bin/env python
"""
二値化しない版 — U-Net の学習 (1ファイル)
=====================================================================
    python 1_raw_train.py

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
  [2] 学習 -> OUT/best.pt (2_raw_track.py の UNET_CKPT に入れる。入力の作り方・部品も ckpt に記録)
  [3] test で確認 -> 「開始モデル (今の best.pt)」と「新しいモデル」の 画素 IoU と 大きさ別の再現率・適合率
                    (新しい test と、OLD_BIN_SRC の test の 2つの表)
相対パスは「このファイルがあるフォルダ」基準。OUT が既にあれば runs/raw2, raw3 ... を新しく作る。
このファイルは tools/build_raw.py が作ったもの (共通の部品は binarized/1_bin_train.py と同じ)。
"""

# ======================================================================
#  設定 — ここだけ直して  python 1_raw_train.py  で実行。Windows のパスは r'...' で囲む
# ======================================================================
SRC = r'C:\Users\Tristan\Desktop\raw\coco'     # Roboflow の書き出し (元画像にラベル。train/ valid/ test/ を含む)
BACKGROUNDS = {                                 # 画像の元の名前の先頭 -> その動画の背景画像 (先頭が長く一致するものが優先)
    'test': r'C:\Users\Tristan\Desktop\raw\bg_test.jpg',
}
DEFAULT_BACKGROUND = None     # BACKGROUNDS のどれにも当てはまらない画像の背景。None なら当てはまらない画像の一覧を出して止まる
INPUT_MODE = 'bin+sign'       # 'bin+sign' (おすすめ) / 'bin+diff' / 'diff' / 'bin'
PREPROC = (15, 4, 0)          # 前処理 (Noise Cut, Brightness, Median)。今の二値化と同じ値 (B はこの値で作る)
OLD_BIN_SRC = None            # 今までの二値化画像の Roboflow 書き出し (例 480枚。train/ valid/ test/ を含む)。None なら使わない。
                              #   train/ -> 学習に混ぜる
                              #   valid/ -> best.pt の選び方にも使う (OLD_VAL_WEIGHT と OLD_VAL_TOL)
                              #   test/  -> [3] で別の表 (今までの画像で今の best.pt より悪くなっていないか)
                              # 新しいデータが少ないうちは使うのがおすすめ (小さい気泡などの今の力を保つ)
OLD_SHARE = 0.5               # 1 epoch で OLD_BIN_SRC の train の画像が占める割合 (新しい画像は 1 epoch に平均1回ずつ出る)
OLD_VAL_WEIGHT = 0.5          # best.pt を選ぶ点数 = (1 - この値) × 新しい val の点数 + この値 × OLD_BIN_SRC の val の点数。
                              # 0 なら新しい val だけで選ぶ (今までの val は表示だけ)
OLD_VAL_TOL = 0.01            # OLD_BIN_SRC の val の点数 (0.4×内部 IoU + 0.6×境界 IoU) が開始モデルよりこの値を超えて下がった epoch は
                              # best.pt に選ばない (新しい val で良くなっても、今までの画像で悪くなったものは使わない)。None なら確認しない
DST = r'dataset_raw'          # 変換したデータセットのフォルダ (毎回作り直す)
OUT = r'runs/raw'             # 結果のフォルダ。既にあれば runs/raw2, raw3 ... を自動で作る
REBUILD_DATASET = True        # True: 毎回 SRC から作り直す / False: DST に変換済みがあればそのまま使う
                              # (SRC / OLD_BIN_SRC / PREPROC が前と違えば作り直す)

# [1] ラベル変換 (今の学習と同じ)
EDGE_PX   = 4                 # 大きい気泡の境界の太さ (px)。小さい気泡は自動で 1〜3px
N_PREVIEW = 8                 # 確認用のプレビュー枚数 (DST/preview/。左から B, DK, DB, ラベル)

# [2] 学習
FINETUNE_FROM = r'best.pt'    # 開始モデル (今の best.pt / TAU の best.pt / 1_raw_train.py の best.pt)。足りない入力・部品の重みは 0 から。
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
USE_PRIOR = False             # True: TAU。事前マスク (内部, 輪郭) も入力する (2_raw_track.py が前後のフレームから作る)。
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
DATASET_LAYOUT = 3            # DST の作り方の版 (変わったら REBUILD_DATASET = False でも作り直す)
SUBDIRS = ('bin', 'diff', 'dark', 'bright', 'masks', 'instances')

# @@RAW_INPUT@@

# @@HELPERS@@


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
         'old_src': str(Path(old_src).resolve()) if old_src else None, 'preproc': list(PREPROC)}
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
        pl = make_planes(raw, bg_cache[bgp], PREPROC)
        H, W = pl['B'].shape
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
        print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]})'
              + (f'  — {"、".join(notes)} (学習前は開始モデルと同じ結果)' if notes else ''))
        return model.train(), ck0['encoder']
    model = build_unet('resnet34', 3, input_channels(INPUT_MODE, USE_PRIOR), CTX_LAYERS, CTX_HEADS, 'imagenet')
    return model.to(dev).train(), 'resnet34'


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

    model, encoder = make_model(dev)
    ce, dice = make_losses(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    meta = {'encoder': encoder, 'classes': 3, 'mean': MEAN, 'std': STD,
            'in_channels': input_channels(INPUT_MODE, USE_PRIOR),
            'input': {'mode': INPUT_MODE, 'preproc': list(PREPROC), 'prior': bool(USE_PRIOR), 'prior_edge_px': PRIOR_EDGE_PX},
            'ctx': {'layers': CTX_LAYERS, 'heads': CTX_HEADS} if CTX_LAYERS else None,
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
def eval_on_test(model, layout, root, dev, gt_inst, preview_dir=None, tag='', split='test'):
    """layout = (INPUT_MODE, 事前マスクを入れるか, 事前マスクの作り方 'empty' / 'synth')"""
    mode, prior, prior_mode = layout
    te = RawDS(root, [split], False, mode=mode, prior=prior, prior_mode=prior_mode)
    ev = evaluate(model, DataLoader(te, 1, shuffle=False, num_workers=WORKERS), dev)
    per = {n: [0, 0, 0, 0] for n, _, _ in SIZE_CLASSES}
    n_gt = n_pred = 0
    for i in range(len(te)):
        stem = te.items[i][1]
        planes, m, ins = te.load(i)
        H, W = m.shape
        x = te[i][0][None].to(dev)                      # 32 の倍数に足した入力 (val と同じ)
        prob = model(x).softmax(1)[0].cpu().numpy()[:, :H, :W]
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
    return {'pixel_iou': {'bg': ev['iou'][0], 'in': ev['iou'][1], 'edge': ev['iou'][2]}, 'n_gt': n_gt, 'n_pred': n_pred,
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
        m0, _, info0 = load_model(resolve(FINETUNE_FROM), dev=dev)
        name0 = f'開始モデル ({info0["mode"]})'
        models.append((name0, m0.eval(), (info0['mode'], info0['prior'], 'empty'), 'now'))
    m1, _, _ = load_model(best_path, dev=dev)
    name1 = f'新 ({INPUT_MODE}' + (f', 変換{CTX_LAYERS}層' if CTX_LAYERS else '') + ')'
    if USE_PRIOR:
        models.append((name1[:-1] + ', 事前なし)', m1.eval(), (INPUT_MODE, True, 'empty'), 'new'))
        models.append((name1[:-1] + ', 事前あり)', m1, (INPUT_MODE, True, 'synth'), 'new_prior'))
    else:
        models.append((name1, m1.eval(), (INPUT_MODE, False, 'empty'), 'new'))
    report = {'columns': None, 'iou_match': IOU_MATCH, 'input_mode': INPUT_MODE, 'ctx_layers': CTX_LAYERS,
              'use_prior': bool(USE_PRIOR)}
    for split, title, gt in sets:
        cols = [(name, eval_on_test(m, layout, root, dev, gt, out / f'{split}_preview', tag, split))
                for name, m, layout, tag in models]
        print_table(title, cols)
        report['columns' if split == 'test' else split] = dict(cols)
    (out / 'test_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
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
    print('\n[1] データセットの変換 (B = 二値化, D = 差分, DK / DB = 暗く / 明るくなった分)')
    src, old_src = resolve(SRC), (resolve(OLD_BIN_SRC) if OLD_BIN_SRC else None)
    meta = json.loads((dst / 'meta.json').read_text(encoding='utf-8')) if (dst / 'meta.json').exists() else None
    same = meta is not None and {k: meta.get(k) for k in ('layout', 'src', 'old_src', 'preproc')} == dataset_key(src, old_src)
    if REBUILD_DATASET or not same:     # SRC / OLD_BIN_SRC / PREPROC / 作り方の版 のどれかが変わったら作り直す
        if not REBUILD_DATASET and meta is not None:
            print('  変換済みのデータセットが今の設定 (SRC / OLD_BIN_SRC / PREPROC) と違うので作り直します')
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
    print('\n完了。2_raw_track.py の設定をこう変えてください:')
    print(f"  UNET_CKPT = r'{best}'")


if __name__ == '__main__':
    main()

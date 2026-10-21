#!/usr/bin/env python
"""
二値化しない版 — U-Net の学習 (1ファイル)
=====================================================================
    python 1_raw_train.py

元画像 (背景の残った画像) と背景画像から 2つの画像を作って U-Net に入れる:
  B = 二値化画像 (今と同じ: 背景差分 -> Noise Cut 未満を 0 -> ×Brightness。白い輪郭)
  D = 差分画像   (B から Noise Cut だけを外したもの。輪郭に加えて、気泡の中が液体より少し暗いという情報が残る)
INPUT_MODE で入れ方を選ぶ (同じデータで3つとも学習して test で比べられる):
  'bin+diff' : B と D を重ねて入れる (4チャンネル)。今の best.pt から始め、D の重みは 0 から
               -> 学習前は今の best.pt と全く同じ結果。学習で D (気泡の中の情報) を使い始める。おすすめ
  'diff'     : D だけ (3チャンネル)。best.pt から始めるが、入力の見た目が変わるので最初は今より悪い
  'bin'      : B だけ (今と同じ入力)。同じ新しいデータで学習した「比較の基準」
ラベルは Roboflow で元画像に描いたもの (座標は B・D と同じ)。背景画像は画像の名前の先頭で選ぶ (BACKGROUNDS)。
今までの二値化画像の学習データ (OLD_BIN_SRC) も使える (D は作れないので B と同じものを入れる =
「気泡の中の情報が無い画像」として学ぶ。白く飛んだ動画と同じ状況):
  train -> 学習に混ぜる / valid -> best.pt の選び方にも使う / test -> 今までの画像で悪くなっていないかを別の表で確認

流れ
  [1] Roboflow の書き出し (SRC) -> B, D, 3クラスのマスク (0=背景, 1=気泡内部, 2=気泡境界) (DST)
  [2] 学習 -> OUT/best.pt (2_raw_track.py の UNET_CKPT に入れる。入力の作り方も ckpt に記録)
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
INPUT_MODE = 'bin+diff'       # 'bin+diff' (おすすめ) / 'diff' / 'bin'
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
N_PREVIEW = 8                 # 確認用のプレビュー枚数 (DST/preview/。左から B, D, ラベル)

# [2] 学習
FINETUNE_FROM = r'best.pt'    # 今の best.pt (二値化, 3チャンネル)。ここから始める。None なら ImageNet から (EPOCHS を増やす)
LR      = 1e-4                # 学習率
EPOCHS  = 80                  # epoch 数
BS      = 4                   # VRAM が足りなければ 2
CROP    = (1088, 416)         # (高さ, 幅)。32 の倍数。画像の中から無作為な位置で切り出す (画像が小さければ反射で足す)
EDGE_W  = 6.0                 # 境界クラスの損失の重み
WORKERS = 0                   # Windows では 0 のまま
SEED    = 0
AUG_FLIP = False              # 左右反転
AUG_ROTATE = False            # ±5° 回転
COPY_PASTE = True             # 小さい気泡 (B, D, ラベルごと) を空いた所に貼る (今の学習と同じ)
CP_PROB = 0.5
CP_MAX = 15
CP_MAX_AREA = 500
CP_ALPHA = (0.35, 1.0)

# [3] test 確認用の後処理 (今の学習と同じ)
MIN_AREA = 4
BAND     = 25
EDGE_THR = 0.5
CLOSE    = 2
TINY_MAX = 300
IOU_MATCH = 0.3
# ======================================================================

import json
import random
import re
import shutil
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

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
DATASET_LAYOUT = 2            # DST の作り方の版 (変わったら REBUILD_DATASET = False でも作り直す)

# @@RAW_INPUT@@

# @@HELPERS@@


# ======================================================================
# [1] Roboflow の書き出し -> B, D, マスク
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


def _preview(B, D, lbl):
    c = lambda a: cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    sep = np.full((B.shape[0], 4, 3), 128, np.uint8)
    return np.hstack([c(B), sep, c(D), sep, label_preview(B, lbl)])


def dataset_key(src, old_src, train_hw=None):
    """DST/meta.json に書く「何から作ったか」。REBUILD_DATASET = False のとき、今の設定と違えば作り直す"""
    k = {'layout': DATASET_LAYOUT, 'src': str(Path(src).resolve()),
         'old_src': str(Path(old_src).resolve()) if old_src else None, 'preproc': list(PREPROC)}
    if train_hw is not None:
        k['train_hw'] = train_hw
    return k


def build_dataset(src, dst, old_src=None):
    """SRC (元画像) -> DST/{bin,diff,masks}/<split>/。OLD_BIN_SRC があればその train / valid / test を
    DST/*/old/, old_val/, old_test/ に (D = B)。
    戻り値: 新しい train 画像の大きさで一番多いもの (推論で画像の大きさをそろえる基準)"""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise FileNotFoundError(f'SRC フォルダがありません: {src}')
    for sub in ('bin', 'diff', 'masks', 'preview'):
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
        B, D = bin_diff(raw, bg_cache[bgp], PREPROC)
        H, W = B.shape
        lbl, _ = make_target(anns, H, W, EDGE_PX)
        stem = Path(im['file_name']).stem
        for sub, a in (('bin', B), ('diff', D), ('masks', lbl)):
            (dst / sub / split).mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dst / sub / split / (stem + '.png')), a)
        if stats[split + '_preview'] < N_PREVIEW:
            (dst / 'preview' / split).mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dst / 'preview' / split / (stem + '.png')), _preview(B, D, lbl))
            stats[split + '_preview'] += 1
        stats[split] += 1
        stats[split + '_bubbles'] += len(anns)
        if split == 'train':
            shapes[(H, W)] += 1
    if not stats['val'] and stats['train']:          # valid が無ければ train の 10% を val に
        tr = list_images(dst / 'bin' / 'train')
        for p in tr[::10]:
            for sub in ('bin', 'diff', 'masks'):
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
                lbl, _ = make_target(by_img.get(im['id'], []), *g.shape, EDGE_PX)
                stem = OLD_PREFIX + Path(im['file_name']).stem
                for sub, a in (('bin', g), ('diff', g), ('masks', lbl)):   # D は作れないので B と同じ
                    (dst / sub / split).mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(str(dst / sub / split / (stem + '.png')), a)
                n_old[split] += 1
        if not_bin:
            raise SystemExit(f'OLD_BIN_SRC に二値化画像に見えない画像が {len(not_bin)}枚あります (黒い画素が半分未満):\n  '
                             + '\n  '.join(not_bin[:10]) + ('\n  ...' if len(not_bin) > 10 else '')
                             + '\n  OLD_BIN_SRC は今までの二値化画像の書き出し、SRC は元画像の書き出しです')
        print(f'  [old] 今までの二値化画像 (D = B): train {n_old["old"]}枚 (学習に混ぜる), '
              f'valid {n_old["old_val"]}枚 (best の選び方), test {n_old["old_test"]}枚 (悪くなっていないかの確認)')
    hw = [int(v) for v in shapes.most_common(1)[0][0]] if shapes else None
    (dst / 'meta.json').write_text(json.dumps(dataset_key(src, old_src, train_hw=hw)), encoding='utf-8')
    print(f'  -> {dst}   (確認: {dst / "preview"}  左から B, D, ラベル)')
    return hw


# ======================================================================
# [2] 学習
# ======================================================================
class RawDS(Dataset):
    """(入力 (C, H, W), 3クラスのラベル) を返す。mode = 'bin' / 'diff' / 'bin+diff'"""

    def __init__(self, root, splits, train, mode=None):
        self.root = Path(root)
        self.items = [(s, p.stem) for s in splits for p in list_images(self.root / 'bin' / s)]
        self.train = train
        self.mode = mode or INPUT_MODE
        self.ch, self.cw = CROP
        self.bank = self._paste_bank() if (train and COPY_PASTE) else []

    def __len__(self):
        return len(self.items)

    def load(self, i):
        s, stem = self.items[i]
        r = lambda sub: cv2.imread(str(self.root / sub / s / (stem + '.png')), cv2.IMREAD_GRAYSCALE)
        B, D, m = r('bin'), r('diff'), r('masks')
        if B is None or D is None or m is None:
            raise RuntimeError(f'{s}/{stem}: B / D / マスクが読めません (REBUILD_DATASET = True で作り直す)')
        return B, D, m

    def _paste_bank(self):
        """学習画像から「離れて1個だけある小さい気泡」を (B, D, ラベル) ごと切り出す"""
        bank = []
        for i in range(len(self.items)):
            B, D, m = self.load(i)
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
                bank.append((B[y:y + h, x:x + w].copy(), D[y:y + h, x:x + w].copy(), lp, comp))
        return bank

    def _copy_paste(self, B, D, m):
        if not self.bank or np.random.rand() >= CP_PROB:
            return B, D, m
        B, D, m = B.copy(), D.copy(), m.copy()
        H, W = m.shape
        occ = cv2.dilate((m >= 1).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        for _ in range(np.random.randint(1, CP_MAX + 1)):
            bp, dp, lp, cp = self.bank[np.random.randint(len(self.bank))]
            if np.random.rand() < 0.5:
                bp, dp, lp, cp = bp[:, ::-1], dp[:, ::-1], lp[:, ::-1], cp[:, ::-1]
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
            for dst_img, src_img in ((B, bp), (D, dp)):
                r = dst_img[y:y + h, x:x + w]
                r[cp] = np.clip(src_img[cp].astype(np.float32) * a, 0, 255).astype(np.uint8)
            m[y:y + h, x:x + w][cp] = lp[cp]
            occ[y - 1:y + h + 1, x - 1:x + w + 1] |= cv2.dilate(np.pad(cp, 1).astype(np.uint8),
                                                                 np.ones((5, 5), np.uint8)) > 0
        return B, D, m

    @staticmethod
    def _pad(arrs, ph, pw):
        return [cv2.copyMakeBorder(a, 0, ph, 0, pw, cv2.BORDER_REFLECT_101) if (ph or pw) else a for a in arrs]

    def sample(self, i):
        B, D, m = self.load(i)
        H, W = m.shape
        if not self.train:
            return self._pad([B, D, m], (-H) % 32, (-W) % 32)
        B, D, m = self._pad([B, D, m], max(0, self.ch - H), max(0, self.cw - W))
        H, W = m.shape
        y, x = np.random.randint(0, H - self.ch + 1), np.random.randint(0, W - self.cw + 1)
        B, D, m = (np.ascontiguousarray(a[y:y + self.ch, x:x + self.cw]) for a in (B, D, m))
        B, D, m = self._copy_paste(B, D, m)
        if AUG_FLIP and np.random.rand() < 0.5:
            B, D, m = B[:, ::-1], D[:, ::-1], m[:, ::-1]
        if AUG_ROTATE and np.random.rand() < 0.5:
            M = cv2.getRotationMatrix2D((self.cw / 2, self.ch / 2), np.random.uniform(-5, 5), 1.0)
            warp = lambda a, f: cv2.warpAffine(np.ascontiguousarray(a), M, (self.cw, self.ch), flags=f,
                                               borderMode=cv2.BORDER_REFLECT_101)
            B, D, m = warp(B, cv2.INTER_LINEAR), warp(D, cv2.INTER_LINEAR), warp(m, cv2.INTER_NEAREST)
        return [np.ascontiguousarray(a) for a in (B, D, m)]

    def __getitem__(self, i):
        B, D, m = self.sample(i)
        x = make_input_raw(B, D, self.mode, MEAN, STD)
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


def drop_prior_channels(sd):
    """TAU (5チャンネル = 画像3 + 事前マスク2) の重み -> 画像 3チャンネルだけの重み。
    事前マスクの入口の重みを捨てるだけなので、「事前マスクなし (全部 0) の TAU」と全く同じ結果になる"""
    k0 = next(k for k, v in sd.items() if k.startswith('encoder.') and v.ndim == 4)
    sd = dict(sd)
    sd[k0] = sd[k0][:, :3].contiguous()
    return sd


def load_model(path, mode, dev):
    """ckpt -> mode の入力のモデル。3チャンネルの best.pt から 'bin+diff' を作るときは D の重みを 0 で足す。
    TAU (1_bin_train.py の USE_PRIOR = True、5チャンネル) は事前マスクの重みを捨てて 3チャンネルとして使う"""
    ck = torch.load(str(path), map_location='cpu')
    sd = {k: (v.float() if v.is_floating_point() else v) for k, v in ck['state_dict'].items()}
    src_ch, want = state_in_channels(sd), input_channels(mode)
    if src_ch == 5 and not ck.get('input'):
        sd, src_ch = drop_prior_channels(sd), 3
        ck = dict(ck, tau_dropped_prior=True)
    model = build_model(ck['encoder'], ck.get('classes', 3), want)
    if src_ch == want:
        model.load_state_dict(sd)
    elif src_ch == 3 and want == 4:
        model.load_state_dict(expand_state_dict(sd, model))
    else:
        raise ValueError(f'{path}: {src_ch}チャンネルの重みから {mode!r} ({want}チャンネル) は作れません')
    return model.to(dev), ck


def make_model(dev):
    if FINETUNE_FROM:
        path = resolve(FINETUNE_FROM)
        if not path.exists():
            raise FileNotFoundError(f'FINETUNE_FROM が見つかりません: {path}')
        model, ck0 = load_model(path, INPUT_MODE, dev)
        print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]})'
              + ('  — TAU (5チャンネル) の事前マスクの重みは使わない (事前マスクなしの TAU と同じ)' if ck0.get('tau_dropped_prior') else '')
              + ('  — D の重みを 0 で足した 4チャンネル版 (学習前は今の best.pt と同じ結果)' if INPUT_MODE == 'bin+diff' else ''))
        return model.train(), ck0['encoder']
    model = build_model('resnet34', 3, input_channels(INPUT_MODE), 'imagenet')
    return model.to(dev).train(), 'resnet34'


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
    tr = RawDS(root, ['train'] + (['old'] if has_old else []), True)
    va = RawDS(root, ['val'], False)
    va_old = RawDS(root, ['old_val'] if use_old else [], False)
    w_old = OLD_VAL_WEIGHT if len(va_old) else 0.0
    n_new = sum(1 for s, _ in tr.items if s == 'train')
    n_old = len(tr) - n_new
    if n_new < 1 or len(va) < 1:
        raise RuntimeError(f'train {n_new}枚 / val {len(va)}枚: 足りません')
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
    print(f'  入力 {INPUT_MODE!r}  train 新 {n_new}枚 + 今までの二値化 {n_old}枚 (1 epoch {len(dl_tr) * BS}サンプル)  '
          f'val 新 {len(va)}枚' + (f' + 今までの {len(va_old)}枚 (点数の重み {w_old})' if len(va_old) else '')
          + f'  device {dev}')
    if dev == 'cpu':
        print('  ※ GPU が見つかりません。CPU での学習はとても遅いです')
    if COPY_PASTE:
        print(f'  Copy-Paste の材料: 小さい気泡 {len(tr.bank)}個')

    model, encoder = make_model(dev)
    ce, dice = make_losses(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    meta = {'encoder': encoder, 'classes': 3, 'mean': MEAN, 'std': STD, 'in_channels': input_channels(INPUT_MODE),
            'input': {'mode': INPUT_MODE, 'preproc': list(PREPROC)}, 'train_hw': train_hw,
            'edge_px': EDGE_PX, 'edge_w': EDGE_W, 'crop': list(CROP), 'seed': SEED,
            'n_train': n_new, 'n_train_old': n_old, 'old_share': OLD_SHARE if n_old else None, 'n_val': len(va),
            'n_val_old': len(va_old), 'old_val_weight': w_old, 'old_val_tol': OLD_VAL_TOL if len(va_old) else None,
            'src': str(SRC), 'old_src': str(OLD_BIN_SRC) if OLD_BIN_SRC else None,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'finetuned_from': str(FINETUNE_FROM) if FINETUNE_FROM else None}
    dl_va = DataLoader(va, 1, shuffle=False, num_workers=WORKERS)
    dl_va_old = DataLoader(va_old, 1, shuffle=False, num_workers=WORKERS) if len(va_old) else None

    def validate():
        """(best を選ぶ点数, 新しい val, 今までの val (無ければ None))"""
        ev = evaluate(model, dl_va, dev)
        ev_old = evaluate(model, dl_va_old, dev) if dl_va_old is not None else None
        sc = score_of(ev) if ev_old is None else (1 - w_old) * score_of(ev) + w_old * score_of(ev_old)
        return sc, ev, ev_old

    def old_msg(ev_old):
        return '' if ev_old is None else f'  | 今までの val 内部 {ev_old["iou"][1]:.3f} 境界 {ev_old["iou"][2]:.3f}'

    best, best_ep, ev0_old = -1.0, 0, None
    if FINETUNE_FROM:      # 開始モデル自体を基準にする -> 悪くなったら best.pt は開始モデルのまま
        best, ev0, ev0_old = validate()
        torch.save(dict(meta, state_dict=model.state_dict(), epoch=0, val=ev0, val_old=ev0_old), out / 'best.pt')
        print(f'  開始モデル val 内部 {ev0["iou"][1]:.3f} 境界 {ev0["iou"][2]:.3f}{old_msg(ev0_old)} (score {best:.4f})')
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
        sc, ev, ev_old = validate()
        entry = {'ep': ep, 'loss': tl / max(1, len(dl_tr)), 'score': sc, 'iou': ev['iou'],
                 'iou_old': ev_old['iou'] if ev_old else None}
        if INPUT_MODE == 'bin+diff':      # D の重みの大きさ (0 のままなら D を使っていない)
            w1 = next(p for p in model.encoder.parameters() if p.ndim == 4).detach().abs()
            entry['diff_w'] = float(w1[:, 3].mean())
            entry['bin_w'] = float(w1[:, :3].mean())
        log.append(entry)
        ck = dict(meta, state_dict=model.state_dict(), epoch=ep, val=ev, val_old=ev_old)
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
        dw = f'  D の重み {entry["diff_w"]:.4f} (B {entry["bin_w"]:.4f})' if 'diff_w' in entry else ''
        print(f'  ep {ep:3d}/{EPOCHS}  loss {entry["loss"]:.4f}  val 内部 {ev["iou"][1]:.3f} 境界 {ev["iou"][2]:.3f}'
              f'{old_msg(ev_old)}{dw}   {time.time() - t0:.0f}s{mark}')
        (out / 'log.json').write_text(json.dumps(log, indent=1), encoding='utf-8')
    print(f'  学習完了。best = epoch {best_ep} (score {best:.4f})'
          + ('  ※ 開始モデルより良くならなかったので best.pt は開始モデルのまま' if FINETUNE_FROM and best_ep == 0 else ''))
    return out / 'best.pt'


# ======================================================================
# [3] test — 開始モデル (今の best.pt) と新しいモデルの比較
# ======================================================================
@torch.no_grad()
def eval_on_test(model, mode, root, dev, gt_inst, preview_dir=None, tag='', split='test'):
    te = RawDS(root, [split], False, mode=mode)
    ev = evaluate(model, DataLoader(te, 1, shuffle=False, num_workers=WORKERS), dev)
    per = {n: [0, 0, 0, 0] for n, _, _ in SIZE_CLASSES}
    n_gt = n_pred = 0
    for i in range(len(te)):
        stem = te.items[i][1]
        B, D, m = te.load(i)
        H, W = m.shape
        Bp, Dp = (cv2.copyMakeBorder(a, 0, (-H) % 32, 0, (-W) % 32, cv2.BORDER_REFLECT_101) for a in (B, D))
        x = torch.from_numpy(make_input_raw(Bp, Dp, mode, MEAN, STD))[None].to(dev)
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
    """新しい test (SRC) と、OLD_BIN_SRC の test (今までの二値化画像) で 開始モデル と 新しいモデル を比べる"""
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
    if FINETUNE_FROM:      # 開始モデルはそれ自身の入力で (今の best.pt なら 'bin')
        mode0 = (torch.load(str(resolve(FINETUNE_FROM)), map_location='cpu').get('input') or {}).get('mode', 'bin')
        models.append((f'開始モデル ({mode0})', load_model(resolve(FINETUNE_FROM), mode0, dev)[0].eval(), mode0, 'now'))
    models.append((f'新 ({INPUT_MODE})', load_model(best_path, INPUT_MODE, dev)[0].eval(), INPUT_MODE, 'new'))
    report = {'columns': None, 'iou_match': IOU_MATCH, 'input_mode': INPUT_MODE}
    for split, title, gt in sets:
        cols = [(name, eval_on_test(m, mode, root, dev, gt, out / f'{split}_preview', tag, split))
                for name, m, mode, tag in models]
        print_table(title, cols)
        report['columns' if split == 'test' else split] = dict(cols)
    (out / 'test_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'\n  オーバーレイ -> {out}/' + ', '.join(f'{s}_preview' for s, _, _ in sets)
          + '  (背景は D。now = 開始モデル, new = 新しいモデル)')


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
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    dst = resolve(DST)
    print('\n[1] データセットの変換 (B = 二値化, D = 差分)')
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

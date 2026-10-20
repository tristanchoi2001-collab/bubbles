#!/usr/bin/env python
"""Tracking-aware U-Net (TAU) の学習 — 1_unet_train.py に「事前マスク」の入力を足したもの

    python 1_tau_unet_train.py

1_unet_train.py との違い
  - 入力が 5チャンネル: 画像 ×3 (今までと同じ) + 事前マスク 2枚 (このフレームに気泡がどこにあるはずか: 内部・輪郭)
    推論 (tau_tracker.py) では、前のパスのトラッカーが前後のフレームから予測した気泡マスクが入る
  - 学習用の事前マスクは、正解ラベルの気泡を崩して作る (tau_unet.synth_prior)。連続フレームのラベルは要らない
      見落とし (消す) / 位置ずれ / 変形 / 一部欠け / 隣と融合 / 割れ / 何も無い所の気泡 / 事前マスクなし
    -> 「事前マスクを参考にするが、画像に無いものは出さない・画像にあるものは事前マスクに無くても出す」を学ぶ
  - FINETUNE_FROM (今の best.pt) から始める。最初の畳み込みに事前マスク用の重みを 0 で足すので、
    学習前は best.pt と全く同じ結果 = 「今より悪くならない所」から始まる
  - val は「事前マスクなし」と「事前マスクあり (正解から作ったもの。毎 epoch 同じ)」の両方で評価する。
    best は BEST_BY で選ぶ (既定: 崩した画像・事前マスクありの点数が最高の epoch。ただし元の画像・事前マスクなしの点数が
    開始モデルより BEST_EMPTY_TOL 以上下がった epoch は選ばない)。毎 epoch「事前の効果」(崩した画像での ありとなしの
    境界 IoU の差) と事前マスク用の重みの大きさも表示する (0 のままなら事前マスクを使っていない)
    「写し」= 事前マスクにあって正解では背景の画素を、気泡と出した割合 (事前マスクをそのまま写していないかの目安。低いほどよい)
  - 正解の気泡ごとのラベルマップ (instances/) もデータセットに保存する (事前マスクを作るため)
  - 画像を崩す増強 (DEGRADE_*): 学習画像の気泡の輪郭を一部消す / 途切れ途切れにし、その気泡は事前マスクに必ず残す
    (正解ラベルはそのまま)。学習画像は輪郭がはっきりしていて画像だけで正解が分かるため、崩さないと事前マスクを全く使わない
    ことが 1回目の学習 (80 epoch で事前の効果 +0.0001) で分かった。val も「崩した画像」で事前なし/ありを比べる
  - 小さい点のラベル補充 (dot_labels.py) の結果を使える: SRC = dot_labels の coco/ (点を足したラベル)、
    IGNORE_SRC = dot_labels の ignore/ (確認していない点の候補 = 学習しない画素)
  - USE_PRIOR = False で事前マスクなしの普通の U-Net (3チャンネル) も学習できる (tracker3.py / watershed.py でそのまま使える)。
    ラベル補充の効果だけを比べるときはこちら

流れ
  [1] Roboflow の COCO-segmentation 書き出し → 3クラスのマスク (0=背景, 1=気泡内部, 2=気泡境界) + 気泡ごとのラベルマップ (DST)
  [2] 学習 → OUT/best.pt (tau_tracker.py の UNET_CKPT に入れる)
  [3] test で確認 → 画素 IoU、気泡の大きさ別の再現率・適合率 (事前マスクなし / あり, FINETUNE_FROM との比較)

tau_unet.py を同じフォルダに置くこと。相対パスは「このファイルがあるフォルダ」基準。
OUT が既にあれば runs/tau2, runs/tau3 ... を新しく作る (前の結果を上書きしない)。
"""

# ======================================================================
#  設定 — ここだけ直して  python 1_tau_unet_train.py  で実行
#  Windows のパスは r'...' で囲む
# ======================================================================
SRC = r'C:\Users\Tristan\Desktop\ams\unet\cocosegmentation'   # Roboflow の書き出しフォルダ (train/ valid/ test/ を含む)
DST = r'dataset_tau'          # 変換したデータセットのフォルダ (images/ masks/ instances/ preview/ は毎回作り直す)
OUT = r'runs/tau'             # 結果のフォルダ。既にあれば runs/tau2, tau3 ... を自動で作る

REBUILD_DATASET = True        # True : 毎回 SRC から変換し直す (Roboflow のラベル修正が反映される)
                              # False: DST に変換済みのデータがあればそのまま使う (instances/ が無ければ作り直す)
IGNORE_SRC = None             # dot_labels.py の書き出しの ignore フォルダ (例 r'dot_labels\ignore')。None なら使わない。
                              # <split>/<画像名>.png の白い所 (ラベルされていない点の候補) を、背景としても気泡としても学習しない。
                              # val/test の評価でもその画素と、そこに出た気泡は数えない。変えたら REBUILD_DATASET = True で
USE_PRIOR = True              # True : TAU (画像 + 事前マスクの 5チャンネル) を学習 → tau_tracker.py で使う
                              # False: 事前マスクなしの普通の U-Net (3チャンネル) を学習 → tracker3.py / watershed.py の
                              #        UNET_CKPT にそのまま使える。ラベル (dot_labels.py) の効果だけを比べたいときはこちら。
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

import json
import random
import shutil
import sys
import time
from collections import Counter
from dataclasses import replace
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

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
try:
    import tau_unet
except ImportError:
    raise SystemExit('tau_unet.py が見つかりません。このファイルと同じフォルダに置いてください')

MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
SPLIT_MAP = {'train': 'train', 'valid': 'val', 'val': 'val', 'test': 'test'}
IGNORE_LABEL = 255            # マスクの「学習しない」画素 (IGNORE_SRC)。損失・評価で除く


def prior_aug():
    return tau_unet.PriorAug(
        p_empty=PRIOR_P_EMPTY, p_drop=PRIOR_P_DROP, shift_px=PRIOR_SHIFT_PX, shift_size=PRIOR_SHIFT_SIZE,
        p_big_shift=PRIOR_P_BIG_SHIFT, scale=tuple(PRIOR_SCALE), morph_px=PRIOR_MORPH_PX, p_trunc=PRIOR_P_TRUNC,
        p_merge=PRIOR_P_MERGE, p_split=PRIOR_P_SPLIT, phantom_rate=PRIOR_PHANTOM_RATE)


def degrade_cfg():
    return tau_unet.ImageDegrade(n_max=DEGRADE_N_MAX, min_area=DEGRADE_MIN_AREA, p_fade=DEGRADE_P_FADE,
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
        return tau_unet.synth_prior(ins, rng, aug, keep_ids=keep)

    def sample(self, i, force_degrade=False):
        """(画像, 3クラスのラベル, 気泡ごとのラベル, 崩した気泡, 事前マスク)"""
        g, m, ins = self.load(i)
        g, m, ins = self._augment(g, m, ins) if self.train else self._pad32(g, m, ins)
        keep = ()
        if not USE_PRIOR:             # 3チャンネル: 画像を崩さない (事前マスクで補えないので、正解と画像が合わなくなるだけ)
            pass
        elif self.train and (force_degrade or (DEGRADE_P > 0 and np.random.rand() < DEGRADE_P)):
            g, keep = tau_unet.degrade_image(g, ins, np.random.default_rng(np.random.randint(0, 2 ** 31 - 1)), degrade_cfg())
        elif not self.train and self.val_degrade:
            g, keep = tau_unet.degrade_image(g, ins, np.random.default_rng((SEED, i, 7)), degrade_cfg())
        return g, m, ins, keep, self.prior_for(i, ins, keep)

    def __getitem__(self, i):
        g, m, ins, keep, prior = self.sample(i)
        x = tau_unet.make_input(g, prior, self.mean, self.std, uses_prior=USE_PRIOR)
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
        if x.shape[1] > tau_unet.IMAGE_CHANNELS:
            ph = (x[:, tau_unet.IMAGE_CHANNELS] > 0.5) & (y == 0)
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
    w = first_conv.detach()[:, tau_unet.IMAGE_CHANNELS:].abs()
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
    in_ch = tau_unet.IMAGE_CHANNELS + (tau_unet.PRIOR_CHANNELS if USE_PRIOR else 0)
    if FINETUNE_FROM:
        path = resolve(FINETUNE_FROM)
        if not path.exists():
            raise FileNotFoundError(f'FINETUNE_FROM が見つかりません: {path}  (今の best.pt のパスを入れてください)')
        if not USE_PRIOR:
            model, ck0, uses = tau_unet.load_tau_model(str(path), dev, force_prior=False)
            if uses:
                raise ValueError(f'USE_PRIOR = False には 3チャンネルの ckpt が要ります ({path} は事前マスク付きの TAU)')
            print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]}) — 3チャンネル (事前マスクなし)')
            return model.train(), ck0['encoder'], FINETUNE_EPOCHS, FINETUNE_LR
        model, ck0, _ = tau_unet.load_tau_model(str(path), dev, force_prior=True)
        print(f'  開始モデル: {path} (epoch {ck0.get("epoch")}, エンコーダ {ck0["encoder"]})'
              f' — 事前マスクの重みを 0 で足した 5チャンネル版 (学習前は元のモデルと同じ結果)')
        return model.train(), ck0['encoder'], FINETUNE_EPOCHS, FINETUNE_LR
    model = tau_unet.build_model(ENCODER, 3, in_ch, 'imagenet')
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
    w = torch.tensor([1.0, 1.0, EDGE_W], device=dev)
    ce = nn.CrossEntropyLoss(weight=w, ignore_index=IGNORE_LABEL)   # 学習しない画素が無ければ今までと同じ
    dice = make_dice()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    first_conv = next(p for n, p in model.encoder.named_parameters() if p.ndim == 4)

    meta = {'encoder': encoder, 'classes': 3, 'mean': MEAN, 'std': STD,
            'in_channels': tau_unet.IMAGE_CHANNELS + (tau_unet.PRIOR_CHANNELS if USE_PRIOR else 0), 'tau': USE_PRIOR,
            'prior_channels': ['interior', 'outline'] if USE_PRIOR else [],
            'prior_edge_px': tau_unet.PRIOR_EDGE_PX if USE_PRIOR else None,
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
    x = tau_unet.make_input(g, pr, MEAN, STD, uses_prior)
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
    model, ck, uses_prior = tau_unet.load_tau_model(str(ckpt_path), dev)
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
        n_pred += len(np.unique(inst)) - (1 if (inst == 0).any() else 0)
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
        return self.m(x[:, :tau_unet.IMAGE_CHANNELS])


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
        print('  「事前あり」は正解から作った事前マスクなので甘めの評価。本当の効果は tau_tracker.py の動画で確認すること')
    if IGNORE_SRC:
        print('  学習しない画素 (IGNORE_SRC) に半分以上ある予測の気泡は数えていない。test の点の候補を dot_labels.py で'
              '全部確認してあれば、tiny の再現率はラベルし直した点も含めた値')
    report = {'columns': {name: r for name, r in cols}, 'iou_match': IOU_MATCH,
              'postprocess': {'min_area': MIN_AREA, 'band': BAND, 'edge_thr': EDGE_THR,
                              'close': CLOSE, 'tiny_max': TINY_MAX}}
    (out / 'test_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'  オーバーレイ → {out / "test_preview"}  (黄 = 事前マスクの輪郭)')


# ======================================================================
def main():
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

    print('\n完了。' + ('tau_tracker.py' if USE_PRIOR else 'tracker3.py / watershed.py / tau_tracker.py')
          + ' の設定をこう変えてください:')
    print(f"  UNET_CKPT = r'{best}'")


if __name__ == '__main__':
    main()

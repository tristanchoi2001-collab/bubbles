#!/usr/bin/env python
"""ラベルの下書き — 今の U-Net の検出結果を COCO にして Roboflow に上げ、人は間違いだけを直す

    python 0_prelabel.py

流れ
  元画像 (背景の残った画像) と背景画像
  -> 2_bin_track.py と同じ前処理 (背景差分 + Noise Cut + 明るさ) で二値化
  -> U-Net (UNET_CKPT) -> 気泡の分け方 (2_bin_track.py の設定のまま。既定 "hybrid")
  -> 気泡ごとの輪郭をポリゴンにする
  -> OUT_FOLDER/ に 画像 + _annotations.coco.json
     (Roboflow の Upload にフォルダごとドラッグすると、ラベル付きの画像として入る。そこで間違いだけ直す)
  -> OUT_FOLDER/preview/ に確認画像 (緑の線 = 下書きのポリゴン)。上げる前に目で確認できる
直すときのこつ: 小さい点の抜けは 1_bin_train.py の STEP = 'dots' でも拾える。大きい気泡は Roboflow の Smart Polygon が速い。
2_bin_track.py を同じフォルダに置くこと (前処理・U-Net・気泡の分け方はそちらをそのまま使う)。
相対パスは「このファイルがあるフォルダ」基準。IMAGE_FOLDER の画像は読むだけで変更しない。
"""

# ======================================================================
#  設定 — ここだけ直して  python 0_prelabel.py  で実行。Windows のパスは r'...' で囲む
# ======================================================================
IMAGE_FOLDER = r'C:\Users\Tristan\Desktop\label_raw'     # ラベルを付ける元画像のフォルダ (背景の残った画像)
BACKGROUND_PATH = r'C:\Users\Tristan\Desktop\bg.jpg'     # その動画の背景画像 (気泡の無いフレーム)
UNET_CKPT = r'best.pt'        # 今の U-Net (3チャンネル。TAU の 5チャンネルでも事前マスクなしで動く)
OUT_FOLDER = r'prelabel'      # 出力フォルダ (画像 + _annotations.coco.json + preview/)。毎回作り直す
PREPROC = (15, 4, 0)          # 前処理 (Noise Cut, Brightness, Median)。学習画像を作ったときと同じ値
EXPORT_IMAGE = 'raw'          # 'raw' = 元画像に下書きを付ける / 'binarized' = 二値化画像 (png) に付ける。座標はどちらも同じ
CLASS_NAME = 'bubble'         # Roboflow のクラス名 (今のラベルと同じ名前にする)
MIN_AREA = 5                  # これより小さい検出は下書きにしない (px)。2_bin_track の IGNORE_PARTICLE_AREA = 4 より大きい
GROW_PX = 1                   # 検出を周りの背景へ広げる px。U-Net の輪郭は白い輪の外側の縁より 0.5〜1.3 px 内側にあるので、
                              # 「輪の外側にポリゴンを描く」今のラベルの描き方に近づける。0 で広げない
SIMPLIFY_PX = 0.7             # ポリゴンの点を減らす許容 (px)。点が多すぎると Roboflow で直しにくい。0 で減らさない
                              # (小さい気泡 = 輪郭の点が SIMPLIFY_MIN_POINTS 以下は減らさない)
SIMPLIFY_MIN_POINTS = 24
SAVE_PREVIEW = True           # OUT_FOLDER/preview/ に確認画像を保存
# ======================================================================

import importlib.util
import json
import shutil
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
ANN_NAME = '_annotations.coco.json'


def resolve(p):
    p = Path(p)
    return p if p.is_absolute() else HERE / p


def load_track():
    """2_bin_track.py (同じフォルダ) を読み込む"""
    path = HERE / '2_bin_track.py'
    if not path.exists():
        raise SystemExit(f'2_bin_track.py が見つかりません: {path}  (このファイルと同じフォルダに置いてください)')
    spec = importlib.util.spec_from_file_location('bin_track', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def grow_instances(inst, r):
    """気泡ごとに r px 広げる。背景の画素にだけ広げ、ほかの気泡には入らない (2つの気泡が取り合う画素は番号の大きい方)"""
    if r <= 0 or not inst.any():
        return inst
    fp = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)).astype(bool)
    dil = ndimage.grey_dilation(inst, footprint=fp)
    out = inst.copy()
    bg = inst == 0
    out[bg] = dil[bg]
    return out


def mask_polygons(m, x0, y0, simplify=SIMPLIFY_PX, min_points=SIMPLIFY_MIN_POINTS):
    """気泡 1つのマスク (切り出し) -> COCO の segmentation (外側の輪郭。島が複数なら複数のポリゴン)。
    座標は画素の中心を通る (1_bin_train.py の変換 fillPoly + polylines で元のマスクに戻る)"""
    cs, _ = cv2.findContours(np.pad(m, 1).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cs:
        if simplify > 0 and len(c) > min_points:
            s = cv2.approxPolyDP(c, simplify, True)
            if len(s) >= 3:
                c = s
        pts = c.reshape(-1, 2) - 1 + np.array([x0, y0])
        if len(pts) < 3:                                     # 1〜2 画素の島: 3点にする
            pts = np.vstack([pts, pts[-1:], pts[:1]])[:3]
        polys.append(pts.astype(float).ravel().tolist())
    return polys


def instances_to_annotations(inst, image_id, next_id, min_area=MIN_AREA, simplify=SIMPLIFY_PX,
                             min_points=SIMPLIFY_MIN_POINTS, category_id=1):
    """気泡ラベルマップ -> COCO の annotations (面積 min_area 未満は除く)"""
    anns = []
    for k, sl in enumerate(ndimage.find_objects(inst), start=1):
        if sl is None:
            continue
        m = inst[sl] == k
        a = int(m.sum())
        if a < min_area:
            continue
        polys = mask_polygons(m, sl[1].start, sl[0].start, simplify, min_points)
        xs = [v for p in polys for v in p[0::2]]
        ys = [v for p in polys for v in p[1::2]]
        anns.append({'id': next_id, 'image_id': image_id, 'category_id': category_id, 'segmentation': polys,
                     'area': float(a), 'bbox': [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)],
                     'iscrowd': 0, 'source': 'prelabel'})
        next_id += 1
    return anns


def preview(img_bgr, anns):
    v = img_bgr.copy()
    for a in anns:
        for p in a['segmentation']:
            cv2.polylines(v, [np.round(np.array(p).reshape(-1, 2)).astype(np.int32)], True, (0, 200, 0), 1)
    return v


def main():
    T = load_track()
    img_dir, bg_path, out = resolve(IMAGE_FOLDER), resolve(BACKGROUND_PATH), resolve(OUT_FOLDER)
    if EXPORT_IMAGE not in ('raw', 'binarized'):
        raise ValueError(f"EXPORT_IMAGE は 'raw' か 'binarized': {EXPORT_IMAGE!r}")
    files = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXT) if img_dir.is_dir() else []
    if not files:
        raise FileNotFoundError(f'IMAGE_FOLDER に画像がありません: {img_dir}')
    ri, ro = img_dir.resolve(), out.resolve()
    if ri == ro or ri in ro.parents or ro in ri.parents:
        raise ValueError('OUT_FOLDER は IMAGE_FOLDER と別のフォルダにしてください (OUT_FOLDER は毎回作り直す)')
    bg = cv2.imread(str(bg_path))
    if bg is None:
        raise FileNotFoundError(f'背景画像が読めません: {bg_path}')
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if SAVE_PREVIEW:
        (out / 'preview').mkdir()

    print(f'U-Net を読み込み中: {resolve(UNET_CKPT)}')
    det = T.TauDetector(str(resolve(UNET_CKPT)), T.TRAIN_IMAGE_HW)   # 3ch / 5ch どちらでも (事前マスクなし)
    print(f'  画像 {len(files)}枚, 前処理 {PREPROC}, 気泡の分け方 "{T.UNET_INSTANCE_MODE}", 書き出す画像 {EXPORT_IMAGE}')
    images, anns = [], []
    for i, p in enumerate(files):
        raw, proc, *_ = T.preprocess_image(str(p), bg, filename=p.name, show_ui=False, current_thresh_val=PREPROC[0],
                                           current_bright_val=PREPROC[1], current_median_val=PREPROC[2])
        if raw is None:
            print(f'    読み込み失敗 (飛ばします): {p}')
            continue
        gray = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)
        inst = grow_instances(T.unet_instances(det.prob(gray)), GROW_PX)
        H, W = gray.shape
        if EXPORT_IMAGE == 'raw':
            fn = p.name
            shutil.copy2(p, out / fn)
            show = raw
        else:
            fn = p.stem + '.png'
            cv2.imwrite(str(out / fn), gray)
            show = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        images.append({'id': len(images), 'file_name': fn, 'height': H, 'width': W})
        a = instances_to_annotations(inst, images[-1]['id'], len(anns) + 1)
        anns += a
        if SAVE_PREVIEW:
            cv2.imwrite(str(out / 'preview' / (p.stem + '.jpg')), preview(show, a))
        print(f'  [{i + 1}/{len(files)}] {p.name}: 気泡 {len(a)}個')
    coco = {'info': {'description': f'prelabel ({resolve(UNET_CKPT).name})',
                     'date_created': datetime.now().strftime('%Y-%m-%d %H:%M')},
            'images': images, 'annotations': anns,
            'categories': [{'id': 1, 'name': CLASS_NAME, 'supercategory': 'none'}]}
    (out / ANN_NAME).write_text(json.dumps(coco, ensure_ascii=False), encoding='utf-8')
    print(f'\n完了: {out}  (画像 {len(images)}枚, 下書きの気泡 {len(anns)}個)')
    print('  1) preview/ で下書きを確認')
    print(f'  2) Roboflow の Upload に {out.name} フォルダごとドラッグ (画像と {ANN_NAME} が一緒に入る)')
    print('  3) Roboflow で間違いだけ直す (抜けた気泡を足す / 余計なものを消す / 形を直す)')


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""小さい点のラベル補充 — ラベルされていない小さい点を自動で探し、人が確認して、学習データに足す

    python dot_labels.py

なぜ必要か
  U-Net は画像にはっきり見える小さい点 (731〜790 で 面積 5〜20 px の点が 1フレーム約17個) を「確実に背景」と出す。
  学習ラベルで小さい点の多くが描かれていない (= 背景だと教えた) ためと考えられる。ラベルが背景だと教える限り、
  どのモデル (CNN・トランスフォーマー・TAU) に変えても同じように見落とす。そこでラベルを補う。

流れ
  [1] 候補: Roboflow の書き出し (SRC) の画像から「光っている小さい塊で、ラベル済みの気泡から離れているもの」を探す。
      U-Net は使わない (U-Net が見落とす点を探すため。U-Net の出力を見せると判断がそれに引きずられる)
  [2] 確認: 候補を拡大したタイルで 1ページ GRID 個ずつ表示する。split ごとに明るい候補から順に並ぶ
      (途中でやめると、残るのは暗い候補 = 無視になる)。タイルの文字は 面積 px / 一番明るい画素の値
        左クリック   = 気泡でない (n)        右クリック = 分からない (u)       同じクリックをもう一度 = 取り消し
        Enter/Space  = このページの残りを「気泡」(y) にして次のページ
        b = 前のページ      q / Esc = 保存して終了 (ウィンドウを閉じても保存される)
      タイルの色: 黄の輪郭 = この候補 (輪郭は点の外側に描くので点そのものは隠れない), 緑の輪郭 = ラベル済みの気泡,
                 水色の輪郭 = ほかの候補。枠: 灰 = 未確認, 緑 = 気泡, 赤 (×) = 気泡でない, 橙 (?) = 分からない
      判定は OUT/decisions.json に保存される。途中でやめても、次に実行すると続きから
  [3] 書き出し (終了すると自動):
      OUT/coco/<split>/              元のラベル + 「気泡」(y) にした点を足した COCO (画像もコピー)。
                                     → 1_tau_unet_train.py の SRC にする
      OUT/ignore/<split>/<名前>.png  「分からない」(u) と まだ確認していない候補の範囲 (白 = 255)。
                                     → 1_tau_unet_train.py の IGNORE_SRC にする (学習・評価でその画素を使わない)
      「気泡でない」(n) は何もしない (今までどおり背景として学習する)
  確認は test → valid → train の順。test を最後まで確認すると、評価用の test がもれなくラベルされた状態になる
  (点の再現率を正しく測れるのはこの状態のときだけ)。
  確認しなかった候補は無視 (ignore) になるので、確認せずに書き出すだけ (REVIEW = False) でも
  「見えている点を背景だと教える」ことは止められる (点を気泡だと教えることにはならない)。

相対パスは「このファイルがあるフォルダ」基準。SRC は読むだけで変更しない。
"""

# ======================================================================
#  設定 — ここだけ直して  python dot_labels.py  で実行
#  Windows のパスは r'...' で囲む
# ======================================================================
SRC = r'C:\Users\Tristan\Desktop\ams\unet\cocosegmentation'   # Roboflow の書き出し (1_tau_unet_train.py の SRC と同じ)
OUT = r'dot_labels'           # 作業フォルダ (decisions.json, coco/, ignore/)
REVIEW = True                 # True: 確認の画面を開く / False: 開かずに書き出すだけ (未確認の候補はすべて ignore)
SPLIT_ORDER = ('test', 'valid', 'train')   # 確認する順 (Roboflow のフォルダ名)

# [1] 候補の条件 (学習画像は二値化済み: 背景差分が Noise Cut 未満は 0、それ以上は ×Brightness)
CAND_LOW = 30                 # この明るさ以上を「光っている」画素とする (0 以外。JPEG のにじみ (〜20) は除く)
CAND_PEAK = 60                # 塊の一番明るい画素がこれ以上 (Noise Cut 15 × Brightness 4 = 60)
CAND_MIN_AREA = 5             # 光っている画素の数の下限 (tracker3 の IGNORE_PARTICLE_AREA = 4 より大きい)
CAND_MAX_AREA = 600           # 塗りつぶした面積の上限 (これより大きい塊は小さい点ではないので候補にしない)
LABEL_GAP = 2                 # ラベル済みの気泡からこの px 以内に掛かる塊は候補にしない (その気泡の輪郭の一部のことが多い)

# [3] 書き出し
IGNORE_PAD = 2                # 無視する範囲を候補の周りにこの px 広げる (点のぼやけた縁も背景として教えない)
GROW_PX = 0                   # 「気泡」にした点のマスクを広げる px。0 = 光っている画素の外側の縁まで
                              # (= 白い輪の外側にポリゴンを描く今のラベルの描き方)

# [2] 確認画面
GRID = (5, 4)                 # 1ページのタイルの数 (横, 縦)
TILE = 180                    # タイル1枚の大きさ (画面の px)
MIN_CROP = 33                 # タイルに映す範囲の最小 (元画像の px)。点の周りの様子も見えるように
# ======================================================================

import json
import os
import shutil
import sys
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ANN_NAME = '_annotations.coco.json'
IGNORE_VALUE = 255
DECISIONS = ('y', 'n', 'u')   # 気泡 / 気泡でない / 分からない


def resolve(p):
    p = Path(p)
    return p if p.is_absolute() else HERE / p


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


def fill_dot(cm):
    """光っている画素の塊 (bool) -> 気泡の範囲。輪の穴と、切れた輪 (C 字、切れ目 約4px まで) を埋める。
    埋めるのは塊の凸包の中だけ (小さい気泡はほぼ円なので)"""
    p = np.pad(cm, 3).astype(np.uint8)
    c = cv2.morphologyEx(p, cv2.MORPH_CLOSE, _disk(2))
    hull = np.zeros_like(p)
    cv2.fillConvexPoly(hull, cv2.convexHull(cv2.findNonZero(p)), 1)
    f = (ndimage.binary_fill_holes(c > 0) & (hull > 0)) | (p > 0)
    return f[3:-3, 3:-3]


class Cand:
    """候補1つ。mask は (y0, x0) から始まる切り出し (bool)"""
    __slots__ = ('split', 'file', 'x0', 'y0', 'mask', 'lit', 'peak', 'ring')

    def __init__(self, split, file, x0, y0, mask, lit, peak, ring):
        self.split, self.file, self.x0, self.y0 = split, file, int(x0), int(y0)
        self.mask, self.lit, self.peak, self.ring = mask, int(lit), int(peak), bool(ring)

    @property
    def area(self):
        return int(self.mask.sum())

    @property
    def id(self):
        """判定の保存に使う名前。条件を変えて探し直しても、同じ塊なら同じ名前になる"""
        h, w = self.mask.shape
        return f'{self.split}/{self.file}@{self.x0},{self.y0},{w}x{h},{self.area}'


def find_candidates(gray, labelled, split='', file='', low=CAND_LOW, peak=CAND_PEAK, min_area=CAND_MIN_AREA,
                    max_area=CAND_MAX_AREA, label_gap=LABEL_GAP):
    """学習画像 1枚の候補。gray: uint8, labelled: ラベル済み気泡の画素 (bool)"""
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
        pk = int(gray[y:y + h, x:x + w][cm].max())
        if pk < peak:
            continue
        f = fill_dot(cm)
        if f.sum() > max_area:
            continue
        out.append(Cand(split, file, x, y, f, a, pk, f.sum() > cm.sum()))
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
        cv2.putText(out, f'{c.area}px / {c.peak}', (6, t - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
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
        line2 = 'L-click: NOT bubble   R-click: unsure   Enter/Space: others = bubble, next page   b: back   q: save+quit'
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


def run_review(rv, dec_path):
    """確認の画面 (OpenCV のウィンドウ)。終わったら判定を保存する"""
    win = 'dot review'
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    state = {'dirty': True}

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
                last = rv.confirm()
                save_decisions(dec_path, rv.dec)
                if last:
                    print('  最後のページまで確認しました')
                    break
                note, state['dirty'] = '', True
            elif key == ord('b'):
                rv.back()
                save_decisions(dec_path, rv.dec)
                state['dirty'] = True
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
    """OUT/coco (元のラベル + y の点) と OUT/ignore (u と未確認の候補) を作り直す。戻り値: 集計"""
    src, out = Path(src), Path(out)
    for sub in ('coco', 'ignore'):
        if (out / sub).exists():
            shutil.rmtree(out / sub)
    by_img = {}
    for c in cands:
        by_img.setdefault((c.split, c.file), []).append(c)
    summary = {}
    for split, d in cocos.items():
        cdir, idir = out / 'coco' / split, out / 'ignore' / split
        cdir.mkdir(parents=True, exist_ok=True)
        anns = list(d['annotations'])
        next_id = max((int(a.get('id', 0)) for a in anns), default=0) + 1
        cat_count = Counter(a.get('category_id') for a in anns)
        cat = cat_count.most_common(1)[0][0] if cat_count else (d.get('categories') or [{'id': 1}])[-1]['id']
        s = Counter()
        for im in d['images']:
            fn = im['file_name']
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
                idir.mkdir(parents=True, exist_ok=True)
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
def main():
    src, out = resolve(SRC), resolve(OUT)
    if not src.exists():
        raise FileNotFoundError(f'SRC フォルダがありません: {src}')
    if out.resolve() == src.resolve() or src.resolve() in out.resolve().parents:
        raise ValueError('OUT は SRC と別のフォルダにしてください (SRC は変更しません)')
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

    if REVIEW and cands:
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
    print('\n1_tau_unet_train.py の設定をこう変えてください:')
    print(f"  SRC = r'{out / 'coco'}'")
    print(f"  IGNORE_SRC = r'{out / 'ignore'}'")


if __name__ == '__main__':
    main()

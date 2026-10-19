"""
Tracking-aware U-Net (TAU) の共通部品
=====================================================================
U-Net の入力に「このフレームに気泡がどこにあるはずか」(トラッカーが前後のフレームから予測した気泡マスク) を足す。
  ch 0-2 : 前処理画像 (グレーを3回。best.pt と同じ正規化)
  ch 3   : 事前マスク・内部 (予測した気泡の塗りつぶし 0/1)
  ch 4   : 事前マスク・輪郭 (予測した気泡ごとの内側の輪郭 PRIOR_EDGE_PX 幅 0/1。くっついた気泡の境目が分かる)
出力は best.pt と同じ 3クラス (背景/内部/境界) なので、気泡の分け方 (wall / hybrid) とトラッカーはそのまま使う。

best.pt (3チャンネル) から学習を始めるときは、最初の畳み込みの事前マスク用の重みを 0 で足す (expand_state_dict)。
学習前のモデルは事前マスクに関係なく best.pt と同じ確率を出す (tests/test_tau.py の a で確認)。
事前マスクが全部 0 のときは、学習後のモデルも事前マスクなしの検出器として働く (学習で PriorAug.p_empty の割合だけ練習する)。

学習用の事前マスクは、正解ラベルの気泡を崩して作る (synth_prior。MaskTrack, Perazzi et al., CVPR 2017 と同じ考え方)。
連続フレームのラベルは要らない。崩し方 = 前のパスの検出・トラッカーの予測で起きる誤り:
  見落とし (消す) / 位置ずれ / 変形 (拡大縮小・膨張収縮) / 一部欠け / 隣と融合 / 割れ / 何も無い所の気泡

1_tau_unet_train.py (学習) と tau_tracker.py (推論) の両方が使う。2つと同じフォルダに置くこと。
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np
from scipy import ndimage

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


def synth_prior(ins: np.ndarray, rng, aug: Optional[PriorAug] = None, edge_px: int = PRIOR_EDGE_PX) -> np.ndarray:
    """正解の気泡ラベルマップ (0 = 背景, 1..N の連番) を崩して学習用の事前マスク (2, H, W) を作る。
    rng = np.random.default_rng(...) (同じ rng の状態なら同じ結果)"""
    aug = aug or PriorAug()
    H, W = ins.shape
    if rng.random() < aug.p_empty:
        return np.zeros((PRIOR_CHANNELS, H, W), np.float32)
    ins = ins.astype(np.int32)
    ids = np.unique(ins)
    ids = ids[ids > 0]
    if ids.size and (ids[-1] != ids.size):     # 連番に詰める (_touching_pairs が番号 = 位置 + 1 を使うため)
        lut = np.zeros(int(ids[-1]) + 1, np.int32)
        lut[ids] = np.arange(1, ids.size + 1)
        ins = lut[ins]
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
        if rng.random() < aug.p_drop:
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
        self.edge_px = int(ck.get("prior_edge_px", PRIOR_EDGE_PX))
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

"""
気泡の大きさ別 PIV 速度場 (docs/PIV_TASK.md 5-1)
=====================================================================
reference/piv_prior.py (相互相関法) をトラッカー用に移植したもの。
個々の気泡は形が似ていて区別できなくても、窓の中の「気泡の並び方」は1フレームの間ほぼ保たれる。
フレーム t と t+1 の同じ位置の窓を相互相関し、ピーク位置 = その窓の移動量 とする。
追跡結果を使わないので、新しく現れた気泡にも その場所・その大きさの気泡の速度を与えられる (予測専用)。

入力は 2値化画像ではなく、U-Net の気泡マスク (Detection) から作った「大きさ区分ごとの画像」。
  - 区分は QC と同じ面積: tiny < 50 <= small < 500 <= large (px)
  - 窓の相関は画素の多い気泡 (= 大きい気泡) に引っ張られるので、区分ごとに別々に相関を取る
  - 既定はマスクの輪郭 (raster="outline")。塗りつぶし (filled) だと大きい気泡の相関ピークが幅広くなり、
    1位/2位ピーク比の判定 (±2px の外の2位) で全ての窓が無効になる (合成・実画像の両方で確認)

手順 (piv_prior.py と同じ)
  1パス目: 大きい窓 (win1, step1) で粗い移動量
  2パス目: 小さい窓 (win2, step2) を、1パス目の移動量だけ t+1 側でずらして比較 (window offset)
  ピーク位置はガウス3点近似でサブピクセル化。1位/2位ピーク比 < min_peak_ratio の窓は無効
  周り 3×3 の中央値から外れたベクトルは無効 (縦横どちらかが外れたら両方)。無効は周りの中央値で埋める

piv_prior.py からの変更 (mode="improved" で有効。mode="faithful" なら piv_prior.py と同じ計算):
  1. lobe_peak        : 2位ピークを「1位ピークの主ローブ (0.5×1位 を超える連結領域)」の外で探す
                         (±2px の外だと、幅広いピークの肩を2位と数えて正しい窓まで無効になる)
     lobe_max_frac    : 主ローブが縦または横に 窓 × この値 より長い窓は無効 (開口問題: スラグの胴体のように
                         平行な輪郭しか見えない窓は、相関が稜線になり移動量が決まらない)
  2. max_disp_frac    : 2パス目で、ずらした後に残る移動量が窓の この割合 を超えたら無効
     pass1_disp_frac  : 1パス目 (ずらしなし) は ±窓/2 の端に出る循環相関の偽ピークだけを除く (窓 × この値)
     require_guide    : (既定は無効) 2パス目は、1パス目で実測できた場所だけを有効にする
  3. validate_isolated: 3×3 に有効な隣が3つ未満のベクトルも、5×5 に有効な隣が2つ以上あれば中央値で検査する
  4. clamp_offset     : 2パス目でずらした窓が画像からはみ出すとき、ずらしを 0 に戻さず画像内に寄せる
     edge_windows     : 右端・下端に揃えた窓を追加し、端の帯 (下端 = 気泡が入ってくる場所) も計測する
  5. sample() は (dy, dx, 有効か) を返す。周りに実測の窓がない (埋めた値しかない) 場所・区分全体で実測が0の
     ときは「無効」とし、トラッカー側で代わりの推定 (大きさの近い周りの気泡の速度 -> 0) に回す

速度場は予測 (新規トラックの初速度) にだけ使う。気泡の速度の計測値は個々の追跡からだけ出す。
"""
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np
from scipy import ndimage

try:
    import cv2
except ImportError:   # 主ローブの計算 (scipy で代用) と描画 (draw) で使う
    cv2 = None
try:                  # scipy.fft はマルチスレッドで速い。なければ numpy.fft
    import scipy.fft as _fft
    _FFT_KW = {"workers": -1}
except ImportError:
    _fft = np.fft
    _FFT_KW = {}

CLASS_NAMES = ("tiny", "small", "large")


def size_class(area: float, bounds: Tuple[float, float] = (50.0, 500.0)) -> str:
    """面積 (px) -> 大きさ区分 (QC と同じ区分)"""
    if area < bounds[0]:
        return "tiny"
    return "small" if area < bounds[1] else "large"


@dataclass
class PIVSettings:
    size_bounds: Tuple[float, float] = (50.0, 500.0)
    # 区分ごとの窓: (1パス目の窓, 間隔, 2パス目の窓, 間隔) [px]。移動量が窓の 1/4 以下になる大きさにする
    windows: Dict[str, Tuple[int, int, int, int]] = field(default_factory=lambda: {
        "tiny": (256, 128, 128, 64), "small": (256, 128, 128, 64), "large": (256, 128, 128, 64)})
    raster: str = "outline"         # "outline" (マスクの輪郭) / "filled" (塗りつぶし)
    outline_px: int = 2             # 輪郭の太さ (px)。画面端で切れた辺は輪郭にしない
    min_area: float = 0.0           # これより小さい検出は使わない (トラッカーの MIN_TRACK_AREA)
    min_peak_ratio: float = 1.2
    median_k: float = 3.0           # 正規化中央値検査: |v - 中央値| > k × (周りの中央値偏差 + eps) なら無効
    median_eps: float = 1.0
    lobe_peak: bool = True          # 変更1
    lobe_max_frac: float = 0.25     # 変更1 (0 で無効)
    max_disp_frac: float = 0.25     # 変更2 (0 で無効)
    pass1_disp_frac: float = 0.45   # 変更2 (0 で無効)
    require_guide: bool = False     # 変更2 (実画像では 1パス目の大きい窓が流れの場所による違いで無効になりやすく、
                                    # 正しい 2パス目まで捨てて誤差が増えたので既定は無効。pass1_disp_frac で折り返しは防げる)
    validate_isolated: bool = True  # 変更3
    clamp_offset: bool = True       # 変更4
    edge_windows: bool = True       # 変更4

    @staticmethod
    def faithful(**kw) -> "PIVSettings":
        """piv_prior.py と同じ計算 (変更1〜4 なし。入力の画像の作り方は raster で別に指定)"""
        base = dict(lobe_peak=False, lobe_max_frac=0.0, max_disp_frac=0.0, pass1_disp_frac=0.0, require_guide=False,
                    validate_isolated=False, clamp_offset=False, edge_windows=False)
        base.update(kw)
        return PIVSettings(**base)


# ==============================================================
# 1. 大きさ区分ごとの画像
# ==============================================================
def rasterize(dets, image_hw: Tuple[int, int], s: PIVSettings) -> Dict[str, np.ndarray]:
    """Detection のリスト -> {区分: uint8 画像 (気泡=255)}"""
    H, W = image_hw
    out = {c: np.zeros((H, W), np.uint8) for c in CLASS_NAMES}
    for d in dets:
        if d.area < s.min_area:
            continue
        m, x0, y0 = d.shape
        if s.raster == "outline":
            m = _outline(m, getattr(d, "touch", (False, False, False, False)), s.outline_px)
        img = out[size_class(d.area, s.size_bounds)]
        h, w = m.shape
        ys, xs = max(0, -y0), max(0, -x0)
        ye, xe = min(h, H - y0), min(w, W - x0)
        if ye > ys and xe > xs:
            img[y0 + ys:y0 + ye, x0 + xs:x0 + xe][m[ys:ye, xs:xe]] = 255
    return out


def _outline(m: np.ndarray, touch, width: int) -> np.ndarray:
    """マスクの内側 width px の輪郭。画面端で切れた辺 (touch = 上/下/左/右) は輪郭にしない"""
    if width <= 0:
        return m
    p = width
    pad = np.zeros((m.shape[0] + 2 * p, m.shape[1] + 2 * p), bool)
    pad[p:-p, p:-p] = m
    if touch[0]:
        pad[:p, p:-p] = m[:1]
    if touch[1]:
        pad[-p:, p:-p] = m[-1:]
    if touch[2]:
        pad[:, :p] = pad[:, p:p + 1]
    if touch[3]:
        pad[:, -p:] = pad[:, -p - 1:-p]
    core = ndimage.binary_erosion(pad, iterations=width)[p:-p, p:-p]
    return m & ~core


# ==============================================================
# 2. 相互相関
# ==============================================================
def _gauss3(m, c, p):
    """ガウス3点近似 (値が正のときのみ)"""
    if min(m, c, p) <= 0:
        return 0.0
    lm, lc, lp = math.log(m), math.log(c), math.log(p)
    den = 2 * lm - 4 * lc + 2 * lp
    return (lm - lp) / den if den != 0 else 0.0


INVALID_EMPTY, INVALID_RATIO, INVALID_DISP, INVALID_MEDIAN, INVALID_NOGUIDE, INVALID_APERTURE = 1, 2, 3, 4, 5, 6


def _lobe_mask(R: np.ndarray, py: int, px: int, p1: float):
    """1位ピークの主ローブ (0.5×1位 を超える 4連結の領域)。戻り値: (2px 膨らませたマスク, 縦の長さ, 横の長さ)"""
    hi = R > 0.5 * p1
    if cv2 is not None:
        _, lab = cv2.connectedComponents(hi.astype(np.uint8), connectivity=4)
        lobe = (lab == lab[py, px]).astype(np.uint8)
        k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        grown = cv2.dilate(lobe, k, iterations=2).astype(bool)
        lobe = lobe.astype(bool)
    else:
        lab, _ = ndimage.label(hi)
        lobe = lab == lab[py, px]
        grown = ndimage.binary_dilation(lobe, iterations=2)
    ys = np.flatnonzero(lobe.any(axis=1))
    xs = np.flatnonzero(lobe.any(axis=0))
    return grown, ys[-1] - ys[0] + 1, xs[-1] - xs[0] + 1


def _peak(R: np.ndarray, s: PIVSettings, disp_frac: float):
    """相互相関 R (fftshift 済み) のピーク。戻り値: (dy, dx, ピーク比, 無効の理由 or 0)"""
    h, w = R.shape
    py, px = np.unravel_index(np.argmax(R), R.shape)
    p1 = R[py, px]
    R2 = R.copy()
    elongated = False
    if s.lobe_peak and p1 > 0:   # 主ローブの外の最大値
        mask, ly, lx = _lobe_mask(R, py, px, p1)
        R2[mask] = -np.inf
        elongated = s.lobe_max_frac > 0 and (ly > s.lobe_max_frac * h or lx > s.lobe_max_frac * w)
    else:                        # piv_prior.py: 1位の周り ±2px の外の最大値
        R2[max(0, py - 2):py + 3, max(0, px - 2):px + 3] = -np.inf
    p2 = R2.max()
    ratio = p1 / p2 if p2 > 0 else np.inf
    sy = _gauss3(R[py - 1, px], p1, R[py + 1, px]) if 0 < py < h - 1 else 0.0
    sx = _gauss3(R[py, px - 1], p1, R[py, px + 1]) if 0 < px < w - 1 else 0.0
    dy, dx = py - h // 2 + sy, px - w // 2 + sx
    if ratio < s.min_peak_ratio:
        return dy, dx, ratio, INVALID_RATIO
    if elongated:
        return dy, dx, ratio, INVALID_APERTURE
    if disp_frac > 0 and (abs(dy) > disp_frac * h or abs(dx) > disp_frac * w):
        return dy, dx, ratio, INVALID_DISP
    return dy, dx, ratio, 0


def _correlate(WA: np.ndarray, WB: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """窓の束 (N, h, w) どうしの相互相関をまとめて FFT で計算。戻り値: (R (N,h,w) fftshift 済み, 空の窓か (N,))"""
    empty = ((WA.max(axis=(1, 2)) == WA.min(axis=(1, 2))) | (WB.max(axis=(1, 2)) == WB.min(axis=(1, 2))))
    A = WA.astype(np.float64)
    B = WB.astype(np.float64)
    A -= A.mean(axis=(1, 2), keepdims=True)
    B -= B.mean(axis=(1, 2), keepdims=True)
    h, w = A.shape[1:]
    R = _fft.irfft2(np.conj(_fft.rfft2(A, **_FFT_KW)) * _fft.rfft2(B, **_FFT_KW), s=(h, w), **_FFT_KW)
    return np.fft.fftshift(R, axes=(1, 2)), empty


def _starts(n: int, win: int, step: int, edge: bool):
    if n <= win:
        return [0]
    st = list(range(0, n - win + 1, step))
    if edge and st[-1] != n - win:
        st.append(n - win)
    return st


def _pass(a, b, win, step, s: PIVSettings, guess=None):
    """1パス分。guess (_Interp) があれば t+1 側の窓をその分ずらす"""
    H, W = a.shape
    wy, wx = min(win, H), min(win, W)
    # はみ出しの判定と窓の中心: faithful では piv_prior.py と同じく窓の公称サイズで判定する
    by, bx = (wy, wx) if s.clamp_offset else (win, win)
    ys, xs = _starts(H, wy, step, s.edge_windows), _starts(W, wx, step, s.edge_windows)
    V = np.full((len(ys), len(xs)), np.nan)
    U = np.full_like(V, np.nan)
    why = np.zeros(V.shape, np.int8)
    cells, WA, WB = [], [], []
    for iy, y0 in enumerate(ys):
        for ix, x0 in enumerate(xs):
            oy = ox = 0
            if guess is not None:
                gdy, gdx = guess(y0 + wy / 2, x0 + wx / 2)
                if np.isfinite(gdy):
                    oy, ox = int(round(gdy)), int(round(gdx))
            yb, xb = y0 + oy, x0 + ox
            if yb < 0 or xb < 0 or yb + by > H or xb + bx > W:
                if s.clamp_offset:
                    yb, xb = min(max(yb, 0), H - wy), min(max(xb, 0), W - wx)
                    oy, ox = yb - y0, xb - x0
                else:
                    oy = ox = 0
                    yb, xb = y0, x0
            guided = guess is None or not s.require_guide or guess.supported(y0 + wy / 2, x0 + wx / 2)
            cells.append((iy, ix, oy, ox, guided))
            WA.append(a[y0:y0 + wy, x0:x0 + wx])
            WB.append(b[yb:yb + wy, xb:xb + wx])
    R, empty = _correlate(np.stack(WA), np.stack(WB))
    disp_frac = s.max_disp_frac if guess is not None else s.pass1_disp_frac
    for k, (iy, ix, oy, ox, guided) in enumerate(cells):
        if empty[k]:
            why[iy, ix] = INVALID_EMPTY
            continue
        if not guided:
            why[iy, ix] = INVALID_NOGUIDE
            continue
        dy, dx, _, bad = _peak(R[k], s, disp_frac)
        if bad:
            why[iy, ix] = bad
        else:
            V[iy, ix], U[iy, ix] = dy + oy, dx + ox
    cy = np.array(ys, float) + (wy if s.clamp_offset else win) / 2
    cx = np.array(xs, float) + (wx if s.clamp_offset else win) / 2
    return cy, cx, V, U, why


def _validate(V, U, why, s: PIVSettings):
    """周りの中央値から大きく外れたベクトルを無効にする (縦横どちらかが外れたら両方無効)"""
    V2, U2 = V.copy(), U.copy()
    H, W = V.shape
    for iy in range(H):
        for ix in range(W):
            if not np.isfinite(V[iy, ix]):
                continue
            nb = [(j, i) for j in range(max(0, iy - 1), min(H, iy + 2)) for i in range(max(0, ix - 1), min(W, ix + 2))
                  if (j, i) != (iy, ix) and np.isfinite(V[j, i])]
            if len(nb) < 3:
                if not s.validate_isolated:
                    continue
                nb = [(j, i) for j in range(max(0, iy - 2), min(H, iy + 3)) for i in range(max(0, ix - 2), min(W, ix + 3))
                      if (j, i) != (iy, ix) and np.isfinite(V[j, i])]
                if len(nb) < 2:
                    continue
            for F in (V, U):
                vals = np.array([F[j, i] for j, i in nb])
                med = np.median(vals)
                if abs(F[iy, ix] - med) > s.median_k * (np.median(np.abs(vals - med)) + s.median_eps):
                    V2[iy, ix] = U2[iy, ix] = np.nan
                    why[iy, ix] = INVALID_MEDIAN
    return V2, U2


def _fill(F):
    """無効 (NaN) を周り3×3の有効値の中央値、それもなければ全体の中央値で埋める"""
    G = F.copy()
    med = np.nanmedian(F) if np.isfinite(F).any() else 0.0
    for iy, ix in zip(*np.where(~np.isfinite(F))):
        nb = F[max(0, iy - 1):iy + 2, max(0, ix - 1):ix + 2]
        G[iy, ix] = np.nanmedian(nb) if np.isfinite(nb).any() else med
    return G


class _Interp:
    """格子 (窓の中心) 上の値を双線形補間。格子の外は端の値"""

    def __init__(self, cy, cx, V, U, valid=None):
        self.cy, self.cx, self.V, self.U = cy, cx, V, U
        self.valid = valid

    def _corners(self, y, x):
        fy = float(np.interp(y, self.cy, np.arange(len(self.cy))))
        fx = float(np.interp(x, self.cx, np.arange(len(self.cx))))
        y0, x0 = int(math.floor(fy)), int(math.floor(fx))
        y1, x1 = min(y0 + 1, len(self.cy) - 1), min(x0 + 1, len(self.cx) - 1)
        ty, tx = fy - y0, fx - x0
        return [(y0, x0, (1 - ty) * (1 - tx)), (y0, x1, (1 - ty) * tx), (y1, x0, ty * (1 - tx)), (y1, x1, ty * tx)]

    def __call__(self, y, x):
        if self.V.size == 0:
            return np.nan, np.nan
        cs = self._corners(y, x)
        return (float(sum(w * self.V[j, i] for j, i, w in cs)), float(sum(w * self.U[j, i] for j, i, w in cs)))

    def supported(self, y, x) -> bool:
        """補間に実測の窓 (重み > 0) が含まれるか"""
        if self.valid is None or self.V.size == 0:
            return False
        return any(w > 1e-9 and self.valid[j, i] for j, i, w in self._corners(y, x))


class DisplacementField:
    """フレーム t -> t+1 の移動量場 (1つの大きさ区分)。sample(x, y) -> (dy, dx, 有効か)"""

    def __init__(self, a: np.ndarray, b: np.ndarray, win1: int, step1: int, win2: int, step2: int,
                 s: Optional[PIVSettings] = None):
        s = s or PIVSettings()
        cy1, cx1, V1, U1, why1 = _pass(a, b, win1, step1, s)
        V1, U1 = _validate(V1, U1, why1, s)
        f1 = _Interp(cy1, cx1, _fill(V1), _fill(U1), np.isfinite(V1))
        self.cy, self.cx, V2, U2, self.why = _pass(a, b, win2, step2, s, guess=f1)
        V2, U2 = _validate(V2, U2, self.why, s)
        self.valid = np.isfinite(V2)
        self.V, self.U = _fill(V2), _fill(U2)
        self._f = _Interp(self.cy, self.cx, self.V, self.U, self.valid)

    def sample(self, x: float, y: float):
        """(dy, dx, 有効か)。周りに実測の窓がない (埋めた値しかない) 場所は無効"""
        dy, dx = self._f(y, x)
        return dy, dx, bool(self.valid.any()) and self._f.supported(y, x)

    @property
    def valid_fraction(self) -> float:
        return float(self.valid.mean()) if self.valid.size else 0.0


def compute_fields(dets_a, dets_b, image_hw: Tuple[int, int], s: Optional[PIVSettings] = None,
                   rasters=None) -> Dict[str, Optional[DisplacementField]]:
    """フレーム t の検出, t+1 の検出 -> {区分: DisplacementField (どちらかのフレームに その区分の気泡がなければ None)}
    rasters = (t の画像, t+1 の画像) を渡すと作り直さない (フレームごとに1回だけ作るため)"""
    s = s or PIVSettings()
    ra, rb = rasters if rasters is not None else (rasterize(dets_a, image_hw, s), rasterize(dets_b, image_hw, s))
    out = {}
    for c in CLASS_NAMES:
        if not ra[c].any() or not rb[c].any():
            out[c] = None
            continue
        out[c] = DisplacementField(ra[c], rb[c], *s.windows[c], s=s)
    return out


def draw(img_gray: np.ndarray, fld: DisplacementField, scale: float = 1.0) -> np.ndarray:
    """ベクトル図 (黄 = 実測, 赤 = 周りから補間)"""
    out = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    for iy, y in enumerate(fld.cy):
        for ix, x in enumerate(fld.cx):
            dy, dx = fld.V[iy, ix], fld.U[iy, ix]
            col = (0, 255, 255) if fld.valid[iy, ix] else (0, 0, 255)
            cv2.arrowedLine(out, (int(x), int(y)), (int(x + scale * dx), int(y + scale * dy)), col, 2, tipLength=0.25)
    return out

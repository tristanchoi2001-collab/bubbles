"""
画像から直接、局所的な移動量(速度場)を求める (PIV と同じ相互相関法)
=====================================================================
個々の気泡は形が似ていて区別できなくても、窓の中の「気泡の並び方」は1フレームの間ほぼ保たれる。
そこで、フレーム t の小窓と フレーム t+1 の同じ位置の窓を相互相関し、相関のピーク位置 = その窓の移動量 とする。
追跡結果(トラックの履歴)を使わないので、新しく現れた気泡にもその場所の速度を与えられる。

手順
  1パス目: 大きい窓 (WIN1) で粗い移動量
  2パス目: 小さい窓 (WIN2) を、1パス目の移動量だけずらした位置で比較して精密化 (window offset)
  ピーク位置はガウス3点近似でサブピクセル化。ピークの鋭さ(1位/2位のピーク比)が低い窓は無効
  無効な窓は周りの有効な窓の中央値で埋める

使い方 (単体)
  連続する2枚の2値化画像 (トラッカーの _cache_processed) を指定して実行 → 速度ベクトルを描いた画像を保存
"""

# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
IMAGE_A = r"C:\Users\inoue-2024-01\Desktop\U-net\output\_cache_processed\image0000010.jpg"   # フレーム t
IMAGE_B = r"C:\Users\inoue-2024-01\Desktop\U-net\output\_cache_processed\image0000011.jpg"   # フレーム t+1
OUT_IMAGE = r"C:\Users\inoue-2024-01\Desktop\U-net\output\piv_field.png"

WIN1, STEP1 = 256, 128     # 1パス目の窓サイズ・間隔 (px)。移動量が窓の 1/4 以下になる大きさにする
WIN2, STEP2 = 128, 64      # 2パス目
MIN_PEAK_RATIO = 1.2       # 1位/2位ピーク比がこれ未満の窓は無効 (曖昧)

# 気泡の大きさ別に速度場を分けるか。窓の相関は「画素の多い気泡 (= 大きい気泡)」の動きに引っ張られるため、
# 大きさで速度が違う流れでは、小さい気泡だけの画像・大きい気泡だけの画像で別々に相関を取る
SPLIT_BY_SIZE = True
SIZE_SPLIT_PX = (9, 25)    # 輪郭の外接矩形の長辺 (px): ≤9 tiny / ≤25 small / それ以上 large (QCの面積 50/500px に相当)


import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def _corr_peak(wa, wb):
    """wa (t) と wb (t+1) の相互相関。戻り値: (dy, dx, ピーク比)。dy, dx は wb が wa からどれだけずれたか"""
    wa = wa.astype(np.float64) - wa.mean()
    wb = wb.astype(np.float64) - wb.mean()
    if wa.std() < 1e-6 or wb.std() < 1e-6:
        return np.nan, np.nan, 0.0
    R = np.fft.irfft2(np.conj(np.fft.rfft2(wa)) * np.fft.rfft2(wb), s=wa.shape)
    R = np.fft.fftshift(R)
    h, w = R.shape
    py, px = np.unravel_index(np.argmax(R), R.shape)
    p1 = R[py, px]
    # 2位のピーク: 1位の周り ±2px を除いた最大値
    R2 = R.copy()
    R2[max(0, py - 2):py + 3, max(0, px - 2):px + 3] = -np.inf
    p2 = R2.max()
    ratio = p1 / p2 if p2 > 0 else np.inf

    def gauss(m, c, p):     # ガウス3点近似 (値が正のときのみ)
        if min(m, c, p) <= 0:
            return 0.0
        lm, lc, lp = np.log(m), np.log(c), np.log(p)
        den = 2 * lm - 4 * lc + 2 * lp
        return (lm - lp) / den if den != 0 else 0.0

    sy = gauss(R[py - 1, px], p1, R[py + 1, px]) if 0 < py < h - 1 else 0.0
    sx = gauss(R[py, px - 1], p1, R[py, px + 1]) if 0 < px < w - 1 else 0.0
    return py - h // 2 + sy, px - w // 2 + sx, ratio


def _pass(a, b, win, step, guess=None):
    """1パス分。guess(y, x) -> (dy, dx) があれば t+1 側の窓をその分ずらす"""
    H, W = a.shape
    ys = list(range(0, max(1, H - win + 1), step))
    xs = list(range(0, max(1, W - win + 1), step))
    U = np.full((len(ys), len(xs)), np.nan)
    V = np.full_like(U, np.nan)
    Q = np.zeros_like(U)
    for iy, y0 in enumerate(ys):
        for ix, x0 in enumerate(xs):
            oy = ox = 0
            if guess is not None:
                gdy, gdx = guess(y0 + win / 2, x0 + win / 2)
                if np.isfinite(gdy):
                    oy, ox = int(round(gdy)), int(round(gdx))
            yb, xb = y0 + oy, x0 + ox
            if yb < 0 or xb < 0 or yb + win > H or xb + win > W:
                oy = ox = 0
                yb, xb = y0, x0
            dy, dx, r = _corr_peak(a[y0:y0 + win, x0:x0 + win], b[yb:yb + win, xb:xb + win])
            if np.isfinite(dy) and r >= MIN_PEAK_RATIO:
                V[iy, ix], U[iy, ix], Q[iy, ix] = dy + oy, dx + ox, r
    cy = np.array(ys) + win / 2
    cx = np.array(xs) + win / 2
    return cy, cx, V, U, Q


def _fill(F):
    """無効 (NaN) を周り3×3の有効値の中央値、それもなければ全体の中央値で埋める"""
    G = F.copy()
    med = np.nanmedian(F) if np.isfinite(F).any() else 0.0
    for iy, ix in zip(*np.where(~np.isfinite(F))):
        nb = F[max(0, iy - 1):iy + 2, max(0, ix - 1):ix + 2]
        G[iy, ix] = np.nanmedian(nb) if np.isfinite(nb).any() else med
    return G


def _validate(V, U, k=3.0):
    """周りの中央値から大きく外れたベクトルを無効にする (正規化中央値テストの簡易版)。縦横どちらかが外れたら両方無効"""
    V2, U2 = V.copy(), U.copy()
    H, W = V.shape
    for iy in range(H):
        for ix in range(W):
            if not np.isfinite(V[iy, ix]):
                continue
            nb = [(j, i) for j in range(max(0, iy - 1), min(H, iy + 2)) for i in range(max(0, ix - 1), min(W, ix + 2))
                  if (j, i) != (iy, ix) and np.isfinite(V[j, i])]
            if len(nb) < 3:
                continue
            for F in (V, U):
                vals = np.array([F[j, i] for j, i in nb])
                med = np.median(vals)
                if abs(F[iy, ix] - med) > k * (np.median(np.abs(vals - med)) + 1.0):
                    V2[iy, ix] = U2[iy, ix] = np.nan
    return V2, U2


class DisplacementField:
    """フレーム t → t+1 の移動量場。sample(x, y) で任意位置の (dy, dx) を返す"""

    def __init__(self, a, b):
        cy1, cx1, V1, U1, _ = _pass(a, b, WIN1, STEP1)
        V1, U1 = _validate(V1, U1)
        V1, U1 = _fill(V1), _fill(U1)
        f1 = _Interp(cy1, cx1, V1, U1)
        self.cy, self.cx, V2, U2, self.Q = _pass(a, b, WIN2, STEP2, guess=f1)
        V2, U2 = _validate(V2, U2)
        self.valid = np.isfinite(V2)
        self.V, self.U = _fill(V2), _fill(U2)
        self._f = _Interp(self.cy, self.cx, self.V, self.U)

    def sample(self, x, y):
        return self._f(y, x)


class _Interp:
    def __init__(self, cy, cx, V, U):
        self.cy, self.cx, self.V, self.U = cy, cx, V, U

    def __call__(self, y, x):
        if self.V.size == 0:
            return np.nan, np.nan
        fy = np.interp(y, self.cy, np.arange(len(self.cy)))
        fx = np.interp(x, self.cx, np.arange(len(self.cx)))
        y0, x0 = int(np.floor(fy)), int(np.floor(fx))
        y1, x1 = min(y0 + 1, len(self.cy) - 1), min(x0 + 1, len(self.cx) - 1)
        ty, tx = fy - y0, fx - x0

        def bil(F):
            return ((1 - ty) * ((1 - tx) * F[y0, x0] + tx * F[y0, x1])
                    + ty * ((1 - tx) * F[y1, x0] + tx * F[y1, x1]))
        return float(bil(self.V)), float(bil(self.U))


def draw(img_gray, field, scale=1.0):
    out = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    for iy, y in enumerate(field.cy):
        for ix, x in enumerate(field.cx):
            dy, dx = field.V[iy, ix], field.U[iy, ix]
            col = (0, 255, 255) if field.valid[iy, ix] else (0, 0, 255)   # 黄 = 実測, 赤 = 周りから補間
            cv2.arrowedLine(out, (int(x), int(y)), (int(x + scale * dx), int(y + scale * dy)), col, 2, tipLength=0.25)
    return out


def split_by_size(g):
    """2値化画像を気泡の大きさ別の画像に分ける (トラッカーに組み込むときは U-Net の気泡マスク面積で分ける)"""
    n, lab, st, _ = cv2.connectedComponentsWithStats((g > 0).astype(np.uint8), 8)
    out = {k: np.zeros_like(g) for k in ("tiny", "small", "large")}
    for i in range(1, n):
        s = max(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT])
        k = "tiny" if s <= SIZE_SPLIT_PX[0] else ("small" if s <= SIZE_SPLIT_PX[1] else "large")
        out[k][lab == i] = 255
    return out


def main():
    a = cv2.imread(IMAGE_A, cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(IMAGE_B, cv2.IMREAD_GRAYSCALE)
    if a is None or b is None:
        raise SystemExit("画像を読み込めません。IMAGE_A / IMAGE_B を確認してください")
    groups = ({"all": (a, b)} if not SPLIT_BY_SIZE else
              {k: (va, vb) for (k, va), vb in zip(split_by_size(a).items(), split_by_size(b).values())})
    panels = []
    for name, (ga, gb) in groups.items():
        fld = DisplacementField(ga, gb)
        print(f"[{name}] 有効な窓 {100 * fld.valid.mean():.0f}%   移動量の中央値: 縦 {np.median(fld.V):.1f}, "
              f"横 {np.median(fld.U):.1f} px/frame (縦は負 = 上向き)")
        img = draw(np.maximum(ga, (a > 0).astype(np.uint8) * 60), fld)
        cv2.putText(img, name, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        panels.append(img)
    cv2.imwrite(OUT_IMAGE, np.hstack([np.pad(p, ((0, 0), (0, 6), (0, 0)), constant_values=255) for p in panels]))
    print("ベクトル図:", OUT_IMAGE, " (黄 = 相関で求めた, 赤 = 周りから補間。明るい輪郭がその大きさの気泡)")


if __name__ == "__main__":
    main()

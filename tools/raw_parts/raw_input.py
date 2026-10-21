# ======================================================================
# 入力の作り方とモデルの形 — 1_raw_train.py と 2_raw_track.py で同じ (tools/raw_parts/raw_input.py から入れる)
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


def make_planes(raw_bgr, bg_bgr, preproc):
    """元画像 + 背景画像 -> {'B', 'D', 'DK', 'DB'} (どれも uint8 (H, W))
    DK / DB: 背景より暗くなった分 / 明るくなった分 (×Brightness)。気液の界面 (メニスカス) は暗く、
    大きい気泡の中の液膜のむら (乾いた所) は明るい -> B と D (絶対値) では区別できないが、DK と DB なら分かれる"""
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
    'diff' (D×3) を二値化の重み (B×3) から始めるときだけ、B の重みをそのまま D に使う (今までの動作)"""
    import torch
    k0 = next(k for k, v in sd.items() if k.startswith('encoder.') and v.ndim == 4)
    w = sd[k0]
    out = torch.zeros((w.shape[0], len(dst_names)) + tuple(w.shape[2:]), dtype=w.dtype)
    for j, n in enumerate(dst_names):
        if n in src_names:
            out[:, j] = w[:, src_names.index(n)]
        elif n in ('D0', 'D1', 'D2') and 'B' + n[1] in src_names:
            out[:, j] = w[:, src_names.index('B' + n[1])]
    sd = dict(sd)
    sd[k0] = out
    return sd


def _pos2d(h, w, dim, device):
    """2次元の位置 (sin / cos)。画像の大きさが学習と違っても同じ式で作れる"""
    import torch
    d = dim // 4
    omega = 1.0 / (10000 ** (torch.arange(d, device=device, dtype=torch.float32) / max(1, d)))
    ys = torch.arange(h, device=device, dtype=torch.float32)[:, None] * omega[None]
    xs = torch.arange(w, device=device, dtype=torch.float32)[:, None] * omega[None]
    pe = torch.cat([torch.sin(ys)[:, None].expand(h, w, d), torch.cos(ys)[:, None].expand(h, w, d),
                    torch.sin(xs)[None].expand(h, w, d), torch.cos(xs)[None].expand(h, w, d)], -1)
    pe = pe.reshape(h * w, 4 * d)
    if 4 * d < dim:
        pe = torch.cat([pe, pe.new_zeros(h * w, dim - 4 * d)], 1)
    return pe[None]


def _context_block(dim, layers, heads):
    """小さいトランスフォーマー (画面全体の関係を見る)。出口の重みは 0 -> 学習前は何もしない (足す前と同じ結果)"""
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
            t = f.flatten(2).transpose(1, 2) + _pos2d(h, w, c, f.device).to(f.dtype)
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

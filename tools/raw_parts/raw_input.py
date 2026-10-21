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
    """画像 {'B', ...} (+ 事前マスク) -> 確率 (3, H, W)。2_raw_track.py と 1_raw_train.py の test で同じ計算:
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

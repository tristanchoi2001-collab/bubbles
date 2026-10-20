# ======================================================================
# 入力の作り方 — 1_raw_train.py と 2_raw_track.py で同じ (tools/raw_parts/raw_input.py から入れる)
# ======================================================================
INPUT_MODES = ('bin', 'diff', 'bin+diff')


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


def input_channels(mode):
    """INPUT_MODE -> ネットワークの入力チャンネル数"""
    if mode not in INPUT_MODES:
        raise ValueError(f'INPUT_MODE は {INPUT_MODES} のどれか: {mode!r}')
    return 4 if mode == 'bin+diff' else 3


def make_input_raw(B, D, mode, mean, std):
    """(B, D) -> ネットワーク入力 (C, H, W) float32
    'bin'      : B を3回 (今の best.pt と同じ入力)
    'diff'     : D を3回
    'bin+diff' : B を3回 + D (4チャンネル目)。best.pt から始めると 4チャンネル目の重みは 0 = 学習前は 'bin' と同じ結果"""
    input_channels(mode)
    base = (D if mode == 'diff' else B).astype(np.float32) / 255.0
    x = [(base - float(m)) / float(s) for m, s in zip(mean, std)]
    if mode == 'bin+diff':
        x.append((D.astype(np.float32) / 255.0 - float(mean[0])) / float(std[0]))
    return np.stack(x)

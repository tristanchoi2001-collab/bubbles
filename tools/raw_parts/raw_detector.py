class RawDetector:
    """1_raw_train.py の ckpt を読み込み、元画像 + 背景画像 (+ 事前マスク) から 背景/内部/境界 の確率 (3, H, W) を返す。
    入力の作り方 (INPUT_MODE、事前マスクの有無) と前処理の値は ckpt に記録したものを使う -> 学習と同じ入力になる。
    記録の無い ckpt (今の二値化の best.pt など) は 'bin' と PREPROC_FIXED (None なら PREPROC_DEFAULT) で動く
    (= 二値化版の UNetDetector と同じ確率)。TAU (5チャンネル) は 'bin' + 事前マスク (= 二値化版の TauDetector と同じ確率)。
    事前マスクを使うモデルに事前マスクを渡さなければ 0 (事前情報なし) を入れる"""

    def __init__(self, ckpt_path, train_hw=None):
        import torch
        self.torch = torch
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        ck = torch.load(ckpt_path, map_location="cpu")
        sd = {k: (v.float() if v.is_floating_point() else v) for k, v in ck["state_dict"].items()}
        inp = ck.get("input") or {}
        self.mode, self.uses_prior, names = ckpt_layout(ck, sd)
        self.preproc = tuple(int(v) for v in (inp.get("preproc") or PREPROC_FIXED or PREPROC_DEFAULT))
        self.edge_px = int(inp.get("prior_edge_px") or ck.get("prior_edge_px") or PRIOR_EDGE_PX)
        ctx = ck.get("ctx") or {}
        self.model = build_unet(ck["encoder"], ck.get("classes", 3), len(names),
                                ctx.get("layers", 0), ctx.get("heads", 8)).to(self.dev)
        self.model.load_state_dict(sd)
        self.model.eval()
        self.mean = np.array(ck["mean"], np.float32)
        self.std = np.array(ck["std"], np.float32)
        hw = ck.get("train_hw") or train_hw
        self.train_hw = (int(hw[0]), int(hw[1])) if hw else None
        self.raw_of = None          # TAU の多パス: フレーム番号 -> (元画像, 背景画像)
        self.last_planes = {}
        self._resize_notice = False
        print(f"  U-Net: {ckpt_path}  (epoch {ck.get('epoch')}, device {self.dev}, 入力 {self.mode!r}, "
              f"前処理 {self.preproc}{'' if inp else ' (ckpt に記録なし)'}"
              f"{', 事前マスク (TAU) あり' if self.uses_prior else ''}"
              f"{', トランスフォーマー ' + str(ctx.get('layers')) + '層' if ctx.get('layers') else ''}, "
              f"学習画像サイズ {self.train_hw if self.train_hw else '記録なし'})")
        if self.dev == "cpu":
            print("  ※ GPUが見つかりません。CPUでも動きますが遅くなります。")

    def prob_raw(self, raw_bgr, bg_bgr, prior=None):
        """元画像 (BGR) + 背景画像 (BGR) (+ 事前マスク (2, H, W)) -> 確率 (3, H, W)"""
        planes = make_planes(raw_bgr, bg_bgr, self.preproc)
        self.last_planes = {k: planes[k] for k in PLANES[self.mode]}     # U-Net が実際に見た画像 (確認用)
        H, W = planes["B"].shape
        if self.train_hw is not None and (H, W) != self.train_hw and not self._resize_notice:
            print(f"  ※ 画像サイズ {H}x{W} が学習画像 {self.train_hw[0]}x{self.train_hw[1]} と異なるため、"
                  "学習サイズに合わせて推論します")
            self._resize_notice = True
        return predict_planes(self.model, self.last_planes, self.mode, self.mean, self.std, self.dev, prior, self.uses_prior,
                              self.train_hw)

    def prob_frame(self, f, gray, prior=None):
        """TAU の多パス用: フレーム番号 f の確率 (gray は表示用の二値化画像。U-Net の入力は元画像から作る)"""
        raw, bg = self.raw_of(f)
        return self.prob_raw(raw, bg, prior)

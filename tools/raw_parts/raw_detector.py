class RawDetector:
    """1_raw_train.py の ckpt を読み込み、元画像 + 背景画像から 背景/内部/境界 の確率 (3, H, W) を返す。
    入力の作り方 (INPUT_MODE と前処理の値) は ckpt に記録したものを使う -> 学習と同じ入力になる。
    記録の無い ckpt (今の二値化の best.pt など) は 'bin' と PREPROC_FIXED (None なら PREPROC_DEFAULT) で動く
    (= 二値化版の UNetDetector と同じ確率)"""

    def __init__(self, ckpt_path, train_hw=None):
        import torch
        import segmentation_models_pytorch as smp
        self.torch = torch
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        ck = torch.load(ckpt_path, map_location="cpu")
        sd = {k: (v.float() if v.is_floating_point() else v) for k, v in ck["state_dict"].items()}
        inp = ck.get("input") or {}
        self.mode = inp.get("mode", "bin")
        self.preproc = tuple(int(v) for v in (inp.get("preproc") or PREPROC_FIXED or PREPROC_DEFAULT))
        in_ch = next(int(v.shape[1]) for k, v in sd.items() if k.startswith("encoder.") and v.ndim == 4)
        if in_ch != input_channels(self.mode):
            raise ValueError(f"{ckpt_path}: 入力 {self.mode!r} には {input_channels(self.mode)}チャンネルが要るのに "
                             f"重みは {in_ch}チャンネル (TAU の 5チャンネルには対応していません)")
        self.model = smp.Unet(ck["encoder"], encoder_weights=None, in_channels=in_ch,
                              classes=ck.get("classes", 3)).to(self.dev)
        self.model.load_state_dict(sd)
        self.model.eval()
        self.mean = np.array(ck["mean"], np.float32)
        self.std = np.array(ck["std"], np.float32)
        hw = ck.get("train_hw") or train_hw
        self.train_hw = (int(hw[0]), int(hw[1])) if hw else None
        self._resize_notice = False
        print(f"  U-Net: {ckpt_path}  (epoch {ck.get('epoch')}, device {self.dev}, 入力 {self.mode!r}, "
              f"前処理 {self.preproc}{'' if inp else ' (ckpt に記録なし)'}, "
              f"学習画像サイズ {self.train_hw if self.train_hw else '記録なし'})")
        if self.dev == "cpu":
            print("  ※ GPUが見つかりません。CPUでも動きますが遅くなります。")

    def _forward(self, B, D):
        torch = self.torch
        H, W = B.shape
        ph, pw = (-H) % 32, (-W) % 32
        B = cv2.copyMakeBorder(B, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
        D = cv2.copyMakeBorder(D, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
        x = torch.from_numpy(make_input_raw(B, D, self.mode, self.mean, self.std))[None].to(self.dev)
        with torch.no_grad():
            p = self.model(x).softmax(1)[0].cpu().numpy()
        return p[:, :H, :W]

    def prob_raw(self, raw_bgr, bg_bgr):
        """元画像 (BGR) + 背景画像 (BGR) -> 確率 (3, H, W)"""
        B, D = bin_diff(raw_bgr, bg_bgr, self.preproc)
        H, W = B.shape
        if self.train_hw is None or (H, W) == self.train_hw:
            return self._forward(B, D)
        th, tw = self.train_hw
        if not self._resize_notice:
            print(f"  ※ 画像サイズ {H}x{W} が学習画像 {th}x{tw} と異なるため、学習サイズに合わせて推論します")
            self._resize_notice = True
        interp = cv2.INTER_AREA if th * tw < H * W else cv2.INTER_LINEAR
        p = self._forward(cv2.resize(B, (tw, th), interpolation=interp), cv2.resize(D, (tw, th), interpolation=interp))
        return np.stack([cv2.resize(c, (W, H), interpolation=cv2.INTER_LINEAR) for c in p])

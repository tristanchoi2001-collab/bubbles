"""
二値化しない版 (raw/1_raw_train.py, raw/2_raw_track.py) の回帰テスト
=====================================================================
  a) 3ファイルが tools/build_raw.py で作り直した内容と同じ (最新)
  b) bin_diff の B = 2_bin_track の前処理 (preprocess_image) の結果。D は Noise Cut を外しただけ。
     DK / DB は暗くなった分 / 明るくなった分 (輪郭は DK、明るいむらは DB)。入力のチャンネル数
  c) RawDetector とモデルの形:
     記録の無い 3ch ckpt = 2_bin_track の UNetDetector と完全に同じ確率 (学習サイズへの拡大縮小も)。
     best.pt から足した入力 ('bin+diff', 'bin+sign') とトランスフォーマーは重み 0 から = 3ch と同じ確率。
     トランスフォーマーは本当に通り道に入っている (出口の重みを変えると確率が変わる)。
     TAU (5ch) = 2_bin_track の TauDetector と同じ確率 (事前マスクなし / あり)。チャンネル数が合わない ckpt は止まる
  d) 学習: Roboflow の名前 (_jpg.rf.<hash>) から背景を選び、4つの INPUT_MODE と OLD_BIN_SRC で最後まで動く。
     OLD_BIN_SRC の valid は best の点数に、test は別の表に使う。背景の決まらない画像・取り違えは止まる。
     トランスフォーマー + TAU (事前マスク) でも最後まで動き、test は 事前マスクなし / あり の 2列。
     できた ckpt を RawDetector が記録どおりの入力・部品で読む
  e) 2_raw_track の main_single: 記録の無い 3ch ckpt なら 2_bin_track の main_single と同じ CSV。
     学習した ckpt でも最後まで動き、qc_report に入力の記録が残る
  f) TAU の多パス: 二値化の TAU ckpt なら 2_raw_track の main は 2_bin_track の main (main_tau) と同じ CSV。
     raw で学習した事前マスク付きの ckpt でも最後まで動く

使い方: リポジトリのルートで  python -B tests/test_raw.py     (pytest でも実行できる)
"""
import importlib.util
import json
import os
import sys
import tempfile

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)


class Skip(Exception):
    pass


def need_torch():
    try:
        import torch  # noqa: F401
        import segmentation_models_pytorch  # noqa: F401
    except ImportError as e:
        raise Skip(f"torch なし ({e})")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TRACK = load(os.path.join(ROOT, "raw", "2_raw_track.py"), "raw_track")
BIN = load(os.path.join(ROOT, "binarized", "2_bin_track.py"), "bin_track_for_raw")


def frame_pair(H=96, W=128, seed=0, shift=0):
    """背景 220 の元画像: 輪郭は暗い輪 (差 100)、気泡の中は液体より少し暗い (差 約9)、背景にノイズ (σ 2)"""
    rng = np.random.default_rng(seed)
    bg = np.clip(220 + rng.normal(0, 2, (H, W, 3)), 0, 255).astype(np.uint8)
    f = np.clip(bg.astype(np.int16) + rng.normal(0, 2, (H, W, 3)).astype(np.int16), 0, 255).astype(np.uint8)
    circles = [(40 + shift, 50, 15), (100, 30 + shift, 6), (20, 80, 9)]
    for cx, cy, r in circles:
        cv2.circle(f, (cx, cy), r, (211, 211, 211), -1)
        cv2.circle(f, (cx, cy), r, (120, 120, 120), 2)
    return f, bg, circles


def circle_poly(cx, cy, r, n=24):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1).ravel().tolist()


# ==============================================================
def test_a_up_to_date():
    import build_raw
    for name, text in build_raw.build_all().items():
        with open(os.path.join(ROOT, "raw", name), encoding="utf-8") as f:
            assert f.read() == text, f"raw/{name} が古い (python tools/build_raw.py で作り直す)"


def test_b_bin_diff_matches_preprocess():
    f, bg, _ = frame_pair()
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "f.png")
        cv2.imwrite(p, f)
        for pre in ((15, 4, 0), (15, 4, 1), (30, 3, 2), (0, 1, 0)):
            _, proc, *_ = BIN.preprocess_image(p, bg, show_ui=False, current_thresh_val=pre[0],
                                               current_bright_val=pre[1], current_median_val=pre[2])
            B, D = TRACK.bin_diff(f, bg, pre)
            assert (B == cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)).all(), pre
            _, Dref = TRACK.bin_diff(f, bg, (0,) + pre[1:])
            assert (D == Dref).all() and (D >= B).all()
            pl = TRACK.make_planes(f, bg, pre)
            assert (pl["B"] == B).all() and (pl["D"] == D).all()
        B, D = TRACK.bin_diff(f, cv2.resize(bg, (64, 48)), (15, 4, 0))   # 背景の大きさが違えば合わせる
        assert B.shape == f.shape[:2]
    B, D = TRACK.bin_diff(f, bg, (15, 4, 0))
    inside = np.zeros(B.shape, bool)
    cv2.circle(inside.view(np.uint8), (40, 50), 11, 1, -1)
    assert B[inside].max() == 0 and np.median(D[inside]) >= 30, "D に気泡の中の薄い差が残っていない"
    # 暗い輪郭は DK、明るいむら (乾いた所) は DB に分かれる。B (絶対値) では両方とも白
    g = f.copy()
    g[5:20, 90:120] = np.clip(bg[5:20, 90:120].astype(np.int16) + 30, 0, 255).astype(np.uint8)
    pl = TRACK.make_planes(g, bg, (15, 4, 0))
    ring = np.zeros(B.shape, bool)
    cv2.circle(ring.view(np.uint8), (40, 50), 15, 1, 2)
    assert np.median(pl["DK"][ring]) > 200 and np.median(pl["DB"][ring]) == 0
    assert np.median(pl["DB"][5:20, 90:120]) > 100 and pl["DK"][5:20, 90:120].max() == 0
    assert np.median(pl["B"][5:20, 90:120]) > 100, "B では明るいむらも白い (区別できない)"
    for mode, n in (("bin", 3), ("diff", 3), ("bin+diff", 4), ("bin+sign", 5)):
        x = TRACK.make_input_raw(pl, mode, TRACK_MEAN, TRACK_STD)
        assert x.shape == (n,) + B.shape and x.dtype == np.float32 and TRACK.input_channels(mode) == n
        xp = TRACK.make_input_raw(pl, mode, TRACK_MEAN, TRACK_STD, None, True)
        assert xp.shape[0] == n + 2 and not xp[n:].any() and TRACK.input_channels(mode, True) == n + 2
    try:
        TRACK.input_channels("raw")
        raise AssertionError("知らない INPUT_MODE で止まらない")
    except ValueError:
        pass


TRACK_MEAN = np.array((0.485, 0.456, 0.406), np.float32)
TRACK_STD = np.array((0.229, 0.224, 0.225), np.float32)


def save_ckpt(path, model, train_hw=None, inp=None, epoch=1, ctx=None):
    import torch
    ck = {"encoder": "resnet34", "classes": 3, "mean": (0.485, 0.456, 0.406), "std": (0.229, 0.224, 0.225),
          "train_hw": train_hw, "epoch": epoch, "state_dict": model.state_dict()}
    if inp is not None:
        ck["input"] = inp
    if ctx is not None:
        ck["ctx"] = ctx
    torch.save(ck, path)


def widen(m3, mode, prior=False, ctx_layers=0):
    """3ch の重み -> mode (+ 事前マスク, + トランスフォーマー) のモデル (足した重みは 0)"""
    model = TRACK.build_unet("resnet34", 3, TRACK.input_channels(mode, prior), ctx_layers).eval()
    sd = TRACK.remap_first_conv(m3.state_dict(), TRACK.channel_names("bin"), TRACK.channel_names(mode, prior))
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not unexpected and all(k.startswith("ctx.") for k in missing)
    return model


def test_c_detector():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    f, bg, _ = frame_pair(90, 120)
    with tempfile.TemporaryDirectory() as td:
        torch.manual_seed(0)
        m3 = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval()
        for hw in (None, [64, 96]):
            ck = os.path.join(td, f"b3_{hw}.pt")
            save_ckpt(ck, m3, hw)
            B, _ = TRACK.bin_diff(f, bg, TRACK.PREPROC_FIXED)
            p_ref = BIN.UNetDetector(ck).prob(B)
            det = TRACK.RawDetector(ck)
            assert det.mode == "bin" and det.preproc == tuple(TRACK.PREPROC_FIXED) and not det.uses_prior
            p = det.prob_raw(f, bg)
            assert p.shape == (3, 90, 120) and np.array_equal(p, p_ref), (hw, float(np.abs(p - p_ref).max()))
        p3 = TRACK.RawDetector(os.path.join(td, "b3_None.pt")).prob_raw(f, bg)
        # 足した入力・トランスフォーマーは重み 0 -> 3ch と同じ確率
        for mode, layers in (("bin+diff", 0), ("bin+sign", 0), ("bin+sign", 2), ("bin", 1)):
            ckm = os.path.join(td, f"w_{mode}_{layers}.pt")
            save_ckpt(ckm, widen(m3, mode, False, layers), None, {"mode": mode, "preproc": [15, 4, 0]},
                      ctx={"layers": layers, "heads": 8} if layers else None)
            dm = TRACK.RawDetector(ckm)
            d = float(np.abs(dm.prob_raw(f, bg) - p3).max())
            assert dm.mode == mode and d < 1e-5, (mode, layers, d)
        # トランスフォーマーは本当に通り道に入っている
        mc = widen(m3, "bin", False, 1)
        with torch.no_grad():
            mc.ctx.out.weight.normal_(0, 0.05)
        ckc = os.path.join(td, "ctx_on.pt")
        save_ckpt(ckc, mc, None, {"mode": "bin", "preproc": [15, 4, 0]}, ctx={"layers": 1, "heads": 8})
        assert float(np.abs(TRACK.RawDetector(ckc).prob_raw(f, bg) - p3).max()) > 1e-3, "トランスフォーマーが効いていない"
        ckd = os.path.join(td, "d3.pt")
        save_ckpt(ckd, m3, None, {"mode": "diff", "preproc": [20, 3, 0]})
        dd = TRACK.RawDetector(ckd)
        _, D = TRACK.bin_diff(f, bg, (20, 3, 0))
        assert dd.preproc == (20, 3, 0) and np.array_equal(dd.prob_raw(f, bg), BIN.UNetDetector(ckd).prob(D))
        # TAU (5ch, 記録なし) = 2_bin_track の TauDetector (事前マスクなし / あり)
        m5 = widen(m3, "bin", True)
        with torch.no_grad():
            m5.encoder.conv1.weight[:, 3:] = torch.randn_like(m5.encoder.conv1.weight[:, 3:])   # 事前マスクの重み (0 でない)
        ck5 = os.path.join(td, "tau5.pt")
        save_ckpt(ck5, m5, None)
        d5, t5 = TRACK.RawDetector(ck5), BIN.TauDetector(ck5)
        B, _ = TRACK.bin_diff(f, bg, TRACK.PREPROC_FIXED)
        prior = TRACK.render_prior([(np.ones((20, 20), bool), 30, 40)], 90, 120, d5.edge_px)
        assert d5.mode == "bin" and d5.uses_prior and d5.edge_px == 2
        for pr in (None, prior):
            d = float(np.abs(d5.prob_raw(f, bg, pr) - t5.prob(B, pr)).max())
            assert d < 1e-5, d
        assert float(np.abs(d5.prob_raw(f, bg, prior) - d5.prob_raw(f, bg)).max()) > 1e-4, "事前マスクが効いていない"
        # 二値化の道具は raw の ckpt ('bin+sign' も 5ch) を TAU と取り違えず止める
        cks5 = os.path.join(td, "sign5.pt")
        save_ckpt(cks5, widen(m3, "bin+sign"), None, {"mode": "bin+sign", "preproc": [15, 4, 0], "prior": False})
        for fn in (lambda: BIN.ckpt_uses_prior(cks5), lambda: BIN.TauDetector(cks5)):
            try:
                fn()
                raise AssertionError("raw の ckpt を二値化の道具が読んでしまう")
            except ValueError as e:
                assert "raw/2_raw_track.py" in str(e)
        assert BIN.ckpt_uses_prior(ck5) and not BIN.ckpt_uses_prior(os.path.join(td, "b3_None.pt"))
        # 'diff' と B の入れ替えはもう一方の重みを使う
        sdd = TRACK.remap_first_conv(m3.state_dict(), TRACK.channel_names("diff"), TRACK.channel_names("bin"))
        assert torch.equal(sdd["encoder.conv1.weight"], m3.state_dict()["encoder.conv1.weight"])
        # トランスフォーマーの位置: ずらした位置 = 大きい格子の一部 (学習中のずらしが推論の位置を含む)
        big = TRACK._pos2d(17, 21, 512, "cpu")[0].reshape(17, 21, 512)
        sh = TRACK._pos2d(13, 15, 512, "cpu", 4, 6)[0].reshape(13, 15, 512)
        assert torch.allclose(big[4:, 6:], sh, atol=1e-5)
        x = torch.randn(1, 3, 64, 96)
        with torch.no_grad():
            a1, a2 = mc.eval()(x), mc(x)
        assert torch.equal(a1, a2), "推論でトランスフォーマーの位置がずれている"
        for bad, inp in ((m3, {"mode": "bin+diff"}), (widen(m3, "bin+diff"), None), (m5, {"mode": "bin+diff"})):
            ckb = os.path.join(td, "bad.pt")
            save_ckpt(ckb, bad, None, inp)
            try:
                TRACK.RawDetector(ckb)
                raise AssertionError(f"チャンネル数の合わない ckpt で止まらない ({inp})")
            except ValueError:
                pass


# ==============================================================
# 学習
# ==============================================================
def make_src(td, name="coco", n_train=3, binarized=False):
    """Roboflow の書き出しの形 (<split>/画像 + _annotations.coco.json)。名前は 'test0000k_jpg.rf.<hash>.jpg'"""
    src = os.path.join(td, name)
    bg = None
    k = 0
    for split, n in (("train", n_train), ("valid", 1), ("test", 1)):
        os.makedirs(os.path.join(src, split))
        images, anns = [], []
        for i in range(n):
            f, bg, circles = frame_pair(seed=k, shift=2 * k)
            fn = f"test{k:05d}_jpg.rf.{k:08x}ab.jpg"
            if binarized:
                f = cv2.cvtColor(TRACK.bin_diff(f, bg, (15, 4, 0))[0], cv2.COLOR_GRAY2BGR)
                fn = f"old{k:05d}_png.rf.{k:08x}cd.png"
            cv2.imwrite(os.path.join(src, split, fn), f)
            im = {"id": i, "file_name": fn, "height": f.shape[0], "width": f.shape[1]}
            if i == 1:
                im["extra"] = {"name": f"test{k:05d}.jpg"}
            images.append(im)
            for cx, cy, r in circles:
                anns.append({"id": len(anns), "image_id": i, "category_id": 1, "segmentation": [circle_poly(cx, cy, r + 1)],
                             "bbox": [cx - r - 1, cy - r - 1, 2 * r + 2, 2 * r + 2], "area": 3.14 * r * r, "iscrowd": 0})
            k += 1
        with open(os.path.join(src, split, "_annotations.coco.json"), "w") as fp:
            json.dump({"images": images, "annotations": anns, "categories": [{"id": 1, "name": "bubble"}]}, fp)
    cv2.imwrite(os.path.join(td, "bg_test.png"), bg)
    return src


def _configure(TR, td, src, mode, base_ckpt, old=None, out="runs"):
    TR.SRC, TR.BACKGROUNDS, TR.DEFAULT_BACKGROUND = src, {"test": os.path.join(td, "bg_test.png"), "zz": "none"}, None
    TR.INPUT_MODE, TR.OLD_BIN_SRC, TR.OLD_SHARE = mode, old, 0.5
    TR.OLD_VAL_WEIGHT, TR.OLD_VAL_TOL, TR.REBUILD_DATASET = 0.3, 0.01, True
    TR.DST, TR.OUT = os.path.join(td, f"ds_{mode}"), os.path.join(td, out, mode.replace("+", "_"))
    TR.FINETUNE_FROM, TR.EPOCHS, TR.BS, TR.CROP, TR.WORKERS = base_ckpt, 1, 2, (64, 96), 0
    TR.CP_PROB = 1.0


def test_d_train_smoke():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    TR = load(os.path.join(ROOT, "raw", "1_raw_train.py"), "raw_train_d")
    assert TR.original_name({"file_name": "a/test00012_jpg.rf.9fA3b.jpg"}) == "test00012.jpg"
    assert TR.original_name({"file_name": "x_png.rf.1.jpg", "extra": {"name": "dir/y.png"}}) == "y.png"
    assert TR.original_name({"file_name": "plain.png"}) == "plain.png"
    bgs = {"test": "A", "test0001": "B"}
    assert TR.background_for("test00012.jpg", bgs, "Z") == "B" and TR.background_for("test00002.jpg", bgs) == "A"
    assert TR.background_for("cam.jpg", bgs, "Z") == "Z"
    with tempfile.TemporaryDirectory() as td:
        src = make_src(td)
        old = make_src(td, "old_coco", n_train=2, binarized=True)
        torch.manual_seed(0)
        base = os.path.join(td, "best.pt")
        save_ckpt(base, smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3), [96, 128], epoch=65)
        _configure(TR, td, src, "bin", base)
        TR.BACKGROUNDS = {"cam": os.path.join(td, "bg_test.png")}
        try:
            TR.main()
            raise AssertionError("背景の決まらない画像で止まらない")
        except SystemExit as e:
            assert "test00000.jpg" in str(e) and "5枚" in str(e), str(e)
        # SRC と OLD_BIN_SRC の取り違えは止める (同じフォルダ / OLD_BIN_SRC が元画像 / SRC が二値化画像)
        for s_, o_, word in ((src, src, "同じフォルダ"), (src, make_src(td, "raw_as_old"), "二値化画像に見えない"),
                             (old, None, "二値化画像に見えます")):
            _configure(TR, td, s_, "bin+diff", base, o_, out="runs_guard")
            TR.BACKGROUNDS = {"test": os.path.join(td, "bg_test.png"), "old": os.path.join(td, "bg_test.png")}
            try:
                TR.main()
                raise AssertionError(f"取り違えで止まらない ({word})")
            except SystemExit as e:
                assert word in str(e), str(e)
        # Roboflow の Augmentation (同じ元画像のコピー) / Resize は止める。失敗した変換の meta.json は残さない
        aug = os.path.join(td, "aug_coco")
        import shutil as _sh
        _sh.copytree(src, aug)
        a0 = json.load(open(os.path.join(aug, "train", "_annotations.coco.json")))
        fn0 = a0["images"][0]["file_name"]
        fn_dup = fn0.replace(".rf.", ".rf.zz")
        _sh.copy(os.path.join(aug, "train", fn0), os.path.join(aug, "train", fn_dup))
        a0["images"].append(dict(a0["images"][0], id=99, file_name=fn_dup))
        json.dump(a0, open(os.path.join(aug, "train", "_annotations.coco.json"), "w"))
        small_bg = os.path.join(td, "bg_small.png")
        cv2.imwrite(small_bg, cv2.resize(cv2.imread(os.path.join(td, "bg_test.png")), (64, 48)))
        for s_, bgp, word in ((aug, None, "同じ元画像"), (src, small_bg, "大きさ")):
            _configure(TR, td, s_, "bin", base, None, out="runs_aug")
            if bgp:
                TR.BACKGROUNDS = {"test": bgp}
            meta_p = TR.resolve(TR.DST) / "meta.json"
            meta_p.parent.mkdir(parents=True, exist_ok=True)
            meta_p.write_text("{}")
            try:
                TR.main()
                raise AssertionError(f"止まらない ({word})")
            except SystemExit as e:
                assert word in str(e), str(e)
            assert not meta_p.exists(), "失敗した変換の meta.json が残っている"
        cks = {}
        groups = {"bin+sign": {"B", "DK", "DB"}, "bin+diff": {"B", "D"}, "diff": {"D"}, "bin": {"B"}}
        for mode, o in (("bin+sign", old), ("bin+diff", None), ("diff", None), ("bin", None)):
            _configure(TR, td, src, mode, base, o)
            TR.main()
            out = TR.resolve(TR.OUT)
            ck = torch.load(str(out / "best.pt"), map_location="cpu")
            assert ck["input"] == {"mode": mode, "preproc": [15, 4, 0], "prior": False, "prior_edge_px": 2}
            assert ck["in_channels"] == TR.input_channels(mode) and ck["ctx"] is None
            assert ck["train_hw"] == [96, 128] and ck["n_train"] == 3 and ck["n_train_old"] == (2 if o else 0)
            assert ck["n_val_old"] == (1 if o else 0) and ck["old_val_weight"] == (0.3 if o else 0.0)
            assert (ck["val_old"] is not None) == bool(o)
            rep = json.load(open(out / "test_report.json", encoding="utf-8"))
            assert len(rep["columns"]) == 2 and rep["input_mode"] == mode
            assert all(c["train_hw"] == [96, 128] for c in rep["columns"].values())   # 2_raw_track と同じ大きさで推論
            for col in rep["columns"].values():
                assert col["n_gt"] == 3
            assert ("old_test" in rep) == bool(o)          # 今までの二値化画像の test は別の表
            if o:
                assert list(rep["old_test"]) == list(rep["columns"]) and all(c["n_gt"] == 3 for c in rep["old_test"].values())
                assert len(os.listdir(out / "old_test_preview")) == 2
            log = json.load(open(out / "log.json"))
            assert len(log) == 1 and set(log[0]["input_w"]) == groups[mode] and "ctx_w" not in log[0]
            sc = lambda iou: 0.4 * iou[1] + 0.6 * iou[2]
            want = 0.7 * sc(log[0]["iou"]) + 0.3 * sc(log[0]["iou_old"]) if o else sc(log[0]["iou"])
            assert abs(log[0]["score"] - want) < 1e-9 and (log[0]["iou_old"] is None) == (not o)
            ds = TR.resolve(TR.DST)
            for sub in ("bin", "diff", "dark", "bright", "masks", "instances"):
                assert len(os.listdir(ds / sub / "train")) == 3 and len(os.listdir(ds / sub / "val")) == 1
                for split, n in (("old", 2), ("old_val", 1), ("old_test", 1)):   # OLD_BIN_SRC の train / valid / test
                    assert len(TR.list_images(ds / sub / split)) == (n if o else 0), (sub, split)
            if o:      # 今までの二値化画像: DK = B, DB = 0
                stem = TR.list_images(ds / "bin" / "old")[0].name
                b_, k_, r_ = (cv2.imread(str(ds / s / "old" / stem), cv2.IMREAD_GRAYSCALE) for s in ("bin", "dark", "bright"))
                assert (k_ == b_).all() and not r_.any()
            cks[mode] = str(out / "best.pt")
            det = TRACK.RawDetector(cks[mode])
            assert det.mode == mode and det.preproc == (15, 4, 0) and det.train_hw == (96, 128) and not det.uses_prior
        # 今までの val が開始モデルより下がった epoch は best にしない (OLD_VAL_TOL < 0 = 必ず「下がった」扱い)
        ev = lambda i, e: {"iou": [0.9, i, e]}
        assert TR.old_val_ok(ev(0.90, 0.50), ev(0.90, 0.51)) and not TR.old_val_ok(ev(0.90, 0.48), ev(0.90, 0.51))
        assert TR.old_val_ok(None, ev(0.9, 0.5)) and TR.old_val_ok(ev(0.1, 0.1), None)
        _configure(TR, td, src, "bin+diff", base, old, out="runs_tol")
        TR.OLD_VAL_TOL = -1.0
        TR.main()
        out = TR.resolve(TR.OUT)
        log = json.load(open(out / "log.json"))
        assert log[0].get("old_val_drop") and torch.load(str(out / "best.pt"), map_location="cpu")["epoch"] == 0
        # REBUILD_DATASET = False: 設定が同じなら使い回す / OLD_BIN_SRC を外したら作り直す (古い old/ を使わない)
        ds_meta = TR.resolve(TR.DST) / "meta.json"
        t0 = os.path.getmtime(ds_meta)
        _configure(TR, td, src, "bin+diff", base, old, out="runs_reuse")
        TR.REBUILD_DATASET = False
        TR.main()
        assert os.path.getmtime(ds_meta) == t0, "設定が同じなのに作り直した"
        _configure(TR, td, src, "bin+diff", base, None, out="runs_noold")
        TR.REBUILD_DATASET = False
        TR.main()
        ck = torch.load(str(TR.resolve(TR.OUT) / "best.pt"), map_location="cpu")
        assert ck["n_train_old"] == 0 and ck["n_val_old"] == 0 and ck["old_src"] is None
        assert not TR.list_images(TR.resolve(TR.DST) / "bin" / "old")
        assert "old_test" not in json.load(open(TR.resolve(TR.OUT) / "test_report.json", encoding="utf-8"))
        # TAU (5ch) の ckpt から: 事前マスクを使わなければ事前マスクの重みは捨てる
        m3 = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3)
        m3.load_state_dict(torch.load(base, map_location="cpu")["state_dict"])
        tau_p = os.path.join(td, "tau3_best.pt")
        save_ckpt(tau_p, widen(m3, "bin", True), [96, 128], epoch=14)
        _configure(TR, td, src, "bin+diff", tau_p, None, out="runs_tau")
        TR.main()
        rep = json.load(open(TR.resolve(TR.OUT) / "test_report.json", encoding="utf-8"))
        assert list(rep["columns"])[0] == "開始モデル (bin)"
        assert torch.load(str(TR.resolve(TR.OUT) / "best.pt"), map_location="cpu")["in_channels"] == 4
        # トランスフォーマー + TAU (事前マスク) を TAU の ckpt から (事前マスクの重みは引き継ぐ)
        _configure(TR, td, src, "bin+sign", tau_p, old, out="runs_ctx_tau")
        TR.CTX_LAYERS, TR.USE_PRIOR = 1, True
        try:
            TR.main()
        finally:
            TR.CTX_LAYERS, TR.USE_PRIOR = 0, False
        out = TR.resolve(TR.OUT)
        ck = torch.load(str(out / "best.pt"), map_location="cpu")
        assert ck["in_channels"] == 7 and ck["input"]["prior"] is True and ck["ctx"] == {"layers": 1, "heads": 8}
        log = json.load(open(out / "log.json"))
        assert "ctx_w" in log[0] and log[0]["iou_prior"] is not None and set(log[0]["input_w"]) == {"B", "DK", "DB", "P_IN", "P_EDGE"}
        rep = json.load(open(out / "test_report.json", encoding="utf-8"))
        assert list(rep["columns"]) == ["開始モデル (bin)", "新 (bin+sign, 変換1層, 事前なし)", "新 (bin+sign, 変換1層, 事前あり)"]
        assert list(rep["old_test"]) == list(rep["columns"]) and rep["use_prior"] and rep["ctx_layers"] == 1
        dt = TRACK.RawDetector(str(out / "best.pt"))
        assert dt.uses_prior and dt.mode == "bin+sign"
        with open(out / "best.pt", "rb") as fp:          # f) で使う (この一時フォルダは消える)
            test_d_train_smoke.ck_prior = fp.read()
        # トランスフォーマーのヘッド数は ckpt のものを使い、その数を記録する (CTX_HEADS と違っても)
        _configure(TR, td, src, "bin+sign", str(out / "best.pt"), None, out="runs_heads")
        TR.CTX_LAYERS, TR.CTX_HEADS, TR.USE_PRIOR = 1, 4, True
        try:
            TR.main()
        finally:
            TR.CTX_LAYERS, TR.CTX_HEADS, TR.USE_PRIOR = 0, 8, False
        assert torch.load(str(TR.resolve(TR.OUT) / "best.pt"), map_location="cpu")["ctx"] == {"layers": 1, "heads": 8}
        # トランスフォーマーの層数が違う ckpt からは始められない
        _configure(TR, td, src, "bin+sign", str(out / "best.pt"), None, out="runs_ctx2")
        TR.CTX_LAYERS, TR.USE_PRIOR = 2, True
        try:
            TR.main()
            raise AssertionError("トランスフォーマーの層数が違うのに止まらない")
        except ValueError:
            pass
        finally:
            TR.CTX_LAYERS, TR.USE_PRIOR = 0, False
        # 学習した 4ch から続けて学習 (開始モデルの列は ckpt の入力で評価)
        _configure(TR, td, src, "bin+diff", cks["bin+diff"], out="runs_b")
        TR.main()
        rep = json.load(open(TR.resolve(TR.OUT) / "test_report.json", encoding="utf-8"))
        assert list(rep["columns"])[0] == "開始モデル (bin+diff)"
        with open(cks["bin+sign"], "rb") as fp:          # e) で使う
            test_d_train_smoke.ck_sign = fp.read()


# ==============================================================
# 検出・追跡
# ==============================================================
def _track_settings(M, frames, bg, ck, out):
    M.IMAGE_FOLDER, M.BACKGROUND_PATH, M.UNET_CKPT, M.OUTPUT_FOLDER = frames, bg, ck, out
    M.PREPROC_FIXED, M.ENABLE_BOOTSTRAP, M.ENABLE_ROI = (15, 4, 0), False, False


def _frames(td, n=4):
    frames = os.path.join(td, "frames")
    os.makedirs(frames)
    for k in range(n):
        f, bg, _ = frame_pair(seed=10 + k, shift=3 * k)
        cv2.imwrite(os.path.join(frames, f"img{k:04d}.png"), f)
    bgp = os.path.join(td, "bg.png")
    cv2.imwrite(bgp, bg)
    return frames, bgp


def test_e_track_end_to_end():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    with tempfile.TemporaryDirectory() as td:
        frames, bgp = _frames(td)
        torch.manual_seed(1)
        ck = os.path.join(td, "best.pt")
        save_ckpt(ck, smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3), [96, 128])
        res = {}
        for name, M in (("bin", BIN), ("raw", TRACK)):
            out = os.path.join(td, "out_" + name)
            _track_settings(M, frames, bgp, ck, out)
            M.main()
            res[name] = out
        for fn in ("result_tracking.csv", "result_area_count.csv"):
            a = open(os.path.join(res["bin"], fn), "rb").read()
            assert a == open(os.path.join(res["raw"], fn), "rb").read(), f"{fn} が 2_bin_track と違う"
            assert len(a) > 50
        q = json.load(open(os.path.join(res["raw"], "qc_report.json"), encoding="utf-8"))
        assert q["used_params"]["UNET"]["detection"]["input"] == {"mode": "bin", "preproc": [15, 4, 0]}
        ck_s = getattr(test_d_train_smoke, "ck_sign", None)
        if ck_s:
            out = os.path.join(td, "out_sign")
            with open(os.path.join(td, "sign.pt"), "wb") as fp:
                fp.write(ck_s)
            _track_settings(TRACK, frames, bgp, os.path.join(td, "sign.pt"), out)
            TRACK.PREPROC_FIXED = (40, 2, 1)          # ckpt の記録 (15, 4, 0) が優先される
            try:
                TRACK.main()
            finally:
                TRACK.PREPROC_FIXED = (15, 4, 0)
            q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
            assert q["used_params"]["UNET"]["detection"]["input"] == {"mode": "bin+sign", "preproc": [15, 4, 0]}
            assert q["used_params"]["preprocess"] == {"noise_cut": 15, "brightness": 4, "median": 0}


def test_f_tau_passes():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    with tempfile.TemporaryDirectory() as td:
        frames, bgp = _frames(td, 5)
        torch.manual_seed(2)
        m5 = widen(smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval(), "bin", True)
        with torch.no_grad():
            m5.encoder.conv1.weight[:, 3:] = torch.randn_like(m5.encoder.conv1.weight[:, 3:]) * 0.5
        ck5 = os.path.join(td, "tau5.pt")
        save_ckpt(ck5, m5, [96, 128])
        res = {}
        for name, M in (("bin", BIN), ("raw", TRACK)):
            out = os.path.join(td, "out_" + name)
            _track_settings(M, frames, bgp, ck5, out)
            M.PRIOR_PASSES = 2
            M.main()                                  # 事前マスクを入れるモデル -> 多パス (main_tau)
            res[name] = out
        for fn in ("result_tracking.csv", "result_area_count.csv", os.path.join("passes", "pass0", "result_tracking.csv")):
            a = open(os.path.join(res["bin"], fn), "rb").read()
            assert a == open(os.path.join(res["raw"], fn), "rb").read(), f"{fn} が 2_bin_track の TAU と違う"
        q = json.load(open(os.path.join(res["raw"], "qc_report.json"), encoding="utf-8"))
        assert q["used_params"]["TAU"]["uses_prior"] and q["used_params"]["TAU"]["input"]["mode"] == "bin"
        ck_p = getattr(test_d_train_smoke, "ck_prior", None)
        if ck_p:
            with open(os.path.join(td, "prior.pt"), "wb") as fp:
                fp.write(ck_p)
            out = os.path.join(td, "out_prior")
            _track_settings(TRACK, frames, bgp, os.path.join(td, "prior.pt"), out)
            TRACK.main()
            s = json.load(open(os.path.join(out, "pass_summary.json"), encoding="utf-8"))
            q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
            assert len(s) >= 1 and q["used_params"]["TAU"]["input"]["mode"] == "bin+sign"
            # PRIOR_PASSES = 0 なら 1回だけ (事前マスクは 0)
            TRACK.PRIOR_PASSES = 0
            try:
                out0 = os.path.join(td, "out_prior0")
                _track_settings(TRACK, frames, bgp, os.path.join(td, "prior.pt"), out0)
                TRACK.main()
                assert not os.path.exists(os.path.join(out0, "pass_summary.json"))
            finally:
                TRACK.PRIOR_PASSES = 2


def main() -> int:
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = []
    for n, f in tests:
        try:
            f()
            print(f"  OK    {n}")
        except Skip as e:
            print(f"  SKIP  {n}: {e}")
        except Exception as e:   # noqa: BLE001
            import traceback
            traceback.print_exc()
            print(f"  FAIL  {n}: {type(e).__name__}: {e}")
            failed.append(n)
    print(f"\n{len(tests) - len(failed)} / {len(tests)} 合格")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

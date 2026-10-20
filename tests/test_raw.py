"""
二値化しない版 (raw/1_raw_train.py, raw/2_raw_track.py) の回帰テスト
=====================================================================
  a) 2ファイルが tools/build_raw.py で作り直した内容と同じ (最新)
  b) bin_diff の B = 2_bin_track の前処理 (preprocess_image) の結果。D は Noise Cut を外しただけ
  c) RawDetector: 記録の無い 3ch ckpt = 2_bin_track の UNetDetector と完全に同じ確率 (学習サイズへの拡大縮小も)。
     best.pt から D の重みを 0 で足した 4ch ('bin+diff') は 3ch と同じ確率。チャンネル数が合わない ckpt は止まる
  d) 学習: Roboflow の名前 (_jpg.rf.<hash>) から背景を選び、3つの INPUT_MODE と OLD_BIN_SRC で最後まで動く。
     背景の決まらない画像があれば一覧を出して止まる。できた ckpt を RawDetector が記録どおりの入力で読む
  e) 2_raw_track の main_single: 記録の無い 3ch ckpt なら 2_bin_track の main_single と同じ CSV。
     学習した 'bin+diff' の ckpt でも最後まで動き、qc_report に入力の記録が残る

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
        B, D = TRACK.bin_diff(f, cv2.resize(bg, (64, 48)), (15, 4, 0))   # 背景の大きさが違えば合わせる
        assert B.shape == f.shape[:2]
    B, D = TRACK.bin_diff(f, bg, (15, 4, 0))
    inside = np.zeros(B.shape, bool)
    cv2.circle(inside.view(np.uint8), (40, 50), 11, 1, -1)
    assert B[inside].max() == 0 and np.median(D[inside]) >= 30, "D に気泡の中の薄い差が残っていない"
    x = TRACK.make_input_raw(B, D, "bin+diff", TRACK_MEAN, TRACK_STD)
    assert x.shape == (4,) + B.shape and x.dtype == np.float32
    assert TRACK.make_input_raw(B, D, "diff", TRACK_MEAN, TRACK_STD).shape[0] == 3
    try:
        TRACK.input_channels("raw")
        raise AssertionError("知らない INPUT_MODE で止まらない")
    except ValueError:
        pass


TRACK_MEAN = np.array((0.485, 0.456, 0.406), np.float32)
TRACK_STD = np.array((0.229, 0.224, 0.225), np.float32)


def save_ckpt(path, model, train_hw=None, inp=None, epoch=1):
    import torch
    ck = {"encoder": "resnet34", "classes": 3, "mean": (0.485, 0.456, 0.406), "std": (0.229, 0.224, 0.225),
          "train_hw": train_hw, "epoch": epoch, "state_dict": model.state_dict()}
    if inp is not None:
        ck["input"] = inp
    torch.save(ck, path)


def test_c_detector():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    TR = load(os.path.join(ROOT, "raw", "1_raw_train.py"), "raw_train_c")
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
            assert det.mode == "bin" and det.preproc == tuple(TRACK.PREPROC_FIXED)
            p = det.prob_raw(f, bg)
            assert p.shape == (3, 90, 120) and np.array_equal(p, p_ref), (hw, float(np.abs(p - p_ref).max()))
        m4 = TR.build_model("resnet34", 3, 4).eval()
        m4.load_state_dict(TR.expand_state_dict(m3.state_dict(), m4))
        ck4 = os.path.join(td, "b4.pt")
        save_ckpt(ck4, m4, None, {"mode": "bin+diff", "preproc": [15, 4, 0]})
        d4 = TRACK.RawDetector(ck4)
        assert d4.mode == "bin+diff"
        d = float(np.abs(d4.prob_raw(f, bg) - TRACK.RawDetector(os.path.join(td, "b3_None.pt")).prob_raw(f, bg)).max())
        assert d < 1e-5, d
        ckd = os.path.join(td, "d3.pt")
        save_ckpt(ckd, m3, None, {"mode": "diff", "preproc": [20, 3, 0]})
        dd = TRACK.RawDetector(ckd)
        _, D = TRACK.bin_diff(f, bg, (20, 3, 0))
        assert dd.preproc == (20, 3, 0) and np.array_equal(dd.prob_raw(f, bg), BIN.UNetDetector(ckd).prob(D))
        for bad, inp in ((m3, {"mode": "bin+diff"}), (m4, None)):
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
        cks = {}
        for mode, o in (("bin+diff", old), ("diff", None), ("bin", None)):
            _configure(TR, td, src, mode, base, o)
            TR.main()
            out = TR.resolve(TR.OUT)
            ck = torch.load(str(out / "best.pt"), map_location="cpu")
            assert ck["input"] == {"mode": mode, "preproc": [15, 4, 0]} and ck["in_channels"] == TR.input_channels(mode)
            assert ck["train_hw"] == [96, 128] and ck["n_train"] == 3 and ck["n_train_old"] == (2 if o else 0)
            rep = json.load(open(out / "test_report.json", encoding="utf-8"))
            assert len(rep["columns"]) == 2 and rep["input_mode"] == mode
            for col in rep["columns"].values():
                assert col["n_gt"] == 3
            log = json.load(open(out / "log.json"))
            assert len(log) == 1 and (("diff_w" in log[0]) == (mode == "bin+diff"))
            ds = TR.resolve(TR.DST)
            for sub in ("bin", "diff", "masks"):
                assert len(os.listdir(ds / sub / "train")) == 3 and len(os.listdir(ds / sub / "val")) == 1
                assert len(TR.list_images(ds / sub / "old")) == (2 if o else 0)
            cks[mode] = str(out / "best.pt")
            det = TRACK.RawDetector(cks[mode])
            assert det.mode == mode and det.preproc == (15, 4, 0) and det.train_hw == (96, 128)
        # 学習した 4ch から続けて学習 (開始モデルの列は ckpt の入力で評価)
        _configure(TR, td, src, "bin+diff", cks["bin+diff"], out="runs_b")
        TR.main()
        rep = json.load(open(TR.resolve(TR.OUT) / "test_report.json", encoding="utf-8"))
        assert list(rep["columns"])[0] == "開始モデル (bin+diff)"
        with open(cks["bin+diff"], "rb") as fp:          # e) で使う (この一時フォルダは消える)
            test_d_train_smoke.ck_bin_diff = fp.read()


# ==============================================================
# 検出・追跡
# ==============================================================
def _track_settings(M, frames, bg, ck, out):
    M.IMAGE_FOLDER, M.BACKGROUND_PATH, M.UNET_CKPT, M.OUTPUT_FOLDER = frames, bg, ck, out
    M.PREPROC_FIXED, M.ENABLE_BOOTSTRAP, M.ENABLE_ROI = (15, 4, 0), False, False


def test_e_track_end_to_end():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    with tempfile.TemporaryDirectory() as td:
        frames = os.path.join(td, "frames")
        os.makedirs(frames)
        for k in range(4):
            f, bg, _ = frame_pair(seed=10 + k, shift=3 * k)
            cv2.imwrite(os.path.join(frames, f"img{k:04d}.png"), f)
        bgp = os.path.join(td, "bg.png")
        cv2.imwrite(bgp, bg)
        torch.manual_seed(1)
        ck = os.path.join(td, "best.pt")
        save_ckpt(ck, smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3), [96, 128])
        res = {}
        for name, M in (("bin", BIN), ("raw", TRACK)):
            out = os.path.join(td, "out_" + name)
            _track_settings(M, frames, bgp, ck, out)
            M.main_single()
            res[name] = out
        for fn in ("result_tracking.csv", "result_area_count.csv"):
            a = open(os.path.join(res["bin"], fn), "rb").read()
            assert a == open(os.path.join(res["raw"], fn), "rb").read(), f"{fn} が 2_bin_track と違う"
            assert len(a) > 50
        q = json.load(open(os.path.join(res["raw"], "qc_report.json"), encoding="utf-8"))
        assert q["used_params"]["UNET"]["detection"]["input"] == {"mode": "bin", "preproc": [15, 4, 0]}
        ck_bd = getattr(test_d_train_smoke, "ck_bin_diff", None)
        if ck_bd:
            out = os.path.join(td, "out_bd")
            with open(os.path.join(td, "bd.pt"), "wb") as fp:
                fp.write(ck_bd)
            _track_settings(TRACK, frames, bgp, os.path.join(td, "bd.pt"), out)
            TRACK.PREPROC_FIXED = (40, 2, 1)          # ckpt の記録 (15, 4, 0) が優先される
            try:
                TRACK.main_single()
            finally:
                TRACK.PREPROC_FIXED = (15, 4, 0)
            q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
            assert q["used_params"]["UNET"]["detection"]["input"] == {"mode": "bin+diff", "preproc": [15, 4, 0]}
            assert q["used_params"]["preprocess"] == {"noise_cut": 15, "brightness": 4, "median": 0}


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

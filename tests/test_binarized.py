"""
binarized/ (二値化画像版) の起動部分のテスト
=====================================================================
binarized/1_bin_train.py, 2_bin_track.py は元は tools/build_binarized.py が old/ のモジュールからまとめたもの。
今はこの 2ファイルを直接直す (中身の回帰テストは test_events / test_instances / test_tau / test_dots が tests/bundles.py
経由でこの 2ファイルを読んで行う)。ここでは 1ファイル版にしかない起動部分を確かめる:
  d) 1_bin_train.py の STEP: 'dots' の結果を 'train' が自動で使う
  e) 2_bin_track.py の起動: 3チャンネルのモデル -> main_single (元 watershed.py)、5チャンネル -> main_tau (元 tau_tracker.py)
  f) 1_bin_train.py と 2_bin_track.py に同じ名前で入っている部品 (TAU の部品・モデルの読み込み) が同じ中身
     (元は tau_unet.py 1つ。今は 2ファイルを直接直すので、片方だけ直すと学習と検出で食い違う)

使い方: リポジトリのルートで  python -B tests/test_binarized.py     (pytest でも実行できる)
"""
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bundles   # noqa: E402

TRAIN = bundles.TRAIN_PATH
TRACK = bundles.TRACK_PATH


class Skip(Exception):
    pass


def need_torch():
    try:
        import torch  # noqa: F401
        import segmentation_models_pytorch  # noqa: F401
    except ImportError as e:
        raise Skip(f"torch / segmentation_models_pytorch なし ({e})")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_d_train_steps():
    need_torch()
    import torch
    import test_dots as TD
    from test_tau import save_fake_ckpt
    TB = load(TRAIN, "bin_train2")
    with tempfile.TemporaryDirectory() as td:
        src = TD.make_src(td)
        TB.SRC, TB.DOT_OUT, TB.DOT_REVIEW, TB.STEP = src, os.path.join(td, "dots"), False, "dots"
        TB.main()
        assert os.path.exists(os.path.join(td, "dots", "coco", "train", "_annotations.coco.json"))
        assert os.path.isdir(os.path.join(td, "dots", "ignore", "train"))
        ck = os.path.join(td, "start.pt")
        save_fake_ckpt(ck, [TD.H0, TD.W0])
        TB.STEP, TB.USE_DOT_LABELS, TB.FINETUNE_FROM = "train", True, ck
        TB.DST, TB.OUT = os.path.join(td, "ds"), os.path.join(td, "runs", "r")
        TB.FINETUNE_EPOCHS, TB.BS, TB.CROP, TB.CP_SAVE_PREVIEW = 1, 1, (96, 128), 0
        TB.main()
        best = torch.load(os.path.join(td, "runs", "r", "best.pt"), map_location="cpu")
        assert best["src"].endswith("coco") and best["ignore_src"].endswith("ignore")
        assert best["in_channels"] == 3                     # USE_PRIOR の既定値は False
        TB.STEP = "nope"
        try:
            TB.main()
            raise AssertionError("STEP の綴りの間違いで止まらない")
        except ValueError:
            pass


def test_e_track_dispatch():
    need_torch()
    import torch
    from test_tau import save_fake_ckpt
    B = load(TRACK, "bin_track_disp")
    with tempfile.TemporaryDirectory() as td:
        ck3 = os.path.join(td, "c3.pt")
        save_fake_ckpt(ck3, [96, 128])
        model, ck, _ = B.load_tau_model(ck3, "cpu", force_prior=True)
        ck5 = os.path.join(td, "c5.pt")
        torch.save(dict(ck, state_dict=model.state_dict(), in_channels=5, tau=True), ck5)
        called = []
        B.main_single = lambda: called.append("single")
        B.main_tau = lambda: called.append("tau")
        for path, passes, want in ((ck3, 2, "single"), (ck5, 2, "tau"), (ck5, 0, "tau"), (ck3, 0, "single")):
            B.UNET_CKPT, B.PRIOR_PASSES = path, passes
            B.main()
            assert called[-1] == want, f"{os.path.basename(path)}, PRIOR_PASSES={passes}: {called[-1]} (期待 {want})"



SHARED_DIFFER = {"main", "extract_instances", "HERE"}   # 2ファイルで中身が違ってよいもの (意図した違い)


def _top_defs(path):
    import ast
    text = open(path, encoding="utf-8").read()
    out = {}
    for n in ast.parse(text).body:
        names = [n.name] if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else \
            [t.id for t in getattr(n, "targets", []) if isinstance(t, ast.Name)]
        for name in names:
            out[name] = ast.get_source_segment(text, n)
    return out


def test_f_shared_parts_same():
    a, b = _top_defs(TRAIN), _top_defs(TRACK)
    shared = sorted(set(a) & set(b) - SHARED_DIFFER)
    for must in ("synth_prior", "PriorAug", "degrade_image", "render_prior", "expand_state_dict", "build_model",
                 "TauDetector", "load_tau_model", "make_input", "PRIOR_EDGE_PX", "PRIOR_CHANNELS", "IMAGE_CHANNELS"):
        assert must in shared, f"{must} が両方に無い (部品の名前が変わった?)"
    diff = [n for n in shared if a[n] != b[n]]
    assert not diff, f"1_bin_train.py と 2_bin_track.py で中身が違う部品: {diff} (両方を同じに直す)"

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

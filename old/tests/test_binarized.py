"""
二値化画像版の 2ファイル (binarized/1_bin_train.py, binarized/2_bin_track.py) の回帰テスト
=====================================================================
binarized/ の 2ファイルは tools/build_binarized.py が元のモジュールからまとめたもの。中身が元と同じであることを確かめる。
  a) 最新か: 今の元ファイルから作り直した内容と同じ
  b) 2_bin_track.py を tracker3 / piv_field / tau_unet / tau_tracker として読み込ませ、元のテスト
     (test_events, test_instances, test_tau) がそのまま通る
  c) 1_bin_train.py の点の候補・書き出しが dot_labels.py と同じ。学習 (TAU / 3チャンネル + ignore) の結果の重みが
     1_tau_unet_train.py と同じ
  d) 1_bin_train.py の STEP: 'dots' の結果を 'train' が自動で使う
  e) 2_bin_track.py の起動: 3チャンネルのモデル -> main_single (元 watershed.py)、5チャンネル -> main_tau (元 tau_tracker.py)

使い方: リポジトリのルートで  python -B tests/test_binarized.py     (pytest でも実行できる)
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

TRAIN = os.path.join(ROOT, "binarized", "1_bin_train.py")
TRACK = os.path.join(ROOT, "binarized", "2_bin_track.py")


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


def test_a_up_to_date():
    import build_binarized as B
    for name, text in B.build_all().items():
        with open(os.path.join(ROOT, "binarized", name), encoding="utf-8") as f:
            assert f.read() == text, f"binarized/{name} が古い (python tools/build_binarized.py で作り直す)"


RUNNER = r"""
import importlib, runpy, sys
sys.path.insert(0, {bindir!r})
B = importlib.import_module("2_bin_track")      # 名前で import する (テストの importlib.reload が見つけられるように)
for n in ("tracker3", "piv_field", "tau_unet", "tau_tracker", "watershed"):
    sys.modules[n] = B
sys.path.insert(0, {tests!r})
sys.path.insert(0, {root!r})
sys.argv = [{test!r}]
runpy.run_path({test!r}, run_name="__main__")
"""


def _run_suite(test_name):
    test = os.path.join(ROOT, "tests", test_name)
    code = RUNNER.format(bindir=os.path.dirname(TRACK), tests=os.path.join(ROOT, "tests"), root=ROOT, test=test)
    r = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=1800)
    tail = "\n".join((r.stdout + r.stderr).splitlines()[-15:])
    assert r.returncode == 0, f"{test_name} が 2_bin_track.py では通らない:\n{tail}"
    return tail


def test_b_track_runs_original_suites():
    for t in ("test_events.py", "test_instances.py"):
        _run_suite(t)
    try:
        import torch  # noqa: F401
    except ImportError:
        return
    _run_suite("test_tau.py")


def _dirs_equal(a, b, skip=("export_summary.json",)):
    fa = sorted(os.path.relpath(os.path.join(r, f), a) for r, _, fs in os.walk(a) for f in fs)
    fb = sorted(os.path.relpath(os.path.join(r, f), b) for r, _, fs in os.walk(b) for f in fs)
    assert fa == fb, f"ファイルの一覧が違う: {set(fa) ^ set(fb)}"
    for f in fa:
        if os.path.basename(f) in skip:
            continue
        with open(os.path.join(a, f), "rb") as x, open(os.path.join(b, f), "rb") as y:
            assert x.read() == y.read(), f"{f} の中身が違う"


def test_c_train_same_as_original():
    import dot_labels as DL
    import test_dots as TD
    TB = load(TRAIN, "bin_train")
    g, anns, _ = TD.scene()
    lm = DL.labelled_mask(anns, *g.shape)
    a = DL.find_candidates(g, lm, "train", "img0.png")
    b = TB.find_candidates(g, lm, "train", "img0.png")
    assert [c.id for c in a] == [c.id for c in b] and all((x.mask == y.mask).all() for x, y in zip(a, b))
    with tempfile.TemporaryDirectory() as td:
        src = TD.make_src(td)
        ca, ka = DL.scan(src, ["test", "valid", "train"])
        cb, kb = TB.scan(src, ["test", "valid", "train"])
        dec = {ca[0].id: "y", ca[1].id: "n", ca[2].id: "u", ca[5].id: "y"}
        DL.export(src, os.path.join(td, "o1"), ca, ka, dec)
        TB.export(src, os.path.join(td, "o2"), cb, kb, dec)
        _dirs_equal(os.path.join(td, "o1"), os.path.join(td, "o2"))

    need_torch()
    import torch
    from test_tau import save_fake_ckpt
    M = TD.load_train_module()
    for use_prior, with_ignore in ((True, False), (False, True)):
        with tempfile.TemporaryDirectory() as td:
            src = TD.make_src(td)
            cands, cocos = DL.scan(src, ["test", "valid", "train"])
            DL.export(src, os.path.join(td, "dots"), cands, cocos, {})
            ck = os.path.join(td, "start.pt")
            save_fake_ckpt(ck, [TD.H0, TD.W0])
            outs = []
            for k, mod in enumerate((M, TB)):
                mod.SRC = os.path.join(td, "dots", "coco")
                mod.IGNORE_SRC = os.path.join(td, "dots", "ignore") if with_ignore else None
                mod.USE_PRIOR, mod.FINETUNE_FROM = use_prior, ck
                mod.DST, mod.OUT = os.path.join(td, f"ds{k}"), os.path.join(td, f"runs{k}", "r")
                mod.FINETUNE_EPOCHS, mod.BS, mod.CROP, mod.CP_SAVE_PREVIEW = 1, 1, (96, 128), 0
                (mod.main_train if mod is TB else mod.main)()
                outs.append(os.path.join(td, f"runs{k}", "r"))
            b0 = torch.load(os.path.join(outs[0], "best.pt"), map_location="cpu")
            b1 = torch.load(os.path.join(outs[1], "best.pt"), map_location="cpu")
            assert b0["epoch"] == b1["epoch"] and b0["in_channels"] == b1["in_channels"]
            for kk, v in b0["state_dict"].items():
                assert torch.equal(v, b1["state_dict"][kk]), f"USE_PRIOR={use_prior}: 重み {kk} が元と違う"
            l0 = json.load(open(os.path.join(outs[0], "log.json")))
            l1 = json.load(open(os.path.join(outs[1], "log.json")))
            assert l0 == l1, f"USE_PRIOR={use_prior}: log.json が元と違う"
            r0 = json.load(open(os.path.join(outs[0], "test_report.json")))
            r1 = json.load(open(os.path.join(outs[1], "test_report.json")))
            for r in (r0, r1):
                for col in r["columns"].values():
                    col.pop("ckpt")
            assert r0 == r1, f"USE_PRIOR={use_prior}: test_report.json が元と違う"


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
        for path, passes, want in ((ck3, 2, "single"), (ck5, 2, "tau"), (ck5, 0, "single")):
            B.UNET_CKPT, B.PRIOR_PASSES = path, passes
            B.main()
            assert called[-1] == want, f"{os.path.basename(path)}, PRIOR_PASSES={passes}: {called[-1]} (期待 {want})"


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

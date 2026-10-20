"""
ラベルの下書き (binarized/0_prelabel.py) の回帰テスト
=====================================================================
  a) 気泡ラベルマップ -> ポリゴン: 点を減らさなければ fillPoly + polylines で元のマスクに戻る (L 字・線・画面端も)。
     減らしても形はほぼ同じ (IoU >= 0.95) で点は減る
  b) grow_instances: 背景にだけ広がり、ほかの気泡には入らない
  c) 元画像 + 背景画像 -> main が最後まで動き、COCO を学習スクリプトの読み込み (load_coco) が読める (raw / binarized)

使い方: リポジトリのルートで  python -B tests/test_prelabel.py     (pytest でも実行できる)
"""
import importlib.util
import json
import os
import sys
import tempfile

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)


class Skip(Exception):
    pass


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PL = load(os.path.join(ROOT, "binarized", "0_prelabel.py"), "prelabel")


def _scene():
    inst = np.zeros((80, 120), np.int32)
    cv2.circle(inst, (20, 20), 9, 1, -1)
    inst[50:70, 5:15] = 2
    inst[60:70, 5:40] = 2                       # L 字
    inst[10, 60:75] = 3                         # 1px の線
    cv2.circle(inst, (118, 40), 12, 4, -1)      # 画面の右端で切れた気泡
    inst[30:33, 90:93] = 5                      # 小さい点 (9px)
    inst[75, 100] = 6                           # 1px (MIN_AREA 未満)
    return inst


def _render(polys, shape):
    m = np.zeros(shape, np.uint8)
    for p in polys:
        q = np.array(p, np.float32).reshape(-1, 2).astype(np.int32)
        cv2.fillPoly(m, [q], 1)
        cv2.polylines(m, [q], True, 1, 1)
    return m > 0


def test_a_polygons():
    inst = _scene()
    anns = PL.instances_to_annotations(inst, 0, 1, min_area=5, simplify=0)
    assert [a["id"] for a in anns] == [1, 2, 3, 4, 5], "1px の検出が除かれていない / 番号が違う"
    for k, a in zip((1, 2, 3, 4, 5), anns):
        assert (_render(a["segmentation"], inst.shape) == (inst == k)).all(), f"気泡 {k} のポリゴンが元に戻らない"
        assert a["area"] == (inst == k).sum()
    big = np.zeros((300, 300), np.int32)
    cv2.ellipse(big, (150, 150), (120, 70), 20, 0, 360, 1, -1)
    full = PL.instances_to_annotations(big, 0, 1, simplify=0)[0]
    simp = PL.instances_to_annotations(big, 0, 1, simplify=0.7)[0]
    r = _render(simp["segmentation"], big.shape)
    iou = (r & (big == 1)).sum() / (r | (big == 1)).sum()
    assert len(simp["segmentation"][0]) < len(full["segmentation"][0]) / 3 and iou >= 0.95, (len(simp["segmentation"][0]), iou)
    small = PL.instances_to_annotations(inst, 0, 1, simplify=0.7)
    assert small[4]["segmentation"] == anns[4]["segmentation"], "小さい点の点まで減らしている"


def test_b_grow():
    inst = np.zeros((40, 40), np.int32)
    inst[10:20, 10:20] = 1
    inst[10:20, 21:30] = 2                      # 1px の隙間
    g = PL.grow_instances(inst, 1)
    assert (g[inst > 0] == inst[inst > 0]).all(), "既にある気泡の画素が変わった"
    assert g[9, 15] == 1 and g[15, 30] == 2 and g[15, 20] in (1, 2)
    assert (g == 1).sum() > (inst == 1).sum() and g[0, 0] == 0
    assert (PL.grow_instances(inst, 0) == inst).all()


def test_c_main_end_to_end():
    try:
        import torch  # noqa: F401
        import segmentation_models_pytorch  # noqa: F401
    except ImportError as e:
        raise Skip(f"torch なし ({e})")
    from test_tau import save_fake_ckpt
    spec = importlib.util.spec_from_file_location("tau_train_pl", os.path.join(ROOT, "1_tau_unet_train.py"))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with tempfile.TemporaryDirectory() as td:
        raw_dir = os.path.join(td, "raw")
        os.makedirs(raw_dir)
        bg = np.full((96, 128, 3), 220, np.uint8)
        cv2.imwrite(os.path.join(td, "bg.png"), bg)
        for i in range(2):
            f = bg.copy()
            cv2.circle(f, (40 + 10 * i, 50), 15, (120, 120, 120), 2)
            cv2.circle(f, (100, 30), 5, (120, 120, 120), 1)
            cv2.imwrite(os.path.join(raw_dir, f"frame{i}.png"), f)
        ck = os.path.join(td, "best.pt")
        save_fake_ckpt(ck, [96, 128])
        for mode in ("raw", "binarized"):
            PL.IMAGE_FOLDER, PL.BACKGROUND_PATH, PL.UNET_CKPT = raw_dir, os.path.join(td, "bg.png"), ck
            PL.OUT_FOLDER, PL.EXPORT_IMAGE = os.path.join(td, f"out_{mode}"), mode
            PL.main()
            out = os.path.join(td, f"out_{mode}")
            d = json.load(open(os.path.join(out, PL.ANN_NAME)))
            assert len(d["images"]) == 2 and d["categories"][0]["name"] == PL.CLASS_NAME
            for im in d["images"]:
                assert os.path.exists(os.path.join(out, im["file_name"]))
                assert (im["height"], im["width"]) == (96, 128)
            assert len(os.listdir(os.path.join(out, "preview"))) == 2
            images, by_img = M.load_coco(os.path.join(out, PL.ANN_NAME))   # 学習スクリプトがそのまま読める
            assert len(images) == 2 and sum(len(v) for v in by_img.values()) == len(d["annotations"])
        PL.OUT_FOLDER = raw_dir
        try:
            PL.main()
            raise AssertionError("OUT_FOLDER = IMAGE_FOLDER で止まらない")
        except ValueError:
            pass
        assert len(os.listdir(raw_dir)) == 2, "IMAGE_FOLDER が消された"


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

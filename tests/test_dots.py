"""
小さい点のラベル補充 (dot_labels.py) と、学習スクリプトの IGNORE_SRC / USE_PRIOR = False の回帰テスト
=====================================================================
  a) 候補: ラベルのない点・輪・C 字の輪だけが候補になる (ラベル済みの気泡とその近く・小さすぎ・暗すぎ・大きすぎは除く)
  b) 「気泡」にした点のポリゴンを 1_tau_unet_train.py の変換 (make_target) に通すと元のマスクに戻る
  c) 書き出し: y はラベルに追加、u と未確認は ignore、n は何もしない。学習用データセットでは ignore が 255 になり、
     ラベル済みの気泡の画素は ignore にならない
  d) 損失と評価: 学習しない画素は損失の勾配が 0、画素 IoU にも数えない。無い場合の Dice は今までと同じ値
  e) USE_PRIOR = False + IGNORE_SRC で学習スクリプトが最後まで動き、best.pt を tracker3.UNetDetector が読める
  f) 確認画面の状態 (クリック・Enter・戻る) と、タイルの位置の計算 (GUI なし)
  g) 判定の保存と、探し直しても同じ候補なら同じ名前

使い方: リポジトリのルートで  python -B tests/test_dots.py     (pytest でも実行できる)
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

import dot_labels as DL   # noqa: E402


class Skip(Exception):
    pass


def need_torch():
    try:
        import torch  # noqa: F401
        import segmentation_models_pytorch  # noqa: F401
    except ImportError as e:
        raise Skip(f"torch / segmentation_models_pytorch なし ({e})")


def load_train_module():
    spec = importlib.util.spec_from_file_location("tau_train_dots", os.path.join(ROOT, "1_tau_unet_train.py"))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def circle_poly(cx, cy, r, n=24):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1).ravel().tolist()


# ==============================================================
# 合成の学習画像 (二値化済みの見た目: 背景 0, 光る所 60〜255)
# ==============================================================
H0, W0 = 120, 160


def scene():
    """(画像, ラベル済みの注釈, 候補になるはずの点の中心 {名前: (x, y)})"""
    g = np.zeros((H0, W0), np.uint8)
    anns = []
    cv2.circle(g, (40, 40), 12, 220, 2)                       # ラベル済みの気泡 (輪)
    anns.append({"id": 1, "image_id": 0, "category_id": 1, "segmentation": [circle_poly(40, 40, 13.5)],
                 "bbox": [26, 26, 28, 28]})
    g[40, 55:58] = 200                                         # ラベル済みの気泡の 2px 以内の切れ端 (候補にしない)
    g[39:41, 54:56] = 200
    g[80:83, 20:23] = 200                                      # ラベルのない点 (9px)
    cv2.circle(g, (70, 90), 4, 180, 1)                         # ラベルのない小さい輪 (穴あり)
    cv2.ellipse(g, (110, 30), (5, 5), 0, 20, 340, 160, 1)      # ラベルのない C 字の輪 (切れ目あり)
    g[100, 100:103] = 255                                      # 小さすぎるノイズ (3px)
    g[60:63, 120:123] = 40                                     # 暗い塊 (CAND_PEAK 未満)
    g[5:35, 125:155] = 200                                     # 大きすぎる塊 (900px)
    g[110:113, 60:63] = 20                                     # JPEG のにじみ程度 (光っていない)
    expect = {"dot": (21, 81), "ring": (70, 90), "c_ring": (110, 30)}
    return g, anns, expect


def _center(c):
    ys, xs = np.nonzero(c.mask)
    return xs.mean() + c.x0, ys.mean() + c.y0


def test_a_candidates():
    g, anns, expect = scene()
    lm = DL.labelled_mask(anns, *g.shape)
    cs = DL.find_candidates(g, lm, "train", "img0.png")
    found = {}
    for c in cs:
        cx, cy = _center(c)
        name = [k for k, (x, y) in expect.items() if abs(cx - x) <= 2 and abs(cy - y) <= 2]
        assert len(name) == 1, f"想定外の候補: 中心 ({cx:.1f}, {cy:.1f}) 面積 {c.area}"
        found[name[0]] = c
    assert set(found) == set(expect), f"見つからない候補: {set(expect) - set(found)}"
    assert found["dot"].area == 9 and not found["dot"].ring
    assert found["ring"].ring and found["ring"].area > found["ring"].lit       # 穴を埋めた
    assert found["c_ring"].ring and found["c_ring"].area > found["c_ring"].lit   # 切れ目を埋めた
    disk = np.zeros((H0, W0), np.uint8)
    cv2.circle(disk, (70, 90), 4, 1, -1)
    full = np.zeros((H0, W0), bool)
    r = found["ring"]
    full[r.y0:r.y0 + r.mask.shape[0], r.x0:r.x0 + r.mask.shape[1]] = r.mask
    assert (full == (disk > 0)).all(), "輪の候補のマスクが塗りつぶした円と違う"


def test_b_polygon_roundtrip():
    M = load_train_module()
    rng = np.random.default_rng(1)
    shapes = [np.ones((3, 3), bool), np.ones((1, 5), bool), np.ones((6, 1), bool), np.eye(5, dtype=bool),
              np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)]
    for _ in range(40):
        h, w = rng.integers(2, 14, 2)
        m = rng.random((h, w)) < 0.6
        n, lab = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
        if n < 2:
            continue
        sizes = np.bincount(lab.ravel())[1:]
        m = DL.fill_dot(lab == 1 + int(np.argmax(sizes)))
        ys, xs = np.nonzero(m)
        shapes.append(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    H, W = 40, 50
    for k, m in enumerate(shapes):
        for x0, y0, gr in ((10, 12, 0), (0, 0, 0), (W - m.shape[1], H - m.shape[0], 0), (10, 12, 1)):
            mm, gx, gy = DL.grow(m, x0, y0, gr, H, W)
            poly = DL.mask_to_polygon(mm, gx, gy)
            xs, ys = poly[0::2], poly[1::2]
            bw, bh = max(xs) - min(xs), max(ys) - min(ys)            # 書き出しの bbox と同じ
            lbl, _ = M.make_target([([np.array(poly, np.float32).reshape(-1, 2)], bw, bh)], H, W, 4)
            want = np.zeros((H, W), bool)
            want[gy:gy + mm.shape[0], gx:gx + mm.shape[1]] = mm
            got = lbl > 0
            if M.edge_thickness(bw, bh, 4) == 1:     # 小さい点: 元のマスクにちょうど戻る
                assert (got == want).all(), f"形 {k} (位置 {x0},{y0}, 広げる {gr}) のポリゴンが元のマスクに戻らない"
            else:   # 境界線が太い (3〜4px) ので、ユーザーのラベルと同じく線の外側半分だけ広がる
                outer = cv2.dilate(want.astype(np.uint8), DL._disk(2)) > 0
                assert (got >= want).all() and (got <= outer).all(), f"形 {k}: 元のマスクより欠けた / 広がりすぎた"


def make_src(td, with_test_ignore_overlap=False):
    """Roboflow の書き出しの形: <split>/画像 + _annotations.coco.json"""
    src = os.path.join(td, "coco_src")
    for split in ("train", "valid", "test"):
        os.makedirs(os.path.join(src, split))
        g, anns, _ = scene()
        images = [{"id": 0, "file_name": "img0.png", "height": H0, "width": W0}]
        cv2.imwrite(os.path.join(src, split, "img0.png"), g)
        with open(os.path.join(src, split, DL.ANN_NAME), "w") as fp:
            json.dump({"images": images, "annotations": anns, "categories": [{"id": 0, "name": "bubbles"},
                                                                             {"id": 1, "name": "bubble"}]}, fp)
    return src


def test_c_export_and_dataset():
    M = load_train_module()
    with tempfile.TemporaryDirectory() as td:
        src = make_src(td)
        out = os.path.join(td, "dots")
        cands, cocos = DL.scan(src, ["test", "valid", "train"])
        assert len(cands) == 9
        by = {}
        for c in cands:
            cx, cy = _center(c)
            by[(c.split, "dot" if abs(cx - 21) <= 2 else ("ring" if abs(cx - 70) <= 2 else "c_ring"))] = c
        dec = {by[("train", "dot")].id: "y", by[("train", "ring")].id: "n", by[("train", "c_ring")].id: "u"}
        summ = DL.export(src, out, cands, cocos, dec)
        assert summ["train"] == {"y": 1, "n": 1, "u": 1, "ignore_images": 1}
        assert summ["test"] == {"unchecked": 3, "ignore_images": 1}
        d = json.load(open(os.path.join(out, "coco", "train", DL.ANN_NAME)))
        assert len(d["annotations"]) == 2 and d["annotations"][1]["source"] == "dot_labels"
        assert d["annotations"][1]["category_id"] == 1 and d["annotations"][1]["id"] == 2
        assert os.path.exists(os.path.join(out, "coco", "train", "img0.png"))
        ign = cv2.imread(os.path.join(out, "ignore", "train", "img0.png"), cv2.IMREAD_GRAYSCALE)
        assert ign[30, 110] == 255 or ign[25, 110] == 255   # u の C 字の輪
        assert ign[90, 70] == 0 and ign[81, 21] == 0        # n と y は無視しない
        ign_t = cv2.imread(os.path.join(out, "ignore", "test", "img0.png"), cv2.IMREAD_GRAYSCALE)
        assert ign_t[81, 21] == 255 and ign_t[90, 70] == 255   # 未確認は無視
        # ラベル済みの気泡に掛かる ignore を足しても、気泡の画素は ignore にならない
        ign_t[22:58, 22:58] = 255
        cv2.imwrite(os.path.join(out, "ignore", "test", "img0.png"), ign_t)
        dst = os.path.join(td, "ds")
        M.build_dataset(os.path.join(out, "coco"), dst, 4, 0, os.path.join(out, "ignore"))
        m_tr = cv2.imread(os.path.join(dst, "masks", "train", "img0.png"), cv2.IMREAD_GRAYSCALE)
        assert m_tr[81, 21] in (1, 2), "y の点がラベルになっていない"
        assert m_tr[90, 70] == 0, "n の輪は背景のまま"
        assert (m_tr == M.IGNORE_LABEL).any()
        m_te = cv2.imread(os.path.join(dst, "masks", "test", "img0.png"), cv2.IMREAD_GRAYSCALE)
        lab, _ = M.make_target([([np.array(circle_poly(40, 40, 13.5), np.float32).reshape(-1, 2)], 28, 28)],
                               H0, W0, 4)
        assert (m_te[lab > 0] != M.IGNORE_LABEL).all(), "ラベル済みの気泡の画素が ignore になった"
        assert m_te[23, 23] == M.IGNORE_LABEL                  # 気泡の外の背景は ignore
        assert m_te[81, 21] == M.IGNORE_LABEL


def test_d_ignore_in_loss_and_eval():
    need_torch()
    import torch
    M = load_train_module()
    torch.manual_seed(0)
    lg = torch.randn(2, 3, 16, 16, requires_grad=True)
    y = torch.randint(0, 3, (2, 16, 16))
    dice_new = M.make_dice()
    import segmentation_models_pytorch as smp
    assert torch.allclose(dice_new(lg, y), smp.losses.DiceLoss(mode="multiclass")(lg, y)), \
        "学習しない画素が無いのに Dice の値が今までと違う"
    w = torch.tensor([1.0, 1.0, 6.0])
    ce_new = torch.nn.CrossEntropyLoss(weight=w, ignore_index=M.IGNORE_LABEL)
    assert torch.allclose(ce_new(lg, y), torch.nn.CrossEntropyLoss(weight=w)(lg, y))
    y2 = y.clone()
    y2[:, 4:9, 4:9] = M.IGNORE_LABEL
    loss = ce_new(lg, y2) + dice_new(lg, y2)
    loss.backward()
    g = lg.grad
    assert g[:, :, 4:9, 4:9].abs().max() == 0, "学習しない画素に勾配が流れている"
    assert g.abs().sum() > 0

    class Fixed(torch.nn.Module):
        def forward(self, x):
            out = torch.zeros(x.shape[0], 3, x.shape[2], x.shape[3])
            out[:, 1] = 1.0                       # 全部「内部」
            return out
    x = torch.zeros(1, 3, 4, 4)
    yy = torch.zeros(1, 4, 4, dtype=torch.long)
    yy[0, :2] = 1
    yy[0, 2:] = M.IGNORE_LABEL                    # 背景の行を学習しない
    ev = M.evaluate(Fixed(), [(x, yy)], "cpu")
    assert abs(ev["iou"][1] - 1.0) < 1e-6, f"学習しない画素を数えている: {ev['iou']}"


def test_e_train_3ch_with_ignore():
    need_torch()
    import torch
    from test_tau import save_fake_ckpt
    import tracker3
    M = load_train_module()
    with tempfile.TemporaryDirectory() as td:
        src = make_src(td)
        for split in ("train",):                               # train を 2枚に (BS=2)
            d = json.load(open(os.path.join(src, split, DL.ANN_NAME)))
            g = cv2.imread(os.path.join(src, split, "img0.png"), cv2.IMREAD_GRAYSCALE)
            cv2.imwrite(os.path.join(src, split, "img1.png"), g[:, ::-1])
            d["images"].append({"id": 1, "file_name": "img1.png", "height": H0, "width": W0})
            json.dump(d, open(os.path.join(src, split, DL.ANN_NAME), "w"))
        out = os.path.join(td, "dots")
        cands, cocos = DL.scan(src, ["test", "valid", "train"])
        DL.export(src, out, cands, cocos, {})
        ck = os.path.join(td, "best.pt")
        save_fake_ckpt(ck, [H0, W0])
        M.SRC, M.DST, M.OUT, M.FINETUNE_FROM = (os.path.join(out, "coco"), os.path.join(td, "ds"),
                                                os.path.join(td, "runs", "u"), ck)
        M.IGNORE_SRC, M.USE_PRIOR = os.path.join(out, "ignore"), False
        M.FINETUNE_EPOCHS, M.BS, M.CROP, M.CP_SAVE_PREVIEW = 1, 2, (96, 128), 1
        M.main()
        best_p = os.path.join(td, "runs", "u", "best.pt")
        best = torch.load(best_p, map_location="cpu")
        assert best["in_channels"] == 3 and not best["tau"] and best["ignore_src"]
        assert best["state_dict"]["encoder.conv1.weight"].shape[1] == 3
        assert os.path.exists(os.path.join(td, "runs", "u", "test_report.json"))
        ds = M.BubbleDS(os.path.join(td, "ds"), "train", 96, 128, train=True)
        x, y = ds[0]
        assert x.shape[0] == 3 and (y == M.IGNORE_LABEL).any()
        det = tracker3.UNetDetector(best_p)
        p = det.prob(np.zeros((H0, W0), np.uint8))
        assert p.shape == (3, H0, W0)


def _fake_cands(n):
    out = []
    for k in range(n):
        out.append(DL.Cand("train", f"img{k // 7}.png", 10 + 5 * (k % 7), 10, np.ones((3, 3), bool), 9, 200, False))
    return out


def test_f_review_state():
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "train"))
        for k in range(4):
            cv2.imwrite(os.path.join(td, "train", f"img{k}.png"), np.zeros((60, 80), np.uint8))
        cs = _fake_cands(25)
        rv = DL.Review(cs, {}, td, grid=(4, 3), tile=60, min_crop=21)
        assert rv.n_pages == 3 and rv.page == 0
        rv.click(0, "left")
        rv.click(1, "right")
        rv.click(2, "left")
        rv.click(2, "left")                       # 取り消し
        assert rv.dec == {cs[0].id: "n", cs[1].id: "u"}
        assert rv.confirm() is False and rv.page == 1
        assert rv.dec[cs[2].id] == "y" and rv.dec[cs[11].id] == "y" and cs[12].id not in rv.dec
        rv.back()
        assert rv.page == 0
        rv.click(0, "left")                       # n -> 未確認に戻す
        assert cs[0].id not in rv.dec
        rv.page = 2
        assert rv.confirm() is True               # 最後のページ
        assert DL.Review(cs, rv.dec, td, grid=(4, 3), tile=60, min_crop=21).page == 0   # cs[0] が未確認
        img = rv.render()
        assert img.shape == (DL.BAR_H + 3 * 62 - 2, 4 * 62 - 2, 3)
        for k in range(12):
            r, q = divmod(k, 4)
            assert rv.tile_at(q * 62 + 30, DL.BAR_H + r * 62 + 30) == k
        assert rv.tile_at(10, 10) == -1 and rv.tile_at(61, DL.BAR_H + 5) == -1


def test_g_decisions_and_ids():
    g, anns, _ = scene()
    lm = DL.labelled_mask(anns, *g.shape)
    a = DL.find_candidates(g, lm, "train", "img0.png")
    b = DL.find_candidates(g, lm, "train", "img0.png", min_area=6)   # 条件を変えて探し直す
    assert {c.id for c in b} <= {c.id for c in a}
    g2 = g.copy()
    g2[83, 21] = 200                                                  # 点の形が変わる -> 別の名前
    c = DL.find_candidates(g2, lm, "train", "img0.png")
    assert len({x.id for x in c} - {x.id for x in a}) == 1
    with tempfile.TemporaryDirectory() as td:
        p = DL.Path(td) / "sub" / "decisions.json"
        DL.save_decisions(p, {a[0].id: "y", a[1].id: "n", "bad": "x"})
        assert DL.load_decisions(p) == {a[0].id: "y", a[1].id: "n"}


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

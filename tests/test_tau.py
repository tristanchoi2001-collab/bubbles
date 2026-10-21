"""
Tracking-aware U-Net (tau_unet.py / tau_tracker.py / 1_tau_unet_train.py) の配管のテスト
=====================================================================
  a) 3チャンネルの重みを 5チャンネルにして事前マスクの重みを 0 で足すと、事前マスクに関係なく元と同じ確率になる
  b) TauDetector に 3チャンネルの ckpt (best.pt と同じ形式) を入れると、tracker3.UNetDetector と全く同じ確率
     (同じ大きさの画像 / 学習サイズと違う大きさの画像の両方)。5チャンネルに変換した ckpt でもほぼ同じ (< 1e-5)
  c) render_prior: 塗りつぶし = 気泡の和集合、輪郭 = 気泡ごとの内側 PRIOR_EDGE_PX 幅 (くっついた気泡の境目に輪郭が入る)、
     画面からはみ出す部分は切る
  d) synth_prior: 同じ乱数なら同じ結果 / 崩しを全部切ると正解そのもの / 融合・何も無い所の気泡・事前マスクなし
  e) 2パス以上の検出 (偽の検出器): 4フレーム続けて見落とした大きい気泡を、前後のフレームから1パスに1フレームずつ取り戻し、
     最後は1本のトラックになる。1フレームだけの誤検出は (事前マスクをそのまま写す最悪の検出器でも) 広がらない
  f) 学習スクリプトの配管: 小さな偽の COCO データで データセット変換 -> 1 epoch (2 step) -> test 確認 まで通る
     (本物の学習ではない。乱数の重み・96x128 の画像。torch が無ければ飛ばす)
対象: binarized/2_bin_track.py (元 tau_unet / tau_tracker / tracker3) と binarized/1_bin_train.py (元 1_tau_unet_train)
使い方: リポジトリのルートで  python -B tests/test_tau.py     (pytest でも実行できる)
"""
import importlib.util
import json
import os
import sys
import tempfile

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bundles         # noqa: E402,F401  (tracker3 などの名前で binarized/2_bin_track.py を読む)

import fake_detector      # noqa: E402
import tau_unet as TU     # noqa: E402
import tau_tracker as TT  # noqa: E402
import tracker3 as T3     # noqa: E402

try:
    import torch
    import segmentation_models_pytorch as smp
    HAVE_TORCH = True
except ImportError:
    HAVE_TORCH = False


class Skip(Exception):
    pass


def need_torch():
    if not HAVE_TORCH:
        try:
            import pytest
            pytest.skip("torch / segmentation_models_pytorch がない")
        except ImportError:
            raise Skip("torch / segmentation_models_pytorch がない")


def save_fake_ckpt(path, train_hw=None, seed=0):
    torch.manual_seed(seed)
    m = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval()
    torch.save({"encoder": "resnet34", "classes": 3, "mean": (0.485, 0.456, 0.406), "std": (0.229, 0.224, 0.225),
                "train_hw": train_hw, "epoch": 1, "state_dict": m.state_dict()}, path)
    return m


def test_a_expand_reproduces_3ch():
    need_torch()
    torch.manual_seed(0)
    m3 = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval()
    m5 = TU.build_model("resnet34", 3, 5).eval()
    sd = TU.expand_state_dict(m3.state_dict(), m5)
    m5.load_state_dict(sd)
    assert float(sd["encoder.conv1.weight"][:, 3:].abs().sum()) == 0.0
    assert torch.equal(sd["encoder.conv1.weight"][:, :3], m3.state_dict()["encoder.conv1.weight"])
    x = torch.randn(1, 3, 64, 96)
    prior = (torch.rand(1, 2, 64, 96) > 0.5).float()
    with torch.no_grad():
        p3 = m3(x).softmax(1)
        p5 = m5(torch.cat([x, prior], 1)).softmax(1)
    d = float((p3 - p5).abs().max())
    assert d < 1e-5, d


def test_b_detector_matches_tracker3():
    need_torch()
    rng = np.random.default_rng(1)
    with tempfile.TemporaryDirectory() as td:
        for hw, shape in ((None, (96, 128)), ((64, 96), (80, 120))):
            ck = os.path.join(td, "best.pt")
            save_fake_ckpt(ck, hw)
            gray = (rng.random(shape) * 255).astype(np.uint8)
            prior = (rng.random((2,) + shape) > 0.5).astype(np.float32)
            ref = T3.UNetDetector(ck).prob(gray)
            tau = TU.TauDetector(ck)
            assert not tau.uses_prior
            got = tau.prob(gray, prior)
            assert np.array_equal(ref, got), float(np.abs(ref - got).max())
            # 5チャンネルに変換して保存 (学習の開始点と同じ) -> 事前マスクを入れてもほぼ同じ
            m5, ck3, _ = TU.load_tau_model(ck, force_prior=True)
            ck5 = os.path.join(td, "tau.pt")
            torch.save(dict(ck3, state_dict=m5.state_dict(), in_channels=5, tau=True), ck5)
            tau5 = TU.TauDetector(ck5)
            assert tau5.uses_prior
            d = float(np.abs(ref - tau5.prob(gray, prior)).max())
            assert d < 1e-5, d


def test_c_render_prior():
    H, W = 40, 50
    a = (np.ones((10, 10), bool), 5, 5)
    b = (np.ones((10, 10), bool), 15, 5)          # a の右隣にくっついている
    c = (np.ones((10, 10), bool), 45, 30)         # 右下で画面からはみ出す (5x10 だけ残る)
    p = TU.render_prior([a, b, c], H, W, edge_px=2)
    assert p.shape == (2, H, W) and p.dtype == np.float32
    fill, ring = p[0] > 0, p[1] > 0
    assert fill.sum() == 100 + 100 + 50
    assert ring[5:15, 5:15].sum() == 100 - 36 and ring[5:15, 15:25].sum() == 100 - 36
    assert ring[10, 13] and ring[10, 14] and ring[10, 15] and ring[10, 16]   # 境目に 2+2px の輪郭
    assert not ring[10, 12] and not ring[10, 17]
    assert ring[30:40, 45:50].sum() == 50 - 6 * 1   # 切った後の 10x5 の輪郭 (画面端にも付く)
    assert (ring <= fill).all()
    labels = np.zeros((H, W), np.int32)
    labels[5:15, 5:15], labels[5:15, 15:25] = 1, 2
    assert np.array_equal(TU.render_prior(TU.label_shapes(labels), H, W), TU.render_prior([a, b], H, W))


def _scene_labels():
    H, W = 120, 100
    yy, xx = np.ogrid[:H, :W]
    lab = np.zeros((H, W), np.int32)
    lab[(xx - 30) ** 2 + (yy - 40) ** 2 <= 15 ** 2] = 1
    lab[((xx - 59) ** 2 + (yy - 40) ** 2 <= 14 ** 2) & (lab == 0)] = 2   # 1 にくっついている
    lab[(xx - 70) ** 2 + (yy - 95) ** 2 <= 5 ** 2] = 7                   # 連番でない番号
    return lab


def test_d_synth_prior():
    lab = _scene_labels()
    aug = TU.PriorAug()
    p1 = TU.synth_prior(lab, np.random.default_rng(5), aug)
    p2 = TU.synth_prior(lab, np.random.default_rng(5), aug)
    assert np.array_equal(p1, p2) and p1.shape == (2,) + lab.shape
    assert set(np.unique(p1)) <= {0.0, 1.0}
    off = TU.PriorAug(p_empty=0, p_drop=0, shift_px=0, shift_size=0, p_big_shift=0, scale=(1, 1), morph_px=0,
                      p_trunc=0, p_merge=0, p_split=0, phantom_rate=0)
    exact = TU.synth_prior(lab, np.random.default_rng(0), off)
    assert np.array_equal(exact, TU.render_prior(TU.label_shapes(lab), *lab.shape))
    empty = TU.synth_prior(lab, np.random.default_rng(0), TU.PriorAug(p_empty=1.0))
    assert not empty.any()
    merged = TU.synth_prior(lab, np.random.default_rng(0), TU.PriorAug(**{**off.__dict__, "p_merge": 1.0}))
    assert merged[0][lab > 0].all()
    assert not merged[1][38:43, 44:46].any()          # 境目の輪郭が消えている (1個の気泡になった)
    assert exact[1][38:43, 44:46].any()
    ph = TU.synth_prior(lab, np.random.default_rng(3), TU.PriorAug(**{**off.__dict__, "phantom_rate": 5.0}))
    assert ph[0][lab == 0].sum() > 0                   # 何も無い所の気泡
    dropped = TU.synth_prior(lab, np.random.default_rng(0), TU.PriorAug(**{**off.__dict__, "p_drop": 1.0}))
    assert not dropped.any()


# ---------------- e) 2パス以上の検出 (偽の検出器) ----------------
EH, EW, EN = 240, 200, 12
MISSING = (4, 5, 6, 7)       # 大きい気泡を見落とすフレーム (MAX_AGE = 3 より長い -> パス0 ではトラックが切れる)
NOISE_FRAME = 2              # 1フレームだけの誤検出


def _gt_frame(f):
    yy, xx = np.ogrid[:EH, :EW]
    lab = np.zeros((EH, EW), np.int32)
    lab[(xx - 100) ** 2 + (yy - (40 + 12 * f)) ** 2 <= 18 ** 2] = 1      # 大きい気泡 (下へ 12px/frame)
    lab[(xx - 40) ** 2 + (yy - 60) ** 2 <= 6 ** 2] = 2                    # 止まっている小さい気泡
    lab[(xx - 165) ** 2 + (yy - 150) ** 2 <= 7 ** 2] = 3
    return lab


class CopyingFakeDetector:
    """事前マスクを使う偽の検出器。gray[0, 0] = フレーム番号
      - 大きい気泡は MISSING のフレームで見落とす。ただし事前マスクの内部が正解の半分以上を覆っていれば見つける
      - NOISE_FRAME には誤検出を1個出す
      - 事前マスクのうち正解の気泡と重ならない部分は、そのまま気泡として出す (事前マスクを写す最悪の検出器)"""
    uses_prior = True
    edge_px = TU.PRIOR_EDGE_PX

    def prob(self, gray, prior=None):
        f = int(gray[0, 0])
        lab = _gt_frame(f)
        if f in MISSING:
            big = lab == 1
            if prior is None or (prior[0][big] > 0.5).mean() < 0.5:
                lab[big] = 0
        nxt = int(lab.max()) + 1
        if f == NOISE_FRAME:
            yy, xx = np.ogrid[:EH, :EW]
            lab[(xx - 170) ** 2 + (yy - 40) ** 2 <= 5 ** 2] = nxt
            nxt += 1
        if prior is not None:
            from scipy import ndimage
            comp, n = ndimage.label((prior[0] > 0.5) & (_gt_frame(f) == 0))
            for k in range(1, n + 1):
                c = comp == k
                if c.sum() > 20 and not (c & (lab > 0)).any():
                    lab[c] = nxt
                    nxt += 1
        return fake_detector.fake_prob(lab)


def _run_e(min_hits, passes=3):
    old = (TT.PRIOR_MIN_HITS, TT.PRIOR_FROM)
    TT.PRIOR_MIN_HITS, TT.PRIOR_FROM = min_hits, "both"
    try:
        def gray_of(f):
            return np.full((EH, EW), f, np.uint8)
        roi = np.ones((EH, EW), bool)
        return TT.run_passes(EN, gray_of, CopyingFakeDetector(), roi, (EH, EW), passes, log=lambda *a: None)
    finally:
        TT.PRIOR_MIN_HITS, TT.PRIOR_FROM = old


def _big_track_ids(dets, rows):
    """大きい気泡 (中心 x ≈ 100) のフレームごとのトラックID"""
    out = {}
    for f in range(EN):
        for r in rows.get(f, []):
            di = r["det_index"]
            if di is not None and abs(dets[f][di].cx - 100) < 5 and dets[f][di].area > 500:
                out[f] = r["track_id"]
    return out


def _noise_frames(dets):
    return [f for f in range(EN) for d in dets[f] if abs(d.cx - 170) < 6 and abs(d.cy - 40) < 6]


def test_e_passes_recover_missing_bubble():
    res = _run_e(min_hits=2)
    d0, r0, _ = res[0]
    ids0 = _big_track_ids(d0, r0)
    assert sorted(ids0) == [f for f in range(EN) if f not in MISSING]
    assert len(set(ids0.values())) == 2                  # パス0: トラックが切れている
    dets, rows, _ = res[-1]
    ids = _big_track_ids(dets, rows)
    assert sorted(ids) == list(range(EN)), sorted(ids)   # 全フレームで検出
    assert len(set(ids.values())) == 1                   # 1本のトラック
    d1, r1, _ = res[1]                                    # パス1 では両端の 4 と 7 だけ取り戻す
    assert sorted(_big_track_ids(d1, r1)) == [f for f in range(EN) if f not in (5, 6)]
    for d, _, _ in res:                                   # 1フレームだけの誤検出は広がらない
        assert _noise_frames(d) == [NOISE_FRAME]
    # 観測1回のトラックも使うと、写す検出器では誤検出が隣のフレームに広がる (PRIOR_MIN_HITS の意味)
    spread = _noise_frames(_run_e(min_hits=1, passes=1)[-1][0])
    assert len(spread) > 1, spread


def test_e2_forward_prior_and_stop():
    obs = TT.TrackObservations(*_run_e(min_hits=2, passes=0)[0][:2])
    t = 4                                                 # 大きい気泡: 3 にいて 4 にいない -> 3 のマスクを 2->3 の移動量だけ前へ
    sh = obs.prior_shapes(t, "both", 2)
    big = [s for s in sh if s[0].sum() > 500]
    assert len(big) == 1
    pr = TU.render_prior(big, EH, EW)[0] > 0
    gt = _gt_frame(t) == 1
    assert (pr & gt).sum() / (pr | gt).sum() > 0.9
    assert not obs.prior_shapes(t, "forward", 50)        # 観測回数が足りないトラックは入れない


def test_f_train_script_smoke():
    need_torch()
    spec = importlib.util.spec_from_file_location("tau_train", bundles.TRAIN_PATH)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "coco")
        for split, n in (("train", 4), ("valid", 2), ("test", 1)):
            os.makedirs(os.path.join(src, split))
            images, anns = [], []
            for i in range(n):
                g = np.zeros((96, 128), np.uint8)
                for _ in range(4):
                    cx, cy, r = int(rng.integers(15, 113)), int(rng.integers(15, 81)), int(rng.integers(4, 12))
                    cv2.circle(g, (cx, cy), r, 255, 2)
                    t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
                    poly = np.stack([cx + (r + 1) * np.cos(t), cy + (r + 1) * np.sin(t)], 1).ravel().tolist()
                    anns.append({"id": len(anns), "image_id": i, "segmentation": [poly],
                                 "bbox": [cx - r, cy - r, 2 * r, 2 * r]})
                fn = f"img{i}.png"
                cv2.imwrite(os.path.join(src, split, fn), g)
                images.append({"id": i, "file_name": fn, "height": 96, "width": 128})
            with open(os.path.join(src, split, "_annotations.coco.json"), "w") as fp:
                json.dump({"images": images, "annotations": anns}, fp)
        ck = os.path.join(td, "best.pt")
        save_fake_ckpt(ck, [96, 128])
        M.SRC, M.DST, M.OUT, M.FINETUNE_FROM = src, os.path.join(td, "ds"), os.path.join(td, "runs", "tau"), ck
        M.FINETUNE_EPOCHS, M.BS, M.CROP, M.CP_SAVE_PREVIEW = 1, 2, (64, 96), 1
        M.USE_PRIOR = True                     # 1_bin_train.py の既定は False (TAU は保留)
        M.main_train()
        ins = cv2.imread(os.path.join(td, "ds", "instances", "train", "img0.png"), cv2.IMREAD_UNCHANGED)
        assert ins.dtype == np.uint16 and ins.max() >= 1
        out = os.path.join(td, "runs", "tau")
        best = torch.load(os.path.join(out, "best.pt"), map_location="cpu")
        assert best["in_channels"] == 5 and best["tau"] and best["state_dict"]["encoder.conv1.weight"].shape[1] == 5
        assert os.path.exists(os.path.join(out, "test_report.json"))
        ds = M.BubbleDS(os.path.join(td, "ds"), "val", 64, 96, train=False)
        x, y = ds[0]
        assert x.shape == (5, 96, 128) and y.shape == (96, 128)
        assert TU.TauDetector(os.path.join(out, "best.pt")).uses_prior


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

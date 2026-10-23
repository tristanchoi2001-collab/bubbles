"""
parity 救済のテスト (raw/5_parity_test.py)
=========================================
  a) wall_regions (壁を足さないとき) = 2_raw_track.py の _wall_regions (しきい値・closing を変えても完全に同じ)
  b) L字のスラグ: 輪郭は出ているが中の内部確率が低い (U-Net の取りこぼし) -> 2_raw_track.py の分け方では出ない。
     parity で 1個足され、正しい L (壁の半分まで) とほぼ一致する。もとの気泡の画素・番号は変わらない
  c) 検出済みのスラグの下の液だまり (液 (アンカー) に接していない) は足さない
  d) 基準の液 (アンカー): 取りこぼしたスラグの方が液より大きいフレーム。"bubbles" は気泡を取り囲む液を基準にするので
     液を足さない (スラグは画面の半分を超えるので足さずに skipped に書く。上限を上げると足す)。
     "largest" は一番大きいスラグを基準にして液を気泡にしてしまう (既定にしない理由)
  e) 取りこぼしが無いフレームはそのまま (ラベルマップが完全に同じ、足した数 0)
  f) 輪郭の切れ目: 輪郭確率の切れ目が大きく、弱い偽の壁で切られた L の下の端だけが先に候補になる。二値化画像の輪 (B) を
     壁にすると L 全体が閉じ、先の候補はその一部として捨てられて L 全体が 1個になる。PARITY_USE_RING = False なら下の端だけ
  g) check / track: 偽の確率 (画像の明るさから作る) で 2_raw_track.py の検出・追跡を通す。check は L を毎フレーム足して画像と
     parity_report.json を出す。track は CSV に L の気泡が入り、PARITY_ENABLE = False なら 2_raw_track.py の main と CSV が
     バイト単位で同じ
  h) まとめる規則 (PARITY_MERGE): U-Net が L の上の帯だけを検出し (境目に偽の壁)、parity が縦の帯を足す。境目に二値化画像の
     白い輪が無ければ 1個 (U-Net の番号) にまとまり L とほぼ一致する。輪があれば 2個のまま (not_merged に記録)、
     PARITY_MERGE = False でも 2個。U-Net が両方検出したとき: "parity" ではそのまま、"all" ならまとめる

使い方: リポジトリのルートで  python -B tests/test_parity.py     (pytest でも実行できる)
"""
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

from test_raw import Skip, need_torch, load, save_ckpt, _track_settings  # noqa: E402

P = load(os.path.join(ROOT, "raw", "5_parity_test.py"), "parity_test")
M = P.load_track()
STEPS = P.steps_for(M)
H, W = 240, 320


def base():
    """液だけの確率 (背景 0.95)"""
    pr = np.zeros((3, H, W), np.float32)
    pr[0], pr[1], pr[2] = 0.95, 0.03, 0.02
    return pr


def put_bubble(pr, cx, cy, r):
    """検出される気泡: 中は内部確率が高く、輪郭 (幅 3) は境界確率が高い"""
    yy, xx = np.mgrid[:H, :W]
    d = np.hypot(xx - cx, yy - cy)
    pr[:, d < r - 1] = np.array([0.03, 0.95, 0.02], np.float32)[:, None]
    pr[:, (d >= r - 1) & (d <= r + 1)] = np.array([0.03, 0.02, 0.95], np.float32)[:, None]


def l_mask(x0=120, x1=300, y0=30, y1=70, xv=260, yb=220):
    """L字: 上の帯 (x0..x1, y0..y1) + 右の縦の帯 (xv..x1, y0..yb)"""
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = True
    m[y0:yb, xv:x1] = True
    return m


def outline(m, width=3):
    return m & ~cv2.erode(m.astype(np.uint8), np.ones((2 * width + 1, 2 * width + 1), np.uint8)).astype(bool)


def put_missed(pr, m, gap=None):
    """U-Net が取りこぼした気体: 輪郭は境界確率が高い (gap の所は出ていない)、中は背景と判定 (内部確率が低い)"""
    o = outline(m)
    if gap is not None:
        o &= ~gap
    pr[:, m & ~o] = np.array([0.93, 0.05, 0.02], np.float32)[:, None]
    pr[:, o] = np.array([0.03, 0.02, 0.95], np.float32)[:, None]


def liquid_with_bubbles():
    pr = base()
    for cx, cy, r in ((40, 40, 12), (60, 200, 12), (180, 160, 10), (30, 120, 9)):
        put_bubble(pr, cx, cy, r)
    return pr


def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)


def run(pr, ring=None, **kw):
    keep = {k: getattr(P, k) for k in kw}
    for k, v in kw.items():
        setattr(P, k, v)
    try:
        inst = M.unet_instances(pr)
        out, rep = P.parity_rescue(pr, inst, ring, STEPS)
    finally:
        for k, v in keep.items():
            setattr(P, k, v)
    return inst, out, rep


# ==============================================================
def test_a_wall_regions_same():
    rng = np.random.default_rng(0)
    for _ in range(3):
        pr = rng.random((3, 64, 96)).astype(np.float32)
        for thr, it in ((0.5, 3), (0.3, 5), (0.1, 7), (0.5, 0)):
            a = P.wall_regions(pr, thr, it)
            b = M._wall_regions(pr, thr, it)
            assert np.array_equal(a[0], b[0]) and a[1] == b[1] and np.array_equal(a[2], b[2]), (thr, it)


def test_b_l_slug():
    pr = liquid_with_bubbles()
    L = l_mask()
    put_missed(pr, L)
    inst, out, rep = run(pr)
    assert not any((inst[L] == l).sum() > 0.5 * L.sum() for l in np.unique(inst[L]) if l), "取りこぼしの設定になっていない"
    assert int(inst.max()) == 4, int(inst.max())                       # 液の中の気泡 4個は検出される
    assert len(rep["added"]) == 1 and not rep["skipped"], rep
    a = rep["added"][0]
    added = out == a["label"]
    assert a["label"] == int(inst.max()) + 1 and iou(added, L) > 0.9, iou(added, L)
    assert np.array_equal(out[inst > 0], inst[inst > 0]) and set(np.unique(out)) == set(np.unique(inst)) | {a["label"]}
    assert rep["anchor"]["how"].startswith("bubbles(") and a["contact_anchor"] >= a["contact_total"] * 0.5
    vis = P.draw_parity(np.zeros((H, W), np.uint8), inst, out, rep)
    assert vis.shape == (H, W, 3) and (vis[..., 2] > 100).sum() > 0.5 * L.sum()   # 赤で塗っている


def test_c_liquid_pocket():
    pr = liquid_with_bubbles()
    band = np.zeros((H, W), bool)
    band[150:185, :] = True                                            # 画面を横切る検出済みのスラグ
    pr[:, band] = np.array([0.03, 0.95, 0.02], np.float32)[:, None]
    pr[:, outline(band) & (np.arange(H)[:, None] > 0) & (np.arange(H)[:, None] < H - 1)] = \
        np.array([0.03, 0.02, 0.95], np.float32)[:, None]
    pr[:, 150:153, :] = np.array([0.03, 0.02, 0.95], np.float32)[:, None, None]
    pr[:, 182:185, :] = np.array([0.03, 0.02, 0.95], np.float32)[:, None, None]
    inst, out, rep = run(pr)                                           # 下の液だまり (185..240) は液 (アンカー) に接しない
    assert (inst[band] > 0).mean() > 0.9, "スラグが検出されていない"
    assert not rep["added"] and np.array_equal(out, inst), rep["added"]


def test_d_anchor():
    pr = base()
    liq = np.zeros((H, W), bool)
    liq[40:200, :110] = True                                           # 液 (画面の 23%): 左の端の四角。3方をスラグに囲まれる
    big = ~liq                                                         # 取りこぼしたスラグ (77%)。中に気泡なし
    put_missed(pr, big)
    for cx, cy, r in ((30, 70, 9), (70, 120, 9), (40, 170, 9)):
        put_bubble(pr, cx, cy, r)                                     # 液に気泡 3個
    inst, out, rep = run(pr)
    assert rep["anchor"]["how"] == "bubbles(3)", rep["anchor"]
    assert not rep["added"] and len(rep["skipped"]) == 1 and np.array_equal(out, inst), rep
    assert rep["skipped"][0]["region_area"] > 0.5 * H * W
    inst, out, rep = run(pr, PARITY_MAX_AREA_FRAC=0.9)                # 上限を上げれば足す (気体なので正しい)
    assert len(rep["added"]) == 1 and iou(out == rep["added"][0]["label"], big) > 0.9
    inst, out, rep = run(pr, PARITY_ANCHOR="largest")                 # 一番大きい領域 = スラグを基準にすると液を足してしまう
    assert rep["anchor"]["how"] == "largest" and len(rep["added"]) == 1, rep
    assert iou(out == rep["added"][0]["label"], liq) > 0.7, "largest で液を足す例になっていない"


def test_e_nothing_missing():
    pr = liquid_with_bubbles()
    put_bubble(pr, 250, 80, 30)                                        # 大きい気泡も検出される
    inst, out, rep = run(pr)
    assert not rep["added"] and not rep["skipped"] and np.array_equal(out, inst)


def test_f_gap_ring_fragment():
    pr = liquid_with_bubbles()
    L = l_mask()
    gap = np.zeros((H, W), bool)
    gap[25:40, 170:195] = True                                         # 上の辺の輪郭が 25 px 出ていない
    put_missed(pr, L, gap)
    pr[:, 168:171, 263:297] = np.array([0.58, 0.02, 0.4], np.float32)[:, None, None]   # 弱い偽の壁 (境界確率 0.4)
    ring = outline(L)                                                  # 二値化画像では輪が全部見えている
    inst, out, rep = run(pr, ring)
    assert len(rep["added"]) == 1 and rep["added"][0]["walls"] == "pedge+ring", rep["added"]
    assert len(rep["fragments"]) == 1 and rep["fragments"][0]["walls"] == "pedge", rep["fragments"]
    assert iou(out == rep["added"][0]["label"], L) > 0.85, iou(out == rep["added"][0]["label"], L)
    inst, out, rep = run(pr, ring, PARITY_USE_RING=False)              # 輪を壁にしなければ下の端だけ
    assert len(rep["added"]) == 1 and rep["added"][0]["region_area"] < 0.25 * L.sum(), rep["added"]


def l_split(pr, detect_vertical=False):
    """L字: 上の帯 (x 120..257) は U-Net が検出 (内部確率が高い)、縦の帯は取りこぼし (detect_vertical なら両方検出)。
    境目 (x 257..259) に偽の壁 (境界確率 0.95)。戻り値: L のマスク"""
    L = l_mask()
    o = outline(L)
    top = np.zeros((H, W), bool)
    top[30:70, 120:257] = True
    pr[:, L & ~o] = np.array([0.93, 0.05, 0.02], np.float32)[:, None]
    pr[:, (top if not detect_vertical else L) & ~o] = np.array([0.03, 0.95, 0.02], np.float32)[:, None]
    pr[:, o] = np.array([0.03, 0.02, 0.95], np.float32)[:, None]
    pr[:, 30:70, 257:260] = np.array([0.03, 0.02, 0.95], np.float32)[:, None, None]
    return L


def test_h_merge_without_rim():
    pr = liquid_with_bubbles()
    L = l_split(pr)
    ring = outline(L)                                                  # 画像では L の輪だけ (境目に線なし)
    inst, out, rep = run(pr, ring)
    top_label = [l for l in np.unique(inst[L]) if l and (inst == l).sum() > 3000]
    assert len(top_label) == 1 and len(rep["added"]) == 1, (top_label, rep["added"])
    t = top_label[0]
    assert len(rep["merged"]) == 1 and rep["merged"][0]["rim_frac"] == 0 and rep["added"][0]["merged_into"] == t, rep["merged"]
    assert iou(out == t, L) > 0.9 and not (out == rep["added"][0]["label"]).any(), iou(out == t, L)
    assert np.array_equal(out[(inst > 0) & (inst != t)], inst[(inst > 0) & (inst != t)])     # ほかの気泡は変わらない
    line = np.zeros((H, W), bool)
    line[30:70, 257:260] = True
    inst, out2, rep2 = run(pr, ring | line)                            # 境目に白い線 (輪) が見える -> まとめない
    assert not rep2["merged"] and rep2["not_merged"] and rep2["not_merged"][0]["rim_frac"] > 0.5, rep2["not_merged"]
    assert (out2 == t).sum() < 0.6 * L.sum() and (out2 == rep2["added"][0]["label"]).sum() > 0.3 * L.sum()
    inst, out3, rep3 = run(pr, ring, PARITY_MERGE=False)
    assert not rep3["merged"] and len(np.unique(out3[L])) >= 3          # 背景 + 2個
    vis = P.draw_parity(np.zeros((H, W), np.uint8), inst, out, rep)
    assert (vis[..., 2][L] > 100).mean() > 0.5                         # まとめた気泡も赤
    # U-Net が偽の壁の両側を検出: "parity" ではそのまま、"all" ならまとめる
    pr = liquid_with_bubbles()
    L = l_split(pr, detect_vertical=True)
    inst, out, rep = run(pr, outline(L))
    assert not rep["added"] and not rep["merged"] and np.array_equal(out, inst)
    assert len([l for l in np.unique(inst[L]) if l and (inst == l).sum() > 3000]) == 2
    inst, out, rep = run(pr, outline(L), PARITY_MERGE_SCOPE="all")
    assert len(rep["merged"]) == 1 and len([l for l in np.unique(out[L]) if l]) == 1 and iou(out == out[100, 280], L) > 0.9


# ---- 検出・追跡を通す ----
def fake_frames(td, n=4):
    """明るさで種類を表した元画像: 液 220、検出される気泡の中 212 と輪 120、取りこぼす L の中 216 と輪 120、
    輪郭確率が出ない輪の切れ目 125 (二値化 B では白)、弱い偽の壁 208 (B では黒)"""
    frames = os.path.join(td, "frames")
    os.makedirs(frames)
    for k in range(n):
        img = np.full((H, W), 220, np.uint8)
        for cx, cy, r in ((40, 40, 12), (60, 200, 12), (180, 160, 10), (30, 120, 9)):
            cv2.circle(img, (cx + 3 * k, cy), r - 1, 212, -1)
            cv2.circle(img, (cx + 3 * k, cy), r, 120, 2)
        L = l_mask(x0=110 + 3 * k, x1=290 + 3 * k, xv=250 + 3 * k)
        img[L] = 216
        img[outline(L)] = 120
        cv2.imwrite(os.path.join(frames, f"img{k:04d}.png"), cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
    bgp = os.path.join(td, "bg.png")
    cv2.imwrite(bgp, np.full((H, W, 3), 220, np.uint8))
    return frames, bgp, l_mask(x0=110, x1=290, xv=250)


def fake_prob(Mod):
    def prob_raw(self, raw_bgr, bg_bgr, prior=None):
        planes = Mod.make_planes(raw_bgr, bg_bgr, self.preproc)
        self.last_planes = {k: planes[k] for k in Mod.PLANES[self.mode]}
        g = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2GRAY)
        pr = np.zeros((3,) + g.shape, np.float32)
        pr[0], pr[1], pr[2] = 0.95, 0.03, 0.02
        pr[:, g == 212] = np.array([0.03, 0.95, 0.02], np.float32)[:, None]
        pr[:, g <= 122] = np.array([0.03, 0.02, 0.95], np.float32)[:, None]
        pr[:, g == 208] = np.array([0.58, 0.02, 0.4], np.float32)[:, None]
        return pr
    return prob_raw


def test_g_check_and_track():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    with tempfile.TemporaryDirectory() as td:
        frames, bgp, L0 = fake_frames(td)
        torch.manual_seed(0)
        ck = os.path.join(td, "best.pt")
        save_ckpt(ck, smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3), [H, W])
        # check
        M1 = P.load_track()
        _track_settings(M1, frames, bgp, ck, os.path.join(td, "out"))
        M1.RawDetector.prob_raw = fake_prob(M1)
        s = P.run_check(M1, os.path.join(td, "out_parity"))
        assert s["frames"] == 4 and s["added"] == 4 and s["frames_with_added"] == 4, s
        rep = json.load(open(os.path.join(td, "out_parity", "parity_report.json"), encoding="utf-8"))
        assert all(abs(f["added"][0]["area"] - L0.sum()) < 0.15 * L0.sum() for f in rep["frames"]), [f["added"] for f in rep["frames"]]
        assert len(os.listdir(os.path.join(td, "out_parity", "check"))) == 4
        # track: parity なし = 2_raw_track.py の main (CSV がバイト単位で同じ)
        M2 = P.load_track()
        _track_settings(M2, frames, bgp, ck, os.path.join(td, "plain"))
        M2.RawDetector.prob_raw = fake_prob(M2)
        M2.main()
        M3 = P.load_track()
        _track_settings(M3, frames, bgp, ck, os.path.join(td, "off"))
        M3.RawDetector.prob_raw = fake_prob(M3)
        P.PARITY_ENABLE = False
        try:
            P.run_track(M3, os.path.join(td, "off_parity"))
        finally:
            P.PARITY_ENABLE = True
        csv = lambda d: open(os.path.join(td, d, "result_tracking.csv"), "rb").read()
        assert csv("plain") == csv("off_parity"), "PARITY_ENABLE = False なのに 2_raw_track.py と結果が違う"
        assert M3.OUTPUT_FOLDER == os.path.join(td, "off") and M3.unet_instances.__module__ == M3.__name__   # 元に戻す
        # track: parity あり -> L の気泡が毎フレーム CSV に入る
        M4 = P.load_track()
        _track_settings(M4, frames, bgp, ck, os.path.join(td, "on"))
        M4.RawDetector.prob_raw = fake_prob(M4)
        s = P.run_track(M4, os.path.join(td, "on_parity"))
        assert s["added"] == 4, s
        import csv as csvmod
        with open(os.path.join(td, "on_parity", "result_tracking.csv"), encoding="utf-8-sig") as fp:
            rows = list(csvmod.DictReader(fp))
        big = [r for r in rows if r["面積(px)"] and float(r["面積(px)"]) > 0.8 * L0.sum()]
        assert len(big) == 4 and len({r["トラックID"] for r in big}) == 1, [(r["フレーム"], r["トラックID"], r["面積(px)"]) for r in big]
        assert len(os.listdir(os.path.join(td, "on_parity", "parity"))) == 4
        rep = json.load(open(os.path.join(td, "on_parity", "parity_report.json"), encoding="utf-8"))
        assert [f["file"] for f in rep["frames"]] == [f"img{k:04d}.png" for k in range(4)]


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

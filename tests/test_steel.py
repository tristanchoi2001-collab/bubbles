"""
鉄 (不透明) の流路用 (steel/1_steel_train.py, steel/2_steel_track.py) の回帰テスト
=====================================================================
steel/ は raw/ (commit bb568f7) から分けた固定コピー。raw/ との違いは「背景画像の明るさ合わせ (BG_MATCH)」だけ。
  a) match_background: 'offset' は全体の明るさの差 b を、'gain' は a × 背景 + b を、気泡 (暗い円・画面の 40% の暗い帯) を
     除いて正しく求める。None はそのまま。知らない値は止まる
  b) make_planes: bg_match=None なら raw/ と完全に同じ。'offset' なら、照明が明るくなっても DB が液体全体に出ない。
     1_steel_train.py と 2_steel_track.py の make_planes / match_background は同じ結果
  c) RawDetector: ckpt の input.bg_match を読む。'offset' の ckpt は、元画像の全体の明るさが変わっても確率がほぼ同じ。
     記録の無い ckpt は raw/ の RawDetector と完全に同じ確率。知らない bg_match は止まる
  d) 学習 (BG_MATCH='offset', 'bin+sign') が最後まで動き、ckpt と DST/meta.json に bg_match が残る。
     BG_MATCH を変えると REBUILD_DATASET = False でも作り直す。できた ckpt で 2_steel_track.py の main が最後まで動き、
     qc_report の入力の記録に bg_match が残る

使い方: リポジトリのルートで  python -B tests/test_steel.py     (pytest でも実行できる)
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

from test_raw import Skip, need_torch, load, save_ckpt, widen, make_src, _configure, _track_settings  # noqa: E402

RAW = load(os.path.join(ROOT, "raw", "2_raw_track.py"), "raw_track_for_steel")
STK = load(os.path.join(ROOT, "steel", "2_steel_track.py"), "steel_track")
STR = load(os.path.join(ROOT, "steel", "1_steel_train.py"), "steel_train")


def steel_pair(H=96, W=128, seed=0, offset=0.0, gain=1.0, slug=False):
    """鉄の流路に似せた画像: 背景は横じま (溝) + ノイズ、気泡の中は液体より 40 暗く、輪郭は明暗の輪。
    元画像 = gain × 背景 + offset (照明の変化) + 気泡"""
    rng = np.random.default_rng(seed)
    yy = np.arange(H)[:, None] * np.ones((1, W))
    base = 130 + 25 * np.sin(yy / 3.0) + rng.normal(0, 3, (H, W))
    bg = np.clip(base, 0, 255)
    f = gain * bg + offset + rng.normal(0, 2, (H, W))
    circles = [(40, 50, 15), (100, 30, 8)]
    for cx, cy, r in circles:
        m = np.zeros((H, W), np.uint8)
        cv2.circle(m, (cx, cy), r, 1, -1)
        f[m > 0] -= 40
        ring = np.zeros((H, W), np.uint8)
        cv2.circle(ring, (cx, cy), r, 1, 2)
        f[ring > 0] += 60
    if slug:
        f[: int(0.4 * H)] -= 40          # 画面の 40% を占める暗い帯 (巨大スラグのつもり)
    to3 = lambda a: cv2.cvtColor(np.clip(np.rint(a), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    return to3(f), to3(bg), circles


# ==============================================================
def test_a_match_background():
    for slug in (False, True):
        raw, bg, _ = steel_pair(offset=6.0, slug=slug)
        out, (a, b) = STK.match_background(raw, bg, "offset")
        assert a == 1.0 and abs(b - 6.0) < 0.6, (slug, a, b)
        liquid = np.ones(raw.shape[:2], bool)
        liquid[: int(0.4 * raw.shape[0]) + 2] = False                       # 暗い帯と気泡のある所を外して確かめる
        cv2.circle(liquid.view(np.uint8), (40, 50), 18, 0, -1)
        cv2.circle(liquid.view(np.uint8), (100, 30), 11, 0, -1)
        d = raw[..., 0].astype(float) - out[..., 0].astype(float)
        assert abs(d[liquid].mean()) < 0.6, d[liquid].mean()
        raw, bg, _ = steel_pair(offset=-3.0, gain=1.04, slug=slug)
        _, (a, b) = STK.match_background(raw, bg, "gain")
        assert abs(a - 1.04) < 0.02 and abs(b + 3.0) < 2.5, (slug, a, b)
    same, ab = STK.match_background(raw, bg, None)
    assert ab == (1.0, 0.0) and np.array_equal(same, bg)
    try:
        STK.match_background(raw, bg, "median")
        raise AssertionError("知らない BG_MATCH で止まらない")
    except ValueError:
        pass


def test_b_make_planes():
    raw, bg, _ = steel_pair(offset=6.0)
    ref = RAW.make_planes(raw, bg, (15, 4, 0))
    for M in (STK, STR):
        p = M.make_planes(raw, bg, (15, 4, 0))
        assert all(np.array_equal(p[k], ref[k]) for k in ref), "bg_match=None が raw/ と違う"
        q = M.make_planes(raw, bg, (15, 4, 0), "offset")
        liquid = np.ones(raw.shape[:2], bool)
        cv2.circle(liquid.view(np.uint8), (40, 50), 18, 0, -1)
        cv2.circle(liquid.view(np.uint8), (100, 30), 11, 0, -1)
        assert p["DB"][liquid].mean() > 15 and q["DB"][liquid].mean() < 5, (p["DB"][liquid].mean(), q["DB"][liquid].mean())
        inner = np.zeros(raw.shape[:2], np.uint8)
        cv2.circle(inner, (40, 50), 10, 1, -1)
        assert q["DK"][inner > 0].mean() > 120 and q["B"][inner > 0].mean() > 120   # 気泡の中が DK と B に白く出る
    for mode in ("offset", "gain"):
        a, b = STK.match_background(raw, bg, mode), STR.match_background(raw, bg, mode)
        assert np.array_equal(a[0], b[0]) and a[1] == b[1]


def test_c_detector():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    torch.manual_seed(0)
    m3 = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval()
    with tempfile.TemporaryDirectory() as td:
        ck0 = os.path.join(td, "plain.pt")
        save_ckpt(ck0, m3, [96, 128])
        raw, bg, _ = steel_pair(offset=0.0)
        a = RAW.RawDetector(ck0).prob_raw(raw, bg)
        b = STK.RawDetector(ck0).prob_raw(raw, bg)
        assert np.array_equal(a, b), "記録の無い ckpt で raw/ と違う"
        assert STK.RawDetector(ck0).bg_match is None
        model = widen(m3, "bin+sign")
        with torch.no_grad():                                   # DK / DB の重みも使うようにする (0 のままだと変化が見えない)
            model.encoder.conv1.weight[:, 3:5] = 0.05 * torch.randn_like(model.encoder.conv1.weight[:, 3:5])
        ck1, ck2 = os.path.join(td, "match.pt"), os.path.join(td, "nomatch.pt")
        inp = {"mode": "bin+sign", "preproc": [15, 4, 0], "prior": False, "prior_edge_px": 2}
        save_ckpt(ck1, model, [96, 128], dict(inp, bg_match="offset"))
        save_ckpt(ck2, model, [96, 128], inp)
        r0, bg0, _ = steel_pair(seed=3, offset=0.0)
        r1, _, _ = steel_pair(seed=3, offset=8.0)
        d1, d2 = STK.RawDetector(ck1), STK.RawDetector(ck2)
        assert d1.bg_match == "offset" and d2.bg_match is None
        p1 = d1.prob_raw(r1, bg0)
        assert abs(d1.last_bg_fit[1] - 8.0) < 0.8, d1.last_bg_fit          # 当てはめた明るさの差 (最後のフレーム)
        diff_match = np.abs(p1 - d1.prob_raw(r0, bg0)).max()
        diff_plain = np.abs(d2.prob_raw(r1, bg0) - d2.prob_raw(r0, bg0)).max()
        assert diff_match < 0.25 * diff_plain, (diff_match, diff_plain)     # 照明が変わっても確率がほとんど変わらない
        save_ckpt(os.path.join(td, "bad.pt"), model, [96, 128], dict(inp, bg_match="both"))
        try:
            STK.RawDetector(os.path.join(td, "bad.pt"))
            raise AssertionError("知らない bg_match で止まらない")
        except ValueError:
            pass


def test_d_train_and_track():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    with tempfile.TemporaryDirectory() as td:
        src = make_src(td)
        torch.manual_seed(0)
        base = os.path.join(td, "best.pt")
        save_ckpt(base, smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3), [96, 128], epoch=65)
        _configure(STR, td, src, "bin+sign", base)
        STR.BG_MATCH = "offset"
        STR.main()
        runs = os.path.join(td, "runs", "bin_sign")
        ck = torch.load(os.path.join(runs, "best.pt"), map_location="cpu")
        assert ck["input"]["bg_match"] == "offset" and ck["input"]["mode"] == "bin+sign"
        meta = json.load(open(os.path.join(STR.DST, "meta.json"), encoding="utf-8"))
        assert meta["bg_match"] == "offset"
        # BG_MATCH を変えたら REBUILD_DATASET = False でも作り直す
        STR.REBUILD_DATASET, STR.BG_MATCH, STR.EPOCHS = False, None, 1
        mtime = os.path.getmtime(os.path.join(STR.DST, "meta.json"))
        STR.main()
        meta2 = json.load(open(os.path.join(STR.DST, "meta.json"), encoding="utf-8"))
        assert meta2["bg_match"] is None and os.path.getmtime(os.path.join(STR.DST, "meta.json")) >= mtime
        STR.BG_MATCH = "both"
        try:
            STR.main()
            raise AssertionError("知らない BG_MATCH で止まらない")
        except ValueError:
            pass
        STR.BG_MATCH = "offset"
        # 2_steel_track.py の main を最後まで
        frames = os.path.join(td, "frames")
        os.makedirs(frames)
        for k in range(4):
            f, bg, _ = steel_pair(seed=10 + k, offset=2.0 * k)
            cv2.imwrite(os.path.join(frames, f"img{k:04d}.png"), f)
        bgp = os.path.join(td, "bg.png")
        cv2.imwrite(bgp, bg)
        out = os.path.join(td, "out_steel")
        _track_settings(STK, frames, bgp, os.path.join(runs, "best.pt"), out)
        STK.main()
        q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
        assert q["used_params"]["UNET"]["detection"]["input"] == {"mode": "bin+sign", "preproc": [15, 4, 0], "bg_match": "offset"}
        assert os.path.getsize(os.path.join(out, "result_tracking.csv")) > 50


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

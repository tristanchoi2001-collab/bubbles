"""
鉄 (不透明) の流路用 (steel/1_steel_train.py, steel/2_steel_track.py) の回帰テスト
=====================================================================
steel/ は raw/ (commit bb568f7) から分けた固定コピー。raw/ との違いは「背景画像の明るさ合わせ (BG_MATCH)」だけ。
  a) fit_background / match_background: 'offset' は全体の明るさの差 b を、'gain' は a × 背景 + b を、気泡を除いて求める。
     暗い帯が画面の 45% あっても正しい。気泡の方が多いフレーム (60%) は信用しない (None)。模様の無い背景の 'gain' は
     'offset' の値になる。色ごとに明るさが違ってもグレーの値で合わせる。None はそのまま。知らない値は止まる
  b) make_planes: bg_match=None なら raw/ と完全に同じ。'offset' / 'gain' なら「合わせた背景で raw/ の make_planes」と完全に同じ
     (B, D, DK, DB 全部)。1_steel_train.py と 2_steel_track.py の関数は同じ結果
  c) RawDetector: ckpt の input.bg_match を読む。'offset' の ckpt は、照明が明るくなっても確率がほぼ同じ。
     検出で U-Net が見た画像 = 学習のデータセットの画像。当てはめを信用しないフレームは直前の値を使う。
     記録の無い ckpt は raw/ の RawDetector と完全に同じ確率。知らない bg_match は止まる。
     raw/2_raw_track.py と binarized/2_bin_track.py は steel の ckpt を止める
  d) データセット: BG_MATCH='offset' で DST に書いた画像 = 合わせた背景で作った画像。同じ設定なら使い回し、BG_MATCH を変えたら作り直す
  e) 学習 (BG_MATCH='offset', 'bin+sign') が最後まで動き、ckpt に bg_match が残る。できた ckpt で 2_steel_track.py の main が
     最後まで動き、qc_report に bg_match と当てはめの範囲が残り、確認画像 (unet_input.png) は U-Net が見た B と同じ。
     TAU (事前マスク付き) の ckpt でも main が最後まで動き、記録が残る

使い方: リポジトリのルートで  python -B tests/test_steel.py     (pytest でも実行できる)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_raw import Skip, need_torch, load, save_ckpt, widen, make_src, _configure, _track_settings  # noqa: E402

RAW = load(os.path.join(ROOT, "raw", "2_raw_track.py"), "raw_track_for_steel")
BIN = load(os.path.join(ROOT, "binarized", "2_bin_track.py"), "bin_track_for_steel")
STK = load(os.path.join(ROOT, "steel", "2_steel_track.py"), "steel_track")
STR = load(os.path.join(ROOT, "steel", "1_steel_train.py"), "steel_train")
INP = {"mode": "bin+sign", "preproc": [15, 4, 0], "prior": False, "prior_edge_px": 2}


def to3(a):
    return cv2.cvtColor(np.clip(np.rint(a), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def steel_pair(H=96, W=128, seed=0, offset=0.0, gain=1.0, slug=0.0, slug_c=-40.0):
    """鉄の流路に似せた画像: 背景は横じま (溝) + ノイズ、気泡の中は液体より 40 暗く、輪郭は明るい輪。
    元画像 = gain × 背景 + offset (照明の変化) + 気泡。slug = 画面の上からこの割合を 40 暗くする (巨大スラグのつもり)"""
    rng = np.random.default_rng(seed)
    yy = np.arange(H)[:, None] * np.ones((1, W))
    bg = np.clip(130 + 25 * np.sin(yy / 3.0) + rng.normal(0, 3, (H, W)), 0, 255)
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
        f[: int(slug * H)] += slug_c
    return to3(f), to3(bg), circles


def liquid_mask(raw, slug=0.0):
    m = np.ones(raw.shape[:2], np.uint8)
    m[: int(slug * raw.shape[0]) + 2] = 0
    cv2.circle(m, (40, 50), 18, 0, -1)
    cv2.circle(m, (100, 30), 11, 0, -1)
    return m > 0


# ==============================================================
def test_a_fit_background():
    for M in (STK, STR):
        for slug in (0.0, 0.4, 0.45):
            raw, bg, _ = steel_pair(offset=6.0, slug=slug)
            out, (a, b), ok = M.match_background(raw, bg, "offset")
            assert ok and a == 1.0 and abs(b - 6.0) < 0.6, (slug, a, b)
            d = raw[..., 0].astype(float) - out[..., 0].astype(float)
            assert abs(d[liquid_mask(raw, slug)].mean()) < 0.6
            raw, bg, _ = steel_pair(offset=-3.0, gain=1.04, slug=slug)
            fit = M.fit_background(raw, bg, "gain")
            assert fit is not None and abs(fit[0] - 1.04) < 0.02 and abs((fit[0] - 1) * 130 + fit[1] - 2.2) < 1.0, (slug, fit)
        raw, bg, _ = steel_pair(offset=6.0, slug=0.6)            # 気泡の方が多い -> 信用しない
        assert M.fit_background(raw, bg, "offset") is None
        out, ab, ok = M.match_background(raw, bg, "offset")
        assert not ok and ab == (1.0, 0.0) and np.array_equal(out, bg)
        rng = np.random.default_rng(1)                           # 模様の無い背景: 'gain' は 'offset' の値 (a = 1)
        bgf, rawf = to3(130 + rng.normal(0, 3, (96, 128))), to3(136 + rng.normal(0, 3, (96, 128)))
        a, b = M.fit_background(rawf, bgf, "gain")
        assert a == 1.0 and abs(b - 6.0) < 0.6, (a, b)
        raw, bg, _ = steel_pair(offset=0.0)                       # 色ごとに違う明るさの変化 -> グレーの値
        raw_c = np.clip(raw.astype(np.float64) + np.array([2.0, 6.0, 12.0]), 0, 255).astype(np.uint8)
        b = M.fit_background(raw_c, bg, "offset")[1]
        assert abs(b - (0.114 * 2 + 0.587 * 6 + 0.299 * 12)) < 0.6, b
        same, ab, ok = M.match_background(raw, bg, None)
        assert ok and ab == (1.0, 0.0) and np.array_equal(same, bg)
        try:
            M.match_background(raw, bg, "median")
            raise AssertionError("知らない BG_MATCH で止まらない")
        except ValueError:
            pass


def test_b_make_planes():
    raw, bg, _ = steel_pair(offset=6.0, gain=1.03)
    ref = RAW.make_planes(raw, bg, (15, 4, 0))
    for M in (STK, STR):
        p = M.make_planes(raw, bg, (15, 4, 0))
        assert all(np.array_equal(p[k], ref[k]) for k in ref), "bg_match=None が raw/ と違う"
        for mode in ("offset", "gain"):
            want = RAW.make_planes(raw, M.match_background(raw, bg, mode)[0], (15, 4, 0))
            got = M.make_planes(raw, bg, (15, 4, 0), mode)
            for k in want:
                assert np.array_equal(got[k], want[k]), (M.__name__, mode, k)
        q = M.make_planes(raw, bg, (15, 4, 0), "offset")
        liq = liquid_mask(raw)
        assert p["DB"][liq].mean() > 15 and q["DB"][liq].mean() < 6, (p["DB"][liq].mean(), q["DB"][liq].mean())
        inner = np.zeros(raw.shape[:2], np.uint8)
        cv2.circle(inner, (40, 50), 10, 1, -1)
        assert q["DK"][inner > 0].mean() > 120 and q["B"][inner > 0].mean() > 120   # 気泡の中が DK と B に白く出る
    for mode in ("offset", "gain"):
        a, b = STK.match_background(raw, bg, mode), STR.match_background(raw, bg, mode)
        assert np.array_equal(a[0], b[0]) and a[1:] == b[1:]


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
        save_ckpt(ck1, model, [96, 128], dict(INP, bg_match="offset"))
        save_ckpt(ck2, model, [96, 128], INP)
        r0, bg0, _ = steel_pair(seed=3, offset=0.0)
        r1, _, _ = steel_pair(seed=3, offset=8.0)
        d1, d2 = STK.RawDetector(ck1), STK.RawDetector(ck2)
        assert d1.bg_match == "offset" and d2.bg_match is None
        p1 = d1.prob_raw(r1, bg0)
        assert abs(d1.last_bg_fit[1] - 8.0) < 0.8, d1.last_bg_fit          # 当てはめた明るさの差 (最後のフレーム)
        want = STR.make_planes(r1, bg0, (15, 4, 0), "offset")              # 学習のデータセットに書く画像
        assert all(np.array_equal(d1.last_planes[k], want[k]) for k in d1.last_planes)
        diff_match = np.abs(p1 - STK.RawDetector(ck1).prob_raw(r0, bg0)).max()   # 別の動画の最初のフレームとして比べる
        diff_plain = np.abs(d2.prob_raw(r1, bg0) - d2.prob_raw(r0, bg0)).max()
        assert diff_match < 0.25 * diff_plain, (diff_match, diff_plain)     # 照明が変わっても確率がほとんど変わらない
        # 気泡が画面の大半のフレームは、直前に信用できたフレームの値を使う
        d3 = STK.RawDetector(ck1)
        d3.prob_raw(steel_pair(seed=4, offset=5.0)[0], bg0)
        d3.prob_raw(steel_pair(seed=4, offset=9.0, slug=0.6)[0], bg0)
        assert d3.bg_rejected == 1 and abs(d3.last_bg_fit[1] - 5.0) < 0.8, d3.last_bg_fit
        s = d3.bg_fit_summary()
        assert s["frames"] == 2 and s["rejected"] == 1 and abs(s["b_min"] - s["b_max"]) < 1e-9
        # 弱い気泡 (-20) が画面の 55%: 当てはめは上限内 (約 -15) に入るが、直前から急に変わるので信用しない。
        # 照明が本当に変わった (+5 -> +12 が 5フレーム続く) ときは受け入れる
        d4 = STK.RawDetector(ck1)
        d4.prob_raw(steel_pair(seed=6, offset=5.0)[0], bg0)
        weak = steel_pair(seed=7, offset=5.0, slug=0.55, slug_c=-20.0)[0]
        assert STK.fit_background(weak, bg0, "offset") is not None           # 1枚だけなら通ってしまう
        d4.prob_raw(weak, bg0)
        assert d4.bg_rejected == 1 and abs(d4.last_bg_fit[1] - 5.0) < 0.8, d4.last_bg_fit
        for k in range(5):
            d4.prob_raw(steel_pair(seed=8 + k, offset=12.0)[0], bg0)
        assert d4.bg_rejected == 5 and abs(d4.last_bg_fit[1] - 12.0) < 0.8, (d4.bg_rejected, d4.last_bg_fit)
        # 知らない bg_match / steel の ckpt を raw/・binarized/ で使う -> 止まる
        save_ckpt(os.path.join(td, "bad.pt"), model, [96, 128], dict(INP, bg_match="both"))
        for fn, path in ((STK.RawDetector, "bad.pt"), (RAW.RawDetector, "match.pt"), (BIN.ckpt_uses_prior, "match.pt"),
                         (BIN.load_tau_model, "match.pt")):
            try:
                fn(os.path.join(td, path))
                raise AssertionError(f"{fn.__qualname__} が {path} で止まらない")
            except ValueError as e:
                assert path == "bad.pt" or "steel" in str(e), str(e)
        save_ckpt(os.path.join(td, "bin_steel.pt"), m3, [96, 128], {"mode": "bin", "preproc": [15, 4, 0], "bg_match": "offset"})
        try:
            BIN.ckpt_uses_prior(os.path.join(td, "bin_steel.pt"))
            raise AssertionError("binarized が steel の 'bin' ckpt で止まらない")
        except ValueError as e:
            assert "steel" in str(e)


def _offset_src(td, off=8.0):
    src = make_src(td)
    for split in ("train", "valid", "test"):
        for fn in os.listdir(os.path.join(src, split)):
            if fn.endswith(".jpg"):
                p = os.path.join(src, split, fn)
                cv2.imwrite(p, np.clip(cv2.imread(p).astype(np.float64) + off, 0, 255).astype(np.uint8))
    return src


def test_d_dataset():
    with tempfile.TemporaryDirectory() as td:
        src = _offset_src(td)
        _configure(STR, td, src, "bin+sign", None)
        STR.BG_MATCH = "offset"
        try:
            STR.build_dataset(src, STR.DST)
            bg = cv2.imread(os.path.join(td, "bg_test.png"))
            n = 0
            for fn in sorted(os.listdir(os.path.join(src, "train"))):
                if not fn.endswith(".jpg"):
                    continue
                raw = cv2.imread(os.path.join(src, "train", fn))
                want = STR.make_planes(raw, bg, STR.PREPROC, "offset")
                assert not np.array_equal(want["DB"], STR.make_planes(raw, bg, STR.PREPROC, None)["DB"])
                for k, sub in STR.PLANE_DIRS.items():
                    got = cv2.imread(os.path.join(STR.DST, sub, "train", Path(fn).stem + ".png"), cv2.IMREAD_GRAYSCALE)
                    assert np.array_equal(got, want[k]), (fn, k)
                n += 1
            assert n >= 2
            # 同じ設定なら使い回し、BG_MATCH を変えたら作り直す (学習と test は飛ばす)
            tr0, tc0 = STR.train, STR.test_check
            STR.train, STR.test_check = (lambda *a: os.path.join(td, "x.pt")), (lambda *a: None)
            try:
                STR.REBUILD_DATASET = False
                STR.main()
                sentinel = os.path.join(STR.DST, "bin", "train", "sentinel.txt")
                open(sentinel, "w").close()
                STR.main()
                assert os.path.exists(sentinel), "REBUILD_DATASET=False で同じ設定なのに作り直した"
                STR.BG_MATCH = None
                STR.main()
                assert not os.path.exists(sentinel), "BG_MATCH を変えたのに作り直さない"
                meta = json.load(open(os.path.join(STR.DST, "meta.json"), encoding="utf-8"))
                assert meta["bg_match"] is None and meta["layout"] == "steel-3"
                STR.BG_MATCH = "both"
                try:
                    STR.main()
                    raise AssertionError("知らない BG_MATCH で止まらない")
                except ValueError:
                    pass
            finally:
                STR.train, STR.test_check = tr0, tc0
        finally:
            STR.REBUILD_DATASET, STR.BG_MATCH = True, "offset"


def _steel_frames(td, n=4):
    frames = os.path.join(td, "frames")
    os.makedirs(frames)
    for k in range(n):
        f, bg, _ = steel_pair(seed=10 + k, offset=6.0 + 2.0 * k)
        cv2.imwrite(os.path.join(frames, f"img{k:04d}.png"), f)
    bgp = os.path.join(td, "bg.png")
    cv2.imwrite(bgp, bg)
    return frames, bgp


def test_e_train_and_track():
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
        frames, bgp = _steel_frames(td)
        out = os.path.join(td, "out_steel")
        _track_settings(STK, frames, bgp, os.path.join(runs, "best.pt"), out)
        STK.main()
        q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
        inp = q["used_params"]["UNET"]["detection"]["input"]
        assert inp["mode"] == "bin+sign" and inp["preproc"] == [15, 4, 0] and inp["bg_match"] == "offset", inp
        assert inp["bg_fit"]["frames"] == 4 and 5.0 < inp["bg_fit"]["b_min"] < inp["bg_fit"]["b_max"] < 13.5, inp["bg_fit"]
        assert os.path.getsize(os.path.join(out, "result_tracking.csv")) > 50
        u = cv2.imread(os.path.join(out, "debug", "unet_input.png"), cv2.IMREAD_GRAYSCALE)
        ub = cv2.imread(os.path.join(out, "debug", "unet_input_B.png"), cv2.IMREAD_GRAYSCALE)
        assert u is not None and np.array_equal(u, ub), "確認画像が U-Net の見た B と違う (合わせていない背景で作った)"
        z = np.load(os.path.join(out, "prob", "img0000.npz"))
        assert np.array_equal(z["u_input"], z["u_B"])
        # TAU (事前マスク付き) の ckpt でも main が最後まで動き、記録が残る
        torch.manual_seed(2)
        m = widen(smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval(), "bin+sign", True)
        tau = os.path.join(td, "tau.pt")
        save_ckpt(tau, m, [96, 128], dict(INP, prior=True, bg_match="offset"))
        out2 = os.path.join(td, "out_tau")
        _track_settings(STK, frames, bgp, tau, out2)
        p0 = STK.PRIOR_PASSES
        STK.PRIOR_PASSES = 1
        try:
            STK.main()
        finally:
            STK.PRIOR_PASSES = p0
        q = json.load(open(os.path.join(out2, "qc_report.json"), encoding="utf-8"))
        t_inp = q["used_params"]["TAU"]["input"]
        assert t_inp["bg_match"] == "offset" and t_inp["bg_fit"]["frames"] == 4, t_inp   # パスをまたいで 1フレーム 1回


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

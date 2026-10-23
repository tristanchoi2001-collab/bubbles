"""
鉄 (不透明) の流路用 (steel/1_steel_train.py, steel/2_steel_track.py) の回帰テスト
=====================================================================
steel/ は raw/ (commit bb568f7) から分けた固定コピー。raw/ との違いは「背景画像の明るさ合わせ (BG_MATCH)」「背景画像の位置合わせ
(BG_REGISTER)」「元の画像 (BMP) を読む (ORIGINAL_IMAGE_DIRS)」「流れの向き (FLOW_DIRECTION)」と鉄ブロック用の既定値。
  a) fit_background / match_background: 'offset' は全体の明るさの差 b を、'gain' は a × 背景 + b を、気泡を除いて求める。
     暗い帯が画面の 45% あっても正しい。気泡の方が多いフレーム (60%) は信用しない (None)。模様の無い背景の 'gain' は
     'offset' の値になる。色ごとに明るさが違ってもグレーの値で合わせる。None はそのまま。知らない値は止まる
  b) make_planes: bg_match=None なら raw/ と完全に同じ。'offset' / 'gain' なら「合わせた背景で raw/ の make_planes」と完全に同じ
     (B, D, DK, DB 全部)。1_steel_train.py と 2_steel_track.py の関数は同じ結果
  c) RawDetector: ckpt の input.bg_match を読む。'offset' の ckpt は、照明が明るくなっても確率がほぼ同じ。
     検出で U-Net が見た画像 = 学習のデータセットの画像。当てはめを信用しないフレームは直前の値を使う。
     記録の無い ckpt は raw/ の RawDetector と完全に同じ確率。知らない bg_match は止まる。
     raw/2_raw_track.py と binarized/2_bin_track.py は steel の ckpt を止める
  d) データセット: BG_MATCH='offset' で DST に書いた画像 = 合わせた背景で作った画像。同じ設定なら使い回し、BG_MATCH / BG_REGISTER を
     変えたら作り直す
  e) 学習 (BG_MATCH='offset', BG_REGISTER='affine', 'bin+sign') が最後まで動き、ckpt に両方が残る。できた ckpt で 2_steel_track.py の
     main が最後まで動き、qc_report に bg_match・bg_register と当てはめの範囲が残り、確認画像 (unet_input.png) は U-Net が見た B と同じ。
     CSV の速度の列は FLOW_DIRECTION の向き。TAU (事前マスク付き) の ckpt でも main が最後まで動き、位置合わせ・明るさ合わせは
     パスをまたいで 1フレーム 1回。パスごとの QC (steel/3_tracking_qc.py) も CSV を読める
  f) FLOW_DIRECTION: 先端部 = 流れの向きの端 ("up" は今までと同じ計算)、後端部 = 反対側。CSV の速度は流れの向きの座標の変化で、
     先端側が画面端で切れた観測どうしは後端部、両側とも切れていれば前の値のまま。合体の直後・飛んだフレームも今までと同じ扱い
  g) fit_register: 溝に似せた模様で、分かっているずれ (実測に近い x -0.8 px + 縦の倍率 0.9966、模様の細かさより大きいずれ、
     平行移動だけ) を 0.3 px 以内で求める。別の背景・模様の無い元画像・許す範囲を超えるずれは None。
     make_planes(bg_register='affine') = 「動かした背景で raw/ の make_planes」で、溝の残り (B の液体の白) が消える。
     背景を合わせる関数は 1_steel_train.py と 2_steel_track.py で同じ
  h) RawDetector の位置合わせ: 最初のフレーム = 学習のデータセットの画像、次のフレームは前の行列から、当てはめられないフレームは
     直前の行列 (最初のフレームなら動かさない = raw/ と同じ入力)。qc_report 用の範囲。知らない bg_register は止まる。
     位置合わせだけの steel の ckpt も raw/・binarized/ では止まる
  i) ORIGINAL_IMAGE_DIRS: Roboflow の書き出し (JPEG) の代わりに元の画像 (BMP) を読む (名前が同じ / 拡張子だけ違う)。
     中身の違う同じ名前・大きさの違う画像は使わず、見つからなければ書き出しを使う。DST の画像 = 元の画像 + 位置合わせで作った画像

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

from test_raw import Skip, need_torch, load, save_ckpt, widen, make_src, circle_poly, _configure, _track_settings  # noqa: E402

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


W_REAL = np.array([[1.0, 0.0, -0.8], [0.0, 0.9966, 2.5]], np.float32)       # 実測に近いずれ (x -0.8 px、縦の倍率 0.9966)
W_BIG = np.array([[1.002, 0.001, 1.7], [-0.0008, 0.997, -3.2]], np.float32)   # 模様の細かさより大きいずれ (位相相関から当てはめ直す)
W_SHIFT = np.array([[1.0, 0.0, 2.3], [0.0, 1.0, -1.4]], np.float32)           # 平行移動だけ
BUBBLES = ((90, 120, 40), (230, 70, 25), (250, 180, 12))                        # (x, y, 半径)。フレームごとに右へ 6 px


def grooves(H=240, W=320, seed=0):
    """鉄ブロックの背景に似せた模様: 細かいむら (σ 2 px でぼかしたノイズ、ばらつき 18) + 横の溝"""
    rng = np.random.default_rng(seed)
    t = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 2.0)
    yy = np.arange(H)[:, None] * np.ones((1, W))
    return np.clip(130 + 18 * t / t.std() + 10 * np.sin(yy / 3.0), 0, 255)


def textured_pair(seed=0, warp=None, frame=0, flat=False):
    """(元画像, 背景画像)。元画像 = 背景を warp で動かしたもの + ノイズ + 気泡 (中 -35、明るい輪 +70)。
    flat = True なら模様の無い元画像 (位置合わせできない)"""
    bg = grooves(seed=seed)
    H, W = bg.shape
    f = np.full((H, W), 130.0) if flat else STK.apply_register(to3(bg), warp)[..., 0].astype(np.float64)
    f += np.random.default_rng(1000 * seed + frame + 1).normal(0, 2, (H, W))
    for cx, cy, r in BUBBLES:
        m = np.zeros((H, W), np.uint8)
        cv2.circle(m, (cx + 6 * frame, cy), r, 1, -1)
        f[m > 0] -= 35
        ring = np.zeros((H, W), np.uint8)
        cv2.circle(ring, (cx + 6 * frame, cy), r, 1, 4)
        f[ring > 0] += 70
    return to3(f), to3(bg)


def textured_liquid(frame=0, H=240, W=320):
    m = np.zeros((H, W), np.uint8)
    m[6:-6, 6:-6] = 1
    for cx, cy, r in BUBBLES:
        cv2.circle(m, (cx + 6 * frame, cy), r + 8, 0, -1)
    return m > 0


def warp_err(Wa, Wb, H=240, W=320):
    """2つの行列で、画面の四隅と中央がどれだけ違う所へ動くか (px)"""
    pts = np.array([[0, 0, 1], [W, 0, 1], [0, H, 1], [W, H, 1], [W / 2, H / 2, 1]], float)
    return float(np.abs(pts @ np.asarray(Wa, float).T - pts @ np.asarray(Wb, float).T).max())


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
    keep = {k: getattr(STR, k) for k in ("REBUILD_DATASET", "BG_MATCH", "BG_REGISTER", "train", "test_check")}
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
                want = STR.make_planes(raw, bg, STR.PREPROC, "offset", STR.BG_REGISTER)
                assert not np.array_equal(want["DB"], STR.make_planes(raw, bg, STR.PREPROC, None, STR.BG_REGISTER)["DB"])
                for k, sub in STR.PLANE_DIRS.items():
                    got = cv2.imread(os.path.join(STR.DST, sub, "train", Path(fn).stem + ".png"), cv2.IMREAD_GRAYSCALE)
                    assert np.array_equal(got, want[k]), (fn, k)
                n += 1
            assert n >= 2
            # 同じ設定なら使い回し、BG_MATCH / BG_REGISTER を変えたら作り直す (学習と test は飛ばす)
            STR.train, STR.test_check = (lambda *a: os.path.join(td, "x.pt")), (lambda *a: None)
            STR.REBUILD_DATASET = False
            STR.main()
            sentinel = os.path.join(STR.DST, "bin", "train", "sentinel.txt")
            open(sentinel, "w").close()
            STR.main()
            assert os.path.exists(sentinel), "REBUILD_DATASET=False で同じ設定なのに作り直した"
            STR.BG_MATCH = None
            STR.main()
            assert not os.path.exists(sentinel), "BG_MATCH を変えたのに作り直さない"
            open(sentinel, "w").close()
            STR.BG_REGISTER = None if STR.BG_REGISTER else "affine"
            STR.main()
            assert not os.path.exists(sentinel), "BG_REGISTER を変えたのに作り直さない"
            meta = json.load(open(os.path.join(STR.DST, "meta.json"), encoding="utf-8"))
            assert meta["bg_match"] is None and meta["bg_register"] == STR.BG_REGISTER and meta["layout"] == "steel-3", meta
            for name, bad in (("BG_MATCH", "both"), ("BG_REGISTER", "rigid")):
                v0 = getattr(STR, name)
                setattr(STR, name, bad)
                try:
                    STR.main()
                    raise AssertionError(f"知らない {name} で止まらない")
                except ValueError:
                    pass
                finally:
                    setattr(STR, name, v0)
        finally:
            for k, v in keep.items():
                setattr(STR, k, v)


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
        keep = STR.BG_MATCH, STR.BG_REGISTER
        STR.BG_MATCH, STR.BG_REGISTER = "offset", "affine"
        try:
            STR.main()
        finally:
            STR.BG_MATCH, STR.BG_REGISTER = keep
        runs = os.path.join(td, "runs", "bin_sign")
        ck = torch.load(os.path.join(runs, "best.pt"), map_location="cpu")
        assert ck["input"]["bg_match"] == "offset" and ck["input"]["bg_register"] == "affine" and ck["input"]["mode"] == "bin+sign"
        frames, bgp = _steel_frames(td)
        out = os.path.join(td, "out_steel")
        _track_settings(STK, frames, bgp, os.path.join(runs, "best.pt"), out)
        STK.main()
        q = json.load(open(os.path.join(out, "qc_report.json"), encoding="utf-8"))
        inp = q["used_params"]["UNET"]["detection"]["input"]
        assert inp["mode"] == "bin+sign" and inp["preproc"] == [15, 4, 0] and inp["bg_match"] == "offset", inp
        assert inp["bg_fit"]["frames"] == 4 and 5.0 < inp["bg_fit"]["b_min"] < inp["bg_fit"]["b_max"] < 13.5, inp["bg_fit"]
        assert inp["bg_register"] == "affine" and inp["bg_reg_fit"]["frames"] == 4, inp      # 位置合わせも 1フレーム 1回
        assert q["used_params"]["FLOW_DIRECTION"] == STK.FLOW_DIRECTION
        assert os.path.getsize(os.path.join(out, "result_tracking.csv")) > 50
        with open(os.path.join(out, "result_tracking.csv"), encoding="utf-8-sig") as fp:
            header = fp.readline()
        assert STK.SPEED_COLUMN[STK.FLOW_DIRECTION] in header and ("上昇速度" in header) == (STK.FLOW_DIRECTION == "up"), header
        u = cv2.imread(os.path.join(out, "debug", "unet_input.png"), cv2.IMREAD_GRAYSCALE)
        ub = cv2.imread(os.path.join(out, "debug", "unet_input_B.png"), cv2.IMREAD_GRAYSCALE)
        assert u is not None and np.array_equal(u, ub), "確認画像が U-Net の見た B と違う (合わせていない背景で作った)"
        z = np.load(os.path.join(out, "prob", "img0000.npz"))
        assert np.array_equal(z["u_input"], z["u_B"])
        # TAU (事前マスク付き) の ckpt でも main が最後まで動き、記録が残る
        torch.manual_seed(2)
        m = widen(smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval(), "bin+sign", True)
        tau = os.path.join(td, "tau.pt")
        save_ckpt(tau, m, [96, 128], dict(INP, prior=True, bg_match="offset", bg_register="affine"))
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
        assert t_inp["bg_register"] == "affine" and t_inp["bg_reg_fit"]["frames"] == 4, t_inp
        ps = json.load(open(os.path.join(out2, "pass_summary.json"), encoding="utf-8"))
        assert ps and all((e.get("qc") or {}).get("n_tracks") is not None for e in ps), ps   # steel/3_tracking_qc.py が CSV を読める


# ==============================================================
def test_f_flow_direction():
    M = STK
    t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    pts = np.stack([100 + 30 * np.cos(t), 60 + 10 * np.sin(t)], 1)          # 横長の楕円 (x 70〜130, y 50〜70)
    n = max(3, int(len(pts) * M.LEADING_EDGE_PERCENTILE / 100.0))
    top = pts[np.argsort(pts[:, 1])[:n]]                                      # 今までの計算 (上側 = y が小さい)
    assert M.leading_edge_from_points(pts, direction="up") == (float(np.mean(top[:, 0])), float(np.mean(top[:, 1])))
    for d, axis, lead_end, back_end in (("up", 1, 50, 70), ("down", 1, 70, 50), ("left", 0, 70, 130), ("right", 0, 130, 70)):
        lead = M.leading_edge_from_points(pts, direction=d)
        back = M.leading_edge_from_points(pts, direction=d, trailing=True)
        assert abs(lead[axis] - lead_end) < 1.0 and abs(back[axis] - back_end) < 1.0, (d, lead, back)
        assert abs(lead[1 - axis] - (100, 60)[1 - axis]) < 0.5 and abs(back[1 - axis] - (100, 60)[1 - axis]) < 0.5, (d, lead, back)
    try:
        M.flow_axis("upward")
        raise AssertionError("知らない FLOW_DIRECTION で止まらない")
    except ValueError:
        pass

    N, L, R, LR = (False,) * 4, (False, False, True, False), (False, False, False, True), (False, False, True, True)
    T, TB = (True, False, False, False), (True, True, False, False)        # 接触 = (上, 下, 左, 右)

    def speeds(direction, tracks, with_dets=True):
        """tracks: ID -> [(フレーム, 先端部, 後端部, 接触[, イベント])] (流れの向きの座標) -> ID -> CSV の速度の列"""
        x = M.flow_axis(direction)[0] == 0
        nf = 1 + max(o[0] for obs in tracks.values() for o in obs)
        rows, dets = {f: [] for f in range(nf)}, [[] for _ in range(nf)]
        for tid, obs in tracks.items():
            for f, lead, back, touch, *ev in obs:
                d = M.Detection(shape=None, contours=[], area=1000.0, cx=0.0, cy=0.0,
                                leading_x=lead if x else 0.0, leading_y=0.0 if x else lead, touches_frame=any(touch),
                                touch=touch, trailing_x=back if x else 0.0, trailing_y=0.0 if x else back)
                rows[f].append({"det_index": len(dets[f]), "track_id": tid, "event": ev[0] if ev else "normal",
                                "leading_x": d.leading_x, "leading_y": d.leading_y})
                dets[f].append(d)
        f0 = M.FLOW_DIRECTION
        M.FLOW_DIRECTION = direction
        try:
            out = M.compute_velocity_ema(rows, nf, dets if with_dets else None)
        finally:
            M.FLOW_DIRECTION = f0
        return {tid: [r["vy"] for f in range(nf) for r in out[f] if r["track_id"] == tid] for tid in tracks}

    def same(a, b):
        return len(a) == len(b) and np.allclose(np.array(a, float), np.array(b, float), equal_nan=True)

    nan = float("nan")
    right = {1: [(0, 50, 20, N), (1, 60, 30, N), (2, 70, 40, N), (3, 100, 45, N, "merge")],   # 画面の中: 先端部。合体の直後は前の値
             2: [(0, 190, 150, N), (1, 199, 160, R), (2, 199, 170, R)],                    # 右端から出ていく: 後端部
             3: [(0, 199, 0, LR), (1, 199, 0, LR), (2, 199, 0, LR)],                       # 画面をまたぐ: 更新しない
             4: [(0, 30, 0, L), (1, 40, 0, L), (2, 50, 0, L)],                             # 左端から入ってくる: 先端部
             5: [(0, 10, 2, N), (2, 30, 5, N)]}                                            # 1フレーム飛んだ: 2 で割る
    want = {1: [nan, 10, 10, 10], 2: [nan, 10, 10], 3: [nan, nan, nan], 4: [nan, 10, 10], 5: [nan, 10]}
    got = speeds("right", right)
    assert all(same(got[k], want[k]) for k in want), got
    old = speeds("right", right, with_dets=False)                                          # 検出が無ければ先端部だけ (今までの計算)
    assert same(old[2], [nan, 9, 9 * M.VELOCITY_EMA_ALPHA]) and same(old[3], [nan, 0, 0]), old
    assert same(speeds("left", {1: [(0, 8, 60, N), (1, 0, 50, L), (2, 0, 40, L)]})[1], [nan, -10, -10])   # 左端から出ていく
    up = {1: [(0, 100, 130, N), (1, 90, 120, N), (2, 80, 110, N)], 2: [(0, 5, 60, N), (1, 0, 50, T), (2, 0, 40, T)],
          3: [(0, 0, 119, TB), (1, 0, 119, TB)]}
    got = speeds("up", up)
    assert same(got[1], [nan, -10, -10]) and same(got[2], [nan, -10, -10]) and same(got[3], [nan, nan]), got
    assert same(speeds("up", {1: up[1]}, with_dets=False)[1], [nan, -10, -10])


def test_g_register():
    import inspect
    for M in (STK, STR):
        for W_true, mode in ((W_REAL, "affine"), (W_BIG, "affine"), (W_SHIFT, "shift")):
            for seed in (0, 1):
                raw, bg = textured_pair(seed, W_true)
                fit = M.fit_register(raw, bg, mode)
                assert fit is not None and warp_err(fit[0], W_true) < 0.3 and fit[1] > 0.9, (M.__name__, mode, seed, fit)
                if mode == "shift":
                    assert np.array_equal(fit[0][:, :2], np.eye(2, dtype=np.float32))
        raw, bg = textured_pair(0, W_BIG)
        fit = M.fit_register(raw, bg, "affine", init=W_BIG + np.float32([[0, 0, 0.6], [0, 0, -0.5]]))   # 前のフレームの行列から
        assert fit is not None and warp_err(fit[0], W_BIG) < 0.3, fit
        assert M.fit_register(textured_pair(0, W_REAL)[0], textured_pair(5)[1], "affine") is None       # 別の背景
        assert M.fit_register(textured_pair(0, flat=True)[0], bg, "affine") is None                      # 模様の見えない元画像
        raw, bg = textured_pair(0, W_REAL)
        lim0 = dict(M.BG_REGISTER_LIMITS)
        for key, v in (("shift", 2.0), ("scale", 0.002)):                     # 許す範囲を超える (移動 2.7 px、縦の倍率 0.9966)
            M.BG_REGISTER_LIMITS[key] = v
            try:
                assert M.fit_register(raw, bg, "affine") is None, key
            finally:
                M.BG_REGISTER_LIMITS.update(lim0)
        W, cc = M.fit_register(raw, bg, None)
        assert np.array_equal(W, np.eye(2, 3, dtype=np.float32)) and cc == 1.0
        assert np.array_equal(M.apply_register(bg, None), bg)
        assert M.apply_register(cv2.resize(bg, (160, 120)), None, raw.shape).shape == raw.shape     # 大きさは合わせる
        try:
            M.fit_register(raw, bg, "rigid")
            raise AssertionError("知らない BG_REGISTER で止まらない")
        except ValueError:
            pass
    # 背景を合わせる関数・設定は 1_steel_train.py と 2_steel_track.py で同じ (学習の画像 = 検出の画像)
    for name in ("fit_background", "apply_background", "match_background", "fit_register", "_ecc_register", "apply_register",
                 "make_planes"):
        assert inspect.getsource(getattr(STK, name)) == inspect.getsource(getattr(STR, name)), f"{name} が 2つのファイルで違う"
    for name in ("BG_MATCH_MODES", "BG_MATCH_MAX", "BG_REGISTER_MODES", "BG_REGISTER_SCALE", "BG_REGISTER_DEV", "BG_REGISTER_LIMITS"):
        assert getattr(STK, name) == getattr(STR, name), name
    # make_planes: 位置を合わせた背景で raw/ の make_planes と完全に同じ。溝の残り (液体の B の白) が消える
    raw, bg = textured_pair(0, W_REAL)
    reg = STK.apply_register(bg, STK.fit_register(raw, bg, "affine")[0], raw.shape)
    for M in (STK, STR):
        got = M.make_planes(raw, bg, (15, 4, 0), None, "affine")
        want = RAW.make_planes(raw, reg, (15, 4, 0))
        assert all(np.array_equal(got[k], want[k]) for k in want), M.__name__
        both = M.make_planes(raw, bg, (15, 4, 0), "offset", "affine")
        want = RAW.make_planes(raw, M.match_background(raw, reg, "offset")[0], (15, 4, 0))
        assert all(np.array_equal(both[k], want[k]) for k in want), M.__name__
        flat = textured_pair(0, flat=True)[0]                                  # 合わなければ背景は動かさない
        got, want = M.make_planes(flat, bg, (15, 4, 0), None, "affine"), RAW.make_planes(flat, bg, (15, 4, 0))
        assert all(np.array_equal(got[k], want[k]) for k in want)
    liq = textured_liquid()
    p0, p1 = STK.make_planes(raw, bg, (15, 4, 0)), STK.make_planes(raw, bg, (15, 4, 0), None, "affine")
    assert (p0["B"][liq] > 0).mean() > 0.1 and (p1["B"][liq] > 0).mean() < 0.01, ((p0["B"][liq] > 0).mean(), (p1["B"][liq] > 0).mean())
    inner = np.zeros(liq.shape, np.uint8)
    cv2.circle(inner, BUBBLES[0][:2], 30, 1, -1)
    assert p1["DK"][inner > 0].mean() > 100 and p1["DB"][inner > 0].mean() < 10    # 気泡の中 (-35) は DK に白く出る


def test_h_register_detector():
    need_torch()
    import torch
    import segmentation_models_pytorch as smp
    torch.manual_seed(0)
    m3 = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=3).eval()
    model = widen(m3, "bin+sign")
    W2 = W_REAL + np.float32([[0, 0, 0.5], [0, 0.0004, -0.4]])
    with tempfile.TemporaryDirectory() as td:
        ck = os.path.join(td, "reg.pt")
        save_ckpt(ck, model, [96, 128], dict(INP, bg_register="affine"))
        d = STK.RawDetector(ck)
        assert d.bg_register == "affine" and d.bg_match is None
        r0, bg = textured_pair(0, W_REAL, frame=0)
        d.prob_raw(r0, bg)
        want = STR.make_planes(r0, bg, (15, 4, 0), None, "affine")             # 学習のデータセットに書く画像と同じ
        assert all(np.array_equal(d.last_planes[k], want[k]) for k in d.last_planes)
        d.prob_raw(textured_pair(0, W2, frame=1)[0], bg)                        # 前のフレームの行列から当てはめる
        d.prob_raw(textured_pair(0, frame=2, flat=True)[0], bg)                 # 当てはめられない -> 直前の行列
        assert d.reg_rejected == 1 and len(d.reg_fits) == 3
        assert warp_err(d.reg_fits[0], W_REAL) < 0.3 and warp_err(d.reg_fits[1], W2) < 0.3, d.reg_fits
        assert np.array_equal(d.reg_fits[2], d.reg_fits[1])
        s = d.reg_summary()
        c = np.array([160.0, 120.0, 1.0])
        sh = [Wm.astype(float) @ c - c[:2] for Wm in (W_REAL, W2)]
        assert s["frames"] == 3 and s["rejected"] == 1, s
        assert abs(s["dx_min"] - min(v[0] for v in sh)) < 0.3 and abs(s["dx_max"] - max(v[0] for v in sh)) < 0.3, s
        assert abs(s["dy_min"] - min(v[1] for v in sh)) < 0.3 and abs(s["dy_max"] - max(v[1] for v in sh)) < 0.3, s
        assert abs(s["sy_min"] - 0.9966) < 0.0025 and abs(s["sy_max"] - 0.997) < 0.0025, s   # 四隅 0.3 px 以内 = 倍率 0.0025 以内
        # 最初のフレームが当てはめられない -> 動かさない (raw/ と同じ入力)
        d2 = STK.RawDetector(ck)
        flat = textured_pair(0, frame=0, flat=True)[0]
        d2.prob_raw(flat, bg)
        assert d2.reg_rejected == 1 and np.array_equal(d2.reg_fits[0], np.eye(2, 3, dtype=np.float32))
        ref = RAW.make_planes(flat, bg, (15, 4, 0))
        assert all(np.array_equal(d2.last_planes[k], ref[k]) for k in d2.last_planes)
        # 記録の無い ckpt は動かさない
        ck0 = os.path.join(td, "plain.pt")
        save_ckpt(ck0, model, [96, 128], INP)
        d3 = STK.RawDetector(ck0)
        d3.prob_raw(r0, bg)
        ref = RAW.make_planes(r0, bg, (15, 4, 0))
        assert d3.bg_register is None and d3.reg_summary() is None and not d3.reg_fits
        assert all(np.array_equal(d3.last_planes[k], ref[k]) for k in d3.last_planes)
        # 知らない bg_register は止まる。位置合わせだけの steel の ckpt も raw/・binarized/ では止まる
        save_ckpt(os.path.join(td, "bad.pt"), model, [96, 128], dict(INP, bg_register="rigid"))
        try:
            STK.RawDetector(os.path.join(td, "bad.pt"))
            raise AssertionError("知らない bg_register で止まらない")
        except ValueError:
            pass
        save_ckpt(os.path.join(td, "bin_reg.pt"), m3, [96, 128], {"mode": "bin", "preproc": [15, 4, 0], "bg_register": "affine"})
        for fn, path in ((RAW.RawDetector, "reg.pt"), (BIN.ckpt_uses_prior, "reg.pt"), (BIN.load_tau_model, "reg.pt"),
                         (RAW.RawDetector, "bin_reg.pt"), (BIN.ckpt_uses_prior, "bin_reg.pt"), (BIN.load_tau_model, "bin_reg.pt")):
            try:
                fn(os.path.join(td, path))
                raise AssertionError(f"{fn.__qualname__} が {path} で止まらない")
            except ValueError as e:
                assert "steel" in str(e), str(e)


def _steel_src(td):
    """鉄ブロックの Roboflow の書き出し (JPEG、名前は 'img000k_bmp.rf.<hash>.jpg') + 元の画像 (BMP) のフォルダ 2つ。
    orig には img0002 だけ無い。orig2 の img0002 は中身の違う画像、img0000 は大きさの違う画像"""
    src, orig, orig2 = (os.path.join(td, n) for n in ("steel_coco", "orig", "orig2"))
    os.makedirs(orig)
    os.makedirs(orig2)
    k = 0
    for split, n in (("train", 3), ("valid", 1), ("test", 1)):
        os.makedirs(os.path.join(src, split))
        images, anns = [], []
        for i in range(n):
            raw, bg = textured_pair(0, W_REAL + np.float32([[0, 0, 0.2 * k], [0, 0, -0.3 * k]]), frame=k)
            fn = f"img{k:04d}_bmp.rf.{k:08x}ef.jpg"
            cv2.imwrite(os.path.join(src, split, fn), raw, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if k != 2:
                cv2.imwrite(os.path.join(orig, f"img{k:04d}.bmp"), raw)
            images.append({"id": i, "file_name": fn, "height": raw.shape[0], "width": raw.shape[1]})
            for cx, cy, r in BUBBLES:
                cx += 6 * k
                anns.append({"id": len(anns), "image_id": i, "category_id": 1, "segmentation": [circle_poly(cx, cy, r + 2)],
                             "bbox": [cx - r - 2, cy - r - 2, 2 * r + 4, 2 * r + 4], "area": 3.14 * r * r, "iscrowd": 0})
            k += 1
        with open(os.path.join(src, split, "_annotations.coco.json"), "w") as fp:
            json.dump({"images": images, "annotations": anns, "categories": [{"id": 1, "name": "bubble"}]}, fp)
    bgp = os.path.join(td, "bg_steel.png")
    cv2.imwrite(bgp, bg)
    cv2.imwrite(os.path.join(orig2, "img0002.bmp"), textured_pair(5, frame=2)[0])
    cv2.imwrite(os.path.join(orig2, "img0000.bmp"), cv2.resize(cv2.imread(os.path.join(orig, "img0000.bmp")), (160, 120)))
    return src, orig, orig2, bgp


def test_i_originals():
    keep = {k: getattr(STR, k) for k in ("ORIGINAL_IMAGE_DIRS", "BG_MATCH", "BG_REGISTER", "BACKGROUNDS")}
    splits = {0: ("train", "train"), 1: ("train", "train"), 2: ("train", "train"), 3: ("valid", "val"), 4: ("test", "test")}
    with tempfile.TemporaryDirectory() as td:
        src, orig, orig2, bgp = _steel_src(td)

        def jpg(k):
            return cv2.imread(os.path.join(src, splits[k][0], f"img{k:04d}_bmp.rf.{k:08x}ef.jpg"))

        def bmp(k):
            return cv2.imread(os.path.join(orig, f"img{k:04d}.bmp"))

        try:
            idx = STR.index_originals([orig, orig2])
            img, path, dm = STR.find_original("img0000.bmp", jpg(0), idx)     # 大きさの違う同じ名前 (orig2) は使わない
            assert Path(path) == Path(orig) / "img0000.bmp" and np.array_equal(img, bmp(0)) and dm < STR.ORIGINAL_MAX_DIFF, (path, dm)
            img, path, dm = STR.find_original("img0001.jpg", jpg(1), idx)     # 拡張子だけ違う名前
            assert Path(path).name == "img0001.bmp" and np.array_equal(img, bmp(1)), path
            img, path, dm = STR.find_original("img0002.bmp", jpg(2), idx)     # 中身の違う同じ名前 -> 使わない
            assert img is None and path is None and dm > STR.ORIGINAL_MAX_DIFF, dm
            assert STR.find_original("img9999.bmp", jpg(0), idx) == (None, None, None)
            try:
                STR.index_originals([os.path.join(td, "none")])
                raise AssertionError("無いフォルダで止まらない")
            except FileNotFoundError:
                pass
            # データセット: 元の画像があれば元の画像 + 位置合わせ、無ければ書き出しの画像
            _configure(STR, td, src, "bin+sign", None)
            STR.BACKGROUNDS = {"img": bgp}
            STR.ORIGINAL_IMAGE_DIRS, STR.BG_MATCH, STR.BG_REGISTER = [orig, orig2], None, "affine"
            STR.build_dataset(src, STR.DST)
            bg = cv2.imread(bgp)
            for k, (_, split) in splits.items():
                raw = jpg(k) if k == 2 else bmp(k)
                want = STR.make_planes(raw, bg, STR.PREPROC, None, "affine")
                for key, sub in STR.PLANE_DIRS.items():
                    got = cv2.imread(os.path.join(STR.DST, sub, split, f"img{k:04d}_bmp.rf.{k:08x}ef.png"), cv2.IMREAD_GRAYSCALE)
                    assert got is not None and np.array_equal(got, want[key]), (k, key)
                if k != 2:
                    assert not np.array_equal(want["B"], STR.make_planes(jpg(k), bg, STR.PREPROC, None, "affine")["B"])
                    liq = textured_liquid(k)
                    assert (want["B"][liq] > 0).mean() < 0.01 < (STR.make_planes(raw, bg, STR.PREPROC)["B"][liq] > 0).mean(), k
        finally:
            for k, v in keep.items():
                setattr(STR, k, v)


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

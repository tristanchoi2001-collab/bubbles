"""
ゲートの較正の回帰テスト (2026-10-21: 小さい気泡の間隔ゲート SPACING_GATE_FRAC, ブートストラップの予測ずれ BOOTSTRAP_CHAIN_FRAMES)
=====================================================================
  a) 小さい気泡が1フレーム抜けた所に、隣の気泡が新しく現れる
       SPACING_GATE_FRAC = 0 (従来): 抜けた気泡のトラックが隣の気泡を奪う (誤連結)
       SPACING_GATE_FRAC = 0.7     : 奪わない (隣の気泡は新規トラック)。ほかの気泡のトラックは両方で同じ
  b) pair_cost の対象: 小さい気泡どうし・速度既知 (または PIV の初速度あり) だけ。
       大きい気泡、画面端に接する気泡、速度未知のトラック、予測に近い検出 には掛からない
  c) set_neighbor_distances: 同じフレームで一番近い別の検出 (中心) までの距離
  d) BOOTSTRAP_CHAIN_FRAMES = 3 は従来の計算 (3フレーム連続・前フレームと同じ速度の予測) と同じ値。
     5 はトラッカーと同じ予測 (最初の移動量 -> VELOCITY_EMA_ALPHA の EMA) からのずれ

対象: binarized/2_bin_track.py (tests/bundles.py が tracker3 の名前で読ませる)
使い方: リポジトリのルートで  python -B tests/test_gates.py     (pytest でも実行できる)
"""
import contextlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bundles         # noqa: E402,F401
import tracker3 as T   # noqa: E402

H, W = 240, 240


@contextlib.contextmanager
def settings(**kw):
    old = {k: getattr(T, k) for k in kw}
    for k, v in kw.items():
        setattr(T, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(T, k, v)


BASE = dict(USE_PIV_PRIOR=False, USE_FLOW_PRIOR=True, POS_GATE=15.0, MAX_SPEED=40.0, AREA_RATIO_GATE=1.8,
            MAX_AGE=3, MAX_AGE_NEW=1, TRANSIENT_MERGE_FRAMES=2, EDGE_TOUCH_PX=3, MIN_TRACK_AREA=10)


def disk_label(bubbles, h=H, w=W):
    """bubbles = [(x, y, r)] -> ラベル画像 (1..N)"""
    lab = np.zeros((h, w), np.int32)
    yy, xx = np.ogrid[:h, :w]
    for k, (x, y, r) in enumerate(bubbles, start=1):
        lab[(xx - x) ** 2 + (yy - y) ** 2 <= r * r] = k
    return lab


def detections(bubbles, h=H, w=W):
    return T.instances_to_detections(disk_label(bubbles, h, w), np.ones((h, w), bool))


def ids_by_x(rows, dets):
    """{検出の中心x (整数に丸め): トラックID}"""
    return {int(round(dets[r["det_index"]].cx)): r["track_id"] for r in rows if r["det_index"] is not None}


# ==============================================================
def scenario_a(frac):
    """4個の小さい気泡 (半径3, 約29 px) が横に 16 px 間隔で並び、上へ 6 px/フレーム。
    P (x=100) はフレーム 0〜2 で見えてフレーム 3 で抜ける。Q (x=116) はフレーム 3 で初めて現れる"""
    xs = {"P": 100, "Q": 116, "R": 132, "S": 148}
    frames = []
    for f in range(5):
        y = 200 - 6 * f
        bs = []
        for name, x in xs.items():
            if name == "P" and f == 3:
                continue
            if name == "Q" and f < 3:
                continue
            bs.append((x, y, 3))
        frames.append(detections(bs))
    with settings(**BASE, SPACING_GATE_FRAC=frac):
        rows = T.run_laptrack(frames, (H, W))
    return {f: ids_by_x(rows[f], frames[f]) for f in range(len(frames))}


def test_a_spacing_gate_stops_neighbour_theft():
    off, on = scenario_a(0.0), scenario_a(0.7)
    p_id = off[2][100]
    assert off[3][116] == p_id, f"前提: ゲートなしでは P のトラックが Q を奪う ({off[3]})"
    p_id_on = on[2][100]
    assert on[3][116] != p_id_on, f"間隔ゲートありでは奪わない ({on[3]})"
    for f in (0, 1, 2, 3, 4):     # R と S は両方で同じトラックのまま
        for x in (132, 148):
            assert (off[f][x] == off[0][x]) and (on[f][x] == on[0][x])


# ==============================================================
def _track_from(d, vx=0.0, vy=-6.0, v_known=True, prior_src=""):
    return T.Track(track_id=1, leading_x=d.leading_x, leading_y=d.leading_y, cx=d.cx, cy=d.cy, area=d.area,
                   shape=d.shape, touch=d.touch, vx=vx, vy=vy, v_known=v_known,
                   prior_vx=vx if prior_src else 0.0, prior_vy=vy if prior_src else 0.0, prior_src=prior_src,
                   last_frame=0)


def _pair(r, offset, nn, y0=120, x0=100, edge=False, **kw):
    """半径 r の気泡のトラック (フレーム0, 速度 (0, -6)) と、予測位置から x 方向に offset ずれた検出 (フレーム1)"""
    xa = 1 + r if edge else x0
    a = detections([(xa, y0, r)])[0]
    b = detections([(xa + offset, y0 - 6, r)])[0]
    b.nn_dist = nn
    return _track_from(a, **kw), b


def test_b_pair_cost_scope():
    with settings(**BASE, SPACING_GATE_FRAC=0.7, SPACING_GATE_MAX_AREA=500):
        t, d = _pair(3, 12, 14.0)
        assert T.pair_cost(t, d, 1) is None, "小さい気泡: 予測から 12 px > 0.7 × 14 px なら つながない"
        t, d = _pair(3, 12, 40.0)
        assert T.pair_cost(t, d, 1) is not None, "隣が遠ければ (0.7 × 40 = 28 > 12) つなぐ"
        t, d = _pair(3, 2, 14.0)
        assert T.pair_cost(t, d, 1) is not None, "予測に近い検出はつなぐ"
        t, d = _pair(14, 14, 15.0)            # 面積 約 615 px >= 500
        assert T.pair_cost(t, d, 1) is not None, "大きい気泡には掛けない"
        t, d = _pair(3, 12, 14.0, edge=True)
        assert any(t.touch) and T.pair_cost(t, d, 1) is not None, "画面端に接する気泡には掛けない"
        t, d = _pair(3, 12, 14.0, v_known=False)
        assert T.pair_cost(t, d, 1) is not None, "速度未知 (PIV なし) のトラックには掛けない"
        t, d = _pair(3, 12, 14.0, v_known=False, prior_src="piv")
        with settings(PIV_GATE=20.0, PIV_KEEP_STATIC=False):
            assert T.pair_cost(t, d, 1) is None, "PIV の初速度があるトラックには掛ける"
    with settings(**BASE, SPACING_GATE_FRAC=0.0):
        t, d = _pair(3, 12, 14.0)
        assert T.pair_cost(t, d, 1) is not None, "0 で無効"


def test_c_neighbor_distances():
    ds = detections([(50, 50, 3), (70, 50, 3), (50, 90, 3)])
    T.set_neighbor_distances(ds)
    got = sorted(round(d.nn_dist, 1) for d in ds)
    assert got == [20.0, 20.0, 40.0], got
    one = detections([(50, 50, 3)])
    T.set_neighbor_distances(one)
    assert one[0].nn_dist == math.inf


# ==============================================================
def _jitter_sequence(n_frames=12, seed=0):
    """離れた中くらいの気泡 12個が上へ平均 8 px/フレーム、毎フレーム ±2 px 揺らぐ"""
    rng = np.random.default_rng(seed)
    base = [(30 + 45 * (k % 4), 60 + 60 * (k // 4)) for k in range(12)]
    vel = [(rng.uniform(-1, 1), -8 + rng.uniform(-1, 1)) for _ in base]
    frames = []
    for f in range(n_frames):
        bs = []
        for (x, y), (vx, vy) in zip(base, vel):
            bs.append((x + vx * f + rng.uniform(-2, 2), y + vy * f + rng.uniform(-2, 2) + 100, 6))
        frames.append(detections(bs, h=400))
    return frames


def _old_resid(dets_pf):
    """従来の計算 (BOOTSTRAP_CHAIN_FRAMES 導入前のコードと同じ)"""
    total = len(dets_pf)
    n_seg = min(T.BOOTSTRAP_NUM_SEGMENTS, total - 1)
    fs = sorted(set(int(round(k * (total - 2) / max(1, n_seg - 1))) for k in range(n_seg)))
    out = []
    for f in fs:
        if f + 2 >= total:
            continue
        p = T._bootstrap_confident_pairs(dets_pf[f], dets_pf[f + 1])
        p2 = T._bootstrap_confident_pairs(dets_pf[f + 1], dets_pf[f + 2])
        A, B, C = dets_pf[f], dets_pf[f + 1], dets_pf[f + 2]
        for i, j in p.items():
            if j not in p2:
                continue
            a, b, c = A[i], B[j], C[p2[j]]
            dx1, dy1, _ = T.displacement(a, b)
            dx2, dy2, _ = T.displacement(b, c)
            out.append(max(0.0, math.hypot(dx2 - dx1, dy2 - dy1) - T.POS_GATE_SIZE_FRAC * T.eq_diameter(b.area)))
    return sorted(out)


def _ema_resid(dets_pf, n_chain):
    """トラッカーと同じ予測で、最大 n_chain フレームの鎖のずれ"""
    total = len(dets_pf)
    n_seg = min(T.BOOTSTRAP_NUM_SEGMENTS, total - 1)
    fs = sorted(set(int(round(k * (total - 2) / max(1, n_seg - 1))) for k in range(n_seg)))
    out = []
    for f in fs:
        p = T._bootstrap_confident_pairs(dets_pf[f], dets_pf[f + 1])
        for i, j in p.items():
            obs = [dets_pf[f][i], dets_pf[f + 1][j]]
            g, cur = f + 1, j
            while len(obs) < n_chain and g + 1 < total:
                pg = T._bootstrap_confident_pairs(dets_pf[g], dets_pf[g + 1])
                if cur not in pg:
                    break
                cur = pg[cur]
                g += 1
                obs.append(dets_pf[g][cur])
            if len(obs) < 3:
                continue
            tr = _track_from(obs[0], v_known=False)
            tr.v_known = False
            tr.observe(obs[1], 1)                      # トラッカーと同じ速度の更新 (Track.observe)
            for k in range(2, len(obs)):
                dx, dy, _ = T.displacement(obs[k - 1], obs[k])
                res = math.hypot(dx - tr.vx, dy - tr.vy)
                out.append(max(0.0, res - T.POS_GATE_SIZE_FRAC * T.eq_diameter(obs[k - 1].area)))
                tr.observe(obs[k], k)
    return sorted(out)


def test_d_bootstrap_chain():
    dets_pf = _jitter_sequence()
    with settings(USE_PIV_PRIOR=False, BOOTSTRAP_CHAIN_FRAMES=3):
        _, resid3, _, q3, _ = T._bootstrap_collect_stats(dets_pf, (400, W))
    ref3 = _old_resid(dets_pf)
    assert len(ref3) > 20 and np.allclose(sorted(resid3), ref3), (len(resid3), len(ref3))
    with settings(USE_PIV_PRIOR=False, BOOTSTRAP_CHAIN_FRAMES=5):
        _, resid5, _, q5, _ = T._bootstrap_collect_stats(dets_pf, (400, W))
    ref5 = _ema_resid(dets_pf, 5)
    assert len(ref5) > len(ref3) and np.allclose(sorted(resid5), ref5), (len(resid5), len(ref5))
    assert q5["chains"] == len(resid5)
    # 位置の揺らぎ (測定誤差) だけなら EMA の予測のほうがずれが小さい (等速の予測の約 0.75 倍)
    assert np.percentile(resid5, 95) < np.percentile(resid3, 95), (np.percentile(resid5, 95), np.percentile(resid3, 95))


TESTS = [test_a_spacing_gate_stops_neighbour_theft, test_b_pair_cost_scope, test_c_neighbor_distances,
         test_d_bootstrap_chain]

if __name__ == "__main__":
    ok = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  OK   {fn.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{ok} / {len(TESTS)} 合格")
    sys.exit(0 if ok == len(TESTS) else 1)

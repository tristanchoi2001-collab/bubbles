"""
確率マップ -> 気泡ラベルマップ (tracker3.extract_instances / extract_instances_seed) の回帰テスト
=====================================================================
  a) 劣化のない確率マップ (fake_detector.fake_prob) では "seed" も "wall" (従来) と同じ気泡を同じ形で出す
  b) 外周の境界が途切れた大きい気泡: "seed" は気泡全体を出す (芯が種なので背景に漏れない)
  c) "hybrid": 劣化のない確率マップでは "wall" と画素・ラベルとも完全に同じ
  d) "hybrid": 外周の境界が途切れた大きい気泡を、"wall" と同じ形の決め方で取り戻す (ほかの気泡は "wall" のまま)
  e) リング気泡 (ring_max > 0): 穴の小さいリングが2個くっついたもの (従来は 面積 > tiny_max で消えていた) を2個の気泡として拾う
  f) リング気泡: 大きい気泡に接した小さいリング (従来は「既にある気泡から 2px 以内」で消えていた) を拾う。
     大きい気泡の画素は変えず、拾った気泡に大きい気泡の輪郭の残りを含めない
  g) リング気泡: 穴が液 (内部確率が低い) の輪は拾わない
  h) リング気泡: wall / hybrid とも、従来の気泡はすべて画素まで同じで、足すだけ
  i) リング気泡: 小気泡の経路で1個にしていた小さいくっついたリング (面積 <= tiny_max) を2個に分ける
  j) リング気泡: 太い境界の中の 1px の芯 (弱い種) から大きい気泡を作らない
  k) リング気泡: 主経路の帯の判定で背景とされた領域を気泡にしない
  l) リング気泡: 穴を横切る細い境界の線で1個の気泡を2個に割らない
  m) リング気泡: 画面の端にかかる気泡は拾わない
  n) 気泡の中の気泡 (UNET_DROP_NESTED): 大きい気泡の中 (周りがその気泡) の気泡は除き、
     液の島 (周りが背景) の中の気泡と、大きい気泡に接しているだけの気泡は残す。外側の気泡は変えない
対象: binarized/2_bin_track.py (元 tracker3.py。tests/bundles.py が tracker3 の名前で読ませる)
使い方: リポジトリのルートで  python -B tests/test_instances.py     (pytest でも実行できる)
"""
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bundles         # noqa: E402,F401  (tracker3 などの名前で binarized/2_bin_track.py を読む)

import fake_detector   # noqa: E402
import tracker3 as T   # noqa: E402

H, W = 300, 240


def disk(cx, cy, r):
    yy, xx = np.ogrid[:H, :W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


def scene():
    """大きい気泡 1 + 小気泡 2 + 接している小気泡のペア"""
    lab = np.zeros((H, W), np.int32)
    lab[disk(80, 100, 40)] = 1
    lab[disk(180, 60, 8)] = 2
    lab[disk(180, 200, 3)] = 3
    lab[disk(60, 230, 9) & (lab == 0)] = 4
    lab[disk(78, 230, 9) & (lab == 0)] = 5
    return lab


def match(lab, inst):
    """正解ごとに、最も重なる検出との IoU"""
    out = {}
    for g in range(1, lab.max() + 1):
        m = lab == g
        ids, cnt = np.unique(inst[m], return_counts=True)
        cnt[ids == 0] = 0
        if cnt.max() == 0:
            out[g] = 0.0
            continue
        d = ids[cnt.argmax()]
        inter = cnt.max()
        out[g] = inter / (m.sum() + (inst == d).sum() - inter)
    return out


def test_a_clean_same_as_wall():
    lab = scene()
    p = fake_detector.fake_prob(lab)
    wall = T.extract_instances(p, 4, 25, 0.5, 2, 300)
    seed = T.extract_instances_seed(p, 4, 0.5, 300, 0.5)
    assert wall.max() == seed.max(), f"気泡の数が違う: wall {wall.max()} / seed {seed.max()}"
    mw, ms = match(lab, wall), match(lab, seed)
    for g in mw:
        assert abs(mw[g] - ms[g]) < 0.1, f"正解 {g}: IoU wall {mw[g]:.2f} / seed {ms[g]:.2f}"


def test_b_gap_in_outer_wall():
    lab = scene()
    p = fake_detector.fake_prob(lab)
    # 大きい気泡の右側の境界を 8px 幅で消す (薄い輪郭が切れた状況)。消した分は背景確率へ
    cut = (np.abs(np.arange(H)[:, None] - 100) <= 4) & (np.arange(W)[None, :] >= 110) & (np.arange(W)[None, :] <= 125)
    cut &= p[2] > 0.5
    p[0][cut] += p[2][cut]
    p[2][cut] = 0.0
    seed = T.extract_instances_seed(p, 4, 0.5, 300, 0.5)
    iou = match(lab, seed)[1]
    assert iou > 0.85, f"seed: 境界が途切れた大きい気泡の IoU {iou:.2f}"
    wall = T.extract_instances(p, 4, 25, 0.5, 2, 300)
    print(f"    境界が途切れた大きい気泡の IoU: wall {match(lab, wall)[1]:.2f} / seed {iou:.2f}")


def soft_prob(lab):
    """実際の U-Net に近い確率マップ: 気泡の縁の内側 3px を境界、その内側を内部とし、σ=0.7 でぼかす"""
    ring = np.zeros(lab.shape, bool)
    for g in range(1, lab.max() + 1):
        m = lab == g
        ring |= m & ~ndimage.binary_erosion(m, iterations=2)
    p = np.stack([lab == 0, (lab > 0) & ~ring, ring]).astype(np.float32)
    p = np.stack([ndimage.gaussian_filter(c, 0.7) for c in p])
    return p / p.sum(0, keepdims=True)


def cut_scene():
    """soft_prob で、大きい気泡 (正解 1) の右側の境界確率を 9px の長さだけ 0.25 に下げたもの
    (実データ 742 の大きい気泡と同じく、壁が「弱い」切れ目)"""
    lab = scene()
    p = soft_prob(lab)
    cut = (np.abs(np.arange(H)[:, None] - 100) <= 4) & (np.arange(W)[None, :] >= 110) & (np.arange(W)[None, :] <= 130)
    cut &= p[2] > 0.25
    p[0][cut] += p[2][cut] - 0.25
    p[2][cut] = 0.25
    return lab, p


def test_c_hybrid_clean_identical_to_wall():
    for p in (fake_detector.fake_prob(scene()), soft_prob(scene())):
        st = {}
        hyb = T.extract_instances_hybrid(p, 4, 25, 0.5, 2, 300, stats=st)
        assert np.array_equal(hyb, T.extract_instances(p, 4, 25, 0.5, 2, 300)), "hybrid が劣化のない確率マップで wall と違う"
        assert st.get("rescued", 0) == 0


def test_d_hybrid_rescues_gap():
    lab, p = cut_scene()
    st = {}
    hyb = T.extract_instances_hybrid(p, 4, 25, 0.5, 2, 300, stats=st)
    wall = T.extract_instances(p, 4, 25, 0.5, 2, 300)
    mh, mw = match(lab, hyb), match(lab, wall)
    print(f"    境界が途切れた大きい気泡の IoU: wall {mw[1]:.2f} / hybrid {mh[1]:.2f} (救済 {st.get('rescued', 0)} 個)")
    assert st.get("rescued", 0) == 1 and mh[1] > 0.9, f"hybrid: IoU {mh[1]:.2f}, 救済 {st.get('rescued', 0)}"
    for g in range(2, lab.max() + 1):   # ほかの気泡は wall と同じ
        assert abs(mh[g] - mw[g]) < 1e-9, f"正解 {g}: wall {mw[g]:.2f} / hybrid {mh[g]:.2f}"


def ring_scene():
    """内部確率 1 の穴 (半径 2.5) + 境界確率 1 の厚いリング (外半径 8) の気泡。
    1, 2 = くっついたリング2個 / 3 = 大きい円 (半径 30) / 4 = 3 に接した小さいリング /
    5 = 離れた普通の小さいリング (従来の小気泡の経路で拾える) / 穴が液の輪 (正解の気泡ではないのでラベル 0)"""
    yy, xx = np.ogrid[:H, :W]
    lab = np.zeros((H, W), np.int32)
    pin = np.zeros((H, W), np.float32)
    pedge = np.zeros((H, W), np.float32)

    def ring(cx, cy, r_hole, r_out, gid, hole_is_bubble=True):
        d2 = (xx - cx) ** 2 + (yy - cy) ** 2
        ann = (d2 > r_hole ** 2) & (d2 <= r_out ** 2) & (pedge == 0) & (pin == 0)
        hole = (d2 <= r_hole ** 2) & (pedge == 0) & (pin == 0)
        pedge[ann] = 1
        if hole_is_bubble:
            pin[hole] = 1
        if gid:
            lab[(ann | hole) & (lab == 0)] = gid
    ring(60, 60, 2.5, 8, 1)
    ring(60, 76, 2.5, 8, 2)                       # 1 の真下にくっつく
    d2 = (xx - 160) ** 2 + (yy - 80) ** 2
    big_edge = (d2 <= 30 ** 2) & (d2 > 28 ** 2)
    pedge[big_edge] = 1
    pin[(d2 <= 28 ** 2)] = 1
    lab[d2 <= 30 ** 2] = 3
    ring(160, 118, 2.5, 8, 4)                     # 大きい円の下端 (y = 110) に接する
    ring(60, 200, 10, 15, 0, hole_is_bubble=False)   # 穴が液の輪
    ring(170, 230, 2.5, 7, 5)                     # 離れた小さいリング (面積 < 300)
    pbg = np.clip(1.0 - pin - pedge, 0, 1)
    p = np.stack([pbg, pin, pedge]).astype(np.float32)
    p = np.stack([ndimage.gaussian_filter(c, 0.5) for c in p])
    return lab, p / p.sum(0, keepdims=True)


def test_e_ring_pair():
    lab, p = ring_scene()
    off = T.extract_instances(p, 4, 25, 0.5, 2, 300)
    st = {}
    on = T.extract_instances(p, 4, 25, 0.5, 2, 300, ring_max=600, stats=st)
    mo, mn = match(lab, off), match(lab, on)
    print(f"    くっついたリング IoU: 従来 {mo[1]:.2f}, {mo[2]:.2f} / リング気泡あり {mn[1]:.2f}, {mn[2]:.2f} (拾った {st.get('ring')} 個)")
    assert mo[1] == 0 and mo[2] == 0, "従来の方式で消えていない (テストの前提が崩れた)"
    assert mn[1] > 0.75 and mn[2] > 0.75, (mn[1], mn[2])
    assert on[lab == 1].max() != on[lab == 2].max(), "2個が1個のまま"


def test_f_ring_touching_large():
    lab, p = ring_scene()
    off = T.extract_instances(p, 4, 25, 0.5, 2, 300)
    on = T.extract_instances(p, 4, 25, 0.5, 2, 300, ring_max=600)
    mo, mn = match(lab, off), match(lab, on)
    print(f"    大きい気泡に接したリング IoU: 従来 {mo[4]:.2f} / リング気泡あり {mn[4]:.2f}, 大きい気泡 {mo[3]:.2f} -> {mn[3]:.2f}")
    assert mo[4] == 0, "従来の方式で消えていない (テストの前提が崩れた)"
    assert mn[4] > 0.75, mn[4]
    assert abs(mn[3] - mo[3]) < 1e-9
    d = np.bincount(on[lab == 4]).argmax()
    assert (on == d).sum() <= 1.3 * (lab == 4).sum(), "大きい気泡の輪郭の残りまで含んでいる"


def test_g_ring_not_liquid_loop():
    lab, p = ring_scene()
    on = T.extract_instances(p, 4, 25, 0.5, 2, 300, ring_max=600)
    yy, xx = np.ogrid[:H, :W]
    loop = (xx - 60) ** 2 + (yy - 200) ** 2 <= 15 ** 2
    assert not on[loop].any(), "穴が液の輪を気泡にした"


def test_h_ring_only_adds():
    lab, p = ring_scene()
    for name, f in (("wall", lambda **kw: T.extract_instances(p, 4, 25, 0.5, 2, 300, **kw)),
                    ("hybrid", lambda **kw: T.extract_instances_hybrid(p, 4, 25, 0.5, 2, 300, **kw))):
        off, on = f(), f(ring_max=600)
        for g in np.unique(off[off > 0]):
            m = off == g
            v = np.unique(on[m])
            assert v.size == 1 and v[0] > 0 and (on == v[0]).sum() == m.sum(), f"{name}: 従来の気泡 {g} が変わった"
        assert match(lab, on)[5] == match(lab, off)[5] > 0.75


def _p(pin, pedge, sigma=0.5):
    p = np.stack([np.clip(1 - pin - pedge, 0, 1), pin, pedge]).astype(np.float32)
    if sigma:
        p = np.stack([ndimage.gaussian_filter(c, sigma) for c in p])
    return (p / p.sum(0, keepdims=True)).astype(np.float32)


def _ring(pin, pedge, cx, cy, rh, ro):
    yy, xx = np.ogrid[:pin.shape[0], :pin.shape[1]]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    ann = (d2 > rh * rh) & (d2 <= ro * ro) & (pedge == 0) & (pin == 0)
    ho = (d2 <= rh * rh) & (pedge == 0) & (pin == 0)
    pedge[ann] = 1
    pin[ho] = 1


def _big(pin, pedge, cx, cy, r=30, wall=2):
    yy, xx = np.ogrid[:pin.shape[0], :pin.shape[1]]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    pedge[(d <= r) & (d > r - wall)] = 1
    pin[d <= r - wall] = 1


def _ring_on_off(p):
    return T.extract_instances(p, 4, 25, 0.5, 2, 300), T.extract_instances(p, 4, 25, 0.5, 2, 300, ring_max=600)


def test_i_small_pair_split():
    pin, pedge = np.zeros((120, 120), np.float32), np.zeros((120, 120), np.float32)
    _ring(pin, pedge, 50, 50, 2, 5)
    _ring(pin, pedge, 50, 60, 2, 5)                 # 合わせても 300px 未満
    off, on = _ring_on_off(_p(pin, pedge))
    print(f"    小さいくっついたリング: 従来 {off.max()} 個 / リング気泡あり {on.max()} 個")
    assert off.max() == 1 and on.max() == 2
    assert set(np.unique(on[off > 0])) == {1, 2} and not ((on > 0) & (off == 0)).any(), "画素が増えた/移った"


def test_j_weak_seed():
    pin, pedge = np.zeros((60, 60), np.float32), np.ones((60, 60), np.float32)
    pin[30, 30], pedge[30, 30] = 1, 0
    off, on = _ring_on_off(_p(pin, pedge, 0))
    assert on.max() == off.max(), "1px の芯から気泡を作った"


def test_k_band_rejected_region():
    yy, xx = np.ogrid[:120, :120]
    d2 = (xx - 60) ** 2 + (yy - 60) ** 2
    pedge = ((d2 > 144) & (d2 <= 225)).astype(np.float32)
    pin = np.where((d2 <= 144) & (xx < 48 + 0.62 * 25), 0.6, 0).astype(np.float32)
    off, on = _ring_on_off(_p(pin, pedge))
    assert on.max() == off.max(), "帯の判定で背景とされた領域を気泡にした"


def test_l_line_across_hole():
    pin, pedge = np.zeros((140, 140), np.float32), np.zeros((140, 140), np.float32)
    _big(pin, pedge, 70, 40)
    _ring(pin, pedge, 70, 79, 3.5, 9)               # 大きい気泡の下端に接したリング
    pedge[72:87, 70] = 1                            # 穴を横切る 1px の線
    pin[72:87, 70] = 0
    off, on = _ring_on_off(_p(pin, pedge))
    yy, xx = np.ogrid[:140, :140]
    gt = (xx - 70) ** 2 + (yy - 79) ** 2 <= 81
    new = np.unique(on[gt & (off == 0) & (on > 0)])
    print(f"    穴を横切る線のあるリング: 拾った気泡 {len(new)} 個")
    assert len(new) == 1


def test_m_frame_edge():
    def scene(x_ring):
        pin, pedge = np.zeros((160, 120), np.float32), np.zeros((160, 120), np.float32)
        _big(pin, pedge, x_ring + 36, 79, r=28)
        _ring(pin, pedge, x_ring, 79, 2.5, 8)       # 大きい気泡の左端に接したリング
        return _p(pin, pedge)
    yy, xx = np.ogrid[:160, :120]
    for x_ring, expect in ((30, True), (9, False)):   # 画面の中 -> 拾う / 左端から 1px -> 拾わない
        off, on = _ring_on_off(scene(x_ring))
        got = bool(((on > 0) & (off == 0) & ((xx - x_ring) ** 2 + (yy - 79) ** 2 <= 9)).any())
        assert got == expect, (x_ring, got)

def test_n_drop_nested():
    yy, xx = np.ogrid[:240, :200]
    pin, pedge = np.zeros((240, 200), np.float32), np.zeros((240, 200), np.float32)
    _big(pin, pedge, 60, 60, r=45)
    pin[(xx - 60) ** 2 + (yy - 60) ** 2 <= 10 ** 2] = 0    # 大きい気泡の中 (気体) のリング (穴が closing で埋まらない大きさ)
    _ring(pin, pedge, 60, 60, 6, 10)
    _big(pin, pedge, 140, 170, r=50)
    d2 = (xx - 140) ** 2 + (yy - 170) ** 2
    pin[d2 <= 22 ** 2] = 0                                 # 液の島 (半径 20) とその壁
    pedge[(d2 <= 22 ** 2) & (d2 > 20 ** 2)] = 1
    _ring(pin, pedge, 140, 170, 2.5, 7)                    # 液の島の中の気泡
    _ring(pin, pedge, 60, 113, 2.5, 8)                     # 1つ目の大きい気泡の下端に接している気泡
    p = _p(pin, pedge)
    old = T.UNET_DROP_NESTED
    try:
        T.UNET_DROP_NESTED = False
        keep = T.unet_instances(p, "wall")
        T.UNET_DROP_NESTED = True
        st = {}
        out = T.unet_instances(p, "wall", stats=st)
    finally:
        T.UNET_DROP_NESTED = old
    def lab_at(m, x, y):
        return int(m[y, x])
    print(f"    気泡の中の気泡: 除外 {st.get('nested', 0)} 個")
    assert lab_at(keep, 60, 60) > 0 and lab_at(out, 60, 60) == 0, "気体の中の気泡が残った (または元々ない)"
    assert lab_at(out, 140, 170) > 0, "液の島の中の気泡を消した"
    assert lab_at(out, 60, 113) > 0, "接しているだけの気泡を消した"
    big = lab_at(keep, 60, 25)
    assert big > 0 and np.array_equal(out == big, keep == big), "外側の気泡が変わった"
    assert st.get("nested") == 1


def main() -> int:
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = []
    for n, f in tests:
        try:
            f()
            print(f"[合格] {n}")
        except AssertionError as e:
            failed.append(n)
            print(f"[不合格] {n}\n{e}")
    print(f"\n{len(tests) - len(failed)} / {len(tests)} 合格")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

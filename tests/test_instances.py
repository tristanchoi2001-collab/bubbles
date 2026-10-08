"""
確率マップ -> 気泡ラベルマップ (tracker3.extract_instances / extract_instances_seed) の回帰テスト
=====================================================================
  a) 劣化のない確率マップ (fake_detector.fake_prob) では "seed" も "wall" (従来) と同じ気泡を同じ形で出す
  b) 外周の境界が途切れた大きい気泡: "seed" は気泡全体を出す (芯が種なので背景に漏れない)
  c) "hybrid": 劣化のない確率マップでは "wall" と画素・ラベルとも完全に同じ
  d) "hybrid": 外周の境界が途切れた大きい気泡を、"wall" と同じ形の決め方で取り戻す (ほかの気泡は "wall" のまま)
使い方: リポジトリのルートで  python -B tests/test_instances.py     (pytest でも実行できる)
"""
import os
import sys

import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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

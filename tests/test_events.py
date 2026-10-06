"""
合体・分裂・新規の判定の回帰テスト (docs/PIV_TASK.md 6-3)
=====================================================================
正解ラベル画像 (0=背景, 1..N=気泡) の短い系列を作り、fake_detector.fake_detect でトラッカー自身の
extract_instances を通した検出に変換してから tracker3.run_laptrack を実行する。
判定 (new / merge / merged_into / split) を「どの正解気泡で始まったトラックか」で表したイベント列にして
(トラックIDの番号に依存しない)、次を確認する。
  (1) PIV prior なし (USE_PIV_PRIOR = False) の結果が期待どおり
  (2) PIV prior あり (USE_PIV_PRIOR = True) の結果が なし と同じ (同じフレームで同じ判定)
  (3) 対応付けが同じなら compute_velocity_ema の速度 (CSV の 上昇速度 の列) も同じ (速度場は予測専用)

シナリオ (画像は 縦 H=600〜1174 / 横 W=464、上向きの流れ = y が減る方向):
  a) 後ろの速いスラグが前のスラグの後端に追いついて合体
       -> 合体フレーム f に merge 1行 (主 = 2本のどちらか)、もう一方は merged_into_<主>。その後は1トラック
  b) スラグの前後分裂 (2片が離れていく)
       -> f に split 1行 (parent_ids = [親])、親のIDは片方の片が引き継ぐ
  c) 動いているスラグの横に小気泡が新しく現れる (スラグの直前の位置とは重ならない)
       -> 小気泡は最初のフレームで new、スラグは normal のまま
  d) 3個が同じフレームで合体 (面積保存)
       -> f に merge 1行 (親2つ) + merged_into 2行
  e) 親が1対1対応しない3分裂 (どの片も 親の面積 / AREA_RATIO_GATE より小さい)
       -> 最大の片が親のIDを継承し、残り2片が split (parent_ids = [親])
  f) 画面上端からの退出 (誤った合体/分裂なし、トラックはそこで終わる) /
     途中の空フレーム (落ちない。速度既知の気泡は 空フレーム1枚をまたいで同じID: MAX_AGE = 3)
合体は TRANSIENT_MERGE_FRAMES より長く続ける (短いと tracker3 が「接触」として書き換えるため)。

イベント列の要素: (フレーム, イベント, トラック名, 相手のトラック名のタプル)
  トラック名 = "g<最初に対応した検出の正解ID>" (同じ正解IDで始まったトラックが2本目以降なら "#2" などを付ける)
  イベント   = new / merge / split / merged_into (normal は含めない)
  相手       = merge: 吸収したトラック, split: 親, merged_into: 吸収先のトラック

使い方: リポジトリのルートで  python -B tests/test_events.py     (pytest でも実行できる)
"""
import csv
import importlib
import inspect
import math
import os
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import fake_detector   # noqa: E402
import tracker3        # noqa: E402

W = 464                 # 画像の横幅 (px)
CSV_VY_COL = "上昇速度(px/frame)"

# 記録 (スクリプト実行時の表示用)
NOTES: list = []
OBSERVED: dict = {}


# ==============================================================
# 1. 正解ラベル画像の作図
# ==============================================================
def capsule(H: int, cx: float, cy: float, w: float, h: float) -> np.ndarray:
    """縦長の角丸長方形 (上下が半円のカプセル形) の boolマスク。幅 w, 高さ h, 中心 (cx, cy)。h <= w なら円"""
    r = w / 2.0
    half = max(h / 2.0 - r, 0.0)
    yy, xx = np.ogrid[:H, :W]
    dy = yy - cy
    dy = dy - np.clip(dy, -half, half)      # 中心線の線分からの縦方向のはみ出し
    return (xx - cx) ** 2 + dy ** 2 <= r * r


def circle(H: int, cx: float, cy: float, r: float) -> np.ndarray:
    return capsule(H, cx, cy, 2.0 * r, 2.0 * r)


def capsule_h_for_area(area: float, w: float) -> float:
    """幅 w のカプセルで面積 area になる高さ"""
    return (area + (4.0 - math.pi) * (w / 2.0) ** 2) / w


def blank(H: int) -> np.ndarray:
    return np.zeros((H, W), np.int32)


def paint(lab: np.ndarray, mask: np.ndarray, gid: int):
    assert not (lab[mask] > 0).any(), f"シナリオ作図の誤り: 正解ID {gid} が別の気泡と重なっている"
    lab[mask] = gid


def frames_after_merge() -> int:
    """合体の後に続けるフレーム数 (TRANSIENT_MERGE_FRAMES より長く)"""
    return tracker3.TRANSIENT_MERGE_FRAMES + 3


# ==============================================================
# 2. トラッカーの実行と結果の要約
# ==============================================================
@dataclass
class Result:
    events: list                     # [(フレーム, イベント, トラック名, 相手のタプル)]
    links: dict                      # (フレーム, 正解ID) -> トラック名
    row_sig: list                    # 全行の (フレーム, イベント, トラック名, 相手, 正解ID)。対応付けの比較用
    vy_rows: list                    # CSV の (フレーム, トラック名, イベント, 上昇速度の文字列)
    missing: list = field(default_factory=list)   # 検出できなかった正解気泡 (フレーム, 正解ID)
    prior_counts: dict = field(default_factory=dict)   # 新規トラックの初速度の出どころ (piv / flow / zero)


def load_tracker(piv: bool):
    """tracker3 を読み直して (グローバル設定を既定値に戻す) PIV prior の有無を設定する。
    USE_PIV_PRIOR がまだ無いときは piv=True なら None を返す (PIV prior なしだけを検証する)"""
    T = importlib.reload(tracker3)
    if hasattr(T, "USE_PIV_PRIOR"):
        T.USE_PIV_PRIOR = piv
    elif piv:
        return None
    return T


def piv_available() -> bool:
    ok = hasattr(tracker3, "USE_PIV_PRIOR")
    if not ok:
        msg = "tracker3.USE_PIV_PRIOR がまだ無いので PIV prior なしだけを検証 (あり/なしの比較は省略)"
        if msg not in NOTES:
            NOTES.append(msg)
    return ok


def call_run_laptrack(T, dets_per_frame, image_size):
    """run_laptrack(..., image_size=(H, W)) を呼ぶ。引数がまだ無ければ従来の形で呼ぶ"""
    if "image_size" in inspect.signature(T.run_laptrack).parameters:
        return T.run_laptrack(dets_per_frame, image_size=image_size)
    msg = "tracker3.run_laptrack が image_size 引数をまだ受け付けないので run_laptrack(検出) で実行"
    if msg not in NOTES:
        NOTES.append(msg)
    return T.run_laptrack(dets_per_frame)


def detect_all(T, frames):
    """正解ラベル画像の系列 -> (検出リストの系列, 各検出の正解IDの系列, 検出できなかった正解気泡)
    検出器で正解を復元できているか (くっついた検出が無いか) もここで確認する (シナリオ作図の確認)"""
    dets_all, gids_all, missing = [], [], []
    for f, gt in enumerate(frames):
        dets, gids, n_gt = fake_detector.fake_detect(T, gt)
        assert all(n == 1 for n in n_gt), f"フレーム {f}: 正解気泡がくっついた検出がある (正解ID {gids}, 含む数 {n_gt})"
        assert len(set(gids)) == len(gids), f"フレーム {f}: 1つの正解気泡が複数の検出に分かれた ({gids})"
        present = set(np.unique(gt)) - {0}
        H, Wd = gt.shape
        for g in sorted(present - set(gids)):
            ys, xs = np.nonzero(gt == g)
            at_edge = ys.min() == 0 or ys.max() == H - 1 or xs.min() == 0 or xs.max() == Wd - 1
            assert at_edge, f"フレーム {f}: 画面内の正解気泡 {g} が検出されない"
            missing.append((f, int(g)))   # 画面端の切れ端は検出器が拾えないことがある
        dets_all.append(dets)
        gids_all.append(gids)
    return dets_all, gids_all, missing


def summarize(T, rows_by_frame, dets_all, gids_all, missing) -> Result:
    n_frames = len(dets_all)
    # トラック名: 最初に対応した検出の正解ID (番号付けの順に依存しないよう (フレーム, 正解ID) で決める)
    first = {}
    for f in range(n_frames):
        for r in rows_by_frame.get(f, []):
            if r["det_index"] is not None and r["track_id"] not in first:
                first[r["track_id"]] = (f, gids_all[f][r["det_index"]])
    name, used = {}, defaultdict(int)
    for tid in sorted(first, key=lambda t: first[t]):
        g = first[tid][1]
        used[g] += 1
        name[tid] = f"g{g}" if used[g] == 1 else f"g{g}#{used[g]}"

    events, links, row_sig = [], {}, []
    for f in range(n_frames):
        for r in rows_by_frame.get(f, []):
            ev = r["event"]
            if ev.startswith("merged_into_"):
                host = int(ev[len("merged_into_"):])
                item = (f, "merged_into", name[r["track_id"]], (name[host],))
                events.append(item)
                row_sig.append(item + (None,))
                continue
            g = gids_all[f][r["det_index"]]
            nm = name[r["track_id"]]
            others = tuple(sorted(name[p] for p in r["parent_ids"]))
            links[(f, g)] = nm
            row_sig.append((f, ev, nm, others, g))
            if ev != "normal":
                events.append((f, ev, nm, others))
    events.sort()
    row_sig.sort(key=repr)

    # 速度 (EMA) -> トラッキングCSV -> 上昇速度の列
    T.compute_velocity_ema(rows_by_frame, n_frames)
    vy_rows = []
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "result_tracking.csv")
        T.write_tracking_csv(path, rows_by_frame, [f"frame{f:04d}.png" for f in range(n_frames)], dets_all)
        with open(path, encoding="utf-8-sig", newline="") as fp:
            for row in csv.DictReader(fp):
                tid = row["トラックID"]
                ev = row["イベント"]
                if ev.startswith("merged_into_"):
                    ev = "merged_into_" + name[int(ev[len("merged_into_"):])]
                vy_rows.append((int(row["フレーム"]), name[int(tid)] if tid else "", ev, row[CSV_VY_COL]))
    vy_rows.sort()
    return Result(events, links, row_sig, vy_rows, missing)


def track(frames, piv: bool):
    """正解ラベル画像の系列をトラッキングして要約を返す。PIV prior が未実装で piv=True なら None"""
    T = load_tracker(piv)
    if T is None:
        return None
    dets_all, gids_all, missing = detect_all(T, frames)
    rows = call_run_laptrack(T, dets_all, frames[0].shape)
    res = summarize(T, rows, dets_all, gids_all, missing)
    stats = getattr(T.run_laptrack, "last_stats", None) or {}
    res.prior_counts = dict(stats.get("prior_counts", {}))
    if piv and getattr(T, "piv_field", None) is None:
        msg = "piv_field.py を読み込めないので PIV prior ありでも速度場を使っていない (比較は無意味)"
        if msg not in NOTES:
            NOTES.append(msg)
    return res


def fmt_events(events) -> str:
    return "\n".join(f"      f{f:>2} {ev:<11} {nm:<5} {'<- ' if ev == 'merge' else ''}{list(o) if o else ''}"
                     for f, ev, nm, o in events) or "      (なし)"


def run_both(key: str, frames):
    """PIV prior なし/あり で実行し、あり/なしの一致 (イベント・対応付け・速度) を確認する。なしの結果を返す"""
    off = track(frames, piv=False)
    OBSERVED[key] = {"off": off.events, "on": None}
    if piv_available():
        on = track(frames, piv=True)
        OBSERVED[key]["on"] = on.events
        OBSERVED[key]["prior_counts"] = on.prior_counts
        assert on.events == off.events, (
            f"[{key}] PIV prior あり/なし でイベントが違う\n  なし:\n{fmt_events(off.events)}\n"
            f"  あり:\n{fmt_events(on.events)}")
        if on.row_sig == off.row_sig:   # 対応付けが同じ -> 速度 (CSV) も同じはず (速度場は予測専用)
            OBSERVED[key]["links_same"] = True
            diff = [(a, b) for a, b in zip(off.vy_rows, on.vy_rows) if a != b]
            assert len(off.vy_rows) == len(on.vy_rows) and not diff, (
                f"[{key}] 対応付けが同じなのに CSV の上昇速度が PIV prior あり/なし で違う: {diff[:5]}")
        else:
            OBSERVED[key]["links_same"] = False
            NOTES.append(f"[{key}] イベントは同じだが 1対1対応が PIV prior あり/なし で違う (速度の比較は省略)")
    return off


def assert_events(key: str, res: Result, alternatives):
    """イベント列が期待 (候補のどれか) と一致するか"""
    alts = [sorted(a) for a in alternatives]
    assert res.events in alts, (
        f"[{key}] PIV prior なし: イベントが期待と違う\n  観測:\n{fmt_events(res.events)}\n"
        + "\n".join(f"  期待 (候補{i + 1}):\n{fmt_events(a)}" for i, a in enumerate(alts)))


def assert_link(key: str, res: Result, frames_range, gid: int, name: str):
    """frames_range の各フレームで 正解気泡 gid が トラック name に対応していること"""
    for f in frames_range:
        got = res.links.get((f, gid))
        assert got == name, f"[{key}] フレーム {f}: 正解気泡 {gid} のトラックが {got} (期待 {name})"


# ==============================================================
# 3. シナリオ
# ==============================================================
def scenario_a():
    """a) 後ろの速いスラグ (正解2, 速度 -16) が 前のスラグ (正解1, 速度 -8) の後端に追いついて合体 (正解3)。
    合体後は 1本の長いスラグ (面積 = 2本の和) として -12 px/frame で上昇"""
    H, cx, F = 1174, 232.0, 5
    frames = []
    for k in range(F):
        lab = blank(H)
        paint(lab, capsule(H, cx, 500 - 8 * k + 160, 100, 320), 1)   # 前: 先端 y=500 から
        paint(lab, capsule(H, cx, 860 - 16 * k + 140, 100, 280), 2)  # 後ろ: 先端 y=860 から (隙間 40 -> 8px)
        frames.append(lab)
    a_sum = int(np.count_nonzero(frames[-1]))
    h_m = capsule_h_for_area(a_sum, 100)
    top0 = 500 - 8 * F                       # 合体した塊の先端 = 前のスラグの先端
    for k in range(frames_after_merge() + 1):
        lab = blank(H)
        paint(lab, capsule(H, cx, top0 - 12 * k + h_m / 2, 100, h_m), 3)
        frames.append(lab)
    return frames, F


def test_a_rear_slug_attaches_to_front_slug():
    key = "a) 後ろのスラグが前のスラグに合体"
    frames, F = scenario_a()
    res = run_both(key, frames)
    alts = []
    for p, q in (("g1", "g2"), ("g2", "g1")):
        alts.append([(0, "new", "g1", ()), (0, "new", "g2", ()),
                     (F, "merge", p, (q,)), (F, "merged_into", q, (p,))])
    assert_events(key, res, alts)
    primary = next(e[2] for e in res.events if e[1] == "merge")
    assert_link(key, res, range(F), 1, "g1")
    assert_link(key, res, range(F), 2, "g2")
    assert_link(key, res, range(F, len(frames)), 3, primary)   # 合体後は1トラック


def scenario_b():
    """b) スラグ (正解1, 高さ 400, -10 px/frame) が 前の片 (正解2, 高さ 250) と 後ろの片 (正解3, 高さ 144) に
    前後に分裂し、前の片は -14、後ろの片は -8 px/frame で離れていく"""
    H, cx, F = 1174, 232.0, 4
    frames = []
    for k in range(F):
        lab = blank(H)
        paint(lab, capsule(H, cx, 640 - 10 * k + 200, 100, 400), 1)
        frames.append(lab)
    top = 640 - 10 * F
    for k in range(6):
        lab = blank(H)
        paint(lab, capsule(H, cx, top - 14 * k + 125, 100, 250), 2)
        paint(lab, capsule(H, cx, top + 256 - 8 * k + 72, 100, 144), 3)
        frames.append(lab)
    return frames, F


def test_b_front_back_split():
    key = "b) スラグの前後分裂"
    frames, F = scenario_b()
    res = run_both(key, frames)
    # 親のIDを引き継ぐのは どちらの片でもよい (分裂した側が split)
    alts = [[(0, "new", "g1", ()), (F, "split", child, ("g1",))] for child in ("g2", "g3")]
    assert_events(key, res, alts)
    child_gid = int(next(e[2] for e in res.events if e[1] == "split")[1:])
    heir_gid = 5 - child_gid
    assert_link(key, res, range(F), 1, "g1")
    assert_link(key, res, range(F, len(frames)), heir_gid, "g1")             # 親のIDが片方に続く
    assert_link(key, res, range(F, len(frames)), child_gid, f"g{child_gid}")


def scenario_c():
    """c) スラグ (正解1, -12 px/frame) の右横 4px にフレーム 3 で小気泡 (正解2, r=10)、
    左横 4px にフレーム 5 で小気泡 (正解3, r=6) が現れ、スラグと一緒に上昇する"""
    H, cx = 1174, 180.0
    F2, F3, n = 3, 5, 9
    frames = []
    for k in range(n):
        lab = blank(H)
        cy = 800 - 12 * k + 150
        paint(lab, capsule(H, cx, cy, 100, 300), 1)
        if k >= F2:
            paint(lab, circle(H, cx + 50 + 4 + 10 + 1, cy - 40, 10), 2)
        if k >= F3:
            paint(lab, circle(H, cx - 50 - 4 - 6 - 1, cy + 60, 6), 3)
        frames.append(lab)
    # 現れた小気泡は 直前フレームのスラグと重ならず、中心は スラグから EVENT_MARGIN より離れている
    # (= 分裂の候補条件に当たらない。当たるなら分裂と判定されても仕様どおりなので、ここで作図を確認する)
    for k, g in ((F2, 2), (F3, 3)):
        prev_slug = frames[k - 1] == 1
        new = frames[k] == g
        assert not (prev_slug & new).any(), "シナリオ作図の誤り: 新しい小気泡が直前のスラグに重なる"
        ys, xs = np.nonzero(new)
        dist = ndimage.distance_transform_edt(~prev_slug)[int(round(ys.mean())), int(round(xs.mean()))]
        assert dist > tracker3.EVENT_MARGIN + 1, "シナリオ作図の誤り: 新しい小気泡の中心が直前のスラグに近すぎる"
        gap = ndimage.distance_transform_edt(~(frames[k] == 1))[new].min()
        assert gap >= 3, "シナリオ作図の誤り: 新しい小気泡とスラグの隙間が 2px 未満"
    return frames, F2, F3


def test_c_new_bubble_beside_slug():
    key = "c) スラグの横に新しい小気泡"
    frames, F2, F3 = scenario_c()
    res = run_both(key, frames)
    assert_events(key, res, [[(0, "new", "g1", ()), (F2, "new", "g2", ()), (F3, "new", "g3", ())]])
    assert_link(key, res, range(len(frames)), 1, "g1")   # スラグは normal のまま
    assert_link(key, res, range(F2, len(frames)), 2, "g2")
    assert_link(key, res, range(F3, len(frames)), 3, "g3")


TRI_ANGLES = (90.0, 210.0, 330.0)


def tri_offsets(R: float):
    return [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in TRI_ANGLES]


def scenario_d():
    """d) 3個 (正解1〜3, r = 24 / 21 / 18) が -10 px/frame で上昇しながら中心に向かって 6 px/frame で集まり、
    フレーム 4 で同時に合体して1個の円 (正解4, 面積 = 3個の和) になる"""
    H, cx, F = 700, 232.0, 4
    radii = (24.0, 21.0, 18.0)
    frames = []
    for k in range(F):
        lab = blank(H)
        cy = 500 - 10 * k
        R = 30 + 6 * (F - 1 - k)
        for g, (r, (ox, oy)) in enumerate(zip(radii, tri_offsets(R)), start=1):
            paint(lab, circle(H, cx + ox, cy + oy, r), g)
        frames.append(lab)
    r_m = math.sqrt(np.count_nonzero(frames[-1]) / math.pi)
    for k in range(frames_after_merge() + 1):
        lab = blank(H)
        paint(lab, circle(H, cx, 500 - 10 * (F + k), r_m), 4)
        frames.append(lab)
    return frames, F


def test_d_triple_merge():
    key = "d) 3個の同時合体"
    frames, F = scenario_d()
    res = run_both(key, frames)
    names = ("g1", "g2", "g3")
    alts = []
    for p in names:
        q = tuple(n for n in names if n != p)
        alts.append([(0, "new", n, ()) for n in names]
                    + [(F, "merge", p, q)] + [(F, "merged_into", n, (p,)) for n in q])
    assert_events(key, res, alts)
    primary = next(e[2] for e in res.events if e[1] == "merge")
    for g in (1, 2, 3):
        assert_link(key, res, range(F), g, f"g{g}")
    assert_link(key, res, range(F, len(frames)), 4, primary)


def scenario_e():
    """e) 親の円 (正解1, r=50, -10 px/frame) が フレーム 4 で 面積 40% / 33% / 27% の3片 (正解2〜4) に分裂し、
    3片は -10 px/frame で上昇しながら 6 px/frame で離れていく。どの片も 親の面積 / AREA_RATIO_GATE より小さい
    (= 親はどの片とも1対1対応できない)"""
    H, cx, F = 700, 232.0, 4
    frames = []
    for k in range(F):
        lab = blank(H)
        paint(lab, circle(H, cx, 500 - 10 * k, 50), 1)
        frames.append(lab)
    a_parent = int(np.count_nonzero(frames[-1]))
    radii = [math.sqrt(fr * a_parent / math.pi) for fr in (0.40, 0.33, 0.27)]
    for k in range(6):
        lab = blank(H)
        cy = 500 - 10 * (F + k)
        for g, (r, (ox, oy)) in enumerate(zip(radii, tri_offsets(38 + 6 * k)), start=2):
            paint(lab, circle(H, cx + ox, cy + oy, r), g)
        frames.append(lab)
    for g in (2, 3, 4):
        assert np.count_nonzero(frames[F] == g) < a_parent / tracker3.AREA_RATIO_GATE, \
            "シナリオ作図の誤り: 片の面積が 親の面積 / AREA_RATIO_GATE 以上"
    return frames, F


def test_e_triple_split_no_one_to_one():
    key = "e) 1対1対応しない3分裂"
    frames, F = scenario_e()
    res = run_both(key, frames)
    # 最大の片 (正解2) が親のIDを継承し、残り2片が split
    assert_events(key, res, [[(0, "new", "g1", ()), (F, "split", "g3", ("g1",)), (F, "split", "g4", ("g1",))]])
    assert_link(key, res, range(F), 1, "g1")
    assert_link(key, res, range(F, len(frames)), 2, "g1")
    assert_link(key, res, range(F, len(frames)), 3, "g3")
    assert_link(key, res, range(F, len(frames)), 4, "g4")


def scenario_f_exit():
    """f-1) スラグ (正解1, 高さ 200, -25 px/frame) と 小気泡 (正解2, r=10, -15 px/frame) が画面上端から出ていく"""
    H = 600
    frames = []
    for k in range(16):
        lab = blank(H)
        m1 = capsule(H, 150.0, 150 - 25 * k + 100, 100, 200)
        if m1.any():
            paint(lab, m1, 1)
        m2 = circle(H, 350.0, 120 - 15 * k, 10)
        if m2.any():
            paint(lab, m2, 2)
        frames.append(lab)
    return frames


def test_f1_exit_through_top_edge():
    key = "f-1) 画面上端からの退出"
    frames = scenario_f_exit()
    res = run_both(key, frames)
    assert_events(key, res, [[(0, "new", "g1", ()), (0, "new", "g2", ())]])
    for g in (1, 2):
        seen = sorted(f for (f, gg) in res.links if gg == g)
        assert_link(key, res, seen, g, f"g{g}")
    assert not any(gg not in (1, 2) for (_, gg) in res.links)
    # 画面内に完全に入っている間は必ず追跡されている
    for f, gt in enumerate(frames):
        for g in (1, 2):
            ys = np.nonzero(gt == g)[0]
            if ys.size and ys.min() > 0:
                assert (f, g) in res.links, f"[{key}] フレーム {f}: 画面内の正解気泡 {g} が追跡されていない"


def scenario_f_empty():
    """f-2) スラグ (正解1, -12 px/frame) と 小気泡 (正解2, r=9, -8 px/frame)。フレーム 4 と最後のフレーム 9 は
    空 (検出 0 個)。気泡は空フレームの間も同じ速度で動いている"""
    H, n, EMPTY = 900, 10, (4, 9)
    frames = []
    for k in range(n):
        lab = blank(H)
        if k not in EMPTY:
            paint(lab, capsule(H, 150.0, 600 - 12 * k + 150, 100, 300), 1)
            paint(lab, circle(H, 350.0, 800 - 8 * k, 9), 2)
        frames.append(lab)
    return frames, EMPTY


def test_f2_empty_frame():
    key = "f-2) 途中の空フレーム"
    frames, EMPTY = scenario_f_empty()
    res = run_both(key, frames)
    assert_events(key, res, [[(0, "new", "g1", ()), (0, "new", "g2", ())]])
    live = [f for f in range(len(frames)) if f not in EMPTY]
    assert_link(key, res, live, 1, "g1")   # 空フレームをまたいで同じID
    assert_link(key, res, live, 2, "g2")


# ==============================================================
# 4. スクリプトとして実行
# ==============================================================
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
    print("\n観測したイベント (フレーム, イベント, トラック名, 相手):")
    for key, ob in OBSERVED.items():
        print(f"  {key}")
        print("    PIV prior なし:")
        print(fmt_events(ob["off"]))
        if ob["on"] is None:
            print("    PIV prior あり: (未実行)")
        else:
            same = "なし と同じ" if ob["on"] == ob["off"] else "なし と違う"
            links = {True: "、1対1対応も同じ", False: "、1対1対応は違う"}.get(ob.get("links_same"), "")
            pc = ob.get("prior_counts") or {}
            print(f"    PIV prior あり: {same}{links} (新規トラックの初速度: PIV {pc.get('piv', 0)}件 / "
                  f"周りの気泡 {pc.get('flow', 0)}件 / 0 {pc.get('zero', 0)}件)")
    for m in NOTES:
        print(f"  注: {m}")
    print(f"\n{len(tests) - len(failed)} / {len(tests)} 合格")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

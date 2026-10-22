"""
binarized/4_link_audit.py (対応付けの抜き取り確認) のテスト (GUI なし)
=====================================================================
  a) TrackIndex.answer: つないだ / 合体の主 (吸収した相手) / 吸収された / 分裂の子 / 見失い後の再接続 (t+3 も) / 終了
  b) population / sample_items: 母集団 (最終フレーム・画面端を除く)、区分ごとの上限、一様な無作為抽出、同じ SEED なら同じ標本
  c) summarize: 判定の規則 (再接続の d は正しい、つないだ件の d は「隣を奪った」)、Wilson 区間、母集団で重み付けした all
  d) Audit: キー操作 (判定、戻る、終了)、判定済みの続きから再開、全部判定した後に b で戻れる、残りの数
  e) render: 画像がない / 画面端 / 全種類の答え で同じ大きさの画像。t+3 の再接続は 4コマ目に緑で出る。
     インスタンス画像があれば輪郭で描き、追跡していない小さい検出は青
  f) main: 判定済みの decisions ファイルがあれば GUI を出さずに集計して link_audit_report_<指紋>.json を書く
使い方: リポジトリのルートで  python -B tests/test_link_audit.py     (pytest でも実行できる)
"""
import csv
import importlib.util
import json
import os
import sys
import tempfile
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("link_audit", os.path.join(ROOT, "binarized", "4_link_audit.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

HEADER = ["ファイル名", "フレーム", "トラックID", "イベント", "親トラックID", "面積(px)", "ROI内面積(px)", "先端部X", "先端部Y",
          "中心X", "中心Y", "上昇速度(px/frame)", "周長(px)", "フレーム接触"]
N_FRAMES = 7


def write_csv(path, rows, n_frames=N_FRAMES):
    """rows = [(frame, tid, event, parents, area, cx, cy, touch)]"""
    by_f = {}
    for r in rows:
        by_f.setdefault(r[0], []).append(r)
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(HEADER)
        for f in range(n_frames):
            name = f"image{f:04d}.png"
            if f not in by_f:
                w.writerow([name, f, "", "気泡なし", "", 0, "", "", "", "", "", "", "", ""])
                continue
            for (_, tid, ev, par, area, cx, cy, touch) in by_f[f]:
                det = not ev.startswith("merged_into_")
                w.writerow([name, f, tid, ev, ";".join(map(str, par)), area, area if det else "", f"{cx:.2f}",
                            f"{cy - 3:.2f}", f"{cx:.2f}", f"{cy:.2f}", "", 10.0 if det else "",
                            ("1" if touch else "0") if det else ""])


def scenario_rows():
    R = []
    for f in range(6):                       # ID1: tiny, 毎フレーム上へ 5 px (つないだ)
        R.append((f, 1, "new" if f == 0 else "normal", [], 21, 50, 100 - 5 * f, False))
    for f in (0, 1, 3):                      # ID2: small, フレーム 2 で見失い -> 3 で再接続 (gap)
        R.append((f, 2, "new" if f == 0 else "normal", [], 200, 120, 100 - 5 * f, False))
    R.append((0, 3, "new", [], 800, 200, 60, False))          # ID3: large、ID4 と合体して ID4 に吸収される
    R.append((1, 3, "merged_into_4", [], 800, 200, 55, False))
    R.append((0, 4, "new", [], 900, 220, 70, False))
    R.append((1, 4, "merge", [3], 1700, 210, 64, False))      # ID4: 合体の主
    R.append((2, 4, "normal", [], 1700, 210, 59, False))
    R.append((2, 5, "split", [4], 300, 240, 59, False))      # ID4 から ID5 が分裂 (ID4 は続く)
    R.append((0, 6, "new", [], 30, 300, 100, False))          # ID6: tiny、フレーム 0 だけ (終了)
    R.append((0, 7, "new", [], 40, 10, 20, True))             # ID7: 画面端 (標本から除く)
    R.append((1, 7, "normal", [], 40, 10, 15, True))
    for f in (0, 1, 4):                      # ID8: small、フレーム 2, 3 で見失い -> 4 で再接続 (t+3)
        R.append((f, 8, "new" if f == 0 else "normal", [], 120, 330, 120 - 4 * f, False))
    R.append((6, 9, "new", [], 50, 30, 30, False))           # 最終フレームの気泡 (次がないので除く)
    return R


def make_index(tmp):
    p = os.path.join(tmp, "result_tracking.csv")
    write_csv(p, scenario_rows())
    rows, files = A.load_csv(p)
    return p, A.TrackIndex(rows), files


def test_a_answers():
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, files = make_index(tmp)
        assert files[0] == "image0000.png" and len(files) == N_FRAMES
        a = ix.answer(1, 2)
        assert a["kind"] == "link" and a["targets"] == [(1, 3)]
        a = ix.answer(2, 1)
        assert a["kind"] == "gap" and a["targets"] == [(2, 3)], a
        a = ix.answer(8, 1)
        assert a["kind"] == "gap" and a["targets"] == [(8, 4)] and "t+3" in a["note"], a
        a = ix.answer(3, 0)
        assert a["kind"] == "merged" and a["targets"] == [(4, 1)], a
        a = ix.answer(4, 0)
        assert a["kind"] == "link" and a["partners"] == [(3, 0)] and "merge host" in a["note"], a
        a = ix.answer(4, 1)
        assert a["kind"] == "link" and a["children"] == [(5, 2)] and "split" in a["note"], a
        a = ix.answer(6, 0)
        assert a["kind"] == "end" and a["targets"] == []
        assert ix.last_frame == 6
        fl = ix.flow(0, 300, 100)
        assert fl is not None and abs(fl[1] + 4.5) < 1.0, fl   # 近くの ID1 (-5), ID2 (-5), ID8 (-4) の中央値に近い


def test_b_population_and_sampling():
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, _ = make_index(tmp)
        pop = A.population(ix, include_edge=False)
        keys = {(it["tid"], it["frame"]) for it in pop}
        assert (7, 0) not in keys, "画面端は除く"
        assert (9, 6) not in keys and all(it["frame"] < ix.last_frame for it in pop), "最終フレームは除く"
        assert (7, 0) in {(it["tid"], it["frame"]) for it in A.population(ix, include_edge=True)}
        cnt = A.population_counts(pop)
        assert cnt["tiny"]["E"] >= 1 and cnt["tiny"]["L"] >= 5
        items = A.sample_items(pop, n_per_class=100, seed=1)
        assert len(items) == len(pop), "上限より少なければ全部"
        assert len({A.item_key(it) for it in items}) == len(items), "重複なし"
        assert items == A.sample_items(pop, 100, 1), "同じ SEED なら同じ標本"
        one = A.sample_items(pop, 2, seed=3)
        assert max(Counter(it["cls"] for it in one).values()) == 2, "区分ごとの上限"
        # 一様抽出: 長いトラックの対応付けは その数に比例して選ばれる (1トラック1件ではない)
        big = [{"tid": 1, "frame": f, "cls": "tiny", "kind": "link"} for f in range(90)] + \
              [{"tid": 100 + k, "frame": 0, "cls": "tiny", "kind": "link"} for k in range(10)]
        hits = sum(sum(1 for it in A.sample_items(big, 10, seed=s) if it["tid"] == 1) for s in range(200))
        assert 8.0 < hits / 200 < 10.0, hits / 200     # 期待値 9 (1トラック1件なら最大 1)


def test_c_summary():
    items = [{"tid": 1, "frame": 0, "cls": "tiny", "kind": "link"}, {"tid": 1, "frame": 1, "cls": "tiny", "kind": "link"},
             {"tid": 1, "frame": 2, "cls": "tiny", "kind": "link"}, {"tid": 6, "frame": 0, "cls": "tiny", "kind": "end"},
             {"tid": 2, "frame": 1, "cls": "small", "kind": "gap"}, {"tid": 8, "frame": 1, "cls": "small", "kind": "gap"},
             {"tid": 3, "frame": 0, "cls": "large", "kind": "merged"}]
    labels = {"1@0": "y", "1@1": "n", "1@2": "d", "6@0": "m", "2@1": "d", "8@1": "m", "3@0": "u"}
    counts = {"tiny": {"L": 30, "E": 10}, "small": {"L": 20, "E": 0}, "large": {"L": 5, "E": 0}}
    s = A.summarize(items, labels, counts)
    t = s["tiny"]
    assert t["linked"]["n"] == 3 and t["linked"]["ok"] == 1 and t["linked"]["wrong"] == 2 and t["stole_neighbour"] == 1
    assert abs(t["link_precision"][0] - 1 / 3) < 1e-3
    assert t["ended"]["missed"] == 1 and abs(t["miss_rate_of_ended"][0] - 1.0) < 1e-9
    # トラッカーの誤り = (30 × 2/3 + 10 × 1) / 40
    assert abs(t["tracker_error_rate"][0] - (30 * 2 / 3 + 10) / 40) < 1e-3, t["tracker_error_rate"]
    sm = s["small"]
    assert sm["link_precision"][0] == 1.0 and sm["delayed_relink"] == 1, "再接続の d / m は正しい再接続"
    assert s["large"]["judged"] == 1 and s["large"]["unsure"] == 1 and s["large"]["link_precision"] is None
    assert s["all"]["judged"] == 7
    assert s["all"]["link_precision"] is None, "large は母集団があるのに判定がない -> 推定できない"
    counts2 = dict(counts, large={"L": 0, "E": 0})
    s2 = A.summarize(items, labels, counts2)
    want = (30 * (1 / 3) + 20 * 1.0) / 50
    assert abs(s2["all"]["link_precision"][0] - want) < 1e-3, (s2["all"]["link_precision"], want)
    w = A.wilson(8, 10)
    assert w[0] == 0.8 and 0.49 < w[1] < 0.5 and 0.94 < w[2] < 0.95, w   # 既知の値 (0.490, 0.943)
    assert A.wilson(0, 0) is None
    assert A.weighted([(1, 0, 0)]) is None and A.weighted([(0, 0, 0)]) is None


def test_d_audit_keys():
    items = [{"tid": k, "frame": 0, "cls": "tiny", "kind": "link"} for k in range(4)]
    labels = {"0@0": "y"}
    au = A.Audit(items, labels)
    assert au.pos == 1 and au.remaining() == 3, "判定済みの次から"
    assert au.key("n") == "next" and labels["1@0"] == "n" and au.pos == 2
    assert au.key("b") == "back" and au.pos == 1
    assert au.key("y") == "next" and labels["1@0"] == "y"
    assert au.key("x") is None and au.pos == 2
    assert au.key("q") == "quit"
    au.key("u")
    au.key("d")
    assert au.done and labels["3@0"] == "d" and au.remaining() == 0
    assert au.key("y") is None, "終わりの画面では判定しない"
    assert au.key("b") == "back" and au.pos == 3 and not au.done, "終わりの画面から b で最後の件に戻る"
    assert au.key("m") == "next" and labels["3@0"] == "m"
    labels.pop("1@0")
    assert A.Audit(items, labels).pos == 1 and au.remaining() == 1


def make_index_with_images(tmp):
    """インスタンス画像 (instances/*.npz) と画像を作り、CSV の面積・重心をインスタンスと同じ値にする
    (2_*_track.py の出力と同じ関係)。追跡していない小さい検出も1個ずつ入れる"""
    import cv2
    rows = scenario_rows()
    os.makedirs(os.path.join(tmp, "instances"), exist_ok=True)
    out = []
    for f in range(N_FRAMES):
        lab = np.zeros((160, 400), np.int32)
        img = np.full((160, 400), 200, np.uint8)
        dets = [r for r in rows if r[0] == f and not r[2].startswith("merged_into_")]
        for k, r in enumerate(dets, start=1):
            rr = max(2, int(round(A.eq_radius(r[4]))))
            cv2.circle(lab, (int(r[5]), int(r[6])), rr, k, -1)
            cv2.circle(img, (int(r[5]), int(r[6])), rr, 0, 1)
        lab[150:153, 380:383] = len(dets) + 1
        np.savez_compressed(os.path.join(tmp, "instances", f"image{f:04d}.npz"), inst=lab)
        cv2.imwrite(os.path.join(tmp, f"image{f:04d}.png"), img)
        for k, r in enumerate(dets, start=1):
            ys, xs = np.nonzero(lab == k)
            out.append((f, r[1], r[2], r[3], float(len(xs)), float(xs.mean()), float(ys.mean()), r[7]))
        out += [r for r in rows if r[0] == f and r[2].startswith("merged_into_")]
    p = os.path.join(tmp, "result_tracking.csv")
    write_csv(p, out)
    rows_, files = A.load_csv(p)
    return A.TrackIndex(rows_), files


def test_e_render():
    if A.cv2 is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        ix, files = make_index_with_images(tmp)
        fr = A.Frames(files, tmp)
        missing = A.Frames(files, os.path.join(tmp, "nothing"))
        withinst = A.Frames(files, tmp, inst_folder=os.path.join(tmp, "instances"))
        shapes = set()
        pop = A.population(ix, include_edge=True)
        for it in pop:
            for frames in (fr, missing, withinst):
                out = A.render(it, ix, frames, {}, 0, 1, panel=120)
                shapes.add(out.shape)
        assert len(shapes) == 1 and next(iter(shapes))[1] == 4 * 120 + 3 * 4, shapes
        # t+3 の再接続: 4コマ目は再接続したフレーム (frame 4) で、緑の輪郭がある
        it = {"tid": 8, "frame": 1, "cls": "small", "kind": "gap"}
        assert A.frames_to_show(it, ix.answer(8, 1)) == [0, 1, 2, 4]
        out = A.render(it, ix, withinst, {}, 0, 1, panel=120)
        last = out[92:, 3 * 124:]
        green = (last[:, :, 1] > 180) & (last[:, :, 0] < 60) & (last[:, :, 2] < 60)
        assert green.sum() > 20, green.sum()
        # 合体の主: t のコマに吸収した相手 (ID3) が橙で出る
        out = A.render({"tid": 4, "frame": 0, "cls": "large", "kind": "link"}, ix, withinst, {}, 0, 1, panel=120)
        p1 = out[92:, 124:244]
        orange = (p1[:, :, 2] > 230) & (np.abs(p1[:, :, 1].astype(int) - 140) < 20) & (p1[:, :, 0] < 30)
        assert orange.sum() > 10, orange.sum()
        st = withinst.instances(0)
        assert st is not None and len(A._match_labels(st[1], ix.by_frame[0])) == len(ix.by_frame[0])


def test_f_main_report():
    with tempfile.TemporaryDirectory() as tmp:
        p, ix, _ = make_index(tmp)
        names = ("TRACKING_CSV", "N_PER_CLASS", "INCLUDE_EDGE", "SEED", "OUT_DIR", "REVIEW")
        old = {k: getattr(A, k) for k in names}
        try:
            A.TRACKING_CSV, A.N_PER_CLASS, A.INCLUDE_EDGE, A.SEED, A.OUT_DIR, A.REVIEW = \
                p, 5, False, 0, os.path.join(tmp, "out"), False
            items = A.sample_items(A.population(ix, False), 5, 0)
            os.makedirs(A.OUT_DIR)
            fp_ = A.csv_fingerprint(p)
            with open(os.path.join(A.OUT_DIR, f"decisions_{fp_}.json"), "w", encoding="utf-8") as fp:
                json.dump({"labels": {A.item_key(it): "y" for it in items}}, fp)
            A.main()
            rep = json.load(open(os.path.join(A.OUT_DIR, f"link_audit_report_{fp_}.json"), encoding="utf-8"))
            assert rep["n_items"] == len(items) and rep["summary"]["all"]["judged"] == len(items)
            assert rep["population"]["tiny"]["E"] >= 1
            dec = json.load(open(os.path.join(A.OUT_DIR, f"decisions_{fp_}.json"), encoding="utf-8"))
            assert len(dec["items"]) == len(items) and all("kind" in it and it["label"] == "y" for it in dec["items"])
        finally:
            for k, v in old.items():
                setattr(A, k, v)


TESTS = [test_a_answers, test_b_population_and_sampling, test_c_summary, test_d_audit_keys, test_e_render,
         test_f_main_report]

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

"""
binarized/4_link_audit.py (対応付けの抜き取り確認) のテスト (GUI なし)
=====================================================================
  a) TrackIndex.answer: つないだ / 合体の主 / 吸収された / 分裂 / 見失い後の再接続 / 終了
  b) sample_items: 区分ごとの上限、1トラック1件、画面端・最終フレームは除く、同じ SEED なら同じ標本
  c) summarize: 判定の数から 正解率・見逃し率・トラッカーの誤り を数え、Wilson 区間を付ける
  d) Audit: キー操作 (判定、戻る、終了) と 判定済みの続きから再開
  e) render: 画像がない / 画面端 / 全種類の答え で落ちずに同じ大きさの画像を返す
  f) main: 判定済みの decisions ファイルがあれば GUI を出さずに集計して link_audit_report.json を書く
使い方: リポジトリのルートで  python -B tests/test_link_audit.py     (pytest でも実行できる)
"""
import csv
import importlib.util
import json
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("link_audit", os.path.join(ROOT, "binarized", "4_link_audit.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

HEADER = ["ファイル名", "フレーム", "トラックID", "イベント", "親トラックID", "面積(px)", "ROI内面積(px)", "先端部X", "先端部Y",
          "中心X", "中心Y", "上昇速度(px/frame)", "周長(px)", "フレーム接触"]


def write_csv(path, rows, n_frames):
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
                w.writerow([name, f, tid, ev, ";".join(map(str, par)), area, area if det else "", cx, cy - 3, cx, cy, "",
                            10.0 if det else "", ("1" if touch else "0") if det else ""])


def scenario_rows():
    R = []
    for f in range(6):                       # ID1: tiny, 毎フレーム上へ 5 px (つないだ)
        R.append((f, 1, "new" if f == 0 else "normal", [], 20, 50, 100 - 5 * f, False))
    for f in (0, 1, 3):                      # ID2: small, フレーム 2 で見失い -> 3 で再接続 (gap)
        R.append((f, 2, "new" if f == 0 else "normal", [], 200, 120, 100 - 5 * f, False))
    R.append((0, 3, "new", [], 800, 200, 60, False))          # ID3: large、ID4 と合体して ID4 に吸収される
    R.append((1, 3, "merged_into_4", [], 800, 200, 55, False))
    R.append((0, 4, "new", [], 900, 220, 70, False))
    R.append((1, 4, "merge", [3], 1700, 210, 64, False))      # ID4: 合体の主
    R.append((2, 4, "normal", [], 1700, 210, 59, False))
    R.append((2, 5, "split", [4], 300, 240, 59, False))      # ID4 から ID5 が分裂
    R.append((0, 6, "new", [], 30, 300, 100, False))          # ID6: tiny、フレーム 0 だけ (終了)
    R.append((0, 7, "new", [], 40, 10, 20, True))             # ID7: 画面端 (標本から除く)
    R.append((1, 7, "normal", [], 40, 10, 15, True))
    return R


def make_index(tmp):
    p = os.path.join(tmp, "result_tracking.csv")
    write_csv(p, scenario_rows(), 6)
    rows, files = A.load_csv(p)
    return p, A.TrackIndex(rows), files


def test_a_answers():
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, files = make_index(tmp)
        assert files[0] == "image0000.png" and len(files) == 6
        a = ix.answer(1, 2)
        assert a["kind"] == "link" and a["targets"] == [(1, 3)]
        a = ix.answer(2, 1)
        assert a["kind"] == "gap" and a["targets"] == [(2, 3)], a
        a = ix.answer(3, 0)
        assert a["kind"] == "merged" and a["targets"] == [(4, 1)], a
        a = ix.answer(4, 0)
        assert a["kind"] == "link" and "merge host" in a["note"], a
        a = ix.answer(4, 1)
        assert a["kind"] == "link" and "split" in a["note"], a
        a = ix.answer(6, 0)
        assert a["kind"] == "end" and a["targets"] == []
        assert ix.last_frame == 5


def test_b_sampling():
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, _ = make_index(tmp)
        items = A.sample_items(ix, n_per_class=5, include_edge=False, seed=1)
        tids = [it["tid"] for it in items]
        assert len(tids) == len(set(tids)), "1トラック1件"
        assert 7 not in tids, "画面端は除く"
        assert all(it["frame"] < ix.last_frame for it in items), "最終フレームは除く (次がない)"
        assert {it["tid"]: it["cls"] for it in items}.get(1) == "tiny"
        assert {it["tid"]: it["cls"] for it in items}.get(4) == "large"
        assert items == A.sample_items(ix, 5, False, 1), "同じ SEED なら同じ標本"
        edge = A.sample_items(ix, 5, True, 1)
        assert 7 in [it["tid"] for it in edge]
        one = A.sample_items(ix, 1, False, 1)
        from collections import Counter
        assert max(Counter(it["cls"] for it in one).values()) == 1, "区分ごとの上限"


def test_c_summary():
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, _ = make_index(tmp)
        items = [{"tid": 1, "frame": 0, "cls": "tiny"}, {"tid": 1, "frame": 1, "cls": "tiny"},
                 {"tid": 1, "frame": 2, "cls": "tiny"}, {"tid": 6, "frame": 0, "cls": "tiny"},
                 {"tid": 2, "frame": 1, "cls": "small"}, {"tid": 3, "frame": 0, "cls": "large"}]
        labels = {"1@0": "y", "1@1": "n", "1@2": "d", "6@0": "m", "2@1": "y", "3@0": "u"}
        s = A.summarize(items, labels, ix)
        t = s["tiny"]
        assert t["linked"]["y"] == 1 and t["linked"]["n"] == 1 and t["linked"]["d"] == 1 and t["ended"]["m"] == 1
        assert abs(t["link_precision"][0] - 1 / 3) < 1e-3
        assert abs(t["miss_rate_of_ended"][0] - 1.0) < 1e-9
        assert t["wrong_link_own_undetected"] == 1
        assert abs(t["tracker_error_rate"][0] - 3 / 4) < 1e-3, t["tracker_error_rate"]
        assert s["large"]["judged"] == 1 and s["large"]["unsure"] == 1 and s["large"]["link_precision"] is None
        assert s["all"]["judged"] == 6
        w = A.wilson(8, 10)
        assert w[0] == 0.8 and 0.49 < w[1] < 0.5 and 0.94 < w[2] < 0.95, w   # 既知の値 (0.490, 0.943)
        assert A.wilson(0, 0) is None


def test_d_audit_keys():
    items = [{"tid": k, "frame": 0, "cls": "tiny"} for k in range(4)]
    labels = {"0@0": "y"}
    au = A.Audit(items, labels)
    assert au.pos == 1, "判定済みの次から"
    assert au.key("n") == "next" and labels["1@0"] == "n" and au.pos == 2
    assert au.key("b") == "back" and au.pos == 1
    assert au.key("y") == "next" and labels["1@0"] == "y"
    assert au.key("x") is None and au.pos == 2
    assert au.key("q") == "quit"
    au.key("u"); au.key("d")
    assert au.done and labels["3@0"] == "d"
    assert au.key("y") is None or au.done


def test_e_render():
    if A.cv2 is None:
        return
    import cv2
    with tempfile.TemporaryDirectory() as tmp:
        _, ix, files = make_index(tmp)
        for f in range(6):
            img = np.full((160, 260), 200, np.uint8)
            cv2.circle(img, (50, 100 - 5 * f), 3, 0, 1)
            cv2.imwrite(os.path.join(tmp, files[f]), img)
        fr = A.Frames(files, tmp)
        missing = A.Frames(files, os.path.join(tmp, "nothing"))
        shapes = set()
        for tid, f in ((1, 2), (2, 1), (3, 0), (4, 0), (4, 1), (6, 0), (7, 0), (1, 4)):
            for frames in (fr, missing):
                out = A.render({"tid": tid, "frame": f, "cls": A.size_class(ix.det[(tid, f)]["area"])}, ix, frames,
                               {}, 0, 1, panel=120)
                shapes.add(out.shape)
        assert len(shapes) == 1 and next(iter(shapes))[1] == 4 * 120 + 3 * 4, shapes


def test_f_main_report():
    with tempfile.TemporaryDirectory() as tmp:
        p, ix, _ = make_index(tmp)
        old = {k: getattr(A, k) for k in ("TRACKING_CSV", "N_PER_CLASS", "INCLUDE_EDGE", "SEED", "OUT_DIR")}
        try:
            A.TRACKING_CSV, A.N_PER_CLASS, A.INCLUDE_EDGE, A.SEED, A.OUT_DIR = p, 5, False, 0, os.path.join(tmp, "out")
            items = A.sample_items(ix, 5, False, 0)
            os.makedirs(A.OUT_DIR)
            dec = os.path.join(A.OUT_DIR, f"decisions_{A.csv_fingerprint(p)}.json")
            with open(dec, "w", encoding="utf-8") as fp:
                json.dump({"labels": {A.item_key(it): "y" for it in items}}, fp)
            A.main()
            rep = json.load(open(os.path.join(A.OUT_DIR, "link_audit_report.json"), encoding="utf-8"))
            assert rep["n_items"] == len(items) and rep["summary"]["all"]["judged"] == len(items)
        finally:
            for k, v in old.items():
                setattr(A, k, v)


TESTS = [test_a_answers, test_b_sampling, test_c_summary, test_d_audit_keys, test_e_render, test_f_main_report]

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

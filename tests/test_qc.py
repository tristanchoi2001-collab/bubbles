"""
3_tracking_qc.py の SWAP_LIKELY 相手候補の判定と詳細文字列のテスト (docs/PIV_TASK.md 5-3)
=====================================================================
小さな result_tracking.csv (と qc_report.json) を一時フォルダに手で書き、analyze() / main() を実行して確認する。
  - 詳細の文字列: 相手IDの重複なし (理由をまとめる)、近い順に最大 SWAP_DETAIL_MAX 件 + 「他N件」
  - 面積比フィルタ: 面積比 > SWAP_PARTNER_AREA_RATIO の気泡は相手にしない (ちょうど 3.0 は含める)
  - 半径の上限: 大きいスラグでも相手を探す半径は SWAP_RADIUS_MAX_PX (200px) まで
  - 同じ気泡・同じフレームの POS_JUMP + AREA_JUMP は1件の SWAP_LIKELY にまとめる
  - 自分自身のトラックの消失は相手に数えない
  - tracker3 形式の qc_report.json: MAX_AGE を読む / ゲート表示に None が出ない / tracker3 向けの助言

実行:  python -B tests/test_qc.py     または     pytest tests/test_qc.py
"""
import contextlib
import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
QC_PATH = os.path.join(HERE, "..", "3_tracking_qc.py")

HEADER = ["ファイル名", "フレーム", "トラックID", "イベント", "親トラックID", "面積(px)", "ROI内面積(px)",
          "先端部X", "先端部Y", "中心X", "中心Y", "上昇速度(px/frame)", "周長(px)", "フレーム接触"]
N_FRAMES = 12         # フレーム 0〜11 (消失の判定は 最終フレーム - MAX_AGE より前のみ)
JUMP_FRAME = 5        # 注目する気泡 (ID1) が位置ジャンプするフレーム


def load_qc():
    """3_tracking_qc.py を新しく読み込む (設定のグローバル変数をテストごとに初期値に戻すため)"""
    spec = importlib.util.spec_from_file_location("tracking_qc_under_test", QC_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def track(tid, frames, xy, area):
    """1本のトラックの観測 [(フレーム, ID, イベント, 面積, cx, cy)]。xy / area は値1つ or フレームごとの関数"""
    out = []
    for i, f in enumerate(frames):
        x, y = xy(f) if callable(xy) else xy
        a = area(f) if callable(area) else area
        out.append((f, tid, "new" if i == 0 else "normal", a, x, y))
    return out


def write_csv(path, obs, n_frames=N_FRAMES):
    """トラッカーと同じ列の result_tracking.csv を書く。気泡の無いフレームは「気泡なし」の行"""
    by_f = defaultdict(list)
    for o in obs:
        by_f[o[0]].append(o)
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(HEADER)
        for f in range(n_frames):
            fn = f"img{f:04d}.png"
            if not by_f[f]:
                w.writerow([fn, f, "", "気泡なし", "", 0, "", "", "", "", "", "", "", ""])
            for _, tid, ev, a, x, y in sorted(by_f[f], key=lambda o: o[1]):
                w.writerow([fn, f, tid, ev, "", f"{a:.0f}", f"{a:.0f}", f"{x:.2f}", f"{y - 5:.2f}",
                            f"{x:.2f}", f"{y:.2f}", "", "", "0"])


def jumper(area=400.0, x=200.0, y0=600.0, v=-10.0, jump=-40.0, last=N_FRAMES - 1, area_after=None):
    """ID1: 等速で上昇し、JUMP_FRAME で予測位置から jump px ずれる (以後は元の速度で進む)。
    area_after を与えると JUMP_FRAME から面積も変わる (POS_JUMP + AREA_JUMP)"""
    def pos(f):
        return (x, y0 + v * f + (jump if f >= JUMP_FRAME else 0.0))

    def ar(f):
        return area_after if (area_after is not None and f >= JUMP_FRAME) else area
    return track(1, range(0, last + 1), pos, ar)


def jump_xy(area=400.0, x=200.0, y0=600.0, v=-10.0, jump=-40.0):
    """ジャンプした位置 (相手候補の距離の基準点)"""
    return (x, y0 + v * JUMP_FRAME + jump)


def analyze_csv(Q, obs, tmp, max_age=None):
    p = os.path.join(tmp, "result_tracking.csv")
    write_csv(p, obs)
    rows, frame_files, has_touch = Q.load_tracking_csv(p)
    return Q.analyze(rows, frame_files, has_touch, None, max_age=max_age)


def swaps_of(flags, tid=1, frame=JUMP_FRAME):
    return [f for f in flags if f["type"] == "SWAP_LIKELY" and f["tid"] == tid and f["frame"] == frame]


# --------------------------------------------------------------
# シナリオ1: 相手8件 (うち ID303 は「新規発生」と「消失」の両方) -> 近い順に5件 + 他3件
#   近い順 (ID順とは違う): ID305 8px, ID303 10px, ID310 12px, ID304 15px, ID306 25px | ID307〜309 28〜34px
# --------------------------------------------------------------
DEDUP_ORDER = [305, 303, 310, 304, 306, 307, 308, 309]


def scenario_dedup():
    jx, jy = jump_xy()
    late = range(JUMP_FRAME, N_FRAMES)                                    # JUMP_FRAME で新規発生、最後まで残る
    obs = jumper()
    obs += track(303, [JUMP_FRAME], (jx + 10, jy), 400)                    # 1フレームだけ: 新規発生・消失
    obs += track(304, late, (jx - 15, jy), 400)                            # 新規発生
    obs += track(305, range(0, JUMP_FRAME), (jx, jy + 8), 400)             # JUMP_FRAME の前で消失
    obs += track(310, late, (jx - 12 * 0.6, jy - 12 * 0.8), 400)           # 新規発生 (ID は大きいが近い)
    for i, tid in enumerate(range(306, 310)):                              # 新規発生 ×4 (距離 25, 28, 31, 34)
        obs += track(tid, late, (jx + (25 + 3 * i) * 0.6, jy - (25 + 3 * i) * 0.8), 400)
    return obs


def test_detail_dedup_order_and_max():
    Q = load_qc()
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_dedup(), tmp)
    sw = swaps_of(flags)
    assert len(sw) == 1, sw
    sw = sw[0]
    assert sw["n_partners"] == 8, sw["n_partners"]
    assert sw["partner_ids"] == DEDUP_ORDER, sw["partner_ids"]
    head = sw["detail"].split(" / ")[0]
    assert head == "相手候補: ID305(消失)、ID303(新規発生・消失)、ID310(新規発生)、ID304(新規発生)、ID306(新規発生) 他3件", head
    assert sw["detail"].count("ID303") == 1, sw["detail"]
    assert "予測位置から 40.0px ずれ" in sw["detail"], sw["detail"]
    en = sw["ascii"].split(" | ")[0]
    assert en == ("partners: ID305(lost), ID303(appeared/lost), ID310(appeared), ID304(appeared), "
                  "ID306(appeared) +3 more"), en


def test_detail_max_setting():
    Q = load_qc()
    Q.SWAP_DETAIL_MAX = 2
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_dedup(), tmp)
    head = swaps_of(flags)[0]["detail"].split(" / ")[0]
    assert head == "相手候補: ID305(消失)、ID303(新規発生・消失) 他6件", head
    Q.SWAP_DETAIL_MAX = 10                       # 全部載るときは「他N件」を付けない
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_dedup(), tmp)
    head = swaps_of(flags)[0]["detail"].split(" / ")[0]
    assert "他" not in head and head.count("ID") == 8, head


def test_format_function():
    Q = load_qc()
    p = {7: {"reasons": {"jump", "new"}, "dist": 3.0}, 2: {"reasons": {"lost"}, "dist": 3.0},
         9: {"reasons": {"lost", "new", "jump"}, "dist": 1.0}}
    jp, en = Q.format_swap_partners(p, max_n=5)
    assert jp == "相手候補: ID9(新規発生・消失・同時ジャンプ)、ID2(消失)、ID7(新規発生・同時ジャンプ)", jp   # 同距離は ID 順
    assert en == "partners: ID9(appeared/lost/jumped), ID2(lost), ID7(appeared/jumped)", en
    jp, en = Q.format_swap_partners(p, max_n=0)
    assert jp == "相手候補: 他3件" and en == "partners: +3 more", (jp, en)


# --------------------------------------------------------------
# シナリオ2: 面積比フィルタ (注目する気泡 400px)
# --------------------------------------------------------------
def scenario_area_ratio():
    jx, jy = jump_xy()
    late = range(JUMP_FRAME, N_FRAMES)
    obs = jumper()
    obs += track(501, late, (jx + 10, jy), 1300)    # 面積比 3.25 -> 除外
    obs += track(502, late, (jx - 15, jy), 1100)    # 2.75 -> 相手
    obs += track(503, late, (jx, jy + 20), 100)     # 4.0  -> 除外
    obs += track(504, late, (jx, jy - 25), 140)     # 2.86 -> 相手
    obs += track(505, late, (jx + 30, jy), 1200)    # ちょうど 3.0 -> 相手 (以下なので含める)
    return obs


def test_area_ratio_filter():
    Q = load_qc()
    assert Q.SWAP_PARTNER_AREA_RATIO == 3.0
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_area_ratio(), tmp)
    sw = swaps_of(flags)
    assert len(sw) == 1 and sw[0]["partner_ids"] == [502, 504, 505], sw
    assert "ID501" not in sw[0]["detail"] and "ID503" not in sw[0]["detail"], sw[0]["detail"]

    Q.SWAP_PARTNER_AREA_RATIO = float("inf")    # フィルタを外すと全部が相手 (除外の原因が面積比であることの確認)
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_area_ratio(), tmp)
    assert swaps_of(flags)[0]["partner_ids"] == [501, 502, 503, 504, 505], swaps_of(flags)[0]["partner_ids"]


def test_area_ratio_only_partner_filtered_means_no_swap():
    Q = load_qc()
    jx, jy = jump_xy()
    obs = jumper() + track(501, range(JUMP_FRAME, N_FRAMES), (jx + 10, jy), 4000)   # 面積比 10 の気泡だけ
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, obs, tmp)
    assert not swaps_of(flags), swaps_of(flags)
    assert any(f["type"] == "POS_JUMP" and f["tid"] == 1 for f in flags)    # 位置ジャンプとしては残る


# --------------------------------------------------------------
# シナリオ3: 半径の上限 200px (注目する気泡 20000px: 等価直径 159.6px -> 2倍で 319px)
# --------------------------------------------------------------
def scenario_radius_cap():
    kw = dict(area=20000.0, x=300.0, y0=1500.0, v=-10.0, jump=-100.0)
    jx, jy = jump_xy(**kw)
    late = range(JUMP_FRAME, N_FRAMES)
    obs = jumper(**kw)
    obs += track(601, late, (jx + 150, jy), 20000)    # 150px -> 相手
    obs += track(602, late, (jx - 250, jy), 20000)    # 250px -> 上限 200px の外
    return obs


def test_radius_cap():
    Q = load_qc()
    assert Q.SWAP_RADIUS_MAX_PX == 200
    assert abs(Q.swap_radius(20000) - 200.0) < 1e-9
    assert abs(Q.swap_radius(10) - 20.0) < 1e-9                       # 10px の下限 × SWAP_RADIUS_FACTOR
    assert abs(Q.swap_radius(400) - 2 * Q.eq_diam(400)) < 1e-9        # 上限・下限にかからない大きさ
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_radius_cap(), tmp)
    sw = swaps_of(flags)
    assert len(sw) == 1 and sw[0]["partner_ids"] == [601], sw

    Q.SWAP_RADIUS_MAX_PX = float("inf")                               # 上限なしなら 250px も相手 (旧版の動作)
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, scenario_radius_cap(), tmp)
    assert swaps_of(flags)[0]["partner_ids"] == [601, 602], swaps_of(flags)[0]["partner_ids"]


# --------------------------------------------------------------
# シナリオ4: 同じフレームに POS_JUMP と AREA_JUMP -> 1件にまとめる / 自分自身の消失は相手ではない
# --------------------------------------------------------------
def test_pos_and_area_jump_merged():
    Q = load_qc()
    jx, jy = jump_xy()
    obs = jumper(area_after=700.0) + track(701, range(JUMP_FRAME, N_FRAMES), (jx + 12, jy), 600)
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, obs, tmp)
    kinds = sorted(f["type"] for f in flags if f["tid"] == 1 and f["frame"] == JUMP_FRAME)
    assert kinds == ["AREA_JUMP", "POS_JUMP", "SWAP_LIKELY"], kinds
    sw = swaps_of(flags)[0]
    assert sw["n_partners"] == 1 and sw["partner_ids"] == [701], sw
    parts = sw["detail"].split(" / ")
    assert parts[0] == "相手候補: ID701(新規発生)", parts
    assert parts[1].startswith("予測位置から") and parts[2].startswith("面積 400→700px"), parts
    assert sw["pred_xy"] is not None                                   # 先頭は位置ジャンプ (予測位置つき)
    assert len(sw["ascii"].split(" | ")) == 3, sw["ascii"]


def test_own_death_is_not_a_partner():
    Q = load_qc()
    obs = jumper(last=JUMP_FRAME)            # ジャンプしたフレームで自分のトラックが終わる (画面内部で消失)
    with tempfile.TemporaryDirectory() as tmp:
        flags, _ = analyze_csv(Q, obs, tmp)
    assert any(f["type"] == "INTERIOR_LOST" and f["tid"] == 1 for f in flags)
    assert not swaps_of(flags), swaps_of(flags)


# --------------------------------------------------------------
# main(): qc_summary.json / qc_flags.csv / tracker3 形式の qc_report.json
# --------------------------------------------------------------
def run_main(Q, tmp, used_params):
    write_csv(os.path.join(tmp, "result_tracking.csv"), scenario_dedup())
    with open(os.path.join(tmp, "qc_report.json"), "w", encoding="utf-8") as fp:
        json.dump({"used_params": used_params}, fp)
    Q.TRACKING_CSV = os.path.join(tmp, "result_tracking.csv")
    Q.OUT_DIR = os.path.join(tmp, "qc")
    Q.SAVE_REVIEW_IMAGES = False
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Q.main()
    with open(os.path.join(tmp, "qc", "qc_summary.json"), encoding="utf-8") as fp:
        s = json.load(fp)
    with open(os.path.join(tmp, "qc", "qc_flags.csv"), encoding="utf-8-sig") as fp:
        flag_rows = list(csv.reader(fp))
    return s, flag_rows, buf.getvalue()


TRACKER3_PARAMS = {"MAX_SPEED": 70.0, "POS_GATE": 15.0, "POS_GATE_SIZE_FRAC": 0.25, "AREA_RATIO_GATE": 1.8,
                   "MAX_AGE": 2, "USE_FLOW_PRIOR": True, "USE_PIV_PRIOR": False, "roi_rect": None}


def test_main_summary_and_tracker3_params():
    Q = load_qc()
    with tempfile.TemporaryDirectory() as tmp:
        s, flag_rows, out = run_main(Q, tmp, TRACKER3_PARAMS)
    sp = s["swap_partners_by_size"]
    assert set(sp) == {"tiny", "small", "large"}, sp
    assert sp["small"] == {"n": 1, "median": 8.0, "max": 8}, sp
    assert sp["tiny"] == {"n": 0, "median": None, "max": None}, sp
    st = s["settings"]
    assert (st["SWAP_RADIUS_MAX_PX"], st["SWAP_PARTNER_AREA_RATIO"], st["SWAP_DETAIL_MAX"]) == (200.0, 3.0, 5), st
    assert st["SWAP_RADIUS_FACTOR"] == 2.0 and st["MAX_AGE"] == 2, st         # MAX_AGE は qc_report.json の値
    assert s["tracker_gates"]["MAX_SPEED"] == 70.0 and s["tracker_gates"]["USE_PIV_PRIOR"] is False, s["tracker_gates"]
    assert flag_rows[0] == ["種類", "内容", "サイズ区分", "フレーム", "ファイル名", "トラックID",
                            "中心X", "中心Y", "面積(px)", "ROI内", "詳細"], flag_rows[0]   # 列は変更なし
    swap_rows = [r for r in flag_rows[1:] if r[0] == "SWAP_LIKELY"]
    assert len(swap_rows) == 1 and swap_rows[0][-1].startswith("相手候補: ID305(消失)、ID303(新規発生・消失)、"), swap_rows
    gate_lines = [ln for ln in out.splitlines() if "トラッカーのゲート" in ln]
    assert len(gate_lines) == 1 and "tracker3" in gate_lines[0] and "None" not in gate_lines[0], gate_lines
    assert "MAX_AGE = 2" in out, out
    assert "[SWAP_LIKELY の相手候補数]" in out, out


def test_max_age_from_report_changes_lost_window():
    """MAX_AGE は消失判定 (最終フレーム - MAX_AGE より前) に効く: 最終フレーム 11、ID9 はフレーム 8 で終了"""
    obs = track(9, range(0, 9), (100.0, 300.0), 400) + track(10, range(0, N_FRAMES), (300.0, 300.0), 400)
    Q = load_qc()
    with tempfile.TemporaryDirectory() as tmp:
        flags3, info3 = analyze_csv(Q, obs, tmp)                  # 設定値 MAX_AGE = 3: 8 < 11 - 3 ではない
        flags2, info2 = analyze_csv(Q, obs, tmp, max_age=2)       # qc_report.json の MAX_AGE = 2: 8 < 9
    lost = lambda fl: [f["tid"] for f in fl if f["type"] == "INTERIOR_LOST"]
    assert lost(flags3) == [] and lost(flags2) == [9], (lost(flags3), lost(flags2))
    assert info3["max_age"] == 3 and info2["max_age"] == 2


def _unstable_summary(Q, gates):
    """small が「速度を予測すれば追える範囲」(比 0.3〜0.7) で不安定、という集計結果を作る"""
    s = {"n_tracks": 1, "n_observations": 1, "observations_by_size": {}, "counts": {t: {c: 0 for c in Q.CLASS_NAMES}
                                                                                     for t in Q.ALL_TYPES},
         "suspicious_ratio_by_count": 0.0, "suspicious_ratio_by_area": 0.0,
         "deviation_from_prediction": {"small": {"n": 100, "median_px": 3.0, "p90_px": 20.0, "p99_px": 40.0,
                                                 "median_rel": 0.2, "frac_over_threshold": 0.3}},
         "motion_vs_spacing": {"small": {"median_next_px": 15.0, "median_neighbor_px": 30.0,
                                         "median_ratio": 0.5, "frac_ratio_over_half": 0.5}},
         "swap_partners_by_size": {c: {"n": 0, "median": None, "max": None} for c in Q.CLASS_NAMES},
         "settings": {}, "tracker_gates": gates}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Q.print_report(s, None)
    return buf.getvalue()


def test_report_advice_by_tracker():
    Q = load_qc()
    keys = Q.TRACKER_PARAM_KEYS
    t3_off = {k: TRACKER3_PARAMS.get(k) for k in keys}
    out = _unstable_summary(Q, t3_off)
    assert "USE_PIV_PRIOR = True" in out and "SPACING_GATE_FRAC" not in out, out
    assert "None" not in out, out

    t3_on = dict(t3_off, USE_PIV_PRIOR=True)
    out = _unstable_summary(Q, t3_on)
    assert "USE_PIV_PRIOR = True" not in out and "SPACING_GATE_FRAC" not in out, out

    t3_old = dict(t3_off, USE_PIV_PRIOR=None)     # PIV prior 対応前の tracker3 (記録なし)
    out = _unstable_summary(Q, t3_old)
    assert "USE_PIV_PRIOR を使うこと" in out and "SPACING_GATE_FRAC" not in out, out

    t2_old = {k: None for k in keys}
    t2_old.update(MAX_LEADING_EDGE_JUMP=40.0, MAX_CENTER_X_JUMP=30.0, AREA_RATIO_GATE=1.8)   # 間隔ゲートなしの旧 tracker2
    out = _unstable_summary(Q, t2_old)
    assert "SPACING_GATE_FRAC" in out and "USE_PIV_PRIOR" not in out, out
    gate = [ln for ln in out.splitlines() if "トラッカーのゲート" in ln]
    assert gate and "tracker2" in gate[0] and "None" not in gate[0], gate

    t2_new = dict(t2_old, SPACING_GATE_FRAC=0.7, USE_FLOW_PRIOR=True)
    out = _unstable_summary(Q, t2_new)
    assert "→ 新しく現れた気泡の初速度推定と間隔ゲート" not in out, out


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
    print(f"\n{len(tests) - len(failed)} / {len(tests)} 合格")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

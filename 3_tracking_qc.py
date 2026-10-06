"""
追跡精度の自動チェック v2 (2_unet_tracker.py / microgaptracker3.py の出力CSVを解析)
=====================================================================
トラッカーはそのまま使い、出力された result_tracking.csv だけを読んで
「追跡ミスの疑いがある箇所」を洗い出す。全部を目で数える代わりに、疑わしい箇所だけ確認すればよい。

v1 からの変更
  - 位置ジャンプの基準を「データの分布」から「気泡自身の大きさ」に変更
      v1 は (中央値 + Z×MAD) で自動決定していたが、ずれの大きいステップが多いデータでは
      基準が一緒に大きくなり、検出できなくなっていた
      v2 は「予測位置から自分の等価直径 × JUMP_REL 以上ずれたら」ジャンプとする
      (隣の気泡に乗り移るには、少なくともその程度は動く必要があるため)
  - 結果をすべて気泡サイズ別 (tiny / small / large) に集計
      発生・消失・見失いが小さい気泡に集中していれば「検出のちらつき」、
      大きい気泡で起きていれば「追跡の問題」と切り分けられる
  - 面積加重の疑わしい割合 (ボイド率・スリップへの影響の目安) を追加
  - 確認用画像を見やすく作り直し (拡大・前/今の位置・予測位置・移動の矢印・説明文)

検出する項目
  SWAP_LIKELY    ID乗り移り   : 位置/面積の急変 + 近くで別トラックが消失・発生、または2本が同時に互いの位置へ
  POS_JUMP       位置ジャンプ : 直前の速度から予測した位置から、自分の大きさの JUMP_REL 倍以上ずれた
  AREA_JUMP      面積急変     : 合体/分裂なしで面積が AREA_JUMP_FACTOR 倍以上変わった
  INTERIOR_NEW   内部で発生   : 画面端でも分裂でもないのに、画面の内側で新しいトラックが始まった
  INTERIOR_LOST  内部で消失   : 画面端でも合体でもないのに、画面の内側でトラックが終わった
  MERGE_AREA     合体の面積不保存 / SPLIT_AREA 分裂の面積不保存
  MERGE_SPLIT    合体直後の分裂 (接触しただけの可能性)
  GAP            見失い       : 数フレーム検出されず、後で同じIDに戻った (追跡は維持されている)

出力 (OUT_DIR)
  qc_flags.csv      疑わしい箇所の一覧
  qc_summary.json   種類×サイズ別の件数、ずれの分布、面積加重の割合
  review/<種類>/     確認用画像 (大きい気泡から順に)
"""

# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
TRACKING_CSV = r"C:\Users\inoue-2024-01\Desktop\ams\output_unet\result_tracking.csv"  # トラッカーの出力CSV
REVIEW_IMAGE_DIR = None  # 確認画像の元。None なら CSVフォルダの _cache_processed (2値化画像。見やすい)、
                         # なければ CSV と同じフォルダ (トラッカーのオーバーレイ画像)
QC_REPORT = None     # トラッカーの qc_report.json (ROI取得用)。None なら CSV と同じフォルダ
OUT_DIR = None       # 結果の保存先。None なら CSV と同じフォルダの qc_tracking/

JUMP_REL = 0.5                # 予測位置からのずれ > 等価直径 × この値 → 位置ジャンプ
MIN_JUMP_PX = 5.0             # ただし最低この px 以上 (小さい気泡の画素ゆらぎ対策)
AREA_JUMP_FACTOR = 1.5        # 面積がこの倍率以上 (または 1/倍率 以下) に変わったら面積急変
MIN_AREA_FOR_AREA_CHECK = 50  # これより小さい気泡は面積チェックしない (画素量子化で面積がぶれるため)
AREA_CONSERVATION_TOL = 0.3   # 合体・分裂の面積保存の許容差 (±30%)
MERGE_SPLIT_WINDOW = 5        # 合体後このフレーム数以内の分裂を MERGE_SPLIT とする
SWAP_RADIUS_FACTOR = 2.0      # 急変地点から (等価直径 × この値) 以内の発生/消失を乗り移りの相手とみなす
MAX_AGE = 3                   # トラッカーの MAX_AGE と同じ値
EDGE_MARGIN_PX = 2            # (旧形式CSVのみ) 画面端接触の判定余白

# 気泡サイズの区分 (面積 px)。自分の画像に合わせて調整してよい
SIZE_CLASSES = [("tiny", 0, 50), ("small", 50, 500), ("large", 500, float("inf"))]

SAVE_REVIEW_IMAGES = True
REVIEW_PANEL = 360            # 確認画像の1パネルの表示サイズ (px)
REVIEW_MIN_CROP = 120         # 切り出しの最小サイズ (px)。気泡が大きければ自動で広げる
MAX_REVIEW_PER_TYPE = 60      # 種類ごとの確認画像の上限 (大きい気泡から優先)


import csv
import json
import math
import os
from collections import defaultdict

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

FLAG_TEXT = {
    "SWAP_LIKELY": "ID乗り移りの可能性が高い", "POS_JUMP": "位置ジャンプ", "AREA_JUMP": "面積急変",
    "INTERIOR_NEW": "画面内部で新規発生", "INTERIOR_LOST": "画面内部で消失",
    "MERGE_AREA": "合体の面積不保存", "SPLIT_AREA": "分裂の面積不保存",
    "MERGE_SPLIT": "合体直後の分裂", "GAP": "一時的な見失い",
}
ALL_TYPES = ["SWAP_LIKELY", "POS_JUMP", "AREA_JUMP", "INTERIOR_NEW", "INTERIOR_LOST",
             "MERGE_AREA", "SPLIT_AREA", "MERGE_SPLIT", "GAP"]
CLASS_NAMES = [c[0] for c in SIZE_CLASSES]


def size_class(area):
    for name, lo, hi in SIZE_CLASSES:
        if lo <= area < hi:
            return name
    return SIZE_CLASSES[-1][0]


def eq_diam(area):
    return 2.0 * math.sqrt(max(area, 1.0) / math.pi)


# ==============================================================
# 1. 読み込み
# ==============================================================
def _f(s, default=float("nan")):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def load_tracking_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fp:
        rd = csv.DictReader(fp)
        cols = rd.fieldnames or []
        has_touch = "フレーム接触" in cols
        rows, frame_files = [], {}
        for r in rd:
            f = int(_f(r.get("フレーム"), -1))
            frame_files.setdefault(f, r.get("ファイル名", ""))
            tid = r.get("トラックID", "")
            if tid in ("", None):
                continue
            pid = r.get("親トラックID", "") or ""
            rows.append({
                "file": r.get("ファイル名", ""), "frame": f, "tid": int(_f(tid)),
                "event": r.get("イベント", ""),
                "parents": [int(p) for p in pid.split(";") if p.strip().isdigit()],
                "area": _f(r.get("面積(px)"), 0.0),
                "cx": _f(r.get("中心X")), "cy": _f(r.get("中心Y")),
                "touch": (r.get("フレーム接触") == "1") if has_touch else None,
            })
    return rows, frame_files, has_touch


def image_size_from(overlay_dir, frame_files):
    if cv2 is None:
        return None
    for f in sorted(frame_files):
        p = os.path.join(overlay_dir, frame_files[f])
        if os.path.exists(p):
            img = cv2.imread(p)
            if img is not None:
                return img.shape[:2]
    return None


def load_roi(path):
    try:
        with open(path, encoding="utf-8") as fp:
            rect = json.load(fp).get("used_params", {}).get("roi_rect")
        if isinstance(rect, list) and len(rect) == 4:
            return tuple(int(v) for v in rect)
    except (OSError, ValueError):
        pass
    return None


# ==============================================================
# 2. 解析
# ==============================================================
def _flag(ftype, r, detail, ascii_detail, prev=None, prev_file=None, next_file=None, pred=None):
    return {"type": ftype, "frame": r["frame"], "tid": r["tid"], "x": r["cx"], "y": r["cy"],
            "area": r["area"], "cls": size_class(r["area"]), "detail": detail, "ascii": ascii_detail,
            "file": r.get("file", ""), "prev_file": prev["file"] if prev else prev_file,
            "prev_xy": (prev["cx"], prev["cy"]) if prev else None, "prev_frame": prev["frame"] if prev else None,
            "next_file": next_file, "pred_xy": pred}


def _dist(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def analyze(rows, frame_files, has_touch, img_hw):
    first_frame, last_frame = min(frame_files), max(frame_files)

    def touches(r):
        if has_touch:
            return bool(r["touch"])
        if img_hw is None:
            return False
        h, w = img_hw
        rad = eq_diam(r["area"]) / 2 + EDGE_MARGIN_PX
        return r["cx"] < rad or r["cy"] < rad or r["cx"] > w - 1 - rad or r["cy"] > h - 1 - rad

    obs, merged_into = defaultdict(list), {}
    for r in rows:
        if r["event"].startswith("merged_into"):
            merged_into[r["tid"]] = r["frame"]
        else:
            obs[r["tid"]].append(r)
    for t in obs:
        obs[t].sort(key=lambda r: r["frame"])
    at = {(r["tid"], r["frame"]): r for t in obs for r in obs[t]}

    affected, split_children = set(), defaultdict(list)
    for r in rows:
        if r["event"] == "merge":
            affected.add((r["tid"], r["frame"]))
        elif r["event"] == "split":
            affected.add((r["tid"], r["frame"]))
            for p in r["parents"]:
                affected.add((p, r["frame"]))
                split_children[(p, r["frame"])].append(r)

    def prev_obs(tid, frame):
        best = None
        for r in obs.get(tid, []):
            if r["frame"] < frame:
                best = r
            else:
                break
        return best

    flags = []
    dist = defaultdict(list)          # サイズ別: 予測からのずれ (px) と 等価直径比
    n_steps = defaultdict(int)

    # トラッカーに依存しない動きの目安:
    #   d_same = 同じフレームで最も近い別の気泡までの距離
    #   d_next = 次のフレームで最も近い気泡までの距離 (追跡結果を使わない)
    #   動きが小さければ次フレームで一番近いのは自分自身 → d_next ≪ d_same
    #   動きが気泡間隔並みに大きいと d_next ≈ d_same → 原理的に対応付けが曖昧
    by_frame = defaultdict(list)
    for t in obs:
        for r in obs[t]:
            by_frame[r["frame"]].append(r)
    motion = defaultdict(list)        # サイズ別: (d_next, d_same)
    for f, lst in by_frame.items():
        nxt = by_frame.get(f + 1)
        if not nxt or len(lst) < 2:
            continue
        xy = np.array([[r["cx"], r["cy"]] for r in lst])
        xn = np.array([[r["cx"], r["cy"]] for r in nxt])
        same = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
        np.fill_diagonal(same, np.inf)
        dn = np.hypot(xy[:, None, 0] - xn[None, :, 0], xy[:, None, 1] - xn[None, :, 1]).min(axis=1)
        for r, a, b in zip(lst, dn, same.min(axis=1)):
            if not touches(r):
                motion[size_class(r["area"])].append((float(a), float(b)))

    # ---- 位置ジャンプ・面積急変 ----
    jump_flags = []
    for tid, lst in obs.items():
        v_ref, v_jump = None, None
        for a, b in zip(lst, lst[1:]):
            dt = b["frame"] - a["frame"]
            if dt > 1:
                flags.append(_flag("GAP", b, f"{dt - 1}フレーム未検出の後に復帰", f"missing {dt - 1} frame(s), then back", prev=a))
            ok = (dt <= MAX_AGE + 1 and (tid, a["frame"]) not in affected and (tid, b["frame"]) not in affected
                  and not touches(a) and not touches(b))
            if not ok:
                v_ref, v_jump = None, None
                continue
            cls = size_class(b["area"])
            n_steps[cls] += 1
            v = ((b["cx"] - a["cx"]) / dt, (b["cy"] - a["cy"]) / dt)
            d = 0.5 * (eq_diam(a["area"]) + eq_diam(b["area"]))
            if v_ref is not None:
                r = math.hypot(v[0] - v_ref[0], v[1] - v_ref[1]) * dt
                if v_jump is not None:      # 直前がジャンプ: 元の流れに戻った / 本当に速度が変わった、は数えない
                    r = min(r, math.hypot(v[0] - v_jump[0], v[1] - v_jump[1]) * dt)
                thr = max(MIN_JUMP_PX, JUMP_REL * d)
                dist[cls].append((r, r / d, r > thr))
                if r > thr:
                    pred = (a["cx"] + v_ref[0] * dt, a["cy"] + v_ref[1] * dt)
                    jump_flags.append(_flag(
                        "POS_JUMP", b, f"予測位置から {r:.1f}px ずれ (等価直径 {d:.1f}px の {r / d:.1f}倍)",
                        f"off prediction by {r:.0f}px = {r / d:.1f} x own size", prev=a, pred=pred))
                    v_jump = v
                else:
                    v_ref, v_jump = v, None
            else:
                v_ref, v_jump = v, None
            if min(a["area"], b["area"]) >= MIN_AREA_FOR_AREA_CHECK:
                ratio = b["area"] / max(a["area"], 1.0)
                if ratio >= AREA_JUMP_FACTOR or ratio <= 1 / AREA_JUMP_FACTOR:
                    jump_flags.append(_flag("AREA_JUMP", b, f"面積 {a['area']:.0f}→{b['area']:.0f}px (×{ratio:.2f})",
                                            f"area {a['area']:.0f} -> {b['area']:.0f}px (x{ratio:.2f})", prev=a))
    flags += jump_flags

    # ---- 画面内部での発生・消失 ----
    births, deaths = [], []
    for tid, lst in obs.items():
        r0, r1 = lst[0], lst[-1]
        if r0["event"] == "new" and r0["frame"] > first_frame and not touches(r0):
            births.append(_flag("INTERIOR_NEW", r0, "画面端・分裂以外での新規トラック", "new track appeared inside the frame",
                                prev_file=frame_files.get(r0["frame"] - 1)))
        if tid not in merged_into and r1["frame"] < last_frame - MAX_AGE and not touches(r1):
            deaths.append(_flag("INTERIOR_LOST", r1, "画面端・合体以外でのトラック終了", "track ended inside the frame",
                                next_file=frame_files.get(r1["frame"] + 1)))
    flags += births + deaths

    # ---- ID乗り移り ----
    swaps = {}
    for fl in jump_flags:
        rad = SWAP_RADIUS_FACTOR * max(eq_diam(fl["area"]), 10.0)
        partners = []
        for b in births:
            if abs(b["frame"] - fl["frame"]) <= 1 and _dist(b, fl) <= rad:
                partners.append(("ID{}が近くで新規発生", "ID{} appeared nearby", b["tid"]))
        for d in deaths:
            if fl["frame"] - 2 <= d["frame"] <= fl["frame"] and _dist(d, fl) <= rad:
                partners.append(("ID{}が近くで消失", "ID{} lost nearby", d["tid"]))
        for o in jump_flags:
            if (o is not fl and o["type"] == "POS_JUMP" and o["frame"] == fl["frame"]
                    and o["tid"] != fl["tid"] and _dist(o, fl) <= rad):
                partners.append(("ID{}も同時にジャンプ", "ID{} jumped at same time", o["tid"]))
        if not partners:
            continue
        jp = "・".join(sorted({p[0].format(p[2]) for p in partners}))
        en = "; ".join(sorted({p[1].format(p[2]) for p in partners}))
        key = (fl["tid"], fl["frame"])
        if key in swaps:
            swaps[key]["detail"] += " / " + fl["detail"]
        else:
            sw = dict(fl)
            sw.update(type="SWAP_LIKELY", detail=jp + " / " + fl["detail"], ascii=en + " | " + fl["ascii"])
            swaps[key] = sw
    flags += list(swaps.values())

    # ---- 合体・分裂の面積保存 / 合体直後の分裂 ----
    merges = []
    for r in rows:
        if r["event"] != "merge":
            continue
        prevs = [prev_obs(t, r["frame"]) for t in [r["tid"]] + r["parents"]]
        if any(p is None for p in prevs) or touches(r) or any(touches(p) for p in prevs):
            continue
        before = sum(p["area"] for p in prevs)
        ratio = r["area"] / max(before, 1.0)
        merges.append((r["tid"], r["frame"], r["parents"]))
        if abs(ratio - 1) > AREA_CONSERVATION_TOL:
            flags.append(_flag("MERGE_AREA", r, f"合体前の合計 {before:.0f}px → 合体後 {r['area']:.0f}px (×{ratio:.2f})",
                               f"merge: {before:.0f} -> {r['area']:.0f}px (x{ratio:.2f})",
                               prev_file=frame_files.get(r["frame"] - 1)))
    for (p, f), kids in split_children.items():
        now, before = at.get((p, f)), prev_obs(p, f)
        if before is None or touches(before) or any(touches(k) for k in kids):
            continue
        after = sum(k["area"] for k in kids) + (now["area"] if now else 0.0)
        ratio = after / max(before["area"], 1.0)
        if abs(ratio - 1) > AREA_CONSERVATION_TOL:
            flags.append(_flag("SPLIT_AREA", now or kids[0],
                               f"分裂前 {before['area']:.0f}px → 分裂後の合計 {after:.0f}px (×{ratio:.2f})",
                               f"split: {before['area']:.0f} -> {after:.0f}px (x{ratio:.2f})", prev=before))
    for tid, f, parents in merges:
        for (p, fs), kids in split_children.items():
            if p == tid and f < fs <= f + MERGE_SPLIT_WINDOW:
                flags.append(_flag("MERGE_SPLIT", at.get((p, fs)) or kids[0],
                                   f"フレーム{f}で ID{','.join(map(str, parents))} と合体 → {fs - f}フレーム後に分裂",
                                   f"merged at f{f}, split again {fs - f} frame(s) later",
                                   prev_file=frame_files.get(fs - 1)))

    for fl in flags:
        fl["file"] = fl["file"] or frame_files.get(fl["frame"], "")

    all_obs = [r for t in obs for r in obs[t]]
    return flags, {"obs": all_obs, "n_tracks": len(obs), "n_steps": n_steps, "dist": dist, "motion": motion}


def in_roi(fl, roi):
    if roi is None:
        return True
    x, y, w, h = roi
    return x <= fl["x"] <= x + w and y <= fl["y"] <= y + h


# ==============================================================
# 3. 集計・解釈
# ==============================================================
def summarize(flags, info, roi):
    obs = info["obs"]
    n_obs_cls = defaultdict(int)
    area_cls = defaultdict(float)
    for r in obs:
        n_obs_cls[size_class(r["area"])] += 1
        area_cls[size_class(r["area"])] += r["area"]

    table = {t: {c: 0 for c in CLASS_NAMES} for t in ALL_TYPES}
    table_roi = {t: {c: 0 for c in CLASS_NAMES} for t in ALL_TYPES}
    for f in flags:
        table[f["type"]][f["cls"]] += 1
        if in_roi(f, roi):
            table_roi[f["type"]][f["cls"]] += 1

    suspect = {}
    for f in flags:
        if f["type"] in ("SWAP_LIKELY", "POS_JUMP", "AREA_JUMP"):
            suspect[(f["tid"], f["frame"])] = f["area"]
    total_area = sum(r["area"] for r in obs) or 1.0

    dist_stats = {}
    for c in CLASS_NAMES:
        d = info["dist"].get(c, [])
        if d:
            px = np.array([x[0] for x in d])
            rel = np.array([x[1] for x in d])
            dist_stats[c] = {"n": int(len(d)), "median_px": round(float(np.median(px)), 2),
                             "p90_px": round(float(np.percentile(px, 90)), 2),
                             "p99_px": round(float(np.percentile(px, 99)), 2),
                             "median_rel": round(float(np.median(rel)), 3),
                             "frac_over_threshold": round(float(np.mean([x[2] for x in d])), 4)}
    motion_stats = {}
    for c in CLASS_NAMES:
        m = info["motion"].get(c, [])
        if m:
            mv = np.array([x[0] for x in m]); nd = np.array([x[1] for x in m])
            ratio = mv / np.maximum(nd, 1e-6)
            motion_stats[c] = {"median_next_px": round(float(np.median(mv)), 2),
                               "median_neighbor_px": round(float(np.median(nd)), 2),
                               "median_ratio": round(float(np.median(ratio)), 3),
                               "frac_ratio_over_half": round(float(np.mean(ratio > 0.5)), 4)}
    return {
        "motion_vs_spacing": motion_stats,
        "n_tracks": info["n_tracks"], "n_observations": len(obs),
        "observations_by_size": dict(n_obs_cls), "steps_checked_by_size": dict(info["n_steps"]),
        "counts": table, "counts_in_roi": table_roi if roi else None, "roi_rect": list(roi) if roi else None,
        "suspicious_ratio_by_count": round(len(suspect) / max(len(obs), 1), 5),
        "suspicious_ratio_by_area": round(sum(suspect.values()) / total_area, 5),
        "deviation_from_prediction": dist_stats,
        "settings": {"JUMP_REL": JUMP_REL, "MIN_JUMP_PX": MIN_JUMP_PX, "AREA_JUMP_FACTOR": AREA_JUMP_FACTOR,
                     "MIN_AREA_FOR_AREA_CHECK": MIN_AREA_FOR_AREA_CHECK, "AREA_CONSERVATION_TOL": AREA_CONSERVATION_TOL,
                     "SIZE_CLASSES": [[n, lo, (hi if hi != float('inf') else None)] for n, lo, hi in SIZE_CLASSES]},
    }


def print_report(s, roi):
    print(f"\nトラック {s['n_tracks']}本 / 観測 {s['n_observations']}件")
    print("サイズ区分 (面積px): " + ", ".join(f"{n} {lo}-{'' if hi == float('inf') else hi}"
                                              for n, lo, hi in SIZE_CLASSES))
    print("観測数: " + ", ".join(f"{c} {s['observations_by_size'].get(c, 0)}" for c in CLASS_NAMES))

    print("\n[予測位置からのずれ] 正常な追跡なら中央値は数px以下、等価直径比は 0.1 程度以下")
    for c in CLASS_NAMES:
        d = s["deviation_from_prediction"].get(c)
        if d:
            print(f"  {c:<6} 中央値 {d['median_px']:>6}px  90%値 {d['p90_px']:>6}px  "
                  f"直径比の中央値 {d['median_rel']:>5}  基準超え {100 * d['frac_over_threshold']:.1f}%")

    key = "counts_in_roi" if roi else "counts"
    print(f"\n[件数] {'ROI内' if roi else '画面全体'} (サイズ別)")
    print(f"  {'種類':<14}" + "".join(f"{c:>8}" for c in CLASS_NAMES) + f"{'合計':>8}  内容")
    for t in ALL_TYPES:
        row = s[key][t]
        print(f"  {t:<14}" + "".join(f"{row[c]:>8}" for c in CLASS_NAMES) + f"{sum(row.values()):>8}  {FLAG_TEXT[t]}")
    print(f"\n疑わしい観測 (SWAP/POS/AREA): 件数で {100 * s['suspicious_ratio_by_count']:.2f}%, "
          f"面積加重で {100 * s['suspicious_ratio_by_area']:.2f}%  ← ボイド率・スリップへの影響の目安")

    print("\n[撮影条件のチェック] 追跡結果を使わず、次フレームで一番近い気泡までの距離 ÷ 同じフレームで一番近い気泡までの距離")
    print("  比が0.3以下 = 次フレームで一番近いのはほぼ自分自身 (追跡しやすい)。0.3を超えると動きが気泡間隔に比べて大きく、対応付けが曖昧になりうる")
    for c in CLASS_NAMES:
        m = s["motion_vs_spacing"].get(c)
        if m:
            print(f"  {c:<6} 次フレーム最近接 {m['median_next_px']:>6}px  同フレーム最近接 {m['median_neighbor_px']:>6}px  "
                  f"比の中央値 {m['median_ratio']:>5}  0.5超え {100 * m['frac_ratio_over_half']:.1f}%")
    g = s.get("tracker_gates")
    if g:
        print(f"  トラッカーのゲート: 先端部Y {g.get('MAX_LEADING_EDGE_JUMP')}px, 中心X {g.get('MAX_CENTER_X_JUMP')}px, "
              f"面積比 {g.get('AREA_RATIO_GATE')}  (qc_report.json)")

    # ---- 自動の読み方ヒント ----
    print("\n[読み方]")
    dev = s["deviation_from_prediction"]
    unstable = [c for c in CLASS_NAMES if dev.get(c) and dev[c]["frac_over_threshold"] > 0.05]
    if not unstable:
        print("  - 全サイズで予測からのずれが小さい → 追跡は安定")
    else:
        print(f"  - 追跡が不安定なサイズ: {', '.join(unstable)} (ステップの5%以上が自分の大きさの半分以上ずれる)")
        mv = s["motion_vs_spacing"]
        lim = [c for c in unstable if mv.get(c) and mv[c]["median_ratio"] > 0.7]
        mid = [c for c in unstable if mv.get(c) and 0.3 < mv[c]["median_ratio"] <= 0.7]
        ok = [c for c in unstable if mv.get(c) and mv[c]["median_ratio"] <= 0.3]
        if lim:
            print(f"    {', '.join(lim)}: 次フレームで一番近い気泡が、同じフレームの隣と同じくらい遠い → 撮影条件の限界。"
                  "動画から間引いていないか確認 (全フレームを使う / fpsを上げる)。")
        if mid:
            g2 = s.get("tracker_gates") or {}
            print(f"    {', '.join(mid)}: 毎フレーム隣の気泡までの距離の3〜7割動く → 一番近いものを選ぶだけでは曖昧だが、"
                  "速度を予測すれば追える範囲 (ソフトで改善可能)。")
            if not g2.get("SPACING_GATE_FRAC"):
                print("      → 新しく現れた気泡の初速度推定と間隔ゲートを持つトラッカー (USE_FLOW_PRIOR / SPACING_GATE_FRAC) を使うこと")
        if ok:
            gx = (g or {}).get("MAX_CENTER_X_JUMP"); gy = (g or {}).get("MAX_LEADING_EDGE_JUMP")
            nd = min(mv[c]["median_neighbor_px"] for c in ok)
            msg = f"    {', '.join(ok)}: 気泡は次フレームでもほぼ同じ場所にあるのに追跡がずれる → トラッカー側の問題 (ソフトで直せる)。"
            if gx is not None and gy is not None and max(gx, gy) > nd:
                msg += f" ゲート({gy}/{gx}px)が気泡間隔({nd:.0f}px)より広く、隣の気泡も候補に入っている。"
            print(msg)
    ra = s["suspicious_ratio_by_area"]
    print(f"  - 面積加重の疑わしい割合 {100 * ra:.1f}%" + (
        " → ボイド率・スリップへの影響は小さい" if ra < 0.02 else
        " → 要注意。review/ で疑わしい箇所を確認してから計測に使うこと" if ra < 0.10 else
        " → このままスリップ等の計測に使わず、原因を先に解消すること"))


# ==============================================================
# 4. 出力
# ==============================================================
def write_flags(path, flags, roi):
    order = {t: i for i, t in enumerate(ALL_TYPES)}
    flags = sorted(flags, key=lambda f: (order[f["type"]], -f["area"], f["frame"]))
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["種類", "内容", "サイズ区分", "フレーム", "ファイル名", "トラックID",
                    "中心X", "中心Y", "面積(px)", "ROI内", "詳細"])
        for f in flags:
            w.writerow([f["type"], FLAG_TEXT[f["type"]], f["cls"], f["frame"], f["file"], f["tid"],
                        f"{f['x']:.1f}", f"{f['y']:.1f}", f"{f['area']:.0f}",
                        "" if roi is None else ("1" if in_roi(f, roi) else "0"), f["detail"]])


def _panel(img, x0, y0, c, label, marks):
    """img から (x0,y0) 起点の c×c を切り出し、REVIEW_PANEL に拡大して目印を描く"""
    h, w = img.shape[:2]
    crop = np.full((c, c, 3), 40, np.uint8)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(w, x0 + c), min(h, y0 + c)
    if xb > xa and yb > ya:
        crop[ya - y0:yb - y0, xa - x0:xb - x0] = img[ya:yb, xa:xb]
    s = REVIEW_PANEL / c
    out = cv2.resize(crop, (REVIEW_PANEL, REVIEW_PANEL), interpolation=cv2.INTER_NEAREST)
    P = lambda xy: (int(round((xy[0] - x0) * s)), int(round((xy[1] - y0) * s)))
    for kind, xy, xy2 in marks:
        if kind == "circle_y":
            cv2.circle(out, P(xy), 14, (0, 255, 255), 2)
        elif kind == "circle_r":
            cv2.circle(out, P(xy), 14, (0, 0, 255), 3)
        elif kind == "square_c":
            p = P(xy)
            cv2.rectangle(out, (p[0] - 10, p[1] - 10), (p[0] + 10, p[1] + 10), (255, 255, 0), 2)
        elif kind == "arrow":
            cv2.arrowedLine(out, P(xy), P(xy2), (0, 0, 255), 2, tipLength=0.15)
    cv2.rectangle(out, (0, 0), (REVIEW_PANEL, 24), (0, 0, 0), -1)
    cv2.putText(out, label, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return out


def save_review_images(flags, overlay_dir, out_dir):
    if cv2 is None:
        return 0
    in_swap = {(f["tid"], f["frame"]) for f in flags if f["type"] == "SWAP_LIKELY"}
    by_type = defaultdict(list)
    for f in flags:
        if f["type"] == "GAP":
            continue
        if f["type"] in ("POS_JUMP", "AREA_JUMP") and (f["tid"], f["frame"]) in in_swap:
            continue
        by_type[f["type"]].append(f)
    cache, saved = {}, 0

    def load(fn):
        if not fn:
            return None
        if fn not in cache:
            p = os.path.join(overlay_dir, fn)
            cache[fn] = cv2.imread(p) if os.path.exists(p) else None
            if len(cache) > 64:
                cache.pop(next(iter(cache)))
        return cache[fn]

    for t, lst in by_type.items():
        lst.sort(key=lambda f: -f["area"])           # 大きい気泡から
        for fl in lst[:MAX_REVIEW_PER_TYPE]:
            cur = (fl["x"], fl["y"])
            pts = [cur] + [p for p in (fl["prev_xy"], fl["pred_xy"]) if p]
            cx, cy = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
            span = max(max(abs(p[0] - cx), abs(p[1] - cy)) for p in pts)
            c = int(max(REVIEW_MIN_CROP, 3 * eq_diam(fl["area"]), 2 * span + 3 * eq_diam(fl["area"])))
            x0, y0 = int(cx - c / 2), int(cy - c / 2)

            if t == "INTERIOR_LOST":
                specs = [(fl["file"], f"LAST f{fl['frame']} (yellow=bubble)", [("circle_y", cur, None)]),
                         (fl["next_file"], f"NEXT f{fl['frame'] + 1} (gone?)", [("circle_r", cur, None)])]
            else:
                pf = fl["prev_frame"] if fl["prev_frame"] is not None else fl["frame"] - 1
                before_marks = [("circle_y", fl["prev_xy"], None)] if fl["prev_xy"] else []
                now_marks = [("circle_r", cur, None)]
                if fl["pred_xy"]:
                    now_marks.append(("square_c", fl["pred_xy"], None))
                if fl["prev_xy"]:
                    now_marks.append(("arrow", fl["prev_xy"], cur))
                specs = [(fl["prev_file"], f"BEFORE f{pf}", before_marks),
                         (fl["file"], f"NOW f{fl['frame']}", now_marks)]
            imgs = [load(fn) for fn, _, _ in specs]
            if all(im is None for im in imgs):
                continue
            panels = [(_panel(im, x0, y0, c, lab, mk) if im is not None
                       else np.full((REVIEW_PANEL, REVIEW_PANEL, 3), 40, np.uint8))
                      for im, (_, lab, mk) in zip(imgs, specs)]
            sheet = np.hstack([panels[0], np.full((REVIEW_PANEL, 6, 3), 255, np.uint8), panels[1]])
            bar = np.zeros((64, sheet.shape[1], 3), np.uint8)
            cv2.putText(bar, f"{t}  ID{fl['tid']}  frame {fl['frame']}  area {fl['area']:.0f}px ({fl['cls']})",
                        (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(bar, fl["ascii"][:95], (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            legend = np.zeros((26, sheet.shape[1], 3), np.uint8)
            cv2.putText(legend, "yellow=previous position  red=current  cyan square=predicted  arrow=actual move",
                        (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            d = os.path.join(out_dir, "review", t)
            os.makedirs(d, exist_ok=True)
            cv2.imwrite(os.path.join(d, f"{fl['cls']}_f{fl['frame']:05d}_ID{fl['tid']}.png"),
                        np.vstack([bar, sheet, legend]))
            saved += 1
    return saved


def main():
    base = os.path.dirname(os.path.abspath(TRACKING_CSV))
    clean_dir = os.path.join(base, "_cache_processed")
    overlay_dir = REVIEW_IMAGE_DIR or (clean_dir if os.path.isdir(clean_dir) else base)
    out_dir = OUT_DIR or os.path.join(base, "qc_tracking")
    os.makedirs(out_dir, exist_ok=True)

    rows, frame_files, has_touch = load_tracking_csv(TRACKING_CSV)
    if not rows:
        raise SystemExit("CSVに気泡の行がありません: " + TRACKING_CSV)
    img_hw = None if has_touch else image_size_from(overlay_dir, frame_files)
    if not has_touch and img_hw is None:
        print("※ フレーム接触の列がなく画像サイズも不明なため、画面端の判定を行いません (旧形式CSV)")
    roi = load_roi(QC_REPORT or os.path.join(base, "qc_report.json"))

    flags, info = analyze(rows, frame_files, has_touch, img_hw)
    s = summarize(flags, info, roi)
    try:
        with open(QC_REPORT or os.path.join(base, "qc_report.json"), encoding="utf-8") as fp:
            up = json.load(fp).get("used_params", {})
        s["tracker_gates"] = {k: up.get(k) for k in ("MAX_LEADING_EDGE_JUMP", "MAX_CENTER_X_JUMP", "AREA_RATIO_GATE",
                                                    "SPACING_GATE_FRAC", "USE_FLOW_PRIOR")}
    except (OSError, ValueError):
        s["tracker_gates"] = None
    s["source_csv"] = os.path.abspath(TRACKING_CSV)
    write_flags(os.path.join(out_dir, "qc_flags.csv"), flags, roi)
    with open(os.path.join(out_dir, "qc_summary.json"), "w", encoding="utf-8") as fp:
        json.dump(s, fp, ensure_ascii=False, indent=2)
    print_report(s, roi)
    n = save_review_images(flags, overlay_dir, out_dir) if SAVE_REVIEW_IMAGES else 0
    print(f"\n一覧: {os.path.join(out_dir, 'qc_flags.csv')}")
    if n:
        print(f"確認用画像 {n}枚: {os.path.join(out_dir, 'review')}  (ファイル名の先頭がサイズ区分。large から確認)")


if __name__ == "__main__":
    main()

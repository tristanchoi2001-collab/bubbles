"""
PIV 初速度推定の検証 (docs/PIV_TASK.md 6-1, 6-2) — 正解ID付きの合成データ
=====================================================================
  - 画像 1174 (縦) × 464 (横)、上向きの流れ。スラグ (large) + 小気泡 (small) + 微小気泡 (tiny)
  - 中速: 大きさによらず ほぼ同じ速度 / 高速: スラグが速い (tiny 25, small 30, large 42 px/frame)、
    フレームごとに ±3 px/frame ゆらぐ (中速は ±1)
  - 検出の欠落: tiny 25%, small 10% (large 0%)
  - U-Net の代わりに、正解マスクから作った確率マップ (fake_detector.py) をトラッカーの extract_instances に通す
  - スラグに追い越された小気泡はスラグに吸収される (正解の合体。吸収先への連結は誤連結に数えない)
  - 指標 (大きさ区分別): 誤連結率 (同じトラックの連続観測で正解の気泡が変わった割合)、
    正解の気泡1個あたりのトラック数 (途切れ)、画面内部での新規トラック数/フレーム
  追加の条件 (仕様外。PIV の弱点を確かめるため):
    lateral : 横向きの流れ (高さで向きが変わる帯状の流れ、最大 ±10 px/frame) -> PIV の横成分 (PIV_USE_DX) の効果
    static  : 小気泡・微小気泡の 30% が壁に付いて止まっている            -> 止まった気泡と動く気泡が混ざる窓

使い方:
  python -B sim_piv.py                  # 全条件 × シード 1〜3
  python -B sim_piv.py --quick          # 中速・高速 × シード 1 だけ
  python -B sim_piv.py --seeds 1 2 3 4 5 --conds fast fast_static
結果は表で表示し、sim_piv_results.json にも保存する。
"""
import argparse
import contextlib
import importlib
import io
import json
import math
import time
from collections import defaultdict

import cv2
import numpy as np
from scipy import ndimage

import fake_detector
import piv_field

H, W = 1174, 464
N_FRAMES = 60
CLASSES = ("tiny", "small", "large")

CONDS = {
    "mid":         dict(v={"tiny": 15.0, "small": 15.0, "large": 16.0}, jit=1.0, vx=0.0, static=0.0),
    "fast":        dict(v={"tiny": 25.0, "small": 30.0, "large": 42.0}, jit=3.0, vx=0.0, static=0.0),
    "fast_lateral": dict(v={"tiny": 25.0, "small": 30.0, "large": 42.0}, jit=3.0, vx=10.0, static=0.0),
    "fast_static": dict(v={"tiny": 25.0, "small": 30.0, "large": 42.0}, jit=3.0, vx=0.0, static=0.3),
}
DROP = {"tiny": 0.25, "small": 0.10, "large": 0.0}
N_ON = {"tiny": 70, "small": 30}     # 画面内の平均個数 (実画像: tiny 約74, small 約28, large 約4)


def size_class(a):
    return piv_field.size_class(a)


# ==============================================================
# 1. 合成シーン
# ==============================================================
def simulate(seed, cond, n_frames=N_FRAMES):
    """戻り値: frames = [(正解ラベル画像, {ラベル: gid})], succ = {gid: 吸収先 gid}, gcls = {gid: 区分}"""
    rng = np.random.default_rng(seed)
    c = CONDS[cond]
    gid = [0]
    succ, gcls = {}, {}

    def new_small(cls, y):
        gid[0] += 1
        area = rng.uniform(15, 49) if cls == "tiny" else rng.uniform(50, 499)
        r = math.sqrt(area / math.pi)
        static = rng.random() < c["static"]
        b = dict(gid=gid[0], cls=cls, x=rng.uniform(6 + r, W - 6 - r), y=y, r=r,
                 vy=0.0 if static else c["v"][cls] * rng.uniform(0.92, 1.08),
                 vx=0.0 if static else (rng.normal(0, 1.0) if c["vx"] else 0.0), static=static)
        gcls[b["gid"]] = cls
        return b

    def new_slug(y):
        gid[0] += 1
        w, l = rng.uniform(110, 170), rng.uniform(180, 380)
        b = dict(gid=gid[0], cls="large", x=rng.uniform(70 + w / 2, W - 70 - w / 2), y=y, w=w, l=l,
                 vy=c["v"]["large"] * rng.uniform(0.97, 1.03), vx=0.0, static=False)
        gcls[b["gid"]] = "large"
        return b

    bubbles = [new_small(cls, rng.uniform(0, H)) for cls in ("tiny", "small") for _ in range(N_ON[cls])]
    y = rng.uniform(80, 300)
    while y < H + 200:
        s = new_slug(y)
        bubbles.append(s)
        y += s["l"] + rng.uniform(200, 450)

    def slug_mask(b):
        m = np.zeros((H, W), np.uint8)
        x0, x1 = int(b["x"] - b["w"] / 2), int(b["x"] + b["w"] / 2)
        nose = b["y"] + b["w"] / 2
        cv2.ellipse(m, (int(b["x"]), int(nose)), (int(b["w"] / 2), int(b["w"] / 2)), 0, 180, 360, 1, -1)
        cv2.rectangle(m, (x0, int(nose)), (x1, int(b["y"] + b["l"])), 1, -1)
        return m.astype(bool)

    frames = []
    drop_stats = {c: defaultdict(int) for c in CLASSES}   # 実際の欠落率 (乱数の欠落 + 接触で描かない分)
    for f in range(n_frames):
        if f > 0:
            for b in bubbles:
                if b["static"]:
                    continue
                b["y"] -= b["vy"] + rng.uniform(-c["jit"], c["jit"])
                lateral = c["vx"] * math.sin(2 * math.pi * b["y"] / 500.0) if b["cls"] != "large" else 0.0
                b["x"] += lateral + b["vx"] + rng.normal(0, 0.5)
                if b["cls"] != "large":
                    rr = b["r"] + 3
                    if b["x"] < rr or b["x"] > W - rr:   # 横の壁で跳ね返る
                        b["vx"] = -b["vx"]
                        b["x"] = min(max(b["x"], rr), W - rr)
            bubbles = [b for b in bubbles if b["y"] + b.get("l", 2 * b.get("r", 0)) > -5]
            for cls in ("tiny", "small"):   # 下から流れ込む
                lam = N_ON[cls] * c["v"][cls] * (1 - c["static"]) / H
                for _ in range(rng.poisson(lam)):
                    bubbles.append(new_small(cls, H + rng.uniform(0, c["v"][cls])))
            slugs_now = [b for b in bubbles if b["cls"] == "large"]
            lowest = max((b["y"] for b in slugs_now), default=-1e9)
            if lowest < H - 200:   # 前のスラグの後端から液の間隔をあけて次のスラグを入れる
                tail = max((b["y"] + b["l"] for b in slugs_now), default=-1e9)
                bubbles.append(new_slug(max(H + rng.uniform(0, 300), tail + rng.uniform(200, 450))))

        lab = np.zeros((H, W), np.int32)
        truth = {}
        k = 0
        slugs = [b for b in bubbles if b["cls"] == "large"]
        smasks = [(b, slug_mask(b)) for b in slugs]
        absorbed = set()
        for b in bubbles:   # スラグに追い越された (重なった) 小気泡はスラグに吸収 = 合体
            if b["cls"] == "large":
                continue
            yi, xi, ri = int(round(b["y"])), int(round(b["x"])), int(b["r"]) + 1
            if not (0 <= yi < H):
                continue
            for s, m in smasks:
                if m[max(0, yi - ri):yi + ri + 1, max(0, xi - ri):xi + ri + 1].any():
                    absorbed.add(b["gid"])
                    succ[b["gid"]] = s["gid"]
                    break
        bubbles = [b for b in bubbles if b["gid"] not in absorbed]
        order = [b for b in bubbles if b["cls"] == "large"] + \
                [b for b in bubbles if b["cls"] == "small"] + [b for b in bubbles if b["cls"] == "tiny"]
        smask_by_gid = {s["gid"]: m for s, m in smasks}
        for b in order:
            inside = 0 <= b["y"] < H
            drop_stats[b["cls"]]["in_frame"] += inside
            if rng.random() < DROP[b["cls"]]:
                drop_stats[b["cls"]]["random_drop"] += inside
                continue
            if b["cls"] == "large":
                mb = smask_by_gid[b["gid"]]
            else:
                m = np.zeros((H, W), np.uint8)
                cv2.circle(m, (int(round(b["x"])), int(round(b["y"]))), max(1, int(round(b["r"]))), 1, -1)
                mb = m.astype(bool)
            if not mb.any():
                continue
            if b["cls"] != "large" and (ndimage.binary_dilation(mb, iterations=2) & (lab > 0)).any():
                drop_stats[b["cls"]]["contact_skip"] += inside
                continue   # 他の気泡と接触 -> 描かない (このフレームは欠落と同じ)
            k += 1
            lab[mb & (lab == 0)] = k
            truth[k] = b["gid"]
        frames.append((lab, truth))
    simulate.last_drop_stats = drop_stats
    return frames, succ, gcls


# ==============================================================
# 2. 偽検出 (正解マスク -> 確率マップ -> extract_instances)
# ==============================================================
def detect_frames(frames, T_ref):
    """各フレームのインスタンスラベル画像と、各インスタンスの正解 gid"""
    out = []
    for lab, truth in frames:
        p = fake_detector.fake_prob(lab, T_ref.UNET_CLOSE)
        inst = T_ref.extract_instances(p, T_ref.UNET_MIN_AREA, T_ref.UNET_BAND, T_ref.UNET_EDGE_THR,
                                       T_ref.UNET_CLOSE, T_ref.UNET_TINY_MAX)
        ov = fake_detector.overlap_table(lab, inst)
        gts = {}
        for r in range(1, inst.max() + 1):
            col = ov[1:, r]
            gts[r] = truth.get(int(np.argmax(col)) + 1) if col.any() else None
        out.append((inst, gts))
    return out


def detections_for(T, detected):
    """トラッカー T の Detection と、各検出の正解 gid"""
    roi = np.ones((H, W), bool)
    dets_pf, gt_pf = [], []
    for inst, gts in detected:
        dets = T.instances_to_detections(inst, roi)
        # 検出をマスクの画素から元のラベルに戻す (IGNORE_PARTICLE_AREA で数 px の検出が捨てられるので、
        # 検出の数・順番はラベルと一致しない)
        labels = []
        for d in dets:
            m, x0, y0 = d.shape
            ys, xs = np.nonzero(m)
            labels.append(int(inst[ys[0] + y0, xs[0] + x0]))
        dets_pf.append(dets)
        gt_pf.append([gts.get(k) for k in labels])
    return dets_pf, gt_pf


# ==============================================================
# 3. トラッカーの実行
# ==============================================================
OLD_FLAGS = {"USE_FLOW_PRIOR": False, "SPACING_GATE_FRAC": 0.0, "COAST_GATE_GROWTH": 1.0, "SHAPE_AREA_REF": 1e-9}

VARIANTS = {
    # 名前: (モジュール, 上書きする設定)
    "旧 (v2前)":            ("tracker2", OLD_FLAGS),
    "v2":                   ("tracker2", {}),
    "tracker3 (変更前)":    ("tracker3", {"USE_PIV_PRIOR": False, "PRIOR_AREA_RATIO": 0.0}),   # PIV 導入前と同じ動作
    "tracker3 PIVなし":     ("tracker3", {"USE_PIV_PRIOR": False}),   # 周りの気泡の速度を大きさの近い気泡に限定しただけ
    "tracker3+PIV(忠実)":   ("tracker3", {"PIV_MODE": "faithful", "PIV_RASTER": "filled"}),
    "tracker3+PIV":         ("tracker3", {}),
    # 以下は既定の比較に含めない設定の比較用 (--variants で指定)
    "PIV soft gate":        ("tracker3", {"PIV_GATE_HARD": False}),
    "PIV hard always":      ("tracker3", {"PIV_STATIC_SPEED": 0.0}),
    "PIV no static":        ("tracker3", {"PIV_KEEP_STATIC": False}),
    "PIV no dx":            ("tracker3", {"PIV_USE_DX": False}),
    "PIV gate10":           ("tracker3", {"PIV_GATE": 10.0}),
    "PIV no size fallback": ("tracker3", {"PRIOR_AREA_RATIO": 0.0}),
    "PIV tiny big window":  ("tracker3", {"PIV_WINDOWS": {"tiny": (384, 192, 192, 96), "small": (256, 128, 128, 64),
                                                          "large": (256, 128, 128, 64)}}),
}
DEFAULT_VARIANTS = ["旧 (v2前)", "v2", "tracker3 (変更前)", "tracker3 PIVなし", "tracker3+PIV(忠実)", "tracker3+PIV"]


def run_variant(module, overrides, dets_pf):
    T = importlib.import_module(module)
    importlib.reload(T)   # 設定 (グローバル変数) を初期値に戻す
    for k, v in overrides.items():
        setattr(T, k, v)
    stats = T._bootstrap_collect_stats(dets_pf) if module == "tracker2" else T._bootstrap_collect_stats(dets_pf, (H, W))
    params = T._bootstrap_compute_params(*stats[:3], *stats[4:5]) if module == "tracker3" else \
        T._bootstrap_compute_params(*stats[:3])
    for k, v in (params or {}).items():   # ブートストラップの自動値を採用 ([Enter] と同じ)
        setattr(T, k, v)
    for k, v in overrides.items():
        if k in ("PIV_GATE",):
            setattr(T, k, v)
    t0 = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        rows = T.run_laptrack(dets_pf, (H, W)) if module == "tracker3" else T.run_laptrack(dets_pf)
    dt = time.perf_counter() - t0
    st = getattr(T.run_laptrack, "last_stats", {}) if module == "tracker3" else {}
    return rows, params, dt, st


# ==============================================================
# 4. 評価
# ==============================================================
def evaluate(rows_by_frame, dets_pf, gt_pf, succ, gcls):
    """大きさ区分別: links / wrong / gt / tracks (全観測) / tracks_in (画面端に接する観測を除く)、
    画面内部の新規トラック数、誤った合体・分裂の数 (この合成で起きる合体はスラグによる吸収だけ、分裂は起きない)"""
    m = {c: defaultdict(int) for c in CLASSES}
    seq = defaultdict(list)
    gt_tracks = defaultdict(set)
    gt_tracks_in = defaultdict(set)
    interior_new = 0
    ev = defaultdict(int)
    merges = []
    for f, gts in enumerate(gt_pf):
        for r in rows_by_frame.get(f, []):
            j = r["det_index"]
            if j is None:
                continue
            g = gts[j]
            d = dets_pf[f][j]
            if r["event"] == "new" and not d.touches_frame and f > 0:
                interior_new += 1
            if r["event"] == "split":
                ev["false_split"] += 1
            if r["event"] == "merge":
                merges.append((f, g, r["parent_ids"]))
            if g is None:
                continue
            seq[r["track_id"]].append((f, g))
            gt_tracks[g].add(r["track_id"])
            if not d.touches_frame:
                gt_tracks_in[g].add(r["track_id"])
    for tid, s_ in seq.items():
        s_.sort()
        for (_, g1), (_, g2) in zip(s_, s_[1:]):
            c = gcls[g1]
            m[c]["links"] += 1
            if g1 != g2 and succ.get(g1) != g2:
                m[c]["wrong"] += 1
    last_gt = {tid: s_ for tid, s_ in seq.items()}
    for f, g, parents in merges:   # 合体の構成メンバーが、合体後の気泡に正しく吸収された気泡か
        ok = g is not None
        for p in parents:
            prev = [gg for ff, gg in last_gt.get(p, []) if ff < f]
            ok = ok and bool(prev) and (prev[-1] == g or succ.get(prev[-1]) == g)
        ev["merge"] += 1
        ev["false_merge"] += int(not ok)
    for g, ts in gt_tracks.items():
        m[gcls[g]]["gt"] += 1
        m[gcls[g]]["tracks"] += len(ts)
    for g, ts in gt_tracks_in.items():
        m[gcls[g]]["gt_in"] += 1
        m[gcls[g]]["tracks_in"] += len(ts)
    return m, interior_new, ev


def prior_errors(frames, dets_pf, gt_pf, succ):
    """新しく現れた気泡 (前フレームで検出されていない気泡) の初速度推定の誤差 (px/frame)。
    PIV の行はすべて「埋めた値も含めて」その場所の値を使い、別に無効 (周りに実測の窓がない) の割合を数える。
      zero          : 速度 0
      nb_all        : 周りの気泡 (150px 以内) の正解速度の中央値。大きさ問わず (v2 の考え方の理想的な場合)
      nb_same       : 同上、同じ大きさ区分の気泡だけ
      all           : 相互相関、全区分まとめた画像 (塗りつぶし)
      class_faithful: 相互相関、区分別 (piv_prior.py と同じ計算、塗りつぶし)
      class_improved: 相互相関、区分別 (改良、輪郭)  <- トラッカーの既定
      class_noself  : 同上、ただし t+1 の画像から「新しく現れた気泡」を除いて計算 (気泡自身との対応ではなく、
                      周りの気泡の動きだけで推定できているかを見る)"""
    pos = defaultdict(dict)
    for f, (dets, gts) in enumerate(zip(dets_pf, gt_pf)):
        for d, g in zip(dets, gts):
            if g is not None and not d.touches_frame:
                pos[g][f] = (d.cx, d.cy, size_class(d.area))
    s_imp = piv_field.PIVSettings()
    s_fai = piv_field.PIVSettings.faithful(raster="filled")
    keys = ("zero", "nb_all", "nb_same", "all", "class_faithful", "class_improved", "class_noself")
    errs = {k: {c: [] for c in CLASSES} for k in keys}
    inval = {k: {c: 0 for c in CLASSES} for k in keys}
    for f in range(len(dets_pf) - 1):
        dets, gts = dets_pf[f], gt_pf[f]
        new_idx = [j for j, g in enumerate(gts) if g is not None and f - 1 not in pos[g] and f in pos[g]
                   and f + 1 in pos[g]]
        if not new_idx:
            continue
        new_g = {gts[j] for j in new_idx}
        nxt = dets_pf[f + 1]
        nxt_wo = [d for d, g in zip(nxt, gt_pf[f + 1]) if g not in new_g]
        fi = piv_field.compute_fields(dets, nxt, (H, W), s_imp)
        fn = piv_field.compute_fields(dets, nxt_wo, (H, W), s_imp)
        ff = piv_field.compute_fields(dets, nxt, (H, W), s_fai)
        ra = sum(piv_field.rasterize(dets, (H, W), s_fai).values()).clip(0, 255).astype(np.uint8)
        rb = sum(piv_field.rasterize(nxt, (H, W), s_fai).values()).clip(0, 255).astype(np.uint8)
        fall = piv_field.DisplacementField(ra, rb, 256, 128, 128, 64, s=s_fai)
        truth_v = {g: (p[f + 1][0] - p[f][0], p[f + 1][1] - p[f][1], p[f][2])
                   for g, p in pos.items() if f in p and f + 1 in p}
        for j in new_idx:
            d, g = dets[j], gts[j]
            c = size_class(d.area)
            tvx, tvy, _ = truth_v[g]
            errs["zero"][c].append(math.hypot(tvx, tvy))
            for key, same in (("nb_all", False), ("nb_same", True)):
                nb = [v for gg, v in truth_v.items() if gg != g and gg not in new_g
                      and math.hypot(pos[gg][f][0] - d.cx, pos[gg][f][1] - d.cy) <= 150 and (not same or v[2] == c)]
                if nb:
                    nvx, nvy = float(np.median([v[0] for v in nb])), float(np.median([v[1] for v in nb]))
                else:
                    nvx = nvy = 0.0
                    inval[key][c] += 1
                errs[key][c].append(math.hypot(tvx - nvx, tvy - nvy))
            dy, dx, ok = fall.sample(d.cx, d.cy)
            inval["all"][c] += int(not ok)
            errs["all"][c].append(math.hypot(tvx - dx, tvy - dy))
            for key, flds in (("class_faithful", ff), ("class_improved", fi), ("class_noself", fn)):
                fl = flds.get(c)
                if fl is None:
                    dy = dx = 0.0
                    ok = False
                else:
                    dy, dx, ok = fl.sample(d.cx, d.cy)
                inval[key][c] += int(not ok)
                errs[key][c].append(math.hypot(tvx - dx, tvy - dy))
    return errs, inval


# ==============================================================
# 5. 実行・表示
# ==============================================================
def fmt_pct(a, b):
    return f"{100.0 * a / b:.2f}" if b else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[1, 2, 3])
    ap.add_argument("--conds", nargs="*", default=list(CONDS))
    ap.add_argument("--frames", type=int, default=N_FRAMES)
    ap.add_argument("--variants", nargs="*", default=DEFAULT_VARIANTS)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-prior-table", action="store_true")
    ap.add_argument("--out", default="sim_piv_results.json")
    args = ap.parse_args()
    if args.quick:
        args.seeds, args.conds = [1], ["mid", "fast"]
    variants = {k: VARIANTS[k] for k in args.variants}
    T3 = importlib.import_module("tracker3")
    results = {}
    for cond in args.conds:
        tot = {v: {c: defaultdict(int) for c in CLASSES} for v in variants}
        newin = defaultdict(int)
        evs = {v: defaultdict(int) for v in variants}
        times = defaultdict(list)
        perr = pinv = None
        drops = {c: defaultdict(int) for c in CLASSES}
        n_frames_total = 0
        for seed in args.seeds:
            frames, succ, gcls = simulate(seed, cond, args.frames)
            for c in CLASSES:
                for k, val in simulate.last_drop_stats[c].items():
                    drops[c][k] += val
            detected = detect_frames(frames, T3)
            n_frames_total += len(frames)
            for v, (module, ov) in variants.items():
                T = importlib.import_module(module)
                dets_pf, gt_pf = detections_for(T, detected)
                rows, params, dt, st = run_variant(module, ov, dets_pf)
                m, ni, ev = evaluate(rows, dets_pf, gt_pf, succ, gcls)
                for c in CLASSES:
                    for k, val in m[c].items():
                        tot[v][c][k] += val
                for k, val in ev.items():
                    evs[v][k] += val
                newin[v] += ni
                times[v].append(1000 * dt / len(frames))
                print(f"  [{cond} seed{seed}] {v}: ブートストラップ {params}  {1000 * dt / len(frames):.0f} ms/フレーム"
                      + (f"  初速度 {st.get('prior_counts')}" if st else ""), flush=True)
            if not args.no_prior_table:
                dets3, gt3 = detections_for(T3, detected)
                e, iv = prior_errors(frames, dets3, gt3, succ)
                if perr is None:
                    perr, pinv = e, iv
                else:
                    for k in perr:
                        for c in CLASSES:
                            perr[k][c] += e[k][c]
                            pinv[k][c] += iv[k][c]
        nf = n_frames_total - len(args.seeds)
        eff = {c: (drops[c]["random_drop"] + drops[c]["contact_skip"]) / max(1, drops[c]["in_frame"]) for c in CLASSES}
        print(f"\n=== 条件 {cond} (シード {args.seeds}, 各 {args.frames} フレーム) ===")
        print("  実際の検出欠落率 (乱数 + 他の気泡に接して描かない分): "
              + ", ".join(f"{c} {100 * eff[c]:.1f}%" for c in CLASSES))
        print(f"{'方式':<20}" + "".join(f"{c + ' 誤連結%':>12}{c + ' トラック/気泡':>14}{'(内部)':>8}" for c in CLASSES)
              + f"{'内部新規/F':>11}{'誤合体':>7}{'分裂':>6}{'ms/F':>7}")
        res_c = {"effective_drop": eff}
        for v in variants:
            row = f"{v:<20}"
            rc = {}
            for c in CLASSES:
                d = tot[v][c]
                tpg = d["tracks"] / d["gt"] if d["gt"] else float("nan")
                tpg_in = d["tracks_in"] / d["gt_in"] if d["gt_in"] else float("nan")
                row += f"{fmt_pct(d['wrong'], d['links']):>12}{tpg:>14.2f}{tpg_in:>8.2f}"
                rc[c] = {"links": d["links"], "wrong": d["wrong"],
                         "wrong_pct": 100.0 * d["wrong"] / d["links"] if d["links"] else None,
                         "gt": d["gt"], "tracks_per_gt": tpg, "tracks_per_gt_interior": tpg_in}
            row += f"{newin[v] / max(1, nf):>11.2f}{evs[v]['false_merge']:>7d}{evs[v]['false_split']:>6d}{np.mean(times[v]):>7.0f}"
            rc.update(interior_new_per_frame=newin[v] / max(1, nf), false_merge=evs[v]["false_merge"],
                      merge=evs[v]["merge"], false_split=evs[v]["false_split"], ms_per_frame=float(np.mean(times[v])))
            res_c[v] = rc
            print(row)
        print("  (トラック/気泡 = 正解の気泡1個あたりのトラック数。(内部) は画面端に接する観測を除いたもの。"
              "誤合体 = 正解の吸収と一致しない合体、分裂 = この合成では起きないので全て誤り)")
        if perr is not None:
            print("\n  新しく現れた気泡の初速度推定の誤差 (中央値 px/frame)。[ ] 内は速度場が無効 (周りに実測の窓がない) の割合")
            names = {"zero": "速度 0", "nb_all": "周りの気泡 正解速度 (大きさ問わず)", "nb_same": "周りの気泡 正解速度 (同じ区分)",
                     "all": "相互相関 全区分まとめて", "class_faithful": "相互相関 区分別 (忠実・塗り)",
                     "class_improved": "相互相関 区分別 (改良・輪郭)", "class_noself": "  同上、t+1 から新規気泡を除く"}
            res_c["prior_error"] = {}
            for k, nm in names.items():
                vals = {}
                line = f"  {nm:<30}"
                for c in CLASSES:
                    e = perr[k][c]
                    if not e:
                        line += f"{c}     -           "
                        continue
                    med, ninv = float(np.median(e)), pinv[k][c]
                    vals[c] = {"median": med, "n": len(e), "invalid_frac": ninv / len(e)}
                    line += f"{c} {med:6.1f} [{100 * ninv / len(e):3.0f}%] "
                res_c["prior_error"][k] = vals
                print(line)
        results[cond] = res_c
    with open(args.out, "w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=False, indent=1)
    print(f"\n結果: {args.out}")


if __name__ == "__main__":
    main()

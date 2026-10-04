"""
合成データで tracker2.py と tracker3.py のトラッキングを比較する検証スクリプト
=====================================================================
U-Net も実画像も使わず、正解 (どの検出がどの気泡か、いつ合体/分裂したか) が分かっている
気泡ラベル画像を作り、各トラッカーの instances_to_detections -> ブートストラップ(自動値) -> run_laptrack
を実行して、正解と突き合わせる。

合成シーン (qc_flags.csv で問題が多かった状況を再現):
  - 静止〜ゆっくり動く小気泡 (面積 15〜450px)
  - 下端から入って斜めに上昇する速い気泡 (30〜55 px/frame、x 方向にも ±25px/frame)
  - ゆっくり変形・移動する大気泡 + 左端で切れている巨大な気泡
  - 速い気泡がほかの気泡にぶつかると合体 (面積保存で丸くなる)
  - 速い気泡のランダムな分裂 (面積保存)
  - 接している2つの静止気泡の境界が 1フレームだけ消える (2値化で境界が途切れた状況。正解は「合体ではない」)
  - 数px のノイズ、検出の一時的な欠落

使い方:  python sim_compare.py            (シード 5 個の合計を表示)
          python sim_compare.py 10 1       (シード 10 個、1 から)
"""
import math
import sys
import importlib
from collections import defaultdict
from dataclasses import dataclass

import cv2
import numpy as np

H, W = 1080, 416
N_FRAMES = 60


@dataclass
class SimBubble:
    gid: int
    x: float
    y: float
    area: float
    vx: float
    vy: float
    kind: str               # "static" / "fast" / "large"
    ar: float = 1.0         # 楕円の縦横比 (large のみ)
    angle: float = 0.0
    phase: float = 0.0
    cooldown: int = 0       # 合体/分裂の直後は次の合体/分裂をしない
    pair: int = -1          # 接触ペアの番号 (このペア同士は合体しない)

    @property
    def r(self):
        return math.sqrt(self.area / math.pi)


def _draw(lab, b: SimBubble, value):
    """気泡 b をラベル画像 lab に値 value で描く"""
    if b.kind == "large":
        a = b.r * math.sqrt(b.ar)
        c = b.r / math.sqrt(b.ar)
        cv2.ellipse(lab, (int(round(b.x)), int(round(b.y))), (max(1, int(a)), max(1, int(c))),
                    b.angle, 0, 360, int(value), -1)
    else:
        cv2.circle(lab, (int(round(b.x)), int(round(b.y))), max(1, int(round(b.r))), int(value), -1)


def simulate(seed: int, n_frames: int = N_FRAMES):
    """戻り値: frames = [(ラベル画像, {ラベル: 正解}), ...], events = [(種類, フレーム, 元のgid群, 後のgid群), ...]
    正解は gid (>=0)、ノイズは -1、接触で1つに見えている塊は ("contact", g1, g2)"""
    rng = np.random.default_rng(seed)
    next_gid = [0]

    def gid():
        next_gid[0] += 1
        return next_gid[0]

    bubbles = []
    for _ in range(35):   # 静止気泡
        bubbles.append(SimBubble(gid(), rng.uniform(15, W - 15), rng.uniform(15, H - 15),
                                 rng.uniform(15, 450), 0.0, 0.0, "static"))
    for p in range(4):    # 接している静止気泡のペア
        r1, r2 = rng.uniform(5, 9), rng.uniform(5, 9)
        x, y = rng.uniform(30, W - 50), rng.uniform(40, H - 40)
        bubbles.append(SimBubble(gid(), x, y, math.pi * r1 * r1, 0.0, 0.0, "static", pair=p))
        bubbles.append(SimBubble(gid(), x + r1 + r2 + 2, y, math.pi * r2 * r2, 0.0, 0.0, "static", pair=p))
    for y in (250, 550, 850):    # 大気泡 (互いに重ならない位置でゆっくり動く)
        bubbles.append(SimBubble(gid(), rng.uniform(190, W - 110), y + rng.uniform(-40, 40),
                                 rng.uniform(5000, 15000), rng.normal(0, 0.3), rng.normal(0, 0.3), "large",
                                 ar=1.5, angle=rng.uniform(0, 180), phase=rng.uniform(0, 6)))
    bubbles.append(SimBubble(gid(), -40.0, 500.0, 60000, 0.0, -0.5, "large", ar=4.0, angle=90.0))  # 左端で切れた巨大気泡

    def spawn_fast(y=None):
        area = rng.uniform(150, 2000)
        r = math.sqrt(area / math.pi)
        return SimBubble(gid(), rng.uniform(r + 5, W - r - 5), H + 0.3 * r if y is None else y, area,
                         rng.uniform(-25, 25), rng.uniform(-55, -30), "fast")

    for _ in range(6):
        bubbles.append(spawn_fast(rng.uniform(100, H - 100)))

    events = []
    frames = []
    for f in range(n_frames):
        # ---- 移動 ----
        for b in bubbles:
            if b.kind == "fast":
                b.vx = float(np.clip(b.vx + rng.normal(0, 2), -30, 30))
                b.vy = float(np.clip(b.vy + rng.normal(0, 2), -60, -25))
                if b.x - b.r < 0 or b.x + b.r > W:
                    b.vx = -b.vx
            elif b.kind == "static":
                b.vx, b.vy = rng.normal(0, 0.3), rng.normal(0, 0.3)
            else:
                b.phase += 0.3
                b.ar = max(1.0, b.ar + 0.15 * math.sin(b.phase)) if b.ar < 3 else b.ar
                b.angle += rng.normal(0, 3)
                b.area *= 1 + rng.normal(0, 0.01)
            if f > 0:
                b.x += b.vx
                b.y += b.vy
            b.cooldown = max(0, b.cooldown - 1)
            if b.kind != "large":
                b.area *= 1 + rng.normal(0, 0.01)
        bubbles = [b for b in bubbles if b.y + b.r > 0]
        if f > 0 and rng.random() < 0.6:
            bubbles.append(spawn_fast())

        # ---- 合体 (ぶつかったら面積保存で1つの気泡に) ----
        if f > 0:
            merged = True
            while merged:
                merged = False
                for a_i in range(len(bubbles)):
                    for b_i in range(a_i + 1, len(bubbles)):
                        a, b = bubbles[a_i], bubbles[b_i]
                        if a.kind != "fast" and b.kind != "fast":
                            continue
                        if a.cooldown or b.cooldown:
                            continue
                        ra = a.r * (0.8 if a.kind == "large" else 1.0)
                        rb = b.r * (0.8 if b.kind == "large" else 1.0)
                        if math.hypot(a.x - b.x, a.y - b.y) >= 0.9 * (ra + rb):
                            continue
                        big, small = (a, b) if a.area >= b.area else (b, a)
                        tot = a.area + b.area
                        c = SimBubble(gid(), (a.x * a.area + b.x * b.area) / tot, (a.y * a.area + b.y * b.area) / tot,
                                      tot, (a.vx * a.area + b.vx * b.area) / tot,
                                      (a.vy * a.area + b.vy * b.area) / tot,
                                      big.kind, ar=big.ar, angle=big.angle, phase=big.phase, cooldown=3)
                        if c.kind == "static":
                            c.kind = "fast"
                        events.append(("merge", f, (a.gid, b.gid), (c.gid,)))
                        bubbles = [x for x in bubbles if x is not a and x is not b] + [c]
                        merged = True
                        break
                    if merged:
                        break

        # ---- 分裂 ----
        if f > 0:
            for b in list(bubbles):
                if b.kind != "fast" or b.cooldown or b.r < 12 or b.y > H - 2 * b.r or b.y < 2 * b.r:
                    continue
                if rng.random() >= 0.03:
                    continue
                q = rng.uniform(0.3, 0.5)
                a1, a2 = b.area * (1 - q), b.area * q
                r1, r2 = math.sqrt(a1 / math.pi), math.sqrt(a2 / math.pi)
                sp = math.hypot(b.vx, b.vy) or 1.0
                nx, ny = -b.vy / sp, b.vx / sp
                if rng.random() < 0.5:
                    nx, ny = -nx, -ny
                d = r1 + r2 + 2
                c1 = SimBubble(gid(), b.x - nx * d * q, b.y - ny * d * q, a1, b.vx - 3 * nx, b.vy - 3 * ny,
                               "fast", cooldown=4)
                c2 = SimBubble(gid(), b.x + nx * d * (1 - q), b.y + ny * d * (1 - q), a2, b.vx + 3 * nx,
                               b.vy + 3 * ny, "fast", cooldown=4)
                events.append(("split", f, (b.gid,), (c1.gid, c2.gid)))
                bubbles = [x for x in bubbles if x is not b] + [c1, c2]

        # ---- 描画 (大きい順に描き、小さい気泡を上に) ----
        lab = np.zeros((H, W), np.int32)
        truth = {}
        k = 0
        contact_now = {p for p in range(4) if rng.random() < 0.08}
        by_pair = defaultdict(list)
        for b in sorted(bubbles, key=lambda b: -b.area):
            if rng.random() < 0.02:   # 検出の一時的な欠落
                continue
            if b.pair >= 0 and b.pair in contact_now:
                by_pair[b.pair].append(b)
                continue
            k += 1
            _draw(lab, b, k)
            truth[k] = b.gid
        for p, members in by_pair.items():
            k += 1
            for b in members:
                _draw(lab, b, k)
            if len(members) == 2:   # 2つの間の隙間も埋めて1つの塊にする
                a, b = members
                cv2.line(lab, (int(a.x), int(a.y)), (int(b.x), int(b.y)), int(k), int(min(a.r, b.r)))
                truth[k] = ("contact", a.gid, b.gid)
            else:
                truth[k] = members[0].gid
        for _ in range(5):            # ノイズ
            k += 1
            x, y = int(rng.uniform(0, W - 3)), int(rng.uniform(0, H - 3))
            s = int(rng.integers(2, 4))
            lab[y:y + s, x:x + s] = k
            truth[k] = -1
        frames.append((lab, truth))
    return frames, events


def to_detections(T, lab, truth):
    """ラベル画像 -> そのトラッカーの Detection リスト と 各検出の正解"""
    present = [v for v in np.unique(lab) if v > 0]
    lut = np.zeros(int(lab.max()) + 1, np.int32)
    lut[present] = np.arange(1, len(present) + 1)
    inst = lut[lab]
    roi = np.ones((H, W), bool)
    dets = T.instances_to_detections(inst, roi)
    assert len(dets) == len(present)
    return dets, [truth[v] for v in present]


def run_tracker(module_name: str, frames, bootstrap: bool = True):
    T = importlib.import_module(module_name)
    importlib.reload(T)   # パラメータ(グローバル変数)を初期値に戻す
    dets_pf, gt_pf = [], []
    for lab, truth in frames:
        d, g = to_detections(T, lab, truth)
        dets_pf.append(d)
        gt_pf.append(g)
    params = None
    if bootstrap:   # ユーザーが [Enter] で自動値を採用した場合と同じ
        stats = T._bootstrap_collect_stats(dets_pf)
        params = T._bootstrap_compute_params(*stats[:3])
        if params:
            for k, v in params.items():
                setattr(T, k, v)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rows = T.run_laptrack(dets_pf)
    return rows, gt_pf, params


def evaluate(rows_by_frame, gt_pf, events):
    succ = defaultdict(set)   # gid -> 合体/分裂で後を継いだ gid
    for kind, f, before, after in events:
        for b in before:
            succ[b].update(after)

    obs = defaultdict(list)   # gid -> [(フレーム, トラックID or None)]
    row_at = {}               # (フレーム, 検出番号) -> 行
    track_seq = defaultdict(list)
    for f, gts in enumerate(gt_pf):
        rows = {r["det_index"]: r for r in rows_by_frame.get(f, []) if r["det_index"] is not None}
        for j, g in enumerate(gts):
            r = rows.get(j)
            row_at[(f, j)] = r
            if isinstance(g, int) and g >= 0:
                obs[g].append((f, r["track_id"] if r else None))
                if r:
                    track_seq[r["track_id"]].append((f, g))

    m = defaultdict(int)
    for g, seq in obs.items():
        seq.sort()
        for (f1, t1), (f2, t2) in zip(seq, seq[1:]):
            if t1 is None or t2 is None:
                continue
            m["links"] += 1
            if t1 != t2:
                m["id_breaks"] += 1          # 同じ気泡なのにIDが変わった
        m["untracked"] += sum(1 for _, t in seq if t is None)
    for tid, seq in track_seq.items():
        seq.sort()
        for (_, g1), (_, g2) in zip(seq, seq[1:]):
            if g1 != g2 and g2 not in succ[g1]:
                m["swaps"] += 1              # 1つのIDが無関係な別の気泡に乗り移った

    def tid_of(g, f):
        for ff, t in obs.get(g, []):
            if ff == f:
                return t
        return None

    def det_of(g, f):
        for j, gg in enumerate(gt_pf[f]):
            if gg == g:
                return j
        return None

    gt_result_dets = defaultdict(set)   # フレーム -> 合体/分裂の結果の検出番号
    for kind, f, before, after in events:
        if f >= len(gt_pf):
            continue
        prev_t = [tid_of(b, f - 1) for b in before]
        after_j = [det_of(a, f) for a in after]
        for j in after_j:
            if j is not None:
                gt_result_dets[f].add(j)
        if any(t is None for t in prev_t) or any(j is None for j in after_j):
            continue   # 前後どちらかが見えていない (画面外・欠落) -> 評価しない
        rows = [row_at[(f, j)] for j in after_j]
        if kind == "merge":
            m["gt_merges"] += 1
            m["merge_found"] += int(rows[0] is not None and rows[0]["event"] == "merge")
            m["merge_id_kept"] += int(rows[0] is not None and rows[0]["track_id"] in prev_t)
        else:
            m["gt_splits"] += 1
            m["split_found"] += int(any(r is not None and r["event"] == "split" for r in rows))
            m["split_id_kept"] += int(any(r is not None and r["track_id"] == prev_t[0] for r in rows))

    for f, rows in rows_by_frame.items():
        for r in rows:
            if r["det_index"] is None or r["event"] not in ("merge", "split"):
                continue
            j = next((jj for (ff, jj), rr in row_at.items() if ff == f and rr is r), None)
            if j not in gt_result_dets[f]:
                g = gt_pf[f][j] if j is not None else None
                if isinstance(g, tuple):
                    m["false_events_contact"] += 1   # 接触(境界の一時的な消失)を合体/分裂と誤判定
                else:
                    m["false_events_other"] += 1

    tids = {r["track_id"] for rows in rows_by_frame.values() for r in rows}
    m["tracks"] = len(tids)
    m["new_events"] = sum(1 for rows in rows_by_frame.values() for r in rows if r["event"] == "new")
    return m


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    total = {name: defaultdict(int) for name in ("tracker2", "tracker3")}
    for seed in range(first, first + n_seeds):
        frames, events = simulate(seed)
        line = [f"seed {seed}:"]
        for name in ("tracker2", "tracker3"):
            rows, gt_pf, params = run_tracker(name, frames)
            m = evaluate(rows, gt_pf, events)
            for k, v in m.items():
                total[name][k] += v
            line.append(f"{name} breaks={m['id_breaks']} swaps={m['swaps']} params={params}")
        print("  ".join(line))

    keys = [
        ("links", "同じ気泡の連続観測の数"),
        ("id_breaks", "  IDが途切れた (新規発生/消失)"),
        ("swaps", "  IDが別の気泡に乗り移った"),
        ("untracked", "  トラッキング対象外 (MIN_TRACK_AREA 未満)"),
        ("gt_merges", "正解の合体"),
        ("merge_found", "  合体と判定できた"),
        ("merge_id_kept", "  合体後に構成メンバーのIDが続いた"),
        ("gt_splits", "正解の分裂"),
        ("split_found", "  分裂と判定できた"),
        ("split_id_kept", "  分裂後に親のIDが続いた"),
        ("false_events_contact", "接触を合体/分裂と誤判定"),
        ("false_events_other", "その他の合体/分裂の誤判定"),
        ("new_events", "new イベントの数"),
        ("tracks", "トラック数"),
    ]
    print(f"\n{'':<40}{'tracker2':>10}{'tracker3':>10}")
    for k, label in keys:
        print(f"{label:<40}{total['tracker2'][k]:>10}{total['tracker3'][k]:>10}")


if __name__ == "__main__":
    main()

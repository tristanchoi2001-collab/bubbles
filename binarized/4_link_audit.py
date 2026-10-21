"""
対応付けの抜き取り確認 (link audit) — 実データでの追跡精度を人の目で測る
=====================================================================
3_tracking_qc.py は「疑わしい箇所」を自動で拾うが、正解がないので精度 (何 % 正しくつないだか) は分からない。
ここでは result_tracking.csv から気泡を無作為に選び、「次のフレームでどこにつないだか」を画像で見せて
人が y / n で判定する。判定の数から、大きさ区分ごとの 対応付けの正解率 と 見逃し (つなげたのに切った) の割合を
95% 信頼区間つきで出す。論文の「実データでの追跡精度」の数値になる。

  - 標本: 大きさ区分 (tiny < 50 <= small < 500 <= large, QC と同じ) ごとに N_PER_CLASS 個。
          1本のトラックから 1個だけ選ぶ (同じトラックの判定は似通うので、独立な標本として数えるため)
  - 1件ごとに フレーム t-1, t, t+1, t+2 の同じ場所を並べて表示する
      黄色の円   : 確認する気泡 (t-1, t)
      緑の円     : トラッカーが t+1 (見失い後なら t+2) でつないだ同じIDの気泡
      橙の円     : t+1 で合体した相手 (この気泡が吸収された先)
      水色の円   : t+1 で分裂した子
      赤い ×     : つなげなかった (終わった) とき、直前の速度で予測した t+1 の位置
      灰色の円   : ほかの検出 (どの気泡が検出されているか)
  - キー
      y : トラッカーの答えは正しい (つないだ相手が同じ気泡 / 終わったのが正しい = 画面外へ出た・消えた・合体した)
      n : 間違い (違う気泡につないだ / 合体・分裂の相手が違う)
      m : 見逃し (トラッカーは終わらせたが、同じ気泡が t+1 で検出されている = 灰色の円がある)
      d : 自分が t+1 に写っているのに検出されていない (円がない)。
          つないだ件なら「本物が抜けて隣の気泡を奪った」(トラッカーの誤り)、終わった件なら「検出漏れで終了」(U-Net 側)
      u : 分からない (集計から除く)
      b : 1件戻る   q : 保存して終了 (次に起動すると続きから)
  - 判定は OUT_DIR/decisions_<CSVの指紋>.json に保存する (CSV が変われば別のファイル = 別の標本)
  - 集計は OUT_DIR/link_audit_report.json と画面に出す (割合には Wilson の 95% 区間)
      対応の正解率   = つないだ件のうち y の割合
      見逃し率       = 終わらせた件のうち m / n の割合 (t+1 に検出があるのに切った)
      トラッカーの誤り = 違う気泡につないだ + 検出があるのに切った の割合 (トラッカーの設定で直せる分)
      検出漏れで終了 = 終わった件の d の件数 (トラッカーでは直せない分)
  - 比べ方: 設定を変えた2つの実行 (例 SPACING_GATE_FRAC = 0 と 0.7) の CSV をそれぞれ確認して、正解率と見逃し率を比べる

使い方: 下の設定 (TRACKING_CSV など) を変えて  python 4_link_audit.py
所要時間の目安: 1件 3〜6 秒 -> 300件で 15〜30分
"""

# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
TRACKING_CSV = r"C:\Users\Tristan\Desktop\Tau\raw\output\result_tracking.csv"   # 2_*_track.py の出力 CSV
IMAGE_FOLDER = None      # 表示する画像のフォルダ (CSV の ファイル名 の画像)。None なら CSV と同じフォルダの _cache_processed
                         # (二値化画像。輪郭がはっきり見える)。元画像で見たければ元画像のフォルダを指定
BACKGROUND_PATH = None   # SHOW = "diff" のときの背景画像
SHOW = "image"           # "image" (画像そのまま) / "diff" (背景との差 × DIFF_GAIN。元画像のフォルダを指定したとき用)
DIFF_GAIN = 4.0
N_PER_CLASS = 100        # 大きさ区分ごとの標本数 (tiny / small / large)。足りなければ ある分だけ
INCLUDE_EDGE = False     # True なら画面端に接する気泡も標本にする (画面への出入りの確認用)
SEED = 0                 # 標本の選び方 (同じ CSV・同じ SEED なら同じ標本)
OUT_DIR = None           # None なら CSV と同じフォルダの link_audit/
PANEL = 300              # 1コマの表示サイズ (px)
MAX_GAP = 3              # 見失い後の再接続をこのフレーム数先まで探す (トラッカーの MAX_AGE と同じ)

# ------------------------------------------------------------
import csv
import hashlib
import json
import math
import os
import sys

import numpy as np

try:
    import cv2
except ImportError:      # 集計だけならなくても動く
    cv2 = None

SIZE_CLASSES = (("tiny", 0, 50), ("small", 50, 500), ("large", 500, float("inf")))   # 面積 px (QC と同じ)
CLASS_NAMES = [c for c, _, _ in SIZE_CLASSES]
LABELS = {"y": "correct", "n": "wrong", "m": "missed", "d": "not detected", "u": "unsure"}
DET_EVENTS = ("normal", "new", "merge", "split")          # 検出のある行 (merged_into_* は吸収された記録で検出なし)

YELLOW, GREEN, ORANGE, CYAN, RED, GRAY = (0, 230, 255), (0, 220, 0), (0, 140, 255), (255, 200, 0), (0, 0, 255), (150, 150, 150)


def size_class(area):
    return next(c for c, lo, hi in SIZE_CLASSES if lo <= area < hi)


def eq_radius(area):
    return math.sqrt(max(area, 1.0) / math.pi)


def _num(s, default=float("nan")):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


# ==============================================================
# 1. CSV の読み込みと「トラッカーの答え」
# ==============================================================
def load_csv(path):
    """-> (rows, files)  rows = [{frame, tid, event, parents, area, cx, cy, touch}], files = {フレーム: ファイル名}"""
    rows, files = [], {}
    with open(path, encoding="utf-8-sig", newline="") as fp:
        for r in csv.DictReader(fp):
            f = int(_num(r.get("フレーム"), -1))
            files.setdefault(f, r.get("ファイル名", ""))
            tid = r.get("トラックID", "")
            if tid in ("", None):
                continue
            pid = r.get("親トラックID", "") or ""
            rows.append({"frame": f, "tid": int(_num(tid)), "event": r.get("イベント", ""),
                         "parents": [int(p) for p in pid.split(";") if p.strip().isdigit()],
                         "area": _num(r.get("面積(px)"), 0.0), "cx": _num(r.get("中心X")), "cy": _num(r.get("中心Y")),
                         "touch": r.get("フレーム接触") == "1"})
    return rows, files


class TrackIndex:
    """CSV の行を引きやすくまとめたもの"""

    def __init__(self, rows):
        self.det = {}            # (tid, frame) -> 行 (検出のある行だけ)
        self.by_frame = {}       # frame -> [検出のある行]
        self.merged_into = {}    # (吸収された tid, frame) -> 吸収先の tid
        self.children = {}       # (親 tid, frame) -> [分裂した子の tid]
        for r in rows:
            if r["event"] in DET_EVENTS:
                self.det[(r["tid"], r["frame"])] = r
                self.by_frame.setdefault(r["frame"], []).append(r)
                if r["event"] == "split":
                    for p in r["parents"]:
                        self.children.setdefault((p, r["frame"]), []).append(r["tid"])
            elif r["event"].startswith("merged_into_"):
                host = r["event"][len("merged_into_"):]
                if host.isdigit():
                    self.merged_into[(r["tid"], r["frame"])] = int(host)
        self.last_frame = max((f for _, f in self.det), default=-1)

    def answer(self, tid, t, max_gap=MAX_GAP):
        """フレーム t の気泡 tid について、トラッカーが t+1 以降でどうしたか。
        -> {"kind": "link" / "merged" / "split" / "gap" / "end", "targets": [(tid, frame)], "note": str}"""
        nxt = self.det.get((tid, t + 1))
        kids = self.children.get((tid, t + 1), [])
        if nxt is not None:
            note = "merge host" if nxt["event"] == "merge" else ""
            if kids:
                note = (note + " " if note else "") + f"+ split children {kids}"
            return {"kind": "link", "targets": [(tid, t + 1)], "note": note}
        if (tid, t + 1) in self.merged_into:
            host = self.merged_into[(tid, t + 1)]
            return {"kind": "merged", "targets": [(host, t + 1)] if (host, t + 1) in self.det else [], "note": f"into ID{host}"}
        if kids:
            return {"kind": "split", "targets": [(k, t + 1) for k in kids], "note": ""}
        for k in range(2, max_gap + 2):
            if (tid, t + k) in self.det:
                return {"kind": "gap", "targets": [(tid, t + k)], "note": f"re-linked at t+{k}"}
        return {"kind": "end", "targets": [], "note": ""}


def csv_fingerprint(path):
    h = hashlib.sha1()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:10]


def sample_items(index, n_per_class=N_PER_CLASS, include_edge=INCLUDE_EDGE, seed=SEED):
    """大きさ区分ごとに n_per_class 個。1本のトラックから1個だけ。表示順は区分を混ぜた無作為の順"""
    rng = np.random.default_rng(seed)
    cand = sorted(((r["tid"], f) for (tid, f), r in index.det.items()
                   if f < index.last_frame and (include_edge or not r["touch"])))
    order = rng.permutation(len(cand))
    used, picked = set(), {c: [] for c in CLASS_NAMES}
    for k in order:
        tid, f = cand[k]
        c = size_class(index.det[(tid, f)]["area"])
        if tid in used or len(picked[c]) >= n_per_class:
            continue
        used.add(tid)
        picked[c].append((tid, f))
    items = [{"tid": tid, "frame": f, "cls": c} for c in CLASS_NAMES for tid, f in picked[c]]
    perm = rng.permutation(len(items))
    return [items[k] for k in perm]


def item_key(it):
    return f"{it['tid']}@{it['frame']}"


# ==============================================================
# 2. 集計
# ==============================================================
def wilson(k, n, z=1.96):
    """二項割合の Wilson 95% 区間 (k / n)。n = 0 なら None"""
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(p, 4), round(max(0.0, mid - half), 4), round(min(1.0, mid + half), 4)]


def summarize(items, labels, index):
    """大きさ区分ごとの集計。linked = つないだ件 (link / merged / split / gap)、ended = 終わらせた件"""
    out = {}
    for c in CLASS_NAMES + ["all"]:
        cnt = {"linked": {k: 0 for k in LABELS}, "ended": {k: 0 for k in LABELS}}
        for it in items:
            if c != "all" and it["cls"] != c:
                continue
            lab = labels.get(item_key(it))
            if lab is None:
                continue
            kind = index.answer(it["tid"], it["frame"])["kind"]
            cnt["ended" if kind == "end" else "linked"][lab] += 1
        L, E = cnt["linked"], cnt["ended"]
        n_link = L["y"] + L["n"] + L["m"] + L["d"]       # u は除く。つないだ件の n / m / d はどれも「違う気泡につないだ」
        n_end = E["y"] + E["n"] + E["m"] + E["d"]
        out[c] = {
            "judged": sum(L.values()) + sum(E.values()), "unsure": L["u"] + E["u"],
            "linked": L, "ended": E,
            "link_precision": wilson(L["y"], n_link),               # つないだ件のうち正しい割合
            "wrong_link_own_undetected": L["d"],                     # 本物が t+1 で検出されず、隣の気泡を奪った (トラッカーの誤り)
            "miss_rate_of_ended": wilson(E["m"] + E["n"], n_end),   # 終わらせた件のうち、検出があるのに切った割合
            "ended_by_detection": E["d"],                            # 検出漏れで切れた (U-Net 側。トラッカーでは直せない)
            # トラッカーの誤り = 違う気泡につないだ + 検出があるのに切った (検出漏れで切れた分は含めない)
            "tracker_error_rate": wilson(n_link - L["y"] + E["m"] + E["n"], n_link + n_end),
        }
    return out


def print_summary(s, n_items):
    def pct(w):
        return "   -   " if not w else f"{100 * w[0]:5.1f}% [{100 * w[1]:4.1f}-{100 * w[2]:4.1f}]"
    print(f"\n対応付けの抜き取り確認: 判定 {s['all']['judged']} / {n_items} 件 (分からない {s['all']['unsure']} 件は除く)")
    print(f"  {'区分':<6}{'判定':>5}{'対応の正解率 [95%]':>26}{'見逃し率 (終わらせた件) [95%]':>32}{'トラッカーの誤り [95%]':>28}"
          f"{'隣を奪った':>8}{'検出漏れで終了':>10}")
    for c in CLASS_NAMES + ["all"]:
        v = s[c]
        print(f"  {c:<6}{v['judged']:>5}{pct(v['link_precision']):>26}{pct(v['miss_rate_of_ended']):>32}"
              f"{pct(v['tracker_error_rate']):>28}{v['wrong_link_own_undetected']:>8}{v['ended_by_detection']:>10}")
    print("  対応の正解率 = つないだ件のうち同じ気泡だった割合。見逃し率 = 終わらせた件のうち、t+1 に検出があるのに切った割合。")
    print("  トラッカーの誤り = 違う気泡につないだ + 検出があるのに切った の割合 (トラッカーの設定で直せる分)。")
    print("  隣を奪った = 自分が t+1 で検出されず、隣の気泡につないだ件 (SPACING_GATE_FRAC が減らす種類)。")
    print("  検出漏れで終了 = 自分が t+1 に写っているのに検出されず終わった件 (U-Net 側の問題。トラッカーでは直せない)")


# ==============================================================
# 3. 表示
# ==============================================================
class Frames:
    def __init__(self, files, folder, show=SHOW, background=None, gain=DIFF_GAIN):
        self.files, self.folder, self.show, self.gain = files, folder, show, gain
        self.bg = None
        if show == "diff" and background and cv2 is not None:
            self.bg = cv2.imread(background, cv2.IMREAD_GRAYSCALE)
        self.cache = {}

    def get(self, f):
        if f not in self.cache:
            img = None
            name = self.files.get(f)
            if name and cv2 is not None:
                img = cv2.imread(os.path.join(self.folder, name), cv2.IMREAD_GRAYSCALE)
            if img is not None and self.bg is not None and self.bg.shape == img.shape:
                img = cv2.convertScaleAbs(cv2.absdiff(img, self.bg), alpha=self.gain)
            if len(self.cache) > 16:
                self.cache.pop(next(iter(self.cache)))
            self.cache[f] = img
        return self.cache[f]


def _crop(img, cx, cy, half, panel):
    """(cx, cy) を中心に 2*half 四方を切り出し panel 四方に拡大。画像の外は灰色。-> (BGR画像, 座標変換)"""
    size = 2 * half
    out = np.full((size, size), 60, np.uint8)
    x0, y0 = int(round(cx)) - half, int(round(cy)) - half
    if img is not None:
        h, w = img.shape[:2]
        sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + size), min(h, y0 + size)
        if sx1 > sx0 and sy1 > sy0:
            out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    scale = panel / size
    interp = cv2.INTER_NEAREST if scale >= 2 else cv2.INTER_AREA
    big = cv2.cvtColor(cv2.resize(out, (panel, panel), interpolation=interp), cv2.COLOR_GRAY2BGR)
    return big, (lambda x, y: (int(round((x - x0) * scale)), int(round((y - y0) * scale)))), scale


def render(item, index, frames, labels, pos, total, panel=PANEL):
    """1件の表示画像 (BGR)"""
    tid, t = item["tid"], item["frame"]
    me = index.det[(tid, t)]
    ans = index.answer(tid, t)
    prev = index.det.get((tid, t - 1))
    targets = [index.det[k] for k in ans["targets"] if k in index.det]
    disp = math.hypot(targets[0]["cx"] - me["cx"], targets[0]["cy"] - me["cy"]) if targets else 0.0
    if prev is not None and not targets:
        disp = math.hypot(me["cx"] - prev["cx"], me["cy"] - prev["cy"])
    r_me = eq_radius(me["area"])
    half = int(min(260, max(40, 2.5 * 2 * r_me + 1.5 * disp + 15)))
    cx, cy = me["cx"], me["cy"]
    if targets and ans["kind"] in ("link", "gap"):
        cx, cy = (me["cx"] + targets[0]["cx"]) / 2, (me["cy"] + targets[0]["cy"]) / 2
    pred = None
    if ans["kind"] in ("end", "gap") and prev is not None:
        pred = (2 * me["cx"] - prev["cx"], 2 * me["cy"] - prev["cy"])
    panels = []
    for k, f in enumerate((t - 1, t, t + 1, t + 2)):
        img, xy, sc = _crop(frames.get(f), cx, cy, half, panel)
        for r in index.by_frame.get(f, []):
            if r["tid"] == tid or (r["tid"], f) in ans["targets"]:
                continue
            p = xy(r["cx"], r["cy"])
            if -50 <= p[0] <= panel + 50 and -50 <= p[1] <= panel + 50:
                cv2.circle(img, p, max(2, int(eq_radius(r["area"]) * sc)), GRAY, 1)
        own = index.det.get((tid, f))
        if own is not None:
            col = YELLOW if f <= t else GREEN
            cv2.circle(img, xy(own["cx"], own["cy"]), max(3, int(eq_radius(own["area"]) * sc) + 2), col, 2)
        for (ttid, tf) in ans["targets"]:
            if tf == f and (ttid, tf) in index.det and ttid != tid:
                r = index.det[(ttid, tf)]
                col = ORANGE if ans["kind"] == "merged" else CYAN
                cv2.circle(img, xy(r["cx"], r["cy"]), max(3, int(eq_radius(r["area"]) * sc) + 2), col, 2)
        if pred is not None and f == t + 1:
            p = xy(*pred)
            cv2.drawMarker(img, p, RED, cv2.MARKER_TILTED_CROSS, 18, 2)
        name = {0: "t-1", 1: "t", 2: "t+1", 3: "t+2"}[k]
        cv2.rectangle(img, (0, 0), (150, 24), (0, 0, 0), -1)
        cv2.putText(img, f"{name}  (frame {f})", (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        panels.append(img)
    sep = np.full((panel, 4, 3), 255, np.uint8)
    body = np.hstack([panels[0], sep, panels[1], sep, panels[2], sep, panels[3]])
    head = np.zeros((70, body.shape[1], 3), np.uint8)
    what = {"link": "LINK (green)", "merged": "MERGED into orange", "split": "SPLIT into cyan",
            "gap": "LOST then re-linked (green)", "end": "ENDED (red x = predicted)"}[ans["kind"]]
    lab = labels.get(item_key(item))
    cv2.putText(head, f"{pos + 1}/{total}   {item['cls']}  {int(me['area'])}px   ID{tid}  frame {t}   tracker: {what} "
                f"{ans['note']}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(head, "y=correct  n=wrong  m=missed (detected at t+1 but not linked)  d=not detected  u=unsure  "
                "b=back  q=save+quit", (8, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(head, f"your answer: {LABELS.get(lab, '-')}", (8, 63), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 255, 255) if lab else (120, 120, 120), 1)
    return np.vstack([head, body])


class Audit:
    """判定の状態 (GUI なしでも動かせる)。key(文字) -> 'next' / 'back' / 'quit' / None"""

    def __init__(self, items, labels):
        self.items, self.labels = items, labels
        self.pos = next((k for k, it in enumerate(items) if item_key(it) not in labels), len(items))

    def key(self, ch):
        if ch == "q":
            return "quit"
        if ch == "b":
            self.pos = max(0, self.pos - 1)
            return "back"
        if ch in LABELS and self.pos < len(self.items):
            self.labels[item_key(self.items[self.pos])] = ch
            self.pos += 1
            return "next"
        return None

    @property
    def done(self):
        return self.pos >= len(self.items)


# ==============================================================
def main():
    csv_path = os.path.abspath(TRACKING_CSV)
    base = os.path.dirname(csv_path)
    folder = IMAGE_FOLDER or os.path.join(base, "_cache_processed")
    out = OUT_DIR or os.path.join(base, "link_audit")
    os.makedirs(out, exist_ok=True)
    rows, files = load_csv(csv_path)
    index = TrackIndex(rows)
    items = sample_items(index, N_PER_CLASS, INCLUDE_EDGE, SEED)
    fp_ = csv_fingerprint(csv_path)
    dec_path = os.path.join(out, f"decisions_{fp_}.json")
    labels = {}
    if os.path.exists(dec_path):
        with open(dec_path, encoding="utf-8") as fp:
            labels = json.load(fp).get("labels", {})
    n_cls = {c: sum(1 for it in items if it["cls"] == c) for c in CLASS_NAMES}
    print(f"CSV: {csv_path}\n  標本 {len(items)} 件 ({', '.join(f'{c} {n}' for c, n in n_cls.items())}), "
          f"判定済み {sum(1 for it in items if item_key(it) in labels)} 件 -> {dec_path}")

    def save():
        with open(dec_path, "w", encoding="utf-8") as fp:
            json.dump({"csv": csv_path, "fingerprint": fp_, "seed": SEED, "n_per_class": N_PER_CLASS,
                       "include_edge": INCLUDE_EDGE, "labels": labels}, fp, ensure_ascii=False, indent=1)

    audit = Audit(items, labels)
    if not audit.done:
        if cv2 is None:
            raise SystemExit("OpenCV (cv2) がありません。pip install opencv-python")
        if not os.path.isdir(folder):
            raise SystemExit(f"画像のフォルダがありません: {folder}\n  IMAGE_FOLDER に CSV の ファイル名 の画像があるフォルダを指定してください")
        frames = Frames(files, folder, SHOW, BACKGROUND_PATH, DIFF_GAIN)
        win = "link audit"
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        while not audit.done:
            cv2.imshow(win, render(items[audit.pos], index, frames, labels, audit.pos, len(items)))
            k = -1
            while k < 0:                      # ウィンドウを × で閉じたら「保存して終了」と同じ
                k = cv2.waitKey(50)
                if k < 0 and cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                    k = ord("q")
            k &= 0xFF
            act = audit.key(chr(k).lower() if k < 128 else "")
            if act == "quit":
                break
            if act == "next" and audit.pos % 10 == 0:
                save()
        cv2.destroyAllWindows()
        save()
    s = summarize(items, labels, index)
    print_summary(s, len(items))
    with open(os.path.join(out, "link_audit_report.json"), "w", encoding="utf-8") as fp:
        json.dump({"csv": csv_path, "fingerprint": fp_, "n_items": len(items), "summary": s}, fp,
                  ensure_ascii=False, indent=1)
    print(f"\n集計: {os.path.join(out, 'link_audit_report.json')}")
    if not audit.done:
        print(f"未判定 {len(items) - audit.pos} 件。もう一度実行すると続きから")


if __name__ == "__main__":
    sys.exit(main())

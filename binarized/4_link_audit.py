"""
対応付けの抜き取り確認 (link audit) — 実データでの追跡精度を人の目で測る
=====================================================================
3_tracking_qc.py は「疑わしい箇所」を自動で拾うが、正解がないので精度 (何 % 正しくつないだか) は分からない。
ここでは result_tracking.csv の「気泡 1個 × 1フレーム」(= 次のフレームへの対応付け 1回) を無作為に選び、
トラッカーが次にどうしたかを画像で見せて 人が判定する。判定の数から、大きさ区分ごとの 対応付けの正解率 と
見逃し (つなげたのに切った) の割合を 95% 信頼区間つきで出す。論文の「実データでの追跡精度」の数値になる。

  - 標本: 大きさ区分 (tiny < 50 <= small < 500 <= large, QC と同じ) ごとに、対応付け (トラック × フレーム) を
          N_PER_CLASS 個、一様に無作為に選ぶ (母集団 = 全ての対応付け。画面端・最終フレームは除く)
  - 1件ごとに フレーム t-1, t, t+1, t+2 の同じ場所を並べて表示する (見失い後の再接続が t+3 以降なら 4コマ目はそのフレーム)
      黄色       : 確認する気泡 (t-1, t)
      緑         : トラッカーが同じIDでつないだ気泡 (t+1、見失い後なら再接続したフレーム)
      橙         : 合体の相手 (この気泡が t+1 で吸収された先 / この気泡が t+1 で吸収した気泡を t に表示)
      水色       : t+1 で分裂した子
      赤い ×     : つなげなかった (終わった) とき の t+1 の予測位置 (自分の速度、なければ周りの気泡の動き)
      マゼンタ   : ほかの追跡中の検出 (MIN_TRACK_AREA 以上)
      青 (細線)  : 検出されたが追跡していない小さい検出 (インスタンス画像があるときだけ)
    2_*_track.py を SAVE_INSTANCE_MASKS = True で実行しておくと、円の代わりに検出の輪郭そのものを描く (大きい気泡で見やすい)
  - キー (英字入力の状態で。ハングル入力だとキーが届かない)
      y : トラッカーの答えは正しい (つないだ相手が同じ気泡 / 終わったのが正しい = 画面外へ出た・消えた・合体した)
      n : 間違い (違う気泡につないだ / 合体・分裂の相手が違う / 終わったが t+1 に検出がある)
      m : 見逃し (トラッカーは終わらせた (または t+1 を飛ばした) が、同じ気泡が t+1 で検出されている)
      d : 自分が t+1 に写っているのに検出がない (または小さすぎて追跡対象外)
          つないだ件なら「本物が抜けて隣の気泡を奪った」(トラッカーの誤り)、終わった件なら「検出なしで終了」
      u : 分からない (集計から除く)
      b : 1件戻る   q : 保存して終了 (次に起動すると続きから。全部判定した後の「終わり」の画面でも b で戻って直せる。
          閉じた後に直すなら REVIEW = True で起動)
    「見失い後に再接続」の件は 緑の円が同じ気泡か だけを判定する (y / n。t+1 で検出がなかったのは d でもよい = 正しい)
  - 判定は OUT_DIR/decisions_<CSVの指紋>.json に保存する (CSV が変われば別のファイル = 別の標本)
  - 集計は OUT_DIR/link_audit_report_<CSVの指紋>.json と画面に出す
      対応の正解率       = つないだ件 (再接続を含む) のうち正しい割合 (Wilson の 95% 区間)
      見逃し率           = 終わらせた件のうち、t+1 に検出があるのに切った割合 (Wilson の 95% 区間)
      トラッカーの誤り   = 対応付け 1回あたり、違う気泡につないだ + 検出があるのに切った の割合
                           (つないだ件 / 終わらせた件 の母集団の数で重み付け。正規近似の 95% 区間)
      隣を奪った         = つないだ件で、自分が t+1 で検出されず隣の気泡につないだ数 (SPACING_GATE_FRAC が減らす種類)
      検出なしで終了     = 終わった件で、自分が写っているのに検出がなかった数 (トラッカーでは直せない)
      all の行           = 区分ごとの値を 各区分の母集団の数で重み付けした値 (標本数の配分の影響を受けない)
  - 比べ方: 設定を変えた2つの実行 (例 SPACING_GATE_FRAC = 0 と 0.7) は 2_*_track.py の OUTPUT_FOLDER を別々にし、
            それぞれの CSV で確認して、正解率と見逃し率を比べる

使い方: 下の設定 (TRACKING_CSV など) を変えて  python 4_link_audit.py
所要時間の目安: 1件 3〜6 秒 -> 300件で 15〜30分
"""

# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
TRACKING_CSV = r"C:\Users\Tristan\Desktop\Tau\raw\output\result_tracking.csv"   # 2_*_track.py の出力 CSV
IMAGE_FOLDER = None      # 表示する画像のフォルダ (CSV の ファイル名 の画像)。None なら CSV と同じフォルダの _cache_processed
                         # (二値化画像。輪郭がはっきり見える)。元画像で見たければ元画像のフォルダを指定
INSTANCE_FOLDER = None   # 検出の輪郭 (2_*_track.py の SAVE_INSTANCE_MASKS = True で保存される instances/*.npz)。
                         # None なら CSV と同じフォルダの instances (なければ円で描く)
BACKGROUND_PATH = None   # SHOW = "diff" のときの背景画像
SHOW = "image"           # "image" (画像そのまま) / "diff" (背景との差 × DIFF_GAIN。元画像のフォルダを指定したとき用)
DIFF_GAIN = 4.0
N_PER_CLASS = 100        # 大きさ区分ごとの標本数 (tiny / small / large)。足りなければ ある分だけ
INCLUDE_EDGE = False     # True なら画面端に接する気泡も標本にする (画面への出入りの確認用)
SEED = 0                 # 標本の選び方 (同じ CSV・同じ SEED なら同じ標本)
OUT_DIR = None           # None なら CSV と同じフォルダの link_audit/
PANEL = 300              # 1コマの表示サイズ (px)
FLOW_RADIUS = 150.0      # 自分の速度がないとき、t+1 の位置を「この半径の中の気泡の動きの中央値」で予測する (px)
REVIEW = False           # True なら全部判定済みでも画面を開く (「終わり」の画面から b で戻って答えを直す)

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
KINDS = ("link", "merged", "split", "gap", "end")

YELLOW, GREEN, ORANGE, CYAN, RED = (0, 230, 255), (0, 220, 0), (0, 140, 255), (255, 200, 0), (0, 0, 255)
MAGENTA, BLUE = (255, 0, 255), (255, 80, 0)


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
        self.frames_of = {}      # tid -> 検出のあるフレーム (昇順)
        for r in rows:
            if r["event"] in DET_EVENTS:
                self.det[(r["tid"], r["frame"])] = r
                self.by_frame.setdefault(r["frame"], []).append(r)
                self.frames_of.setdefault(r["tid"], []).append(r["frame"])
                if r["event"] == "split":
                    for p in r["parents"]:
                        self.children.setdefault((p, r["frame"]), []).append(r["tid"])
            elif r["event"].startswith("merged_into_"):
                host = r["event"][len("merged_into_"):]
                if host.isdigit():
                    self.merged_into[(r["tid"], r["frame"])] = int(host)
        for fs in self.frames_of.values():
            fs.sort()
        self.last_frame = max((f for _, f in self.det), default=-1)

    def answer(self, tid, t):
        """フレーム t の気泡 tid について、トラッカーが t+1 以降でどうしたか。
        -> {"kind": link / merged / split / gap / end, "targets": [(tid, frame)],
            "children": [(子の tid, t+1)], "partners": [(吸収した tid, t)], "note": str}
        トラックIDは使い回されないので、t+2 以降に同じIDの検出があれば それが見失い後の再接続"""
        nxt = self.det.get((tid, t + 1))
        kids = [(k, t + 1) for k in self.children.get((tid, t + 1), [])]
        out = {"kind": "end", "targets": [], "children": kids, "partners": [], "note": ""}
        if nxt is not None:
            out.update(kind="link", targets=[(tid, t + 1)])
            if nxt["event"] == "merge":
                out["partners"] = [(p, t) for p in nxt["parents"] if (p, t) in self.det]
                out["note"] = "merge host (absorbed: " + ",".join(f"ID{p}" for p in nxt["parents"]) + ")"
            if kids:
                out["note"] = (out["note"] + " " if out["note"] else "") + "split children: " + ",".join(f"ID{k}" for k, _ in kids)
            return out
        if (tid, t + 1) in self.merged_into:
            host = self.merged_into[(tid, t + 1)]
            out.update(kind="merged", targets=[(host, t + 1)] if (host, t + 1) in self.det else [], note=f"into ID{host}")
            return out
        if kids:
            out.update(kind="split", targets=list(kids), children=[])
            return out
        later = [f for f in self.frames_of.get(tid, []) if f > t + 1]
        if later:
            out.update(kind="gap", targets=[(tid, later[0])], note=f"re-linked at t+{later[0] - t}")
        return out

    def flow(self, t, x, y, radius=FLOW_RADIUS):
        """フレーム t -> t+1 で同じIDのまま続いた気泡の移動量の中央値 (x, y の近くを優先)。なければ None"""
        moves, near = [], []
        for r in self.by_frame.get(t, []):
            n = self.det.get((r["tid"], t + 1))
            if n is None:
                continue
            mv = (n["cx"] - r["cx"], n["cy"] - r["cy"])
            moves.append(mv)
            if math.hypot(r["cx"] - x, r["cy"] - y) <= radius:
                near.append(mv)
        use = near or moves
        if not use:
            return None
        a = np.array(use)
        return float(np.median(a[:, 0])), float(np.median(a[:, 1]))


def csv_fingerprint(path):
    h = hashlib.sha1()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:10]


def population(index, include_edge=INCLUDE_EDGE):
    """標本の母集団: 全ての対応付け (トラック × フレーム)。最終フレーム (次がない) と 画面端 (include_edge でなければ) を除く。
    -> [{"tid", "frame", "cls", "kind"}]"""
    pop = []
    for (tid, f), r in sorted(index.det.items()):
        if f >= index.last_frame or (r["touch"] and not include_edge):
            continue
        pop.append({"tid": tid, "frame": f, "cls": size_class(r["area"]), "kind": index.answer(tid, f)["kind"]})
    return pop


def population_counts(pop):
    """区分ごとの つないだ件 (L) / 終わらせた件 (E) の数"""
    n = {c: {"L": 0, "E": 0} for c in CLASS_NAMES}
    for it in pop:
        n[it["cls"]]["E" if it["kind"] == "end" else "L"] += 1
    return n


def sample_items(pop, n_per_class=N_PER_CLASS, seed=SEED):
    """区分ごとに n_per_class 個を一様に無作為に (重複なし)。表示順は区分を混ぜた無作為の順"""
    rng = np.random.default_rng(seed)
    items = []
    for c in CLASS_NAMES:
        cand = [it for it in pop if it["cls"] == c]
        k = min(n_per_class, len(cand))
        if k:
            items += [cand[i] for i in sorted(rng.choice(len(cand), size=k, replace=False))]
    perm = rng.permutation(len(items))
    return [dict(items[k]) for k in perm]


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


def weighted(parts, z=1.96):
    """parts = [(重み W, 割合の推定 k / n)] の重み付き平均と 正規近似の 95% 区間。
    重みが正なのに n = 0 の部分があれば推定できないので None"""
    tot = sum(w for w, _, _ in parts)
    if tot <= 0:
        return None
    p, var = 0.0, 0.0
    for w, k, n in parts:
        if w <= 0:
            continue
        if n <= 0:
            return None
        q = k / n
        p += w / tot * q
        var += (w / tot) ** 2 * q * (1 - q) / n
    half = z * math.sqrt(var)
    return [round(p, 4), round(max(0.0, p - half), 4), round(min(1.0, p + half), 4)]


def tally(items, labels, cls=None):
    """判定の数え上げ。つないだ件 (link / merged / split / gap) と終わらせた件 (end) に分ける"""
    L = {"ok": 0, "wrong": 0, "stole": 0, "delayed": 0, "n": 0}
    E = {"ok": 0, "missed": 0, "nodet": 0, "n": 0}
    unsure = judged = 0
    for it in items:
        if cls is not None and it["cls"] != cls:
            continue
        lab = labels.get(item_key(it))
        if lab is None:
            continue
        judged += 1
        if lab == "u":
            unsure += 1
            continue
        if it["kind"] == "end":
            E["n"] += 1
            if lab == "y":
                E["ok"] += 1
            elif lab in ("m", "n"):
                E["missed"] += 1      # t+1 に検出があるのに切った (トラッカーの誤り)
            else:
                E["nodet"] += 1       # d: 検出がなくて終わった (トラッカーでは直せない)
        elif it["kind"] == "gap":     # 見失い後の再接続: 再接続の相手が同じ気泡か
            L["n"] += 1
            if lab == "n":
                L["wrong"] += 1
            else:
                L["ok"] += 1
                L["delayed"] += lab == "m"   # t+1 に検出があったのに1フレーム飛ばした
        else:
            L["n"] += 1
            if lab == "y":
                L["ok"] += 1
            else:
                L["wrong"] += 1
                L["stole"] += lab == "d"     # 自分が検出されず、隣の気泡を奪った
    return L, E, judged, unsure


def summarize(items, labels, pop_counts):
    """大きさ区分ごとと all (母集団の数で重み付け)"""
    out, parts_l, parts_e, parts_err = {}, [], [], []
    for c in CLASS_NAMES:
        L, E, judged, unsure = tally(items, labels, c)
        NL, NE = pop_counts[c]["L"], pop_counts[c]["E"]
        out[c] = {
            "population_linked": NL, "population_ended": NE, "judged": judged, "unsure": unsure,
            "linked": L, "ended": E,
            "link_precision": wilson(L["ok"], L["n"]),
            "miss_rate_of_ended": wilson(E["missed"], E["n"]),
            "tracker_error_rate": weighted([(NL, L["wrong"], L["n"]), (NE, E["missed"], E["n"])]),
            "stole_neighbour": L["stole"], "delayed_relink": L["delayed"], "ended_without_detection": E["nodet"],
        }
        parts_l.append((NL, L["ok"], L["n"]))
        parts_e.append((NE, E["missed"], E["n"]))
        parts_err += [(NL, L["wrong"], L["n"]), (NE, E["missed"], E["n"])]
    L, E, judged, unsure = tally(items, labels)
    out["all"] = {
        "population_linked": sum(pop_counts[c]["L"] for c in CLASS_NAMES),
        "population_ended": sum(pop_counts[c]["E"] for c in CLASS_NAMES),
        "judged": judged, "unsure": unsure, "linked": L, "ended": E,
        "link_precision": weighted(parts_l), "miss_rate_of_ended": weighted(parts_e),
        "tracker_error_rate": weighted(parts_err),
        "stole_neighbour": L["stole"], "delayed_relink": L["delayed"], "ended_without_detection": E["nodet"],
    }
    return out


def print_summary(s, n_items):
    def pct(w):
        return "   -   " if not w else f"{100 * w[0]:5.1f}% [{100 * w[1]:4.1f}-{100 * w[2]:4.1f}]"
    print(f"\n対応付けの抜き取り確認: 判定 {s['all']['judged']} / {n_items} 件 (分からない {s['all']['unsure']} 件は除く)")
    print(f"  {'区分':<6}{'判定':>5}{'対応の正解率 [95%]':>26}{'見逃し率 [95%]':>24}{'トラッカーの誤り [95%]':>28}"
          f"{'隣を奪った':>8}{'検出なしで終了':>10}")
    for c in CLASS_NAMES + ["all"]:
        v = s[c]
        print(f"  {c:<6}{v['judged']:>5}{pct(v['link_precision']):>26}{pct(v['miss_rate_of_ended']):>24}"
              f"{pct(v['tracker_error_rate']):>28}{v['stole_neighbour']:>8}{v['ended_without_detection']:>10}")
    print("  対応の正解率 = つないだ件 (再接続を含む) のうち同じ気泡だった割合。")
    print("  見逃し率 = 終わらせた件のうち、t+1 に検出があるのに切った割合。")
    print("  トラッカーの誤り = 対応付け 1回あたり、違う気泡につないだ + 検出があるのに切った の割合 (トラッカーの設定で直せる分)。")
    print("  隣を奪った = 自分が t+1 で検出されず、隣の気泡につないだ件 (SPACING_GATE_FRAC が減らす種類)。")
    print("  検出なしで終了 = 自分が t+1 に写っているのに検出がなく終わった件 (U-Net の見落とし、または MIN_TRACK_AREA 未満)。")
    print("  all = 区分ごとの値を各区分の母集団 (つないだ件 / 終わらせた件 の数) で重み付けした値")


# ==============================================================
# 3. 表示
# ==============================================================
class Frames:
    """画像とインスタンス (検出の輪郭) の読み込み (最近の数フレームだけ保持)"""

    def __init__(self, files, folder, show=SHOW, background=None, gain=DIFF_GAIN, inst_folder=None):
        self.files, self.folder, self.show, self.gain, self.inst_folder = files, folder, show, gain, inst_folder
        self.bg = None
        if show == "diff" and background and cv2 is not None:
            self.bg = cv2.imread(background, cv2.IMREAD_GRAYSCALE)
        self.cache, self.icache = {}, {}

    @staticmethod
    def _put(cache, k, v):
        if len(cache) > 16:
            cache.pop(next(iter(cache)))
        cache[k] = v

    def get(self, f):
        if f not in self.cache:
            img = None
            name = self.files.get(f)
            if name and cv2 is not None:
                img = cv2.imread(os.path.join(self.folder, name), cv2.IMREAD_GRAYSCALE)
            if img is not None and self.bg is not None and self.bg.shape == img.shape:
                img = cv2.convertScaleAbs(cv2.absdiff(img, self.bg), alpha=self.gain)
            self._put(self.cache, f, img)
        return self.cache[f]

    def instances(self, f):
        """-> (ラベル画像, {ラベル: (cx, cy, area)}) / None"""
        if f not in self.icache:
            val = None
            name = self.files.get(f)
            if name and self.inst_folder:
                p = os.path.join(self.inst_folder, os.path.splitext(name)[0] + ".npz")
                if os.path.exists(p):
                    lab = np.load(p)["inst"]
                    n = int(lab.max())
                    ys, xs = np.nonzero(lab)
                    ids = lab[ys, xs]
                    area = np.bincount(ids, minlength=n + 1)
                    sx = np.bincount(ids, xs, minlength=n + 1)
                    sy = np.bincount(ids, ys, minlength=n + 1)
                    stats = {k: (sx[k] / area[k], sy[k] / area[k], int(area[k])) for k in range(1, n + 1) if area[k]}
                    val = (lab, stats)
            self._put(self.icache, f, val)
        return self.icache[f]


def _match_labels(stats, rows):
    """CSV の行 -> インスタンスのラベル (重心が 0.6 px 以内・面積が同じ)"""
    out = {}
    if not stats:
        return out
    keys = list(stats)
    arr = np.array([stats[k] for k in keys], np.float64)
    for r in rows:
        d = np.hypot(arr[:, 0] - r["cx"], arr[:, 1] - r["cy"])
        j = int(np.argmin(d))
        if d[j] <= 0.6 and abs(arr[j, 2] - r["area"]) <= 0.5:
            out[(r["tid"], r["frame"])] = keys[j]
    return out


def _crop(img, cx, cy, half, panel):
    """(cx, cy) を中心に 2*half 四方を切り出し panel 四方に拡大。画像の外は灰色。-> (BGR画像, 座標変換, 倍率, 左上)"""
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
    return big, (lambda x, y: (int(round((x - x0) * scale)), int(round((y - y0) * scale)))), scale, (x0, y0)


def _label_contours(lab, k, x0, y0, size, scale):
    """ラベル k の輪郭 (表示座標)。切り出し範囲の中だけ"""
    h, w = lab.shape
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + size), min(h, y0 + size)
    if sx1 <= sx0 or sy1 <= sy0:
        return []
    m = (lab[sy0:sy1, sx0:sx1] == k).astype(np.uint8)
    if not m.any():
        return []
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return [np.round((c.astype(np.float64) + [sx0 - x0, sy0 - y0]) * scale).astype(np.int32) for c in cs]


def frames_to_show(item, ans):
    t = item["frame"]
    last = t + 2
    if ans["kind"] == "gap" and ans["targets"] and ans["targets"][0][1] > t + 2:
        last = ans["targets"][0][1]
    return [t - 1, t, t + 1, last]


def render(item, index, frames, labels, pos, total, panel=PANEL):
    """1件の表示画像 (BGR)"""
    tid, t = item["tid"], item["frame"]
    me = index.det[(tid, t)]
    ans = index.answer(tid, t)
    prev = index.det.get((tid, t - 1))
    targets = [index.det[k] for k in ans["targets"] if k in index.det]
    pred, pred_src = None, ""
    if ans["kind"] in ("end", "gap"):
        if prev is not None:
            pred, pred_src = (2 * me["cx"] - prev["cx"], 2 * me["cy"] - prev["cy"]), "own velocity"
        else:
            fl = index.flow(t, me["cx"], me["cy"])
            if fl is not None:
                pred, pred_src = (me["cx"] + fl[0], me["cy"] + fl[1]), "neighbours' flow"
    ref = (targets[0]["cx"], targets[0]["cy"]) if targets else pred
    disp = math.hypot(ref[0] - me["cx"], ref[1] - me["cy"]) if ref else 0.0
    half = int(min(260, max(40, 5 * eq_radius(me["area"]) + 1.5 * disp + 15)))
    cx, cy = ((me["cx"] + ref[0]) / 2, (me["cy"] + ref[1]) / 2) if ref else (me["cx"], me["cy"])
    special = {k: ORANGE for k in ans["partners"]}
    special.update({k: CYAN for k in ans["children"]})
    for k in ans["targets"]:
        if k[0] != tid:
            special[k] = ORANGE if ans["kind"] == "merged" else CYAN
    shown = frames_to_show(item, ans)
    panels = []
    for k, f in enumerate(shown):
        img, xy, sc, (x0, y0) = _crop(frames.get(f), cx, cy, half, panel)
        size = 2 * half
        inst = frames.instances(f)
        rows_f = index.by_frame.get(f, [])
        lab_of = _match_labels(inst[1], rows_f) if inst else {}

        def draw(row, col, thick):
            key = (row["tid"], f)
            if inst is not None and key in lab_of:
                cs = _label_contours(inst[0], lab_of[key], x0, y0, size, sc)
                if cs:
                    cv2.drawContours(img, cs, -1, col, thick)
                    return
            p = xy(row["cx"], row["cy"])
            if -60 <= p[0] <= panel + 60 and -60 <= p[1] <= panel + 60:
                cv2.circle(img, p, max(3, int(eq_radius(row["area"]) * sc) + 3), col, thick)

        if inst is not None:                     # 追跡していない (小さい) 検出: 青の細線
            used = set(lab_of.values())
            for lb, (lx, ly, _) in inst[1].items():
                if lb in used or not (x0 <= lx < x0 + size and y0 <= ly < y0 + size):
                    continue
                cs = _label_contours(inst[0], lb, x0, y0, size, sc)
                if cs:
                    cv2.drawContours(img, cs, -1, BLUE, 1)
        for r in rows_f:
            key = (r["tid"], f)
            if r["tid"] == tid or key in special:
                continue
            draw(r, MAGENTA, 1)
        for key, col in special.items():
            if key[1] == f and key in index.det:
                draw(index.det[key], col, 2)
        own = index.det.get((tid, f))
        if own is not None:
            draw(own, YELLOW if f <= t else GREEN, 2)
        if pred is not None and f == t + 1:
            cv2.drawMarker(img, xy(*pred), RED, cv2.MARKER_TILTED_CROSS, 18, 2)
        name = f"t{f - t:+d}" if f != t else "t"
        cv2.rectangle(img, (0, 0), (150, 22), (0, 0, 0), -1)
        cv2.putText(img, f"{name}  (frame {f})", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        panels.append(img)
    sep = np.full((panel, 4, 3), 255, np.uint8)
    body = np.hstack([panels[0], sep, panels[1], sep, panels[2], sep, panels[3]])
    head = np.zeros((92, body.shape[1], 3), np.uint8)
    what = {"link": "LINK (green)", "merged": "MERGED into orange", "split": "SPLIT into cyan",
            "gap": "LOST then re-linked (green): is green the same bubble?",
            "end": "ENDED" + (f" (red x = {pred_src})" if pred is not None else "")}[ans["kind"]]
    lab = labels.get(item_key(item))
    cv2.putText(head, f"{pos + 1}/{total}   {item['cls']}  {int(me['area'])}px   ID{tid}  frame {t}   tracker: {what} "
                f"{ans['note']}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(head, "yellow=this bubble  green=same ID later  orange=merge partner  cyan=split child  "
                "magenta=other detections  blue=untracked small", (8, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
    cv2.putText(head, "y=correct  n=wrong  m=missed (detected at t+1 but not linked)  d=no detection at t+1  u=unsure  "
                "b=back  q=save+quit   (English input mode)", (8, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
    cv2.putText(head, f"your answer: {LABELS.get(lab, '-')}", (8, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 255, 255) if lab else (120, 120, 120), 1)
    return np.vstack([head, body])


def render_done(n_items, n_labeled, width=4 * PANEL + 12):
    img = np.zeros((120, width, 3), np.uint8)
    cv2.putText(img, f"all {n_items} items judged ({n_labeled} answers).", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 255), 2)
    cv2.putText(img, "b = go back and change answers   q = save and finish", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (220, 220, 220), 1)
    return img


class Audit:
    """判定の状態 (GUI なしでも動かせる)。key(文字) -> 'next' / 'back' / 'quit' / None。
    全部判定した後は「終わり」の位置 (pos == 件数) にいて、b で最後の件に戻れる"""

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

    def remaining(self):
        return sum(1 for it in self.items if item_key(it) not in self.labels)


def _disable_ime(win):
    """Windows: このウィンドウの日本語/韓国語入力 (IME) を切る (キーがそのまま届くように)。失敗しても何もしない"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, win)
        if hwnd:
            ctypes.windll.imm32.ImmAssociateContextEx(hwnd, None, 0x0001)   # IACE_CHILDREN
    except Exception:
        pass


# ==============================================================
def main():
    csv_path = os.path.abspath(TRACKING_CSV)
    if not os.path.exists(csv_path):
        raise SystemExit(f"CSV がありません: {csv_path}\n  TRACKING_CSV に 2_*_track.py の result_tracking.csv を指定してください")
    base = os.path.dirname(csv_path)
    folder = IMAGE_FOLDER or os.path.join(base, "_cache_processed")
    inst_folder = INSTANCE_FOLDER or os.path.join(base, "instances")
    out = OUT_DIR or os.path.join(base, "link_audit")
    os.makedirs(out, exist_ok=True)
    rows, files = load_csv(csv_path)
    index = TrackIndex(rows)
    pop = population(index, INCLUDE_EDGE)
    counts = population_counts(pop)
    items = sample_items(pop, N_PER_CLASS, SEED)
    fp_ = csv_fingerprint(csv_path)
    dec_path = os.path.join(out, f"decisions_{fp_}.json")
    labels = {}
    if os.path.exists(dec_path):
        with open(dec_path, encoding="utf-8") as fp:
            labels = json.load(fp).get("labels", {})
    n_cls = {c: sum(1 for it in items if it["cls"] == c) for c in CLASS_NAMES}
    print(f"CSV: {csv_path}\n  標本 {len(items)} 件 ({', '.join(f'{c} {n}' for c, n in n_cls.items())}), "
          f"母集団 (つないだ / 終わらせた) " + ", ".join(f"{c} {counts[c]['L']}/{counts[c]['E']}" for c in CLASS_NAMES)
          + f"\n  判定済み {sum(1 for it in items if item_key(it) in labels)} 件 -> {dec_path}")

    def save():
        with open(dec_path, "w", encoding="utf-8") as fp:
            json.dump({"csv": csv_path, "fingerprint": fp_, "seed": SEED, "n_per_class": N_PER_CLASS,
                       "include_edge": INCLUDE_EDGE, "labels": labels,
                       "items": [dict(it, label=labels.get(item_key(it))) for it in items]},
                      fp, ensure_ascii=False, indent=1)

    audit = Audit(items, labels)
    if audit.remaining() or REVIEW:
        if cv2 is None:
            raise SystemExit("OpenCV (cv2) がありません。pip install opencv-python")
        if not os.path.isdir(folder):
            raise SystemExit(f"画像のフォルダがありません: {folder}\n  IMAGE_FOLDER に CSV の ファイル名 の画像があるフォルダを指定してください")
        if not os.path.isdir(inst_folder):
            print("  (検出の輪郭 instances/*.npz がないので円で描きます。輪郭で見るには 2_*_track.py を SAVE_INSTANCE_MASKS = True で実行)")
        frames = Frames(files, folder, SHOW, BACKGROUND_PATH, DIFF_GAIN, inst_folder if os.path.isdir(inst_folder) else None)
        win = "link audit"
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        try:
            first = True
            while True:
                if audit.done:
                    canvas = render_done(len(items), sum(1 for it in items if item_key(it) in labels))
                else:
                    canvas = render(items[audit.pos], index, frames, labels, audit.pos, len(items))
                cv2.imshow(win, canvas)
                if first:
                    _disable_ime(win)
                    first = False
                k = -1
                while k < 0:                      # ウィンドウを × で閉じたら「保存して終了」と同じ
                    k = cv2.waitKey(50)
                    if k < 0 and cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                        k = ord("q")
                k &= 0xFF
                act = audit.key(chr(k).lower() if k < 128 else "")
                if act in ("next", "back"):
                    save()
                if act == "quit":
                    break
        finally:
            save()
            cv2.destroyAllWindows()
    save()
    s = summarize(items, labels, counts)
    print_summary(s, len(items))
    rep = os.path.join(out, f"link_audit_report_{fp_}.json")
    with open(rep, "w", encoding="utf-8") as fp:
        json.dump({"csv": csv_path, "fingerprint": fp_, "n_items": len(items), "seed": SEED,
                   "population": counts, "summary": s}, fp, ensure_ascii=False, indent=1)
    print(f"\n集計: {rep}")
    left = audit.remaining()
    if left:
        print(f"未判定 {left} 件。もう一度実行すると続きから")


if __name__ == "__main__":
    main()

"""
QC の結果を並べて比較する (docs/PIV_TASK.md 6-4: 実データで PIV なし/あり の比較)
=====================================================================
使い方:
  1) tracker3.py を USE_PIV_PRIOR = False で実行 -> 3_tracking_qc.py を実行 (出力: .../qc_tracking/qc_summary.json)
  2) OUTPUT_FOLDER を変えて USE_PIV_PRIOR = True で実行 -> 3_tracking_qc.py を実行
  3) python qc_compare.py なし=<1つ目の qc_summary.json> あり=<2つ目の qc_summary.json>
     (「名前=パス」の形で何個でも並べられる。名前を省くとフォルダ名)
遅い流速・高速の両方の条件で行うこと。

表の項目:
  基準超え%      : 予測位置から自分の等価直径の半分以上ずれた割合 (tiny / small / large)
  内部新規/フレーム: 画面端でも分裂でもないのに画面の内側で始まったトラック (フレームあたり)
  内部消失/フレーム: 画面端でも合体でもないのに画面の内側で終わったトラック (フレームあたり)
  ID乗り移り      : SWAP_LIKELY の件数
  面積加重の疑わしい割合: SWAP/POS/AREA の観測の面積 ÷ 全観測の面積 (ボイド率・スリップへの影響の目安)
"""
import csv
import json
import os
import sys

CLASSES = ("tiny", "small", "large")


def n_frames_of(summary):
    """qc_summary.json の元 CSV からフレーム数を数える (見つからなければ None)"""
    path = summary.get("source_csv")
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig", newline="") as fp:
        return len({r.get("フレーム") for r in csv.DictReader(fp)})


def load(arg):
    name, _, path = arg.partition("=")
    if not path:
        path, name = name, os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(name)))) or name
    with open(path, encoding="utf-8") as fp:
        s = json.load(fp)
    return name, s


def main(argv):
    if not argv:
        print(__doc__)
        return
    runs = [load(a) for a in argv]
    cols = [n for n, _ in runs]
    w = max(12, max(len(c) for c in cols) + 2)

    def line(label, vals):
        print(f"{label:<28}" + "".join(f"{v:>{w}}" for v in vals))

    print(f"{'':<28}" + "".join(f"{c:>{w}}" for c in cols))
    for c in CLASSES:
        vals = []
        for _, s in runs:
            d = s.get("deviation_from_prediction", {}).get(c)
            vals.append(f"{100 * d['frac_over_threshold']:.1f}" if d else "-")
        line(f"基準超え% {c}", vals)
    for key, label in (("INTERIOR_NEW", "内部新規/フレーム"), ("INTERIOR_LOST", "内部消失/フレーム")):
        for c in CLASSES + ("合計",):
            vals = []
            for _, s in runs:
                cnt = s["counts"][key]
                n = sum(cnt.values()) if c == "合計" else cnt.get(c, 0)
                nf = n_frames_of(s)
                vals.append(f"{n / nf:.2f}" if nf else f"{n}件")
            line(f"{label} {c}", vals)
    for c in CLASSES:
        line(f"ID乗り移り {c}", [str(s["counts"]["SWAP_LIKELY"].get(c, 0)) for _, s in runs])
    line("面積加重の疑わしい割合%", [f"{100 * s['suspicious_ratio_by_area']:.2f}" for _, s in runs])
    line("トラック数", [str(s["n_tracks"]) for _, s in runs])
    line("観測数", [str(s["n_observations"]) for _, s in runs])
    print("\n(フレーム数が分からないときは件数で表示。基準超え% は 3_tracking_qc.py の JUMP_REL / MIN_JUMP_PX の基準)")


if __name__ == "__main__":
    main(sys.argv[1:])

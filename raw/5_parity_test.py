"""
parity 救済のテスト (透明な流路用)
==================================
    python 5_parity_test.py

2_raw_track.py は書き換えずにそのまま読み込み、気泡の分け方 (UNET_INSTANCE_MODE) の最後に parity 救済を足して動かす。
手で書いたファイル (tools/build_raw.py では作らない)。2_raw_track.py と同じフォルダに置く。

なぜ: U-Net は輪郭 (境界確率) はほぼ正確に出すが、二値化画像では気泡の中と液が同じ黒なので、L字の巨大スラグなどで
「壁のどちら側が気体か」を間違える (液の側に内部確率を出し、気体の帯を背景にする)。バックライトの透明な流路では
元画像にも気泡の中の手がかりがない (中と液の差 -1〜+3 階調)。parity 救済は「液から壁を 1枚越えた先は気体」という
位相の規則で、U-Net が取りこぼした大きい気体の領域を足す。
(保存した確率マップでの実験: 637〜641 の L字スラグの縦の帯を戻せた唯一の規則。731〜790 の 60フレームで足した候補は 1個)

やり方 (フレームごと、2_raw_track.py の気泡の分け方の後):
  1. 壁 = 境界確率 > しきい値 を closing で閉じ、壁で区切られた領域に分ける (2_raw_track.py の救済と同じ作り方)。
     PARITY_STEPS の順に試す (しきい値を下げる / closing を増やす = 壁の切れ目を強く閉じる)。
     PARITY_USE_RING なら、二値化画像 B の白い画素 (輪郭の輪) も壁に加えた分け方も試す
  2. 基準にする液の領域 (アンカー) を決める。PARITY_ANCHOR:
       "bubbles" (既定): 検出済みの気泡を一番多く取り囲んでいる領域 (気泡のまわりは液)。
                         PARITY_ANCHOR_MIN_BUBBLES 個未満なら、ほとんどどの気泡にも属さない領域のうち一番大きいもの
       "largest"       : 一番大きい領域 (実験と同じ)。スラグが画面の半分を超えるとスラグが基準になり判定が逆になる
  3. 足す候補 (全部満たすもの):
       - 面積 >= PARITY_MIN_AREA、画素の PARITY_FREE_FRAC 以上がどの気泡にも属さない (U-Net が取りこぼした所だけ)
       - アンカーとの接触 (壁をはさんで向き合う長さ) が PARITY_CONTACT_MIN px 以上、かつ自分の全接触の
         PARITY_CONTACT_FRAC 以上 (= 液に囲まれた領域。スラグの下の液だまりのように別の気体と接する領域は足さない)
       - 面積 <= 画面 × PARITY_MAX_AREA_FRAC (超えたものは足さずに parity_report.json の skipped に書く)
  4. 足す気泡の形: 2_raw_track.py の救済と同じく、境界確率の尾根で壁の画素を両側に分ける (面積の決め方が同じ)

使い方:
  1. 2_raw_track.py の設定 (UNET_CKPT, IMAGE_FOLDER, BACKGROUND_PATH, OUTPUT_FOLDER など) はいつもどおりそちらに書く
  2. このファイルの MODE を選んで実行する。結果は 2_raw_track.py の OUTPUT_FOLDER + OUTPUT_SUFFIX に出る
       "check": 検出だけ (追跡しない。ROI・承認の画面なし)。parity で足した気泡を塗った画像を check/ に、
                足した気泡の一覧を parity_report.json に保存する。まずこれで、足したものが正しいかを目で見る
       "track": 2_raw_track.py の main をそのまま実行する (parity 込み)。CSV・オーバーレイ・qc_report.json に加えて
                parity/ (足したフレームの画像) と parity_report.json。いつもの結果と 3_tracking_qc.py で比べる。
                ROI は元の OUTPUT_FOLDER の roi_saved.json があれば写して同じ ROI を使う。
                比べるときは 2つの実行のゲートを同じにする (ENABLE_BOOTSTRAP = False か、承認画面で同じ値)
  3. 画像の色: 緑 = もともとの気泡、赤 = parity で足した気泡、青 = 基準にした液の領域、紫 = 大きすぎて足さなかった候補
"""
import glob
import importlib.util
import json
import os
import shutil
import time

import cv2
import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed

HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 設定
# ============================================================
MODE = "check"                 # "check" (検出だけ、画像で確認) / "track" (2_raw_track.py の main を parity 込みで実行)
TRACK_SCRIPT = "2_raw_track.py"   # 同じフォルダの検出・追跡ファイル
OUTPUT_SUFFIX = "_parity"      # 2_raw_track.py の OUTPUT_FOLDER にこれを付けたフォルダに出す (元の結果を上書きしない)
CHECK_EVERY = 1                # "check": 何枚おきに見るか (1 = 全部)
PARITY_ENABLE = True           # False なら parity を足さない (このファイル経由でも 2_raw_track.py と同じ結果。比較用)

PARITY_STEPS = None            # 壁の作り方 ((境界確率のしきい値, closing 回数), ...)。None なら ((0.5, 3),) +
                               # 2_raw_track.py の RESCUE_SCHEDULE (実験と同じ)。先の段階で閉じた領域を優先する
PARITY_USE_RING = True         # 二値化画像 B の白い画素も壁にした分け方も試す (実験では 637 / 641 がこれで戻った)
PARITY_MIN_AREA = 500          # 足す領域の最小面積 (px)。小さい気泡は U-Net に任せる
PARITY_FREE_FRAC = 0.95        # 領域の画素のこの割合以上がどの気泡にも属さないときだけ足す
PARITY_CONTACT_FRAC = 0.5      # アンカー (液) との接触が自分の全接触のこの割合以上
PARITY_CONTACT_MIN = 50        # アンカーとの接触の最小長 (px)
PARITY_ANCHOR = "bubbles"      # "bubbles" / "largest" (上の説明)
PARITY_ANCHOR_MIN_BUBBLES = 3  # "bubbles": この数以上の気泡を取り囲む領域がなければ、空いている一番大きい領域
PARITY_MAX_AREA_FRAC = 0.5     # 画面のこの割合より大きい領域は足さない (基準を取り違えたときに画面の大半を気泡にしないため)
SAVE_IMAGES = True             # 足した (または大きすぎて足さなかった) フレームの確認画像を保存
SAVE_IMAGES_MAX = 300          # 保存する確認画像の最大枚数


# ============================================================
# parity 救済
# ============================================================
def wall_regions(prob, edge_thr, close_iters, extra=None):
    """2_raw_track.py の _wall_regions と同じ作り方 (extra = 壁に加える画素 (bool) があればそれも壁)。
    戻り値: (領域ラベル, 領域数, 壁)"""
    edge_raw = prob[2] > edge_thr
    if extra is not None:
        edge_raw = edge_raw | extra
    p = close_iters + 2                                    # closing がフレーム端の壁を削らないよう余白
    ep = np.pad(edge_raw, p, constant_values=True)
    if close_iters > 0:
        ep = ndimage.binary_closing(ep, iterations=close_iters)
    ep = ep[p - 1:-(p - 1), p - 1:-(p - 1)]                # 1px の外枠だけ残す
    ep[0, :] = ep[-1, :] = ep[:, 0] = ep[:, -1] = True
    lab, n = ndimage.label(~ep)
    return lab[1:-1, 1:-1], n, ep[1:-1, 1:-1]


def region_contacts(lab, n):
    """壁の画素を一番近い領域に配り (EDT)、配った領域どうしが接する画素の組を数える。
    戻り値: (配った領域ラベル, {(a, b): 接触の長さ (a < b)}, 領域ごとの全接触)"""
    _, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    exp = lab[iy, ix]
    keys = []
    for a, b in ((exp[:, :-1], exp[:, 1:]), (exp[:-1, :], exp[1:, :])):
        m = (a != b) & (a > 0) & (b > 0)
        keys.append(np.minimum(a[m], b[m]).astype(np.int64) * (n + 1) + np.maximum(a[m], b[m]))
    keys = np.concatenate(keys)
    contact = {}
    tot = np.zeros(n + 1, np.int64)
    for k, cnt in zip(*np.unique(keys, return_counts=True)):
        a, b = int(k // (n + 1)), int(k % (n + 1))
        contact[(a, b)] = int(cnt)
        tot[a] += cnt
        tot[b] += cnt
    return exp, contact, tot


def instance_rings(inst):
    """気泡のすぐ外側 (2〜4 px) の画素と、それぞれ一番近い気泡の番号。戻り値: (画素の (y, x), 気泡の番号)"""
    if not inst.any():
        return (np.zeros(0, int), np.zeros(0, int)), np.zeros(0, np.int64)
    d, (iy, ix) = ndimage.distance_transform_edt(inst == 0, return_indices=True)
    ring = (inst == 0) & (d >= 2) & (d <= 4)
    yy, xx = np.nonzero(ring)
    return (yy, xx), inst[iy[ring], ix[ring]].astype(np.int64)


def bubble_votes(lab, n, exp, inst, rings):
    """領域ごとに「その領域に取り囲まれている検出済みの気泡の数」。気泡ごとに、すぐ外側の画素が一番多く属する領域
    (気泡自身の中の領域は除く) に 1票"""
    votes = np.zeros(n + 1, np.int64)
    (yy, xx), ids = rings
    if ids.size == 0:
        return votes
    m = (inst > 0) & (lab > 0)
    own = {}
    for k, cnt in zip(*np.unique(inst[m].astype(np.int64) * (n + 1) + lab[m], return_counts=True)):
        i, r = divmod(int(k), n + 1)
        if cnt > own.get(i, (0, 0))[1]:
            own[i] = (r, cnt)
    best = {}
    for k, cnt in zip(*np.unique(ids * (n + 1) + exp[yy, xx], return_counts=True)):
        i, r = divmod(int(k), n + 1)
        if r == 0 or r == own.get(i, (-1, 0))[0]:
            continue
        if cnt > best.get(i, (0, 0))[1]:
            best[i] = (r, cnt)
    for r, _ in best.values():
        votes[r] += 1
    return votes


def choose_anchor(lab, n, size, free, votes, mode):
    """基準にする液の領域。戻り値: (領域番号, 決め方の説明)"""
    lf = np.bincount(lab[free], minlength=n + 1)
    mostly_free = lf >= 0.5 * size
    mostly_free[0] = False
    if mode == "largest":
        return int(np.argmax(size[1:]) + 1), "largest"
    if mode != "bubbles":
        raise ValueError(f'PARITY_ANCHOR は "bubbles" / "largest": {mode!r}')
    v = np.where(mostly_free, votes, 0)
    if v.max() >= PARITY_ANCHOR_MIN_BUBBLES:
        best = np.lexsort((size, v))[-1]                   # 票が同じなら大きい方
        return int(best), f"bubbles({int(v[best])})"
    cand = np.where(mostly_free, size, 0)
    if cand.max() > 0:
        return int(np.argmax(cand)), "largest_free"
    return int(np.argmax(size[1:]) + 1), "largest"


def parity_rescue(prob, inst, ring=None, steps=None):
    """確率マップ (3,H,W) と 気泡ラベルマップ -> (parity で領域を足したラベルマップ, 記録)。
    もとの気泡の画素とラベル番号は変えない (足した気泡は inst.max() + 1 から)。
    ring = 壁に加える画素 (二値化画像 B > 0)。PARITY_USE_RING のときだけ使う。
    1) すべての壁の作り方で候補を集める (先の作り方で取った候補と半分以上重なる領域は取らない)
    2) 後の候補 (強く閉じた / 輪も壁にした) が前の候補の半分以上を含むなら、前の候補はその一部とみなして捨てる
       (L字が 下の端の小さい領域 + 残り の 2個にならないように)
    3) 残った候補を見つけた順に、境界確率の尾根で壁の画素を分けて気泡にする"""
    H, W = inst.shape
    steps = tuple(steps) if steps is not None else ((0.5, 3),)
    free0 = inst == 0
    taken = np.zeros((H, W), bool)
    rings = instance_rings(inst) if PARITY_ANCHOR == "bubbles" else None
    rep = {"added": [], "skipped": [], "fragments": [], "anchor": None}
    variants = [("pedge", None)]
    if PARITY_USE_RING and ring is not None and ring.shape == (H, W):
        variants.append(("pedge+ring", ring.astype(bool)))
    anchor_mask = None
    cands = []                                             # (記録, 領域ラベル, 領域番号, 領域の画素)
    for walls, extra in variants:
        for thr, it in steps:
            lab, n, _ = wall_regions(prob, thr, it, extra)
            if n < 2:
                continue
            size = np.bincount(lab.ravel(), minlength=n + 1)
            size[0] = 0
            lf = np.bincount(lab[free0], minlength=n + 1)
            pre = (size >= PARITY_MIN_AREA) & (lf >= PARITY_FREE_FRAC * size)
            pre[0] = False
            npre = int(pre.sum())
            if npre == 0 or (npre == 1 and pre[int(np.argmax(size))]):
                continue                                   # 足せる大きさの空いた領域が 一番大きい領域 (液) だけ -> 候補なし
            exp, contact, tot = region_contacts(lab, n)
            votes = bubble_votes(lab, n, exp, inst, rings) if rings is not None else None
            anchor, how = choose_anchor(lab, n, size, free0, votes, PARITY_ANCHOR)
            if anchor_mask is None:
                anchor_mask = lab == anchor
                rep["anchor"] = {"how": how, "area": int(size[anchor]), "step": [thr, it], "walls": walls}
            for r in np.nonzero(pre)[0]:
                if r == anchor:
                    continue
                ca = contact.get((min(anchor, r), max(anchor, r)), 0)
                if ca < PARITY_CONTACT_MIN or ca < PARITY_CONTACT_FRAC * tot[r]:
                    continue
                m = lab == r
                if (taken & m).sum() > 0.5 * size[r]:
                    continue
                taken |= m
                cy, cx = ndimage.center_of_mass(m)
                ys, xs = np.nonzero(m)
                info = {"step": [thr, it], "walls": walls, "region_area": int(size[r]), "cx": round(float(cx)),
                        "cy": round(float(cy)), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                        "contact_anchor": int(ca), "contact_total": int(tot[r]),
                        "mean_p_in": round(float(prob[1][m].mean()), 3), "anchor": how,
                        "touches_frame": bool(ys.min() == 0 or xs.min() == 0 or ys.max() == H - 1 or xs.max() == W - 1)}
                if size[r] > PARITY_MAX_AREA_FRAC * H * W:
                    info["why"] = f"面積が画面の {size[r] / (H * W):.0%} (> PARITY_MAX_AREA_FRAC)"
                    rep["skipped"].append(info)
                    continue
                cands.append((info, lab, int(r), m))
    keep = []
    for i, (info, lab, r, m) in enumerate(cands):
        if any((m & cands[j][3]).sum() * 2 >= info["region_area"] for j in range(i + 1, len(cands))):
            rep["fragments"].append(info)                  # 後で見つけた大きい候補の一部
            continue
        keep.append((info, lab, r))
    out = inst.copy()
    k = int(inst.max())
    free = free0.copy()
    for info, lab, r in keep:
        ws = watershed(prob[2], markers=np.where(free, lab, 0).astype(np.int32), mask=free)
        mm = ws == r
        if int(mm.sum()) < PARITY_MIN_AREA:
            continue
        k += 1
        out[mm] = k
        free &= ~mm
        info.update(label=k, area=int(mm.sum()))
        rep["added"].append(info)
    rep["anchor_mask"] = anchor_mask
    return out, rep


def draw_parity(base_gray, inst, out, rep):
    """確認画像: 緑 = もともとの気泡、赤 = 足した気泡、青 = 基準の液の領域、紫 = 大きすぎて足さなかった候補"""
    vis = cv2.cvtColor(base_gray, cv2.COLOR_GRAY2BGR).astype(np.float32)
    am = rep.get("anchor_mask")
    if am is not None:
        vis[am] = vis[am] * 0.75 + np.array((255, 120, 0), np.float32) * 0.25
    added = np.isin(out, [a["label"] for a in rep["added"]]) if rep["added"] else np.zeros(out.shape, bool)
    vis[added] = vis[added] * 0.5 + np.array((0, 0, 255), np.float32) * 0.5
    vis = vis.astype(np.uint8)
    cs, _ = cv2.findContours((inst > 0).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(vis, cs, -1, (0, 200, 0), 1)
    for a in rep["added"]:
        cs, _ = cv2.findContours((out == a["label"]).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(vis, cs, -1, (0, 0, 255), 2)
    for s in rep["skipped"]:
        x0, y0, x1, y1 = s["bbox"]
        cv2.rectangle(vis, (x0, y0), (x1, y1), (255, 0, 255), 2)
    txt = f"parity +{len(rep['added'])}" + (f"  skip {len(rep['skipped'])}" if rep["skipped"] else "") + \
          (f"  anchor {rep['anchor']['how']}" if rep.get("anchor") else "")
    cv2.putText(vis, txt, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(vis, txt, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return vis


# ============================================================
# 実行
# ============================================================
def load_track(path=None):
    """2_raw_track.py をモジュールとして読み込む (そのファイルの設定もそのまま使う)"""
    path = path or os.path.join(HERE, TRACK_SCRIPT)
    spec = importlib.util.spec_from_file_location("raw_track_for_parity", path)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def steps_for(M):
    return PARITY_STEPS if PARITY_STEPS is not None else ((0.5, 3),) + tuple(M.RESCUE_SCHEDULE)


def list_images(M):
    """2_raw_track.py の検出と同じ画像の並び"""
    files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff'):
        files.extend(glob.glob(os.path.join(M.IMAGE_FOLDER, ext)))
    files = sorted(set(files))
    return [p for p in files if os.path.normcase(os.path.abspath(p)) != os.path.normcase(os.path.abspath(M.BACKGROUND_PATH))]


def b_plane(M, detector, raw, bg):
    """U-Net が見た二値化画像 B (入力に B がない ckpt なら作る)"""
    B = (getattr(detector, "last_planes", None) or {}).get("B")
    return B if B is not None else M.make_planes(raw, bg, detector.preproc)["B"]


def strip(rep):
    return {k: v for k, v in rep.items() if k != "anchor_mask"}


def summarize(frames, out_dir, t_parity):
    added = [a for f in frames for a in f["added"]]
    skipped = [s for f in frames for s in f["skipped"]]
    summary = {"frames": len(frames), "frames_with_added": sum(1 for f in frames if f["added"]),
               "added": len(added), "added_area_total": int(sum(a["area"] for a in added)),
               "added_area_max": int(max((a["area"] for a in added), default=0)),
               "added_touching_frame": sum(1 for a in added if a["touches_frame"]),
               "skipped_too_large": len(skipped), "parity_sec_per_frame": round(t_parity / max(len(frames), 1), 3)}
    settings = {k: globals()[k] for k in ("PARITY_STEPS", "PARITY_USE_RING", "PARITY_MIN_AREA", "PARITY_FREE_FRAC",
                                          "PARITY_CONTACT_FRAC", "PARITY_CONTACT_MIN", "PARITY_ANCHOR",
                                          "PARITY_ANCHOR_MIN_BUBBLES", "PARITY_MAX_AREA_FRAC", "PARITY_ENABLE")}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "parity_report.json"), "w", encoding="utf-8") as fp:
        json.dump({"summary": summary, "settings": settings, "frames": frames}, fp, ensure_ascii=False, indent=1)
    print(f"\n[parity] {summary['frames']}フレーム中 {summary['frames_with_added']}フレームで {summary['added']}個 足した "
          f"(合計 {summary['added_area_total']} px, 最大 {summary['added_area_max']} px, 画面端に接する {summary['added_touching_frame']}個)"
          + (f", 大きすぎて足さなかった候補 {summary['skipped_too_large']}個" if skipped else "")
          + f"  parity の時間 {summary['parity_sec_per_frame']} s/フレーム")
    print(f"  一覧: {os.path.join(out_dir, 'parity_report.json')}")
    return summary


def run_check(M, out_dir):
    """検出だけ: 各フレームで 2_raw_track.py の分け方 -> parity。足したフレームの画像を check/ に保存"""
    detector = M.RawDetector(M.UNET_CKPT, M.TRAIN_IMAGE_HW)
    bg = cv2.imread(M.BACKGROUND_PATH)
    if bg is None:
        raise FileNotFoundError(f"背景画像が見つかりません: {M.BACKGROUND_PATH}")
    files = list_images(M)[::max(1, int(CHECK_EVERY))]
    if not files:
        raise FileNotFoundError(f"'{M.IMAGE_FOLDER}' フォルダに画像がありません。")
    img_dir = os.path.join(out_dir, "check")
    os.makedirs(img_dir, exist_ok=True)
    steps = steps_for(M)
    frames, n_img, t_par = [], 0, 0.0
    print(f"[parity check] {len(files)}枚 (CHECK_EVERY = {CHECK_EVERY}), 分け方 {M.UNET_INSTANCE_MODE!r}, 出力先 {out_dir}")
    for p in files:
        raw = cv2.imread(p)
        if raw is None:
            print(f"  -> {os.path.basename(p)}: 読み込み失敗、スキップ")
            continue
        prob = detector.prob_raw(raw, bg)
        inst = M.unet_instances(prob)
        B = b_plane(M, detector, raw, bg)
        t0 = time.time()
        out, rep = parity_rescue(prob, inst, B > 0, steps) if PARITY_ENABLE else (inst, {"added": [], "skipped": [], "anchor": None})
        t_par += time.time() - t0
        name = os.path.basename(p)
        frames.append({"file": name, **strip(rep)})
        if rep["added"] or rep["skipped"]:
            print(f"  [{name}] parity +{len(rep['added'])} " + " ".join(f"{a['area']}px@({a['cx']},{a['cy']})" for a in rep["added"])
                  + (f"  (大きすぎて足さない {len(rep['skipped'])}個)" if rep["skipped"] else ""))
            if SAVE_IMAGES and n_img < SAVE_IMAGES_MAX:
                cv2.imwrite(os.path.join(img_dir, os.path.splitext(name)[0] + ".png"), draw_parity(B, inst, out, rep))
                n_img += 1
    return summarize(frames, out_dir, t_par)


def run_track(M, out_dir):
    """2_raw_track.py の main を、気泡の分け方の後に parity を足して実行する"""
    orig_out = M.OUTPUT_FOLDER
    M.OUTPUT_FOLDER = out_dir
    os.makedirs(out_dir, exist_ok=True)
    roi_src = os.path.join(orig_out, "roi_saved.json")
    if M.ROI_SAVE_PATH is None and os.path.exists(roi_src) and not os.path.exists(os.path.join(out_dir, "roi_saved.json")):
        shutil.copy(roi_src, os.path.join(out_dir, "roi_saved.json"))     # 元の実行と同じ ROI
        print(f"  ROI は元の結果の {roi_src} を使います")
    steps = steps_for(M)
    cur = {"name": None, "B": None, "n": 0}
    frames, t_par = [], [0.0]
    img_dir = os.path.join(out_dir, "parity")
    os.makedirs(img_dir, exist_ok=True)

    orig_pre, orig_prob, orig_inst = M.preprocess_image, M.RawDetector.prob_raw, M.unet_instances

    def preprocess_image(img_path, *a, **kw):
        cur["name"] = kw.get("filename") or os.path.basename(img_path)
        return orig_pre(img_path, *a, **kw)

    def prob_raw(self, raw_bgr, bg_bgr, *a, **kw):
        p = orig_prob(self, raw_bgr, bg_bgr, *a, **kw)
        cur["B"] = b_plane(M, self, raw_bgr, bg_bgr)
        return p

    def unet_instances(prob, mode=None, stats=None):
        inst = orig_inst(prob, mode, stats)
        if mode is not None or not PARITY_ENABLE or prob.shape[1] < 16:   # 比べる分け方 (COMPARE_INSTANCE_MODES)・綴りの確認は そのまま
            return inst
        B = cur["B"] if cur["B"] is not None and cur["B"].shape == inst.shape else None
        t0 = time.time()
        out, rep = parity_rescue(prob, inst, None if B is None else B > 0, steps)
        t_par[0] += time.time() - t0
        cur["n"] += 1
        name = cur["name"] or f"frame{cur['n']:05d}"
        frames.append({"file": name, **strip(rep)})
        if rep["added"] or rep["skipped"]:
            print(f"    parity +{len(rep['added'])} " + " ".join(f"{a['area']}px@({a['cx']},{a['cy']})" for a in rep["added"])
                  + (f"  (大きすぎて足さない {len(rep['skipped'])}個)" if rep["skipped"] else ""))
            if SAVE_IMAGES and sum(1 for f in frames if f["added"] or f["skipped"]) <= SAVE_IMAGES_MAX and B is not None:
                cv2.imwrite(os.path.join(img_dir, os.path.splitext(name)[0] + ".png"), draw_parity(B, inst, out, rep))
        return out

    M.preprocess_image, M.RawDetector.prob_raw, M.unet_instances = preprocess_image, prob_raw, unet_instances
    try:
        print(f"[parity track] {TRACK_SCRIPT} の main を parity 込みで実行します (PARITY_ENABLE = {PARITY_ENABLE}), 出力先 {out_dir}")
        M.main()
    finally:
        M.preprocess_image, M.RawDetector.prob_raw, M.unet_instances = orig_pre, orig_prob, orig_inst
        M.OUTPUT_FOLDER = orig_out
    return summarize(frames, out_dir, t_par[0])


def main():
    if MODE not in ("check", "track"):
        raise ValueError(f'MODE は "check" / "track": {MODE!r}')
    if PARITY_ANCHOR not in ("bubbles", "largest"):
        raise ValueError(f'PARITY_ANCHOR は "bubbles" / "largest": {PARITY_ANCHOR!r}')
    M = load_track()
    out_dir = M.OUTPUT_FOLDER.rstrip("\\/") + OUTPUT_SUFFIX
    print(f"実行中のファイル: {os.path.abspath(__file__)}  (検出・追跡: {TRACK_SCRIPT}, MODE = {MODE!r})")
    return run_check(M, out_dir) if MODE == "check" else run_track(M, out_dir)


if __name__ == "__main__":
    main()

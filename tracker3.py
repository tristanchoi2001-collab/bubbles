"""
Microgap Bubble Tracking - U-Net版 (tracker3)
=====================================================================
microgaptracker3.py の検出部(YOLO)を、1_unet_train.py で学習した U-Net に置き換えたもの。
前処理・ROI・ブートストラップ・CSV/オーバーレイ出力は microgaptracker3.py の構成を引き継ぐ。

処理の流れ:
  1) 前処理(2値化) : 背景差分 -> Median -> Noise Cut -> 明度増幅   ※学習画像と同じ処理
  2) 検出(U-Net)   : 画素ごとに 背景/気泡内部/気泡境界 の確率を出力
                     -> 境界を壁として領域分割 -> 壁で囲まれた領域 = 気泡1個 (画素マスク)
  3) トラッキング   : LeadingEdgeLapTracker
       同一気泡 : 2次元速度で予測した位置からのずれ・面積変化・予測マスクとの重なり・形状 のコストで
                  ハンガリアン法により1対1対応
       合体     : 対応の取れなかったトラックの予測マスクが検出と重なり、
                  「面積(A) + 面積(B) ≈ 面積(X)」(面積保存) が確認できた場合
       分裂     : 対応の取れなかった検出が親トラックの予測マスクと重なり、
                  「面積(X) ≈ 面積(A') + 面積(B')」(面積保存) が確認できた場合
       接触     : 合体の直後 (TRANSIENT_MERGE_FRAMES 以内) に元の気泡に分かれ直したら、
                  2値化で境界が一時的に消えただけとみなし、元のIDに戻す (合体/分裂として記録しない)
  4) 後処理       : 速度(EMA) -> CSV -> オーバーレイ画像 -> QCレポート

tracker2.py からの変更点 (QC で多かった 新規発生/消失・ID乗り移り・合体分裂の誤判定への対策):
  - 予測を「先端部の y 速度だけ」から「x, y の2次元速度」に変更
      斜めに動く気泡 (1フレームで x にも 15〜40px) が MAX_CENTER_X_JUMP で毎回切れていた
  - 見失った後に復帰したときの速度更新で、移動量をフレーム数で割っていなかったバグを修正
      (2フレームぶりなら速度が約2倍になり、次のフレームでまた見失っていた)
  - ゲートを px の固定値から「予測ずれの許容 POS_GATE + 等価直径に比例する分」に変更し、
    速度がまだ分からないトラック (新規・分裂直後) は「静止」と「周りの流れ」の2仮説 +
    物理的に動ける最大距離 MAX_SPEED で探索
      tracker2 では速い気泡 (30〜60px/frame) が新規トラックになると、初速度が周りの静止気泡から
      0 と推定されてゲートを外れ、毎フレーム新しいIDになっていた (QC の新規発生の約半数)
  - SPACING_GATE_FRAC (隣の気泡との距離によるゲート) を廃止
      移動量が気泡間隔より大きいと正しい対応まで捨てていた。乗り移りはコスト(面積・形状・予測ずれ)と
      ハンガリアン法の全体最適で防ぐ
  - 予測マスクとの IoU (重心合わせなし = 位置と形を同時に見る) をコストに追加し、
    IoU が OVERLAP_ACCEPT_IOU 以上なら位置ゲートの外でも対応候補にする (大きく変形する大気泡用)
  - 画面端で切れた気泡は、重心ではなく切れていない側の端で位置を比べる
  - 合体/分裂の確定条件を Union IoU から面積保存に変更
      合体した気泡は丸くなるので「A∪B の形 ≈ X の形」は成り立たない
      (同じ大きさの円2つが合体して円になると Union IoU は約0.52 で、しきい値 0.6 に届かない)
      逆に、接している2つの気泡の境界が一時的に消えただけのときに合体と判定されていた
  - 合体で吸収されたトラックを TRANSIENT_MERGE_FRAMES の間保持し、分かれ直したら元のIDに戻す
  - MIN_TRACK_AREA 未満の検出 (数px のノイズ) はトラッキングしない (面積・個数の集計には含む)
  - ブートストラップで 最大移動量 MAX_SPEED / 予測ずれ POS_GATE / 面積比 を自動算出

tracker2.py での変更点 (microgaptracker3.py から。一部は上記の tracker3 の変更で置き換え):
  - ultralytics(YOLO) 不要。torch + segmentation_models_pytorch を使用
  - 形状比較(IoU)をポリゴンではなく画素マスクで計算
  - 合体/分裂の候補探索を「先端部ゲート」から「マスクの重なり」に変更
      前後に並んだ気泡の合体/分裂では、両者の先端部が気泡長だけ離れているため先端部ゲートを通らない。
      旧方式では、合体は後方気泡が見失われてゲートが広がった後に遅れて検出され
      (気泡長が約160pxを超えると検出不可)、前後方向の分裂は「new」と判定されていた
  - 分裂にも合体と同じ Union IoU 検証を追加 (近くに新しく現れた気泡を分裂と誤判定しない)
  - 合体メンバーは直前フレームで観測されたトラックに限定 (同じ気泡の重複トラックを合体と誤判定しない)
  - 3個以上の同時合体・同時分裂に対応
  - 生まれたばかりのトラック(速度未知)は初回のみ先端部ゲートを NEW_TRACK_GATE_SCALE 倍に拡大
  - ブートストラップの位置ゲートに下限 BOOTSTRAP_MIN_JUMP を設定
  - トラッキングCSVの末尾に 周長(px)・フレーム接触 の列を追加
"""

# ------------------------------------------------------------
# パスの設定 (自分の環境に合わせて変更すること)
# ------------------------------------------------------------
UNET_CKPT = r"C:\Users\inoue-2024-01\Desktop\U-net\best.pt"   # U-Netの学習結果 (best.pt)
IMAGE_FOLDER = r"C:\Users\inoue-2024-01\Desktop\U-net\test w0.7 a0.5"                          # 分析する画像があるフォルダ
BACKGROUND_PATH = r"C:\Users\inoue-2024-01\Desktop\U-net\bg2real\image0000000.jpg"  # 背景画像のパス
OUTPUT_FOLDER = r"C:\Users\inoue-2024-01\Desktop\U-net\output"                   # 結果を保存するフォルダ

# 前処理(背景差分 + Noise Cut + Median + 明度増幅)を有効にするか。
# U-Netは2値化済み画像で学習しているので、基本は True のまま。
ENABLE_PREPROCESSING = True

# 前処理パラメータ (Noise Cut, Brightness, Median)。学習画像を作ったときと同じ値にすること。
#   None : 最初のフレームでスライダー調整 (初期値は PREPROC_DEFAULT)
#   固定 : 例) PREPROC_FIXED = (40, 3, 1)  -> スライダーを出さずにこの値を使う (再現性のため推奨)
PREPROC_FIXED = None
PREPROC_DEFAULT = (30, 3, 0)

# 入力チェック: 前処理後の画像は学習画像と同じく「ほぼ黒い背景 + 白い輪郭」でなければならない
MIN_BLACK_FRACTION = 0.7   # 黒画素(<15)の割合がこれ未満なら警告 (学習画像は約0.94)
SAVE_DEBUG_FIRST_FRAME = True   # 最初のフレームの U-Net 入力画像と確率マップを OUTPUT_FOLDER/debug に保存

# ------------------------------------------------------------
# U-Net 検出パラメータ (1_unet_train.py の [3] と同じ値にすること)
# ------------------------------------------------------------
UNET_MIN_AREA = 4       # これより小さい気泡は捨てる (px)
IGNORE_PARTICLE_AREA = 4  # 面積がこの値 (px) 以下の検出は粒子 (ゴミ・ノイズ) として無視する。
                          # 面積・個数の集計 (ROI)、トラッキング、PIV、オーバーレイ、CSV のすべてから除く。0 で無効。
                          # SAVE_INSTANCE_MASKS の npz には U-Net の結果をそのまま (除く前) 保存する
UNET_BAND = 25          # 壁近傍の判定帯の幅 (px)
UNET_EDGE_THR = 0.5     # 境界確率のしきい値
UNET_CLOSE = 2          # 境界の途切れを塞ぐ closing 回数
UNET_TINY_MAX = 300     # 境界の塊として拾う小気泡の最大面積 (px)
UNET_INSTANCE_MODE = "wall"  # 確率マップ -> 気泡の分け方
                             #   "wall": 境界 (> UNET_EDGE_THR) を壁にして閉じた領域を気泡とする (従来)。
                             #           壁が途切れると気泡の内部が背景とつながり、気泡ごと消えることがある
                             #   "seed": 内部確率の「芯」(内部 > UNET_SEED_THR かつ 境界 <= UNET_EDGE_THR) を種にした watershed。
                             #           芯は壁の途切れに関係なく決まるので、輪郭が途切れても気泡が背景に漏れない。
                             #           U-Net がそもそも反応していない気泡は どちらの方式でも拾えない
UNET_SEED_THR = 0.5          # "seed" の芯の内部確率のしきい値
TRAIN_IMAGE_HW = None   # 学習画像のサイズ (H, W)。best.pt に記録があればそちらを使う。
                        # 古い best.pt で、撮影画像と学習画像のサイズが違う場合のみ指定。例: (1080, 416)
SAVE_INSTANCE_MASKS = False  # True ならフレームごとの気泡ラベルマップを OUTPUT_FOLDER/instances/*.npz に保存
SAVE_PROB_MAPS = False       # True ならフレームごとの U-Net 確率マップを OUTPUT_FOLDER/prob/*.npz に保存
                             # (キー: p_in = 内部確率, p_edge = 境界確率 (どちらも 0〜255 の uint8), u_input = U-Net 入力画像)。
                             # 検出漏れが U-Net 自体か後処理 (extract_instances) かを調べる用。1 フレーム数百 KB

# ------------------------------------------------------------
# ROI (関心領域) 設定
#   - 検出とトラッキングは画面全体で実行
#   - 「合計面積」は各気泡マスクがROIと重なる部分のピクセルのみ合算
#   - 「個数」はROIに少しでもかかった気泡を1個としてカウント
# ------------------------------------------------------------
ENABLE_ROI = True    # Falseなら画面全体基準
ROI_RECT = None      # Noneなら最初のフレームでマウスドラッグで選択。
                     # 再現性が必要なら (x, y, w, h) タプルで固定。例: ROI_RECT = (100, 200, 400, 600)
ROI_SAVE_PATH = None # 選択したROIを保存/再利用するファイルパス。NoneならOUTPUT_FOLDER/roi_saved.jsonを使用

# ------------------------------------------------------------
# トラッキングパラメータ（気泡のスケール・撮影fpsに合わせて調整すること）
# ------------------------------------------------------------
LEADING_EDGE_PERCENTILE = 5.0

# --- 1対1対応のゲート (ブートストラップで自動算出できる) ---
MAX_SPEED = 70.0             # 1フレームで気泡が動ける最大距離 (px)。速度がまだ分からないトラック(新規・分裂直後)の探索半径
POS_GATE = 15.0              # 速度が分かっているトラック: 予測位置からのずれの許容 (px)
POS_GATE_SIZE_FRAC = 0.25    # 予測ずれの許容に「等価直径 × この値」を足す (大きい気泡ほど変形で位置が揺れる)
AREA_RATIO_GATE = 1.8        # 1対1対応で許す面積比。これを超える変化は合体/分裂として扱う
                             # (画面端で切れている気泡は この2倍まで許す。小さい側が画面端で切れているとき
                             #  = 画面に入ってくる途中/出ていく途中 は、見えている面積がいくらでも変わるので面積ゲートなし)
AREA_RELAX_RATIO = 4.0       # 位置がぴったり合うときに 1対1対応で許す面積比 (AREA_RATIO_GATE より大きくする)。
                             # U-Net が同じ気泡を内側/外側の輪郭で切り替えると、位置はそのままで面積だけが大きく変わり、
                             # 「消失 + 同じ場所に新規」になる。合体/分裂の判定の後に残った「速度既知のトラック」と「検出」で、
                             # 予測位置のずれが AREA_RELAX_POS 以内・互いにほかの候補がない・合体/分裂の相手になりうる
                             # 別の気泡が重なっていない組だけをつなぐ (速度は更新しない)。画面端で切れている気泡は対象外。
                             # AREA_RATIO_GATE 以下 (0 など) で無効
AREA_RELAX_POS = 6.0         # 上の「ぴったり」の位置ずれの許容 (px)。+ 小さい側の等価直径 × POS_GATE_SIZE_FRAC。
                             # 見失っている間は COAST_GATE_GROWTH で広げる
OVERLAP_ACCEPT_IOU = 0.4     # 予測マスクとの IoU がこれ以上なら、位置ゲートの外でも対応候補にする (大きく変形する大気泡用)
MAX_AGE = 3                  # 見失ってから何フレームまで復帰を待つか
MAX_AGE_NEW = 1              # 1回しか観測していない (速度未知の) トラックは このフレーム数まで。
                             # 探索半径が MAX_SPEED と広いので、長く残すとノイズや画面端の切れ端のトラックが
                             # 後から通りかかった別の気泡を奪う
COAST_GATE_GROWTH = 0.5      # 見失っている間、1フレームごとに位置ゲートを何倍ずつ広げるか
VELOCITY_EMA_ALPHA = 0.5
MIN_TRACK_AREA = 10          # これより小さい検出はトラッキングしない (数px のノイズの点滅で新規/消失が大量に出るため)。
                             # 面積・個数の集計 (ROI) には含まれる。0 なら全てトラッキング

# --- 1対1対応のコストの重み (各項は 0〜1 に正規化済み) ---
W_POS = 1.0                  # 予測位置からのずれ (ゲート半径で正規化)
W_AREA = 1.0                 # 面積変化
W_OVERLAP = 1.0              # 予測マスクとの重なり (1 - IoU)。位置と形を同時に見る
W_SHAPE = 0.5                # 形状 (重心を合わせた IoU)。形だけを見る
W_COAST = 0.3                # 見失っていたフレーム1つあたりのペナルティ (見失い中のトラックが通りすがりの気泡を奪うのを防ぐ)
W_UNKNOWN_V = 0.3            # 速度未知トラックのペナルティ (速度既知のトラックと同じ検出を取り合ったら既知側を優先)
SHAPE_AREA_REF = 300.0       # 面積がこれより小さい気泡では重なり/形状の重みを面積に比例して下げる (小さい気泡は形がどれも似ているため)

# --- 速度未知トラックの初速度の推定 ---
USE_FLOW_PRIOR = True        # 新しく現れた気泡は「静止」と「周りの気泡と同じ速度で移動」の2仮説で次の位置を探す (False なら静止のみ)
FLOW_PRIOR_RADIUS = 150.0    # 「周り」とみなす半径 (px)
PRIOR_AREA_RATIO = 3.0       # 「周りの気泡」は面積比がこれ以内の気泡だけ (大きさで速度が違う流れで、スラグの速度を
                             # 小さい気泡に当てはめないため)。周りに該当がなければ 0 (静止のみ)。0 なら大きさを問わない (旧動作)

# --- PIV 速度場による初速度の推定 (docs/PIV_TASK.md, piv_field.py) ---
# 新しく現れた気泡の初速度を、フレーム t と t+1 の「同じ大きさ区分の気泡だけの画像」の相互相関 (PIV) で求める。
# 追跡の履歴を使わないので、速い気泡が新しく現れても その場所・その大きさの気泡の速度で次の位置を予測できる。
# 速度場は予測専用。CSV の速度 (計測値) は従来どおり個々の追跡だけから出す。
USE_PIV_PRIOR = True         # 沸騰 (加熱) 実験では核生成気泡が静止から動き出し PIV の初速度が外れるので False にすること
                             # (PIV 導入前の tracker3 と完全に同じ動作にするには PRIOR_AREA_RATIO = 0 も必要)
                             # TODO: 同じ位置で繰り返し発生する気泡 (核生成点) は初速度 0 にする
PIV_GATE = 10.0              # PIV で初速度が分かった新規トラック: 予測位置からのずれの許容 (px)。+ 等価直径 × POS_GATE_SIZE_FRAC。
                             # 速度未知トラックの MAX_SPEED より狭い。PIV が外れたときは「つながずに途切れさせる」
                             # (途切れ = 標本が減るだけ、誤接続 = 誤った速度が混入する)。ブートストラップで自動算出できる
PIV_GATE_HARD = True         # True: PIV_GATE の外の候補はつながない (誤接続より途切れ)。
                             # False: MAX_SPEED までは認めるが W_PIV_OUTSIDE のペナルティを足す
PIV_STATIC_SPEED = 3.0       # PIV の移動量がこれ未満 (px/frame) の場所では PIV_GATE_HARD でもペナルティ付きで MAX_SPEED まで認める。
                             # 止まった気泡が大半の窓では、少数の速い気泡の動きが相関に現れず PIV が ≈0 になるため
                             # (合成データで確認: ここを硬いゲートにすると途切れだけが増え、誤連結は減らなかった)。0 で無効
W_PIV_OUTSIDE = 1.0          # PIV の予測から外れた候補 (上の2つで認める場合) に足すコスト
PIV_KEEP_STATIC = True       # PIV の予測に加えて「静止」も候補にする (壁に付いて止まっている気泡が多い視野向け)。
                             # どちらの候補も PIV_GATE で絞る
PIV_USE_DX = True            # PIV の横方向 (x) の移動量も使う (False なら縦だけ)
PIV_MODE = "improved"        # "improved" (piv_field.py の変更1〜4 あり) / "faithful" (reference/piv_prior.py と同じ計算)
PIV_RASTER = "outline"       # 相関に使う画像: "outline" (気泡マスクの輪郭) / "filled" (塗りつぶし。大きい気泡で無効になりやすい)
PIV_SIZE_CLASSES = (50, 500) # 大きさ区分の境界 (面積 px): tiny < 50 <= small < 500 <= large (QC と同じ)
PIV_WINDOWS = {              # 区分ごとの窓 (1パス目の窓, 間隔, 2パス目の窓, 間隔) [px]
    "tiny": (256, 128, 128, 64), "small": (256, 128, 128, 64), "large": (256, 128, 128, 64)}
SAVE_PIV_DEBUG = False       # True なら速度場のベクトル図を OUTPUT_FOLDER/piv/ に保存 (黄 = 実測, 赤 = 周りから補間)

# --- 合体/分裂 ---
EVENT_OVERLAP_MIN = 0.3      # 候補条件: 吸収される側/分裂した子 の面積のうち、相手(の予測マスク)と重なっている割合の下限
EVENT_MARGIN = 5             # 候補条件(その2): 中心が相手の予測マスクを この幅(px) だけ膨らませた範囲に入っていれば候補にする
EVENT_AREA_TOL = 1.35        # 確定条件: 面積保存。合体後の面積 / 合体前の面積の和 (分裂は逆) が 1/この値 〜 この値 の範囲
                             # (画面端で切れている気泡が絡むときは この値の2乗 まで許す)
EVENT_MINOR_FRAC = 0.1       # 相手の面積のこの割合より小さい気泡は面積保存で確認できない (誤差に埋もれる) ので、
EVENT_MINOR_OVERLAP = 0.5    #   重なり割合がこの値以上 (または中心が相手の中) のときだけ合体/分裂に含める
TRANSIENT_MERGE_FRAMES = 2   # 合体からこのフレーム数以内に分かれ直したら「接触しただけ」とみなし元のIDに戻す。0 で無効

# ------------------------------------------------------------
# 自動ブートストラップキャリブレーション設定
# ------------------------------------------------------------
ENABLE_BOOTSTRAP = True       # Trueなら本トラッキング前にパラメータ自動算出 + ユーザー承認ステップを経る
BOOTSTRAP_NUM_SEGMENTS = 20   # 映像全体を何等分して均等サンプリングするか
# tracker2 は移動量の 90 パーセンタイルをゲートにしていたため、静止した気泡が大半だと
# 少数の速い気泡の移動量がゲートの外になり、毎フレーム新規トラックになっていた。
# ここでは「最大移動量 (速度未知のとき)」と「予測ずれ (速度既知のとき)」を分けて求める。
BOOTSTRAP_SPEED_PERCENTILE = 99   # 最大移動量 MAX_SPEED: 移動量分布のこのパーセンタイル × 安全係数
BOOTSTRAP_RESID_PERCENTILE = 95   # 予測ずれ POS_GATE: 3フレーム連続で対応した気泡の「等速と仮定した予測からのずれ」のこのパーセンタイル × 安全係数
BOOTSTRAP_AREA_PERCENTILE = 99    # 面積比ゲート
BOOTSTRAP_JUMP_MARGIN = 1.3  # 位置ゲートの安全係数 (パーセンタイル値 × この値)
BOOTSTRAP_AREA_MARGIN = 1.1  # 面積比ゲートの安全係数
BOOTSTRAP_MIN_JUMP = 5.0     # 位置ゲートの下限(px)。移動が非常に安定していてもゲートが0近くに潰れないように
BOOTSTRAP_LOOSE_GATE = 120.0     # 仮マッチング用の緩い探索半径 (px)。本ゲートより広め → 循環問題の回避
BOOTSTRAP_LOOSE_AREA_GATE = 3.0
BOOTSTRAP_RATIO_TEST = 0.7   # 仮マッチングは「1番手のコスト < 2番手 × この値」かつ相互に1番手のときだけ採用 (曖昧な対応を統計に入れない)
BOOTSTRAP_PREVIEW_FRAMES = 4  # 承認画面に表示するサンプルオーバーレイのフレーム数


import cv2
import math
import numpy as np
import os
import glob
import csv
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import watershed

try:   # piv_field.py はこのファイルと同じフォルダに置く
    import piv_field
except ImportError:
    piv_field = None

Shape = Tuple[np.ndarray, int, int]   # (bboxで切り出したboolマスク, x0, y0)


# ==============================================================
# 1. 前処理 (microgaptracker3.py と同一。UI調整は最初の1枚のみ)
# ==============================================================
def preprocess_image(img_path, bg_img, filename="Image", show_ui=False,
                      current_thresh_val=30, current_bright_val=3, current_median_val=0):
    img = cv2.imread(img_path)
    if img is None:
        return None, None, current_thresh_val, current_bright_val, current_median_val

    if not ENABLE_PREPROCESSING:
        return img, img.copy(), current_thresh_val, current_bright_val, current_median_val

    if img.shape != bg_img.shape:
        bg_img_resized = cv2.resize(bg_img, (img.shape[1], img.shape[0]))
    else:
        bg_img_resized = bg_img

    diff = cv2.absdiff(img, bg_img_resized)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    final_thresh = current_thresh_val
    final_bright = current_bright_val
    final_median = current_median_val

    if show_ui:
        hist = cv2.calcHist([gray_diff], [0], None, [256], [0, 256])
        hist_img_base = np.zeros((256, 256, 3), dtype=np.uint8)
        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
        for x, y in enumerate(hist):
            cv2.line(hist_img_base, (x, 256), (x, 256 - int(y.item())), (200, 200, 200), 1)

        window_name = f"Preview - {filename} (Adjust Sliders & Press ENTER)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        def update_preview(*args):
            th = cv2.getTrackbarPos("Noise Cut", window_name)
            br = cv2.getTrackbarPos("Brightness", window_name)
            md = cv2.getTrackbarPos("Median Filter", window_name)
            if br < 1:
                br = 1
            ksize = md * 2 + 1
            preview_blur = cv2.medianBlur(gray_diff, ksize)
            _, preview_clean = cv2.threshold(preview_blur, th, 255, cv2.THRESH_TOZERO)
            preview_bright = cv2.convertScaleAbs(preview_clean, alpha=br, beta=0)
            temp_hist = hist_img_base.copy()
            cv2.line(temp_hist, (th, 0), (th, 256), (0, 0, 255), 2)
            cv2.imshow("Histogram", temp_hist)
            preview_bgr = cv2.cvtColor(preview_bright, cv2.COLOR_GRAY2BGR)
            cv2.imshow(window_name, preview_bgr)

        cv2.createTrackbar("Noise Cut", window_name, current_thresh_val, 100, update_preview)
        cv2.createTrackbar("Brightness", window_name, current_bright_val, 10, update_preview)
        cv2.createTrackbar("Median Filter", window_name, current_median_val, 5, update_preview)
        update_preview()
        print(f"{filename}: ヒストグラム, 明るさ, Medianフィルターを調整してENTERを押してください.")

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key in [13, 32]:
                break

        final_thresh = cv2.getTrackbarPos("Noise Cut", window_name)
        final_bright = cv2.getTrackbarPos("Brightness", window_name)
        final_median = cv2.getTrackbarPos("Median Filter", window_name)
        if final_bright < 1:
            final_bright = 1
        cv2.destroyWindow(window_name)
        try:
            cv2.destroyWindow("Histogram")
        except Exception:
            pass

    ksize_final = final_median * 2 + 1
    blur_diff = cv2.medianBlur(gray_diff, ksize_final)
    _, clean_diff = cv2.threshold(blur_diff, final_thresh, 255, cv2.THRESH_TOZERO)
    bright_diff = cv2.convertScaleAbs(clean_diff, alpha=final_bright, beta=0)
    processed_img = cv2.cvtColor(bright_diff, cv2.COLOR_GRAY2BGR)

    return img, processed_img, final_thresh, final_bright, final_median


# ==============================================================
# 2. U-Net 検出
# ==============================================================
class UNetDetector:
    """best.pt を読み込み、画素ごとの 背景/内部/境界 確率 (3, H, W) を返す。"""

    def __init__(self, ckpt_path, train_hw=None):
        import torch
        import segmentation_models_pytorch as smp
        self.torch = torch
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        ck = torch.load(ckpt_path, map_location=self.dev)
        self.model = smp.Unet(ck["encoder"], encoder_weights=None,
                              in_channels=3, classes=ck["classes"]).to(self.dev)
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()
        self.mean = np.array(ck["mean"], np.float32)
        self.std = np.array(ck["std"], np.float32)
        hw = ck.get("train_hw") or train_hw
        self.train_hw = (int(hw[0]), int(hw[1])) if hw else None
        self._resize_notice = False
        print(f"  U-Net: {ckpt_path}  (epoch {ck.get('epoch')}, device {self.dev}, "
              f"学習画像サイズ {self.train_hw if self.train_hw else '記録なし'})")
        if self.dev == "cpu":
            print("  ※ GPUが見つかりません。CPUでも動きますが遅くなります。")

    def _forward(self, gray):
        torch = self.torch
        H, W = gray.shape
        ph, pw = (-H) % 32, (-W) % 32
        g = cv2.copyMakeBorder(gray, 0, ph, 0, pw, cv2.BORDER_REFLECT_101)
        x = np.stack([g] * 3, -1).astype(np.float32) / 255.0
        x = (x - self.mean) / self.std
        x = torch.from_numpy(x).permute(2, 0, 1)[None].to(self.dev)
        with torch.no_grad():
            p = self.model(x).softmax(1)[0].cpu().numpy()
        return p[:, :H, :W]

    def prob(self, gray):
        H, W = gray.shape
        if self.train_hw is None or (H, W) == self.train_hw:
            return self._forward(gray)
        # 撮影画像と学習画像のサイズが違う → 学習サイズに合わせて推論し、確率マップを元のサイズに戻す
        th, tw = self.train_hw
        if not self._resize_notice:
            print(f"  ※ 画像サイズ {H}x{W} が学習画像 {th}x{tw} と異なるため、学習サイズに合わせて推論します")
            self._resize_notice = True
        interp = cv2.INTER_AREA if th * tw < H * W else cv2.INTER_LINEAR
        p = self._forward(cv2.resize(gray, (tw, th), interpolation=interp))
        return np.stack([cv2.resize(c, (W, H), interpolation=cv2.INTER_LINEAR) for c in p])


def extract_instances(prob, min_area=4, band=25, edge_thr=0.5, close_it=2, tiny_max=300):
    """確率マップ (3,H,W) -> 気泡ラベルマップ (0=なし, 1..N=気泡)
    1) 境界(class 2)を壁として領域分割。フレーム端も壁とする -> 画面で切れた気泡の領域も閉じる
    2) 領域の判定: 壁近傍の帯で 内部確率 > 背景確率 なら気泡
    3) watershed で境界画素を隣接領域に配分
    4) 内部画素が残らなかった小気泡: 閉じた境界の塊を塗りつぶして気泡とする
    """
    H, W = prob.shape[1:]
    edge_raw = prob[2] > edge_thr

    p = close_it + 3                                       # closing がフレーム端の壁を削らないよう余白
    ep = np.pad(edge_raw, p, constant_values=True)
    if close_it > 0:
        ep = ndimage.binary_closing(ep, iterations=close_it + 1)
    ep = ep[p - 1:-(p - 1), p - 1:-(p - 1)]                # 1px の外枠だけ残す
    ep[0, :] = ep[-1, :] = ep[:, 0] = ep[:, -1] = True
    lab, n = ndimage.label(~ep)
    lab = lab[1:-1, 1:-1]
    edge = ep[1:-1, 1:-1]

    inst = np.zeros((H, W), np.int32)
    k = 0
    if n > 0:
        wall_band = ndimage.binary_dilation(edge, iterations=band)
        size = np.bincount(lab.ravel(), minlength=n + 1)
        lb = lab[wall_band]
        cnt = np.bincount(lb, minlength=n + 1)
        s_in = np.bincount(lb, weights=prob[1][wall_band].astype(np.float64), minlength=n + 1)
        s_bg = np.bincount(lb, weights=prob[0][wall_band].astype(np.float64), minlength=n + 1)
        ok = (size >= min_area) & (cnt > 0) & (s_in > s_bg)
        ok[0] = False
        keep = np.nonzero(ok)[0]
        if keep.size:
            ws = watershed(prob[2], markers=lab)
            lut = np.zeros(n + 1, np.int32)
            lut[keep] = np.arange(1, keep.size + 1, dtype=np.int32)
            inst = lut[ws]
            k = int(keep.size)

    assigned = inst > 0
    near_assigned = ndimage.binary_dilation(assigned, iterations=2)
    comp, nc = ndimage.label(edge_raw & ~assigned)         # closing 前の境界を使う (角の残骸を拾わない)
    for ci, sl in enumerate(ndimage.find_objects(comp), start=1):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, H)
        x0, x1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, W)
        c = comp[y0:y1, x0:x1] == ci
        if (c & near_assigned[y0:y1, x0:x1]).any():         # 大きい気泡のリングの外側半分 -> 除外
            continue
        filled = ndimage.binary_fill_holes(c)
        a = int(filled.sum())
        if a < min_area or a > tiny_max:
            continue
        k += 1
        inst[y0:y1, x0:x1][filled] = k
    return inst


def extract_instances_seed(prob, min_area=4, edge_thr=0.5, tiny_max=300, seed_thr=0.5, close_it=2):
    """確率マップ (3,H,W) -> 気泡ラベルマップ (0=なし, 1..N=気泡)。UNET_INSTANCE_MODE = "seed" の方式。
    1) 種 = 気泡の芯 (内部確率 > seed_thr かつ 境界確率 <= edge_thr) のかたまり。壁が閉じているかに関係なく決まる
    2) 背景 (背景確率 >= 0.5) も種にして、境界確率を標高とする watershed で境界画素を両側に配分する
       (従来の "wall" と同じく、境界の帯の尾根で分ける)。芯は固定なので、壁が途切れていても背景に漏れない
    3) 芯のない前景 (背景確率 < 0.5) のかたまり = 内部確率が出ない小さい点 は、穴を埋めたかたまり全体を1個の気泡とする
       (従来の小気泡の経路と同じ)。面積が min_area〜tiny_max のものだけ
    芯は "wall" の closing と同じ回数の opening をかける: "wall" で閉じてしまう細い内部 (小さいリング気泡の穴) は芯にせず
    3) で扱うので、気泡の面積の決め方 (輪郭の内側/外側) が "wall" と揃う"""
    H, W = prob.shape[1:]
    fg = prob[0] < 0.5
    core = (prob[1] > seed_thr) & (prob[2] <= edge_thr)
    if close_it > 0:
        core = ndimage.binary_opening(core, iterations=close_it + 1)
    markers, n = ndimage.label(core)
    markers = markers.astype(np.int32)
    fl, nf = ndimage.label(fg)
    has_core = np.zeros(nf + 1, bool)
    has_core[np.unique(fl[core])] = True
    k = n
    for ci, sl in enumerate(ndimage.find_objects(fl), start=1):
        if sl is None or has_core[ci]:
            continue
        y0, y1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, H)
        x0, x1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, W)
        filled = ndimage.binary_fill_holes(fl[y0:y1, x0:x1] == ci)
        a = int(filled.sum())
        if a < min_area or a > tiny_max:
            continue
        k += 1
        markers[y0:y1, x0:x1][filled & (markers[y0:y1, x0:x1] == 0)] = k
    bg_id = k + 1
    markers[~fg & (markers == 0)] = bg_id
    ws = watershed(prob[2], markers=markers)
    ws[ws == bg_id] = 0
    area = np.bincount(ws.ravel(), minlength=bg_id + 1)
    keep = np.nonzero(area[:bg_id] >= min_area)[0]
    keep = keep[keep > 0]
    lut = np.zeros(bg_id + 1, np.int32)
    lut[keep] = np.arange(1, keep.size + 1, dtype=np.int32)
    return lut[ws]


def unet_instances(prob):
    """UNET_INSTANCE_MODE に従って確率マップを気泡ラベルマップにする"""
    if UNET_INSTANCE_MODE == "seed":
        return extract_instances_seed(prob, UNET_MIN_AREA, UNET_EDGE_THR, UNET_TINY_MAX, UNET_SEED_THR, UNET_CLOSE)
    return extract_instances(prob, UNET_MIN_AREA, UNET_BAND, UNET_EDGE_THR, UNET_CLOSE, UNET_TINY_MAX)


# ==============================================================
# 3. 検出データ構造
# ==============================================================
@dataclass
class Detection:
    shape: Shape              # (boolマスク, x0, y0)。形状IoU・合体/分裂判定用
    contours: list            # 画像座標の輪郭 (描画用。成分ごとに別々に描く)
    area: float               # 全体面積 (トラッキングのゲート/コスト用 - ROIと無関係に維持)
    cx: float
    cy: float
    leading_x: float
    leading_y: float
    perimeter: float = 0.0    # 輪郭長 (px)
    touches_frame: bool = False  # 画面端に接している (切れた気泡: 面積・周長は不完全)
    touch: Tuple[bool, bool, bool, bool] = (False, False, False, False)  # 画面の 上/下/左/右 端に接しているか
    conf: float = 1.0
    area_in_roi: float = 0.0  # ROIと重なる部分の面積 (統計用)
    in_roi: bool = True       # ROIに少しでもかかっているか (個数カウント用)


def leading_edge_from_points(pts: np.ndarray, percentile: float = LEADING_EDGE_PERCENTILE):
    """輪郭点のうち上側(yが小さい)percentile%の平均 = 先端部"""
    n = max(3, int(len(pts) * percentile / 100.0))
    top = pts[np.argsort(pts[:, 1])[:n]]
    return float(np.mean(top[:, 0])), float(np.mean(top[:, 1]))


def instances_to_detections(inst: np.ndarray, roi_bool: np.ndarray) -> List[Detection]:
    H, W = inst.shape
    dets: List[Detection] = []
    for k, sl in enumerate(ndimage.find_objects(inst), start=1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        m = inst[y0:y1, x0:x1] == k
        area = int(np.count_nonzero(m))
        if area == 0 or area <= IGNORE_PARTICLE_AREA:   # 粒子 (IGNORE_PARTICLE_AREA 以下) は無視
            continue
        ys, xs = np.nonzero(m)
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,
                                 offset=(x0, y0))
        pts = np.vstack([c.reshape(-1, 2) for c in cs]).astype(np.float64)
        lx, ly = leading_edge_from_points(pts)
        per = float(sum(cv2.arcLength(c, True) for c in cs))
        a_roi = float(np.count_nonzero(m & roi_bool[y0:y1, x0:x1]))
        touch = (bool(y0 == 0), bool(y1 == H), bool(x0 == 0), bool(x1 == W))
        dets.append(Detection(
            shape=(m, x0, y0), contours=cs, area=float(area),
            cx=float(xs.mean() + x0), cy=float(ys.mean() + y0),
            leading_x=lx, leading_y=ly, perimeter=per,
            touches_frame=any(touch), touch=touch,
            area_in_roi=a_roi, in_roi=a_roi > 0,
        ))
    return dets


# ==============================================================
# 4. 形状比較 (画素マスク)
# ==============================================================
def overlap_px(a: Shape, b: Shape) -> int:
    """2つのマスクの重なり画素数"""
    ma, ax, ay = a
    mb, bx, by = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1 = min(ax + ma.shape[1], bx + mb.shape[1])
    y1 = min(ay + ma.shape[0], by + mb.shape[0])
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(np.count_nonzero(ma[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & mb[y0 - by:y1 - by, x0 - bx:x1 - bx]))


def group_iou(shapes_a: List[Shape], shift: Tuple[float, float], shapes_b: List[Shape]) -> float:
    """「shapes_a の和集合を shift だけ平行移動したもの」と「shapes_b の和集合」の IoU。
    1対1 (形状維持の確認)、多対1 (合体の確認)、1対多 (分裂の確認) をすべてこれで計算する。
    2つの和集合を囲む小さなキャンバスだけで計算するので軽い。"""
    if not shapes_a or not shapes_b:
        return 0.0
    sx, sy = int(round(shift[0])), int(round(shift[1]))
    a_list = [(m, x + sx, y + sy) for m, x, y in shapes_a]
    allsh = a_list + list(shapes_b)
    X0 = min(x for _, x, _ in allsh)
    Y0 = min(y for _, _, y in allsh)
    X1 = max(x + m.shape[1] for m, x, _ in allsh)
    Y1 = max(y + m.shape[0] for m, _, y in allsh)
    W, H = X1 - X0, Y1 - Y0
    if W <= 0 or H <= 0 or W > 4000 or H > 4000:
        return 0.0
    ua = np.zeros((H, W), bool)
    ub = np.zeros((H, W), bool)
    for m, x, y in a_list:
        ua[y - Y0:y - Y0 + m.shape[0], x - X0:x - X0 + m.shape[1]] |= m
    for m, x, y in shapes_b:
        ub[y - Y0:y - Y0 + m.shape[0], x - X0:x - X0 + m.shape[1]] |= m
    inter = int(np.count_nonzero(ua & ub))
    union = int(np.count_nonzero(ua | ub))
    return inter / union if union else 0.0


def compute_motion_compensated_iou(prev_shape: Optional[Shape], curr_shape: Optional[Shape],
                                   shift_x: float, shift_y: float) -> float:
    """トラックの前回マスクを「この検出が正解と仮定した実測移動量」(検出中心 - 前回中心)だけ平行移動して IoU を計算。
    予測移動量を使わないのは、予測が外れると同一物体でも形がずれて見え、形状比較が汚れるため。
    形を保ったまま移動しただけなら IoU は高く、合体/分裂のように形自体が急変すると低くなる。"""
    if prev_shape is None or curr_shape is None:
        return 0.5  # 履歴のないトラックにはペナルティもボーナスも与えない(中立値)
    return group_iou([prev_shape], (shift_x, shift_y), [curr_shape])


def eq_diameter(area: float) -> float:
    """等価直径 (同じ面積の円の直径)"""
    return 2.0 * math.sqrt(max(area, 0.0) / math.pi)


def shift_shape(s: Shape, dx: float, dy: float) -> Shape:
    m, x0, y0 = s
    return (m, x0 + int(round(dx)), y0 + int(round(dy)))


def mask_iou(a: Shape, area_a: float, b: Shape, area_b: float) -> float:
    """重心合わせをしない素の IoU。位置と形の両方が合っているときだけ高くなる。"""
    ov = overlap_px(a, b)
    return ov / max(1.0, area_a + area_b - ov) if ov else 0.0


def _near_bbox(s: Shape, x: float, y: float, r: int) -> bool:
    m, x0, y0 = s
    return x0 - r <= x < x0 + m.shape[1] + r and y0 - r <= y < y0 + m.shape[0] + r


def point_in_shape(s: Shape, x: float, y: float) -> bool:
    m, x0, y0 = s
    xi, yi = int(round(x)) - x0, int(round(y)) - y0
    return 0 <= yi < m.shape[0] and 0 <= xi < m.shape[1] and bool(m[yi, xi])


def dilate_shape(s: Shape, r: int) -> Shape:
    """マスクを r px 膨らませる (合体/分裂の候補探索用)"""
    if r <= 0:
        return s
    m, x0, y0 = s
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return (cv2.dilate(np.pad(m, r).astype(np.uint8), k).astype(bool), x0 - r, y0 - r)


def _axis_modes(touch_a, touch_b):
    """2つの観測 (前回と今回) の位置をどこで比べるかを軸ごとに決める。
    画面端で切れた気泡の重心は、見えている部分が増減するだけで実際の移動と無関係に動く。
    そこで、どちらかの観測で上端が切れていれば下端、下端が切れていれば上端を使う (x も同様)。
    両側とも切れていれば重心を使い、信頼度が低いことを返す。
    戻り値: (x の基準, y の基準, 信頼度が低いか)   基準は "c"=重心, "lo"=座標の小さい側の端, "hi"=大きい側の端"""
    def mode(lo_cut, hi_cut):
        if lo_cut and hi_cut:
            return "c", True
        if lo_cut:
            return "hi", False
        if hi_cut:
            return "lo", False
        return "c", False
    my, loose_y = mode(touch_a[0] or touch_b[0], touch_a[1] or touch_b[1])
    mx, loose_x = mode(touch_a[2] or touch_b[2], touch_a[3] or touch_b[3])
    return mx, my, (loose_x or loose_y)


def _ref_xy(obj, mx: str, my: str) -> Tuple[float, float]:
    """_axis_modes で決めた基準点。obj は Track でも Detection でもよい"""
    m, x0, y0 = obj.shape
    x = obj.cx if mx == "c" else float(x0 if mx == "lo" else x0 + m.shape[1] - 1)
    y = obj.cy if my == "c" else float(y0 if my == "lo" else y0 + m.shape[0] - 1)
    return x, y


def displacement(a, b) -> Tuple[float, float, bool]:
    """観測 a -> b の移動量 (dx, dy) と、その信頼度が低いか (両側とも画面端で切れている)"""
    mx, my, loose = _axis_modes(a.touch, b.touch)
    ax, ay = _ref_xy(a, mx, my)
    bx, by = _ref_xy(b, mx, my)
    return bx - ax, by - ay, loose


# ==============================================================
# 5. LAPトラッカー (ハンガリアン法 + 合体/分裂)
# ==============================================================
@dataclass
class Track:
    track_id: int
    leading_x: float
    leading_y: float
    cx: float
    cy: float
    area: float
    shape: Optional[Shape] = None  # 直近でマッチした検出のマスク
    touch: Tuple[bool, bool, bool, bool] = (False, False, False, False)
    vx: float = 0.0                # 速度 (px/frame)。v_known が False の間は使わない
    vy: float = 0.0
    v_known: bool = False          # 2回以上観測して速度を実測したか
    prior_vx: float = 0.0          # 速度未知の間に使う初速度の推定 (PIV / 周りの流れ / 分裂の子なら親の速度)
    prior_vy: float = 0.0
    prior_src: str = ""            # 初速度の出どころ: "piv" (PIV 速度場) / "" (それ以外)
    hits: int = 1
    time_since_update: int = 0
    first_frame: int = 0
    last_frame: int = 0
    parent_ids: List[int] = field(default_factory=list)
    # 合体直後の一時保持 (接触しただけで すぐ分かれ直したときに元のIDに戻すため)
    merge_frame: int = -1
    dormant: List["Track"] = field(default_factory=list)   # 吸収したトラック (合体直前の状態のまま)
    pre_merge: Optional["Track"] = None                     # 合体直前の自分自身

    def motion_hypotheses(self, k: int) -> List[Tuple[float, float]]:
        """k フレーム後までの移動量の仮説。速度既知なら1つ、未知なら「静止」と「周りの流れ」の2つ
        (PIV で初速度が分かったトラックは「PIV」、PIV_KEEP_STATIC なら + 「静止」)"""
        if self.v_known:
            return [(self.vx * k, self.vy * k)]
        if self.prior_src == "piv":
            hyps = [(self.prior_vx * k, self.prior_vy * k)]
            if PIV_KEEP_STATIC:
                hyps.append((0.0, 0.0))
            return hyps
        hyps = [(0.0, 0.0)]
        if USE_FLOW_PRIOR and (self.prior_vx or self.prior_vy):
            hyps.append((self.prior_vx * k, self.prior_vy * k))
        return hyps

    def predicted_shapes(self, frame_idx: int) -> List[Shape]:
        """前回マスクを予測移動量 (x, y) だけ平行移動した予測マスク"""
        k = max(1, frame_idx - self.last_frame)
        return [shift_shape(self.shape, dx, dy) for dx, dy in self.motion_hypotheses(k)]

    def observe(self, d: Detection, frame_idx: int, hold_v: bool = False):
        """検出 d で状態を更新する。
        速度は「移動量 / 経過フレーム数」の EMA (tracker2 は見失い後の復帰で経過フレーム数で割っていなかった)"""
        if not hold_v:
            k = max(1, frame_idx - self.last_frame)
            dx, dy, _ = displacement(self, d)
            if self.v_known:
                a = VELOCITY_EMA_ALPHA
                self.vx = a * self.vx + (1 - a) * dx / k
                self.vy = a * self.vy + (1 - a) * dy / k
            else:
                self.vx, self.vy, self.v_known = dx / k, dy / k, True
        self.leading_x, self.leading_y = d.leading_x, d.leading_y
        self.cx, self.cy = d.cx, d.cy
        self.area = d.area
        self.shape = d.shape
        self.touch = d.touch
        self.hits += 1
        self.time_since_update = 0
        self.last_frame = frame_idx

    def clear_transient(self):
        self.merge_frame, self.dormant, self.pre_merge = -1, [], None


def pair_cost(t: Track, d: Detection, frame_idx: int) -> Optional[float]:
    """トラック t と検出 d を同じ気泡として対応させるコスト (各項 0〜1 の重み付き和)。ゲート外なら None。
      位置 : 予測位置からのずれ / ゲート半径。ゲート半径は「POS_GATE + 等価直径 × POS_GATE_SIZE_FRAC」
             (速度未知なら + MAX_SPEED) なので、大きい気泡ほど・速度が分からないトラックほど広い
      面積 : |log 面積比| / log AREA_RATIO_GATE
      重なり: 予測マスクとの素の IoU (位置と形を同時に見る)。小さい気泡では重みを下げる
      形状 : 重心を合わせた IoU (形だけを見る)。小さい気泡では重みを下げる"""
    k = max(1, frame_idx - t.last_frame)
    extra = 0.0
    touching = any(t.touch) or any(d.touch)
    area_gate = AREA_RATIO_GATE * (2.0 if touching else 1.0)
    area_ratio = max(t.area, d.area) / max(1.0, min(t.area, d.area))
    smaller_cut = any(t.touch) if t.area <= d.area else any(d.touch)   # 画面に入ってくる途中/出ていく途中
    if area_ratio > area_gate and not smaller_cut:
        return None
    dx, dy, loose = displacement(t, d)
    resid = min(math.hypot(dx - hx, dy - hy) for hx, hy in t.motion_hypotheses(k))
    size_slack = POS_GATE_SIZE_FRAC * eq_diameter(max(t.area, d.area))
    slack = POS_GATE + size_slack
    if t.v_known:
        radius = slack * (1.0 + COAST_GATE_GROWTH * (k - 1))
        gate_dist = resid
    elif t.prior_src == "piv":   # PIV で初速度が分かっている: 予測 (と静止) の周りだけ。MAX_SPEED の円より広げない
        radius = min((PIV_GATE + size_slack) * (1.0 + COAST_GATE_GROWTH * (k - 1)), MAX_SPEED * k + slack)
        gate_dist = resid
        hard = PIV_GATE_HARD and math.hypot(t.prior_vx, t.prior_vy) >= PIV_STATIC_SPEED
        if resid > radius and not hard:   # PIV の予測から外れる: 速度未知と同じ広さまで、ペナルティ付き
            radius = MAX_SPEED * k + slack
            gate_dist = math.hypot(dx, dy)
            extra = W_PIV_OUTSIDE
        elif math.hypot(dx, dy) > (MAX_SPEED * k + slack) * (2.0 if loose else 1.0):
            return None   # PIV の予測の円でも、物理的に動ける距離 (MAX_SPEED) の外は認めない
    else:   # 速度未知: 物理的に動ける距離までは候補にする (コストは2仮説の近い方で評価)
        radius = MAX_SPEED * k + slack
        gate_dist = math.hypot(dx, dy)
    if loose:
        radius *= 2.0
    iou_pred = max(mask_iou(ps, t.area, d.shape, d.area) for ps in t.predicted_shapes(frame_idx))
    if gate_dist > radius and iou_pred < OVERLAP_ACCEPT_IOU:
        return None
    size_w = min(1.0, min(t.area, d.area) / SHAPE_AREA_REF)
    if smaller_cut:   # 切れ端と全体の比較になるので、面積と形は判断材料にしない
        c_area = c_shape = 0.0
    else:
        c_area = min(1.0, math.log(area_ratio) / math.log(max(area_gate, 1.01)))
        c_shape = 1.0 - compute_motion_compensated_iou(t.shape, d.shape, d.cx - t.cx, d.cy - t.cy)
    return (W_POS * min(1.0, (resid / radius) ** 2)
            + W_AREA * c_area
            + size_w * (W_OVERLAP * (1.0 - iou_pred) + W_SHAPE * c_shape)
            + W_COAST * (k - 1)
            + (0.0 if t.v_known else W_UNKNOWN_V)
            + extra)


def _relax_tight(t: Track, d: Detection, frame_idx: int) -> bool:
    """面積ゲートの緩和 (AREA_RELAX_RATIO) の候補か: 速度既知・画面端に接していない・面積比が AREA_RELAX_RATIO 以内で、
    予測位置からのずれが AREA_RELAX_POS + 小さい側の等価直径 × POS_GATE_SIZE_FRAC 以内"""
    if not t.v_known or any(t.touch) or any(d.touch):
        return False
    if max(t.area, d.area) / max(1.0, min(t.area, d.area)) > AREA_RELAX_RATIO:
        return False
    k = max(1, frame_idx - t.last_frame)
    dx, dy, _ = displacement(t, d)
    tight = (AREA_RELAX_POS + POS_GATE_SIZE_FRAC * eq_diameter(min(t.area, d.area))) * (1.0 + COAST_GATE_GROWTH * (k - 1))
    return math.hypot(dx - t.vx * k, dy - t.vy * k) <= tight


def _area_tol(touching: bool) -> float:
    return EVENT_AREA_TOL ** 2 if touching else EVENT_AREA_TOL


def _grow_group(members_area: float, have_members: bool, cand_area: float, total_area: float,
                frac: float, center_in: bool, tol: float, is_merge: bool) -> bool:
    """合体/分裂のグループに候補を加えるか。
    members_area : 今のグループの面積の和 (合体: 吸収するトラック群, 分裂: 子の検出群)
    total_area   : 相手の面積 (合体: 合体後の検出, 分裂: 分裂前の親)
    面積保存 (合計 ≈ 相手) が良くなるなら加える。相手の EVENT_MINOR_FRAC 未満の小さい気泡は
    面積では確認できないので、重なり (合体なら中心が相手の中でもよい) だけで判定する。"""
    if cand_area < EVENT_MINOR_FRAC * total_area:
        return frac >= EVENT_MINOR_OVERLAP or (is_merge and center_in)
    if not have_members:
        return True
    before = abs(math.log(total_area / max(1.0, members_area)))
    after_ratio = total_area / (members_area + cand_area)
    inside = frac >= EVENT_MINOR_OVERLAP or center_in
    return abs(math.log(after_ratio)) < before or (inside and 1.0 / tol <= after_ratio <= tol)


class LeadingEdgeLapTracker:
    """フレーム間対応付け。
      同一気泡 : ハンガリアン法 (コスト = 予測ずれ + 面積変化 + 予測マスクとの重なり + 形状、ゲート付き)
      接触復帰 : 直前に合体したトラックが元の気泡に分かれ直したら元のIDに戻す
      合体     : 対応なしトラックの予測マスクが検出と重なる -> 面積保存「A + B ≈ X」で確認
      分裂     : 対応なし検出が親トラックの予測マスクと重なる -> 面積保存「X ≈ A' + B'」で確認
    """

    def __init__(self):
        self.tracks: List[Track] = []
        self._next_id = 1
        self.restores: List[Tuple[int, int, int, int]] = []   # (合体フレーム, 復帰フレーム, ホストID, 戻したID)
        self.prior_counts: Dict[str, int] = defaultdict(int)  # 新規トラックの初速度の出どころ (piv / flow / zero)
        self.relaxed_links = 0                                # 面積ゲートの緩和 (AREA_RELAX_RATIO) でつないだ数

    def _new_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def update(self, detections: List[Detection], frame_idx: int, piv=None) -> List[dict]:
        """piv: フレーム frame_idx -> frame_idx+1 の大きさ区分ごとの速度場 {区分: DisplacementField or None}。
        新しく現れた気泡の初速度にだけ使う (None なら従来どおり)"""
        det_ids = [j for j, d in enumerate(detections) if d.area >= MIN_TRACK_AREA]   # 元の検出番号
        dets = [detections[j] for j in det_ids]
        self.tracks = [t for t in self.tracks
                       if t.time_since_update <= (MAX_AGE if t.v_known else MAX_AGE_NEW)]
        active = list(self.tracks)
        n_t, n_d = len(active), len(dets)

        # ---- 1) 同一気泡: コスト行列 + ハンガリアン法 ----
        det_to_track: Dict[int, int] = {}
        if n_t and n_d:
            cost = np.full((n_t, n_d), 1e6)
            for i, t in enumerate(active):
                for j, d in enumerate(dets):
                    c = pair_cost(t, d, frame_idx)
                    if c is not None:
                        cost[i, j] = c
            for i, j in zip(*linear_sum_assignment(cost)):
                if cost[i, j] < 1e6:
                    det_to_track[j] = i
        matched_t = set(det_to_track.values())

        # ---- 2) 接触からの復帰: 合体直後のトラックが元の気泡に分かれ直したら元のIDに戻す ----
        # 候補 = 吸収されたトラック (合体直前の状態) + ハンガリアン法で対応しなかったホストの合体直前の状態
        restored: Dict[int, Tuple[Track, Track]] = {}   # 検出j -> (戻す状態, ホスト)
        if TRANSIENT_MERGE_FRAMES > 0:
            cands: List[Tuple[Track, Track]] = []
            for i, h in enumerate(active):
                if h.merge_frame < 0 or frame_idx - h.merge_frame > TRANSIENT_MERGE_FRAMES:
                    continue
                cands += [(m, h) for m in h.dormant]
                if i not in matched_t and h.pre_merge is not None:
                    cands.append((h.pre_merge, h))
            free = [j for j in range(n_d) if j not in det_to_track]
            if cands and free:
                cost = np.full((len(cands), len(free)), 1e6)
                for a, (snap, h) in enumerate(cands):
                    # PIV の初速度を持つ (速度未知の) 気泡は、塊になっている間ホストと一緒に動いていたかもしれないので、
                    # 「ホストの移動量で動いた」も候補に加える (PIV の予測だけだと、接触から戻った気泡を見逃す)。
                    # PIV 導入前の広いゲートに戻すと、遠くの別の気泡を戻してしまう誤接続が出るので戻さない
                    alts = [snap]
                    hj = next((jj for jj, ii in det_to_track.items() if active[ii] is h), None)
                    if not snap.v_known and snap.prior_src == "piv" and h.pre_merge is not None and hj is not None:
                        kk = max(1, frame_idx - snap.last_frame)
                        hdx, hdy, _ = displacement(h.pre_merge, dets[hj])
                        alts.append(replace(snap, prior_vx=hdx / kk, prior_vy=hdy / kk))
                    for b, j in enumerate(free):
                        cs = [c for c in (pair_cost(s_, dets[j], frame_idx) for s_ in alts) if c is not None]
                        if cs:
                            cost[a, b] = min(cs)
                for a, b in zip(*linear_sum_assignment(cost)):
                    if cost[a, b] < 1e6:
                        restored[free[b]] = cands[a]
            # 面積保存で確認: 分かれ直した後の面積の和 ≈ 合体していた塊の面積 (塊がそのまま残っていて、
            # 近くに別の気泡が現れただけなら和が大きくなりすぎる -> 取り消す)。
            # ホスト側が見つからない (塊が さらに別の気泡と合体した等) ときは確認できないので、個々のゲートだけで判断する
            track_idx = {id(t): i for i, t in enumerate(active)}
            by_host: Dict[int, List[int]] = defaultdict(list)
            for j, (_, h) in restored.items():
                by_host[id(h)].append(j)
            for hid, js in by_host.items():
                h = active[track_idx[hid]]
                hj = next((j for j, i in det_to_track.items() if active[i] is h), None)
                if hj is None and not any(restored[j][0] is h.pre_merge for j in js):
                    continue
                parts = js + ([hj] if hj is not None else [])
                touching = any(h.touch) or any(any(dets[j].touch) for j in parts)
                tol = _area_tol(touching)
                ratio = sum(dets[j].area for j in parts) / max(1.0, h.area)
                if not (1.0 / tol <= ratio <= tol):
                    for j in js:
                        del restored[j]
        restored_hosts = {id(h) for snap, h in restored.values() if snap is h.pre_merge}
        hosts_with_restore = {id(h) for _, h in restored.values()}

        # ---- 3) 合体: 対応なしトラック i の予測マスクが、どの検出に重なるか ----
        # 構成メンバーは全員「直前フレームで観測されたトラック」に限る。
        # 同じフレームの検出同士は重ならない = 確実に別々の気泡なので、
        # 同じ気泡の古い重複トラック(ID途切れの残り)を「合体」と誤判定しない。
        dil_cache: Dict[int, Shape] = {}

        def dilated_det(j):
            if j not in dil_cache:
                dil_cache[j] = dilate_shape(dets[j].shape, EVENT_MARGIN)
            return dil_cache[j]

        cand_by_det: Dict[int, List[Tuple[float, bool, int]]] = defaultdict(list)
        for i, t in enumerate(active):
            if i in matched_t or t.last_frame != frame_idx - 1 or id(t) in restored_hosts:
                continue
            shapes = [t.shape] + t.predicted_shapes(frame_idx)
            centers = [(t.cx, t.cy)] + [(t.cx + hx, t.cy + hy) for hx, hy in t.motion_hypotheses(1)]
            best = None
            for j, d in enumerate(dets):
                if j in restored or d.area < t.area / _area_tol(True):
                    continue   # 合体後の塊は構成メンバーより小さくならない
                frac = max(overlap_px(s, d.shape) for s in shapes) / max(1.0, t.area)
                center_in = any(_near_bbox(d.shape, x, y, EVENT_MARGIN) and point_in_shape(dilated_det(j), x, y)
                                for x, y in centers)
                if frac >= EVENT_OVERLAP_MIN or center_in:
                    if best is None or (frac, center_in) > best[:2]:
                        best = (frac, center_in, j)
            if best:
                cand_by_det[best[2]].append((best[0], best[1], i))

        merge_map: Dict[int, List[int]] = {}   # 検出j -> 吸収されたトラックの index
        for j, cands in cand_by_det.items():
            d = dets[j]
            primary = det_to_track.get(j)
            if primary is not None and id(active[primary]) in hosts_with_restore:
                continue   # 接触から戻ったばかりのホストは同じフレームで合体させない
            members = [primary] if primary is not None else []
            touching = any(d.touch) or any(any(active[k].touch) for k in members)
            for frac, center_in, i in sorted(cands, key=lambda c: -active[c[2]].area):   # 大きい順
                t = active[i]
                tol = _area_tol(touching or any(t.touch))
                if _grow_group(sum(active[k].area for k in members), bool(members), t.area, d.area,
                               frac, center_in, tol, is_merge=True):
                    members.append(i)
                    touching = touching or any(t.touch)
            if len(members) < 2:
                continue
            ratio = d.area / sum(active[k].area for k in members)
            tol = _area_tol(touching)
            if not (1.0 / tol <= ratio <= tol):
                continue
            if primary is None:   # ハンガリアン法で対応しなかった合体塊 -> 最大のトラックのIDを継承
                primary = max(members, key=lambda k: active[k].area)
                det_to_track[j] = primary
            merge_map[j] = [k for k in members if k != primary]

        absorbed_t = {k for ks in merge_map.values() for k in ks}
        merge_primary_t = {det_to_track[j] for j in merge_map}

        # ---- 4) 分裂: 対応なし検出 j が、どの親トラックの (予測)マスクと重なるか ----
        claimed_d = set(det_to_track) | set(restored)
        parents_ok = [i for i in range(n_t)
                      if i not in absorbed_t and i not in merge_primary_t and id(active[i]) not in restored_hosts]
        parent_shapes = {i: [active[i].shape] + active[i].predicted_shapes(frame_idx) for i in parents_ok}
        parent_dil: Dict[Tuple[int, int], Shape] = {}
        cand_by_parent: Dict[int, List[Tuple[float, bool, int]]] = defaultdict(list)
        for j, d in enumerate(dets):
            if j in claimed_d:
                continue
            best = None
            for i in parents_ok:
                t = active[i]
                if d.area > t.area * _area_tol(True):
                    continue   # 子は親より大きくならない
                frac = max(overlap_px(s, d.shape) for s in parent_shapes[i]) / max(1.0, d.area)
                center_in = False
                for h, s in enumerate(parent_shapes[i]):
                    if _near_bbox(s, d.cx, d.cy, EVENT_MARGIN):
                        if (i, h) not in parent_dil:
                            parent_dil[(i, h)] = dilate_shape(s, EVENT_MARGIN)
                        if point_in_shape(parent_dil[(i, h)], d.cx, d.cy):
                            center_in = True
                            break
                if frac >= EVENT_OVERLAP_MIN or center_in:
                    if best is None or (frac, center_in) > best[:2]:
                        best = (frac, center_in, i)
            if best:
                cand_by_parent[best[2]].append((best[0], best[1], j))

        track_to_det = {i: j for j, i in det_to_track.items()}
        split_map: Dict[int, int] = {}        # 新しい検出j -> 親トラックの index
        heirs = set()                         # 親が1対1対応しなかった分裂で、親のIDを継承した検出
        split_parents = set()
        for i, cands in cand_by_parent.items():
            t = active[i]
            primary_j = track_to_det.get(i)
            children = [primary_j] if primary_j is not None else []
            touching = any(t.touch) or any(any(dets[c].touch) for c in children)
            for frac, center_in, j in sorted(cands, key=lambda c: -dets[c[2]].area):   # 大きい順
                d = dets[j]
                tol = _area_tol(touching or any(d.touch))
                if _grow_group(sum(dets[c].area for c in children), bool(children), d.area, t.area,
                               frac, center_in, tol, is_merge=False):
                    children.append(j)
                    touching = touching or any(d.touch)
            if len(children) < 2:
                continue
            ratio = sum(dets[c].area for c in children) / t.area
            tol = _area_tol(touching)
            if not (1.0 / tol <= ratio <= tol):
                continue
            if primary_j is None:   # 親がハンガリアン法で対応しなかった -> 最大の子が親のIDを継承
                primary_j = max(children, key=lambda c: dets[c].area)
                det_to_track[primary_j] = i
                heirs.add(primary_j)
            split_parents.add(i)
            for c in children:
                if c != primary_j:
                    split_map[c] = i

        # ---- 4b) 面積ゲートの緩和: 位置がぴったり合う残り同士を、面積比 AREA_RELAX_RATIO までつなぐ ----
        # 合体/分裂の判定 (3, 4) の後に、どちらにも使われなかったトラックと検出だけで行うので、その判定は変えない。
        # 互いに唯一の候補で、ほかのトラックの予測マスク/ほかの検出が重なっていない (合体・分裂かもしれない) 組だけ
        relaxed = set()
        if AREA_RELAX_RATIO > AREA_RATIO_GATE:
            busy_t = set(det_to_track.values()) | absorbed_t
            free_t = [i for i in range(n_t) if i not in busy_t and id(active[i]) not in restored_hosts
                      and active[i].merge_frame < 0]   # 合体直後 (接触復帰の受付中) の塊は対象外
            free_d = [j for j in range(n_d) if j not in det_to_track and j not in split_map and j not in restored]
            pairs = [(i, j) for i in free_t for j in free_d if _relax_tight(active[i], dets[j], frame_idx)]
            n_pi = defaultdict(int)
            n_pj = defaultdict(int)
            for i, j in pairs:
                n_pi[i] += 1
                n_pj[j] += 1

            def predicted(o: Track) -> List[Tuple[Shape, float, float]]:
                k = max(1, frame_idx - o.last_frame)
                return [(shift_shape(o.shape, hx, hy), o.cx + hx, o.cy + hy) for hx, hy in o.motion_hypotheses(k)]

            def overlaps(s: Shape, sx: float, sy: float, s_area: float, d: Detection) -> bool:
                """合体/分裂の候補と同じ基準: 重なりが小さい側の面積の EVENT_OVERLAP_MIN 以上か、
                どちらかの中心が相手 (EVENT_MARGIN だけ膨らませる) の中"""
                if overlap_px(s, d.shape) >= EVENT_OVERLAP_MIN * min(s_area, d.area):
                    return True
                if _near_bbox(s, d.cx, d.cy, EVENT_MARGIN) and point_in_shape(dilate_shape(s, EVENT_MARGIN), d.cx, d.cy):
                    return True
                return (_near_bbox(d.shape, sx, sy, EVENT_MARGIN)
                        and point_in_shape(dilate_shape(d.shape, EVENT_MARGIN), sx, sy))

            for i, j in pairs:
                if n_pi[i] != 1 or n_pj[j] != 1:
                    continue
                t, d = active[i], dets[j]
                if any(overlaps(s, sx, sy, o.area, d) for ii, o in enumerate(active) if ii != i
                       for s, sx, sy in predicted(o)):
                    continue   # 別のトラックもこの検出に重なる (合体かもしれない)
                if any(overlaps(s, sx, sy, t.area, dd) for jj, dd in enumerate(dets) if jj != j
                       for s, sx, sy in predicted(t)):
                    continue   # 別の検出もこのトラックの予測マスクに重なる (分裂かもしれない)
                det_to_track[j] = i
                relaxed.add(j)
            self.relaxed_links += len(relaxed)

        # ---- 5) 結果の記録・トラック更新 ----
        frame_rows: List[dict] = []

        def row_of(t, j, event, parent_ids, hold_v=False):
            return {"det_index": det_ids[j], "track_id": t.track_id, "event": event,
                    "parent_ids": parent_ids, "leading_x": t.leading_x, "leading_y": t.leading_y,
                    "cx": t.cx, "cy": t.cy, "area": t.area, "vy": t.vy, "hold_v": hold_v}

        for j, i in det_to_track.items():
            t = active[i]
            d = dets[j]
            absorbed = merge_map.get(j, [])
            # 合体/分裂の直後・接触から戻った直後は、塊の重心の動きが気泡自身の動きではないので速度更新を保留
            # 面積ゲートの緩和でつないだときも、輪郭の取り方が変わっただけで重心の動きは気泡の動きではないので保留
            hold_v = (bool(absorbed) or j in heirs or i in split_parents or id(t) in hosts_with_restore
                      or j in relaxed)
            if id(t) in hosts_with_restore and t.pre_merge is not None:
                t.vx, t.vy, t.v_known = t.pre_merge.vx, t.pre_merge.vy, t.pre_merge.v_known
            if absorbed and TRANSIENT_MERGE_FRAMES > 0:
                t.pre_merge = replace(t, dormant=[], pre_merge=None, merge_frame=-1,
                                      parent_ids=list(t.parent_ids))
                t.dormant = []
                for k in absorbed:
                    active[k].clear_transient()
                    t.dormant.append(active[k])
                t.merge_frame = frame_idx
            t.observe(d, frame_idx, hold_v)
            frame_rows.append(row_of(t, j, "merge" if absorbed else "normal",
                                     [active[k].track_id for k in absorbed], hold_v))

        restored_host_idx = set()
        for j, (snap, h) in restored.items():
            d = dets[j]
            if id(h) in restored_hosts and snap is h.pre_merge:   # ホスト自身が元の気泡に戻った
                h.vx, h.vy, h.v_known = snap.vx, snap.vy, snap.v_known
                h.observe(d, frame_idx, hold_v=True)
                restored_host_idx.add(next(i for i, t in enumerate(active) if t is h))
                frame_rows.append(row_of(h, j, "normal", [], True))
            else:                     # 吸収されていた気泡が分かれ直した -> 元のIDで復帰
                h.dormant = [m for m in h.dormant if m is not snap]
                snap.observe(d, frame_idx)
                self.tracks.append(snap)
                self.restores.append((h.merge_frame, frame_idx, h.track_id, snap.track_id))
                frame_rows.append(row_of(snap, j, "split", [h.track_id]))
        for _, h in restored.values():
            if not h.dormant:
                h.clear_transient()

        merged_away_ids = set()
        for j, absorbed in merge_map.items():
            primary_id = active[det_to_track[j]].track_id
            for i in absorbed:
                t = active[i]
                merged_away_ids.add(t.track_id)
                frame_rows.append({
                    "det_index": None, "track_id": t.track_id, "event": f"merged_into_{primary_id}",
                    "parent_ids": [], "leading_x": t.leading_x, "leading_y": t.leading_y,
                    "cx": t.cx, "cy": t.cy, "area": 0.0, "vy": float("nan"),
                })

        for j, i in split_map.items():
            parent = active[i]
            d = dets[j]
            pvx, pvy = (parent.vx, parent.vy) if parent.v_known else (parent.prior_vx, parent.prior_vy)
            new_track = Track(
                track_id=self._new_id(), leading_x=d.leading_x, leading_y=d.leading_y,
                cx=d.cx, cy=d.cy, area=d.area, shape=d.shape, touch=d.touch,
                prior_vx=pvx, prior_vy=pvy,
                hits=1, time_since_update=0, first_frame=frame_idx, last_frame=frame_idx,
                parent_ids=[parent.track_id],
            )
            self.tracks.append(new_track)
            frame_rows.append(row_of(new_track, j, "split", [parent.track_id]))

        # 周りで追跡中の「動いている」気泡の速度 (今フレームで対応が取れ、3回以上観測されたトラック)。
        # 静止した気泡が大半の視野では全体の中央値が 0 になり、速い気泡の初速度推定に使えないため
        movers = [(t.cx, t.cy, t.vx, t.vy, t.area) for t in self.tracks
                  if t.v_known and t.last_frame == frame_idx and t.hits >= 3
                  and math.hypot(t.vx, t.vy) >= POS_GATE]

        def flow_prior(x, y, area):
            if not USE_FLOW_PRIOR or not movers:
                return 0.0, 0.0
            if PRIOR_AREA_RATIO > 0:   # 大きさの近い周りの気泡だけ。いなければ 0
                near = [m for m in movers if math.hypot(m[0] - x, m[1] - y) <= FLOW_PRIOR_RADIUS
                        and max(m[4], area) / max(1.0, min(m[4], area)) <= PRIOR_AREA_RATIO]
                if not near:
                    return 0.0, 0.0
            else:                      # 旧動作: 大きさを問わず、周りにいなければ画面全体
                near = [m for m in movers if math.hypot(m[0] - x, m[1] - y) <= FLOW_PRIOR_RADIUS] or movers
            return float(np.median([m[2] for m in near])), float(np.median([m[3] for m in near]))

        def initial_velocity(d):
            """新しく現れた気泡の初速度: 同じ大きさ区分の PIV 速度場 -> 大きさの近い周りの気泡の速度 -> 0"""
            if piv:
                fld = piv.get(piv_field.size_class(d.area, PIV_SIZE_CLASSES))
                if fld is not None:
                    pdy, pdx, ok = fld.sample(d.cx, d.cy)
                    if ok:
                        self.prior_counts["piv"] += 1
                        return (pdx if PIV_USE_DX else 0.0), pdy, "piv"
            pvx, pvy = flow_prior(d.cx, d.cy, d.area)
            self.prior_counts["flow" if (pvx or pvy) else "zero"] += 1
            return pvx, pvy, ""

        claimed_d = set(det_to_track) | set(split_map) | set(restored)
        for j, d in enumerate(dets):
            if j in claimed_d:
                continue
            pvx, pvy, src = initial_velocity(d)
            new_track = Track(
                track_id=self._new_id(), leading_x=d.leading_x, leading_y=d.leading_y,
                cx=d.cx, cy=d.cy, area=d.area, shape=d.shape, touch=d.touch,
                prior_vx=pvx, prior_vy=pvy, prior_src=src,
                hits=1, time_since_update=0, first_frame=frame_idx, last_frame=frame_idx,
            )
            self.tracks.append(new_track)
            frame_rows.append(row_of(new_track, j, "new", []))

        consumed_t = set(det_to_track.values()) | absorbed_t | restored_host_idx
        for i in range(n_t):
            if i not in consumed_t:
                active[i].time_since_update += 1
        for t in self.tracks:   # 接触復帰の受付期間が過ぎた合体は確定 (吸収されたトラックを破棄)
            if t.merge_frame >= 0 and frame_idx - t.merge_frame >= TRANSIENT_MERGE_FRAMES:
                t.clear_transient()

        self.tracks = [
            t for t in self.tracks
            if t.track_id not in merged_away_ids and t.time_since_update <= MAX_AGE
        ]
        return frame_rows


def suppress_transient_merges(rows_by_frame: Dict[int, List[dict]], restores) -> int:
    """「合体 -> TRANSIENT_MERGE_FRAMES 以内に元の気泡へ分かれ直した」組を接触として書き換える。
    合体/分裂のイベントを消し、吸収されていた気泡は その間だけ見えなかった (一時的な見失い) 扱いにする。
    塊になっていた間のホストの行は速度更新を保留する。戻り値: 書き換えた組の数"""
    for f1, f2, host_id, member_id in restores:
        rows1 = rows_by_frame.get(f1, [])
        for r in rows1:
            if r["track_id"] == host_id and r["det_index"] is not None and member_id in r["parent_ids"]:
                r["parent_ids"] = [p for p in r["parent_ids"] if p != member_id]
                if not r["parent_ids"] and r["event"] == "merge":
                    r["event"] = "normal"
        rows_by_frame[f1] = [r for r in rows1
                             if not (r["track_id"] == member_id and r["event"] == f"merged_into_{host_id}")]
        for r in rows_by_frame.get(f2, []):
            if r["track_id"] == member_id and r["event"] == "split":
                r["event"], r["parent_ids"] = "normal", []
        for f in range(f1, f2 + 1):
            for r in rows_by_frame.get(f, []):
                if r["track_id"] == host_id and r["det_index"] is not None:
                    r["hold_v"] = True
    return len(restores)


def infer_image_size(detections_per_frame: List[List[Detection]]) -> Optional[Tuple[int, int]]:
    """画像サイズが渡されないときの推定: 下端/右端に接する検出の端、なければ検出の外接矩形の最大"""
    H = W = 0
    Hs, Ws = [], []
    for dets in detections_per_frame:
        for d in dets:
            m, x0, y0 = d.shape
            y1, x1 = y0 + m.shape[0], x0 + m.shape[1]
            H, W = max(H, y1), max(W, x1)
            if d.touch[1]:
                Hs.append(y1)
            if d.touch[3]:
                Ws.append(x1)
    if not H:
        return None
    return (max(Hs) if Hs else H, max(Ws) if Ws else W)


def piv_settings():
    """tracker3 の設定から piv_field の設定を作る"""
    kw = dict(size_bounds=tuple(PIV_SIZE_CLASSES), windows=dict(PIV_WINDOWS), raster=PIV_RASTER,
              min_area=MIN_TRACK_AREA)
    return piv_field.PIVSettings.faithful(**kw) if PIV_MODE == "faithful" else piv_field.PIVSettings(**kw)


class _LazyFields:
    """{区分: DisplacementField or None} を、その区分が初めて必要になったときに計算する
    (新しく現れた気泡がない区分は計算しない)"""

    def __init__(self, seq, f):
        self.seq, self.f, self._d = seq, f, {}

    def get(self, c):
        if c not in self._d:
            self._d[c] = self.seq.field(self.f, c)
        return self._d[c]

    def __bool__(self):
        return True


class PIVSequence:
    """フレームの組 (t, t+1) ごとの大きさ区分別の速度場。各フレームの画像は1回だけ作る"""

    def __init__(self, detections_per_frame, image_size):
        self.dets = detections_per_frame
        self.hw = image_size
        self.s = piv_settings()
        self._raster = {}
        self.time_s = 0.0
        self.n_fields = 0

    def _r(self, f):
        if f not in self._raster:
            self._raster = {k: v for k, v in self._raster.items() if k >= f - 1}   # 古いフレームは捨てる
            self._raster[f] = piv_field.rasterize(self.dets[f], self.hw, self.s)
        return self._raster[f]

    def field(self, f, c):
        """フレーム f -> f+1、区分 c の速度場 (どちらかのフレームにその区分の気泡がなければ None)"""
        t0 = time.perf_counter()
        a, b = self._r(f)[c], self._r(f + 1)[c]
        out = piv_field.DisplacementField(a, b, *self.s.windows[c], s=self.s) if a.any() and b.any() else None
        self.time_s += time.perf_counter() - t0
        self.n_fields += 1
        return out

    def fields(self, f):
        """フレーム f -> f+1 の速度場 (区分ごとに必要になったとき計算)。最後のフレームなら None"""
        if f + 1 >= len(self.dets):
            return None
        return _LazyFields(self, f)


def make_piv_sequence(detections_per_frame, image_size=None) -> Optional[PIVSequence]:
    """USE_PIV_PRIOR が有効で piv_field.py が読み込めれば PIVSequence、そうでなければ None"""
    if not USE_PIV_PRIOR:
        return None
    if piv_field is None:
        print("  ※ piv_field.py が見つからないため PIV による初速度推定を使いません (同じフォルダに置いてください)")
        return None
    hw = image_size or infer_image_size(detections_per_frame)
    if hw is None:
        return None
    return PIVSequence(detections_per_frame, tuple(int(v) for v in hw))


def run_laptrack(detections_per_frame: List[List[Detection]], image_size=None,
                 piv_debug_dir: Optional[str] = None) -> Dict[int, List[dict]]:
    """image_size = (高さ, 幅)。PIV の画像を作るのに使う (None なら検出から推定)"""
    tracker = LeadingEdgeLapTracker()
    seq = make_piv_sequence(detections_per_frame, image_size)
    rows_by_frame: Dict[int, List[dict]] = {}
    t_track = 0.0
    for frame_idx, dets in enumerate(detections_per_frame):
        piv = seq.fields(frame_idx) if seq is not None else None
        if piv is not None and piv_debug_dir:
            save_piv_debug(piv_debug_dir, frame_idx, piv, seq)
        t0, p0 = time.perf_counter(), (seq.time_s if seq is not None else 0.0)
        rows_by_frame[frame_idx] = tracker.update(dets, frame_idx, piv)
        t_track += time.perf_counter() - t0 - ((seq.time_s - p0) if seq is not None else 0.0)   # PIV の分は除く
    n = suppress_transient_merges(rows_by_frame, tracker.restores)
    if n:
        print(f"  合体直後に分かれ直した {n} 組を「接触」として元のIDに戻しました")
    if tracker.relaxed_links:
        print(f"  位置がぴったり合うので面積比 {AREA_RATIO_GATE}〜{AREA_RELAX_RATIO} でもつないだ対応: {tracker.relaxed_links}件")
    nf = max(1, len(detections_per_frame))
    pc = tracker.prior_counts
    if seq is not None:
        print(f"  新規トラックの初速度: PIV {pc['piv']}件 / 周りの気泡 {pc['flow']}件 / 0 {pc['zero']}件")
        print(f"  計算時間: PIV {1000 * seq.time_s / nf:.0f} ms/フレーム (区分ごとの速度場 {seq.n_fields}個), "
              f"対応付け {1000 * t_track / nf:.0f} ms/フレーム")
    run_laptrack.last_stats = {"prior_counts": dict(pc), "piv_ms_per_frame": 1000 * seq.time_s / nf if seq else 0.0,
                               "piv_fields": seq.n_fields if seq else 0, "track_ms_per_frame": 1000 * t_track / nf,
                               "relaxed_links": tracker.relaxed_links}
    return rows_by_frame


def save_piv_debug(out_dir: str, frame_idx: int, piv, seq: PIVSequence):
    """速度場のベクトル図 (区分ごとに横に並べる)。黄 = 実測, 赤 = 周りから補間"""
    os.makedirs(out_dir, exist_ok=True)
    panels = []
    for c in piv_field.CLASS_NAMES:
        base = seq._r(frame_idx)[c]
        fld = piv.get(c)
        img = piv_field.draw(base, fld) if fld is not None else cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)
        cv2.putText(img, c, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        panels.append(np.pad(img, ((0, 0), (0, 6), (0, 0)), constant_values=255))
    cv2.imwrite(os.path.join(out_dir, f"piv_{frame_idx:05d}.png"), np.hstack(panels))


# ==============================================================
# 6. 速度計算(EMA)
# ==============================================================
def compute_velocity_ema(rows_by_frame: Dict[int, List[dict]], total_frames: int) -> Dict[int, List[dict]]:
    track_history: Dict[int, List[Tuple[int, dict]]] = defaultdict(list)
    for f in range(total_frames):
        for row in rows_by_frame.get(f, []):
            if row["det_index"] is None:
                continue
            track_history[row["track_id"]].append((f, row))

    for track_id, hist in track_history.items():
        hist.sort(key=lambda x: x[0])
        prev_vy = None       # 旧版は 0 から始めていたため、最初の数フレームの速度が小さく出ていた
        prev_leading_y = None
        prev_frame = None
        for f, row in hist:
            if prev_leading_y is None:
                row["vy"] = float("nan")
            elif row["event"] in ("merge", "split") or row.get("hold_v"):
                row["vy"] = prev_vy if prev_vy is not None else float("nan")  # 合体/分裂直後は速度更新を保留
            else:
                dt = max(f - prev_frame, 1)
                raw_v = (row["leading_y"] - prev_leading_y) / dt
                row["vy"] = raw_v if prev_vy is None else VELOCITY_EMA_ALPHA * prev_vy + (1 - VELOCITY_EMA_ALPHA) * raw_v
            if row["vy"] == row["vy"]:
                prev_vy = row["vy"]
            prev_leading_y = row["leading_y"]
            prev_frame = f
    return rows_by_frame


# ==============================================================
# 7. QCレポート (今回の実行結果の健全性チェック用)
# ==============================================================
def qc_report(rows_by_frame: Dict[int, List[dict]], total_frames: int) -> dict:
    track_history: Dict[int, List[Tuple[int, dict]]] = defaultdict(list)
    for f in range(total_frames):
        for row in rows_by_frame.get(f, []):
            if row["det_index"] is None:
                continue
            track_history[row["track_id"]].append((f, row))

    num_tracks = len(track_history)
    lengths = [len(h) for h in track_history.values()]
    avg_track_length = float(np.mean(lengths)) if lengths else 0.0
    all_rows = [r for f in range(total_frames) for r in rows_by_frame.get(f, [])]
    return {
        "num_tracks": num_tracks,
        "avg_track_length_frames": round(avg_track_length, 2),
        "merge_events": sum(1 for r in all_rows if r["event"] == "merge"),
        "split_events": sum(1 for r in all_rows if r["event"] == "split"),
        "new_events": sum(1 for r in all_rows if r["event"] == "new"),
    }


# ==============================================================
# 8. 出力(CSV / オーバーレイ画像)
# ==============================================================
EVENT_COLORS = {
    "normal": (0, 255, 0), "new": (0, 255, 255),
    "merge": (0, 128, 255), "split": (255, 128, 0),
}


def write_tracking_csv(csv_path: str, rows_by_frame: Dict[int, List[dict]], filenames: List[str],
                        detections_per_frame: List[List[Detection]]):
    """トラッキング専用CSV: 気泡ごとのID/イベント/位置/速度。
    列は microgaptracker3.py と同じ順で、末尾に 周長(px)・フレーム接触 を追加。"""
    out_dir = os.path.dirname(csv_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["ファイル名", "フレーム", "トラックID", "イベント", "親トラックID",
                    "面積(px)", "ROI内面積(px)", "先端部X", "先端部Y", "中心X", "中心Y",
                    "上昇速度(px/frame)", "周長(px)", "フレーム接触"])
        for frame_idx, filename in enumerate(filenames):
            rows = rows_by_frame.get(frame_idx, [])
            dets = detections_per_frame[frame_idx] if frame_idx < len(detections_per_frame) else []
            if rows:
                for row in rows:
                    vy = row["vy"]
                    vy_str = "" if vy != vy else f"{vy:.3f}"
                    parent_str = ";".join(str(p) for p in row["parent_ids"])
                    di = row["det_index"]
                    roi_area_str = per_str = touch_str = ""
                    if di is not None and di < len(dets):
                        roi_area_str = f"{dets[di].area_in_roi:.0f}"
                        per_str = f"{dets[di].perimeter:.1f}"
                        touch_str = "1" if dets[di].touches_frame else "0"
                    w.writerow([filename, frame_idx, row["track_id"], row["event"], parent_str,
                                row["area"], roi_area_str,
                                f"{row['leading_x']:.2f}", f"{row['leading_y']:.2f}",
                                f"{row['cx']:.2f}", f"{row['cy']:.2f}", vy_str, per_str, touch_str])
            else:
                w.writerow([filename, frame_idx, "", "気泡なし", "", 0, "", "", "", "", "", "", "", ""])


def write_area_count_csv(csv_path: str, filenames: List[str],
                          total_areas: List[float], roi_counts: List[int]):
    """面積・個数専用CSV: フレームごとのROI内気泡数と合計面積。"""
    out_dir = os.path.dirname(csv_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(["ファイル名", "フレーム", "ROI内気泡数", "ROI内合計面積(px)"])
        for frame_idx, filename in enumerate(filenames):
            w.writerow([filename, frame_idx, roi_counts[frame_idx], total_areas[frame_idx]])


def _draw_detection(img, det, color, label=None, thickness=2):
    cv2.drawContours(img, det.contours, -1, color, thickness)   # 輪郭は成分ごとに別々に描く(直線で繋がない)
    cv2.circle(img, (int(det.leading_x), int(det.leading_y)), 4, (0, 0, 255), -1)
    if label:
        cv2.putText(img, label, (int(det.leading_x), max(0, int(det.leading_y) - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def draw_overlays(cache_dir: str, output_dir: str, rows_by_frame: Dict[int, List[dict]],
                   detections_per_frame: List[List[Detection]], filenames: List[str],
                   total_areas: List[float], roi_counts: List[int], roi_rect=None):
    os.makedirs(output_dir, exist_ok=True)
    for frame_idx, filename in enumerate(filenames):
        img = cv2.imread(os.path.join(cache_dir, filename))
        if img is None:
            continue

        if roi_rect is not None:   # ROI矩形 (マゼンタ)
            rx, ry, rw2, rh2 = roi_rect
            cv2.rectangle(img, (rx, ry), (rx + rw2, ry + rh2), (255, 0, 255), 2)

        row_by_det_index = {r["det_index"]: r for r in rows_by_frame.get(frame_idx, []) if r["det_index"] is not None}
        for idx, det in enumerate(detections_per_frame[frame_idx]):
            row = row_by_det_index.get(idx)
            event = row["event"] if row else "normal"
            color = EVENT_COLORS.get(event, (0, 255, 0))
            if not det.in_roi:   # ROI外の気泡はグレーの細線 (検出はされるが統計には含まれない)
                cv2.drawContours(img, det.contours, -1, (128, 128, 128), 1)
                continue
            label = f"ID{row['track_id']} {int(det.area_in_roi)}px" if row else None
            _draw_detection(img, det, color, label)

        cv2.putText(img, f"ROI Area: {total_areas[frame_idx]:.0f} px  Count: {roi_counts[frame_idx]}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.imwrite(os.path.join(output_dir, filename), img)


# ==============================================================
# 9. 自動ブートストラップキャリブレーション
# ==============================================================
BOOTSTRAP_PARAM_NAMES = ("MAX_SPEED", "POS_GATE", "AREA_RATIO_GATE", "PIV_GATE")


def _bootstrap_confident_pairs(dets_a: List[Detection], dets_b: List[Detection]) -> Dict[int, int]:
    """隣接フレーム間の「確実な」対応だけを返す (統計用)。{a の番号: b の番号}
    コスト = 距離/探索半径 + (1 - 形状IoU) + |log 面積比| で、相互に1番手 かつ
    2番手と明確に差がある (1番手 < 2番手 × BOOTSTRAP_RATIO_TEST) ペアだけを採用する。
    tracker2 は形状(IoU)最優先の全体最適だったため、形がどれも似ている小さい気泡では
    でたらめな対応が統計に混ざっていた。"""
    n_a, n_b = len(dets_a), len(dets_b)
    if not n_a or not n_b:
        return {}
    cost = np.full((n_a, n_b), np.inf)
    for i, a in enumerate(dets_a):
        if a.area < MIN_TRACK_AREA:
            continue
        for j, b in enumerate(dets_b):
            if b.area < MIN_TRACK_AREA:
                continue
            ar = max(a.area, b.area) / max(1.0, min(a.area, b.area))
            if ar > BOOTSTRAP_LOOSE_AREA_GATE:
                continue
            dx, dy, _ = displacement(a, b)
            dist = math.hypot(dx, dy)
            if dist > BOOTSTRAP_LOOSE_GATE:
                continue
            iou = compute_motion_compensated_iou(a.shape, b.shape, b.cx - a.cx, b.cy - a.cy)
            cost[i, j] = dist / BOOTSTRAP_LOOSE_GATE + (1.0 - iou) + math.log(ar)
    pairs = {}
    for i in range(n_a):
        if not np.isfinite(cost[i]).any():
            continue
        j = int(np.argmin(cost[i]))
        if int(np.argmin(cost[:, j])) != i:
            continue   # 相互に1番手でない
        second = min(np.partition(cost[i], 1)[1] if n_b > 1 else np.inf,
                     np.partition(cost[:, j], 1)[1] if n_a > 1 else np.inf)
        if np.isfinite(second) and cost[i, j] > BOOTSTRAP_RATIO_TEST * second:
            continue   # 2番手と紛らわしい
        pairs[i] = j
    return pairs


def _bootstrap_collect_stats(detections_per_frame: List[List[Detection]], image_size=None):
    """映像全体から均等に抽出した隣接フレームで確実な対応だけを集め、
      speed_list      : 1フレームの移動量 |d|            -> MAX_SPEED (速度未知のトラックの探索半径)
      resid_list      : 3フレーム連続の対応で「前フレームと同じ速度」と仮定した予測からのずれ
                        (等価直径に比例する分 POS_GATE_SIZE_FRAC × 直径 を差し引いたもの) -> POS_GATE
      area_ratio_list : 面積比                             -> AREA_RATIO_GATE
      piv_resid_list  : PIV 速度場 (同じ大きさ区分) で予測した位置からのずれ (同じく直径分を差し引く) -> PIV_GATE
                        (USE_PIV_PRIOR のときだけ。速度場が有効な場所の気泡だけ)
    を返す。静止した気泡が大半でも、少数の速い気泡の移動量が MAX_SPEED に反映されるよう高いパーセンタイルを使う。"""
    total_frames = len(detections_per_frame)
    quality = {"pairs": 0, "chains": 0, "match_fail_rate": 0.0}
    if total_frames < 2:
        return [], [], [], quality, []
    seq = make_piv_sequence(detections_per_frame, image_size)
    piv_resid_list = []

    n_seg = min(BOOTSTRAP_NUM_SEGMENTS, total_frames - 1)
    sample_frames = sorted(set(
        int(round(k * (total_frames - 2) / max(1, n_seg - 1))) for k in range(n_seg)
    ))

    cache: Dict[int, Dict[int, int]] = {}

    def pairs_of(f):
        if f not in cache:
            cache[f] = _bootstrap_confident_pairs(detections_per_frame[f], detections_per_frame[f + 1])
        return cache[f]

    speed_list, resid_list, area_ratio_list = [], [], []
    total_candidates = 0
    for f in sample_frames:
        A, B = detections_per_frame[f], detections_per_frame[f + 1]
        p = pairs_of(f)
        total_candidates += sum(1 for a in A if a.area >= MIN_TRACK_AREA)
        fields = seq.fields(f) if (seq is not None and p) else None
        for i, j in p.items():
            a, b = A[i], B[j]
            dx, dy, _ = displacement(a, b)
            speed_list.append(math.hypot(dx, dy))
            area_ratio_list.append(max(a.area, b.area) / max(1.0, min(a.area, b.area)))
            fld = fields.get(piv_field.size_class(a.area, PIV_SIZE_CLASSES)) if fields else None
            if fld is not None:
                pdy, pdx, ok = fld.sample(a.cx, a.cy)
                if ok:
                    res = math.hypot(dx - (pdx if PIV_USE_DX else 0.0), dy - pdy)
                    piv_resid_list.append(max(0.0, res - POS_GATE_SIZE_FRAC * eq_diameter(a.area)))
        if f + 2 < total_frames:
            p2 = pairs_of(f + 1)
            C = detections_per_frame[f + 2]
            for i, j in p.items():
                if j not in p2:
                    continue
                a, b, c = A[i], B[j], C[p2[j]]
                dx1, dy1, _ = displacement(a, b)
                dx2, dy2, _ = displacement(b, c)
                res = math.hypot(dx2 - dx1, dy2 - dy1)
                resid_list.append(max(0.0, res - POS_GATE_SIZE_FRAC * eq_diameter(b.area)))

    quality = {
        "pairs": len(speed_list),
        "chains": len(resid_list),
        "match_fail_rate": (1.0 - len(speed_list) / total_candidates) if total_candidates else 0.0,
    }
    return speed_list, resid_list, area_ratio_list, quality, piv_resid_list


def _bootstrap_compute_params(speed_list, resid_list, area_ratio_list, piv_resid_list=None):
    """収集した分布からゲートパラメータを算出する(パーセンタイル × 安全係数)。
    PIV_GATE は POS_GATE 〜 MAX_SPEED の範囲 (PIV の予測は速度既知のトラックの予測より粗いので POS_GATE より狭くしない)"""
    if not speed_list:
        return None
    if len(resid_list) >= 10:
        pos_gate = max(BOOTSTRAP_MIN_JUMP,
                       float(np.percentile(resid_list, BOOTSTRAP_RESID_PERCENTILE)) * BOOTSTRAP_JUMP_MARGIN)
    else:   # 3フレーム連続の対応が少なすぎる -> 現在値を維持
        pos_gate = POS_GATE
    max_speed = max(2.0 * pos_gate,
                    float(np.percentile(speed_list, BOOTSTRAP_SPEED_PERCENTILE)) * BOOTSTRAP_JUMP_MARGIN)
    area_gate = float(np.percentile(area_ratio_list, BOOTSTRAP_AREA_PERCENTILE)) * BOOTSTRAP_AREA_MARGIN
    if piv_resid_list is not None and len(piv_resid_list) >= 10:
        piv_gate = float(np.percentile(piv_resid_list, BOOTSTRAP_RESID_PERCENTILE)) * BOOTSTRAP_JUMP_MARGIN
        piv_gate = min(max(piv_gate, pos_gate), max_speed)
    else:   # PIV を使わない / 有効な場所の対応が少なすぎる -> 現在値を維持
        piv_gate = PIV_GATE
    return {
        "MAX_SPEED": round(max_speed, 1),
        "POS_GATE": round(pos_gate, 1),
        "AREA_RATIO_GATE": round(min(3.0, max(1.3, area_gate)), 2),
        "PIV_GATE": round(piv_gate, 1),
    }


def _apply_params(params: dict):
    global MAX_SPEED, POS_GATE, AREA_RATIO_GATE, PIV_GATE
    MAX_SPEED = params["MAX_SPEED"]
    POS_GATE = params["POS_GATE"]
    AREA_RATIO_GATE = params["AREA_RATIO_GATE"]
    PIV_GATE = params.get("PIV_GATE", PIV_GATE)


def _current_params() -> dict:
    return {"MAX_SPEED": MAX_SPEED, "POS_GATE": POS_GATE, "AREA_RATIO_GATE": AREA_RATIO_GATE, "PIV_GATE": PIV_GATE}


def _bootstrap_preview_overlays(detections_per_frame, filenames, cache_dir, auto_params, image_size=None):
    """自動パラメータでサンプル区間を実際にトラッキングし、オーバーレイ画像数枚を返す。"""
    saved = _current_params()
    _apply_params(auto_params)
    seq = make_piv_sequence(detections_per_frame, image_size)

    total_frames = len(detections_per_frame)
    start = max(0, total_frames // 2 - BOOTSTRAP_PREVIEW_FRAMES // 2)
    preview_range = list(range(start, min(total_frames, start + BOOTSTRAP_PREVIEW_FRAMES)))

    try:
        tracker = LeadingEdgeLapTracker()
        overlays = []
        warmup_start = max(0, start - 3)   # 少し手前からウォームアップしてIDを安定させる
        for f in range(warmup_start, min(total_frames, start + BOOTSTRAP_PREVIEW_FRAMES)):
            rows = tracker.update(detections_per_frame[f], f, seq.fields(f) if seq is not None else None)
            if f not in preview_range:
                continue
            img = cv2.imread(os.path.join(cache_dir, filenames[f]))
            if img is None:
                continue
            row_by_det = {r["det_index"]: r for r in rows if r["det_index"] is not None}
            for idx, det in enumerate(detections_per_frame[f]):
                row = row_by_det.get(idx)
                event = row["event"] if row else "normal"
                _draw_detection(img, det, EVENT_COLORS.get(event, (0, 255, 0)),
                                f"ID{row['track_id']}" if row else None)
            cv2.putText(img, f"frame {f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            overlays.append((f, img))
        return overlays
    finally:
        _apply_params(saved)


def _bootstrap_show_approval_window(speed_list, resid_list, area_ratio_list, auto_params, quality, overlays,
                                    piv_resid_list=None):
    """ヒストグラム + サンプルオーバーレイを一つのウィンドウにまとめて表示する。
    matplotlibがない、またはGUIが使えない環境ではコンソール出力にフォールバックする。"""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("  [bootstrap] matplotlibを読み込めないためグラフプレビューをスキップします(コンソール値のみ表示)。")
        return

    specs = [
        ("Displacement per frame |d| (MAX_SPEED)", speed_list, auto_params["MAX_SPEED"]),
        ("Prediction residual (POS_GATE)", resid_list, auto_params["POS_GATE"]),
        ("Area ratio", area_ratio_list, auto_params["AREA_RATIO_GATE"]),
    ]
    if piv_resid_list:
        specs.append(("PIV prediction residual (PIV_GATE)", piv_resid_list, auto_params["PIV_GATE"]))
    n_rows = len(specs)
    fig = plt.figure(figsize=(19, 10))
    fig.suptitle("Bootstrap Calibration - Review (close window to continue)", fontsize=14)
    gs = fig.add_gridspec(n_rows, 3, width_ratios=[0.7, 1.4, 1.4], hspace=0.6, wspace=0.15)
    for k, (title, data, cutoff) in enumerate(specs):
        ax = fig.add_subplot(gs[k, 0])
        if data:
            ax.hist(data, bins=30, color="#5B8FF9", edgecolor="white")
            ax.axvline(cutoff, color="#E24B4A", linestyle="--", linewidth=2, label=f"gate = {cutoff}")
            ax.legend(fontsize=9)
            if k != 2:
                ax.set_yscale("log")   # 静止気泡が大半でも速い気泡の山が見えるように
        ax.set_title(title, fontsize=10)
        ax.tick_params(labelsize=8)

    sub = gs[0:n_rows, 1:3].subgridspec(2, 2, hspace=0.15, wspace=0.08)
    for k, (f_idx, img) in enumerate(overlays[:4]):
        ax = fig.add_subplot(sub[k // 2, k % 2])
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(f"frame {f_idx}", fontsize=11)
        ax.axis("off")

    q_txt = (f"pairs={quality['pairs']}   chains={quality['chains']}   "
             f"match fail={quality['match_fail_rate']*100:.0f}%")
    fig.text(0.05, 0.02, q_txt, fontsize=10, color="#444")

    print("  [bootstrap] 確認ウィンドウを表示しました。確認後ウィンドウを閉じるとコンソールで承認ステップに進みます。")
    plt.show()


def run_bootstrap_calibration(detections_per_frame, filenames, cache_dir, image_size=None):
    """統計収集 -> パラメータ算出 -> 確認ウィンドウ -> コンソール承認/修正 -> 確定パラメータをグローバルに反映。"""
    print("\n[ブートストラップ] 映像全体の均等サンプルから移動量/予測ずれ/面積比の統計を収集します...")
    speed_list, resid_list, area_ratio_list, quality, piv_resid_list = _bootstrap_collect_stats(
        detections_per_frame, image_size)
    auto_params = _bootstrap_compute_params(speed_list, resid_list, area_ratio_list, piv_resid_list)

    if auto_params is None:
        print("  [ブートストラップ] 有効なマッチングサンプルがないため自動算出をスキップします。現在の手動値を維持します。")
        return

    print(f"  確実な対応ペア: {quality['pairs']}個, 3フレーム連続: {quality['chains']}個, "
          f"対応なし率: {quality['match_fail_rate']*100:.0f}%")
    if piv_resid_list:
        print(f"  PIV 予測のずれ (直径分を除く): 中央値 {np.median(piv_resid_list):.1f}px, "
              f"95%値 {np.percentile(piv_resid_list, 95):.1f}px ({len(piv_resid_list)}個)")
    names = [n for n in BOOTSTRAP_PARAM_NAMES if n != "PIV_GATE" or USE_PIV_PRIOR]

    while True:
        current = _current_params()
        print("\n=== 自動ブートストラップ結果 ===")
        print(f"{'パラメータ':<26}{'現在の手動値':>12}{'自動計算値':>14}")
        for name in names:
            print(f"{name:<26}{current[name]:>12}{auto_params[name]:>14}")

        overlays = _bootstrap_preview_overlays(detections_per_frame, filenames, cache_dir, auto_params, image_size)
        _bootstrap_show_approval_window(speed_list, resid_list, area_ratio_list, auto_params, quality, overlays,
                                        piv_resid_list)

        choice = input("\n[Enter] 自動値を使用 / [m] 手動値を維持 / [e] 直接入力 / [r] プレビューを再表示: ").strip().lower()
        if choice == "":
            _apply_params(auto_params)
            print("  -> 自動値を適用しました。")
            break
        elif choice == "m":
            print("  -> 現在の手動値を維持します。")
            break
        elif choice == "e":
            try:
                vals = {}
                for name in names:
                    v = input(f"  {name} (Enter=自動 {auto_params[name]}): ").strip()
                    vals[name] = float(v) if v else auto_params[name]
                _apply_params(vals)
                print("  -> 入力値を適用しました。")
                break
            except ValueError:
                print("  -> 数値形式ではありません。もう一度お試しください。")
                continue
        elif choice == "r":
            continue
        else:
            print("  -> 不明な入力です。もう一度選択してください。")
            continue

    print(f"  [ブートストラップ] 確定ゲート: MAX_SPEED={MAX_SPEED}, "
          f"POS_GATE={POS_GATE}, AREA={AREA_RATIO_GATE}" + (f", PIV_GATE={PIV_GATE}" if USE_PIV_PRIOR else "") + "\n")


# ==============================================================
# 10. ROI
# ==============================================================
def _roi_save_path() -> str:
    return ROI_SAVE_PATH if ROI_SAVE_PATH else os.path.join(OUTPUT_FOLDER, "roi_saved.json")


def load_saved_roi():
    """保存済みROIがあれば(x, y, w, h)タプルで返す。なければ、または破損していればNone。"""
    path = _roi_save_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rect = data.get("roi_rect")
        if isinstance(rect, list) and len(rect) == 4:
            return tuple(int(v) for v in rect)
    except Exception as e:
        print(f"  [ROI] 保存ファイルを読み込めませんでした({e})。新規に選択します。")
    return None


def save_roi(rect):
    """選択したROIをファイルに保存し、次回実行時に再利用できるようにする。"""
    if rect is None:
        return
    path = _roi_save_path()
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"roi_rect": list(rect)}, f, ensure_ascii=False, indent=2)
    print(f"  [ROI] 選択領域を保存しました: {path}")


def resolve_roi(sample_img: np.ndarray):
    """ROI決定: コード固定値 -> 保存済みROIの再利用確認 -> マウス選択+保存"""
    if ROI_RECT is not None:
        print(f"  [ROI] コードに固定されたROI_RECTを使用: {ROI_RECT}")
        return tuple(ROI_RECT)

    saved = load_saved_roi()
    if saved is not None:
        x, y, rw, rh = saved
        choice = input(f"\n[ROI] 保存済みROIがあります: x={x}, y={y}, w={rw}, h={rh}\n"
                       f"      [Enter] 再利用 / [n] 新規選択: ").strip().lower()
        if choice != "n":
            print("  [ROI] 保存済みROIを再利用します。")
            return saved

    rect = select_roi_interactive(sample_img)
    save_roi(rect)
    return rect


def select_roi_interactive(sample_img: np.ndarray):
    """最初のフレームでマウスドラッグによりROIを選択。ENTER/SPACEで確定、cでキャンセル(画面全体)。"""
    print("\n[ROI] マウスで関心領域をドラッグしてからENTERまたはSPACEを押してください。(c=キャンセル、キャンセル時は画面全体)")
    rect = cv2.selectROI("Select ROI (ENTER=OK, c=cancel)", sample_img, showCrosshair=True)
    cv2.destroyWindow("Select ROI (ENTER=OK, c=cancel)")
    x, y, rw, rh = [int(v) for v in rect]
    if rw <= 0 or rh <= 0:
        print("  [ROI] 選択がキャンセルされたため画面全体をROIとして使用します。")
        return None
    print(f"  [ROI] 選択されました: x={x}, y={y}, w={rw}, h={rh}")
    print(f"  [ROI] 再現するにはコード上部で ROI_RECT = ({x}, {y}, {rw}, {rh}) と固定できます。")
    return (x, y, rw, rh)


def make_roi_mask(image_h: int, image_w: int, roi_rect):
    """ROI矩形を0/1マスクに変換。roi_rectがNoneなら画面全体。"""
    mask = np.zeros((image_h, image_w), dtype=np.uint8)
    if roi_rect is None:
        mask[:, :] = 1
        return mask
    x, y, rw, rh = roi_rect
    x2, y2 = min(image_w, x + rw), min(image_h, y + rh)
    x, y = max(0, x), max(0, y)
    mask[y:y2, x:x2] = 1
    return mask


# ==============================================================
# 11. 検出ステップ (前処理 -> U-Net)
# ==============================================================
def check_unet_input(gray, prob, inst, detector, filename):
    """最初のフレームで「U-Netに入る画像が学習画像と同じ種類か」を確認し、デバッグ画像を保存する。"""
    h, w = gray.shape
    black = float((gray < 15).mean())
    cover = float((inst > 0).mean())
    print(f"  [入力チェック] {filename}: サイズ {h}x{w}, 黒画素 {black:.0%}, 気泡判定の画素 {cover:.0%}")
    if black < MIN_BLACK_FRACTION:
        print("  !!! 警告: 前処理後の背景が黒くなっていません (学習画像は約94%が黒)。")
        print("      U-Netは「黒い背景 + 白い輪郭」の2値化画像で学習しているため、このままでは正しく検出できません。")
        print("      -> Noise Cut を上げる / 背景画像(BACKGROUND_PATH)が同じ撮影条件か確認 /")
        print("         学習画像を作ったときの値を PREPROC_FIXED に設定")
    if cover > 0.5:
        print("  !!! 警告: 画面の半分以上が気泡と判定されています。背景そのものを気泡と誤認している可能性が高いです。")
    if getattr(detector, "train_hw", None) is None:
        print("  ※ best.pt に学習画像サイズの記録がありません。学習画像とサイズが違う場合は TRAIN_IMAGE_HW を指定してください。")
    if SAVE_DEBUG_FIRST_FRAME:
        d = os.path.join(OUTPUT_FOLDER, "debug")
        os.makedirs(d, exist_ok=True)
        cv2.imwrite(os.path.join(d, "unet_input.png"), gray)                          # U-Netが実際に見た画像
        cv2.imwrite(os.path.join(d, "prob_in.png"), (prob[1] * 255).astype(np.uint8))  # 内部確率 (白=1)
        cv2.imwrite(os.path.join(d, "prob_edge.png"), (prob[2] * 255).astype(np.uint8))  # 境界確率 (白=1)
        print(f"  [入力チェック] U-Net入力と確率マップを保存: {d}")


def run_detection_phase(cache_dir: str):
    print("U-Netモデルをロード中...")
    detector = UNetDetector(UNET_CKPT, TRAIN_IMAGE_HW)

    bg_img = cv2.imread(BACKGROUND_PATH)
    if bg_img is None and ENABLE_PREPROCESSING:
        raise FileNotFoundError(f"背景画像が見つかりません: {BACKGROUND_PATH}")
    if not ENABLE_PREPROCESSING:
        print("  [前処理OFF] 元画像をそのままU-Netに入力します (2値化画像で学習したモデルには非推奨)。")

    image_files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff'):
        image_files.extend(glob.glob(os.path.join(IMAGE_FOLDER, ext)))
    image_files = sorted(set(image_files))
    image_files = [p for p in image_files if os.path.normcase(os.path.abspath(p))
                   != os.path.normcase(os.path.abspath(BACKGROUND_PATH))]
    if not image_files:
        raise FileNotFoundError(f"'{IMAGE_FOLDER}' フォルダに画像がありません。")

    print(f"合計{len(image_files)}枚の画像が見つかりました。検出ステップを開始します。\n")
    os.makedirs(cache_dir, exist_ok=True)
    inst_dir = os.path.join(OUTPUT_FOLDER, "instances")
    if SAVE_INSTANCE_MASKS:
        os.makedirs(inst_dir, exist_ok=True)
    prob_dir = os.path.join(OUTPUT_FOLDER, "prob")
    if SAVE_PROB_MAPS:
        os.makedirs(prob_dir, exist_ok=True)

    is_first = True
    thresh_val, bright_val, median_val = PREPROC_FIXED if PREPROC_FIXED else PREPROC_DEFAULT
    use_ui = ENABLE_PREPROCESSING and PREPROC_FIXED is None
    detections_per_frame: List[List[Detection]] = []
    filenames: List[str] = []
    total_areas: List[float] = []   # ROI使用時: ROI内面積の合計。未使用時: 全体面積の合計
    roi_counts: List[int] = []      # フレームごとのROIにかかった気泡数
    image_size = None
    roi_rect = ROI_RECT
    roi_bool = None

    for img_path in image_files:
        filename = os.path.basename(img_path)
        img, processed_img, thresh_val, bright_val, median_val = preprocess_image(
            img_path, bg_img, filename=filename, show_ui=(is_first and use_ui),
            current_thresh_val=thresh_val, current_bright_val=bright_val, current_median_val=median_val,
        )
        if img is None:
            print(f"  -> {filename}: 画像の読み込みに失敗、スキップ")
            continue
        if is_first:
            print(f"  -> 設定値: Noise={thresh_val}, Brightness={bright_val}, Median={median_val}")
            print(f"  -> 気泡の分け方: UNET_INSTANCE_MODE = \"{UNET_INSTANCE_MODE}\""
                  + (f" (芯の内部確率 > {UNET_SEED_THR})" if UNET_INSTANCE_MODE == "seed" else ""))
            if ENABLE_ROI and roi_rect is None:
                roi_rect = resolve_roi(processed_img)
            is_first = False

        cv2.imwrite(os.path.join(cache_dir, filename), processed_img)
        h, w = processed_img.shape[:2]
        image_size = (h, w)
        if roi_bool is None or roi_bool.shape != (h, w):
            roi_bool = make_roi_mask(h, w, roi_rect if ENABLE_ROI else None).astype(bool)

        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        prob = detector.prob(gray)
        inst = unet_instances(prob)
        if not filenames:   # 最初のフレームだけ入力の健全性チェック
            check_unet_input(gray, prob, inst, detector, filename)
        if SAVE_INSTANCE_MASKS:
            np.savez_compressed(os.path.join(inst_dir, os.path.splitext(filename)[0] + ".npz"), inst=inst)
        if SAVE_PROB_MAPS:
            np.savez_compressed(os.path.join(prob_dir, os.path.splitext(filename)[0] + ".npz"),
                                p_in=np.round(prob[1] * 255).astype(np.uint8),
                                p_edge=np.round(prob[2] * 255).astype(np.uint8), u_input=gray)

        dets = instances_to_detections(inst, roi_bool)
        total_area = float(sum(d.area_in_roi for d in dets))
        roi_count = sum(1 for d in dets if d.in_roi)

        detections_per_frame.append(dets)
        filenames.append(filename)
        total_areas.append(total_area)
        roi_counts.append(roi_count)
        print(f"  [{filename}] 検出{len(dets)}個 (ROI内{roi_count}個), ROI内合計面積 {total_area:.0f}px")

    preprocess_params = {"noise_cut": thresh_val, "brightness": bright_val, "median": median_val}
    return detections_per_frame, filenames, total_areas, roi_counts, image_size, roi_rect, preprocess_params


# ==============================================================
# 12. メインパイプライン
# ==============================================================
def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    cache_dir = os.path.join(OUTPUT_FOLDER, "_cache_processed")

    (detections_per_frame, filenames, total_areas, roi_counts,
     image_size, roi_rect, preprocess_params) = run_detection_phase(cache_dir)
    total_frames = len(filenames)

    if ENABLE_BOOTSTRAP:
        run_bootstrap_calibration(detections_per_frame, filenames, cache_dir, image_size)

    print("\n[LAPトラッカー] 実行中...")
    rows = run_laptrack(detections_per_frame, image_size,
                        piv_debug_dir=os.path.join(OUTPUT_FOLDER, "piv") if SAVE_PIV_DEBUG else None)
    rows = compute_velocity_ema(rows, total_frames)

    tracking_csv_path = os.path.join(OUTPUT_FOLDER, "result_tracking.csv")
    area_csv_path = os.path.join(OUTPUT_FOLDER, "result_area_count.csv")
    write_tracking_csv(tracking_csv_path, rows, filenames, detections_per_frame)
    write_area_count_csv(area_csv_path, filenames, total_areas, roi_counts)
    draw_overlays(cache_dir, OUTPUT_FOLDER, rows, detections_per_frame, filenames,
                  total_areas, roi_counts, roi_rect=(roi_rect if ENABLE_ROI else None))

    report = qc_report(rows, total_frames)
    report["used_params"] = {
        "UNET_CKPT": UNET_CKPT,
        "IGNORE_PARTICLE_AREA": IGNORE_PARTICLE_AREA,
        "UNET": {"min_area": UNET_MIN_AREA, "band": UNET_BAND, "edge_thr": UNET_EDGE_THR,
                 "close": UNET_CLOSE, "tiny_max": UNET_TINY_MAX,
                 "mode": UNET_INSTANCE_MODE, "seed_thr": UNET_SEED_THR},
        "preprocess": preprocess_params if ENABLE_PREPROCESSING else None,
        "MAX_SPEED": MAX_SPEED, "POS_GATE": POS_GATE, "POS_GATE_SIZE_FRAC": POS_GATE_SIZE_FRAC,
        "AREA_RATIO_GATE": AREA_RATIO_GATE, "OVERLAP_ACCEPT_IOU": OVERLAP_ACCEPT_IOU,
        "AREA_RELAX_RATIO": AREA_RELAX_RATIO, "AREA_RELAX_POS": AREA_RELAX_POS,
        "MAX_AGE": MAX_AGE, "COAST_GATE_GROWTH": COAST_GATE_GROWTH, "MIN_TRACK_AREA": MIN_TRACK_AREA,
        "weights": {"pos": W_POS, "area": W_AREA, "overlap": W_OVERLAP, "shape": W_SHAPE,
                    "coast": W_COAST, "unknown_v": W_UNKNOWN_V},
        "SHAPE_AREA_REF": SHAPE_AREA_REF,
        "USE_FLOW_PRIOR": USE_FLOW_PRIOR, "PRIOR_AREA_RATIO": PRIOR_AREA_RATIO,
        "USE_PIV_PRIOR": USE_PIV_PRIOR and piv_field is not None, "PIV_GATE": PIV_GATE,
        "PIV_GATE_HARD": PIV_GATE_HARD, "PIV_STATIC_SPEED": PIV_STATIC_SPEED, "W_PIV_OUTSIDE": W_PIV_OUTSIDE,
        "PIV_KEEP_STATIC": PIV_KEEP_STATIC, "PIV_USE_DX": PIV_USE_DX, "PIV_MODE": PIV_MODE,
        "PIV_RASTER": PIV_RASTER, "PIV_SIZE_CLASSES": list(PIV_SIZE_CLASSES),
        "PIV_WINDOWS": {k: list(v) for k, v in PIV_WINDOWS.items()},
        "piv_stats": getattr(run_laptrack, "last_stats", None),
        "EVENT_OVERLAP_MIN": EVENT_OVERLAP_MIN, "EVENT_MARGIN": EVENT_MARGIN,
        "EVENT_AREA_TOL": EVENT_AREA_TOL, "EVENT_MINOR_FRAC": EVENT_MINOR_FRAC,
        "EVENT_MINOR_OVERLAP": EVENT_MINOR_OVERLAP, "TRANSIENT_MERGE_FRAMES": TRANSIENT_MERGE_FRAMES,
        "bootstrap_enabled": ENABLE_BOOTSTRAP,
        "roi_enabled": ENABLE_ROI,
        "roi_rect": list(roi_rect) if (ENABLE_ROI and roi_rect is not None) else None,
    }
    report_path = os.path.join(OUTPUT_FOLDER, "qc_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nCSV保存完了:")
    print(f"  - トラッキング(移動距離): {tracking_csv_path}")
    print(f"  - 面積・個数:            {area_csv_path}")
    print(f"オーバーレイ画像の保存完了: {OUTPUT_FOLDER}")
    print(f"QCレポート: {json.dumps(report, ensure_ascii=False, indent=2)}")
    print("\n全ての処理が完了しました!")


if __name__ == "__main__":
    main()

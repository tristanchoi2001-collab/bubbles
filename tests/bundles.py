"""
テスト用: binarized/ の 1ファイル版を、元のモジュールの名前 (tracker3 など) でも import できるようにする
=====================================================================
元のモジュール (tracker3.py, piv_field.py, tau_unet.py, tau_tracker.py, watershed.py, dot_labels.py,
1_tau_unet_train.py) は old/ に保管した。今使うのは binarized/2_bin_track.py と binarized/1_bin_train.py で、
元のテスト (test_events, test_instances, test_tau, test_dots) はこれらをそのまま元の名前で読む。

    import bundles   # これを先に import する
    import tracker3  # -> binarized/2_bin_track.py

importlib.reload(tracker3) が使えるように、binarized/ を sys.path に入れて名前で import する
(spec_from_file_location で読んだモジュールは reload で見つからない)。
"""
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(ROOT, "binarized")
RAW_DIR = os.path.join(ROOT, "raw")
TRACK_PATH = os.path.join(BIN_DIR, "2_bin_track.py")
TRAIN_PATH = os.path.join(BIN_DIR, "1_bin_train.py")      # 元 1_tau_unet_train.py + dot_labels.py + tau_unet.py
QC_PATH = os.path.join(BIN_DIR, "3_tracking_qc.py")

if BIN_DIR not in sys.path:
    sys.path.insert(0, BIN_DIR)

track = importlib.import_module("2_bin_track")             # 元 tracker3 / watershed / piv_field / tau_unet / tau_tracker
train = importlib.import_module("1_bin_train")             # 元 dot_labels (学習の部品は TRAIN_PATH を別に読む)
for _name, _mod in (("tracker3", track), ("watershed", track), ("piv_field", track), ("tau_unet", track),
                    ("tau_tracker", track), ("dot_labels", train)):
    _have = sys.modules.setdefault(_name, _mod)
    if _have is not _mod:      # old/ のモジュールが先に読まれていると、そちらをテストしてしまう
        raise ImportError(f"{_name} が old/ などから既に読み込まれています ({getattr(_have, '__file__', '?')})。"
                          "tests/ と old/tests は別々に実行してください")

#!/usr/bin/env python
"""二値化しない版のファイル (raw/1_raw_train.py, raw/2_raw_track.py, raw/3_tracking_qc.py) を作る

    python tools/build_raw.py           # 作り直す
    python tools/build_raw.py --check   # 作り直した内容と今のファイルが同じか確認だけ (違えば終了コード 1)

作り方
  1_raw_train.py = tools/raw_parts/train.py (学習の本体) に
                   tools/raw_parts/raw_input.py (B, D の作り方) と
                   binarized/1_bin_train.py の共通の部品 (HELPERS。ラベル変換・後処理・test の照合など) を写したもの
  2_raw_track.py = binarized/2_bin_track.py から TAU (事前マスク・多パス) を除き、
                   U-Net の入力を tools/raw_parts/ の RawDetector (元画像 + 背景画像 -> B, D) に替えたもの
  3_tracking_qc.py = binarized/3_tracking_qc.py をそのまま写したもの (raw/ だけで全部そろうように)
  置き換えの回数は決めておき、元が変わって数が合わなければ止まる。
  binarized/ のファイルを直したら、これも作り直す (tests/test_raw.py の a が最新か確かめる)。
"""
import argparse
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARTS = HERE / 'raw_parts'
OUT_DIR = ROOT / 'raw'
TRAIN_NAME = '1_raw_train.py'
TRACK_NAME = '2_raw_track.py'
BIN_TRAIN = ROOT / 'binarized' / '1_bin_train.py'
BIN_TRACK = ROOT / 'binarized' / '2_bin_track.py'
QC_NAME = '3_tracking_qc.py'
BIN_QC = ROOT / 'binarized' / QC_NAME

# binarized/1_bin_train.py から写す部品 (この順に並べる)
HELPERS = ('resolve', 'list_images', 'unique_dir', 'edge_thickness', 'make_target', 'label_preview', 'load_coco',
           'score_of', 'state_in_channels', 'extract_instances',
           'instance_overlay', 'SIZE_CLASSES', '_size_cls', 'load_gt_instances', 'match_by_size',
           # TAU (事前マスク) の部品: 学習用の事前マスクを正解から作る
           'PRIOR_CHANNELS', 'PRIOR_EDGE_PX', 'Shape', '_paste_or', 'render_prior', 'label_shapes', 'PriorAug',
           '_deform', '_split', '_touching_pairs', 'synth_prior', 'prior_aug')
# binarized/2_bin_track.py の [B] (TAU の部品) のうち 2_raw_track.py で使わないもの (事前マスクを描く render_prior だけ残す)
TAU_DROP = ('IMAGE_CHANNELS', 'build_model', 'state_in_channels', 'expand_state_dict', 'load_tau_model', 'make_input',
            'label_shapes', 'PriorAug', '_deform', '_split', '_touching_pairs', 'synth_prior', 'ImageDegrade',
            'degrade_image', 'TauDetector')
BAR = '# ' + '=' * 70


def sub(text, pattern, repl, count, what):
    """正規表現の置き換え。回数が count と違えば止まる (元ファイルが変わったことに気付くため)"""
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != count:
        raise SystemExit(f'置き換えの回数が違います ({what}): 期待 {count} 回, 実際 {n} 回  パターン {pattern!r}')
    return new


def drop_defs(text, names):
    """最上位の定義 (関数・クラス・代入) を名前で除く。無い名前があれば止まる"""
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    cut, found = set(), set()
    for n in tree.body:
        hit = [nm for nm in _names(n) if nm in names]
        if hit:
            first = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
            cut.update(range(first, n.end_lineno + 1))
            found.update(hit)
    if set(names) - found:
        raise SystemExit(f'除く定義が見つからない: {sorted(set(names) - found)}')
    return re.sub(r'\n{4,}', '\n\n\n', ''.join(ln for i, ln in enumerate(lines, start=1) if i not in cut))


def read(p):
    return Path(p).read_text(encoding='utf-8')


def banner(title):
    return f'{BAR}\n# {title}\n{BAR}\n'


def _names(n):
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        return [n.name]
    if isinstance(n, ast.Assign):
        return [t.id for t in n.targets if isinstance(t, ast.Name)]
    return []


def helpers_source():
    text = read(BIN_TRAIN)
    lines = text.splitlines(keepends=True)
    found = {}
    for n in ast.parse(text).body:
        for name in _names(n):
            if name in HELPERS:
                if name in found:
                    raise SystemExit(f'{BIN_TRAIN.name}: {name} が2回定義されている')
                first = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
                found[name] = ''.join(lines[first - 1:n.end_lineno]).rstrip() + '\n'
    missing = [h for h in HELPERS if h not in found]
    if missing:
        raise SystemExit(f'{BIN_TRAIN.name} に見つからない部品: {missing}')
    src = '\n\n'.join(found[h] for h in HELPERS)
    return (banner('共通の部品 — binarized/1_bin_train.py と同じ (tools/build_raw.py が写したもの)') + '\n' + src)


def build_train():
    t = read(PARTS / 'train.py')
    t = sub(t, r'^# @@RAW_INPUT@@\n', lambda m: read(PARTS / 'raw_input.py'), 1, '学習: RAW_INPUT')
    t = sub(t, r'^# @@HELPERS@@\n', lambda m: helpers_source(), 1, '学習: HELPERS')
    return t


TRACK_DOC = '''#!/usr/bin/env python
\"\"\"
二値化しない版 — 気泡の検出と追跡 (1ファイル)
=====================================================================
    python 2_raw_track.py

元画像 + 背景画像 -> 二値化画像 B・差分画像 D・暗く/明るくなった分 DK/DB (1_raw_train.py と同じ作り方)
-> U-Net (背景 / 気泡内部 / 気泡境界) -> 気泡ごとのマスク -> トラッキング
-> result_tracking.csv / result_area_count.csv / オーバーレイ / qc_report.json
このファイルだけで動く (3_tracking_qc.py が同じフォルダにあれば、TAU のパスごとの比較表も出す)。

UNET_CKPT に入れるもの (入力の作り方・部品は ckpt の記録を見て自動で合わせる。スライダーは出ない):
  - 1_raw_train.py の best.pt: INPUT_MODE・前処理の値・トランスフォーマー・事前マスク (TAU) の有無
  - 今の二値化の best.pt (記録なし): 二値化画像 B だけ (前処理は PREPROC_FIXED) = 2_bin_track.py と同じ結果
  - 二値化の TAU の best.pt (5チャンネル): B + 事前マスク = 2_bin_track.py の TAU と同じ結果
事前マスクを入力するモデル (TAU) なら、前のパスの追跡結果から事前マスクを作って PRIOR_PASSES 回 検出し直す。
オーバーレイ・確率マップの確認画像の背景は二値化画像 B。

中身 (tools/build_raw.py が binarized/2_bin_track.py から作ったもの):
  [A] PIV (大きさ別の速度場。新しい気泡の初速度)                       2_bin_track.py と同じ
  [B] TAU の事前マスクを描く部品                                       2_bin_track.py と同じ (使う部分だけ)
  [B2] 入力の作り方・モデルの形 (トランスフォーマー)・RawDetector      tools/raw_parts/
  [C] 前処理・気泡の分け方・トラッカー・CSV/オーバーレイ/QC             2_bin_track.py と同じ (U-Net に入れる画像だけ違う)
  [D] TAU の多パス検出                                                 2_bin_track.py と同じ (U-Net に入れる画像だけ違う)
  [E] 起動
\"\"\"
'''

TRACK_TAIL = banner('[E] 起動') + '''def main():
    \"\"\"事前マスク (TAU) を入力するモデルで PRIOR_PASSES > 0 なら多パス (main_tau)、それ以外は 1回 (main_single)\"\"\"
    import torch
    ck = torch.load(UNET_CKPT, map_location="cpu")
    _, prior, _ = ckpt_layout(ck, ck["state_dict"])
    if prior and PRIOR_PASSES > 0:
        print("事前マスク (TAU) を入力するモデルなので、前のパスの追跡結果から事前マスクを作って検出し直します")
        return main_tau()
    return main_single()


if __name__ == "__main__":
    main()
'''

PREPROC_OLD = r'''# 前処理パラメータ \(Noise Cut, Brightness, Median\)。学習画像を作ったときと同じ値にすること。
#   None : 最初のフレームでスライダー調整 \(初期値は PREPROC_DEFAULT\)
#   固定 : 例\) PREPROC_FIXED = \(40, 3, 1\)  -> スライダーを出さずにこの値を使う \(再現性のため推奨\)
PREPROC_FIXED = None
'''
PREPROC_NEW = '''# 前処理パラメータ (Noise Cut, Brightness, Median)。1_raw_train.py の ckpt には学習に使った値が記録されていて、
# それを自動で使う (スライダーは出ない)。記録の無い ckpt (今の二値化の best.pt) のときだけ PREPROC_FIXED を使う
# (None なら PREPROC_DEFAULT)。学習画像を作ったときと同じ値にすること
PREPROC_FIXED = (15, 4, 0)
'''


def build_track():
    t = read(BIN_TRACK)
    i = t.index('\n\n\n' + BAR + '\n# 設定')
    t = TRACK_DOC + t[i:]
    # [B] TAU の部品: 事前マスクを描く部分だけ残し、その後ろに raw の部品 [B2] を入れる
    m = re.search('(?s)^' + BAR + r'\n# \[B\] TAU の部品.*?(?=^' + BAR + r'\n# \[C\])', t, flags=re.M)
    if not m:
        raise SystemExit('[B] TAU の部品が見つからない')
    seg = drop_defs(m.group(0), TAU_DROP).replace('# [B] TAU の部品 — 元 tau_unet.py', '# [B] TAU の事前マスクを描く部品 — 元 tau_unet.py の一部', 1)
    raw = (banner('[B2] 入力の作り方 (B, D, DK, DB)・モデルの形・RawDetector — tools/raw_parts/') + '\n'
           + read(PARTS / 'raw_input.py').split(BAR + '\n', 2)[2].lstrip('\n') + '\n\n'
           + read(PARTS / 'raw_detector.py') + '\n\n')
    t = t[:m.start()] + seg.rstrip('\n') + '\n\n\n' + raw + t[m.end():]
    t = sub(t, '(?s)^' + BAR + r'\n# \[E\] 起動.*\Z', lambda m: TRACK_TAIL, 1, '[E]')
    # [C] (元 watershed.py) の U-Net の入力を RawDetector に替える
    t = sub(t, r'(?s)^class UNetDetector:\n.*?(?=^def _wall_regions)', '', 1, 'UNetDetector')
    t = sub(t, r'output_bin"', 'output_raw"', 1, '出力フォルダ')
    t = sub(t, PREPROC_OLD, lambda m: PREPROC_NEW, 1, 'PREPROC_FIXED')
    t = sub(t, r'# U-Netは2値化済み画像で学習しているので、基本は True のまま。',
            '# True のまま (False にするとオーバーレイ・確認画像が元画像になり、入力チェックの警告が出る。U-Net の入力は変わらない)', 1,
            'ENABLE_PREPROCESSING の説明')
    t = sub(t, r'detector = UNetDetector\(UNET_CKPT, TRAIN_IMAGE_HW\)', 'detector = RawDetector(UNET_CKPT, TRAIN_IMAGE_HW)', 1,
            '検出器')
    t = sub(t, r'if bg_img is None and ENABLE_PREPROCESSING:', 'if bg_img is None:', 2, '背景画像は必須')
    t = sub(t, r'print\("  \[前処理OFF\] 元画像をそのままU-Netに入力します \(2値化画像で学習したモデルには非推奨\)。"\)',
            'print("  [前処理OFF] オーバーレイ・確認画像を元画像にします (U-Net の入力は変わりません)")', 1, '前処理OFF')
    t = sub(t, r'thresh_val, bright_val, median_val = PREPROC_FIXED if PREPROC_FIXED else PREPROC_DEFAULT\n'
               r'    use_ui = ENABLE_PREPROCESSING and PREPROC_FIXED is None\n',
            'thresh_val, bright_val, median_val = detector.preproc   # U-Net の入力と同じ値 (ckpt の記録 / PREPROC_FIXED)\n'
            '    use_ui = False\n', 1, '前処理の値')
    t = sub(t, r'prob = detector\.prob\(gray\)', 'prob = detector.prob_raw(img, bg_img)', 1, 'U-Net の入力')
    t = sub(t, r'(\n\n    DETECTION_STATS\.clear\(\)\n    DETECTION_STATS\["mode"\] = UNET_INSTANCE_MODE\n)',
            lambda m: m.group(1) + '    DETECTION_STATS["input"] = {"mode": detector.mode, "preproc": list(detector.preproc)}\n',
            1, '入力の記録')
    # [D] (元 tau_tracker.py) も RawDetector で (元画像 + 背景 -> 入力。事前マスクはそのまま)
    t = sub(t, r'detector = TauDetector\(UNET_CKPT, TRAIN_IMAGE_HW\)', 'detector = RawDetector(UNET_CKPT, TRAIN_IMAGE_HW)', 1,
            'TAU の検出器')
    t = sub(t, r'    tv, bv, mv = PREPROC_FIXED if PREPROC_FIXED else PREPROC_DEFAULT\n'
               r'    use_ui = ENABLE_PREPROCESSING and PREPROC_FIXED is None\n',
            '    tv, bv, mv = detector.preproc   # U-Net の入力と同じ値 (ckpt の記録 / PREPROC_FIXED)\n'
            '    use_ui = False\n', 1, 'TAU の前処理の値')
    t = sub(t, r'^(    names = \[os\.path\.basename\(p\) for p in files\]\n)',
            lambda m: m.group(1) + '    detector.raw_of = lambda f: (cv2.imread(files[f]), bg_img)   # U-Net の入力は元画像 + 背景から作る\n',
            1, 'TAU の元画像')
    t = sub(t, r'prob = detector\.prob\(gray, prior\)', 'prob = detector.prob_frame(f, gray, prior)', 1, 'TAU の U-Net の入力')
    t = sub(t, r'tau_params = \{"UNET_CKPT": UNET_CKPT, ',
            'tau_params = {"UNET_CKPT": UNET_CKPT, "input": {"mode": detector.mode, "preproc": list(detector.preproc)}, ',
            1, 'TAU の入力の記録')
    for name in ('TauDetector(', 'UNetDetector(', 'class UNetDetector', 'class TauDetector', 'ckpt_uses_prior('):
        if name in t:
            raise SystemExit(f'2_raw_track.py に {name} が残っている')
    return t


def build_all():
    out = {TRAIN_NAME: build_train(), TRACK_NAME: build_track(), QC_NAME: read(BIN_QC)}
    for name, text in out.items():
        ast.parse(text)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='作り直さずに、今のファイルが最新か確認する')
    a = ap.parse_args(argv)
    out = build_all()
    stale = []
    for name, text in out.items():
        p = OUT_DIR / name
        old = p.read_text(encoding='utf-8') if p.exists() else None
        if old != text:
            stale.append(name)
            if not a.check:
                OUT_DIR.mkdir(exist_ok=True)
                p.write_text(text, encoding='utf-8')
    if a.check:
        print('最新です' if not stale else f'古いファイル: {stale}  (python tools/build_raw.py で作り直す)')
        return 1 if stale else 0
    print(f'作り直しました: {stale}' if stale else '変更なし')
    return 0


if __name__ == '__main__':
    sys.exit(main())

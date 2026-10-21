#!/usr/bin/env python
"""二値化画像版の 2ファイル (binarized/1_bin_train.py, binarized/2_bin_track.py) を元のモジュールから作る

    python tools/build_binarized.py           # 作り直す
    python tools/build_binarized.py --check   # 作り直した内容と今のファイルが同じか確認だけ (違えば終了コード 1)

なぜ作るか
  二値化画像 (背景差分 + Noise Cut) 用のコードは今 7ファイル (+ 共通の 3_tracking_qc.py) に分かれている。
  ユーザーの PC では「学習 1ファイル + 検出・追跡 1ファイル」だけで動くようにまとめる。
  中身は元のモジュールと同じ (名前の付け替えと import の整理だけ)。元を直したらこのスクリプトで作り直す
  (tests/test_binarized.py が「作り直した内容と同じか」「元と同じ結果か」を確認する)。

作り方
  - 各元ファイルを「説明 (docstring) / 設定 (docstring と最初の import の間) / 本体」に分ける
  - 設定はファイルの先頭にまとめる。import は重複を除いて設定の後にまとめる
  - 元ファイルどうしの参照 (tracker3 の T3.名前, tau_unet.名前, piv_field.名前) は、同じファイルの中の名前にする
  - 名前がぶつかるものは付け替える (下の各 build_* の rename)。付け替えの回数は決めておき、元が変わって数が合わなければ止まる
"""
import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'binarized'
TRAIN_NAME = '1_bin_train.py'
TRACK_NAME = '2_bin_track.py'
SIBLINGS = {'tracker3', 'tau_unet', 'piv_field', 'dot_labels', 'tau_tracker', 'watershed'}


class Src:
    """元ファイル 1つ (行で切り出す。行番号は 1 始まり)"""

    def __init__(self, name):
        self.name = name
        self.text = (ROOT / name).read_text(encoding='utf-8')
        self.lines = self.text.splitlines(keepends=True)
        self.tree = ast.parse(self.text)
        body = self.tree.body
        self.doc_node = body[0] if (body and isinstance(body[0], ast.Expr)
                                    and isinstance(getattr(body[0], 'value', None), ast.Constant)
                                    and isinstance(body[0].value.value, str)) else None
        self.first_import = next(n.lineno for n in body if isinstance(n, (ast.Import, ast.ImportFrom)))

    @property
    def doc(self):
        return self.doc_node.value.value if self.doc_node else ''

    def settings(self):
        """docstring の後から最初の import の前まで (設定)"""
        start = self.doc_node.end_lineno + 1 if self.doc_node else 1
        return _trim(''.join(self.lines[start - 1:self.first_import - 1]))

    def imports(self):
        """最上位の import 文 (兄弟モジュールの import は除く)"""
        out = []
        for n in self.tree.body:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or '']
                if any(m.split('.')[0] in SIBLINGS for m in mods):
                    continue
                out.append(ast.get_source_segment(self.text, n))
        return out

    def body(self, drop=lambda n: False):
        """最初の import から後ろ。最上位の import・兄弟モジュールを読む try・sys.path の追加・
        if __name__ == '__main__'・drop(node) が真のノードを除く"""
        cut = set()
        for n in self.tree.body:
            if n.lineno < self.first_import:
                continue
            if isinstance(n, (ast.Import, ast.ImportFrom)) or _is_main_guard(n) or _is_sibling_try(n) \
                    or _is_syspath(n) or drop(n):
                first = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
                cut.update(range(first, n.end_lineno + 1))
        keep = [ln for i, ln in enumerate(self.lines, start=1) if i >= self.first_import and i not in cut]
        return _trim(re.sub(r'\n{4,}', '\n\n\n', ''.join(keep)))


def _trim(s):
    return s.strip('\n') + '\n'


def _is_main_guard(n):
    return isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) \
        and n.test.left.id == '__name__'


def _is_sibling_try(n):
    if not isinstance(n, ast.Try):
        return False
    for s in n.body:
        if isinstance(s, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in s.names] if isinstance(s, ast.Import) else [s.module or '']
            if any(m.split('.')[0] in SIBLINGS for m in mods):
                return True
    return False


def _is_syspath(n):
    return isinstance(n, ast.If) and 'sys.path' in ast.unparse(n.test)


def _defines(n, names):
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        return n.name in names
    if isinstance(n, ast.Assign):
        return any(isinstance(t, ast.Name) and t.id in names for t in n.targets)
    return False


def sub(text, pattern, repl, count, what):
    """正規表現の置き換え。回数が count と違えば止まる (元ファイルが変わったことに気付くため)"""
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != count:
        raise SystemExit(f'置き換えの回数が違います ({what}): 期待 {count} 回, 実際 {n} 回  パターン {pattern!r}')
    return new


def check_shadowing(src, prefixes):
    """prefix.名前 を 名前 に付け替えたとき、その関数の中で 名前 に代入していると局所変数になって壊れる。
    そういう所が無いか確認する (あれば止まる)。戻り値: 付け替える属性の名前の集合"""
    names = set()
    problems = []
    for fn in ast.walk(src.tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        used, stored = set(), set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in prefixes:
                used.add(n.attr)
                if isinstance(n.ctx, ast.Store):
                    stored.add(n.attr)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                stored.add(n.id)
            elif isinstance(n, ast.arg):
                stored.add(n.arg)
        names |= used
        bad = used & stored
        if bad:
            problems.append((fn.name, sorted(bad)))
    return names, problems


def as_comment(text, title):
    lines = [f'# {title}'] + [('# ' + ln).rstrip() for ln in text.strip('\n').splitlines()]
    return '\n'.join(lines) + '\n'


def banner(title):
    bar = '# ' + '=' * 70
    return f'\n\n{bar}\n# {title}\n{bar}\n'


def merge_imports(*groups, unused=('sys',)):
    """import 文をまとめる: 同じモジュールの from ... import は 1行に、同じ import は 1回に (最初に出てきた順)。
    unused: 元では sys.path の追加にだけ使っていて、まとめると要らなくなるもの"""
    order, plain, froms = [], set(unused and [f'import {u}' for u in unused]), {}
    for g in groups:
        for seg in g:
            n = ast.parse(seg).body[0]
            if isinstance(n, ast.Import):
                for a in n.names:
                    line = f'import {a.name}' + (f' as {a.asname}' if a.asname else '')
                    if line not in plain:
                        plain.add(line)
                        order.append(('plain', line))
            else:
                key = (n.level, n.module)
                if key not in froms:
                    froms[key] = []
                    order.append(('from', key))
                for a in n.names:
                    nm = a.name + (f' as {a.asname}' if a.asname else '')
                    if nm not in froms[key]:
                        froms[key].append(nm)
    out = []
    for kind, v in order:
        if kind == 'plain':
            out.append(v)
        else:
            level, mod = v
            out.append(f"from {'.' * level}{mod or ''} import {', '.join(froms[v])}")
    return '\n'.join(out) + '\n'


def _is_cv2_try(n):
    """piv_field.py の「cv2 が無ければ None」(まとめたファイルでは cv2 は必須なので要らない)"""
    return isinstance(n, ast.Try) and len(n.body) == 1 and isinstance(n.body[0], ast.Import) \
        and [a.name for a in n.body[0].names] == ['cv2']


# ======================================================================
# 2_bin_track.py  (watershed.py + piv_field.py + tau_unet.py + tau_tracker.py)
# ======================================================================
TRACK_HEADER = '''#!/usr/bin/env python
"""
二値化画像版 — 気泡の検出と追跡 (1ファイル)
=====================================================================
    python 2_bin_track.py

背景差分 + 二値化した画像 -> U-Net (背景 / 気泡内部 / 気泡境界) -> 気泡ごとのマスク -> トラッキング
-> result_tracking.csv / result_area_count.csv / オーバーレイ / qc_report.json
このファイルだけで動く (3_tracking_qc.py が同じフォルダにあれば、TAU のパスごとの比較表も出す)。

使うモデル (UNET_CKPT) は自動で見分ける:
  - 普通の U-Net (3チャンネル。1_bin_train.py の USE_PRIOR = False、または今の best.pt)
      -> 1回だけ検出して追跡 (元の watershed.py と同じ。確率マップの保存・分け方の比較もここ)
  - TAU (5チャンネル。1_bin_train.py の USE_PRIOR = True)
      -> 前のパスの追跡結果を事前マスクにして PRIOR_PASSES 回 検出し直す (元の tau_tracker.py と同じ)

設定はこの下にまとめてある (パス・気泡の分け方・トラッキング・PIV・TAU の多パス)。

中身 (tools/build_binarized.py が元のファイルからまとめたもの。処理は元と同じ):
  [A] PIV (大きさ別の速度場。新しい気泡の初速度)                 元 piv_field.py
  [B] TAU の部品 (事前マスク・TAU モデルの読み込み)               元 tau_unet.py
  [C] 前処理・U-Net・気泡の分け方・トラッカー・CSV/オーバーレイ/QC   元 watershed.py (= tracker3.py の既定値違い)
  [D] TAU の多パス検出                                            元 tau_tracker.py
  [E] 起動 (モデルを見て [C] か [D] を動かす)
"""
'''

TRACK_TAIL = '''

# ======================================================================
# [E] 起動
# ======================================================================
def ckpt_uses_prior(path):
    """UNET_CKPT が TAU (事前マスク付き 5チャンネル) か"""
    import torch
    ck = torch.load(path, map_location="cpu")
    sd = ck["state_dict"] if isinstance(ck, dict) and "state_dict" in ck else ck
    return state_in_channels(sd) > IMAGE_CHANNELS


def main():
    """普通の U-Net なら main_single (元 watershed.py)、TAU なら main_tau (元 tau_tracker.py)"""
    if PRIOR_PASSES > 0 and ckpt_uses_prior(UNET_CKPT):
        print("TAU のモデル (5チャンネル) なので、事前マスク付きの多パス検出をします")
        return main_tau()
    return main_single()


if __name__ == "__main__":
    main()
'''


def build_track():
    ws, pv, tu, tt = Src('watershed.py'), Src('piv_field.py'), Src('tau_unet.py'), Src('tau_tracker.py')

    # --- 設定: watershed.py の設定 + tau_tracker.py の TAU の設定 (パス・分け方は watershed と同じものを使う)
    s_ws = ws.settings()
    s_ws = sub(s_ws, r'output_watershed', 'output_bin', 1, '出力フォルダ')
    tt_dups = {'UNET_CKPT', 'IMAGE_FOLDER', 'BACKGROUND_PATH', 'OUTPUT_FOLDER', 'UNET_INSTANCE_MODE'}
    s_tt = tt.settings()
    s_tt = sub(s_tt, r'^(UNET_CKPT|IMAGE_FOLDER|BACKGROUND_PATH|OUTPUT_FOLDER|UNET_INSTANCE_MODE) = .*\n', '', 5,
               'tau_tracker の重複した設定')
    s_tt = sub(s_tt, r'^# -+\n# パスの設定 \(自分の環境に合わせて変更すること\)\n# -+\n\n?', '', 1, 'tau_tracker のパスの見出し')
    s_tt = sub(s_tt, r'^# Tracking-aware の設定$', '# TAU (5チャンネルのモデル) の多パス検出の設定。普通の U-Net では使わない',
               1, 'TAU の見出し')

    # --- [A] piv_field.py
    b_pv = pv.body(drop=_is_cv2_try)

    # --- [B] tau_unet.py
    b_tu = tu.body()

    # --- [C] watershed.py
    names_ws, bad = check_shadowing(ws, {'piv_field'})
    if bad:
        raise SystemExit(f'watershed.py: piv_field.名前 を付け替えると局所変数とぶつかる: {bad}')
    b_ws = ws.body()
    b_ws = sub(b_ws, r'^    if piv_field is None:\n        print\(".*piv_field\.py.*"\)\n        return None\n', '', 1,
               'piv_field が無いときの分岐')
    b_ws = sub(b_ws, r'USE_PIV_PRIOR and piv_field is not None', 'USE_PIV_PRIOR', 1, 'piv_field の有無')
    b_ws = sub(b_ws, r'\bpiv_field\.(?!py\b)(\w+)', r'\1', 8, 'piv_field.名前')
    b_ws = sub(b_ws, r'^def main\(\):', 'def main_single():', 1, 'watershed の main')
    b_ws = sub(b_ws, r'USE_PIV_PRIOR が有効で piv_field\.py が読み込めれば PIVSequence', 'USE_PIV_PRIOR が有効なら PIVSequence',
               1, 'PIV の説明')

    # --- [D] tau_tracker.py
    names_tt, bad = check_shadowing(tt, {'T3', 'tau_unet'})
    bad = [(f, b) for f, b in bad if f != 'main']   # main の T3.名前 = ... は下で直す
    if bad:
        raise SystemExit(f'tau_tracker.py: T3./tau_unet. を付け替えると局所変数とぶつかる: {bad}')
    b_tt = tt.body(drop=lambda n: _defines(n, {'size_class', 'SIZE_CLASSES'}))   # 使われていない。残すと [A] の size_class を上書きする
    b_tt = sub(b_tt, r'^    T3\.(UNET_CKPT|OUTPUT_FOLDER|UNET_INSTANCE_MODE) = \1\n', '', 3, 'main の同じ値の代入')
    b_tt = sub(b_tt, r'^def main\(\):\n', 'def main_tau():\n    global IMAGE_FOLDER, BACKGROUND_PATH\n', 1,
               'tau_tracker の main')
    b_tt = sub(b_tt, r'\b(T3|tau_unet)\.(?!py\b)(\w+)', r'\2', 64, 'T3./tau_unet.名前')

    imports = merge_imports(ws.imports(), pv.imports(), tu.imports(), tt.imports())
    for b in (b_pv, b_tu, b_ws, b_tt):
        assert 'sys.' not in b, 'sys を使っているので import sys を外せない'
    parts = [
        TRACK_HEADER,
        banner('設定 (元 watershed.py)'), s_ws,
        banner('TAU の多パス検出の設定 (元 tau_tracker.py)'), s_tt,
        banner('import'), imports,
        banner('[A] PIV — 元 piv_field.py'), as_comment(pv.doc, '元 piv_field.py の説明:'), '\n', b_pv,
        banner('[B] TAU の部品 — 元 tau_unet.py'), as_comment(tu.doc, '元 tau_unet.py の説明:'), '\n', b_tu,
        banner('[C] 検出・追跡 — 元 watershed.py (tracker3.py)'), as_comment(ws.doc, '元 watershed.py の説明:'), '\n', b_ws,
        banner('[D] TAU の多パス検出 — 元 tau_tracker.py'), as_comment(tt.doc, '元 tau_tracker.py の説明:'), '\n', b_tt,
        TRACK_TAIL,
    ]
    return ''.join(parts)


# ======================================================================
# 1_bin_train.py  (tau_unet.py + dot_labels.py + 1_tau_unet_train.py)
# ======================================================================
TRAIN_HEADER = '''#!/usr/bin/env python
"""
二値化画像版 — U-Net の学習 (1ファイル)
=====================================================================
    python 1_bin_train.py

STEP で何をするか選ぶ (設定はこの下):
  STEP = 'dots'  : 小さい点のラベル補充。ラベルされていない小さい点の候補を探し、確認の画面で選ぶ
                     左クリック = 気泡でない   右クリック = 分からない (くっついた2個も)   もう一度 = 取り消し
                     Enter/Space = このページの残りを「気泡」にして次へ   b = 前のページ   q / Esc = 保存して終了
                   -> DOT_OUT/coco (点を足したラベル) と DOT_OUT/ignore (確認していない候補 = 学習しない所)
                   途中でやめても次は続きから (DOT_OUT/decisions.json)
  STEP = 'train' : U-Net を学習する。USE_DOT_LABELS = True なら STEP = 'dots' の結果を自動で使う
                     USE_PRIOR = False -> 普通の U-Net (3チャンネル)。ラベル補充の効果だけを比べるときはこちら
                     USE_PRIOR = True  -> TAU (画像 + 事前マスクの 5チャンネル)
                   -> OUT/best.pt を 2_bin_track.py の UNET_CKPT に入れる (どちらのモデルも自動で見分ける)

中身 (tools/build_binarized.py が元のファイルからまとめたもの。処理は元と同じ):
  [A] TAU の部品 (モデル・入力・学習用の事前マスク・画像を崩す増強)   元 tau_unet.py
  [B] 小さい点のラベル補充 (STEP = 'dots')                           元 dot_labels.py
  [C] 学習 (STEP = 'train')                                           元 1_tau_unet_train.py
  [D] 起動
"""
'''

TRAIN_SETTINGS_TOP = '''# ======================================================================
#  何をするか — ここを選んで  python 1_bin_train.py  で実行。Windows のパスは r'...' で囲む
# ======================================================================
STEP = 'dots'                 # 'dots' = 小さい点のラベル補充 (確認の画面) / 'train' = 学習
USE_DOT_LABELS = True         # STEP = 'train' のとき STEP = 'dots' の結果 (DOT_OUT/coco と DOT_OUT/ignore) を使う。
                              # False なら SRC (Roboflow の書き出し) と IGNORE_SRC をそのまま使う
DOT_OUT = r'dot_labels'       # STEP = 'dots' の作業・出力フォルダ (SRC の外に置く)
'''

TRAIN_TAIL = '''

# ======================================================================
# [D] 起動
# ======================================================================
def main():
    """STEP = 'dots' -> main_dots (元 dot_labels.py) / 'train' -> main_train (元 1_tau_unet_train.py)"""
    global SRC, IGNORE_SRC
    if STEP == 'dots':
        return main_dots()
    if STEP != 'train':
        raise ValueError(f"STEP は 'dots' か 'train': {STEP!r}")
    if USE_DOT_LABELS:
        d = resolve(DOT_OUT)
        if not (d / 'coco').exists():
            raise FileNotFoundError(f"{d / 'coco'} がありません。先に STEP = 'dots' で実行するか、USE_DOT_LABELS = False に")
        SRC, IGNORE_SRC = str(d / 'coco'), str(d / 'ignore')
        print(f'  小さい点のラベル補充の結果を使います: SRC = {SRC}, IGNORE_SRC = {IGNORE_SRC}')
    return main_train()


if __name__ == '__main__':
    main()
'''


def build_train():
    tu, dl, tr = Src('tau_unet.py'), Src('dot_labels.py'), Src('1_tau_unet_train.py')

    # --- 設定
    s_tr = tr.settings()
    s_tr = sub(s_tr, r"^DST = r'dataset_tau'", "DST = r'dataset_bin'", 1, 'DST')
    s_tr = sub(s_tr, r"^OUT = r'runs/tau'( +)# 結果のフォルダ。既にあれば runs/tau2, tau3",
               r"OUT = r'runs/bin'\1# 結果のフォルダ。既にあれば runs/bin2, bin3", 1, 'OUT')
    s_tr = sub(s_tr, r"^USE_PRIOR = True ", "USE_PRIOR = False", 1, 'USE_PRIOR の既定値')
    s_tr = sub(s_tr, r'^# ={10,}\n#  設定 — ここだけ直して  python 1_tau_unet_train\.py  で実行\n#  Windows のパスは r\'\.\.\.\' で囲む\n# ={10,}\n',
               '', 1, '学習の設定の見出し (上の見出しと重なる)')
    s_tr = sub(s_tr, r'\n# ={10,}\n\Z', '\n', 1, '学習の設定の終わりの線')
    s_tr = sub(s_tr, r'を学習 → tau_tracker\.py で使う', 'を学習 → 2_bin_track.py で使う', 1, 'USE_PRIOR の説明 (TAU)')
    s_tr = sub(s_tr, r'^(IGNORE_SRC = None +)# dot_labels\.py の書き出しの ignore フォルダ .*None なら使わない。$',
               r"\1# 学習しない画素のマスク (USE_DOT_LABELS = True なら DOT_OUT/ignore を自動で使う)。None なら使わない。",
               1, 'IGNORE_SRC の説明')
    s_tr = sub(s_tr, r'tracker3\.py / watershed\.py の\n(\s*#\s*)UNET_CKPT にそのまま使える',
               r'2_bin_track.py で\n\1そのまま使える', 1, 'USE_PRIOR の説明')
    s_tr = sub(s_tr, r'ラベル \(dot_labels\.py\) の効果', "ラベル補充 (STEP = 'dots') の効果", 1, 'USE_PRIOR の説明 2')
    s_dl = dl.settings()
    s_dl = sub(s_dl, r"^SRC = .*\n", '', 1, 'dot_labels の SRC (学習と同じ SRC を使う)')
    s_dl = sub(s_dl, r"^OUT = r'dot_labels' +# 作業フォルダ \(decisions\.json, coco/, ignore/\)\n", '', 1,
               'dot_labels の OUT (DOT_OUT にした)')
    s_dl = sub(s_dl, r'^# ={10,}\n#  設定 — ここだけ直して  python dot_labels\.py  で実行\n#  Windows のパスは r\'\.\.\.\' で囲む\n# ={10,}\n',
               "# ======================================================================\n"
               "#  STEP = 'dots' (小さい点のラベル補充) の設定\n"
               "# ======================================================================\n", 1, 'dot_labels の見出し')
    s_dl = sub(s_dl, r'\bREVIEW\b', 'DOT_REVIEW', 1, 'REVIEW')
    s_dl = sub(s_dl, r'^# ={10,}\n\Z', '', 1, 'dot_labels の設定の終わりの線')

    # --- [A] tau_unet.py
    b_tu = tu.body()

    # --- [B] dot_labels.py
    b_dl = dl.body(drop=lambda n: _defines(n, {'HERE', 'resolve'}))
    b_dl = sub(b_dl, r'^def main\(\):', 'def main_dots():', 1, 'dot_labels の main')
    b_dl = sub(b_dl, r'\bOUT\b', 'DOT_OUT', 8, 'OUT (コードと案内の文)')
    b_dl = sub(b_dl, r'\bREVIEW\b', 'DOT_REVIEW', 1, 'REVIEW')
    b_dl = sub(b_dl, r"    print\('\\n1_tau_unet_train\.py の設定をこう変えてください:'\)\n(    print\(.*\n){4}",
               lambda m: "    print(\"\\n次は STEP = 'train' で学習 (USE_DOT_LABELS = True ならこの結果を自動で使う。\"\n"
                         "          \"ラベル補充の効果だけを比べるなら USE_PRIOR = False)\")\n", 1, '最後の案内')

    # --- [C] 1_tau_unet_train.py
    names_tr, bad = check_shadowing(tr, {'tau_unet'})
    if bad:
        raise SystemExit(f'1_tau_unet_train.py: tau_unet.名前 を付け替えると局所変数とぶつかる: {bad}')
    b_tr = tr.body()
    b_tr = sub(b_tr, r'^def main\(\):', 'def main_train():', 1, '学習の main')
    b_tr = sub(b_tr, r'\btau_unet\.(?!py\b)(\w+)', r'\1', 20, 'tau_unet.名前')
    b_tr = sub(b_tr, r'tau_tracker\.py の動画で確認すること', '2_bin_track.py の動画で確認すること', 1, 'test の案内')
    b_tr = sub(b_tr, r"test の点の候補を dot_labels\.py で'", 'test の点の候補を STEP = "dots" で\'', 1, 'test の案内 2')
    b_tr = sub(b_tr, r"\('tau_tracker\.py' if USE_PRIOR else 'tracker3\.py / watershed\.py / tau_tracker\.py'\)",
               "'2_bin_track.py'", 1, '最後の案内')

    imports = merge_imports(tr.imports(), dl.imports(), tu.imports())
    for b in (b_tu, b_dl, b_tr):
        assert 'sys.' not in b, 'sys を使っているので import sys を外せない'
    parts = [
        TRAIN_HEADER,
        '\n', TRAIN_SETTINGS_TOP,
        banner('STEP = \'train\' (学習) の設定 (元 1_tau_unet_train.py)'), s_tr,
        '\n', s_dl,
        banner('import'), imports,
        banner('[A] TAU の部品 — 元 tau_unet.py'), as_comment(tu.doc, '元 tau_unet.py の説明:'), '\n', b_tu,
        banner('[B] 小さい点のラベル補充 (STEP = \'dots\') — 元 dot_labels.py'),
        as_comment(dl.doc, '元 dot_labels.py の説明 (OUT -> DOT_OUT, REVIEW -> DOT_REVIEW):'), '\n', b_dl,
        banner('[C] 学習 (STEP = \'train\') — 元 1_tau_unet_train.py'),
        as_comment(tr.doc, '元 1_tau_unet_train.py の説明:'), '\n', b_tr,
        TRAIN_TAIL,
    ]
    return ''.join(parts)


def build_all():
    return {TRAIN_NAME: build_train(), TRACK_NAME: build_track()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='作り直さずに、今のファイルが最新か確認する')
    a = ap.parse_args(argv)
    files = build_all()
    for name, text in files.items():
        compile(text, name, 'exec')
    if a.check:
        stale = [n for n, t in files.items()
                 if not (OUT_DIR / n).exists() or (OUT_DIR / n).read_text(encoding='utf-8') != t]
        if stale:
            print(f'古いファイル: {stale}  (python tools/build_binarized.py で作り直してください)')
            return 1
        print('binarized/ は最新です')
        return 0
    OUT_DIR.mkdir(exist_ok=True)
    for name, text in files.items():
        (OUT_DIR / name).write_text(text, encoding='utf-8')
        print(f'  {OUT_DIR / name}  ({text.count(chr(10))} 行)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

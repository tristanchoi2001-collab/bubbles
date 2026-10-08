"""
best.pt を分割して渡せるようにする (アップロードの大きさ制限対策)
=====================================================================
使い方 (best.pt と同じ PC で):
  python shrink_ckpt.py best.pt --split 20          -> best.pt.part01, part02, ... (20MB ずつ。中身はそのまま = 推論結果も同じ)
  python shrink_ckpt.py best.pt --fp16              -> best_fp16.pt (float16 にして約半分。推論結果がわずかに変わる)
  python shrink_ckpt.py best.pt --fp16 --split 20   -> 半分にしてから分割
分割したファイルは全部そろえて結合すれば元に戻る:
  Windows: copy /b best.pt.part01 + best.pt.part02 + best.pt.part03 best.pt
  Linux:   cat best.pt.part* > best.pt
best_fp16.pt は tracker3.py / watershed.py / 1_unet_train.py (FINETUNE_FROM) がそのまま読める (読み込むときに float32 に戻る)。
ただし重みを丸めるので確率がわずかに変わる (学習していない resnet34 U-Net の確認では最大 0.08〜0.13)。
結果を完全に同じにしたいときは --fp16 を使わず分割だけにすること。
"""
import argparse
import os

import torch


def to_fp16(src: str) -> str:
    ck = torch.load(src, map_location="cpu")
    sd = ck["state_dict"]
    half = {k: (v.half() if v.is_floating_point() else v) for k, v in sd.items()}
    dst = os.path.splitext(src)[0] + "_fp16.pt"
    torch.save(dict(ck, state_dict=half), dst)
    print(f"{src}: {os.path.getsize(src) / 2**20:.1f} MB -> {dst}: {os.path.getsize(dst) / 2**20:.1f} MB")
    try:   # 元のモデルとの確率の違いを確認 (segmentation_models_pytorch があるときだけ)
        import segmentation_models_pytorch as smp
        models = []
        for w in (sd, half):
            m = smp.Unet(ck["encoder"], encoder_weights=None, in_channels=3, classes=ck["classes"])
            m.load_state_dict(w)
            models.append(m.eval())
        x = torch.randn(1, 3, 256, 256)
        with torch.no_grad():
            d = (models[0](x).softmax(1) - models[1](x).softmax(1)).abs().max().item()
        print(f"  確認: 元のモデルとの確率の最大差 {d:.4f}")
    except ImportError:
        print("  (segmentation_models_pytorch が無いので確認は省略)")
    except Exception as e:   # 確認に失敗しても best_fp16.pt は作ってある
        print(f"  ※ 確認に失敗しました ({type(e).__name__}: {str(e)[:200]})")
    return dst


def split(path: str, part_mb: float):
    size = int(part_mb * 2**20)
    k = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(size)
            if not chunk:
                break
            k += 1
            with open(f"{path}.part{k:02d}", "wb") as g:
                g.write(chunk)
    print(f"  {os.path.getsize(path) / 2**20:.1f} MB を {k} 個に分割: {path}.part01 ... part{k:02d} (全部アップロードしてください)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ckpt", help="best.pt のパス")
    ap.add_argument("--fp16", action="store_true", help="float16 にして約半分にする (推論結果がわずかに変わる)")
    ap.add_argument("--split", type=float, default=0, metavar="MB", help="この大きさ (MB) ごとに分割する")
    a = ap.parse_args()
    path = to_fp16(a.ckpt) if a.fp16 else a.ckpt
    if a.split > 0:
        split(path, a.split)
    elif not a.fp16:
        print("--split か --fp16 を指定してください (python shrink_ckpt.py -h)")

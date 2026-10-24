"""철 채널(불투명 바닥) 기존 영상으로 하는 속도 시험 두 가지 (아이디어 I98, I96).

I98  기포 안쪽 밝기 대 속도: 같은 크기·같은 화면 위치에서 안쪽 평균 밝기 차 ΔI(원본 − 배경)를 속도 잔차(V/V̄_칸 − 1)에
     회귀한다. 마른 자리면 느린 기포가 다르고, 막 광학이면 ΔI가 V^(2/3)을 따라 매끈하고, 갇힌 빛이면 상관이 없다.
     트랙 단위 부트스트랩으로 기울기의 95% 구간을 낸다. 같은 기포의 ΔI가 화면 안에서 머문 시간과 함께 변하는지도 낸다.
I96  홈 위 속도 변조: 프레임 수가 충분한 트랙마다 흐름 방향 속도 v(t)의 스펙트럼에서 주파수 V̄/λ_g(홈 간격 λ_g) 근처
     진폭 δV를 찾는다. 힘 균형에서 홈 하나의 고정력 진폭 F_pin ≈ D·(δV/V̄)·(2/3 + 1/Δ)(독립 검토 6 정정).
     2/3은 마찰 법칙 D = k·σ·a·Ca^(2/3)(k 16.85, I89)의 속도 의존, 1/Δ는 기포가 느려질 때 커지는 Darcy 압력 힘이다.
     Δ = K·D/(V·A·H), K = H²/12μ, A = πa². 원형(C = 1), 국소 액체 속도가 기포 감속에 흔들리지 않는다고 가정.

입력 (추적 프로그램 steel/2_steel_track.py의 출력)
    --csv      result_tracking.csv (속도 열은 이름에 「速度」가 든 열, 흐름 방향 좌표 변화 px/frame)
    --masks    SAVE_INSTANCE_MASKS = True로 저장한 OUTPUT_FOLDER/instances 폴더(<파일 이름>.npz, 라벨 지도 inst)
    --images   원본 영상 폴더(CSV의 ファイル名), --bg 배경 영상
    --px_mm, --fps, --flow(right/left/up/down), (선택) --groove_mm, --H_mm(갭, 기본 1.0), --sigma, --mu
사용
    python steel_velocity_checks.py --csv result_tracking.csv --masks instances --images frames --bg bg.bmp --px_mm 0.01 --fps 500 --groove_mm 1.0 --out sv_out
    python steel_velocity_checks.py --demo --out sv_demo     # 합성 자료로 스스로 점검
출력: brightness_vs_speed.csv(칸별 기울기·구간), groove_spectrum.csv(트랙별 δV/V̄·F_pin), 요약 출력.
주의: 크기와 속도가 강하게 상관하므로 크기 칸 안에서만 비교한다. 화면 위치에 따른 조명 기울기 때문에 흐름 방향 위치도 칸으로 나눈다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

AXIS = {"right": ("X", +1), "left": ("X", -1), "down": ("Y", +1), "up": ("Y", -1)}


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("トラックID")]
    speed = next((c for c in rows[0] if "速度" in c), None) if rows else None
    return rows, speed


def _erode(m, it):
    """4-이웃 이진 침식(numpy만, scipy 없이)."""
    for _ in range(it):
        e = m.copy()
        e[1:, :] &= m[:-1, :]; e[:-1, :] &= m[1:, :]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        e[0, :] = e[-1, :] = False; e[:, 0] = e[:, -1] = False
        m = e
    return m


def interior_mean(diff, inst, label, erode_px=3):
    """라벨 영역을 erode_px만큼 깎은 안쪽의 평균 밝기 차(밝은 테두리 제외)."""
    ys, xs = np.nonzero(inst == label)
    if not len(ys):
        return float("nan")
    y0, y1, x0, x1 = max(ys.min() - 1, 0), ys.max() + 2, max(xs.min() - 1, 0), xs.max() + 2
    m = _erode(inst[y0:y1, x0:x1] == label, erode_px)
    return float(diff[y0:y1, x0:x1][m].mean()) if m.sum() >= 20 else float("nan")


def label_at(inst, cx, cy):
    y, x = int(round(cy)), int(round(cx))
    if 0 <= y < inst.shape[0] and 0 <= x < inst.shape[1] and inst[y, x] > 0:
        return int(inst[y, x])
    ys, xs = np.nonzero(inst)
    if not len(ys):
        return 0
    k = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    return int(inst[ys[k], xs[k]]) if (xs[k] - cx) ** 2 + (ys[k] - cy) ** 2 < 25 else 0


def collect(rows, speed_col, masks, images, bg_path, flow, load_image=None):
    """기포·프레임마다 (트랙, 프레임, 등가 지름 px, 흐름 방향 속도 px/frame, 흐름 방향 위치, ΔI)."""
    ax, sgn = AXIS[flow]
    if load_image is None:
        import cv2
        def load_image(p):
            im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
            if im is None:
                raise FileNotFoundError(p)
            return im.astype(np.float32)
    bg = load_image(bg_path)
    by_file = defaultdict(list)
    for r in rows:
        if r.get("フレーム接触") == "1" or not r.get(speed_col):
            continue
        by_file[r["ファイル名"]].append(r)
    out = []
    for fname, rs in by_file.items():
        npz = os.path.join(masks, os.path.splitext(fname)[0] + ".npz")
        if not os.path.exists(npz):
            continue
        inst = np.load(npz)["inst"]
        diff = load_image(os.path.join(images, fname)) - bg
        diff -= np.median(diff[inst == 0])                  # 액체의 전체 밝기 차(조명 표류)를 뺀다
        for r in rs:
            lab = label_at(inst, float(r["中心X"]), float(r["中心Y"]))
            if not lab:
                continue
            d = math.sqrt(4 * float(r["面積(px)"]) / math.pi)
            out.append((r["トラックID"], int(r["フレーム"]), d, sgn * float(r[speed_col]), float(r[f"中心{ax}"]),
                        interior_mean(diff, inst, lab)))
    return out


def brightness_vs_speed(obs, n_size=4, n_pos=3, n_boot=300, seed=0):
    """크기·위치 칸마다 ΔI를 속도 잔차에 회귀. 트랙 단위 부트스트랩 95% 구간."""
    rng = np.random.default_rng(seed)
    o = [t for t in obs if t[5] == t[5] and t[3] > 0]
    if len(o) < 20:
        return []
    d = np.array([t[2] for t in o]); s = np.array([t[4] for t in o])
    de = np.quantile(d, np.linspace(0, 1, n_size + 1)); se = np.quantile(s, np.linspace(0, 1, n_pos + 1))
    res = []
    for i in range(n_size):
        for j in range(n_pos):
            sel = [t for t in o if de[i] <= t[2] <= de[i + 1] and se[j] <= t[4] <= se[j + 1]]
            if len(sel) < 15:
                continue
            v = np.array([t[3] for t in sel]); dI = np.array([t[5] for t in sel])
            x = v / v.mean() - 1
            slope = float(np.polyfit(x, dI, 1)[0]) if x.std() > 0 else float("nan")
            tracks = sorted(set(t[0] for t in sel))
            idx = {tr: [k for k, t in enumerate(sel) if t[0] == tr] for tr in tracks}
            boots = []
            for _ in range(n_boot):
                pick = rng.choice(len(tracks), len(tracks))
                kk = [k for p in pick for k in idx[tracks[p]]]
                xb, yb = x[kk], dI[kk]
                if xb.std() > 0:
                    boots.append(np.polyfit(xb, yb, 1)[0])
            lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (float("nan"), float("nan")))
            # 막 광학 예측의 꼴: ΔI ∝ V^(2/3) → 같은 칸에서 log 기울기 2/3 꼴인지(양·음 모두 가능)
            res.append(dict(d_px=f"{de[i]:.0f}-{de[i + 1]:.0f}", pos=f"{se[j]:.0f}-{se[j + 1]:.0f}", n=len(sel), tracks=len(tracks),
                            mean_dI=float(dI.mean()), slope_dI_per_relV=slope, ci_lo=float(lo), ci_hi=float(hi),
                            corr=float(np.corrcoef(x, dI)[0, 1]) if x.std() > 0 and dI.std() > 0 else float("nan")))
    return res


def groove_spectrum(obs, px_mm, groove_mm, sigma, mu, fps, H_mm=1.0, min_len=32):
    """트랙마다 v(t)의 스펙트럼에서 V̄/λ_g 근처 진폭 δV(봉우리 주변 ±1칸의 최대)와 이웃 칸 대비 비."""
    by = defaultdict(list)
    for t in obs:
        by[t[0]].append(t)
    lam_px = groove_mm / px_mm
    res = []
    for tr, ts in by.items():
        ts.sort(key=lambda t: t[1])
        fr = np.array([t[1] for t in ts]); v = np.array([t[3] for t in ts])
        if len(v) < min_len or np.any(np.diff(fr) != 1) or v.mean() <= 0:
            continue
        vb = v.mean()
        f_g = vb / lam_px                                    # 주기/프레임
        if not 2.0 / len(v) < f_g < 0.45:
            continue
        x = (v - vb) * np.hanning(len(v))
        spec = np.abs(np.fft.rfft(x)) * 2 / np.hanning(len(v)).sum()
        fq = np.fft.rfftfreq(len(v))
        k = int(np.argmin(np.abs(fq - f_g)))
        win = spec[max(k - 1, 0):k + 2]
        amp = float(win.max())
        bgn = np.median(np.concatenate([spec[max(k - 8, 1):max(k - 2, 1)], spec[k + 3:k + 9]])) if len(spec) > k + 3 else float("nan")
        d_px = float(np.mean([t[2] for t in ts]))
        a_m = d_px / 2 * px_mm * 1e-3
        V_ms = vb * px_mm * 1e-3 * fps
        Ca = mu * V_ms / sigma
        D = 16.85 * sigma * a_m * Ca ** (2 / 3)
        H = H_mm * 1e-3
        Delta = H * H / (12 * mu) * D / (V_ms * math.pi * a_m * a_m * H)
        res.append(dict(track=tr, frames=len(v), d_px=d_px, V_px_per_frame=vb, f_groove=f_g, dV_over_V=amp / vb,
                        peak_to_background=amp / bgn if bgn and bgn == bgn else float("nan"),
                        Delta=Delta, F_pin_N=D * amp / vb * (2 / 3 + 1 / Delta)))
    return res


def make_demo(out):
    """합성: 원형 기포 40개(겹치지 않게 줄마다 하나) × 48프레임, 오른쪽으로 이동, 속도에 홈 변조(간격 1 mm = 100 px, 진폭 8%).
    안쪽 밝기는 막 광학형으로 절대 속도에 묶는다: ΔI = −40 + 30·((V/6)^(2/3) − 1)(V는 px/frame).
    같은 칸에서 상대 속도 1당 기울기는 약 20·(V̄/6)^(2/3) ≈ +15~+23, δV/V̄ ≈ 0.08을 되돌려야 한다."""
    rng = np.random.default_rng(3)
    os.makedirs(os.path.join(out, "instances"), exist_ok=True)
    H, W, px_mm, NF = 1000, 1200, 0.01, 48
    lam = 100.0
    bubbles = []
    for b in range(40):
        bubbles.append(dict(id=b + 1, r=rng.uniform(6, 11), x0=rng.uniform(15, 300), y=25 + 24 * b,
                            v0=rng.uniform(4.0, 8.0), ph=rng.uniform(0, 6.28)))
    for b in bubbles:                                       # 위치를 속도 적분으로: v(x) = v0(1 + 0.08 sin(2πx/λ + ph))
        xs, x = [], b["x0"]
        for _ in range(NF):
            xs.append(x)
            x += b["v0"] * (1 + 0.08 * math.sin(2 * math.pi * x / lam + b["ph"]))
        b["xs"] = xs
    rows, imgs = [], {}
    bg = np.full((H, W), 120.0, np.float32)
    yy, xx = np.ogrid[:H, :W]
    for f in range(NF):
        im = bg + rng.normal(0, 2.0, (H, W)).astype(np.float32)
        inst = np.zeros((H, W), np.int32)
        for b in bubbles:
            x = b["xs"][f]
            v = b["v0"] * (1 + 0.08 * math.sin(2 * math.pi * x / lam + b["ph"]))
            if x + b["r"] >= W - 2:
                continue
            m = (xx - x) ** 2 + (yy - b["y"]) ** 2 <= b["r"] ** 2
            inst[m] = b["id"]
            im[m] += -40 + 30 * ((v / 6.0) ** (2 / 3) - 1)
            rows.append({"ファイル名": f"f{f:03d}.png", "フレーム": f, "トラックID": b["id"], "イベント": "", "親トラックID": "",
                         "面積(px)": f"{m.sum():.0f}", "ROI内面積(px)": f"{m.sum():.0f}", "先端部X": f"{x + b['r']:.2f}",
                         "先端部Y": f"{b['y']:.2f}", "中心X": f"{x:.2f}", "中心Y": f"{b['y']:.2f}", "速度X(px/frame)": f"{v:.4f}",
                         "周長(px)": "", "フレーム接触": "0"})
        np.savez_compressed(os.path.join(out, "instances", f"f{f:03d}.npz"), inst=inst)
        imgs[f"f{f:03d}.png"] = np.clip(im, 0, 255).astype(np.uint8)
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    imgs["bg.png"] = bg.astype(np.uint8)
    return path, imgs, px_mm


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--masks"); ap.add_argument("--images"); ap.add_argument("--bg")
    ap.add_argument("--px_mm", type=float); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--flow", default="right"); ap.add_argument("--groove_mm", type=float, default=float("nan"))
    ap.add_argument("--sigma", type=float, default=0.072); ap.add_argument("--mu", type=float, default=1.0e-3)
    ap.add_argument("--H_mm", type=float, default=1.0)
    ap.add_argument("--out", default="sv_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    loader = None
    if a.demo:
        a.csv, imgs, a.px_mm = make_demo(a.out)
        a.masks, a.images, a.bg, a.groove_mm, a.flow = os.path.join(a.out, "instances"), "", "bg.png", 1.0, "right"
        loader = lambda p: imgs[os.path.basename(p)].astype(np.float32)
    rows, speed = read_rows(a.csv)
    obs = collect(rows, speed, a.masks, a.images, a.bg, a.flow, load_image=loader)
    print(f"짝지은 관측 {len(obs)}개(트랙 {len(set(t[0] for t in obs))}개)")
    bv = brightness_vs_speed(obs)
    if bv:
        with open(os.path.join(a.out, "brightness_vs_speed.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(bv[0].keys())); w.writeheader(); w.writerows(bv)
        sl = np.array([r["slope_dI_per_relV"] for r in bv])
        print(f"I98 안쪽 밝기 대 속도 잔차: 칸 {len(bv)}개, 기울기 중앙값 {np.nanmedian(sl):+.1f} 계조/(상대 속도 1), "
              f"95% 구간이 0을 빼는 칸 {sum(1 for r in bv if r['ci_lo'] > 0 or r['ci_hi'] < 0)}개. "
              "0에 가까우면 갇힌 빛, 크기 칸마다 같은 부호의 매끈한 기울기면 막 광학, 느린 쪽에서만 꺾이면 마른 자리 쪽(I98).")
    if a.groove_mm == a.groove_mm:
        gs = groove_spectrum(obs, a.px_mm, a.groove_mm, a.sigma, a.mu, a.fps, a.H_mm)
        if gs:
            with open(os.path.join(a.out, "groove_spectrum.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(gs[0].keys())); w.writeheader(); w.writerows(gs)
            r = np.array([g["dV_over_V"] for g in gs]); pb = np.array([g["peak_to_background"] for g in gs])
            print(f"I96 홈 변조: 트랙 {len(gs)}개, δV/V̄ 중앙값 {np.median(r):.3f}, 봉우리/주변 중앙값 {np.nanmedian(pb):.1f}, "
                  f"Δ 중앙값 {np.median([g['Delta'] for g in gs]):.2f}, "
                  f"F_pin 중앙값 {np.median([g['F_pin_N'] for g in gs]):.2e} N(D = 16.85σaCa^(2/3), F_pin = D·(δV/V̄)·(2/3 + 1/Δ) 가정)")
        else:
            print("I96: 조건(연속 프레임 ≥ 32, 2/N < V̄/λ_g < 0.45)을 만족하는 트랙이 없다.")


if __name__ == "__main__":
    main()

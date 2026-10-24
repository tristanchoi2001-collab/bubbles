"""철 채널(불투명 바닥) 기존 영상으로 하는 속도 시험 두 가지 (아이디어 I98, I96).

I98  기포 안쪽 밝기 대 속도: 같은 크기·같은 화면 위치에서 안쪽 평균 밝기 차 ΔI(원본 − 배경)를 속도 잔차(V/V̄_칸 − 1)에
     회귀한다. 마른 자리면 느린 기포가 다르고, 막 광학이면 ΔI가 V^(2/3)을 따라 매끈하고, 갇힌 빛이면 상관이 없다.
     트랙 단위 부트스트랩으로 기울기의 95% 구간을 낸다.
     속도는 중심 위치의 중심 차분 (x_{f+1} − x_{f−1})/2로 그 프레임에 맞춘다. CSV 속도 열(선단부 차분의 EMA α 0.5)은 한 프레임쯤 늦고
     칸 안 속도 잔차를 줄인다(검토 10 #22). 앞뒤 프레임 사이에 합체·분열(중심 점프)이 있으면 그 프레임은 쓰지 않는다.
     같은 기포의 ΔI가 화면 안에서 머문 시간과 함께 변하는지(idea_log I98)는 아직 하지 않는다: 기포가 모두 같은 쪽에서 들어오면
     머문 시간이 흐름 방향 위치와 같아져 조명 기울기와 가를 수 없다.
I96  홈 위 속도 변조: 프레임 수가 충분한 트랙마다 흐름 방향 속도 v(t)의 스펙트럼에서 주파수 f_g = V̄/λ_g(홈 간격 λ_g) 근처
     진폭 δV를 찾는다. 힘 균형에서 홈 하나의 고정력 진폭 F_pin ≈ D·(δV/V̄)·(2/3 + 1/Δ)(독립 검토 6 정정).
     2/3은 마찰 법칙 D = k·σ·a·Ca^(2/3)(k 16.85, I89)의 속도 의존, 1/Δ는 기포가 느려질 때 커지는 Darcy 압력 힘이다.
     Δ = K·D/(V·A·H), K = H²/12μ, A = πa². 원형(C = 1), 국소 액체 속도가 기포 감속에 흔들리지 않는다고 가정.
     속도는 중심 위치의 한 프레임 차분이다(CSV 속도 열의 EMA는 홈 주파수에서 진폭을 |H| = 0.5/√(1.25 − cos 2πf)배,
     f 0.1·0.25·0.4에서 0.75·0.45·0.35로 깎는다, 끝까지 시험에서 발견). 한 프레임 차분도 프레임 시간 평균이라 진폭이
     sinc(πf_g)배(0.98·0.90·0.76)로 깎이므로 나눠서 되돌린다(검토 10 #14, F_pin도 같은 배). 진폭은 0을 8배 덧붙인 FFT의
     봉우리(±1칸 안 최대)로 읽어 칸 사이 손실(한 칸 Hann 창에서 최대 15%)을 없앤다.
     표본화 한계: f_g < 0.45라 홈 간격이 프레임당 이동의 2.2배보다 길어야 한다, 곧 fps ≥ 2.2·V/λ_g(검토 10 #15).
     철 블록 영상(약 48~53 px/frame)이면 홈 간격 약 110 px보다 짧은 홈은 그 fps로는 못 본다. 건너뛴 트랙 수와 필요한 fps를 출력한다.
     더 빠르면 홈 변조가 |f_g − round(f_g)|로 접혀 보이지만 sinc 감쇠가 크고(f_g 1에서 0) 평균 속도와 섞여 쓰지 않는다.
     트랙은 빠진 프레임과 합체·분열(중심 점프) 앞에서 잘라 가장 긴 조각을 쓴다(검토 10 #22).
I116 홈 위 길이 간섭: 앞끝과 뒤끝은 홈을 2πL/λ_g만큼 어긋난 위상으로 지나므로 중심 속도 변조는
     δV(L)/V̄ = (δV₁/V̄)·|1 + ρ·e^{−2πiL/λ_g}|다(L = 흐름 방향 길이). 젖은 막의 모세관 기하 힘(보존력)은 앞·뒤 부호가 반대라
     ρ = −1(정수배 L에서 변조 0), 마른 접촉선 고정(소산력)은 같은 부호라 ρ > 0(정수배에서 최대)이다.
     트랙마다 δV/V̄(위 I96 값)에서 잡음 진폭(스펙트럼 주변 중앙값)을 제곱으로 빼고, φ = frac(L/λ_g)에 대해
     (δV/V̄)² = b₀ + b₁cos 2πφ + b₂sin 2πφ를 맞춘다. r = √(b₁² + b₂²)/b₀ = 2|ρ|/(1 + ρ²)에서 |ρ| ≤ 1의 근,
     위상 ψ = atan2(b₂, b₁)(0 근처면 ρ > 0, π 근처면 ρ < 0). 구간은 트랙 부트스트랩. L은 마스크가 있으면 라벨의 흐름 방향 폭,
     없으면 CSV의 先端部와 中心으로 2·(앞끝 − 중심)이다.

입력 (추적 프로그램 steel/2_steel_track.py의 출력)
    --csv      result_tracking.csv (중심 위치를 쓴다. 이름에 「速度」가 든 속도 열은 없어도 된다)
    --masks    SAVE_INSTANCE_MASKS = True로 저장한 OUTPUT_FOLDER/instances 폴더(<파일 이름>.npz, 라벨 지도 inst)
    --images   원본 영상 폴더(CSV의 ファイル名), --bg 배경 영상(없으면 I98은 건너뛰고 CSV만으로 I96을 한다)
    --px_mm, --fps, --flow(right/left/up/down), (선택) --groove_mm, --H_mm(갭, 기본 1.0), --sigma, --mu
사용
    python steel_velocity_checks.py --csv result_tracking.csv --masks instances --images frames --bg bg.bmp --px_mm 0.01 --fps 500 --groove_mm 1.0 --out sv_out
    python steel_velocity_checks.py --demo --out sv_demo     # 합성 자료로 스스로 점검(연속 운동, f_g 0.06·0.25·0.40·0.50, 합체 점프, I116 젖음·마름)
출력: brightness_vs_speed.csv(칸별 기울기·구간), groove_spectrum.csv(트랙별 δV/V̄·F_pin·L), groove_interference.csv(I116 φ 칸), 요약 출력.
주의: 크기와 속도가 강하게 상관하므로 크기 칸 안에서만 비교한다. 화면 위치에 따른 조명 기울기 때문에 흐름 방향 위치도 칸으로 나눈다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

AXIS = {"right": ("X", +1), "left": ("X", -1), "down": ("Y", +1), "up": ("Y", -1)}
JUMP_EVENTS = ("merge", "split")        # 이 프레임에서 중심이 뛴다(앞 프레임과의 차분을 쓰지 않는다)


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


def _usable(r):
    """기포가 있는 행(면적 > 0, 화면 끝 접촉 아님, 합체로 사라진 기록·「気泡なし」 아님)."""
    try:
        A = float(r.get("面積(px)") or 0)
    except ValueError:
        return False
    ev = r.get("イベント") or ""
    return A > 0 and r.get("フレーム接触") != "1" and not ev.startswith("merged_into") and ev != "気泡なし"


def collect(rows, speed_col, masks, images, bg_path, flow, load_image=None):
    """기포·프레임마다 (트랙, 프레임, 등가 지름 px, CSV 속도 열 px/frame(없으면 nan), 흐름 방향 위치(흐름 쪽이 +), ΔI, 사건).
    영상·배경·마스크 가운데 하나라도 없거나 그 프레임의 라벨을 못 찾으면 ΔI = nan(I96 홈 변조는 위치만 필요하다)."""
    ax, sgn = AXIS[flow]
    nan = float("nan")

    def base(r):
        d = math.sqrt(4 * float(r["面積(px)"]) / math.pi)
        v = sgn * float(r[speed_col]) if speed_col and r.get(speed_col) else nan
        return r["トラックID"], int(r["フレーム"]), d, v, sgn * float(r[f"中心{ax}"])

    def length_front(r):
        """흐름 방향 길이 어림 2·(앞끝 − 중심)(px). 先端部 열이 없으면 nan."""
        try:
            L = 2 * sgn * (float(r[f"先端部{ax}"]) - float(r[f"中心{ax}"]))
        except (KeyError, TypeError, ValueError):
            return nan
        return L if L > 0 else nan

    use = [r for r in rows if _usable(r)]
    if load_image is None and not (images and bg_path and masks):
        return [base(r) + (nan, r.get("イベント") or "", length_front(r)) for r in use]
    if load_image is None:
        import cv2
        def load_image(p):
            im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
            if im is None:
                raise FileNotFoundError(p)
            return im.astype(np.float32)
    bg = load_image(bg_path)
    by_file = defaultdict(list)
    for r in use:
        by_file[r["ファイル名"]].append(r)
    out = []
    for fname, rs in by_file.items():
        npz = os.path.join(masks, os.path.splitext(fname)[0] + ".npz")
        inst = np.load(npz)["inst"] if os.path.exists(npz) else None
        if inst is not None:
            diff = load_image(os.path.join(images, fname)) - bg
            diff -= np.median(diff[inst == 0])              # 액체의 전체 밝기 차(조명 표류)를 뺀다
        for r in rs:
            lab = label_at(inst, float(r["中心X"]), float(r["中心Y"])) if inst is not None else 0
            L = length_front(r)
            if lab:
                yy, xx = np.nonzero(inst == lab)
                c = xx if ax == "X" else yy
                L = float(c.max() - c.min() + 1)                # 라벨의 흐름 방향 폭(I116)
            out.append(base(r) + (interior_mean(diff, inst, lab) if lab else nan, r.get("イベント") or "", L))
    return out


def position_speed(obs):
    """(트랙, 프레임) → 중심 차분 속도 (x_{f+1} − x_{f−1})/2(px/frame, 흐름 방향 +). 앞뒤 프레임이 없거나 사이에 합체·분열이 있으면 없음."""
    by = defaultdict(dict)
    for t in obs:
        by[t[0]][t[1]] = t
    v = {}
    for tr, fr in by.items():
        for f, t in fr.items():
            a, b = fr.get(f - 1), fr.get(f + 1)
            if a is None or b is None or t[6] in JUMP_EVENTS or b[6] in JUMP_EVENTS:
                continue
            v[(tr, f)] = 0.5 * (b[4] - a[4])
    return v


def brightness_vs_speed(obs, n_size=4, n_pos=3, n_boot=300, seed=0):
    """크기·위치 칸마다 ΔI를 속도 잔차(중심 위치 차분)에 회귀. 트랙 단위 부트스트랩 95% 구간."""
    rng = np.random.default_rng(seed)
    vpos = position_speed(obs)
    o = [t[:3] + (vpos[(t[0], t[1])],) + t[4:] for t in obs if t[5] == t[5] and vpos.get((t[0], t[1]), 0.0) > 0]
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


def segments(ts):
    """프레임 순 관측을 빠진 프레임과 합체·분열(중심 점프) 앞에서 자른 조각들."""
    segs, cur = [], [ts[0]]
    for p, t in zip(ts, ts[1:]):
        if t[1] - p[1] != 1 or t[6] in JUMP_EVENTS:
            segs.append(cur)
            cur = []
        cur.append(t)
    segs.append(cur)
    return segs


def groove_spectrum(obs, px_mm, groove_mm, sigma, mu, fps, H_mm=1.0, min_len=32, stats=None):
    """트랙마다 가장 긴 조각의 v(t)(위치의 한 프레임 차분) 스펙트럼에서 f_g = V̄/λ_g 근처 진폭 δV(±1칸 안 최대, 8배 0 덧붙임)를
    sinc(πf_g)로 나눠 되돌린 값과 이웃 칸 대비 비. stats(dict)를 주면 건너뛴 트랙 수를 채운다:
    short(조각 < min_len + 1 프레임), fast(f_g ≥ 0.45, 표본화 한계), slow(f_g ≤ 2/N, 홈 두 주기 미만), back(평균 속도 ≤ 0)."""
    by = defaultdict(list)
    for t in obs:
        by[t[0]].append(t)
    lam_px = groove_mm / px_mm
    st = dict(tracks=0, short=0, fast=0, slow=0, back=0, v_fast=[])
    res = []
    for tr, ts in by.items():
        st["tracks"] += 1
        ts.sort(key=lambda t: t[1])
        seg = max(segments(ts), key=len)
        if len(seg) < min_len + 1:
            st["short"] += 1
            continue
        v = np.diff(np.array([t[4] for t in seg]))
        vb = float(v.mean())
        if vb <= 0:
            st["back"] += 1
            continue
        n = len(v)
        f_g = vb / lam_px                                    # 주기/프레임
        if f_g >= 0.45:
            st["fast"] += 1
            st["v_fast"].append(vb)
            continue
        if f_g <= 2.0 / n:
            st["slow"] += 1
            continue
        w = np.hanning(n)
        x = (v - vb) * w
        spec = np.abs(np.fft.rfft(x)) * 2 / w.sum()
        k = int(np.argmin(np.abs(np.fft.rfftfreq(n) - f_g)))
        bgn = np.median(np.concatenate([spec[max(k - 8, 1):max(k - 2, 1)], spec[k + 3:k + 9]])) if len(spec) > k + 3 else float("nan")
        spec8 = np.abs(np.fft.rfft(x, 8 * n)) * 2 / w.sum()
        amp_raw = float(spec8[np.abs(np.fft.rfftfreq(8 * n) - f_g) <= 1.0 / n].max())
        att = float(np.sinc(f_g))                            # 한 프레임 차분 = 프레임 시간 평균: sin(πf)/(πf)
        amp = amp_raw / att
        d_px = float(np.mean([t[2] for t in seg]))
        a_m = d_px / 2 * px_mm * 1e-3
        V_ms = vb * px_mm * 1e-3 * fps
        Ca = mu * V_ms / sigma
        D = 16.85 * sigma * a_m * Ca ** (2 / 3)
        H = H_mm * 1e-3
        Delta = H * H / (12 * mu) * D / (V_ms * math.pi * a_m * a_m * H)
        Ls = [t[7] for t in seg if len(t) > 7 and t[7] == t[7]]
        res.append(dict(track=tr, frames=n, d_px=d_px, V_px_per_frame=vb, f_groove=f_g, dV_over_V=amp / vb,
                        dV_over_V_raw=amp_raw / vb, sinc=att,
                        peak_to_background=amp_raw / bgn if bgn and bgn == bgn else float("nan"),
                        noise_over_V=bgn / att / vb if bgn == bgn else float("nan"),
                        L_px=float(np.median(Ls)) if Ls else float("nan"),
                        Delta=Delta, F_pin_N=D * amp / vb * (2 / 3 + 1 / Delta)))
    if stats is not None:
        stats.update(st)
    return res


def _rho_from_r(r):
    """r = 2|ρ|/(1 + ρ²)의 |ρ| ≤ 1 근."""
    r = min(abs(r), 1.0)
    return (1 - math.sqrt(1 - r * r)) / r if r > 1e-12 else 0.0


def groove_interference(gs, lam_px, n_bins=5, n_boot=300, seed=0, min_per_bin=3):
    """I116: φ = frac(L/λ_g)에 대해 (δV/V̄)² − (잡음)² = b₀ + b₁cos 2πφ + b₂sin 2πφ를 최소제곱으로 맞춘다.
    반환 dict: n, b0, b1, b2, rho(부호 = b₁ 부호, |ρ| ≤ 1), psi(라디안), 부트스트랩 구간, 칸 표, 판정 문구. 조건이 모자라면 None."""
    tr = [g for g in gs if g.get("L_px", float("nan")) == g.get("L_px", float("nan")) and g["L_px"] > 0]
    if len(tr) < n_bins * min_per_bin:
        return None
    phi = np.array([(g["L_px"] / lam_px) % 1.0 for g in tr])
    y = np.array([g["dV_over_V"] for g in tr])
    nz = np.array([g.get("noise_over_V", float("nan")) for g in tr])
    y2 = y * y - np.where(np.isfinite(nz), nz * nz, 0.0)
    cnt = np.bincount(np.minimum((phi * n_bins).astype(int), n_bins - 1), minlength=n_bins)
    if (cnt >= min_per_bin).sum() < max(3, n_bins - 1):
        return dict(n=len(tr), coverage=cnt.tolist(), verdict="L/λ_g가 한 주기에 고르게 퍼지지 않아 맞추지 않음(칸당 트랙 수 "
                    + "/".join(str(c) for c in cnt) + ")")
    X = np.column_stack([np.ones_like(phi), np.cos(2 * np.pi * phi), np.sin(2 * np.pi * phi)])

    def fit(ii):
        b, *_ = np.linalg.lstsq(X[ii], y2[ii], rcond=None)
        if b[0] <= 0:
            return None
        r = math.hypot(b[1], b[2]) / b[0]
        psi = math.atan2(b[2], b[1])
        rho = _rho_from_r(r) * (1 if math.cos(psi) >= 0 else -1)
        return b, rho, psi, r
    base = fit(np.arange(len(tr)))
    if base is None:
        return dict(n=len(tr), coverage=cnt.tolist(), verdict="평균 변조가 잡음보다 작아 맞추지 않음")
    rng = np.random.default_rng(seed)
    rb = []
    for _ in range(n_boot):
        f = fit(rng.integers(0, len(tr), len(tr)))
        if f is not None:
            rb.append((f[1], f[2], f[3]))
    rb = np.array(rb) if rb else np.zeros((0, 3))
    ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) > 20 else (float("nan"),) * 2
    b, rho, psi, r = base
    bins = []
    for q in range(n_bins):
        m = (phi >= q / n_bins) & (phi < (q + 1) / n_bins)
        pc = (q + 0.5) / n_bins
        model = math.sqrt(max(b[0] + b[1] * math.cos(2 * math.pi * pc) + b[2] * math.sin(2 * math.pi * pc), 0.0))
        bins.append(dict(phi_lo=q / n_bins, phi_hi=(q + 1) / n_bins, n=int(m.sum()),
                         dV_over_V_med=float(np.median(y[m])) if m.any() else float("nan"), model=model))
    rlo, rhi = ci(rb[:, 0]) if len(rb) else (float("nan"),) * 2
    if rhi < -0.3:
        verdict = "정수배 L에서 변조가 작다(ρ < 0): 앞·뒤 힘이 반대 부호 → 젖은 막 위 모세관 기하 힘(보존) 쪽"
    elif rlo > 0.3:
        verdict = "정수배 L에서 변조가 크다(ρ > 0): 앞·뒤 힘이 같은 부호 → 접촉선 고정(소산, 마름) 쪽"
    else:
        verdict = "ρ 구간이 0 근처를 품는다: 한쪽 끝만 걸리거나 섞임, 또는 표본 부족"
    return dict(n=len(tr), coverage=cnt.tolist(), b0=float(b[0]), b1=float(b[1]), b2=float(b[2]), r=r, rho=rho, psi=psi,
                rho_lo=rlo, rho_hi=rhi, psi_lo=ci(rb[:, 1])[0] if len(rb) else float("nan"),
                psi_hi=ci(rb[:, 1])[1] if len(rb) else float("nan"), dV1_over_V=math.sqrt(b[0] / (1 + rho * rho)),
                bins=bins, verdict=verdict)


def run(obs, px_mm, fps, groove_mm, sigma, mu, H_mm, out):
    """I98·I96을 계산해 CSV로 쓰고 요약을 출력한다. (I98 칸 결과, I96 트랙 결과, I96 건너뜀 통계)."""
    bv = brightness_vs_speed(obs)
    if bv:
        with open(os.path.join(out, "brightness_vs_speed.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(bv[0].keys())); w.writeheader(); w.writerows(bv)
        sl = np.array([r["slope_dI_per_relV"] for r in bv])
        print(f"I98 안쪽 밝기 대 속도 잔차(중심 위치 차분 속도): 칸 {len(bv)}개, 기울기 중앙값 {np.nanmedian(sl):+.1f} 계조/(상대 속도 1), "
              f"95% 구간이 0을 빼는 칸 {sum(1 for r in bv if r['ci_lo'] > 0 or r['ci_hi'] < 0)}개. "
              "0에 가까우면 갇힌 빛, 크기 칸마다 같은 부호의 매끈한 기울기면 막 광학, 느린 쪽에서만 꺾이면 마른 자리 쪽(I98).")
    gs, st = [], {}
    if groove_mm == groove_mm:
        gs = groove_spectrum(obs, px_mm, groove_mm, sigma, mu, fps, H_mm, stats=st)
        lam_px = groove_mm / px_mm
        if gs:
            with open(os.path.join(out, "groove_spectrum.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(gs[0].keys())); w.writeheader(); w.writerows(gs)
            r = np.array([g["dV_over_V"] for g in gs]); pb = np.array([g["peak_to_background"] for g in gs])
            sc = np.array([g["sinc"] for g in gs])
            if np.nanmedian(pb) < 3:
                print("  참고: 봉우리/주변 중앙값이 3 미만이라 홈 주파수에 뚜렷한 봉우리가 없다(잡음 수준). δV/V̄·F_pin은 상한으로만 본다.")
            print(f"I96 홈 변조: 트랙 {len(gs)}개, δV/V̄ 중앙값 {np.median(r):.3f}(sinc(πf_g) {sc.min():.2f}~{sc.max():.2f}로 나눔, "
                  f"나누기 전 {np.median([g['dV_over_V_raw'] for g in gs]):.3f}), 봉우리/주변 중앙값 {np.nanmedian(pb):.1f}, "
                  f"Δ 중앙값 {np.median([g['Delta'] for g in gs]):.2f}, "
                  f"F_pin 중앙값 {np.median([g['F_pin_N'] for g in gs]):.2e} N(D = 16.85σaCa^(2/3), F_pin = D·(δV/V̄)·(2/3 + 1/Δ) 가정)")
        else:
            print("I96: 조건(연속 프레임 ≥ 33, 2/N < V̄/λ_g < 0.45)을 만족하는 트랙이 없다.")
        skipped = {k: st.get(k, 0) for k in ("short", "fast", "slow", "back")}
        if any(skipped.values()):
            print(f"  I96 건너뜀(트랙 {st.get('tracks', 0)}개 중): 조각 < 33 프레임 {skipped['short']}, f_g ≥ 0.45 {skipped['fast']}, "
                  f"홈 두 주기 미만 {skipped['slow']}, 역방향 {skipped['back']}")
        gi = groove_interference(gs, lam_px) if gs else None
        if gi and "rho" in gi:
            with open(os.path.join(out, "groove_interference.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(gi["bins"][0].keys())); w.writeheader(); w.writerows(gi["bins"])
            print(f"I116 홈 위 길이 간섭(트랙 {gi['n']}개, φ = frac(L/λ_g) 칸 {'/'.join(str(c) for c in gi['coverage'])}): "
                  f"ρ {gi['rho']:+.2f} [{gi['rho_lo']:+.2f}~{gi['rho_hi']:+.2f}], 위상 ψ {math.degrees(gi['psi']):+.0f}°, "
                  f"한 끝 진폭 δV₁/V̄ {gi['dV1_over_V']:.3f} → {gi['verdict']}. 칸별 중앙값: "
                  + ", ".join(f"φ {bb['phi_lo']:.1f}~{bb['phi_hi']:.1f} {bb['dV_over_V_med']:.3f}(모형 {bb['model']:.3f})" for bb in gi["bins"]))
        elif gi:
            print("I116: " + gi["verdict"])
        if st.get("fast"):
            vf = float(np.median(st["v_fast"]))
            print(f"  표본화 한계: 홈 간격 {lam_px:.0f} px가 프레임당 이동 {vf:.1f} px의 2.2배보다 짧다 → fps ≥ 2.2·V/λ_g = "
                  f"{2.2 * vf * fps / lam_px:.0f} fps로 찍어야 홈 변조를 본다(지금 {fps:g} fps, 검토 10 #15).")
    return bv, gs, st


def _integrate(x0, v0, ph, lam, eps, nf, sub=20):
    """연속 운동 dx/dt = v0·(1 + eps·sin(2πx/λ + ph))를 프레임마다 sub번 RK4로 적분한 프레임 시각의 위치."""
    def fn(x):
        return v0 * (1 + eps * math.sin(2 * math.pi * x / lam + ph))
    xs, x, h = [], x0, 1.0 / sub
    for _ in range(nf):
        xs.append(x)
        for _ in range(sub):
            k1 = fn(x); k2 = fn(x + h * k1 / 2); k3 = fn(x + h * k2 / 2); k4 = fn(x + h * k3)
            x += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return xs


def _ema(xs):
    """추적기처럼 한 프레임 차분의 EMA(α 0.5), 첫 프레임은 없음."""
    out, prev = [], None
    for f in range(len(xs)):
        raw = xs[f] - xs[f - 1] if f else float("nan")
        prev = raw if prev is None or prev != prev else 0.5 * prev + 0.5 * raw
        out.append(prev)
    return out


def make_demo(out):
    """합성: 원형 기포 40개(겹치지 않게 줄마다 하나) × 48프레임, 오른쪽으로 이동, 속도에 홈 변조(간격 1 mm = 100 px, 진폭 8%).
    위치는 연속 운동을 적분해 프레임 시각에 찍는다(검토 10 #14: 프레임마다 x += v(x)로 건너뛰면 sinc 감쇠가 없어 못 본다).
    안쪽 밝기는 막 광학형으로 순간 속도에 묶는다: ΔI = −40 + 30·((V/6)^(2/3) − 1)(V는 px/frame).
    같은 칸에서 상대 속도 1당 기울기는 약 20·(V̄/6)^(2/3) ≈ +15~+23, δV/V̄ ≈ 0.08을 되돌려야 한다.
    CSV 속도 열은 추적기처럼 EMA(α 0.5)로 쓰므로 위치 차분을 쓰는지도 함께 시험된다(속도 열을 쓰면 약 0.04~0.06으로 깎인다)."""
    rng = np.random.default_rng(3)
    os.makedirs(os.path.join(out, "instances"), exist_ok=True)
    H, W, px_mm, NF = 1000, 1200, 0.01, 48
    lam = 100.0
    bubbles = []
    for b in range(40):
        bubbles.append(dict(id=b + 1, r=rng.uniform(6, 11), x0=rng.uniform(15, 300), y=25 + 24 * b,
                            v0=rng.uniform(4.0, 8.0), ph=rng.uniform(0, 6.28)))
    for b in bubbles:
        b["xs"] = _integrate(b["x0"], b["v0"], b["ph"], lam, 0.08, NF)
        b["ema"] = _ema(b["xs"])
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
                         "先端部Y": f"{b['y']:.2f}", "中心X": f"{x:.2f}", "中心Y": f"{b['y']:.2f}",
                         "速度X(px/frame)": f"{b['ema'][f]:.4f}" if b["ema"][f] == b["ema"][f] else "",
                         "周長(px)": "", "フレーム接触": "0"})
        np.savez_compressed(os.path.join(out, "instances", f"f{f:03d}.npz"), inst=inst)
        imgs[f"f{f:03d}.png"] = np.clip(im, 0, 255).astype(np.uint8)
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    imgs["bg.png"] = bg.astype(np.uint8)
    return path, imgs, px_mm


def make_demo_fast(out, seed=7):
    """CSV만(영상 없음)의 I96 합성: 홈 간격 100 px, 진폭 8%, 연속 운동, 위치 잡음 0.1 px, 무리마다 20개 × 48프레임.
    평균 속도 6·25·40·50 px/frame = f_g 약 0.06·0.25·0.40·0.50(마지막은 표본화 한계 밖이라 건너뛰어야 한다).
    f_g 0.25 무리의 절반은 96프레임이고 30번째 프레임에서 합체한다(중심 +12 px 점프, 면적 ×1.6, 사건 merge)
    → 그 앞에서 잘라 뒤 조각(66프레임)만 써야 한다(검토 10 #22). 자르지 않으면 점프가 넓은 띠 성분이 되어 홈 봉우리 진폭을 흔든다
    (고치기 전 판으로 같은 자료: 점프 없는 트랙 0.071, 점프 트랙 0.064, 둘 다 sinc 보정 없음)."""
    rng = np.random.default_rng(seed)
    lam, NF, F_JUMP = 100.0, 48, 30
    rows, tid = [], 0
    for v0 in (6.0, 25.0, 40.0, 50.0):
        for b in range(20):
            tid += 1
            jump = v0 == 25.0 and b % 2 == 0
            nf = 2 * NF if jump else NF
            xs = _integrate(rng.uniform(0, 100), v0 * rng.uniform(0.97, 1.03), rng.uniform(0, 6.28), lam, 0.08, nf)
            xs = [x + rng.normal(0, 0.1) + (12.0 if jump and f >= F_JUMP else 0.0) for f, x in enumerate(xs)]
            ema = _ema(xs)
            for f in range(nf):
                A = math.pi * 64 * (1.6 if jump and f >= F_JUMP else 1.0)
                rows.append({"ファイル名": f"g{f:03d}.png", "フレーム": f, "トラックID": tid,
                             "イベント": "new" if f == 0 else ("merge" if jump and f == F_JUMP else "normal"), "親トラックID": "",
                             "面積(px)": f"{A:.0f}", "中心X": f"{xs[f]:.2f}", "中心Y": f"{30.0 * tid:.2f}",
                             "速度X(px/frame)": f"{ema[f]:.4f}" if ema[f] == ema[f] else "", "フレーム接触": "0"})
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "demo_fast_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path


def make_demo_interf(out, rho, seed=11, n=60, eps=0.04, v0=6.0, lam=100.0, nf=80):
    """I116 합성(CSV만): 앞끝 힘 + ρ × 뒤끝 힘이 홈 간격 λ로 속도를 흔든다. 연속 운동 RK4(프레임당 20단계).
    dx/dt = v0·(1 + eps·[sin(k·x_f + ph) + ρ·sin(k·(x_f − L) + ph)]), x_f = x + L/2. L은 1.5λ~4.5λ에서 고르게.
    CSV의 先端部X = x + L/2라 도구는 L을 2·(앞끝 − 중심)으로 읽는다. 위치 잡음 0.1 px."""
    rng = np.random.default_rng(seed)
    k = 2 * math.pi / lam
    rows = []
    for tid in range(1, n + 1):
        L, ph, x = rng.uniform(1.5 * lam, 4.5 * lam), rng.uniform(0, 6.28), rng.uniform(0, lam)

        def fn(x_):
            xf = x_ + L / 2
            return v0 * (1 + eps * (math.sin(k * xf + ph) + rho * math.sin(k * (xf - L) + ph)))
        xs, h = [], 1.0 / 20
        for _ in range(nf):
            xs.append(x)
            for _ in range(20):
                k1 = fn(x); k2 = fn(x + h * k1 / 2); k3 = fn(x + h * k2 / 2); k4 = fn(x + h * k3)
                x += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        for f, xc in enumerate(xs):
            rows.append({"ファイル名": f"h{f:03d}.png", "フレーム": f, "トラックID": tid, "イベント": "new" if f == 0 else "normal",
                         "親トラックID": "", "面積(px)": f"{math.pi * (L / 2) ** 2:.0f}", "先端部X": f"{xc + L / 2 + rng.normal(0, 0.1):.2f}",
                         "先端部Y": f"{40.0 * tid:.2f}", "中心X": f"{xc + rng.normal(0, 0.1):.2f}", "中心Y": f"{40.0 * tid:.2f}",
                         "フレーム接触": "0"})
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"demo_interf_{'wet' if rho < 0 else 'dry'}.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path


def _demo(out):
    fails = []

    def check(ok, label, msg):
        print(f"  {'통과' if ok else '실패'}  {label}: {msg}")
        if not ok:
            fails.append(label)

    os.makedirs(out, exist_ok=True)
    print("[1] 영상 합성(I98 + I96, f_g 약 0.06)")
    path, imgs, px_mm = make_demo(out)
    rows, speed = read_rows(path)
    obs = collect(rows, speed, os.path.join(out, "instances"), "", "bg.png", "right",
                  load_image=lambda p: imgs[os.path.basename(p)].astype(np.float32))
    bv, gs, _ = run(obs, px_mm, 500.0, 1.0, 0.072, 1e-3, 1.0, out)
    sl = float(np.nanmedian([r["slope_dI_per_relV"] for r in bv])) if bv else float("nan")
    check(15 <= sl <= 25, "I98 기울기", f"{sl:+.1f}(기대 +15~+23)")
    r = float(np.median([g["dV_over_V"] for g in gs])) if gs else float("nan")
    check(abs(r - 0.08) <= 0.008, "I96 f_g 약 0.06", f"δV/V̄ {r:.4f}(참 0.08)")
    print("[2] CSV만 합성(I96, f_g 0.06·0.25·0.40·0.50, 합체 점프)")
    sub = os.path.join(out, "fast")
    rows, speed = read_rows(make_demo_fast(sub))
    obs = collect(rows, speed, None, None, None, "right")
    _, gs, st = run(obs, 0.01, 500.0, 1.0, 0.072, 1e-3, 1.0, sub)
    for lo, hi, name in ((0.04, 0.09, "0.06"), (0.2, 0.3, "0.25"), (0.35, 0.45, "0.40")):
        g = [x for x in gs if lo <= x["f_groove"] < hi]
        r = float(np.median([x["dV_over_V"] for x in g])) if g else float("nan")
        rr = float(np.median([x["dV_over_V_raw"] for x in g])) if g else float("nan")
        check(len(g) == 20 and abs(r - 0.08) <= 0.008, f"I96 f_g {name}",
              f"트랙 {len(g)}개, δV/V̄ {r:.4f}(sinc로 나누기 전 {rr:.4f}, 참 0.08)")
    jumped = [x for x in gs if 0.2 <= x["f_groove"] < 0.3 and int(x["track"]) % 2 == 1]
    r = float(np.median([x["dV_over_V"] for x in jumped])) if jumped else float("nan")
    check(len(jumped) == 10 and all(x["frames"] == 65 for x in jumped) and abs(r - 0.08) <= 0.008, "합체 점프 앞에서 자름",
          f"트랙 {len(jumped)}개, 조각 {sorted({x['frames'] for x in jumped})} 프레임 차분, δV/V̄ {r:.4f}")
    check(st.get("fast") == 20, "f_g 0.50 건너뜀(표본화 한계)", f"{st.get('fast')}개(20개여야 함)")
    print("[3] I116 홈 위 길이 간섭(CSV만, f_g 0.06, 진폭 4%, L 1.5~4.5 λ_g): 젖은 모세관 기하 ρ = −1, 마른 고정 ρ = +0.6")
    for rho_t, name in ((-1.0, "젖음"), (0.6, "마름")):
        sub = os.path.join(out, "interf")
        rows, speed = read_rows(make_demo_interf(sub, rho_t))
        obs = collect(rows, speed, None, None, None, "right")
        gs = groove_spectrum(obs, 0.01, 1.0, 0.072, 1e-3, 500.0)
        gi = groove_interference(gs, 100.0)
        ok = gi is not None and "rho" in gi and abs(gi["rho"] - rho_t) <= 0.2 and (gi["rho_hi"] < -0.3 if rho_t < 0 else gi["rho_lo"] > 0.3)
        msg = (f"ρ {gi['rho']:+.2f} [{gi['rho_lo']:+.2f}~{gi['rho_hi']:+.2f}](참 {rho_t:+.1f}), δV₁/V̄ {gi['dV1_over_V']:.3f}(참 0.040), "
               f"{gi['verdict']}") if gi and "rho" in gi else (gi or {}).get("verdict", "맞춤 없음")
        check(ok, f"I116 {name}", msg)
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--masks"); ap.add_argument("--images"); ap.add_argument("--bg")
    ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px), 예 0.01"); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--flow", default="right", choices=list(AXIS)); ap.add_argument("--groove_mm", type=float, default=float("nan"))
    ap.add_argument("--sigma", type=float, default=0.072); ap.add_argument("--mu", type=float, default=1.0e-3)
    ap.add_argument("--H_mm", type=float, default=1.0)
    ap.add_argument("--out", default="sv_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm):
        ap.error("--csv, --px_mm가 필요하다")
    if a.px_mm > 1:
        ap.error("--px_mm은 화소 하나의 크기(mm/px)다(예 0.01). 1보다 크면 px/mm로 넣은 것 같다.")
    os.makedirs(a.out, exist_ok=True)
    rows, speed = read_rows(a.csv)
    if not (a.images and a.bg and a.masks):
        print("영상·배경·마스크 중 빠진 것이 있어 I98(안쪽 밝기 대 속도)은 건너뛰고 CSV 위치만으로 I96을 본다.")
    obs = collect(rows, speed, a.masks, a.images, a.bg, a.flow)
    print(f"짝지은 관측 {len(obs)}개(트랙 {len(set(t[0] for t in obs))}개)")
    run(obs, a.px_mm, a.fps, a.groove_mm, a.sigma, a.mu, a.H_mm, a.out)


if __name__ == "__main__":
    main()

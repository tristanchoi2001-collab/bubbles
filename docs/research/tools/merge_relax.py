"""합체 뒤 모양 이완으로 메니스커스 마찰과 마른 발자국을 읽는다(아이디어 I107, 검토 8·9 반영).

배경 (원형 근처의 2번 모드 r = a(1 + ε·cos 2(θ − φ)), 깊이 평균 Darcy)
    되돌리는 힘은 평면 곡률 압력 (π/4)σκ_∥, 막는 힘은 바깥 Darcy 흐름과 메니스커스 마찰이다. Darcy만이면 τ₂ = 8μa³/(πσH²)의 지수 감쇠다.
    움직이는 기포(V ≫ a·|ε̇|): 마찰 D ∝ V^m을 이동 속도 V 둘레로 선형화하므로 m과 상관없이 지수 감쇠다(검토 8 #1).
        τ = τ₂(1 + Φ_t), Φ_t = 2m(I/J)Δ ≈ 1.84~2.00Δ(m 1/3~1, m에 거의 무관), Δ = 2U_loc/V − 1(s = V/U_loc = 2/(1 + Δ)).
        → 움직이는 사건에서는 m이 아니라 τ/τ₂(마찰 세기 Δ)를 읽는다.
    멈춘 기포(V ≈ 0): 마찰이 비선형 그대로라 ε̇ = −C·ε^q, q = 1/m(m 1: 지수, m 2/3: q 1.5로 꼬리 t^(−2), m 1/3: q 3). m은 여기서만 읽는다.
    접촉선이 붙은(마른) 발자국이면 남는 변형 ε_r에서 멈춘다: ε̇ = −C·(ε − ε_r)^q.

쓰는 법
    python merge_relax.py --csv result_tracking.csv --fps 500 --px_mm 0.02 --H_mm 0.3 --flow up [--masks_dir OUTPUT_FOLDER/instances]
        [--U_loc 0.05] [--max_frames 40] [--dH_bins 2,5,15,50] [--quiet 10] --out mr_out
    python merge_relax.py --demo --out mr_demo      # 멈춘 기포 세 법칙 + 움직이는 기포(정상 변형이 있는 흐름 방향·무작위 방향 합체)로 스스로 점검
    --px_mm은 화소 하나의 크기(mm/px)다(예 0.02). 마스크(추적기 SAVE_INSTANCE_MASKS의 instances/*.npz)를 쓰는 것을 권한다.

계산
    1. 합체 사건: イベント == "merge"인 행(합친 쪽 트랙)에서 다른 사건(merge/split/new)·화면 끝 접촉·빠진 프레임까지(최대 --max_frames) 따라간다.
       합체 방향: 흡수된 트랙(親トラックID와 merged_into_ 행)의 마지막 검출 중심과 합친 쪽 트랙의 직전 중심을 잇는 선이 흐름 방향과 이루는 각.
       45° 미만이면 흐름 방향(추월) 합체, 이상이면 가로 합체다. 사건 속도 V는 사건 뒤 트랙 중심의 프레임 간 변위 중앙값(px/frame)이다.
    2. 변형(--masks_dir가 있을 때): 짝지은 마스크(중심 3 px·면적 비 0.8~1.25)의 흐름 기준 2차 모멘트 Q_ss, Q_cc, Q_sc로
       e = ((Q_ss − Q_cc), 2Q_sc)/(Q_ss + Q_cc)를 낸다(모멘트에 선형, 작은 변형에서 |e| ≈ 2ε). 크기를 ε = (1 − √(1 − |e|²))/|e|로 바꿔
       부호 있는 변형 벡터 ε⃗ = ε·(cos 2φ, sin 2φ)를 쓴다(φ = 장축과 흐름 방향 사이 각. ε는 (√λ₁ − √λ₂)/(√λ₁ + √λ₂)와 같고,
       첫째 성분은 shape_flatten.py의 ε_x와 같다. 흐름 방향으로 늘어나면 +, 눌리면 −).
       정상 변형(움직이는 기포의 눌림·늘어남, 화소·분할·조명 비등방)은 사건마다 같은 크기·같은 속도 조용한 기포의 ε⃗ 중앙값을 **벡터로** 뺀다.
       이웃: (ln(d/d₀)/0.15)² + (ln((V + 0.2)/(V₀ + 0.2))/0.3)² ≤ 1, 10개가 안 되면 반경을 2배·4배로, 그래도 없으면 크기만(|ln(d/d₀)| ≤ 0.3·0.6).
       모드 진폭은 벡터로 더해지므로 이 빼기는 합체 방향과 무관하다. 사건 계열은 처음(0~--skip 프레임) 변형 방향에 사영한 부호 있는 값이다
       (크기 |ε⃗|와 달리 꼬리에서 잡음이 양으로 치우치지 않는다).
    2'. 마스크가 없으면 둘레·면적으로 ε² ≈ (P²/(4πA) − 1)/1.5를 내고, 같은 크기·속도 조용한 기포의 ε² 중앙값(cv2 둘레의 크기별 치우침 포함)을
       제곱으로 뺀다. 방향을 모르므로 정상 변형과 같은 축의 합체(추월 합체)에서는 치우친다(검토 9 #5) → 가능하면 마스크 경로를 쓴다.
    3. 사건 분류: 사건마다 ε = ε₀e^(−k/τ_ev) + ε_r 맞춤(프레임)으로 ρ = V·τ_ev/(a·(ε(--skip) − ε_r)) ≈ V/(a|ε̇|)를 낸다.
       ρ ≥ 1이면 "움직임"(선형화가 성립, τ/τ₂를 읽음), V·τ_ev < 0.1a면 "멈춤"(m을 읽음), 그 사이는 "중간"(참고값만).
    4. (d/H 구간, 분류)마다 사건 계열의 프레임별 중앙값 곡선을 맞춘다(흐름 방향·가로 합체가 각각 3개 이상이면 따로도 낸다).
       - 지수 + 남는 변형 ε(t) = ε₀e^(−t/τ) + ε_r(ε_r 격자 탐색, 로그 맞춤은 값으로 가중): 모든 분류에서 τ와 τ/τ₂.
         --U_loc(m/s)을 주면 Δ = 2U_loc/V − 1과 예측 1 + 1.9Δ를 같이 낸다. τ/τ₂로 거꾸로 푼 Δ와 s = 2/(1 + Δ)도 참고로 낸다.
       - 멈춤 분류만: 위상 평면에서 ln(−ε̇)를 ln(ε − ε_r)에 회귀 → q, m = 1/q.
       - 멈춤(plateau, 접촉선 고정 후보) 판정: 마지막 1/3 중앙값이 "기준선 산포 σ_b의 3배 + 0.05"와 처음 값의 40% 이상이고,
         마지막 1/3 기울기가 처음 1/3의 20% 미만. σ_b는 조용한 이웃에서 정상 변형을 뺀 뒤 남는 변형의 전형적 크기
         (마스크: 성분당 σ = 중앙값 |ε⃗ − 기준|/1.177, 둘레: √ε²의 1.4826·MAD).
출력: mr_events.csv(사건별 분류·방향·속도·기준선·ε 계열), mr_classes.csv(구간·분류별 요약), 요약 출력.
주의: 합체 직후 몇 프레임은 목(neck) 동역학과 관성이 섞인다 → --skip(기본 1)프레임은 맞춤에서 뺀다. 큰 기포는 시야를 빨리 떠난다.
      예상 크기(I107): 0.3 mm에서 τ₂는 d/H 10/20/30이면 1.3/10.6/36 ms라 500 fps에서 d/H ≳ 20만 이완이 몇 프레임 이상 보인다.
"""
import argparse
import csv
import math
import os
from collections import defaultdict

import numpy as np

V_OFF = 0.2        # 속도 이웃을 ln(V + V_OFF)(px/frame)로 고른다: 멈춘 기포(V = 0)도 같은 식으로 다룬다
BASE_MIN = 10      # 기준선(정상 변형) 이웃 최소 수
PHI_T = 1.9        # I107: Φ_t ≈ 1.84~2.00Δ(m 1/3·2/3·1)의 가운데 값
NAN = float("nan")


def _f(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def axis_of(flow):
    return {"up": ("Y", -1), "down": ("Y", +1), "right": ("X", +1), "left": ("X", -1)}[flow]


def to_flow(x, y, flow):
    """영상 좌표 → (s, c): s는 흐름 방향(+가 하류), c는 가로(velocity_fluctuations·void_waves와 같은 규약). 배열도 된다."""
    ax, sgn = axis_of(flow)
    return (sgn * y, x) if ax == "Y" else (sgn * x, y)


def eps_from_mask(mask):
    """마스크의 2차 모멘트로 ε = (√λ₁ − √λ₂)/(√λ₁ + √λ₂)."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 5:
        return float("nan")
    x = xs - xs.mean(); y = ys - ys.mean()
    cov = np.array([[np.mean(x * x), np.mean(x * y)], [np.mean(x * y), np.mean(y * y)]])
    l2, l1 = np.linalg.eigvalsh(cov)
    if l2 <= 0:
        return float("nan")
    r1, r2 = math.sqrt(l1), math.sqrt(l2)
    return (r1 - r2) / (r1 + r2)


def eps_from_perimeter(P, A):
    """2번 모드의 등주 부족 P²/(4πA) − 1 ≈ 1.5ε²에서 ε."""
    if not (P > 0 and A > 0):
        return float("nan")
    return math.sqrt(max(P * P / (4 * math.pi * A) - 1.0, 0.0) / 1.5)


def eps_vector(Qxx, Qyy, Qxy, flow):
    """영상 좌표의 중심 2차 모멘트 → 흐름 기준 부호 있는 변형 벡터 (ε_∥, ε_×) = ε·(cos 2φ, sin 2φ)(문서 2번)."""
    ax, sgn = axis_of(flow)
    Qss, Qcc = (Qyy, Qxx) if ax == "Y" else (Qxx, Qyy)
    Qsc = sgn * Qxy
    T = Qss + Qcc
    if not T > 0:
        return NAN, NAN
    e1, e2 = (Qss - Qcc) / T, 2.0 * Qsc / T
    em = math.hypot(e1, e2)
    if em < 1e-12:
        return 0.0, 0.0
    ec = min(em, 1.0 - 1e-12)
    eps = (1.0 - math.sqrt(1.0 - ec * ec)) / ec
    return eps * e1 / em, eps * e2 / em


def eps_vector_from_mask(mask, flow):
    ys, xs = np.nonzero(mask)
    if len(xs) < 5:
        return NAN, NAN
    x = xs - xs.mean(); y = ys - ys.mean()
    return eps_vector(float(np.mean(x * x)), float(np.mean(y * y)), float(np.mean(x * y)), flow)


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


class MaskLookup:
    """masks_dir의 프레임별 라벨 지도에서 CSV 기포와 짝지은 마스크의 ε(eps)와 2차 모멘트(moments)."""

    def __init__(self, masks_dir):
        self.dir = masks_dir
        self.cache = {}
        self.mcache = {}                                 # 프레임별 라벨 모멘트 표(작아서 버리지 않는다)

    def _load(self, fname):
        stem = os.path.splitext(fname)[0]
        if stem not in self.cache:
            path = os.path.join(self.dir, stem + ".npz")
            if not os.path.exists(path):
                self.cache[stem] = None
            else:
                inst = np.load(path)["inst"]
                lab = inst.ravel().astype(np.int64)
                cnt = np.bincount(lab)
                yy, xx = np.indices(inst.shape)
                sx = np.bincount(lab, weights=xx.ravel()); sy = np.bincount(lab, weights=yy.ravel())
                ids = np.nonzero(cnt)[0]
                ids = ids[ids > 0]
                self.cache[stem] = (inst, ids, sx[ids] / cnt[ids], sy[ids] / cnt[ids], cnt[ids])
            if len(self.cache) > 64:                     # 메모리: 오래된 것을 버린다
                self.cache.pop(next(iter(self.cache)))
        return self.cache[stem]

    def eps(self, fname, cx, cy, A):
        d = self._load(fname)
        if d is None or not len(d[1]):
            return float("nan")
        inst, ids, cxs, cys, cnt = d
        d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
        j = int(np.argmin(d2))
        if d2[j] > 9.0 or not 0.8 <= cnt[j] / A <= 1.25:
            return float("nan")
        return eps_from_mask(inst == ids[j])

    def _moment_table(self, fname):
        stem = os.path.splitext(fname)[0]
        if stem not in self.mcache:
            d = self._load(fname)
            if d is None or not len(d[1]):
                self.mcache[stem] = None
            else:
                inst, ids, cxs, cys, cnt = d
                lab = inst.ravel().astype(np.int64)
                yy, xx = np.indices(inst.shape)
                xx = xx.ravel().astype(np.float64); yy = yy.ravel().astype(np.float64)
                n = int(lab.max()) + 1
                sxx = np.bincount(lab, weights=xx * xx, minlength=n)[ids] / cnt - cxs ** 2
                syy = np.bincount(lab, weights=yy * yy, minlength=n)[ids] / cnt - cys ** 2
                sxy = np.bincount(lab, weights=xx * yy, minlength=n)[ids] / cnt - cxs * cys
                self.mcache[stem] = (cxs, cys, cnt, sxx, syy, sxy)
        return self.mcache[stem]

    def moments(self, fname, cx, cy, A):
        """짝지은 기포(eps와 같은 규칙)의 중심 2차 모멘트 (Q_xx, Q_yy, Q_xy)(영상 좌표, px²). 못 찾으면 None."""
        t = self._moment_table(fname)
        if t is None:
            return None
        cxs, cys, cnt, sxx, syy, sxy = t
        d2 = (cxs - cx) ** 2 + (cys - cy) ** 2
        j = int(np.argmin(d2))
        if d2[j] > 9.0 or not 0.8 <= cnt[j] / A <= 1.25:
            return None
        return float(sxx[j]), float(syy[j]), float(sxy[j])


def collect(rows, H_px, masks=None, flow="up", max_frames=40, quiet=10):
    """사건(합체 뒤 계열)과 조용한 관측(정상 변형 기준선 표본)."""
    tracks = defaultdict(dict)
    absorbed = defaultdict(set)                          # (합친 트랙, 프레임) → 흡수된 트랙들
    for r in rows:
        tid = r.get("トラックID")
        ev = r.get("イベント") or ""
        if not tid or ev == "気泡なし":
            continue
        if ev.startswith("merged_into_"):
            absorbed[(ev[len("merged_into_"):], int(r["フレーム"]))].add(tid)
            continue
        if not _f(r.get("面積(px)")) > 0:
            continue
        f = int(r["フレーム"])
        tracks[tid][f] = r
        if ev == "merge":
            for p in (r.get("親トラックID") or "").replace(",", ";").split(";"):
                if p.strip():
                    absorbed[(tid, f)].add(p.strip())
    ev_frames = defaultdict(set)
    for tid, fr in tracks.items():
        for f, r in fr.items():
            if r.get("イベント") in ("merge", "split", "new"):
                ev_frames[tid].add(f)

    def sc(r):
        return to_flow(_f(r.get("中心X")), _f(r.get("中心Y")), flow)

    def vel(fr, f, w=3):
        """프레임 f의 중심 속도 (v_s, v_c)(px/frame): ±w 프레임 안 앞뒤 차분의 성분별 중앙값(사건 V처럼 위치 잡음에 강하게).
        앞뒤 차분이 하나도 없으면 한쪽 차분."""
        vs, vc = [], []
        for g in range(f - w, f + w + 1):
            p, n = fr.get(g - 1), fr.get(g + 1)
            if p is not None and n is not None:
                a_, b_ = sc(p), sc(n)
                vs.append((b_[0] - a_[0]) / 2); vc.append((b_[1] - a_[1]) / 2)
        if vs:
            return float(np.median(vs)), float(np.median(vc))
        p, n = fr.get(f - 1), fr.get(f + 1)
        if n is not None:
            a_, b_ = sc(fr[f]), sc(n)
            return b_[0] - a_[0], b_[1] - a_[1]
        if p is not None:
            a_, b_ = sc(p), sc(fr[f])
            return b_[0] - a_[0], b_[1] - a_[1]
        return NAN, NAN

    def vec(r):
        if masks is None:
            return NAN, NAN
        Q = masks.moments(r.get("ファイル名", ""), _f(r.get("中心X")), _f(r.get("中心Y")), _f(r.get("面積(px)")))
        return eps_vector(*Q, flow) if Q is not None else (NAN, NAN)

    def e2p(r):
        P, A = _f(r.get("周長(px)")), _f(r.get("面積(px)"))
        return (P * P / (4 * math.pi * A) - 1.0) / 1.5 if P > 0 and A > 0 else NAN

    def merge_angle(tid, f):
        """흡수된 트랙(가장 큰 것)의 마지막 검출 중심 − 합친 트랙의 직전 중심이 흐름 방향과 이루는 각(0~90°)."""
        fr = tracks[tid]
        hp = fr.get(f - 1) or fr.get(f)
        best = None
        for aid in absorbed.get((tid, f), ()):
            afr = tracks.get(aid)
            gs = [g for g in afr if g < f] if afr else []
            if not gs:
                continue
            ar = afr[max(gs)]
            Aa = _f(ar.get("面積(px)"))
            if best is None or Aa > best[0]:
                best = (Aa, ar)
        if best is None or hp is None:
            return NAN
        (hs, hc), (as_, ac) = sc(hp), sc(best[1])
        if hs == as_ and hc == ac:
            return NAN
        return math.degrees(math.atan2(abs(ac - hc), abs(as_ - hs)))

    events, quiet_obs = [], []
    for tid, fr in tracks.items():
        evs = ev_frames[tid]
        for f, r in fr.items():
            if r.get("フレーム接触") == "1":
                continue
            a_px = math.sqrt(_f(r["面積(px)"]) / math.pi)
            dH = 2 * a_px / H_px
            ev = r.get("イベント")
            if ev == "merge":
                ser = []
                for k in range(max_frames + 1):
                    g = f + k
                    q = fr.get(g)
                    if q is None or q.get("フレーム接触") == "1" or (k > 0 and g in evs):
                        break
                    ser.append(q)
                if len(ser) < 4:
                    continue
                pos = np.array([sc(q) for q in ser], float)
                v_s, v_c = (float(np.median(np.diff(pos[:, 0]))), float(np.median(np.diff(pos[:, 1]))))
                events.append(dict(track=tid, frame=f, dH=dH, a_px=a_px, V=math.hypot(v_s, v_c), V_s=v_s,
                                   angle=merge_angle(tid, f), vec=[vec(q) for q in ser], e2p=[e2p(q) for q in ser]))
            elif ev in ("normal", "") and not any(abs(f - e) <= quiet for e in evs):
                v = vel(fr, f)
                quiet_obs.append((dH, math.hypot(*v) if v[0] == v[0] else NAN, vec(r), e2p(r)))
    return events, quiet_obs


class Baseline:
    """조용한 관측으로 (크기, 속도) 이웃의 정상 변형 기준선."""

    def __init__(self, quiet_obs):
        q = quiet_obs
        self.lnd = np.log(np.array([o[0] for o in q], float)) if q else np.zeros(0)
        self.lnv = np.log(np.array([o[1] for o in q], float) + V_OFF) if q else np.zeros(0)
        self.v1 = np.array([o[2][0] for o in q], float) if q else np.zeros(0)
        self.v2 = np.array([o[2][1] for o in q], float) if q else np.zeros(0)
        self.e2p = np.array([o[3] for o in q], float) if q else np.zeros(0)

    def select(self, dH, V, valid):
        """반환 (고른 표본, 넓힌 배수: + = 크기·속도 타원, − = 크기만, 0 = 없음)."""
        if not len(self.lnd):
            return None, 0.0
        dd = (self.lnd - math.log(dH)) / 0.15
        if V == V:
            dv = (self.lnv - math.log(V + V_OFF)) / 0.3
            for s_ in (1.0, 2.0, 4.0):
                sel = valid & np.isfinite(dv) & (dd * dd + dv * dv <= s_ * s_)
                if sel.sum() >= BASE_MIN:
                    return sel, s_
        for s_ in (2.0, 4.0):
            sel = valid & (np.abs(dd) <= s_)
            if sel.sum() >= BASE_MIN:
                return sel, -s_
        return None, 0.0

    def vector(self, dH, V):
        """(기준 ε⃗, σ_b(성분당), 표본 수, 넓힘)."""
        sel, how = self.select(dH, V, np.isfinite(self.v1) & np.isfinite(self.v2))
        if sel is None:
            return (0.0, 0.0), NAN, 0, 0.0
        b1, b2 = float(np.median(self.v1[sel])), float(np.median(self.v2[sel]))
        rr = np.hypot(self.v1[sel] - b1, self.v2[sel] - b2)
        return (b1, b2), float(np.median(rr)) / 1.177, int(sel.sum()), how

    def perimeter(self, dH, V):
        """(기준 ε², σ_b, 표본 수, 넓힘)."""
        sel, how = self.select(dH, V, np.isfinite(self.e2p))
        if sel is None:
            return 0.0, NAN, 0, 0.0
        v = self.e2p[sel]
        e = np.sqrt(np.maximum(v, 0.0))
        return float(np.median(v)), 1.4826 * float(np.median(np.abs(e - np.median(e)))), int(sel.sum()), how


def event_series(ev, base, use_masks, skip):
    """기준선을 뺀 사건 계열. 마스크: 처음 변형 방향에 사영한 부호 있는 ε와 그 방향 φ₀. 둘레: √(ε² − 기준 ε²)."""
    if use_masks:
        (b1, b2), sb, nb, how = base.vector(ev["dH"], ev["V"])
        rel = [(v[0] - b1, v[1] - b2) for v in ev["vec"]]
        u = np.nansum(np.array(rel[:skip + 1], float), axis=0) if rel else np.zeros(2)
        un = float(math.hypot(u[0], u[1]))
        if not un > 0:
            return [NAN] * len(rel), [NAN] * len(rel), NAN, sb, nb, how
        u = u / un
        proj = [r[0] * u[0] + r[1] * u[1] for r in rel]
        mag = [math.hypot(*r) for r in rel]
        phi0 = abs(0.5 * math.degrees(math.atan2(u[1], u[0])))   # 처음 장축과 흐름 방향 사이 각(0~90°)
        return proj, mag, phi0, sb, nb, how
    b, sb, nb, how = base.perimeter(ev["dH"], ev["V"])
    ser = [math.sqrt(max(e - b, 0.0)) if e == e else NAN for e in ev["e2p"]]
    return ser, ser, NAN, sb, nb, how


def tau_event(e, skip, floor):
    """사건 하나의 지수 시간 τ_ev(프레임)와 남는 변형 ε_r: --skip 뒤 유한한 점에 ε = ε₀e^(−k/τ) + ε_r(fit_exp_offset).
    멈춘 발자국(ε_r > 0)도 이완 시간이 나온다. 맞춤이 안 되면 (nan, 0)."""
    k = np.arange(len(e), dtype=float)
    x = np.asarray(e, float)
    keep = np.isfinite(x) & (k >= skip)
    if keep.sum() < 3:
        return NAN, 0.0
    tau, _, er, _, _ = fit_exp_offset(k[keep], x[keep], 0, floor)
    return (tau, er) if tau == tau else (NAN, 0.0)


def motion_of(V, tau_ev, a_px, e_skip, n):
    """("moving"|"mid"|"stuck", ρ = V·τ/(a·ε)). e_skip은 이완하는 몫(ε(--skip) − ε_r). τ를 모르면(맞춤 실패) 계열 길이의 10배로 둔다."""
    tau = tau_ev if (tau_ev == tau_ev and 0 < tau_ev < 10.0 * n) else 10.0 * n
    if not V == V:
        return "?", NAN
    rho = V * tau / (a_px * max(e_skip if e_skip == e_skip else 0.0, 1e-3))
    if V * tau < 0.1 * a_px:
        return "stuck", rho
    return ("moving" if rho >= 1.0 else "mid"), rho


def phase_plane_fit(t, e, eps_r=0.0, skip=1, floor=0.01, min_pts=6):
    """ε̇ = −C(ε − ε_r)^q를 위상 평면에서 맞춘다(ε_r는 고정). 반환 (q, C, 잔차, 점 수)."""
    e = np.asarray(e, float)
    es = np.convolve(np.pad(e, 1, mode="edge"), np.ones(3) / 3, mode="valid") if len(e) >= 3 else e
    de = np.gradient(es, t)
    x = es - eps_r
    ok = (np.arange(len(es)) >= skip) & (x > floor) & (de < 0)
    if ok.sum() < min_pts:
        return float("nan"), float("nan"), float("nan"), int(ok.sum())
    lx, ly = np.log(x[ok]), np.log(-de[ok])
    A = np.vstack([lx, np.ones_like(lx)]).T
    sol = np.linalg.lstsq(A, ly, rcond=None)[0]
    rms = float(np.sqrt(np.mean((A @ sol - ly) ** 2)))
    return float(sol[0]), float(math.exp(sol[1])), rms, int(ok.sum())


def fit_exp_offset(t, e, skip, floor, n_grid=41):
    """ε(t) = ε₀e^(−t/τ) + ε_r. ε_r 격자마다 ln(ε − ε_r)를 값으로 가중해 맞추고 선형 잔차가 가장 작은 것. 반환 (τ, ε₀, ε_r, 잔차, 점 수)."""
    t = np.asarray(t, float); e = np.asarray(e, float)
    tf, ef = t[skip:], e[skip:]
    if len(ef) < 3:
        return NAN, NAN, NAN, NAN, 0
    hi = 0.95 * ef.min() if ef.min() > 0 else 0.0
    lo = min(0.0, ef.min()) - 0.02
    best = None
    for er in np.linspace(lo, hi, n_grid):
        x = ef - er
        ok = x > floor
        if ok.sum() < 3:
            continue
        sl, ic = np.polyfit(tf[ok], np.log(x[ok]), 1, w=x[ok])
        if not sl < 0:
            continue
        rms = float(np.sqrt(np.mean((er + np.exp(ic + sl * tf) - ef) ** 2)))
        if best is None or rms < best[3]:
            best = (-1.0 / sl, math.exp(ic), float(er), rms, int(ok.sum()))
    return best if best else (NAN, NAN, NAN, NAN, 0)


def plateau(e, skip=1, thr=0.05):
    """멈춤 판정: 마지막 1/3의 중앙값이 thr(= 3σ_b + 0.05)와 처음 값의 40% 이상이고, 마지막 1/3의 기울기가 처음 1/3 기울기의 20% 미만."""
    e = np.asarray(e, float)
    n = len(e)
    if n < 6:
        return False, float("nan")
    k3 = max(n // 3, 2)
    early, late = e[skip:skip + k3], e[-k3:]
    s_e = abs(np.polyfit(np.arange(len(early)), early, 1)[0]) if len(early) >= 2 else 0.0
    s_l = abs(np.polyfit(np.arange(len(late)), late, 1)[0])
    lv = float(np.median(late))
    return bool(lv >= max(thr, 0.4 * e[skip]) and s_l < 0.2 * max(s_e, 1e-9)), lv


def prepare(events, base, use_masks, skip):
    """사건마다 기준선을 빼고 τ_ev·분류·방향을 붙인다(제자리)."""
    for ev in events:
        proj, mag, phi0, sb, nb, how = event_series(ev, base, use_masks, skip)
        fl = max(2 * sb, 0.01) if sb == sb else 0.01
        tau_ev, er_ev = tau_event(proj, skip, fl)
        e_skip = proj[min(skip, len(proj) - 1)] - er_ev
        motion, rho = motion_of(ev["V"], tau_ev, ev["a_px"], e_skip, len(proj))
        ang = ev["angle"]
        ev.update(proj=proj, mag=mag, phi0=phi0, sigma_b=sb, n_base=nb, base_how=how, tau_ev=tau_ev, motion=motion, rho=rho,
                  orient=("s" if ang < 45 else "c") if ang == ang else "?")
    return events


def fit_group(g, motion, fps, H_m, px_m, mu, sigma, skip, U_loc):
    T = max(len(ev["proj"]) for ev in g)
    med = []
    for k in range(T):
        v = [ev["proj"][k] for ev in g if k < len(ev["proj"]) and ev["proj"][k] == ev["proj"][k]]
        if len(v) < 3:
            break
        med.append(float(np.median(v)))
    if len(med) < 5:
        return None
    sbs = [ev["sigma_b"] for ev in g if ev["sigma_b"] == ev["sigma_b"]]
    sb = float(np.median(sbs)) if sbs else NAN
    noise = max(1.253 * sb / math.sqrt(len(g)), 0.002) if sb == sb else 0.005
    thr = 3 * sb + 0.05 if sb == sb else 0.05
    t = np.arange(len(med)) / fps
    floor = max(3 * noise, 0.02 * med[skip] if len(med) > skip else 0.0, 0.003)
    pinned, late = plateau(med, skip, thr)
    tau, e0, er_fit, rms_e, n_e = fit_exp_offset(t, med, skip, floor)
    q = C = rms_q = NAN
    npts_q = 0
    if motion == "stuck":
        q, C, rms_q, npts_q = phase_plane_fit(t, med, eps_r=(late - 0.5 * floor) if pinned else 0.0, skip=skip, floor=floor)
    a_px = float(np.median([ev["a_px"] for ev in g]))
    V_px = float(np.median([ev["V"] for ev in g]))
    V_s = float(np.median([ev["V_s"] for ev in g]))
    tau2 = 8 * mu * (a_px * px_m) ** 3 / (math.pi * sigma * H_m * H_m)
    ratio = tau / tau2 if tau2 > 0 else NAN
    V_ms = V_s * px_m * fps
    Delta = 2 * U_loc / V_ms - 1 if (U_loc == U_loc and U_loc and V_ms > 0) else NAN
    D_tau = (ratio - 1) / PHI_T if ratio == ratio else NAN
    return dict(n_events=len(g), n_s=sum(ev["orient"] == "s" for ev in g), n_c=sum(ev["orient"] == "c" for ev in g),
                frames=len(med), a_px=a_px, V_px=V_px, V_s_px=V_s, V_mps=V_ms, sigma_b=sb, noise=noise, plateau_thr=thr,
                eps0=med[0], eps_end=med[-1], eps_r=late if pinned else 0.0, pinned=int(pinned),
                tau_exp_s=tau, eps_r_fit=er_fit, fit_rms=rms_e, fit_points=n_e, tau2_s=tau2, tau_over_tau2=ratio,
                Delta_Uloc=Delta, pred_tau_over_tau2=1 + PHI_T * Delta if Delta == Delta else NAN,
                Delta_from_tau=D_tau, s_from_tau=2 / (1 + D_tau) if D_tau == D_tau and D_tau > -1 else NAN,
                q=q, m=1 / q if (motion == "stuck" and q == q and q > 0) else NAN, q_fit_rms=rms_q, q_fit_points=npts_q,
                curve=";".join(f"{v:.4f}" for v in med))


def analyse(events, bins, fps, H_m, px_m, mu=1e-3, sigma=0.072, skip=1, U_loc=NAN):
    """prepare를 거친 사건으로 (d/H 구간, 분류)마다 요약. 흐름 방향·가로가 각각 3개 이상이면 따로도."""
    out = []
    for lo, hi in bins:
        for motion in ("moving", "mid", "stuck"):
            grp = [ev for ev in events if lo <= ev["dH"] < hi and ev["motion"] == motion]
            if len(grp) < 3:
                continue
            subsets = [("all", grp)]
            gs = [ev for ev in grp if ev["orient"] == "s"]
            gc = [ev for ev in grp if ev["orient"] == "c"]
            if len(gs) >= 3 and len(gc) >= 3:
                subsets += [("s", gs), ("c", gc)]
            for orient, g in subsets:
                r = fit_group(g, motion, fps, H_m, px_m, mu, sigma, skip, U_loc)
                if r is not None:
                    out.append(dict(dict(dH_lo=lo, dH_hi=hi, motion=motion, orient=orient), **r))
    return out


MOTION_KO = {"moving": "움직임", "mid": "중간", "stuck": "멈춤", "?": "속도 모름"}
ORIENT_KO = {"all": "", "s": " 흐름 방향 합체만", "c": " 가로 합체만"}


def describe(r):
    head = (f"d/H {r['dH_lo']:g}~{r['dH_hi']:g} {MOTION_KO[r['motion']]}{ORIENT_KO[r['orient']]}: 사건 {r['n_events']}"
            f"(흐름 방향 {r['n_s']}·가로 {r['n_c']}), V {r['V_px']:.2f} px/frame, ε {r['eps0']:.3f} → {r['eps_end']:.3f}({r['frames']}프레임), "
            f"σ_b {r['sigma_b']:.3f}")
    tail = f", τ {r['tau_exp_s'] * 1e3:.1f} ms = τ₂의 {r['tau_over_tau2']:.2f}배"
    if r["motion"] == "moving":
        if r["pred_tau_over_tau2"] == r["pred_tau_over_tau2"]:
            tail += f"(U_loc로 Δ {r['Delta_Uloc']:.2f} → 예측 1 + 1.9Δ = {r['pred_tau_over_tau2']:.2f})"
        if r["s_from_tau"] == r["s_from_tau"]:
            tail += f"; τ/τ₂로 거꾸로 푼 Δ {r['Delta_from_tau']:.2f}, s {r['s_from_tau']:.2f}"
    elif r["motion"] == "stuck":
        tail += f", q {r['q']:.2f} → m {r['m']:.2f}"
    else:
        tail += "(선형화 경계라 참고값, m·Δ 판독 안 함)"
    if r["pinned"]:
        tail += f", ε_r {r['eps_r']:.3f}(멈춤: 접촉선 고정 후보, 문턱 {r['plateau_thr']:.3f})"
    return head + tail


def summarize_events(events):
    cnt = defaultdict(int)
    for ev in events:
        cnt[(ev["motion"], ev["orient"])] += 1
    parts = [f"{MOTION_KO[m]}·{({'s': '흐름 방향', 'c': '가로', '?': '방향 모름'})[o]} {n}" for (m, o), n in sorted(cnt.items())]
    dif = [abs(ev["phi0"] - ev["angle"]) for ev in events if ev["phi0"] == ev["phi0"] and ev["angle"] == ev["angle"]]
    s = "사건 분류: " + ", ".join(parts)
    if dif:
        s += f"; 처음 장축 방향과 합체 방향의 차 중앙값 {np.median(dif):.1f}°"
    return s


# ---------------------------------------------------------------- 자가 시험
try:
    import cv2
except ImportError:                                      # 자가 시험의 둘레만 cv2를 쓴다(추적기와 같은 cv2 둘레)
    cv2 = None

# 이름, 반경 px, 법칙, 이동 px/frame, 정상 변형(흐름 방향 +면 늘어남), 합체 방향, d/H 구간(H 6 px)
DEMO_CASES = (
    ("stuck_exp", 30.0, "exp", 0.0, 0.0, "random", (8, 12)),
    ("stuck_pow", 45.0, "pow", 0.0, +0.06, "stream", (12, 20)),
    ("stuck_pin", 70.0, "pin", 0.0, 0.0, "random", (20, 30)),
    ("move_flat", 12.0, "exp", 4.3, -0.04, "stream", (3, 5)),
    ("move_long", 20.0, "exp", 4.3, +0.06, "stream", (5, 8)),
    ("move_rand", 30.0, "exp", 4.3, +0.06, "random", (8, 12)),
)


def _law_eps(kind, k):
    if kind == "exp":
        return 0.3 * math.exp(-k / 6)                    # τ 6 프레임 = 12 ms(500 fps)
    if kind == "pow":
        C = 0.828 / (6 * math.sqrt(0.3))                 # ε̇ = −Cε^1.5(m 2/3), 6프레임에 반
        return (0.3 ** -0.5 + C * k / 2) ** -2
    return 0.25 + 0.15 * math.exp(-k / 4)                # 멈춤 ε_r 0.25


def _ellipse(xx, yy, cx, cy, a, ev, flow):
    """흐름 기준 변형 벡터 ev = ε·(cos 2φ, sin 2φ)의 면적 보존 타원(장축 a√((1+ε)/(1−ε)))."""
    e = min(math.hypot(*ev), 0.9)
    phi = 0.5 * math.atan2(ev[1], ev[0])
    A_ax, B_ax = a * math.sqrt((1 + e) / (1 - e)), a * math.sqrt((1 - e) / (1 + e))
    ds, dc = to_flow(xx - cx, yy - cy, flow)
    u = ds * math.cos(phi) + dc * math.sin(phi)
    w = -ds * math.sin(phi) + dc * math.cos(phi)
    return (u / A_ax) ** 2 + (w / B_ax) ** 2 <= 1.0, (A_ax, B_ax)


def _perim(mask, axes):
    if cv2 is not None:                                  # 추적기(instances_to_detections)와 같은 둘레
        cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return float(sum(cv2.arcLength(c, True) for c in cs))
    A_ax, B_ax = axes
    return math.pi * (3 * (A_ax + B_ax) - math.sqrt((3 * A_ax + B_ax) * (A_ax + 3 * B_ax))) * 1.03


def make_demo(out, seed=11, n_rep=6, n_k=36, jitter=0.5):
    """합성 라벨 지도 + CSV(흐름 up). 사건마다 합체 직전 프레임에 반 면적 원 두 개(흡수될 트랙 = merged_into_ 행)를 그리고,
    합체 뒤 n_k 프레임 동안 법칙대로 이완하는 타원(정상 변형과 벡터로 더함)을 그린다. 같은 크기·속도·정상 변형의 조용한 기포 두 개가 기준선이다.
    모든 중심에 프레임마다 ±jitter px 고른 흔들림을 더해 화소화 산포(σ_b)와 cv2 둘레 잡음이 실제처럼 생기게 한다."""
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(out, "instances"), exist_ok=True)
    flow = "up"
    W, Hh = 520, 520
    yy, xx = np.indices((Hh, W))
    rows, truth = [], []
    frame, tid = 0, 0

    def add(inst, lab, m, fname, f, track, event, parent, axes):
        inst[m & (inst == 0)] = lab
        rows.append({"ファイル名": fname, "フレーム": f, "トラックID": track, "イベント": event, "親トラックID": parent,
                     "面積(px)": int(m.sum()), "中心X": f"{xx[m].mean():.3f}", "中心Y": f"{yy[m].mean():.3f}",
                     "周長(px)": f"{_perim(m, axes):.2f}", "フレーム接触": "0"})

    for name, a, law, V, eps_s, mode, _ in DEMO_CASES:
        for rep in range(n_rep):
            host, partner, quiet_ids = tid + 1, tid + 2, (tid + 3, tid + 4)
            tid += 4
            phi_m = rng.normal(0.0, math.radians(5)) if mode == "stream" else rng.uniform(-math.pi / 2, math.pi / 2)
            truth.append(dict(case=name, host=host, phi_m=math.degrees(phi_m)))
            cx0, cy0 = (260.0, 440.0) if V > 0 else (260.0, 200.0)
            qy0 = cy0 if V > 0 else 420.0
            steady = (eps_s, 0.0)
            for k in range(-1, n_k):
                inst = np.zeros((Hh, W), np.uint16)
                fname = f"f{frame:05d}.png"
                cy = cy0 - V * (k + 1)
                if k < 0:                                # 합체 직전: 반 면적 원 두 개, 합체 축 φ_m 위에 거의 닿게
                    r2 = a / math.sqrt(2)
                    dsx, dcx = math.cos(phi_m) * 1.04 * r2, math.sin(phi_m) * 1.04 * r2
                    for lab, track, sgn in ((1, host, -1), (4, partner, +1)):
                        # (s, c) 변위 → 영상(up: x = c, y = −s)
                        jx, jy = rng.uniform(-jitter, jitter, 2)
                        m, ax_ = _ellipse(xx, yy, cx0 + sgn * dcx + jx, cy - sgn * dsx + jy, r2, steady, flow)
                        add(inst, lab, m, fname, frame, track, "new", "", ax_)
                else:
                    e = _law_eps(law, k)
                    ev = (steady[0] + e * math.cos(2 * phi_m), steady[1] + e * math.sin(2 * phi_m))
                    jx, jy = rng.uniform(-jitter, jitter, 2)
                    m, ax_ = _ellipse(xx, yy, cx0 + jx, cy + jy, a, ev, flow)
                    add(inst, 1, m, fname, frame, host, "merge" if k == 0 else "normal", str(partner) if k == 0 else "", ax_)
                    if k == 0:
                        rows.append({"ファイル名": fname, "フレーム": frame, "トラックID": partner, "イベント": f"merged_into_{host}",
                                     "親トラックID": "", "面積(px)": 0, "中心X": "", "中心Y": "", "周長(px)": "", "フレーム接触": ""})
                for j, qid in enumerate(quiet_ids):
                    jx, jy = rng.uniform(-jitter, jitter, 2)
                    m, ax_ = _ellipse(xx, yy, 130.0 + 260 * j + jx, qy0 - V * (k + 1) + jy, a * 0.999, steady, flow)
                    add(inst, 2 + j, m, fname, frame, qid, "normal", "", ax_)
                np.savez_compressed(os.path.join(out, "instances", fname.replace(".png", ".npz")), inst=inst)
                frame += 1
    path = os.path.join(out, "demo_tracking.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path, 6.0, truth


def _old_way(events, quiet, bins, fps, skip=1):
    """검토 9 #5의 예전 방식: 크기 |ε⃗|(빼기 전)에서 구간 전체 조용한 기포의 ε² 중앙값을 제곱으로 뺀다(비교용)."""
    out = {}
    for lo, hi in bins:
        qv = [o[2][0] ** 2 + o[2][1] ** 2 for o in quiet if lo <= o[0] < hi and o[2][0] == o[2][0]]
        base = float(np.median(qv)) if len(qv) >= 10 else 0.0
        for motion in ("moving", "stuck"):
            evs = [ev for ev in events if lo <= ev["dH"] < hi and ev["motion"] == motion]
            if len(evs) < 3:
                continue
            med = []
            for k in range(max(len(ev["vec"]) for ev in evs)):
                v = [math.sqrt(max(ev["vec"][k][0] ** 2 + ev["vec"][k][1] ** 2 - base, 0.0)) for ev in evs
                     if k < len(ev["vec"]) and ev["vec"][k][0] == ev["vec"][k][0]]
                if len(v) < 3:
                    break
                med.append(float(np.median(v)))
            t = np.arange(len(med)) / fps
            e1 = np.array(med[skip:]); tt = t[skip:]
            ok = e1 > 0.003
            tau = float(-1 / np.polyfit(tt[ok], np.log(e1[ok]), 1)[0]) if ok.sum() >= 3 else NAN
            q = phase_plane_fit(t, med, 0.0, skip, 0.003)[0]
            out[(lo, hi, motion)] = (tau, q)
    return out


def _demo(out):
    path, Hpx, truth = make_demo(out)
    rows = read_rows(path)
    bins = ((3, 5), (5, 8), (8, 12), (12, 20), (20, 30))
    fps, px_m = 500.0, 2e-5
    want = {"stuck_exp": ((8, 12), "stuck", "q", 1.0), "stuck_pow": ((12, 20), "stuck", "q", 1.5),
            "stuck_pin": ((20, 30), "stuck", "pin", 0.25), "move_flat": ((3, 5), "moving", "tau", 0.012),
            "move_long": ((5, 8), "moving", "tau", 0.012), "move_rand": ((8, 12), "moving", "tau", 0.012)}
    case_of = {t_["host"]: t_["case"] for t_ in truth}
    fails = []
    if cv2 is None:
        print("참고: cv2가 없어 둘레를 해석식 × 1.03으로 그렸다(검토 9 #11의 cv2 둘레 치우침은 이 시험에 없다).")
    for label, masks in (("마스크 2차 모멘트", MaskLookup(os.path.join(out, "instances"))), ("둘레·면적(마스크 없음)", None)):
        events, quiet = collect(rows, Hpx, masks, flow="up", max_frames=35, quiet=40)
        prepare(events, Baseline(quiet), masks is not None, 1)
        res = analyse(events, bins, fps=fps, H_m=Hpx * px_m, px_m=px_m)
        print(f"[{label}] 사건 {len(events)}개. " + summarize_events(events))
        # 사건 분류·방향
        for name, (b, motion, _, _) in want.items():
            evs = [ev for ev in events if case_of.get(int(ev["track"])) == name]
            mot_ok = all(ev["motion"] == motion for ev in evs)
            stream = DEMO_CASES[[c[0] for c in DEMO_CASES].index(name)][5] == "stream"
            ori_ok = (not stream) or all(ev["orient"] == "s" for ev in evs)
            if not (len(evs) == 6 and mot_ok and ori_ok):
                fails.append(f"{label} {name} 분류(사건 {len(evs)}, 분류 {[ev['motion'] for ev in evs]}, 방향 {[ev['orient'] for ev in evs]})")
        for name, (b, motion, kind, val) in want.items():
            r = next((r for r in res if (r["dH_lo"], r["dH_hi"]) == b and r["motion"] == motion and r["orient"] == "all"), None)
            if r is None:
                fails.append(f"{label} {name}: 요약 없음")
                print(f"  실패  {label}: {name} 요약 없음")
                continue
            print("  " + describe(r))
            if kind == "pin":
                ok = r["pinned"] == 1 and abs(r["eps_r"] - val) <= 0.05
            elif masks is None:                          # 둘레 경로: 멈춤 여부만(작은 ε는 화소 둘레 잡음에 묻힘)
                ok = r["pinned"] == 0
            elif kind == "q":
                ok = abs(r["q"] - val) <= 0.3 and not r["pinned"]
            else:
                ok = abs(r["tau_exp_s"] / val - 1) <= 0.2 and not r["pinned"]
            print(f"  {'통과' if ok else '실패'}  {label}: {name}" + (f" (τ 참 {val * 1e3:.0f} ms)" if kind == "tau" else f" (참 {val})"))
            if not ok:
                fails.append(f"{label} {name}")
        if masks is None:
            print("  참고: 둘레 경로의 τ·q는 위처럼 치우친다(방향을 모르는 제곱 빼기·cv2 둘레 잡음, 검토 9 #5·#11). 이 경로는 멈춤 여부만 판정한다.")
        else:
            old = _old_way(events, quiet, bins, fps)
            for name in ("move_flat", "move_long", "stuck_pow"):
                b, motion, kind, val = want[name]
                tau_o, q_o = old.get((b[0], b[1], motion), (NAN, NAN))
                r = next((r for r in res if (r["dH_lo"], r["dH_hi"]) == b and r["motion"] == motion and r["orient"] == "all"), None)
                new = (f"τ {r['tau_exp_s'] * 1e3:.1f} ms" if kind == "tau" else f"q {r['q']:.2f}") if r else "없음"
                was = f"τ {tau_o * 1e3:.1f} ms" if kind == "tau" else f"q {q_o:.2f}"
                print(f"  비교 {name}(정상 변형 {DEMO_CASES[[c[0] for c in DEMO_CASES].index(name)][4]:+.2f}, 흐름 방향 합체): "
                      f"예전 제곱 빼기 {was} → 벡터 빼기 {new} (참 {'12 ms' if kind == 'tau' else '1.5'})")
    print("자가 시험 " + ("모두 통과" if not fails else f"실패 {len(fails)}건: " + ", ".join(fails)))
    return not fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv"); ap.add_argument("--fps", type=float, default=500.0)
    ap.add_argument("--px_mm", type=float, help="화소 하나의 크기(mm/px), 예 0.02")
    ap.add_argument("--H_mm", type=float, help="갭 H(mm)")
    ap.add_argument("--flow", default="up", choices=["up", "down", "right", "left"])
    ap.add_argument("--masks_dir", default="", help="추적기 instances/*.npz 폴더(SAVE_INSTANCE_MASKS). 주면 흐름 기준 변형 벡터를 쓴다")
    ap.add_argument("--max_frames", type=int, default=40)
    ap.add_argument("--quiet", type=int, default=10, help="기준선: 앞뒤 이 프레임 안에 사건이 없는 관측만")
    ap.add_argument("--skip", type=int, default=1, help="합체 직후 맞춤에서 뺄 프레임 수(목 동역학)")
    ap.add_argument("--dH_bins", default="2,5,15,50")
    ap.add_argument("--U_loc", type=float, default=float("nan"),
                    help="국소장 U_loc(m/s). 주면 움직이는 사건의 τ/τ₂를 1 + 1.9Δ(Δ = 2U_loc/V − 1, I107)와 비교한다")
    ap.add_argument("--mu", type=float, default=1.0e-3); ap.add_argument("--sigma", type=float, default=0.072)
    ap.add_argument("--out", default="mr_out"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raise SystemExit(0 if _demo(a.out) else 1)
    if not (a.csv and a.px_mm and a.H_mm):
        ap.error("--csv, --px_mm, --H_mm가 필요하다")
    if a.px_mm > 1:
        ap.error(f"--px_mm {a.px_mm:g}: 화소 하나의 크기(mm/px)를 넣는다(예 0.02). 1보다 크면 px/mm로 넣은 것 같다")
    os.makedirs(a.out, exist_ok=True)
    H_px = a.H_mm / a.px_mm
    masks = MaskLookup(a.masks_dir) if a.masks_dir else None
    events, quiet = collect(read_rows(a.csv), H_px, masks, a.flow, a.max_frames, a.quiet)
    prepare(events, Baseline(quiet), masks is not None, a.skip)
    edges = [float(v) for v in a.dH_bins.split(",")]
    res = analyse(events, list(zip(edges[:-1], edges[1:])), a.fps, a.H_mm * 1e-3, a.px_mm * 1e-3, a.mu, a.sigma, a.skip, a.U_loc)
    with open(os.path.join(a.out, "mr_events.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["track", "frame", "dH", "a_px", "V_px", "V_s_px", "merge_angle_deg", "orient", "phi0_deg", "motion", "rho",
                    "tau_ev_frames", "sigma_b", "n_base", "base_widen", "eps_series", "eps_mag_series"])
        for ev in events:
            w.writerow([ev["track"], ev["frame"], f"{ev['dH']:.2f}", f"{ev['a_px']:.2f}", f"{ev['V']:.3f}", f"{ev['V_s']:.3f}",
                        f"{ev['angle']:.1f}", ev["orient"], f"{ev['phi0']:.1f}", ev["motion"], f"{ev['rho']:.3g}",
                        f"{ev['tau_ev']:.3g}", f"{ev['sigma_b']:.4f}", ev["n_base"], f"{ev['base_how']:g}",
                        ";".join(f"{v:.4f}" if v == v else "" for v in ev["proj"]),
                        ";".join(f"{v:.4f}" if v == v else "" for v in ev["mag"])])
    if res:
        with open(os.path.join(a.out, "mr_classes.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            for r in res:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    print(f"합체 사건 {len(events)}개, 기준선 관측 {len(quiet)}개({'마스크: 흐름 기준 변형 벡터' if masks else '둘레·면적: 방향 모름'})")
    print(summarize_events(events))
    for r in res:
        print("  " + describe(r))
    if not masks:
        print("주의: 둘레 경로는 변형 방향을 모른다. 정상 변형과 같은 축의 합체(추월 합체)에서 τ·q가 치우친다(검토 9 #5) → --masks_dir를 권한다.")
    print("읽는 법: 움직이는 사건은 m과 상관없이 지수 감쇠다. τ/τ₂ = 1 + Φ_t ≈ 1 + 1.9Δ(I107)라 마찰 세기 Δ(= 2U_loc/V − 1)를 읽는다.")
    print("         m(q = 1/m: 1 지수, 1.5 깨끗한 막 2/3)은 멈춘 사건에서만 읽는다. ε_r > 0이면 원으로 돌아가지 않는다(마른 발자국, I107).")
    print("         사건이 적으면(< 10) 곡선이 시끄럽다. 흐름 방향·가로 합체의 τ가 다르면 이동 방향에 대한 마찰 비등방(R ≠ 1) 후보다.")


if __name__ == "__main__":
    main()

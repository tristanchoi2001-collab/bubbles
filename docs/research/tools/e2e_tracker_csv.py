"""연구 도구 끝까지 시험용 실제 형식 CSV 만들기: 합성 팬케이크 라벨 영상 → tests/fake_detector.fake_prob → 저장소 추적기의
extract_instances·instances_to_detections·run_laptrack·compute_velocity_ema·write_tracking_csv → result_tracking.csv + instances/*.npz.
저장소 코드는 고치지 않고 파일 경로로 불러온다(torch 불필요: scipy, scikit-image, opencv만). 결과 정리는 docs/research/tool_e2e_2026-10-24.md.
    python e2e_tracker_csv.py OUT --tracker bin      # binarized/2_bin_track.py, 흐름 up, 1080 × 416
    python e2e_tracker_csv.py OUT --tracker steel    # steel/2_steel_track.py, 흐름 right, 480 × 1200
도구에 줄 값: --px_mm 0.05(mm/px) --H_mm 0.3 --fps 500.
정답은 OUT/truth.json(구분별 속도, 큰 기포의 가로 표류, 합체 뒤 지수 완화 τ(프레임), 합체 목록).
--tracker bin  : binarized/2_bin_track.py, 흐름 up (영상 H×W = 1080×416, 흐름이 긴 축)
--tracker steel: steel/2_steel_track.py, 흐름 right (영상 480×1200). compute_velocity_ema에 검출을 넘겨 화면 끝에서 잘린 쪽을
                 피한다(steel/2_steel_track.py main과 같게, 검토 10 #22).
줄마다 생성 시각을 흩는다(첫 생성 프레임 0~주기−1, 간격 주기 ±25%, 검토 10 #23). 모든 줄이 같은 프레임에 만들어지면 프레임 수준 주기 신호가
    강해 실제 영상을 대표하지 못한다. --no_stagger는 예전 방식이다(같은 시드면 투명은 예전 CSV와 바이트까지 같고,
    철은 화면 끝에서 선단이 잘린 행의 속도 열만 다르다: 300 프레임에서 183행, 예 8.0 → 14.4 px/frame).
한계(실제 영상과 다른 점)
    - 상호작용 없음(각 기포는 자기 속도로 곧게 감) → 요동·공극률 파 도구는 영(null)이 나와야 하고, λ ≠ 0의 이득(쌍극자 장에 반응하는
      정도를 되찾는지)은 이 경로로 시험하지 않는다(각 도구의 자가 시험에만 있다).
    - 정답 마스크에서 만든 확률맵이라 분할 잡음·깜빡임이 없고, 이웃이 가까울 때 분할 경계가 중심을 미는 오차(거리·방향에 따라
      달라 쌍극자 회귀자와 상관할 수 있음)도 없다.
    - 크기가 두 무리(반경 8·20 px)와 합체한 것뿐이라 크기 분포가 실제보다 좁다."""
import os, sys, math, json, argparse, importlib.util, inspect
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests"))
ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--tracker", default="bin", choices=["bin", "steel"])
ap.add_argument("--nf", type=int, default=300); ap.add_argument("--seed", type=int, default=5)
ap.add_argument("--tau", type=float, default=12.0); ap.add_argument("--e0", type=float, default=0.3)
ap.add_argument("--drift", type=float, default=0.10, help="큰 기포의 가로 속도(px/frame, +c)")
ap.add_argument("--no_stagger", action="store_true", help="모든 줄을 같은 프레임에 만든다(예전 방식)")
a = ap.parse_args()
path = os.path.join(ROOT, "binarized/2_bin_track.py" if a.tracker == "bin" else "steel/2_steel_track.py")
spec = importlib.util.spec_from_file_location("tracker3", path)
T = importlib.util.module_from_spec(spec); sys.modules["tracker3"] = T; spec.loader.exec_module(T)
import fake_detector as FD
flow = "up" if a.tracker == "bin" else "right"
if a.tracker == "steel":
    T.FLOW_DIRECTION = "right"
Ls, Lc = (1080, 416) if flow == "up" else (1200, 480)      # 흐름 방향 길이, 가로 길이
H, W = (Ls, Lc) if flow == "up" else (Lc, Ls)
os.makedirs(os.path.join(a.out, "instances"), exist_ok=True)
rng = np.random.default_rng(a.seed)
V_SMALL, V_LARGE, R_SMALL, R_LARGE = (3.0, 7.0, 8.0, 20.0) if flow == "up" else (6.0, 14.0, 8.0, 20.0)
small_lanes = np.linspace(40, 0.45 * Lc, 5)
large_lanes = np.linspace(0.58 * Lc, Lc - 50, 3)
bub, nid = [], [0]
def spawn(c, R, v, vc, f0, s=-25.0):
    nid[0] += 1
    bub.append(dict(id=nid[0], s=s, c=c, A=math.pi * R * R, v=v, vc=vc, f_merge=None, e0=0.0, cls="small" if R < 12 else "large"))
spawn_small, spawn_large = 9, 16
lanes = ([dict(c=c, R=R_SMALL, v=V_SMALL, vc=0.0, period=spawn_small) for c in small_lanes]
         + [dict(c=c, R=R_LARGE, v=V_LARGE, vc=a.drift, period=spawn_large) for c in large_lanes])
for L in lanes:                                            # 줄마다 첫 생성 프레임(흩기: 0~주기−1)
    L["next"] = 0 if a.no_stagger else int(rng.integers(0, L["period"]))
log_merge = []
yy, xx = np.mgrid[0:H, 0:W]
names = []
dets_all = []
for f in range(a.nf):
    for L in lanes:
        if f >= L["next"]:
            spawn(L["c"] + rng.normal(0, 2), L["R"], L["v"] * (1 + 0.03 * rng.standard_normal()), L["vc"], f)
            jit = L["period"] // 4                         # 다음 생성까지 주기 ±25%
            L["next"] += L["period"] if a.no_stagger else L["period"] + int(rng.integers(-jit, jit + 1))
    # 이동
    for b in bub:
        b["s"] += b["v"]; b["c"] += b["vc"]
    # 합체(원 근사로 겹치면 하나로; 면적 보존, 위치·속도는 면적 가중)
    merged = True
    while merged:
        merged = False
        for i in range(len(bub)):
            for j in range(i + 1, len(bub)):
                p, q = bub[i], bub[j]
                Rp, Rq = math.sqrt(p["A"] / math.pi), math.sqrt(q["A"] / math.pi)
                if math.hypot(p["s"] - q["s"], p["c"] - q["c"]) < 0.98 * (Rp + Rq):
                    A = p["A"] + q["A"]
                    host, other = (p, q) if p["A"] >= q["A"] else (q, p)
                    host.update(s=(p["s"] * p["A"] + q["s"] * q["A"]) / A, c=(p["c"] * p["A"] + q["c"] * q["A"]) / A,
                                v=(p["v"] * p["A"] + q["v"] * q["A"]) / A, vc=(p["vc"] * p["A"] + q["vc"] * q["A"]) / A,
                                A=A, f_merge=f, e0=a.e0, cls="large" if A > math.pi * 12 ** 2 else "small")
                    log_merge.append(dict(frame=f, A=A, s=host["s"], c=host["c"]))
                    bub.remove(other)
                    merged = True
                    break
            if merged:
                break
    bub[:] = [b for b in bub if b["s"] < Ls + 30]
    lab = np.zeros((H, W), np.int32)
    for k, b in enumerate(bub, start=1):
        R = math.sqrt(b["A"] / math.pi)
        e = b["e0"] * math.exp(-(f - b["f_merge"]) / a.tau) if b["f_merge"] is not None else 0.0
        As, Ac = R * math.sqrt((1 + e) / (1 - e)), R * math.sqrt((1 - e) / (1 + e))   # 흐름 방향으로 늘어난 타원, 면적 보존
        if flow == "up":
            x0, y0, ax, ay = b["c"], Ls - b["s"], Ac, As
        else:
            x0, y0, ax, ay = b["s"], b["c"], As, Ac
        x_lo, x_hi = int(max(0, x0 - ax - 2)), int(min(W, x0 + ax + 3))
        y_lo, y_hi = int(max(0, y0 - ay - 2)), int(min(H, y0 + ay + 3))
        if x_lo >= x_hi or y_lo >= y_hi:
            continue
        sub = ((xx[y_lo:y_hi, x_lo:x_hi] - x0) / ax) ** 2 + ((yy[y_lo:y_hi, x_lo:x_hi] - y0) / ay) ** 2 <= 1.0
        lab[y_lo:y_hi, x_lo:x_hi][sub] = k
    p = FD.fake_prob(lab, T.UNET_CLOSE)
    inst = T.extract_instances(p, T.UNET_MIN_AREA, T.UNET_BAND, T.UNET_EDGE_THR, T.UNET_CLOSE, T.UNET_TINY_MAX)
    dets = T.instances_to_detections(inst, np.ones(lab.shape, bool))
    name = f"frame{f:04d}.png"
    np.savez_compressed(os.path.join(a.out, "instances", f"frame{f:04d}.npz"), inst=inst)
    names.append(name); dets_all.append(dets)
rows = T.run_laptrack(dets_all, image_size=(H, W))
if len(inspect.signature(T.compute_velocity_ema).parameters) >= 3:
    T.compute_velocity_ema(rows, a.nf, dets_all)          # 철 추적기: 화면 끝에서 선단이 잘리면 후단부 차분
else:
    T.compute_velocity_ema(rows, a.nf)
T.write_tracking_csv(os.path.join(a.out, "result_tracking.csv"), rows, names, dets_all)
json.dump(dict(flow=flow, H=H, W=W, V_small=V_SMALL, V_large=V_LARGE, R_small=R_SMALL, R_large=R_LARGE, drift_large=a.drift,
               tau=a.tau, e0=a.e0, stagger=not a.no_stagger, n_merge=len(log_merge), merges=log_merge[:400]),
          open(os.path.join(a.out, "truth.json"), "w"), indent=1)
print("merges", len(log_merge), "frames", a.nf, "->", a.out)

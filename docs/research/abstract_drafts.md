# 논문 초록 초안 (2026-10-24, 실험 전 가안)

> 목적: 신규성 주장이 논문에서 어떻게 읽힐지 미리 본다. 숫자는 실험 뒤에 채울 빈칸([…])이다. 결과 문장은 모두 **예상**이며, 실험이 반대로 나오면 설계 12장의 시나리오 표대로 고쳐 쓴다.
> 근거: 보고서 ①·④, 추정 5.4·5.5절, 설계 1·3·16·17·18장, 아이디어 I53·I54·I57·I58·I59·I61·I65.
> 2026-10-24 판별 평면(I73)·Sadatomi 1992 선례 반영. 같은 날 독립 검토 2(`review_2.md` 9·11번) 반영: "보인다" → "시험한다", 기본식은 2α/(1 − α) − B, 세 추정은 서로 독립이 아님, C 꼴은 폐합의 대수적 귀결(Chisholm 1967 선례), 3·7 mm는 "어디서 어떻게 깨지는지 그린다", 논문 2에 온도 조건과 Stefan 인자, 첫 문장의 근거 없는 주장 삭제.

## 논문 1 (단열): 영상 운동학으로 압력 강하를 맞춤 없이 예측

**제목 후보**: Pressure drop of confined bubbly flow in narrow gaps predicted from imaged bubble kinematics without fitted coefficients

**초록 (영문 초안)**
Two-phase pressure-drop correlations for narrow rectangular channels fit a Chisholm-type parameter C to flow rates and geometry, so they carry no explicit information on bubble size or shape. We test whether, in the pancake-bubble regime, the bubble-induced increase of the pressure drop follows from two kinematic quantities alone: the imaged void fraction α and the gas-to-liquid flow ratio B. Treating gap-spanning bubbles as two-dimensional inclusions in Darcy flow gives, for α ≲ 0.3, E = φ_L² − 1 = c·α/(1 − α) − (c − 1)·B with the shape factor c = 1 + b/a taken from the imaged aspect ratio (2α/(1 − α) − B for circular bubbles). The separated-flow model with measured void fraction used for narrow channels since Sadatomi et al. (1992), E = α/(1 − α), is the dipole-free limit c = 1. The closure contains no friction law or fitted constant; bubble size enters only through the aspect ratio and a rim correction of order H/d. In the plane y = E(1 − α)/α versus x = 1 − s̄, with the mean bubble mobility s̄ = B(1 − α)/α, the closure and the separated model are straight lines through (0, 1) and flow-rate correlations are lines through (1, 0). Changing only the injector at fixed flow rates therefore discriminates them by the slope: b/a − 2Q/(1 − α) for the closure, where the layout anisotropy Q is measured from the same images, zero for the separated model, and negative for flow-rate correlations. Random errors in α move points only towards (1, 0) and cannot create a positive slope on average; the rim convention, which can, is calibrated first against the gas flux. We test it in horizontal channels with gaps of 0.3, 0.7 and 1 mm using deep-learning detection and tracking of [N] bubbles, together with differential pressure. The void fraction implied by the pressure transient after switching the gas on agrees with the imaged one within [X]% (a test of the closure), and the gas flux carried by tracked bubbles agrees with the metered flow within [X]% (a test of gas conservation), for Ca < [..] and Re_H·H/d < [..]. Changing only the injector changes the pressure drop at fixed flow rates by [X]%, and we test whether all points remain on the same closure line; a flow-rate-based correlation has no term for this change. In Lockhart–Martinelli form the closure implies C = (μ_L/μ_G)^{1/2}B^{1/2}(2 − s̄)/s̄ − (μ_G/μ_L)^{1/2}B^{1/2}, a Hele-Shaw counterpart of the slip dependence in Chisholm's separated-flow theory, and one candidate reason why fitted C differs between facilities. At 3 and 7 mm, where bubbles no longer span the gap and inertia matters (Re_H·H/d up to about 10³), we map where and how the closure fails with the same imaging pipeline.

**초록 (한국어)**
좁은 직사각 유로의 이상류 압력 강하 상관식은 Chisholm 계수 C를 유량과 형상에 맞추므로, 기포 크기나 모양에 대한 정보를 직접 담지 않는다. 우리는 팬케이크 기포 영역에서 기포에 의한 압력 강하 증가분이 영상 기공률 α와 기체/액체 유량비 B 두 가지 운동학 양만으로 정해지는지 시험한다. 갭을 채운 기포를 Darcy 흐름 속 2차원 포함물로 보면 α ≲ 0.3에서 E = φ_L² − 1 = c·α/(1 − α) − (c − 1)·B이고, 모양 인자 c = 1 + b/a는 영상 종횡비에서 얻는다(원형이면 2α/(1 − α) − B). Sadatomi 외(1992) 이래 좁은 유로에 쓰인 측정 기공률 분리류 모델 E = α/(1 − α)는 쌍극자가 없는 c = 1 극한이다. 이 식에는 마찰 법칙과 맞춘 상수가 없고, 기포 크기는 종횡비와 H/d 차수의 가장자리 보정으로만 들어간다. 평균 기포 이동도 s̄ = B(1 − α)/α를 써서 y = E(1 − α)/α 대 x = 1 − s̄로 그리면 폐합과 분리류는 (0, 1)을, 유량 상관식은 (1, 0)을 지나는 직선이 된다. 그래서 같은 유량에서 주입기만 바꾼 점들의 기울기로 모델을 가른다: 폐합은 b/a − 2Q/(1 − α)(배치 비등방 Q도 같은 영상에서 잰다), 분리류는 0, 유량 상관식은 음수다. α의 무작위 오차는 점을 (1, 0) 쪽으로만 옮겨 기대값으로 양의 기울기를 만들지 못하고, 기울기를 바꿀 수 있는 윤곽 테두리 규약은 기체 유량으로 먼저 보정한다. 0.3·0.7·1 mm 수평 유로에서 딥러닝 검출·추적([N]개 기포)과 차압으로 시험한다. 기체를 켤 때의 압력 과도가 말하는 기공률은 영상 기공률과 [X]% 안에서 일치하고(폐합의 시험), 추적한 기포가 나르는 기체 유량은 유량계 값과 [X]% 안에서 일치한다(기체 보존의 시험). 범위는 Ca < [..], Re_H·H/d < [..]다. 주입기만 바꾸면 같은 유량에서 압력 강하가 [X]% 달라지고, 모든 점이 같은 폐합 선에 남는지 시험한다. 유량만 쓰는 상관식에는 이 변화를 나타낼 항이 없다. Lockhart–Martinelli 꼴로 쓰면 폐합에서 C = (μ_L/μ_G)^{1/2}B^{1/2}(2 − s̄)/s̄ − (μ_G/μ_L)^{1/2}B^{1/2}가 나온다. 이것은 Chisholm 분리류 이론의 미끄럼 의존을 Hele-Shaw 기포류에 맞게 다시 쓴 꼴이며, 장치마다 맞춘 C가 다른 이유의 후보 하나다. 기포가 갭을 채우지 않고 관성이 커지는(Re_H·H/d 최대 약 10³) 3·7 mm에서는 같은 영상 처리로 폐합이 어디서 어떻게 깨지는지 그린다.

**기여 (심사자가 볼 순서)**
1. 맞춘 상수 없는 폐합과 그 시험(원형·α ≲ 0.3·Darcy 범위 안. 속도 없이 α·B만으로도, 추적이 있으면 더 강하게).
2. 기체 계단 응답: 켜는 순간의 계단으로 유량계 없이 β(0.3·0.7 mm에서 정밀), 과도로 압력이 말하는 기공률 α_P(폐합 가정).
3. Chisholm 1967의 미끄럼 의존을 Hele-Shaw 기포류에 맞게 쓴 꼴(E/B = (2 − s̄)/s̄)과, 주입기를 바꾸는 반증 실험.
4. 검출·추적 오차(사람 감사, 기체 보존)를 결론까지 전파.

**미리 정해 둘 약점과 답**
- "유효 매질 식은 고전 이론이다" → 맞다. C와 미끄럼의 연결도 Chisholm 1967에 있다. 새 것은 기액 흐름에서의 맞춤 없는 시험, 압력으로 재는 기공률·이동도, 주입기 바꾸기로 하는 크기 의존 시험이다.
- "범용 상관식(예: Kim & Mudawar 2012)은 여러 자료를 평균 오차 약 20%대로 맞춘다고 한다(원문 수치 확인 필요)" → 모델의 C도 기존 상관식과 같은 자릿수다(그림 r7). 우리 주장은 정확도 경쟁이 아니라 "같은 유량에서 크기를 바꾸면 ΔP가 바뀌는가"다. 유량만 쓰는 상관식은 이 질문에 답하지 못한다.
- "0.3 mm만 맞고 1 mm는 어긋난다" → 성립 범위를 Re_H·H/d로 그리는 것이 결과다(시나리오 S5).
- "영상 기공률의 윤곽 규약" → 합체 면적 수지와 기체 보존으로 교정, 오차 전파. 작은 기포 경로와 주 경로의 윤곽 전환(면적 ×1.5~1.9)은 E로 0.05~0.1 차이를 낼 수 있으므로 따로 보정한다(보고서 5.4 점검 3단계).

## 논문 1 — 속도 중심판 (2026-10-24, 사용자 방향 "공극률이 아니라 추적 속도로 연결", I89~I91·I95)

**제목 후보**
- Tracked bubble velocities close the pressure drop of confined bubbly flow in narrow gaps
- The excess pressure drop of pancake bubbles is the sum of their friction forces: a velocity-based test with image tracking

**초록 (영문 초안)**
In narrow horizontal gaps, gap-spanning (pancake) bubbles move through liquid in Darcy flow. The wall friction of the liquid is linear in its local velocity, so its integral depends only on the superficial liquid velocity. The excess two-phase pressure drop is therefore exactly the sum of the friction forces on the bubble footprints, and each of these depends only on that bubble's own speed and shape. We test this force balance in gaps of 0.3, 0.7 and 1 mm using deep-learning detection and tracking of [N] bubbles with synchronised differential pressure, without using void fraction, bubble layout or a mean-field assumption. With the meniscus friction of clean interfaces (D ≈ 17σaCa^(2/3)), the tracked velocities predict the excess pressure drop within [..]% at [..] operating points. Regressing the pressure on the tracked velocities gives the friction coefficient and its velocity exponent [m = ..], which separate clean films (2/3), rigid interfaces (≈ 1/2) and dry footprints (≈ 0). Dividing each bubble's speed by the mean of the pressure-implied Darcy velocity and the total flux collapses all operating points onto one single-bubble mobility curve, as the two-dimensional local-field theory predicts. The classical void-fraction closure follows as the mean-field limit, and we show where it fails ([α ≳ 0.2], aligned layouts). The same capillary number sets the film thickness that governs footprint heat transfer and dryout, which links the adiabatic friction measurement to heated operation. The velocity–size curve also shows directly where bubbles stop spanning the gap at 3 and 7 mm.

**초록 (한국어 대역)**
좁은 수평 갭에서 갭을 채운 팬케이크 기포는 Darcy 흐름의 액체 속을 움직인다. 액체의 벽 마찰은 국소 속도에 선형이라 그 합이 겉보기 액체 속도로만 정해진다. 그래서 이상류의 초과 압력 강하는 정확히 기포 발자국에 걸리는 마찰력의 합이고, 각 마찰력은 그 기포 자신의 속도와 모양에만 달린다. 우리는 0.3, 0.7, 1 mm 갭에서 딥러닝 검출·추적한 기포 [N]개와 동기화한 차압으로, 공극률·배치·평균장 가정 없이 이 힘 균형을 시험한다. 깨끗한 계면의 메니스커스 마찰(D ≈ 17σaCa^(2/3))을 쓰면 추적 속도가 [..]개 운전점의 초과 압력 강하를 [..]% 안으로 예측한다. 압력을 추적 속도에 회귀하면 마찰 계수와 속도 지수 [m = ..]가 나오고, 이것이 깨끗한 막(2/3), 굳은 계면(약 1/2), 마른 발자국(약 0)을 가른다. 각 기포의 속도를 압력이 말하는 Darcy 속도와 전체 유량의 평균으로 나누면, 2차원 국소장 이론의 예측대로 모든 운전점이 단일 기포 이동도 곡선 하나에 모인다. 고전적 공극률 폐합은 그 평균장 극한으로 나오고, 어디서 깨지는지([α ≳ 0.2], 정렬된 배치) 보인다. 같은 모세관 수가 발자국 열전달과 마름을 정하는 막 두께를 정하므로, 단열 마찰 측정이 가열 운전으로 이어진다. 속도–크기 곡선은 3·7 mm에서 기포가 갭을 채우지 않게 되는 곳도 바로 보여 준다.

**심사자 관점에서 새것 (초안)**
1. 2차원 Darcy 기포 흐름의 정확한 힘 균형(초과 ΔP = Σ 기포 마찰)과, 그것을 기포 수천 개의 추적 속도로 닫는 시험. 1차원 Taylor 흐름의 합 모델과 2차원 거품의 판 마찰을 잇는 중간 영역(묽은~중간 기공률, 크기가 섞임)이다.
2. 압력으로 기포 마찰 법칙(계수, 지수, 크기별)을 재서 발자국 젖음 상태를 읽는 방법.
3. 이동도 붕괴 정규화 (U_P + J)/2와, 공극률 폐합이 "힘 균형 + 평균장"이라는 분해. 수치 확인(I82): 힘 균형은 모든 α에서 0.1~0.3%, 공극률 폐합은 α 0.4에서 7% 벗어난다.
4. 공극률 대신 속도를 쓰므로 윤곽 규약 오차에 강하다(위치의 차).

## 논문 2 (가열): 갭에 따른 공기 주입 열전달을 접촉·갱신·증발로 설명

**제목 후보**: Gap-dependent heat transfer of air-injected flow in narrow channels over an opaque heated wall: contact, renewal and evaporation resolved by image-informed inverse conduction

**초록 (영문 초안)**
Air injection can raise or lower heat transfer in narrow channels, and image-based correlations have so far been fitted for single channels. We heat a steel wall below horizontal gaps of [0.3–7] mm, inject air, and image the flow from above through the cover. An image-informed inverse conduction method uses the bubble footprint and the time since the last bubble passage at every pixel as the spatial pattern of the boundary condition, so that a few coefficients — liquid renewal and footprint conductance — are fitted to all embedded thermocouples at once. The footprint conductance exceeds gas conduction already at [50] °C and rises to [..] kW/m²K at [90] °C, following (dp_sat/dT)·P/(P − p_v) as expected for Stefan-enhanced vapour diffusion inside the bubbles. In near-isothermal runs with preheated liquid and gas, the vapour added to the bubbles, inferred from the pressure closure as B_eff/B_in, agrees with the bubble-volume budget within [X]% at 90 °C. The ratio of two-phase to single-phase heat transfer collapses on the contact fraction, a renewal Fourier number and the footprint-to-liquid conductance ratio, h_TP/h_1φ ≈ (1 − φ_c)·max[1, 0.42·Fo^{-1/2}] + φ_c·r_b(T), predicting a gap left out of the fit within [X]%. Below about 50 °C, heat transfer drops below the single-phase value at 0.3 mm and low passage frequency; above about 80 °C the footprints conduct better than the liquid in every gap.

**초록 (한국어)**
공기를 넣으면 좁은 유로의 열전달이 오르기도 내리기도 하며, 영상 기반 상관식은 지금까지 채널 하나에 맞춘 것이었다. 우리는 수평 갭 [0.3~7] mm의 아래 철 벽을 가열하고 공기를 넣어 위 덮개 너머로 촬영한다. 영상 정보 역열전도는 화소마다 기포 발자국과 마지막 기포가 지나간 뒤의 시간을 경계조건의 공간 모양으로 쓰므로, 몇 개의 계수(액체 갱신, 발자국 전도)만 모든 매립 열전대에 함께 맞춘다. 발자국 전도는 [50] °C에서 이미 기체 전도보다 크고 [90] °C에서 [..] kW/m²K까지 커지며, (dp_sat/dT)·P/(P − p_v)를 따르는 모양이 Stefan 흐름이 더해진 기포 속 수증기 확산과 맞는다. 액체와 기체를 미리 데운 거의 등온 운전에서, 압력 폐합으로 추정한 증기 몫(B_eff/B_in)은 90 °C에서 기포 부피 수지와 [X]% 안에서 일치한다. 이상/단상 열전달 비는 접촉 비율, 갱신 Fourier 수, 발자국/액체 전도 비로 모이고(h_TP/h_1φ ≈ (1 − φ_c)·max[1, 0.42·Fo^{-1/2}] + φ_c·r_b(T)), 맞춤에서 뺀 갭을 [X]% 안에서 예측한다. 약 50 °C 이하에서는 0.3 mm 저빈도에서 단상보다 낮아지고, 약 80 °C 이상에서는 모든 갭에서 발자국이 액체보다 잘 전도한다.

**기여**
1. 불투명 금속 가열면에서 영상으로 경계조건 모양을 정하는 역열전도(I59).
2. 공기 주입의 숨은 항(기체 부피 변화, 잠열, 기포 속 열관)을 두 추정(압력 폐합의 B_eff/B_in, 영상 부피 수지)으로 정량(I29, I47, I57). 둘 다 영상 α를 쓰므로 완전히 독립은 아니다. 70 °C는 약 2σ(α 오차가 지배), 90 °C는 B_in ≈ 0.1로 잡으면 뚜렷하다.
3. 갭 하나 빼기로 시험한 물리 모델(I7, I65). 발자국/액체 전도 비 r_b(T)는 갭과 무관하고(둘 다 1/H에 비례) 약 75~80 °C에서 1을 넘는다(그림 r8).

**미리 정해 둘 약점과 답**
- "영상 → 열전달은 이미 있다(Huang 2024 등)" → 그들은 채널 하나·비등·회귀다. 우리는 갭 여러 개·비등 없음·물리 모델·역열전도다.
- "증발이 작으면?" → 50 °C 이하 결과만으로도 접촉·갱신 모델이 선다. 증발은 70 °C 이상의 추가 결과로 둔다.
- "가열 운전의 ΔP 차이는 점성 변화 때문 아니냐" → 기포가 벽 온도를 1 K 바꿀 때 마찰이 약 0.5~0.9% 바뀌어 E로 0.005~0.03이 된다(판별력과 같은 크기). 그래서 증발 판정은 거의 등온 운전으로 한다.

## 논문 2 — 속도 중심판 (2026-10-24, I90·I92·I94·I96·I97)

**제목 후보**
- Bubble velocities from image tracking predict film, evaporation and heat transfer of air injection in heated narrow gaps
- From friction to heat: tracked pancake-bubble velocities set the wall films that govern heat transfer in heated microgaps

**초록 (영문 초안)**
Injecting air into a heated narrow gap changes heat transfer through three bubble-scale processes: conduction and evaporation through the thin liquid film under each bubble footprint, renewal of the thermal boundary layer between bubbles, and evaporation into the bubbles. All three are set by bubble kinematics. The capillary number of a tracked bubble sets its film thickness (h_f ≈ 0.67·H·Ca^(2/3) for clean interfaces). The friction coefficient measured from the adiabatic pressure drop with the same tracked velocities [paper 1] tells whether the interfaces are clean or rigid, and hence the film thickness to within [..]%. Passage statistics from tracking give the residence and renewal times at every wall point. The downstream growth of the imaged gas flux, Σ A·h_g·V, measures the evaporation rate along the channel without a model of the gas phase. In gaps of [0.3, 0.7, 1] mm at wall temperatures of 50–90 °C, a kinematic model built from these quantities predicts the local heat transfer coefficients obtained by image-informed inverse conduction from embedded thermocouples within [..]%, and the latent fraction of the heat input within [..]. Velocity fluctuations of tracked bubbles act as an in-situ flowmeter and reveal the onset of flow oscillations before the pressure signal does. On the steel heater, velocity modulation over machined grooves gives the pinning force per groove, which [does/does not] correlate with the dark footprint contrast that would indicate dry patches.

**초록 (한국어 대역)**
가열된 좁은 갭에 공기를 넣으면 기포 크기의 세 과정이 열전달을 바꾼다. 각 기포 발자국 밑 얇은 액막을 통한 전도와 증발, 기포 사이 열경계층의 재생, 기포 안으로의 증발이다. 셋 모두 기포 운동학이 정한다.
- 추적한 기포의 모세관 수가 막 두께(깨끗한 계면이면 h_f ≈ 0.67·H·Ca^(2/3))를 정한다.
- 같은 추적 속도로 단열 압력 강하에서 잰 마찰 계수[논문 1]가 계면이 깨끗한지 굳었는지, 따라서 막 두께를 [..]% 안으로 알려 준다.
- 추적의 통과 통계는 벽 위 모든 점의 머무름·재생 시간을 준다.
- 영상 기체 유량 Σ A·h_g·V의 하류 증가는 기체상 모형 없이 길이 방향 증발률을 잰다.
[0.3, 0.7, 1] mm 갭, 벽 온도 50~90 °C에서 이 양들로 만든 운동학 모형이 매립 열전대의 영상 정보 역열전도로 얻은 국소 열전달 계수를 [..]% 안으로, 열 입력 중 잠열 몫을 [..] 안으로 예측한다. 추적 기포의 속도 요동은 시험부 안 유량계가 되어, 압력 신호보다 먼저 유량 진동의 시작을 보여 준다. 철 가열면에서는 가공 홈 위의 속도 변조로 홈 하나의 고정력을 재고, 그것이 마른 자리를 뜻하는 어두운 발자국 대비와 상관이 [있는지/없는지] 본다.


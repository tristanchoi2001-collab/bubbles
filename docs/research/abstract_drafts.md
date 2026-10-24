# 논문 초록 초안 (2026-10-24, 실험 전 가안)

> 목적: 신규성 주장이 논문에서 어떻게 읽힐지 미리 본다. 숫자는 실험 뒤에 채울 빈칸([…])이다. 결과 문장은 모두 **예상**이며, 실험이 반대로 나오면 설계 12장의 시나리오 표대로 고쳐 쓴다.
> 근거: 보고서 ①·④, 추정 5.4·5.5절, 설계 1·3·16·17·18장, 아이디어 I53·I54·I57·I58·I59·I61·I65.
> 2026-10-24 독립 검토 2(`review_2.md` 9·11번) 반영: "보인다" → "시험한다", 기본식은 2α/(1 − α) − B, 세 추정은 서로 독립이 아님, C 꼴은 폐합의 대수적 귀결(Chisholm 1967 선례), 3·7 mm는 "어디서 어떻게 깨지는지 그린다", 논문 2에 온도 조건과 Stefan 인자, 첫 문장의 근거 없는 주장 삭제.

## 논문 1 (단열): 영상 운동학으로 압력 강하를 맞춤 없이 예측

**제목 후보**: Pressure drop of confined bubbly flow in narrow gaps predicted from imaged bubble kinematics without fitted coefficients

**초록 (영문 초안)**
Two-phase pressure-drop correlations for narrow rectangular channels fit a Chisholm-type parameter C to flow rates and geometry, so they carry no explicit information on bubble size or shape. We test whether, in the pancake-bubble regime, the bubble-induced increase of the pressure drop follows from two kinematic quantities alone: the imaged void fraction α and the gas-to-liquid flow ratio B. Treating gap-spanning, near-circular bubbles as two-dimensional inclusions in Darcy flow gives, for α ≲ 0.3, φ_L² − 1 = 2α/(1 − α) − B, equivalently B(2 − s̄)/s̄ with the mean bubble mobility s̄ = B(1 − α)/α. The closure contains no friction law or fitted constant; bubble size enters only through a geometric rim correction of order H/d. We test it in horizontal channels with gaps of 0.3, 0.7 and 1 mm using deep-learning detection and tracking of [N] bubbles, together with differential pressure. The void fraction implied by the pressure transient after switching the gas on agrees with the imaged one within [X]% (a test of the closure), and the gas flux carried by tracked bubbles agrees with the metered flow within [X]% (a test of gas conservation), for Ca < [..] and Re_H·H/d < [..]. Changing only the injector changes the pressure drop at fixed flow rates by [X]%, and we test whether all points remain on the same closure line; a flow-rate-based correlation has no term for this change. In Lockhart–Martinelli form the closure implies C = (μ_L/μ_G)^{1/2}B^{1/2}(2 − s̄)/s̄ − (μ_G/μ_L)^{1/2}B^{1/2}, a Hele-Shaw counterpart of the slip dependence in Chisholm's separated-flow theory, and one candidate reason why fitted C differs between facilities. At 3 and 7 mm, where bubbles no longer span the gap and inertia matters (Re_H·H/d up to about 10³), we map where and how the closure fails with the same imaging pipeline.

**초록 (한국어)**
좁은 직사각 유로의 이상류 압력 강하 상관식은 Chisholm 계수 C를 유량과 형상에 맞추므로, 기포 크기나 모양에 대한 정보를 직접 담지 않는다. 우리는 팬케이크 기포 영역에서 기포에 의한 압력 강하 증가분이 영상 기공률 α와 기체/액체 유량비 B 두 가지 운동학 양만으로 정해지는지 시험한다. 갭을 채운 원에 가까운 기포를 Darcy 흐름 속 2차원 포함물로 보면 α ≲ 0.3에서 φ_L² − 1 = 2α/(1 − α) − B이고, 같은 식을 평균 기포 이동도 s̄ = B(1 − α)/α로 쓰면 B(2 − s̄)/s̄다. 이 식에는 마찰 법칙과 맞춘 상수가 없고, 기포 크기는 H/d 차수의 가장자리 기하 보정으로만 들어간다. 0.3·0.7·1 mm 수평 유로에서 딥러닝 검출·추적([N]개 기포)과 차압으로 시험한다. 기체를 켤 때의 압력 과도가 말하는 기공률은 영상 기공률과 [X]% 안에서 일치하고(폐합의 시험), 추적한 기포가 나르는 기체 유량은 유량계 값과 [X]% 안에서 일치한다(기체 보존의 시험). 범위는 Ca < [..], Re_H·H/d < [..]다. 주입기만 바꾸면 같은 유량에서 압력 강하가 [X]% 달라지고, 모든 점이 같은 폐합 선에 남는지 시험한다. 유량만 쓰는 상관식에는 이 변화를 나타낼 항이 없다. Lockhart–Martinelli 꼴로 쓰면 폐합에서 C = (μ_L/μ_G)^{1/2}B^{1/2}(2 − s̄)/s̄ − (μ_G/μ_L)^{1/2}B^{1/2}가 나온다. 이것은 Chisholm 분리류 이론의 미끄럼 의존을 Hele-Shaw 기포류에 맞게 다시 쓴 꼴이며, 장치마다 맞춘 C가 다른 이유의 후보 하나다. 기포가 갭을 채우지 않고 관성이 커지는(Re_H·H/d 최대 약 10³) 3·7 mm에서는 같은 영상 처리로 폐합이 어디서 어떻게 깨지는지 그린다.

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

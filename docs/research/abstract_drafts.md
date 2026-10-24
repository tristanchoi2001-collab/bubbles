# 논문 초록 초안 (2026-10-24, 실험 전 가안)

> 목적: 신규성 주장이 논문에서 어떻게 읽힐지 미리 본다. 숫자는 실험 뒤에 채울 빈칸([…])이다. 결과 문장은 모두 **예상**이며, 실험이 반대로 나오면 설계 12장의 시나리오 표대로 고쳐 쓴다.
> 근거: 보고서 ①·④, 추정 5.4·5.5절, 설계 1·3·16·17·18장, 아이디어 I53·I54·I57·I58·I59·I61.

## 논문 1 (단열): 영상 운동학으로 압력 강하를 맞춤 없이 예측

**제목 후보**: Pressure drop of confined bubbly flow in narrow gaps predicted from imaged bubble kinematics without fitted coefficients

**초록 (영문 초안)**
Two-phase pressure-drop correlations for narrow rectangular channels fit a Chisholm-type parameter to flow rates and geometry, and their coefficients rarely transfer between facilities. We show that in the pancake-bubble regime the bubble-induced increase of the pressure drop follows from two kinematic quantities alone: the imaged area void fraction α and the gas-to-liquid flow ratio B. Treating gap-spanning bubbles as two-dimensional inclusions in Darcy flow gives φ_L² − 1 = B(2 − s̄)/s̄, where s̄ = B(1 − α)/α is the mean bubble mobility. The closure contains no bubble size, friction law, or fitted constant. We test it in horizontal channels with gaps of 0.3, 0.7 and 1 mm using deep-learning detection and tracking of [N] bubbles, together with differential pressure. Three independent estimates of s̄ — from the pressure transient after switching the gas on, from the imaged void fraction, and from tracked bubble velocities — agree within [X]% for Ca < [..] and Re_H·H/d < [..]. Changing only the injector changes the pressure drop at fixed flow rates by [X]%, yet all points fall on the same closure line, whereas a flow-rate-based Chisholm parameter would predict no change. The fitted Chisholm parameter therefore reflects bubble mobility, C ≈ (μ_L/μ_G)^{1/2} B^{1/2} (2 − s̄)/s̄. At 3 and 7 mm the closure fails in the way predicted by buoyancy (half-gap Bond number), which we map with the same imaging pipeline.

**초록 (한국어)**
좁은 직사각 유로의 이상류 압력 강하 상관식은 Chisholm 계수를 유량과 형상에 맞추며, 그 계수는 장치가 바뀌면 잘 맞지 않는다. 우리는 팬케이크 기포 영역에서 기포에 의한 압력 강하 증가분이 영상 기공률 α와 기체/액체 유량비 B 두 가지 운동학 양만으로 정해짐을 보인다. 갭을 채운 기포를 Darcy 흐름 속 2차원 포함물로 보면 φ_L² − 1 = B(2 − s̄)/s̄이고, s̄ = B(1 − α)/α는 평균 기포 이동도다. 이 식에는 기포 크기, 마찰 법칙, 맞춘 상수가 없다. 0.3·0.7·1 mm 수평 유로에서 딥러닝 검출·추적([N]개 기포)과 차압으로 시험한다. 평균 이동도를 세 가지(기체를 켤 때의 압력 과도, 영상 기공률, 추적 속도)로 재면 Ca < [..], Re_H·H/d < [..]에서 [X]% 안에서 일치한다. 주입기만 바꾸면 같은 유량에서 압력 강하가 [X]% 달라지지만 모든 점이 같은 폐합 선에 놓인다. 유량만 쓰는 Chisholm 계수는 이 차이를 예측하지 못한다. 그래서 맞춘 Chisholm 계수는 기포 이동도를 반영한다: C ≈ (μ_L/μ_G)^{1/2} B^{1/2} (2 − s̄)/s̄. 3·7 mm에서는 부력(반높이 Bond 수)이 예측하는 방식으로 폐합이 깨지며, 같은 영상 처리로 그 경계를 그린다.

**기여 (심사자가 볼 순서)**
1. 맞춘 상수 없는 폐합과 그 시험(속도 없이 α·B만으로도, 추적이 있으면 더 강하게).
2. 압력만으로 평균 기포 이동도를 재는 방법(기체 계단 응답), 유량계 없이 B를 재는 방법(켜는 순간의 계단).
3. Chisholm 계수의 물리적 해석과, 주입기를 바꾸는 반증 실험.
4. 검출·추적 오차(사람 감사, 기체 보존)를 결론까지 전파.

**미리 정해 둘 약점과 답**
- "유효 매질 식은 고전 이론이다" → 맞다. 새 것은 기액 흐름에서의 맞춤 없는 시험, 압력으로 재는 이동도, C의 해석이다.
- "0.3 mm만 맞고 1 mm는 어긋난다" → 성립 범위를 Re_H·H/d로 그리는 것이 결과다(시나리오 S5).
- "영상 기공률의 윤곽 규약" → 합체 면적 수지와 기체 보존으로 교정, 오차 전파.

## 논문 2 (가열): 갭에 따른 공기 주입 열전달을 접촉·갱신·증발로 설명

**제목 후보**: Gap-dependent heat transfer of air-injected flow in narrow channels over an opaque heated wall: contact, renewal and evaporation resolved by image-informed inverse conduction

**초록 (영문 초안)**
Air injection can raise or lower heat transfer in narrow channels, and image-based correlations have so far been fitted for single channels. We heat a steel wall below horizontal gaps of [0.3–7] mm, inject air, and image the flow from above through the cover. An image-informed inverse conduction method uses the bubble footprint and the time since the last bubble passage at every pixel as the spatial pattern of the boundary condition, so that a few coefficients — liquid renewal and footprint conductance — are fitted to all embedded thermocouples at once. The footprint conductance exceeds gas conduction already at [50] °C and rises to [..] kW/m²K at [90] °C, following the slope of the saturation vapour pressure as expected for vapour diffusion inside the bubbles, and the evaporation inferred from the pressure closure agrees with the bubble-volume budget within [X]%. The ratio of two-phase to single-phase heat transfer collapses on the contact fraction and a renewal Fourier number, h_TP/h_1φ ≈ (1 − φ_c)·max[1, 0.42·Fo^{-1/2}], predicting a gap left out of the fit within [X]%. Heat transfer drops below the single-phase value at 0.3 mm and low passage frequency, and is enhanced at 1 mm.

**초록 (한국어)**
공기를 넣으면 좁은 유로의 열전달이 오르기도 내리기도 하며, 영상 기반 상관식은 지금까지 채널 하나에 맞춘 것이었다. 우리는 수평 갭 [0.3~7] mm의 아래 철 벽을 가열하고 공기를 넣어 위 덮개 너머로 촬영한다. 영상 정보 역열전도는 화소마다 기포 발자국과 마지막 기포가 지나간 뒤의 시간을 경계조건의 공간 모양으로 쓰므로, 몇 개의 계수(액체 갱신, 발자국 전도)만 모든 매립 열전대에 함께 맞춘다. 발자국 전도는 [50] °C에서 이미 기체 전도보다 크고 [90] °C에서 [..] kW/m²K까지 커지며, 포화 증기압 기울기를 따르는 모양이 기포 속 수증기 확산과 맞는다. 압력 폐합으로 추정한 증발량은 기포 부피 수지와 [X]% 안에서 일치한다. 이상/단상 열전달 비는 접촉 비율과 갱신 Fourier 수로 모이고(h_TP/h_1φ ≈ (1 − φ_c)·max[1, 0.42·Fo^{-1/2}]), 맞춤에서 뺀 갭을 [X]% 안에서 예측한다. 0.3 mm 저빈도에서는 단상보다 낮아지고, 1 mm에서는 강화된다.

**기여**
1. 불투명 금속 가열면에서 영상으로 경계조건 모양을 정하는 역열전도(I59).
2. 공기 주입의 숨은 항(기체 부피 변화, 잠열, 기포 속 열관)을 두 독립 추정(압력·영상)으로 정량(I29, I47, I57).
3. 갭 하나 빼기로 시험한 물리 모델(I7).

**미리 정해 둘 약점과 답**
- "영상 → 열전달은 이미 있다(Huang 2024 등)" → 그들은 채널 하나·비등·회귀다. 우리는 갭 여러 개·비등 없음·물리 모델·역열전도다.
- "증발이 작으면?" → 50 °C 이하 결과만으로도 접촉·갱신 모델이 선다. 증발은 70 °C 이상의 추가 결과로 둔다.

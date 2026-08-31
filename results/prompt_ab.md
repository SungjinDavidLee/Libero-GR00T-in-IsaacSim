# 지시문 변형 원본

공간 관계를 명시하고 목표 유지·안전 이탈·안정 완료를 문장으로 추가한 지시문의 대조 실험이다.

---

## 1. 지시문

| # | 원문 | 변형 |
|---|---|---|
| T0 | pick up the black bowl between the plate and the ramekin and place it on the plate | Locate the black bowl positioned between the plate and the ramekin. Pick up that same bowl and place it fully and stably on the plate. |
| T3 | pick up the black bowl on the cookie box and place it on the plate | Locate the black bowl resting on top of the cookie box. Pick up that same bowl, lift it clear of the box, and place it fully on the plate. |
| T6 | pick up the black bowl next to the cookie box and place it on the plate | Locate the black bowl directly next to the cookie box. Pick up that same bowl and place it fully and stably on the plate. |
| T9 | pick up the black bowl on the wooden cabinet and place it on the plate | Locate the black bowl resting on top of the wooden cabinet. Pick up that same bowl, lift it clear of the cabinet, and place it fully on the plate. |

변형안의 설계 원칙은 목표 물체 → 공간 단서·기준 물체 → 동일 대상 유지 → 안전 이탈 → 목적지 → 안정적 완료 조건 순서다. 좌·우·전·후 관계나 시뮬레이터 좌표는 추가하지 않았다.

---

## 2. 결과

태스크당 12 에피소드. 다른 파라미터는 동일하다.

| 태스크 | 원문 배치 | 변형 배치 | 원문 무교란 | 변형 무교란 | 원문 상승량 | 변형 상승량 |
|---|---|---|---|---|---|---|
| T0 | 8 / 12 | 7 / 12 | 3 | 1 | 0.054 | 0.050 |
| T3 | 6 / 12 | **2 / 12** | 1 | 0 | 0.062 | 0.047 |
| T6 | 1 / 12 | 1 / 12 | 0 | 0 | 0.041 | 0.016 |
| T9 | 5 / 12 | **2 / 12** | 0 | 0 | 0.072 | 0.066 |
| **합계** | **20 / 48** | **12 / 48** | **4** | **1** | | |

---

## 3. 해석

4개 태스크 전부에서 성능이 떨어졌다.

들어올리기를 명시적으로 지시한 T3·T9의 하락 폭이 가장 컸다(6→2, 5→2). "lift it clear of the box"를 추가했는데 **들어올린 높이 중앙값이 오히려 줄었다**(0.062 → 0.047).

지시문이 정책에 정상 전달된 것은 실행 로그로 확인했다. 전달 실패가 아니다.

학습 지시문은 전부 한 문장이며, 정책의 언어 임베딩은 그 분포에서 나왔다. 문장이 2~3개로 늘어나면서 조건화가 흐려진 것으로 보인다. 다만 이 설명은 확인된 것이 아니다.

**본 벤치마크는 원문 지시문으로 측정했다.**

---

## 4. 한계

| # | 항목 |
|---|---|
| 1 | 4개 태스크, 태스크당 12 에피소드. 표본이 작다 |
| 2 | 변형안 전체(10개 태스크)를 측정하지 않았다 |
| 3 | 문장 길이와 내용 변경이 분리되어 있지 않다. "한 문장으로 유지하되 공간 단서만 강화" 조건을 시험하지 않았다 |

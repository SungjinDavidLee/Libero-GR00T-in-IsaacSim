# 적용 방법

기존 저장소에 그대로 올릴 수 있는 완성본이다. 지시서가 아니라 파일이다.

## 파일

```
README.md                      기존 README.md 를 이것으로 교체
docs/workspace.md              신규
docs/distractor.md             신규
docs/camera.md                 신규
data/task_summary_all.csv      신규
data/reach_sweep.csv           신규
data/camera_sweep_t5t9.csv     신규
```

기존 `data/episodes.csv`, `results/*`, `assets/*`, `media/*`, 나머지 `docs/*` 는
건드리지 않는다. FR5 내용은 들어 있지 않다.

## 명령

```bash
cd <저장소>
cp /path/to/ghadd/README.md .
cp /path/to/ghadd/docs/*.md docs/
cp /path/to/ghadd/data/*.csv data/

git add README.md docs/workspace.md docs/distractor.md docs/camera.md \
        data/task_summary_all.csv data/reach_sweep.csv data/camera_sweep_t5t9.csv
git commit -m "add: workspace distance, distractor restoration, D405 camera spec"
git push
```

## README.md 가 기존과 달라진 곳

올리기 전에 `git diff README.md` 로 확인하면 아래만 나와야 한다.

| 위치 | 변경 |
|---|---|
| 전역 | `GR00T N1.6` → `GR00T N1.7` (부제 · §2-1 표 · mermaid 2곳 · §11-1 표) |
| 문서 링크 줄 | `workspace.md` · `distractor.md` · `camera.md` 추가 |
| 목차 §6 | "태스크별 · 단계별 · 문턱별" → "… · 조건별" |
| §1 핵심 수치 표 | `목표 그릇 선택 99.8%` 행 추가 + 아래 단락 추가 |
| §1 요약 | "세 줄 요약" → "다섯 줄 요약", ④⑤ 추가 |
| §1 질문 표 | 2행 추가 |
| §6 | 6-4 조건 변형, 6-5 카메라 규격 신설 |
| §7 | 7-4 실패를 가르는 변수 — 거리 신설 |
| §9 | 측정값 표에 새 CSV 3행 추가 |
| §10 | 항목 3 해소로 교체, 11 · 12 추가 |
| §11-2 | 카메라 프로파일 전환 단락 추가 |
| §12 | 체크 3개, 항목 2개 추가 |
| 저장소 구성 | 새 파일 6개 반영 |

본문 §2 ~ §5, §6-1 ~ §6-3, §7-1 ~ §7-3, §8, §11-1 · §11-3 은 한 글자도 바꾸지
않았다. 그림 경로도 그대로다.

## 확인할 것 하나

원본 README 의 mermaid 블록이 ```` ```mermaid ```` 로 열려 있는지 확인한다.
이 파일은 그렇게 작성했다. GitHub 렌더에서 다이어그램이 그림으로 보이면 맞다.

## 영문판

`en/README.md` 는 갱신하지 않았다. 같은 구조로 옮기면 되고, 필요하면 따로 만든다.

## FR5

별개 작업이므로 이 패키지에 넣지 않았다. 별도 저장소용 자료가 따로 있다.

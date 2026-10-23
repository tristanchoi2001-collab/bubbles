# 연구 조사 진행 기록 (HANDOFF.md 작업)

중단되면 이 파일부터 읽고 이어서 한다. 브랜치는 `claude/tracker2-bubble-tracking-ffz50u`. 푸시 전에 `git pull --rebase`.

## 비용 규칙 (최우선, 사용자 지시 2026-10-23)
- 추가 비용이 생기는 외부 서비스·유료 API·유료 검색·유료 도구는 쓰지 않는다. 무료 공개 API와 공개 웹페이지만 쓴다.
- API 키를 발급하거나 쓰지 않는다(OpenAlex 키 포함). 환경변수에 키가 있어도 쓰지 않는다.
- 유료 논문은 결제·우회하지 않는다. 공개 초록, 저자 공개본, 오픈액세스만 쓴다.
- 차단되면 유료 프록시·우회 서비스를 쓰지 않는다. 무료 경로가 없으면 "확인 못 함"으로 남긴다.
- 비용이 생길 수 있는 작업은 하기 전에 멈추고 사용자 승인을 받는다.
- 확인한 사실 (공식 문서를 curl로 읽음)
  - 클라우드 세션·서브 에이전트·예약 작업은 요금제 사용량에서 차감된다. 클라우드 VM은 별도 요금이 없다.
  - 구독 계정에서 한도를 넘은 사용이 과금되는 경로는 Usage credits뿐이다. **사용자가 끔(2026-10-23 확인).** 끄면 한도에서 요청이 거부된다.
  - WebFetch: 토큰 외 추가 비용 없음. WebSearch: API 키 요금은 1,000회당 $10이지만 구독에서는 사용량 차감이다. **사용자가 사용 허가(2026-10-23).** standard 모드만 쓴다.
  - OpenAlex는 키 없이 무료 공용 예산만 쓴다(유료 크레딧 구매 금지).

## 접속 상태
- **2026-10-23 16:30 UTC (새 세션 session_01QFVWo3BPZ98Eh7jXYmYxkN, 네트워크 "모든 도메인 허용")**
  - Crossref API: 200 정상. 일부 문헌은 초록도 준다 → DOI 대조 가능.
  - OpenAlex: 접속은 되지만 429. 이 클라우드 IP가 함께 쓰는 무료 일일 예산이 바닥났다(00:00 UTC = 09:00 KST 초기화).
    무료 API 키는 이메일 등록이 필요하다. 개인 이메일을 요청에 넣지 않는 규칙 때문에 발급하지 않았다.
  - Semantic Scholar: 429(인증 없는 공용 한도). 간격을 두고 재시도한다.
  - Google Scholar: curl은 CAPTCHA("unusual traffic")로 막힌다. **WebFetch 도구로는 검색 결과(인용 수 포함)가 열린다.** 사용자 요청(2026-10-23)으로 함께 참조한다.
  - 열림: arXiv, J-STAGE, Europe PMC, Cambridge Core, NASA NTRS, OSTI 검색 페이지, HAL, CiNii, doi.org.
  - 막힘(사이트 쪽 Cloudflare 봇 차단 403): ScienceDirect, Wiley, T&F, ASME, AIP, APS, ResearchGate, CORE. KoreaScience는 시간 초과.
- 2026-10-23 16:14 UTC (이전 세션): OpenAlex, Crossref, Semantic Scholar, doi.org, arXiv, J-STAGE, ScienceDirect, Springer, OSTI 모두 프록시 403(정책 거부). WebFetch도 DNS 실패.
  - 이 세션의 환경: `env_01KeTKUxBSkb8xf3iEYPtuzC`.
- 확인 수준 표시 규칙
  - `C+F` Crossref 대조 + 전문 확인 / `C+A` Crossref 대조 + 초록 확인(수치에 "(초록 기준)") / `C` Crossref 대조만(내용은 2차 자료, 수치에 "(2차 인용)") / `U` 미대조.
  - Elsevier PII(ScienceDirect 주소의 S…)에서 만든 DOI는 Crossref로 대조하기 전까지 "PII 유도"로 표시한다.

## 작업 상태
| # | 작업 | 상태 | 결과 파일 |
|---|---|---|---|
| 1 | 크기 추정(압력 강하 항, 열전달 항, 열전대 응답) | 대기 | `docs/research/estimates_microgap.md` |
| 2 | 주제별 문헌 조사(HANDOFF 3장의 6주제) | 대기 | `docs/research/lit_*.md` |
| 3 | 보고서 `docs/research_microgap_paper.md` | 대기 | |
| 4 | `docs/refs_microgap.bib` | 대기 | |
| 5 | 발표 원고 14·15번 슬라이드 수정 | 대기 | `docs/presentation_2026-10-26/slides_ko.md` |

## 자동 재개
- 사용자 요청: 일요일 10시(주간 한도 초기화, UTC+9로 가정 = 2026-10-25 01:00 UTC)까지 스스로 계속한다. 세션 한도가 끝나면 초기화를 기다렸다가 이어서 한다.
- 이 세션(session_01QFVWo3BPZ98Eh7jXYmYxkN)의 매시간 예약 작업: **`trig_01HkakuwX8ZSm3zyqsZLz9aU`** (매시 41분). 2026-10-25 01:00 UTC가 지나면 지운다.
- 이전 세션(session_01Lo4WDHp5j9p8HWM9B3Vtdx)의 예약 작업은 지웠다.

## 기록
- 2026-10-23 16:20 UTC: 시작. 접속 확인, 브랜치 전환, 기존 자료(HANDOFF, notes_websearch, status, slides) 읽음.
- 2026-10-23 16:30 UTC: 두 "Default" 환경이 모두 "trusted network access"(기본값)로 표시됐다. 지난번 변경은 저장되지 않은 것으로 보인다.
  - 바꾸는 곳: claude.ai/code 새 세션 화면 → 입력창 위 구름 아이콘(환경 이름) → 환경 오른쪽 톱니바퀴 → Network access(None/Trusted/Full/Custom) → 저장 → 새 세션. 실행 중인 세션에서는 바꿀 수 없다.
  - 사용자가 설정을 바꾸고 새 세션에서 시작하기로 했다. 이 세션은 조사·계산을 시작하지 않았다(작업 1~5 모두 미착수).

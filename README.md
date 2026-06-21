# KATS — Korea Investment Auto Trading System

한국투자증권 OpenAPI 기반 자동매매 플랫폼입니다.

## 요구 사항

- Python **3.12**
- Windows 10 / 11

## 설치

```bash
# 가상환경 생성 (Python 3.12)
python -m venv .venv
.venv\Scripts\activate

# 런타임 + 개발 의존성 설치 (requirements.txt 포함)
pip install -r requirements-dev.txt
```

`requirements-dev.txt`는 `-r requirements.txt`로 런타임 패키지(`pydantic`, `python-dotenv`)를 함께 설치합니다.

### Optional: Desktop UI (PySide6)

UI는 **optional dependency**입니다. 기본 설치만으로는 Desktop UI를 실행할 수 없습니다.

```bash
# pyproject.toml [project.optional-dependencies] ui
pip install -e ".[ui]"
```

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `ui` | PySide6 | Desktop UI (`python main.py --ui`) |
| `dev` | pytest, ruff, black, mypy | 개발/테스트 (requirements-dev.txt와 동등) |

## 실행 순서

아래 순서대로 진행하면 v1.0을 로컬에서 기동할 수 있습니다.

```bash
# 1. 환경 변수 템플릿 복사 후 KIS OpenAPI 값 입력
copy .env.example .env

# 2. 설정·런타임 검증
python main.py --check

# 3. SQLite 마이그레이션
python main.py --migrate

# 4. 통합 런타임 기동 (Config → Logging → Database → EventBus → Services)
python main.py

# 5. (선택) Desktop UI — PySide6 설치 후
pip install -e ".[ui]"
python main.py --ui

# 6. (개발자) 전체 품질 게이트
python scripts/run_checks.py
```

## 실행 모드

| 명령 | 설명 |
|------|------|
| `python main.py --check` | 설정·런타임 검증만 수행 후 종료 |
| `python main.py --migrate` | SQLite 마이그레이션 적용 후 종료 |
| `python main.py` | `ApplicationBootstrap` wiring + HealthCheck 후 ready 상태로 종료 |
| `python main.py --ui` | Desktop UI 실행 (`UiAppContext` → `ApplicationContext`) |

## v1.0 제한사항

KATS v1.0은 **개발·통합·모의투자(VTS) 검증**을 목표로 합니다. 아래 항목은 현재 버전에서 제한됩니다.

| 항목 | v1.0 상태 |
|------|-----------|
| WebSocket production transport | **구현됨** (`ProductionWsTransport`, FINAL-02) — bootstrap 기본 wiring. **실 KIS 환경 장기 안정성·재연결 검증은 아직 필요** |
| WebSocket 자동 연결 | 없음 — `ApplicationContext.connect_websocket()` 명시 호출 필요 |
| Scheduler 백그라운드 루프 | CLI headless daemon 미구현 — `scheduler.enabled=true`여도 tick 루프는 별도 구동 필요 |
| Portfolio 런타임 store | In-Memory 기본 — 재시작 시 포트폴리오 상태 초기화 |
| Notification 외부 채널 | Telegram/Discord/Email/Slack provider 미구현 |
| UI View 테스트 | PySide6 widget 계층 pytest 미포함 |

## 안전 규칙 (실전거래)

> **실계좌 자동매매는 v1.0에서 지원 대상이 아닙니다. 반드시 모의투자(VTS) 환경에서 먼저 검증하세요.**

- 실주문 기본 **비활성화**: `order.live_trading_enabled=false` (`config/default.json`)
- `.env`의 `KIS_ACCOUNT_TYPE=mock`으로 VTS(모의) 계정 사용 권장
- production 환경은 `.env` 파일 **필수**
- real account + `live_trading_enabled=true` 조합은 RuntimeValidator 통과 후에만 허용
- API Key·Secret·Token·계좌번호를 코드·로그·Git에 포함하지 않음

모의투자(VTS) 검증 순서: `.env` 설정 → `--check` → `--migrate` → VTS REST/WebSocket 수동 확인 → 소액 mock 주문 테스트

## 통합 구조 (v1.0)

```text
ApplicationBootstrap
  ├── ConfigManager
  ├── LoggerService
  ├── DatabaseManager
  ├── EventBusService
  └── Services
        ├── Portfolio / Strategy / Risk / Backtest
        ├── Order / Notification / Scheduler / Plugins
        └── WebSocket (`ProductionWsTransport` 기본 wiring, `connect_websocket()`으로 연결)
```

## 개발 도구

```bash
# 전체 품질 게이트
python scripts/run_checks.py

# 개별 실행
python -m ruff check .
python -m black --check .
python -m mypy app main.py
python -m pytest
```

## 프로젝트 구조

```text
KATS/
├── app/
│   ├── bootstrap/     # ApplicationBootstrap, HealthCheck
│   ├── context/       # ApplicationContext
│   ├── release/       # CLI (--check, --migrate, --ui)
│   └── ...
├── config/            # 환경별 JSON 설정
├── docs/              # 설계 문서 (Document First)
├── tests/             # unit + integration 테스트
├── main.py            # 진입점
├── requirements.txt   # 런타임 의존성
├── requirements-dev.txt
└── pyproject.toml
```

## 문서 (docs/)

모든 구현은 `docs/` 설계 문서를 기준으로 합니다.

| 문서 | 내용 |
|------|------|
| [00_PROJECT.md](docs/00_PROJECT.md) | 프로젝트 개요 |
| [02_ARCHITECTURE.md](docs/02_ARCHITECTURE.md) | 아키텍처 |
| [10_CONFIGURATION.md](docs/10_CONFIGURATION.md) | 설정 관리 |
| [11_PROJECT_STRUCTURE.md](docs/11_PROJECT_STRUCTURE.md) | 디렉터리 표준 |
| [12_DEVELOPMENT_ROADMAP.md](docs/12_DEVELOPMENT_ROADMAP.md) | 개발 로드맵 |
| [22_API_INTEGRATION.md](docs/22_API_INTEGRATION.md) | KIS API 연동 |
| [23_KIS_OFFICIAL_GUIDE.md](docs/23_KIS_OFFICIAL_GUIDE.md) | **KIS 공식 저장소 정렬 (필수)** |

전체 문서 목록은 [docs/](docs/) 디렉터리를 참조하세요.

## 개발 원칙

- **Document First** — 구현 전 docs 확인, 구현 후 문서·코드 일치 검증
- **Clean Architecture** — UI → Controller → Service → Domain → Repository/Broker
- **Event-Driven** — 모듈 간 EventBus 통신
- **Test First** — Unit Test Coverage 80% 이상

## 라이선스

Proprietary

# 11_PROJECT_STRUCTURE.md

# KATS Project Directory Standard

Version: 1.0.0

---

# 목적

본 문서는 KATS 프로젝트의 표준 디렉터리 구조를 정의한다.

모든 소스코드는 본 구조를 준수하며, 기능 추가 시 기존 구조를 우선 활용한다.

---

# 최상위 구조

```text
KATS/

├── app/
├── config/
├── data/
├── docs/
├── logs/
├── plugins/
├── resources/
├── scripts/
├── tests/
├── tools/
├── .cursor/
├── .github/
├── .env.example
├── pyproject.toml
├── requirements.txt
├── README.md
└── main.py
```

---

# app

모든 애플리케이션 코드

```text
app/

├── broker/
├── config/
├── controller/
├── core/
├── database/
├── domain/
├── dto/
├── events/
├── infrastructure/
├── models/
├── repository/
├── service/
├── strategy/
├── ui/
├── utils/
└── workers/
```

---

# broker

```text
broker/

├── interfaces/
├── kis/
├── auth/
├── websocket/
├── parser/
├── mapper/
└── exceptions/
```

Broker 구현만 존재한다.

---

# config

```text
config/

├── default.json
├── development.json
├── simulation.json
├── production.json
├── logging.json
├── strategy.json
└── ui.json
```

프로그램 설정만 저장한다.

---

# controller

```text
controller/

├── account_controller.py
├── market_controller.py
├── order_controller.py
├── strategy_controller.py
├── settings_controller.py
└── system_controller.py
```

Controller는 Service만 호출한다.

---

# service

```text
service/

├── account_service.py
├── auth_service.py
├── market_service.py
├── order_service.py
├── portfolio_service.py
├── strategy_service.py
├── risk_service.py
├── logging_service.py
├── notification_service.py
├── settings_service.py
├── system_service.py
└── backtest_service.py
```

---

# repository

```text
repository/

├── interfaces/
├── sqlite/
├── cache/
└── mapper/
```

Repository는 Database 접근만 담당한다.

---

# domain

```text
domain/

├── account/
├── order/
├── portfolio/
├── market/
├── strategy/
├── indicator/
├── risk/
├── common/
├── events/
├── exceptions/
└── value_objects/
```

순수 비즈니스 로직만 포함한다.

---

# dto

```text
dto/

├── request/
├── response/
├── event/
└── common/
```

계층 간 데이터 전달 객체를 관리한다.

---

# events

```text
events/

├── base_event.py
├── event_bus.py
├── event_dispatcher.py
├── handlers/
├── subscribers/
├── publishers/
└── registry/
```

---

# infrastructure

```text
infrastructure/

├── logging/
├── cache/
├── scheduler/
├── notification/
├── security/
└── filesystem/
```

외부 기술 의존성을 구현한다.

---

# ui

```text
ui/

├── main_window.py
├── dialogs/
├── views/
├── viewmodels/
├── widgets/
├── charts/
├── themes/
└── resources/
```

MVVM 구조를 적용한다.

---

# workers

```text
workers/

├── api_worker.py
├── websocket_worker.py
├── database_worker.py
├── strategy_worker.py
├── logging_worker.py
└── scheduler_worker.py
```

모든 백그라운드 작업을 관리한다.

---

# utils

```text
utils/

├── datetime.py
├── decimal.py
├── string.py
├── retry.py
├── validator.py
└── helper.py
```

공통 유틸리티만 포함한다.

---

# plugins

```text
plugins/

├── strategies/
├── indicators/
├── brokers/
├── notifications/
└── examples/
```

런타임에 자동 탐색한다.

---

# data

```text
data/

├── database/
├── backup/
├── cache/
├── auth/
├── export/
├── import/
└── settings/
```

사용자 데이터만 저장한다.

---

# logs

```text
logs/

├── api.log
├── order.log
├── strategy.log
├── websocket.log
├── database.log
├── system.log
├── error.log
└── archive/
```

로그는 날짜별 Rotation을 적용한다.

---

# resources

```text
resources/

├── icons/
├── fonts/
├── images/
├── styles/
└── locale/
```

---

# docs

```text
docs/

├── architecture/
├── api/
├── database/
├── development/
├── deployment/
├── testing/
├── user/
└── decisions/
```

모든 설계 문서를 관리한다.

---

# tests

```text
tests/

├── unit/
├── integration/
├── performance/
├── regression/
├── fixtures/
├── mocks/
└── data/
```

운영 데이터는 포함하지 않는다.

---

# scripts

```text
scripts/

├── build.py
├── clean.py
├── migrate.py
├── backup.py
├── release.py
└── run_tests.py
```

자동화 스크립트만 저장한다.

---

# tools

```text
tools/

├── benchmark/
├── profiler/
├── database/
└── developer/
```

개발 지원 도구를 관리한다.

---

# .cursor

```text
.cursor/

├── rules/
├── prompts/
├── tasks/
├── templates/
└── memory/
```

Cursor 전용 개발 자산을 저장한다.

---

# .github

```text
.github/

├── workflows/
├── ISSUE_TEMPLATE/
├── PULL_REQUEST_TEMPLATE.md
└── CODEOWNERS
```

CI/CD 및 협업 설정을 관리한다.

---

# 파일 생성 규칙

새로운 기능은 기존 디렉터리를 우선 사용한다.

동일한 목적의 디렉터리를 중복 생성하지 않는다.

---

# Import 규칙

상위 디렉터리 참조를 최소화한다.

순환 Import를 허용하지 않는다.

---

# Module Size

권장 기준

* 파일 500줄 이하
* 디렉터리 30개 파일 이하

필요 시 하위 디렉터리로 분리한다.

---

# Naming Rules

디렉터리

* snake_case

파일

* snake_case.py

클래스

* PascalCase

함수

* snake_case

상수

* UPPER_CASE

---

# Dependency Rules

허용

```text
ui
↓

controller
↓

service
↓

domain
↓

repository
↓

database
```

금지

```text
ui

↓

database
```

```text
domain

↓

ui
```

```text
repository

↓

broker
```

---

# 확장 규칙

새로운 Broker, Strategy, Indicator는 Plugin 구조를 사용한다.

기존 Service 수정 없이 추가 가능해야 한다.

---

# Validation Checklist

* 표준 디렉터리 구조 준수
* 계층 분리 유지
* Plugin 구조 지원
* MVVM UI 구조 적용
* Worker 분리
* Infrastructure 분리
* 테스트 디렉터리 분리
* Cursor 전용 디렉터리 포함
* CI/CD 디렉터리 포함
* 순환 참조 없음
* 문서와 구현 일치

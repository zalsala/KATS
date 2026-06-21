# 18_TESTING_GUIDE.md

# KATS Testing & Quality Assurance Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS 프로젝트의 테스트 전략과 품질 관리 기준을 정의한다.

모든 기능은 구현과 동시에 테스트를 작성하며, 테스트되지 않은 기능은 완료된 것으로 간주하지 않는다.

---

# Testing Pyramid

```text id="7e0e7k"
E2E Test

↑

Integration Test

↑↑

Unit Test
```

목표 비율

* Unit Test : 70%
* Integration Test : 25%
* E2E Test : 5%

---

# Directory Structure

```text id="v7l2g4"
tests/

├── unit/
├── integration/
├── e2e/
├── performance/
├── regression/
├── fixtures/
├── mocks/
├── data/
└── conftest.py
```

---

# Test Categories

## Unit Test

검증 대상

* Domain
* Service
* Repository(Mock)
* Strategy
* Indicator
* Risk Rule
* DTO
* Utility

외부 API 호출 금지

---

## Integration Test

검증 대상

* Broker
* SQLite
* EventBus
* Repository
* Service
* WebSocket(Mock)

Mock API 또는 Simulation 환경을 사용한다.

---

## End-to-End Test

전체 흐름 검증

```text id="d4l1h8"
Application

↓

Login

↓

Market Data

↓

Strategy

↓

Risk

↓

Order

↓

Portfolio

↓

Log
```

---

# Performance Test

측정 항목

* Tick 처리 속도
* 주문 처리 시간
* EventBus 처리량
* Database 조회 속도
* 메모리 사용량

---

# Regression Test

다음 항목은 회귀 테스트를 수행한다.

* 주문
* 전략
* 백테스트
* 인증
* 실시간 데이터
* Portfolio 계산

---

# Test Naming

형식

```text id="x8b5am"
test_<module>_<behavior>_<expected>()
```

예시

```text id="b9z3ep"
test_order_submit_success()

test_token_auto_refresh()

test_strategy_generate_buy_signal()
```

---

# Fixture

공통 Fixture

```text id="n1f7cx"
MockBroker

MockRepository

MockEventBus

SamplePortfolio

SampleOrder

SampleStrategy
```

---

# Mock Policy

Mock 대상

* REST API
* WebSocket
* Database
* Notification
* Clock(Time)

실제 외부 서비스 호출 금지

---

# Coverage

최소 목표

```text id="t2r6vz"
Overall

80%

----------------

Domain

95%

----------------

Service

90%

----------------

Risk

100%
```

---

# Static Analysis

필수

* Ruff
* Black
* mypy

배포 전 반드시 통과해야 한다.

---

# Code Quality

목표

* Lint Error : 0
* Type Error : 0
* Critical Bug : 0
* Circular Dependency : 0

---

# Test Data

테스트 데이터는 운영 데이터와 분리한다.

```text id="a3w4ek"
tests/

data/

sample_prices.csv

sample_orders.json

sample_positions.json
```

---

# Continuous Integration

실행 순서

```text id="h8g6pa"
Ruff

↓

Black

↓

mypy

↓

Unit Test

↓

Integration Test

↓

Coverage

↓

Build
```

---

# Failure Policy

테스트 실패 시

* Build 중단
* Release 금지

---

# Benchmark

목표

| 항목               |     기준 |
| ---------------- | -----: |
| Unit Test        | 30초 이하 |
| Integration Test |  5분 이하 |
| 전체 테스트           | 10분 이하 |

---

# Test Report

생성

* Coverage Report
* JUnit XML
* HTML Report

---

# Acceptance Criteria

기능 완료 조건

* 요구사항 구현
* Unit Test 작성
* Integration Test 작성
* 문서 업데이트
* Code Review 완료

---

# Validation Checklist

* Testing Pyramid 준수
* Mock 기반 테스트
* Coverage 80% 이상
* 정적 분석 통과
* 회귀 테스트 작성
* 성능 테스트 포함
* CI 자동 실행
* 테스트 데이터 분리
* 배포 전 전체 테스트 수행
* 문서와 구현 일치

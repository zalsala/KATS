# 12_DEVELOPMENT_ROADMAP.md

# KATS Development Roadmap

Version: 1.0.0

---

# 목적

본 문서는 KATS 프로젝트의 전체 개발 순서를 정의한다.

모든 구현은 본 로드맵을 기준으로 진행하며, 이전 단계가 완료되기 전에는 다음 단계를 구현하지 않는다.

---

# 개발 원칙

각 Phase는 독립적으로 완료 가능해야 한다.

각 Phase 종료 시

* 코드 리뷰
* Unit Test
* Integration Test
* 문서 검토

를 완료한다.

---

# 전체 일정

```text
Phase 01
Project Foundation

↓

Phase 02
Core Framework

↓

Phase 03
Database

↓

Phase 04
Authentication

↓

Phase 05
Broker

↓

Phase 06
Market Data

↓

Phase 07
Account

↓

Phase 08
Order

↓

Phase 09
Portfolio

↓

Phase 10
Strategy Engine

↓

Phase 11
Backtest

↓

Phase 12
GUI

↓

Phase 13
Testing

↓

Phase 14
Deployment
```

---

# Phase 01

## Project Foundation

목표

프로젝트 기본 환경 구축

구현

* 프로젝트 생성
* pyproject.toml
* requirements
* Logger
* Config
* 기본 구조
* Git 설정
* Cursor Rule

완료 조건

* 프로젝트 실행
* Ruff 통과
* Black 통과

---

# Phase 02

## Core Framework

구현

* EventBus
* Base Service
* Base Repository
* Base Strategy
* Exception
* DTO
* Common Utility

완료 조건

* EventBus 테스트 완료

---

# Phase 03

## Database

구현

* SQLite
* Migration
* Repository
* Entity Mapping

테이블

* Account
* Order
* Position
* Strategy
* Settings

완료 조건

Repository Test 성공

---

# Phase 04

## Authentication

구현

* OAuth
* Token Manager
* Approval Key
* HashKey
* Header Builder

완료 조건

토큰 자동 갱신

---

# Phase 05

## Broker

구현

* Broker Interface
* REST Client
* WebSocket Client
* Parser
* Mapper

완료 조건

REST API 호출 성공

---

# Phase 06

## Market Data

구현

* 현재가
* 호가
* 차트
* 실시간 체결
* 실시간 호가
* Cache

완료 조건

실시간 시세 수신

---

# Phase 07

## Account

구현

* 계좌조회
* 잔고조회
* 체결조회
* 예수금조회

완료 조건

실계좌/모의계좌 지원

---

# Phase 08

## Order

구현

* 매수
* 매도
* 정정
* 취소
* 주문조회

추가

* Retry
* Timeout
* Validation

완료 조건

주문 성공

---

# Phase 09

## Portfolio

구현

* 보유종목
* 손익
* 평가금액
* 통계

완료 조건

자동 갱신

---

# Phase 10

## Strategy Engine

구현

* Strategy Loader
* Strategy Runner
* Plugin
* Scheduler
* Signal Engine

기본 전략

* SMA
* EMA
* RSI
* MACD
* Bollinger

완료 조건

자동매매 가능

---

# Phase 11

## Backtest

구현

* CSV Loader
* Strategy Test
* Report
* Statistics

성과지표

* CAGR
* MDD
* Sharpe Ratio
* Win Rate
* Profit Factor

완료 조건

전략 비교 가능

---

# Phase 12

## GUI

구현

메인 화면

* Dashboard
* Watchlist
* Chart
* Order
* Account
* Portfolio
* Strategy
* Log
* Settings

완료 조건

모든 기능 GUI 제공

---

# Phase 13

## Testing

구현

* Unit Test
* Integration Test
* Performance Test
* Regression Test

목표

Coverage

80% 이상

---

# Phase 14

## Deployment

구현

* Build
* Installer
* Update
* Backup
* Recovery

배포

* Windows Installer

---

# 개발 순서

```text
Foundation

↓

Framework

↓

Database

↓

Authentication

↓

Broker

↓

Market

↓

Account

↓

Order

↓

Portfolio

↓

Strategy

↓

Backtest

↓

GUI

↓

Test

↓

Release
```

---

# Task 관리

모든 작업은 Task 단위로 관리한다.

규칙

* 하나의 Task는 하나의 기능만 구현한다.
* 하나의 Task는 하나의 PR로 완료한다.
* 하나의 Task는 하루 이내 완료 가능한 크기로 작성한다.

---

# Task 규모

| 구분             | 개수 |
| -------------- | -: |
| Foundation     | 10 |
| Core           | 12 |
| Database       | 10 |
| Authentication |  8 |
| Broker         | 15 |
| Market         | 15 |
| Account        |  8 |
| Order          | 15 |
| Portfolio      |  8 |
| Strategy       | 18 |
| Backtest       | 10 |
| GUI            | 20 |
| Testing        | 15 |
| Deployment     |  6 |

총 예상 Task

**약 155개**

---

# 개발 완료 기준

각 Phase는 다음 조건을 만족해야 완료된다.

* 기능 구현 완료
* Unit Test 통과
* Integration Test 통과
* 문서 업데이트
* Ruff 통과
* Black 통과
* mypy 통과
* 코드 리뷰 완료

---

# 위험 관리

주요 위험 요소

* API 변경
* 네트워크 장애
* 토큰 만료
* 실시간 연결 종료
* 주문 실패
* 데이터 손상

대응 전략

* Retry
* Circuit Breaker
* Auto Reconnect
* Backup
* Fail Safe
* Recovery Manager

---

# 품질 목표

* Unit Test Coverage 80% 이상
* Public API Type Hint 100%
* Docstring 100%
* Lint Error 0
* Critical Bug 0
* Memory Leak 0
* 순환 참조 0

---

# 마일스톤

| Milestone | 완료 기준                 |
| --------- | --------------------- |
| M1        | 프로젝트 실행               |
| M2        | REST API 연동           |
| M3        | WebSocket 연동          |
| M4        | 주문 기능 구현              |
| M5        | 자동매매 구현               |
| M6        | 백테스트 구현               |
| M7        | GUI 완성                |
| M8        | 베타 테스트                |
| M9        | Release Candidate     |
| M10       | Version 1.0.0 Release |

---

# Validation Checklist

* Phase 순서 준수
* Task 기반 개발
* 문서 우선 개발
* 테스트 우선 검증
* 품질 기준 충족
* 마일스톤 관리
* 위험 관리 계획 포함
* 배포 계획 포함
* 구현과 문서 일치

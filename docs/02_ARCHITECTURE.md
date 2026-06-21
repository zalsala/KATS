# 02_ARCHITECTURE.md

# KATS Architecture Specification

Version: 1.0.0

---

# Architecture Overview

KATS는 **Clean Architecture**, **DDD Lite**, **Event-Driven Architecture**를 기반으로 설계한다.

각 계층은 자신의 책임만 수행하며 상위 계층은 하위 계층의 구현을 알지 못한다.

```
Presentation

↓

Application

↓

Domain

↓

Infrastructure

↓

External Systems
```

---

# Layer Structure

```
GUI

↓

Controller

↓

Application Service

↓

Domain

↓

Repository

↓

Broker

↓

KIS OpenAPI
```

---

# Dependency Rule

의존성은 항상 안쪽으로만 향한다.

```
GUI
    ↓

Controller
    ↓

Service
    ↓

Domain
    ↓

Repository Interface
    ↓

Infrastructure
```

반대 방향 참조는 금지한다.

---

# Directory Structure

```
KATS/

app/

    controller/

    service/

    domain/

    repository/

    broker/

    strategy/

    events/

    database/

    infrastructure/

    config/

    core/

    dto/

    models/

    utils/

ui/

resources/

tests/

docs/

logs/

scripts/
```

---

# Layer Responsibilities

## Presentation

책임

* UI 표시
* 사용자 입력
* 이벤트 전달

금지

* API 호출
* SQL 실행
* 비즈니스 로직

---

## Controller

책임

* UI 요청 처리
* DTO 변환
* Service 호출

금지

* API 호출
* Database 접근

---

## Application Service

책임

* Use Case 실행
* Transaction 관리
* Domain 호출
* Event 발행

금지

* UI 접근
* SQL 작성

---

## Domain

책임

* 비즈니스 규칙
* Entity
* Value Object
* Domain Service

금지

* GUI
* Database
* REST API

---

## Repository

책임

* Database 저장
* Database 조회

금지

* API 호출
* UI 접근

---

## Broker

책임

* KIS REST API
* KIS WebSocket

금지

* UI 접근
* DB 접근

---

# Event Architecture

모든 모듈은 EventBus를 이용하여 통신한다.

```
Market Tick

↓

MarketDataEvent

↓

Strategy

↓

SignalEvent

↓

RiskManager

↓

OrderRequestEvent

↓

OrderService

↓

Broker

↓

OrderExecutedEvent

↓

Portfolio

↓

UI
```

---

# Broker Architecture

```
IBroker

↓

KISBroker

↓

REST Client

↓

WebSocket Client

↓

KIS OpenAPI
```

Broker는 Interface를 통해 접근한다.

---

# Service Architecture

```
AccountService

MarketService

OrderService

StrategyService

PortfolioService

SettingsService

LoggingService

BacktestService

RiskService
```

Service끼리는 직접 호출하지 않는다.

공통 Event 또는 Facade를 사용한다.

---

# Repository Architecture

```
AccountRepository

OrderRepository

PositionRepository

WatchlistRepository

StrategyRepository

SettingsRepository

MarketRepository
```

모든 Repository는 Interface를 구현한다.

---

# Domain Model

```
Account

Position

Order

Trade

Portfolio

WatchItem

Strategy

Signal

RiskRule

MarketData
```

Entity는 자신의 상태를 관리한다.

---

# DTO

DTO는 계층 간 데이터 전달만 담당한다.

```
LoginDTO

OrderDTO

PositionDTO

MarketDTO

AccountDTO

StrategyDTO
```

DTO에는 비즈니스 로직을 작성하지 않는다.

---

# Configuration

```
Config

↓

Environment

↓

Settings

↓

Runtime Configuration
```

Config는 Singleton으로 관리한다.

---

# Authentication

```
AuthService

↓

TokenManager

↓

HashKeyManager

↓

ApprovalKeyManager

↓

KIS OAuth
```

토큰은 메모리와 로컬 저장소에서 함께 관리한다.

---

# Order Flow

```
UI

↓

Controller

↓

OrderService

↓

RiskManager

↓

OrderValidator

↓

Broker

↓

KIS API

↓

Execution Event

↓

Portfolio Update

↓

UI Refresh
```

---

# Market Data Flow

```
REST

↓

Snapshot

↓

Market Cache

↓

Indicator Engine

↓

Strategy
```

```
WebSocket

↓

Tick

↓

Market Cache

↓

EventBus

↓

Strategy

↓

Chart

↓

UI
```

---

# Strategy Engine

```
StrategyManager

↓

BaseStrategy

↓

Indicator

↓

Signal

↓

Order Request
```

전략은 Broker를 직접 호출하지 않는다.

---

# Risk Engine

```
Signal

↓

Risk Rules

↓

Position Size

↓

Validation

↓

Approved Order
```

---

# Portfolio Engine

```
Execution

↓

Position Update

↓

PnL Update

↓

Account Update

↓

Dashboard
```

---

# Logging Architecture

```
Application

↓

LoggerService

↓

Logging Adapter

↓

File

↓

Console

↓

Future Extension
```

모든 로그는 LoggerService를 통해 기록한다.

---

# Exception Flow

```
Exception

↓

Exception Handler

↓

Logger

↓

Recovery

↓

Event

↓

UI Notification
```

예외는 사용자에게 직접 노출하지 않는다.

---

# Thread Model

```
Main Thread

GUI

-------------------

Worker Thread

REST API

-------------------

Worker Thread

Database

-------------------

Worker Thread

Strategy

-------------------

Worker Thread

Logging

-------------------

Async Loop

WebSocket
```

GUI Thread는 블로킹 작업을 수행하지 않는다.

---

# Cache Layer

```
Token Cache

Market Cache

Settings Cache

Account Cache
```

캐시는 TTL 정책을 적용한다.

---

# Plugin Architecture

```
plugins/

strategy/

indicator/

broker/

notification/
```

플러그인은 런타임에 자동 탐색한다.

---

# Notification Layer

지원 예정

```
Telegram

Discord

Slack

Email
```

NotificationService를 통해 통합 관리한다.

---

# Extension Points

다음 모듈은 교체 가능하도록 설계한다.

* Broker
* Strategy
* Indicator
* Database
* Notification
* Logger
* Cache

---

# Architecture Principles

* Presentation은 Domain을 직접 참조하지 않는다.
* UI는 EventBus를 통해 갱신한다.
* Service는 Broker Interface만 사용한다.
* Repository는 Database만 담당한다.
* Domain은 외부 시스템을 알지 못한다.
* Strategy는 Signal만 생성한다.
* RiskManager를 우회한 주문은 허용하지 않는다.
* 모든 외부 의존성은 Infrastructure 계층에서 구현한다.

---

# Architecture Validation Checklist

모든 구현은 아래 항목을 만족해야 한다.

* Layer 의존성 준수
* 순환 참조 없음
* Interface 기반 설계
* SOLID 준수
* Event 기반 통신
* 테스트 가능 구조
* 모듈 독립성 유지
* 교체 가능한 Broker 구조
* 교체 가능한 Strategy 구조
* UI와 비즈니스 로직 분리
* Repository를 통한 데이터 접근
* 문서와 구현 일치

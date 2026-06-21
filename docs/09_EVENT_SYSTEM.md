# 09_EVENT_SYSTEM.md

# KATS Event System Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 Event-Driven Architecture를 정의한다.

모든 모듈은 직접 참조 대신 EventBus를 통해 통신한다.

Event는 시스템의 결합도를 낮추고 확장성을 높이는 핵심 구성 요소이다.

---

# Architecture

```text
Presentation

↓

Controller

↓

Service

↓

EventBus

↓

Subscribers

↓

Infrastructure
```

---

# 설계 원칙

모든 모듈은 Event를 발행(Publish)하거나 구독(Subscribe)할 수 있다.

Publisher는 Subscriber를 알지 못한다.

Subscriber는 Publisher를 알지 못한다.

---

# Directory Structure

```text
app/

    events/

        event_bus.py

        event_dispatcher.py

        event_handler.py

        event_publisher.py

        event_subscriber.py

        event_registry.py

        event_types.py

        base_event.py

        event_context.py
```

---

# Event Flow

```text
Market Tick

↓

PriceUpdatedEvent

↓

EventBus

↓

Strategy Engine

↓

SignalGeneratedEvent

↓

Risk Engine

↓

OrderRequestedEvent

↓

Order Service

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

# Event Lifecycle

```text
Create

↓

Publish

↓

Queue

↓

Dispatch

↓

Handler

↓

Complete
```

---

# Base Event

모든 Event는 BaseEvent를 상속한다.

공통 속성

```text
event_id

event_name

occurred_at

source

correlation_id

payload
```

---

# Event Categories

## Market Events

```text
MarketOpenedEvent

MarketClosedEvent

PriceUpdatedEvent

OrderBookUpdatedEvent

TradeTickEvent

MinuteCandleEvent

DailyCandleEvent
```

---

## Order Events

```text
OrderRequestedEvent

OrderSubmittedEvent

OrderAcceptedEvent

OrderRejectedEvent

OrderCancelledEvent

OrderModifiedEvent

OrderExecutedEvent
```

---

## Portfolio Events

```text
PositionOpenedEvent

PositionClosedEvent

PositionUpdatedEvent

PortfolioUpdatedEvent

BalanceChangedEvent
```

---

## Strategy Events

```text
StrategyLoadedEvent

StrategyStartedEvent

StrategyPausedEvent

StrategyStoppedEvent

StrategyRemovedEvent

SignalGeneratedEvent
```

---

## Account Events

```text
AccountConnectedEvent

AccountDisconnectedEvent

AccountUpdatedEvent

TokenExpiredEvent

AuthenticationSucceededEvent

AuthenticationFailedEvent
```

---

## System Events

```text
ApplicationStartedEvent

ApplicationStoppedEvent

ConfigurationChangedEvent

ErrorOccurredEvent

HealthCheckEvent

ShutdownRequestedEvent
```

---

# EventBus

EventBus는 Singleton으로 생성한다.

책임

* Publish
* Subscribe
* Unsubscribe
* Dispatch
* Error Handling

---

# Publish

```text
Publisher

↓

EventBus.publish()

↓

Queue
```

Publisher는 EventBus만 호출한다.

---

# Subscribe

```text
Subscriber

↓

EventBus.subscribe()

↓

Event Registry
```

Subscriber는 Event Type만 등록한다.

---

# Event Registry

Registry는

```text
Event Type

↓

Handler List
```

를 관리한다.

---

# Dispatch

```text
Queue

↓

Dispatcher

↓

Handler

↓

Complete
```

Dispatcher는 Handler를 순차 실행한다.

---

# Async Event

다음 이벤트는 비동기 처리한다.

```text
Logging

Notification

Statistics

Cache Update
```

---

# Sync Event

다음 이벤트는 동기 처리한다.

```text
OrderRequestedEvent

RiskCheckEvent

OrderExecutedEvent

AuthenticationFailedEvent
```

---

# Event Queue

기본 Queue는 FIFO를 사용한다.

```text
Publish

↓

Queue

↓

Dispatch

↓

Handler
```

향후 Priority Queue를 지원한다.

---

# Priority

우선순위

```text
Critical

High

Normal

Low
```

Critical Event는 즉시 처리한다.

---

# Event Context

모든 Event는 Context를 가진다.

```text
User

Session

Broker

Account

Strategy

Timestamp
```

---

# Correlation ID

동일한 작업 흐름은 Correlation ID를 공유한다.

예시

```text
Order Request

↓

Risk

↓

Broker

↓

Execution

↓

Portfolio Update
```

모든 로그에서 추적 가능해야 한다.

---

# Event Handler

Handler는 하나의 Event만 처리한다.

예시

```text
PriceUpdatedHandler

OrderExecutedHandler

PortfolioUpdatedHandler
```

---

# Handler Rules

Handler는

* 짧아야 한다.
* 하나의 책임만 가진다.
* 예외를 처리한다.
* Event를 수정하지 않는다.

---

# Error Handling

Handler 예외

```text
Exception

↓

Logger

↓

ErrorOccurredEvent

↓

Continue Dispatch
```

하나의 Handler 실패가 전체 Dispatch를 중단하지 않는다.

---

# Retry Policy

재시도 대상

* Notification
* Logging
* External Service

재시도 제외

* Validation
* Risk
* Domain Exception

---

# Dead Letter Queue

처리 실패한 Event는

```text
Dead Letter Queue
```

에 저장한다.

재처리 가능해야 한다.

---

# Event Logging

모든 Event는 선택적으로 기록한다.

기록 항목

* Event Name
* Time
* Source
* Duration
* Result

Payload는 Debug 모드에서만 저장한다.

---

# Event Ordering

동일 Correlation ID에서는

Event 순서를 보장한다.

---

# Thread Safety

EventBus는 Thread Safe 해야 한다.

다중 Thread Publish를 지원한다.

---

# Performance Goals

Publish

1ms 이하

Dispatch

5ms 이하

Event Queue

100,000건 이상 처리 가능

---

# Extension

새로운 Event 추가 시

수정 대상

```text
Event Class

↓

Handler

↓

Registry
```

기존 코드 수정은 최소화한다.

---

# Testing

Unit Test

* Publish
* Subscribe
* Unsubscribe
* Dispatch
* Exception
* Queue
* Priority
* Correlation ID

Integration Test

* Strategy → Order
* Order → Portfolio
* Portfolio → UI
* WebSocket → Strategy

---

# Validation Checklist

* Singleton EventBus
* Thread Safe
* FIFO Queue
* Handler 분리
* Correlation ID 지원
* Dead Letter Queue 지원
* Event Logging 지원
* Async/Sync 분리
* Publisher와 Subscriber 분리
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

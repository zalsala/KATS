# 14_STRATEGY_ENGINE.md

# KATS Strategy Engine Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 자동매매 전략 엔진(Strategy Engine)을 정의한다.

전략 엔진은 실시간 시세를 수신하여 매수·매도 신호를 생성하고, Risk Engine을 거쳐 주문을 실행한다.

전략은 Plugin 구조로 설계하여 새로운 전략을 코드 수정 없이 추가할 수 있어야 한다.

---

# Architecture

```text
Market Data

↓

EventBus

↓

Strategy Manager

↓

Strategy Runner

↓

Strategy Plugin

↓

Signal

↓

Risk Engine

↓

Order Service

↓

Broker
```

---

# Directory Structure

```text
app/

    strategy/

        base/

        manager/

        runner/

        loader/

        scheduler/

        signals/

        indicators/

        plugins/

        context/

        exceptions/
```

---

# Strategy Components

```text
StrategyManager

├── StrategyLoader

├── StrategyRunner

├── StrategyScheduler

├── SignalEngine

├── IndicatorEngine

└── StrategyRegistry
```

---

# Base Strategy

모든 전략은 BaseStrategy를 상속한다.

필수 메서드

```python
initialize()

on_start()

on_tick()

on_candle()

on_order()

on_position()

on_stop()
```

---

# Strategy Lifecycle

```text
Load

↓

Initialize

↓

Ready

↓

Running

↓

Paused

↓

Stopped

↓

Disposed
```

---

# Strategy Context

모든 전략은 StrategyContext를 전달받는다.

포함 항목

* Broker
* EventBus
* Config
* Logger
* Symbol
* Account
* Position
* Portfolio
* Cache

---

# Strategy Manager

책임

* 전략 등록
* 전략 제거
* 전략 시작
* 전략 종료
* 상태 관리

---

# Strategy Loader

Plugin 디렉터리를 자동 탐색한다.

```text
plugins/

    strategies/

        rsi_strategy.py

        macd_strategy.py

        breakout_strategy.py
```

---

# Strategy Runner

Runner는 전략 실행을 담당한다.

```text
Tick

↓

Strategy

↓

Signal

↓

Risk

↓

Order
```

---

# Scheduler

지원

* 장 시작
* 장 종료
* 시간 기반 실행
* Interval 실행
* Cron 실행(향후)

---

# Indicator Engine

지원 Indicator

```text
SMA

EMA

RSI

MACD

ATR

ADX

CCI

OBV

VWAP

Bollinger Bands

Stochastic
```

Indicator는 재사용 가능해야 한다.

---

# Signal Engine

Signal 종류

```text
BUY

SELL

HOLD

EXIT

CANCEL
```

Signal은 Order를 직접 생성하지 않는다.

---

# Signal Object

속성

```text
Signal ID

Strategy Name

Symbol

Direction

Price

Quantity

Confidence

Timestamp
```

---

# Signal Flow

```text
Price Tick

↓

Indicator Update

↓

Strategy

↓

Signal

↓

Risk

↓

Order
```

---

# Multi Strategy

동시에 여러 전략을 실행할 수 있어야 한다.

```text
Strategy A

Strategy B

Strategy C

↓

Portfolio
```

---

# Symbol Subscription

전략은 필요한 종목만 구독한다.

예시

```text
RSI

↓

005930

000660

035420
```

---

# Position Access

전략은 Position을 읽을 수 있다.

직접 수정은 금지한다.

---

# Order Request

전략은 OrderService를 직접 호출하지 않는다.

```text
Strategy

↓

Signal Event

↓

Order Service
```

---

# Strategy Parameters

예시

```text
RSI

period = 14

buy = 30

sell = 70
```

JSON으로 저장한다.

---

# Strategy Persistence

저장 항목

* Enabled
* Parameters
* Symbols
* State

Repository를 통해 저장한다.

---

# Event Subscription

전략은 다음 Event를 구독할 수 있다.

```text
PriceUpdatedEvent

OrderExecutedEvent

PositionUpdatedEvent

MarketOpenedEvent

MarketClosedEvent
```

---

# Event Publish

전략은 다음 Event를 발행한다.

```text
SignalGeneratedEvent

StrategyStartedEvent

StrategyStoppedEvent

StrategyErrorEvent
```

---

# Error Handling

전략 예외는 다른 전략에 영향을 주지 않는다.

```text
Strategy Error

↓

Logger

↓

StrategyErrorEvent

↓

Continue
```

---

# Isolation

전략은 서로의 내부 상태를 참조하지 않는다.

공유 데이터는 Portfolio만 사용한다.

---

# Thread Model

전략은 Worker Thread에서 실행한다.

GUI Thread 사용 금지.

---

# Strategy State

```text
CREATED

↓

INITIALIZED

↓

RUNNING

↓

PAUSED

↓

STOPPED

↓

DISPOSED
```

---

# Performance

목표

* Tick 처리 5ms 이하
* Signal 생성 2ms 이하
* Strategy 실행 10ms 이하

---

# Testing

Unit Test

* Strategy 실행
* Indicator 계산
* Signal 생성
* Parameter 검증

Integration Test

* Tick → Signal
* Signal → Order
* Order → Portfolio

---

# Validation Checklist

* Plugin 구조 지원
* BaseStrategy 상속
* Signal 기반 주문
* Multi Strategy 지원
* EventBus 사용
* Thread 분리
* Strategy 격리
* Parameter 저장 지원
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

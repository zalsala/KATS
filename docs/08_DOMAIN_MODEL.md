# 08_DOMAIN_MODEL.md

# KATS Domain Model Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 Domain 계층을 정의한다.

Domain은 시스템의 핵심 비즈니스 규칙을 담당하며, 외부 기술(REST API, Database, GUI, Framework)에 의존하지 않는다.

모든 비즈니스 로직은 Domain 계층에서 구현한다.

---

# Domain Architecture

```text
Presentation

↓

Application

↓

Domain

↓

Infrastructure
```

Domain은 Infrastructure를 알지 못한다.

---

# Domain Directory

```text
app/

    domain/

        account/

        order/

        portfolio/

        market/

        strategy/

        risk/

        indicator/

        common/

        events/

        value_objects/

        exceptions/
```

---

# Domain 구성 요소

```text
Entity

↓

Value Object

↓

Aggregate

↓

Domain Service

↓

Domain Event

↓

Specification
```

---

# Entity

Entity는 고유한 식별자(ID)를 가지며 생명주기 동안 상태가 변경될 수 있다.

Entity 목록

```text
Account

Position

Order

Trade

Portfolio

Strategy

WatchItem
```

---

# Value Object

Value Object는 불변(Immutable) 객체로 설계한다.

```text
Money

Quantity

Price

Profit

Percentage

Symbol

AccountNumber

OrderNumber

MarketCode

OrderType

OrderSide

OrderStatus
```

모든 Value Object는 Equality를 지원한다.

---

# Aggregate

Aggregate Root

```text
Account

├── Position

├── Portfolio

└── Order
```

```text
Strategy

└── Indicator
```

Aggregate 외부에서는 Root만 접근한다.

---

# Domain Service

Domain Service 목록

```text
RiskCalculator

PositionCalculator

ProfitCalculator

OrderValidator

IndicatorCalculator

PortfolioCalculator

CommissionCalculator

TaxCalculator
```

Entity에 포함하기 어려운 비즈니스 로직을 담당한다.

---

# Domain Event

```text
OrderCreated

OrderSubmitted

OrderExecuted

OrderCancelled

PositionOpened

PositionClosed

PositionUpdated

SignalGenerated

StrategyStarted

StrategyStopped

PortfolioUpdated
```

Domain Event는 EventBus를 통해 전달된다.

---

# Entity Design Rules

모든 Entity는

* ID 보유
* 상태 변경 메서드 제공
* Validation 수행
* 직접 Repository 접근 금지
* 직접 Broker 접근 금지

---

# Account Entity

속성

```text
account_id

account_number

broker

account_type

cash_balance

withdrawable_amount

updated_at
```

행위

```text
deposit()

withdraw()

update_balance()

can_order()
```

---

# Position Entity

속성

```text
position_id

symbol

quantity

available_quantity

average_price

current_price

profit

profit_rate
```

행위

```text
buy()

sell()

update_price()

calculate_profit()
```

---

# Order Entity

속성

```text
order_id

order_number

symbol

price

quantity

filled_quantity

status

side

created_at
```

행위

```text
submit()

cancel()

modify()

fill()

reject()

complete()
```

Order는 자신의 상태를 직접 변경한다.

---

# Portfolio Entity

속성

```text
positions

total_asset

cash

evaluation

profit

profit_rate
```

행위

```text
add_position()

remove_position()

update()

calculate_total_asset()
```

---

# Strategy Entity

속성

```text
strategy_id

name

enabled

parameters

symbols
```

행위

```text
start()

stop()

pause()

resume()

update_parameter()
```

---

# Indicator

모든 Indicator는 BaseIndicator를 상속한다.

지원 예정

```text
SMA

EMA

RSI

MACD

Bollinger Bands

ATR

CCI

Stochastic

ADX

OBV

VWAP
```

---

# Risk Rules

Risk Domain은 다음 규칙을 관리한다.

* 최대 손실
* 최대 보유 종목
* 최대 주문 수량
* 종목별 투자 비율
* 일일 손실 한도
* 연속 손실 제한
* 중복 주문 제한

---

# Specification Pattern

복잡한 조건은 Specification으로 분리한다.

예시

```text
CanBuySpecification

CanSellSpecification

MarketOpenSpecification

EnoughCashSpecification

RiskSpecification
```

---

# Factory Pattern

Entity 생성은 Factory를 사용한다.

```text
OrderFactory

StrategyFactory

PortfolioFactory
```

생성 로직은 Constructor에 작성하지 않는다.

---

# Builder Pattern

복잡한 DTO는 Builder를 사용한다.

```text
OrderBuilder

StrategyBuilder
```

---

# Immutable Rules

다음 객체는 Immutable이다.

```text
Money

Price

Quantity

Symbol

OrderNumber

AccountNumber
```

값 변경 시 새 객체를 생성한다.

---

# Money Object

Money는 float를 직접 사용하지 않는다.

내부적으로 Decimal을 사용한다.

지원 연산

```text
+

-

*

/

compare

round
```

---

# State Pattern

Order State

```text
Pending

↓

Submitted

↓

Accepted

↓

Partially Filled

↓

Filled
```

또는

```text
Rejected
```

또는

```text
Cancelled
```

---

# Strategy State

```text
Created

↓

Initialized

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

# Validation

모든 Entity는 자신의 상태를 검증한다.

예시

```text
수량 > 0

가격 > 0

종목코드 형식

주문 가능 상태
```

---

# Equality Rules

Entity

ID 기준 비교

Value Object

값 기준 비교

---

# Exception

Domain 전용 예외

```text
DomainException

├── InvalidOrderException

├── InvalidPriceException

├── InvalidQuantityException

├── RiskViolationException

├── StrategyException

└── PortfolioException
```

---

# Dependency Rules

Domain은 다음을 참조하지 않는다.

* GUI
* Database
* REST API
* HTTP Client
* SQLite
* WebSocket
* Config 파일
* Framework

---

# Serialization

Domain Entity는 직접 JSON 직렬화를 수행하지 않는다.

Mapper를 사용한다.

---

# Testing

모든 Entity

100% Unit Test 작성

테스트 항목

* 생성
* Validation
* 상태 변경
* Exception
* Equality
* 계산 결과

---

# Performance

Domain은 Pure Python으로 구현한다.

외부 입출력(IO)을 수행하지 않는다.

---

# Validation Checklist

* Domain은 Infrastructure를 참조하지 않는다.
* Entity는 자신의 상태를 관리한다.
* Value Object는 Immutable이다.
* Domain Event를 사용한다.
* Specification Pattern을 적용한다.
* Factory Pattern을 적용한다.
* Builder Pattern을 필요한 곳에 적용한다.
* Decimal 기반 금액 계산을 사용한다.
* Domain Exception을 사용한다.
* 모든 Domain 객체에 Unit Test를 작성한다.
* Domain은 순수 비즈니스 로직만 포함한다.

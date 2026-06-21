# 07_SERVICE_LAYER.md

# KATS Service Layer Specification

Version: 1.0.0

---

# 목적

Service Layer는 Application의 모든 비즈니스 유스케이스를 담당한다.

Controller는 Service만 호출하며, Service는 Domain과 Repository, Broker를 조합하여 하나의 업무를 수행한다.

---

# Architecture

```text
Presentation

↓

Controller

↓

Application Service

↓

Repository
Broker
EventBus

↓

Infrastructure
```

Service는 GUI와 Database 사이의 유일한 비즈니스 계층이다.

---

# Service 목록

```text
AccountService

AuthService

MarketService

OrderService

PortfolioService

StrategyService

RiskService

SettingsService

LoggingService

NotificationService

BacktestService

SystemService
```

---

# 공통 책임

모든 Service는 다음 책임을 가진다.

* Use Case 실행
* Transaction 관리
* Event 발행
* Repository 호출
* Broker 호출
* Domain 객체 생성
* Validation 수행

---

# 금지 사항

Service는 다음을 수행하지 않는다.

* SQL 작성
* HTTP 요청 생성
* GUI 접근
* Widget 접근
* JSON Parsing
* Thread 생성
* Config 직접 수정

---

# Dependency Rule

```text
Controller

↓

Service

↓

Repository Interface

↓

Broker Interface

↓

EventBus
```

Service끼리 직접 의존하지 않는다.

---

# Service Base Class

모든 Service는 BaseService를 상속한다.

공통 기능

* Logger
* Config
* EventBus
* Exception Handler

---

# AccountService

책임

* 계좌 조회
* 예수금 조회
* 주문 가능 금액 조회
* 계좌 갱신

Repository

* AccountRepository

Broker

* AccountBroker

발행 이벤트

```text
AccountUpdatedEvent

BalanceChangedEvent
```

---

# MarketService

책임

* 현재가 조회
* 호가 조회
* 차트 조회
* 시세 캐시

Repository

* MarketRepository

Broker

* MarketBroker

발행 이벤트

```text
PriceUpdatedEvent

MarketOpenedEvent

MarketClosedEvent
```

---

# OrderService

책임

* 주문 요청
* 주문 취소
* 주문 정정
* 주문 조회

주문 처리 순서

```text
Validate

↓

Risk Check

↓

Broker

↓

Repository

↓

Event Publish
```

---

# OrderService Workflow

```text
Controller

↓

OrderRequestDTO

↓

Validation

↓

RiskService

↓

Broker

↓

OrderRepository

↓

OrderExecutedEvent
```

---

# PortfolioService

책임

* 보유 종목 계산
* 손익 계산
* 평가금액 계산
* 계좌 요약

Repository

* PositionRepository

---

# StrategyService

책임

* 전략 실행
* 전략 중지
* 전략 등록
* 전략 제거
* 전략 스케줄링

전략은 Plugin Loader를 통해 로드한다.

---

# Strategy Lifecycle

```text
Load

↓

Initialize

↓

Start

↓

Running

↓

Stop

↓

Unload
```

---

# RiskService

책임

* 주문 검증
* 최대 손실 확인
* 종목 비중 확인
* 중복 주문 확인
* 투자 가능 여부 판단

모든 주문은 반드시 RiskService를 통과한다.

---

# BacktestService

책임

* 데이터 로딩
* 전략 실행
* 성과 계산
* 결과 저장

실시간 Broker를 사용하지 않는다.

---

# NotificationService

책임

* Telegram
* Discord
* Slack
* Email

Notification Provider를 통해 확장한다.

---

# LoggingService

책임

* 로그 기록
* 로그 검색
* 로그 보관
* 로그 삭제

Application은 logging 모듈을 직접 호출하지 않는다.

---

# SettingsService

책임

* 설정 조회
* 설정 저장
* 설정 검증

Repository를 통해 저장한다.

---

# SystemService

책임

* 프로그램 종료
* 프로그램 시작
* 상태 확인
* Health Check

---

# Service Communication

직접 호출 금지

```text
OrderService

↓

MarketService
```

허용

```text
OrderService

↓

EventBus

↓

MarketService
```

또는

```text
Facade

↓

Service
```

---

# Transaction Policy

Transaction은 Service에서 시작한다.

```text
Service

↓

Repository A

↓

Repository B

↓

Commit
```

Repository는 Commit하지 않는다.

---

# Validation

Service는 DTO Validation 이후 실행된다.

Validation 실패 시

Repository 호출 금지

---

# Event Publishing

Service는 작업 완료 후 Event를 발행한다.

예시

```text
OrderPlacedEvent

OrderExecutedEvent

PositionChangedEvent

StrategyStartedEvent

StrategyStoppedEvent
```

---

# Error Handling

Service는 Infrastructure 예외를

Application 예외로 변환한다.

예시

```text
HTTPError

↓

BrokerException

↓

OrderException
```

---

# Cache Policy

조회성 Service는 Cache를 사용할 수 있다.

예시

```text
Market

1초

Account

3초

Settings

60초
```

---

# Async Policy

허용

* MarketService
* NotificationService
* LoggingService

동기 처리

* OrderService
* RiskService

---

# State Management

Service는 가능한 Stateless를 유지한다.

상태가 필요한 경우

Manager 객체를 사용한다.

---

# Dependency Injection

모든 Service는

Constructor Injection을 사용한다.

```text
Repository

Broker

EventBus

Logger

Config
```

---

# Unit Test

모든 Service는

Mock Repository

Mock Broker

Mock EventBus

를 사용하여 테스트한다.

---

# Integration Test

다음 항목을 검증한다.

* Repository 연동
* Broker 연동
* Event 발행
* Transaction
* Exception

---

# Performance Goals

OrderService

평균 처리시간

100ms 이하

MarketService Cache Hit

95% 이상

Account 조회

500ms 이하

---

# Validation Checklist

* Service는 하나의 Use Case 담당
* SQL 없음
* REST 호출 없음
* GUI 접근 없음
* Repository Pattern 준수
* Broker Interface 사용
* Event 발행
* Transaction 관리
* Exception 변환
* Constructor Injection
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

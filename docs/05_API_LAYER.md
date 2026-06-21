# 05_API_LAYER.md

# KATS API Layer Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 API Layer 설계를 정의한다.

API Layer는 한국투자 OpenAPI와 프로그램 사이의 유일한 통신 계층이다.

Application은 REST API 및 WebSocket을 직접 호출하지 않는다.

모든 외부 통신은 Broker Interface를 통해 수행한다.

---

# Architecture

```text
Application

↓

Application Service

↓

Broker Interface

↓

KISBroker

↓

REST Client / WebSocket Client

↓

KIS OpenAPI
```

---

# 설계 원칙

Broker는 외부 API Adapter이다.

Broker는 다음 책임만 가진다.

* API 요청 생성
* API 응답 변환
* 인증 헤더 생성
* 오류 변환
* Rate Limit 대응

비즈니스 로직은 포함하지 않는다.

---

# Directory Structure

```text
app/

broker/

    interfaces/

        broker.py

    kis/

        kis_broker.py

        auth_client.py

        market_client.py

        account_client.py

        order_client.py

        websocket_client.py

        parser.py

        mapper.py

        exceptions.py
```

---

# Broker Interface

```python
class IBroker(Protocol):

    def get_current_price(...):

    def get_orderbook(...):

    def get_balance(...):

    def place_order(...):

    def cancel_order(...):

    def modify_order(...):
```

Broker 교체 시 Interface는 변경하지 않는다.

---

# API Client 구성

Broker 내부는 기능별 Client로 분리한다.

```text
KISBroker

├── AuthClient

├── MarketClient

├── AccountClient

├── OrderClient

└── WebSocketClient
```

---

# AuthClient

책임

* OAuth
* Access Token
* Approval Key
* HashKey

비즈니스 로직 금지

---

# MarketClient

책임

* 현재가
* 호가
* 분봉
* 일봉
* 종목검색

---

# AccountClient

책임

* 계좌조회
* 잔고조회
* 주문가능금액
* 체결조회

---

# OrderClient

책임

* 매수
* 매도
* 정정
* 취소

주문 검증은 수행하지 않는다.

---

# WebSocketClient

책임

* 연결
* 인증
* Subscribe
* Unsubscribe
* Heartbeat
* Reconnect

---

# HTTP Client

httpx 사용

```python
AsyncClient

Client
```

Connection Pool 사용

Timeout 적용

Retry 적용

---

# Timeout

기본값

```text
Connect Timeout

5초

Read Timeout

10초

Write Timeout

10초
```

설정에서 변경 가능해야 한다.

---

# Retry Policy

재시도 대상

* Timeout
* Connection Error
* Temporary Server Error

재시도 횟수

```text
MAX_RETRY = 3
```

Exponential Backoff 적용

```text
1

↓

2

↓

4
```

---

# Authentication

모든 요청은

```text
TokenManager

↓

Access Token

↓

Header Builder

↓

HTTP Request
```

순으로 처리한다.

---

# Header Builder

Header 생성은 전담 객체에서 수행한다.

```text
Authorization

AppKey

AppSecret

Transaction ID

HashKey
```

Header를 하드코딩하지 않는다.

---

# Request Builder

REST 요청은 Builder를 사용한다.

```text
OrderRequest

↓

RequestBuilder

↓

HTTP Request
```

---

# Response Parser

응답 Parsing은 전담 객체에서 수행한다.

```text
HTTP Response

↓

ResponseParser

↓

DTO

↓

Service
```

Service는 JSON을 직접 처리하지 않는다.

---

# DTO Mapping

JSON

↓

Response DTO

↓

Domain Model

↓

Application

DTO와 Domain은 분리한다.

---

# Exception Mapping

HTTP 예외를 Domain 예외로 변환한다.

```text
Timeout

↓

NetworkError

----------------

401

↓

AuthenticationError

----------------

403

↓

AuthorizationError

----------------

404

↓

ResourceNotFoundError

----------------

429

↓

RateLimitError

----------------

500

↓

BrokerServerError
```

---

# API Logging

모든 요청은 로그를 남긴다.

기록 항목

* 요청 시간
* 응답 시간
* 응답 코드
* Transaction ID
* 처리 시간

민감정보는 기록하지 않는다.

---

# Sensitive Data

로그 금지

* Access Token
* App Key
* App Secret
* 계좌번호
* HashKey

마스킹 후 저장한다.

---

# Rate Limit

Broker는 호출 횟수를 관리한다.

```text
Application

↓

RateLimiter

↓

Broker

↓

KIS API
```

초과 시 Queue에서 대기한다.

---

# Cache

조회 API는 Cache 사용 가능

예시

```text
현재가

1초

호가

1초

계좌

3초

설정

60초
```

TTL 이후 재조회한다.

---

# Circuit Breaker

반복 실패 시

```text
Closed

↓

Open

↓

Half Open

↓

Closed
```

상태를 관리한다.

---

# WebSocket Architecture

```text
ConnectionManager

↓

Authenticator

↓

SubscriptionManager

↓

MessageParser

↓

EventPublisher
```

---

# WebSocket Reconnect

연결 종료 시

```text
Disconnect

↓

Retry

↓

Reconnect

↓

Restore Subscription
```

자동 수행한다.

---

# Subscription Manager

구독 목록을 유지한다.

재접속 시 자동 복구한다.

---

# Message Parser

수신 메시지는 Parser에서 처리한다.

```text
Raw Message

↓

Parser

↓

DTO

↓

EventBus
```

---

# API Event

Broker는 다음 이벤트를 발행한다.

```text
Connected

Disconnected

Authenticated

TokenExpired

PriceUpdated

OrderReceived

OrderExecuted

ErrorOccurred
```

---

# Client Lifetime

Application 실행 중

HTTP Client는 Singleton

WebSocket은 Singleton

TokenManager는 Singleton

---

# Broker Factory

Broker 생성은 Factory를 사용한다.

```text
BrokerFactory

↓

IBroker

↓

KISBroker
```

향후 Broker 추가 시 Factory만 수정한다.

---

# Configuration

API 관련 설정

```text
api/

    timeout

    retry

    base_url

    websocket_url

    logging

    cache

    rate_limit
```

Config 객체에서만 접근한다.

---

# Testing

모든 Client는 Mock 가능해야 한다.

테스트

* Unit Test
* Mock API Test
* Timeout Test
* Retry Test
* Exception Test
* Parser Test

실제 API 호출 없이 테스트 가능해야 한다.

---

# Validation Checklist

모든 구현은 아래 조건을 만족해야 한다.

* Broker Interface 준수
* REST 직접 호출 없음
* JSON 직접 처리 없음
* DTO 사용
* Domain 분리
* Retry 적용
* Timeout 적용
* Circuit Breaker 적용
* Cache 적용
* Rate Limiter 적용
* Singleton Client 사용
* 민감정보 로그 금지
* 테스트 가능 구조 유지

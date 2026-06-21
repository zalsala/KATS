# 22_API_INTEGRATION.md

# KATS KIS OpenAPI Integration Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS와 한국투자 OpenAPI의 연동 구조를 정의한다.

Broker Layer는 OpenAPI를 추상화하며, Application은 OpenAPI를 직접 호출하지 않는다.

---

# Architecture

```text id="api01"
Application

↓

Service

↓

Broker Interface

↓

KIS Broker

↓

REST API

WebSocket API
```

---

# Directory Structure

```text id="api02"
app/

    broker/

        interfaces/

        kis/

            auth/

            rest/

            websocket/

            parsers/

            mappers/

            handlers/

            exceptions/
```

---

# Broker Interface

```text id="api03"
Broker

├── Authentication

├── Account

├── Market

├── Order

├── Portfolio

└── WebSocket
```

Broker Interface만 Service에서 참조한다.

---

# Authentication Module

구성

* TokenManager
* ApprovalKeyManager
* HeaderBuilder
* HashKeyManager
* TokenCache

---

# REST Client

책임

* Request 생성
* Header 생성
* Retry
* Timeout
* Error 처리

REST Client는 Business Logic을 포함하지 않는다.

---

# WebSocket Client

책임

* 연결
* 재연결
* Ping
* Pong
* Subscription
* Message Parsing

---

# API Categories

```text id="api04"
Authentication

Account

Order

Market

Portfolio

Ranking

Condition

ETF

ETN

ELW
```

---

# Account Module

지원 기능

* 계좌조회
* 잔고조회
* 예수금조회
* 체결조회

---

# Order Module

지원 기능

* 매수
* 매도
* 정정
* 취소
* 주문조회

---

# Market Module

지원 기능

* 현재가
* 호가
* 체결
* 일봉
* 분봉
* 관심종목

---

# Portfolio Module

지원 기능

* 보유종목
* 평가손익
* 총자산
* 수익률

---

# Request Flow

```text id="api05"
Service

↓

Broker

↓

Request Builder

↓

REST Client

↓

KIS API

↓

Response Parser

↓

DTO

↓

Service
```

---

# WebSocket Flow

```text id="api06"
Strategy

↓

Subscribe

↓

WebSocket

↓

Message Parser

↓

EventBus

↓

Strategy
```

---

# DTO Mapping

REST Response는 Domain 객체로 직접 변환하지 않는다.

```text id="api07"
REST Response

↓

Response DTO

↓

Mapper

↓

Domain Model
```

---

# Error Handling

Broker는 API 오류를 Domain Exception으로 변환한다.

예시

```text id="api08"
HTTP Error

↓

Broker Exception

↓

Application Exception
```

---

# Retry Policy

적용 대상

* GET 요청
* 네트워크 오류
* Timeout

미적용

* 주문 요청
* 정정
* 취소

---

# Timeout

기본값

```text id="api09"
REST

10초

WebSocket

30초
```

ConfigManager에서 변경 가능하다.

---

# Rate Limiter

Broker 내부에서 호출 빈도를 관리한다.

기능

* 초당 호출 제한
* Queue
* Delay
* Burst 방지

---

# Cache

캐시 대상

* 종목정보
* 시장정보
* 설정값

실시간 시세는 캐시하지 않는다.

---

# Connection Manager

관리 항목

* REST Session
* WebSocket Session
* Heartbeat
* Reconnect
* Status

---

# Event

발행 Event

```text id="api10"
BrokerConnectedEvent

BrokerDisconnectedEvent

MarketDataReceivedEvent

OrderCompletedEvent

AccountUpdatedEvent
```

---

# Logging

기록

* Request ID
* API 종류
* 처리시간
* 결과

민감정보는 기록하지 않는다.

---

# Security

금지

* AppKey 로그 출력
* Secret 로그 출력
* Access Token 로그 출력
* 계좌번호 로그 출력

모든 민감정보는 마스킹한다.

---

# Performance Goal

* REST 응답 처리 50ms 이하
* WebSocket 메시지 처리 5ms 이하
* 재연결 3초 이내

---

# Testing

Unit Test

* Request Builder
* Header Builder
* Response Parser
* DTO Mapper
* Error Handler

Integration Test

* Authentication
* Account
* Market
* Order
* WebSocket

Mock Broker를 사용하여 테스트한다.

---

# Validation Checklist

* Broker Interface 사용
* REST/WebSocket 분리
* DTO 기반 매핑
* Retry 정책 적용
* Rate Limiter 적용
* EventBus 연동
* 민감정보 마스킹
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

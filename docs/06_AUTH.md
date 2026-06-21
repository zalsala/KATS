# 06_AUTH.md

# KATS Authentication Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 인증(Authentication) 계층을 정의한다.

인증 계층은 한국투자 OpenAPI와 통신하기 위한 모든 인증 정보를 관리하며, Application 계층은 인증 구현을 알지 못한다.

---

# 책임

Authentication Layer는 다음 기능만 담당한다.

* Access Token 발급
* Access Token 저장
* Access Token 갱신
* Access Token 만료 확인
* HashKey 발급
* Approval Key 발급
* 인증 Header 생성

비즈니스 로직은 포함하지 않는다.

---

# Architecture

```text
Application

↓

Service

↓

IBroker

↓

AuthService

↓

TokenManager

↓

HeaderBuilder

↓

KIS OAuth
```

---

# Directory Structure

```text
app/

broker/

    auth/

        auth_service.py

        token_manager.py

        token_storage.py

        approval_manager.py

        hashkey_manager.py

        header_builder.py

        auth_models.py

        auth_exceptions.py
```

---

# Component Overview

```text
AuthService

├── TokenManager

├── ApprovalManager

├── HashKeyManager

├── HeaderBuilder

└── TokenStorage
```

---

# AuthService

책임

* 인증 초기화
* 토큰 획득
* 토큰 갱신
* 인증 상태 확인

외부에서 사용하는 유일한 인증 진입점이다.

---

# TokenManager

책임

* Access Token 관리
* 만료 시간 계산
* 자동 갱신
* 메모리 캐시 관리

---

# TokenStorage

책임

* 로컬 저장
* 로컬 로드
* 암호화 저장(향후 지원)

기본 저장 위치

```text
data/

    auth/

        token.json
```

---

# ApprovalManager

책임

* Approval Key 요청
* Approval Key 캐시
* WebSocket 인증 지원

---

# HashKeyManager

책임

* HashKey 생성 요청
* 주문 요청용 HashKey 관리

HashKey는 필요한 요청에서만 생성한다.

---

# HeaderBuilder

책임

인증 Header 생성

```text
Authorization

AppKey

AppSecret

HashKey

Transaction ID
```

Application은 Header를 직접 생성하지 않는다.

---

# Authentication Flow

```text
Application Start

↓

Load Token

↓

Valid?

↓

YES

↓

Use Token

↓

NO

↓

Request Token

↓

Save Token

↓

Continue
```

---

# Token Lifecycle

```text
Issue

↓

Cache

↓

Use

↓

Expire Check

↓

Refresh

↓

Cache Update
```

---

# Memory Cache

Token은 메모리에서 우선 조회한다.

```text
Memory

↓

Disk

↓

OAuth API
```

---

# Token Validation

매 요청마다

```text
is_expired()

↓

False

↓

Use

----------------

True

↓

Refresh
```

---

# Refresh Policy

자동 갱신

조건

* 만료
* 인증 실패
* 강제 재발급

중복 갱신을 방지하기 위해 Lock을 사용한다.

---

# Thread Safety

TokenManager는 Thread Safe 해야 한다.

동시에 여러 요청이 발생해도

토큰은 한 번만 갱신한다.

---

# Token Model

```python
AccessToken

token

expired_at

issued_at
```

만료 시각은 UTC 기준으로 저장한다.

---

# Header Generation

모든 REST 요청

```text
Request

↓

HeaderBuilder

↓

HTTP Client
```

직접 Header를 생성하지 않는다.

---

# WebSocket Authentication

```text
WebSocket

↓

ApprovalManager

↓

Approval Key

↓

Connection
```

Approval Key는 Access Token과 별도로 관리한다.

---

# Local Storage

토큰 저장

```text
data/

    auth/

        token.json

        approval.json
```

파일 접근은 TokenStorage만 수행한다.

---

# Security Policy

저장 금지

* App Secret 로그 출력
* Access Token 로그 출력
* Approval Key 로그 출력

민감정보는 모두 마스킹한다.

---

# Configuration

```text
auth/

    auto_refresh

    token_path

    refresh_margin

    retry

    timeout
```

Config 객체를 통해 접근한다.

---

# Exception Hierarchy

```text
AuthenticationError

├── TokenExpiredError

├── TokenRefreshError

├── ApprovalKeyError

├── HashKeyError

└── InvalidCredentialError
```

---

# Retry Policy

인증 실패

재시도

```text
1

↓

2

↓

4
```

최대 3회

---

# Lock Policy

동시에 여러 Thread가

refresh()

를 호출하면

한 개만 수행한다.

나머지는 완료를 기다린다.

---

# State Machine

```text
INITIAL

↓

LOADING

↓

READY

↓

EXPIRED

↓

REFRESHING

↓

READY

↓

FAILED
```

---

# Logging

기록

* Token 발급
* Refresh
* 만료
* 인증 실패

기록 금지

* Token 값
* Secret
* Approval Key

---

# Unit Test

반드시 작성

* Token Load
* Token Save
* Expire Check
* Refresh
* Concurrent Refresh
* Approval Key
* HashKey
* Header Builder
* Exception

---

# Integration Test

Mock OAuth 사용

실제 API 호출 없이 테스트 가능해야 한다.

---

# Validation Checklist

* AuthService 단일 진입점
* TokenManager 사용
* HeaderBuilder 사용
* TokenStorage 사용
* Thread Safe
* Singleton 적용
* 자동 Refresh
* Lock 적용
* 민감정보 로그 금지
* 테스트 완료
* 문서와 구현 일치

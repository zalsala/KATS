# 19_CURSOR_RULES.md

# KATS Cursor AI Development Rules

Version: 1.0.0

---

# 목적

본 문서는 Cursor AI가 KATS 프로젝트를 개발할 때 반드시 따라야 하는 개발 규칙을 정의한다.

모든 코드 생성은 본 문서를 최우선으로 준수한다.

---

# AI 역할

Cursor AI는 다음 역할만 수행한다.

* 기능 구현
* 리팩토링
* 테스트 작성
* 문서 업데이트
* 버그 수정

프로젝트 구조를 임의로 변경하지 않는다.

---

# 최우선 원칙

Priority

```text id="2sqgk8"
Architecture

↓

Specification

↓

Coding Rule

↓

Implementation
```

구현보다 설계 문서를 우선한다.

---

# 금지 사항

Cursor는 다음을 수행하지 않는다.

* Architecture 변경
* Layer 무시
* Repository 우회
* Broker 직접 호출
* UI에서 Database 접근
* Service에서 SQL 작성
* 하드코딩
* 임의 라이브러리 추가

---

# 프로젝트 구조

반드시 다음 구조를 유지한다.

```text id="13cb9x"
Controller

↓

Service

↓

Domain

↓

Repository

↓

Database
```

또는

```text id="i5t44d"
Controller

↓

Service

↓

Broker

↓

KIS OpenAPI
```

---

# 계층 규칙

UI

↓

Controller

↓

Service

↓

Repository

↓

SQLite

UI

↓

Controller

↓

Service

↓

Broker

↓

REST API

계층을 건너뛰지 않는다.

---

# 생성 규칙

새로운 기능을 구현할 때

반드시

1.

DTO 생성

↓

2.

Interface 작성

↓

3.

Implementation 작성

↓

4.

Unit Test 작성

↓

5.

문서 수정

순으로 구현한다.

---

# Import Rule

허용

```text id="1am9um"
Controller

↓

Service
```

```text id="h0zwdr"
Service

↓

Repository
```

```text id="3ec2js"
Service

↓

Broker
```

금지

```text id="i3cbg8"
UI

↓

Repository
```

```text id="xkpm3g"
Domain

↓

Broker
```

```text id="gsy3dk"
Repository

↓

Service
```

---

# Domain Rule

Domain은

절대로

* SQL
* HTTP
* Config
* Logger
* GUI

를 참조하지 않는다.

---

# Service Rule

Service는

* Use Case 하나만 담당
* Transaction 관리
* Event 발행

Repository 직접 생성 금지

Broker 직접 생성 금지

DI를 사용한다.

---

# Repository Rule

Repository는

Database 접근만 수행한다.

금지

* Business Logic
* Validation
* REST API

---

# Broker Rule

Broker는

REST API Adapter이다.

금지

* Portfolio 계산
* Risk 계산
* Strategy 실행

---

# Event Rule

모든 모듈 간 통신은

가능하면 EventBus를 사용한다.

직접 참조를 최소화한다.

---

# Configuration Rule

설정값

금지

```python id="x04rdr"
timeout = 30
```

허용

```python id="q2vddr"
timeout = config.api.timeout
```

---

# Logging Rule

사용

```python id="8by81u"
logger.info()

logger.warning()

logger.error()
```

금지

```python id="g7v8re"
print()
```

---

# Exception Rule

예외는 무시하지 않는다.

금지

```python id="8c8fqu"
except:
    pass
```

허용

```python id="tw4kso"
except OrderException as ex:
    logger.exception(ex)
    raise
```

---

# Type Hint

모든 Public Method

Type Hint 필수

예시

```python id="ny9ts0"
def submit_order(
    request: OrderRequestDTO
) -> OrderResult:
```

---

# Docstring

Public Class

Public Function

반드시 작성

Google Style 사용

---

# Async Rule

허용

* WebSocket
* Notification
* Logging

금지

* Order
* Risk

---

# File Size

권장

```text id="1tk99g"
500 Lines 이하
```

초과 시 분리한다.

---

# Test Rule

새로운 기능은

반드시

Unit Test 작성

기존 테스트 통과

Regression 확인

---

# Commit Rule

한 Commit

↓

한 기능

Commit Message

```text id="5njlwm"
feat:

fix:

refactor:

docs:

test:
```

Conventional Commit 사용

---

# Pull Request

PR에는 반드시 포함

* 변경 내용
* 테스트 결과
* 관련 문서
* 영향 범위

---

# AI Output Rule

Cursor가 생성하는 코드는

반드시

* Ruff 통과
* Black 통과
* mypy 통과
* pytest 통과

를 목표로 작성한다.

---

# 생성 우선순위

```text id="hy74o0"
Correctness

↓

Architecture

↓

Readability

↓

Performance

↓

Optimization
```

성능보다 구조를 우선한다.

---

# Refactoring Rule

리팩토링은

동작 변경 없이 수행한다.

테스트가 없는 리팩토링은 금지한다.

---

# Code Review Checklist

검토 항목

* Architecture 준수
* Layer 준수
* DI 사용
* EventBus 사용
* Exception 처리
* Logging
* Type Hint
* Test
* 문서 업데이트

---

# Definition of Done

기능 완료 조건

* 구현 완료
* Unit Test 통과
* Integration Test 통과
* Ruff 통과
* Black 통과
* mypy 통과
* 문서 업데이트
* 코드 리뷰 완료

---

# Cursor Prompt Rule

Cursor에 기능을 요청할 때 항상 다음 규칙을 따른다.

```text id="p9sq8y"
1. 구현 대상 명시

2. 관련 문서 확인

3. 기존 구조 유지

4. 테스트 작성

5. 문서 업데이트

6. 구현 완료 후 자체 검토
```

---

# Validation Checklist

* Architecture 우선
* Layer 위반 없음
* DI 적용
* EventBus 사용
* Type Hint 적용
* Google Docstring 적용
* Test 우선 개발
* Conventional Commit 사용
* 문서와 코드 일치
* Cursor AI 규칙 준수

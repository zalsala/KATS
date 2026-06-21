# 03_CODING_RULE.md

# KATS Coding Standards

Version: 1.0.0

---

# 목적

본 문서는 KATS 프로젝트의 모든 Python 코드에 적용되는 표준 코딩 규칙을 정의한다.

모든 AI(Cursor, Claude Code, GitHub Copilot 등)와 개발자는 동일한 규칙을 따른다.

---

# Python Version

Python 3.12 이상

최신 문법 사용을 권장한다.

---

# Formatter

Black 사용

설정

* line-length = 100

---

# Linter

Ruff 사용

모든 Warning 제거

모든 Error 제거

---

# Type Checker

mypy 사용

모든 Public Method

Type Hint 100%

---

# Docstring

Google Style Docstring 사용

예시

```python
class OrderService:
    """주문 서비스."""

    def place_order(self, request: OrderRequest) -> OrderResult:
        """주문을 생성한다.

        Args:
            request:
                주문 요청 객체

        Returns:
            주문 결과

        Raises:
            OrderValidationError:
                주문 검증 실패
        """
```

---

# Import 규칙

순서

```text
Python Standard Library

↓

Third Party

↓

Application
```

예시

```python
from pathlib import Path
from typing import Final

import pandas as pd

from app.service.order_service import OrderService
```

금지

```python
from xxx import *
```

---

# Naming Convention

## Package

snake_case

```text
market_data
order_service
```

---

## Module

snake_case

```text
order_repository.py

market_service.py
```

---

## Class

PascalCase

```python
MarketService

OrderRepository

PortfolioManager
```

---

## Function

snake_case

```python
get_current_price()

place_order()

load_config()
```

---

## Variable

snake_case

```python
current_price

order_quantity
```

---

## Constant

UPPER_CASE

```python
MAX_RETRY

API_TIMEOUT

DEFAULT_PORT
```

---

## Enum

PascalCase

```python
OrderType

MarketType
```

Enum 값

```python
class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
```

---

# Class Rules

클래스는 하나의 책임만 가진다.

권장

* 300줄 이하
* Public Method 20개 이하

금지

* God Object
* Utility Class 남용

---

# Function Rules

권장

* 50줄 이하
* Parameter 5개 이하
* Return 1개

중첩

최대 3단계

---

# Exception Rules

예외를 무시하지 않는다.

금지

```python
except Exception:
    pass
```

허용

```python
except NetworkError as exc:
    logger.exception(exc)
    raise
```

---

# Logging Rules

print() 사용 금지

logging 사용

예시

```python
logger.info("Order submitted")

logger.warning("Retry order")

logger.error("Order failed")

logger.exception(exc)
```

---

# Magic Number

금지

```python
if retry > 3:
```

허용

```python
MAX_RETRY = 3

if retry > MAX_RETRY:
```

---

# Configuration

설정값

Config 객체 사용

금지

```python
API_KEY = "..."
```

허용

```python
config.api_key
```

---

# Dataclass

DTO

Request

Response

Value Object

Dataclass 사용

예시

```python
@dataclass(slots=True)
class OrderRequest:
    symbol: str
    quantity: int
```

---

# Pydantic

외부 입력은

Pydantic Validation

사용

예시

```python
class LoginRequest(BaseModel):
    app_key: str
```

---

# Async

REST

동기

WebSocket

비동기

asyncio 사용

GUI Thread에서는 async 호출 금지

---

# Thread

GUI Thread

UI만 담당

Worker Thread

REST

Database

Indicator

Strategy

---

# Event

모듈 간 직접 호출 최소화

EventBus 사용

예시

```text
PriceUpdatedEvent

↓

SignalEvent

↓

OrderRequestEvent
```

---

# Repository Rules

Repository

Database만 담당

금지

* API 호출
* Business Logic

---

# Service Rules

Service는

Use Case 담당

금지

* SQL
* GUI
* REST 직접 호출

---

# Controller Rules

Controller는

입력 검증

↓

DTO 생성

↓

Service 호출

만 수행한다.

---

# UI Rules

UI

비즈니스 로직 금지

Database 접근 금지

API 접근 금지

---

# Strategy Rules

Strategy는

Signal 생성만 수행한다.

금지

Broker 호출

DB 저장

UI 접근

---

# Broker Rules

Broker는

외부 API Adapter이다.

반드시 Interface 구현

---

# Database Rules

Repository만 접근

Transaction은 Service에서 관리

---

# Cache Rules

TTL 적용

Cache 직접 수정 금지

CacheManager 사용

---

# Return Rules

None 반환 최소화

Optional 명시

예시

```python
Optional[Account]
```

---

# Boolean

금지

```python
if flag == True:
```

허용

```python
if flag:
```

---

# Comparison

금지

```python
len(items) == 0
```

허용

```python
if not items:
```

---

# String

f-string 사용

금지

```python
"Price : " + price
```

허용

```python
f"Price : {price}"
```

---

# Path

pathlib 사용

금지

```python
os.path.join()
```

---

# Resource

with 문 사용

예시

```python
with open(path) as file:
```

---

# Dependency Injection

Service 생성 시

Constructor Injection

사용

예시

```python
class OrderService:

    def __init__(
        self,
        broker: IBroker,
        repository: IOrderRepository,
    ):
        ...
```

---

# Testing Rules

모든 Public Method

Unit Test 작성

외부 API

Mock 사용

Database

Test DB 사용

Coverage

80% 이상

---

# File Structure

권장 순서

```text
Module Docstring

↓

Imports

↓

Constants

↓

Enums

↓

Dataclass

↓

Interface

↓

Implementation

↓

Private Function
```

---

# Comment Rules

주석은

왜(Why)를 설명한다.

무엇(What)은 코드로 표현한다.

금지

```python
i += 1

# i를 증가시킨다.
```

---

# Code Review Checklist

모든 PR은 아래 항목을 만족해야 한다.

* Ruff 통과
* Black 적용
* mypy 통과
* Test 성공
* Type Hint 적용
* Docstring 작성
* Logger 적용
* Exception 처리
* Config 사용
* 하드코딩 없음
* Magic Number 없음
* print() 없음
* 순환 참조 없음
* Layer 위반 없음
* Repository Pattern 준수
* Service Layer 준수
* EventBus 규칙 준수
* 테스트 코드 포함
* 문서 업데이트 완료

---

# Definition of Done

코드는 다음 조건을 만족해야 완료로 인정한다.

* 기능 구현 완료
* 예외 처리 완료
* 테스트 통과
* 코드 스타일 준수
* 문서 반영 완료
* 아키텍처 위반 없음
* 기술 부채 없음
* 임시 코드 없음
* TODO 없음
* 리팩터링 불필요 수준의 품질 확보

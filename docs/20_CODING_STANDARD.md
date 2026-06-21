# 20_CODING_STANDARD.md

# KATS Python Coding Standard

Version: 1.0.0

---

# 목적

본 문서는 KATS 프로젝트의 Python 코딩 표준을 정의한다.

모든 소스코드는 본 문서의 규칙을 준수하며, 일관성 있는 코드 품질을 유지한다.

---

# Python Version

지원 버전

```text id="q3l8xm"
Python 3.12
```

다른 버전의 기능은 사용하지 않는다.

---

# Formatter

사용

```text id="d5j4ha"
Black
```

수동 포매팅보다 Black 규칙을 우선한다.

---

# Linter

사용

```text id="j8m2pd"
Ruff
```

Lint Error는 0개를 유지한다.

---

# Type Checker

사용

```text id="r2v7ku"
mypy
```

Public API는 반드시 Type Hint를 작성한다.

---

# Import Rule

순서

```text id="k8n6ef"
Standard Library

↓

Third Party

↓

Project Package
```

Wildcard Import는 사용하지 않는다.

---

# Naming Convention

Module

```text id="r4p8vx"
snake_case.py
```

Class

```text id="z5h9nt"
PascalCase
```

Function

```text id="y7d4la"
snake_case()
```

Variable

```text id="w3u2gs"
snake_case
```

Constant

```text id="t9k3dm"
UPPER_CASE
```

Private

```text id="p2c8ja"
_private_name
```

---

# File Size

권장

* 500줄 이하

초과 시 모듈을 분리한다.

---

# Function Size

권장

* 50줄 이하

복잡한 로직은 Helper 또는 Service로 분리한다.

---

# Class Size

권장

* 300줄 이하

하나의 책임만 갖도록 설계한다.

---

# Docstring

Public Class와 Public Function은 Google Style Docstring을 작성한다.

예시

```python id="h7z6ua"
def place_order(request: OrderRequestDTO) -> OrderResult:
    """Submit an order.

    Args:
        request: Order request.

    Returns:
        Order execution result.
    """
```

---

# Type Hint

필수

```python id="q5b2sm"
def get_price(symbol: str) -> Decimal:
    ...
```

금지

```python id="m4x8pk"
def get_price(symbol):
    ...
```

---

# Exception Rule

구체적인 예외만 처리한다.

허용

```python id="x1g9vr"
except OrderException:
    ...
```

금지

```python id="b8f3yd"
except:
    ...
```

---

# Logging

사용

```python id="s6n7te"
logger.debug()

logger.info()

logger.warning()

logger.error()

logger.exception()
```

print()는 디버깅 외에는 사용하지 않는다.

---

# Magic Number

금지

```python id="u9m4lp"
if retry > 3:
```

허용

```python id="f2k8as"
MAX_RETRY = 3

if retry > MAX_RETRY:
```

---

# Boolean

허용

```python id="d4j9xe"
if is_connected:
```

금지

```python id="n6v5ct"
if is_connected == True:
```

---

# None Check

허용

```python id="p8r2zw"
if value is None:
```

금지

```python id="a5w1mu"
if value == None:
```

---

# Collection

List, Dict, Set은 Type Hint를 사용한다.

```python id="g3x9lk"
list[str]

dict[str, Decimal]

set[str]
```

---

# Decimal

금액 계산은 float를 사용하지 않는다.

```python id="v2e4rb"
Decimal
```

---

# Dataclass

DTO와 Value Object는 dataclass 사용을 권장한다.

Entity는 필요 시 일반 클래스로 구현한다.

---

# Dependency Injection

객체 생성

금지

```python id="j5m8pt"
service = OrderService()
```

허용

```python id="e7k2yh"
def __init__(
    self,
    service: OrderService,
):
```

---

# Async

허용

* WebSocket
* Logging
* Notification

금지

* Order
* Risk

---

# Configuration

설정은 ConfigManager를 통해 접근한다.

하드코딩을 금지한다.

---

# TODO Rule

TODO는 이슈 번호를 포함한다.

예시

```text id="c4n7fw"
TODO(KATS-102): Add retry policy
```

---

# Test Rule

새로운 Public Method는 반드시 Unit Test를 작성한다.

버그 수정 시 Regression Test를 추가한다.

---

# Security Rule

코드에 포함 금지

* App Key
* App Secret
* Access Token
* 계좌번호
* 개인정보

---

# Review Checklist

* Type Hint 작성
* Docstring 작성
* Logging 적용
* Exception 처리
* Unit Test 작성
* Black 통과
* Ruff 통과
* mypy 통과

---

# Validation Checklist

* Python 3.12 기준
* Black 적용
* Ruff 적용
* mypy 적용
* Google Docstring 적용
* Type Hint 100%
* Decimal 사용
* DI 사용
* 하드코딩 금지
* Unit Test 작성
* 문서와 구현 일치

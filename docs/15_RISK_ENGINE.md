# 15_RISK_ENGINE.md

# KATS Risk Engine Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 Risk Engine 설계를 정의한다.

모든 주문은 반드시 Risk Engine을 통과해야 하며, Risk Engine을 우회하여 주문을 실행할 수 없다.

Risk Engine은 자동매매 시스템의 최종 안전장치이다.

---

# Architecture

```text id="d3d6pn"
Strategy

↓

Signal

↓

Risk Engine

↓

Risk Rules

↓

Order Service

↓

Broker
```

---

# Directory Structure

```text id="m4tkh8"
app/

    risk/

        engine/

        rules/

        validators/

        calculators/

        policies/

        exceptions/

        context/
```

---

# Risk Engine 구성

```text id="zj6hy2"
RiskEngine

├── RiskValidator

├── RuleManager

├── PositionChecker

├── ExposureCalculator

├── LossCalculator

├── EmergencyManager
```

---

# 주문 처리 순서

```text id="6w0sqa"
Signal

↓

Parameter Validation

↓

Market Status Check

↓

Position Check

↓

Exposure Check

↓

Risk Rule Check

↓

Daily Loss Check

↓

Order Approval

↓

Order Service
```

---

# Risk Rule

기본 규칙

* 장 운영시간 확인
* 종목 거래 가능 여부
* 최대 주문 금액
* 최대 주문 수량
* 최대 보유 종목 수
* 최대 종목 비중
* 최대 계좌 노출 비율
* 일일 손실 제한
* 연속 손실 제한
* 중복 주문 제한

---

# Market Validation

확인 항목

```text id="s7xg7r"
Market Open

Trading Halt

Volatility Interruption

ETF 여부

상장폐지 여부
```

---

# Position Validation

검사

* 기존 보유 여부
* 평균단가
* 매도 가능 수량
* 중복 진입
* 분할매수 허용 여부

---

# Exposure Management

계산 항목

```text id="57m4t7"
총 자산

현금

평가금액

투자금액

종목별 비중

현금 비율
```

---

# Position Size

기본 계산 방식

```text id="7r77cs"
투자 가능 금액

↓

Risk %

↓

주문 가능 수량
```

Position Size 계산은 별도 Calculator에서 수행한다.

---

# Daily Loss Limit

예시

```text id="pjlwmn"
일일 손실

3%

↓

모든 신규 주문 차단
```

관리자 해제 전까지 유지한다.

---

# Consecutive Loss

예시

```text id="03h3zi"
연속 손실

5회

↓

전략 자동 중지
```

---

# Max Position

예시

```text id="4q7eqh"
최대 보유 종목

20개
```

설정에서 변경 가능하다.

---

# Duplicate Order

동일 조건

* 동일 종목
* 동일 방향
* 동일 가격
* 동일 수량

일정 시간 내 중복 주문은 차단한다.

---

# Emergency Stop

다음 상황에서 즉시 주문을 차단한다.

* Broker 연결 끊김
* WebSocket 끊김
* 인증 실패
* 계좌 오류
* 일일 손실 초과
* 시스템 오류

---

# Circuit Breaker

```text id="d4dd4x"
정상

↓

경고

↓

차단

↓

복구
```

상태를 관리한다.

---

# Rule Priority

```text id="ujmjlwm"
Critical

↓

High

↓

Normal

↓

Low
```

Critical Rule 실패 시 즉시 종료한다.

---

# Risk Result

판정 결과

```text id="20cng6"
APPROVED

REJECTED

WARNING

BLOCKED
```

---

# Risk Response

반환 정보

```text id="vgn6yk"
Result

Rule Name

Reason

Message

Timestamp
```

---

# Policy

지원 정책

```text id="wnrz1y"
Conservative

Balanced

Aggressive

Custom
```

---

# Portfolio Risk

계산 항목

* 총 투자 비율
* 종목 집중도
* 업종 집중도
* 현금 비율
* 변동성

---

# Strategy Risk

전략별 제한

* 최대 동시 주문
* 최대 손실
* 최대 투자금
* 최대 보유 종목

전략별로 독립 적용한다.

---

# Exception

```text id="8b2m5r"
RiskException

├── MarketClosedException

├── PositionLimitException

├── DailyLossException

├── ExposureException

├── DuplicateOrderException

└── EmergencyStopException
```

---

# Event

발행 Event

```text id="67tbxh"
RiskApprovedEvent

RiskRejectedEvent

EmergencyStopEvent

RiskWarningEvent
```

---

# Logging

기록

* Rule 이름
* 판정 결과
* 거부 사유
* 처리 시간

민감정보는 기록하지 않는다.

---

# Performance

목표

* Risk Check 3ms 이하
* Rule 실행 1ms 이하
* 전체 검증 10ms 이하

---

# Testing

Unit Test

* Rule 검증
* Position Size
* Daily Loss
* Duplicate Order
* Exposure

Integration Test

* Strategy → Risk
* Risk → Order
* Emergency Stop
* Recovery

---

# Validation Checklist

* 모든 주문 Risk Engine 통과
* Rule 기반 검증
* Emergency Stop 지원
* Position Size 계산 지원
* Daily Loss 제한
* Duplicate Order 차단
* Strategy별 Risk 적용
* EventBus 연동
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

# 16_BACKTEST_ENGINE.md

# KATS Backtest Engine Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 백테스트 엔진 설계를 정의한다.

Backtest Engine은 과거 데이터를 이용하여 전략을 검증하고 성과를 분석하는 시스템이다.

실시간 자동매매와 동일한 Strategy Engine을 사용하여 코드 중복을 최소화한다.

---

# Architecture

```text id="1h8srb"
Historical Data

↓

Data Loader

↓

Backtest Engine

↓

Strategy Engine

↓

Risk Engine

↓

Virtual Broker

↓

Portfolio

↓

Performance Analyzer

↓

Report
```

---

# Directory Structure

```text id="n7m9tb"
app/

    backtest/

        engine/

        loader/

        broker/

        analyzer/

        reports/

        statistics/

        optimizer/

        exporter/

        exceptions/
```

---

# Backtest Engine 구성

```text id="v0y2wa"
BacktestEngine

├── DataLoader

├── SimulationBroker

├── StrategyRunner

├── RiskEngine

├── PortfolioEngine

├── StatisticsEngine

└── ReportGenerator
```

---

# 실행 순서

```text id="m8f4pk"
Load Data

↓

Initialize Strategy

↓

Replay Candle

↓

Generate Signal

↓

Risk Check

↓

Virtual Order

↓

Portfolio Update

↓

Statistics

↓

Finish
```

---

# 지원 데이터

* 일봉
* 분봉
* Tick(향후)
* CSV
* SQLite
* Parquet(향후)

---

# Data Loader

책임

* 데이터 읽기
* 정렬
* 결측치 처리
* 시간 검증
* 심볼 병합

---

# Simulation Broker

Virtual Broker는 실제 API를 호출하지 않는다.

지원

* 시장가
* 지정가
* 부분 체결
* 주문 취소
* 주문 정정

---

# Fill Engine

체결 규칙

```text id="4t4u2z"
Signal

↓

Order

↓

Matching

↓

Fill

↓

Portfolio
```

슬리피지와 수수료를 반영한다.

---

# Slippage

지원 방식

```text id="0c3l8k"
Fixed

Percent

ATR Based

Custom
```

---

# Commission

지원

* 고정 수수료
* 비율 수수료
* 사용자 정의

---

# Tax

국내 주식 거래세를 설정으로 관리한다.

실행 시점의 정책을 적용할 수 있도록 설계한다.

---

# Portfolio Engine

계산

* 총 자산
* 현금
* 평가금액
* 실현손익
* 미실현손익

---

# Statistics

계산 항목

```text id="bd8lqy"
Total Return

Annual Return

CAGR

MDD

Sharpe Ratio

Sortino Ratio

Calmar Ratio

Profit Factor

Win Rate

Average Profit

Average Loss

Expectancy
```

---

# Equity Curve

생성

```text id="4d7z7v"
Initial Capital

↓

Trade

↓

Daily Equity

↓

Final Equity
```

---

# Drawdown

계산

* MDD
* Average Drawdown
* Drawdown Duration

---

# Benchmark

비교 대상

* KOSPI
* KOSDAQ
* 사용자 지정 지수

---

# Walk Forward Test

지원

```text id="q0u6ja"
Train

↓

Validate

↓

Forward Test
```

---

# Parameter Optimization

지원 방식

```text id="c1ct7k"
Grid Search

Random Search

Genetic Algorithm (향후)
```

---

# Multi Strategy

동시에 여러 전략을 테스트할 수 있다.

```text id="v7ahq5"
Strategy A

+

Strategy B

+

Strategy C
```

---

# Multi Symbol

여러 종목 동시 테스트 지원

---

# Report

생성 형식

```text id="2s8m4e"
HTML

PDF

CSV

JSON
```

---

# Report 내용

* 전략 정보
* 기간
* 종목
* 거래 횟수
* 수익률
* 손익 그래프
* Equity Curve
* Drawdown
* 거래 목록

---

# Export

지원

* CSV
* Excel
* JSON

---

# Event

발행 Event

```text id="4a2jtk"
BacktestStartedEvent

BacktestProgressEvent

TradeExecutedEvent

BacktestCompletedEvent
```

---

# Performance

목표

* 10년 일봉 1종목 5초 이내
* 100만 Candle 처리 지원
* 메모리 사용 최소화

---

# Testing

Unit Test

* Data Loader
* Fill Engine
* Statistics
* Report
* Portfolio

Integration Test

* Strategy 실행
* Risk 적용
* Virtual Broker
* Report 생성

---

# Validation Checklist

* 실시간 Strategy 재사용
* Virtual Broker 사용
* Risk Engine 연동
* Slippage 지원
* Commission 지원
* Tax 지원
* Statistics 제공
* Report 생성
* Optimization 지원
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

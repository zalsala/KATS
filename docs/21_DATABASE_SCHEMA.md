# 21_DATABASE_SCHEMA.md

# KATS Database Schema Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 SQLite 데이터베이스 구조를 정의한다.

모든 데이터는 Repository를 통해 접근하며, SQL을 직접 호출하지 않는다.

---

# Database Engine

사용

```text id="db01"
SQLite 3
```

향후 지원

* PostgreSQL
* MySQL

---

# Directory Structure

```text id="db02"
data/

    database/

        kats.db

        migrations/

        backup/
```

---

# Architecture

```text id="db03"
Application

↓

Repository

↓

SQLite

↓

Database
```

---

# Tables

```text id="db04"
accounts

orders

positions

executions

strategies

watchlists

symbols

market_data

daily_prices

settings

logs

backtest_results

system_events
```

---

# accounts

| Column       | Type       |
| ------------ | ---------- |
| id           | INTEGER PK |
| account_no   | TEXT       |
| account_name | TEXT       |
| broker       | TEXT       |
| created_at   | DATETIME   |
| updated_at   | DATETIME   |

---

# positions

| Column        | Type       |
| ------------- | ---------- |
| id            | INTEGER PK |
| symbol        | TEXT       |
| quantity      | INTEGER    |
| avg_price     | DECIMAL    |
| current_price | DECIMAL    |
| profit        | DECIMAL    |
| profit_rate   | DECIMAL    |
| updated_at    | DATETIME   |

---

# orders

| Column     | Type       |
| ---------- | ---------- |
| id         | INTEGER PK |
| order_no   | TEXT       |
| symbol     | TEXT       |
| side       | TEXT       |
| order_type | TEXT       |
| price      | DECIMAL    |
| quantity   | INTEGER    |
| status     | TEXT       |
| strategy   | TEXT       |
| created_at | DATETIME   |

---

# executions

| Column          | Type       |
| --------------- | ---------- |
| id              | INTEGER PK |
| order_no        | TEXT       |
| execution_price | DECIMAL    |
| quantity        | INTEGER    |
| executed_at     | DATETIME   |

---

# strategies

| Column     | Type       |
| ---------- | ---------- |
| id         | INTEGER PK |
| name       | TEXT       |
| enabled    | BOOLEAN    |
| parameters | JSON       |
| symbols    | JSON       |
| created_at | DATETIME   |

---

# watchlists

| Column     | Type       |
| ---------- | ---------- |
| id         | INTEGER PK |
| name       | TEXT       |
| symbol     | TEXT       |
| sort_order | INTEGER    |

---

# symbols

| Column     | Type     |
| ---------- | -------- |
| symbol     | TEXT PK  |
| name       | TEXT     |
| market     | TEXT     |
| sector     | TEXT     |
| updated_at | DATETIME |

---

# market_data

실시간 Cache 저장

| Column    | Type     |
| --------- | -------- |
| symbol    | TEXT     |
| price     | DECIMAL  |
| volume    | INTEGER  |
| timestamp | DATETIME |

---

# daily_prices

OHLCV 데이터

| Column     | Type    |
| ---------- | ------- |
| symbol     | TEXT    |
| trade_date | DATE    |
| open       | DECIMAL |
| high       | DECIMAL |
| low        | DECIMAL |
| close      | DECIMAL |
| volume     | INTEGER |

---

# settings

프로그램 설정 저장

| Column     | Type     |
| ---------- | -------- |
| key        | TEXT PK  |
| value      | TEXT     |
| updated_at | DATETIME |

---

# logs

| Column     | Type       |
| ---------- | ---------- |
| id         | INTEGER PK |
| level      | TEXT       |
| module     | TEXT       |
| message    | TEXT       |
| created_at | DATETIME   |

---

# backtest_results

| Column       | Type       |
| ------------ | ---------- |
| id           | INTEGER PK |
| strategy     | TEXT       |
| symbol       | TEXT       |
| start_date   | DATE       |
| end_date     | DATE       |
| cagr         | DECIMAL    |
| mdd          | DECIMAL    |
| sharpe       | DECIMAL    |
| total_return | DECIMAL    |

---

# system_events

| Column     | Type       |
| ---------- | ---------- |
| id         | INTEGER PK |
| event_name | TEXT       |
| payload    | JSON       |
| created_at | DATETIME   |

---

# Index

생성

```text id="db05"
orders(order_no)

orders(symbol)

positions(symbol)

daily_prices(symbol, trade_date)

market_data(symbol)
```

---

# Migration

도구

```text id="db06"
Alembic
```

모든 Schema 변경은 Migration으로 관리한다.

---

# Transaction

원칙

* Service에서 시작
* Repository에서 Commit 금지
* Rollback 지원

---

# Backup

자동 백업

```text id="db07"
data/

    backup/

        kats_YYYYMMDD.db
```

---

# Repository Mapping

```text id="db08"
AccountRepository

OrderRepository

PositionRepository

StrategyRepository

SettingsRepository
```

---

# Performance Goal

* 조회 5ms 이하
* 저장 10ms 이하
* Index Scan 우선
* Full Scan 최소화

---

# Validation Checklist

* SQLite 사용
* Repository 패턴 적용
* Migration 지원
* Index 적용
* Transaction 분리
* Backup 지원
* JSON 컬럼 사용
* SQL 직접 호출 금지
* Unit Test 작성
* 문서와 구현 일치

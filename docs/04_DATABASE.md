# 04_DATABASE.md

# KATS Database Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 데이터 저장 구조를 정의한다.

모든 데이터는 Repository Pattern을 통해 접근하며, SQLite를 기본 데이터베이스로 사용한다.

향후 PostgreSQL로 교체 가능하도록 설계한다.

---

# Database Engine

기본

* SQLite

향후 지원

* PostgreSQL

Database 접근은 Repository Interface를 통해 수행한다.

---

# Database Architecture

```text
Application

↓

Service

↓

Repository Interface

↓

SQLite Repository

↓

SQLite
```

Application은 SQL을 직접 실행하지 않는다.

---

# Database File

```
data/

    kats.db
```

로그와 데이터베이스는 분리한다.

---

# Table List

```
accounts

positions

orders

fills

watchlists

strategies

market_cache

settings

system_state

logs

events
```

---

# accounts

계좌 정보

| Column       | Type     | Description |
| ------------ | -------- | ----------- |
| id           | INTEGER  | PK          |
| account_no   | TEXT     | 계좌번호        |
| account_name | TEXT     | 계좌명         |
| broker       | TEXT     | 증권사         |
| account_type | TEXT     | 모의/실전       |
| created_at   | DATETIME | 생성일         |
| updated_at   | DATETIME | 수정일         |

---

# positions

보유 종목

| Column             | Type     |
| ------------------ | -------- |
| id                 | INTEGER  |
| account_id         | INTEGER  |
| symbol             | TEXT     |
| name               | TEXT     |
| quantity           | INTEGER  |
| available_quantity | INTEGER  |
| average_price      | REAL     |
| current_price      | REAL     |
| evaluation_amount  | REAL     |
| profit             | REAL     |
| profit_rate        | REAL     |
| updated_at         | DATETIME |

---

# orders

주문 정보

| Column          | Type     |
| --------------- | -------- |
| id              | INTEGER  |
| order_no        | TEXT     |
| account_id      | INTEGER  |
| symbol          | TEXT     |
| order_type      | TEXT     |
| side            | TEXT     |
| price           | REAL     |
| quantity        | INTEGER  |
| filled_quantity | INTEGER  |
| status          | TEXT     |
| requested_at    | DATETIME |
| updated_at      | DATETIME |

---

# fills

체결 내역

| Column      | Type     |
| ----------- | -------- |
| id          | INTEGER  |
| order_id    | INTEGER  |
| fill_no     | TEXT     |
| symbol      | TEXT     |
| quantity    | INTEGER  |
| price       | REAL     |
| fee         | REAL     |
| tax         | REAL     |
| executed_at | DATETIME |

---

# watchlists

관심종목

| Column     | Type     |
| ---------- | -------- |
| id         | INTEGER  |
| symbol     | TEXT     |
| name       | TEXT     |
| market     | TEXT     |
| memo       | TEXT     |
| created_at | DATETIME |

---

# strategies

전략 설정

| Column        | Type     |
| ------------- | -------- |
| id            | INTEGER  |
| strategy_name | TEXT     |
| class_name    | TEXT     |
| enabled       | INTEGER  |
| parameters    | TEXT     |
| symbols       | TEXT     |
| created_at    | DATETIME |
| updated_at    | DATETIME |

parameters는 JSON 문자열로 저장한다.

---

# market_cache

최근 시세 캐시

| Column        | Type     |
| ------------- | -------- |
| symbol        | TEXT     |
| current_price | REAL     |
| open_price    | REAL     |
| high_price    | REAL     |
| low_price     | REAL     |
| volume        | INTEGER  |
| updated_at    | DATETIME |

---

# settings

프로그램 설정

| Column     | Type     |
| ---------- | -------- |
| key        | TEXT     |
| value      | TEXT     |
| updated_at | DATETIME |

예시

* theme
* language
* auto_login
* broker
* account

---

# system_state

시스템 상태

| Column     | Type     |
| ---------- | -------- |
| key        | TEXT     |
| value      | TEXT     |
| updated_at | DATETIME |

예시

* websocket_status
* last_token_refresh
* last_login
* last_shutdown

---

# logs

로그 인덱스

| Column     | Type     |
| ---------- | -------- |
| id         | INTEGER  |
| level      | TEXT     |
| logger     | TEXT     |
| message    | TEXT     |
| created_at | DATETIME |

상세 로그는 파일에 저장하며 DB에는 검색용 인덱스만 저장한다.

---

# events

EventBus 기록

| Column     | Type     |
| ---------- | -------- |
| id         | INTEGER  |
| event_name | TEXT     |
| payload    | TEXT     |
| created_at | DATETIME |

Debug 모드에서만 저장한다.

---

# Entity Relationship

```
Account

│

├── Position

├── Order

│      │

│      └── Fill

│

└── Strategy
```

---

# Repository Structure

```
repository/

    interfaces/

        account_repository.py

        order_repository.py

        fill_repository.py

        strategy_repository.py

        settings_repository.py

        market_repository.py

    sqlite/

        sqlite_account_repository.py

        sqlite_order_repository.py

        sqlite_fill_repository.py

        sqlite_strategy_repository.py
```

---

# Repository Interface

모든 Repository는 다음 메서드를 구현한다.

```
add()

update()

delete()

find_by_id()

find_all()

exists()
```

필요 시 도메인 전용 조회 메서드를 추가한다.

---

# Transaction Policy

Transaction은 Service에서 관리한다.

Repository는 Commit을 수행하지 않는다.

예시

```
OrderService

↓

begin()

↓

OrderRepository

↓

PositionRepository

↓

commit()
```

---

# Index Policy

Index를 생성한다.

```
orders(order_no)

orders(symbol)

positions(symbol)

fills(order_id)

watchlists(symbol)

strategies(strategy_name)
```

---

# Foreign Key

SQLite Foreign Key를 활성화한다.

```
PRAGMA foreign_keys = ON;
```

---

# Migration

Schema 변경은 Migration으로 관리한다.

```
database/

    migrations/

        001_initial.py

        002_strategy.py

        003_event.py
```

기존 데이터를 삭제하지 않는다.

---

# Backup Policy

자동 백업

```
data/

    backup/

        kats_YYYYMMDD.db
```

프로그램 종료 시 백업 여부를 설정으로 제어한다.

---

# Cache Policy

실시간 시세는 DB보다 Memory Cache를 우선 사용한다.

```
REST

↓

Memory Cache

↓

SQLite

↓

KIS API
```

TTL이 만료되면 API를 호출한다.

---

# Naming Rules

Table

복수형

예시

```
orders

positions

fills
```

Primary Key

```
id
```

Foreign Key

```
account_id

order_id
```

Timestamp

```
created_at

updated_at

executed_at
```

---

# Data Integrity

필수 정책

* Foreign Key 활성화
* Unique 제약조건 사용
* NOT NULL 적극 사용
* CHECK 제약조건 적용
* Transaction 보장

---

# Database Validation Checklist

모든 구현은 아래 조건을 만족해야 한다.

* Repository Pattern 준수
* SQL 직접 호출 없음
* Transaction 적용
* Foreign Key 활성화
* Index 생성
* Migration 지원
* Memory Cache 연동
* 테스트 데이터 분리
* Mock Database 지원
* PostgreSQL 전환 가능 구조 유지

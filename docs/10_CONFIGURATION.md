# 10_CONFIGURATION.md

# KATS Configuration Management Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 모든 설정(Configuration) 관리 정책을 정의한다.

프로그램에서 사용하는 모든 설정은 Config Layer를 통해 접근하며, 설정값을 직접 하드코딩하지 않는다.

---

# Architecture

```text
Application

↓

Config Service

↓

Config Manager

↓

Environment Loader

↓

Settings Repository

↓

.env / settings.json / Database
```

---

# 설계 원칙

Configuration은 다음 원칙을 따른다.

* Single Source of Truth
* Immutable Runtime Configuration
* Type Safe
* Validation 지원
* 환경별 설정 분리
* Hot Reload 지원(선택)

---

# Directory Structure

```text
config/

    default.json

    development.json

    production.json

    simulation.json

    logging.json

    strategy.json

.env

app/

    config/

        config_manager.py

        config_loader.py

        config_validator.py

        config_models.py

        config_service.py
```

---

# Configuration Source Priority

설정 우선순위

```text
Environment Variable

↓

.env

↓

JSON File

↓

Default Value
```

항상 상위 우선순위가 적용된다.

---

# Configuration Categories

```text
Application

Broker

Authentication

Database

Logging

Strategy

Backtest

Market

Order

Risk

Notification

UI

System
```

---

# Application Configuration

```text
Application

├── Name

├── Version

├── Language

├── Theme

├── Debug

└── Timezone
```

---

# Broker Configuration

```text
Broker

├── Broker Type

├── Base URL

├── WebSocket URL

├── Timeout

├── Retry

└── Rate Limit
```

---

# Authentication Configuration

```text
Authentication

├── App Key

├── App Secret

├── Token Path

├── Auto Refresh

├── Refresh Margin

└── Approval Cache
```

민감정보는 Environment Variable 또는 .env에서만 관리한다.

---

# Database Configuration

```text
Database

├── Engine

├── Database Path

├── Backup Path

├── Migration

├── Cache

└── Pool Size
```

---

# Logging Configuration

```text
Logging

├── Level

├── Rotation

├── Max File Size

├── Backup Count

├── Console Output

└── File Output
```

---

# Strategy Configuration

```text
Strategy

├── Auto Load

├── Plugin Path

├── Scan Interval

├── Max Strategy Count

└── Auto Start
```

---

# Risk Configuration

```text
Risk

├── Daily Loss Limit

├── Position Limit

├── Max Quantity

├── Max Order Amount

├── Duplicate Order Block

└── Emergency Stop
```

---

# Order Configuration

```text
Order

├── Default Order Type

├── Retry

├── Timeout

├── Partial Fill

└── Auto Cancel
```

---

# Market Configuration

```text
Market

├── Cache TTL

├── Tick Buffer

├── Candle Buffer

├── Refresh Interval

└── Timezone
```

---

# Notification Configuration

```text
Notification

├── Enable Telegram

├── Enable Discord

├── Enable Email

├── Enable Slack

└── Sound
```

---

# UI Configuration

```text
UI

├── Theme

├── Font

├── Window Size

├── Layout

├── Chart Style

└── Language
```

---

# Config Manager

ConfigManager는 Singleton으로 생성한다.

책임

* Load
* Save
* Validate
* Reload
* Get
* Set

---

# Config Service

Application은 ConfigManager를 직접 호출하지 않는다.

```text
Application

↓

ConfigService

↓

ConfigManager
```

---

# Config Model

모든 설정은 Pydantic Model로 관리한다.

예시

```python
class DatabaseConfig(BaseModel):
    engine: str
    database_path: Path
    backup_path: Path
```

---

# Validation

모든 설정은 로딩 시 검증한다.

검증 예시

* Path 존재 여부
* Port 범위
* Timeout 범위
* URL 형식
* 파일 권한

---

# Environment Variable

민감정보

```text
KIS_APP_KEY

KIS_APP_SECRET

KIS_ACCOUNT_NO

KATS_ENV
```

JSON에 저장하지 않는다.

---

# Default Configuration

기본값은

```text
config/default.json
```

에서 관리한다.

---

# Environment

지원 환경

```text
development

simulation

production
```

실행 시 환경을 선택한다.

---

# Runtime Configuration

런타임 변경 가능한 항목

* Theme
* Logging Level
* Notification
* Cache TTL

재시작이 필요한 항목

* Database
* Broker
* Language

---

# Hot Reload

지원 대상

* Logging
* Theme
* Notification
* Strategy

지원하지 않는 대상

* Database
* Broker
* Authentication

---

# Save Policy

사용자 설정은

```text
data/

    settings.json
```

에 저장한다.

프로그램 기본 설정은 변경하지 않는다.

---

# Backup

설정 변경 전

자동 백업

```text
data/

    backup/

        settings_YYYYMMDD_HHMMSS.json
```

---

# Error Handling

설정 오류

```text
Invalid Config

↓

Validation Error

↓

Logger

↓

Default Value

↓

Continue
```

치명적인 설정 오류는 프로그램 시작을 중단한다.

---

# Thread Safety

ConfigManager는 Thread Safe 해야 한다.

동시 접근 시 Lock을 사용한다.

---

# Testing

Unit Test

* Load
* Save
* Reload
* Validation
* Environment
* Default Value
* Backup

Integration Test

* Environment 변경
* Config Reload
* Runtime Update

---

# Performance Goals

초기 설정 로드

100ms 이하

설정 조회

1ms 이하

Reload

200ms 이하

---

# Validation Checklist

* Singleton ConfigManager
* ConfigService 사용
* Pydantic Validation
* Environment 지원
* Hot Reload 지원
* Thread Safe
* 민감정보 분리
* Backup 지원
* JSON 직접 접근 금지
* Unit Test 작성
* Integration Test 작성
* 문서와 구현 일치

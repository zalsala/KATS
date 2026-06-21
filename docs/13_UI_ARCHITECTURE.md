# 13_UI_ARCHITECTURE.md

# KATS UI Architecture Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 GUI 아키텍처를 정의한다.

UI는 Presentation Layer이며 비즈니스 로직을 포함하지 않는다.

모든 데이터는 Service와 EventBus를 통해 전달된다.

---

# Framework

GUI

* PySide6

Pattern

* MVVM
* Event Driven

---

# Architecture

```text
User

↓

View

↓

ViewModel

↓

Controller

↓

Service

↓

EventBus

↓

ViewModel

↓

View
```

---

# UI Design Principles

UI는

* 표시
* 입력
* 이벤트 전달

만 수행한다.

금지

* SQL
* REST API
* WebSocket
* Repository
* Business Logic

---

# Directory Structure

```text
app/

    ui/

        windows/

        dialogs/

        views/

        viewmodels/

        widgets/

        charts/

        models/

        themes/

        resources/
```

---

# Main Window

```text
MainWindow

├── Menu Bar

├── Tool Bar

├── Navigation

├── Workspace

├── Status Bar

└── Notification Area
```

---

# Main Navigation

```text
Dashboard

Market

Watchlist

Order

Portfolio

Strategy

Backtest

Logs

Settings
```

---

# Dashboard

표시

* 계좌 현황
* 총 자산
* 평가 손익
* 금일 손익
* 실행 중 전략
* 연결 상태
* CPU
* Memory

자동 갱신

---

# Market View

구성

* 종목 검색
* 현재가
* 호가
* 체결
* 차트
* 거래량
* 관심종목 추가

---

# Order View

구성

* 매수
* 매도
* 정정
* 취소
* 주문내역
* 미체결

---

# Portfolio View

구성

* 보유종목
* 평가금액
* 수익률
* 실현손익
* 종목별 손익

---

# Strategy View

구성

* 전략 목록
* 실행 상태
* 설정
* 로그
* 시작
* 중지
* 일시정지

---

# Backtest View

구성

* 전략 선택
* 기간 선택
* 종목 선택
* 결과
* 그래프
* 통계

---

# Log View

구성

* API
* Order
* Strategy
* System
* Database
* Error

검색 지원

---

# Settings View

구성

* Broker
* Account
* Theme
* Language
* Notification
* Logging
* Database
* Backup

---

# Window Hierarchy

```text
MainWindow

├── DashboardView

├── MarketView

├── OrderView

├── PortfolioView

├── StrategyView

├── BacktestView

├── LogView

└── SettingsView
```

---

# ViewModel

모든 View는 하나의 ViewModel을 가진다.

```text
MarketView

↓

MarketViewModel

↓

MarketService
```

---

# Widget Rules

Widget는 재사용 가능해야 한다.

공통 Widget

```text
PriceLabel

OrderBookWidget

ChartWidget

PositionTable

OrderTable

StrategyTable

LogViewer

StatusIndicator
```

---

# Dialog

```text
LoginDialog

OrderDialog

StrategyDialog

SettingsDialog

AboutDialog

ConfirmationDialog
```

---

# Theme

지원

```text
Light

Dark
```

ThemeManager를 통해 변경한다.

---

# Chart

Chart Engine

* pyqtgraph

지원

* Candle
* Volume
* MA
* EMA
* RSI
* MACD
* Bollinger

---

# Status Bar

표시

* Broker
* Login
* WebSocket
* API Delay
* CPU
* Memory
* Version

---

# Notification

표시

* 주문 완료
* 주문 실패
* 전략 시작
* 전략 종료
* 연결 종료
* 오류 발생

---

# UI Update

UI는 Event를 통해 갱신한다.

```text
PriceUpdatedEvent

↓

ViewModel

↓

View Refresh
```

---

# Thread Rule

GUI Thread는

* Widget Update

만 수행한다.

Worker Thread

* REST
* Database
* Strategy
* Logging

---

# Loading

모든 장시간 작업은 Loading Indicator를 표시한다.

UI Block 금지

---

# Error Display

사용자에게

* 이해 가능한 메시지

를 표시한다.

Stack Trace는 표시하지 않는다.

---

# Keyboard Shortcut

```text
F1

Help

F5

Refresh

Ctrl+B

Buy

Ctrl+S

Sell

Ctrl+L

Log

Ctrl+Q

Exit
```

---

# Responsive Rule

최소 해상도

```text
1920 × 1080
```

권장

```text
2560 × 1440
```

DPI Scaling 지원

---

# Accessibility

지원

* Font Size
* Color Theme
* Keyboard Navigation

---

# UI State

```text
Loading

↓

Ready

↓

Updating

↓

Error

↓

Ready
```

---

# Validation

입력 검증

* 숫자
* 가격
* 수량
* 날짜
* 종목코드

Controller 호출 전 검증한다.

---

# Performance

UI 갱신

30 FPS 이상

차트

60 FPS 목표

실시간 Tick 처리

지연 100ms 이하

---

# Testing

Unit Test

* ViewModel
* Controller
* Validation

UI Test

* Navigation
* Dialog
* Theme
* Chart
* Order Flow

---

# Validation Checklist

* MVVM 구조 적용
* UI와 Business Logic 분리
* EventBus 사용
* Thread 분리
* 재사용 Widget 구성
* Theme 지원
* Chart 지원
* ViewModel 사용
* Controller 사용
* Unit Test 작성
* UI Test 작성
* 문서와 구현 일치

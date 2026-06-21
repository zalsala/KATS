# 00_PROJECT.md

# KATS (Korea Investment Auto Trading System)

Version: 1.0.0

Status: Draft

---

# 프로젝트 비전

KATS는 한국투자증권 OpenAPI를 기반으로 구축하는 상용 수준의 자동매매 플랫폼이다.

본 프로젝트의 목표는 단순한 API 예제가 아니라 다음 요구사항을 만족하는 완성도 높은 트레이딩 플랫폼을 개발하는 것이다.

* 실전 운용 가능한 구조
* 유지보수가 쉬운 구조
* 확장 가능한 구조
* AI(Cursor)가 지속적으로 개발 가능한 구조
* 테스트 가능한 구조
* 장애 복구가 가능한 구조

---

# 프로젝트 목표

다음 기능을 제공한다.

## 거래

* 국내주식
* 미국주식
* 모의투자
* 실전투자

---

## 시세

* 현재가
* 호가
* 체결
* 분봉
* 일봉
* 실시간 시세(WebSocket)

---

## 주문

* 지정가
* 시장가
* 조건부 주문
* 정정
* 취소

---

## 계좌

* 잔고조회
* 예수금조회
* 주문가능금액
* 체결내역
* 손익조회

---

## 자동매매

* 전략 실행
* 전략 중지
* 다중 전략
* 전략 스케줄링
* 종목별 전략 적용

---

## 백테스트

* CSV 기반
* DB 기반
* 전략별 비교
* 기간별 성능 분석
* 거래 통계

---

## 리스크 관리

* 최대 손실 제한
* 종목당 투자 비율 제한
* 계좌 손실 제한
* 자동 손절
* 자동 익절
* 트레일링 스탑
* 중복 주문 방지

---

## 사용자 인터페이스

* 관심종목
* 차트
* 주문창
* 계좌현황
* 로그창
* 전략관리
* 설정

---

# 개발 원칙

모든 코드는 아래 원칙을 따른다.

* Clean Architecture
* SOLID
* DRY
* KISS
* Dependency Injection
* Repository Pattern
* Event Driven
* Service Layer
* Domain Driven Design(부분 적용)

---

# 지원 운영체제

* Windows 11
* Windows 10

향후 지원 예정

* macOS
* Linux

---

# 개발 언어

Python 3.12 이상

---

# 사용 라이브러리

GUI

* PySide6

Database

* SQLite

Data

* pandas
* numpy

Chart

* pyqtgraph

HTTP

* httpx

WebSocket

* websockets

Validation

* pydantic

Environment

* python-dotenv

Logging

* logging

Testing

* pytest

Formatting

* ruff
* black
* mypy

---

# 아키텍처

Application

↓

Controller

↓

Service

↓

Repository

↓

Broker

↓

KIS OpenAPI

모든 외부 API는 Broker 계층을 통해서만 접근한다.

GUI는 API를 직접 호출하지 않는다.

---

# 프로젝트 구조

KATS/

app/

config/

core/

domain/

broker/

repository/

service/

strategy/

backtest/

database/

events/

gui/

widgets/

resources/

tests/

docs/

logs/

scripts/

main.py

---

# 개발 범위

포함

* 자동매매
* 실시간 시세
* 주문
* 계좌
* 전략
* 백테스트
* 로그
* 설정
* 데이터 저장

제외

* HTS 기능 전체 구현
* 뉴스 크롤링
* 해외 데이터 공급사 연동
* 머신러닝 자동 생성 전략
* 모바일 앱

---

# 성능 목표

프로그램 시작

3초 이내

메모리

500MB 이하

평균 CPU

10% 이하

실시간 데이터 지연

1초 이하

예외 발생 후 자동 복구

30초 이내

---

# 품질 목표

Unit Test Coverage

80% 이상

Lint

100% 통과

Type Hint

100%

Public Method

Docstring 필수

모든 예외

로그 기록

---

# 개발 규칙

금지 사항

* print()
* 전역 변수
* 하드코딩
* 순환 참조
* SQL 직접 호출
* UI에서 API 호출
* UI에서 Database 접근

필수 사항

* Logger 사용
* Type Hint
* Docstring
* Exception 처리
* Unit Test
* Config 사용

---

# 프로젝트 철학

모든 기능은 독립적으로 교체 가능해야 한다.

Broker는 교체 가능해야 한다.

Strategy는 플러그인 방식이어야 한다.

Database는 Repository를 통해 접근한다.

UI는 EventBus만 사용한다.

Service는 Domain을 직접 수정하지 않는다.

---

# Broker 추상화

지원 예정

Broker

├── KISBroker

├── KiwoomBroker

├── EBestBroker

├── MiraeBroker

├── BinanceBroker

└── BybitBroker

현재 구현 대상은 KISBroker이다.

---

# 전략 구조

BaseStrategy

├── MovingAverageStrategy

├── RSIStrategy

├── MACDStrategy

├── BollingerStrategy

├── BreakoutStrategy

├── VolumeStrategy

└── CustomStrategy

모든 전략은 BaseStrategy를 상속한다.

---

# 이벤트 구조

MarketDataReceived

↓

IndicatorCalculated

↓

SignalGenerated

↓

RiskChecked

↓

OrderRequested

↓

OrderSubmitted

↓

OrderExecuted

↓

PositionUpdated

↓

PortfolioUpdated

↓

UIUpdated

---

# 저장 데이터

* 계좌
* 주문
* 체결
* 포지션
* 관심종목
* 전략
* 설정
* 로그
* 시스템 상태

---

# 로그 정책

분리 저장

api.log

order.log

strategy.log

system.log

database.log

websocket.log

error.log

---

# 테스트 정책

모든 모듈은 다음 테스트를 작성한다.

* Unit Test
* Integration Test
* Mock Test

회귀 테스트가 가능해야 한다.

---

# 완료 기준

프로젝트는 다음 조건을 만족해야 완료로 간주한다.

* 전체 테스트 통과
* 린트 오류 없음
* 타입 검사 통과
* 모의투자 자동매매 정상 동작
* 실전 계좌 수동 주문 정상 동작
* 실시간 시세 수신 정상
* 장애 발생 시 자동 복구 가능
* 사용자 매뉴얼 작성 완료
* 개발 문서 최신 상태 유지

---

# 문서 관리

모든 설계 변경은 docs 디렉터리에서 관리한다.

Cursor는 구현 전에 관련 문서를 확인하고, 구현 후 문서와 코드의 일치 여부를 검증한다.

본 프로젝트의 모든 구현은 문서 우선(Document First) 원칙을 따른다.

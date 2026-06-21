# 23_KIS_OFFICIAL_GUIDE.md

# KIS OpenAPI 공식 가이드 정렬 (Official Repository Alignment)

Version: 1.0.0

Reference: [koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api)

---

# 목적

본 문서는 한국투자증권 **공식 Open API 샘플 저장소**의 제작 지침·구조·관례를 KATS에 어떻게 적용할지 정의한다.

KATS는 공식 샘플 코드를 **그대로 복사하지 않고**, Clean Architecture 내 Broker 계층에서 **동등한 동작**을 구현한다.

**Document First 원칙:** Broker·Auth 구현 전 본 문서와 `docs/22_API_INTEGRATION.md`를 반드시 확인한다.

---

# 공식 저장소 개요

| 항목 | 내용 |
|------|------|
| 저장소 | `koreainvestment/open-trading-api` |
| 포털 | [KIS Developers](https://apiportal.koreainvestment.com/) |
| Python | 3.11+ (KATS는 3.12) |
| 패키지 | uv 권장 (KATS는 pip/pyproject.toml) |
| 설정 파일 | `kis_devlp.yaml` → KATS는 `.env` + `config/*.json` |

---

# 공식 문서 목록 (KATS 참조 우선순위)

| 순위 | 공식 경로 | KATS 대응 |
|------|-----------|-----------|
| 1 | `README.md` | 본 문서 §환경·인증·API 카테고리 |
| 2 | `docs/convention.md` | `docs/03_CODING_RULE.md`, `docs/20_CODING_STANDARD.md` |
| 3 | `kis_devlp.yaml` | `config/default.json`, `.env`, `SecretManager` |
| 4 | `examples_user/kis_auth.py` | `app/broker/kis/auth/` (Phase 04~05) |
| 5 | `examples_user/auth/auth_functions.py` | OAuth·Approval Key API 시그니처 |
| 6 | `examples_user/domestic_stock/` | `app/broker/kis/rest/market_client.py` 등 |
| 7 | `strategy_builder/` `.kis.yaml` | `app/strategy/` (Phase 10, 참고용) |

---

# 유의사항 (공식 README)

다음은 공식 저장소가 명시한 **법적·운영적 유의사항**이다. KATS도 동일하게 준수한다.

* 샘플 코드는 **참고용**이며, 무단 업데이트될 수 있다.
* 샘플 기반 프로그램으로 인한 **손해에 대해 증권사는 책임지지 않는다.**
* API Key·Secret·Token·계좌번호는 **코드·로그·Git에 포함하지 않는다.**

---

# 환경·도메인 (kis_devlp.yaml 기준)

## REST Base URL

| KIS 키 | 용도 | URL |
|--------|------|-----|
| `prod` | 실전 REST | `https://openapi.koreainvestment.com:9443` |
| `vps` | 모의 REST | `https://openapivts.koreainvestment.com:29443` |

## WebSocket URL

| KIS 키 | 용도 | URL |
|--------|------|-----|
| `ops` | 실전 WebSocket | `ws://ops.koreainvestment.com:21000` |
| `vops` | 모의 WebSocket | `ws://ops.koreainvestment.com:31000` |

## KATS 매핑

| KIS `svr` | KATS `environment` | KATS `account_type` | REST | WebSocket |
|-----------|-------------------|---------------------|------|-----------|
| `vps` | `development`, `simulation` | `mock` | VTS URL | vops (31000) |
| `prod` | `production` | `real` | prod URL | ops (21000) |

```python
# 공식 샘플 (kis_auth.py)
ka.auth(svr="prod", product="01")   # 실전 위탁계좌
ka.auth(svr="vps", product="01")  # 모의투자
```

KATS Broker 구현 시 **동일한 svr/product 조합**을 사용한다.

---

# 인증 (Authentication)

## OAuth Access Token

| 항목 | 값 |
|------|-----|
| Endpoint | `POST {base_url}/oauth2/tokenP` |
| Body | `grant_type=client_credentials`, `appkey`, `appsecret` |
| 유효기간 | 1일 (6시간 이내 재발급 시 동일 토큰) |
| 재발급 | 1분당 1회 제한 (공식 문제해결 가이드) |

## WebSocket Approval Key

| 항목 | 값 |
|------|-----|
| Endpoint | `POST {base_url}/oauth2/Approval` |
| Body | `grant_type`, `appkey`, `secretkey`, (optional) `token` |
| 선행 조건 | REST Access Token 발급 후 호출 |

## HashKey (주문)

| 항목 | 값 |
|------|-----|
| Endpoint | `POST {base_url}/uapi/hashkey` |
| 용도 | 주문 요청 Body 변조 방지 (Header `hashkey`) |

## KATS Auth 모듈 매핑 (Phase 04)

| 공식 (`kis_auth.py`) | KATS |
|----------------------|------|
| `auth()` | `TokenManager.issue()` |
| `auth_ws()` | `ApprovalKeyManager.issue()` |
| `read_token()` / `save_token()` | `TokenStorage` |
| `reAuth()` | `TokenManager.refresh()` |
| `set_order_hash_key()` | `HashKeyManager.generate()` |
| `changeTREnv()` | `ConfigManager` + `AppSettings` |
| `getTREnv()` | `KisTradingEnvironment` (DTO) |

## REST 공통 Header (공식)

```
Content-Type: application/json
Accept: text/plain
charset: UTF-8
User-Agent: {my_agent}
authorization: Bearer {access_token}
appkey: {app_key}
appsecret: {app_secret}
tr_id: {transaction_id}
custtype: P
```

KATS `HeaderBuilder`는 위 필드를 **하드코딩 없이** Config·SecretManager에서 조립한다.

---

# 계좌·설정 (kis_devlp.yaml)

## 필수 설정 항목

| YAML 키 | 설명 | KATS 환경변수 / Config |
|---------|------|------------------------|
| `my_app` / `paper_app` | 실전/모의 App Key | `KIS_APP_KEY` |
| `my_sec` / `paper_sec` | App Secret | `KIS_APP_SECRET` |
| `my_htsid` | HTS ID (체결통보·WebSocket) | `KIS_HTS_ID` |
| `my_acct_stock` | 증권계좌 앞 8자리 | `KIS_ACCOUNT_NO` (8자리) |
| `my_paper_stock` | 모의 증권계좌 8자리 | `KIS_PAPER_ACCOUNT_NO` |
| `my_prod` | 계좌상품코드 2자리 | `KIS_ACCOUNT_PRODUCT` |

## 계좌상품코드 (`my_prod`)

| 코드 | 의미 |
|------|------|
| `01` | 종합계좌 (위탁) — **기본값** |
| `03` | 국내선물옵션 |
| `08` | 해외선물옵션 |
| `22` | 개인연금 |
| `29` | 퇴직연금 |

KATS 주문 API 호출 시 **8자리 계좌 + 2자리 product**를 분리하여 전달한다.

---

# API 카테고리 (공식 폴더 구조)

공식 `examples_user/` / `examples_llm/` 카테고리와 KATS Broker 모듈 매핑:

| 공식 폴더 | 설명 | KATS Broker Client |
|-----------|------|-------------------|
| `auth` | 토큰·접속키 | `auth_client.py` |
| `domestic_stock` | 국내주식 | `market_client.py`, `order_client.py`, `account_client.py` |
| `overseas_stock` | 해외주식 | Phase 2+ |
| `domestic_bond` | 국내채권 | 제외 (00_PROJECT) |
| `domestic_futureoption` | 국내선물옵션 | 제외 |
| `elw` / `etfetn` | ELW / ETF·ETN | 제외 |

## REST URL 패턴 (공식 convention)

```
/uapi/{category}/v1/{sub}/{api-name}
```

예: `/uapi/domestic-stock/v1/quotations/inquire-price`

KATS Parser/Mapper는 **tr_id**, **rt_cd**, **msg_cd**, **msg1** 응답 필드를 표준 처리한다.

---

# Rate Limit (공식 kis_auth.py)

| 환경 | `_smartSleep` | KATS 상수 |
|------|---------------|-----------|
| 실전 (`prod`) | 0.05초 | `KIS_RATE_LIMIT_SLEEP_PROD` |
| 모의 (`vps`) | 0.5초 | `KIS_RATE_LIMIT_SLEEP_VPS` |

모의투자 계좌는 REST 호출 제한이 낮다. 연속 호출 시 `EGW00201` (초당 거래건수 초과) 발생 가능.

KATS `RateLimiter`는 위 값을 **최소 간격**으로 사용한다.

---

# API 응답 처리 (공식 APIResp)

공식 샘플의 성공/실패 판정:

```python
# 성공: body.rt_cd == "0"
# 실패: msg_cd, msg1 로그 기록
```

KATS Broker Exception Mapping:

| 공식 | KATS Exception |
|------|----------------|
| `rt_cd != "0"` | `BrokerApiError` |
| HTTP 401 | `AuthenticationError` |
| HTTP 429 / EGW00201 | `RateLimitError` |

---

# 코딩 컨벤션 (docs/convention.md → KATS)

| 공식 규칙 | KATS 적용 |
|-----------|-----------|
| snake_case 함수/변수 | `03_CODING_RULE.md` 준수 |
| PascalCase 클래스 | 동일 |
| UPPER_SNAKE_CASE 상수 | `app/core/constants.py` |
| Wildcard import 금지 | Ruff enforced |
| Type Hint 필수 | mypy strict |
| Google Docstring | 필수 |
| 설정 코드 분리 | ConfigManager + SecretManager |
| logging 사용 | LoggerService (STEP-03) |
| 구체적 except + logging | Exception 계층 사용 |

## 공식 파일 명명 (Broker 내부 참고)

| 공식 | KATS Broker |
|------|-------------|
| `{api_name}.py` (한줄 호출) | `{api_name}_client.py` 또는 통합 Client 메서드 |
| `chk_{api_name}.py` | `tests/unit/broker/test_{api_name}.py` |
| `{category}_functions.py` | `{category}_client.py` |

KATS는 **통합 Client + Parser** 패턴을 사용하되, 공식 API 파라미터명(`fid_input_iscd` 등)은 Mapper에서 **그대로 유지**한다.

---

# WebSocket (공식)

## 호출 순서

```
ka.auth()        → REST Token
ka.auth_ws()     → Approval Key
ka.KISWebSocket  → Subscribe
```

## KATS WebSocket Client 책임

* 연결·재연결 (`No close frame received` → HTS ID 확인)
* Ping/Pong·Heartbeat
* Subscribe/Unsubscribe 목록 유지 (재접속 시 복구)
* Message Parser → EventBus (Phase 02 이후)

---

# 전략·백테스트 (공식 strategy_builder / backtester)

KATS Phase 10~11 구현 시 참고:

| 공식 | KATS |
|------|------|
| `.kis.yaml` 전략 포맷 | Strategy YAML import (선택) |
| 10개 프리셋 전략 | `plugins/strategies/` |
| BUY/SELL/HOLD Signal | `SignalEngine` |
| Backtester (Lean) | `app/backtest/` Virtual Broker |

KATS는 Lean/Docker 의존 없이 **자체 Backtest Engine**을 사용하되, 시그널 의미(BUY/SELL/HOLD)는 공식과 동일하게 유지한다.

---

# KATS 구현 체크리스트 (Broker Phase)

Broker 구현 시 아래 항목을 **전부** 만족해야 한다.

* [ ] `prod` / `vps` 환경 전환 지원
* [ ] REST/WebSocket URL 공식 도메인 사용
* [ ] OAuth `tokenP` + Approval Key 순서 준수
* [ ] HashKey 주문 연동
* [ ] 계좌 8자리 + product 2자리 분리
* [ ] HTS ID 설정 (WebSocket)
* [ ] User-Agent Header 포함
* [ ] `rt_cd == "0"` 성공 판정
* [ ] Rate Limit (`smart_sleep` 동등)
* [ ] 민감정보 로그 마스킹 (STEP-03)
* [ ] Correlation ID 로그 추적 (STEP-03)
* [ ] API latency Performance Log (STEP-03)
* [ ] Unit Test + Mock (공식 `chk_*.py` 패턴)

---

# 문제 해결 (공식 README §5)

| 증상 | 원인 | KATS 대응 |
|------|------|-----------|
| 토큰 오류 | 만료 | `TokenManager.refresh()` |
| WebSocket 끊김 | HTS ID 오류 | Config 검증 + 로그 |
| EGW00201 | Rate Limit | `RateLimiter` + vps sleep |
| 설정 오류 | yaml 키/계좌 형식 | `ConfigValidator` |

---

# 문서 갱신 정책

* KIS 공식 저장소 **README/convention 변경** 시 본 문서를 먼저 갱신한다.
* Broker 구현 PR에는 **본 체크리스트** 준수 여부를 명시한다.
* 공식 샘플과 KATS 동작이 다를 경우, **차이와 사유**를 본 문서에 기록한다.

---

# Validation Checklist

* 공식 도메인 URL 일치
* prod/vps 환경 매핑 정의
* 인증 API 경로 정의
* 계좌/product/hts_id 설정 매핑
* Rate Limit 정책 반영
* API 카테고리·폴더 매핑
* convention.md 코딩 규칙 반영
* KATS Architecture Layer 유지
* SecretManager·LoggerService 연동
* 문서와 constants.py 일치

# VTS 검증 가이드

KATS v1.0에서 **한국투자증권 OpenAPI 모의투자(VTS)** 환경이 정상 동작하는지 단계별로 확인하는 절차입니다.

> **주의:** v1.0은 실계좌 자동매매를 지원 대상으로 하지 않습니다. 반드시 `KIS_ACCOUNT_TYPE=mock`(VTS)에서 먼저 검증하세요.

---

## 1. `.env` 설정 방법

### 1.1 파일 준비

프로젝트 루트에서 `.env.example`을 복사합니다.

```powershell
copy .env.example .env
```

`.env`는 **Git에 커밋하지 않습니다.** API 키·시크릿·계좌번호는 `.env`와 OS 환경 변수에서만 읽으며, `config/*.json`에는 저장하지 않습니다.

### 1.2 필수 항목

| 변수 | 설명 | VTS 권장값 |
|------|------|------------|
| `KATS_ENV` | 런타임 환경 | `simulation` |
| `KIS_APP_KEY` | KIS 앱 키 | 한국투자 OpenAPI에서 발급 |
| `KIS_APP_SECRET` | KIS 앱 시크릿 | 한국투자 OpenAPI에서 발급 |
| `KIS_ACCOUNT_NO` | 모의투자 계좌번호(8자리 CANO) | VTS HTS에서 확인 |
| `KIS_ACCOUNT_TYPE` | 계좌 모드 | `mock` (VTS) |
| `KIS_ACCOUNT_PRODUCT` | 계좌 상품코드 | `01` (기본값, HTS와 동일하게) |

### 1.3 예시

```env
KATS_ENV=simulation

KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret
KIS_ACCOUNT_NO=12345678
KIS_ACCOUNT_TYPE=mock
KIS_ACCOUNT_PRODUCT=01
```

### 1.4 확인 사항

- `KIS_ACCOUNT_TYPE`은 반드시 `mock`입니다. `real`이면 VTS 스크립트가 거부됩니다.
- `config/simulation.json`의 REST URL은 `https://openapivts.koreainvestment.com:29443` 입니다. `main.py --check`가 이 URL과 환경을 함께 검증합니다.
- `config/order.live_trading_enabled`는 `false`로 유지합니다. VTS 매수 테스트 스크립트도 이 값을 요구합니다.

---

## 2. 실행 순서

아래 순서를 **위에서 아래로** 진행합니다. 앞 단계가 실패하면 다음 단계로 넘어가지 마세요.

```text
1. .env 설정
2. python main.py --check          ← 설정·런타임 검증
3. python main.py --migrate        ← DB 마이그레이션
4. python scripts/test_auth_token.py
5. python scripts/test_current_price.py
6. python scripts/test_orderable_amount.py
7. python scripts/test_vts_buy_order.py   ← 유일한 주문 실행 단계 (YES 확인 필요)
8. python scripts/test_order_inquiry.py
```

**의존 관계 요약**

| 단계 | 선행 조건 |
|------|-----------|
| `--check` | `.env` 존재, simulation/VTS URL 일치 |
| `--migrate` | `--check` 통과 |
| 토큰 테스트 | 유효한 `KIS_APP_KEY` / `KIS_APP_SECRET` |
| 시세·주문가능·주문·조회 | 토큰 발급 가능 + (계좌 API는) `KIS_ACCOUNT_NO` |
| 매수 주문 | 위 전부 + 사용자 `YES` 입력 + **장중(영업일)** 권장 |

---

## 3. 각 스크립트 명령어

모든 명령은 **프로젝트 루트**에서 실행합니다.

### 3.1 환경 검증

```powershell
python main.py --check
```

**기대 출력 예**

```text
OK: environment=simulation
OK: account_type=mock
OK: live_trading_enabled=False
OK: database=data/database/kats.db
OK: dotenv=present
KATS environment check passed.
```

### 3.2 DB 마이그레이션

```powershell
python main.py --migrate
```

**기대 출력 예**

```text
Migrations applied: ['001_initial.sql']
```

(이미 적용된 경우 빈 목록이 나올 수 있습니다.)

### 3.3 Access Token 발급

```powershell
python scripts/test_auth_token.py
```

**기대 출력 예**

```text
APP_KEY source: env
APP_SECRET source: env
ACCOUNT_NO source: env
BASE_URL: openapivts...
ACCOUNT_TYPE: mock
Status: SUCCESS
Expires at: 2026-06-20 23:59:59 KST
```

토큰 문자열·계좌번호 원문은 출력되지 않습니다.

### 3.4 현재가 조회 (삼성전자 005930)

```powershell
python scripts/test_current_price.py
```

**기대 출력 예**

```text
rt_cd: 0
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
current_price: 70000
```

### 3.5 주문가능금액 조회

```powershell
python scripts/test_orderable_amount.py
```

**기대 출력 예**

```text
rt_cd: 0
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
orderable_amount: 10000000
```

### 3.6 VTS 모의 매수 주문 (1주, 지정가)

```powershell
python scripts/test_vts_buy_order.py
```

프롬프트가 표시됩니다.

```text
VTS 모의 매수 주문 1주를 실행합니다. 계속하려면 YES 입력
```

`YES`를 입력해야 주문이 전송됩니다. 현재가 − 100원 지정가로 1주 매수를 시도합니다.

**기대 출력 예**

```text
rt_cd: 0
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
order_number: 0000123456
```

### 3.7 주문·체결 조회 (당일)

```powershell
python scripts/test_order_inquiry.py
```

**기대 출력 예 (주문 없음)**

```text
rt_cd: 0
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
order_count: 0
```

**기대 출력 예 (주문 있음)**

```text
rt_cd: 0
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
order_count: 1
order_number: 0000123456
symbol: 005930
quantity: 0
status: pending
```

---

## 4. 성공 기준

| 명령 | 종료 코드 | 성공 조건 |
|------|-----------|-----------|
| `main.py --check` | `0` | `KATS environment check passed.` 출력 |
| `main.py --migrate` | `0` | 마이그레이션 오류 없음 |
| `test_auth_token.py` | `0` | `Status: SUCCESS`, 만료 시각 출력 |
| `test_current_price.py` | `0` | `rt_cd: 0`, `current_price`에 숫자 |
| `test_orderable_amount.py` | `0` | `rt_cd: 0`, `orderable_amount`에 숫자 |
| `test_vts_buy_order.py` | `0` | `rt_cd: 0`, `order_number` 비어 있지 않음 |
| `test_vts_buy_order.py` | `2` | 사용자가 `YES` 미입력 → 취소 (정상 취소) |
| `test_order_inquiry.py` | `0` | `rt_cd: 0` (주문 건수 0도 API 성공이면 OK) |

**KIS 공통 응답 코드**

- `rt_cd: 0` — API 호출 성공
- `rt_cd: 1` (또는 `0` 이외) — 오류. `msg_cd`, `msg1`을 확인

---

## 5. 자주 나오는 오류

### 설정·자격 증명

| 증상 | 원인 | 조치 |
|------|------|------|
| `KIS_APP_KEY and KIS_APP_SECRET are required` | `.env`에 키/시크릿 누락 | `.env` 값 입력 후 재실행 |
| `KIS_ACCOUNT_NO is required` | 계좌번호 누락 | VTS 계좌번호 8자리 입력 |
| `Expected environment=simulation` | `KATS_ENV` 불일치 | `KATS_ENV=simulation` 설정 |
| `Broker base URL is not the KIS VTS simulation endpoint` | 실서버 URL 사용 | `KATS_ENV=simulation` 및 `config/simulation.json` 확인 |
| `VTS mock account only` | `KIS_ACCOUNT_TYPE=real` | `mock`으로 변경 |
| `live_trading_enabled must remain false` | 실주문 플래그 켜짐 | `config`에서 `order.live_trading_enabled: false` 유지 |
| `CHECK FAILED` (`main.py --check`) | production URL·mock 계좌 조합 등 | 메시지에 따라 `.env` / `config` 수정 |

### 인증·네트워크

| 증상 | 원인 | 조치 |
|------|------|------|
| `Status: FAILED` (토큰) | 잘못된 앱키/시크릿, IP 미등록 | KIS 개발자센터에서 키·IP 허용 확인 |
| 타임아웃 / 연결 오류 | 방화벽, VPN, KIS 장애 | 네트워크 확인 후 재시도 |
| `Secret '...' found in JSON config` (로그) | JSON에 민감정보 잔존 | `config/*.json`·`data/settings.json`에서 키 제거, `.env`만 사용 |

### 주문 스크립트

| 증상 | 원인 | 조치 |
|------|------|------|
| `msg_cd: CANCELLED` / 종료 코드 `2` | `YES` 미입력 | 의도적 취소. 재실행 후 `YES` 입력 |
| `rt_cd: 1`, 주문 거부 메시지 | 잔고 부족, 가격 오류, 장외 | 잔고·가격·영업일 확인 (아래 6절) |
| `Current price is missing` | 시세 API 응답 이상 | `test_current_price.py` 먼저 통과 여부 확인 |

### JSON 설정 관련

민감정보(`app_key`, `app_secret`, `account_no`)는 **`.env`에만** 둡니다. `data/settings.json`에 예전 값이 남아 있어도 런타임은 `.env`를 우선하지만, 경고를 피하려면 해당 키를 삭제하세요.

---

## 6. 영업일이 아닐 때 나오는 오류

KIS VTS API는 **한국 주식시장 영업일·장 운영 시간**에 맞춰 동작합니다. 휴장일·주말·장 시작 전·장 마감 후에는 아래와 같은 현상이 **정상적으로** 발생할 수 있습니다.

### 6.1 흔한 증상

- `test_current_price.py`는 성공하지만 **주문·체결 관련 API**가 `rt_cd: 1`로 실패
- `msg1`에 **장운영시간**, **영업일**, **주문 가능 시간** 등과 관련된 문구
- 체결 조회에서 당일 주문은 보이지만 `quantity: 0`, `status: pending`만 유지 (장외 미체결)

### 6.2 영향 받는 단계

| 단계 | 휴장/장외 시 |
|------|----------------|
| `test_auth_token.py` | 대체로 **가능** (인증은 장과 무관) |
| `test_current_price.py` | **가능**한 경우가 많음 (전일 종가·기준가 반환) |
| `test_orderable_amount.py` | **실패할 수 있음** |
| `test_vts_buy_order.py` | **실패할 수 있음** |
| `test_order_inquiry.py` | API 성공(`rt_cd: 0`)이어도 `order_count: 0`일 수 있음 |

### 6.3 대응

1. **평일 09:00~15:30 KST**(정규장, 점심시간 포함 연속)에 다시 실행합니다.
2. 공휴일·대체공휴일은 [한국거래소 휴장일](https://www.krx.co.kr)을 확인합니다.
3. 장외에 인증·시세만 확인했다면, **주문·주문가능·체결 검증은 다음 영업일**에 이어서 진행합니다 (7절).

> VTS도 실제 시장 일정을 따릅니다. “API 키는 맞는데 주문만 안 된다”면 설정 문제보다 **영업일/장 시간**을 먼저 의심하세요.

---

## 7. 내일 주문 검증 순서

오늘 장중에 `test_vts_buy_order.py`까지 성공한 뒤, **다음 영업일**에 체결·조회 흐름을 마무리하는 권장 순서입니다.

### 7.1 전제

- 전일 VTS 모의 매수 주문이 `rt_cd: 0`으로 접수되었고 `order_number`를 기록해 두었습니다.
- `.env`와 `KATS_ENV=simulation`은 그대로 유지합니다.

### 7.2 다음 영업일 절차

```text
1. python main.py --check
2. python scripts/test_auth_token.py
3. python scripts/test_order_inquiry.py    ← 전일 주문·체결 반영 확인
```

필요 시 추가 확인:

```powershell
python scripts/test_current_price.py
python scripts/test_orderable_amount.py
```

### 7.3 `test_order_inquiry.py`에서 확인할 것

| 필드 | 기대 |
|------|------|
| `rt_cd` | `0` |
| `order_count` | `1` 이상 (당일 조회 범위에 주문이 있을 때) |
| `order_number` | 전일 접수 시 받은 번호와 일치 |
| `symbol` | `005930` (테스트 기본 종목) |
| `quantity` | 체결 시 `0` 초과 |
| `status` | 체결 시 `filled`, 미체결 시 `pending` |

당일 조회 스크립트는 **조회 실행일(KST) 당일** 범위를 사용합니다. 전일 주문을 보려면 영업일 당일 아침에 다시 조회하거나, 추후 날짜 파라미터 확장이 필요할 수 있습니다. 전일 접수 직후 같은 날 장중에 `test_order_inquiry.py`를 실행하면 `order_number`와 `pending` 상태까지 먼저 확인할 수 있습니다.

### 7.4 체결되지 않았을 때

- 지정가가 시장가보다 낮으면 미체결(`pending`)일 수 있습니다.
- 다음 영업일에도 미체결이면 VTS HTS에서 주문 상태를 확인하거나, 새 지정가로 재주문 테스트를 검토합니다 (본 가이드의 매수 스크립트는 1주·현재가−100원 기준).

---

## 참고

- 상세 설정 정책: [10_CONFIGURATION.md](10_CONFIGURATION.md)
- API 연동: [22_API_INTEGRATION.md](22_API_INTEGRATION.md)
- KIS 공식 정렬: [23_KIS_OFFICIAL_GUIDE.md](23_KIS_OFFICIAL_GUIDE.md)
- 프로젝트 개요·제한 사항: [README.md](../README.md)

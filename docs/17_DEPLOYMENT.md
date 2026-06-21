# 17_DEPLOYMENT.md

# KATS Deployment Specification

Version: 1.0.0

---

# 목적

본 문서는 KATS의 빌드, 배포, 설치, 업데이트 및 운영 환경을 정의한다.

개발 환경과 운영 환경을 명확히 분리하며, 누구나 동일한 절차로 프로그램을 설치하고 실행할 수 있어야 한다.

---

# Deployment Architecture

```text id="h5g2rk"
Source Code

↓

Build

↓

Package

↓

Release

↓

Installer

↓

User Environment
```

---

# 지원 운영체제

Primary

* Windows 11
* Windows 10

향후

* Linux
* macOS

---

# Python Version

지원

```text id="4r6puk"
Python 3.12
```

개발 및 운영 환경은 동일한 버전을 사용한다.

---

# Build Tool

사용

* PyInstaller

향후 지원

* Nuitka

---

# Directory Structure

```text id="i7vb2m"
release/

    KATS.exe

    config/

    resources/

    plugins/

    logs/

    data/

    README.txt
```

---

# Build Process

```text id="4zjzwd"
Source

↓

Unit Test

↓

Lint

↓

Type Check

↓

Build

↓

Package

↓

Release
```

---

# Build Commands

빌드 순서

```text id="j8m9cx"
ruff check

↓

black --check

↓

mypy

↓

pytest

↓

pyinstaller
```

---

# Installer

설치 항목

* 실행 파일
* 기본 설정
* Resource
* Plugin
* SQLite Database

---

# First Launch

최초 실행 시

```text id="bb5h5f"
Create Data Directory

↓

Create Database

↓

Create Log Directory

↓

Load Config

↓

Initialize Application
```

---

# Environment

지원

```text id="l2k5s9"
Development

Simulation

Production
```

환경별 설정을 분리한다.

---

# Configuration

배포 대상

```text id="2m5fqr"
config/

resources/

plugins/
```

민감정보는 포함하지 않는다.

---

# Environment Variables

필수

```text id="x2b5ar"
KIS_APP_KEY

KIS_APP_SECRET

KATS_ENV
```

운영 시 환경변수 또는 .env를 사용한다.

---

# Log Directory

```text id="2d8hxe"
logs/

    system.log

    api.log

    order.log

    strategy.log

    websocket.log

    error.log
```

---

# Data Directory

```text id="6wxr0d"
data/

    database/

    auth/

    backup/

    cache/

    export/

    settings/
```

---

# Update Policy

지원 방식

* 수동 업데이트
* 자동 업데이트(향후)

업데이트 시 사용자 데이터는 유지한다.

---

# Backup Policy

업데이트 전

자동 백업

```text id="op2d7q"
data/

backup/

YYYYMMDD_HHMMSS/
```

백업 실패 시 업데이트를 중단한다.

---

# Recovery

복구 절차

```text id="x17r6u"
Stop Application

↓

Restore Backup

↓

Restart
```

---

# Release Version

버전 형식

```text id="2x2n3v"
MAJOR.MINOR.PATCH

예)

1.0.0

1.1.0

1.1.1
```

---

# Release Package

포함

* 실행 파일
* 기본 Config
* Resource
* Plugin
* License
* README

제외

* API Key
* Access Token
* 사용자 데이터
* 로그

---

# CI/CD

자동 실행

```text id="krz6sj"
Git Push

↓

GitHub Actions

↓

Lint

↓

Test

↓

Build

↓

Artifact
```

---

# Quality Gate

배포 조건

* Ruff 통과
* Black 통과
* mypy 통과
* Unit Test 성공
* Integration Test 성공

---

# Rollback

지원

```text id="bt9j4v"
Current Release

↓

Failure

↓

Previous Release
```

자동 복구 가능해야 한다.

---

# Security

배포 시 확인

* Debug 비활성화
* 로그 레벨 확인
* 민감정보 제거
* Token 제거
* 테스트 데이터 제거

---

# Monitoring

운영 시 확인

* CPU
* Memory
* API Error
* WebSocket Status
* Strategy Status

---

# Release Checklist

* Version 증가
* CHANGELOG 작성
* README 업데이트
* 테스트 완료
* Installer 생성
* Release Package 생성

---

# Validation Checklist

* Windows 배포 지원
* PyInstaller 사용
* 환경 분리
* 자동 백업
* Rollback 지원
* CI/CD 지원
* 사용자 데이터 보호
* 민감정보 제외
* 테스트 통과 후 배포
* 문서와 구현 일치

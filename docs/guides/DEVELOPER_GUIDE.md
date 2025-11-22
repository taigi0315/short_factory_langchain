# Developer Guide / 개발자 가이드

This guide explains how to set up and run the ShortFactoryLangChain project using our automated tools.
이 가이드는 자동화 도구를 사용하여 ShortFactoryLangChain 프로젝트를 설정하고 실행하는 방법을 설명합니다.

## Prerequisites / 필수 조건

- **Python**: 3.8+
- **Node.js**: 18+
- **API Keys**: Google Gemini API Key (Required)

## 1. Quick Start / 빠른 시작

The easiest way to start developing is using the helper script.
개발을 시작하는 가장 쉬운 방법은 헬퍼 스크립트를 사용하는 것입니다.

1.  **Configure Environment / 환경 설정**:
    - Copy `.env.example` to `.env`.
    - `.env.example` 파일을 `.env`로 복사합니다.
    - Add your `GEMINI_API_KEY` in `.env`.
    - `.env` 파일에 `GEMINI_API_KEY`를 입력하세요.

2.  **Run Everything / 전체 실행**:
    ```bash
    ./start_dev.sh
    ```
    - This will install all dependencies (if missing).
    - 이 명령은 모든 의존성 패키지를 설치합니다 (없는 경우).
    - It opens the Frontend in a new tab and runs the Backend in the current tab.
    - 프론트엔드를 새 탭에서 열고, 백엔드를 현재 탭에서 실행합니다.

---

## 2. Manual Commands (Makefile) / 수동 명령어

If you prefer running things manually, use `make`.
수동으로 실행하고 싶다면 `make` 명령어를 사용하세요.

### Setup / 설치
Install all dependencies for Backend and Frontend.
백엔드와 프론트엔드의 모든 의존성을 설치합니다.
```bash
make setup
```

### Run Backend / 백엔드 실행
Runs the FastAPI server on `http://localhost:8001`.
`http://localhost:8001`에서 FastAPI 서버를 실행합니다.
```bash
make run-backend
```

### Run Frontend / 프론트엔드 실행
Runs the Next.js app on `http://localhost:3000`.
`http://localhost:3000`에서 Next.js 앱을 실행합니다.
```bash
make run-frontend
```

### Run Tests / 테스트 실행
Runs Python unit tests.
파이썬 유닛 테스트를 실행합니다.
```bash
make test
```

### Clean / 청소
Removes virtual environment, node_modules, and cache files.
가상 환경, node_modules, 캐시 파일들을 삭제합니다.
```bash
make clean
```

---

## 3. Verification / 확인

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend Health**: [http://localhost:8001/health](http://localhost:8001/health)
- **Frontend Proxy Check**: [http://localhost:3000/api/health](http://localhost:3000/api/health) (Should return backend status)

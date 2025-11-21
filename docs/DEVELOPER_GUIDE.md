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

1. **Configure Environment / 환경 설정**:
   - Copy `.env.example` to `.env`.
   - `.env.example` 파일을 `.env`로 복사합니다.
   - Add your `GEMINI_API_KEY` in `.env`.
   - `.env` 파일에 `GEMINI_API_KEY`를 입력하세요.

2. **Run Everything / 전체 실행**:
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
```bash
make setup
```

### Run Backend / 백엔드 실행
```bash
make run-backend
```
Runs the FastAPI server on `http://localhost:8001`.
`http://localhost:8001`에서 FastAPI 서버를 실행합니다.

### Run Frontend / 프론트엔드 실행
```bash
make run-frontend
```
Runs the Next.js app on `http://localhost:3000`.
`http://localhost:3000`에서 Next.js 앱을 실행합니다.

### Run Tests / 테스트 실행
```bash
make test
```
Runs Python unit tests.
파이썬 유닛 테스트를 실행합니다.

### Clean / 청소
```bash
make clean
```
Removes virtual environment, node_modules, and cache files.
가상 환경, node_modules, 캐시 파일들을 삭제합니다.

---

## 3. Verification / 확인

- **Frontend**: http://localhost:3000
- **Backend Health**: http://localhost:8001/health
- **Frontend Proxy Check**: http://localhost:3000/api/health (Should return backend status)

## 4. Dev Mode / 개발자 모드

Dev Mode allows you to test individual components of the video generation pipeline without running the full flow.
개발자 모드를 사용하면 전체 플로우를 실행하지 않고도 비디오 생성 파이프라인의 개별 구성 요소를 테스트할 수 있습니다.

### How to Access / 접속 방법
1. Start the development environment: `./start_dev.sh`
2. Open http://localhost:3000 (Dev Mode dashboard loads automatically)

### Features / 기능
- **Image Gen**: Generate single images from prompts with different styles (Cinematic, Single Character, Infographic, Comic Panel)
- **Script & Scenes**: Generate complete video scripts from story ideas
- **Video Gen**: Test video generation (Text to Video, Image to Video) - Currently mock implementation

### Configuration / 설정
Dev Mode respects environment variables:
```bash
# Use real services
USE_REAL_LLM=True
USE_REAL_IMAGE=True
GEMINI_API_KEY=your_key
NANO_BANANA_API_KEY=your_key

# Or use mock mode (default)
USE_REAL_LLM=False
USE_REAL_IMAGE=False
```

---

## 5. Documentation / 문서

Comprehensive documentation is available in the `docs/` directory:

- **[project.md](project.md)** - Complete project overview and architecture
- **[agents/README.md](agents/README.md)** - Agent implementations and patterns
- **[api/README.md](api/README.md)** - API endpoints and error handling
- **[core/README.md](core/README.md)** - Configuration management
- **[models/README.md](models/README.md)** - Data models and schemas
- **[dev-mode/README.md](dev-mode/README.md)** - Dev Mode usage guide

---

## 6. Troubleshooting / 문제 해결

### Backend Issues

**Problem**: `KeyError: "Attempt to overwrite 'args' in LogRecord"`
**Solution**: This has been fixed. Ensure you're using the latest code.

**Problem**: `404 models/gemini-1.5-flash is not found`
**Solution**: Update `.env` to use `LLM_MODEL_NAME=gemini-1.5-flash-latest`

**Problem**: `GEMINI_API_KEY required when USE_REAL_LLM=true`
**Solution**: Set `GEMINI_API_KEY` in `.env` file or disable real LLM with `USE_REAL_LLM=False`

### Frontend Issues

**Problem**: React hydration mismatch warning
**Solution**: This is caused by browser extensions (e.g., DarkReader). Safe to ignore or disable the extension.

**Problem**: API requests failing
**Solution**: Ensure backend is running on port 8001. Check http://localhost:8001/health

---

## 7. API Documentation / API 문서

Interactive API documentation is automatically generated:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

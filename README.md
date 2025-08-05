# CognitoVid

AI 기반 교육용 비디오 자동 생성 시스템

## 프로젝트 개요

CognitoVid는 복잡한 개념이나 용어를 자동으로 설명하는 짧고 간단한 교육용 비디오를 생성하는 AI 기반 애플리케이션입니다. 사용자 프롬프트를 입력하면 스크립트 생성부터 시각 자산, 음성 합성, 최종 비디오 조립까지 완전 자동화된 파이프라인을 통해 완성된 비디오를 제공합니다.

## 주요 기능

- 🤖 **자동 스크립트 생성**: 사용자 쿼리와 대상 연령에 맞는 명확하고 이해하기 쉬운 스크립트 생성
- 🛡️ **다층 안전성 검증**: 사용자 입력과 AI 생성 콘텐츠에 대한 포괄적인 안전성 검사
- ✅ **사실 검증**: 외부 지식 소스를 통한 생성된 정보의 교차 검증
- 🎨 **동적 시각 자산**: 스크립트의 핵심 포인트에 대한 관련 정적 이미지 시퀀스 생성
- 🎤 **고품질 음성 합성**: ElevenLabs API를 활용한 정확한 동기화를 위한 단어별 타임스탬프
- ⚙️ **사용자 맞춤 설정**: 대상 연령, 시각 스타일, 비디오 길이, 배경 음악, 브랜딩 등

## 기술 스택

- **오케스트레이션**: LangChain & LangGraph
- **백엔드**: FastAPI + GCP Cloud Tasks
- **데이터베이스**: Firestore (상태 관리)
- **캐싱**: Redis (Memorystore)
- **AI 서비스**: Google Gemini Pro, Imagen 2, ElevenLabs
- **비디오 처리**: FFmpeg
- **모니터링**: OpenTelemetry, Cloud Monitoring

## 개발 단계

1. **Phase 1**: 아키텍처 기반 설정
2. **Phase 2**: 핵심 로직 및 상태 관리
3. **Phase 3**: LLM, 오디오, 검증 통합
4. **Phase 4**: 시각 자산 및 FFmpeg 조립
5. **Phase 5**: 관찰성 및 고급 맞춤 설정
6. **Phase 6**: 국제화 및 베타 출시

## 시작하기

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
uvicorn app.main:app --reload
```

## 라이선스

MIT License 
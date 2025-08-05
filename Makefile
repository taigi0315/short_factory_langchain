.PHONY: help install test lint format clean build run docker-build docker-run docker-stop

# 기본 타겟
help: ## 사용 가능한 명령어를 표시합니다
	@echo "CognitoVid 개발 도구"
	@echo "=================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 개발 환경 설정
install: ## Python 의존성을 설치합니다
	pip install -r requirements.txt

install-dev: ## 개발 의존성을 포함하여 설치합니다
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# 테스트
test: ## 테스트를 실행합니다
	pytest tests/ -v --cov=app --cov-report=html

test-unit: ## 단위 테스트만 실행합니다
	pytest tests/unit/ -v

test-integration: ## 통합 테스트만 실행합니다
	pytest tests/integration/ -v

# 코드 품질
lint: ## 코드 린팅을 실행합니다
	flake8 app/ tests/
	mypy app/

format: ## 코드 포맷팅을 실행합니다
	black app/ tests/
	isort app/ tests/

# 정리
clean: ## 임시 파일들을 정리합니다
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# 로컬 실행
run: ## 로컬에서 애플리케이션을 실행합니다
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker: ## 워커를 실행합니다
	python -m app.workers.task_worker

# Docker 관련
docker-build: ## Docker 이미지를 빌드합니다
	docker build -t cognitovid:latest .

docker-run: ## Docker Compose로 애플리케이션을 실행합니다
	docker-compose up -d

docker-stop: ## Docker Compose 서비스를 중지합니다
	docker-compose down

docker-logs: ## Docker 로그를 확인합니다
	docker-compose logs -f

# 배포
deploy-dev: ## 개발 환경에 배포합니다
	@echo "개발 환경 배포 중..."
	# TODO: 개발 환경 배포 스크립트 추가

deploy-prod: ## 프로덕션 환경에 배포합니다
	@echo "프로덕션 환경 배포 중..."
	# TODO: 프로덕션 환경 배포 스크립트 추가

# 데이터베이스
db-migrate: ## 데이터베이스 마이그레이션을 실행합니다
	@echo "데이터베이스 마이그레이션 실행..."
	# TODO: Firestore 마이그레이션 스크립트 추가

# 모니터링
monitor: ## 모니터링 대시보드를 실행합니다
	@echo "모니터링 대시보드 실행..."
	# TODO: 모니터링 대시보드 실행 스크립트 추가

# 문서
docs-serve: ## 문서 서버를 실행합니다
	mkdocs serve

docs-build: ## 문서를 빌드합니다
	mkdocs build

# 환경 설정
setup-env: ## 환경 변수 파일을 설정합니다
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "환경 변수 파일이 생성되었습니다. .env 파일을 편집하여 설정을 완료하세요."; \
	else \
		echo ".env 파일이 이미 존재합니다."; \
	fi

# 개발 환경 초기 설정
init-dev: setup-env install-dev ## 개발 환경을 초기 설정합니다
	@echo "개발 환경 초기 설정이 완료되었습니다."
	@echo "다음 단계:"
	@echo "1. .env 파일을 편집하여 API 키와 설정을 입력하세요"
	@echo "2. 'make run' 명령으로 애플리케이션을 실행하세요" 
# 제안된 에이전트 아키텍처 리팩토링 (Proposed Agent Architecture Refactor)

## 목표 (Objective)

역할을 분리하고, **Director Agent(감독 에이전트)**를 활성화하며, 명확한 지휘 체계를 확립하여 에이전트 워크플로우를 재구성합니다. 이를 통해 각 에이전트가 본연의 임무에 집중하게 하여 스토리, 대본, 비주얼의 품질을 높입니다.

## 제안된 워크플로우 (Proposed Workflow)

```mermaid
graph TD
    User[사용자 입력] --> StoryFinder[스토리 발굴 에이전트]
    StoryFinder -->|스토리 컨셉| ScriptWriter[작가 에이전트]
    ScriptWriter -->|VideoScript (텍스트 중심)| Director[감독 에이전트]
    
    subgraph "비주얼 파이프라인"
        Director -->|DirectedScript (비주얼 지시)| ImageGen[이미지 생성 에이전트]
        Director -->|효과/전환| Assembly[비디오 조립 에이전트]
    end
    
    subgraph "오디오 파이프라인"
        ScriptWriter -->|대사| Voice[음성 에이전트]
    end
    
    ImageGen -->|이미지| Assembly
    Voice -->|오디오| Assembly
    Assembly -->|최종 비디오| Output
```

## 에이전트 별 역할 (Proposed Responsibilities)

### 1. Story Finder Agent (스토리 발굴 에이전트)
- **역할:** **연구원 (The Researcher)**.
- **임무:** 사용자의 주제에 맞춰 흥미로운 이야기, 사실, 뉴스를 찾아냅니다.
- **출력:** 구조화된 `StoryConcept` (주제, 핵심 사실, 관점).
- **변경점:** 파이프라인의 시작점이 되어야 합니다.

### 2. Script Writer Agent (작가 에이전트)
- **역할:** **각본가 (The Screenwriter)**.
- **임무:** 오직 서사, 대사, 페이싱(속도감)에만 집중합니다.
- **변경점:** 
    - **제거:** 상세한 이미지 프롬프트 작성 업무를 제거합니다.
    - **유지:** 기본적인 장면 묘사 (예: "분주한 시장").
    - **출력:** 풍부한 대사와 고수준의 장면 묘사가 담긴 `VideoScript`.

### 3. Director Agent (감독 에이전트)
- **역할:** **비전 제시자 (The Visionary)**.
- **임무:** 텍스트 대본을 시각적 경험으로 번역합니다.
- **변경점:** 파이프라인에서 이 에이전트를 **활성화**합니다.
    - **비주얼:** 기본적인 장면 묘사를 상세하고 스타일이 일관된 `image_prompts`(시각적 세그먼트)로 변환합니다.
    - **촬영:** `shot_type`(샷 종류), `camera_movement`(카메라 움직임), `lighting`(조명)을 결정합니다.
    - **효과:** 감정의 흐름(Beat)에 맞춰 비디오 효과(줌, 팬, 흔들림)를 명시적으로 선택합니다.
    - **출력:** `DirectedScript`.

### 4. Image Gen Agent (이미지 생성 에이전트)
- **역할:** **촬영감독 / 아티스트 (The Cinematographer / Artist)**.
- **임무:** 감독의 비전을 실행에 옮깁니다.
- **변경점:** 작가가 아닌 **감독**이 작성한 상세 프롬프트를 사용합니다.

### 5. Video Assembly Agent (비디오 조립 에이전트)
- **역할:** **편집자 (The Editor)**.
- **임무:** 최종 편집본을 조립합니다.
- **변경점:** **감독**이 지시한 효과와 전환 방식을 적용합니다.

## 구현 계획 (Implementation Plan)

1.  **`DirectorAgent` 리팩토링**: 현재의 `VideoScript`를 입력받아 후속 에이전트와 호환되는 `DirectedScript`를 출력하도록 수정합니다.
2.  **`ScriptWriter` 업데이트**: 스토리에 집중하도록 프롬프트를 단순화합니다.
3.  **`ImageGen` 업데이트**: `DirectedScript`를 수용하도록 수정합니다 (또는 `DirectedScript`가 향상된 프롬프트를 가진 `VideoScript`처럼 보이도록 어댑터 적용).
4.  **`VideoAssembly` 업데이트**: `DirectedScript`에서 효과/전환 메타데이터를 읽도록 수정합니다.
5.  **오케스트레이션**: `src/api/routes/videos.py`를 재작성하여 이 에이전트들을 올바르게 연결합니다.

## 기대 효과 (Benefits)
- **더 나은 스토리:** 작가가 비주얼에 신경 쓰지 않고 스토리에 집중할 수 있습니다.
- **더 나은 비주얼:** 감독이 시각적 언어와 일관성에만 집중할 수 있습니다.
- **모듈화:** 개별 에이전트를 업그레이드하기 쉬워집니다 (예: 작가 로직을 건드리지 않고 감독 로직만 교체 가능).

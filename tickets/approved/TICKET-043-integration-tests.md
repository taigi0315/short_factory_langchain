# [TICKET-043] Add Integration Tests for Complete Video Generation Pipeline

## Priority
- [ ] Critical
- [ ] High
- [x] Medium
- [ ] Low

## Type
- [x] Test Coverage

## Impact Assessment

**Business Impact**: Confidence in complete system, catch integration issues

**Technical Impact**:
- Modules Affected: All agents (integration)
- Files to Change: ~5 new test files
- Test Count: 10+ integration tests
- Coverage: End-to-end workflows

**Effort Estimate**: Medium (3-4 days)

## Problem Description

### Current State

**Missing Integration Tests:**
- No test for complete video generation workflow
- No test for workflow state persistence and resume
- No test for error recovery
- No test for agent interactions

**Current Tests:**
- Only unit tests for individual agents
- No end-to-end validation
- Manual testing required for full pipeline

## Proposed Solution

### Implementation

**Test 1: Complete Pipeline** (`tests/integration/test_complete_pipeline.py`):

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_video_generation():
    """Test complete video generation from topic to final video."""
    
    # 1. Generate story
    story_finder = StoryFinderAgent()
    stories = await story_finder.find_stories("AI technology", num_stories=1)
    assert len(stories.stories) > 0
    
    # 2. Generate script
    script_writer = ScriptWriterAgent()
    script = await script_writer.generate_script(stories.stories[0].summary)
    assert len(script.scenes) >= settings.MIN_SCENES
    
    # 3. Add cinematic direction
    director = DirectorAgent()
    directed_script = await director.analyze_script(script)
    assert len(directed_script.directed_scenes) == len(script.scenes)
    
    # 4. Generate images
    image_gen = ImageGenAgent()
    image_paths = await image_gen.generate_images_from_directed_script(directed_script)
    assert len(image_paths) == len(script.scenes)
    
    # 5. Generate audio
    voice_agent = VoiceAgent()
    audio_paths = await voice_agent.generate_audio_for_scenes(script.scenes)
    assert len(audio_paths) == len(script.scenes)
    
    # 6. Assemble video
    video_assembly = VideoAssemblyAgent()
    video_path = await video_assembly.assemble_video(
        script=script,
        image_paths=image_paths,
        audio_paths=audio_paths
    )
    assert os.path.exists(video_path)
    assert video_path.endswith(".mp4")
```

**Test 2: Workflow Resumability**:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_resume_after_failure():
    """Test workflow can resume after failure."""
    workflow_id = "test_workflow_123"
    
    # 1. Start workflow
    workflow_manager.create_workflow(workflow_id, topic="Test")
    
    # 2. Complete script generation
    script = await generate_script("Test")
    workflow_manager.save_script(workflow_id, script_path, len(script.scenes))
    workflow_manager.mark_step_complete(workflow_id, WorkflowStep.SCRIPT_GENERATION)
    
    # 3. Partially complete image generation (simulate failure)
    for i in range(3):  # Only 3 of 8 scenes
        image_path = await generate_image(script.scenes[i])
        workflow_manager.save_image(workflow_id, i+1, image_path)
    
    # Simulate failure
    workflow_manager.mark_failed(
        workflow_id,
        WorkflowStep.IMAGE_GENERATION,
        "Simulated failure"
    )
    
    # 4. Resume workflow
    state = workflow_manager.load_state(workflow_id)
    assert state.status == WorkflowStatus.FAILED
    assert state.images_completed == 3
    
    # Resume from scene 4
    for i in range(3, len(script.scenes)):
        if i+1 not in state.image_paths:
            image_path = await generate_image(script.scenes[i])
            workflow_manager.save_image(workflow_id, i+1, image_path)
    
    # Mark complete
    workflow_manager.mark_step_complete(workflow_id, WorkflowStep.IMAGE_GENERATION)
    
    state = workflow_manager.load_state(workflow_id)
    assert state.images_completed == len(script.scenes)
```

**Test 3: Error Recovery**:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery_with_retry():
    """Test system recovers from transient errors."""
    
    # Mock API to fail twice, then succeed
    call_count = 0
    
    async def flaky_api_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise APIError("Transient error")
        return "success"
    
    # Should succeed after retries
    result = await retry_with_backoff()(flaky_api_call)()
    assert result == "success"
    assert call_count == 3
```

**Test 4: Agent Interactions**:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_director_enhances_script_writer_output():
    """Test Director Agent enhances Script Writer output."""
    
    # Generate basic script
    script_writer = ScriptWriterAgent()
    script = await script_writer.generate_script("AI story")
    
    # Get basic image prompts
    basic_prompts = [scene.image_create_prompt for scene in script.scenes]
    
    # Add cinematic direction
    director = DirectorAgent()
    directed_script = await director.analyze_script(script)
    
    # Get enhanced prompts
    enhanced_prompts = [
        seg.image_prompt
        for scene in directed_script.directed_scenes
        for seg in scene.visual_segments
    ]
    
    # Verify enhancement
    assert len(enhanced_prompts) >= len(basic_prompts)
    for enhanced in enhanced_prompts:
        assert len(enhanced) > 50  # Enhanced prompts are detailed
        assert any(keyword in enhanced.lower() for keyword in [
            "cinematic", "shot", "lighting", "composition"
        ])
```

### Test Configuration

**pytest.ini**:

```ini
[pytest]
markers =
    integration: Integration tests (slow, require API keys)
    unit: Unit tests (fast, no external dependencies)

# Run only unit tests by default
addopts = -m "not integration"

# To run integration tests:
# pytest -m integration
```

## Files Affected

### New Test Files
- `tests/integration/test_complete_pipeline.py` - Full pipeline test
- `tests/integration/test_workflow_resumability.py` - Resume tests
- `tests/integration/test_error_recovery.py` - Error handling tests
- `tests/integration/test_agent_interactions.py` - Agent integration tests
- `tests/integration/conftest.py` - Integration test fixtures

### Configuration Files
- `pytest.ini` - Add integration marker
- `.github/workflows/test.yml` - Add integration test job (optional)

## Dependencies

- **Depends on**: TICKET-037 (Unit Tests - foundation)
- **Blocks**: None
- **Related to**: TICKET-039 (Error Handling)

## Success Criteria

- [ ] Complete pipeline test passing
- [ ] Workflow resumability test passing
- [ ] Error recovery test passing
- [ ] Agent interaction tests passing
- [ ] 10+ integration tests total
- [ ] Integration tests documented
- [ ] CI/CD integration (optional)

---

**Estimated Effort**: 3-4 days  
**Priority**: Medium  
**Risk**: Low  
**ROI**: High (confidence in system)

---
## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent
**Review Date:** 2025-11-26
**Decision:** ✅ APPROVED

**Strategic Rationale:**
Why this aligns with our architectural vision:
- **System Integrity**: Unit tests verify components, but integration tests verify the *system*. This is crucial for a pipeline where output of A is input of B.
- **Regression Prevention**: Ensures that changes in one agent don't break downstream agents.
- **Workflow Validation**: Specifically validates the "Resumable Workflow" architecture we are building.

**Implementation Phase:** Phase 3 - Performance & Validation
**Sequence Order:** #8 in implementation queue (Final validation)

**Architectural Guidance:**
Key considerations for implementation:
- **Mocking Strategy**: For integration tests, we should *still* mock the expensive/slow external APIs (LLMs, Image Gen) but use *real* internal components (WorkflowManager, File System). This is "Component Integration Testing".
- **Real E2E**: Have *one* true E2E test that hits real APIs, but run it manually or on a schedule (not on every commit) due to cost/time.
- **Data Cleanup**: Ensure tests clean up generated files/artifacts so they don't pollute the workspace.

**Dependencies:**
- **Must complete first**: TICKET-037 (Unit Tests) - Establish the testing patterns first.
- **Should complete first**: TICKET-042 (Async Patterns) - Integration tests should test the final async implementation.
- **Blocks**: None

**Risk Mitigation:**
- **Flakiness**: Integration tests are prone to flakiness. Use retries in tests and ensure deterministic inputs where possible.
- **Cost**: Be careful with real API calls. Use `vcrpy` or similar to record/replay API interactions if possible.

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Tests use a temporary directory for artifacts.
- [ ] "Mock Integration" vs "Real Integration" modes supported via env var.

**Alternative Approaches Considered:**
- **Selected approach:** Pytest integration suite with component mocking.

**Implementation Notes:**
- Create `tests/integration` directory.
- Use `pytest-asyncio`.

**Estimated Timeline**: 3-4 days
**Recommended Owner**: QA Engineer / Senior Backend Engineer

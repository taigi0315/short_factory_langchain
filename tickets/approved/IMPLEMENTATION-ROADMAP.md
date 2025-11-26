# Implementation Roadmap: Codebase Improvements

**Status**: 🟢 Ready for Execution
**Start Date**: 2025-11-26
**Estimated Duration**: 2-3 Weeks

This roadmap defines the sequence of execution for the approved code improvement tickets. The order is designed to minimize merge conflicts and build a solid foundation before adding complexity.

## Phase 1: Foundation & Quality (Week 1)
*Goal: Establish the structural backbone and ensure safety for future changes.*

1.  **[TICKET-036] Refactor Agent Base Class** (Critical)
    *   *Why First?*: It changes the inheritance hierarchy of every agent. Doing this later would require rewriting code twice.
    *   *Dependencies*: None.
    *   *Output*: `src/agents/base_agent.py` and updated agents.

2.  **[TICKET-041] Extract Hardcoded Config** (Medium)
    *   *Why Second?*: The new `BaseAgent` should use the centralized settings immediately.
    *   *Dependencies*: Can be done in parallel with 036, but best merged after.
    *   *Output*: Updated `src/core/config.py`.

3.  **[TICKET-037] Comprehensive Unit Test Suite** (Critical)
    *   *Why Third?*: Now that the structure (`BaseAgent`) is stable, we write tests against it. Writing tests before 036 would mean rewriting them immediately.
    *   *Dependencies*: TICKET-036.
    *   *Output*: ~80% test coverage.

## Phase 2: Reliability & Standardization (Week 2)
*Goal: Make the system robust, consistent, and easy to read.*

4.  **[TICKET-039] Standardize Error Handling** (High)
    *   *Why Fourth?*: Builds upon the `BaseAgent` and `Config` work. Adds retry logic to the clean base.
    *   *Dependencies*: TICKET-036, TICKET-041.
    *   *Output*: `src/core/retry.py` and standardized error logs.

5.  **[TICKET-040] Add Type Hints** (High)
    *   *Why Fifth?*: Can be done anytime, but easier once the major structural changes (Base Class, Error Handling) are in place.
    *   *Dependencies*: None (soft dependency on 036).
    *   *Output*: `mypy` passing.

6.  **[TICKET-038] Remove Unnecessary Comments** (High)
    *   *Why Sixth?*: Cleanup task. Best done after the code has settled to avoid "cleaning" code that gets deleted.
    *   *Dependencies*: None.
    *   *Output*: Cleaner codebase.

## Phase 3: Performance & Validation (Week 3)
*Goal: Optimize for scale and validate the entire system.*

7.  **[TICKET-042] Refactor Async Patterns** (Medium)
    *   *Why Seventh?*: Optimization step. Requires a stable codebase to ensure we don't introduce regressions while changing I/O patterns.
    *   *Dependencies*: TICKET-039 (Error handling needs to be async-aware).
    *   *Output*: Non-blocking I/O.

8.  **[TICKET-043] Integration Tests** (Medium)
    *   *Why Last?*: Validates the final state of the system, including all refactors and optimizations.
    *   *Dependencies*: All previous tickets.
    *   *Output*: End-to-end confidence.

## Execution Strategy

-   **Parallelism**:
    -   TICKET-041 (Config) and TICKET-038 (Comments) can be picked up by a second developer while TICKET-036/037 are in progress.
    -   TICKET-040 (Type Hints) is also a good parallel task.
-   **Checkpoints**:
    -   After Phase 1: Full regression test (manual).
    -   After Phase 2: Code freeze for major refactors.
    -   After Phase 3: Performance benchmarking.

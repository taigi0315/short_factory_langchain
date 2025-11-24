# [TICKET-028] Fix Frontend Video Generation Timeout

## Priority
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [x] Bug Fix
- [ ] Security Issue
- [ ] Technical Debt
- [ ] Code Duplication
- [ ] Feature Implementation

## Impact Assessment
**Business Impact:**
- **HIGH**: Users perceive the video generation as failed when it is actually still processing, leading to frustration and potential re-submissions.

**Technical Impact:**
- Affects: `frontend/src/app/page.tsx`, `frontend/src/components/DevDashboard.tsx`, `src/api/routes`
- Requires: Improving status polling or extending timeout handling.

**Effort Estimate:**
- Small (< 1 day)

---

## Problem Description

### Current State
**Status:** Bug
**What's happening:**
The frontend shows a "failed" message (or timeout error) while the backend is still processing the video. The user reports that the backend log shows completion, but the file continues to grow for 5-10 minutes.

**Current Error:**
Frontend displays error/timeout message while backend process is still active.

---

## Requirements

### Functional Requirements
**FR-1: Accurate Status Reporting**
- The frontend MUST NOT show an error message while the backend is still successfully processing the video.
- The frontend SHOULD poll for status or maintain a connection until the video is fully ready.

**FR-2: Timeout Handling**
- Increase the timeout limit on the frontend to accommodate the 5-10 minute generation time.
- Alternatively, implement an asynchronous job queue where the frontend polls for job completion.

### Non-Functional Requirements
**NFR-1: User Feedback**
- Provide clear progress indicators to the user during the long wait.

---

## Implementation Plan

### Phase 1: Investigation & Fix
1.  **Analyze Backend Endpoint**: Check `src/api/routes` to see if the video generation endpoint is blocking or async.
2.  **Update Frontend Timeout**: In `frontend/src/app/page.tsx` and `DevDashboard.tsx`, increase the fetch timeout or `AbortController` signal timeout to at least 15 minutes.
3.  **Implement Polling (Optional but Recommended)**: If the connection drops, implement a polling mechanism to check if the video file exists and is complete.

---

## Verification Plan

### Manual Verification
1.  Trigger a video generation.
2.  Wait for > 5 minutes.
3.  Verify that the frontend continues to show "Generating..." and does not time out.
4.  Verify that the final success message appears only when the video is fully ready and playable.

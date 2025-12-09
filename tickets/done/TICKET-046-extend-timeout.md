# [TICKET-046] Extend Default Request Timeout

## Priority
- [ ] Critical
- [x] High
- [ ] Medium
- [ ] Low

## Type
- [x] Configuration Change
- [ ] Refactoring
- [ ] Feature

## Impact Assessment
**Business Impact**: Prevents failures on long script generation tasks.
**Technical Impact**: `config.py`
**Effort Estimate**: Tiny (< 15 mins)

## Problem Description
Use reported timeout errors at the very end of script generation. The current default timeout (30 seconds) is insufficient for complex LLM tasks like full script writing.

## Proposed Solution
1. **Increase Default Timeout**: Update `DEFAULT_REQUEST_TIMEOUT` in `src/core/config.py` from `30.0` to `300.0` (5 minutes). This is a safe upper bound for most LLM operations.
2. **Verify Usage**: Ensure `ScriptWriterAgent` uses this timeout setting (already confirmed in TICKET-041 refactor, but double-check).

## Files Affected
- `src/core/config.py`

## Success Criteria
- [ ] No timeout errors during standard script generation.

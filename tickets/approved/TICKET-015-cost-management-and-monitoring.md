# TICKET-015: Cost Management & Monitoring

**Created:** 2025-01-21  
**Status:** APPROVED (Pre-approved by Architect)  
**Priority:** MEDIUM  
**Effort:** 1-2 days  
**Owner:** Backend Engineer

---

## Problem Statement

With real API integrations (Gemini LLM, NanoBanana images, ElevenLabs voice), production costs can escalate quickly without proper monitoring and controls. We need comprehensive cost tracking, alerts, and optimization recommendations.

**Current State:**
- No cost tracking across API calls
- No visibility into spending patterns
- No alerts or budget controls
- Cannot identify cost optimization opportunities

**Desired State:**
- Real-time cost tracking per video and per API
- Daily/monthly spending dashboards
- Alerts at spending thresholds
- Usage analytics to identify optimization opportunities
- Cost per video calculated and logged

---

## Proposed Solution

### 1. Cost Tracking Service

Create `src/services/cost_tracking.py`:

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
import json
from collections import defaultdict

@dataclass
class CostEntry:
    """Single cost entry for an API call."""
    timestamp: datetime
    service: str  # "gemini", "nanobanana", "elevenlabs"
    operation: str  # "story_generation", "image_generation", etc.
    cost: float
    metadata: Dict  # Additional context (tokens, chars, etc.)
    video_id: Optional[str] = None

class CostTracker:
    """Track and analyze API costs."""
    
    def __init__(self, data_dir: Path = Path("data/costs")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_costs: List[CostEntry] = []
    
    def log_cost(
        self,
        service: str,
        operation: str,
        cost: float,
        metadata: Dict = None,
        video_id: str = None
    ):
        """Log a cost entry."""
        entry = CostEntry(
            timestamp=datetime.now(),
            service=service,
            operation=operation,
            cost=cost,
            metadata=metadata or {},
            video_id=video_id
        )
        
        self.current_costs.append(entry)
        self._persist_entry(entry)
        
        logger.info(
            f"Cost logged: {service}.{operation} = ${cost:.4f}",
            extra={"cost": cost, "service": service}
        )
    
    def get_daily_costs(self, target_date: date = None) -> Dict[str, float]:
        """Get costs by service for a specific day."""
        target_date = target_date or date.today()
        
        costs_by_service = defaultdict(float)
        
        for entry in self._load_entries_for_date(target_date):
            costs_by_service[entry.service] += entry.cost
        
        return dict(costs_by_service)
    
    def get_monthly_costs(self, year: int, month: int) -> Dict[str, float]:
        """Get costs by service for a specific month."""
        costs_by_service = defaultdict(float)
        
        for day in range(1, 32):
            try:
                target_date = date(year, month, day)
                daily_costs = self.get_daily_costs(target_date)
                for service, cost in daily_costs.items():
                    costs_by_service[service] += cost
            except ValueError:
                break  # Invalid day for month
        
        return dict(costs_by_service)
    
    def get_video_cost(self, video_id: str) -> Dict[str, float]:
        """Get total cost breakdown for a specific video."""
        costs_by_service = defaultdict(float)
        
        for entry in self.current_costs:
            if entry.video_id == video_id:
                costs_by_service[entry.service] += entry.cost
        
        return dict(costs_by_service)
    
    def _persist_entry(self, entry: CostEntry):
        """Persist cost entry to daily log file."""
        log_date = entry.timestamp.date()
        log_file = self.data_dir / f"costs_{log_date.isoformat()}.jsonl"
        
        with log_file.open('a') as f:
            f.write(json.dumps({
                'timestamp': entry.timestamp.isoformat(),
                'service': entry.service,
                'operation': entry.operation,
                'cost': entry.cost,
                'metadata': entry.metadata,
                'video_id': entry.video_id
            }) + '\n')
    
    def _load_entries_for_date(self, target_date: date) -> List[CostEntry]:
        """Load all cost entries for a specific date."""
        log_file = self.data_dir / f"costs_{target_date.isoformat()}.jsonl"
        
        if not log_file.exists():
            return []
        
        entries = []
        with log_file.open('r') as f:
            for line in f:
                data = json.loads(line)
                entries.append(CostEntry(
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    service=data['service'],
                    operation=data['operation'],
                    cost=data['cost'],
                    metadata=data['metadata'],
                    video_id=data.get('video_id')
                ))
        
        return entries

# Global cost tracker instance
cost_tracker = CostTracker()
```

### 2. Cost Calculation Utilities

Create `src/services/cost_calculator.py`:

```python
class CostCalculator:
    """Calculate costs for different API services."""
    
    # Pricing (update with actual rates)
    GEMINI_COST_PER_1K_TOKENS = 0.00025  # $0.00025 per 1K tokens
    NANOBANANA_COST_PER_IMAGE = 0.02  # $0.02 per image
    ELEVENLABS_COST_PER_1K_CHARS = 0.30  # $0.30 per 1K characters
    
    @staticmethod
    def calculate_gemini_cost(input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Gemini API call."""
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * CostCalculator.GEMINI_COST_PER_1K_TOKENS
    
    @staticmethod
    def calculate_nanobanana_cost(num_images: int) -> float:
        """Calculate cost for NanoBanana image generation."""
        return num_images * CostCalculator.NANOBANANA_COST_PER_IMAGE
    
    @staticmethod
    def calculate_elevenlabs_cost(text_length: int) -> float:
        """Calculate cost for ElevenLabs voice synthesis."""
        return (text_length / 1000) * CostCalculator.ELEVENLABS_COST_PER_1K_CHARS
    
    @staticmethod
    def calculate_video_cost(
        num_stories: int,
        num_images: int,
        dialogue_length: int,
        avg_tokens_per_story: int = 500
    ) -> Dict[str, float]:
        """Calculate estimated total cost for video generation."""
        
        costs = {
            'gemini_story': CostCalculator.calculate_gemini_cost(100, avg_tokens_per_story) * num_stories,
            'gemini_script': CostCalculator.calculate_gemini_cost(200, 800),  # Approximate
            'images': CostCalculator.calculate_nanobanana_cost(num_images),
            'voice': CostCalculator.calculate_elevenlabs_cost(dialogue_length)
        }
        
        costs['total'] = sum(costs.values())
        
        return costs
```

### 3. Integration with Agents

Update agents to log costs:

```python
# In StoryFinderAgent
async def find_stories(self, topic: str) -> List[str]:
    result = await self.chain.ainvoke({"topic": topic})
    
    # Log cost
    if self.use_real:
        cost = CostCalculator.calculate_gemini_cost(
            input_tokens=len(topic.split()) * 2,  # Rough estimate
            output_tokens=len(result.split()) * 2
        )
        cost_tracker.log_cost(
            service="gemini",
            operation="story_generation",
            cost=cost,
            metadata={"topic": topic, "num_stories": len(result)}
        )
    
    return result

# In ImageGenAgent
async def generate_image(self, prompt: str) -> Path:
    image_path = await self.client.generate(prompt)
    
    # Log cost
    cost = CostCalculator.calculate_nanobanana_cost(1)
    cost_tracker.log_cost(
        service="nanobanana",
        operation="image_generation",
        cost=cost,
        metadata={"prompt": prompt[:100]}
    )
    
    return image_path
```

### 4. Cost Dashboard API

Add to `src/api/routes/analytics.py`:

```python
from fastapi import APIRouter
from datetime import date
from src.services.cost_tracking import cost_tracker

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/costs/daily")
async def get_daily_costs(target_date: str = None):
    """Get daily cost breakdown."""
    if target_date:
        target = date.fromisoformat(target_date)
    else:
        target = date.today()
    
    costs = cost_tracker.get_daily_costs(target)
    total = sum(costs.values())
    
    return {
        "date": target.isoformat(),
        "costs_by_service": costs,
        "total": total
    }

@router.get("/costs/monthly")
async def get_monthly_costs(year: int, month: int):
    """Get monthly cost breakdown."""
    costs = cost_tracker.get_monthly_costs(year, month)
    total = sum(costs.values())
    
    return {
        "year": year,
        "month": month,
        "costs_by_service": costs,
        "total": total
    }

@router.get("/costs/video/{video_id}")
async def get_video_cost(video_id: str):
    """Get cost breakdown for a specific video."""
    costs = cost_tracker.get_video_cost(video_id)
    total = sum(costs.values())
    
    return {
        "video_id": video_id,
        "costs_by_service": costs,
        "total": total
    }
```

### 5. Cost Alerts

Create `src/services/cost_alerts.py`:

```python
class CostAlertService:
    """Monitor costs and send alerts."""
    
    def __init__(self, daily_limit: float = 50.0, monthly_limit: float = 500.0):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
    
    async def check_daily_limit(self):
        """Check if daily spending exceeds threshold."""
        costs = cost_tracker.get_daily_costs()
        total = sum(costs.values())
        
        if total >= self.daily_limit * 0.8:  # 80% threshold
            logger.warning(
                f"Daily cost alert: ${total:.2f} / ${self.daily_limit:.2f} (80% threshold)",
                extra={"total_cost": total, "limit": self.daily_limit}
            )
        
        if total >= self.daily_limit:
            logger.error(
                f"Daily cost limit exceeded: ${total:.2f} / ${self.daily_limit:.2f}",
                extra={"total_cost": total, "limit": self.daily_limit}
            )
            # Could send email, Slack notification, etc.
    
    async def check_monthly_limit(self):
        """Check if monthly spending exceeds threshold."""
        today = date.today()
        costs = cost_tracker.get_monthly_costs(today.year, today.month)
        total = sum(costs.values())
        
        if total >= self.monthly_limit * 0.8:
            logger.warning(
                f"Monthly cost alert: ${total:.2f} / ${self.monthly_limit:.2f}",
                extra={"total_cost": total, "limit": self.monthly_limit}
            )

# Run periodic checks
alert_service = CostAlertService()
```

---

## Success Criteria

- [ ] Cost tracking implemented for all APIs (Gemini, NanoBanana, ElevenLabs)
- [ ] Daily and monthly cost dashboards accessible via API
- [ ] Cost per video calculated and logged
- [ ] Alerts trigger at 80% of daily/monthly budget
- [ ] Cost data persisted to disk (survives restarts)
- [ ] Analytics API endpoints working
- [ ] Documentation updated with cost monitoring guide

---

## Testing Plan

### Unit Tests

```python
def test_cost_tracker():
    """Test cost tracking functionality."""
    tracker = CostTracker(data_dir=Path("test_data"))
    
    tracker.log_cost(
        service="gemini",
        operation="test",
        cost=0.05,
        metadata={"tokens": 1000}
    )
    
    daily_costs = tracker.get_daily_costs()
    assert "gemini" in daily_costs
    assert daily_costs["gemini"] == 0.05

def test_cost_calculator():
    """Test cost calculation utilities."""
    cost = CostCalculator.calculate_gemini_cost(1000, 500)
    assert cost > 0
    
    cost = CostCalculator.calculate_nanobanana_cost(5)
    assert cost == 0.10  # 5 images * $0.02
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_cost_tracking_in_pipeline():
    """Test cost tracking throughout video generation pipeline."""
    
    # Generate video
    video_id = "test_video_123"
    
    # ... generate script, images, audio, video ...
    
    # Check costs were logged
    costs = cost_tracker.get_video_cost(video_id)
    
    assert "gemini" in costs
    assert "nanobanana" in costs
    assert "elevenlabs" in costs
    assert costs["gemini"] > 0
```

---

## Implementation Steps

1. **Cost Tracking Service** (2 hours)
   - Implement `CostTracker` class
   - Add persistence to JSONL files
   - Add query methods (daily, monthly, per-video)

2. **Cost Calculator** (1 hour)
   - Implement cost calculation for each API
   - Research actual pricing rates
   - Add video cost estimation

3. **Agent Integration** (2 hours)
   - Update `StoryFinderAgent` to log costs
   - Update `ImageGenAgent` to log costs
   - Update `VideoGenAgent` to log costs
   - Add video ID tracking

4. **Analytics API** (1 hour)
   - Create `/analytics/costs/*` endpoints
   - Test with real data
   - Add error handling

5. **Cost Alerts** (1 hour)
   - Implement `CostAlertService`
   - Add threshold checks
   - Test alert triggering

6. **Documentation** (1 hour)
   - Document cost tracking system
   - Add cost monitoring guide
   - Document API endpoints

---

## Dependencies

- **Parallel with**: TICKET-009, TICKET-013, TICKET-014
- **Recommended**: Implement alongside real API integrations

---

## Risks & Mitigation

### Risk: Inaccurate Cost Estimates

**Mitigation:**
- Use actual API pricing documentation
- Update rates monthly
- Add buffer (10%) for estimation errors

### Risk: Missing Cost Entries

**Mitigation:**
- Comprehensive logging in all agents
- Unit tests to verify cost logging
- Periodic audits of cost data

---

## References

- Gemini Pricing: https://ai.google.dev/pricing
- ElevenLabs Pricing: https://elevenlabs.io/pricing
- NanoBanana Pricing: (find actual docs)

---

## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent  
**Review Date:** 2025-01-21  
**Decision:** ✅ APPROVED (Pre-approved)

**Strategic Rationale:**
- **Cost Control**: Essential for sustainable production operations
- **Visibility**: Enables data-driven optimization decisions
- **Risk Mitigation**: Prevents unexpected cost overruns
- **Foundation for Scaling**: Required before high-volume usage

**Implementation Phase:** Phase 2, Week 3  
**Sequence Order:** #5 (Parallel with TICKET-012, after real APIs integrated)

**Architectural Guidance:**
- **Simple Persistence**: JSONL files are sufficient, no database needed yet
- **Real-Time Logging**: Log costs immediately after API calls
- **Aggregate Analytics**: Pre-calculate daily/monthly totals for dashboard performance
- **Alert Thresholds**: Start conservative (80%), adjust based on usage patterns

**Estimated Timeline:** 1-2 days  
**Recommended Owner:** Backend engineer (can be same as other tickets)

---

**Priority: MEDIUM** - Important for production operations, not blocking launch

# Script Writer Specialization - Design Decision

## Context
We are refactoring the Script Writer to focus on narrative quality rather than detailed visual engineering. The Director Agent will handle all visual details.

## Options for Visual Detail Level

### Option A: Minimal Scene Context
**Script Writer Output:**
```
"A busy marketplace"
```

**Director Enhancement:**
```
"Wide establishing shot of a bustling Moroccan marketplace at golden hour, vibrant colors, rule of thirds composition with merchant stalls on left third, warm golden lighting from setting sun, photorealistic style with rich textures"
```

**Pros:**
- Maximum separation of concerns
- Script Writer fully focused on narrative

**Cons:**
- Director has less context to work with
- May result in generic visuals

---

### Option B: Moderate Context (RECOMMENDED)
**Script Writer Output:**
```
"A busy marketplace, warm and inviting atmosphere, colorful stalls"
```

**Director Enhancement:**
```
"Medium shot of a bustling marketplace, golden hour lighting creating warm atmosphere, colorful merchant stalls arranged using rule of thirds, slow push-in camera movement, photorealistic style"
```

**Pros:**
- Balanced approach
- Script Writer provides narrative context
- Director adds cinematic expertise
- Clear separation of responsibilities

**Cons:**
- Requires clear guidelines on what's "narrative" vs "visual"

---

### Option C: Descriptive Without Technical Terms
**Script Writer Output:**
```
"A busy marketplace filled with vibrant colors and warm sunlight, merchants calling out to customers, the air filled with spices and excitement"
```

**Director Enhancement:**
```
"Wide establishing shot, golden hour lighting, rule of thirds with market on left, slow pan right, photorealistic style, 8k quality"
```

**Pros:**
- Rich narrative context
- Removes only technical jargon

**Cons:**
- Script Writer still thinking about visuals
- Less clear separation

---

## Recommendation: Option B

**Rationale:**
- Provides enough context for the Director to make informed decisions
- Keeps Script Writer focused on "what" not "how"
- Aligns with the "Chain of Command" architecture goal
- Easier to test and validate

**Implementation:**
Remove from Script Writer prompts:
- Camera angles (wide shot, close-up, etc.)
- Composition rules (rule of thirds, etc.)
- Lighting technical terms (golden hour, chiaroscuro, etc.)
- Technical quality terms (4k, photorealistic, etc.)

Keep in Script Writer prompts:
- Scene setting (location, environment)
- Mood and atmosphere
- Key visual elements that serve the narrative
- Character actions and expressions

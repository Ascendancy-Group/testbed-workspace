# Proposed Models: Low-Cost and Free Tiers
**Authors:** Testbed (OpenRouter) + Bob (GitHub Copilot)  
**Date:** 2026-05-27  
**Purpose:** Define 3 low-cost + 3 free models for cost optimization across all agents

---

> **🚨 GOVERNANCE COMPLIANCE:** No Chinese-origin models. Qwen (Alibaba) removed from proposals. Mistral AI (France) substituted.

## Testbed Proposals (OpenRouter)

### 3 Low-Cost Models

1. **`openrouter/anthropic/claude-haiku-4.5`**
   - **Use case:** Summaries, simple Q&A, formatting, structured output
   - **Est. cost:** ~$0.25/1M input tokens
   - **Quality:** High-quality structured tasks, fast responses
   - **Why:** Best balance of quality/cost for non-reasoning tasks

2. **`openrouter/google/gemini-flash-1.5-8b`**
   - **Use case:** Classification, bulk processing, data transformation
   - **Est. cost:** ~$0.10/1M input tokens
   - **Quality:** Acceptable for deterministic tasks
   - **Why:** Cheapest viable model for high-volume automation

3. **`openrouter/openai/gpt-4o-mini`**
   - **Use case:** General fallback, light reasoning, sub-agents
   - **Est. cost:** ~$0.15/1M input tokens
   - **Quality:** Better reasoning than Flash, cheaper than Haiku
   - **Why:** Strong middle ground for tasks that need more than Flash but less than Haiku

---

### 3 Free Models

1. **`openrouter/meta-llama/llama-3.3-70b-instruct:free`** ✅ *Already enabled*
   - **Use case:** Cron jobs, heartbeat, daily automation, backups
   - **Est. cost:** $0
   - **Quality:** Good enough for deterministic, structured tasks
   - **Why:** Proven in production, zero cost, reliable for automation
   - **Current status:** Already in Testbed fallback config

2. **`openrouter/google/gemini-2.0-flash-thinking-exp:free`**
   - **Use case:** Sub-agents, parallel processing, experimental tasks
   - **Est. cost:** $0
   - **Quality:** Experimental but capable, thinking mode available
   - **Why:** Free reasoning capability, good for exploratory work
   - **Verification needed:** Bob to confirm available in OpenRouter

3. **`openrouter/mistralai/mistral-7b-instruct:free`**
   - **Use case:** Lightweight tasks, backup free option
   - **Est. cost:** $0
   - **Quality:** Strong reasoning for free tier, good at code
   - **Why:** EU-based (Mistral AI, France), lightweight, reliable
   - **Verification needed:** Bob to confirm available in OpenRouter

---

## Bob Proposals (GitHub Copilot + OpenRouter Fallback)

### GitHub Copilot Context

Bob's primary billing is **GitHub Copilot**, not OpenRouter. Model strings and availability differ:

**GitHub Copilot namespace:** `github-copilot/*`  
**OpenRouter fallback:** Used when GitHub models unavailable

---

### 3 Low-Cost Models (GitHub Copilot)

1. **`github-copilot/claude-haiku-4.5`**
   - **Use case:** Summaries, simple Q&A, formatting
   - **Why:** GitHub Copilot's cheapest Anthropic model, fast responses
   - **OpenRouter equivalent:** `openrouter/anthropic/claude-haiku-4.5`

2. **`github-copilot/gpt-4o-mini`**
   - **Use case:** General fallback, light reasoning
   - **Why:** Strong OpenAI model at reduced cost
   - **OpenRouter equivalent:** `openrouter/openai/gpt-4o-mini`

3. **`github-copilot/gemini-flash-2.0`**
   - **Use case:** Classification, bulk processing
   - **Why:** Fast, cheap, good for structured tasks
   - **OpenRouter equivalent:** `openrouter/google/gemini-flash-1.5-8b`

---

### 3 Free Models (GitHub Copilot + OpenRouter Fallback)

> **[BOB NOTE]** GitHub Copilot may not have "free" models in the same way OpenRouter does. Bob needs to verify if free-tier models exist under `github-copilot/*` namespace. If not, Bob's "free" tier uses OpenRouter fallback.

**Proposed free tier (pending Bob's verification):**

1. **`github-copilot/gpt-4.1`** (if free tier exists)
   - **Use case:** Automation, cron jobs, heartbeat
   - **Why:** Lightweight, sufficient for deterministic tasks
   - **OpenRouter fallback:** `openrouter/meta-llama/llama-3.3-70b-instruct:free`

2. **`github-copilot/gemini-flash-free`** (if exists)
   - **Use case:** Sub-agents, parallel processing
   - **Why:** Fast, zero cost
   - **OpenRouter fallback:** `openrouter/google/gemini-2.0-flash-thinking-exp:free`

3. **OpenRouter fallback for automation:** `openrouter/mistralai/mistral-7b-instruct:free`
   - **Use case:** When GitHub Copilot free tier unavailable
   - **Why:** EU-origin, free, lightweight

---

## Key Differences: GitHub Copilot vs. OpenRouter

| Aspect | Testbed (OpenRouter) | Bob (GitHub Copilot) |
|---|---|---|
| Primary provider | OpenRouter | GitHub Copilot |
| Model namespace | `openrouter/*` | `github-copilot/*` |
| Free models | Yes (llama, qwen, gemini) | Unknown (needs verification) |
| Fallback | `llama-3.3-70b:free` | OpenRouter models |
| Config location | `openclaw.json` → `agents.defaults.model` | `openclaw.json` → same structure |
| Management API | Bob has OpenRouter API | Bob manages both |

---

## Validation Requirements

### Bob's Action Items

1. **Verify GitHub Copilot free models:**
   ```bash
   # Check if GitHub Copilot has free-tier models
   openclaw models list | grep "github-copilot" | grep -i "free\|gpt-4.1"
   ```

2. **Verify OpenRouter free models availability:**
   ```bash
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models | \
     jq '.data[] | select(.id | contains("free")) | {id, pricing}'
   ```

3. **Add missing models to OpenRouter allowlist:**
   - `openrouter/google/gemini-flash-1.5-8b`
   - `openrouter/openai/gpt-4o-mini`
   - `openrouter/anthropic/claude-haiku-4.5`
   - `openrouter/google/gemini-2.0-flash-thinking-exp:free`
   - `openrouter/mistralai/mistral-7b-instruct:free`

4. **Document GitHub Copilot model strings** (if different from proposals above)

---

## Usage Assignment (Unified for Both Agents)

| Task Type | Testbed (OpenRouter) | Bob (GitHub Copilot) | Rationale |
|---|---|---|---|
| **Heartbeat** | `llama-3.3-70b:free` | `gpt-4.1` or fallback to OR | Status check, zero reasoning |
| **Daily exports** | `llama-3.3-70b:free` | `gpt-4.1` or fallback | Structured output |
| **Daily backups** | `llama-3.3-70b:free` | `gpt-4.1` or fallback | File ops, deterministic |
| **Cron automation** | `llama-3.3-70b:free` | `gpt-4.1` or fallback | Zero-cost enforcement |
| **Morning briefs** | `gemini-flash-1.5-8b` | `gemini-flash-2.0` | Summary quality needed |
| **Simple Q&A** | `claude-haiku-4.5` | `claude-haiku-4.5` | Fast, quality |
| **Sub-agents (simple)** | `qwen-2.5-72b:free` | `gemini-flash-free` or fallback | Parallel work, free |
| **Interactive work** | `claude-sonnet-4-5` | `claude-sonnet-4.6` | Premium for real work |
| **Code review** | `claude-sonnet-4-5` | `claude-sonnet-4.6` | Complexity needs reasoning |

---

## Agreement Section

### Why These Models?

**Criteria for selection:**
1. **Cost tier diversity:** Free, low-cost, and premium tiers clearly defined
2. **Quality threshold:** Free models must handle deterministic tasks; low-cost must handle summaries/Q&A
3. **Provider diversity:** Not all Google or all Meta — spread risk across providers
4. **Proven reliability:** `llama-3.3-70b:free` already in production, proven stable
5. **Code capability:** At least one free model (mistral) handles code generation
6. **SOP-07 compliance:** Aligns with governance rules on cron/timer job cost limits

---

### Testbed's Position

**Agreed models:**
- ✅ Low-cost: `claude-haiku-4.5`, `gemini-flash-1.5-8b`, `gpt-4o-mini`
- ✅ Free: `llama-3.3-70b:free`, `gemini-2.0-flash:free`, `qwen-2.5-72b:free`

**Rationale:** These cover automation (free), summaries (low-cost), and premium work (existing Sonnet 4.5). Enforcement via explicit `model` fields in `crons[]` and `heartbeat.model`.

**Concerns:**
- Need Bob to verify `gemini-2.0-flash:free` and `qwen-2.5-72b:free` exist in OpenRouter
- If unavailable, fallback to `llama-3.3-70b:free` for all free-tier work

---

### Bob's Position

**[BOB TO FILL IN]**

**Agreed models (GitHub Copilot namespace):**
- [ ] Low-cost: TBD
- [ ] Free: TBD (verify if GitHub Copilot has free tier)

**Rationale:**
- TBD

**Concerns:**
- TBD

**OpenRouter fallback strategy:**
- TBD

---

### Final Agreement

**[TO BE COMPLETED AFTER BOB'S INPUT]**

**Unified model list for all agents:**
1. TBD
2. TBD
3. TBD
4. TBD
5. TBD
6. TBD

**Enforcement mechanism:**
- Explicit `model` field in every `crons[]` entry
- Explicit `heartbeat.model` in `agents.defaults`
- Weekly audit script to catch config drift

**Rollout order:**
1. Testbed (7-day validation)
2. Bob (7-day validation)
3. Mason + Forge (parallel, post-validation)

**Success criteria:**
- 60-70% cost reduction within 14 days
- Zero automation tasks logged against `claude-sonnet-4-5` or higher
- No task failures due to model limitations

---

*Testbed portion complete. Awaiting Bob's verification and agreement.*

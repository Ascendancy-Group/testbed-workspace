# Rollout Plan: memory_search Local Embeddings
**Authored:** 2026-08-14 by Testbed
**Scheduled:** Monday 2026-08-18
**Approved by:** Pieter van der Wal 2026-08-14
**Status:** READY FOR EXECUTION

---

## Objective

Switch all agents from OpenAI embeddings (broken — no API key) to
`provider: "local"` using embeddinggemma-300m (free, on-device, no external API).

**Model:** `hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf`
Downloads once on first use. Cached at `~/.node-llama-cpp/models/`.

---

## Rollout Order

1. Forge (forge-m1)
2. Mason (mason-m1)
3. Vera (vera-m1)
4. Bob (bobwebdev-m1)
5. Testbed (testbed-m1) — last, after fleet proven

---

## Pre-Conditions (before touching ANY machine)

- [ ] Pieter takes Hetzner snapshot of the target machine
- [ ] Testbed validates snapshot exists via Hetzner API
- [ ] Snapshot name format: `pre-memory-search-local-{machine}-{YYYY-MM-DD-HHMM}`
- [ ] Agent backs up openclaw.json: `openclaw.json.backup-memory-search-local-{YYYYMMDD-HHMMSS}`
- [ ] Backup path: `Backups-Granular/openclaw.json__YYYY-MM-DD_HH-MM/`
- [ ] Confirm Node version is 24 on target machine: `node --version`

---

## Per-Machine Procedure

### Step 1 — Snapshot + Backup (non-negotiable)
```bash
# Pieter takes Hetzner snapshot first — validate via API:
curl -H "Authorization: Bearer $HETZNER_TOKEN" \
  "https://api.hetzner.cloud/v1/images?type=snapshot" | \
  python3 -m json.tool | grep "pre-memory-search"

# Agent backs up openclaw.json:
cp ~/.openclaw/openclaw.json \
  ~/.openclaw/openclaw.json.backup-memory-search-local-$(date +%Y%m%d-%H%M%S)
```

### Step 2 — Install Plugin
```bash
openclaw plugins install @openclaw/llama-cpp-provider
```
Verify install:
```bash
openclaw plugins list | grep llama
```
Expected: `@openclaw/llama-cpp-provider` listed and enabled.

### Step 3 — Edit openclaw.json
Add under `agents.defaults`:
```json
"memorySearch": {
  "provider": "local",
  "local": {
    "modelPath": "hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf"
  }
}
```

### Step 4 — Restart Gateway
```bash
oc-restart
```
Wait for gateway to come back up:
```bash
openclaw status
```
Expected: `Gateway ... running`

### Step 5 — Model Download (first run only)
On first `memory_search` call, the model downloads (~300MB).
Trigger it explicitly and wait:
```bash
openclaw chat --message "test memory search" --no-reply 2>&1 | head -20
```
Or just run a session and observe. Download happens once, cached permanently.

### Step 6 — Verification Tests
```bash
# 1. Gateway healthy
openclaw status | grep "running"

# 2. memory_search functional — run a test query via agent
# Expected: results returned, no "OpenAI API key missing" error

# 3. Check model cache exists
ls ~/.node-llama-cpp/models/ | grep embedding
```

**Pass criteria:**
- [ ] Gateway running post-restart
- [ ] No embedding provider auth errors in logs
- [ ] memory_search returns results
- [ ] Model file present in cache

### Step 7 — Post-Work Snapshot
```bash
# After successful verification:
# Pieter or Testbed creates post-work snapshot via Hetzner API
# Name: post-memory-search-local-{machine}-{YYYY-MM-DD-HHMM}
```

---

## Rollback Procedure

If anything goes wrong at any step — STOP. Do not attempt fixes. Rollback first.

### Rollback Steps
1. Restore openclaw.json from backup:
```bash
cp ~/.openclaw/openclaw.json.backup-memory-search-local-* ~/.openclaw/openclaw.json
```
2. Restart gateway:
```bash
oc-restart
```
3. Verify gateway running:
```bash
openclaw status
```
4. If still broken → Pieter restores Hetzner snapshot via console
5. Document failure + root cause in daily note
6. Alert Pieter immediately
7. Do NOT proceed to next machine until failure is understood

**Rollback time estimate:** < 5 minutes from backup. < 15 minutes from Hetzner snapshot.

---

## Go / No-Go Gates Between Machines

Each machine must fully pass Step 6 verification before moving to the next.

| Machine | Snapshot Validated | Plugin Installed | JSON Edited | Gateway Running | memory_search OK | Post Snapshot |
|---|---|---|---|---|---|---|
| forge-m1 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| mason-m1 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| vera-m1  | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| bobwebdev-m1 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| testbed-m1 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## Known Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| node-llama-cpp native build fails | Low (Node 24 on all machines) | Plugin install step catches it before JSON change |
| Model download fails (HuggingFace unreachable) | Low | Retry; no gateway impact until first search call |
| Gateway fails to restart post-JSON edit | Low | Backup + snapshot means < 5 min rollback |
| Mason migration lock pattern (seen 2026-08-12) | Medium | Wait 2 min, reset-failed, manual start — known fix |

---

## Notes
- embeddinggemma-300m is ~300MB download, one-time
- No API key required ever again after this
- GitHub Copilot does NOT expose an embeddings API — local model is the right call
- Node 24 confirmed on all machines from 2026-08-12 upgrade run

---

## Sign-Off
- Authored: Testbed 2026-08-14
- Approved: Pieter van der Wal 2026-08-14
- Bob review: pending (Monday)
- Execute: Monday 2026-08-18

# n8n Research & Integration Plan — 2026-07-20

## Executive Summary

**n8n** is an open-source, self-hostable workflow automation platform (Zapier alternative) that can integrate with our OpenClaw agent infrastructure via **MCP (Model Context Protocol)**.

**Key value propositions:**
1. **Cost savings:** 80-90% cheaper than Zapier at scale (unlimited self-hosted executions)
2. **Data sovereignty:** Full control, on-prem deployment behind firewall
3. **OpenClaw integration:** Native MCP support enables agents to trigger/build workflows
4. **Internal system access:** Connect to databases, private APIs, internal services
5. **Developer-friendly:** Git versioning, code nodes, CI/CD integration

**Recommendation:** Deploy n8n on honcho-m1 as automation backend for OpenClaw agents.

---

## What is n8n?

**n8n** (pronounced "n-eight-n") is an open-source workflow automation tool designed for self-hosting. It provides a visual workflow editor similar to Zapier/Make but runs on your own infrastructure.

**Core capabilities:**
- Visual workflow builder with 1,500+ integrations
- Self-hostable (Docker, VPS, on-prem)
- Webhook triggers + API integrations
- Code nodes (JavaScript, Python)
- Database connectors (PostgreSQL, MySQL, MongoDB)
- Scheduling, conditionals, loops, data transformation
- MCP server support (native OpenClaw integration)

**License:** Fair-code (Apache 2.0 for self-hosted community edition)

---

## n8n vs Zapier Comparison (2026)

| Feature | Zapier | n8n (Self-Hosted) |
|---------|--------|-------------------|
| **Hosting** | Cloud-only SaaS | Self-host on VPS/on-prem + optional cloud |
| **Pricing** | Task-based ($29-$599/mo for 750-50K tasks) | Free (unlimited executions) + hosting cost |
| **Data control** | Zapier's cloud | Full sovereignty (behind firewall) |
| **Integrations** | 9,000+ apps | 1,500+ nodes |
| **Complexity** | Low (non-technical users) | Medium (developer-oriented) |
| **AI features** | AI orchestration suite | AI nodes + local LLM support (Ollama) |
| **Internal systems** | Public SaaS APIs only | Direct DB, private API, local services |
| **Code capability** | Limited code steps | Full JavaScript/Python nodes |
| **Version control** | No | Git integration, CI/CD |
| **Cost at 10K runs/mo** | ~$299/mo | ~$5-10/mo VPS |

**Verdict:** n8n is dramatically cheaper at scale, better for technical teams, and essential for self-hosting requirements.

---

## Cost Analysis

### Zapier Pricing (2026)
- Free: 100 tasks/month, 5 Zaps
- Starter: ~$30/mo for 750 tasks
- Professional: ~$299/mo for 10K tasks
- Team: ~$599/mo for 50K tasks

**Problem:** Multi-step workflows consume tasks quickly (5-step workflow × 1,000 runs = 5,000 tasks = $200-500/mo)

### n8n Self-Hosted (Community Edition)
- **License:** Free, unlimited executions
- **Hosting:** $5-10/mo VPS (Hetzner CPX21)
- **Total cost:** $5-10/mo for 10K-100K+ executions

**Savings:** 80-90% lower cost at scale

### Our Use Case
- Estimated monthly workflows: 1,000-5,000 executions
- Zapier equivalent: $200-300/mo
- n8n on honcho-m1: $0/mo (existing infrastructure)

**Annual savings:** $2,400-3,600

---

## Integration with OpenClaw (MCP)

n8n has **native MCP (Model Context Protocol) support**, enabling OpenClaw agents to:
1. Trigger n8n workflows via MCP tools
2. Build new workflows dynamically
3. Query workflow status and results
4. Integrate with internal systems via n8n

### Integration Pattern 1: n8n as MCP Server

**How it works:**
1. Create workflow in n8n with **MCP Server Trigger** node
2. Expose workflow as MCP tool
3. Register n8n MCP server in OpenClaw
4. Agents call workflows via MCP

**Example workflow:**
```
User: "Create a GitHub issue for this bug"
↓
OpenClaw → MCP call → n8n workflow
↓
n8n: GitHub API → create issue
↓
Return issue URL to OpenClaw
↓
Agent: "Issue created: https://github.com/..."
```

**OpenClaw config:**
```json
{
  "mcpServers": {
    "n8n": {
      "transport": "http",
      "url": "http://100.77.0.47:5678/mcp/openclaw-mcp",
      "headers": {
        "Authorization": "Bearer ${N8N_MCP_BEARER_TOKEN}"
      }
    }
  }
}
```

### Integration Pattern 2: n8n-claw (OpenClaw inside n8n)

**n8n-claw** is a community project that rebuilds OpenClaw's architecture inside n8n:
- Memory (Supabase/PostgreSQL)
- Web search (SearXNG)
- Skills library (MCP)
- Reminders, task management
- Expert sub-agents

**Benefits:**
- Self-contained agent stack in n8n
- Instance-level MCP (Claude Desktop, Cursor can connect)
- Self-expanding (agent builds new workflows)

**Not recommended for us:** We already have OpenClaw infrastructure; Pattern 1 is cleaner.

### Integration Pattern 3: Workflow Ops via MCP

**synta MCP** and **n8n-ops-mcp** turn AI agents into n8n specialists:
- List, inspect, validate workflows
- Static analysis and debugging
- Safe workflow editing
- Trigger execution

**Use case:** "AI DevOps for n8n" — agents maintain automation infrastructure.

---

## Deployment Architecture

### Recommended: honcho-m1 Deployment

**Rationale:**
- Centralized infrastructure node (already hosts MemPalace, Dropbox MCP)
- Tailscale-accessible (secure internal network)
- Existing PostgreSQL (can share with n8n)
- Docker Compose stack (consistent with Dropbox MCP)

**Stack:**
```
┌─────────────────────────────────────┐
│         honcho-m1 (100.77.0.47)     │
├─────────────────────────────────────┤
│  n8n (Docker)                       │
│  ├─ PostgreSQL                      │
│  ├─ Reverse proxy (Caddy/Traefik)  │
│  └─ Persistent volumes              │
├─────────────────────────────────────┤
│  MemPalace                          │
│  Dropbox MCP                        │
│  (existing services)                │
└─────────────────────────────────────┘
         ↓
    Tailscale
         ↓
┌────────────────┐  ┌────────────────┐
│ Bob (agent)    │  │ Mason (agent)  │
│ OpenClaw       │  │ OpenClaw       │
│ MCP client     │  │ MCP client     │
└────────────────┘  └────────────────┘
```

**Access:**
- Internal: `http://100.77.0.47:5678` (Tailscale)
- External: `https://n8n.ascendancy.group` (optional, behind reverse proxy)
- MCP endpoint: `http://100.77.0.47:5678/mcp/openclaw-mcp`

---

## Production Deployment Spec

### Docker Compose Stack

**Location:** `/home/pieter/docker/n8n/docker-compose.yml`

**Services:**
- n8n (workflow engine)
- PostgreSQL (database)
- Caddy (reverse proxy + HTTPS)
- Redis (optional, for queue mode)

**Key environment variables:**
```yaml
N8N_ENCRYPTION_KEY: <generated-secret>
N8N_HOST: 100.77.0.47
N8N_PROTOCOL: https
N8N_PORT: 5678
WEBHOOK_URL: https://n8n.ascendancy.group
DB_TYPE: postgresdb
DB_POSTGRESDB_HOST: postgres
DB_POSTGRESDB_DATABASE: n8n
N8N_METRICS: true
EXECUTIONS_MODE: regular  # or 'queue' for scaling
```

**Persistent volumes:**
```
/home/pieter/docker/n8n/
├── n8n-data/          # n8n config, credentials, workflows
├── postgres-data/     # PostgreSQL database
├── caddy-data/        # Caddy TLS certs
└── docker-compose.yml
```

**Resource requirements:**
- CPU: 1-2 cores
- RAM: 2-4 GB
- Disk: 10-20 GB (grows with execution history)

---

## Security Considerations

### Access Control
- **Internal only:** Bind to Tailscale IP (100.77.0.47) by default
- **External (optional):** HTTPS via Caddy with Basic Auth or OAuth
- **MCP access:** Bearer token authentication
- **Admin UI:** Restrict to authorized users (Bob, Pieter)

### Data Sovereignty
- All workflow data stays on honcho-m1 (no external SaaS)
- Credentials encrypted with N8N_ENCRYPTION_KEY
- Database backups include encrypted credentials

### Network Isolation
- n8n behind Tailscale (private network)
- PostgreSQL not exposed publicly
- Webhooks only accept signed/authenticated requests

### Secrets Management
- N8N_ENCRYPTION_KEY stored in 1Password
- MCP bearer token in 1Password
- Service credentials (GitHub, Slack, Dropbox) via n8n's credential store

---

## Use Cases for Ascendancy

### 1. GitHub Automation
**Workflow:** Issue triage + PR automation
- Trigger: GitHub webhook (new issue)
- Action: Label, assign, create project card
- Notify: Post to Slack #github-notifications

**Value:** Automated project management, reduced manual triage

---

### 2. Slack-to-GitHub Bridge
**Workflow:** Convert Slack thread → GitHub issue
- Trigger: Slack message with emoji reaction (:ticket:)
- Action: Create GitHub issue with thread context
- Response: Post issue link back to Slack

**Value:** Seamless issue tracking from chat

---

### 3. MemPalace Backup to Dropbox
**Workflow:** Weekly MemPalace backup upload
- Trigger: Schedule (Sunday 02:00 UTC)
- Action: Compress `/opt/mempalace/`, upload to Dropbox
- Notify: Post success/failure to Slack

**Value:** Automated off-server backups (complements systemd timer)

---

### 4. Agent Task Orchestration
**Workflow:** Multi-agent task coordination
- Trigger: OpenClaw MCP call
- Action: Route task to Bob/Mason/Forge based on type
- Response: Return task status to requester

**Value:** Dynamic agent delegation without hardcoded logic

---

### 5. Monitoring & Alerts
**Workflow:** Infrastructure health checks
- Trigger: Schedule (every 15 min)
- Action: Ping services (honcho-m1, testbed-m1), check disk usage
- Alert: Post to Slack if threshold exceeded

**Value:** Proactive monitoring, early failure detection

---

### 6. Document Processing Pipeline
**Workflow:** Dropbox → OCR → MemPalace
- Trigger: Dropbox webhook (new file in `/Inbox/`)
- Action: OCR image/PDF, extract text, file to MemPalace
- Cleanup: Move to `/Processed/`

**Value:** Automated document ingestion

---

### 7. Agent Deployment Pipeline
**Workflow:** Git push → deploy agent config
- Trigger: GitHub webhook (push to `ascendancy-governance`)
- Action: Pull changes, validate config, restart affected agents
- Notify: Post deployment status to Slack

**Value:** GitOps for agent configurations

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Deploy n8n on honcho-m1 (Docker Compose)
- [ ] Configure PostgreSQL database
- [ ] Set up Caddy reverse proxy (HTTPS)
- [ ] Verify admin UI accessible via Tailscale
- [ ] Create N8N_ENCRYPTION_KEY, store in 1Password
- [ ] Document deployment in `ascendancy-infra`

**Deliverables:**
- n8n running at `http://100.77.0.47:5678`
- Admin credentials in 1Password
- Runbook: `ascendancy-infra/docs/runbooks/n8n-deployment.md`

---

### Phase 2: MCP Integration (Week 2)
- [ ] Create test workflow with MCP Server Trigger
- [ ] Generate MCP bearer token
- [ ] Register n8n MCP server in Bob's OpenClaw config
- [ ] Test MCP call from Bob: "Trigger n8n test workflow"
- [ ] Document MCP integration in governance repo

**Deliverables:**
- Working MCP integration (Bob → n8n)
- Test workflow: "Echo MCP call"
- SOP: `ascendancy-governance/playbook/sops/SOP-17-n8n-workflows.md`

---

### Phase 3: Core Workflows (Week 3-4)
- [ ] Implement GitHub automation workflows
- [ ] Implement Slack-to-GitHub bridge
- [ ] Implement MemPalace backup to Dropbox
- [ ] Implement monitoring & alerts
- [ ] Test all workflows end-to-end

**Deliverables:**
- 4 production workflows operational
- Documentation for each workflow
- Alert channels configured (Slack #infra-alerts)

---

### Phase 4: Multi-Agent Rollout (Week 5)
- [ ] Register n8n MCP in Mason's OpenClaw config
- [ ] Register n8n MCP in Forge's OpenClaw config
- [ ] Register n8n MCP in Testbed's OpenClaw config
- [ ] Test agent task orchestration workflow
- [ ] Create workflow library (common patterns)

**Deliverables:**
- All agents can trigger n8n workflows
- Workflow library with 10+ reusable patterns
- Training session for agents (via documentation)

---

## Backup & Disaster Recovery

### n8n Backup Strategy

**Critical data:**
1. PostgreSQL database (workflows, credentials, execution history)
2. N8N_ENCRYPTION_KEY (decrypt credentials)
3. n8n-data volume (workflow files, settings)

**Backup approach:**
- **Daily:** PostgreSQL dump to `/opt/n8n-backups/`
- **Weekly:** PostgreSQL dump + tarball to Dropbox
- **Retention:** 30 days local, 90 days Dropbox

**Backup script:**
```bash
#!/bin/bash
# n8n daily backup
BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/opt/n8n-backups/daily-$BACKUP_DATE"
mkdir -p "$BACKUP_DIR"

# PostgreSQL dump
docker exec n8n-postgres pg_dump -U n8n n8n > "$BACKUP_DIR/n8n-postgres.sql"

# n8n data volume
docker cp n8n:/home/node/.n8n "$BACKUP_DIR/n8n-data"

# Encryption key (reference only, actual key in 1Password)
echo "N8N_ENCRYPTION_KEY stored in 1Password: AgentStack/n8n-encryption-key" > "$BACKUP_DIR/ENCRYPTION_KEY_REFERENCE.txt"

# Cleanup old backups
find /opt/n8n-backups -maxdepth 1 -type d -name "daily-*" -mtime +30 -exec rm -rf {} \;
```

**Systemd timer:**
- Schedule: 03:00 UTC daily
- Service: `n8n-backup.service`
- Timer: `n8n-backup.timer`

---

### Restore Procedure

**Scenario: n8n data loss**

```bash
# 1. Stop n8n
cd /home/pieter/docker/n8n
docker compose down

# 2. Restore PostgreSQL
BACKUP_DATE="2026-07-20"
cat "/opt/n8n-backups/daily-$BACKUP_DATE/n8n-postgres.sql" | \
  docker exec -i n8n-postgres psql -U n8n n8n

# 3. Restore n8n data
docker cp "/opt/n8n-backups/daily-$BACKUP_DATE/n8n-data" n8n:/home/node/.n8n

# 4. Verify encryption key
# Check docker-compose.yml has correct N8N_ENCRYPTION_KEY from 1Password

# 5. Restart n8n
docker compose up -d

# 6. Verify workflows
curl http://100.77.0.47:5678/healthz
```

**Recovery time:** 5-10 minutes

---

## Monitoring & Alerting

### Health Checks
- n8n health endpoint: `GET http://100.77.0.47:5678/healthz`
- PostgreSQL connection: `docker exec n8n-postgres pg_isready`
- Disk usage: `/opt/n8n-backups/` and docker volumes

### Metrics
- Workflow execution count (daily/weekly)
- Execution success/failure rate
- Average execution time
- Database size growth

### Alerts
- n8n unreachable (>5 min downtime)
- PostgreSQL connection failed
- Disk usage >80%
- Workflow failure rate >10%

**Alert channel:** Slack #infra-alerts

---

## Cost-Benefit Analysis

### Implementation Costs
- **Development time:** 4-5 weeks (40-50 hours)
- **Infrastructure:** $0 (honcho-m1 existing)
- **Maintenance:** 2-4 hours/month

### Annual Benefits
- **Cost savings:** $2,400-3,600/year (vs Zapier)
- **Automation efficiency:** 10-20 hours/month saved (manual tasks)
- **Agent capabilities:** Expanded automation surface (GitHub, Slack, Dropbox, monitoring)

**ROI:** Positive within 2-3 months

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| n8n complexity vs Zapier | Medium | Phased rollout, workflow library, documentation |
| Integration maintenance burden | Medium | Limit to stable APIs, monitor for breakage |
| Single point of failure (honcho-m1) | Medium | Daily backups, documented restore procedure |
| MCP schema changes | Low | OpenClaw gateway restart to refresh schema |
| Resource contention on honcho-m1 | Low | Monitor CPU/RAM, scale to dedicated server if needed |

---

## Decision: Deploy n8n on honcho-m1

**Rationale:**
1. **Cost savings:** $2,400-3,600/year vs Zapier
2. **OpenClaw integration:** Native MCP support enables agent-driven automation
3. **Data sovereignty:** Full control, on-prem deployment
4. **Internal system access:** Direct DB, API, file system access
5. **Existing infrastructure:** honcho-m1 has capacity, already hosts centralized services

**Next steps:**
1. Wait for Pieter approval
2. Execute Phase 1 deployment (Week 1)
3. Document deployment in `ascendancy-infra`
4. Begin Phase 2 MCP integration (Week 2)

---

## References

- **n8n official docs:** https://docs.n8n.io/
- **n8n GitHub:** https://github.com/n8n-io/n8n
- **n8n-claw (OpenClaw in n8n):** https://github.com/freddy-schuetz/n8n-claw
- **MCP Server Trigger docs:** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook
- **Docker deployment guide:** https://ciela.ai/blogs/how-to-deploy-n8n-on-docker-production

---

*Research complete: 2026-07-20 03:15 UTC*  
*Researcher: Testbed*  
*Approval required: Pieter van der Wal*

# Honcho Upgrade: v3.0.6 → v3.0.12

**Date:** 2026-07-20  
**Server:** honcho-m1 (100.77.0.47)  
**Snapshot:** ✅ `Honch01-M1-Pre-MemPalace & Honcho upgrade-07-20-2026` (covers both upgrades)

---

## Pre-Upgrade Status

**Current Version:** v3.0.6 (commit 58f9abba)  
**Target Version:** v3.0.12 (commit 055d73b5)  
**Version Gap:** 113 commits, 6 minor versions

**Deployment:** Docker Compose on honcho-m1  
**Data Location:** Docker volumes  
- PostgreSQL: `/var/lib/docker/volumes/honcho_pgdata/_data` (61 MB)
- Redis: `/var/lib/docker/volumes/honcho_redis-data/_data`

**Current Services:**
- honcho-api-1: Up 17 min (healthy)
- honcho-database-1: Up 2 months (healthy)
- honcho-deriver-1: Up 13 hours (unhealthy)
- honcho-redis-1: Up 2 months (healthy)

---

## Key Changes v3.0.6 → v3.0.12

**v3.0.7:**
- OpenAI tool_choice fallback fixes (#850)
- LLM client capture fixes (#849)

**v3.0.8:**
- Namespace correlation for Sentry monitoring (#870)

**v3.0.9:**
- Exact content deduplication (#861)
- SDK updates

**v3.0.10:**
- Dreamer specialist output improvements (#894)

**v3.0.11:**
- CloudEvents + Langfuse tracing (#845)
- Prometheus metrics (in-flight tracking)

**v3.0.12:**
- Redis cluster support (#905)
- Stability improvements

**Priority:** Moderate (observability + stability improvements, no critical security patches)

---

## Upgrade Procedure

### Phase 1: Backup PostgreSQL Data

```bash
ssh pieter@100.77.0.47

# Stop API to prevent writes during backup
cd ~/honcho
docker compose stop api deriver

# Backup PostgreSQL
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker compose exec -T database pg_dumpall -U postgres > ~/honcho-backups/honcho-postgres-$TIMESTAMP.sql

# Verify backup
ls -lh ~/honcho-backups/honcho-postgres-$TIMESTAMP.sql

# Backup docker-compose.yml and .env
mkdir -p ~/honcho-backups/config-$TIMESTAMP
cp docker-compose.yml .env ~/honcho-backups/config-$TIMESTAMP/
```

### Phase 2: Pull Latest Code

```bash
cd ~/honcho

# Pull latest from upstream
git fetch
git status

# Check for local changes
git diff

# If clean, checkout v3.0.12
git checkout v3.0.12
git status
```

### Phase 3: Rebuild Containers

```bash
# Rebuild with new code
docker compose build --no-cache

# Verify build success
docker compose images
```

### Phase 4: Restart Services

```bash
# Start database and redis first
docker compose up -d database redis

# Wait for healthy
sleep 10
docker compose ps

# Start API and deriver
docker compose up -d api deriver

# Check health
docker compose ps
docker compose logs --tail 50 api
```

### Phase 5: Verify Honcho Access

```bash
# Test health endpoint
curl -s http://100.77.0.47:8000/health | jq '.'

# Test from testbed
python3 ~/.openclaw/workspace/scripts/honcho-integration/honcho_client.py health
```

### Phase 6: Functional Testing

```bash
# On testbed
python3 ~/.openclaw/workspace/scripts/honcho-integration/honcho_client.py get-context

# Expected: Returns workspace and peer info
```

### Phase 7: Post-Upgrade Snapshot

**Via Hetzner Console (if needed separately):**
- Name: `post-honcho-upgrade-2026-07-20-HHMM`

*(Or rely on combined post-MemPalace snapshot if taken after both upgrades)*

---

## Rollback Procedure

**If upgrade fails:**

```bash
# 1. Stop services
cd ~/honcho
docker compose down

# 2. Checkout old version
git checkout v3.0.6

# 3. Rebuild old containers
docker compose build --no-cache

# 4. Restore PostgreSQL backup (if needed)
cat ~/honcho-backups/honcho-postgres-TIMESTAMP.sql | docker compose exec -T database psql -U postgres

# 5. Start services
docker compose up -d

# 6. Verify
curl http://100.77.0.47:8000/health

# 7. Restore from Hetzner snapshot if needed
# (Via Hetzner console - Pieter)
```

---

## Success Criteria

- ✅ `git describe --tags` reports v3.0.12
- ✅ All containers healthy (database, redis, api)
- ✅ Health endpoint returns 200
- ✅ Honcho client can connect from testbed
- ✅ No errors in container logs
- ✅ Post-upgrade snapshot created (or combined snapshot confirmed)

---

## Known Risks

**1. Deriver Currently Unhealthy**
- Status: Up 13 hours but marked unhealthy
- Risk: May remain unhealthy after upgrade if underlying issue persists
- Mitigation: Document current state, investigate post-upgrade if still unhealthy

**2. Database Migration**
- Risk: Schema changes may require migrations
- Mitigation: PostgreSQL backup taken before upgrade

**3. Container Rebuild**
- Risk: `--no-cache` rebuild takes longer (~5-10 min)
- Mitigation: API downtime acceptable for testbed environment

---

## Estimated Timeline

| Phase | Duration |
|-------|----------|
| Backup PostgreSQL | 2 min |
| Pull latest code | 1 min |
| Rebuild containers | 8 min |
| Restart services | 2 min |
| Verify access | 2 min |
| Functional testing | 2 min |
| Post-upgrade snapshot | 3 min |
| **Total** | **20 min** |

---

## Status: Ready to Execute

**Blocker:** None  
**Snapshot:** ✅ Confirmed (covers both MemPalace + Honcho)  
**Backup Plan:** ✅ Documented  
**Procedure:** ✅ Documented

**Awaiting:** Go-ahead from Pieter

---

*Prepared by: Testbed*  
*Date: 2026-07-20 14:05 CDT*

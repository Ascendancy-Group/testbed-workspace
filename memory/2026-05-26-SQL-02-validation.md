# SQL-02: Retrieval Tool Validation — Testbed
*Date: 2026-05-26 16:54 CDT*
*Ticket: https://github.com/Ascendancy-Group/ascendancy-testing/issues/32*

## Summary

Tested OpenClaw's memory retrieval tools (`memory_search` and `memory_get`) to validate end-to-end functionality.

## Test Results

### memory_search

**Test 1: Known term search ("bootstrap size limits")**
- Query: `bootstrap size limits configuration`
- Results: 3 hits
- Top result: MEMORY.md (score: 0.81)
- Search time: 5.2s (first run)
- Verdict: ✅ **PASS**

**Test 2: Recent work search ("QW-03")**
- Query: `QW-03 implementation complete Bob testbed`
- Results: 3 hits
- Top result: MEMORY.md, SQL-01 audit doc
- Search time: 68ms (cached)
- Verdict: ✅ **PASS**

**Findings:**
- Text-based FTS5 search working correctly
- Result ranking sensible (0.74-0.81 scores)
- Performance varies: 68ms-5.2s (cache-dependent)
- Only searches indexed files (SQLite database)

---

### memory_get

**Test 3: Retrieve from MEMORY.md**
- Path: `MEMORY.md`
- Lines: 1-10
- Result: Exact match ✅
- Truncation indicator: Present ✅
- Verdict: ✅ **PASS**

**Test 4: Retrieve from today's audit**
- Path: `memory/2026-05-26-SQL-01-audit.md`
- Lines: 1-15
- Result: Exact match ✅ (file NOT in SQLite yet)
- Verdict: ✅ **PASS**

**Test 5: Nonexistent file**
- Path: `memory/nonexistent-file.md`
- Result: Empty text, graceful handling ✅
- Verdict: ✅ **PASS**

**Findings:**
- `memory_get` reads files DIRECTLY from workspace
- Does NOT require files to be in SQLite index
- Works on brand-new files written today
- Graceful error handling

---

## Key Insight

**memory_search vs memory_get:**

| Tool | Backend | Speed | Coverage |
|------|---------|-------|----------|
| **memory_search** | SQLite FTS5 | 68ms-5s | Indexed files only |
| **memory_get** | Direct filesystem | Instant | All workspace files |

**memory_get bypasses SQLite** - it's a direct file reader, not a database query. This is why it works on files written today (not yet indexed).

---

## Recommendations

1. **Use memory_search for discovery** - find relevant context across all indexed history
2. **Use memory_get for exact retrieval** - pull specific lines once you know the path
3. **Indexing cadence** - files may not be indexed immediately (today's docs not yet in SQLite)
4. **No action needed** - both tools working as designed ✅

---

## Next

**HR-01:** Add context injection hard rule to AGENTS.md

---

*Validation complete. Both tools working correctly.*

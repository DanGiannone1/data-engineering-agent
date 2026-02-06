# AI Data Engineering Agent - Cost Analysis

**Version:** 3.0
**Date:** February 6, 2026
**Baseline Scenario:** ~1,250 runs/month (3,000 clients × 5 runs/year)

---

## Executive Summary

This cost analysis provides detailed projections for running the AI Data Engineering Agent at realistic production volumes. Based on customer estimates from the January 30, 2026 call, the baseline is **~1,250 runs/month** — significantly higher than our initial v2.0 estimate of 100 runs/month.

### Cost Summary

| Scenario | Volume | Cache Hit | Monthly | Quarterly | Annual |
|----------|--------|-----------|---------|-----------|--------|
| **POC Pilot** (limited) | 50 runs/month | 0% | **$256** | **$768** | **$3,072** |
| **Cold Start Q1** (full volume) | 1,250 runs/month | 0% | **$2,746** | **$8,238** | — |
| **Steady State** (post-Q1) | 1,250 runs/month | 60% | **$2,613** | **$7,839** | **$31,356** |
| **Steady State (optimized)** | 1,250 runs/month | 70% | **$1,269** | **$3,807** | **$15,228** |
| **Busy Season Peak** | 1,500 runs/month | 50% | **$3,183** | **$9,549** | — |

**Key Insight:** At realistic volumes (~1,250 runs/month), the dominant cost is **Databricks Spark compute** (60-70% of total). LLM costs remain a minor line item. The first quarter cold start (0% cache hits) will be the most expensive period, after which costs drop significantly as the cache builds.

## Cost Assumptions

**Platform Decisions:**
- **Big Data Processing:** Azure Databricks (Jobs Compute — per-job pricing)
- **AI Agent Runtime:** Azure Durable Functions + **Microsoft Agent Framework** (customer's existing tech stack)
- **LLM Backend:** Azure OpenAI (GPT-4o for complex analysis, GPT-4o-mini for simple tasks) — **no platform fee**, pure per-token consumption
- **Agent State + Code Cache + Audit Trail:** Cosmos DB serverless (3 containers: code-cache, agent-state, audit-trail)
- **Approved Code:** Cosmos DB (Sprint 1) / ADO Repos (future sprint)
- **Audit Archive:** ADLS Gen2 immutable storage (WORM policy for legal hold)

**Key Cost Drivers:**
1. **Azure Databricks:** Per-job Spark compute (~60-70% of total cost at production volume)
2. **Agent Runtime (Durable Functions):** Hosting the agent process (~15-25%)
3. **Azure OpenAI tokens:** LLM calls for profiling, pseudocode, PySpark generation (~3-10%)
4. **Cosmos DB:** Code cache + agent thread state + audit trail
5. **ADLS Gen2:** Immutable audit archive

---

## Azure Pricing (2026)

### Agent Runtime: Azure Durable Functions (Premium Plan)

- **Minimum instances:** 1 pre-warmed instance ($0.173/vCPU-hour)
- **Execution charges:** $0.000016/GB-s
- **Monthly cost:** ~$125-250 depending on utilization
- **Why Durable Functions:** Already in customer's tech stack, provides native durable orchestration for human-in-the-loop workflows (agent pauses at review checkpoints, resumes on auditor response), avoids introducing new services per CTO guardrails

### Azure OpenAI (LLM Backend)
**No platform fee** — pure per-token consumption.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| **GPT-4o** | $5.00 | $15.00 | Complex analysis, pseudocode generation |
| **GPT-4o-mini** | $0.15 | $0.60 | Data profiling, cache lookups, simple validation |
| **GPT-5.2** (if used) | ~$5.00 | ~$14.00 | Higher quality, similar pricing to GPT-4o |

**Token Usage Per Transformation (estimated):**

| Phase | Model | Input Tokens | Output Tokens | Cost |
|-------|-------|-------------|---------------|------|
| Data profiling | GPT-4o-mini | ~2,000 | ~1,000 | $0.001 |
| Pseudocode generation | GPT-4o | ~5,000 | ~3,000 | $0.070 |
| Human feedback iteration (avg 1 round) | GPT-4o | ~3,000 | ~2,000 | $0.055 |
| PySpark code generation | GPT-4o-mini | ~4,000 | ~5,000 | $0.004 |
| Integrity check analysis | GPT-4o-mini | ~3,000 | ~1,000 | $0.001 |
| **Total per new transformation** | | | | **~$0.13** |

**Note:** Using GPT-4o-mini for PySpark code generation (from already-approved pseudocode) significantly reduces cost vs. v2.0 estimate of $0.22/transform. The hard reasoning work is in pseudocode generation; code gen from pseudocode is mechanical.

**Monthly LLM Costs:**

| Runs/Month | Cache Hit Rate | New Transforms | LLM Cost/Month |
|------------|---------------|----------------|----------------|
| 50 | 0% | 50 | **$6.50** |
| 1,250 | 0% (cold start) | 1,250 | **$162.50** |
| 1,250 | 60% | 500 | **$65.00** |
| 1,250 | 70% | 375 | **$48.75** |
| 1,500 | 50% | 750 | **$97.50** |

### Azure Databricks (Jobs Compute)
- **DBU cost:** $0.15 per DBU-hour (Jobs Compute — cheapest tier)
- **VM cost:** Standard_DS3_v2 at $0.27/hour per node
- **Cluster config:** 3-node (1 driver + 2 workers), 6 DBUs/hour total
- **All-in hourly rate:** $1.71/hour ($0.90 DBU + $0.81 VMs)
- **Spot instances:** 40-80% discount on worker VMs (reduces to ~$0.69/hour)
- **Key advantage:** Pay only when jobs run — no idle capacity charges

**Important:** All runs require Spark execution — including cache hits (which skip AI processing but still run the cached PySpark code). The Databricks cost scales with **total runs**, not just cache misses.

### Microsoft Agent Framework
- **Platform fee:** $0 (open-source SDK, MIT license)

### Azure Cosmos DB (Serverless)
- **RU cost:** $0.25 per 1M RUs
- **Storage:** $0.25 per GB/month
- **Estimated:** $5-25/month depending on volume

### Azure Data Lake Storage Gen2 (Hot Tier)
- **Storage:** $0.0184 per GB/month
- **Transactions:** $0.004-0.05 per 10K operations
- **Estimated:** ~$85-300/month depending on volume

### ADLS Gen2 Immutable Storage (Audit Archive)
- **Storage:** $0.018 per GB/month (WORM policy — no additional cost over hot tier)
- **Estimated:** ~$10-20/month
- **Purpose:** Legal hold archive for code snapshots, execution logs, and approval records

---

## Detailed Cost Scenarios

### Scenario 1: POC Pilot (50 runs/month, 0% cache hit)

**Context:** Initial POC with 3-4 test engagements, limited volume

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $125 | Premium plan, minimal instances |
| ADLS Gen2 | $20 | Small storage footprint |
| Azure OpenAI (LLM) | $7 | 50 new transforms × $0.13 |
| Azure Databricks | $86 | 50 jobs × 1hr × $1.71/hr |
| Cosmos DB (cache + state + audit) | $8 | Serverless, 3 containers, minimal volume |
| ADLS Immutable Archive | $10 | WORM-protected audit archive |
| Azure Synapse (serverless SQL) | $2 | ~$5/TB queried; minimal POC volume |
| **Total** | **$258/month** | |

---

### Scenario 2: Cold Start Q1 (1,250 runs/month, 0% cache hit)

**Context:** First quarter at full volume — every transformation is new. No existing PySpark to migrate (current system uses Spark notebooks + M code/Power Query).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $200 | Higher utilization |
| ADLS Gen2 | $200 | 1,250 clients × ~8GB I/O |
| Azure OpenAI (LLM) | $163 | 1,250 new transforms × $0.13 |
| **Azure Databricks** | **$2,138** | **1,250 jobs × 1hr × $1.71/hr** |
| Cosmos DB (cache + state + audit) | $30 | Building cache + high audit write volume |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| Azure Synapse (serverless SQL) | $25 | ~$5/TB queried; 1,250 runs × ~4MB avg |
| **Total** | **$2,771/month** | |
| **3-Month Cold Start** | **$8,313** | |

**Per-run cost:** $2,771 / 1,250 = **$2.22/run** (vs. $800 manual = **99.7% reduction**)

**With Spot instances** (60% discount on Databricks workers): Total drops to ~$1,495/month

---

### Scenario 3: Steady State (1,250 runs/month, 60% cache hit)

**Context:** Post-Q1 once cache is partially built. 60% of runs are cache hits (skip AI processing, still execute PySpark on Spark).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $175 | Moderate utilization |
| ADLS Gen2 | $200 | Same I/O volume |
| Azure OpenAI (LLM) | $65 | 500 new transforms × $0.13 |
| **Azure Databricks** | **$2,138** | **1,250 jobs × 1hr × $1.71/hr** (all runs need Spark) |
| Cosmos DB (cache + state + audit) | $20 | Mature cache, mostly reads + audit writes |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| Azure Synapse (serverless SQL) | $25 | ~$5/TB queried |
| **Total** | **$2,638/month** | |
| **Quarterly** | **$7,914** | |
| **Annual** | **$31,656** | |

**Per-run cost:** $2,638 / 1,250 = **$2.11/run**

**Note:** Cache hits save LLM costs ($65/month savings per 10% cache improvement) but NOT Spark costs — all runs execute PySpark regardless.

---

### Scenario 3b: Steady State Optimized (Spot instances + 70% cache)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $150 | Optimized scaling |
| ADLS Gen2 | $180 | Lifecycle management |
| Azure OpenAI (LLM) | $49 | 375 new transforms × $0.13 |
| **Azure Databricks (Spot)** | **$863** | **1,250 jobs × 1hr × $0.69/hr** |
| Cosmos DB (cache + state + audit) | $15 | Mature cache + steady audit |
| ADLS Immutable Archive | $12 | WORM-protected audit archive |
| Azure Synapse (serverless SQL) | $25 | ~$5/TB queried |
| **Total** | **$1,294/month** | |
| **Quarterly** | **$3,882** | |
| **Annual** | **$15,528** | |

**Per-run cost:** $1,294 / 1,250 = **$1.04/run**

**Spot instances are the single biggest cost lever** — reducing Databricks from $2,138 to $863/month (60% savings on Spark compute).

---

### Scenario 4: Busy Season Peak (1,500 runs/month, 50% cache hit)

**Context:** February-April peak load (3 months/year)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $225 | Near capacity |
| ADLS Gen2 | $250 | Higher I/O |
| Azure OpenAI (LLM) | $98 | 750 new transforms × $0.13 |
| **Azure Databricks** | **$2,565** | **1,500 jobs × 1hr × $1.71/hr** |
| Cosmos DB (cache + state + audit) | $30 | High volume + audit |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| Azure Synapse (serverless SQL) | $30 | ~$5/TB queried; higher volume |
| **Total** | **$3,213/month** | |
| **3-Month Busy Season** | **$9,639** | |

**With Spot instances:** ~$1,690/month (total), $5,070/quarter

---

## Annual Cost Projections

### Year 1 (Building Cache)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (cold start) | 1,250 | 0% | $2,746 | $8,238 |
| Q2 (cache building) | 1,250 | 40% | $2,670 | $8,010 |
| Q3 (maturing) | 1,250 | 60% | $2,613 | $7,839 |
| Q4 (optimized) | 1,250 | 70% | $2,580 | $7,740 |
| **Year 1 Total** | | | | **$31,827** |

**With Spot instances throughout Year 1: ~$16,300**

### Year 2+ (Steady State)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (busy season) | 1,500 | 50% | $3,183 | $9,549 |
| Q2 | 1,250 | 70% | $2,580 | $7,740 |
| Q3 | 1,250 | 75% | $2,555 | $7,665 |
| Q4 | 1,250 | 75% | $2,555 | $7,665 |
| **Year 2 Total** | | | | **$32,619** |

**With Spot instances: ~$16,800/year**

---

## Why Databricks Over Fabric

### For 1,250 runs/month with 60% cache hit rate:

| Platform | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| **Azure Databricks (Jobs Compute)** | **$2,613** | **$31,356** | **Pay-per-job, scales with usage** |
| **Azure Databricks (Spot)** | **$1,269** | **$15,228** | **60% VM discount** |
| Microsoft Fabric (F8 Reserved) | $765 fixed + overage | $15,000+ | May need F16+ for this volume |
| Microsoft Fabric (F16 Reserved) | $1,251 fixed | $15,012 | Competitive at high volume |

**At 1,250 runs/month, Fabric F16 becomes competitive** with Spot-optimized Databricks. However, Databricks is preferred because:
1. Customer already uses Databricks (no new service)
2. Per-job cost transparency (attribute costs per client)
3. Spot instances give 60% discount on workers
4. Autoscaling (1-5 workers) matches variable job sizes
5. No capacity management overhead

**Recommendation:** Databricks with Spot instances for Year 1. Evaluate Fabric if customer consolidates to Azure-native stack in Year 2+.

---

## LLM Model Options

### GPT-4o vs. GPT-5.2

Monty's POC uses GPT-5.2 ($14/M output tokens). Our design uses GPT-4o ($15/M output) for complex tasks and GPT-4o-mini ($0.60/M output) for code generation.

| Approach | Cost per New Transform | Monthly LLM at 500 new | Notes |
|----------|----------------------|----------------------|-------|
| **GPT-4o + GPT-4o-mini (mixed)** | **$0.13** | **$65** | Pseudocode with 4o, code gen with mini |
| GPT-4o only | $0.22 | $110 | Higher quality, higher cost |
| GPT-5.2 only | ~$0.20 | $100 | Monty's current model |
| GPT-5.2 + GPT-4o-mini (mixed) | ~$0.12 | $60 | 5.2 for pseudocode, mini for code gen |

**Recommendation:** Use the best available model for pseudocode generation (where reasoning matters), and a cheaper model for PySpark code generation from approved pseudocode (mechanical translation). This saves 40-50% on LLM costs.

---

## Cost Optimization Strategies

### 1. Spot Instances (Biggest Lever)
**Impact:** 60% discount on Databricks worker VMs

```
Standard: 1,250 jobs × $1.71/hr = $2,138/month
Spot:     1,250 jobs × $0.69/hr = $863/month
Savings:  $1,275/month ($15,300/year)
```

**Risk:** Jobs may be interrupted (rare for 1-hour jobs). Use spot for workers, on-demand for driver.

### 2. Maximize Cache Hit Rates
**Impact:** Each 10% cache improvement saves ~$13/month in LLM costs

At 1,250 runs/month:
| Cache Hit Rate | New Transforms | LLM Cost |
|----------------|----------------|----------|
| 0% | 1,250 | $163/month |
| 50% | 625 | $81/month |
| 60% | 500 | $65/month |
| 70% | 375 | $49/month |
| 80% | 250 | $33/month |

**Note:** Cache hits save LLM costs but not Spark costs (all runs execute PySpark).

### 3. Right-Size Clusters
- Use autoscaling (1-5 workers) based on data volume
- Small jobs (1-3 GB): 2-node cluster ($1.14/hr)
- Large jobs (7-10 GB): 4-node cluster ($2.28/hr)
- **Potential savings:** 15-25% on Databricks costs

### 4. Model Tiering
- GPT-4o-mini for PySpark code generation (mechanical from pseudocode)
- GPT-4o for pseudocode generation (requires reasoning)
- **Savings:** ~40% on LLM costs vs. using GPT-4o for everything

### 5. Batch Processing
- Group multiple small clients into single Spark session
- Process overnight during off-peak hours
- **Potential savings:** 10-20% on Spark startup overhead

### 6. ADLS Lifecycle Management
- Move old data to Cool tier after 30 days
- Archive after 90 days
- **Potential savings:** 50-80% on storage for historical data

---

## ROI Analysis

### Cost Savings vs. Manual Process

**Assumptions:**
- Manual data engineering: 8 hours per client onboarding
- Specialist salary: $100/hour fully loaded
- Manual cost per client: $800

**Annual Comparison:**

| | Manual Process | Agent (Standard) | Agent (Spot Optimized) |
|--|----------------|-------------------|----------------------|
| 15,000 runs/year | $12,000,000 | $31,827 | $16,300 |
| Cost per run | $800 | $2.12 | $1.09 |
| **Savings** | — | **99.7%** | **99.9%** |

**Annual savings:** $11.97M (standard) to $11.98M (optimized) — infrastructure cost is negligible vs. labor

**ROI:** Infrastructure cost is negligible compared to labor savings.

---

## Risk Factors

### 1. Cold Start Cost Spike
**Risk:** Q1 at 0% cache hits = $2,746/month (vs. $2,613 steady state)
**Impact:** Moderate — only $133/month difference; LLM is a small portion of total cost
**Mitigation:** Spot instances bring Q1 cost to ~$1,470/month

### 2. Spark Processing Takes Longer
**Risk:** Jobs average 1.5 hours instead of 1 hour
**Impact:** +50% on Databricks costs (+$1,069/month standard, +$432/month spot)
**Mitigation:** Autoscaling, larger clusters for big datasets, batch processing

### 3. LLM Costs Higher Than Estimated
**Risk:** Complex transformations need more tokens or feedback iterations
**Impact:** Even 3x token usage only adds ~$130/month at 60% cache hit
**Mitigation:** Model tiering (mini for simple tasks), cache warming

### 4. Databricks Cost Transparency
**Risk:** Hard to attribute Spark costs per client
**Mitigation:** Job tagging in Databricks, cost allocation by client_id

---

## Summary

### Realistic Production Costs (1,250 runs/month):

| Configuration | Monthly | Annual |
|--------------|---------|--------|
| Standard (60% cache, on-demand) | $2,638 | $31,656 |
| **Optimized (70% cache, Spot)** | **$1,294** | **$15,528** |
| Aggressive (80% cache, Spot, right-sized) | $1,055 | $12,660 |

### Per-Run Cost:

| Configuration | Cost per Run | vs. $800 Manual |
|--------------|-------------|-----------------|
| Standard | $2.11 | **99.7% reduction** |
| Optimized | $1.04 | **99.9% reduction** |

### Cost Distribution (Steady State, Standard):

| Component | % of Total | Monthly |
|-----------|-----------|---------|
| Azure Databricks | **81%** | $2,138 |
| ADLS Gen2 | 8% | $200 |
| Agent Runtime (Durable Functions) | 7% | $175 |
| Azure OpenAI | 2% | $65 |
| Azure Synapse (serverless SQL) | 1% | $25 |
| Cosmos DB (cache + state + audit) + ADLS Archive | 1% | $35 |

**Databricks is the dominant cost.** Spot instances are the single most impactful optimization lever. Synapse serverless SQL adds minimal cost (~$5/TB queried, pay-per-use).

---

*This cost analysis reflects realistic production volumes from the January 30, 2026 customer call. Will be updated as POC data becomes available.*

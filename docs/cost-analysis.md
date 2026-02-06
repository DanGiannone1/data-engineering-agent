# AI Data Engineering Agent - Cost Analysis

**Version:** 3.3
**Date:** February 6, 2026
**Baseline Scenario:** ~1,250 runs/month (3,000 clients x 5 runs/year)

---

## Executive Summary

This cost analysis provides detailed projections for running the AI Data Engineering Agent at realistic production volumes. Based on customer estimates from the January 30, 2026 call, the baseline is **~1,250 runs/month** — significantly higher than our initial v2.0 estimate of 100 runs/month.

### Cost Summary

| Scenario | Volume | Cache Hit | Monthly | Quarterly | Annual |
|----------|--------|-----------|---------|-----------|--------|
| **POC Pilot** (limited) | 50 runs/month | 0% | **$232** | **$696** | **$2,784** |
| **Cold Start Q1** (full volume) | 1,250 runs/month | 0% | **$5,180** | **$15,540** | — |
| **Steady State** (post-Q1) | 1,250 runs/month | 60% | **$3,595** | **$10,785** | **$43,140** |
| **Steady State (optimized)** | 1,250 runs/month | 70% | **$2,690** | **$8,070** | **$32,280** |
| **Busy Season Peak** | 1,500 runs/month | 50% | **$4,640** | **$13,920** | — |

**Key Insight:** At realistic volumes (~1,250 runs/month) and 400K input / 100K output tokens per transformation, the two dominant costs are **Databricks Spark compute** (~62%) and **Azure OpenAI LLM** (~29%). Maximizing cache hit rates is the most impactful lever — each 10% improvement saves ~$263/month in LLM costs. Spot instances provide additional savings (~27%) on Spark compute.

## Cost Assumptions

**Platform Decisions:**
- **Big Data Processing:** Azure Databricks (Jobs Compute — per-job pricing)
- **AI Agent Runtime:** Azure Durable Functions + **Microsoft Agent Framework** (customer's existing tech stack)
- **LLM Backend:** Azure OpenAI (GPT-5.2) — **no platform fee**, pure per-token consumption
- **Approved Code + Agent State + Audit Trail:** Cosmos DB serverless (3 containers: approved-code, agent-state, audit-trail)
- **Approved Code Repository:** Cosmos DB (Sprint 1) / ADO Repos (future sprint)
- **Audit Archive:** ADLS Gen2 immutable storage (WORM policy for legal hold)
- **Output Destination:** Azure Synapse Analytics dedicated SQL pool (existing customer infrastructure — no incremental cost)

**Key Cost Drivers:**
1. **Azure Databricks:** Per-job Spark compute (~62% of total cost at steady state)
2. **Azure OpenAI tokens:** LLM calls for profiling, pseudocode, PySpark generation (~29%)
3. **ADLS Gen2:** Data storage and I/O (~6%)
4. **Agent Runtime (Durable Functions):** Hosting the agent process (~2%)
5. **Cosmos DB + Audit Archive:** Minor line items (~1%)

---

## Azure Pricing (2026)

### Agent Runtime: Azure Durable Functions

**Consumption Plan (Y1) — used for POC:**
- **Executions:** $0.20 per million (first 1M/month free)
- **Duration:** $0.000016/GB-s (first 400K GB-s/month free)
- **POC cost:** Effectively **$0/month** at 50 runs — well within free grants
- **Note:** Orchestrator replays count as separate invocations; Azure Storage transactions for state persistence billed separately

**Premium Plan (EP1) — for production:**
- **Instance cost:** $0.084/hour (~$61/month for 1 always-on instance)
- **Includes:** Unlimited executions, no orchestrator replay charges, VNet integration, pre-warmed instances
- **Monthly cost:** ~$61-120 depending on scaling (1-2 EP1 instances)

**Why Durable Functions:** Already in customer's tech stack, provides native durable orchestration for human-in-the-loop workflows (agent pauses at review checkpoints, resumes on auditor response), avoids introducing new services per CTO guardrails

### Azure OpenAI (LLM Backend)
**No platform fee** — pure per-token consumption.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|----------------------|------------------------|-------|
| **GPT-5.2** | $1.75 | $14.00 | All phases — pseudocode, code gen, profiling |

**Token Usage Per Transformation (estimated):**

| Phase | Input Tokens | Output Tokens | Cost |
|-------|-------------|---------------|------|
| Data profiling | ~50,000 | ~10,000 | $0.23 |
| Pseudocode generation | ~150,000 | ~40,000 | $0.82 |
| Human feedback iteration (avg 1 round) | ~80,000 | ~20,000 | $0.42 |
| PySpark code generation | ~80,000 | ~25,000 | $0.49 |
| Integrity check analysis | ~40,000 | ~5,000 | $0.14 |
| **Total per new transformation** | **~400,000** | **~100,000** | **~$2.10** |

**Monthly LLM Costs:**

| Runs/Month | Cache Hit Rate | New Transforms | LLM Cost/Month |
|------------|---------------|----------------|----------------|
| 50 | 0% | 50 | **$105** |
| 1,250 | 0% (cold start) | 1,250 | **$2,625** |
| 1,250 | 60% | 500 | **$1,050** |
| 1,250 | 70% | 375 | **$788** |
| 1,500 | 50% | 750 | **$1,575** |

### Azure Databricks (Jobs Compute)
- **DBU cost:** $0.15 per DBU-hour (Jobs Compute, Standard tier)
- **VM cost:** Standard_DS3_v2 at $0.293/hour per node
- **Cluster config:** 3-node (1 driver + 2 workers), 6 DBUs/hour total
- **All-in hourly rate:** $1.78/hour ($0.90 DBU + $0.88 VMs)
- **Spot instances:** ~80% discount on worker **VMs only** (DBU charges are not discounted)
  - Driver on-demand: $0.293/hr + Workers Spot: 2 x $0.054/hr = $0.108/hr + DBU: $0.90/hr
  - **Spot all-in rate: $1.30/hour** (27% savings vs on-demand)
- **Key advantage:** Pay only when jobs run — no idle capacity charges

**Important:** All runs require Spark execution — including approved code reruns (which skip AI processing but still run the PySpark). Databricks cost scales with **total runs**, not just new transforms.

> **Standard tier retirement notice:** Azure Databricks Standard tier retires **October 1, 2026** (no new Standard workspaces after April 1, 2026). After retirement, Premium tier DBU rate of $0.30/DBU-hr applies — doubling the DBU component from $0.90 to $1.80/hr. All estimates below use Standard tier pricing. See Risk Factors for Premium tier impact.

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

### Azure Synapse Analytics (Dedicated SQL Pool)
- **Cost:** $0 incremental — existing customer infrastructure already in production
- **Purpose:** Output destination for transformed data (loaded into existing tables)

---

## Detailed Cost Scenarios

### Scenario 1: POC Pilot (50 runs/month, 0% cache hit)

**Context:** Initial POC with 3-4 test engagements, limited volume

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $0 | Consumption plan — within free grants at POC volume |
| ADLS Gen2 | $20 | Small storage footprint |
| Azure OpenAI (LLM) | $105 | 50 new transforms x $2.10 |
| Azure Databricks | $89 | 50 jobs x 1hr x $1.78/hr |
| Cosmos DB (serverless) | $8 | 3 containers, minimal volume |
| ADLS Immutable Archive | $10 | WORM-protected audit archive |
| **Total** | **$232/month** | |

---

### Scenario 2: Cold Start Q1 (1,250 runs/month, 0% cache hit)

**Context:** First quarter at full volume — every transformation is new. No existing PySpark to migrate (current system uses Spark notebooks + M code/Power Query).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $85 | EP1 Premium, some scaling headroom |
| ADLS Gen2 | $200 | 1,250 clients x ~8GB I/O |
| **Azure OpenAI (LLM)** | **$2,625** | **1,250 new transforms x $2.10** |
| **Azure Databricks** | **$2,225** | **1,250 jobs x 1hr x $1.78/hr** |
| Cosmos DB (serverless) | $30 | Building approved code store + high audit write volume |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$5,180/month** | |
| **3-Month Cold Start** | **$15,540** | |

**Per-run cost:** $5,180 / 1,250 = **$4.14/run** (vs. $800 manual = **99.5% reduction**)

**With Spot instances** (driver on-demand, workers ~80% discount): Total drops to ~$4,580/month

---

### Scenario 3: Steady State (1,250 runs/month, 60% cache hit)

**Context:** Post-Q1 once cache is partially built. 60% of runs are cache hits (skip AI processing, still execute PySpark on Spark).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $85 | EP1 Premium, steady load |
| ADLS Gen2 | $200 | Same I/O volume |
| **Azure OpenAI (LLM)** | **$1,050** | **500 new transforms x $2.10** |
| **Azure Databricks** | **$2,225** | **1,250 jobs x 1hr x $1.78/hr** (all runs need Spark) |
| Cosmos DB (serverless) | $20 | Mature approved code store, mostly reads + audit writes |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$3,595/month** | |
| **Quarterly** | **$10,785** | |
| **Annual** | **$43,140** | |

**Per-run cost:** $3,595 / 1,250 = **$2.88/run**

**Note:** Approved code reuse saves LLM costs but NOT Spark costs — all runs execute PySpark regardless. Cache optimization is now the biggest single lever for cost reduction.

---

### Scenario 3b: Steady State Optimized (Spot instances + 70% cache)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $70 | EP1 Premium, optimized |
| ADLS Gen2 | $180 | Lifecycle management |
| Azure OpenAI (LLM) | $788 | 375 new transforms x $2.10 |
| **Azure Databricks (Spot)** | **$1,625** | **1,250 jobs x 1hr x $1.30/hr** |
| Cosmos DB (serverless) | $15 | Mature approved code store + steady audit |
| ADLS Immutable Archive | $12 | WORM-protected audit archive |
| **Total** | **$2,690/month** | |
| **Quarterly** | **$8,070** | |
| **Annual** | **$32,280** | |

**Per-run cost:** $2,690 / 1,250 = **$2.15/run**

**Spot breakdown:** Spot discounts only the VM component (~80% on workers), not DBU charges. Driver stays on-demand for job reliability. Savings: $2,225 -> $1,625/month (**27% reduction** on Databricks compute).

---

### Scenario 4: Busy Season Peak (1,500 runs/month, 50% cache hit)

**Context:** February-April peak load (3 months/year)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $100 | EP1 Premium, higher scaling |
| ADLS Gen2 | $250 | Higher I/O |
| **Azure OpenAI (LLM)** | **$1,575** | **750 new transforms x $2.10** |
| **Azure Databricks** | **$2,670** | **1,500 jobs x 1hr x $1.78/hr** |
| Cosmos DB (serverless) | $30 | High volume + audit |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$4,640/month** | |
| **3-Month Busy Season** | **$13,920** | |

**With Spot instances:** ~$3,920/month, $11,760/quarter

---

## Annual Cost Projections

### Year 1 (Building Cache)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (cold start) | 1,250 | 0% | $5,180 | $15,540 |
| Q2 (building) | 1,250 | 40% | $4,125 | $12,375 |
| Q3 (maturing) | 1,250 | 60% | $3,595 | $10,785 |
| Q4 (optimized) | 1,250 | 70% | $3,333 | $10,000 |
| **Year 1 Total** | | | | **$48,700** |

**With Spot instances throughout Year 1: ~$41,500**

### Year 2+ (Steady State)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (busy season) | 1,500 | 50% | $4,640 | $13,920 |
| Q2 | 1,250 | 70% | $3,333 | $10,000 |
| Q3 | 1,250 | 75% | $3,201 | $9,600 |
| Q4 | 1,250 | 75% | $3,201 | $9,600 |
| **Year 2 Total** | | | | **$43,120** |

**With Spot instances: ~$35,900/year**

---

## Why Databricks Over Fabric

### For 1,250 runs/month with 60% cache hit rate:

| Platform | Monthly Spark Cost | Annual Spark Cost | Notes |
|----------|-------------------|-------------------|-------|
| **Azure Databricks (Jobs Compute)** | **$2,225** | **$26,700** | **Pay-per-job, scales with usage** |
| **Azure Databricks (Spot)** | **$1,625** | **$19,500** | **~80% VM discount on workers** |
| Microsoft Fabric (F8 Reserved) | $765 fixed + overage | $15,000+ | May need F16+ for this volume |
| Microsoft Fabric (F16 Reserved) | $1,251 fixed | $15,012 | Competitive at high volume |

**At 1,250 runs/month, Fabric F16 is cheaper** than Spot-optimized Databricks. However, Databricks is preferred because:
1. Customer already uses Databricks (no new service)
2. Per-job cost transparency (attribute costs per client)
3. Spot instances give 60% discount on workers
4. Autoscaling (1-5 workers) matches variable job sizes
5. No capacity management overhead

**Recommendation:** Databricks with Spot instances for Year 1. Evaluate Fabric if customer consolidates to Azure-native stack in Year 2+.

---

## LLM Model Options

### GPT-5.2 vs. Alternatives

Our design uses GPT-5.2 ($1.75/M input, $14.00/M output) for all phases — single model deployment simplifies operations. At ~400K input / ~100K output tokens per transformation, LLM is a significant cost driver.

| Approach | Cost per New Transform | Monthly LLM at 500 new | Notes |
|----------|----------------------|----------------------|-------|
| **GPT-5.2 (all phases)** | **$2.10** | **$1,050** | **Current baseline — single model, simplest ops** |
| GPT-5.2 + GPT-4o-mini (mixed) | $1.51 | $755 | 5.2 for pseudocode/feedback, mini for code gen + profiling — 28% savings |
| GPT-4o-mini (all phases) | $0.12 | $60 | Cheapest option — may sacrifice quality on pseudocode |

**Recommendation:** Start with GPT-5.2 for all phases (best quality, simplest ops). If LLM costs need reduction, tier down code generation and profiling to GPT-4o-mini — these are mechanical tasks where mini's quality is sufficient. This saves ~$295/month at 60% cache rate.

---

## Cost Optimization Strategies

### 1. Maximize Cache Hit Rates (Biggest Lever)
**Impact:** Each 10% cache improvement saves **~$263/month** in LLM costs

At 1,250 runs/month:
| Cache Hit Rate | New Transforms | LLM Cost | Total Monthly |
|----------------|----------------|----------|---------------|
| 0% | 1,250 | $2,625/month | $5,180 |
| 50% | 625 | $1,313/month | $3,858 |
| 60% | 500 | $1,050/month | $3,595 |
| 70% | 375 | $788/month | $3,333 |
| 80% | 250 | $525/month | $3,070 |

**Note:** Approved code reuse saves LLM costs but not Spark costs (all runs execute PySpark).

### 2. Spot Instances
**Impact:** ~80% discount on Databricks worker **VMs only** (DBU charges are not discounted)

```
On-demand: 1,250 jobs x $1.78/hr = $2,225/month
Spot:      1,250 jobs x $1.30/hr = $1,625/month
Savings:   $600/month ($7,200/year)

Breakdown of Spot rate ($1.30/hr):
  DBU:     6 x $0.15       = $0.90/hr  (fixed, never discounted)
  Driver:  1 x $0.293      = $0.293/hr (on-demand for reliability)
  Workers: 2 x $0.054      = $0.108/hr (Spot at ~81% discount)
```

**Risk:** Worker VMs may be preempted (rare for 1-hour jobs). Driver stays on-demand to ensure job coordination.

### 3. Model Tiering
- GPT-5.2 for pseudocode generation + human feedback (where reasoning quality matters)
- GPT-4o-mini for code generation, profiling, and integrity checks (mechanical tasks)
- **Savings:** ~$295/month at 60% cache ($1,050 -> $755 LLM)
- **Trade-off:** Two model deployments to manage

### 4. Right-Size Clusters
- Use autoscaling (1-5 workers) based on data volume
- Small jobs (1-3 GB): 2-node cluster ($1.19/hr)
- Large jobs (7-10 GB): 4-node cluster ($2.37/hr)
- **Potential savings:** 15-25% on Databricks costs

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
| 15,000 runs/year | $12,000,000 | $48,700 | $41,500 |
| Cost per run | $800 | $3.25 | $2.77 |
| **Savings** | — | **99.6%** | **99.7%** |

**Annual savings:** ~$11.95M — infrastructure cost is negligible vs. labor

**ROI:** Infrastructure cost is negligible compared to labor savings.

---

## Risk Factors

### 1. Databricks Standard Tier Retirement (Oct 2026)
**Risk:** Standard tier ($0.15/DBU) retires October 2026. Premium tier ($0.30/DBU) will apply — doubling the DBU component.
**Impact:** On-demand rate increases from $1.78/hr to $2.68/hr (+51%). Monthly Databricks cost jumps from $2,225 to $3,350 at 1,250 runs.
**Mitigation:** Factor into Year 2 budget. Evaluate Fabric F16 ($1,251/month fixed) which becomes clearly cheaper at Premium DBU rates. Right-size clusters to reduce DBU count.

### 2. Cold Start Cost Spike
**Risk:** Q1 at 0% cache hits = $5,180/month (vs. $3,595 steady state)
**Impact:** Significant — $1,585/month difference driven by LLM costs (all transforms are new)
**Mitigation:** Spot instances bring Q1 cost to ~$4,580/month. Model tiering brings LLM portion down further.

### 3. Spark Processing Takes Longer
**Risk:** Jobs average 1.5 hours instead of 1 hour
**Impact:** +50% on Databricks costs (+$1,113/month on-demand, +$813/month Spot)
**Mitigation:** Autoscaling, larger clusters for big datasets, batch processing

### 4. LLM Costs Higher Than Estimated
**Risk:** Complex transformations need more tokens or feedback iterations
**Impact:** 2x token usage at 60% cache = $2,100/month LLM, total $4,645/month
**Mitigation:** Model tiering (mini for code gen), approved code reuse, prompt optimization

### 5. Databricks Cost Transparency
**Risk:** Hard to attribute Spark costs per client
**Mitigation:** Job tagging in Databricks, cost allocation by client_id

---

## Summary

### Realistic Production Costs (1,250 runs/month):

| Configuration | Monthly | Annual |
|--------------|---------|--------|
| Standard (60% cache, on-demand) | $3,595 | $43,140 |
| **Optimized (70% cache, Spot)** | **$2,690** | **$32,280** |
| Aggressive (80% cache, Spot, model tiering) | $2,175 | $26,100 |

### Per-Run Cost:

| Configuration | Cost per Run | vs. $800 Manual |
|--------------|-------------|-----------------|
| Standard | $2.88 | **99.6% reduction** |
| Optimized | $2.15 | **99.7% reduction** |

### Cost Distribution (Steady State, Standard):

| Component | % of Total | Monthly |
|-----------|-----------|---------|
| Azure Databricks | **62%** | $2,225 |
| Azure OpenAI (GPT-5.2) | **29%** | $1,050 |
| ADLS Gen2 | 6% | $200 |
| Agent Runtime (Durable Functions) | 2% | $85 |
| Cosmos DB (serverless) + ADLS Archive | 1% | $35 |

**Databricks and LLM are the two dominant costs (91% combined).** Maximizing cache hit rates is the single most impactful optimization — each 10% improvement saves ~$263/month in LLM costs. Spot instances provide an additional 27% reduction on Spark compute.

---

*This cost analysis reflects realistic production volumes from the January 30, 2026 customer call. Will be updated as POC data becomes available.*

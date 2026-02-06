# AI Data Engineering Agent - Cost Analysis

**Version:** 3.2
**Date:** February 6, 2026
**Baseline Scenario:** ~1,250 runs/month (3,000 clients x 5 runs/year)

---

## Executive Summary

This cost analysis provides detailed projections for running the AI Data Engineering Agent at realistic production volumes. Based on customer estimates from the January 30, 2026 call, the baseline is **~1,250 runs/month** — significantly higher than our initial v2.0 estimate of 100 runs/month.

### Cost Summary

| Scenario | Volume | Cache Hit | Monthly | Quarterly | Annual |
|----------|--------|-----------|---------|-----------|--------|
| **POC Pilot** (limited) | 50 runs/month | 0% | **$137** | **$411** | **$1,644** |
| **Cold Start Q1** (full volume) | 1,250 runs/month | 0% | **$2,805** | **$8,415** | — |
| **Steady State** (post-Q1) | 1,250 runs/month | 60% | **$2,645** | **$7,935** | **$31,740** |
| **Steady State (optimized)** | 1,250 runs/month | 70% | **$1,977** | **$5,931** | **$23,724** |
| **Busy Season Peak** | 1,500 runs/month | 50% | **$3,215** | **$9,645** | — |

**Key Insight:** At realistic volumes (~1,250 runs/month), the dominant cost is **Databricks Spark compute** (~84% of total). LLM costs remain a minor line item. Spot instances provide meaningful savings (~27%) but only discount the VM component — DBU charges are fixed.

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
1. **Azure Databricks:** Per-job Spark compute (~84% of total cost at production volume)
2. **ADLS Gen2:** Data storage and I/O (~8%)
3. **Azure OpenAI tokens:** LLM calls for profiling, pseudocode, PySpark generation (~4%)
4. **Agent Runtime (Durable Functions):** Hosting the agent process (~3%)
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
| Data profiling | ~2,000 | ~1,000 | $0.018 |
| Pseudocode generation | ~5,000 | ~3,000 | $0.051 |
| Human feedback iteration (avg 1 round) | ~3,000 | ~2,000 | $0.033 |
| PySpark code generation | ~4,000 | ~5,000 | $0.077 |
| Integrity check analysis | ~3,000 | ~1,000 | $0.019 |
| **Total per new transformation** | | | **~$0.20** |

**Monthly LLM Costs:**

| Runs/Month | Cache Hit Rate | New Transforms | LLM Cost/Month |
|------------|---------------|----------------|----------------|
| 50 | 0% | 50 | **$10** |
| 1,250 | 0% (cold start) | 1,250 | **$250** |
| 1,250 | 60% | 500 | **$100** |
| 1,250 | 70% | 375 | **$75** |
| 1,500 | 50% | 750 | **$150** |

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
| Azure OpenAI (LLM) | $10 | 50 new transforms x $0.20 |
| Azure Databricks | $89 | 50 jobs x 1hr x $1.78/hr |
| Cosmos DB (serverless) | $8 | 3 containers, minimal volume |
| ADLS Immutable Archive | $10 | WORM-protected audit archive |
| **Total** | **$137/month** | |

---

### Scenario 2: Cold Start Q1 (1,250 runs/month, 0% cache hit)

**Context:** First quarter at full volume — every transformation is new. No existing PySpark to migrate (current system uses Spark notebooks + M code/Power Query).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $85 | EP1 Premium, some scaling headroom |
| ADLS Gen2 | $200 | 1,250 clients x ~8GB I/O |
| Azure OpenAI (LLM) | $250 | 1,250 new transforms x $0.20 |
| **Azure Databricks** | **$2,225** | **1,250 jobs x 1hr x $1.78/hr** |
| Cosmos DB (serverless) | $30 | Building approved code store + high audit write volume |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$2,805/month** | |
| **3-Month Cold Start** | **$8,415** | |

**Per-run cost:** $2,805 / 1,250 = **$2.24/run** (vs. $800 manual = **99.7% reduction**)

**With Spot instances** (driver on-demand, workers ~80% discount): Total drops to ~$2,205/month

---

### Scenario 3: Steady State (1,250 runs/month, 60% cache hit)

**Context:** Post-Q1 once cache is partially built. 60% of runs are cache hits (skip AI processing, still execute PySpark on Spark).

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $85 | EP1 Premium, steady load |
| ADLS Gen2 | $200 | Same I/O volume |
| Azure OpenAI (LLM) | $100 | 500 new transforms x $0.20 |
| **Azure Databricks** | **$2,225** | **1,250 jobs x 1hr x $1.78/hr** (all runs need Spark) |
| Cosmos DB (serverless) | $20 | Mature approved code store, mostly reads + audit writes |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$2,645/month** | |
| **Quarterly** | **$7,935** | |
| **Annual** | **$31,740** | |

**Per-run cost:** $2,645 / 1,250 = **$2.12/run**

**Note:** Approved code reuse saves LLM costs but NOT Spark costs — all runs execute PySpark regardless.

---

### Scenario 3b: Steady State Optimized (Spot instances + 70% cache)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $70 | EP1 Premium, optimized |
| ADLS Gen2 | $180 | Lifecycle management |
| Azure OpenAI (LLM) | $75 | 375 new transforms x $0.20 |
| **Azure Databricks (Spot)** | **$1,625** | **1,250 jobs x 1hr x $1.30/hr** |
| Cosmos DB (serverless) | $15 | Mature approved code store + steady audit |
| ADLS Immutable Archive | $12 | WORM-protected audit archive |
| **Total** | **$1,977/month** | |
| **Quarterly** | **$5,931** | |
| **Annual** | **$23,724** | |

**Per-run cost:** $1,977 / 1,250 = **$1.58/run**

**Spot breakdown:** Spot discounts only the VM component (~80% on workers), not DBU charges. Driver stays on-demand for job reliability. Savings: $2,225 -> $1,625/month (**27% reduction** on Databricks compute).

---

### Scenario 4: Busy Season Peak (1,500 runs/month, 50% cache hit)

**Context:** February-April peak load (3 months/year)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Agent Runtime (Durable Functions) | $100 | EP1 Premium, higher scaling |
| ADLS Gen2 | $250 | Higher I/O |
| Azure OpenAI (LLM) | $150 | 750 new transforms x $0.20 |
| **Azure Databricks** | **$2,670** | **1,500 jobs x 1hr x $1.78/hr** |
| Cosmos DB (serverless) | $30 | High volume + audit |
| ADLS Immutable Archive | $15 | WORM-protected audit archive |
| **Total** | **$3,215/month** | |
| **3-Month Busy Season** | **$9,645** | |

**With Spot instances:** ~$2,495/month, $7,485/quarter

---

## Annual Cost Projections

### Year 1 (Building Cache)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (cold start) | 1,250 | 0% | $2,805 | $8,415 |
| Q2 (building) | 1,250 | 40% | $2,700 | $8,100 |
| Q3 (maturing) | 1,250 | 60% | $2,645 | $7,935 |
| Q4 (optimized) | 1,250 | 70% | $2,620 | $7,860 |
| **Year 1 Total** | | | | **$32,310** |

**With Spot instances throughout Year 1: ~$25,100**

### Year 2+ (Steady State)

| Quarter | Runs/Month | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------------|-----------|-------------|----------------|
| Q1 (busy season) | 1,500 | 50% | $3,215 | $9,645 |
| Q2 | 1,250 | 70% | $2,620 | $7,860 |
| Q3 | 1,250 | 75% | $2,608 | $7,824 |
| Q4 | 1,250 | 75% | $2,608 | $7,824 |
| **Year 2 Total** | | | | **$33,153** |

**With Spot instances: ~$26,000/year**

---

## Why Databricks Over Fabric

### For 1,250 runs/month with 60% cache hit rate:

| Platform | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| **Azure Databricks (Jobs Compute)** | **$2,645** | **$31,740** | **Pay-per-job, scales with usage** |
| **Azure Databricks (Spot)** | **$1,977** | **$23,724** | **~80% VM discount on workers** |
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

Our design uses GPT-5.2 ($1.75/M input, $14.00/M output) for all phases — single model deployment simplifies operations.

| Approach | Cost per New Transform | Monthly LLM at 500 new | Notes |
|----------|----------------------|----------------------|-------|
| **GPT-5.2 (all phases)** | **$0.20** | **$100** | **Current baseline — single model, simplest ops** |
| GPT-5.2 + GPT-4o-mini (mixed) | $0.13 | $65 | 5.2 for pseudocode, mini for code gen — 35% savings |
| GPT-4o + GPT-4o-mini (mixed) | $0.13 | $65 | Previous generation, similar cost when mixed |
| GPT-4o only | $0.22 | $110 | Previous generation, no cost advantage |

**Recommendation:** GPT-5.2 for all phases provides the best quality at a competitive price point. The PySpark code generation phase (mechanical translation from pseudocode) could use GPT-4o-mini to save ~35% on LLM costs, but at ~$100/month total LLM spend, the operational simplicity of a single model outweighs the $35/month savings. Revisit if LLM costs become material.

---

## Cost Optimization Strategies

### 1. Spot Instances (Biggest Lever)
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

### 2. Maximize Cache Hit Rates
**Impact:** Each 10% cache improvement saves ~$25/month in LLM costs

At 1,250 runs/month:
| Cache Hit Rate | New Transforms | LLM Cost |
|----------------|----------------|----------|
| 0% | 1,250 | $250/month |
| 50% | 625 | $125/month |
| 60% | 500 | $100/month |
| 70% | 375 | $75/month |
| 80% | 250 | $50/month |

**Note:** Approved code reuse saves LLM costs but not Spark costs (all runs execute PySpark).

### 3. Right-Size Clusters
- Use autoscaling (1-5 workers) based on data volume
- Small jobs (1-3 GB): 2-node cluster ($1.19/hr)
- Large jobs (7-10 GB): 4-node cluster ($2.37/hr)
- **Potential savings:** 15-25% on Databricks costs

### 4. Model Tiering (Optional)
- GPT-5.2 for pseudocode generation (where reasoning quality matters)
- GPT-4o-mini for PySpark code generation (mechanical translation from approved pseudocode)
- **Savings:** ~35% on LLM costs ($100 -> $65/month at 60% cache)
- **Trade-off:** Two model deployments to manage vs. $35/month savings

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
| 15,000 runs/year | $12,000,000 | $32,310 | $25,100 |
| Cost per run | $800 | $2.15 | $1.67 |
| **Savings** | — | **99.7%** | **99.8%** |

**Annual savings:** ~$11.97M — infrastructure cost is negligible vs. labor

**ROI:** Infrastructure cost is negligible compared to labor savings.

---

## Risk Factors

### 1. Databricks Standard Tier Retirement (Oct 2026)
**Risk:** Standard tier ($0.15/DBU) retires October 2026. Premium tier ($0.30/DBU) will apply — doubling the DBU component.
**Impact:** On-demand rate increases from $1.78/hr to $2.68/hr (+51%). Monthly Databricks cost jumps from $2,225 to $3,350 at 1,250 runs.
**Mitigation:** Factor into Year 2 budget. Evaluate Fabric F16 ($1,251/month fixed) which becomes clearly cheaper at Premium DBU rates. Right-size clusters to reduce DBU count.

### 2. Cold Start Cost Spike
**Risk:** Q1 at 0% cache hits = $2,805/month (vs. $2,645 steady state)
**Impact:** Moderate — only $160/month difference; LLM is a small portion of total cost
**Mitigation:** Spot instances bring Q1 cost to ~$2,205/month

### 3. Spark Processing Takes Longer
**Risk:** Jobs average 1.5 hours instead of 1 hour
**Impact:** +50% on Databricks costs (+$1,113/month on-demand, +$813/month Spot)
**Mitigation:** Autoscaling, larger clusters for big datasets, batch processing

### 4. LLM Costs Higher Than Estimated
**Risk:** Complex transformations need more tokens or feedback iterations
**Impact:** Even 3x token usage only adds ~$200/month at 60% cache rate
**Mitigation:** Model tiering (mini for code gen), approved code reuse

### 5. Databricks Cost Transparency
**Risk:** Hard to attribute Spark costs per client
**Mitigation:** Job tagging in Databricks, cost allocation by client_id

---

## Summary

### Realistic Production Costs (1,250 runs/month):

| Configuration | Monthly | Annual |
|--------------|---------|--------|
| Standard (60% cache, on-demand) | $2,645 | $31,740 |
| **Optimized (70% cache, Spot)** | **$1,977** | **$23,724** |
| Aggressive (80% cache, Spot, right-sized) | $1,700 | $20,400 |

### Per-Run Cost:

| Configuration | Cost per Run | vs. $800 Manual |
|--------------|-------------|-----------------|
| Standard | $2.12 | **99.7% reduction** |
| Optimized | $1.58 | **99.8% reduction** |

### Cost Distribution (Steady State, Standard):

| Component | % of Total | Monthly |
|-----------|-----------|---------|
| Azure Databricks | **84%** | $2,225 |
| ADLS Gen2 | 8% | $200 |
| Azure OpenAI (GPT-5.2) | 4% | $100 |
| Agent Runtime (Durable Functions) | 3% | $85 |
| Cosmos DB (serverless) + ADLS Archive | 1% | $35 |

**Databricks is the dominant cost (84%).** Spot instances provide a meaningful 27% reduction on Spark compute but only discount the VM component — DBU charges are fixed. Right-sizing clusters for smaller datasets is an additional lever.

---

*This cost analysis reflects realistic production volumes from the January 30, 2026 customer call. Will be updated as POC data becomes available.*

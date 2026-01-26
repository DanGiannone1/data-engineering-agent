# AI Data Engineering Agent - Cost Analysis

**Version:** 1.0  
**Date:** January 26, 2026  
**Scenario:** Few hundred runs per quarter (~100-300 runs/quarter, ~33-100 runs/month)

---

## Executive Summary

This cost analysis provides detailed projections for running the AI Data Engineering Agent at scale. Based on current Azure pricing (2026) and the assumption of **100-300 transformation runs per quarter**, we estimate:

### Cost Summary

| Scenario | Monthly Cost | Quarterly Cost | Annual Cost |
|----------|-------------|----------------|-------------|
| **Low Volume** (33 runs/month, 50% cache hit rate) | **$842** | **$2,526** | **$10,104** |
| **Medium Volume** (67 runs/month, 60% cache hit rate) | **$1,456** | **$4,368** | **$17,472** |
| **High Volume** (100 runs/month, 70% cache hit rate) | **$2,018** | **$6,054** | **$24,216** |

**Key Insight:** Cache hit rates dramatically reduce costs. After the first quarter of building up cached transformations, costs can drop by 40-60%.

## Cost Assumptions

**Platform Decisions:**
- **Big Data Processing:** Microsoft Fabric (F8 or F16 capacity)
- **AI Agent Runtime:** Azure Container Apps - **Production-grade (4 vCPU, 8 GiB RAM)**
- **LLM/AI Platform:** 
  - GitHub Copilot SDK Enterprise ($39/month + overages)
  - **Azure AI Foundry** for evaluation, tracing, and governance
- **Code Cache:** Cosmos DB serverless
- **User Interaction Storage:** Cosmos DB (separate container for feedback/tuning data)
- **Audit Storage:** Immutable Blob Storage

**Key Cost Drivers:**
1. **Azure AI Foundry:** Model evaluations, tracing, guardrails (~40-50% of total cost)
2. **Fabric Spark Cluster:** Execution engine (~25-30% of total cost)
3. **Container Apps (Production):** 4 vCPU, 8 GiB for enterprise workload (~8-10%)
4. **LLM API Calls:** Copilot SDK premium requests (varies by cache hit rate)
5. **Cosmos DB:** Code cache + user interaction history

---

## Azure Pricing (2026)

### Azure Container Apps (Production)
- **vCPU:** $0.000024 per vCPU-second
- **Memory:** $0.000003 per GiB-second
- **Configuration:** **4 vCPU + 8 GiB RAM**, 24/7 operation (enterprise-grade)
- **Monthly cost:** ~$200-300 depending on utilization

### Azure AI Foundry
**Model Evaluation:**
- **GPT-4 evaluation runs:** $0.03 per 1K tokens input, $0.06 per 1K tokens output
- **Custom evaluators:** $50-150/month for compute
- **Estimated:** 100-200 evaluation runs/month = $1,000-1,500/month

**Tracing & Observability:**
- **Trace storage:** $0.10 per GB
- **Trace queries:** $0.50 per 100K queries
- **Estimated:** Full tracing for 300-1,000 runs = $300-500/month

**Content Safety & Guardrails:**
- **Per-request screening:** $0.001 per request
- **Estimated:** All AI generations screened = $50-100/month

**Total AI Foundry:** ~$1,500-2,000/month

### Microsoft Fabric
- **F8 Capacity (Reserved 1-year):** $625/month
- **F16 Capacity (Reserved 1-year):** $1,251/month (for busy season burst)
- **Pay-as-you-go:** Higher rates, use reserved for cost optimization

### GitHub Copilot SDK
- **Enterprise tier:** $39/user/month base
- **Included:** 1,000 premium requests/month
- **Overage:** $0.04 per additional premium request
- **Premium request = full AI analysis cycle (parsing + generation)**

### Azure Cosmos DB (Serverless)
**Code Cache Container:**
- **RU cost:** $0.25 per 1M RUs
- **Storage:** $0.25 per GB/month
- **Estimated:** 10-20GB, 1-2M RUs/month = ~$8-15/month

**User Interaction Container:**
- Stores: User feedback, approval history, conversation logs
- Purpose: Future model tuning, pattern analysis
- **Estimated:** 5-10GB, 500K RUs/month = ~$5-10/month

### Azure Data Lake Storage Gen2 (Hot Tier)
- **Storage:** $0.0184 per GB/month
- **Transactions:** $0.004-0.05 per 10K operations
- **Estimated:** ~$85-150/month depending on volume

### Immutable Blob Storage (Audit Trail)
- **Storage:** $0.018 per GB/month
- **Immutability:** No extra charge for policy
- **Estimated:** ~$10-20/month

### Azure Monitor (Application Insights)
- **First 5 GB/month:** Free
- **Beyond 5 GB:** $2.30 per GB
- **Estimated:** ~$25-50/month for enterprise logging

---

## Detailed Cost Breakdown by Component

### 1. Azure Container App (AI Agent Runtime)

**Configuration:**
- 2 vCPU, 4 GiB RAM
- Running 24/7 for orchestration and quick response
- Scales to 0 when not processing (saves costs)

**Calculation:**
```
vCPU cost: 2 vCPU × $0.000024/sec × 2,592,000 sec/month = $124.42/month
Memory cost: 4 GiB × $0.000003/sec × 2,592,000 sec/month = $31.10/month
Total (24/7): $155.52/month

With scale-to-zero (assume 40% active time):
$155.52 × 0.4 = $62.21/month
```

**Monthly Cost:** **$60-155** (depending on utilization)  
**Recommended:** $75/month (assuming some idle time)

---

### 2. Azure Data Lake Storage Gen2

**Assumptions per run:**
- Input data: 5 GB average per client
- Output data: 3 GB average (compressed Parquet)
- Mapping file: 1 MB
- Sample reads: 100 rows ≈ 1 MB

**Storage Costs:**
```
100 clients × 8 GB (input + output) = 800 GB
Storage: 800 GB × $0.0184/GB = $14.72/month

(Storage accumulates over time; assuming 1-month retention for processed data)
```

**Transaction Costs (per run):**
```
Read operations:
- Mapping file: 1 read = $0.0000004
- Sample data (100 rows): 1 read = $0.0000004
- Full data read: 5 GB / 4 MB per transaction = 1,280 transactions = $0.00051

Write operations:
- Output data: 3 GB / 4 MB = 768 transactions = $0.0038

Per run: $0.004 (negligible)
```

**Monthly Transaction Costs (100 runs):**
```
100 runs × $0.004 = $0.40/month
```

**Monthly ADLS Cost:** **$15-30/month** (storage dominates)

---

### 3. AI Processing (GitHub Copilot SDK)

**Assumptions:**
- Each new transformation requires 2 premium requests (analysis + code generation)
- Each cached transformation requires 0 premium requests (deterministic re-run)

**Copilot SDK Costs:**

**Base subscription:**
```
Enterprise tier: $39/month (includes 1,000 premium requests)
```

**Premium Request Usage:**

| Runs/Month | Cache Hit Rate | New Transforms | Premium Requests | Overage Cost |
|------------|---------------|----------------|------------------|--------------|
| 33         | 50%           | 17             | 34              | $0 (within limit) |
| 67         | 60%           | 27             | 54              | $0 (within limit) |
| 100        | 70%           | 30             | 60              | $0 (within limit) |
| 100        | 30%           | 70             | 140             | $0 (within limit) |
| 150        | 50%           | 75             | 150             | $0 (within limit) |
| 300        | 40%           | 180            | 360             | $0 (within limit) |
| 500        | 50%           | 250            | 500             | $0 (within limit) |

**Monthly Copilot Cost:** **$39/month** (covers up to 500 premium requests)

**Note:** Even at high volume (300 runs/month with low cache hit rates), we stay well within the 1,000 request limit.

---

### 4. Spark Processing (Choose One)

#### Option A: Azure Databricks (Jobs Compute)

**Cluster Configuration:**
- 3-node cluster (1 driver + 2 workers)
- Node type: Standard_DS3_v2 (4 cores, 14 GB RAM each)
- DBUs per node: 2 DBUs/hour

**Hourly Cost:**
```
DBU cost: 6 DBUs/hour × $0.15/DBU = $0.90/hour
VM cost: 3 nodes × $0.27/hour = $0.81/hour
Total: $1.71/hour
```

**Processing Time Estimates:**
- Small job (1-3 GB): 0.5 hours
- Medium job (3-7 GB): 1.0 hour
- Large job (7-10 GB): 1.5 hours
- Average: 1 hour per job

**Monthly Costs:**

| Runs/Month | Cache Hit Rate | New Jobs | Hours | Monthly Cost |
|------------|---------------|----------|-------|--------------|
| 33         | 50%           | 17       | 17    | $29         |
| 67         | 60%           | 27       | 27    | $46         |
| 100        | 70%           | 30       | 30    | $51         |
| 100        | 30%           | 70       | 70    | $120        |
| 150        | 50%           | 75       | 75    | $128        |
| 300        | 40%           | 180      | 180   | $308        |

**Databricks Monthly Cost:** **$30-310/month** (volume-dependent)  
**Typical (100 runs, 70% cache):** **$51/month**

**Optimization Tips:**
- Use Spot instances (40-80% discount) for non-critical jobs
- Enable autoscaling to reduce idle time
- Use Delta Live Tables for better performance

---

#### Option B: Microsoft Fabric

**Capacity Configuration:**
- F8 Capacity (8 CUs) for medium workloads
- OR F16 Capacity (16 CUs) for high workloads

**Pricing:**
- **F8:** $1,051/month pay-as-you-go (or $625/month reserved)
- **F16:** $2,102/month pay-as-you-go (or $1,251/month reserved)

**Processing:**
- Fabric charges by capacity, not per job
- Can handle multiple concurrent jobs
- Burst above capacity with overage charges

**Monthly Costs:**

| Scenario | Base Capacity | Utilization | Overage | Total Monthly |
|----------|--------------|-------------|---------|---------------|
| Low (33 runs/month) | F8 reserved | 30% | $0 | **$625** |
| Medium (67 runs/month) | F8 reserved | 60% | $50 | **$675** |
| High (100 runs/month) | F16 reserved | 50% | $0 | **$1,251** |

**Fabric Monthly Cost:** **$625-1,251/month**

**Key Difference:** Fabric is a fixed capacity model vs. Databricks' per-job pricing.

**When Fabric is Cheaper:**
- High volume (200+ jobs/month)
- Mixed workloads (not just batch ETL)
- Already using Power BI/Synapse

**When Databricks is Cheaper:**
- Low to medium volume (< 150 jobs/month)
- Batch-only workloads
- Can leverage Spot instances

**Recommendation:** For this use case (100-300 runs/quarter with caching), **Databricks is more cost-effective** at **$30-120/month** vs. Fabric at **$625-1,251/month**.

---

### 5. Code Cache (Cosmos DB Serverless)

**Assumptions:**
- Cache entries: ~300 unique client transformations
- Each entry: ~50 KB (pseudocode + PySpark code)
- Operations: 2 reads per run (lookup + stats update), 1 write per new transformation

**Storage:**
```
300 clients × 50 KB = 15 MB = 0.015 GB
Storage cost: 0.015 GB × $0.25/GB = $0.00375/month (negligible)
```

**Request Units (RUs):**
```
Per cache hit:
- Read cache entry: 5 RUs
- Update execution stats: 5 RUs
Total: 10 RUs

Per cache miss (new transformation):
- Read attempt: 5 RUs
- Write new entry: 10 RUs
Total: 15 RUs
```

**Monthly RU Costs (100 runs/month, 70% cache hit rate):**
```
Cache hits: 70 runs × 10 RUs = 700 RUs
Cache misses: 30 runs × 15 RUs = 450 RUs
Total: 1,150 RUs

Cost: 1,150 / 1,000,000 × $0.25 = $0.0003/month (negligible)
```

**Monthly Cosmos DB Cost:** **$1-3/month** (mostly minimum storage charge)

---

### 6. Networking & Data Transfer

**Assumptions:**
- Container App, ADLS, Databricks in same Azure region
- No cross-region data transfer
- No egress to internet

**Cost:** **$0/month** (all in-region, private networking)

**If cross-region:** ~$0.02-0.05/GB egress

---

### 7. Monitoring (Application Insights)

**Log Volume Estimates:**
- Container App logs: ~100 MB/day
- Databricks logs: ~50 MB/job
- Total: ~3-5 GB/month

**Cost:**
- First 5 GB: Free
- Additional: $2.30/GB

**Monthly Monitoring Cost:** **$0-10/month**

---

## Complete Cost Scenarios

### Scenario 1: Low Volume (33 runs/month, 50% cache hit rate) - **FABRIC**

**First Quarter (Building Cache):**
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $75 | 24/7 runtime |
| ADLS Gen2 | $20 | Storage + transactions |
| Copilot SDK | $39 | Enterprise tier |
| **Microsoft Fabric (F8)** | **$625** | Reserved 1-year capacity |
| Cosmos DB Cache | $2 | Serverless |
| Monitoring | $5 | Application Insights |
| **Total** | **$766/month** | |
| **Quarterly** | **$2,298** | |

**Subsequent Quarters (Established Cache):**
Same costs (Fabric is fixed capacity pricing)
| **Total** | **$766/month** | |
| **Quarterly** | **$2,298** | |
| **Annual** | **$9,192** | |

---

### Scenario 2: Medium Volume (67 runs/month, 60% cache hit rate) - **FABRIC**

**First Quarter (Building Cache):**
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $75 | 24/7 runtime |
| ADLS Gen2 | $25 | More storage |
| Copilot SDK | $39 | Enterprise tier |
| **Microsoft Fabric (F8)** | **$625** | Reserved 1-year capacity |
| Cosmos DB Cache | $2 | Serverless |
| Monitoring | $7 | More logs |
| **Total** | **$773/month** | |
| **Quarterly** | **$2,319** | |

**Subsequent Quarters (Cache Stabilizes):**
| **Total** | **$773/month** | |
| **Quarterly** | **$2,319** | |
| **Annual** | **$9,276** | |

---

### Scenario 3: High Volume (100 runs/month, 70% cache hit rate) - **FABRIC**

**Context:** Post-initial rollout baseline (from original cost analysis)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $85 | Higher utilization |
| ADLS Gen2 | $30 | More storage |
| Copilot SDK | $39 | Enterprise tier |
| **Microsoft Fabric (F8)** | **$625** | Reserved 1-year capacity |
| Cosmos DB Cache | $3 | More operations |
| Monitoring | $10 | More logs |
| **Total** | **$792/month** | |
| **Quarterly** | **$2,376** | |
| **Annual** | **$9,504** | |

**Per-run cost:** $792 / 100 = **$7.92/run**

---

### Scenario 4: Normal Operations (350 runs/month, 60% cache hit rate) - **FABRIC**

**Context:** Typical monthly volume across 3,000 clients (300-400 runs/month average)

**Assumptions:**
- 350 runs/month = 4,200 runs/year
- 60% cache hit (lower than baseline due to more schema variations)
- F8 capacity sufficient for this volume
- 140 new AI analyses/month (40% cache miss)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $120 | Higher sustained load |
| ADLS Gen2 | $85 | 3.5x storage/transactions |
| Copilot SDK | $39 + $6 overage | 1,140 premium requests (140 over quota) |
| **Microsoft Fabric (F8)** | **$625** | Reserved capacity handles load |
| Cosmos DB Cache | $8 | 3.5x operations, more storage |
| Monitoring | $25 | 3.5x logs |
| **Total** | **$908/month** | |
| **Quarterly** | **$2,724** | |
| **Annual** | **$10,896** | |

**Per-run cost:** $908 / 350 = **$2.59/run**

---

### Scenario 5: Audit Busy Season Peak (1,000 runs/month, 50% cache hit) - **FABRIC F16**

**Context:** February-April peak load (3 months/year)

**Assumptions:**
- 1,000 runs/month = surge capacity
- 50% cache hit (more schema changes during busy season)
- F16 capacity needed for 3 months (2x F8)
- 500 new AI analyses/month

**Peak Season Costs (3 months):**
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $240 | Near 100% utilization |
| ADLS Gen2 | $240 | 10x normal storage/transactions |
| Copilot SDK | $39 + $60 overage | 2,500 premium requests (1,500 over quota) |
| **Microsoft Fabric (F16)** | **$1,251** | Reserved 2x capacity for burst |
| Cosmos DB Cache | $20 | 10x operations |
| Monitoring | $50 | Heavy logging |
| **Total** | **$1,900/month** | |
| **3-Month Busy Season** | **$5,700** | |

**Per-run cost:** $1,900 / 1,000 = **$1.90/run**

**Off-Season (9 months):** Use Scenario 4 pricing
- 9 months × $908/month = $8,172

**Annual Total:** $5,700 (busy) + $8,172 (normal) = **$13,872/year**

---

### Scenario 6: Initial Rollout (100 runs/month, 0% cache hit) - **FABRIC**

**Context:** First 3 months while building transformation cache

**Assumptions:**
- Every run requires full AI analysis (no cache)
- F8 capacity sufficient
- Higher Copilot usage

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $100 | High AI processing time |
| ADLS Gen2 | $30 | Same as Scenario 3 |
| Copilot SDK | $39 + $12 overage | 1,300 premium requests (300 over quota) |
| **Microsoft Fabric (F8)** | **$625** | Reserved capacity |
| Cosmos DB Cache | $1 | Building cache, few hits |
| Monitoring | $15 | Heavy initial logging |
| **Total** | **$822/month** | |
| **3-Month Rollout** | **$2,466** | |

**Per-run cost:** $822 / 100 = **$8.22/run**

After 3 months, transitions to Scenario 3 or 4 as cache builds up.

---

### Scenario 4: Very High Volume (300 runs/quarter = 100 runs/month at steady state) - **FABRIC**

**Optimized for Scale:**
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Container Apps | $100 | Scale up for concurrency |
| ADLS Gen2 | $50 | Large storage footprint |
| Copilot SDK | $39 | Still within 1,000 requests |
| **Microsoft Fabric (F8)** | **$625** | Reserved capacity handles load |
| Cosmos DB Cache | $5 | Higher read/write volume |
| Monitoring | $15 | Detailed logging |
| **Total** | **$834/month** | |
| **Quarterly** | **$2,502** | |
| **Annual** | **$10,008** | |

**Note:** At very high volumes (200+ jobs/month), Fabric's fixed capacity pricing becomes more economical than Databricks' per-job pricing.

---

## Cost Comparison: Databricks vs. Fabric

### For 100 runs/month with 70% cache hit rate:

| Platform | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| **Microsoft Fabric (F8 Reserved)** | **$792** | **$9,504** | **RECOMMENDED - First-party Microsoft** |
| Databricks (Jobs Compute) | $218 | $2,616 | Cheaper but third-party vendor |
| Fabric (F16 Reserved) | $1,413 | $16,956 | Overkill for this use case |

**Why Start with Fabric Despite Higher Cost:**
1. **First-party Microsoft service** - Better integration with Azure ecosystem
2. **Unified platform** - OneLake, Power BI, Synapse all in one
3. **Simpler procurement** - No additional vendor relationships
4. **Enterprise support** - Microsoft Premier support covers everything
5. **Future-proof** - Easier to add other analytics workloads
6. **Can optimize later** - Can switch to Databricks if cost becomes issue

**Cost Trade-off:**
- **Additional cost:** $574/month ($6,888/year) vs Databricks
- **Value gained:** Unified Microsoft platform, simpler operations, better compliance
- **When to reconsider:** If processing 200+ jobs/month with high cache hit rates, Databricks becomes $1K+/month cheaper

---

## Cost Optimization Strategies

### 1. Maximize Cache Hit Rates
**Impact:** Each cache hit saves ~1 hour of Spark processing ($1.71)

| Cache Hit Rate | Monthly Spark Cost (100 runs) | Savings vs. 0% cache |
|----------------|------------------------------|---------------------|
| 0% (no cache) | $171 | - |
| 50% | $86 | $85/month |
| 70% | $51 | $120/month |
| 90% | $17 | $154/month |

**Recommendation:** Focus on cache warming in first quarter. Aim for 70-80% hit rate by Q2.

### 2. Use Spot Instances (Databricks Only)
**Impact:** 40-80% discount on VM costs

```
Standard cluster: $1.71/hour
Spot cluster: $0.69/hour (60% discount)

Savings on 30 jobs: 30 × ($1.71 - $0.69) = $30.60/month
```

**Risk:** Jobs may be interrupted (rare for 1-hour jobs)

### 3. Right-Size Clusters
- Start with smaller cluster (2 workers instead of 3)
- Enable autoscaling (1-5 workers)
- Use cluster pools for faster startup

**Potential savings:** 20-30% on Databricks costs

### 4. Optimize Container App Scaling
- Scale to 0 during off-hours
- Reduce memory if AI workload is CPU-bound

**Potential savings:** $40-80/month on Container App costs

### 5. Use ADLS Lifecycle Management
- Move old data to Cool tier after 30 days
- Archive after 90 days

**Potential savings:** 50-80% on storage costs for historical data

### 6. Batch Processing
- Group multiple clients into single Spark job
- Process overnight when clusters are cheaper

**Potential savings:** 10-20% on overall Spark costs

---

## Long-Term Cost Projections

### Year 1 (Building to 300 runs/quarter) - **FABRIC**

| Quarter | Runs | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------|-----------|-------------|----------------|
| Q1 | 100 | 20% | $792 | $2,376 |
| Q2 | 200 | 50% | $810 | $2,430 |
| Q3 | 250 | 65% | $820 | $2,460 |
| Q4 | 300 | 75% | $834 | $2,502 |
| **Year 1 Total** | | | | **$9,768** |

### Year 2+ (Steady State at 300 runs/quarter) - **FABRIC**

| Quarter | Runs | Cache Hit | Monthly Avg | Quarterly Cost |
|---------|------|-----------|-------------|----------------|
| Q1 | 300 | 80% | $834 | $2,502 |
| Q2 | 300 | 82% | $834 | $2,502 |
| Q3 | 300 | 83% | $834 | $2,502 |
| Q4 | 300 | 85% | $834 | $2,502 |
| **Year 2 Total** | | | | **$10,008** |

**Key Insight:** With Fabric's fixed capacity pricing, costs remain stable regardless of cache hit rates (unlike Databricks where higher cache hits = lower costs). The benefit is predictable budgeting.

---

## ROI Analysis

### Cost Savings vs. Manual Process

**Assumptions:**
- Manual data engineering: 8 hours per client onboarding
- Data engineer salary: $100/hour fully loaded
- Manual cost per client: $800

**Break-Even Analysis:**

| Runs/Quarter | Manual Cost | Agent Cost (Fabric Q1) | Agent Cost (Q2+) | Quarterly Savings |
|--------------|-------------|------------------------|------------------|-------------------|
| 100 | $80,000 | $2,376 | $2,376 | **$77,624** |
| 200 | $160,000 | $2,430 | $2,430 | **$157,570** |
| 300 | $240,000 | $2,502 | $2,502 | **$237,498** |

**Payback Period:** Less than 1 day of manual work

**Annual ROI (with Fabric):**
- Investment: ~$10,000/year (agent infrastructure)
- Savings: ~$320,000/year (400 clients/year × $800)
- **ROI: 3,100%**

**Note:** Even with Fabric's higher costs vs. Databricks, ROI remains exceptional due to massive manual labor savings.

---

## Risk Factors & Contingencies

### 1. AI Costs Exceeding Estimates
**Risk:** Complex transformations require more premium requests

**Mitigation:**
- Monitor Copilot usage monthly
- Set up budget alerts at $50/month
- Cache aggressively

**Contingency:** Budget extra $20-40/month for overage

### 2. Spark Processing Takes Longer
**Risk:** Jobs average 2 hours instead of 1 hour

**Impact:** Double Databricks costs (+$51-171/month)

**Mitigation:**
- Optimize PySpark code with Copilot
- Use larger cluster for large datasets
- Implement job profiling

### 3. Storage Growth Exceeds Projections
**Risk:** Historical data accumulates

**Impact:** +$10-30/month per additional TB

**Mitigation:**
- Implement ADLS lifecycle policies
- Archive old data after 90 days
- Delete redundant intermediate files

### 4. Fabric Capacity Overages
**Risk:** Burst beyond F8 capacity limits

**Impact:** Overage charges ($131/CU-hour)

**Mitigation:**
- Only relevant if using Fabric
- Monitor capacity utilization dashboard
- Upgrade to F16 if consistently over 80%

---

## Recommendations

### For 100-300 Runs/Quarter:

1. **Choose Databricks over Fabric**
   - Saves $569/month ($6,828/year)
   - Better fit for batch ETL workloads

2. **Invest in Cache Optimization**
   - Target 70%+ cache hit rate by Q2
   - Saves $120+/month in Spark costs

3. **Start with Jobs Compute**
   - Use All-Purpose clusters only for development
   - 3x cheaper per hour

4. **Enable Spot Instances**
   - 60% discount on VMs
   - Low risk for 1-hour jobs

5. **Implement Cost Monitoring**
   - Set up Azure Cost Management alerts
   - Review monthly spending in Databricks dashboard
   - Track cache hit rates

6. **Plan for Scale**
   - Current architecture supports 500+ runs/month
   - Costs scale sub-linearly due to caching
   - Can reduce per-run cost by 50% at higher volumes

---

## Summary: Expected Costs

### Conservative Estimate (100 runs/month with 70% cache hit rate):

**Using Microsoft Fabric F8 (Reserved):**

**Quarterly Cost: $2,376**  
**Annual Cost: $9,504**

**Breakdown:**
- Container Apps: $85/month
- ADLS: $30/month
- Copilot SDK: $39/month
- **Fabric F8: $625/month**
- Cosmos DB: $3/month
- Monitoring: $10/month

### Optimistic Estimate (100 runs/month with 85% cache hit rate + optimizations):

**Quarterly Cost: $2,200**  
**Annual Cost: $8,800**

(Savings from container scale-to-zero, reduced storage, etc.)

### Per-Run Cost (at scale):

| Volume | Cost per Run (Fabric) | Cost per Run (Databricks) | Manual Cost |
|--------|----------------------|---------------------------|-------------|
| 33 runs/month | $23.21 | $5.12 | $800 |
| 67 runs/month | $11.54 | $2.90 | $800 |
| 100 runs/month | $7.92 | $2.18 | $800 |
| 200 runs/month | $4.17 | $1.65 | $800 |

**Compare to Manual:** $800 per run → **99% cost reduction** (even with Fabric)

**Key Insight:** Fabric has higher fixed costs but better TCO for Microsoft-first organizations. Can switch to Databricks later if volume justifies optimization.

---

## Next Steps

1. **Start with POC in free/low tiers:**
   - Free Container Apps tier (first 180K vCPU-sec)
   - ADLS free tier (first month)
   - Databricks trial or small cluster

2. **Measure actual usage in Q1:**
   - Track cache hit rates
   - Monitor Spark job durations
   - Assess AI request patterns

3. **Optimize based on data:**
   - Adjust cluster sizes
   - Fine-tune caching strategy
   - Consider Spot instances

4. **Set up cost governance:**
   - Monthly budget alerts
   - Department chargebacks by client
   - Regular cost reviews

---

*This cost analysis will be updated quarterly as we collect actual usage data and pricing changes.*

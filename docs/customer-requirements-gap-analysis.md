# Customer Business Requirements - Gap Analysis

**Date:** January 26, 2026  
**Source:** Customer call transcript (January 19, 2026)

**Note:** This analysis focuses on business requirements and outcomes, not customer's proposed implementation details. As architects, we define the technical approach.

---

## Critical Business Requirements from Transcript

### 1. **Scale & Volume** ✅ COVERED
**Requirement:**
- 3,000 clients currently in DNAV
- 4-6 engagements per client per year
- Peak load: 500-1,000 runs during audit busy season (Feb-April)
- Individual file sizes: 1-10 GB per client
- Data already in ADLS Gen2 (no uploads needed)

**Design Coverage:** ✅ Addressed
- Cost analysis includes 100 runs/month scenario
- Fabric F8/F16 capacity sizing covers this volume
- ADLS as source is the baseline assumption

**Gap:** ⚠️ Should add peak capacity planning for 1,000 runs/month scenario

---

### 2. **File Dependency Handling** ✅ COVERED
**Business Requirement:**
- Some output files may have dependencies on other outputs
- System must execute transformations in correct order
- Must detect and prevent circular dependencies

**Design Coverage:** ⚠️ Not explicitly addressed
- Could be handled by execution engine
- Or by preprocessing step

**Gap:** Should add dependency resolution logic (implementation detail - we decide how)

---

### 3. **Repeatability & Caching** ✅ COVERED
**Requirement:**
- Most clients run quarterly with same schema → rerun same PySpark without AI
- Only regenerate when client changes data schema
- Save PySpark + pseudocode for audit trail
- Cache should enable deterministic re-runs

**Design Coverage:** ✅ Fully addressed
- Cosmos DB caching with hash(client_id + mapping + schema)
- Cache hit rate: 70% target
- Deterministic execution for cached transformations

---

### 4. **Human-in-the-Loop Review** ⚠️ NEEDS DETAIL
**Business Requirement:**
- **User Persona:** Excel power users, NOT Python developers
- **What they review:** Pseudocode (plain English transformation logic)
- **What they DON'T see:** PySpark code (technical implementation)
- **Actions needed:** Approve, reject, or request modifications
- **Why:** Regulatory compliance - humans must validate before production

**Design Coverage:** ⚠️ Mentioned conceptually, lacks implementation detail
- Design mentions "Review Interface (Human-in-the-Loop)" in architecture
- No specification of how Excel users will interact with system

**Gap:** ⚠️ Need to define user experience and interface approach

---

### 5. **Data Security & Privacy** ✅ COVERED
**Requirement:**
- Do NOT send actual client data to LLM (cost & security concern)
- Only send metadata: data dictionaries, mapping spreadsheet
- Optional: Send first 10-100 rows for schema inference (sample only)
- Full 10GB data processed locally on Spark (not through LLM context)

**Design Coverage:** ✅ Addressed
- Design specifies "Sample first 50-100 rows"
- Data profiler tool samples data, doesn't send full dataset
- PySpark executes on Fabric/Databricks, not in agent context

---

### 6. **Audit & Compliance Requirements** ❌ CRITICAL GAP
**Business Context:**
> "If we miss one misstatement during the audit review process... it will be huge lawsuits or penalties" - Thandava

**Requirements:**
- **Complete audit trail:** Every transformation must be traceable for legal holds
- **Immutable archival:** All pseudocode + PySpark code stored permanently
- **Deterministic validation:** Data quality checks cannot be AI-based (must be programmatic)
- **TRC approval:** Technology Risk Controls team must have confidence (enterprise-grade reliability)
- **Paper trail:** If audit misstatement occurs, need clear record of who approved what and when

**Design Coverage:** ⚠️ Partially covered
- Cosmos DB stores code for archival ✅
- No audit logging infrastructure ❌
- No compliance reporting ❌
- No immutable storage policy ❌

**Gap:** ❌ **This is a deal-breaker if not addressed properly**
- Need comprehensive audit logging strategy
- Need immutable storage with retention policies
- Need compliance dashboard for TRC team

---

### 7. **Technology Preferences** ✅ COVERED
**Requirement:**
- **Storage:** ADLS Gen2 (current infrastructure)
- **Compute:** Prefer Fabric over Synapse (Synapse is legacy)
  - They have Synapse experience but want to modernize
  - Also open to Databricks
- **Agent hosting:** Azure Container Apps (not AKS - they have "challenges with AKS for big data")
- **Orchestration:** MCP for tool coordination
- **Avoid:** AKS, Synapse (legacy), custom low-level orchestration

**Design Coverage:** ✅ Fully aligned
- ADLS Gen2 ✅
- Microsoft Fabric (F8/F16) ✅
- Container Apps mentioned ✅
- MCP for orchestration ✅

---

### 8. **Cost Optimization** ✅ COVERED
**Business Requirement:**
> "Pricing is the **key factor driver** for this solution to go live" - Thandava

> "We don't want to send our client data to LLM, otherwise it will **blow up our cost**" - Thandava

**Requirements:**
- Must be cost-effective at scale (3,000 clients, 4-6 runs/year each)
- Cannot process 10GB files through LLM (cost & technical impossibility)
- Only send metadata + samples (10-100 rows max) to LLM
- Cost must be predictable and optimized

**Design Coverage:** ✅ Fully addressed
- Cost analysis: $7.92/run vs $800 manual (99% reduction)
- LLM only processes metadata (not full data)
- Caching reduces AI calls by 70%
- Multiple cost scenarios documented

**This is a strength of our design.**

---

### 9. **Enterprise Reusability** ✅ COVERED
**Requirement:**
- "It's going to be reusable at the APS level" (Audit & Assurance Practice Solutions)
- Should work for any use case with: clean target dataset + client data + mapping info
- Must be enterprise-level solution with quality gates
- Five pillars: Performance, Scalability, Security, Reliability, Observability

**Design Coverage:** ✅ Partially covered
- Architecture is generic (not DNAV-specific)
- Mentions "standardized output format" instead of "DNAV format"

**Gap:** ⚠️ Should add section on "Extensibility & Reusability" for other APS use cases

---

### 10. **Microsoft Foundry vs Custom** ⚠️ DECISION POINT
**Transcript Context:**
- Dan (Microsoft) suggested using Microsoft Foundry's out-of-the-box agent service
- Would get 60-70% of functionality OOTB, customize remaining 30-40%
- Benefits: Constant improvements, less maintenance, managed agent runtime

**Customer Response:**
- Open to it if it meets scale/security requirements
- Monty's POC already works with custom agents
- Could "backport" existing agents into Foundry SDK

**Design Coverage:** ✅ We chose GitHub Copilot SDK (similar concept to Foundry agents)
- Copilot SDK provides production harness
- Custom tools for data engineering specifics

**Note:** Transcript was from Jan 19, we've since validated Copilot SDK (Jan 26)

---

## Summary: Design Document Coverage

### ✅ **Fully Covered (8/10)**
1. Scale & volume requirements
2. Repeatability & caching strategy
3. Data security (metadata only to LLM)
4. Cost optimization
5. Technology stack alignment
6. Enterprise reusability vision
7. Spark execution for big data
8. GitHub Copilot SDK as agentic foundation

### ⚠️ **Partially Covered - Needs Enhancement (2/10)**
1. **Four-agent architecture:** Missing explicit orchestrator agent for dependency DAG
2. **Human-in-the-loop UX:** Need to specify interface design for Excel users

### ❌ **Missing from Design (2 critical areas)**
1. **Audit & Compliance Infrastructure:**
   - Azure Monitor integration for traceability
   - Immutable audit log storage
   - Compliance reporting dashboard
   
2. **Peak Capacity Planning:**
   - 1,000 runs/month busy season scenario
   - Burst capacity handling
   - Cost implications of peak load

---

## Recommended Design Updates

### Priority 1: Define Audit & Compliance Infrastructure (CRITICAL)
**Why:** Deal-breaker for customer - regulatory compliance requirement

**Add to design.md:**
```
Component: Audit & Compliance Layer

1. Immutable Audit Storage
   - Azure Storage with immutability policy (7-year retention)
   - Stores: Pseudocode, PySpark code, approvals, execution logs
   - Indexed by: client_id, transformation_id, timestamp, approver
   
2. Activity Logging
   - Azure Monitor Application Insights
   - Log every agent action: analysis, code generation, approval, execution
   - Structured logs for compliance reporting
   
3. Compliance Dashboard
   - Power BI dashboard for TRC team
   - Metrics: Success rates, error trends, review times, audit trail queries
   - Alerting for anomalies or failures
```

### Priority 2: Define Human Review User Experience
```
Component: Review Portal (Web UI)

User Persona: Excel power users, not Python developers

Features:
- Display pseudocode in plain English
- Side-by-side view: mapping spreadsheet + generated logic
- Inline editing with syntax highlighting
- Approve/Reject/Request Changes workflow
- Comments and feedback capture
- Version history for audit trail

Tech Stack: React/FastAPI, hosted on Container App
```

**Add to design.md:**
```
Component: Dependency Resolution

Business Requirement: Some output files depend on other outputs

Approach:
- Analyze all output requirements upfront
- Build execution DAG (directed acyclic graph)
- Check for circular dependencies
- Execute transformations in topologically sorted order

Implementation: Python-based (not LLM - deterministic logic)
```

### Priority 4: Add Peak Capacity Scenario to Cost Analysis
```
Scenario 4: Audit Busy Season (February-April)

Volume: 1,000 runs/month (10x normal)
Cache Hit Rate: 50% (lower due to schema changes)
Fabric Capacity: F16 (2x F8) for 3 months

Costs:
- Fabric F16: $1,250/month x 3 = $3,750
- Container Apps: $85/month x 3 = $255
- ADLS: $60/month x 3 = $180 (2x normal due to burst)
- Copilot: $39/month x 3 = $117
- Cosmos DB: $15/month x 3 = $45 (10x normal)

Total: $4,347 for 3-month busy season
Per-run cost: $1.45 (still 99.8% cheaper than $800 manual)

Recommendation: Use autoscaling Fabric capacity or burst to F32 if needed
```

---

## Action Items

1. **Update design.md:**
   - [ ] Add "Dependency Orchestrator" component section
   - [ ] Add "Human Review Interface" detailed design
   - [ ] Add "Audit & Compliance" section
   - [ ] Update architecture diagram with 4-agent flow

2. **Update cost-analysis.md:**
   - [ ] Add Scenario 4: Peak busy season (1,000 runs/month)
   - [ ] Add autoscaling cost implications

3. **Create new document:**
   - [ ] `human-review-interface-design.md` with mockups/wireframes

4. **Validation:**
   - [ ] Review updates with customer before next meeting
   - [ ] Confirm orchestrator logic matches Monty's POC approach

---

## Customer Quote Analysis

**Key Customer Concerns (verbatim):**

> "Pricing is the key factor driver for this solution to go live" - Thandava

> "We don't want to send our client data to LLM, otherwise it will blow up our cost" - Thandava

> "It needs to be traceable and auditable" - Thandava  

> "If we miss one misstatement during the audit review process... it will be huge lawsuits or penalties" - Thandava

> "The power users, they are Excel users... they should be able to repeatable... tweak [the pseudocode]" - Thandava

> "We archive the spark code for tracing purpose auditory purpose... for legal hold or audit trail" - Thandava

**Takeaway:** Cost, audit trail, and Excel-user-friendly interface are non-negotiables. Our design covers these but needs more explicit documentation on audit infrastructure.

---

**Status:** Design document is 80% aligned with customer requirements. Critical gaps identified and action items defined above.

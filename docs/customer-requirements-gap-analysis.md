# Customer Business Requirements - Gap Analysis

**Date:** February 6, 2026
**Source:** Customer call transcripts — January 19, 2026 and January 30, 2026

**Note:** This analysis focuses on business requirements and outcomes, not customer's proposed implementation details. As architects, we define the technical approach.

---

## Critical Business Requirements from Transcripts

### 1. **Self-Service for Auditors** ✅ COVERED
**Requirement (Jan 30 — TK):**
> "The main objective from the business sponsors is to make this data engineering self-service for auditors and reduce the dependency on the specialist. Replace the specialist with the agent."

- **Auditors** (Excel power users) should be able to provide data dictionary/inputs and iterate with the agent
- Agent replaces the **specialist** role (data engineers who write PySpark)
- Auditors review pseudocode and output — NOT code
- Feedback loop must be conversational and repeatable

**Design Coverage:** ✅ Addressed in v2.0
- Problem statement frames auditor vs. specialist role change
- Pseudocode review in plain English
- Full loop-back from output review to pseudocode revision

---

### 2. **Scale & Volume** ✅ COVERED
**Requirement (Jan 19, confirmed Jan 30):**
- 3,000 clients currently in DNAV
- 5 engagements per client per year (updated from 4-6)
- ~1,250 runs/month baseline (3,000 × 5 ÷ 12)
- Peak load during audit busy season (Feb-April): potentially higher
- Individual file sizes: 1-10 GB per client
- Data already in ADLS Gen2

**Volume estimate (Jan 30 — Monty):**
> "3,000 clients a year, five runs per client on average, 15,000 / 12 would be a little over 1,000 runs a month, like 1,200-1,250."

**Design Coverage:** ✅ Updated
- Design doc scale targets reflect ~1,250/month
- Cost analysis updated with realistic volume scenarios

---

### 3. **Technology Stack — Use Existing Services** ✅ COVERED (Jan 30)
**Requirement (Jan 30 — TK):**
> "There is strong pushback from our CTO organization to limit our tech stack. For each use case, I cannot introduce a new service."

**Customer's existing tech stack:**
| Service | Role |
|---------|------|
| .NET | Application platform |
| Azure SQL | Primary database |
| Azure Service Bus | Async messaging |
| Azure Functions (Durable) | Compute / long-running workflows |
| AKS | Container orchestration |
| Azure Databricks | Spark notebooks (existing) |
| ADLS Gen2 | Data lake storage |

**Key change from Jan 19:** Customer previously seemed open to Container Apps. Jan 30 transcript makes clear they **will not introduce Container Apps** initially.

**Design Coverage:** ✅ Fully addressed (v3.0)
- Agent runtime: **Azure Durable Functions** (locked in — provides native durable orchestration for human-in-the-loop)
- Container Apps noted as future roadmap option
- Customer tech stack documented in design
- No new services introduced — Cosmos DB, ADLS, Durable Functions, Databricks all already in stack

**Note (Jan 19):** Customer mentioned "challenges with AKS for big data" — this was about Spark processing (solved by Databricks), not about agent hosting.

---

### 4. **Repeatability & Caching** ✅ COVERED
**Requirement (Jan 19 + Jan 30):**
- Most clients run quarterly with same schema → rerun same PySpark without AI
- Only regenerate when client changes data schema
- Save PySpark + pseudocode for audit trail
- Cache should enable deterministic re-runs
- **Entire pipeline (pseudocode → code gen → execution → review) must be repeatable** (Jan 30)

**Design Coverage:** ✅ Fully addressed
- Cosmos DB caching with hash(client_id + mapping + schema)
- Full loop-back from output review to pseudocode revision
- Target cache hit rate: 70% (after initial quarter)

---

### 5. **Cold Start Quarter (0% Cache Hits)** ⚠️ NEW (Jan 30)
**Requirement (Jan 30 — Monty):**
> "In our first release, the first quarter, every single thing is going to be new. So it'll be basically 0 caches."

- Currently using Spark notebooks in Databricks + M code/Power Query
- No existing PySpark scripts to migrate day one
- Could potentially feed existing logic into pseudocode generation as a "nice add-on" (Monty)
- First quarter = ~1,250 runs at 0% cache hit = maximum cost

**Design Coverage:** ✅ Addressed in cost analysis
- Added cold start Q1 scenario
- Migration path noted as future optimization

---

### 6. **Human-in-the-Loop Review** ⚠️ NEEDS UX DETAIL
**Business Requirement (Jan 19 + Jan 30):**
- **User Persona:** Auditors — Excel power users, NOT Python developers
- **What they review:** Pseudocode (Phase 3) and output data (Phase 6)
- **What they DON'T see:** PySpark code
- **Actions needed:** Approve, reject, or request modifications via conversational feedback
- **UI:** Entirely net new — must be built from ground up (confirmed Jan 30)
- **Platform:** .NET (customer's platform)

**Design Coverage:** ⚠️ Workflow is defined, but UI/UX not specified
- Workflow checkpointing with auditor review is designed
- Missing: Interface mockups, .NET integration approach

**Gap:** Need to define review portal UX for Excel-level users

---

### 7. **Code Storage — ADO Repos** ✅ COVERED (Phased)
**Requirement (Jan 30 — TK):**
> "Ultimate goal is all the codes should go to repos. For the audit trail or whatever the purpose."

- Final approved PySpark code should be stored in **Azure DevOps Repos** (not just Cosmos DB)
- Cosmos DB is acceptable as intermediate/runtime cache
- ADO Repos provides: git history, version control, legal hold, audit trail
- Open question: Who reviews PRs? Specialists? Or automated commits?

**Design Coverage:** ✅ Addressed with phased approach (v3.0)
- **Sprint 1:** Cosmos DB as sole code store (3 containers: code-cache, agent-state, audit-trail)
- **Future Sprint:** ADO Repos integration for git-based version history
- `commit_to_ado_repo` MCP tool marked as "Future Sprint"
- **Reason for phasing:** Authenticating from Durable Functions to ADO Repos requires service principal with PAT or OAuth app registration — more complex than Managed Identity. Sprint 1 focuses on proving the core pipeline.
- Customer's goal of "all codes in repos" is honored — just phased after Sprint 1

---

### 8. **Retry Logic (3 Tries)** ✅ COVERED (Jan 30)
**Requirement (Jan 30 — Monty):**
> "Multiple try or retry logic around the reviewer... if it fails after say three tries, then you just say here's the failure message."

**Pattern:**
1. Execute PySpark → if execution fails → pass error log to agent → retry
2. If execution succeeds → run reviewer script (deterministic) → if fails → pass error log back
3. After both succeed → human sees output
4. After 3 total failures → show failure message to auditor

**Design Coverage:** ✅ Fully addressed
- 3-try retry with error log passback in workflow
- Deterministic reviewer script (not AI)
- Failure escalation to auditor after max retries

---

### 9. **MCP Interest from Deloitte** ⚠️ NEEDS DOCUMENTATION
**Requirement (Jan 30 — TK + Monty):**
> "There's a great interest in MCP on the Deloitte side." - Monty

- Customer wants MCP client/server called out explicitly in architecture
- Want to know which Azure services have native MCP servers
- TK: "Wherever it is required, just call that out server and client both"
- MCP is NOT required everywhere — use where it makes sense (Dan's guidance)

**Design Coverage:** ⚠️ MCP tools listed in design, but not mapped to Azure service availability
- MCP tool table exists
- Missing: Which Azure services offer MCP servers vs. direct API calls

**Gap:** Add MCP server availability matrix for Azure services used in this solution

---

### 10. **Data Security & Privacy** ✅ COVERED
**Requirement (Jan 19):**
- Do NOT send actual client data to LLM (cost & security)
- Only send metadata: data dictionaries, mapping spreadsheet
- Sample first 10-100 rows for schema inference
- Full data processed on Spark (not through LLM)

**Design Coverage:** ✅ Addressed

---

### 11. **Audit & Compliance Requirements** ✅ COVERED
**Business Context (Jan 19):**
> "If we miss one misstatement during the audit review process... it will be huge lawsuits or penalties" - TK

**Requirements:**
- Complete audit trail for legal holds
- Immutable archival of pseudocode + PySpark code
- Deterministic validation (not AI-based)
- TRC team confidence
- Paper trail: who approved what, when

**Design Coverage:** ✅ Addressed in v3.0
- **Cosmos DB `audit-trail` container**: Structured JSON events for every approval, tool call, LLM invocation, and execution result — queryable for compliance dashboards
- **ADLS Gen2 immutable storage (WORM policy)**: Long-term archive of code snapshots, execution logs, and approval records for legal hold
- Deterministic reviewer script (not AI)
- ADO Repos for versioned code history (future sprint)

---

### 12. **Cost Optimization** ✅ COVERED
**Requirement (Jan 19 + Jan 30):**
> "Pricing is the key factor driver for this solution to go live" - TK

- Must be cost-effective at ~1,250 runs/month
- LLM cost sensitivity — Monty estimated low 5-figure range for GPT-5.2
- Dan estimated $200-$8K for 600M tokens — noted cheaper model for code gen from pseudocode
- Cost must be predictable and transparent per client

**Design Coverage:** ✅ Updated cost analysis with realistic volumes

---

### 13. **POC Success Criteria** ❌ NEW DELIVERABLE NEEDED
**Requirement (Jan 30 — TK):**
> "The success criteria — how many engagements with the volume? Maybe 3 or 4 with various levels of complexities — low, medium, high."

- 3-4 test engagements at varying complexity levels
- Metrics: latency, scalability, quality
- Detailed pricing for POC
- Developer resources: TK + Monty + possibly 1 more

**Design Coverage:** ❌ Not yet documented
- Need new section or document defining POC success criteria

---

### 14. **Existing Code Migration** ⚠️ FUTURE CONSIDERATION
**Context (Jan 30 — Monty):**
> "Today we have a mixture of Spark notebooks in Databricks and M code and Power Query... day one there's not really a Python job equivalent."

- No existing PySpark to migrate — all new generation
- Could potentially feed existing logic/notebooks into pseudocode generation ("nice add-on")
- Not blocking for POC, but would reduce cold start costs

**Design Coverage:** Not addressed (low priority for POC)

---

### 15. **Enterprise Reusability** ✅ COVERED
**Requirement (Jan 19):**
- Reusable at APS level (Audit & Assurance Practice Solutions)
- Architecture should be generic, not DNAV-specific
- Five pillars: Performance, Scalability, Security, Reliability, Observability

**Design Coverage:** ✅ Architecture is generic

---

### 16. **Agent Framework Decision** ✅ COVERED
**Context (Jan 30):**
- Dan presented Copilot SDK (just announced 2 weeks prior) with Agent Framework as backup
- TK: "provide that alternate agent and also the documentation"
- Monty: If Copilot SDK does MCP natively, separate MCP server not needed

**Design Coverage:** ✅ Decision made
- Agent Framework selected (Copilot SDK GA timeline risk)
- Comparison documented in copilot-sdk-setup.md
- Migration path preserved

---

## Summary: Design Document Coverage

### ✅ **Fully Covered (13/16)**
1. Self-service for auditors
2. Scale & volume (~1,250 runs/month)
3. Technology stack alignment (Durable Functions locked in)
4. Repeatability & caching
5. Cold start quarter (cost scenario)
6. Code storage (Cosmos DB Sprint 1 + ADO Repos future sprint)
7. Retry logic (3 tries with error log passback)
8. Data security (metadata only to LLM)
9. Audit & compliance infrastructure (Cosmos DB audit trail + ADLS WORM archive)
10. Cost optimization
11. Enterprise reusability
12. Agent Framework decision
13. ADO Repos phased approach

### ⚠️ **Partially Covered — Needs Enhancement (2/16)**
1. **Human-in-the-loop UX:** Workflow defined, UI/UX not specified (need .NET integration plan)
2. **MCP server availability:** MCP tools listed, but Azure service availability not mapped

### ❌ **Missing (1 deliverable)**
1. **POC Success Criteria:** Need document defining 3-4 test engagements, complexity levels, metrics

---

## Action Items

1. **Define POC success criteria:**
   - [ ] Create `poc-success-criteria.md` with 3-4 test engagements, metrics, timeline
   - [ ] Include detailed POC pricing

2. **Design human review UX:**
   - [ ] Define review portal for Excel-level auditors
   - [ ] Determine .NET integration approach (embed in existing DNAV platform)

3. **Map MCP server availability:**
   - [ ] Document which Azure services have native MCP servers
   - [ ] Determine where MCP vs. direct API makes sense

4. **Validation:**
   - [ ] Review updated design (v3.0) with customer
   - [ ] Get mapping walkthrough recording from Dalton (or schedule new session)
   - [ ] Get schema stability percentage from Mahesh (for cache hit rate projection)

---

## Customer Quote Analysis

**Key Customer Concerns (verbatim):**

> "The main objective from the business sponsors is to make this data engineering self-service for auditors and reduce the dependency on the specialist." - TK (Jan 30)

> "There is strong pushback from our CTO organization to limit our tech stack. For each use case, I cannot introduce a new service." - TK (Jan 30)

> "Ultimate goal is all the codes should go to repos. For the audit trail." - TK (Jan 30)

> "Pricing is the key factor driver for this solution to go live" - TK (Jan 19)

> "We don't want to send our client data to LLM, otherwise it will blow up our cost" - TK (Jan 19)

> "If we miss one misstatement during the audit review process... it will be huge lawsuits or penalties" - TK (Jan 19)

> "The power users, they are Excel users... they should be able to repeatable... tweak the pseudocode" - TK (Jan 19)

> "In our first release, the first quarter, every single thing is going to be new. So it'll be basically 0 caches." - Monty (Jan 30)

> "There's a great interest in MCP on the Deloitte side." - Monty (Jan 30)

**Takeaway:** Self-service for auditors, existing tech stack constraints, cost transparency, ADO Repos for audit trail, and Excel-friendly UX are the non-negotiables. Design is ~90% aligned after v2.0 updates.

---

**Status:** Design document v3.0 is ~93% aligned with customer requirements. Durable Functions locked in, audit trail redesigned (Cosmos DB + ADLS WORM), ADO Repos phased. Primary remaining gaps are POC success criteria document and human review UX design.

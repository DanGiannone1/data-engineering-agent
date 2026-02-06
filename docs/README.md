# Documentation Overview

This folder contains all planning, design, and strategic documents for the AI-powered data engineering agent project.

## Documents

### Technical Implementation
- **[design.md](./design.md)** - Customer-specific technical design: AKS/Durable Functions + ADO Repos (adapted to customer's existing tech stack)
- **[reference-architecture.md](./reference-architecture.md)** - Reusable reference architecture: Container Apps + GitHub (Microsoft's recommended stack for field/partner reuse)
- **[copilot-sdk-setup.md](./copilot-sdk-setup.md)** - Agent runtime decision log: pivot from GitHub Copilot SDK to Microsoft Agent Framework

### Financial & Analysis
- **[cost-analysis.md](./cost-analysis.md)** - Cost breakdown at realistic volumes (~1,250 runs/month), per-run costs, ROI calculations (v3.0)

### Strategic & Business Case
- **[strategic-business-case.md](./strategic-business-case.md)** - ROI justification, market opportunity, go-to-market strategy, competitive positioning (Microsoft internal)
- **[linkedin-article-agentic-ai.md](./linkedin-article-agentic-ai.md)** - Thought leadership article on agentic harness problem and Microsoft's positioning

### Requirements & Analysis
- **[customer-requirements-gap-analysis.md](./customer-requirements-gap-analysis.md)** - Requirements mapping from both customer calls (~90% coverage), remaining gaps
- **[transcript-2026-01-19.txt](./transcript-2026-01-19.txt)** - First customer call transcript
- **[transcript-2026-01-30.md](./transcript-2026-01-30.md)** - Second customer call transcript (key decisions: tech stack, volumes, ADO repos)

---

## Two Architecture Documents

| Document | Stack | Audience | Purpose |
|----------|-------|----------|---------|
| `design.md` | AKS/Durable Functions + ADO Repos | This customer | Adapted to customer's CTO-approved tech stack |
| `reference-architecture.md` | Container Apps + GitHub | Field teams, partners, other customers | Microsoft's recommended stack for reuse |

Both documents share the same agent workflow (6 phases), Agent Framework runtime, Databricks compute, and Cosmos DB caching. The difference is the hosting and code storage layer.

---

## Document Relationships

```
reference-architecture.md (Reusable Template)
  └─> Generalized for any customer

design.md (Customer-Specific Adaptation)
  ├─ Architecture adapted to customer constraints
  ├─ AKS/Durable Functions (CTO requirement)
  └─ ADO Repos (customer's code platform)

cost-analysis.md (v3.0 — Realistic Volumes)
  └─> strategic-business-case.md (Business Justification)
        ├─ $241-382K 3-year CLV
        ├─ Market opportunity
        └─ Competitive analysis

customer-requirements-gap-analysis.md
  └─> Tracks coverage from both Jan 19 + Jan 30 calls

copilot-sdk-setup.md (Agent Runtime Decision Log)
  └─> Documents pivot from Copilot SDK → Agent Framework
```

---

## Audience Guide

| Document | Primary Audience | Purpose |
|----------|-----------------|---------|
| `design.md` | Customer architects, developers | Customer-specific implementation |
| `reference-architecture.md` | Microsoft field teams, partners | Reusable pattern for other customers |
| `copilot-sdk-setup.md` | Developers | Agent runtime decision log |
| `cost-analysis.md` | Finance, procurement, executives | Budget planning |
| `strategic-business-case.md` | Microsoft leadership, account team | Investment justification |
| `customer-requirements-gap-analysis.md` | Project team | Requirements tracking |
| `linkedin-article-agentic-ai.md` | External audience | Thought leadership |

---

## Status

All documents current as of February 6, 2026.

- [x] Architecture planning complete (v2.0+ — Microsoft Agent Framework)
- [x] Cost analysis validated (v3.0 — realistic volumes, ~1,250 runs/month)
- [x] Agent runtime decision: Microsoft Agent Framework
- [x] Reference architecture for internal reuse (Container Apps + GitHub)
- [x] Business case with updated projections ($241-382K 3-year CLV)
- [x] Gap analysis updated with Jan 30 call findings (~90% coverage)
- [ ] POC success criteria document
- [ ] Human review UX design
- [ ] MCP server availability matrix
- [ ] POC implementation

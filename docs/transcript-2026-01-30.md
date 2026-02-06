# Deloitte DNAV - Agentic Data Modernization: Meeting Transcript

**Date:** January 30, 2026, 5:04 PM
**Duration:** 40 minutes 34 seconds
**Transcription started by:** Aishwarya Umachandran

## Attendees
- Dan Giannone (Microsoft)
- Christina Ye (Microsoft)
- Aishwarya Umachandran (Microsoft)
- Elsa White (Microsoft)
- Rajeev Singh (Microsoft)
- Vallepalli, Thandava "TK" (Deloitte)
- Steele, Montgomery "Monty" (Deloitte)

---

## Problem Statement Recap

**Dan Giannone (0:03):**
Basically, just to recap — you guys have many different clients, all with different inputs, formats, data structures. You have people today that write the PySpark code to transform every client's unique data set into the common DNAV format, which is then used for the actual audit. Goal is to have an agent that does this, so those folks writing the PySpark can go focus on the more valuable work.

**Thandava Vallepalli (0:47):**
One thing I want to add — DNAV currently has two types of roles: **auditors** and **specialists** (also called the support team). The specialists handle data wrangling, data transformation, data engineering. Right now we are using a tool called Omnia Data, which requires PySpark skills — that's why it's all specialist activity.

**The main objective from the business sponsors is to make this data engineering self-service for auditors and reduce the dependency on specialists.** Replace the specialist with the agent — the auditor should be able to provide the data dictionary or whatever inputs, and the agent should be able to wrangle the data. It should be repeatable and adopt feedback from the auditor for course corrections.

---

## Architecture Walkthrough

**Dan Giannone (2:01):**
The source is ADLS — it's got the client data and the client mappings. The general idea:

1. Agent reads the mapping spreadsheet end-to-end and does a small sampling of the actual data
2. Generates pseudocode/business logic
3. **Human-in-the-loop:** Agent shows pseudocode to the auditor for review — approve or request changes, iterate until comfortable
4. Agent generates PySpark and submits the job to an actual Spark cluster (not on the agent runtime — handles data up to 5-10 GB)
5. Intelligent caching — reuse code when client schema unchanged
6. Quality checks and final human review

**Thandava Vallepalli (5:06):**
We also need a **feedback loop after PySpark code execution**, not just after pseudocode. The auditor doesn't have skills to review Spark code, but can review the **output** of execution. If the output doesn't meet requirements, they can go back to pseudocode, do conversational feedback, course corrections, and re-execute. **The entire process 1-2-3-4 should be repeatable.**

---

## Reviewer Agent Clarification

**Montgomery Steele (6:41):**
The **preparer** and the **reviewer** will both be AI agents. But the **reviewer is just a script** — deterministic logic, no AI.

**Dan Giannone (6:53):**
So there's the deterministic review check, but do you also want the auditor to look at the output in addition to those deterministic checks?

**Montgomery Steele (7:11):**
I envision **try/retry logic** around the reviewer:
- If the reviewer's code **fails to execute** → pass error log back to the preparer
- If it **does execute** → the reviewer script runs; if it **fails** → pass error log back
- Once **both succeed** (code executed + review logic passed) → **human sees the output**
- If it **fails after 3 tries** → show failure message to human, who can inspect

**Dan Giannone (7:53):**
That makes sense — SIT (systems integration testing) first, then UAT (user acceptance testing) second.

---

## Compute: Container Apps vs. Existing Tech Stack

**Thandava Vallepalli (11:53):**
Can we use **Azure Functions** or something else instead of Container Apps? We're not currently using Container Apps. Can we leverage Functions or other existing services?

**Dan Giannone (12:24):**
Functions are designed for short-lived processes, whereas agents can run for a couple minutes. There is the concept of **durable functions** though.

**Thandava Vallepalli (12:42):**
Yeah, we are using durable functions.

**Christina Ye (13:09):**
Durable functions have unique use cases — long-running and stateful workflows. Container Apps is great for scaling and lightweight workloads. There's a lot of engineering investment to integrate Container Apps with Foundry — sandbox environments, code interpreter, etc.

**Thandava Vallepalli (14:17):**
I understand the benefits of Container Apps, but **there is strong pushback from our CTO organization to limit our tech stack.** For each use case, we cannot introduce a new service. We have guardrails.

**Dan Giannone (14:54):**
I definitely get that. I would just make your leadership aware that Microsoft is moving in this direction. We can see if we can fit your existing tech stack for this use case.

**Thandava Vallepalli (15:16):**
Future roadmap, definitely. But immediate — we want to leverage the existing tech stack.

### Customer's Current Tech Stack
- **.NET** (platform)
- **SQL**
- **Azure Service Bus** (async transactions)
- **Azure Functions** (main compute)
- **AKS** (Kubernetes)

---

## Human-in-the-Loop UI

**Dan Giannone (15:42):**
What are you envisioning as the user interface for human-in-the-loop? Do you already have a page in your application?

**Thandava Vallepalli (16:26):**
No — this feature is **entirely net new.** We need to build from the ground up.

**Dan Giannone (16:30):**
And the platform is .NET?

**Thandava Vallepalli (16:38):**
Yes — **.NET, SQL, Service Bus, Functions** is the main tech stack.

---

## Code Storage: Cosmos DB vs. ADO Repos

**Thandava Vallepalli (17:12):**
Can't we leverage **ADO (Azure DevOps) repos** for PySpark code instead of Cosmos DB? For audit trail purposes.

**Dan Giannone (17:25):**
I had that same thought. It likely makes more sense to use code repos. We'd need to figure out access — doing pull requests, who would own that.

**Montgomery Steele (17:56):**
Considering the try/retry logic, would it make sense to keep Cosmos DB for **intermediate steps**, with ADO repos for the **final code**?

**Dan Giannone (18:13):**
Who would review the PRs? Specialists, since auditors won't know what they're looking at. Or do we have a dedicated repo where the agent can do PRs without human code review? Interesting question — need to workshop this.

**Thandava Vallepalli (23:48):**
Cosmos DB is fine as an alternate/phase-one approach, but the **ultimate goal is all code should go to repos** for audit trail purposes. Document both options — either Cosmos DB or ADO.

---

## MCP (Model Context Protocol) Discussion

**Thandava Vallepalli (21:15):**
Remember Monty, we discussed MCP to communicate with ADLS, ADO repos, Fabric, etc.

**Montgomery Steele (21:30):**
If the Copilot SDK does that natively, we wouldn't separately need an MCP server. For the agentic backup approach, we should discuss whether MCP makes sense vs. the agents having direct network access.

**Dan Giannone (22:01):**
Some connections might be MCP, others might be direct API calls — depends on the details.

**Montgomery Steele (22:20):**
From TK — there's **great interest in MCP on the Deloitte side.** If there's a use case for it, the business would be very curious to see the application. If worth including, I'll call it out in the tech stack.

**Thandava Vallepalli (24:15):**
Wherever MCP is required, call out **both MCP server and MCP client.** The MCP server should be supported by the respective Azure service (ADLS Gen2, etc.).

**Dan Giannone (25:06):**
It's up to each service whether they have an MCP server. Some of our products have them, others don't. DNAV could also stand up its own MCP server for others to interact with through AI.

**Thandava Vallepalli (26:20):**
The key thing is **MCP server should be available** for the Azure services we're using.

**Dan Giannone (26:22):**
The goal should not be to leverage MCP servers — it should be to do what works best for the use case. But if we can, we should. I'll call that out and do some digging.

---

## Cost and Volume Estimates

**Dan Giannone (27:16):**
I need to update the cost estimates — did the calculation based on 100 runs/month, but you guys said it was more in the hundreds per month. Probably in the range of $5-10K monthly. Directionally, it's not a massive cost use case.

**Montgomery Steele (30:55):**
We're estimating **3,000 clients/year × 5 runs/client = 15,000/year ÷ 12 = ~1,250 runs/month.**

**Dan Giannone (31:09):**
Would those all need tokens, or would many be cache hits?

**Montgomery Steele (31:24):**
I'm assuming **all zero cache hits** (all brand new from the start). Realistically an overestimate, but want to be safe.

**Dan Giannone (31:35):**
Even at 1,200 × 500K tokens = 600 million tokens — that's maybe a couple hundred bucks.

**Montgomery Steele (32:10):**
When I did my estimate using **GPT-5.2**, output pricing is ~$14/million tokens. That got us in the **low 5-figure range.**

**Dan Giannone (32:30):**
The hard part is getting the pseudocode right. You could use a **cheaper model** to take the pseudocode and generate the PySpark — save a good amount.

**Dan Giannone (34:46):**
600 million tokens for GPT-5.2 would be somewhere between **$200 and $8,000.** Initial run would spike, then costs drop. After first quarter: maybe **~$1,000/month.**

**Montgomery Steele (33:15):**
First quarter = **0% cache hits** (all new). After that, depends on what percentage of clients have the same schema quarter to quarter — large number, but don't have the percentage offhand.

### Existing Code Migration
**Dan Giannone (33:39):**
Don't you already have code? Why would all first runs be net new?

**Montgomery Steele (33:56):**
Today we have a mixture of **Spark notebooks in Databricks** and **M code + Power Query.** When we put everything into the new system, day one there's no Python job equivalent. We have the logic — maybe we can think of a way to migrate it (pass previous logic to pseudocode generation). But you'd still have to run the job and make the new script.

---

## POC Requirements

**Thandava Vallepalli (36:24):**
Once we align on architecture and pricing, we are standing by. I need:
1. **Detailed pricing** — cost of this POC, everything
2. **Success criteria** — how many engagements, with volume (3-4 engagements with various complexity levels: low, medium, high)
3. **Metrics** — latency, scalability, quality

**Dan Giannone (37:11):**
Who would be the developers?

**Thandava Vallepalli (37:20):**
Both of us (TK + Monty). We might pull one more person.

---

## Next Steps

1. Dan to send current architecture docs as Word document (draft version)
2. Dan to update architecture with feedback:
   - Call out LLM explicitly in diagram
   - Show auditor interaction in the loop
   - Document Cosmos DB vs. ADO repos options for code storage
   - Call out MCP client/server where applicable
3. Dan to update cost estimates for ~1,250 runs/month with token costs
4. Dan to check for previous mapping walkthrough recording (from Mahesh's session)
5. Schedule 30-minute session for mapping spreadsheet walkthrough if recording unavailable
6. Dalton to schedule follow-up call for next week
7. Define POC success criteria (3-4 engagements, low/medium/high complexity)
8. Find 2-week time slot with 50% developer capacity for code-with

**Aishwarya Umachandran (39:56):**
Has the data changed since last time? We have a version from October.

**Montgomery Steele (40:09):**
No, same set. Might want additional sets as we move on.

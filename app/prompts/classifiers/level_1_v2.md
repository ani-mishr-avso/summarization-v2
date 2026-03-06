### TASK
Analyze the provided meeting transcript and metadata to determine the primary **intent** of the call. Categorize it into one of the four business classifications below.

### CLASSIFICATION DEFINITIONS
1. **AE/Sales**:
    * **Focus**: New business revenue, competitive displacement, and pricing negotiations.
    * **Signal**: Technical discussions serve as "Solutioning" to prove viability for a future purchase. Look for "PO," "POV/POC," or "Budget."
2. **CSM/Post-Sale**:
    * **Focus**: Existing customer health, realization of value, and retention.
    * **Signal**: Technical talk focuses on "Optimization" of an existing service. Look for "Renewal," "EBR/QBR," "Licensing," or "Health Scores".
3. **Internal/Implementation**:
    * **Focus**: The "How" of technical delivery.
    * **Signal**: Use this for **internal-only syncs**, partner-to-partner strategy, or purely technical data-mapping/ETL without a business value component.
4. **SDR/Outbound**:
    * **Focus**: High-velocity outreach.
    * **Signal**: Short duration and focused solely on qualifying a lead or booking a follow-up.

---

### METADATA
* **Participant Domains**: {{ domains }}
* **CRM Opportunity Stage**: {{ crm_stage }}
* **Call Duration (In Minutes)**: {{ duration_mins }}

### TRANSCRIPT EXCERPT
{{ transcript }}

---



### CLASSIFICATION INSTRUCTIONS
1. **Prioritize Intent Over Keywords**: Technical terms like "API," "Collector," or "Mapping" appear in all call types.
    * If the API discussion is to **close a new deal**, it is **Sales**.
    * If the API discussion is to **fix an existing client's health or optimize their environment**, it is **CSM**.
    * If the API discussion is **colleague-to-colleague** regarding a sprint or internal architecture, it is **Internal**.
2. **Apply CRM Weights**: 
    * If **CRM Stage** is "Closed Won," the default should be **CSM/Post-Sale** unless the call is strictly an internal strategy session.
    * If **CRM Stage** is "Discovery," "Negotiation," or "Solutioning," the default is **AE/Sales**.
3. **Analyze Relationship Dynamics**:
    * **Buyer/Seller**: Focus on business cases, timelines, and value realization (Sales/CSM).
    * **Colleague/Partner**: Focus on task completion, technical hurdles, or internal roadmap alignment (Internal).

### OUTPUT FORMAT (JSON Only)
{
  "reasoning": "A concise explanation identifying the 'Goal of the Conversation' and how it aligns with the CRM stage and participant dynamics.",
  "call_type": "STRING",
  "confidence_level": "LOW" | "MEDIUM" | "HIGH" | "VERY HIGH",
  "primary_topics": ["TOPIC1", "TOPIC2"]
}
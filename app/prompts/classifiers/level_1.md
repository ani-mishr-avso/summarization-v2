### TASK
Analyze the provided meeting transcript and metadata to determine the primary purpose of the call. 

### CLASSIFICATION DEFINITIONS
1. **AE/Sales**: Focuses on new business, discovery of pain points, pricing for new deals, or contract negotiations for prospects.
2. **Internal/Implementation**: Focuses on technical setup, data mapping, project blockers, or internal team syncs.
3. **CSM/Post-Sale**: Focuses on existing customer health, QBRs, renewals, expansion of existing accounts, or feature adoption.
4. **SDR/Outbound**: Short, high-velocity calls focused on setting a meeting or initial cold/warm outreach.
5. **Unclassified**

### METADATA
- **Participant Domains**: {{ domains }}
- **CRM Opportunity Stage**: {{ crm_stage }}
- **Call Duration (In Minutes)**: {{ duration_mins }}

### TRANSCRIPT EXCERPT
{{ transcript }}

### INSTRUCTIONS
1. Analyze the relationship between participants. (Are they talking like partners/colleagues or buyer/seller?)
2. Identify keywords. (e.g., "PO", "Discount", "Champion" -> Sales; "Mapping", "API", "Sprint" -> Internal).
3. Provide your output in JSON format only.

### OUTPUT FORMAT
{
  "call_type_reasoning": "A brief explanation of why this classification was chosen based on specific transcript signals.",
  "call_type": "STRING",
  "confidence_level": "LOW" | "MEDIUM" | "HIGH" | "VERY HIGH",
  "participant_roles": {
    "name": "STRING",
    "role": "STRING"
  }
}
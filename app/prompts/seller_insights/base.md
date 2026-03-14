# Role: {{ role_title | default("") }}
{{ role_goal | default("") }}

## Output Constraints
- Output MUST be valid JSON.
- Do NOT include markdown code blocks (e.g., ```json) in the response.
- Do NOT include any preamble or conversational text.
- If a technique is not detected, score it as "Not Observed" and leave evidence as null.

## Evaluation Criteria
Focus specifically on how the seller uses these dimensions to validate technical fit and navigate skepticism:

1. **Labeling**: Did the seller name the prospect's technical concerns or "aha" moments?
2. **Getting to "That's Right"**: Did the seller summarize a complex prospect requirement so well that the prospect responded with "That's right" or an equivalent acknowledgement?
3. **Calibrated Questions**: Did the seller ask "How" or "What" questions to explore how the demonstrated feature fits into the prospect's specific environment?
4. **Mirroring**: Did the seller repeat the prospect's technical requirements or objections to encourage them to provide more detail?
5. **Tactical Empathy**: Did the seller acknowledge the difficulty of the prospect's current manual processes?
6. **Accusation Audit**: Did the seller proactively name potential technical gaps or implementation hurdles?
7. **Black Swan Discovery**: Did the seller uncover a hidden technical constraint or internal stakeholder requirement not previously mentioned?

## Scoring Scale
- **Effective**: Skillful application that led to deeper insight or prospect alignment.
- **Partial**: Attempted the technique, but it was clunky or didn't land effectively.
- **Not Observed**: No evidence of the technique in the transcript.

## JSON Schema
{
  "primary_dimensions": [
{% for dim in primary_dimensions|default([]) %}
    {
      "dimension": "{{ dim }}",
      "score": "Effective" | "Partial" | "Not Observed",
      "excerpts": ["Speaker Name: \"Transcript Excerpt\""],
      "reasoning": "Brief explanation behind the score"
    }{% if not loop.last %},{% endif %}
{% endfor %}
  ],
  "secondary_dimensions": [
{% for dim in secondary_dimensions|default([]) %}
    {
      "dimension": "{{ dim }}",
      "score": "Effective" | "Partial" | "Not Observed",
      "excerpts": ["Speaker Name: \"Transcript Excerpt\""],
      "reasoning": "Brief explanation behind the score"
    }{% if not loop.last %},{% endif %}
{% endfor %}
  ]
}

## Transcript
{{ transcript }}

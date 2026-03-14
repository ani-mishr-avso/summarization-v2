# Role: {{ role_title | default("") }}
{{ role_goal | default("") }}

## Output Constraints
- Output MUST be valid JSON.
- Do NOT include markdown code blocks (e.g., ```json) in the response.
- Do NOT include any preamble or conversational text.
- If a technique is not detected, score it as "Not Observed" and leave evidence as null.

## Evaluation Criteria
Focus specifically on how the seller uses these dimensions to validate technical fit and navigate skepticism:

1. **Labeling**: Did the seller articulate the buyer’s emotions or unspoken feelings using “It seems like…” or “It sounds like…” or equivalent framing?
2. **Getting to "That's Right"**: Did the seller summarize the buyer’s position so accurately that the buyer confirms with “That’s right” or equivalent acknowledgement?
3. **Calibrated Questions**: Did the seller ask open-ended “How” and “What” questions that steer toward the desired outcome?
4. **Mirroring**: Did the seller repeat the last 1–3 critical words to encourage the buyer to elaborate and reveal deeper information?
5. **Tactical Empathy**: Did the seller demonstrate genuine understanding of the buyer’s perspective, emotions, and constraints?
6. **Accusation Audit**: Did the seller preemptively address potential negatives or objections before the buyer raises them?
7. **Black Swan Discovery**: Did the seller uncover unknown unknowns such as hidden constraints, internal politics, or emotional drivers?

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

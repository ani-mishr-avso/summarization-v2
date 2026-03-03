# LLM-as-a-Judge Evaluation Framework

A production-ready evaluation framework for validating structured summaries generated from sales call transcripts using a 3-layer validation system.

## Overview

This framework implements a comprehensive evaluation system with three layers:

1. **Layer 1 - Call Type Validation**: Validates predicted call type based on transcript content
2. **Layer 2 - Schema Validation**: Validates required keys and nested structure correctness  
3. **Layer 3 - LLM-as-Judge Evaluation**: Segment-by-segment evaluation using LLM with type-specific rubrics

## Features

- **Multi-Layer Validation**: Three comprehensive validation layers
- **Type-Specific Rubrics**: Different evaluation criteria for each call type
- **Configurable Metrics**: Core metrics (faithfulness, completeness, factuality) + business-specific metrics
- **Production Ready**: Robust error handling, logging, and configuration
- **Easy to Use**: Simple CLI interface for batch processing

## Supported Call Types

- **AE/Sales**: Discovery, Demo/Evaluation, Proposal, Negotiation
- **CSM/Post-Sale**: General Health Check, QBR
- **Internal/Implementation**: Project meetings and technical discussions
- **SDR/Outbound**: Cold calls and prospecting

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Groq API key:
```bash
export GROQ_API_KEY="your-api-key-here"
```

## Usage

### Command Line Interface

```bash
python cli.py --transcript transcript.txt --output structured_output.json --results results.json
```

#### Arguments

- `--transcript, -t`: Path to the transcript text file (required)
- `--output, -o`: Path to the structured output JSON file (required)  
- `--results, -r`: Path to save evaluation results JSON file (required)
- `--model`: LLM model to use (default: llama-3.1-70b-versatile)
- `--temperature`: Temperature for LLM generation (default: 0.0)
- `--verbose, -v`: Enable verbose logging

### Example

```bash
# Set API key
export GROQ_API_KEY="your-groq-api-key"

# Run evaluation
python cli.py \
  --transcript examples/sample_transcript.txt \
  --output examples/sample_output.json \
  --results results/evaluation_results.json \
  --verbose
```

## Input Format

### Transcript File (.txt)
Plain text file with speaker labels:
```
Speaker1: Hello, this is John from ABC Corp. Thanks for taking the time to meet today.
Speaker2: Hi John, I'm Sarah from XYZ Solutions. Great to connect with you.
Speaker1: We've been looking at various solutions for our sales enablement needs...
```

### Structured Output File (.json)
JSON file with structured output from your summarization tool:
```json
{
  "call_type": "AE/Sales",
  "sub_type": "Discovery/Qualification", 
  "output": {
    "meeting_context": {
      "attendees": ["John", "Sarah"],
      "referral_source": "",
      "initial_rapport": "Positive"
    },
    "smart_summary": ["Initial discovery call to understand needs"],
    "pain_discovery": {
      "current_state": "Using manual processes",
      "pain_points": ["Inefficient workflow", "Lack of automation"],
      "business_impact": "Lost productivity",
      "workarounds": "Manual tracking"
    }
  }
}
```

## Output Format

The evaluation results are saved as JSON with the following structure:

```json
{
  "evaluation_metadata": {
    "timestamp": "2024-02-24T15:40:00",
    "model_used": "llama-3.1-70b-versatile",
    "temperature": 0.0
  },
  "call_type_validation": {
    "predicted_call_type": "AE/Sales",
    "predicted_sub_type": "Discovery/Qualification",
    "confidence": 0.85,
    "validation_passed": true,
    "reasoning": "Found 5/8 keywords for AE/Sales"
  },
  "schema_validation": {
    "schema_passed": true,
    "missing_fields": [],
    "extra_fields": [],
    "reasoning": "Schema validation: 0 missing, 0 extra fields"
  },
  "segment_evaluations": [
    {
      "segment_name": "meeting_context",
      "metrics": {
        "faithfulness": {
          "score": 4,
          "reason": "Content matches transcript accurately"
        },
        "completeness": {
          "score": 3,
          "reason": "Some details missing from transcript"
        }
      },
      "weighted_score": 3.5,
      "llm_response": "..."
    }
  ],
  "overall_score": 4.2
}
```

## Evaluation Metrics

### Core Metrics (1-5 scoring)
- **Faithfulness**: Checks if extracted content is supported by transcript
- **Completeness**: Validates all relevant information is captured
- **Factuality**: Ensures accuracy and truthfulness

### Business-Specific Metrics
- **Business Relevance**: Evaluates business context relevance
- **Action Item Precision**: Measures accuracy of captured action items
- **Action Item Recall**: Measures completeness of captured action items
- **Timeline Accuracy**: Validates timeline capture accuracy

## Configuration

The framework uses `config.py` for all configuration:

- **Model Settings**: LLM model, temperature, API key
- **Call Type Keywords**: Keywords for call type validation
- **Evaluation Rubrics**: Type-specific evaluation criteria and weights
- **Metric Descriptions**: Detailed descriptions for LLM prompts

## Schema Files

Schema files are located in the `output_schema/` directory and define the expected structure for each call type. The framework automatically loads the appropriate schema based on the call type and sub-type.

## Error Handling

The framework handles various error scenarios:

- Missing or malformed input files
- Invalid JSON in structured output
- Missing required fields in schema
- LLM API errors
- Missing API key

## Development

### Adding New Call Types

1. Add schema file to `output_schema/` directory
2. Add call type keywords to `CALL_TYPE_KEYWORDS` in `config.py`
3. Add evaluation rubrics to `RUBRICS` in `config.py`

### Customizing Metrics

Modify the `CORE_METRICS` and `BUSINESS_METRICS` lists in `config.py` to customize which metrics are evaluated.

### Adjusting Weights

Update the `weights` dictionaries in the rubrics to adjust the importance of different metrics for each segment.

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `GROQ_API_KEY` environment variable is set
2. **File Not Found**: Check file paths are correct
3. **JSON Parse Error**: Validate JSON structure in input files
4. **Schema Validation Failed**: Check that structured output matches expected schema

### Debug Mode

Use the `--verbose` flag to enable detailed logging:
```bash
python cli.py --transcript file.txt --output file.json --results results.json --verbose
```

## License

This project is licensed under the MIT License.

## Support

For questions or support, please create an issue in the repository.
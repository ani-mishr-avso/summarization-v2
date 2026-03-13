#!/usr/bin/env python3
"""
LLM-as-a-Judge Evaluation Framework for Sales Call Transcripts

This module implements a 3-layer validation system:
1. Call Type Validation
2. Schema Validation  
3. LLM-as-Judge Segment Evaluation
"""

import json
import os
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI

# Import required libraries
try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    raise ImportError("Please install required dependencies: pip install langchain-groq")

# Import configuration
from config import (
    MODEL_CONFIG, 
    RUBRICS, 
    CALL_TYPE_KEYWORDS,
    CORE_METRICS,
    BUSINESS_METRICS,
    CALL_TYPE_VALIDATION_PROMPTS,
    ACTION_ITEM_EVALUATION_PROMPT
)


class EvaluationEngine:
    """Main evaluation engine implementing 3-layer validation system."""
    
    def __init__(self, model_config: Dict[str, Any] = None, model_family: str = "groq"):
        """Initialize the evaluation engine."""
        self.model_config = model_config or MODEL_CONFIG
        
        if model_family.lower() == "groq":
            # Initialize LLM
            print("Initializing Groq LLM with model:", self.model_config["model_name"])
            self.llm = ChatGroq(
                model=self.model_config["model_name"],
                temperature=self.model_config["temperature"],
                api_key=os.getenv("GROQ_API_KEY"),
                max_tokens=self.model_config.get("max_tokens", 15000),
                reasoning_effort=self.model_config.get("reasoning_effort", "medium"),
                service_tier=self.model_config.get("service_tier", "auto")
            )
        
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=self.model_config["temperature"],
                )
            
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def evaluate_call(self, transcript: str, structured_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main evaluation method implementing all 3 layers.
        
        Args:
            transcript: Raw sales call transcript text
            structured_output: Structured output from summarization tool
            
        Returns:
            Complete evaluation results with all 3 layers
        """
        self.logger.info("Starting evaluation for call type: %s", structured_output.get("call_type", "Unknown"))
        
        # Layer 1: Call Type Validation
        call_type_result = self.validate_call_type(transcript, structured_output)
        
        # Layer 2: Schema Validation
        schema_result = self.validate_schema(structured_output)
        
        # Layer 3: LLM-as-Judge Evaluation (only if schema validation passes)
        segment_results = []
        overall_score = 0.0
        
        if schema_result["schema_passed"]:
            segment_results = self.evaluate_segments(transcript, structured_output)
            overall_score = self.calculate_overall_score(segment_results)
        
        # Combine all results
        evaluation_result = {
            "evaluation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model_config["model_name"],
                "temperature": self.model_config["temperature"]
            },
            "call_type_validation": call_type_result,
            "schema_validation": schema_result,
            "segment_evaluations": segment_results,
            "overall_score": overall_score
        }
        
        self.logger.info("Evaluation completed with overall score: %.2f", overall_score)
        return evaluation_result
    
    def validate_call_type(self, transcript: str, structured_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 1: Validate predicted call type using two-stage LLM-based approach.
        
        Args:
            transcript: Raw sales call transcript text
            structured_output: Structured output containing predicted call type
            
        Returns:
            Call type validation result
        """
        predicted_type = structured_output.get("call_type", "")
        predicted_sub_type = structured_output.get("sub_type", "")
        
        # Stage 1: Main call type classification using transcript summarization
        stage1_result = self._stage1_main_type_classification(transcript)
        
        # Stage 2: Subtype validation (only for AE/Sales calls)
        stage2_result = None
        if stage1_result["predicted_call_type"] == "AE/Sales":
            stage2_result = self._stage2_subtype_validation(transcript)
        
        # Compare predicted vs actual and determine validation result
        main_type_match = stage1_result["predicted_call_type"] == predicted_type
        subtype_match = True
        
        if stage2_result and predicted_sub_type:
            subtype_match = stage2_result["predicted_subtype"] == predicted_sub_type
        
        # Calculate overall confidence
        main_confidence = stage1_result["confidence"]
        subtype_confidence = stage2_result["confidence"] if stage2_result else 0.0
        
        if stage2_result:
            overall_confidence = (main_confidence + subtype_confidence) / 2
        else:
            overall_confidence = main_confidence
        
        validation_passed = main_type_match and subtype_match
        
        return {
            "predicted_call_type": predicted_type,
            "predicted_sub_type": predicted_sub_type,
            "llm_predicted_call_type": stage1_result["predicted_call_type"],
            "llm_predicted_subtype": stage2_result["predicted_subtype"] if stage2_result else None,
            "confidence": round(overall_confidence, 2),
            "validation_passed": validation_passed,
            "stage1_result": stage1_result,
            "stage2_result": stage2_result,
            "reasoning": f"Main type match: {main_type_match}, Subtype match: {subtype_match}"
        }
    
    def _stage1_main_type_classification(self, transcript: str) -> Dict[str, Any]:
        """Stage 1: Classify main call type using transcript summarization."""
        try:
            # Create transcript summary for efficient analysis
            summary = self._create_transcript_summary(transcript)
            
            # Build prompt for main type classification
            prompt = CALL_TYPE_VALIDATION_PROMPTS["stage1_main_type"].format(
                transcript_summary=transcript
            )
            
            # Get LLM response
            response = self._get_llm_response(prompt)
            
            # Parse response
            return self._parse_call_type_response(response, "main_type")
            
        except Exception as e:
            self.logger.error("Error in stage 1 call type classification: %s", e)
            return {
                "predicted_call_type": "Unknown",
                "confidence": 1.0,
                "reasoning": f"Error in LLM classification: {str(e)}"
            }
    
    def _stage2_subtype_validation(self, transcript: str) -> Dict[str, Any]:
        """Stage 2: Validate AE/Sales subtype using full transcript."""
        try:
            # Build prompt for subtype classification
            prompt = CALL_TYPE_VALIDATION_PROMPTS["stage2_subtype"].format(
                transcript=transcript
            )
            
            # Get LLM response
            response = self._get_llm_response(prompt)
            
            # Parse response
            return self._parse_call_type_response(response, "subtype")
            
        except Exception as e:
            self.logger.error("Error in stage 2 subtype classification: %s", e)
            return {
                "predicted_subtype": "Unknown",
                "confidence": 1.0,
                "reasoning": f"Error in LLM classification: {str(e)}"
            }
    
    def _create_transcript_summary(self, transcript: str) -> str:
        """Create a concise summary of the transcript for efficient analysis."""
        # If transcript is short, use it as-is
        if len(transcript) < 3000:
            return transcript
        
        # For longer transcripts, extract key segments
        lines = transcript.split('\n')
        total_lines = len(lines)
        
        # Extract beginning, middle, and end segments
        start_segment = '\n'.join(lines[:min(20, total_lines//3)])
        middle_segment = '\n'.join(lines[total_lines//3:2*total_lines//3])
        end_segment = '\n'.join(lines[-min(20, total_lines//3):])
        
        # Combine segments with separators
        summary = f"""
        BEGINNING:
        {start_segment}
        
        MIDDLE:
        {middle_segment}
        
        END:
        {end_segment}
        """
        
        return summary
    
    def _parse_call_type_response(self, response: str, response_type: str) -> Dict[str, Any]:
        """Parse LLM response for call type classification."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                
                if response_type == "main_type":
                    return {
                        "predicted_call_type": parsed.get("predicted_call_type", "Unknown"),
                        "confidence": parsed.get("confidence", 3.0),
                        "reasoning": parsed.get("reasoning", "No reasoning provided")
                    }
                else:  # subtype
                    return {
                        "predicted_subtype": parsed.get("predicted_subtype", "Unknown"),
                        "confidence": parsed.get("confidence", 3.0),
                        "reasoning": parsed.get("reasoning", "No reasoning provided")
                    }
        
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        if response_type == "main_type":
            # Look for call type in response
            call_types = ["AE/Sales", "CSM/Post-Sale", "Internal/Implementation", "SDR/Outbound"]
            predicted_type = "Unknown"
            for call_type in call_types:
                if call_type.lower() in response.lower():
                    predicted_type = call_type
                    break
            
            # Look for confidence score
            confidence_match = re.search(r'confidence[:\s]+(\d+)', response, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 3.0
            
            return {
                "predicted_call_type": predicted_type,
                "confidence": max(1.0, min(5.0, confidence)),
                "reasoning": "Parsed from text response"
            }
        else:
            # Look for subtype in response
            subtypes = ["Discovery/Qualification", "Demo/Evaluation", "Proposal/Business Case", "Negotiation/Close"]
            predicted_subtype = "Unknown"
            for subtype in subtypes:
                if subtype.lower() in response.lower():
                    predicted_subtype = subtype
                    break
            
            # Look for confidence score
            confidence_match = re.search(r'confidence[:\s]+(\d+)', response, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 3.0
            
            return {
                "predicted_subtype": predicted_subtype,
                "confidence": max(1.0, min(5.0, confidence)),
                "reasoning": "Parsed from text response"
            }
    
    def validate_schema(self, structured_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 2: Validate schema structure and required fields.
        
        Args:
            structured_output: Structured output to validate
            
        Returns:
            Schema validation result
        """
        call_type = structured_output.get("call_type", "")
        sub_type = structured_output.get("sub_type", "")
        
        # Load expected schema
        expected_schema = self._load_schema(call_type, sub_type)
        if not expected_schema:
            return {
                "schema_passed": False,
                "missing_fields": [],
                "extra_fields": [],
                "reasoning": f"No schema found for {call_type}/{sub_type}"
            }
        
        # Validate structure
        missing_fields = []
        extra_fields = []
        
        # Check required fields in main structure
        required_main_fields = ["call_type", "output"]  # ["call_type", "sub_type", "output"]
        for field in required_main_fields:
            if field not in structured_output:
                missing_fields.append(f"main.{field}")
        
        # Check output structure
        if "output" in structured_output:
            output_data = structured_output["output"]
            expected_output = expected_schema.get("output", {})
            
            # Recursively validate nested structure
            missing, extra = self._validate_nested_structure(output_data, expected_output, "output")
            missing_fields.extend(missing)
            extra_fields.extend(extra)
        
        schema_passed = len(missing_fields) == 0
        
        return {
            "schema_passed": schema_passed,
            "missing_fields": missing_fields,
            "extra_fields": extra_fields,
            "reasoning": f"Schema validation: {len(missing_fields)} missing, {len(extra_fields)} extra fields"
        }
    
    def _validate_nested_structure(self, actual: Dict[str, Any], expected: Dict[str, Any], path: str) -> Tuple[List[str], List[str]]:
        """Recursively validate nested structure."""
        missing = []
        extra = []
        
        # Check for missing fields
        for key, expected_value in expected.items():
            if key not in actual:
                missing.append(f"{path}.{key}")
            elif isinstance(expected_value, dict) and isinstance(actual.get(key), dict):
                # Recursively validate nested dict
                sub_missing, sub_extra = self._validate_nested_structure(
                    actual[key], expected_value, f"{path}.{key}"
                )
                missing.extend(sub_missing)
                extra.extend(sub_extra)
        
        # Check for extra fields
        for key in actual:
            if key not in expected:
                extra.append(f"{path}.{key}")
        
        return missing, extra
    
    def _load_schema(self, call_type: str, sub_type: str) -> Optional[Dict[str, Any]]:
        """Load schema for given call type and sub-type."""
        # Handle calls without subtypes (like Internal/Implementation)
        if not sub_type or sub_type.strip() == "":
            schema_file = f"output_schema/{call_type.lower().replace('/', '_')}.json"
        else:
            schema_file = f"output_schema/{call_type.lower().replace('/', '_')}_{sub_type.lower().replace('/', '_').replace(' ', '_')}.json"
        
        try:
            with open(schema_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Schema file not found: %s", schema_file)
            return None
        except json.JSONDecodeError as e:
            self.logger.error("Error parsing schema file %s: %s", schema_file, e)
            return None
    
    def evaluate_segments(self, transcript: str, structured_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Layer 3: LLM-as-Judge segment-by-segment evaluation.
        
        Args:
            transcript: Raw sales call transcript text
            structured_output: Structured output to evaluate
            
        Returns:
            List of segment evaluation results
        """
        call_type = structured_output.get("call_type", "")
        sub_type = structured_output.get("sub_type", "")
        
        # Get rubric for this call type
        if sub_type == "" or sub_type is None:
            rubric = RUBRICS.get(call_type, {})
        else:
            rubric = RUBRICS.get(call_type, {}).get(sub_type, {})
        if not rubric:
            self.logger.warning("No rubric found for %s/%s", call_type, sub_type)
            return []
        
        output_data = structured_output.get("output", {})
        segment_results = []
        
        # Evaluate each segment
        for segment_name, segment_data in output_data.items():
            if segment_name in rubric.get("segments", {}):
                segment_rubric = rubric["segments"][segment_name]
                evaluation = self._evaluate_segment(
                    transcript, segment_name, segment_data, segment_rubric, call_type, sub_type
                )
                segment_results.append(evaluation)
        
        return segment_results
    
    def _evaluate_segment(self, transcript: str, segment_name: str, segment_data: Any, rubric: Dict[str, Any], call_type: str, sub_type: str) -> Dict[str, Any]:
        """Evaluate a single segment using LLM-as-Judge."""
        
        # Check if this is an action item segment that needs special evaluation
        if self._is_action_item_segment(segment_name):
            # Use new action item evaluation method
            metric_scores = self._evaluate_action_item_segment(transcript, segment_name, segment_data, rubric.get("description", ""))
            weighted_score = self._calculate_weighted_score(metric_scores, rubric.get("weights", {}))
            
            return {
                "segment_name": segment_name,
                "metrics": metric_scores,
                "weighted_score": round(weighted_score, 2),
                "llm_response": "Action item evaluation with mathematical precision/recall calculation"
            }
        
        # Use traditional LLM evaluation for other segments
        # Prepare segment content for evaluation
        if isinstance(segment_data, list):
            segment_text = "\n".join(str(item) for item in segment_data)
        elif isinstance(segment_data, dict):
            segment_text = json.dumps(segment_data, indent=2)
        else:
            segment_text = str(segment_data)
        
        # Get metrics for this segment
        metrics = rubric.get("metrics", CORE_METRICS)
        segment_description = rubric.get("description", "")

        segment_output_structure = self._load_schema(call_type, sub_type)
        segment_output_structure = segment_output_structure.get("output", {}).get(segment_name, {}) if segment_output_structure else {}
        segment_output_structure = json.dumps(segment_output_structure, indent=2)
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            transcript, segment_name, segment_text, metrics, segment_description, segment_output_structure
        )
        
        # Get LLM response
        response = self._get_llm_response(prompt)
        
        # Parse response and calculate scores
        metric_scores = self._parse_llm_response(response, metrics)
        weighted_score = self._calculate_weighted_score(metric_scores, rubric.get("weights", {}))
        
        return {
            "segment_name": segment_name,
            "metrics": metric_scores,
            "weighted_score": round(weighted_score, 2),
            "llm_response": response
        }
    
    def _build_evaluation_prompt(self, transcript: str, segment_name: str, segment_text: str, metrics: List[str], segment_description: str = "", segment_output_structure: str = "") -> str:
        """Build evaluation prompt for LLM."""
        
        metrics_description = "\n".join([f"- {metric}" for metric in metrics])
        
        # prompt = f"""
        # You are an expert evaluator for sales call transcript analysis.
        # Your task is to evaluate the quality of extracted information from a sales call transcript.
        # Extracted information is bifurcated into multiple segment. Given the segment name, segment description,
        # extracted information for that segment and entire transcript perform the evaluation.
        # Evaluation of the extracted information should be based on Segment Description.
        # If the required information as per description is not present in the transcript, then that information should not be considered in evaluation and score should be based on information supported by transcript.
        # Whererever SEGMENT_OUTPUT_STRUCTURE is provided, use that structure to evaluate the extracted information. If the structure is not provided, evaluate based on segment description.

        # TRANSCRIPT:
        # {transcript}

        # SEGMENT NAME: {segment_name}
        # SEGMENT DESCRIPTION: {segment_description}
        # SEGMENT OUTPUT STRUCTURE: {segment_output_structure}
        # EXTRACTED CONTENT:
        # {segment_text}

        # EVALUATION METRICS:
        # {metrics_description}

        # Use below scoring rubric for each metric and along with score provide a brief reason for the score (1-2 sentences):

        # Metric: Faithfulness (accuracy of extracted information relative to transcript)
        # A score from 1-5 (1 = Poor, 5 = Excellent)
        #     Score 1: The summary attributes statements to the wrong meeting or invents an entirely false narrative.
        #     Score 2: Contains multiple facts or figures that contradict the transcript or were never discussed.
        #     Score 3: Most info is correct, but includes 1-2 significant claims (like a specific price point) not found in the transcript
        #     Score 4: 95%+ grounded. Contains a minor non-factual embellishment (e.g., "The mood was light") that doesn't impact business data.
        #     Score 5: 100% of claims are directly supported by the transcript. No external information added.
        
        # Metric: Completeness (degree to which all relevant information is captured and no important information is omitted)
        # A score from 1-5 (1 = Poor, 5 = Excellent)
        #     Score 1: Fails to capture the primary outcome or purpose of the call. The summary is unusable for a CRM.
        #     Score 2: Only captures surface-level "small talk." High-value business context is ignored
        #     Score 3: Captures the "gist" but misses a major thematic pillar (e.g., missed the specific technical blocker).
        #     Score 4: Most key points captured; one minor detail (e.g., a secondary stakeholder mention) was omitted.
        #     Score 5: All key sales markers (Pain, Budget, Competitors, Decision Logic) mentioned are captured in detail.
        
        # Metric: Business Relevance (the degree to which the extracted information is relevant and actionable for business decision-making)
        # A score from 1-5 (1 = Poor, 5 = Excellent)
        #     Score 1: The summary captures only high-impact business drivers (Pain, Value, Decision Criteria). Zero "fluff" or irrelevant small talk.
        #     Score 2: Important business drivers are buried under a narrative summary of the entire conversation.
        #     Score 3: Captures the business objective but includes a significant amount of "noise" (e.g., long descriptions of weather or rapport-building).
        #     Score 4: Focuses on business context with very minor inclusions of non-essential details.
        #     Score 5: All key sales markers (Pain, Budget, Competitors, Decision Logic) mentioned are captured in detail.

        # Format your response as JSON:
        # {{
        #     "metrics": {{
        #         "metric_name": {{
        #             "score": number,
        #             "reason": "text"
        #         }}
        #     }}
        # }}

        # Be objective and focus on the quality of information extraction relative to the transcript.
        # """

        prompt = f"""
        You are a segment-level evaluator for structured sales call transcript analysis.

        Your task is to evaluate the quality of extracted information for ONE specific segment.

        This evaluation is strictly segment-scoped.
        Do NOT evaluate beyond the boundaries defined for this segment.

        You are given:

        - Full transcript
        - Segment name
        - Segment description
        - Optional segment output structure
        - Extracted content for this segment

        ------------------------------------------------------------
        EVALUATION RULES (MANDATORY)
        ------------------------------------------------------------

        1. Segment Boundary Rule

        Evaluate ONLY what is required by:
        - SEGMENT DESCRIPTION
        - SEGMENT OUTPUT STRUCTURE (if provided)

        Do NOT introduce expectations beyond these definitions.
        Do NOT apply generic sales-summary standards unless explicitly required in the segment description.

        If stakeholders, pricing, renewal dates, decision criteria, pain points, etc. are not required by this segment,
        their absence MUST NOT reduce the score.

        ------------------------------------------------------------

        2. Structured Segment Rule

        If SEGMENT OUTPUT STRUCTURE is provided:

        - Treat it as the strict contract.
        - Evaluate completeness ONLY for the keys defined in that structure.
        - Do NOT penalize for missing information outside those keys.
        - Do NOT reward extra information outside the structure unless explicitly required.

        If a field exists in the structure:
        - Check whether it is supported by the transcript.
        - Check whether required information for that field is missing (only if present in transcript).

        ------------------------------------------------------------

        3. Unstructured Segment Rule

        If SEGMENT OUTPUT STRUCTURE is NOT provided:

        - Evaluate only based on SEGMENT DESCRIPTION.
        - Do NOT infer additional required components.
        - Do NOT evaluate against general CRM or sales expectations unless described.

        ------------------------------------------------------------

        4. Transcript Grounding Rule

        All factual claims in the extracted content must be verifiable in the transcript.

        If the segment requires interpretation (as defined in the segment description),
        inference is allowed provided it is reasonably supported by transcript evidence.

        Only penalize Faithfulness if:
        - The inference contradicts the transcript
        - The inference has no reasonable supporting evidence
        - The inference exaggerates the transcript signals

        If the transcript does NOT contain certain expected information:
        - Do NOT penalize Completeness for its absence.

        ------------------------------------------------------------
        INPUTS
        ------------------------------------------------------------

        TRANSCRIPT:
        {transcript}

        SEGMENT NAME:
        {segment_name}

        SEGMENT DESCRIPTION:
        {segment_description}

        SEGMENT OUTPUT STRUCTURE:
        {segment_output_structure}

        EXTRACTED CONTENT:
        {segment_text}

        EVALUATION METRICS:
        {metrics_description}

        ------------------------------------------------------------
        SCORING METRICS
        ------------------------------------------------------------

        For each metric:
        - Assign a score from 1 to 5.
        - Provide a concise justification (1 to 2 sentences). Base reasoning strictly on the segment scope.
        - Provide Specific detail i.e. for Faithfulness: hallucination, for completeness: Omission, for Business Relevance: irrelevant_information. Do NOT provide generic feedback like "good job" or "needs improvement" without specific details. Nothing required for Conciseness.

        ------------------------------------------------------------

        Metric: Faithfulness
        Definition: Accuracy of extracted content relative to the transcript.

        Score 1: Major fabrication or incorrect attribution.
        Score 2: Multiple unsupported or contradictory claims.
        Score 3: Mostly accurate but contains at least one significant unsupported or inferred claim.
        Score 4: Nearly fully grounded with only minor non-material inference.
        Score 5: All claims directly supported by the transcript.

        ------------------------------------------------------------

        Metric: Completeness
        Definition: Degree to which the extracted content captures all information required by this segment and supported by the transcript.

        Score 1: Fails to capture the primary required information for this segment.
        Score 2: Captures limited required information; major required elements missing.
        Score 3: Captures main required elements but misses at least one important component.
        Score 4: Captures almost all required elements; only minor omissions.
        Score 5: Fully captures all information required by the segment description and/or output structure that is present in the transcript.

        Important:
        Completeness must be evaluated ONLY within this segment’s defined scope.

        ------------------------------------------------------------

        Metric: Business Relevance
        Definition: Degree to which the extracted content is focused, decision-useful, and free from unnecessary information within this segment.

        Score 1: Mostly irrelevant or unusable for this segment.
        Score 2: Important segment-specific information is buried under noise.
        Score 3: Core information present but includes noticeable unnecessary content.
        Score 4: Strong focus with minimal irrelevant details.
        Score 5: Fully focused and concise for this segment’s purpose.

        Metric: Conciseness
        Definition: Evaluate how efficiently the response delivers relevant information without unnecessary verbosity, redundancy, or tangential content. Conciseness measures informational density, not length alone. A concise response provides sufficient detail to be complete, but avoids filler, repetition, or over explanation.

        Score 1: Very Low Conciseness. Majority of the response includes filler, repetition, or irrelevant content. Poor signal-to-noise ratio.
        Score 2: Low Conciseness. Significant verbosity, repeated points, or unnecessary elaboration. Multiple sections could be removed without affecting completeness.
        Score 3: Moderately Concise. Noticeable redundancy, mild repetition, or limited tangential content. Some sections could be shortened without losing meaning.
        Score 4: Mostly Concise. Minor verbosity or small redundant phrases, but overall efficient and focused. No meaningful tangents.
        Score 5: Highly Concise. The response contains only task-relevant information. No redundancy, filler, repetition, or unnecessary elaboration. Efficient and tightly scoped.


        ------------------------------------------------------------
        OUTPUT FORMAT (STRICT JSON ONLY)
        ------------------------------------------------------------

        {{
        "metrics": {{
            "Faithfulness": {{
            "score": number,
            "reason": "text",
            "hallucination": "specific fabricated or unsupported claim if score < 5, else 'None'"
            }},
            "Completeness": {{
            "score": number,
            "reason": "text",
            "omission": "specific missing required information if score < 5, else 'None'"
            }},
            "Business Relevance": {{
            "score": number,
            "reason": "text",
            "irrelevant_information": "specific irrelevant content if score < 5, else 'None'"
            }},
            "Conciseness": {{
            "score": number,
            "reason": "text"
            }}
        }}
        }}

        Do not output any text outside this JSON.
        Do not restate instructions.
        Evaluate only this segment.
        """
        
        return prompt
    
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM."""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            self.logger.error("Error getting LLM response: %s", e)
            return f"Error: {str(e)}"
    
    def _parse_llm_response(self, response: str, metrics: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse LLM response and extract metric scores."""
        metric_scores = {}
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                return parsed.get("metrics", {})
            else:
                resp = re.sub(r"```json|```", "", response).strip()
                parsed = json.loads(resp)
                return parsed.get("metrics", {})
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        for metric in metrics:
            score_match = re.search(rf'{metric}.*?score[:\s]+(\d+)', response, re.IGNORECASE)
            reason_match = re.search(rf'{metric}.*?reason[:\s]+(.+?)(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
            
            score = int(score_match.group(1)) if score_match else 3  # Default to 3
            reason = reason_match.group(1).strip() if reason_match else "No reason provided"

            specific_details = ""
            specific_details_key = ""
            if metric.lower() == "faithfulness":
                hallucination_match = re.search(r'hallucination[:\s]+(.+?)(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
                specific_details = hallucination_match.group(1).strip() if hallucination_match else "None"
                specific_details_key = "hallucination"
            elif metric.lower() == "completeness":
                omission_match = re.search(r'omission[:\s]+(.+?)(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
                specific_details = omission_match.group(1).strip() if omission_match else "None"
                specific_details_key = "omission"
            elif metric.lower() == "business relevance":
                irrelevant_match = re.search(r'irrelevant_information[:\s]+(.+?)(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
                specific_details = irrelevant_match.group(1).strip() if irrelevant_match else "None"
                specific_details_key = "irrelevant_information"
            else:
                specific_details_key = "specific_details"
                specific_details = "N/A for this metric"
            
            metric_scores[metric] = {
                "score": max(1, min(5, score)),  # Ensure score is between 1-5
                "reason": reason,
                specific_details_key: specific_details
            }
        
        return metric_scores
    
    def _evaluate_action_item_segment(self, transcript: str, segment_name: str, segment_data: Any, segment_description: str) -> Dict[str, Dict[str, Any]]:
        """Evaluate action item segments with LLM-extracted counts and Python calculations."""
        
        # Prepare segment content for evaluation
        if isinstance(segment_data, list):
            segment_text = "\n".join(str(item) for item in segment_data)
        elif isinstance(segment_data, dict):
            segment_text = json.dumps(segment_data, indent=2)
        else:
            segment_text = str(segment_data)
        
        # Build action item evaluation prompt
        prompt = ACTION_ITEM_EVALUATION_PROMPT.format(
            transcript=transcript,
            segment_name=segment_name,
            segment_text=segment_text,
            segment_description=segment_description
        )
        
        # Get LLM response
        response = self._get_llm_response(prompt)
        
        # Parse counts and timeline accuracy from LLM response
        result = self._parse_action_item_counts_with_timeline(response)
        
        # Calculate precision and recall mathematically
        precision = result["correct_items"] / result["total_predicted_items"] if result["total_predicted_items"] > 0 else 0
        recall = result["captured_items"] / result["total_actual_items"] if result["total_actual_items"] > 0 else 0
        
        # Convert to 1-5 scale
        precision_score = 1 + (precision * 4)
        recall_score = 1 + (recall * 4)
        
        # Get factuality score from LLM
        # factuality_result = self._evaluate_factuality_only(transcript, segment_data)
        
        return {
            "precision": {
                "score": round(precision_score, 2),
                "reason": f"Correct: {result['correct_items']}/{result['total_predicted_items']} items. {result['analysis']}"
            },
            "recall": {
                "score": round(recall_score, 2), 
                "reason": f"Captured: {result['captured_items']}/{result['total_actual_items']} items. {result['analysis']}"
            },
            # "factuality": factuality_result,
            "timeline_accuracy": {
                "score": result["timeline_accuracy_score"],
                "reason": result["timeline_accuracy_reason"]
            },
            "owner_attribution": {
                "score": result["owner_attribution_score"],
                "reason": result["owner_attribution_reason"]
            }
        }
    
    def _parse_action_item_counts_with_timeline(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract counts, timeline accuracy, and owner attribution."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
            else:
                resp = re.sub(r"```json|```", "", response).strip()
                parsed = json.loads(resp)
            return {
                "total_actual_items": parsed.get("total_actual_items", 0),
                "captured_items": parsed.get("captured_items", 0),
                "correct_items": parsed.get("correct_items", 0),
                "total_predicted_items": parsed.get("total_predicted_items", 0),
                "timeline_accuracy_score": parsed.get("timeline_accuracy_score", 3.0),
                "timeline_accuracy_reason": parsed.get("timeline_accuracy_reason", "No reason provided"),
                "owner_attribution_score": parsed.get("owner_attribution_score", 3.0),
                "owner_attribution_reason": parsed.get("owner_attribution_reason", "No reason provided"),
                "analysis": parsed.get("analysis", "No analysis provided")
            }
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        result = {
            "total_actual_items": 0,
            "captured_items": 0,
            "correct_items": 0,
            "total_predicted_items": 0,
            "timeline_accuracy_score": 3.0,
            "timeline_accuracy_reason": "Parsed from text response",
            "owner_attribution_score": 3.0,
            "owner_attribution_reason": "Parsed from text response",
            "analysis": "No analysis provided"
        }
        
        # Extract counts
        count_fields = [
            ("total_actual_items", r'total_actual_items[:\s]+(\d+)'),
            ("captured_items", r'captured_items[:\s]+(\d+)'),
            ("correct_items", r'correct_items[:\s]+(\d+)'),
            ("total_predicted_items", r'total_predicted_items[:\s]+(\d+)')
        ]
        
        for field, pattern in count_fields:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result[field] = int(match.group(1))
        
        # Extract timeline accuracy
        timeline_match = re.search(r'timeline_accuracy_score[:\s]+(\d+)', response, re.IGNORECASE)
        if timeline_match:
            result["timeline_accuracy_score"] = float(timeline_match.group(1))
        
        # Extract owner attribution
        owner_match = re.search(r'owner_attribution_score[:\s]+(\d+)', response, re.IGNORECASE)
        if owner_match:
            result["owner_attribution_score"] = float(owner_match.group(1))
        
        return result
    
    def _evaluate_factuality_only(self, transcript: str, segment_data: Any) -> Dict[str, Any]:
        """Evaluate only factuality for action item segments."""
        
        # Prepare segment content for evaluation
        if isinstance(segment_data, list):
            segment_text = "\n".join(str(item) for item in segment_data)
        elif isinstance(segment_data, dict):
            segment_text = json.dumps(segment_data, indent=2)
        else:
            segment_text = str(segment_data)
        
        # Build factuality evaluation prompt
        prompt = f"""
        You are an expert evaluator for sales call transcript analysis.
        
        TRANSCRIPT:
        {transcript}
        
        SEGMENT: factuality evaluation
        EXTRACTED CONTENT:
        {segment_text}
        
        TASK: Evaluate the factuality of the extracted content.
        
        Assess whether the extracted information is accurate and truthful relative to the transcript.
        
        Return JSON:
        {{
            "score": number (1-5),
            "reason": "text"
        }}
        
        Be objective and focus on the accuracy of information extraction relative to the transcript.
        """
        
        # Get LLM response
        response = self._get_llm_response(prompt)
        
        # Parse response
        try:
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                return {
                    "score": parsed.get("score", 3.0),
                    "reason": parsed.get("reason", "No reason provided")
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        score_match = re.search(r'score[:\s]+(\d+)', response, re.IGNORECASE)
        reason_match = re.search(r'reason[:\s]+(.+?)(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
        
        score = float(score_match.group(1)) if score_match else 3.0
        reason = reason_match.group(1).strip() if reason_match else "No reason provided"
        
        return {
            "score": max(1.0, min(5.0, score)),
            "reason": reason
        }
    
    def _is_action_item_segment(self, segment_name: str) -> bool:
        """Check if segment is an action item segment that needs special evaluation."""
        action_item_segments = [
            "next_steps", "path_to_close", "action_plan", 
            "joint_action_plan", "action_items", "outcome_metrics"
        ]
        return segment_name in action_item_segments
    
    def _calculate_weighted_score(self, metric_scores: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> float:
        """Calculate weighted score for a segment."""
        if not metric_scores:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, data in metric_scores.items():
            weight = weights.get(metric, 1.0)  # Default weight = 1.0
            total_score += data["score"] * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def calculate_overall_score(self, segment_results: List[Dict[str, Any]]) -> float:
        """Calculate overall weighted score across all segments."""
        if not segment_results:
            return 0.0
        
        total_score = sum(result["weighted_score"] for result in segment_results)
        return total_score / len(segment_results)


def main():
    """Example usage of the evaluation engine."""
    # Example usage
    engine = EvaluationEngine()
    
    # Example transcript and structured output
    transcript = """
    Speaker1: Hello, this is John from ABC Corp. Thanks for taking the time to meet today.
    Speaker2: Hi John, I'm Sarah from XYZ Solutions. Great to connect with you.
    Speaker1: We've been looking at various solutions for our sales enablement needs...
    """
    
    structured_output = {
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
    
    # Run evaluation
    result = engine.evaluate_call(transcript, structured_output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
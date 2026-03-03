#!/usr/bin/env python3
"""
Single File HTML Report Generator for LLM-as-a-Judge Evaluation Framework

This module generates detailed HTML reports for individual evaluation result files.
It provides deep analysis of a single file's evaluation with mathematical breakdowns
and LLM response transparency.

Usage:
    python single_report_generator.py --input results/12345_output.json --output reports/single_report_12345.html
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class SingleReportGenerator:
    """Generates detailed HTML reports for single evaluation result files."""
    
    def __init__(self, json_file_path: str):
        """
        Initialize the single report generator.
        
        Args:
            json_file_path: Path to the single evaluation result JSON file
        """
        self.json_file_path = Path(json_file_path)
        self.evaluation_result = None
        self.file_id = None
        
        # Load the evaluation result
        self._load_evaluation_result()
    
    def _load_evaluation_result(self) -> None:
        """Load the evaluation result from JSON file."""
        try:
            with open(self.json_file_path, 'r') as f:
                self.evaluation_result = json.load(f)
            
            # Extract file ID from filename
            self.file_id = self.json_file_path.stem.replace('_output', '')
            self.evaluation_result['file_id'] = self.file_id
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error loading {self.json_file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error processing {self.json_file_path}: {e}")
    
    def generate_single_report(self, output_file: str = "single_report.html") -> None:
        """Generate the complete single file HTML report."""
        # Generate HTML content
        html_content = self._generate_html_content()
        
        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Single file report generated: {output_path.absolute()}")
    
    def _generate_html_content(self) -> str:
        """Generate the complete HTML content for single file report."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Single File Evaluation Report - {self.file_id}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script>
        {self._get_javascript()}
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Context Aware Summarization - Evaluation Framework</h1>
            <p class="subtitle">Detailed analysis of evaluation result for file: <strong>{self.file_id}</strong></p>
            <div class="file-meta">
                <span class="badge">Overall Score: {self.evaluation_result.get('overall_score', 0):.2f}/5</span>
                <span class="badge">Call Type: {self._get_call_type()}</span>
                <span class="badge">Timestamp: {self._get_timestamp()}</span>
            </div>
        </header>
        
        <!-- File Overview -->
        <section class="report-section">
            <h2>📋 File Overview</h2>
            {self._generate_file_overview()}
        </section>
        
        <!-- Call Type Validation -->
        <section class="report-section">
            <h2>🎯 Call Type Validation</h2>
            {self._generate_validation_section()}
        </section>
        
        <!-- Schema Validation -->
        <section class="report-section">
            <h2>🔍 Schema Validation</h2>
            {self._generate_schema_section()}
        </section>
        
        <!-- Segment Analysis -->
        <section class="report-section">
            <h2>📊 Segment Analysis</h2>
            {self._generate_segment_analysis()}
        </section>
        
    </div>
</body>
</html>"""

        # <!-- Metric Deep Dive -->
        # <section class="report-section">
        #     <h2>📈 Metric Deep Dive</h2>
        #     {self._generate_metric_deep_dive()}
        # </section>
        
        
        # <!-- LLM Response Logs -->
        # <section class="report-section">
        #     <h2>🤖 LLM Response Logs</h2>
        #     {self._generate_llm_response_logs()}
        # </section>
    
    def _get_call_type(self) -> str:
        """Get the call type from evaluation result."""
        call_type_validation = self.evaluation_result.get('call_type_validation', {})
        return call_type_validation.get('predicted_call_type', 'Unknown')
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp from evaluation result."""
        metadata = self.evaluation_result.get('evaluation_metadata', {})
        timestamp = metadata.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return timestamp
        return 'Unknown'
    
    def _get_css_styles(self) -> str:
        """Generate CSS styles for the HTML report."""
        return """
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --info-color: #17a2b8;
            --text-color: #333;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --border-color: #e9ecef;
            --shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: var(--shadow);
            padding: 2rem;
            margin-bottom: 2rem;
            border-left: 4px solid var(--secondary-color);
        }
        
        h1 {
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
        
        .file-meta {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .badge {
            background: var(--primary-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .report-section {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
            padding: 2rem;
        }
        
        h2 {
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 0.5rem;
        }
        
        /* Overview Cards */
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .overview-card {
            background: #f8f9fa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }
        
        .overview-card h3 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            padding: 0.25rem 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .metric-value {
            font-weight: bold;
            color: var(--secondary-color);
        }
        
        /* Validation Section */
        .validation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        
        .validation-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            background: #f8f9fa;
        }
        
        .validation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-success { background: #d4edda; color: #155724; }
        .status-danger { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        
        /* Schema Section */
        .schema-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        
        .schema-list {
            background: #f8f9fa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .schema-item {
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
        }
        
        .schema-item:last-child {
            border-bottom: none;
        }
        
        /* Segment Analysis */
        .segment-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }
        
        .segment-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            background: #f8f9fa;
        }
        
        .segment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .segment-name {
            font-weight: bold;
            color: var(--primary-color);
            font-size: 1.1rem;
        }
        
        .segment-score {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--success-color);
        }
        
        .metric-breakdown {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .metric-detail {
            background: white;
            padding: 1rem;
            border-radius: 4px;
            border-left: 3px solid var(--secondary-color);
        }
        
        .metric-title {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .metric-score {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--success-color);
        }
        
        .metric-reason {
            font-size: 0.85rem;
            color: #666;
            margin-top: 0.5rem;
            line-height: 1.4;
        }
        
        /* Metric Deep Dive */
        .deep-dive-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        
        .calculation-card {
            background: #f8f9fa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }
        
        .calculation-step {
            background: white;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            border-left: 3px solid var(--info-color);
        }
        
        .calculation-formula {
            font-family: monospace;
            background: #f8f9fa;
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
        
        /* LLM Response Logs */
        .response-accordion {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .response-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .response-header {
            padding: 1rem 1.5rem;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }
        
        .response-header:hover {
            background: #e9ecef;
        }
        
        .response-content {
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-in-out;
        }
        
        .response-content.active {
            max-height: 1000px;
            padding: 1.5rem;
        }
        
        .response-text {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .report-section {
                padding: 1.5rem;
            }
            
            .schema-details {
                grid-template-columns: 1fr;
            }
            
            .metric-breakdown {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Generate JavaScript for interactive features."""
        return """
        function toggleResponse(responseId) {
            const content = document.getElementById('content-' + responseId);
            const icon = document.getElementById('icon-' + responseId);
            
            content.classList.toggle('active');
            icon.textContent = content.classList.contains('active') ? '−' : '+';
        }
        """
    
    def _generate_file_overview(self) -> str:
        """Generate HTML for file overview section."""
        call_type_validation = self.evaluation_result.get('call_type_validation', {})
        schema_validation = self.evaluation_result.get('schema_validation', {})
        overall_score = self.evaluation_result.get('overall_score', 0)
        
        # Calculate validation status
        validation_passed = call_type_validation.get('validation_passed', False)
        schema_passed = schema_validation.get('schema_passed', False)
        
        validation_class = "status-success" if validation_passed else "status-danger"
        validation_text = "PASSED" if validation_passed else "FAILED"
        
        schema_class = "status-success" if schema_passed else "status-danger"
        schema_text = "PASSED" if schema_passed else "FAILED"
        
        overview_html = f"""
        <div class="overview-grid">
            <div class="overview-card">
                <h3>📁 File Information</h3>
                <div class="metric-row">
                    <span class="metric-label">File ID:</span>
                    <span class="metric-value">{self.file_id}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Model Used:</span>
                    <span class="metric-value">{self.evaluation_result.get('evaluation_metadata', {}).get('model_used', 'Unknown')}</span>
                </div>
                
            </div>
            
            <div class="overview-card">
                <h3>🎯 Call Type Validation</h3>
                <div class="metric-row">
                    <span class="metric-label">Actual Type:</span>
                    <span class="metric-value">{call_type_validation.get('predicted_call_type', 'Unknown')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Predicted Type:</span>
                    <span class="metric-value">{call_type_validation.get('llm_predicted_call_type', 'Unknown')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Validation:</span>
                    <span class="status-badge {validation_class}">{validation_text}</span>
                </div>
            </div>
            
            <div class="overview-card">
                <h3>🔍 Schema Validation</h3>
                <div class="metric-row">
                    <span class="metric-label">Schema Status:</span>
                    <span class="status-badge {schema_class}">{schema_text}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Missing Fields:</span>
                    <span class="metric-value">{len(schema_validation.get('missing_fields', []))}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Extra Fields:</span>
                    <span class="metric-value">{len(schema_validation.get('extra_fields', []))}</span>
                </div>
            </div>
            
            <div class="overview-card">
                <h3>📊 Overall Performance</h3>
                <div class="metric-row">
                    <span class="metric-label">Overall Score:</span>
                    <span class="metric-value" style="font-size: 1.5rem; color: var(--success-color);">{overall_score:.2f}/5</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Segment Count:</span>
                    <span class="metric-value">{len(self.evaluation_result.get('segment_evaluations', []))}</span>
                </div>
                
            </div>
        </div>
        """
        
        return overview_html
    
    def _generate_validation_section(self) -> str:
        """Generate HTML for call type validation section."""
        call_type_validation = self.evaluation_result.get('call_type_validation', {})
        
        # Stage 1 details
        stage1 = call_type_validation.get('stage1_result', {})
        stage1_confidence = stage1.get('confidence', 0)
        stage1_class = self._get_confidence_class(stage1_confidence)
        
        # Stage 2 details (if exists)
        stage2 = call_type_validation.get('stage2_result', {})
        stage2_exists = bool(stage2)
        
        validation_html = f"""
        <div class="validation-grid">
            <div class="validation-card">
                <div class="validation-header">
                    <h3>Stage 1: Main Type Classification</h3>
                    <span class="status-badge {stage1_class}">Confidence: {stage1_confidence}/5</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Predicted Type:</span>
                    <span class="metric-value">{stage1.get('predicted_call_type', 'Unknown')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Reasoning:</span>
                    <span class="metric-value">{stage1.get('reasoning', 'No reasoning provided')}</span>
                </div>
            </div>
        """
        
        if stage2_exists:
            stage2_confidence = stage2.get('confidence', 0)
            stage2_class = self._get_confidence_class(stage2_confidence)
            
            validation_html += f"""
            <div class="validation-card">
                <div class="validation-header">
                    <h3>Stage 2: Subtype Classification</h3>
                    <span class="status-badge {stage2_class}">Confidence: {stage2_confidence}/5</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Predicted Subtype:</span>
                    <span class="metric-value">{stage2.get('predicted_subtype', 'Unknown')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Reasoning:</span>
                    <span class="metric-value">{stage2.get('reasoning', 'No reasoning provided')}</span>
                </div>
            </div>
            """
        
        validation_html += """
        </div>
        """
        
        return validation_html
    
    def _generate_schema_section(self) -> str:
        """Generate HTML for schema validation section."""
        schema_validation = self.evaluation_result.get('schema_validation', {})
        
        missing_fields = schema_validation.get('missing_fields', [])
        extra_fields = schema_validation.get('extra_fields', [])
        
        schema_html = f"""
        <div class="schema-details">
            <div>
                <h3>❌ Missing Fields ({len(missing_fields)})</h3>
                <div class="schema-list">
        """
        
        if missing_fields:
            for field in missing_fields:
                schema_html += f'<div class="schema-item">{field}</div>'
        else:
            schema_html += '<div class="schema-item">No missing fields</div>'
        
        schema_html += f"""
                </div>
            </div>
            
            <div>
                <h3>⚠️ Extra Fields ({len(extra_fields)})</h3>
                <div class="schema-list">
        """
        
        if extra_fields:
            for field in extra_fields:
                schema_html += f'<div class="schema-item">{field}</div>'
        else:
            schema_html += '<div class="schema-item">No extra fields</div>'
        
        schema_html += """
                </div>
            </div>
        </div>
        """
        
        return schema_html
    
    def _generate_segment_analysis(self) -> str:
        """Generate HTML for segment analysis section."""
        segment_evaluations = self.evaluation_result.get('segment_evaluations', [])
        
        if not segment_evaluations:
            return '<p>No segment evaluations found.</p>'
        
        segment_html = '<div class="segment-grid">'
        
        for segment in segment_evaluations:
            segment_name = segment['segment_name']
            weighted_score = segment['weighted_score']
            metrics = segment['metrics']
            
            segment_html += f"""
            <div class="segment-card">
                <div class="segment-header">
                    <div class="segment-name">{segment_name.replace("_", " ").title()}</div>
                    <div class="segment-score">{weighted_score:.2f}/5</div>
                </div>
                
                <div class="metric-breakdown">
            """
            
            for metric_name, metric_data in metrics.items():
                score = metric_data['score']
                reason = metric_data['reason']
                metric_class = self._get_metric_class(score)

                if metric_name in ['precision', 'recall']:
                    segment_html += f"""
                    <div class="metric-detail">
                        <div class="metric-title">{metric_name.replace("_", " ").title()}</div>
                        <div class="metric-score">{(score - 1) / 4 * 100:.2f} %</div>
                        <div class="metric-reason">{reason}</div>
                    </div>
                    """
                else:
                
                    segment_html += f"""
                    <div class="metric-detail">
                        <div class="metric-title">{metric_name.replace("_", " ").title()}</div>
                        <div class="metric-score">{score}/5</div>
                        <div class="metric-reason">{reason}</div>
                    </div>
                    """
            
            segment_html += """
                </div>
            </div>
            """
        
        segment_html += "</div>"
        
        return segment_html
    
    def _generate_metric_deep_dive(self) -> str:
        """Generate HTML for metric deep dive section."""
        segment_evaluations = self.evaluation_result.get('segment_evaluations', [])
        
        action_item_segments = []
        for segment in segment_evaluations:
            if any(metric in segment['metrics'] for metric in ['precision', 'recall']):
                action_item_segments.append(segment)
        
        if not action_item_segments:
            return '<p>No action item segments found for deep dive analysis.</p>'
        
        deep_dive_html = '<div class="deep-dive-grid">'
        
        for segment in action_item_segments:
            segment_name = segment['segment_name']
            metrics = segment['metrics']
            
            deep_dive_html += f"""
            <div class="calculation-card">
                <h3>🧮 {segment_name.title()} Analysis</h3>
            """
            
            # Precision calculation
            if 'precision' in metrics:
                precision_data = metrics['precision']
                deep_dive_html += f"""
                <div class="calculation-step">
                    <div class="metric-title">Precision Calculation</div>
                    <div class="calculation-formula">
                        Precision = correct_items / total_predicted_items<br>
                        Score = 1 + (precision * 4)
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Score:</span>
                        <span class="metric-value">{precision_data['score']}/5</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Reason:</span>
                        <span class="metric-value">{precision_data['reason']}</span>
                    </div>
                </div>
                """
            
            # Recall calculation
            if 'recall' in metrics:
                recall_data = metrics['recall']
                deep_dive_html += f"""
                <div class="calculation-step">
                    <div class="metric-title">Recall Calculation</div>
                    <div class="calculation-formula">
                        Recall = captured_items / total_actual_items<br>
                        Score = 1 + (recall * 4)
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Score:</span>
                        <span class="metric-value">{recall_data['score']}/5</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Reason:</span>
                        <span class="metric-value">{recall_data['reason']}</span>
                    </div>
                </div>
                """
            
            # Factuality
            if 'factuality' in metrics:
                factuality_data = metrics['factuality']
                deep_dive_html += f"""
                <div class="calculation-step">
                    <div class="metric-title">Factuality Assessment</div>
                    <div class="metric-row">
                        <span class="metric-label">Score:</span>
                        <span class="metric-value">{factuality_data['score']}/5</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Reason:</span>
                        <span class="metric-value">{factuality_data['reason']}</span>
                    </div>
                </div>
                """
            
            # Timeline Accuracy
            if 'timeline_accuracy' in metrics:
                timeline_data = metrics['timeline_accuracy']
                deep_dive_html += f"""
                <div class="calculation-step">
                    <div class="metric-title">Timeline Accuracy</div>
                    <div class="metric-row">
                        <span class="metric-label">Score:</span>
                        <span class="metric-value">{timeline_data['score']}/5</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Reason:</span>
                        <span class="metric-value">{timeline_data['reason']}</span>
                    </div>
                </div>
                """
            
            deep_dive_html += "</div>"
        
        deep_dive_html += "</div>"
        
        return deep_dive_html
    
    def _generate_llm_response_logs(self) -> str:
        """Generate HTML for LLM response logs section."""
        call_type_validation = self.evaluation_result.get('call_type_validation', {})
        segment_evaluations = self.evaluation_result.get('segment_evaluations', [])
        
        response_html = '<div class="response-accordion">'
        
        # Call Type Validation Response
        stage1_response = call_type_validation.get('stage1_result', {}).get('reasoning', 'No response')
        response_html += f"""
        <div class="response-card">
            <div class="response-header" onclick="toggleResponse('stage1')">
                <span>Stage 1: Main Type Classification Response</span>
                <span id="icon-stage1" class="toggle-icon">+</span>
            </div>
            <div id="content-stage1" class="response-content">
                <div class="response-text">{stage1_response}</div>
            </div>
        </div>
        """
        
        # Stage 2 Response (if exists)
        if call_type_validation.get('stage2_result'):
            stage2_response = call_type_validation.get('stage2_result', {}).get('reasoning', 'No response')
            response_html += f"""
            <div class="response-card">
                <div class="response-header" onclick="toggleResponse('stage2')">
                    <span>Stage 2: Subtype Classification Response</span>
                    <span id="icon-stage2" class="toggle-icon">+</span>
                </div>
                <div id="content-stage2" class="response-content">
                    <div class="response-text">{stage2_response}</div>
                </div>
            </div>
            """
        
        # Segment Responses
        for i, segment in enumerate(segment_evaluations):
            segment_name = segment['segment_name']
            llm_response = segment.get('llm_response', 'No response')
            response_id = f"segment_{i}"
            
            response_html += f"""
            <div class="response-card">
                <div class="response-header" onclick="toggleResponse('{response_id}')">
                    <span>Segment {i+1}: {segment_name} Response</span>
                    <span id="icon-{response_id}" class="toggle-icon">+</span>
                </div>
                <div id="content-{response_id}" class="response-content">
                    <div class="response-text">{llm_response}</div>
                </div>
            </div>
            """
        
        response_html += "</div>"
        
        return response_html
    
    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class based on confidence score."""
        if confidence >= 4:
            return "status-success"
        elif confidence >= 3:
            return "status-warning"
        else:
            return "status-danger"
    
    def _get_metric_class(self, score: float) -> str:
        """Get CSS class based on metric score."""
        if score >= 4:
            return "status-success"
        elif score >= 3:
            return "status-warning"
        else:
            return "status-danger"


def main():
    """Main function to generate single file report."""
    parser = argparse.ArgumentParser(description='Generate single file evaluation report')
    parser.add_argument('--input', '-i', required=True, help='Path to evaluation result JSON file')
    parser.add_argument('--output', '-o', default='single_report.html', help='Output HTML file path')
    
    args = parser.parse_args()
    
    try:
        generator = SingleReportGenerator(args.input)
        generator.generate_single_report(args.output)
        print(f"✅ Single file report generated successfully: {args.output}")
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
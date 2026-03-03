#!/usr/bin/env python3
"""
HTML Report Generator for LLM-as-a-Judge Evaluation Framework

This module generates comprehensive HTML reports with:
1. Overall metrics (accuracy, precision, recall for call type classification)
2. Detailed file-level reports with collapsible segments
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import statistics


class ReportGenerator:
    """Generates HTML reports from LLM-as-a-Judge evaluation results."""
    
    def __init__(self, results_directory: str):
        """
        Initialize the report generator.
        
        Args:
            results_directory: Path to directory containing evaluation result JSON files
        """
        self.results_directory = Path(results_directory)
        self.evaluation_results = []
        self.call_types = ["AE/Sales", "CSM/Post-Sale", "Internal/Implementation", "SDR/Outbound"]
        
    def load_evaluation_results(self) -> None:
        """Load all evaluation result files from the results directory."""
        json_files = [i for i in list(self.results_directory.glob("*.json")) if "gemini" not in i.stem]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    result = json.load(f)
                    # Extract file ID from filename
                    file_id = json_file.stem.replace('_output', '')
                    result['file_id'] = file_id
                    self.evaluation_results.append(result)
            except json.JSONDecodeError as e:
                print(f"Error loading {json_file}: {e}")
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
    
    def calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall metrics for call type classification."""
        if not self.evaluation_results:
            return {}
        
        # Initialize counters
        total_files = len(self.evaluation_results)
        correct_predictions = 0
        
        # For precision and recall calculation
        tp = defaultdict(int)  # True positives
        fp = defaultdict(int)  # False positives
        fn = defaultdict(int)  # False negatives
        
        valid_results = []
        
        for result in self.evaluation_results:
            call_type_validation = result.get('call_type_validation', {})
            schema_validation = result.get('schema_validation', {})
            
            # Only include results that passed schema validation for call type metrics
            if schema_validation.get('schema_passed', False):
                valid_results.append(result)
                
                actual_type = call_type_validation.get('predicted_call_type', '')
                predicted_type = call_type_validation.get('llm_predicted_call_type', '')
                validation_passed = call_type_validation.get('validation_passed', False)
                
                if validation_passed:
                    correct_predictions += 1
                
                # Calculate TP, FP, FN for each call type
                if actual_type in self.call_types:
                    if predicted_type == actual_type:
                        tp[actual_type] += 1
                    else:
                        fn[actual_type] += 1
                        if predicted_type in self.call_types:
                            fp[predicted_type] += 1
        
        # Calculate accuracy
        accuracy = (correct_predictions / len(valid_results)) * 100 if valid_results else 0
        
        # Calculate precision, recall, and F1 for each call type
        metrics = {
            'total_files': total_files,
            'valid_files': len(valid_results),
            'accuracy': round(accuracy, 2),
            'call_type_metrics': {}
        }
        
        for call_type in self.call_types:
            precision = (tp[call_type] / (tp[call_type] + fp[call_type])) * 100 if (tp[call_type] + fp[call_type]) > 0 else 0
            recall = (tp[call_type] / (tp[call_type] + fn[call_type])) * 100 if (tp[call_type] + fn[call_type]) > 0 else 0
            f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics['call_type_metrics'][call_type] = {
                'precision': round(precision, 2),
                'recall': round(recall, 2),
                'f1_score': round(f1_score, 2),
                'true_positives': tp[call_type],
                'false_positives': fp[call_type],
                'false_negatives': fn[call_type]
            }
        
        # Calculate schema validation success rate
        schema_passed_count = sum(1 for r in self.evaluation_results if r.get('schema_validation', {}).get('schema_passed', False))
        metrics['schema_validation_success_rate'] = round((schema_passed_count / total_files) * 100, 2) if total_files > 0 else 0
        
        # Calculate overall score statistics
        valid_scores = [r.get('overall_score', 0) for r in valid_results if r.get('overall_score', 0) > 0]
        if valid_scores:
            metrics['overall_score_stats'] = {
                'average': round(statistics.mean(valid_scores), 2),
                'median': round(statistics.median(valid_scores), 2),
                'min': round(min(valid_scores), 2),
                'max': round(max(valid_scores), 2)
            }
        else:
            metrics['overall_score_stats'] = {
                'average': 0,
                'median': 0,
                'min': 0,
                'max': 0
            }
        
        return metrics
    
    def generate_html_report(self, output_file: str = "evaluation_report.html") -> None:
        """Generate the complete HTML report."""
        # Load results and calculate metrics
        self.load_evaluation_results()
        overall_metrics = self.calculate_overall_metrics()
        
        # Generate HTML content
        html_content = self._generate_html_content(overall_metrics)
        
        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_path.absolute()}")
    
    def _generate_html_content(self, metrics: Dict[str, Any]) -> str:
        """Generate the complete HTML content."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI Summarization - LLM-as-a-Judge Evaluation Report</title>
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
            <h1>CI Summarization - LLM-as-a-Judge Evaluation Report</h1>
            <p class="subtitle">Comprehensive analysis of structured summary validation</p>
        </header>
        
        <!-- Section 1: Overall Report -->
        <section id="overall-report" class="report-section">
            <h2>📊 Overall Report</h2>
            <div class="metrics-grid">
                {self._generate_overall_metrics_cards(metrics)}
            </div>
            
            <div class="charts-container">
                <div class="chart-card">
                    <h3>Call Type Classification Accuracy</h3>
                    <div class="metric-circle">
                        <svg viewBox="0 0 36 36" class="circular-chart">
                            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <path class="circle" stroke-dasharray="{metrics['accuracy']}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <text x="18" y="20.5" class="percentage">{metrics['accuracy']}%</text>
                        </svg>
                    </div>
                </div>
                
                <div class="chart-card">
                    <h3>Schema Validation Success Rate</h3>
                    <div class="metric-circle">
                        <svg viewBox="0 0 36 36" class="circular-chart">
                            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <path class="circle schema-circle" stroke-dasharray="{metrics['schema_validation_success_rate']}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <text x="18" y="20.5" class="percentage">{metrics['schema_validation_success_rate']}%</text>
                        </svg>
                    </div>
                </div>
            </div>
            
            <div class="detailed-metrics">
                <h3>📈 Detailed Call Type Metrics</h3>
                {self._generate_call_type_table(metrics['call_type_metrics'])}
            </div>
        </section>
        
        <!-- Section 2: Detailed Report -->
        <section id="detailed-report" class="report-section">
            <h2>📋 Detailed Report</h2>
            <div class="file-list">
                {self._generate_file_accordion()}
            </div>
        </section>
    </div>
</body>
</html>"""
    
    def _get_css_styles(self) -> str:
        """Generate CSS styles for the HTML report."""
        return """
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --text-color: #333;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --border-color: #e9ecef;
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
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        h1 {
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1rem;
        }
        
        .report-section {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 3rem;
            padding: 2rem;
        }
        
        h2 {
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 0.5rem;
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2.5rem;
            margin-bottom: 4rem;
        }
        
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #de594d; /*var(--secondary-color);*/
            display: block;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Charts */
        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .chart-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
        }
        
        .chart-card h3 {
            margin-bottom: 2rem;
            font-size: 1.2rem;
        }
        
        .circular-chart {
            width: 200px;
            height: 200px;
            margin: 0 auto;
        }
        
        .circle-bg {
            fill: none;
            stroke: var(--border-color);
            stroke-width: 2;
        }
        
        .circle {
            fill: none;
            stroke: var(--success-color);
            stroke-width: 2;
            stroke-linecap: round;
            animation: progress 1s ease-out forwards;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
        }
        
        .schema-circle {
            stroke: var(--secondary-color);
        }
        
        .percentage {
            fill: var(--text-color);
            font-size: 0.4rem;
            font-weight: bold;
            text-anchor: middle;
            
        }
        
        @keyframes progress {
            0% { stroke-dashoffset: 100; }
            100% { stroke-dashoffset: 0; }
        }
        
        /* Tables */
        .detailed-metrics {
            margin-top: 2rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .metric-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .badge-success { background-color: #d4edda; color: #155724; }
        .badge-warning { background-color: #fff3cd; color: #856404; }
        .badge-danger { background-color: #f8d7da; color: #721c24; }
        
        /* File Accordion */
        .file-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .file-card {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            background: var(--card-bg);
        }
        
        .file-header {
            padding: 1.5rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            transition: background-color 0.2s;
        }
        
        .file-header:hover {
            background: #e9ecef;
        }
        
        .file-title {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .file-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.9rem;
            color: #666;
        }
        
        .file-content {
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-in-out;
        }
        
        .file-content.active {
            max-height: 2000px;
            padding: 1.5rem;
        }
        
        .segment-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .segment-card {
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            background: #fafafa;
        }
        
        .segment-name {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            font-size: 0.9rem;
        }
        
        .score-value {
            font-weight: bold;
            color: var(--secondary-color);
        }
        
        .overall-score {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--success-color);
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .report-section {
                padding: 1.5rem;
            }
            
            .charts-container {
                grid-template-columns: 1fr;
            }
            
            .circular-chart {
                width: 150px;
                height: 150px;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Generate JavaScript for interactive features."""
        return """
        function toggleFile(fileId) {
            const content = document.getElementById('content-' + fileId);
            const icon = document.getElementById('icon-' + fileId);
            
            content.classList.toggle('active');
            icon.textContent = content.classList.contains('active') ? '−' : '+';
        }
        
        function filterFiles() {
            const filter = document.getElementById('file-filter').value.toLowerCase();
            const fileCards = document.querySelectorAll('.file-card');
            
            fileCards.forEach(card => {
                const title = card.querySelector('.file-title').textContent.toLowerCase();
                if (title.includes(filter)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        """
    
    def _generate_overall_metrics_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML for overall metrics cards."""
        cards = []
        
        # Total files card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['total_files']}</span>
            <span class="metric-label">Total Files</span>
        </div>
        """)
        
        # Valid files card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['valid_files']}</span>
            <span class="metric-label">Valid Files</span>
        </div>
        """)
        
        # Average overall score card
        avg_score = metrics['overall_score_stats']['average']
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{avg_score} / 5</span>
            <span class="metric-label">Avg Overall Score</span>
        </div>
        """)
        
        # Schema validation success rate card
        schema_rate = metrics['schema_validation_success_rate']
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{schema_rate}%</span>
            <span class="metric-label">Schema Validation Success</span>
        </div>
        """)
        
        return ''.join(cards)
    
    def _generate_call_type_table(self, call_type_metrics: Dict[str, Any]) -> str:
        """Generate HTML table for call type metrics."""
        table_html = """
        <table>
            <thead>
                <tr>
                    <th>Call Type</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1-Score</th>
                    <th>True Positives</th>
                    <th>False Positives</th>
                    <th>False Negatives</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for call_type, metrics in call_type_metrics.items():
            precision_class = self._get_metric_class(metrics['precision'])
            recall_class = self._get_metric_class(metrics['recall'])
            f1_class = self._get_metric_class(metrics['f1_score'])
            
            table_html += f"""
            <tr>
                <td><strong>{call_type}</strong></td>
                <td><span class="metric-badge {precision_class}">{metrics['precision']}%</span></td>
                <td><span class="metric-badge {recall_class}">{metrics['recall']}%</span></td>
                <td><span class="metric-badge {f1_class}">{metrics['f1_score']}%</span></td>
                <td>{metrics['true_positives']}</td>
                <td>{metrics['false_positives']}</td>
                <td>{metrics['false_negatives']}</td>
            </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        return table_html
    
    def _get_metric_class(self, value: float) -> str:
        """Get CSS class based on metric value."""
        if value >= 90:
            return "badge-success"
        elif value >= 70:
            return "badge-warning"
        else:
            return "badge-danger"
    
    def _generate_file_accordion(self) -> str:
        """Generate HTML for file accordion."""
        accordion_html = ""
        
        for result in self.evaluation_results:
            file_id = result['file_id']
            call_type_validation = result.get('call_type_validation', {})
            schema_validation = result.get('schema_validation', {})
            overall_score = result.get('overall_score', 0)
            
            # File header
            actual_type = call_type_validation.get('predicted_call_type', 'Unknown')
            predicted_type = call_type_validation.get('llm_predicted_call_type', 'Unknown')
            validation_passed = call_type_validation.get('validation_passed', False)
            
            header_class = "success" if validation_passed else "danger"
            validation_icon = "✓" if validation_passed else "✗"
            
            accordion_html += f"""
            <div class="file-card">
                <div class="file-header" onclick="toggleFile('{file_id}')">
                    <div>
                        <div class="file-title">{file_id}</div>
                        <div class="file-meta">
                            <span>LLM Tool: {actual_type}</span>
                            <span>LLM Judge: {predicted_type}</span>
                            <span class="badge-{header_class}">{validation_icon} Validation</span>
                        </div>
                    </div>
                    <div>
                        <span class="overall-score">Score: {overall_score:.2f}</span>
                        <span id="icon-{file_id}" class="toggle-icon">+</span>
                    </div>
                </div>
                <div id="content-{file_id}" class="file-content">
                    {self._generate_file_details(result)}
                </div>
            </div>
            """
        
        return accordion_html
    
    def _generate_file_details(self, result: Dict[str, Any]) -> str:
        """Generate detailed file information."""
        call_type_validation = result.get('call_type_validation', {})
        schema_validation = result.get('schema_validation', {})
        segment_evaluations = result.get('segment_evaluations', [])
        
        details_html = f"""
        <div class="file-details">
            <h4>Call Type Validation Details</h4>
            <div class="segment-grid">
                <div class="segment-card">
                    <div class="segment-name">Stage 1: Main Type</div>
                    <div class="metric-row">
                        <span>Predicted:</span>
                        <span class="score-value">{call_type_validation.get('llm_predicted_call_type', 'Unknown')}</span>
                    </div>
                    <div class="metric-row">
                        <span>Confidence:</span>
                        <span class="score-value">{call_type_validation.get('stage1_result', {}).get('confidence', 0)}/5</span>
                    </div>
                </div>
        """
        
        if call_type_validation.get('stage2_result'):
            stage2 = call_type_validation['stage2_result']
            details_html += f"""
                <div class="segment-card">
                    <div class="segment-name">Stage 2: Subtype</div>
                    <div class="metric-row">
                        <span>Predicted:</span>
                        <span class="score-value">{stage2.get('predicted_subtype', 'Unknown')}</span>
                    </div>
                    <div class="metric-row">
                        <span>Confidence:</span>
                        <span class="score-value">{stage2.get('confidence', 0)}/5</span>
                    </div>
                </div>
            """
        
        details_html += """
            </div>
            
            <h4>Schema Validation</h4>
            <div class="segment-grid">
                <div class="segment-card">
                    <div class="segment-name">Schema Status</div>
                    <div class="metric-row">
                        <span>Passed:</span>
                        <span class="score-value">""" + ("Yes" if schema_validation.get('schema_passed', False) else "No") + """</span>
                    </div>
                    <div class="metric-row">
                        <span>Missing Fields:</span>
                        <span class="score-value">""" + str(len(schema_validation.get('missing_fields', []))) + """</span>
                    </div>
                    <div class="metric-row">
                        <span>Extra Fields:</span>
                        <span class="score-value">""" + str(len(schema_validation.get('extra_fields', []))) + """</span>
                    </div>
                </div>
            </div>
        """
        
        if segment_evaluations:
            details_html += """
            <h4>Segment Evaluations</h4>
            <div class="segment-grid">
            """
            
            for segment in segment_evaluations:
                segment_name = segment['segment_name']
                weighted_score = segment['weighted_score']
                metrics = segment['metrics']
                
                details_html += f"""
                <div class="segment-card">
                    <div class="segment-name">{segment_name}</div>
                    <div class="metric-row">
                        <span>Weighted Score:</span>
                        <span class="score-value">{weighted_score:.2f}/5</span>
                    </div>
                """
                
                for metric_name, metric_data in metrics.items():
                    score = metric_data['score']
                    reason = metric_data['reason']
                    details_html += f"""
                    <div class="metric-row">
                        <span>{metric_name}:</span>
                        <span class="score-value">{score}/5</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">
                        {reason}
                    </div>
                    """
                
                details_html += "</div>"
            
            details_html += "</div>"
        
        details_html += "</div>"
        
        return details_html


def main():
    """Main function to generate the report."""
    # Use the examples/results directory
    results_dir = "evaluation_framework/examples/results"
    output_file = "reports/evaluation_report.html"
    
    generator = ReportGenerator(results_dir)
    generator.generate_html_report(output_file)
    
    print(f"Report generated successfully: {output_file}")


if __name__ == "__main__":
    main()
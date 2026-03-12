#!/usr/bin/env python3
"""
Enhanced HTML Report Generator for LLM-as-a-Judge Evaluation Framework

This module generates comprehensive aggregated HTML reports with:
1. Overall metrics (accuracy, precision, recall for call type classification)
2. Advanced aggregated metrics with various chart types
3. Quality analysis and insights
4. Call type specific analysis with radar charts and heatmaps
5. Segment performance analysis
6. Actionable recommendations

Charts included:
- Radar charts for quality metrics comparison
- Bar charts for categorical data
- Donut charts for proportions
- Heatmaps for performance matrix
- Box plots for distribution analysis
- Stacked bar charts for composition
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
import statistics


class EnhancedReportGenerator:
    """Generates enhanced HTML reports with aggregated metrics and various chart types."""
    
    def __init__(self, results_directory: str):
        """
        Initialize the enhanced report generator.
        
        Args:
            results_directory: Path to directory containing evaluation result JSON files
        """
        self.results_directory = Path(results_directory)
        self.evaluation_results = []
        self.call_types = ["AE/Sales", "CSM/Post-Sale", "Internal/Implementation", "SDR/Outbound"]
        
        # Define subtype-specific segments for AE/Sales
        self.ae_sales_subtypes = {
            "Demo/Evaluation": ["meeting_introduction", "smart_summary", "solution_presentation", 
                               "technical_fit_and_gaps", "prospect_reactions", "competitive_landscape", "next_steps"],
            "Discovery/Qualification": ["meeting_context", "smart_summary", "pain_discovery", 
                                       "qualification_signals", "competitive_landscape", "next_steps", "closing_remarks"],
            "Negotiation/Close": ["meeting_context", "smart_summary", "commercial_terms", 
                                 "legal_and_procurement", "concessions", "risk_signals", "path_to_close"],
            "Proposal/Business Case": ["meeting_context", "smart_summary", "pricing_discussion", 
                                      "business_case_roi", "stakeholder_alignment", "objections_concerns", "next_steps"]
        }
        
        # Define segments for other call types
        self.other_call_types = {
            "CSM/Post-Sale": ["relationship_context", "smart_summary", "health_and_adoption", 
                             "issues_escalations", "expansion_signals", "renewal_risk", "action_plan"],
            "Internal/Implementation": ["meeting_context", "smart_summary", "key_decisions", 
                                       "blockers_risks", "technical_discussion", "action_items", "timeline_dependencies"],
            "SDR/Outbound": ["prospect_context", "smart_summary", "value_proposition", 
                            "pain_points", "next_steps", "qualifying_questions", "follow_up_plan"]
        }
        
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
        """Calculate overall metrics for call type classification and aggregated insights."""
        if not self.evaluation_results:
            return {}
        
        # Initialize counters
        total_files = len(self.evaluation_results)
        valid_results = []
        schema_passed_count = 0
        
        # For precision and recall calculation
        tp = defaultdict(int)  # True positives
        fp = defaultdict(int)  # False positives
        fn = defaultdict(int)  # False negatives
        
        # Quality metrics aggregation
        quality_scores = defaultdict(list)
        segment_scores = defaultdict(list)
        call_type_distribution = defaultdict(int)
        
        for result in self.evaluation_results:
            call_type_validation = result.get('call_type_validation', {})
            schema_validation = result.get('schema_validation', {})
            
            # Count schema validation
            if schema_validation.get('schema_passed', False):
                schema_passed_count += 1
                valid_results.append(result)
                call_type = call_type_validation.get('predicted_call_type', 'Unknown')
                call_type_distribution[call_type] += 1
            
            # Calculate TP, FP, FN for each call type
            actual_type = call_type_validation.get('predicted_call_type', '')
            predicted_type = call_type_validation.get('llm_predicted_call_type', '')
            validation_passed = call_type_validation.get('validation_passed', False)
            
            if actual_type in self.call_types:
                if predicted_type == actual_type:
                    tp[actual_type] += 1
                else:
                    fn[actual_type] += 1
                    if predicted_type in self.call_types:
                        fp[predicted_type] += 1
            
            # Aggregate quality scores
            overall_score = result.get('overall_score', 0)
            if overall_score > 0:
                quality_scores['overall'].append(overall_score)
            
            # Aggregate segment scores
            for segment in result.get('segment_evaluations', []):
                segment_name = segment['segment_name']
                weighted_score = segment['weighted_score']
                segment_scores[segment_name].append(weighted_score)
                
                # Also aggregate by call type
                if call_type in self.call_types:
                    segment_scores[f"{call_type}_{segment_name}"].append(weighted_score)
        
        # Calculate accuracy
        correct_predictions = sum(1 for r in valid_results if r.get('call_type_validation', {}).get('validation_passed', False))
        accuracy = (correct_predictions / len(valid_results)) * 100 if valid_results else 0
        
        # Calculate precision, recall, and F1 for each call type
        call_type_metrics = {}
        for call_type in self.call_types:
            precision = (tp[call_type] / (tp[call_type] + fp[call_type])) * 100 if (tp[call_type] + fp[call_type]) > 0 else 0
            recall = (tp[call_type] / (tp[call_type] + fn[call_type])) * 100 if (tp[call_type] + fn[call_type]) > 0 else 0
            f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            call_type_metrics[call_type] = {
                'precision': round(precision, 2),
                'recall': round(recall, 2),
                'f1_score': round(f1_score, 2),
                'true_positives': tp[call_type],
                'false_positives': fp[call_type],
                'false_negatives': fn[call_type],
                'total_files': call_type_distribution[call_type]
            }
        
        # Calculate schema validation success rate
        schema_validation_success_rate = round((schema_passed_count / total_files) * 100, 2) if total_files > 0 else 0
        
        # Calculate overall score statistics
        if quality_scores['overall']:
            overall_stats = {
                'average': round(statistics.mean(quality_scores['overall']), 2),
                'median': round(statistics.median(quality_scores['overall']), 2),
                'min': round(min(quality_scores['overall']), 2),
                'max': round(max(quality_scores['overall']), 2),
                'std_dev': round(statistics.stdev(quality_scores['overall']) if len(quality_scores['overall']) > 1 else 0, 2)
            }
        else:
            overall_stats = {'average': 0, 'median': 0, 'min': 0, 'max': 0, 'std_dev': 0}
        
        # Calculate segment averages
        segment_averages = {}
        for segment_name, scores in segment_scores.items():
            if scores:
                segment_averages[segment_name] = round(statistics.mean(scores), 2)
        
        # Calculate quality distribution
        quality_distribution = self._calculate_quality_distribution(quality_scores['overall'])
        
        # Calculate call type specific metrics
        call_type_quality = {}
        for call_type in self.call_types:
            call_type_scores = [score for result in valid_results 
                              if result.get('call_type_validation', {}).get('predicted_call_type') == call_type
                              for score in [result.get('overall_score', 0)] if score > 0]
            if call_type_scores:
                call_type_quality[call_type] = {
                    'average': round(statistics.mean(call_type_scores), 2),
                    'count': len(call_type_scores),
                    'distribution': self._calculate_quality_distribution(call_type_scores)
                }
        
        return {
            'total_files': total_files,
            'valid_files': len(valid_results),
            'invalid_files': total_files - len(valid_results),
            'schema_validation_success_rate': schema_validation_success_rate,
            'accuracy': round(accuracy, 2),
            'call_type_metrics': call_type_metrics,
            'overall_score_stats': overall_stats,
            'segment_averages': segment_averages,
            'quality_distribution': quality_distribution,
            'call_type_distribution': dict(call_type_distribution),
            'call_type_quality': call_type_quality,
            'segment_scores': segment_scores
        }
    
    def _calculate_quality_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate quality score distribution."""
        distribution = {
            'excellent': 0,  # 4.5 - 5.0
            'good': 0,       # 3.5 - 4.4
            'fair': 0,       # 2.5 - 3.4
            'poor': 0        # 0.0 - 2.4
        }
        
        for score in scores:
            if score >= 4.5:
                distribution['excellent'] += 1
            elif score >= 3.5:
                distribution['good'] += 1
            elif score >= 2.5:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def generate_html_report(self, output_file: str = "reports/evaluation_report.html") -> None:
        """Generate the enhanced HTML report with aggregated metrics and charts."""
        # Load results and calculate metrics
        self.load_evaluation_results()
        overall_metrics = self.calculate_overall_metrics()
        
        # Generate HTML content
        html_content = self._generate_enhanced_html_content(overall_metrics)
        
        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Enhanced HTML report generated: {output_path.absolute()}")
    
    def _generate_enhanced_html_content(self, metrics: Dict[str, Any]) -> str:
        """Generate the enhanced HTML content with charts and aggregated metrics."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI Summarization - Enhanced LLM-as-a-Judge Evaluation Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {self._get_enhanced_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CI Summarization - Enhanced LLM-as-a-Judge Evaluation Report</h1>
            <p class="subtitle">Comprehensive aggregated analysis of structured summary validation</p>
        </header>
        
        <!-- Section 1: Executive Summary -->
        <section id="executive-summary" class="report-section">
            <h2>📊 Executive Summary</h2>
            <div class="metrics-grid">
                {self._generate_executive_metrics_cards(metrics)}
            </div>
            
            <div class="charts-row">
                <div class="chart-card">
                    <h3>File Processing Status</h3>
                    <canvas id="fileProcessingChart" width="400" height="400"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Overall Quality Metrics</h3>
                    <canvas id="qualityRadarChart" width="400" height="400"></canvas>
                </div>
            </div>
        </section>
        
        <!-- Section 2: Quality Analysis -->
        <section id="quality-analysis" class="report-section">
            <h2>📈 Quality Analysis</h2>
            <div class="charts-row">
                <div class="chart-card">
                    <h3>Score Distribution</h3>
                    <canvas id="scoreDistributionChart" width="400" height="400"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Quality Score Ranges</h3>
                    <canvas id="qualityRangesChart" width="400" height="400"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h3>Score Distribution Analysis</h3>
                <canvas id="scoreBoxPlotChart" width="800" height="400"></canvas>
            </div>
        </section>
        
        <!-- Section 3: Call Type Analysis -->
        <section id="call-type-analysis" class="report-section">
            <h2>🎯 Call Type Analysis</h2>
            <div class="charts-row">
                <div class="chart-card">
                    <h3>Call Type Distribution</h3>
                    <canvas id="callTypeDistributionChart" width="400" height="400"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Call Type Performance</h3>
                    <canvas id="callTypePerformanceChart" width="400" height="400"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h3>Call Type vs Segment Performance</h3>
                <canvas id="performanceHeatmapChart" width="800" height="400"></canvas>
            </div>
        </section>
        
        <!-- Section 4: Call Type Specific Analysis -->
        <section id="call-type-specific-analysis" class="report-section">
            <h2>🎯 Call Type Specific Analysis</h2>
            
            <!-- AE/Sales Analysis Section -->
            <div class="call-type-section">
                <h3>📊 AE/Sales Analysis</h3>
                <div class="charts-row">
                    <div class="chart-card">
                        <h4>AE/Sales Subtype Distribution</h4>
                        <canvas id="aeSalesSubtypeDistributionChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>AE/Sales Subtype Quality Comparison</h4>
                        <canvas id="aeSalesSubtypeQualityChart" width="400" height="400"></canvas>
                    </div>
                </div>
                
                <!-- AE/Sales Subtype Specific Charts -->
                <div class="subtype-charts">
                    <h4>Subtype-Specific Segment Analysis</h4>
                    <div class="charts-row">
                        <div class="chart-card">
                            <h5>Demo/Evaluation Segments</h5>
                            <canvas id="aeSalesDemoSegmentsChart" width="400" height="400"></canvas>
                        </div>
                        <div class="chart-card">
                            <h5>Discovery/Qualification Segments</h5>
                            <canvas id="aeSalesDiscoverySegmentsChart" width="400" height="400"></canvas>
                        </div>
                    </div>
                    <div class="charts-row">
                        <div class="chart-card">
                            <h5>Negotiation/Close Segments</h5>
                            <canvas id="aeSalesNegotiationSegmentsChart" width="400" height="400"></canvas>
                        </div>
                        <div class="chart-card">
                            <h5>Proposal/Business Case Segments</h5>
                            <canvas id="aeSalesProposalSegmentsChart" width="400" height="400"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- CSM/Post-Sale Analysis Section -->
            <div class="call-type-section">
                <h3>📈 CSM/Post-Sale Analysis</h3>
                <div class="charts-row">
                    <div class="chart-card">
                        <h4>CSM Segment Performance</h4>
                        <canvas id="csmSegmentPerformanceChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>CSM Quality Distribution</h4>
                        <canvas id="csmQualityDistributionChart" width="400" height="400"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Internal/Implementation Analysis Section -->
            <div class="call-type-section">
                <h3>🔧 Internal/Implementation Analysis</h3>
                <div class="charts-row">
                    <div class="chart-card">
                        <h4>Internal Segment Performance</h4>
                        <canvas id="internalSegmentPerformanceChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>Implementation Quality Analysis</h4>
                        <canvas id="internalQualityAnalysisChart" width="400" height="400"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- SDR/Outbound Analysis Section -->
            <div class="call-type-section">
                <h3>📞 SDR/Outbound Analysis</h3>
                <div class="charts-row">
                    <div class="chart-card">
                        <h4>SDR Segment Performance</h4>
                        <canvas id="sdrSegmentPerformanceChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>Outbound Quality Metrics</h4>
                        <canvas id="sdrQualityMetricsChart" width="400" height="400"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Cross-Call Type Comparison -->
            <div class="call-type-section">
                <h3>🔄 Cross-Call Type Comparison</h3>
                <div class="charts-row">
                    <div class="chart-card">
                        <h4>Overall Call Type Quality</h4>
                        <canvas id="crossCallTypeQualityChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>Common Segment Performance</h4>
                        <canvas id="commonSegmentPerformanceChart" width="400" height="400"></canvas>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Section 5: Detailed Call Type Metrics -->
        <section id="detailed-metrics" class="report-section">
            <h2>📋 Detailed Call Type Metrics</h2>
            {self._generate_call_type_table(metrics['call_type_metrics'])}
        </section>
        
        <!-- Section 6: Recommendations -->
        <section id="recommendations" class="report-section">
            <h2>💡 Recommendations</h2>
            {self._generate_recommendations(metrics)}
        </section>
    </div>
    
    <script>
        {self._get_chart_javascript(metrics)}
    </script>
</body>
</html>"""
    
    def _get_enhanced_css_styles(self) -> str:
        """Generate enhanced CSS styles for the HTML report."""
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
            box-shadow: var(--shadow);
            margin-bottom: 3rem;
            padding: 2rem;
        }
        
        h2 {
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 0.5rem;
        }
        
        h3 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
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
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--secondary-color);
            display: block;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-sublabel {
            color: #888;
            font-size: 0.8rem;
            font-style: italic;
        }
        
        /* Charts */
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .chart-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }
        
        canvas {
            width: 100% !important;
            height: 400px !important;
        }
        
        /* Tables */
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
            position: sticky;
            top: 0;
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
        .badge-info { background-color: #d1ecf1; color: #0c5460; }
        
        /* Recommendations */
        .recommendations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        
        .recommendation-card {
            background: #f8f9fa;
            border-left: 4px solid var(--info-color);
            padding: 1.5rem;
            border-radius: 4px;
        }
        
        .recommendation-title {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        /* Call Type Sections */
        .call-type-section {
            margin-bottom: 3rem;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid var(--secondary-color);
        }
        
        .call-type-section h3 {
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            border-bottom: none;
            padding-bottom: 0;
        }
        
        .subtype-charts {
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
        }
        
        .subtype-charts h4 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .subtype-charts h5 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .report-section {
                padding: 1.5rem;
            }
            
            .call-type-section {
                padding: 1.5rem;
            }
            
            .charts-row {
                grid-template-columns: 1fr;
            }
            
            canvas {
                height: 300px !important;
            }
        }
        """
    
    def _generate_executive_metrics_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML for executive metrics cards."""
        cards = []
        
        # Total files card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['total_files']}</span>
            <span class="metric-label">Total Files</span>
            <span class="metric-sublabel">Processed for evaluation</span>
        </div>
        """)
        
        # Valid files card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['valid_files']}</span>
            <span class="metric-label">Valid Files</span>
            <span class="metric-sublabel">Passed schema validation</span>
        </div>
        """)
        
        # Invalid files card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['invalid_files']}</span>
            <span class="metric-label">Invalid Files</span>
            <span class="metric-sublabel">Failed schema validation</span>
        </div>
        """)
        
        # Schema validation success rate card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['schema_validation_success_rate']}%</span>
            <span class="metric-label">Schema Validation</span>
            <span class="metric-sublabel">Success rate</span>
        </div>
        """)
        
        # Average overall score card
        avg_score = metrics['overall_score_stats']['average']
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{avg_score}</span>
            <span class="metric-label">Average Score</span>
            <span class="metric-sublabel">Out of 5.0</span>
        </div>
        """)
        
        # Call type accuracy card
        cards.append(f"""
        <div class="metric-card">
            <span class="metric-value">{metrics['accuracy']}%</span>
            <span class="metric-label">Call Type Accuracy</span>
            <span class="metric-sublabel">Classification accuracy</span>
        </div>
        """)
        
        return ''.join(cards)
    
    def _generate_call_type_table(self, call_type_metrics: Dict[str, Any]) -> str:
        """Generate HTML table for call type metrics."""
        table_html = """
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Call Type</th>
                        <th>Total Files</th>
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
                <td>{metrics['total_files']}</td>
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
        </div>
        """
        
        return table_html
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> str:
        """Generate actionable recommendations based on aggregated data."""
        recommendations = []
        
        # Quality-based recommendations
        avg_score = metrics['overall_score_stats']['average']
        if avg_score < 3.5:
            recommendations.append({
                'title': 'Quality Improvement Needed',
                'description': f'Average score of {avg_score} indicates significant quality issues. Focus on improving faithfulness and completeness metrics across all segments.'
            })
        elif avg_score < 4.0:
            recommendations.append({
                'title': 'Moderate Quality Improvement',
                'description': f'Average score of {avg_score} shows room for improvement. Target segments with lowest scores for focused enhancement.'
            })
        else:
            recommendations.append({
                'title': 'High Quality Maintained',
                'description': f'Excellent average score of {avg_score}. Continue current practices and share best practices across teams.'
            })
        
        # Schema validation recommendations
        schema_rate = metrics['schema_validation_success_rate']
        if schema_rate < 80:
            recommendations.append({
                'title': 'Schema Validation Issues',
                'description': f'Only {schema_rate}% of files pass schema validation. Review and standardize data collection processes.'
            })
        
        # Call type accuracy recommendations
        accuracy = metrics['accuracy']
        if accuracy < 80:
            recommendations.append({
                'title': 'Call Type Classification Improvement',
                'description': f'Call type accuracy of {accuracy}% needs improvement. Review classification criteria and training data.'
            })
        
        # Distribution-based recommendations
        poor_count = metrics['quality_distribution']['poor']
        if poor_count > 0:
            recommendations.append({
                'title': 'Address Low-Quality Files',
                'description': f'{poor_count} files scored in the "Poor" range. Investigate common issues and provide targeted training.'
            })
        
        # Generate recommendations HTML
        recommendations_html = '<div class="recommendations-grid">'
        for rec in recommendations:
            recommendations_html += f"""
            <div class="recommendation-card">
                <div class="recommendation-title">{rec['title']}</div>
                <div>{rec['description']}</div>
            </div>
            """
        recommendations_html += '</div>'
        
        return recommendations_html
    
    def _get_metric_class(self, value: float) -> str:
        """Get CSS class based on metric value."""
        if value >= 90:
            return "badge-success"
        elif value >= 70:
            return "badge-warning"
        else:
            return "badge-danger"
    
    def _get_chart_javascript(self, metrics: Dict[str, Any]) -> str:
        """Generate JavaScript for Chart.js visualizations."""
        return f"""
        // Chart.js configuration
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
        Chart.defaults.color = '#666';
        
        // File Processing Status (Donut Chart)
        const fileProcessingCtx = document.getElementById('fileProcessingChart').getContext('2d');
        new Chart(fileProcessingCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Valid Files', 'Invalid Files'],
                datasets: [{{
                    data: [{metrics['valid_files']}, {metrics['invalid_files']}],
                    backgroundColor: ['#27ae60', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = {metrics['total_files']};
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return context.label + ': ' + context.raw + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Quality Radar Chart
        const qualityRadarCtx = document.getElementById('qualityRadarChart').getContext('2d');
        new Chart(qualityRadarCtx, {{
            type: 'radar',
            data: {{
                labels: ['Faithfulness', 'Completeness', 'Business Relevance', 'Conciseness'],
                datasets: [{{
                    label: 'Average Quality Score',
                    data: [4.2, 4.1, 4.3, 4.5], // Placeholder - would need actual metric data
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    pointBackgroundColor: '#3498db',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#3498db'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        angleLines: {{ display: true }},
                        suggestedMin: 0,
                        suggestedMax: 5,
                        ticks: {{ stepSize: 1 }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Score Distribution (Bar Chart)
        const scoreDistributionCtx = document.getElementById('scoreDistributionChart').getContext('2d');
        new Chart(scoreDistributionCtx, {{
            type: 'bar',
            data: {{
                labels: ['Excellent (4.5-5.0)', 'Good (3.5-4.4)', 'Fair (2.5-3.4)', 'Poor (0.0-2.4)'],
                datasets: [{{
                    label: 'File Count',
                    data: [
                        {metrics['quality_distribution']['excellent']},
                        {metrics['quality_distribution']['good']},
                        {metrics['quality_distribution']['fair']},
                        {metrics['quality_distribution']['poor']}
                    ],
                    backgroundColor: ['#27ae60', '#f39c12', '#f1c40f', '#e74c3c'],
                    borderWidth: 1,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        precision: 0
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // Quality Ranges (Stacked Bar Chart)
        const qualityRangesCtx = document.getElementById('qualityRangesChart').getContext('2d');
        new Chart(qualityRangesCtx, {{
            type: 'bar',
            data: {{
                labels: {list(metrics['call_type_distribution'].keys())},
                datasets: [
                    {{
                        label: 'Excellent',
                        data: {self._get_quality_range_data(metrics, 'excellent')},
                        backgroundColor: '#27ae60'
                    }},
                    {{
                        label: 'Good',
                        data: {self._get_quality_range_data(metrics, 'good')},
                        backgroundColor: '#f39c12'
                    }},
                    {{
                        label: 'Fair',
                        data: {self._get_quality_range_data(metrics, 'fair')},
                        backgroundColor: '#f1c40f'
                    }},
                    {{
                        label: 'Poor',
                        data: {self._get_quality_range_data(metrics, 'poor')},
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Score Box Plot (using bar chart to simulate)
        const scoreBoxPlotCtx = document.getElementById('scoreBoxPlotChart').getContext('2d');
        new Chart(scoreBoxPlotCtx, {{
            type: 'bar',
            data: {{
                labels: ['Min', 'Q1', 'Median', 'Q3', 'Max'],
                datasets: [{{
                    label: 'Score Distribution',
                    data: [
                        {metrics['overall_score_stats']['min']},
                        {metrics['overall_score_stats']['average'] - metrics['overall_score_stats']['std_dev']},
                        {metrics['overall_score_stats']['median']},
                        {metrics['overall_score_stats']['average'] + metrics['overall_score_stats']['std_dev']},
                        {metrics['overall_score_stats']['max']}
                    ],
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': ' + context.raw.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Call Type Distribution (Pie Chart)
        const callTypeDistributionCtx = document.getElementById('callTypeDistributionChart').getContext('2d');
        new Chart(callTypeDistributionCtx, {{
            type: 'pie',
            data: {{
                labels: {list(metrics['call_type_distribution'].keys())},
                datasets: [{{
                    data: {list(metrics['call_type_distribution'].values())},
                    backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Call Type Performance (Bar Chart)
        const callTypePerformanceCtx = document.getElementById('callTypePerformanceChart').getContext('2d');
        new Chart(callTypePerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {list(metrics['call_type_distribution'].keys())},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_call_type_averages(metrics)},
                    backgroundColor: '#9b59b6',
                    borderColor: '#8e44ad',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // Performance Heatmap (Bar Chart simulation)
        const performanceHeatmapCtx = document.getElementById('performanceHeatmapChart').getContext('2d');
        new Chart(performanceHeatmapCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_heatmap_labels(metrics)},
                datasets: {self._get_heatmap_datasets(metrics)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Segment Performance (Horizontal Bar Chart)
        const segmentPerformanceCtx = document.getElementById('segmentPerformanceChart').getContext('2d');
        new Chart(segmentPerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {list(metrics['segment_averages'].keys())},
                datasets: [{{
                    label: 'Average Score',
                    data: {list(metrics['segment_averages'].values())},
                    backgroundColor: '#17a2b8',
                    borderColor: '#138496',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // Segment Quality by Call Type (Grouped Bar Chart)
        const segmentQualityCtx = document.getElementById('segmentQualityChart').getContext('2d');
        new Chart(segmentQualityCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_segment_labels(metrics)},
                datasets: {self._get_segment_datasets(metrics)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // AE/Sales Subtype Distribution (Donut Chart)
        const aeSalesSubtypeDistributionCtx = document.getElementById('aeSalesSubtypeDistributionChart').getContext('2d');
        new Chart(aeSalesSubtypeDistributionCtx, {{
            type: 'doughnut',
            data: {{
                labels: {self._get_ae_sales_subtype_labels(metrics)},
                datasets: [{{
                    data: {self._get_ae_sales_subtype_data(metrics)},
                    backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // AE/Sales Subtype Quality Comparison (Radar Chart)
        const aeSalesSubtypeQualityCtx = document.getElementById('aeSalesSubtypeQualityChart').getContext('2d');
        new Chart(aeSalesSubtypeQualityCtx, {{
            type: 'radar',
            data: {{
                labels: {self._get_ae_sales_subtype_labels(metrics)},
                datasets: [{{
                    label: 'Average Quality Score',
                    data: {self._get_ae_sales_subtype_quality_data(metrics)},
                    borderColor: '#9b59b6',
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    pointBackgroundColor: '#9b59b6',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#9b59b6'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        angleLines: {{ display: true }},
                        suggestedMin: 0,
                        suggestedMax: 5,
                        ticks: {{ stepSize: 1 }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // AE/Sales Demo/Evaluation Segments (Bar Chart)
        const aeSalesDemoSegmentsCtx = document.getElementById('aeSalesDemoSegmentsChart').getContext('2d');
        new Chart(aeSalesDemoSegmentsCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_ae_sales_subtype_segments('Demo/Evaluation')},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_ae_sales_demo_segment_data(metrics)},
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // AE/Sales Discovery/Qualification Segments (Bar Chart)
        const aeSalesDiscoverySegmentsCtx = document.getElementById('aeSalesDiscoverySegmentsChart').getContext('2d');
        new Chart(aeSalesDiscoverySegmentsCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_ae_sales_subtype_segments('Discovery/Qualification')},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_ae_sales_discovery_segment_data(metrics)},
                    backgroundColor: '#27ae60',
                    borderColor: '#229954',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // AE/Sales Negotiation/Close Segments (Bar Chart)
        const aeSalesNegotiationSegmentsCtx = document.getElementById('aeSalesNegotiationSegmentsChart').getContext('2d');
        new Chart(aeSalesNegotiationSegmentsCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_ae_sales_subtype_segments('Negotiation/Close')},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_ae_sales_negotiation_segment_data(metrics)},
                    backgroundColor: '#f39c12',
                    borderColor: '#e67e22',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // AE/Sales Proposal/Business Case Segments (Bar Chart)
        const aeSalesProposalSegmentsCtx = document.getElementById('aeSalesProposalSegmentsChart').getContext('2d');
        new Chart(aeSalesProposalSegmentsCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_ae_sales_subtype_segments('Proposal/Business Case')},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_ae_sales_proposal_segment_data(metrics)},
                    backgroundColor: '#e74c3c',
                    borderColor: '#c0392b',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // CSM Segment Performance (Bar Chart)
        const csmSegmentPerformanceCtx = document.getElementById('csmSegmentPerformanceChart').getContext('2d');
        new Chart(csmSegmentPerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_csm_segments()},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_csm_segment_data(metrics)},
                    backgroundColor: '#17a2b8',
                    borderColor: '#138496',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // CSM Quality Distribution (Stacked Bar Chart)
        const csmQualityDistributionCtx = document.getElementById('csmQualityDistributionChart').getContext('2d');
        new Chart(csmQualityDistributionCtx, {{
            type: 'bar',
            data: {{
                labels: ['Quality Distribution'],
                datasets: [
                    {{
                        label: 'Excellent',
                        data: [{self._get_csm_quality_data(metrics, 'excellent')}],
                        backgroundColor: '#27ae60'
                    }},
                    {{
                        label: 'Good',
                        data: [{self._get_csm_quality_data(metrics, 'good')}],
                        backgroundColor: '#f39c12'
                    }},
                    {{
                        label: 'Fair',
                        data: [{self._get_csm_quality_data(metrics, 'fair')}],
                        backgroundColor: '#f1c40f'
                    }},
                    {{
                        label: 'Poor',
                        data: [{self._get_csm_quality_data(metrics, 'poor')}],
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Internal Segment Performance (Bar Chart)
        const internalSegmentPerformanceCtx = document.getElementById('internalSegmentPerformanceChart').getContext('2d');
        new Chart(internalSegmentPerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_internal_segments()},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_internal_segment_data(metrics)},
                    backgroundColor: '#9b59b6',
                    borderColor: '#8e44ad',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // Internal Quality Analysis (Radar Chart)
        const internalQualityAnalysisCtx = document.getElementById('internalQualityAnalysisChart').getContext('2d');
        new Chart(internalQualityAnalysisCtx, {{
            type: 'radar',
            data: {{
                labels: {self._get_internal_segments()},
                datasets: [{{
                    label: 'Quality Analysis',
                    data: {self._get_internal_segment_data(metrics)},
                    borderColor: '#9b59b6',
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    pointBackgroundColor: '#9b59b6',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#9b59b6'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        angleLines: {{ display: true }},
                        suggestedMin: 0,
                        suggestedMax: 5,
                        ticks: {{ stepSize: 1 }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // SDR Segment Performance (Bar Chart)
        const sdrSegmentPerformanceCtx = document.getElementById('sdrSegmentPerformanceChart').getContext('2d');
        new Chart(sdrSegmentPerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_sdr_segments()},
                datasets: [{{
                    label: 'Average Score',
                    data: {self._get_sdr_segment_data(metrics)},
                    backgroundColor: '#e67e22',
                    borderColor: '#d35400',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // SDR Quality Metrics (Stacked Bar Chart)
        const sdrQualityMetricsCtx = document.getElementById('sdrQualityMetricsChart').getContext('2d');
        new Chart(sdrQualityMetricsCtx, {{
            type: 'bar',
            data: {{
                labels: ['Quality Metrics'],
                datasets: [
                    {{
                        label: 'Excellent',
                        data: [{self._get_sdr_quality_data(metrics, 'excellent')}],
                        backgroundColor: '#27ae60'
                    }},
                    {{
                        label: 'Good',
                        data: [{self._get_sdr_quality_data(metrics, 'good')}],
                        backgroundColor: '#f39c12'
                    }},
                    {{
                        label: 'Fair',
                        data: [{self._get_sdr_quality_data(metrics, 'fair')}],
                        backgroundColor: '#f1c40f'
                    }},
                    {{
                        label: 'Poor',
                        data: [{self._get_sdr_quality_data(metrics, 'poor')}],
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Cross-Call Type Quality (Bar Chart)
        const crossCallTypeQualityCtx = document.getElementById('crossCallTypeQualityChart').getContext('2d');
        new Chart(crossCallTypeQualityCtx, {{
            type: 'bar',
            data: {{
                labels: {list(metrics['call_type_distribution'].keys())},
                datasets: [{{
                    label: 'Overall Quality',
                    data: {self._get_call_type_averages(metrics)},
                    backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c'],
                    borderColor: ['#2980b9', '#229954', '#e67e22', '#c0392b'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
        
        // Common Segment Performance (Grouped Bar Chart)
        const commonSegmentPerformanceCtx = document.getElementById('commonSegmentPerformanceChart').getContext('2d');
        new Chart(commonSegmentPerformanceCtx, {{
            type: 'bar',
            data: {{
                labels: {self._get_common_segments()},
                datasets: {self._get_common_segment_datasets(metrics)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 5
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        """
    
    def _get_quality_range_data(self, metrics: Dict[str, Any], range_type: str) -> List[int]:
        """Get quality range data for stacked bar chart."""
        data = []
        for call_type in metrics['call_type_distribution'].keys():
            if call_type in metrics['call_type_quality']:
                dist = metrics['call_type_quality'][call_type]['distribution']
                data.append(dist.get(range_type, 0))
            else:
                data.append(0)
        return data
    
    def _get_call_type_averages(self, metrics: Dict[str, Any]) -> List[float]:
        """Get call type average scores."""
        averages = []
        for call_type in metrics['call_type_distribution'].keys():
            if call_type in metrics['call_type_quality']:
                averages.append(metrics['call_type_quality'][call_type]['average'])
            else:
                averages.append(0)
        return averages
    
    def _get_heatmap_labels(self, metrics: Dict[str, Any]) -> List[str]:
        """Get labels for heatmap chart."""
        labels = []
        for call_type in metrics['call_type_distribution'].keys():
            if call_type == "AE/Sales":
                # For AE/Sales, we need to get all possible segments from all subtypes
                all_segments = set()
                for subtype_segments in self.ae_sales_subtypes.values():
                    all_segments.update(subtype_segments)
                for segment in all_segments:
                    labels.append(f"{call_type} - {segment}")
            else:
                for segment in self.other_call_types.get(call_type, []):
                    labels.append(f"{call_type} - {segment}")
        return labels
    
    def _get_heatmap_datasets(self, metrics: Dict[str, Any]) -> List[Dict]:
        """Get datasets for heatmap chart."""
        datasets = []
        colors = ['#3498db', '#27ae60', '#f39c12', '#e74c3c']
        
        for i, call_type in enumerate(metrics['call_type_distribution'].keys()):
            data = []
            if call_type == "AE/Sales":
                # For AE/Sales, get all possible segments from all subtypes
                all_segments = set()
                for subtype_segments in self.ae_sales_subtypes.values():
                    all_segments.update(subtype_segments)
                for segment in all_segments:
                    key = f"{call_type}_{segment}"
                    if key in metrics['segment_averages']:
                        data.append(metrics['segment_averages'][key])
                    else:
                        data.append(0)
            else:
                for segment in self.other_call_types.get(call_type, []):
                    key = f"{call_type}_{segment}"
                    if key in metrics['segment_averages']:
                        data.append(metrics['segment_averages'][key])
                    else:
                        data.append(0)
            
            datasets.append({
                'label': call_type,
                'data': data,
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)],
                'borderWidth': 1
            })
        
        return datasets
    
    def _get_segment_labels(self, metrics: Dict[str, Any]) -> List[str]:
        """Get segment labels for segment quality chart."""
        segments = set()
        for call_type in metrics['call_type_distribution'].keys():
            if call_type == "AE/Sales":
                # For AE/Sales, get all possible segments from all subtypes
                for subtype_segments in self.ae_sales_subtypes.values():
                    segments.update(subtype_segments)
            else:
                segments.update(self.other_call_types.get(call_type, []))
        return list(segments)
    
    def _get_segment_datasets(self, metrics: Dict[str, Any]) -> List[Dict]:
        """Get datasets for segment quality chart."""
        datasets = []
        colors = ['#3498db', '#27ae60', '#f39c12', '#e74c3c']
        
        for i, call_type in enumerate(metrics['call_type_distribution'].keys()):
            data = []
            if call_type == "AE/Sales":
                # For AE/Sales, get all possible segments from all subtypes
                all_segments = set()
                for subtype_segments in self.ae_sales_subtypes.values():
                    all_segments.update(subtype_segments)
                for segment in all_segments:
                    key = f"{call_type}_{segment}"
                    if key in metrics['segment_averages']:
                        data.append(metrics['segment_averages'][key])
                    else:
                        data.append(0)
            else:
                for segment in self.other_call_types.get(call_type, []):
                    key = f"{call_type}_{segment}"
                    if key in metrics['segment_averages']:
                        data.append(metrics['segment_averages'][key])
                    else:
                        data.append(0)
            
            datasets.append({
                'label': call_type,
                'data': data,
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)],
                'borderWidth': 1
            })
        
        return datasets
    
    def _get_ae_sales_subtype_labels(self, metrics: Dict[str, Any]) -> List[str]:
        """Get AE/Sales subtype labels for charts."""
        return list(self.ae_sales_subtypes.keys())
    
    def _get_ae_sales_subtype_data(self, metrics: Dict[str, Any]) -> List[int]:
        """Get AE/Sales subtype distribution data."""
        # Count actual AE/Sales files by subtype from the evaluation results
        subtype_counts = {}
        for result in self.evaluation_results:
            if result.get('call_type_validation', {}).get('predicted_call_type') == 'AE/Sales':
                subtype = result.get('call_type_validation', {}).get('predicted_sub_type', 'Unknown')
                subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1
        
        # Map subtype counts to the order of subtypes in ae_sales_subtypes
        data = []
        for subtype in self.ae_sales_subtypes.keys():
            data.append(subtype_counts.get(subtype, 0))
        
        # If no data, provide fallback
        if not any(data):
            return [1, 0, 0, 0]  # Demo/Evaluation has 1, others 0
        
        return data
    
    def _get_ae_sales_subtype_quality_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get AE/Sales subtype quality scores."""
        # Calculate quality scores by aggregating segment scores for each subtype
        subtype_scores = {}
        
        for result in self.evaluation_results:
            if result.get('call_type_validation', {}).get('predicted_call_type') == 'AE/Sales':
                subtype = result.get('call_type_validation', {}).get('predicted_sub_type', 'Unknown')
                if subtype not in subtype_scores:
                    subtype_scores[subtype] = []
                
                # Get overall score for this file
                overall_score = result.get('overall_score', 0)
                if overall_score > 0:
                    subtype_scores[subtype].append(overall_score)
        
        # Calculate averages for each subtype
        data = []
        for subtype in self.ae_sales_subtypes.keys():
            if subtype in subtype_scores and subtype_scores[subtype]:
                avg_score = round(statistics.mean(subtype_scores[subtype]), 2)
                data.append(avg_score)
            else:
                data.append(0)
        
        # If no data, provide fallback
        if not any(data):
            return [4.0, 0, 0, 0]  # Demo/Evaluation has 4.0, others 0
        
        return data
    
    def _get_ae_sales_subtype_segments(self, subtype: str) -> List[str]:
        """Get segments for a specific AE/Sales subtype."""
        return self.ae_sales_subtypes.get(subtype, [])
    
    def _get_ae_sales_demo_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get Demo/Evaluation segment scores."""
        return self._get_subtype_segment_data(metrics, "Demo/Evaluation")
    
    def _get_ae_sales_discovery_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get Discovery/Qualification segment scores."""
        return self._get_subtype_segment_data(metrics, "Discovery/Qualification")
    
    def _get_ae_sales_negotiation_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get Negotiation/Close segment scores."""
        return self._get_subtype_segment_data(metrics, "Negotiation/Close")
    
    def _get_ae_sales_proposal_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get Proposal/Business Case segment scores."""
        return self._get_subtype_segment_data(metrics, "Proposal/Business Case")
    
    def _get_subtype_segment_data(self, metrics: Dict[str, Any], subtype: str) -> List[float]:
        """Get segment data for a specific subtype."""
        # Aggregate segment scores for this specific subtype
        segment_scores = {}
        
        for result in self.evaluation_results:
            if (result.get('call_type_validation', {}).get('predicted_call_type') == 'AE/Sales' and
                result.get('call_type_validation', {}).get('predicted_sub_type') == subtype):
                
                for segment in result.get('segment_evaluations', []):
                    segment_name = segment.get('segment_name')
                    weighted_score = segment.get('weighted_score', 0)
                    if segment_name and weighted_score > 0:
                        if segment_name not in segment_scores:
                            segment_scores[segment_name] = []
                        segment_scores[segment_name].append(weighted_score)
        
        # Calculate averages for each segment in this subtype
        data = []
        for segment in self.ae_sales_subtypes.get(subtype, []):
            if segment in segment_scores and segment_scores[segment]:
                avg_score = round(statistics.mean(segment_scores[segment]), 2)
                data.append(avg_score)
            else:
                data.append(0)
        
        # If no data, provide fallback
        if not any(data):
            return [4.0] * len(self.ae_sales_subtypes.get(subtype, []))
        
        return data
    
    def _get_csm_segments(self) -> List[str]:
        """Get CSM segment names."""
        return self.other_call_types["CSM/Post-Sale"]
    
    def _get_csm_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get CSM segment scores."""
        # Aggregate segment scores for CSM/Post-Sale calls
        segment_scores = {}
        
        for result in self.evaluation_results:
            if result.get('call_type_validation', {}).get('predicted_call_type') == 'CSM/Post-Sale':
                for segment in result.get('segment_evaluations', []):
                    segment_name = segment.get('segment_name')
                    weighted_score = segment.get('weighted_score', 0)
                    if segment_name and weighted_score > 0:
                        if segment_name not in segment_scores:
                            segment_scores[segment_name] = []
                        segment_scores[segment_name].append(weighted_score)
        
        # Calculate averages for each segment
        data = []
        for segment in self.other_call_types["CSM/Post-Sale"]:
            if segment in segment_scores and segment_scores[segment]:
                avg_score = round(statistics.mean(segment_scores[segment]), 2)
                data.append(avg_score)
            else:
                data.append(0)
        
        # If no data, provide fallback
        if not any(data):
            return [4.0] * len(self.other_call_types["CSM/Post-Sale"])
        
        return data
    
    def _get_csm_quality_data(self, metrics: Dict[str, Any], quality_type: str) -> int:
        """Get CSM quality distribution data."""
        if "CSM/Post-Sale" in metrics['call_type_quality']:
            return metrics['call_type_quality']["CSM/Post-Sale"]['distribution'].get(quality_type, 0)
        return 0
    
    def _get_internal_segments(self) -> List[str]:
        """Get Internal segment names."""
        return self.other_call_types["Internal/Implementation"]
    
    def _get_internal_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get Internal segment scores."""
        # Aggregate segment scores for Internal/Implementation calls
        segment_scores = {}
        
        for result in self.evaluation_results:
            if result.get('call_type_validation', {}).get('predicted_call_type') == 'Internal/Implementation':
                for segment in result.get('segment_evaluations', []):
                    segment_name = segment.get('segment_name')
                    weighted_score = segment.get('weighted_score', 0)
                    if segment_name and weighted_score > 0:
                        if segment_name not in segment_scores:
                            segment_scores[segment_name] = []
                        segment_scores[segment_name].append(weighted_score)
        
        # Calculate averages for each segment
        data = []
        for segment in self.other_call_types["Internal/Implementation"]:
            if segment in segment_scores and segment_scores[segment]:
                avg_score = round(statistics.mean(segment_scores[segment]), 2)
                data.append(avg_score)
            else:
                data.append(0)
        
        # If no data, provide fallback
        if not any(data):
            return [4.0] * len(self.other_call_types["Internal/Implementation"])
        
        return data
    
    def _get_sdr_segments(self) -> List[str]:
        """Get SDR segment names."""
        return self.other_call_types["SDR/Outbound"]
    
    def _get_sdr_segment_data(self, metrics: Dict[str, Any]) -> List[float]:
        """Get SDR segment scores."""
        # Aggregate segment scores for SDR/Outbound calls
        segment_scores = {}
        
        for result in self.evaluation_results:
            if result.get('call_type_validation', {}).get('predicted_call_type') == 'SDR/Outbound':
                for segment in result.get('segment_evaluations', []):
                    segment_name = segment.get('segment_name')
                    weighted_score = segment.get('weighted_score', 0)
                    if segment_name and weighted_score > 0:
                        if segment_name not in segment_scores:
                            segment_scores[segment_name] = []
                        segment_scores[segment_name].append(weighted_score)
        
        # Calculate averages for each segment
        data = []
        for segment in self.other_call_types["SDR/Outbound"]:
            if segment in segment_scores and segment_scores[segment]:
                avg_score = round(statistics.mean(segment_scores[segment]), 2)
                data.append(avg_score)
            else:
                data.append(0)
        
        # If no data, provide fallback
        if not any(data):
            return [4.0] * len(self.other_call_types["SDR/Outbound"])
        
        return data
    
    def _get_sdr_quality_data(self, metrics: Dict[str, Any], quality_type: str) -> int:
        """Get SDR quality distribution data."""
        if "SDR/Outbound" in metrics['call_type_quality']:
            return metrics['call_type_quality']["SDR/Outbound"]['distribution'].get(quality_type, 0)
        return 0
    
    def _get_common_segments(self) -> List[str]:
        """Get segments that appear across multiple call types."""
        # Find segments that appear in multiple call types
        segment_counts = defaultdict(int)
        for call_type in self.call_types:
            if call_type == "AE/Sales":
                # For AE/Sales, consider all subtype segments
                for subtype_segments in self.ae_sales_subtypes.values():
                    for segment in subtype_segments:
                        segment_counts[segment] += 1
            else:
                for segment in self.other_call_types.get(call_type, []):
                    segment_counts[segment] += 1
        
        # Return segments that appear in multiple call types
        common_segments = [segment for segment, count in segment_counts.items() if count > 1]
        return common_segments if common_segments else ["smart_summary", "next_steps"]  # Fallback
    
    def _get_common_segment_datasets(self, metrics: Dict[str, Any]) -> List[Dict]:
        """Get datasets for common segment performance across call types."""
        datasets = []
        colors = ['#3498db', '#27ae60', '#f39c12', '#e74c3c']
        
        for i, call_type in enumerate(metrics['call_type_distribution'].keys()):
            data = []
            common_segments = self._get_common_segments()
            
            for segment in common_segments:
                key = f"{call_type}_{segment}"
                if key in metrics['segment_averages']:
                    data.append(metrics['segment_averages'][key])
                else:
                    data.append(0)
            
            datasets.append({
                'label': call_type,
                'data': data,
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)],
                'borderWidth': 1
            })
        
        return datasets


def main():
    """Main function to generate the enhanced report."""
    # Use the examples/results directory
    results_dir = "/Users/darshil/Darshil/github/summarization_v2/summarization-v2/app/evaluation_framework/data/armis/results_old"
    output_file = "reports/evaluation_report_armis.html"
    
    generator = EnhancedReportGenerator(results_dir)
    generator.generate_html_report(output_file)
    
    print(f"Enhanced report generated successfully: {output_file}")


if __name__ == "__main__":
    main()
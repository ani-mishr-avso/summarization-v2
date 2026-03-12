import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import json
from pathlib import Path
import os
import streamlit.components.v1 as components
import math

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="LLM Eval Report", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    h1 { color: #1E3A8A; font-family: 'Helvetica Neue', sans-serif; }
    h2, h3, h4, h5 { color: #334155; }
    
    .custom-metric {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.5rem 1.25rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.2s ease;
    }
    .custom-metric:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    .custom-metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .custom-metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    
    .section-divider {
        margin-top: 2.5rem;
        margin-bottom: 2.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .diagnostic-header {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #475569;
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    
    .action-callout {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1.25rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.5rem;
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.5;
    }
    
    .appendix-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .appendix-title {
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    .appendix-text {
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Inject Print-Specific CSS
st.markdown("""
    <style>
    /* Targeted CSS that only activates when printing to PDF */
    @media print {
        /* Hide Streamlit UI elements (sidebar, hamburger menu, footer) */
        header, footer, .stSidebar, .stApp > header {
            display: none !important;
        }
        
        /* Ensure the main container expands to fill the PDF page */
        .block-container {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* Prevent metric cards and charts from breaking across pages */
        .custom-metric, .appendix-box, .section-divider {
            page-break-inside: avoid;
        }
        
        /* Hide the print button itself on the final PDF */
        #print-button-container {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# COLOR LOGIC & HELPER FUNCTIONS
# ==========================================
def get_score_color(val_str, metric_type="score"):
    try:
        val = float(str(val_str).replace('%', ''))
        
        if metric_type == "percentage":
            if val < 50: return "#ef4444"
            elif val < 70: return "#f59e0b"
            elif val < 90: return "#3b82f6"
            else: return "#10b981"
        elif metric_type == "ratio":
            if val < 0.5: return "#ef4444"
            elif val < 0.7: return "#f59e0b"
            elif val < 0.9: return "#3b82f6"
            else: return "#10b981"
        elif metric_type == "neutral":
            return "#1E3A8A"
        else:
            if val < 2.5: return "#ef4444"
            elif val < 3.5: return "#f59e0b"
            elif val < 4.5: return "#3b82f6"
            else: return "#10b981"
    except ValueError:
        return "#334155"

def render_dynamic_metric(label, value, metric_type="score"):
    # Calculate color based on the raw value
    color = get_score_color(value, metric_type)
    
    # Format the display string based on the metric type
    display_value = str(value)
    if metric_type == "score":
        # Append " / 5" with styled span to keep the denominator subtle
        display_value = f"{value} <span style='font-size: 1.1rem; color: #94a3b8; font-weight: 500;'>/ 5</span>"
    elif metric_type == "ratio":
        # Convert decimal ratio to whole number percentage
        try:
            display_value = f"{int(float(value) * 100)}%"
        except ValueError:
            pass
            
    html = f'''
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value" style="color: {color};">{display_value}</div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# DATA GENERATION
# ==========================================
results_file = Path("/Users/darshil/Darshil/github/summarization_v2/summarization-v2/app/evaluation_framework/data/iron_clad/results_old")
evaluation_results = []
failed_files = []

def load_evaluation_results() -> None:
    """Load all evaluation result files from the results directory."""
    json_files = list(results_file.glob("*.json"))
    evaluation_results = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                # Extract file ID from filename
                file_id = json_file.stem.replace('_output', '')
                result['file_id'] = file_id
                evaluation_results.append(result)
        except json.JSONDecodeError as e:
            failed_files.append((json_file.name, str(e)))
            print(f"Error loading {json_file}: {e}")
        except Exception as e:
            failed_files.append((json_file.name, str(e)))
            print(f"Error processing {json_file}: {e}")
    
    return evaluation_results

# Load the evaluation results
evaluation_results = load_evaluation_results()

total_files = len(evaluation_results)
correct_call_type = 0
valid_schemas = 0

overall_scores = []
pred_call_type = []
llm_call_type = []
call_type_passed = []
schema_validation_passed = []

for i in evaluation_results:
    call_type_passed.append(i.get('call_type_validation', {'validation_passed': 'False'}).get('validation_passed', 'False'))
    schema_validation_passed.append(i.get('schema_validation', {'schema_passed': 'False'}).get('schema_passed', 'False'))    
    
    pred_call_type.append(i.get('call_type_validation').get('predicted_call_type'))
    llm_call_type.append(i.get('call_type_validation').get('llm_predicted_call_type'))
    

    segment_resuls = i.get('segment_evaluations', [])
    avg_score = 0
    for segment in segment_resuls:
        avg_score += segment.get('weighted_score', 0)
    
    avg_score = avg_score / len(segment_resuls) if segment_resuls else 0
    overall_scores.append(avg_score)

summary_df = pd.DataFrame()
summary_df['pred_call_type'] = pred_call_type
summary_df['llm_call_type'] = llm_call_type
summary_df['overall_scores'] = overall_scores
summary_df['call_type_passed'] = call_type_passed
summary_df['schema_validation_passed'] = schema_validation_passed
bins = [0, 2.5, 3.5, 4.5, 5.0]
labels = ['Poor: 0.0-2.4', 'Fair: 2.5-3.4', 'Good: 3.5-4.4', 'Excellent: 4.5-5.0']
summary_df["band"] = pd.cut(
    summary_df["overall_scores"],
    bins=bins,
    labels=labels,
    include_lowest=True
)



kpi_data = {
    "Total Calls": {"value": len(summary_df), "type": "neutral"},
    "Call Type Accuracy": {"value": f"{float(summary_df['call_type_passed'].sum()*100/len(summary_df)):.1f}%", "type": "percentage"},
    "Schema Success": {"value": f"{min(1.0, float(summary_df['schema_validation_passed'].sum()/summary_df['call_type_passed'].sum()))*100:.1f}%", "type": "percentage"},
    "Average Score": {"value": f"{summary_df[summary_df['call_type_passed']]['overall_scores'].mean():.1f}", "type": "score"}
}

# call_types = ['AE/Sales', 'CSM/Post-Sale', 'Internal', 'SDR/Outbound']
call_types = ['CSM/Post-Sale', 'Internal/Implementation', 'AE/Sales', 'SDR/Outbound']
conf_matrix = np.array(pd.crosstab(summary_df['pred_call_type'], summary_df['llm_call_type']).reindex(index=call_types, columns=call_types).fillna(0).astype(int))

density_labels = list(summary_df[summary_df['call_type_passed']]['pred_call_type'].unique())
density_data = [np.array(summary_df[(summary_df['call_type_passed']) & (summary_df['pred_call_type']==i)]['overall_scores']) for i in density_labels]
# density_data = [np.array(summary_df[(summary_df['call_type_passed']) & (summary_df['pred_call_type']==i)]['overall_scores']) for i in call_types]
# density_labels = ['CSM/Post-Sale', 'Internal', 'AE/Sales', 'SDR/Outbound']
density_colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][:len(density_labels)]
scores_range = summary_df[summary_df['call_type_passed']]['overall_scores']
scores_range = [math.floor(scores_range.min()), math.ceil(scores_range.max())]


ae_sales_call = []
internal_call = []
csm_call = []
sdr_call = []

for i in evaluation_results:
    if i['call_type_validation']['predicted_call_type'] == "AE/Sales" and i['call_type_validation']['validation_passed'] == True:
        ae_sales_call.append(i['segment_evaluations'])
    elif i['call_type_validation']['predicted_call_type'] == "Internal/Implementation" and i['call_type_validation']['validation_passed'] == True:
        internal_call.append(i['segment_evaluations'])
    elif i['call_type_validation']['predicted_call_type'] == "CSM/Post-Sale" and i['call_type_validation']['validation_passed'] == True:
        csm_call.append(i['segment_evaluations'])
    elif i['call_type_validation']['predicted_call_type'] == "SDR/Outbound" and i['call_type_validation']['validation_passed'] == True:
        sdr_call.append(i['segment_evaluations'])
    elif i['call_type_validation']['validation_passed'] == False:
        pass
    else:
        print("Error")

def get_call_level_primary_metrics(call_segment_list):
    if not call_segment_list:
        return {'Faithfulness': 0, 'Completeness': 0, 'Conciseness': 0, 'Business Relevance': 0}
    primary_metrics = ['Faithfulness', 'Completeness', 'Conciseness', 'Business Relevance']
    overall_metrics_df = pd.DataFrame()
    for i in call_segment_list:
        score_df = pd.DataFrame()
        for segments in i:
            metric_dict = segments['metrics']
            if "BusinessRelevance" in metric_dict:
                metric_dict["Business Relevance"] = metric_dict.pop("BusinessRelevance")
            score_df = pd.concat([score_df, pd.DataFrame(metric_dict).loc[['score']]])
        score_df=score_df.dropna(subset=['Faithfulness'])
        score_df = score_df[primary_metrics]
        
        overall_metrics_df = pd.concat([overall_metrics_df, pd.DataFrame(score_df.mean()).T])
    
    return dict(overall_metrics_df.mean())

ae_sales_primary_scores = get_call_level_primary_metrics(ae_sales_call)
internal_call_primary_scores = get_call_level_primary_metrics(internal_call)
csm_call_primary_scores = get_call_level_primary_metrics(csm_call)
sdr_call_primary_scores = get_call_level_primary_metrics(sdr_call)

def get_action_item_scores(call_segment_list):
    if not call_segment_list:
        return {'precision': 0,'recall': 0,'timeline_accuracy': 0,'owner_attribution': 0}
    overall_metrics_df = pd.DataFrame()
    for i in call_segment_list:
        score_df = pd.DataFrame()
        for segment in i:
            metric_dict = segment['metrics']
            if "precision" in metric_dict:
                score_df = pd.concat([score_df, pd.DataFrame(metric_dict).T[['score']].T])
        overall_metrics_df = pd.concat([overall_metrics_df, pd.DataFrame(score_df.mean()).T])
    overall_metrics_df = dict(overall_metrics_df.mean())
    overall_metrics_df['precision'] = (overall_metrics_df['precision'] - 1) / 4 * 100
    overall_metrics_df['recall'] = (overall_metrics_df['recall'] - 1) / 4 * 100
    return overall_metrics_df

ae_sales_secondary_scores = get_action_item_scores(ae_sales_call)
internal_call_secondary_scores = get_action_item_scores(internal_call)
csm_call_secondary_scores = get_action_item_scores(csm_call)
sdr_call_secondary_scores = get_action_item_scores(sdr_call)

categories = ['Faithfulness', 'Completeness', 'Business Relevance', 'Conciseness']

drilldown_data = {
    "AE/Sales": {
        "metrics": {"Faithfulness": f"{ae_sales_primary_scores['Faithfulness']:.1f}", "Completeness": f"{ae_sales_primary_scores['Completeness']:.1f}", "Business Relevance": f"{ae_sales_primary_scores['Business Relevance']:.1f}", "Conciseness": f"{ae_sales_primary_scores['Conciseness']:.1f}" },
        "radar": [ae_sales_primary_scores['Faithfulness'], ae_sales_primary_scores['Completeness'], ae_sales_primary_scores['Business Relevance'], ae_sales_primary_scores['Conciseness']],
        "desc": "Struggling with extracting next-steps and pricing details. Highly recommended to add few-shot examples.",
        "diagnostic": {"Precision": f"{ae_sales_secondary_scores['precision']:.1f}%", "Recall": f"{ae_sales_secondary_scores['recall']:.1f}%", "Owner Attrib.": f"{ae_sales_secondary_scores['owner_attribution']:.1f}", "Timeline Acc.": f"{ae_sales_secondary_scores['timeline_accuracy']:.1f}"},
        "next_steps": "Low recall indicates the model is missing key entities. <strong>Action:</strong> Update the prompt schema."
    },
    "CSM/Post-Sale": {
        "metrics": {"Faithfulness": f"{csm_call_primary_scores['Faithfulness']:.1f}", "Completeness": f"{csm_call_primary_scores['Completeness']:.1f}", "Business Relevance": f"{csm_call_primary_scores['Business Relevance']:.1f}", "Conciseness": f"{csm_call_primary_scores['Conciseness']:.1f}" },
        "radar": [csm_call_primary_scores['Faithfulness'], csm_call_primary_scores['Completeness'], csm_call_primary_scores['Business Relevance'], csm_call_primary_scores['Conciseness']],
        "desc": "High performance overall. Excellent at capturing action items and summarizing client sentiment.",
        "diagnostic": {"Precision": f"{csm_call_secondary_scores['precision']:.1f}%", "Recall": f"{csm_call_secondary_scores['recall']:.1f}%", "Owner Attrib.": f"{csm_call_secondary_scores['owner_attribution']:.1f}", "Timeline Acc.": f"{csm_call_secondary_scores['timeline_accuracy']:.1f}"},
        "next_steps": "Metrics are stable. <strong>Action:</strong> Freeze current prompt version for CSM."
    },
    "Internal/Implementation": {
        "metrics": {"Faithfulness": f"{internal_call_primary_scores['Faithfulness']:.1f}", "Completeness": f"{internal_call_primary_scores['Completeness']:.1f}", "Business Relevance": f"{internal_call_primary_scores['Business Relevance']:.1f}", "Conciseness": f"{internal_call_primary_scores['Conciseness']:.1f}" },
        "radar": [internal_call_primary_scores['Faithfulness'], internal_call_primary_scores['Completeness'], internal_call_primary_scores['Business Relevance'], internal_call_primary_scores['Conciseness']],
        "desc": "Strong business relevance, but occasionally hallucinating timelines.",
        "diagnostic": {"Precision": f"{internal_call_secondary_scores['precision']:.1f}%", "Recall": f"{internal_call_secondary_scores['recall']:.1f}%", "Owner Attrib.": f"{internal_call_secondary_scores['owner_attribution']:.1f}", "Timeline Acc.": f"{internal_call_secondary_scores['timeline_accuracy']:.1f}"},
        "next_steps": "High recall but low timeline accuracy means the model is aggressively grabbing dates. <strong>Action:</strong> Inject Chain of Thought."
    },
    "SDR/Outbound": {
        "metrics": {"Faithfulness": f"{sdr_call_primary_scores['Faithfulness']:.1f}", "Completeness": f"{sdr_call_primary_scores['Completeness']:.1f}", "Business Relevance": f"{sdr_call_primary_scores['Business Relevance']:.1f}", "Conciseness": f"{sdr_call_primary_scores['Conciseness']:.1f}" },
        "radar": [sdr_call_primary_scores['Faithfulness'], sdr_call_primary_scores['Completeness'], sdr_call_primary_scores['Business Relevance'], sdr_call_primary_scores['Conciseness']],
        "desc": "Struggling to consistently identify BANT criteria. Too concise in areas requiring detail.",
        "diagnostic": {"Precision": f"{sdr_call_secondary_scores['precision']:.1f}%", "Recall": f"{sdr_call_secondary_scores['recall']:.1f}%", "Owner Attrib.": f"{sdr_call_secondary_scores['owner_attribution']:.1f}", "Timeline Acc.": f"{sdr_call_secondary_scores['timeline_accuracy']:.1f}"},
        "next_steps": "High precision but terrible recall. <strong>Action:</strong> Relax the strictness in the extraction prompt."
    }
}

# ==========================================
# DASHBOARD LAYOUT
# ==========================================
st.title("Context Aware Summarization")
st.subheader("LLM-as-a-Judge Evaluation: Benchmark Dataset Run")
st.markdown("---")

st.markdown("---")

# --- ROW 1: KPI Ribbon ---
cols = st.columns(4)
for i, (key, data) in enumerate(kpi_data.items()):
    with cols[i]:
        render_dynamic_metric(key, data["value"], metric_type=data["type"])

st.markdown("<br>", unsafe_allow_html=True)

# --- ROW 2: Confusion Matrix & Density Plot ---
st.markdown("### Classification & Score Distribution Analysis")
col1, col2 = st.columns((1, 1.2))

with col1:
    fig_cm = px.imshow(conf_matrix, labels=dict(x="Predicted", y="Actual", color="Count"),
                       x=call_types, y=call_types, color_continuous_scale="Blues", text_auto=True)
    fig_cm.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=380)
    st.plotly_chart(fig_cm, use_container_width=True)

with col2:
    fig_density = ff.create_distplot(density_data, density_labels, show_hist=False, show_rug=False, colors=density_colors)
    
    # NEW: Add shading under the density curves
    fig_density.update_traces(fill='tozeroy', opacity=0.002)
    
    fig_density.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=380,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_density.update_xaxes(title_text="Evaluation Score (0-5)", range=scores_range)
    st.plotly_chart(fig_density, use_container_width=True)

st.markdown("---")

# --- ROW 3: Call Type Drilldowns ---
st.markdown("### Score Drilldown by Call Type")

for call_type, data in drilldown_data.items():
    with st.container():
        st.markdown(f"#### {call_type}")
        
        col_text, col_chart = st.columns([2, 1])
        
        with col_text:
            st.info(f"**Model Insight:** {data['desc']}")
            
            # Primary Metrics rendered dynamically
            m1, m2, m3, m4 = st.columns(4)
            with m1: render_dynamic_metric("Faithfulness", data["metrics"]["Faithfulness"])
            with m2: render_dynamic_metric("Completeness", data["metrics"]["Completeness"])
            with m3: render_dynamic_metric("Business Relevance", data["metrics"]["Business Relevance"])
            with m4: render_dynamic_metric("Conciseness", data["metrics"]["Conciseness"])
            
            st.markdown('<div class="diagnostic-header">↳ Diagnostics & Action Plan</div>', unsafe_allow_html=True)
            
            # Diagnostic Metrics
            d1, d2, d3, d4 = st.columns(4)
            with d1: render_dynamic_metric("Precision", data["diagnostic"]["Precision"], metric_type="ratio")
            with d2: render_dynamic_metric("Recall", data["diagnostic"]["Recall"], metric_type="ratio")
            with d3: render_dynamic_metric("Owner Attrib.", data["diagnostic"]["Owner Attrib."])
            with d4: render_dynamic_metric("Timeline Acc.", data["diagnostic"]["Timeline Acc."])
            
            st.markdown(f'<div class="action-callout">💡 {data["next_steps"]}</div>', unsafe_allow_html=True)
            
        with col_chart:
            avg_score = sum(data["radar"]) / len(data["radar"])
            radar_color = get_score_color(avg_score, metric_type="score")
            
            fig_radar = go.Figure()
            radar_vals = data["radar"] + [data["radar"][0]]
            cat_vals = categories + [categories[0]]
            
            fig_radar.add_trace(go.Scatterpolar(r=radar_vals, theta=cat_vals, fill='toself', name=call_type, line_color=radar_color))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=300)
            st.plotly_chart(fig_radar, use_container_width=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# --- ROW 4: Appendix ---
st.markdown("### Appendix: Evaluation Framework & Metrics Glossary")
st.markdown("Review the defined rubrics and mathematical logic underpinning the LLM-as-a-Judge evaluations.")

app_col1, app_col2 = st.columns(2)

with app_col1:
    st.markdown('''
    <div class="appendix-box">
        <div class="appendix-title">General Quality Metrics (1-5 Scale)</div>
        <div class="appendix-text">
            <b>Faithfulness:</b> Evaluates if the summary is free of hallucinations and strictly adheres to the transcript. (5 = Faithful, 1 = Dangerous).<br><br>
            <b>Completeness:</b> Checks if all vital information from the transcript is included and no key details are omitted. (5 = Comprehensive, 1 = Incomplete).<br><br>
            <b>Business Relevance:</b> Evaluates whether the extracted information focuses on business-critical drivers vs. fluff. (5 = Critical Focus, 1 = Irrelevant).<br><br>
            <b>Conciseness:</b> Evaluates the brevity of the summary. A high score means maximum information density with minimal words.
        </div>
    </div>
    ''', unsafe_allow_html=True)

with app_col2:
    st.markdown('''
    <div class="appendix-box">
        <div class="appendix-title">Diagnostics & Next Steps Metrics</div>
        <div class="appendix-text">
            <b>Precision (Percentage):</b> Measures hallucinated tasks. Formula: <i>(Correct Predicted Items) / (Total Predicted Items)</i>.<br><br>
            <b>Recall (Percentage):</b> Measures dropped tasks. Formula: <i>(Correct Predicted Items) / (Total Ground Truth Items)</i>.<br><br>
            <b>Owner Attribution (1-5 Scale):</b> Assesses the correctness of identifying the responsible party for a given task. (5 = Correct, 1 = Unattributed).<br><br>
            <b>Timeline Accuracy (1-5 Scale):</b> Assesses the accuracy of dates, deadlines, and timeframes. (5 = Pinpoint, 1 = Missing).
        </div>
    </div>
    ''', unsafe_allow_html=True)
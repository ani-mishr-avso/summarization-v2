from bokeh.plotting import figure, output_file
from bokeh.io import save
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models import Div, InlineStyleSheet
from bokeh.transform import transform
from bokeh.palettes import Category20
import numpy as np
import json
from pathlib import Path
import os
import pandas as pd
from bokeh.transform import cumsum
from bokeh.palettes import Category10, Blues9


# Set output file
output_file("summarization_report.html")

results_file = Path("/Users/darshil/Darshil/github/summarization_v2/summarization-v2/app/evaluation_framework/data/armis/results_old")
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

# Calculate statistics
total_files = len(evaluation_results)
correct_call_type = 0
valid_schemas = 0

overall_scores = []
pred_call_type = []
call_type_passed = []
for i in evaluation_results:
    cct = i.get('call_type_validation', {'validation_passed': 'False'}).get('validation_passed', 'False')
    if cct == True:
        correct_call_type += 1
        call_type_passed.append(True)
    else:
        call_type_passed.append(False)
    csv = i.get('schema_validation', {'schema_passed': 'False'}).get('schema_passed', 'False')
    if csv == True:
        valid_schemas += 1

    pred_call_type.append(i.get('call_type_validation').get('predicted_call_type'))

    segment_resuls = i.get('segment_evaluations', [])
    avg_score = 0
    for segment in segment_resuls:
        avg_score += segment.get('weighted_score', 0)
    avg_score = avg_score / len(segment_resuls) if segment_resuls else 0
    overall_scores.append(avg_score)


summary_df = pd.DataFrame()
summary_df['pred_call_type'] = pred_call_type
summary_df['overall_scores'] = overall_scores
summary_df['call_type_passed'] = call_type_passed
bins = [0, 2.5, 3.5, 4.5, 5.0]
labels = ['Poor: 0.0-2.4', 'Fair: 2.5-3.4', 'Good: 3.5-4.4', 'Excellent: 4.5-5.0']
summary_df["band"] = pd.cut(
    summary_df["overall_scores"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

call_type_success_rate = (correct_call_type / total_files) * 100 if total_files > 0 else 0
schema_validation_success_rate = min(1, (valid_schemas / correct_call_type)) * 100 if correct_call_type > 0 else 0
print(schema_validation_success_rate)
average_overall_score = float(summary_df[summary_df['call_type_passed']==True]['overall_scores'].mean()) #avg_score

print(f"Total files found: {total_files}")

# Create title
title = Div(
    text="""
<div style="margin-bottom: 40px; text-align: center; padding-top: 50px;">
    <h1 style="color: #110d4f; margin: 0; font-size: 40px; font-weight: bold;">Context Aware Summarization - LLM-as-a-Judge Evaluation Report</h1>
</div>
""",
    sizing_mode="stretch_width",
)

# Stylesheet to override Bokeh's default flex-start alignment so children stretch to full width
col_stylesheet = InlineStyleSheet(css=".bk-panel-models-layout-Column { align-items: stretch !important; }")

overall_summary = Div(
    text="""
<div style="margin-bottom: 4px; text-align: center; padding-top: 40px; padding-left: 5px;">
    <h1 style="color: #2b2b2b; margin: 0; font-size: 26px;">Overall Summary</h1>
</div>
""",
    sizing_mode="stretch_width",
)

# <h2 style="color: #333; margin-top: 0;">📊 Overall Summary</h2>
# Create statistics section
stats_html = f"""
<div style="background-color: #f5f5f5; padding: 20px; margin-bottom: 30px; width=100%">
    
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 15px;">
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #1f77b4;">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Total Files</p>
            <p style="margin: 5px 0 0 0; color: #1f77b4; font-size: 28px; font-weight: bold;">{total_files}</p>
        </div>
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #2ca02c;">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Call Type AccuracyProcessed</p>
            <p style="margin: 5px 0 0 0; color: #2ca02c; font-size: 28px; font-weight: bold;">{call_type_success_rate:.1f}%</p>
        </div>
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #d62728;">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Schema Validation Success Rate%</p>
            <p style="margin: 5px 0 0 0; color: #d62728; font-size: 28px; font-weight: bold;">{schema_validation_success_rate:.1f}%</p>
        </div>
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #d62728;">
            <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Average Score</p>
            <p style="margin: 5px 0 0 0; color: #d62728; font-size: 28px; font-weight: bold;">{average_overall_score:.1f}</p>
        </div>
    </div>
</div>
"""

stats = Div(text=stats_html)

score_analysis_div = Div(
    text="""
<div style="margin-bottom: 4px; text-align: center; padding-top: 40px; padding-left: 5px;">
    <h1 style="color: #2b2b2b; margin: 0; font-size: 26px;">Score Analysis</h1>
</div>
""",
    sizing_mode="stretch_width",
)

####### Score Dist #######
# df = pd.DataFrame({"score": overall_scores})
# bins = [0, 2.5, 3.5, 4.5, 5.0]
# labels = ['Poor: 0.0-2.4', 'Fair: 2.5-3.4', 'Good: 3.5-4.4', 'Excellent: 4.5-5.0']
# df["band"] = pd.cut(
#     df["score"],
#     bins=bins,
#     labels=labels,
#     include_lowest=True
# )
df = (
    summary_df[summary_df["call_type_passed"]==True]["band"]
    .value_counts()
    .reindex(labels)   # enforce desired order
    .reset_index()
)
df.columns = ["band", "count"]
source = ColumnDataSource(df)

score_dist = figure(
    x_range=labels,
    title="Overall Score Distribution",
    x_axis_label="Score band",
    y_axis_label="Number of calls",
    height=400,
    width=600
)
score_dist.vbar(x="band", top="count", width=0.9, source=source)
score_dist.xgrid.grid_line_color = None
score_dist.y_range.start = 0

score_dist.title.align = "center"
score_dist.title.text_font_size = "12pt"
####### ####### #######

bands = labels

stack_df = (
    summary_df[summary_df['call_type_passed']]
    .groupby(['pred_call_type','band'])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=bands)
    .reset_index()
    .fillna(0)
)

source = ColumnDataSource(stack_df)

score_dist_call_type = figure(
    x_range=list(stack_df["pred_call_type"]),
    title="Score Distribution by Call Type",
    x_axis_label="Call Type",
    y_axis_label="Number of calls",
    height=400,
    width=600
)
colors = ["#d73027", "#fc8d59", "#6cba4d", "#21972b"]
score_dist_call_type.vbar_stack(
    bands,
    x='pred_call_type',
    source=source,
    width=0.9,
    legend_label=bands,
    color=colors
)

score_dist_call_type.title.align = "center"
score_dist_call_type.title.text_font_size = "12pt"

##### ##### #####

call_type_analysis_div = Div(
    text="""
<div style="margin-bottom: 4px; text-align: center; padding-top: 40px; padding-left: 5px;">
    <h1 style="color: #2b2b2b; margin: 0; font-size: 26px;">Call Type Analysis</h1>
</div>
""",
    sizing_mode="stretch_width",
)

call_type_df = (
    summary_df[summary_df['call_type_passed']]
    .groupby("pred_call_type")
    .size()
    .reset_index(name="count")
)

# Sort for better visual ordering
call_type_df = call_type_df.sort_values("count", ascending=False)

# Convert counts to angles
call_type_df["angle"] = call_type_df["count"] / call_type_df["count"].sum() * 2 * np.pi

# Assign colors
n = len(call_type_df)
# palette = Category10[10] if n <= 10 else Category10[10] * (n // 10 + 1)
palette = Blues9 #[9] if n <= 9 else Blues9[9] * (n // 9 + 1)
call_type_df["color"] = palette[:n]

# Convert to Bokeh source
source = ColumnDataSource(call_type_df)


# ---- Create pie chart ----
call_type_pie = figure(
    height=400,
    width=500,
    title="Call Type Distribution",
    toolbar_location=None,
    tools="hover",
    tooltips="@pred_call_type: @count",
    x_range=(-1, 1)
)

call_type_pie.wedge(
    x=0,
    y=0,
    radius=0.6,
    start_angle=cumsum("angle", include_zero=True),
    end_angle=cumsum("angle"),
    line_color="white",
    fill_color="color",
    legend_field="pred_call_type",
    source=source
)

# Remove axes/grid
call_type_pie.axis.visible = False
call_type_pie.grid.grid_line_color = None
call_type_pie.title.align = "center"
call_type_pie.title.text_font_size = "12pt"

# Legend formatting
call_type_pie.legend.location = "top_right"
call_type_pie.legend.label_text_font_size = "10pt"

##### ##### #####

avg_df = (
    summary_df[summary_df['call_type_passed']]
    .groupby("pred_call_type")["overall_scores"]
    .mean()
    .reset_index(name="avg_score")
)
avg_df = avg_df.sort_values("avg_score")
source = ColumnDataSource(avg_df)

avg_score_plot = figure(
    y_range=avg_df["pred_call_type"].tolist(),
    height=400,
    width=600,
    title="Average Score by Call Type",
    x_axis_label="Average Score",
    y_axis_label="Call Type",
    tools="hover",
    tooltips="@pred_call_type: @avg_score{0.00}"
)
avg_score_plot.hbar(
    y="pred_call_type",
    right="avg_score",
    height=0.6,
    source=source
)
avg_score_plot.x_range.start = 0
avg_score_plot.xgrid.grid_line_color = None
avg_score_plot.title.text_font_size = "12pt"
avg_score_plot.title.align = "center"
avg_score_plot.x_range.end = 5

########## Call Specific Analysis ##########

call_specific_analysis_div = Div(
    text="""
<div style="margin-bottom: 4px; text-align: center; padding-top: 40px; padding-left: 5px;">
    <h1 style="color: #2b2b2b; margin: 0; font-size: 26px;">Call Type Detailed Analysis</h1>
</div>
""",
    sizing_mode="stretch_width",
)

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


def stats_html_func(metric, call_name):
    stats_html = f"""
    <div style="background-color: #f5f5f5; padding: 20px; margin-bottom: 30px; width=100%">
        <h2 style="color: #333; margin-top: 0; ">📊 {call_name} Scores</h2>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 15px;">
            <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #1f77b4;">
                <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Faithfulness</p>
                <p style="margin: 5px 0 0 0; color: #1f77b4; font-size: 28px; font-weight: bold;">{metric['Faithfulness']:.1f}</p>
            </div>
            <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #2ca02c;">
                <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Completeness</p>
                <p style="margin: 5px 0 0 0; color: #2ca02c; font-size: 28px; font-weight: bold;">{metric['Completeness']:.1f}</p>
            </div>
            <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #d62728;">
                <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Business Relevance</p>
                <p style="margin: 5px 0 0 0; color: #d62728; font-size: 28px; font-weight: bold;">{metric['Business Relevance']:.1f}</p>
            </div>
            <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #d62728;">
                <p style="margin: 0; color: #666; font-size: 12px; font-weight: bold; text-transform: uppercase;">Conciseness</p>
                <p style="margin: 5px 0 0 0; color: #d62728; font-size: 28px; font-weight: bold;">{metric['Conciseness']:.1f}</p>
            </div>
        </div>
    </div>
    """
    return stats_html

ae_stats = Div(text=stats_html_func(ae_sales_primary_scores, "AE/Sales"), width=500, align="center")
internal_stats = Div(text=stats_html_func(internal_call_primary_scores, "Internal/Implementation") , width=500)
csm_stats = Div(text=stats_html_func(csm_call_primary_scores, "CSM/Post-Sale"))
sdr_stats = Div(text=stats_html_func(sdr_call_primary_scores, "SDR/Outbound"))

layout = column(
    title,
    overall_summary,
    stats,
    score_analysis_div,
    row(score_dist,score_dist_call_type),
    call_type_analysis_div,
    row(call_type_pie,avg_score_plot),
    call_specific_analysis_div,
    row(ae_stats, csm_stats),
    row(internal_stats, sdr_stats),


    sizing_mode="stretch_width",
    stylesheets=[col_stylesheet],
)

# Save to HTML
save(layout)
print("Report saved as 'summarization_report.html'")


from bokeh.plotting import figure, output_file, save
from bokeh.layouts import row, column
from bokeh.models import Div
from bokeh.transform import transform
from bokeh.palettes import Category20
import numpy as np

# Set output file
output_file("summarization_report.html")

# Create dummy data
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
sales_data = [150, 200, 175, 250, 220, 290]
visitors_data = [100, 120, 110, 160, 140, 180]

# Time series data for line chart
weeks = list(range(1, 13))
engagement = [45, 50, 48, 65, 72, 85, 92, 88, 95, 110, 125, 135]

# Pie chart data
categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
values = [35, 25, 20, 15, 5]
colors = ['#3182bd', '#e6550d', '#31a354', '#756bb1', '#ff7f0e']

# ===== BAR CHART =====
p1 = figure(x_range=months, 
            title="Sales by Month",
            toolbar_location=None,
            tools="",
            width=400, 
            height=400)
p1.vbar(x=months, top=sales_data, width=0.7, color='steelblue')
p1.xaxis.axis_label = 'Month'
p1.yaxis.axis_label = 'Sales ($)'
p1.title.text_font_size = '14pt'

# ===== LINE CHART =====
p2 = figure(title="User Engagement Over Time",
            x_axis_label='Week',
            y_axis_label='Engagement Score',
            toolbar_location=None,
            tools="",
            width=400, 
            height=400)
p2.line(weeks, engagement, line_width=2, color='navy', alpha=0.8)
p2.circle(weeks, engagement, size=5, color='navy', alpha=0.5)
p2.title.text_font_size = '14pt'

# Combine bar and line charts in one row
charts_row = row(p1, p2)

# ===== SECTION HEADING =====
section_heading = Div(text="""
<h2 style="color: #333; margin-top: 30px; margin-bottom: 20px;">Category Distribution</h2>
""")

# ===== PIE CHART =====
# Create pie chart data
angle_offset = 0
angles = []
angle_sum = 0
for value in values:
    angle = (value / sum(values)) * 2 * np.pi
    angles.append(angle)

# Calculate cumulative angles for positioning
cumulative_angles = []
cumulative = 0
for angle in angles:
    cumulative_angles.append(cumulative)
    cumulative += angle

# Create pie chart using wedges
p3 = figure(title="Distribution by Category",
            toolbar_location=None,
            tools="hover",
            tooltips="@category: @value",
            width=500, 
            height=400,
            x_range=(-0.5, 1.0))

# Prepare data for wedges
pie_data = {
    'category': categories,
    'value': values,
    'angle': angles,
    'color': colors,
    'cum_angle': cumulative_angles
}

p3.wedge(x=0, y=1, radius=0.4,
         start_angle=transform('cum_angle', cumulative_angles),
         end_angle=transform('cum_angle', cumulative_angles),
         fill_color='color',
         legend_field='category',
         source=pie_data)

# Adjust wedge end_angle calculation
from bokeh.models import ColumnDataSource
source = ColumnDataSource(data={
    'category': categories,
    'value': values,
    'angle': angles,
    'color': colors,
    'cum_angle': cumulative_angles
})

p3 = figure(title="Distribution by Category",
            toolbar_location=None,
            tools="",
            width=500, 
            height=400,
            x_range=(-0.5, 1.0),
            y_range=(0, 1))
p3.axis.visible = False
p3.grid.grid_line_color = None

# Create wedges manually
for i, (category, value, color) in enumerate(zip(categories, values, colors)):
    start_angle = sum(angles[:i])
    end_angle = start_angle + angles[i]
    p3.wedge(x=0, y=1, radius=0.4,
             start_angle=start_angle,
             end_angle=end_angle,
             fill_color=color,
             line_color='white',
             line_width=2)

# Add legend manually with labels
label_angles = []
for i in range(len(categories)):
    start_angle = sum(angles[:i])
    label_angle = start_angle + angles[i] / 2
    label_angles.append(label_angle)

# Add labels to pie chart
from bokeh.models import LabelSet, ColumnDataSource
label_distance = 0.65
label_x = [label_distance * np.cos(angle - np.pi/2) for angle in label_angles]
label_y = [1 + label_distance * np.sin(angle - np.pi/2) for angle in label_angles]

label_source = ColumnDataSource(data={
    'x': label_x,
    'y': label_y,
    'text': [f"{cat} ({val})" for cat, val in zip(categories, values)]
})

labels = LabelSet(x='x', y='y', text='text', source=label_source,
                  text_font_size='10pt', text_align='center')
p3.add_layout(labels)
p3.title.text_font_size = '14pt'

# ===== LAYOUT =====
# Title
title = Div(text="""
<h1 style="text-align: center; color: #1f77b4; margin-bottom: 30px;">Summarization Report</h1>
""")

# Combine everything
layout = column(
    title,
    charts_row,
    section_heading,
    p3
)

# Save to HTML
save(layout)
print("Report saved as 'summarization_report.html'")

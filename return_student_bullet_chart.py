import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from io import BytesIO


from reportlab.lib.units import mm, inch
from reportlab.platypus import Image


def return_daily_only(attd_df):
    data_df = attd_df[attd_df["Course"] == "DAILY"]
    return main(attd_df, data_df, y_aspect=70)


def return_classes_only(attd_df):
    data_df = attd_df[attd_df["Course"] != "DAILY"]
    return main(attd_df, data_df, y_aspect=475)


def main(
    attd_df,
    data_df,
    y_aspect=400,
):
    data_df = data_df.reset_index()
    fig = go.Figure()

    student_name = attd_df.iloc[0, :]["Student Name"]
    total_days_absent = attd_df.iloc[-1, :]["Number Days Absent"]
    total_days_enrolled = attd_df.iloc[-1, :]["Number Reporting Days"]

    x_range_student = attd_df["Number Days Absent"].max()
    x_range_comp = attd_df["Median Days Absent"].max()
    x_range = max(x_range_student, x_range_comp)
    x_range = total_days_enrolled

    if x_range < 20:
        gauge_axis_dtick = 1
    elif x_range < 40:
        gauge_axis_dtick = 2
    else:
        gauge_axis_dtick = 5

    fig = go.Figure()

    num_of_classes = len(data_df)
    y_ranges = []

    width = 1 / num_of_classes
    adjusted_width = 0.5 * width
    for i in range(num_of_classes):
        center = width / 2 + i * width
        y_range = [
            center - adjusted_width / 2 + 0.04,
            min(center + adjusted_width / 2 + 0.04,1),
        ]
        y_ranges.append(y_range)

    if num_of_classes == 1:
        y_ranges = [[0.5, 0.8]]

    for i, class_attd in data_df.iterrows():
        value = class_attd["Number Days Absent"]
        reference = class_attd["Median Days Absent"]
        title = class_attd["Label"]


        bar_color = 'Black'

        fig.add_trace(
            go.Indicator(
                # mode="number+gauge+delta",
                mode="gauge",
                value=value,
                delta={"reference": total_days_absent},
                domain={"x": [0.15, 1], "y": y_ranges[i]},
                title={"text": title, "font": {"size": 12}},
                gauge={
                    "shape": "bullet",
                    "axis": {"range": [None, x_range + 1]},
                    "threshold": {
                        "line": {"color": "black", "width": 2},
                        "thickness": 0.75,
                        "value": total_days_absent,
                    },
                    "steps": [
                        {"range": [0, reference], "color": "lightgray"},
                    ],
                    "bar": {"color": bar_color,"line":{"color":'black',"width":1}},
                },
            )
        )

    x_aspect = 700

    scale = 1.25

    fig.add_annotation(x=0.5+0.15/2, y=0,text="Total Missed Days",    xref="x domain",
    yref="y domain",showarrow=False)
    
    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=0, b=0),
        height=scale * y_aspect,
        width=scale * x_aspect,
    )

    fig.update_traces(
        gauge_axis_dtick=gauge_axis_dtick,
        gauge_axis_tick0=0,
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)
    I = Image(buffer)
    I.drawHeight = y_aspect / x_aspect * 6 * inch
    I.drawWidth = x_aspect / x_aspect * 6 * inch

    return I

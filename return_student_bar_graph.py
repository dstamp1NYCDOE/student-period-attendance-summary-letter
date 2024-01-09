import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from io import BytesIO


from reportlab.lib.units import mm, inch
from reportlab.platypus import Image

def return_daily_only(attd_df):
    attd_df = attd_df[attd_df['Course']=='DAILY']
    return main(attd_df,y_aspect = 125)

def return_classes_only(attd_df):
    attd_df = attd_df[attd_df['Course']!='DAILY']
    return main(attd_df, y_aspect = 450)    

def main(attd_df, y_aspect = 400):
    fig = go.Figure()

    student_name = attd_df.iloc[0,1]

    data_cols = [
        'Label', 'Number Days Absent','Median Days Absent'
    ]
    data_df = attd_df[data_cols]
    


    fig.add_trace(go.Bar(
        y=data_df['Label'],
        x=data_df['Median Days Absent'],
        name='Average HSFI Student',
        orientation='h',
        width=0.75,
        marker_color='lightgrey',
        marker_line_color='grey',
        opacity=0.6,
        marker_line_width=2
    ))

    fig.add_trace(go.Bar(
        y=data_df['Label'],
        x=data_df['Number Days Absent'],
        name=student_name,
        orientation='h',
        width=0.25,
        
        marker_color='black',
    ))

    x_aspect = 700
    
    scale = 1.25

    fig.update_layout(
        template = 'simple_white',
        margin=dict(l=0, r=0, t=50, b=0),
        # title={
        # 'text':f"2023-2024 Attd for {student_name}",
        # 'font_family':"Avenir Next Condensed",
        # },
        barmode='overlay',
        height=scale*y_aspect,
        width=scale*x_aspect,
        xaxis_title="Total Missed Days of Class",
        
        # yaxis_title="Course",
        legend=dict(
        orientation="h",
        entrywidth=110,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1),
        xaxis = dict(
            tickmode = 'linear',
            tick0 = 0,
            dtick = 1,
            showgrid=True,
            gridwidth=2,
            gridcolor='darkgrey',
        ),
    )

    
    buffer = BytesIO()
    pio.write_image(fig, buffer)
    I = Image(buffer)
    I.drawHeight =  y_aspect/x_aspect*6*inch
    I.drawWidth = x_aspect/x_aspect*6*inch

    return I

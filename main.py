import pandas as pd

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate


import return_student_bar_graph
import return_student_bullet_chart


def main(data):
    RIPA_df = pd.read_excel("data/RIPA.xlsx", skiprows=3)
    RIPA_df = RIPA_df.rename(columns={"Student ID": "StudentID"})

    daily_df = RIPA_df[RIPA_df["Course Section"] == "DAILY-ATTD"]

    programs_df = pd.read_csv("data/1_01.csv").drop_duplicates(
        subset=["StudentID", "Course", "Section"]
    )
    cols = ["StudentID", "Course", "Section", "Teacher1", "Period",'Mark2']
    programs_df = programs_df[cols]

    programs_df["Course Section"] = programs_df.apply(
        lambda x: f"{x['Course']}-{str(x['Section']).zfill(2)}", axis=1
    )

    RIPA_df = programs_df.merge(
        RIPA_df, on=["StudentID", "Course Section"], how="left"
    ).dropna()

    RIPA_df = pd.concat([RIPA_df, daily_df])
    RIPA_df = RIPA_df.fillna({"Period": -1, "Teacher1": "", "Course": "DAILY"})

    RIPA_df["Dept"] = RIPA_df["Course"].apply(return_course_dept)
    RIPA_df["Label"] = RIPA_df.apply(return_bar_label, axis=1)

    ## determine median absences by course/section
    median_abs_by_course_section = pd.pivot_table(
        RIPA_df,
        index="Course Section",
        values="Number Days Absent",
        aggfunc="median",
    )
    median_abs_by_course_section.columns = ["Median Days Absent"]
    median_abs_by_course_section = median_abs_by_course_section.reset_index()

    RIPA_df = RIPA_df.merge(
        median_abs_by_course_section, on=["Course Section"], how="left"
    ).fillna(0)

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="Normal_RIGHT",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body_Justify",
            parent=styles["BodyText"],
            alignment=TA_JUSTIFY,
        )
    )

    letter_head = [
        Paragraph("High School of Fashion Industries", styles["Normal"]),
        Paragraph("225 W 24th St", styles["Normal"]),
        Paragraph("New York, NY 10011", styles["Normal"]),
        Paragraph("Principal, Daryl Blank", styles["Normal"]),
    ]

    closing = [
        Spacer(width=0, height=0.25 * inch),
        Paragraph("Warmly,", styles["Normal_RIGHT"]),
        Paragraph("Derek Stampone", styles["Normal_RIGHT"]),
        Paragraph("Assistant Principal, Attendance", styles["Normal_RIGHT"]),
    ]

    flowables = []

    RIPA_df = RIPA_df[RIPA_df["StudentID"] == 234056992]
    

    for (student_name, StudentID), attd_df in RIPA_df.groupby(
        ["Student Name", "StudentID"]
    ):
        if len(attd_df) <= 1:
            continue

        attd_df = attd_df.sort_values(by=["Period"], ascending=False)

        total_days_absent = attd_df.iloc[-1, :]["Number Days Absent"]
        total_days_enrolled = attd_df.iloc[-1, :]["Number Reporting Days"]

        total_missed_days_of_classes = (
            attd_df["Number Days Absent"].sum() - total_days_absent
        )

        flowables.extend(letter_head)
        flowables.append(Spacer(width=0, height=0.25 * inch))

        first_name = student_name.split(",")[1]
        last_name = student_name.split(",")[0]
        student_name = f"{first_name.title()} {last_name.title()}"
        paragraph = Paragraph(
            f"Dear {student_name} ({StudentID}) and your Parent/Guardian,",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        paragraph = Paragraph(
            f"{first_name} has missed {total_days_absent:.0f} out of {total_days_enrolled:.0f} days this school year. In the chart below, the narrow bar represents {first_name}'s days absent (based on period 3 official attendance) and the wide gray bar represents the average days absent for HSFI Students.",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        chart_flowable = return_student_bullet_chart.return_daily_only(attd_df)
        flowables.append(chart_flowable)

        paragraph = Paragraph(
            f"Attending on time every day to all classes will help {first_name} learn and stay on track. {first_name} missed {total_missed_days_of_classes:.0f} periods of instruction combined in all of their classes including excused absences, early dismissals, field trips, PSAL games, etc.. In the chart below, the narrow bar represents {first_name}'s periods absent by class and the wide gray bar represents the average periods absent of the other students in {first_name}'s classes.",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        chart_flowable = return_student_bullet_chart.return_classes_only(attd_df)
        flowables.append(chart_flowable)

        paragraph = Paragraph(
            f"You are key to helping {first_name} attend school on time every day and every period possible; our classes are better when {first_name} is there!",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        paragraph = Paragraph(
            f"We are here to help! Call the school (212-255-1235) and we will connect you to {first_name}'s counselor, attendance teacher, classroom teachers, or any other resources.",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        flowables.extend(closing)
        flowables.append(PageBreak())

    filename = "output/Fall2023-StudentAttendanceSummaryLetter.pdf"
    my_doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)
    return True


def return_bar_label(row):
    PD = row["Period"]
    Course = row["Course"]
    if PD == -1 and Course == "DAILY":
        return "Overall<br>Daily<br>Absences"
    Dept = row["Dept"]
    Teacher = row["Teacher1"].title()
    return f"P{int(PD)} {Dept}<br>{Teacher}"


def return_course_dept(course_code):
    if course_code == "DAILY":
        return "Overall"
    if course_code[0] == "E":
        return "ELA"
    if course_code[0] == "M":
        return "Math"
    if course_code[0] == "S":
        return "Science"
    if course_code[0:2] == "FS":
        return "Spanish"
    if course_code[0] == "H":
        return "SS"
    if course_code[0] == "R":
        return "Career<br>Readiness"
    if course_code[0:2] == "PP":
        return "Phys Ed"
    if course_code[0:2] == "PH":
        return "Health"
    if course_code[0:2] == "GA":
        return "Advisory"
    if course_code[0:2] == "GQ":
        return "College Apps"
    if course_code in ["AHS22X", "AHS22X"]:
        return "AP Art Hist"
    if course_code in ["APS21X", "APS22X"]:
        return "AP Art 2D"
    if course_code[0] in ["A", "B", "T"]:
        return "CTE"
    if course_code[0:2] in ["SK"]:
        return "CTE"

if __name__ == "__main__":
    data = {}
    main(data)

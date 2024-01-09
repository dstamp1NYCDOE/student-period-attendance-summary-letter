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


def main(data):
    RIPA_df = pd.read_excel("data/RIPA.xlsx", skiprows=3)
    RIPA_df["Course"] = RIPA_df["Course Section"].apply(lambda x: x.split("-")[0])
    RIPA_df["Section"] = RIPA_df["Course Section"].apply(lambda x: x.split("-")[1])

    print(RIPA_df)

    # HonorRoll_df = pd.read_excel('data/HonorRoll.xlsx')
    # HonorRoll_StudentIDs = HonorRoll_df['Student ID'].to_list()

    MasterSchedule_df = pd.read_excel("data/MasterSchedule.xlsx").drop_duplicates(
        subset=["Course Code", "Section"]
    )
    MasterSchedule_df["Course Section"] = MasterSchedule_df.apply(
        lambda x: f"{x['Course Code']}-{str(x['Section']).zfill(2)}", axis=1
    )
    MasterSchedule_df = MasterSchedule_df[["Course Section", "Teacher Name", "PD"]]
    print(MasterSchedule_df)

    RIPA_df = RIPA_df.merge(
        MasterSchedule_df, on=["Course Section"], how="left"
    ).fillna({"Teacher Name": "", "PD": -1})

    RIPA_df["Dept"] = RIPA_df["Course"].apply(return_course_dept)
    RIPA_df["Label"] = RIPA_df.apply(return_bar_label, axis=1)

    ## determine median absences by course/section
    median_abs_by_course_section = pd.pivot_table(
        # RIPA_df[RIPA_df['Student ID'].isin(HonorRoll_StudentIDs)],
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
    # RIPA_df = RIPA_df[RIPA_df['Median Days Absent']>0]
    # RIPA_df = RIPA_df[RIPA_df['Student ID']==100620332]

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
    for (student_name, StudentID), attd_df in RIPA_df.groupby(
        ["Student Name", "Student ID"]
    ):
        attd_df = attd_df.sort_values(by=["PD"], ascending=False)

        total_days_absent = attd_df.iloc[-1, 10]

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
            f"{first_name} has missed {total_days_absent} days this school year. The narrow black bar represents {first_name}'s attendance and the wide grey bar represents the number of days absent by the average HSFI student.",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        chart_flowable = return_student_bar_graph.return_daily_only(attd_df)
        flowables.append(chart_flowable)

        paragraph = Paragraph(
            f"Attending on time every day to all classes will help {first_name} learn and stay on track. The chart below shows how much {first_name} has missed in their classes (narrow black bar) and how much class the average HSFI student has missed (wide grey bar)",
            styles["BodyText"],
        )
        flowables.append(paragraph)

        chart_flowable = return_student_bar_graph.return_classes_only(attd_df)
        flowables.append(chart_flowable)

        paragraph = Paragraph(
            f"You are key to helping {first_name} attend school every day possible; our classes are better when {first_name} is there.",
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
    PD = row["PD"]
    Course = row["Course"]
    if PD == -1 and Course == "DAILY":
        return "Overall<br>Daily<br>Attd"
    Dept = row["Dept"]
    Teacher = row["Teacher Name"].title()
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
    if course_code[0] == "H":
        return "Social Studies"
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


if __name__ == "__main__":
    data = {}
    main(data)

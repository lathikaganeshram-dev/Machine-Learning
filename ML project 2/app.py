from flask import Flask, render_template, request, session, send_file, redirect
import pandas as pd
import joblib
import io
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# ==========================
# Flask App
# ==========================

app = Flask(__name__)
app.secret_key = "placement_predictor_secret_key"

# ==========================
# Load Machine Learning Model
# ==========================

model = joblib.load("placement_model.pkl")
import sqlite3

def create_database():

    conn = sqlite3.connect("placement.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        prediction TEXT,
        probability REAL,
        readiness INTEGER,
        salary TEXT,
        performance TEXT,
        confidence TEXT

    )
    """)

    conn.commit()
    conn.close()

create_database()


@app.route("/", methods=["GET", "POST"])
def home():

    # Default Values

    prediction = None
    probability = 0
    readiness = 0
    salary = "-"
    performance = "-"
    confidence = "-"
    suggestions = []

    # Chart Values

    cgpa = 0
    coding = 0
    dsa = 0
    aptitude = 0
    communication = 0

    if request.method == "POST":

        # Student Details
        
        student_name = request.form["student_name"]

        cgpa = float(request.form["cgpa"])
        if cgpa < 0 or cgpa > 10:
            return "CGPA must be between 0 and 10"
        branch = int(request.form["branch"])
        backlogs = int(request.form["backlogs"])
        if backlogs < 0:
            return "Backlogs cannot be negative"
        coding = float(request.form["coding_skills"])
        if coding < 0 or coding > 100:
            return "Coding Skills must be between 0 and 100"
        dsa = float(request.form["dsa_score"])
        if dsa < 0 or dsa > 100:
            return "DSA Score must be between 0 and 100"
        aptitude = float(request.form["aptitude_score"])
        if aptitude < 0 or aptitude > 100:
            return "Aptitude Score must be between 0 and 100"
        communication = float(request.form["communication_skills"])
        if communication < 0 or communication > 100:
            return "Communication Skills must be between 0 and 100"
        internships = int(request.form["internships"])
        if internships < 0:
            return "Internships cannot be negative"
        projects = int(request.form["projects_count"])
        if projects < 0:
            return "Projects cannot be negative"
        certifications = int(request.form["certifications"])
        if certifications < 0:
            return "Certifications cannot be negative"
                # ==========================
        # Create Input DataFrame
        # ==========================

        input_data = pd.DataFrame([{

            "cgpa": cgpa,
            "coding_skills": coding,
            "dsa_score": dsa,
            "aptitude_score": aptitude,
            "communication_skills": communication,
            "internships": internships,
            "projects_count": projects,
            "certifications": certifications,
            "backlogs": backlogs,
            "branch": branch

        }])

        # ==========================
        # Predict Placement
        # ==========================

        result = model.predict(input_data)
        print("Prediction:", result[0])
        print("Probability:", model.predict_proba(input_data))
        

        probability_score = model.predict_proba(input_data)

        probability = round(probability_score[0][1] * 100, 2)

        # ==========================
        # Placement Status
        # ==========================

        if result[0] == 1:
            prediction = "🟢 PLACED"
        else:
            prediction = "🔴 NOT PLACED"
                # ==========================
        # Career Readiness Score
        # ==========================

        readiness = round(
            (
                cgpa * 10 +
                coding +
                dsa +
                aptitude +
                communication +
                internships * 5 +
                projects * 5 +
                certifications * 3
            ) / 5
        )

        if readiness > 100:
            readiness = 100

        # ==========================
        # Expected Salary
        # ==========================
        if prediction == "🔴 NOT PLACED":
            salary = "Not Applicable"
            confidence="Low"
        else:


            if probability >= 90:
                salary = "₹12 - ₹18 LPA"

            elif probability >= 80:
                salary = "₹8 - ₹12 LPA"

            elif probability >= 70:
                salary = "₹6 - ₹8 LPA"

            elif probability >= 60:
                salary = "₹4 - ₹6 LPA"

            else:
                salary = "Below ₹4 LPA"

        # ==========================
        # Performance Level
        # ==========================

        if readiness >= 90:
            performance = "Excellent ⭐⭐⭐⭐⭐"

        elif readiness >= 75:
            performance = "Very Good ⭐⭐⭐⭐"

        elif readiness >= 60:
            performance = "Good ⭐⭐⭐"

        elif readiness >= 40:
            performance = "Average ⭐⭐"

        else:
            performance = "Needs Improvement ⭐"

        # ==========================
        # Model Confidence
        # ==========================

        if probability >= 90:
            confidence = "High"

        elif probability >= 75:
            confidence = "Medium"

        else:
            confidence = "Low"

        # ==========================
        # Smart Suggestions
        # ==========================

        if coding < 70:
            suggestions.append("Improve Coding Skills")

        if dsa < 70:
            suggestions.append("Practice DSA Daily")

        if aptitude < 70:
            suggestions.append("Improve Aptitude Skills")

        if communication < 70:
            suggestions.append("Improve Communication Skills")

        if internships == 0:
            suggestions.append("Complete at least one Internship")

        if projects < 2:
            suggestions.append("Build More Real-world Projects")

        if certifications < 2:
            suggestions.append("Complete More Certifications")

        if backlogs > 0:
            suggestions.append("Clear All Backlogs")

        if len(suggestions) == 0:
            suggestions.append("Excellent Profile! Keep it up! 🎉")
            # Save Data for PDF

        session["student_name"] = student_name
        session["prediction"] = prediction
        session["probability"] = probability
        session["readiness"] = readiness
        session["salary"] = salary
        session["performance"] = performance
        session["confidence"] = confidence
        session["suggestions"] = suggestions
        # ==========================
# Save Prediction to Database
# ==========================

        conn = sqlite3.connect("placement.db")

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO prediction_history
        (student_name, prediction, probability, readiness, salary, performance, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            student_name,
            prediction,
            probability,
            readiness,
            salary,
            performance,
            confidence

        ))

        conn.commit()
        conn.close()
    return render_template(

        "index.html",

        prediction=prediction,
        probability=probability,
        readiness=readiness,
        salary=salary,
        performance=performance,
        confidence=confidence,
        suggestions=suggestions,

        # Chart Values
        cgpa=cgpa,
        coding=coding,
        dsa=dsa,
        aptitude=aptitude,
        communication=communication
    )


# ==========================
# Run Flask App
# ==========================




@app.route("/download_report")
def download_report():


    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    current_date = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    import random

    report_id = "REP-" + str(random.randint(1000,9999))

    story.append(Paragraph("<b><font size=22 color='darkblue'>SMART COLLEGE PLACEMENT PREDICTOR</font></b>", styles["Title"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<b><font size=18>Placement Prediction Report</font></b>", styles["Heading1"]))

    story.append(Paragraph(f"<b>Generated On :</b> {current_date}", styles["Normal"]))
    story.append(Paragraph(f"<b>Report ID :</b> {report_id}", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<hr width='100%'/>", styles["Normal"]))
    story.append(
        Paragraph(
            "<b><font size=16 color='green'>OVERALL RESULT : SUCCESSFULLY ANALYZED</font></b>",
            styles["Heading2"]
        )
    )

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<b><font size=15 color='darkblue'>STUDENT DETAILS</font></b>", styles["Heading2"]))

    table_data = [

        ["Student Name", session.get("student_name", "-")],

        ["Placement Status", session.get("prediction", "-")],

        ["Probability", f"{session.get('probability', '-') } %"],

        ["Career Readiness", f"{session.get('readiness', '-')}/100"],

        ["Expected Salary", session.get("salary", "-")],

        ["Performance", session.get("performance", "-")],

        ["Confidence", session.get("confidence", "-")]

    ]

    table = Table(table_data, colWidths=[180, 220])

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#1E3A8A")),

        ("TEXTCOLOR", (0,0), (0,-1), colors.white),

        ("BACKGROUND", (1,0), (1,-1), colors.whitesmoke),

        ("GRID", (0,0), (-1,-1), 1, colors.grey),

        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0,0), (-1,-1), 10),

        ("TOPPADDING", (0,0), (-1,-1), 10),

        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        ("ALIGN", (0,0), (-1,-1), "CENTER")

    ]))

    story.append(table)

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph("<b><font size=15 color='darkblue'>SUGGESTIONS</font></b>", styles["Heading2"]))
    story.append(Paragraph("<br/>", styles["Normal"]))
    for item in session.get("suggestions", []):
        story.append(Paragraph(f"• {item}", styles["Normal"]))
    story.append(Paragraph("<br/><br/>", styles["Normal"]))

    story.append(Paragraph("<hr width='100%'/>", styles["Normal"]))

    story.append(Paragraph(f"<b>Report ID :</b> {report_id}", styles["Normal"]))

    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(
        Paragraph(
            "<font size='10' color='grey'><b>Generated by Machine Learning Based Career Predictor</b></font>",
            styles["Normal"]
        )
    )
    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Placement_Report.pdf",
        mimetype="application/pdf"
    )
@app.route("/history")
def history():

    conn = sqlite3.connect("placement.db")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT student_name,
           prediction,
           probability,
           readiness,
           salary,
           performance,
           confidence
    FROM prediction_history
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return render_template("history.html", records=rows)
@app.route("/clear_history")
def clear_history():

    conn = sqlite3.connect("placement.db")

    cursor = conn.cursor()

    cursor.execute("DELETE FROM prediction_history")

    conn.commit()

    conn.close()

    return redirect("/history")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
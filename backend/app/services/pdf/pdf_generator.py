# backend/app/services/pdf/pdf_generator.py
"""
PDF Document Generator Engine for ClinicalPrep AI v2.0.

Purpose:
    Compiles structured session state memory and summary briefs into 
    clean, professional, 1-page PDF documents for physician review using fpdf2.
"""

from io import BytesIO
from datetime import date
from fpdf import FPDF


class ClinicalBriefPDF(FPDF):
    """Custom PDF Layout Builder for Clinical Record Summaries."""

    def header(self):
        # Header Banner
        self.set_fill_color(120, 53, 15)  # Amber-900 / Dark Brown
        self.rect(0, 0, 210, 18, 'F')
        
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 4)
        self.cell(0, 10, "ClinicalPrep AI - Patient Pre-Visit Record", align="L")
        
        self.set_font("Helvetica", "", 9)
        self.set_xy(-60, 4)
        self.cell(50, 10, f"Date: {date.today().strftime('%B %d, %Y')}", align="R")
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0, 10, 
            "Disclaimer: Administrative pre-visit summary. Not a diagnostic tool. Confidential Medical Record.", 
            align="C"
        )


def generate_clinical_record_pdf(session_state_dict: dict) -> bytes:
    """
    Generates binary PDF byte data from the structured session state object.

    Args:
        session_state_dict (dict): IntakeSessionState model serialized to dictionary.

    Returns:
        bytes: Binary PDF file bytes suitable for HTTP streaming download.
    """
    demo = session_state_dict.get("demographics", {})
    clin = session_state_dict.get("clinical_slots", {})

    pdf = ClinicalBriefPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 20, 15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(120, 53, 15)
    pdf.cell(0, 10, "Patient Pre-Visit Clinical Summary", ln=True)
    pdf.set_draw_color(217, 119, 6)  # Amber divider line
    pdf.set_line_width(0.6)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Section 1: Patient Demographics
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 7, "1. Patient Information", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    
    col1 = f"Name: {demo.get('name') or 'Not reported'}\nAge: {demo.get('age') or 'Not reported'}\nGender: {demo.get('gender') or 'Not reported'}"
    col2 = f"Height: {demo.get('height') or 'Not reported'}\nWeight: {demo.get('weight') or 'Not reported'}\nContact: {demo.get('contact') or 'Not reported'}"
    
    pdf.multi_cell(85, 5, col1, border=0)
    pdf.set_xy(105, pdf.get_y() - 15)
    pdf.multi_cell(85, 5, col2, border=0)
    pdf.ln(6)

    # Section 2: Chief Complaint & HPI
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 7, "2. Chief Complaint & History of Present Illness", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 6, f"- Primary Concern: {clin.get('chief_complaint') or 'Not reported'}", ln=True)
    pdf.cell(0, 6, f"- Onset & Duration: {clin.get('onset_duration') or 'Not reported'}", ln=True)
    pdf.cell(0, 6, f"- Severity Rating: {clin.get('severity') or 'Not reported'}", ln=True)
    pdf.cell(0, 6, f"- Pattern / Triggers: {clin.get('pattern_triggers') or 'Not reported'}", ln=True)
    pdf.ln(4)

    # Section 3: Current Interventions & History
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 7, "3. Current Interventions & Medications", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 6, f"- Medications / Supplements: {clin.get('current_medications') or 'None reported'}", ln=True)
    pdf.ln(4)

    # Section 4: Physician Discussion Points / Goals
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 7, "4. Top Questions / Goals for Physician", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    goals = clin.get("patient_goals") or "None reported"
    pdf.multi_cell(0, 6, f"a. {goals}")
    pdf.ln(6)

    # Output to Bytes
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    
    return buffer.getvalue()
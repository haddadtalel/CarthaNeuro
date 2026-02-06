"""
PDF Report Generation Service
Generates medical reports in PDF format
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

from config import settings


class PDFService:
    """Service for generating medical PDF reports"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

"""
PDF Report Generation Service
Generates medical reports in PDF format
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from config import settings


class PDFService:
    """Service for generating medical PDF reports"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles with clean design"""
        # Professional color palette
        self.primary_color = colors.HexColor('#2563eb')  # Modern blue
        self.secondary_color = colors.HexColor('#059669')  # Medical green
        self.accent_color = colors.HexColor('#dc2626')  # Alert red
        self.warning_color = colors.HexColor('#f59e0b')  # Warning orange
        self.neutral_color = colors.HexColor('#6b7280')  # Neutral gray
        self.light_bg = colors.HexColor('#f8fafc')  # Light background
        self.card_bg = colors.white  # Card background

        # Enhanced header style
        self.styles.add(ParagraphStyle(
            name='MedicalHeader',
            parent=self.styles['Heading1'],
            fontSize=22,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=self.primary_color,
            fontName='Helvetica-Bold'
        ))

        # Clean section headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=self.secondary_color,
            fontName='Helvetica-Bold'
        ))

        # Clean body text
        self.styles.add(ParagraphStyle(
            name='NormalMedical',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leading=16,
            fontName='Helvetica',
            textColor=colors.HexColor('#374151')
        ))

        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.neutral_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))

        # Highlight style for important information
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            leading=16,
            fontName='Helvetica-Bold',
            textColor=self.primary_color
        ))

        # Success style
        self.styles.add(ParagraphStyle(
            name='Success',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=self.secondary_color
        ))

        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=self.warning_color
        ))

        # Alert style
        self.styles.add(ParagraphStyle(
            name='Alert',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=self.accent_color
        ))

    def generate_medical_report(
        self,
        consultation_data: Optional[Dict[str, Any]],
        prediction_data: Dict[str, Any],
        doctor_info: Dict[str, Any],
        mri_image_path: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive medical report PDF

        Args:
            consultation_data: Consultation details
            prediction_data: Prediction results
            doctor_info: Doctor information
            mri_image_path: Path to MRI image file

        Returns:
            Path to generated PDF file
        """

        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        patient_name = (consultation_data.get('patient_full_name') if consultation_data else prediction_data.get('patient_full_name', 'Unknown')).replace(' ', '_')
        filename = f"medical_report_{patient_name}_{timestamp}.pdf"
        pdf_path = os.path.join(settings.UPLOAD_DIR, 'reports', filename)

        # Ensure reports directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []

        # Header
        story.extend(self._create_header())

        # Patient and Doctor Information
        story.extend(self._create_patient_doctor_info(consultation_data, prediction_data, doctor_info))

        # Consultation Details (only if consultation data exists)
        if consultation_data:
            story.extend(self._create_consultation_details(consultation_data))

        # Prediction Results
        story.extend(self._create_prediction_results(prediction_data))

        # Clinical Summary
        story.extend(self._create_summary(prediction_data, consultation_data))

        # MRI Image (if available)
        if mri_image_path and os.path.exists(mri_image_path):
            story.extend(self._create_mri_section(mri_image_path))

        # Recommendations
        story.extend(self._create_recommendations(prediction_data))

        # Footer
        story.extend(self._create_footer())

        # Build PDF
        doc.build(story, onFirstPage=self._add_page_decorations, onLaterPages=self._add_page_decorations)

        return pdf_path

    def _create_header(self):
        """Create clean report header"""
        elements = []

        # Simple title
        elements.append(Paragraph("Cartha Neuro Medical Report", self.styles['MedicalHeader']))
        elements.append(Spacer(1, 10))

        # Subtitle
        elements.append(Paragraph("Comprehensive Alzheimer's Disease Analysis", self.styles['Highlight']))
        elements.append(Spacer(1, 15))

        # Report generation info
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['NormalMedical']
        ))
        elements.append(Spacer(1, 30))

        return elements

    def _create_patient_doctor_info(self, consultation_data: Optional[Dict], prediction_data: Dict, doctor_info: Dict):
        """Create patient and doctor information section"""
        elements = []

        elements.append(Paragraph("Patient & Physician Information", self.styles['SectionHeader']))

        # Get patient data from consultation or prediction - prioritize consultation data
        patient_name = consultation_data.get('patient_full_name', '') if consultation_data else prediction_data.get('patient_full_name', '')
        patient_id = consultation_data.get('patient_id', prediction_data.get('patient_id', 'N/A')) if consultation_data else prediction_data.get('patient_id', 'N/A')
        gender = consultation_data.get('gender', 'N/A').capitalize() if consultation_data else 'N/A'
        age = str(consultation_data.get('age', 'N/A')) if consultation_data else 'N/A'

        # Handle date formatting for both datetime objects and ISO strings
        if consultation_data:
            created_at = consultation_data.get('created_at', datetime.now().isoformat())
            if isinstance(created_at, str):
                consultation_date = datetime.fromisoformat(created_at).strftime('%B %d, %Y')
            else:
                consultation_date = created_at.strftime('%B %d, %Y')
        else:
            created_at = prediction_data.get('created_at', datetime.now())
            if isinstance(created_at, str):
                consultation_date = datetime.fromisoformat(created_at).strftime('%B %d, %Y')
            else:
                consultation_date = created_at.strftime('%B %d, %Y')

        # Simple patient information table
        patient_data = [
            ["Patient Name:", patient_name or 'N/A'],
            ["Patient ID:", patient_id],
            ["Age:", age],
            ["Gender:", gender],
        ]

        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_color),
        ]))

        elements.append(patient_table)
        elements.append(Spacer(1, 15))

        # Physician information
        physician_data = [
            ["Doctor :", doctor_info.get('full_name', 'N/A')],
            ["Analysis Date:", consultation_date],
        ]

        physician_table = Table(physician_data, colWidths=[2*inch, 4*inch])
        physician_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.secondary_color),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))

        elements.append(physician_table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_consultation_details(self, consultation_data: Dict):
        """Create consultation details section"""
        elements = []

        elements.append(Paragraph("Consultation Details", self.styles['SectionHeader']))

        # Medical History
        elements.append(Paragraph("Medical History:", self.styles['NormalMedical']))

        history_items = []
        history_items.append(f"{'Yes' if consultation_data.get('family_history_ad') else 'No'} - Family history of Alzheimer's Disease")
        history_items.append(f"{'Yes' if consultation_data.get('diabetes') else 'No'} - Diabetes")
        history_items.append(f"{'Yes' if consultation_data.get('hypertension') else 'No'} - Hypertension")
        history_items.append(f"{'Yes' if consultation_data.get('heart_disease') else 'No'} - Heart Disease")
        history_items.append(f"{'Yes' if consultation_data.get('stroke_history') else 'No'} - Stroke History")
        history_items.append(f"{'Yes' if consultation_data.get('smoking') else 'No'} - Smoking")
        history_items.append(f"{'Yes' if consultation_data.get('alcohol_use') else 'No'} - Alcohol Use")

        elements.append(Paragraph("<br/>".join(f"• {item}" for item in history_items), self.styles['NormalMedical']))
        elements.append(Spacer(1, 10))

        # Cognitive Symptoms
        elements.append(Paragraph("Cognitive Symptoms Assessment:", self.styles['NormalMedical']))

        symptoms = [
            ("Memory Complaints", consultation_data.get('memory_complaints', 0)),
            ("Difficulty Concentrating", consultation_data.get('difficulty_concentrating', 0)),
            ("Problem Solving Difficulty", consultation_data.get('problem_solving_difficulty', 0)),
            ("Mood Changes", consultation_data.get('mood_changes', 0)),
            ("Confusion", consultation_data.get('confusion', 0)),
            ("Personality Changes", consultation_data.get('personality_changes', 0)),
            ("Disorientation", consultation_data.get('disorientation', 0)),
            ("Difficulty with Daily Tasks", consultation_data.get('difficulty_with_daily_tasks', 0)),
        ]

        symptom_data = [["Symptom", "Severity"]]
        severity_labels = {0: "None", 1: "Mild", 2: "Moderate", 3: "Severe"}

        for symptom, severity in symptoms:
            symptom_data.append([symptom, severity_labels.get(severity, "Unknown")])

        symptom_table = Table(symptom_data, colWidths=[3*inch, 1*inch])
        symptom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))

        elements.append(symptom_table)
        elements.append(Spacer(1, 10))

        # Additional Information
        additional_info = []
        if consultation_data.get('symptoms_duration_months'):
            additional_info.append(f"Symptoms Duration: {consultation_data['symptoms_duration_months']} months")
        if consultation_data.get('previous_ad_evaluation'):
            additional_info.append("Previous Alzheimer's Disease Evaluation: Yes")
        if consultation_data.get('current_medications'):
            additional_info.append(f"Current Medications: {consultation_data['current_medications']}")
        if consultation_data.get('notes'):
            additional_info.append(f"Additional Notes: {consultation_data['notes']}")

        if additional_info:
            elements.append(Paragraph("<br/>".join(additional_info), self.styles['NormalMedical']))

        elements.append(Spacer(1, 20))

        return elements

    def _create_prediction_results(self, prediction_data: Dict):
        """Create prediction results section"""
        elements = []

        elements.append(Paragraph("AI Analysis Results", self.styles['SectionHeader']))

        # Main prediction
        disease_class = prediction_data.get('predicted_class', 'Unknown')
        probability = prediction_data.get('combined_probability', 0)
        confidence = prediction_data.get('confidence', 'Unknown')

        # Diagnosis result
        diagnosis_data = [["Primary Diagnosis:", f"{disease_class}"]]
        diagnosis_table = Table(diagnosis_data, colWidths=[2.5*inch, 4*inch])
        diagnosis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.secondary_color),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('BACKGROUND', (1, 0), (1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(diagnosis_table)
        elements.append(Spacer(1, 10))

        # Key metrics
        prob_percentage = probability * 100 if isinstance(probability, (int, float)) else 0
        metrics_data = [
            ["Probability:", f"{prob_percentage:.1f}%", "Confidence Level:", f"{confidence}"]
        ]
        metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_mri_section(self, mri_image_path: str):
        """Create enhanced MRI image section"""
        elements = []

        elements.append(Paragraph("🧠 MRI Image Analysis", self.styles['SectionHeader']))

        try:
            # Add image with enhanced styling
            img = Image(mri_image_path)
            img.drawHeight = 3*inch
            img.drawWidth = 4*inch

            # Create a bordered container for the image
            image_data = [[img]]
            image_table = Table(image_data, colWidths=[4*inch])
            image_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.card_bg),
                ('GRID', (0, 0), (-1, -1), 2, self.primary_color),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(image_table)

            elements.append(Spacer(1, 10))
            elements.append(Paragraph("🔬 MRI scan analyzed for Alzheimer's disease markers using advanced AI algorithms", self.styles['NormalMedical']))
        except Exception as e:
            # Enhanced error message
            error_data = [["❌ Unable to include MRI image in report"]]
            error_table = Table(error_data, colWidths=[6*inch])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.accent_color),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, self.accent_color),
            ]))
            elements.append(error_table)
            elements.append(Paragraph(f"Error details: {str(e)}", self.styles['NormalMedical']))

        elements.append(Spacer(1, 20))

        return elements

    def _create_recommendations(self, prediction_data: Dict):
        """Create enhanced recommendations section"""
        elements = []

        elements.append(Paragraph("💡 Clinical Recommendations", self.styles['SectionHeader']))

        recommendations = prediction_data.get('recommendations', 'No specific recommendations available')

        # Enhanced recommendations formatting
        rec_lines = recommendations.split('\n')
        formatted_recs = []

        for line in rec_lines:
            line = line.strip()
            if line.startswith('•'):
                formatted_recs.append(f"✅ {line[1:].strip()}")
            elif line:
                formatted_recs.append(f"✅ {line}")

        if formatted_recs:
            rec_table_data = [[rec] for rec in formatted_recs]
            rec_table = Table(rec_table_data, colWidths=[6*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.card_bg),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            elements.append(rec_table)

        elements.append(Spacer(1, 15))

        # Enhanced follow-up recommendations
        elements.append(Paragraph("<b>📅 Follow-up Recommendations:</b>", self.styles['NormalMedical']))
        follow_up = [
            "• Schedule a follow-up consultation in 3-6 months",
            "• Consider additional cognitive assessments if symptoms persist",
            "• Monitor for changes in daily functioning",
            "• Maintain regular communication with healthcare provider",
            "• Keep a journal of symptoms and cognitive changes"
        ]

        follow_up_table_data = [[item] for item in follow_up]
        follow_up_table = Table(follow_up_table_data, colWidths=[6*inch])
        follow_up_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(follow_up_table)

        elements.append(Spacer(1, 20))

        return elements

    def _create_summary(self, prediction_data: Dict, consultation_data: Optional[Dict] = None):
        """Create clinical summary section"""
        elements = []

        elements.append(Paragraph("Clinical Summary", self.styles['SectionHeader']))

        disease_class = prediction_data.get('predicted_class', 'Unknown')
        probability = prediction_data.get('combined_probability', 0)

        if "No Alzheimer's" in disease_class:
            summary_text = (
                "The AI analysis indicates no significant markers for Alzheimer's Disease based on the "
                "provided MRI image and clinical data. The patient demonstrates normal cognitive function "
                "for their age group. However, maintaining a healthy lifestyle and regular monitoring is recommended."
            )
        elif "Mild Cognitive Impairment" in disease_class:
            summary_text = (
                "The AI analysis suggests mild cognitive impairment. This stage represents a transitional "
                "phase between normal age-related cognitive decline and more serious conditions. Early intervention "
                "and lifestyle modifications may help slow progression."
            )
        elif "Alzheimer's" in disease_class:
            summary_text = (
                f"The AI analysis indicates signs of {disease_class}. The probability score of {probability * 100:.1f}% "
                "suggests a high likelihood of the condition. A comprehensive clinical evaluation is strongly recommended "
                "to confirm the diagnosis and develop an appropriate care plan."
            )
        else:
            summary_text = "Unable to generate a clinical summary. Please consult with a healthcare professional."

        # Create summary paragraph
        summary_data = [[f"Summary:{summary_text}"]]
        summary_table = Table(summary_data, colWidths=[6.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.card_bg),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 2, self.primary_color),
        ]))

        #elements.append(summary_table)
        #elements.append(Spacer(1, 20))

        return elements

    def _create_footer(self):
        """Create report footer"""
        elements = []

        footer_text = (
            "This report was generated by Cartha Neuro AI System. "
            "For questions or concerns, please contact your healthcare provider. "
            f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        elements.append(Paragraph(footer_text, self.styles['Footer']))
        elements.append(Spacer(1, 10))

        return elements

    def _add_page_decorations(self, canvas, doc):
        """Add enhanced page decorations like headers/footers"""
        canvas.saveState()

        # Add subtle gradient border
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(1)
        canvas.rect(0.3*inch, 0.3*inch, 7.4*inch, 10.4*inch)

        # Add inner border
        canvas.setStrokeColor(colors.HexColor('#e5e7eb'))
        canvas.setLineWidth(0.5)
        canvas.rect(0.5*inch, 0.5*inch, 7*inch, 10*inch)

        # Add page number with styling
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(self.primary_color)
        page_num = canvas.getPageNumber()
        canvas.drawRightString(7.5*inch, 0.4*inch, f"Page {page_num}")

        # Add subtle watermark
        canvas.setFont('Helvetica', 50)
        canvas.setFillColor(colors.HexColor('#f3f4f6'))
        canvas.saveState()
        canvas.translate(4*inch, 5*inch)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "Cartha Neuro")
        canvas.restoreState()

        canvas.restoreState()


# Create singleton instance
pdf_service = PDFService()


async def generate_report(
    prediction_id: str,
    patient_id: str,
    predicted_class: str,
    confidence: float,
    probabilities: Dict[str, float],
    doctor_name: str,
    doctor_username: str,
    created_at: datetime,
    consultation_data: Optional[Dict[str, Any]] = None,
    mri_image_path: Optional[str] = None
) -> bytes:
    """
    Generate a PDF report for a prediction
     
    Args:
        prediction_id: Prediction ID
        patient_id: Patient ID
        predicted_class: Predicted disease class
        confidence: Confidence level
        probabilities: Dictionary of class probabilities
        doctor_name: Doctor's full name
        doctor_username: Doctor's username
        created_at: Creation timestamp
        consultation_data: Optional consultation data for comprehensive report
        mri_image_path: Optional path to MRI image for inclusion in report
         
    Returns:
        PDF file content as bytes
    """
    # Create prediction data dict
    # Convert confidence to float for comparison
    conf = confidence
    if isinstance(confidence, str):
        conf_map = {"Very High": 0.9, "High": 0.75, "Moderate": 0.5, "Low": 0.25, "Very Low": 0.1}
        conf = conf_map.get(confidence, 0.5)
    
    prediction_data = {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probability": conf,
        "combined_probability": conf,
        "probabilities": probabilities,
        "factors": {
            "contribution_image": 0.6,
            "contribution_consultation": 0.4
        },
        "patient_id": patient_id,
        "patient_full_name": consultation_data.get("patient_full_name", "") if consultation_data else "",
        "created_at": created_at,
        "recommendations": get_recommendations_for_class(predicted_class, conf)
    }
    
    # Create doctor info dict
    doctor_info = {
        "full_name": doctor_name,
        "username": doctor_username
    }
    
    # Generate report
    service = PDFService()
    
    # Ensure reports directory exists
    reports_dir = os.path.join(settings.UPLOAD_DIR, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"medical_report_{prediction_id}_{timestamp}.pdf"
    pdf_path = os.path.join(reports_dir, filename)
    
    # Generate the medical report with enhanced data
    generated_pdf_path = service.generate_medical_report(
        consultation_data=consultation_data,
        prediction_data=prediction_data,
        doctor_info=doctor_info,
        mri_image_path=mri_image_path
    )
    
    # Read and return PDF content from the generated path
    with open(generated_pdf_path, 'rb') as f:
        return f.read()


def get_recommendations_for_class(disease_class: str, probability: float) -> str:
    """Get recommendations based on disease class"""
    recommendations = []
    
    # Convert probability to float if it's a string (e.g., "High", "Moderate")
    if isinstance(probability, str):
        prob_map = {"Very High": 0.9, "High": 0.75, "Moderate": 0.5, "Low": 0.25, "Very Low": 0.1}
        probability = prob_map.get(probability, 0.5)
    
    if disease_class == "No Alzheimer's Disease":
        recommendations = [
            "Continue regular health check-ups",
            "Maintain a healthy lifestyle with regular exercise",
            "Stay mentally active with puzzles and social engagement",
            "Follow a brain-healthy diet (Mediterranean or MIND diet)"
        ]
    elif disease_class == "Mild Cognitive Impairment":
        recommendations = [
            "Schedule follow-up cognitive assessment in 6 months",
            "Consider cognitive training programs",
            "Review and manage cardiovascular risk factors",
            "Maintain social and mental engagement"
        ]
    elif "Alzheimer's" in disease_class:
        recommendations = [
            "Consult with a neurologist or geriatric psychiatrist",
            "Consider comprehensive neuropsychological evaluation",
            "Discuss treatment options with healthcare provider",
            "Plan for care support and long-term management",
            "Inform family members and create support network"
        ]
    
    if isinstance(probability, (int, float)) and probability < 0.6:
        recommendations.insert(0, "Note: Confidence level is moderate. Consider additional testing.")
    
    return "\n".join([f"• {rec}" for rec in recommendations])

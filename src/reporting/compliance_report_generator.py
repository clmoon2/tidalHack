"""
Compliance report generator for regulatory reporting.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage


class ComplianceReportGenerator:
    """
    Generate regulatory compliance reports.
    
    Supports:
    - Executive summaries
    - Immediate action tables
    - Risk distribution charts
    - Growth rate analysis
    - PDF reports
    - CSV exports
    """
    
    # Regulatory color scheme
    COLORS = {
        'CRITICAL': '#DC143C',      # Crimson Red
        'HIGH': '#FF8C00',          # Dark Orange
        'MODERATE': '#FFD700',      # Gold
        'LOW': '#4169E1',           # Royal Blue
        'ACCEPTABLE': '#32CD32'     # Lime Green
    }
    
    def __init__(self):
        """Initialize report generator."""
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def generate_executive_summary(
        self,
        assessments: List[Dict]
    ) -> Dict:
        """
        Generate executive summary with counts by risk level.
        
        Args:
            assessments: List of risk assessments
        
        Returns:
            Dictionary with summary statistics
        """
        df = pd.DataFrame(assessments)
        
        # Count by risk level
        risk_counts = df['risk_level'].value_counts().to_dict()
        
        # Count by CFR classification
        cfr_counts = df['cfr_classification'].value_counts().to_dict()
        
        # Count by ASME growth classification
        asme_counts = df['asme_growth_classification'].value_counts().to_dict()
        
        # Statistics
        summary = {
            'total_anomalies': len(df),
            'risk_level_counts': risk_counts,
            'cfr_classification_counts': cfr_counts,
            'asme_growth_counts': asme_counts,
            'immediate_action_count': cfr_counts.get('IMMEDIATE_ACTION', 0),
            'critical_high_count': (
                risk_counts.get('CRITICAL', 0) + risk_counts.get('HIGH', 0)
            ),
            'mean_risk_score': df['total_risk_score'].mean(),
            'max_risk_score': df['total_risk_score'].max(),
            'mean_depth': df['depth_pct'].mean(),
            'mean_growth_rate': df['growth_rate'].mean()
        }
        
        return summary
    
    def generate_immediate_action_table(
        self,
        assessments: List[Dict]
    ) -> pd.DataFrame:
        """
        Generate table of immediate action items.
        
        Args:
            assessments: List of risk assessments
        
        Returns:
            DataFrame sorted by risk score
        """
        df = pd.DataFrame(assessments)
        
        # Filter immediate action items
        immediate = df[df['cfr_classification'] == 'IMMEDIATE_ACTION'].copy()
        
        # Sort by risk score
        immediate = immediate.sort_values('total_risk_score', ascending=False)
        
        # Select relevant columns
        columns = [
            'anomaly_id',
            'depth_pct',
            'growth_rate',
            'total_risk_score',
            'risk_level',
            'is_hca'
        ]
        
        return immediate[columns]
    
    def generate_risk_distribution_chart(
        self,
        assessments: List[Dict],
        output_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate risk distribution chart with regulatory colors.
        
        Args:
            assessments: List of risk assessments
            output_path: Optional path to save chart
        
        Returns:
            Plotly figure
        """
        df = pd.DataFrame(assessments)
        
        # Count by risk level
        risk_counts = df['risk_level'].value_counts()
        
        # Order by severity
        order = ['CRITICAL', 'HIGH', 'MODERATE', 'LOW', 'ACCEPTABLE']
        risk_counts = risk_counts.reindex(order, fill_value=0)
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=risk_counts.index,
                y=risk_counts.values,
                marker_color=[self.COLORS.get(level, '#808080') for level in risk_counts.index],
                text=risk_counts.values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Risk Level Distribution',
            xaxis_title='Risk Level',
            yaxis_title='Number of Anomalies',
            template='plotly_white',
            height=400
        )
        
        if output_path:
            fig.write_html(output_path)
        
        return fig
    
    def generate_growth_rate_analysis(
        self,
        assessments: List[Dict],
        output_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate growth rate analysis with ASME B31.8S thresholds.
        
        Args:
            assessments: List of risk assessments
            output_path: Optional path to save chart
        
        Returns:
            Plotly figure
        """
        df = pd.DataFrame(assessments)
        
        # Create histogram
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df['growth_rate'],
            nbinsx=30,
            name='Growth Rate Distribution',
            marker_color='lightblue'
        ))
        
        # Add ASME B31.8S threshold lines
        thresholds = [
            (0.5, 'ACCEPTABLE', 'green'),
            (2.0, 'LOW RISK', 'yellow'),
            (5.0, 'MODERATE RISK', 'orange'),
        ]
        
        for threshold, label, color in thresholds:
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color=color,
                annotation_text=f"{label} ({threshold} pp/yr)",
                annotation_position="top"
            )
        
        fig.update_layout(
            title='Growth Rate Distribution (ASME B31.8S Thresholds)',
            xaxis_title='Growth Rate (percentage points/year)',
            yaxis_title='Number of Anomalies',
            template='plotly_white',
            height=400,
            showlegend=True
        )
        
        if output_path:
            fig.write_html(output_path)
        
        return fig
    
    def add_regulatory_disclaimers(self) -> List[str]:
        """
        Get regulatory disclaimers for reports.
        
        Returns:
            List of disclaimer paragraphs
        """
        return [
            "REGULATORY DISCLAIMER:",
            "",
            "This report is prepared in accordance with:",
            "• 49 CFR Parts 192 & 195 (Federal Pipeline Safety Regulations)",
            "• ASME B31.8S (Managing System Integrity of Gas Pipelines)",
            "",
            "This report is for informational purposes only and does not constitute "
            "engineering advice or regulatory compliance certification. All decisions "
            "regarding pipeline integrity management should be made by qualified "
            "personnel in accordance with applicable regulations and industry standards.",
            "",
            "Operators are responsible for ensuring compliance with all applicable "
            "federal, state, and local regulations."
        ]
    
    def add_regulatory_references(self) -> List[str]:
        """
        Get regulatory references for reports.
        
        Returns:
            List of reference citations
        """
        return [
            "REGULATORY REFERENCES:",
            "",
            "1. 49 CFR Part 192 - Transportation of Natural and Other Gas by Pipeline: "
            "Minimum Federal Safety Standards",
            "",
            "2. 49 CFR Part 195 - Transportation of Hazardous Liquids by Pipeline",
            "",
            "3. ASME B31.8S-2020 - Managing System Integrity of Gas Pipelines",
            "",
            "4. API 1160 - Managing System Integrity for Hazardous Liquid Pipelines",
            "",
            "5. NACE SP0502 - Pipeline External Corrosion Direct Assessment Methodology"
        ]
    
    def generate_pdf_report(
        self,
        assessments: List[Dict],
        intervals: List[Dict],
        output_path: str,
        pipeline_name: str = "Pipeline",
        report_date: Optional[datetime] = None
    ):
        """
        Generate comprehensive PDF compliance report.
        
        Args:
            assessments: List of risk assessments
            intervals: List of inspection intervals
            output_path: Path to save PDF
            pipeline_name: Name of pipeline
            report_date: Report date (defaults to now)
        """
        if report_date is None:
            report_date = datetime.now()
        
        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title page
        title = Paragraph(
            f"Pipeline Integrity Compliance Report<br/>{pipeline_name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 12))
        
        date_text = Paragraph(
            f"Report Date: {report_date.strftime('%B %d, %Y')}",
            self.styles['Normal']
        )
        story.append(date_text)
        story.append(Spacer(1, 24))
        
        # Executive Summary
        summary = self.generate_executive_summary(assessments)
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Anomalies', str(summary['total_anomalies'])],
            ['Immediate Action Required', str(summary['immediate_action_count'])],
            ['Critical + High Risk', str(summary['critical_high_count'])],
            ['Mean Risk Score', f"{summary['mean_risk_score']:.1f}"],
            ['Mean Depth', f"{summary['mean_depth']:.1f}%"],
            ['Mean Growth Rate', f"{summary['mean_growth_rate']:.2f} pp/yr"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 24))
        
        # Immediate Action Items
        story.append(Paragraph("Immediate Action Items (49 CFR 192.933)", self.styles['SectionHeader']))
        
        immediate_df = self.generate_immediate_action_table(assessments)
        
        if len(immediate_df) > 0:
            immediate_data = [immediate_df.columns.tolist()] + immediate_df.values.tolist()
            immediate_table = Table(immediate_data, colWidths=[1.2*inch]*6)
            immediate_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(immediate_table)
        else:
            story.append(Paragraph("No immediate action items identified.", self.styles['Normal']))
        
        story.append(PageBreak())
        
        # Regulatory Disclaimers
        story.append(Paragraph("Regulatory Information", self.styles['SectionHeader']))
        
        for line in self.add_regulatory_disclaimers():
            story.append(Paragraph(line, self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 12))
        
        for line in self.add_regulatory_references():
            story.append(Paragraph(line, self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
    
    def export_csv(
        self,
        assessments: List[Dict],
        intervals: List[Dict],
        output_path: str
    ):
        """
        Export compliance data to CSV with regulatory fields.
        
        Args:
            assessments: List of risk assessments
            intervals: List of inspection intervals
            output_path: Path to save CSV
        """
        # Merge assessments and intervals
        df_assess = pd.DataFrame(assessments)
        df_intervals = pd.DataFrame(intervals)
        
        # Merge on anomaly_id
        df = df_assess.merge(
            df_intervals[['anomaly_id', 'interval_years', 'basis', 'note']],
            on='anomaly_id',
            how='left'
        )
        
        # Add header comment with regulatory references
        with open(output_path, 'w') as f:
            f.write("# Pipeline Integrity Compliance Export\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Regulatory Standards: 49 CFR Parts 192 & 195, ASME B31.8S\n")
            f.write("#\n")
            
            # Write DataFrame
            df.to_csv(f, index=False)

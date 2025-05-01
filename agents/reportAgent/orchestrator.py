import json
import datetime
from typing import List, Dict, Any
import os
import logging
from agents.reportAgent import executivesummaryAgent, riskindicatorAgent
import pandas as pd
from plotnine import *
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the draw function for visualization
from visuals import timeSeries

class Orchestrator:
    """
    Class to directly generate political risk reports from agent outputs
    without needing to parse HTML.
    """
    def __init__(self, api_key, subcategories, user_data, subcategories_scores, visuals_df, column_visual, title="Political Risk Assessment", subtitle="Risk Factors Analysis"):
        """Initialize the report with basic metadata"""
        self.title = title
        self.subtitle = subtitle
        self.generation_date = datetime.datetime.now().strftime("%B %d, %Y")
        self.assessment_period = "12-Month Forecast"
        self.executive_summary = ""
        self.methodology = {
            "description": "",
            "data_sources": "",
            "disclaimer": ""
        }
        self.trend_chart_caption = "Political Risk Index Trends - 12-Month Rolling Assessment"
        self.api_key = api_key
        self.subcategories = subcategories
        self.user_data = user_data
        self.subcategories_scores = subcategories_scores
        self.visuals_df = visuals_df
        self.column_visual = column_visual
        self.risk_analysis_agent = riskindicatorAgent.agent(api_key=api_key, subcategories=subcategories, user_data=user_data, subcategories_scores=subcategories_scores)
        self.summary_agent = executivesummaryAgent.agent(api_key=api_key, user_data=user_data)

    def set_metadata(self, assessment_period: str):
        """Set the report metadata"""
        self.assessment_period = assessment_period
    
    def set_methodology(self, description: str, data_sources: str, disclaimer: str):
        """Set the methodology section content"""
        self.methodology = {
            "description": description,
            "data_sources": data_sources,
            "disclaimer": disclaimer
        }
    
    def create_report(self, output_html_path: str = "political_risk_report.html", output_json_path: str = "political_risk_data.json"):
        """
        Create a complete report using the initialized agents
        
        Args:
            output_html_path: Path to save the HTML report
            output_json_path: Path to save the JSON data
        
        Returns:
            str: The generated HTML report content
        """
        try:
            # Generate risk factors
            logger.info("Generating risk analysis")
            risk_factors = self.risk_analysis_agent.generate_risk_analysis()
            
            # Generate risk factors HTML
            logger.info("Generating risk factors HTML")
            risk_factors_html = self.risk_analysis_agent.generate_risk_factors()
            
            # Generate executive summary
            logger.info("Creating executive summary")
            self.summary_agent.create_executive_summary(risk_factors_html)
            self.executive_summary = self.summary_agent.executive_summary
            
            # Generate the HTML report
            logger.info("Generating complete HTML report")
            html_content = self.generate_html(risk_factors)
        
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            raise
    
    def _generate_header(self) -> str:
        """Generate the HTML for the report header"""
        return f"""
        <div class="report-header">
            <h1 class="report-title">{self.title}</h1>
            <p class="report-subtitle">{self.subtitle}</p>
            
            <div class="meta-info">
                <div class="meta-block">
                    <div class="meta-label">Report Generated</div>
                    <div class="meta-value" id="generation-date">{self.generation_date}</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_executive_summary(self) -> str:
        """Generate the HTML for the executive summary"""
        return f"""
        <div class="executive-summary">
            <h2 class="section-title">Executive Summary</h2>
            <p class="summary-content">
                {self.executive_summary}
            </p>
        </div>
        """
    
    def _generate_trend_chart(self) -> str:
        """Generate the HTML for the trend chart section"""
        chart_period = f"Q2 {datetime.datetime.now().year - 1} - Q1 {datetime.datetime.now().year}"
        
        # Check if we have visualization data available
        if self.visuals_df is not None and not self.visuals_df.empty:
            try:
                # Generate the plot using the draw function
                  # Adjust based on actual column name in your DataFrame
                plot = timeSeries.draw(
                    self.visuals_df, 
                    column=self.column_visual,
                    title='Political Risk Over Time', 
                    x_label='Date', 
                    y_label='Risk Score'
                )
                
                # Save the plot to a BytesIO object
                img_buffer = BytesIO()
                plot.save(img_buffer, format="png", dpi=100)
                img_buffer.seek(0)
                
                # Encode the image as base64 for embedding in HTML
                img_str = base64.b64encode(img_buffer.read()).decode('utf-8')
                
                # Create HTML with the embedded image
                chart_html = f"""
                <div class="chart-container" style="height: auto;">
                    <img src="data:image/png;base64,{img_str}" alt="Political Risk Trend Chart" style="width: 100%; max-width: 100%;">
                </div>
                """
            except Exception as e:
                logger.error(f"Error generating visualization: {e}")
                # Fallback to placeholder if visualization fails
                chart_html = """
                <div class="chart-container">
                    <div class="chart-placeholder">
                        [TIME-SERIES CHART ERROR: Failed to generate visualization. Check logs for details.]
                    </div>
                </div>
                """
        else:
            # If no data is available, use placeholder
            chart_html = """
            <div class="chart-container">
                <div class="chart-placeholder">
                    [TIME-SERIES CHART PLACEHOLDER: No visualization data available. Please ensure visuals_data.csv is loaded correctly.]
                </div>
            </div>
            """
        
        return f"""
        <div class="risk-trend-chart">
            <h2 class="section-title">Risk Trend Analysis</h2>
            {chart_html}
            <p class="chart-caption">Figure 1: {self.trend_chart_caption} ({chart_period})</p>
        </div>
        """
    
    def _generate_risk_factors(self, risk_factors: List[Dict[str, Any]]) -> str:
        """Generate the HTML for all risk factors"""
        risk_factors_html = ""
        
        for i, factor in enumerate(risk_factors, 1):
            indicators_html = ""
            for j, indicator in enumerate(factor["indicators"], 1):
                indicators_html += f"""
                <div class="indicator-item">
                    <div class="indicator-number">{j}.</div>
                    <div class="indicator-text">{indicator}</div>
                </div>
                """
            
            risk_factors_html += f"""
            <div class="risk-factor-card">
                <div class="risk-factor-header">
                    <div class="risk-factor-title">{factor["title"]}</div>
                    <div class="risk-badge badge-{factor["risk_level"]}">{factor["risk_level"].capitalize()} Risk</div>
                </div>
                <div class="risk-factor-content">
                    <div class="risk-description">
                        <p>{factor["description"]}</p>
                    </div>
                    
                    <div class="impact-analysis">
                        <h3>Impact Analysis</h3>
                        <div class="impact-content">
                            <p>{factor["impact_analysis"]}</p>
                        </div>
                    </div>
                    
                    <div class="indicators">
                        <h3>Key Risk Indicators</h3>
                        <div class="indicator-list">
                            {indicators_html}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return risk_factors_html
    
    def _generate_methodology(self) -> str:
        """Generate the HTML for the methodology section"""
        return f"""
        <div class="methodology">
            <h2 class="section-title">Methodology & Data Sources</h2>
            <div class="methodology-content">
                <p>{self.methodology["description"]}</p>
                <p>{self.methodology["data_sources"]}</p>
                <p>{self.methodology["disclaimer"]}</p>
            </div>
        </div>
        """
    
    def _generate_footer(self) -> str:
        """Generate the HTML for the report footer"""
        return f"""
        <div class="report-footer">
            <p>{self.title}</p>
            <p class="timestamp">Generated: {self.generation_date} | Valid for {self.assessment_period}</p>
        </div>
        """
    
    def generate_html(self, risk_factors: List[Dict[str, Any]]) -> str:
        """
        Generate the complete HTML for the report
        
        Args:
            risk_factors: List of risk factor dictionaries from the risk factor agent
            
        Returns:
            str: Complete HTML report
        """
        # Include the HTML head and style definitions
        html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Political Risk Assessment Template</title>
    <style>
        :root {
            --primary: #2c3e50;
            --secondary: #34495e;
            --accent: #465c70;
            --light: #f3f3f3;
            --dark: #333333;
            --danger: #c0392b;
            --warning: #d35400;
            --success: #27ae60;
            --neutral: #7f8c8d;
            --background: #ffffff;
            --border: #e0e0e0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: Arial, Helvetica, sans-serif;
        }
        
        body {
            background-color: var(--background);
            color: var(--dark);
            line-height: 1.5;
            padding: 40px 0;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .report-header {
            margin-bottom: 40px;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 15px;
        }
        
        .report-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .report-subtitle {
            font-size: 1.1rem;
            color: var(--secondary);
            font-weight: 400;
        }
        
        .meta-info {
            display: flex;
            justify-content: space-between;
            margin: 25px 0;
            background-color: var(--light);
            padding: 15px;
            border: 1px solid var(--border);
        }
        
        .meta-block {
            flex: 1;
            padding: 0 15px;
        }
        
        .meta-label {
            font-size: 0.8rem;
            color: var(--secondary);
            margin-bottom: 3px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .meta-value {
            font-size: 1rem;
        }
        
        .executive-summary {
            background-color: var(--background);
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }
        
        .section-title {
            font-size: 1.3rem;
            color: var(--primary);
            margin-bottom: 15px;
            font-weight: 600;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }
        
        .summary-content {
            color: var(--dark);
        }
        
        .risk-trend-chart {
            background-color: var(--background);
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }
        
        .chart-container {
            width: 100%;
            margin: 15px 0;
            background-color: var(--light);
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--border);
        }
        
        .chart-placeholder {
            text-align: center;
            color: var(--secondary);
            font-style: italic;
            padding: 30px;
        }
        
        .chart-caption {
            text-align: center;
            font-size: 0.9rem;
            color: var(--secondary);
            margin-top: 10px;
        }
        
        .overall-risk {
            display: flex;
            align-items: center;
            margin: 20px 0;
        }
        
        .risk-label {
            font-weight: 600;
            width: 180px;
        }
        
        .risk-meter {
            flex: 1;
            height: 15px;
            background-color: #eee;
            border-radius: 0;
            overflow: hidden;
            position: relative;
            border: 1px solid var(--border);
        }
        
        .risk-fill {
            height: 100%;
            transition: width 0.8s;
        }
        
        .risk-text {
            width: 120px;
            text-align: right;
            font-weight: 600;
            padding-left: 15px;
            font-size: 0.9rem;
        }
        
        .low {
            background-color: #4a4a4a;
        }
        
        .moderate {
            background-color: #4a4a4a;
        }
        
        .high {
            background-color: #4a4a4a;
        }
        
        .risk-factor-card {
            background-color: var(--background);
            margin-bottom: 25px;
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        .risk-factor-header {
            background-color: var(--light);
            color: var(--dark);
            padding: 12px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }
        
        .risk-factor-title {
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .risk-factor-content {
            padding: 15px;
        }
        
        .risk-description {
            margin-bottom: 20px;
        }
        
        .impact-analysis {
            margin-bottom: 25px;
        }
        
        .impact-content {
            background-color: var(--light);
            padding: 15px;
            margin-top: 10px;
            border: 1px solid var(--border);
        }
        
        .indicators {
            margin-top: 20px;
        }
        
        .indicator-list {
            margin-top: 15px;
        }
        
        .indicator-item {
            display: flex;
            margin-bottom: 12px;
        }
        
        .indicator-number {
            margin-right: 15px;
            flex-shrink: 0;
            font-weight: bold;
            color: var(--secondary);
        }
        
        .indicator-text {
            flex: 1;
        }
        
        .risk-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .risk-item {
            background-color: var(--background);
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        .risk-item-header {
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            background-color: var(--light);
        }
        
        .risk-item-title {
            font-weight: 600;
            font-size: 1rem;
        }
        
        .risk-badge {
            padding: 3px 8px;
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
            text-transform: uppercase;
        }
        
        .badge-low {
            background-color: #4a4a4a;
        }
        
        .badge-moderate {
            background-color: #4a4a4a;
        }
        
        .badge-high {
            background-color: #4a4a4a;
        }
        
        .risk-item-content {
            padding: 15px;
        }
        
        .methodology {
            background-color: var(--background);
            padding: 20px;
            margin-top: 40px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }
        
        .methodology-content {
            background-color: var(--light);
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9rem;
            border: 1px solid var(--border);
        }
        
        .report-footer {
            margin-top: 50px;
            text-align: center;
            color: var(--secondary);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
            padding-top: 20px;
        }
        
        .timestamp {
            margin-top: 5px;
            font-size: 0.8rem;
        }
        
        h3 {
            font-size: 1.1rem;
            margin-bottom: 10px;
            color: var(--secondary);
        }
        
        /* Print styling */
        @media print {
            body {
                background-color: white;
                color: black;
                padding: 0;
                margin: 0;
            }
            
            .container {
                max-width: 100%;
                padding: 0 1cm;
            }
            
            .report-header {
                margin-bottom: 1.5cm;
            }
            
            .meta-info, 
            .executive-summary, 
            .risk-factor-card,
            .methodology,
            .risk-trend-chart {
                box-shadow: none;
                border: 1px solid #cccccc;
                break-inside: avoid;
            }
            
            .report-footer {
                margin-top: 1cm;
                padding-top: 0.5cm;
            }
        }
    </style>
</head>
<body>
    <div class="container">
"""
        html_end = """
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Any additional JavaScript can go here
        });
    </script>
</body>
</html>
"""
        
        # Generate the HTML content for each section
        header = self._generate_header()
        executive_summary = self._generate_executive_summary()
        trend_chart = self._generate_trend_chart()
        risk_factors_html = self._generate_risk_factors(risk_factors)
        methodology = self._generate_methodology()
        footer = self._generate_footer()
        
        # Combine all sections into the complete HTML
        report_html = f"{html_start}{header}{executive_summary}{trend_chart}{risk_factors_html}{methodology}{footer}{html_end}"
        
        return report_html
    
    
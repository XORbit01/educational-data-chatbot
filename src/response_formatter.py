"""
Response Formatter for Educational Data Chatbot.

Provides intelligent visualization generation and response formatting
based on query results and data types.

Developer: aliawada127001@outlook.com
"""

from typing import Any, Optional, Tuple, List
from dataclasses import dataclass
import re

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import config
from logger import app_logger


@dataclass
class VisualizationResult:
    """Result of visualization generation."""
    figure: Optional[go.Figure]
    chart_type: str
    title: str
    description: str


class ChartDetector:
    """
    Detects the appropriate chart type based on data and question.
    """
    
    # Keywords for different chart types
    CHART_KEYWORDS = {
        'bar': ['compare', 'comparison', 'vs', 'versus', 'each', 'per', 'by', 'breakdown'],
        'line': ['trend', 'over time', 'progress', 'improvement', 'change', 'across'],
        'pie': ['distribution', 'proportion', 'percentage', 'share', 'breakdown'],
        'scatter': ['correlation', 'relationship', 'between', 'vs', 'affect'],
        'box': ['distribution', 'spread', 'variance', 'range', 'quartile'],
        'histogram': ['distribution', 'frequency', 'histogram', 'spread'],
        'heatmap': ['correlation', 'matrix', 'heatmap', 'all', 'relationship'],
    }
    
    @classmethod
    def detect_chart_type(
        cls, 
        data: Any, 
        question: str = ""
    ) -> str:
        """
        Detect the most appropriate chart type for the data.
        
        Args:
            data: The result data
            question: Original question for context
            
        Returns:
            Chart type string
        """
        question_lower = question.lower()
        
        # Check question keywords first
        for chart_type, keywords in cls.CHART_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                # Validate that data supports this chart type
                if cls._can_create_chart(data, chart_type):
                    return chart_type
        
        # Infer from data structure
        if isinstance(data, pd.DataFrame):
            if len(data.columns) == 2:
                # Two columns - likely comparison
                return 'bar'
            elif len(data.columns) > 3:
                # Multiple numeric columns - correlation
                return 'heatmap'
            else:
                return 'bar'
        
        elif isinstance(data, pd.Series):
            if len(data) <= 10:
                return 'bar'
            elif len(data) <= 5:
                return 'pie'
            else:
                return 'bar'
        
        elif isinstance(data, (int, float)):
            return 'metric'  # Single value display
        
        return 'table'  # Fallback to table display
    
    @classmethod
    def _can_create_chart(cls, data: Any, chart_type: str) -> bool:
        """Check if data supports the specified chart type."""
        if chart_type in ['bar', 'line', 'pie']:
            return isinstance(data, (pd.Series, pd.DataFrame))
        elif chart_type in ['scatter', 'heatmap']:
            return isinstance(data, pd.DataFrame) and len(data.columns) >= 2
        elif chart_type in ['box', 'histogram']:
            return isinstance(data, (pd.Series, pd.DataFrame))
        return True


class VisualizationGenerator:
    """
    Generates Plotly visualizations from query results.
    """
    
    # Color scheme - modern, accessible palette
    COLORS = [
        '#2E86AB',  # Blue
        '#A23B72',  # Magenta
        '#F18F01',  # Orange
        '#C73E1D',  # Red
        '#3B1F2B',  # Dark
        '#95C623',  # Green
        '#5C4D7D',  # Purple
        '#F7B538',  # Yellow
    ]
    
    def __init__(self):
        self.chart_height = config.ui.default_chart_height
        self.theme = config.ui.chart_theme
    
    def generate(
        self, 
        data: Any, 
        question: str = "",
        chart_type: str = None
    ) -> VisualizationResult:
        """
        Generate an appropriate visualization for the data.
        
        Args:
            data: Result data to visualize
            question: Original question for context
            chart_type: Optional override for chart type
            
        Returns:
            VisualizationResult with Plotly figure
        """
        if data is None:
            return VisualizationResult(
                figure=None,
                chart_type='none',
                title='',
                description='No data to visualize'
            )
        
        # Detect chart type if not specified
        if chart_type is None:
            chart_type = ChartDetector.detect_chart_type(data, question)
        
        # Generate appropriate chart
        try:
            if chart_type == 'metric':
                return self._create_metric(data, question)
            elif chart_type == 'bar':
                return self._create_bar_chart(data, question)
            elif chart_type == 'line':
                return self._create_line_chart(data, question)
            elif chart_type == 'pie':
                return self._create_pie_chart(data, question)
            elif chart_type == 'scatter':
                return self._create_scatter_plot(data, question)
            elif chart_type == 'box':
                return self._create_box_plot(data, question)
            elif chart_type == 'histogram':
                return self._create_histogram(data, question)
            elif chart_type == 'heatmap':
                return self._create_heatmap(data, question)
            else:
                return VisualizationResult(
                    figure=None,
                    chart_type='table',
                    title='',
                    description='Data displayed as table'
                )
                
        except Exception as e:
            app_logger.warning(
                "Visualization generation failed",
                error=str(e),
                chart_type=chart_type
            )
            return VisualizationResult(
                figure=None,
                chart_type='error',
                title='',
                description=f'Could not generate visualization: {str(e)}'
            )
    
    def _create_bar_chart(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a bar chart."""
        title = self._generate_title(question, 'Comparison')
        
        if isinstance(data, pd.Series):
            fig = px.bar(
                x=data.index.astype(str),
                y=data.values,
                labels={'x': data.index.name or 'Category', 'y': data.name or 'Value'},
                title=title,
                color_discrete_sequence=self.COLORS
            )
        elif isinstance(data, pd.DataFrame):
            # Use first column as x, others as y
            if len(data.columns) >= 2:
                fig = px.bar(
                    data,
                    x=data.columns[0],
                    y=data.columns[1:].tolist(),
                    title=title,
                    barmode='group',
                    color_discrete_sequence=self.COLORS
                )
            else:
                fig = px.bar(
                    data,
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
        else:
            return VisualizationResult(
                figure=None,
                chart_type='bar',
                title=title,
                description='Invalid data for bar chart'
            )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='bar',
            title=title,
            description='Bar chart comparison'
        )
    
    def _create_line_chart(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a line chart."""
        title = self._generate_title(question, 'Trend')
        
        if isinstance(data, pd.Series):
            fig = px.line(
                x=data.index,
                y=data.values,
                labels={'x': data.index.name or 'Index', 'y': data.name or 'Value'},
                title=title,
                markers=True
            )
        elif isinstance(data, pd.DataFrame):
            fig = px.line(
                data,
                title=title,
                markers=True,
                color_discrete_sequence=self.COLORS
            )
        else:
            return VisualizationResult(
                figure=None,
                chart_type='line',
                title=title,
                description='Invalid data for line chart'
            )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='line',
            title=title,
            description='Line chart trend'
        )
    
    def _create_pie_chart(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a pie chart."""
        title = self._generate_title(question, 'Distribution')
        
        if isinstance(data, pd.Series):
            fig = px.pie(
                values=data.values,
                names=data.index.astype(str),
                title=title,
                color_discrete_sequence=self.COLORS
            )
        elif isinstance(data, pd.DataFrame) and len(data.columns) >= 2:
            fig = px.pie(
                data,
                values=data.columns[1],
                names=data.columns[0],
                title=title,
                color_discrete_sequence=self.COLORS
            )
        else:
            return VisualizationResult(
                figure=None,
                chart_type='pie',
                title=title,
                description='Invalid data for pie chart'
            )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='pie',
            title=title,
            description='Pie chart distribution'
        )
    
    def _create_scatter_plot(
        self, 
        data: pd.DataFrame, 
        question: str
    ) -> VisualizationResult:
        """Create a scatter plot."""
        title = self._generate_title(question, 'Correlation')
        
        if not isinstance(data, pd.DataFrame) or len(data.columns) < 2:
            return VisualizationResult(
                figure=None,
                chart_type='scatter',
                title=title,
                description='Invalid data for scatter plot'
            )
        
        x_col = data.columns[0]
        y_col = data.columns[1]
        
        fig = px.scatter(
            data,
            x=x_col,
            y=y_col,
            title=title,
            trendline='ols' if len(data) > 3 else None,
            color_discrete_sequence=self.COLORS
        )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='scatter',
            title=title,
            description='Scatter plot correlation'
        )
    
    def _create_box_plot(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a box plot."""
        title = self._generate_title(question, 'Distribution')
        
        if isinstance(data, pd.Series):
            fig = px.box(
                y=data.values,
                title=title,
                color_discrete_sequence=self.COLORS
            )
        elif isinstance(data, pd.DataFrame):
            fig = px.box(
                data,
                title=title,
                color_discrete_sequence=self.COLORS
            )
        else:
            return VisualizationResult(
                figure=None,
                chart_type='box',
                title=title,
                description='Invalid data for box plot'
            )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='box',
            title=title,
            description='Box plot distribution'
        )
    
    def _create_histogram(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a histogram."""
        title = self._generate_title(question, 'Distribution')
        
        if isinstance(data, pd.Series):
            fig = px.histogram(
                x=data.values,
                title=title,
                color_discrete_sequence=self.COLORS
            )
        elif isinstance(data, pd.DataFrame):
            # Use first numeric column
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                fig = px.histogram(
                    data,
                    x=numeric_cols[0],
                    title=title,
                    color_discrete_sequence=self.COLORS
                )
            else:
                return VisualizationResult(
                    figure=None,
                    chart_type='histogram',
                    title=title,
                    description='No numeric data for histogram'
                )
        else:
            return VisualizationResult(
                figure=None,
                chart_type='histogram',
                title=title,
                description='Invalid data for histogram'
            )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='histogram',
            title=title,
            description='Histogram distribution'
        )
    
    def _create_heatmap(
        self, 
        data: pd.DataFrame, 
        question: str
    ) -> VisualizationResult:
        """Create a correlation heatmap."""
        title = self._generate_title(question, 'Correlation Matrix')
        
        if not isinstance(data, pd.DataFrame):
            return VisualizationResult(
                figure=None,
                chart_type='heatmap',
                title=title,
                description='Invalid data for heatmap'
            )
        
        # If it's already a correlation matrix, use it
        if data.shape[0] == data.shape[1] and all(data.columns == data.index):
            corr_matrix = data
        else:
            # Calculate correlation for numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            if len(numeric_data.columns) < 2:
                return VisualizationResult(
                    figure=None,
                    chart_type='heatmap',
                    title=title,
                    description='Not enough numeric columns for heatmap'
                )
            corr_matrix = numeric_data.corr()
        
        fig = px.imshow(
            corr_matrix,
            title=title,
            color_continuous_scale='RdBu_r',
            aspect='auto',
            text_auto='.2f'
        )
        
        self._apply_theme(fig)
        
        return VisualizationResult(
            figure=fig,
            chart_type='heatmap',
            title=title,
            description='Correlation heatmap'
        )
    
    def _create_metric(
        self, 
        data: Any, 
        question: str
    ) -> VisualizationResult:
        """Create a metric display (for single values)."""
        title = self._generate_title(question, 'Result')
        
        # For single values, we'll return None and let the UI handle it
        # as a styled metric display
        return VisualizationResult(
            figure=None,
            chart_type='metric',
            title=title,
            description=f'Value: {data}'
        )
    
    def _generate_title(self, question: str, fallback: str) -> str:
        """Generate a chart title from the question."""
        if not question:
            return fallback
        
        # Clean up the question for use as title
        title = question.strip()
        if title.endswith('?'):
            title = title[:-1]
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + '...'
        
        return title or fallback
    
    def _apply_theme(self, fig: go.Figure) -> None:
        """Apply consistent theme to figure."""
        fig.update_layout(
            template=self.theme,
            height=self.chart_height,
            font=dict(family="Inter, sans-serif"),
            title_font=dict(size=16, color='#1f2937'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=40, r=40, t=60, b=40)
        )


# Global instance
_visualizer: Optional[VisualizationGenerator] = None


def get_visualizer() -> VisualizationGenerator:
    """Get or create the global visualizer."""
    global _visualizer
    if _visualizer is None:
        _visualizer = VisualizationGenerator()
    return _visualizer


def generate_visualization(
    data: Any, 
    question: str = "",
    chart_type: str = None
) -> VisualizationResult:
    """
    Convenience function for visualization generation.
    
    Args:
        data: Data to visualize
        question: Original question
        chart_type: Optional chart type override
        
    Returns:
        VisualizationResult with Plotly figure
    """
    return get_visualizer().generate(data, question, chart_type)


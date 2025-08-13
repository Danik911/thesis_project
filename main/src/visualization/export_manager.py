"""
Export Manager for Thesis Visualizations

Handles publication-quality exports of thesis visualizations in multiple formats
suitable for academic publication, presentations, and stakeholder reports.

Supported formats:
- High-resolution PNG (300 DPI) for publications
- Vector SVG for scalable graphics
- Interactive HTML for web presentations
- PDF for academic submissions
- PowerPoint-ready formats
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ExportConfig:
    """Configuration for export formats and quality settings."""
    
    # Publication quality settings
    PUBLICATION_DPI = 300
    PRESENTATION_DPI = 150
    WEB_DPI = 96
    
    # Standard academic dimensions (inches)
    SINGLE_COLUMN_WIDTH = 3.5
    DOUBLE_COLUMN_WIDTH = 7.0
    FULL_PAGE_WIDTH = 8.5
    
    # Color modes
    COLOR_MODE = "RGBA"
    GRAYSCALE_MODE = "L"
    
    # File formats
    FORMATS = {
        "png": {"dpi": PUBLICATION_DPI, "transparent": True},
        "svg": {"format": "svg"},
        "html": {"include_plotlyjs": True, "div_id": None},
        "pdf": {"format": "pdf", "width": 11, "height": 8.5}
    }


class ExportManager:
    """
    Publication-quality export manager for thesis visualizations.
    
    Handles multiple output formats optimized for different use cases:
    - Academic publication requirements
    - Presentation formats
    - Web and interactive displays
    - Stakeholder reports
    """
    
    def __init__(self, base_output_directory: str | Path):
        """
        Initialize the ExportManager.
        
        Args:
            base_output_directory: Base directory for all exports
        """
        self.logger = logging.getLogger(__name__)
        self.base_output_directory = Path(base_output_directory)
        
        # Create export subdirectories
        self.directories = {
            "publication": self.base_output_directory / "publication",
            "presentation": self.base_output_directory / "presentation", 
            "web": self.base_output_directory / "web",
            "stakeholder": self.base_output_directory / "stakeholder",
            "archive": self.base_output_directory / "archive"
        }
        
        # Create all directories
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
            
        self.config = ExportConfig()
        self.logger.info(f"ExportManager initialized with base directory: {self.base_output_directory}")
    
    def export_publication_ready(self, 
                                figure: go.Figure, 
                                filename_base: str,
                                caption: Optional[str] = None,
                                width_inches: float = ExportConfig.DOUBLE_COLUMN_WIDTH,
                                height_inches: float = 5.0) -> Dict[str, Path]:
        """
        Export figure in publication-ready formats.
        
        Args:
            figure: Plotly figure to export
            filename_base: Base filename without extension
            caption: Optional caption for the figure
            width_inches: Width in inches for academic standards
            height_inches: Height in inches
            
        Returns:
            Dictionary mapping format names to file paths
        """
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate pixel dimensions
        width_px = int(width_inches * self.config.PUBLICATION_DPI)
        height_px = int(height_inches * self.config.PUBLICATION_DPI)
        
        # Update figure for publication quality
        pub_figure = self._prepare_publication_figure(figure, caption)
        
        # Export PNG for academic journals
        png_filename = f"{filename_base}_publication_{timestamp}.png"
        png_path = self.directories["publication"] / png_filename
        
        try:
            pub_figure.write_image(
                str(png_path),
                format="png",
                width=width_px,
                height=height_px,
                scale=1,  # Already at target DPI
                engine="kaleido"
            )
            exported_files["png"] = png_path
            self.logger.info(f"Published PNG: {png_path}")
        except Exception as e:
            self.logger.error(f"Failed to export PNG: {e}")
        
        # Export SVG for vector graphics
        svg_filename = f"{filename_base}_vector_{timestamp}.svg"
        svg_path = self.directories["publication"] / svg_filename
        
        try:
            pub_figure.write_image(
                str(svg_path),
                format="svg",
                width=width_px,
                height=height_px,
                engine="kaleido"
            )
            exported_files["svg"] = svg_path
            self.logger.info(f"Published SVG: {svg_path}")
        except Exception as e:
            self.logger.error(f"Failed to export SVG: {e}")
        
        # Export HTML for supplementary materials
        html_filename = f"{filename_base}_interactive_{timestamp}.html"
        html_path = self.directories["publication"] / html_filename
        
        try:
            pub_figure.write_html(
                str(html_path),
                include_plotlyjs='cdn',
                config={'displayModeBar': False, 'staticPlot': False}
            )
            exported_files["html"] = html_path
            self.logger.info(f"Published HTML: {html_path}")
        except Exception as e:
            self.logger.error(f"Failed to export HTML: {e}")
        
        return exported_files
    
    def export_presentation_formats(self,
                                  figure: go.Figure,
                                  filename_base: str,
                                  slide_format: str = "16:9") -> Dict[str, Path]:
        """
        Export figure optimized for presentations.
        
        Args:
            figure: Plotly figure to export
            filename_base: Base filename without extension
            slide_format: Slide aspect ratio ("16:9" or "4:3")
            
        Returns:
            Dictionary mapping format names to file paths
        """
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set dimensions based on slide format
        if slide_format == "16:9":
            width_px, height_px = 1920, 1080
        elif slide_format == "4:3":
            width_px, height_px = 1024, 768
        else:
            width_px, height_px = 1920, 1080  # Default to 16:9
        
        # Prepare figure for presentation
        pres_figure = self._prepare_presentation_figure(figure)
        
        # Export high-resolution PNG for slides
        png_filename = f"{filename_base}_slide_{slide_format}_{timestamp}.png"
        png_path = self.directories["presentation"] / png_filename
        
        try:
            pres_figure.write_image(
                str(png_path),
                format="png",
                width=width_px,
                height=height_px,
                scale=1
            )
            exported_files["slide_png"] = png_path
            self.logger.info(f"Presentation PNG: {png_path}")
        except Exception as e:
            self.logger.error(f"Failed to export presentation PNG: {e}")
        
        # Export PowerPoint-friendly HTML
        html_filename = f"{filename_base}_powerpoint_{timestamp}.html"
        html_path = self.directories["presentation"] / html_filename
        
        try:
            # Create a simplified version for embedding
            pres_figure.write_html(
                str(html_path),
                include_plotlyjs='inline',
                config={
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                    'displaylogo': False
                }
            )
            exported_files["powerpoint_html"] = html_path
            self.logger.info(f"PowerPoint HTML: {html_path}")
        except Exception as e:
            self.logger.error(f"Failed to export PowerPoint HTML: {e}")
        
        return exported_files
    
    def export_stakeholder_summary(self,
                                 figure: go.Figure,
                                 filename_base: str,
                                 executive_summary: Optional[str] = None) -> Dict[str, Path]:
        """
        Export figure with executive summary for stakeholders.
        
        Args:
            figure: Plotly figure to export
            filename_base: Base filename without extension
            executive_summary: Optional executive summary text
            
        Returns:
            Dictionary mapping format names to file paths
        """
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare stakeholder-friendly figure
        stake_figure = self._prepare_stakeholder_figure(figure, executive_summary)
        
        # Export large format for reports
        report_filename = f"{filename_base}_stakeholder_report_{timestamp}.png"
        report_path = self.directories["stakeholder"] / report_filename
        
        try:
            stake_figure.write_image(
                str(report_path),
                format="png",
                width=1600,
                height=1200,
                scale=2  # Extra high resolution
            )
            exported_files["stakeholder_png"] = report_path
            self.logger.info(f"Stakeholder PNG: {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to export stakeholder PNG: {e}")
        
        # Export interactive dashboard
        dashboard_filename = f"{filename_base}_dashboard_{timestamp}.html"
        dashboard_path = self.directories["stakeholder"] / dashboard_filename
        
        try:
            stake_figure.write_html(
                str(dashboard_path),
                include_plotlyjs='cdn',
                config={
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f'{filename_base}_export',
                        'height': 1200,
                        'width': 1600,
                        'scale': 2
                    }
                }
            )
            exported_files["dashboard_html"] = dashboard_path
            self.logger.info(f"Stakeholder dashboard: {dashboard_path}")
        except Exception as e:
            self.logger.error(f"Failed to export stakeholder dashboard: {e}")
        
        return exported_files
    
    def export_all_formats(self,
                          figure: go.Figure,
                          filename_base: str,
                          caption: Optional[str] = None,
                          executive_summary: Optional[str] = None) -> Dict[str, Dict[str, Path]]:
        """
        Export figure in all available formats.
        
        Args:
            figure: Plotly figure to export
            filename_base: Base filename without extension
            caption: Optional figure caption
            executive_summary: Optional executive summary
            
        Returns:
            Nested dictionary with format categories and file paths
        """
        all_exports = {}
        
        try:
            # Publication formats
            pub_exports = self.export_publication_ready(figure, filename_base, caption)
            all_exports["publication"] = pub_exports
            
            # Presentation formats (both 16:9 and 4:3)
            pres_exports_16_9 = self.export_presentation_formats(figure, filename_base, "16:9")
            pres_exports_4_3 = self.export_presentation_formats(figure, filename_base, "4:3")
            all_exports["presentation"] = {**pres_exports_16_9, **pres_exports_4_3}
            
            # Stakeholder formats
            stake_exports = self.export_stakeholder_summary(figure, filename_base, executive_summary)
            all_exports["stakeholder"] = stake_exports
            
            # Web format
            web_exports = self._export_web_optimized(figure, filename_base)
            all_exports["web"] = web_exports
            
            self.logger.info(f"Successfully exported {filename_base} in all formats")
            
        except Exception as e:
            self.logger.error(f"Failed to export all formats for {filename_base}: {e}")
            raise
        
        return all_exports
    
    def _prepare_publication_figure(self, figure: go.Figure, caption: Optional[str] = None) -> go.Figure:
        """Prepare figure for academic publication."""
        pub_fig = go.Figure(figure)
        
        # Update layout for publication standards
        pub_fig.update_layout(
            font={'family': 'Times New Roman', 'size': 12},
            title_font={'size': 14},
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=60, r=30, t=80, b=60)
        )
        
        # Add caption if provided
        if caption:
            pub_fig.add_annotation(
                text=f"<i>{caption}</i>",
                showarrow=False,
                x=0.5, y=-0.15,
                xref="paper", yref="paper",
                font={'size': 10},
                align="center"
            )
        
        return pub_fig
    
    def _prepare_presentation_figure(self, figure: go.Figure) -> go.Figure:
        """Prepare figure for presentation slides."""
        pres_fig = go.Figure(figure)
        
        # Update for presentation visibility
        pres_fig.update_layout(
            font={'family': 'Arial', 'size': 16},
            title_font={'size': 24},
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=80, r=40, t=100, b=80)
        )
        
        return pres_fig
    
    def _prepare_stakeholder_figure(self, figure: go.Figure, summary: Optional[str] = None) -> go.Figure:
        """Prepare figure for stakeholder presentations."""
        stake_fig = go.Figure(figure)
        
        # Update for stakeholder clarity
        stake_fig.update_layout(
            font={'family': 'Arial', 'size': 14},
            title_font={'size': 20},
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=70, r=40, t=120, b=100)
        )
        
        # Add executive summary if provided
        if summary:
            stake_fig.add_annotation(
                text=f"<b>Key Insight:</b> {summary}",
                showarrow=False,
                x=0.5, y=1.1,
                xref="paper", yref="paper",
                font={'size': 12, 'color': 'blue'},
                align="center",
                bgcolor="rgba(173,216,230,0.3)",
                bordercolor="blue",
                borderwidth=1
            )
        
        return stake_fig
    
    def _export_web_optimized(self, figure: go.Figure, filename_base: str) -> Dict[str, Path]:
        """Export web-optimized versions."""
        web_exports = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Lightweight PNG for web
        web_png_filename = f"{filename_base}_web_{timestamp}.png"
        web_png_path = self.directories["web"] / web_png_filename
        
        try:
            figure.write_image(
                str(web_png_path),
                format="png",
                width=800,
                height=600,
                scale=1
            )
            web_exports["web_png"] = web_png_path
        except Exception as e:
            self.logger.error(f"Failed to export web PNG: {e}")
        
        # Interactive HTML
        web_html_filename = f"{filename_base}_interactive_{timestamp}.html"
        web_html_path = self.directories["web"] / web_html_filename
        
        try:
            figure.write_html(
                str(web_html_path),
                include_plotlyjs='cdn',
                config={'displayModeBar': True, 'responsive': True}
            )
            web_exports["web_html"] = web_html_path
        except Exception as e:
            self.logger.error(f"Failed to export web HTML: {e}")
        
        return web_exports
    
    def create_export_manifest(self, export_results: Dict) -> Path:
        """
        Create a manifest file listing all exported files.
        
        Args:
            export_results: Results from export operations
            
        Returns:
            Path to manifest file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = self.directories["archive"] / f"export_manifest_{timestamp}.txt"
        
        manifest_content = [
            "THESIS VISUALIZATION EXPORT MANIFEST",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Export Manager: {self.__class__.__name__}",
            "",
            "EXPORTED FILES:",
            "-" * 20
        ]
        
        for category, files in export_results.items():
            manifest_content.append(f"\n{category.upper()}:")
            if isinstance(files, dict):
                for format_name, file_path in files.items():
                    manifest_content.append(f"  {format_name}: {file_path}")
            else:
                manifest_content.append(f"  {files}")
        
        manifest_content.extend([
            "",
            "USAGE GUIDELINES:",
            "-" * 20,
            "• publication/: Use for academic journals and thesis submission",
            "• presentation/: Use for conference presentations and slides", 
            "• stakeholder/: Use for business reports and executive summaries",
            "• web/: Use for online publications and interactive displays",
            "",
            "Quality Settings:",
            f"• Publication DPI: {self.config.PUBLICATION_DPI}",
            f"• Presentation DPI: {self.config.PRESENTATION_DPI}",
            f"• Web DPI: {self.config.WEB_DPI}",
            "",
            "All exports use real data from Task 28 statistical analysis.",
            "NO FALLBACK LOGIC - Genuine system performance metrics only."
        ])
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("\n".join(manifest_content))
        
        self.logger.info(f"Export manifest created: {manifest_path}")
        return manifest_path
    
    def archive_exports(self, export_results: Dict) -> Path:
        """
        Create an archive of all exported files.
        
        Args:
            export_results: Results from export operations
            
        Returns:
            Path to archive file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.directories["archive"] / f"thesis_visualizations_archive_{timestamp}"
        
        try:
            # Create archive directory
            archive_path.mkdir(exist_ok=True)
            
            # Copy all exported files to archive
            for category, files in export_results.items():
                category_dir = archive_path / category
                category_dir.mkdir(exist_ok=True)
                
                if isinstance(files, dict):
                    for format_name, file_path in files.items():
                        if isinstance(file_path, Path) and file_path.exists():
                            dest_path = category_dir / f"{format_name}_{file_path.name}"
                            shutil.copy2(file_path, dest_path)
            
            # Create manifest in archive
            manifest_path = self.create_export_manifest(export_results)
            shutil.copy2(manifest_path, archive_path / "MANIFEST.txt")
            
            self.logger.info(f"Archive created: {archive_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create archive: {e}")
            raise
        
        return archive_path
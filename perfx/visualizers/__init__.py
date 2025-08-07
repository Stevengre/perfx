#!/usr/bin/env python3
"""
Visualization modules for perfx
"""

from .charts import ChartGenerator
from .tables import TableGenerator
from .reports import ReportGenerator
from .latex_tables import LatexTableGenerator, generate_latex_table
from .academic_charts import AcademicChartGenerator
from .latex_document import LatexDocumentGenerator, generate_latex_document
# Removed outdated modules: comparison_config, comparison_engine, analysis_engine

__all__ = [
    "ChartGenerator",
    "TableGenerator", 
    "ReportGenerator",
    "LatexTableGenerator",
    "generate_latex_table",
    "AcademicChartGenerator",
    "LatexDocumentGenerator",
    "generate_latex_document"
]

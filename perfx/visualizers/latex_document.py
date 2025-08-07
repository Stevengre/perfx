#!/usr/bin/env python3
"""
LaTeX Document Generator for perfx

This module provides functionality to combine all generated charts and tables
into a single LaTeX document and compile it to PDF.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from rich.console import Console

console = Console()


class LatexDocumentGenerator:
    """Generates a LaTeX document containing all charts and tables"""
    
    def __init__(self, output_dir: str = "results/analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_document(self, 
                         charts: List[Dict[str, Any]], 
                         tables: List[Dict[str, Any]], 
                         title: str = "Evaluation Results",
                         author: str = "perfx",
                         document_class: str = "article") -> Dict[str, Any]:
        """
        Generate a LaTeX document containing all charts and tables
        
        Args:
            charts: List of chart configurations
            tables: List of table configurations  
            title: Document title
            author: Document author
            document_class: LaTeX document class
            
        Returns:
            Dict with success status and file paths
        """
        try:
            # Create LaTeX content
            latex_content = self._generate_latex_content(charts, tables, title, author, document_class)
            
            # Write LaTeX file
            latex_file = self.output_dir / "evaluation_report.tex"
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile to PDF
            pdf_file = self.output_dir / "evaluation_report.pdf"
            success = self._compile_latex(latex_file, pdf_file)
            
            if success:
                console.print(f"[green]✓ LaTeX document generated: {latex_file}[/green]")
                console.print(f"[green]✓ PDF generated: {pdf_file}[/green]")
                return {
                    'success': True,
                    'latex_file': str(latex_file),
                    'pdf_file': str(pdf_file),
                    'charts_included': len(charts),
                    'tables_included': len(tables)
                }
            else:
                console.print(f"[yellow]⚠ LaTeX document generated but PDF compilation failed: {latex_file}[/yellow]")
                return {
                    'success': False,
                    'latex_file': str(latex_file),
                    'pdf_file': None,
                    'error': 'PDF compilation failed',
                    'charts_included': len(charts),
                    'tables_included': len(tables)
                }
                
        except Exception as e:
            console.print(f"[red]✗ Error generating LaTeX document: {e}[/red]")
            return {
                'success': False,
                'error': str(e),
                'charts_included': 0,
                'tables_included': 0
            }
    
    def _generate_latex_content(self, 
                               charts: List[Dict[str, Any]], 
                               tables: List[Dict[str, Any]], 
                               title: str, 
                               author: str, 
                               document_class: str) -> str:
        """Generate the complete LaTeX content"""
        
        # Document header
        content = f"""\\documentclass[{document_class}]{{article}}

% Packages
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\usepackage{{float}}
\\usepackage{{hyperref}}
\\usepackage{{caption}}
\\usepackage{{subcaption}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{xcolor}}
\\usepackage{{tabularx}}

% Page setup
\\geometry{{a4paper, margin=2.5cm}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{6pt}}

% Hyperref setup
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    citecolor=red
}}

% Title
\\title{{{title}}}
\\author{{{author}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\tableofcontents
\\newpage

"""
        
        # Add tables
        if tables:
            content += "\\section{Tables}\n\n"
            for i, table in enumerate(tables):
                table_name = table.get('name', f'table_{i}')
                table_title = table.get('title', table_name)
                table_file = table.get('output_file', '')
                
                if table_file:
                    # Check if file exists relative to output directory
                    full_table_path = os.path.join(str(self.output_dir), table_file)
                    if os.path.exists(full_table_path):
                        content += "\\subsection{" + table_title + "}\\label{tab:" + table_name + "}\n\n"
                        # Use \input command for simple table files
                        content += "\\input{" + table_file + "}\n\n"
                        content += "\\newpage\n\n"
                    else:
                        console.print(f"[yellow]⚠ Table file not found: {full_table_path}[/yellow]")
                else:
                    console.print(f"[yellow]⚠ No table file specified for: {table_name}[/yellow]")
        
        # Add charts from configuration
        if charts:
            content += "\\section{Charts}\n\n"
            for i, chart in enumerate(charts):
                chart_name = chart.get('name', f'chart_{i}')
                chart_title = chart.get('title', chart_name)
                chart_file = chart.get('output_file', '')
                
                if chart_file:
                    # Check if file exists relative to output directory
                    full_chart_path = os.path.join(str(self.output_dir), chart_file)
                    if os.path.exists(full_chart_path):
                        content += "\\subsection{" + chart_title + "}\\label{fig:" + chart_name + "}\n\n"
                        content += "\\begin{figure}[H]\n"
                        content += "\\centering\n"
                        content += "\\includegraphics[width=0.8\\textwidth]{" + chart_file + "}\n"
                        content += "\\caption{" + chart_title + "}\n"
                        content += "\\label{fig:" + chart_name + "}\n"
                        content += "\\end{figure}\n\n"
                        content += "\\newpage\n\n"
                    else:
                        console.print(f"[yellow]⚠ Chart file not found: {full_chart_path}[/yellow]")
                else:
                    console.print(f"[yellow]⚠ No chart file specified for: {chart_name}[/yellow]")
        
        # Document footer
        content += "\\end{document}\n"
        
        return content
    
    def _compile_latex(self, latex_file: Path, pdf_file: Path) -> bool:
        """Compile LaTeX file to PDF"""
        try:
            # Check if pdflatex is available
            result = subprocess.run(['which', 'pdflatex'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                console.print("[yellow]⚠ pdflatex not found. PDF compilation skipped.[/yellow]")
                return False
            
            # Compile LaTeX to PDF
            console.print(f"[blue]Compiling LaTeX to PDF: {latex_file}[/blue]")
            
            # Run pdflatex twice to resolve references
            for run in range(2):
                try:
                    result = subprocess.run([
                        'pdflatex',
                        '-interaction=nonstopmode',
                        '-output-directory=' + str(latex_file.parent),
                        str(latex_file)
                    ], capture_output=True, text=True, cwd=latex_file.parent, timeout=60)
                    
                    if result.returncode != 0:
                        console.print(f"[red]✗ LaTeX compilation failed (run {run + 1}):[/red]")
                        console.print(f"[dim]{result.stderr}[/dim]")
                        return False
                        
                except subprocess.TimeoutExpired:
                    console.print(f"[red]✗ LaTeX compilation timed out (run {run + 1})[/red]")
                    return False
            
            # Check if PDF was created
            if pdf_file.exists():
                console.print(f"[green]✓ PDF successfully generated: {pdf_file}[/green]")
                return True
            else:
                console.print(f"[red]✗ PDF file not created: {pdf_file}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]✗ Error during LaTeX compilation: {e}[/red]")
            return False
    
    def _extract_table_content(self, table_file_path: str) -> str:
        """Extract table content from a LaTeX file, removing document structure"""
        try:
            with open(table_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the table content between \begin{document} and \end{document}
            start_marker = "\\begin{document}"
            end_marker = "\\end{document}"
            
            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker)
            
            if start_pos != -1 and end_pos != -1:
                # Extract content between document markers
                table_content = content[start_pos + len(start_marker):end_pos].strip()
                # Remove problematic commands that should only be in preamble
                table_content = self._clean_table_content(table_content)
                return table_content
            else:
                # If no document markers, return the content as-is for simple table files
                # This handles files that only contain table content
                return content
                
        except Exception as e:
            console.print(f"[red]Error extracting table content from {table_file_path}: {e}[/red]")
            return ""
    
    def _clean_table_content(self, content: str) -> str:
        """Clean table content by removing problematic LaTeX commands"""
        # Remove commands that should only be in preamble
        problematic_commands = [
            r'\\title\{[^}]*\}',
            r'\\author\{[^}]*\}',
            r'\\date\{[^}]*\}',
            r'\\maketitle',
            r'\\documentclass\{[^}]*\}',
            r'\\usepackage\{[^}]*\}',
            r'\\geometry\{[^}]*\}',
            r'\\hypersetup\{[^}]*\}'
        ]
        
        import re
        for pattern in problematic_commands:
            content = re.sub(pattern, '', content)
        
        # Remove extra blank lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def _clean_simple_table_content(self, content: str) -> str:
        """Clean simple table content (files without document structure)"""
        import re
        
        # For simple table files, we only remove extra blank lines
        # and ensure proper spacing
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()


def generate_latex_document(config: Dict[str, Any], base_dir: str = ".") -> Dict[str, Any]:
    """
    Generate a LaTeX document from visualization configuration
    
    Args:
        config: Visualization configuration containing charts and tables
        base_dir: Base directory for resolving relative paths
        
    Returns:
        Dict with generation results
    """
    try:
        # Extract configuration
        data_dir = Path(base_dir) / config.get('data_directory', 'results/processed')
        output_dir = Path(base_dir) / config.get('output_directory', 'results/analysis')
        title = config.get('document_title', 'Evaluation Results')
        author = config.get('document_author', 'perfx')
        document_class = config.get('document_class', 'article')
        
        # Get charts and tables from config
        charts = config.get('charts', [])
        tables = config.get('tables', [])
        
        # Resolve relative paths - use relative paths for LaTeX compatibility
        for chart in charts:
            if 'output_file' in chart:
                # Use relative path from output directory
                chart['output_file'] = chart['output_file']
        
        for table in tables:
            if 'output_file' in table:
                # Use relative path from output directory
                table['output_file'] = table['output_file']
        
        # Generate document
        generator = LatexDocumentGenerator(str(output_dir))
        result = generator.generate_document(
            charts=charts,
            tables=tables,
            title=title,
            author=author,
            document_class=document_class
        )
        
        return result
        
    except Exception as e:
        console.print(f"[red]✗ Error in generate_latex_document: {e}[/red]")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate LaTeX document from configuration")
    parser.add_argument("--config", required=True, help="Path to visualization config JSON")
    parser.add_argument("--base-dir", default=".", help="Base directory")
    parser.add_argument("--output-dir", default="results/analysis", help="Output directory")
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Generate document
    result = generate_latex_document(config, args.base_dir)
    
    if result['success']:
        print(f"✓ Document generated successfully")
        print(f"  LaTeX: {result.get('latex_file', 'N/A')}")
        print(f"  PDF: {result.get('pdf_file', 'N/A')}")
    else:
        print(f"✗ Document generation failed: {result.get('error', 'Unknown error')}")
        exit(1) 
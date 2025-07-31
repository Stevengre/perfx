#!/usr/bin/env python3
"""
Table generator for Perfx
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


class TableGenerator:
    """Generator for creating various types of tables"""

    def create_table(
        self,
        data: Dict[str, Any],
        columns: List[str],
        output_file: Path,
        format: str = "markdown",
    ) -> None:
        """Create a table in the specified format"""
        try:
            if format == "markdown":
                self._create_markdown_table(data, columns, output_file)
            elif format == "csv":
                self._create_csv_table(data, columns, output_file)
            elif format == "latex":
                self._create_latex_table(data, columns, output_file)
            elif format == "html":
                self._create_html_table(data, columns, output_file)
            else:
                print(f"Unknown table format: {format}")

        except Exception as e:
            print(f"Error creating table: {e}")

    def _create_markdown_table(
        self, data: Dict[str, Any], columns: List[str], output_file: Path
    ) -> None:
        """Create a markdown table"""
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header
            f.write("| " + " | ".join(columns) + " |\n")
            f.write("| " + " | ".join(["---"] * len(columns)) + " |\n")

            # Write data rows
            rows = self._extract_table_data(data, columns)
            for row in rows:
                f.write("| " + " | ".join(str(cell) for cell in row) + " |\n")

    def _create_csv_table(
        self, data: Dict[str, Any], columns: List[str], output_file: Path
    ) -> None:
        """Create a CSV table"""
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(columns)

            # Write data rows
            rows = self._extract_table_data(data, columns)
            writer.writerows(rows)

    def _create_latex_table(
        self, data: Dict[str, Any], columns: List[str], output_file: Path
    ) -> None:
        """Create a LaTeX table"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\\begin{table}[h]\n")
            f.write("\\centering\n")
            f.write("\\begin{tabular}{|" + "|".join(["c"] * len(columns)) + "|}\n")
            f.write("\\hline\n")

            # Write header
            f.write(" & ".join(columns) + " \\\\\n")
            f.write("\\hline\n")

            # Write data rows
            rows = self._extract_table_data(data, columns)
            for row in rows:
                f.write(" & ".join(str(cell) for cell in row) + " \\\\\n")

            f.write("\\hline\n")
            f.write("\\end{tabular}\n")
            f.write("\\caption{Evaluation Results}\n")
            f.write("\\end{table}\n")

    def _create_html_table(
        self, data: Dict[str, Any], columns: List[str], output_file: Path
    ) -> None:
        """Create an HTML table"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('<table border="1">\n')

            # Write header
            f.write("<thead>\n<tr>\n")
            for column in columns:
                f.write(f"<th>{column}</th>\n")
            f.write("</tr>\n</thead>\n")

            # Write data rows
            f.write("<tbody>\n")
            rows = self._extract_table_data(data, columns)
            for row in rows:
                f.write("<tr>\n")
                for cell in row:
                    f.write(f"<td>{cell}</td>\n")
                f.write("</tr>\n")
            f.write("</tbody>\n")

            f.write("</table>\n")

    def _extract_table_data(
        self, data: Dict[str, Any], columns: List[str]
    ) -> List[List[str]]:
        """Extract data for table from the data structure"""
        rows = []

        try:
            if isinstance(data, dict):
                if "test_results" in data:
                    # Pytest results format
                    for test in data["test_results"]:
                        row = []
                        for column in columns:
                            if column == "test_name":
                                row.append(test.get("name", "Unknown"))
                            elif column == "status":
                                row.append(test.get("status", "Unknown"))
                            elif column == "duration":
                                duration = test.get("duration")
                                row.append(
                                    f"{duration:.2f}s"
                                    if duration is not None
                                    else "N/A"
                                )
                            else:
                                row.append(str(test.get(column, "")))
                        rows.append(row)

                elif "results" in data:
                    # Step results format
                    results = data["results"]
                    if isinstance(results, dict):
                        for key, value in results.items():
                            row = []
                            for column in columns:
                                if column == "step":
                                    row.append(key)
                                elif column == "value":
                                    row.append(str(value))
                                else:
                                    row.append(
                                        str(value.get(column, ""))
                                        if isinstance(value, dict)
                                        else str(value)
                                    )
                            rows.append(row)

                else:
                    # Generic dict format - handle step data
                    for step_name, step_data in data.items():
                        if isinstance(step_data, dict) and "results" in step_data:
                            results = step_data["results"]
                            if isinstance(results, dict):
                                for key, value in results.items():
                                    row = []
                                    for column in columns:
                                        if column == "step":
                                            row.append(f"{step_name}.{key}")
                                        elif column == "status":
                                            row.append(
                                                "Success"
                                                if results.get("success", False)
                                                else "Failed"
                                            )
                                        elif column == "duration":
                                            row.append(
                                                "N/A"
                                            )  # Duration not available in this format
                                        elif column == "details":
                                            row.append(str(value))
                                        else:
                                            row.append(
                                                str(value.get(column, ""))
                                                if isinstance(value, dict)
                                                else str(value)
                                            )
                                    rows.append(row)
                            else:
                                # Simple step result
                                row = []
                                for column in columns:
                                    if column == "step":
                                        row.append(step_name)
                                    elif column == "status":
                                        row.append(
                                            "Success"
                                            if results.get("success", False)
                                            else "Failed"
                                        )
                                    elif column == "duration":
                                        row.append("N/A")
                                    elif column == "details":
                                        row.append(str(results))
                                    else:
                                        row.append(
                                            str(results.get(column, ""))
                                            if isinstance(results, dict)
                                            else str(results)
                                        )
                                rows.append(row)
                        else:
                            # Direct key-value pairs
                            row = []
                            for column in columns:
                                if column == "step":
                                    row.append(step_name)
                                elif column == "value":
                                    row.append(str(step_data))
                                else:
                                    row.append(
                                        str(step_data.get(column, ""))
                                        if isinstance(step_data, dict)
                                        else str(step_data)
                                    )
                            rows.append(row)

            elif isinstance(data, list):
                # List format
                for i, item in enumerate(data):
                    row = []
                    for column in columns:
                        if column == "index":
                            row.append(str(i))
                        elif column == "value":
                            row.append(str(item))
                        else:
                            row.append(
                                str(item.get(column, ""))
                                if isinstance(item, dict)
                                else str(item)
                            )
                    rows.append(row)

            return rows

        except Exception as e:
            print(f"Error extracting table data: {e}")
            return []

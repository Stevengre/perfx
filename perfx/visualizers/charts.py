#!/usr/bin/env python3
"""
Chart generator for Perfx
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np


class ChartGenerator:
    """Generator for creating various types of charts"""

    def __init__(self):
        # Set matplotlib style
        plt.style.use("default")
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["font.size"] = 10

    def create_line_chart(
        self,
        data: Dict[str, Any],
        x_axis: str,
        y_axis: str,
        title: str,
        output_file: Path,
    ) -> None:
        """Create a line chart"""
        try:
            # Extract data for plotting
            x_values, y_values = self._extract_plot_data(data, x_axis, y_axis)

            if not x_values or not y_values:
                return

            plt.figure()
            plt.plot(x_values, y_values, marker="o", linewidth=2, markersize=6)
            plt.title(title)
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save chart
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            print(f"Error creating line chart: {e}")

    def create_bar_chart(
        self,
        data: Dict[str, Any],
        x_axis: str,
        y_axis: str,
        title: str,
        output_file: Path,
    ) -> None:
        """Create a bar chart"""
        try:
            # Extract data for plotting
            x_values, y_values = self._extract_plot_data(data, x_axis, y_axis)

            if not x_values or not y_values:
                return

            plt.figure()
            bars = plt.bar(
                x_values, y_values, alpha=0.7, color="skyblue", edgecolor="navy"
            )
            plt.title(title)
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
            plt.grid(True, alpha=0.3, axis="y")
            plt.xticks(rotation=45)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.2f}",
                    ha="center",
                    va="bottom",
                )

            plt.tight_layout()

            # Save chart
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            print(f"Error creating bar chart: {e}")

    def create_scatter_plot(
        self,
        data: Dict[str, Any],
        x_axis: str,
        y_axis: str,
        title: str,
        output_file: Path,
    ) -> None:
        """Create a scatter plot"""
        try:
            # Extract data for plotting
            x_values, y_values = self._extract_plot_data(data, x_axis, y_axis)

            if not x_values or not y_values:
                return

            plt.figure()
            plt.scatter(x_values, y_values, alpha=0.6, s=50)
            plt.title(title)
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save chart
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            print(f"Error creating scatter plot: {e}")

    def create_histogram(
        self,
        data: Dict[str, Any],
        x_axis: str,
        title: str,
        output_file: Path,
        bins: int = 20,
    ) -> None:
        """Create a histogram"""
        try:
            # Extract data for plotting
            x_values, _ = self._extract_plot_data(data, x_axis, None)

            if not x_values:
                return

            plt.figure()
            plt.hist(
                x_values, bins=bins, alpha=0.7, color="lightcoral", edgecolor="black"
            )
            plt.title(title)
            plt.xlabel(x_axis)
            plt.ylabel("Frequency")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save chart
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()

        except Exception as e:
            print(f"Error creating histogram: {e}")

    def _extract_plot_data(
        self, data: Dict[str, Any], x_axis: str, y_axis: str
    ) -> tuple:
        """Extract x and y values from data for plotting"""
        x_values = []
        y_values = []

        try:
            # Handle different data structures
            if isinstance(data, dict):
                if "test_results" in data:
                    # Pytest results format
                    for test in data["test_results"]:
                        if x_axis == "test_name":
                            x_values.append(test.get("name", "Unknown"))
                        elif x_axis == "status":
                            x_values.append(test.get("status", "Unknown"))

                        if y_axis == "duration":
                            duration = test.get("duration")
                            if duration is not None:
                                y_values.append(duration)
                        elif y_axis == "status_count":
                            # Count by status
                            pass  # Would need to implement counting logic

                elif "results" in data:
                    # Step results format
                    results = data["results"]
                    if isinstance(results, dict):
                        for key, value in results.items():
                            x_values.append(key)
                            if isinstance(value, (int, float)):
                                y_values.append(value)
                            else:
                                y_values.append(0)

                else:
                    # Generic dict format
                    for key, value in data.items():
                        x_values.append(str(key))
                        if isinstance(value, (int, float)):
                            y_values.append(value)
                        else:
                            y_values.append(0)

            elif isinstance(data, list):
                # List format
                for i, item in enumerate(data):
                    x_values.append(str(i))
                    if isinstance(item, (int, float)):
                        y_values.append(item)
                    else:
                        y_values.append(0)

            # Ensure we have matching lengths
            if len(x_values) != len(y_values):
                min_len = min(len(x_values), len(y_values))
                x_values = x_values[:min_len]
                y_values = y_values[:min_len]

            return x_values, y_values

        except Exception as e:
            print(f"Error extracting plot data: {e}")
            return [], []

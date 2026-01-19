"""
Tool Definitions Module
Defines tools for Azure OpenAI function calling to enable dashboard visualizations.
"""
from typing import Any


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "show_chart",
            "description": "Display a chart or visualization in the dashboard. Use this when the user asks to see data visually, wants a graph, or requests data comparison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["line", "bar", "pie", "area"],
                        "description": "The type of chart to display"
                    },
                    "title": {
                        "type": "string",
                        "description": "Chart title"
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["label", "value"]
                        },
                        "description": "Data points for the chart"
                    }
                },
                "required": ["chart_type", "title", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_metrics",
            "description": "Update the metrics panel with key performance indicators. Use this when the user asks about specific numbers, KPIs, or wants to see summary statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "The metric name/label"
                                },
                                "value": {
                                    "type": "number",
                                    "description": "The metric value"
                                },
                                "unit": {
                                    "type": "string",
                                    "description": "The unit of measurement (e.g., '$', '%', 'users')"
                                }
                            },
                            "required": ["label", "value", "unit"]
                        },
                        "description": "Array of metrics to display"
                    }
                },
                "required": ["metrics"]
            }
        }
    }
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool by name with the given arguments.

    For visualization tools, the "execution" is simply returning the arguments
    to be rendered by the frontend. The backend doesn't need to process
    the data - it just passes it through to the frontend.

    Args:
        name: The tool name (e.g., "show_chart", "show_metrics")
        arguments: The tool arguments as parsed from the LLM response

    Returns:
        The tool result to be sent to the frontend
    """
    if name == "show_chart":
        return {
            "chart_type": arguments.get("chart_type"),
            "title": arguments.get("title"),
            "data": arguments.get("data", [])
        }
    elif name == "show_metrics":
        return {
            "metrics": arguments.get("metrics", [])
        }
    else:
        # Unknown tool - return error
        return {"error": f"Unknown tool: {name}"}

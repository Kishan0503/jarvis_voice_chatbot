import json
from datetime import datetime
from typing import Dict, Any

# Import Tool and FunctionDeclaration types from google.generativeai
from google.generativeai.types import Tool, FunctionDeclaration

def get_current_datetime() -> Dict[str, Any]:
    """
    Gets the current date, time, day of the week, month, and year.
    """
    now = datetime.now()
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.year
    }

# Define the FunctionDeclaration for the calendar tool
calendar_tool_declaration = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="get_current_datetime",
            description="Gets the current date, time, day of the week, month, and year.",
            parameters={
                "type": "object",
                "properties": {}, # This function takes no parameters
                "required": [],
            },
        )
    ]
)

# Define a dictionary mapping tool names to their actual Python functions
tool_functions = {
    "get_current_datetime": get_current_datetime
}
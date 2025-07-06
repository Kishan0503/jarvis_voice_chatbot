import json
from typing import Dict, Any

# Import API client
from googleapiclient.discovery import build

# Import app_config for API keys
from config import app_config

# Import Tool and FunctionDeclaration types from google.generativeai
from google.generativeai.types import Tool, FunctionDeclaration

# Retrieve Google Custom Search API Key and CX
GOOGLE_CSE_API_KEY = app_config.GOOGLE_CSE_API_KEY
GOOGLE_CSE_CX = app_config.GOOGLE_CSE_CX

# Initialize the Custom Search service
# We build this once to reuse the service object
try:
    search_service = build("customsearch", "v1", developerKey=GOOGLE_CSE_API_KEY)
except Exception as e:
    print(f"Error initializing Google Custom Search service: {e}")
    search_service = None # Set to None if initialization fails

def google_search(query: str) -> Dict[str, Any]:
    """
    Performs a Google search and returns a summary of the top results.

    Args:
        query: The search query string.
    """
    if not search_service:
        return {"error": "Google Custom Search service not initialized. Check API key and network."}

    try:
        # Perform the search
        # num=5 fetches the top 5 results
        # cx is the Search Engine ID
        result = search_service.cse().list(q=query, cx=GOOGLE_CSE_CX, num=5).execute()

        search_results = []
        if 'items' in result:
            for item in result['items']:
                search_results.append({
                    "title": item.get('title'),
                    "link": item.get('link'),
                    "snippet": item.get('snippet')
                })
            return {"results": search_results}
        else:
            return {"results": [], "message": "No search results found."}

    except Exception as e:
        print(f"Error during Google search for query '{query}': {e}")
        return {"error": f"Failed to perform search: {str(e)}"}

# Define the FunctionDeclaration for the Google Search tool
search_tool_declaration = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="google_search",
            description="Performs a Google search to find information on the internet. Use this for general knowledge questions, current events, or anything requiring external information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query string."},
                },
                "required": ["query"],
            },
        )
    ]
)

# Define a dictionary mapping tool names to their actual Python functions
tool_functions = {
    "google_search": google_search
}
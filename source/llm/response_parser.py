"""Parser for structured LLM responses."""

import json
import re
from typing import Any, Dict, Optional


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse a JSON response from the LLM.

    Handles cases where the response might contain markdown code blocks or extra text.

    Args:
        response: The raw response string from the LLM

    Returns:
        Parsed JSON as dictionary. Returns a default structure if parsing fails.
    """
    # Try to extract JSON from markdown code blocks first
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the response (handles cases with extra text)
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # If no JSON found, try parsing the entire response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Return a default structure if all parsing fails
    return get_default_response(error="Failed to parse LLM response as JSON")


def get_default_response(error: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a default response structure.

    Args:
        error: Optional error message to include

    Returns:
        Default response dictionary
    """
    return {
        "overall_score": 0,
        "overall_feedback": error or "Unable to parse response",
        "criteria_scores": {
            "separation_of_concerns": 0,
            "documentation": 0,
            "logic_clarity": 0,
            "understandability": 0,
            "efficiency": 0,
            "error_handling": 0,
            "testability": 0,
            "reusability": 0,
            "code_consistency": 0,
            "dependency_management": 0,
            "security_awareness": 0,
            "side_effects": 0,
            "scalability": 0,
            "resource_management": 0,
            "encapsulation": 0,
            "readability": 0,
        },
        "criteria_feedback": {
            "separation_of_concerns": None,
            "documentation": None,
            "logic_clarity": None,
            "understandability": None,
            "efficiency": None,
            "error_handling": None,
            "testability": None,
            "reusability": None,
            "code_consistency": None,
            "dependency_management": None,
            "security_awareness": None,
            "side_effects": None,
            "scalability": None,
            "resource_management": None,
            "encapsulation": None,
            "readability": None,
        },
        "suggestions": [],
        "strengths": [],
    }


def format_structured_response(response_dict: Dict[str, Any]) -> str:
    """
    Format a structured response dictionary for display.

    Args:
        response_dict: The parsed response dictionary

    Returns:
        Formatted string for display
    """
    output = []

    # Overall score and feedback
    output.append(f"Overall Score: {response_dict.get('overall_score', 0)}/10")
    output.append(f"Feedback: {response_dict.get('overall_feedback', 'N/A')}")
    output.append("")

    # Criteria scores
    output.append("=== Criteria Scores ===")
    criteria_scores = response_dict.get("criteria_scores", {})
    for criterion, score in criteria_scores.items():
        formatted_criterion = criterion.replace("_", " ").title()
        output.append(f"{formatted_criterion}: {score}/10")

    output.append("")

    # Criteria feedback
    output.append("=== Detailed Feedback ===")
    criteria_feedback = response_dict.get("criteria_feedback", {})
    for criterion, feedback in criteria_feedback.items():
        if feedback:
            formatted_criterion = criterion.replace("_", " ").title()
            output.append(f"{formatted_criterion}: {feedback}")

    output.append("")

    # Strengths
    strengths = response_dict.get("strengths", [])
    if strengths:
        output.append("=== Strengths ===")
        for strength in strengths:
            output.append(f"• {strength}")
        output.append("")

    # Suggestions
    suggestions = response_dict.get("suggestions", [])
    if suggestions:
        output.append("=== Improvement Suggestions ===")
        for suggestion in suggestions:
            output.append(f"• {suggestion}")

    return "\n".join(output)

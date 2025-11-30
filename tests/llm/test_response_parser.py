"""Unit tests for response_parser module."""

import json

import pytest

from source.llm.response_parser import format_structured_response, get_default_response, parse_json_response


class TestParseJsonResponse:
    """Tests for parse_json_response function."""

    def test_parse_valid_raw_json(self):
        """Test parsing valid raw JSON."""
        response = json.dumps(
            {
                "overall_score": 8,
                "overall_feedback": "Good method",
                "criteria_scores": {
                    k: 7
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "criteria_feedback": {
                    k: None
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "suggestions": ["Improve efficiency"],
                "strengths": ["Good structure"],
            }
        )

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 8
        assert parsed["overall_feedback"] == "Good method"
        assert len(parsed["criteria_scores"]) == 16
        assert parsed["suggestions"] == ["Improve efficiency"]
        assert parsed["strengths"] == ["Good structure"]

    def test_parse_markdown_wrapped_json(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """Here's the analysis:

```json
{
    "overall_score": 7,
    "overall_feedback": "Decent code",
    "criteria_scores": {
        "separation_of_concerns": 7,
        "documentation": 6,
        "logic_clarity": 7,
        "understandability": 7,
        "efficiency": 5,
        "error_handling": 6,
        "testability": 7,
        "reusability": 6,
        "code_consistency": 8,
        "dependency_management": 7,
        "security_awareness": 6,
        "side_effects": 7,
        "scalability": 4,
        "resource_management": 6,
        "encapsulation": 7,
        "readability": 8
    },
    "criteria_feedback": {},
    "suggestions": [],
    "strengths": []
}
```
"""

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 7
        assert parsed["overall_feedback"] == "Decent code"
        assert len(parsed["criteria_scores"]) == 16

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with surrounding text."""
        response = """The analysis shows:

{
    "overall_score": 9,
    "overall_feedback": "Excellent",
    "criteria_scores": {
        "separation_of_concerns": 9,
        "documentation": 9,
        "logic_clarity": 9,
        "understandability": 9,
        "efficiency": 8,
        "error_handling": 9,
        "testability": 9,
        "reusability": 9,
        "code_consistency": 9,
        "dependency_management": 9,
        "security_awareness": 8,
        "side_effects": 9,
        "scalability": 8,
        "resource_management": 9,
        "encapsulation": 9,
        "readability": 9
    },
    "criteria_feedback": {},
    "suggestions": [],
    "strengths": []
}

This is a great method!"""

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 9
        assert len(parsed["criteria_scores"]) == 16

    def test_parse_invalid_json_returns_default(self):
        """Test that invalid JSON returns default response."""
        response = "This is not JSON at all: {invalid}"

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 0
        assert parsed["overall_feedback"].startswith("Failed to parse")
        assert len(parsed["criteria_scores"]) == 16
        assert all(v == 0 for v in parsed["criteria_scores"].values())

    def test_parse_with_nested_json(self):
        """Test parsing with deeply nested JSON structures."""
        response = json.dumps(
            {
                "overall_score": 8,
                "overall_feedback": "Good",
                "criteria_scores": {
                    k: 8
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "criteria_feedback": {
                    "separation_of_concerns": "Good separation",
                    "documentation": "Well documented",
                    "logic_clarity": None,
                    "understandability": "Clear names",
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
                "suggestions": ["Add type hints", "Optimize loops"],
                "strengths": ["Good structure", "Clear intent"],
            }
        )

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 8
        assert parsed["criteria_feedback"]["separation_of_concerns"] == "Good separation"
        assert len(parsed["suggestions"]) == 2
        assert len(parsed["strengths"]) == 2


class TestFormatStructuredResponse:
    """Tests for format_structured_response function."""

    def test_format_complete_response(self):
        """Test formatting a complete response."""
        response_dict = {
            "overall_score": 8,
            "overall_feedback": "Well-written code",
            "criteria_scores": {
                "separation_of_concerns": 9,
                "documentation": 8,
                "logic_clarity": 8,
                "understandability": 8,
                "efficiency": 7,
                "error_handling": 7,
                "testability": 8,
                "reusability": 7,
                "code_consistency": 9,
                "dependency_management": 8,
                "security_awareness": 7,
                "side_effects": 8,
                "scalability": 6,
                "resource_management": 7,
                "encapsulation": 8,
                "readability": 9,
            },
            "criteria_feedback": {
                "separation_of_concerns": "Good single responsibility",
                "documentation": None,
                "logic_clarity": None,
                "understandability": None,
                "efficiency": "Consider optimization",
                "error_handling": None,
                "testability": None,
                "reusability": None,
                "code_consistency": None,
                "dependency_management": None,
                "security_awareness": None,
                "side_effects": None,
                "scalability": "May not scale",
                "resource_management": None,
                "encapsulation": None,
                "readability": None,
            },
            "suggestions": ["Add type hints", "Improve efficiency"],
            "strengths": ["Well-structured", "Good documentation"],
        }

        formatted = format_structured_response(response_dict)

        # Check key components are present
        assert "Overall Score: 8/10" in formatted
        assert "Well-written code" in formatted
        assert "=== Criteria Scores ===" in formatted
        assert "Separation Of Concerns: 9/10" in formatted
        assert "=== Detailed Feedback ===" in formatted
        assert "Good single responsibility" in formatted
        assert "=== Strengths ===" in formatted
        assert "Well-structured" in formatted
        assert "=== Improvement Suggestions ===" in formatted
        assert "Add type hints" in formatted

    def test_format_minimal_response(self):
        """Test formatting a minimal response."""
        response_dict = {
            "overall_score": 5,
            "overall_feedback": "Needs improvement",
            "criteria_scores": {
                k: 5
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "criteria_feedback": {
                k: None
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "suggestions": [],
            "strengths": [],
        }

        formatted = format_structured_response(response_dict)

        assert "Overall Score: 5/10" in formatted
        assert "Needs improvement" in formatted
        assert "Criteria Scores" in formatted

    def test_format_with_empty_lists(self):
        """Test formatting with empty suggestions and strengths."""
        response_dict = get_default_response()
        response_dict["overall_score"] = 6

        formatted = format_structured_response(response_dict)

        assert "Overall Score: 6/10" in formatted
        # Empty lists shouldn't cause errors

    def test_format_all_criteria_present(self):
        """Test that all 16 criteria are formatted."""
        response_dict = {
            "overall_score": 7,
            "overall_feedback": "Test",
            "criteria_scores": {
                k: 7
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "criteria_feedback": {
                k: None
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "suggestions": [],
            "strengths": [],
        }

        formatted = format_structured_response(response_dict)

        # Check that all 16 criteria are mentioned
        criteria_names = [
            "Separation Of Concerns",
            "Documentation",
            "Logic Clarity",
            "Understandability",
            "Efficiency",
            "Error Handling",
            "Testability",
            "Reusability",
            "Code Consistency",
            "Dependency Management",
            "Security Awareness",
            "Side Effects",
            "Scalability",
            "Resource Management",
            "Encapsulation",
            "Readability",
        ]

        for criterion in criteria_names:
            assert criterion in formatted


class TestGetDefaultResponse:
    """Tests for get_default_response function."""

    def test_default_response_structure(self):
        """Test that default response has correct structure."""
        default = get_default_response()

        assert "overall_score" in default
        assert "overall_feedback" in default
        assert "criteria_scores" in default
        assert "criteria_feedback" in default
        assert "suggestions" in default
        assert "strengths" in default

    def test_default_response_values(self):
        """Test default response has expected values."""
        default = get_default_response()

        assert default["overall_score"] == 0
        assert len(default["criteria_scores"]) == 16
        assert len(default["criteria_feedback"]) == 16
        assert default["suggestions"] == []
        assert default["strengths"] == []
        assert all(v == 0 for v in default["criteria_scores"].values())
        assert all(v is None for v in default["criteria_feedback"].values())

    def test_default_response_with_error(self):
        """Test default response with error message."""
        error_msg = "Test error"
        default = get_default_response(error=error_msg)

        assert error_msg in default["overall_feedback"]

    def test_default_response_all_criteria_keys(self):
        """Test default response has all 16 criteria."""
        criteria = [
            "separation_of_concerns",
            "documentation",
            "logic_clarity",
            "understandability",
            "efficiency",
            "error_handling",
            "testability",
            "reusability",
            "code_consistency",
            "dependency_management",
            "security_awareness",
            "side_effects",
            "scalability",
            "resource_management",
            "encapsulation",
            "readability",
        ]

        default = get_default_response()

        for criterion in criteria:
            assert criterion in default["criteria_scores"]
            assert criterion in default["criteria_feedback"]


class TestRoundTripConversion:
    """Tests for round-trip conversion (parse -> format -> parse)."""

    def test_round_trip_preserves_data(self):
        """Test that parse -> format -> parse preserves essential data."""
        original_json = json.dumps(
            {
                "overall_score": 8,
                "overall_feedback": "Good",
                "criteria_scores": {
                    k: 8
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "criteria_feedback": {
                    k: None
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "suggestions": ["Test suggestion"],
                "strengths": ["Test strength"],
            }
        )

        # Parse
        parsed = parse_json_response(original_json)

        # Format
        formatted = format_structured_response(parsed)

        # Verify key data is in formatted output
        assert "8/10" in formatted
        assert "Good" in formatted
        assert "Test suggestion" in formatted
        assert "Test strength" in formatted


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        parsed = parse_json_response("")

        assert parsed["overall_score"] == 0
        assert "Failed to parse" in parsed["overall_feedback"]

    def test_parse_null_values(self):
        """Test parsing with null values in feedback."""
        response = json.dumps(
            {
                "overall_score": 5,
                "overall_feedback": None,
                "criteria_scores": {
                    k: 5
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "criteria_feedback": {
                    k: None
                    for k in [
                        "separation_of_concerns",
                        "documentation",
                        "logic_clarity",
                        "understandability",
                        "efficiency",
                        "error_handling",
                        "testability",
                        "reusability",
                        "code_consistency",
                        "dependency_management",
                        "security_awareness",
                        "side_effects",
                        "scalability",
                        "resource_management",
                        "encapsulation",
                        "readability",
                    ]
                },
                "suggestions": [],
                "strengths": [],
            }
        )

        parsed = parse_json_response(response)

        assert parsed["overall_score"] == 5

    def test_format_with_special_characters(self):
        """Test formatting with special characters in feedback."""
        response_dict = {
            "overall_score": 8,
            "overall_feedback": "Great! 🚀 Well done.",
            "criteria_scores": {
                k: 8
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "criteria_feedback": {
                k: None
                for k in [
                    "separation_of_concerns",
                    "documentation",
                    "logic_clarity",
                    "understandability",
                    "efficiency",
                    "error_handling",
                    "testability",
                    "reusability",
                    "code_consistency",
                    "dependency_management",
                    "security_awareness",
                    "side_effects",
                    "scalability",
                    "resource_management",
                    "encapsulation",
                    "readability",
                ]
            },
            "suggestions": ["Use \"type hints\"", "Handle edge cases"],
            "strengths": ["Code is 'clean'"],
        }

        formatted = format_structured_response(response_dict)

        assert "Great" in formatted
        assert "type hints" in formatted

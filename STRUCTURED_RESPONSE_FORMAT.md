# Structured Response Format

## Overview

Codewise now uses structured JSON responses from the LLM instead of free-form text. This provides:
- **Better data organization** - Easy to parse and analyze
- **Programmatic access** - Query specific criteria scores
- **Better caching** - Structured data stored persistently
- **Enhanced UI display** - Formatted for readability

## JSON Response Structure

### Root Object

```json
{
  "overall_score": 8,
  "overall_feedback": "Well-structured method with clear documentation...",
  "criteria_scores": { ... },
  "criteria_feedback": { ... },
  "suggestions": [ ... ],
  "strengths": [ ... ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | Integer (1-10) | Overall quality score for the method |
| `overall_feedback` | String | General assessment and summary |
| `criteria_scores` | Object | Scores for each of 16 criteria |
| `criteria_feedback` | Object | Detailed feedback for each criterion |
| `suggestions` | Array | List of improvement suggestions |
| `strengths` | Array | List of method strengths |

## Criteria Scores

The `criteria_scores` object contains individual scores (1-10) for:

```json
{
  "criteria_scores": {
    "separation_of_concerns": 8,
    "documentation": 9,
    "logic_clarity": 7,
    "understandability": 8,
    "efficiency": 6,
    "error_handling": 7,
    "testability": 8,
    "reusability": 7,
    "code_consistency": 9,
    "dependency_management": 8,
    "security_awareness": 6,
    "side_effects": 8,
    "scalability": 5,
    "resource_management": 7,
    "encapsulation": 8,
    "readability": 9
  }
}
```

### Criteria Definitions

1. **Separation of Concerns** - Does the method follow single-responsibility principle?
2. **Documentation** - Is it well-documented with clear docstrings?
3. **Logic Clarity** - Are there logical issues or potential bugs?
4. **Understandability** - Is code straightforward and readable?
5. **Efficiency** - Is it optimized for performance and memory?
6. **Error Handling** - Does it handle edge cases gracefully?
7. **Testability** - Is it easy to unit test?
8. **Reusability** - Is it modular and flexible?
9. **Code Consistency** - Does it follow PEP 8 conventions?
10. **Dependency Management** - Does it avoid unnecessary dependencies?
11. **Security Awareness** - Does it avoid common security issues?
12. **Side Effects** - Are unintended side effects minimized?
13. **Scalability** - Can it handle high-traffic scenarios?
14. **Resource Management** - Does it handle resources safely?
15. **Encapsulation** - Does it use appropriate access controls?
16. **Readability** - Is complex logic broken down clearly?

## Criteria Feedback

The `criteria_feedback` object contains string feedback (or null) for each criterion:

```json
{
  "criteria_feedback": {
    "separation_of_concerns": "Method does one thing well - good use of helper functions",
    "documentation": null,
    "logic_clarity": "Consider adding comments for the complex loop logic",
    "understandability": "Variable names are clear and descriptive",
    ...
  }
}
```

## Suggestions and Strengths

```json
{
  "suggestions": [
    "Add type hints for better IDE support and documentation",
    "Consider caching repeated calculations",
    "Add unit tests for edge cases"
  ],
  "strengths": [
    "Excellent separation of concerns",
    "Well-documented with examples",
    "Efficient algorithm implementation"
  ]
}
```

## Complete Example

```json
{
  "overall_score": 8,
  "overall_feedback": "Well-implemented method with good separation of concerns and documentation. Could improve efficiency and error handling.",
  "criteria_scores": {
    "separation_of_concerns": 9,
    "documentation": 9,
    "logic_clarity": 8,
    "understandability": 8,
    "efficiency": 6,
    "error_handling": 7,
    "testability": 8,
    "reusability": 8,
    "code_consistency": 9,
    "dependency_management": 8,
    "security_awareness": 7,
    "side_effects": 8,
    "scalability": 5,
    "resource_management": 7,
    "encapsulation": 8,
    "readability": 9
  },
  "criteria_feedback": {
    "separation_of_concerns": "Method has clear responsibility",
    "documentation": "Excellent docstring and inline comments",
    "logic_clarity": "Logic is mostly clear, minor improvements possible",
    "understandability": "Variable names follow conventions",
    "efficiency": "Consider using set instead of list for O(1) lookups",
    "error_handling": "Add validation for null inputs",
    "testability": "Good isolation for unit testing",
    "reusability": "Could be more generic for other data types",
    "code_consistency": "Follows PEP 8 strictly",
    "dependency_management": "No unnecessary imports",
    "security_awareness": "Handles user input safely",
    "side_effects": "Pure function with no side effects",
    "scalability": "May have issues with very large datasets",
    "resource_management": "Properly manages file handles",
    "encapsulation": "Good use of private methods",
    "readability": "Very readable code structure"
  },
  "suggestions": [
    "Use set instead of list for O(1) membership testing",
    "Add input validation for edge cases",
    "Consider adding caching for repeated calls",
    "Add type hints (Python 3.9+)"
  ],
  "strengths": [
    "Clear and focused method",
    "Excellent documentation",
    "Follows Python best practices",
    "Well-named variables and functions",
    "No unnecessary side effects"
  ]
}
```

## Cached Response Storage

When results are cached, the structure is:

```json
{
  "timestamp": "2025-11-30T13:26:45.123456",
  "analysis_mode": "entire_project",
  "root_directory": "/path/to/project",
  "file_path": null,
  "metadata": {
    "method_count": 42,
    "file_count": 15
  },
  "results": [
    {
      "method_name": "initialize_memory",
      "file_path": "/path/to/memori/core/memory.py",
      "raw_response": "{ ... original JSON string ... }",
      "structured_response": { ... parsed JSON object ... }
    },
    ...
  ]
}
```

## Parsing Response

The `response_parser.py` module handles parsing:

```python
from source.llm.response_parser import parse_json_response, format_structured_response

# Parse raw LLM response
raw_response = "{ ... }"
structured = parse_json_response(raw_response)

# Access specific data
overall_score = structured["overall_score"]
documentation_score = structured["criteria_scores"]["documentation"]
suggestions = structured["suggestions"]

# Format for display
display_text = format_structured_response(structured)
```

## Display Formatting

The `format_structured_response()` function produces human-readable output:

```
Overall Score: 8/10
Feedback: Well-implemented method...

=== Criteria Scores ===
Separation Of Concerns: 9/10
Documentation: 9/10
Logic Clarity: 8/10
...

=== Detailed Feedback ===
Separation Of Concerns: Method has clear responsibility
Documentation: Excellent docstring...
...

=== Strengths ===
• Clear and focused method
• Excellent documentation
...

=== Improvement Suggestions ===
• Use set instead of list
• Add input validation
...
```

## Migration from Old Format

Old cache format (raw responses only):
```json
{
  "method_name": "foo",
  "api_response": "Free-form text response..."
}
```

New format with structured data:
```json
{
  "method_name": "foo",
  "raw_response": "Original JSON string...",
  "structured_response": { ... parsed JSON ... }
}
```

The UI handles both formats automatically for backward compatibility.

## Advantages of Structured Format

1. **Queryable** - Easy to extract specific criterion scores
2. **Aggregatable** - Can compute statistics across methods
3. **Machine-readable** - Perfect for further analysis
4. **Cacheable** - Persistent storage of parsed data
5. **Displayable** - Can format for different UIs (CLI, GUI, web)
6. **Comparable** - Easy to compare scores across methods

## Future Enhancements

Possible improvements:
- Trend analysis across analysis runs
- Comparative reports between methods
- Aggregate statistics by criterion
- Export to different formats (CSV, Excel, HTML)
- Integration with code review tools

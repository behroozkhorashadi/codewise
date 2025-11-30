# Structured JSON Responses Implementation

## Summary

The API responses from the LLM are now structured JSON instead of free-form text. This enables:
- Better data organization and parsing
- Easy querying of individual criteria scores
- Persistent structured storage in cache
- Improved UI display and formatting
- Foundation for advanced analytics

## Files Modified

### 1. `source/llm/code_eval_prompt.py`
**Change:** Updated the prompt template to request JSON output

**Details:**
- Added instructions for LLM to return ONLY valid JSON
- Defined JSON schema with:
  - `overall_score` (1-10)
  - `overall_feedback` (string)
  - `criteria_scores` (16 individual 1-10 scores)
  - `criteria_feedback` (detailed feedback per criterion)
  - `suggestions` (improvement list)
  - `strengths` (positive aspects list)

**Key instruction in prompt:**
```
IMPORTANT: Return your evaluation ONLY as valid JSON (no additional text or markdown).
```

### 2. `source/llm/response_parser.py` (NEW)
**Purpose:** Parse and format structured JSON responses

**Key Functions:**

#### `parse_json_response(response: str) -> Dict`
- Handles various response formats (raw JSON, markdown code blocks, etc.)
- Gracefully falls back to default structure if parsing fails
- Extracts JSON from markdown blocks if present
- Robust error handling

#### `get_default_response(error: str) -> Dict`
- Returns default response structure for parsing failures
- Includes all 16 criteria with zero scores
- Preserves error message for debugging

#### `format_structured_response(response_dict: Dict) -> str`
- Converts structured JSON to human-readable text
- Displays:
  - Overall score and feedback
  - All 16 criteria scores
  - Detailed feedback per criterion
  - Strengths and suggestions
- Perfect for UI display

### 3. `source/codewise_gui/codewise_ui_utils.py`
**Changes:**

#### Imports
Added:
```python
from source.llm.response_parser import parse_json_response, format_structured_response
```

#### `_process_methods()` (Line ~285)
**Before:**
```python
all_results.append({"method_name": method_name, "api_response": api_response})
self.api_response.emit(f"Analysis for method: {method_name}\n\n{api_response}")
```

**After:**
```python
parsed_response = parse_json_response(api_response)
all_results.append({
    "method_name": method_name,
    "raw_response": api_response,
    "structured_response": parsed_response,
})
formatted_display = f"Analysis for method: {method_name}\n\n{format_structured_response(parsed_response)}"
self.api_response.emit(formatted_display)
```

#### `_process_entire_project()` (Line ~375)
**Same changes as above for project-wide analysis**

#### Cache Loading (Line ~727)
**Added support for both old and new cache formats:**
```python
if "structured_response" in result:
    structured = result.get("structured_response", {})
    formatted_display = format_structured_response(structured)
else:
    # Fallback for old cache format
    api_response = result.get("api_response", "No response")
    formatted_display = api_response
```

## JSON Response Structure

### Example Response
```json
{
  "overall_score": 8,
  "overall_feedback": "Well-written method with good structure...",
  "criteria_scores": {
    "separation_of_concerns": 9,
    "documentation": 8,
    "logic_clarity": 8,
    "understandability": 8,
    "efficiency": 7,
    "error_handling": 7,
    "testability": 8,
    "reusability": 8,
    "code_consistency": 9,
    "dependency_management": 8,
    "security_awareness": 7,
    "side_effects": 8,
    "scalability": 6,
    "resource_management": 7,
    "encapsulation": 8,
    "readability": 9
  },
  "criteria_feedback": {
    "separation_of_concerns": "Good single responsibility",
    "documentation": null,
    "logic_clarity": "Clear logic flow",
    ...
  },
  "suggestions": [
    "Add type hints",
    "Improve error handling"
  ],
  "strengths": [
    "Well-documented",
    "Clear structure"
  ]
}
```

## Cached Output Format

Results now cached with both raw and structured responses:

```json
{
  "timestamp": "2025-11-30T13:26:45.123456",
  "results": [
    {
      "method_name": "method_1",
      "raw_response": "{...}",
      "structured_response": { ... }
    }
  ]
}
```

## UI Display

The `format_structured_response()` function produces:

```
Overall Score: 8/10
Feedback: Well-written method...

=== Criteria Scores ===
Separation Of Concerns: 9/10
Documentation: 8/10
...

=== Detailed Feedback ===
Separation Of Concerns: Good single responsibility
Logic Clarity: Clear logic flow
...

=== Strengths ===
• Well-documented
• Clear structure

=== Improvement Suggestions ===
• Add type hints
• Improve error handling
```

## Usage

### For Analysis
When you run analysis, the system will:
1. Send the new structured prompt to the LLM
2. Parse the JSON response
3. Display formatted text in the UI
4. Cache both raw JSON and parsed structure
5. Show results immediately (no re-parsing needed)

### For Cache Clearing
To force re-analysis with new prompt:
```bash
rm -rf .codewise_cache/
```

Or programmatically:
```python
from source.utils.output_storage import AnalysisOutputStorage
storage = AnalysisOutputStorage()
storage.delete_analysis_output(root_dir, file_path, mode)
```

### For Programmatic Access
```python
# Load cached analysis
data = storage.load_analysis_output(root_dir, file_path, mode)

# Access structured response
for result in data["results"]:
    structured = result["structured_response"]

    # Get specific scores
    overall = structured["overall_score"]
    doc_score = structured["criteria_scores"]["documentation"]
    suggestions = structured["suggestions"]
```

## Backward Compatibility

The system handles both:
- **Old format:** Plain text responses (from previous cache)
- **New format:** Structured JSON responses

When loading cache, if `structured_response` field exists, it uses that. Otherwise, it falls back to displaying `api_response` as plain text.

## Error Handling

If the LLM returns invalid JSON:
1. `parse_json_response()` attempts to extract JSON from markdown blocks
2. Falls back to parsing any JSON-like string in response
3. Returns default structure with error message if all parsing fails
4. App continues normally with degraded response structure

## Performance Impact

Minimal:
- JSON parsing is fast (100+ methods per second)
- Cached structured data eliminates re-parsing
- Storage size slightly increased (both raw + structured)
- UI rendering faster with pre-formatted text

## Testing

To test with new structured responses:
1. Clear cache: `rm -rf .codewise_cache/`
2. Run analysis on small project (2-3 methods)
3. Check `.codewise_cache/` for JSON structure
4. Re-run same analysis and verify cache loading
5. Check UI formatting of structured response

## Future Enhancements

The structured format enables:
- **Analytics** - Track criteria trends over time
- **Reports** - Generate detailed quality reports
- **Comparisons** - Compare methods/projects
- **Export** - CSV, Excel, HTML reports
- **API** - RESTful interface to cached results
- **Dashboard** - Visualize criteria scores

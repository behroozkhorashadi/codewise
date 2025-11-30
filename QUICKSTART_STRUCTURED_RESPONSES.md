# Quick Start: Structured JSON Responses

## What Changed?

API responses are now **structured JSON** instead of free-form text:
- ✓ All 16 criteria scores (1-10 each)
- ✓ Individual feedback per criterion
- ✓ Suggestions list
- ✓ Strengths list
- ✓ Cached for future use

## Getting Started

### 1. Clear Old Cache (One-time)
```bash
rm -rf .codewise_cache/
```

### 2. Run Analysis
```bash
python code_evaluator.py
```

1. Select "Entire Project Mode"
2. Choose the Memori directory: `/Users/peejakhorashadi/masters_project/sample_projects/memori`
3. Click Submit
4. Watch the analysis run (will take a while due to many methods)

### 3. View Results

**In the UI:**
- Left panel: Progress logs
- Right panel: Formatted analysis results showing:
  - Overall score
  - All 16 criteria with individual scores
  - Detailed feedback per criterion
  - List of strengths
  - List of improvement suggestions

**Example:**
```
Analysis for method: initialize_memory

Overall Score: 8/10
Feedback: Well-implemented method with good separation of concerns...

=== Criteria Scores ===
Separation Of Concerns: 9/10
Documentation: 9/10
Logic Clarity: 8/10
... (13 more)

=== Detailed Feedback ===
Separation Of Concerns: Method has clear single responsibility
Documentation: Excellent docstring with examples
... (14 more)

=== Strengths ===
• Clear and focused method
• Excellent documentation
• Follows Python best practices

=== Improvement Suggestions ===
• Add type hints
• Consider caching for repeated calls
```

## Cache System

### Automatic Caching
Results are automatically cached in `.codewise_cache/`:

```
.codewise_cache/
├── memori_entire_project.json      # From full project analysis
└── specific_file_single_file.json  # From single file analysis
```

### Reuse Cached Results
On the next run with same configuration:
1. System detects cached results
2. Dialog asks: "Use cached results or re-run?"
3. Click "Yes" to load instantly from cache
4. Click "No" to re-run with API

### Clear Specific Cache
```bash
# Remove all cache
rm -rf .codewise_cache/

# Or programmatically:
from source.utils.output_storage import AnalysisOutputStorage
storage = AnalysisOutputStorage()
storage.delete_analysis_output(root_dir, file_path, mode)
```

## For Developers

### Access Cached Results Programmatically

```python
from source.utils.output_storage import AnalysisOutputStorage

# Load cached analysis
storage = AnalysisOutputStorage()
data = storage.load_analysis_output(
    root_directory="/path/to/memori",
    file_path=None,
    analysis_mode="entire_project"
)

# Iterate through results
for result in data["results"]:
    method_name = result["method_name"]
    structured = result["structured_response"]

    # Access scores
    overall = structured["overall_score"]
    doc_score = structured["criteria_scores"]["documentation"]

    # Access feedback
    efficiency_feedback = structured["criteria_feedback"]["efficiency"]

    # Access lists
    suggestions = structured["suggestions"]
    strengths = structured["strengths"]

    # Process the data
    if overall < 7:
        print(f"Method {method_name} needs improvement")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
```

### Parse Raw Response

```python
from source.llm.response_parser import parse_json_response, format_structured_response

# Parse LLM response
raw_response = "{...JSON from LLM...}"
structured = parse_json_response(raw_response)

# Format for display
display_text = format_structured_response(structured)
print(display_text)

# Access data
score = structured["overall_score"]
criteria = structured["criteria_scores"]
feedback = structured["criteria_feedback"]
```

## JSON Structure

### Full Cache File
```json
{
  "timestamp": "2025-11-30T14:16:53.816966",
  "analysis_mode": "entire_project",
  "root_directory": "/path/to/memori",
  "file_path": null,
  "metadata": {
    "method_count": 42,
    "file_count": 12
  },
  "results": [
    {
      "method_name": "initialize_memory",
      "file_path": "/path/to/file.py",
      "raw_response": "{...original JSON string...}",
      "structured_response": {
        "overall_score": 8,
        "overall_feedback": "...",
        "criteria_scores": {
          "separation_of_concerns": 9,
          "documentation": 9,
          ... (14 more criteria)
        },
        "criteria_feedback": {
          "separation_of_concerns": "...",
          ... (15 more feedback items)
        },
        "suggestions": ["...", "..."],
        "strengths": ["...", "..."]
      }
    },
    { ...more methods... }
  ]
}
```

## Backward Compatibility

The system automatically handles:
- ✓ Old cache format (plain text responses)
- ✓ New cache format (structured JSON)
- ✓ Graceful fallback if parsing fails

No migration needed - old cache still works!

## Performance

- **Cache file size:** ~8 KB per 2 methods
- **Parsing speed:** 100+ methods per second
- **Load from cache:** Instant (no API calls)
- **Storage:** Efficient JSON format

## Troubleshooting

**Q: Results look different from before**
A: Yes! The new format shows structured data with 16 criteria instead of free-form text.

**Q: Want old text format back?**
A: Edit `source/llm/code_eval_prompt.py` to change the prompt back to free-form text.

**Q: Cache taking up too much space?**
A: Run `rm -rf .codewise_cache/` to clear old cache. You can re-analyze anytime.

**Q: How to export results?**
A: Load cached JSON and process programmatically to export as CSV, Excel, etc.

## Examples

### Find Methods with Low Scores
```python
storage = AnalysisOutputStorage()
data = storage.load_analysis_output(root_dir, None, "entire_project")

for result in data["results"]:
    score = result["structured_response"]["overall_score"]
    if score < 7:
        print(f"⚠️  {result['method_name']}: {score}/10")
```

### Generate Report
```python
data = storage.load_analysis_output(root_dir, None, "entire_project")

scores = []
for result in data["results"]:
    score = result["structured_response"]["overall_score"]
    scores.append(score)

avg = sum(scores) / len(scores)
print(f"Average score: {avg:.1f}/10")
print(f"Methods: {len(scores)}")
print(f"Range: {min(scores)}-{max(scores)}")
```

### Filter by Criterion
```python
data = storage.load_analysis_output(root_dir, None, "entire_project")

# Find methods with poor documentation
for result in data["results"]:
    structured = result["structured_response"]
    doc_score = structured["criteria_scores"]["documentation"]
    if doc_score < 8:
        print(f"{result['method_name']}: Doc score {doc_score}/10")
        feedback = structured["criteria_feedback"]["documentation"]
        print(f"  {feedback}")
```

## Next Steps

1. Run analysis on Memori project
2. Check `.codewise_cache/memori_entire_project.json`
3. Load cache and process results
4. Build reports or dashboards
5. Track improvements over time

## Support

See these files for more details:
- `STRUCTURED_RESPONSE_FORMAT.md` - Full format specification
- `STRUCTURED_RESPONSES_IMPLEMENTATION.md` - Implementation details
- `TESTING_SUMMARY.md` - Test results and verification

---

Ready to analyze! 🚀

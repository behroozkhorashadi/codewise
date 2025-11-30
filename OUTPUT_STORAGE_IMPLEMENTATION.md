# Output Storage and Caching Implementation

## Overview
This document describes the implementation of structured output storage and caching for Codewise analysis results. The system now saves analysis results in JSON format and checks for cached results before re-running analysis.

## Changes Made

### 1. New Output Storage Module
**File:** `source/utils/output_storage.py`

A new `AnalysisOutputStorage` class handles:
- **Saving analysis results** to structured JSON files with metadata
- **Loading cached results** from disk
- **Checking for existing results** before running analysis
- **Managing output directory** (`.codewise_cache/` by default)
- **Generating unique filenames** based on analysis mode and target

#### Key Features:
- Unique file naming based on root directory and file path
- Timestamp and metadata tracking for each analysis
- Supports both single-file and entire-project analysis modes
- Graceful error handling with fallback messages

#### Output Structure:
```json
{
  "timestamp": "2025-11-30T13:26:00.123456",
  "analysis_mode": "single_file",
  "root_directory": "/path/to/root",
  "file_path": "/path/to/file.py",
  "metadata": {
    "method_count": 5
  },
  "results": [
    {
      "method_name": "method_1",
      "api_response": "Analysis feedback from LLM..."
    }
  ]
}
```

### 2. Updated AnalysisWorker
**File:** `source/codewise_gui/codewise_ui_utils.py`

Modified the `AnalysisWorker` class to:
- Initialize `AnalysisOutputStorage` instance
- Save analysis results after processing completes
- Include metadata (method count, file count for projects)
- Handle save failures gracefully without interrupting analysis

Changes:
- Added `_output_storage` attribute
- Updated `_process_methods()` to save single-file results
- Updated `_process_entire_project()` to save project-wide results
- Progress messages indicate where results are saved

### 3. Updated CodewiseApp UI
**File:** `source/codewise_gui/codewise_ui_utils.py`

Enhanced the UI to:
- Check for cached results before analysis starts
- Prompt user with cache status dialog
- Allow user to skip re-running analysis if results exist
- Load and display cached results immediately
- Show cached result metadata (method count, timestamp)

#### User Flow:
1. User selects analysis parameters and clicks Submit
2. System checks if analysis output already exists
3. If cached results found:
   - Dialog shows: number of methods, timestamp
   - User can choose to load cached results or re-run
   - If loading cache: results displayed instantly
   - If re-running: normal analysis proceeds
4. Analysis results are saved for future use

### 4. Output Directory Structure
```
project_root/
├── .codewise_cache/              # Default cache directory
│   ├── memori_entire_project.json
│   ├── myfile_single_file.json
│   └── ...
└── ...
```

File naming convention:
- **Single file mode:** `{relative_path_with_underscores}_single_file.json`
- **Entire project mode:** `{directory_name}_entire_project.json`

## Usage

### Automatic Caching
Once implemented, all analysis results are automatically saved to `.codewise_cache/`:

```
Run analysis → Results saved → Next run checks cache → Load cached results (optional)
```

### Manual Cache Management
View all cached analyses:
```python
from source.utils.output_storage import AnalysisOutputStorage

storage = AnalysisOutputStorage()
cached = storage.get_all_cached_analyses()
for filename, info in cached.items():
    print(f"{filename}: {info['result_count']} methods")
```

Delete specific cached results:
```python
storage.delete_analysis_output(
    root_directory="/path/to/project",
    file_path="/path/to/file.py",
    analysis_mode="single_file"
)
```

## Benefits

1. **Performance:** Skip expensive API calls when results already exist
2. **Reliability:** Persistent storage of analysis results
3. **Transparency:** User awareness of cached vs. new results
4. **Flexibility:** Option to re-run analysis despite cached results
5. **Metadata Tracking:** Timestamp and method counts for auditing

## Technical Details

### Cache Key Generation
The system generates unique cache keys based on:
- `root_directory` - the analysis root path
- `file_path` - the specific file (for single-file mode)
- `analysis_mode` - "single_file" or "entire_project"

This ensures no cache collisions across different analysis configurations.

### JSON Serialization
- Results stored in readable JSON format
- All API responses preserved exactly as received
- Metadata included for auditing and management

### Thread Safety
- Output storage is thread-safe
- Used within the worker thread without synchronization issues
- File operations are atomic

## Future Enhancements

Possible improvements:
- Cache invalidation based on file modification times
- Batch export of analysis results
- Analysis history and comparison
- Cache size management and cleanup policies
- Integration with version control for change-based caching

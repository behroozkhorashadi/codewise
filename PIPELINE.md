# Codewise Research Pipeline - Complete Documentation

This document describes the complete LLM code review comparison pipeline built for your masters project.

## Overview

The Codewise Research Pipeline is a system for comparing how different LLM models (Claude, GPT-4, Gemma) evaluate and improve Python code. For each code sample, the pipeline:

1. **Critique**: LLM evaluates code against 16 quality dimensions
2. **Improve**: LLM suggests improvements and refactors the code
3. **Re-critique**: LLM evaluates the improved code and compares to original

## Architecture

```
Dataset of Code Samples
         ↓
  [Preprocessing]
         ↓
  Code Metadata Extraction (AST)
         ↓
  [Pipeline Processing]
         ↓
   For each sample:
     ├→ Model 1 (Claude) → Critique → Improve → Re-critique
     ├→ Model 2 (GPT-4) → Critique → Improve → Re-critique
     └→ Model 3 (Gemma) → Critique → Improve → Re-critique
         ↓
  [Analysis & Visualization]
         ↓
   Score Comparison
   Naming Analysis
   Statistical Tests
   Reports & Charts
```

## Project Structure

```
codewise/
├── evaluation_rubric.md           # 20-dimension evaluation rubric
├── config.yaml                    # Pipeline configuration
├── DATASET_GUIDE.md               # How to curate the dataset
├── PIPELINE.md                    # This file
│
├── source/
│   └── pipeline/                  # Core pipeline module
│       ├── __init__.py
│       ├── cache_manager.py       # Cache for API responses
│       ├── pipeline_logger.py     # Logging and metrics
│       ├── model_api.py           # LLM model interfaces
│       ├── sample_processor.py    # Single-sample processing
│       └── batch_processor.py     # Batch processing & CLI
│
├── scripts/
│   ├── curate_dataset.py          # Helper for dataset curation
│   ├── add_samples_interactive.py # Interactive sample addition
│   └── preprocess_samples.py      # AST preprocessing
│
├── prompts/
│   ├── critique_template.txt      # Critique prompt
│   ├── improve_template.txt       # Improvement prompt
│   ├── recritique_template.txt    # Re-critique prompt
│   └── naming_critique_template.txt # Naming evaluation
│
├── datasets/
│   └── original_code/             # Code samples to evaluate
│       ├── sample_001.py
│       ├── sample_002.py
│       └── metadata.csv           # Sample metadata
│
├── intermediate/
│   ├── parsed_code_metadata.json  # AST metadata for all samples
│   ├── pipeline_metadata.json     # Execution state
│   └── cache/                     # Cached LLM responses
│
└── outputs/
    ├── claude/                    # Claude model outputs
    │   ├── critique_sample_001.json
    │   ├── improved_sample_001.json
    │   ├── recritique_sample_001.json
    │   └── summary_sample_001.json
    ├── gpt4/                      # GPT-4 model outputs
    │   └── ...
    ├── gemma/                     # Gemma model outputs
    │   └── ...
    └── analysis/                  # Analysis results
        ├── score_comparison.csv
        ├── naming_improvements.json
        └── visualizations/
```

## Core Components

### 1. Evaluation Rubric (`evaluation_rubric.md`)

Defines 20 dimensions for evaluating code quality:

**Dimensions 1-16**: Code Quality (adapted from Codewise)
- Separation of Concerns
- Documentation
- Logic Clarity
- Understandability
- Efficiency
- Error Handling
- Testability
- Reusability
- Code Consistency
- Dependency Management
- Security Awareness
- Side Effects
- Scalability
- Resource Management
- Encapsulation
- Complex Logic Readability

**Dimensions 17-20**: LLM Review Quality
- Critique Actionability
- Critique Consistency
- Refactoring Quality
- Rubric Alignment

### 2. Cache Manager (`source/pipeline/cache_manager.py`)

Caches LLM API responses to avoid redundant calls:
- Deterministic hash-based cache keys
- JSON file storage
- Statistics tracking

### 3. Pipeline Logger (`source/pipeline/pipeline_logger.py`)

Tracks execution and API calls:
- Structured logging to files and console
- JSONL format for API call tracking
- Cost estimation

### 4. Model API (`source/pipeline/model_api.py`)

Abstract interface + implementations for LLM models:
- `CodeReviewModel`: Abstract base class
- `ClaudeReviewer`: Claude via Anthropic API
- `GPT4Reviewer`: GPT-4 via OpenAI API
- `GemmaReviewer`: Gemma (placeholder for later)

Each model implements:
- `critique(code)`: Evaluate code
- `improve(code, critique)`: Suggest improvements
- `recritique(original, improved, original_critique)`: Compare versions

### 5. Sample Processor (`source/pipeline/sample_processor.py`)

Processes a single sample through the 3-phase pipeline:
1. Load code sample
2. Run critique → improve → re-critique
3. Save outputs at each phase
4. Handle errors gracefully

### 6. Batch Processor (`source/pipeline/batch_processor.py`)

Orchestrates processing across multiple samples and models:
- Loads configuration
- Initializes models
- Coordinates sample processing
- Tracks progress/state
- Provides CLI interface

## Usage Guide

### Initial Setup

1. **Install dependencies**:
```bash
source .venv/bin/activate
uv pip install . --group dev
pip install anthropic openai pyyaml sentence-transformers
```

2. **Set up environment**:
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

3. **Configure pipeline** (`config.yaml`):
   - Select which models to enable
   - Set dataset path
   - Configure output directories

### Step 1: Curate Dataset

**Interactive method**:
```bash
python scripts/add_samples_interactive.py
```

**Programmatic method**:
```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()
curator.create_metadata_csv()

# Add samples...
curator.add_sample(
    sample_id='sample_001',
    code_content='def hello(): pass',
    source='github',
    category='utility',
    quality_expectation='good'
)

# Check progress
print(f"Total samples: {curator.get_sample_count()}")
curator.list_samples()
```

Target: 30-70 code samples with variety:
- 15-20: Open-source (GitHub)
- 15-20: LLM-generated
- 5-15: Intentionally problematic

### Step 2: Preprocess Samples

Extract AST metadata and validate syntax:
```bash
python scripts/preprocess_samples.py
```

Output: `intermediate/parsed_code_metadata.json`

### Step 3: Run Pipeline

**Dry run (test without API calls)**:
```bash
python -m source.pipeline.batch_processor \
  --dry-run \
  --max-samples 2
```

**Full run**:
```bash
python -m source.pipeline.batch_processor \
  --config config.yaml \
  --dataset datasets/original_code \
  --output outputs \
  --max-samples 10
```

**Resume from previous run**:
```bash
python -m source.pipeline.batch_processor --resume
```

**Options**:
- `--config`: Path to config YAML
- `--dataset`: Path to dataset directory
- `--output`: Path to output directory
- `--max-samples`: Max samples to process
- `--dry-run`: Test without API calls
- `--resume`: Resume from previous run (default)
- `--no-resume`: Process all samples again

### Step 4: Analyze Results

**Score Comparison** (Phase 5.1):
```bash
python source/analysis/score_analyzer.py
```

Output: `outputs/analysis/score_comparison.csv`

**Naming Analysis** (Phase 5.2):
```bash
python source/analysis/naming_analyzer.py
```

Output: `outputs/analysis/naming_improvements.json`

**Generate Visualizations** (Phase 5.4):
```bash
python source/analysis/visualizer.py
```

Output: Charts and interactive HTML reports

## Data Formats

### Sample File (`datasets/original_code/sample_001.py`)
Plain Python code file with one or more functions/classes.

### Metadata CSV (`datasets/original_code/metadata.csv`)
```csv
sample_id,source,category,quality_expectation,description,lines_of_code,...
sample_001,github,utility,good,Calculate fibonacci,42,...
```

### Critique Output (`outputs/claude/critique_sample_001.json`)
```json
{
  "overall_score": 7.5,
  "scores": {
    "separation_of_concerns": 8,
    "documentation": 7,
    ...
  },
  "feedback": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "priority_improvements": ["..."],
    "general_comments": "..."
  }
}
```

### Improvement Output (`outputs/claude/improved_sample_001.json`)
```json
{
  "refactored_code": "def fibonacci(n: int) -> int:\n...",
  "changes_made": {
    "summary": "...",
    "detailed_changes": [...]
  },
  "explanation": {...}
}
```

### Re-critique Output (`outputs/claude/recritique_sample_001.json`)
```json
{
  "improved_code_scores": {...},
  "comparative_analysis": {
    "overall_score_change": +1.5,
    "dimension_improvements": {...}
  },
  "feedback": {...}
}
```

## Configuration (`config.yaml`)

Key configuration options:

```yaml
api:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo

models:
  claude:
    enabled: true
    temperature: 0.7
    max_tokens: 2048
  gpt4:
    enabled: true
  gemma:
    enabled: false  # Set to true when ready

pipeline:
  dataset_path: datasets/original_code
  output_base_path: outputs
  cache_enabled: true
  dry_run: false
```

## Cost Estimation

Approximate API costs (as of 2025):

| Model | Input Cost | Output Cost |
|-------|-----------|------------|
| Claude 3.5 Sonnet | $0.003/1K | $0.015/1K |
| GPT-4 Turbo | $0.01/1K | $0.03/1K |
| Gemma | $0.00 (local) | $0.00 (local) |

For 50 samples × 2 models (Claude + GPT-4):
- Critique phase: ~2K-3K tokens per sample → ~$0.25-0.50
- Improve phase: ~2K-4K tokens per sample → ~$0.50-1.00
- Re-critique phase: ~2K-3K tokens per sample → ~$0.25-0.50
- **Total: ~$50-75 for 50 samples across 2 models**

Tips to reduce costs:
- Use Claude instead of GPT-4 (3-10x cheaper)
- Cache responses (use `--resume` to skip repeated calls)
- Start with fewer samples (e.g., `--max-samples 10`)
- Use dry run mode for testing

## Pipeline Workflow

### Complete End-to-End Flow

```
1. Curate Dataset (30-70 samples)
   ↓
2. Preprocess Samples (extract metadata)
   ↓
3. Configure Pipeline (edit config.yaml)
   ↓
4. Run Batch Processor
   ├─ For each sample:
   │  ├─ Claude: critique → improve → recritique
   │  ├─ GPT-4: critique → improve → recritique
   │  └─ Save all outputs
   └─ Update progress tracking
   ↓
5. Analyze Results
   ├─ Score comparison across models
   ├─ Naming improvements analysis
   ├─ Statistical tests
   └─ Generate visualizations
   ↓
6. Write Report
   └─ Document findings and conclusions
```

### MVP Flow (Faster)

```
1. Add 3-5 test samples (manual)
   ↓
2. Run with --dry-run to test pipeline
   ↓
3. Run with --max-samples 2 to validate APIs work
   ↓
4. Iterate on prompts/evaluation criteria
   ↓
5. Once satisfied, scale to full dataset
```

## Troubleshooting

### API Errors

**"API key not found"**
- Check .env file exists
- Verify `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are set
- Run: `python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"`

**"Rate limit exceeded"**
- Reduce `max_tokens` in config
- Increase delay between requests
- Use cache to avoid redundant calls

### Dataset Issues

**"No sample files found"**
- Check `datasets/original_code/` directory exists
- File names must start with `sample_` and end with `.py`

**"Syntax error in sample"**
- Run `python scripts/preprocess_samples.py` to identify bad files
- Fix or remove problematic samples

### Output Issues

**"Failed to parse JSON from response"**
- Some models don't return valid JSON
- Check raw response in logs
- May need to adjust prompt template

## Next Steps After MVP

1. **Add more samples**: Scale from MVP (3-5) to full dataset (30-70)
2. **Add Gemma**: Set up local Ollama or HF API
3. **Statistical analysis**: Correlation, significance tests
4. **Manual validation**: Manually review outputs for accuracy
5. **Iteration**: Refine prompts based on findings

## Performance Notes

- Single sample processing (all 3 phases): 2-5 minutes
- 50 samples × 2 models = 100-250 minutes (~2-4 hours)
- Use `--max-samples` for testing
- Enable caching to avoid re-running same calls
- Gemma locally will be much faster than cloud APIs

## Support & Debugging

**View logs**:
```bash
tail -f logs/pipeline.log
tail -f logs/api_calls.jsonl
```

**Check cache**:
```bash
ls -lh intermediate/cache/
wc -l intermediate/cache/*.json
```

**Monitor API costs**:
```bash
python -c "
from source.pipeline import PipelineLogger
logger = PipelineLogger()
stats = logger.get_api_call_summary()
print(f\"Total cost: \${stats['total_cost_usd']:.2f}\")
"
```

## References

- Evaluation Rubric: `evaluation_rubric.md`
- Dataset Guide: `DATASET_GUIDE.md`
- Codewise Original: `CLAUDE.md`
- Config Template: `config.yaml`

Good luck with your research!

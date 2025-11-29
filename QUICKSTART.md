# Quick Start Guide - Codewise Research Pipeline

Get up and running in 30 minutes!

## 1. Prerequisites (5 minutes)

```bash
# Ensure you're in the codewise directory
cd /Users/peejakhorashadi/masters_project/codewise

# Activate virtual environment
source .venv/bin/activate

# Install required packages
pip install anthropic openai pyyaml sentence-transformers

# Set up .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

Replace the keys with your actual API keys.

## 2. Add Test Samples (5 minutes)

### Option A: Interactive Method

```bash
python scripts/add_samples_interactive.py
```

Follow the prompts to add 3-5 test samples.

### Option B: Quick Programmatic Method

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()
curator.create_metadata_csv()

# Sample 1: Good code
curator.add_sample(
    sample_id='sample_001',
    code_content="""
def fibonacci(n: int) -> int:
    '''Compute nth Fibonacci number.'''
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
""",
    source='github',
    category='utility',
    quality_expectation='good',
    description='Efficient Fibonacci calculator'
)

# Sample 2: Bad code
curator.add_sample(
    sample_id='sample_002',
    code_content="""
def f(d):
    x = []
    for k in d:
        for i in range(len(d[k])):
            if d[k][i] > 0 and d[k][i] < 100:
                x.append(d[k][i] * 2)
    return x
""",
    source='intentionally_bad',
    category='data_processing',
    quality_expectation='bad',
    description='Poorly written data processor'
)

# Sample 3: LLM-generated
curator.add_sample(
    sample_id='sample_003',
    code_content="""
def merge_sorted_arrays(arr1: list, arr2: list) -> list:
    '''Merge two sorted arrays.'''
    result = []
    i = j = 0
    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1
    result.extend(arr1[i:] + arr2[j:])
    return result
""",
    source='llm_generated',
    category='utility',
    quality_expectation='good',
    description='Merge two sorted arrays'
)

print(f"Added {curator.get_sample_count()} samples")
curator.list_samples()
```

## 3. Preprocess Samples (2 minutes)

```bash
python scripts/preprocess_samples.py
```

This validates your code samples and extracts AST metadata.

## 4. Configure Pipeline (2 minutes)

Edit `config.yaml` and set:
- Which models to use (enable Claude, GPT-4)
- Dataset path (should be `datasets/original_code`)
- Output path (can be `outputs`)

Default is fine for testing.

## 5. Test with Dry Run (2 minutes)

```bash
python -m source.pipeline.batch_processor \
  --dry-run \
  --max-samples 2
```

This tests the pipeline WITHOUT calling APIs. Good for validation!

## 6. Run Real Pipeline (10+ minutes)

```bash
python -m source.pipeline.batch_processor \
  --max-samples 2
```

This will:
1. Load samples
2. Run critique → improve → re-critique for each sample
3. Save outputs to `outputs/{model}/`
4. Print summary

**Expected output** (~1-2 minutes per sample per model):
```
======================================================================
CODEWISE RESEARCH PIPELINE
======================================================================

Loading samples from datasets/original_code...
✓ Loaded 3 samples

Initializing models...
✓ Initialized 2 models: claude, gpt4

Processing 2 samples...

--- Processing sample 1/2: sample_001 ---
[claude] Phase 1/3: Critiquing sample_001
✓ API Call: claude/critique/sample_001 - Tokens: 1,245 - Cost: $0.02
[claude] Phase 2/3: Improving sample_001
✓ API Call: claude/improve/sample_001 - Tokens: 2,456 - Cost: $0.05
[claude] Phase 3/3: Re-critiquing sample_001
✓ API Call: claude/recritique/sample_001 - Tokens: 1,890 - Cost: $0.04
... (repeats for GPT-4 and other samples)

======================================================================
PROCESSING SUMMARY
======================================================================
Total samples processed: 6
Completed: 6
Failed: 0

Cache statistics:
  Cached files: 6
  Cache size: 2.45 MB

API call statistics:
  Total calls: 18
  Successful: 18
  Cached: 0
  Total cost: $1.25

======================================================================
```

## 7. Check Results

```bash
# List output files
ls -la outputs/claude/
ls -la outputs/gpt4/

# View a critique
cat outputs/claude/critique_sample_001.json | python -m json.tool

# View an improvement
cat outputs/claude/improved_sample_001.json | python -m json.tool | head -50

# View logs
tail -20 logs/pipeline.log
```

## 8. Next Steps

### Scale Up
```bash
# Process 10 samples
python -m source.pipeline.batch_processor --max-samples 10

# Or resume from last run (skips already processed)
python -m source.pipeline.batch_processor --resume
```

### Add More Samples
```bash
python scripts/add_samples_interactive.py
# Add more samples, then re-run pipeline
```

### Analyze Results
(Coming soon - Phase 5 implementation)

```bash
# Will generate these once Phase 5 is done:
python source/analysis/score_analyzer.py      # Compare scores
python source/analysis/naming_analyzer.py     # Naming quality
python source/analysis/visualizer.py          # Create charts
```

## Common Issues

### Error: "API key not found"
→ Check your `.env` file has `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`

### Error: "No sample files found"
→ Check you added samples using one of the methods above

### Error: "Syntax error in sample"
→ Run `python scripts/preprocess_samples.py` to identify bad files

### Model returns invalid JSON
→ This is expected sometimes. The pipeline will log the error and continue.

### Want to speed things up?
→ Use Claude only (cheaper and faster than GPT-4)
→ Edit `config.yaml` and set `gpt4.enabled: false`

## File Structure After Quick Start

```
codewise/
├── datasets/original_code/
│   ├── sample_001.py
│   ├── sample_002.py
│   ├── sample_003.py
│   └── metadata.csv
├── intermediate/
│   ├── parsed_code_metadata.json
│   ├── pipeline_metadata.json
│   └── cache/
│       ├── abc123def.json
│       └── ... (6+ cached responses)
├── outputs/
│   ├── claude/
│   │   ├── critique_sample_001.json
│   │   ├── improved_sample_001.json
│   │   ├── recritique_sample_001.json
│   │   └── summary_sample_001.json
│   ├── gpt4/
│   │   └── ... (similar structure)
│   └── analysis/  (empty until Phase 5)
└── logs/
    └── pipeline.log
```

## Typical Time Breakdown

| Step | Time | Notes |
|------|------|-------|
| Setup | 5 min | One-time |
| Add samples | 5 min | Add as many as you want |
| Preprocess | 1 min | Validates code |
| Config | 2 min | Edit once, done |
| Dry run | 2 min | Tests pipeline |
| Real run (2 samples, 2 models) | 5-10 min | Actual API calls |
| **Total for MVP** | **~20-25 min** | |

## Cost for Quick Start

For 2 samples × 2 models (3 phases each = 6 API calls per sample):

| Model | Rough Cost |
|-------|----------|
| Claude (2 samples) | ~$0.20 |
| GPT-4 (2 samples) | ~$0.60 |
| **Total** | **~$0.80** |

This gets you familiar with the pipeline. Scaling to 50 samples will cost ~$20-40.

## Pro Tips

1. **Use `--dry-run` first** to test without costs
2. **Use `--resume`** to continue without reprocessing
3. **Start small** with 2-5 samples, scale up later
4. **Monitor logs** with `tail -f logs/pipeline.log`
5. **Check cache** to see what's been processed: `ls intermediate/cache/ | wc -l`

## Need More Help?

- **Full documentation**: Read `PIPELINE.md`
- **Dataset guide**: Read `DATASET_GUIDE.md`
- **Evaluation rubric**: Read `evaluation_rubric.md`
- **Config options**: Edit and read `config.yaml`

## Ready to Dive Deeper?

Once you've completed the quick start:

1. **Expand dataset**: Add 30-70 samples using the curator
2. **Implement Phase 5**: Build analysis and visualization tools
3. **Manual review**: Check a few outputs for quality
4. **Iterate**: Refine prompts based on what you learn

Good luck! 🚀

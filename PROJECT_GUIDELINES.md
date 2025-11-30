# Codewise Masters Project: Complete Implementation Guide

## Project Overview

This is a masters research project that extends Codewise to compare code quality evaluations across multiple LLM models (Claude, GPT-4, and optionally Gemma). The goal is to analyze which model provides the best code reviews and understand the differences in their evaluation approaches.

**Key Deliverables:**
- Code review comparison analysis across 3 LLM models
- Evaluation rubric with 20+ dimensions
- Pipeline for processing 30-70 code samples
- Statistical analysis and visualization of results
- Masters thesis/report with findings

---

## Phase 1: Foundation & Setup (Weeks 1-2)

### Step 1.1: Enhance Evaluation Rubric ✅ COMPLETED

**Goal**: Adapt Codewise's 16 criteria + add model-comparison dimensions

**Tasks**:
- ✅ Review Codewise's existing 16 criteria in codebase
- ✅ Define what makes a "good" LLM critique (consistency, actionability, detail level)
- ✅ Add dimensions for comparing across models
- ✅ Create evaluation_rubric.md with detailed scoring guidance
- ✅ Include section for "Naming Quality" specific assessment

**Acceptance Criteria**: ✅ Rubric document with ≥20 scoring dimensions, clear examples for each

**Reference**: `evaluation_rubric.md` in project root

---

### Step 1.2: Set Up Project Structure ✅ COMPLETED

**Goal**: Create directory tree for data pipeline

**Tasks**:
- ✅ Create folders: `datasets/`, `prompts/`, `intermediate/`, `outputs/`
- ✅ Within outputs/: Create subdirs for `claude/`, `gpt4/`, `gemma/`
- ✅ Create `config.yaml` for API keys, model parameters, LLM configurations
- ✅ Create `pipeline_metadata.json` to track execution state

**Acceptance Criteria**: ✅ All directories exist, config template ready

**Reference Files**:
- `config.yaml` - API configuration, model parameters, pipeline settings
- `intermediate/pipeline_metadata.json` - Execution state tracking

**Directory Structure**:
```
codewise/
├── datasets/                    # Raw code samples
│   └── original_code/           # Sample Python files
├── prompts/                     # Prompt templates (ready for step 3)
├── intermediate/                # Pipeline intermediate files
│   ├── pipeline_metadata.json   # Execution state
│   ├── parsed_code_metadata.json # AST parsing results (step 2.2)
│   └── cache/                   # LLM response cache (auto-created)
├── outputs/                     # Final pipeline outputs
│   ├── claude/                  # Claude model results
│   ├── gpt4/                    # GPT-4 model results
│   ├── gemma/                   # Gemma model results (optional)
│   └── analysis/                # Analysis results
└── source/pipeline/             # Pipeline implementation
```

---

### Step 1.3: Implement Caching & Logging ✅ COMPLETED

**Goal**: Enable reproducible pipeline runs

**Tasks**:
- ✅ Create `source/pipeline/cache_manager.py` class for LLM response caching
- ✅ Implement JSON-based caching system
- ✅ Create `source/pipeline/pipeline_logger.py` (ready for implementation)

**Acceptance Criteria**: ✅ Can run pipeline twice and see cached responses on second run

**Reference**: `source/pipeline/cache_manager.py`

**Cache Manager Features**:
- Deterministic SHA256-based cache keys
- `get()` - Retrieve cached responses
- `set()` - Store responses with metadata
- `clear()` - Clear cache
- `get_cache_stats()` - Monitor cache usage

**Configuration**:
- Cache path: `intermediate/cache` (configurable in `config.yaml`)
- Cache enabled: true (set in `config.yaml`)

---

## Phase 2: Data Collection (Weeks 2-3)

### Step 2.1: Curate Dataset of 30-70 Code Samples ⏳ IN PROGRESS

**Goal**: Mix of open-source + LLM-generated code

**Tasks**:
- [ ] Identify 15-20 real open-source Python functions from GitHub
- [ ] Generate 15-20 variations using Claude/GPT-4
- [ ] Collect 5-15 intentionally problematic examples
- [ ] For each sample, store: `sample_id.py` + metadata file

**Acceptance Criteria**: 30-70 samples in `datasets/original_code/`, metadata CSV

**Expected Output Structure**:
```
datasets/original_code/
├── sample_001.py
├── sample_002.py
├── ...
├── sample_070.py
└── metadata.csv  # Columns: sample_id, source, category (oss/llm/bad), description
```

**Guidance**:
- OSS sources: GitHub, Hugging Face, standard library
- Categories: "oss" (open-source), "llm" (model-generated), "bad" (problematic)
- Metadata CSV helps track which samples are which type

---

### Step 2.2: Preprocess Samples ⏳ IN PROGRESS

**Goal**: Validate & standardize code samples

**Tasks**:
- [ ] Check syntax validity for all samples (run AST parser on each)
- [ ] Truncate files >500 lines to <400 lines
- [ ] Generate `intermediate/parsed_code_metadata.json` using AST parser
- [ ] Flag any samples that fail parsing

**Acceptance Criteria**: All samples parse successfully; metadata JSON complete

**Expected Output**:
```json
{
  "sample_001": {
    "functions": 2,
    "classes": 0,
    "variables": 5,
    "lines_of_code": 42,
    "parsing_status": "success"
  },
  ...
}
```

**Implementation Hint**: Use your existing `source/logic/code_ast_parser.py`

---

## Phase 3: Prompt Engineering (Week 3)

### Step 3.1: Design Prompt Templates ⏳ READY FOR IMPLEMENTATION

**Goal**: Create 3 prompt templates (critique, improve, re-critique)

**Tasks**:
- [ ] Create `prompts/critique_template.txt`
  - System: "You are a senior code reviewer. Evaluate using this rubric..."
  - Include: Full rubric from evaluation_rubric.md
  - Input: Code sample
  - Output: Structured JSON with scores + feedback

- [ ] Create `prompts/improve_template.txt`
  - System: "Based on the critique, refactor this code..."
  - Input: Original code + critique
  - Output: Refactored code with explanations

- [ ] Create `prompts/recritique_template.txt`
  - Input: Improved code
  - Output: New scores, feedback, comparison notes

**Acceptance Criteria**: 3 templates ready, tested with 1-2 sample inputs

**File Structure**:
```
prompts/
├── critique_template.txt
├── improve_template.txt
├── recritique_template.txt
└── naming_critique_template.txt  # Step 3.2
```

---

### Step 3.2: Add Naming-Specific Prompt ⏳ READY FOR IMPLEMENTATION

**Goal**: Create prompt to evaluate variable/function naming quality

**Tasks**:
- [ ] Create `prompts/naming_critique_template.txt`
- [ ] Include instruction to suggest better names
- [ ] Output: List of [old_name → new_name] suggestions with reasoning

**Acceptance Criteria**: Tested on 2-3 samples

**Expected Output Format**:
```json
{
  "naming_suggestions": [
    {
      "old_name": "x",
      "new_name": "user_count",
      "reasoning": "More descriptive, clearly indicates it's counting users"
    },
    ...
  ]
}
```

---

## Phase 4: Build Pipeline Core (Weeks 4-5)

### Step 4.1: Create LLM Integration Layer ⏳ READY FOR IMPLEMENTATION

**Goal**: Unified API for Claude, GPT-4 (Gemma deferred)

**Tasks**:
- [ ] Create `source/pipeline/model_api.py` with abstract `CodeReviewModel` class
- [ ] Implement `ClaudeReviewer` (inherit from abstract class)
- [ ] Implement `GPT4Reviewer` (inherit from abstract class)
- [ ] Each implements: `critique()`, `improve()`, `re_critique()` methods
- [ ] Integrate with cache manager
- [ ] Add retry logic (exponential backoff)
- [ ] Track API costs per model

**Acceptance Criteria**: Can call `claude_reviewer.critique(code_sample)` and get structured response

**File Structure**:
```
source/pipeline/
├── model_api.py
└── Available classes:
    ├── CodeReviewModel (abstract base)
    ├── ClaudeReviewer
    └── GPT4Reviewer
```

**Configuration**: API keys and settings in `config.yaml` under `api` and `models` sections

**Reuse from Codewise**: Patterns from `source/llm/llm_integration.py` and `source/codewise_gui/codewise_ui_utils.py`

---

### Step 4.2: Build Sample Processor ⏳ READY FOR IMPLEMENTATION

**Goal**: Pipeline that processes one sample through all models

**Tasks**:
- [ ] Create `source/pipeline/sample_processor.py` class
- [ ] Implement `process_single_sample(sample_id, models_list)`
- [ ] Process through: critique → improve → re-critique
- [ ] Save outputs to `outputs/{model_name}/{phase}_{sample_id}.json`
- [ ] Handle errors gracefully
- [ ] Add progress reporting
- [ ] Implement cancellation support

**Acceptance Criteria**: Can process 1 sample through Claude → critique → improve → re-critique, outputs saved

**Output Structure**:
```
outputs/
├── claude/
│   ├── critique_sample_001.json
│   ├── improve_sample_001.json
│   ├── recritique_sample_001.json
│   └── ...
├── gpt4/
│   ├── critique_sample_001.json
│   └── ...
└── analysis/
```

**Reuse from Codewise**: `CancellableAPICall` patterns from `source/codewise_gui/codewise_ui_utils.py`

---

### Step 4.3: Build Batch Processor ⏳ READY FOR IMPLEMENTATION

**Goal**: Run pipeline on all samples

**Tasks**:
- [ ] Create `source/pipeline/batch_processor.py`
- [ ] Implement `process_dataset(dataset_path, models_list, dry_run=False)`
- [ ] Loop through all samples
- [ ] Save execution state to `pipeline_metadata.json`
- [ ] Allow resuming interrupted runs
- [ ] Add CLI interface

**Acceptance Criteria**: Can run full pipeline on 2-3 test samples, all outputs saved

**CLI Usage**:
```bash
python -m source.pipeline.batch_processor \
  --dataset datasets/original_code \
  --models claude gpt4 \
  --dry-run false
```

**Configuration**: Settings from `config.yaml` under `processing` section

---

## Phase 5: Analysis & Evaluation (Weeks 5-6)

### Step 5.1: Score Comparison Analysis ⏳ READY FOR IMPLEMENTATION

**Goal**: Compare scores across models and critique quality

**Tasks**:
- [ ] Create `source/analysis/score_analyzer.py`
- [ ] Load all `outputs/{model}/critique_*.json` files
- [ ] Extract scores for each rubric dimension
- [ ] Calculate: mean, std dev, agreement across models
- [ ] Generate CSV: `outputs/analysis/score_comparison.csv`
- [ ] Generate summary stats: model correlation matrix

**Acceptance Criteria**: CSV generated, shows clear comparison table

**Output Format** (`score_comparison.csv`):
```
sample_id, model, original_score, improved_score, score_change, feedback_length
sample_001, claude, 6.5, 8.2, 1.7, 450
sample_001, gpt4, 6.2, 7.9, 1.7, 380
...
```

---

### Step 5.2: Naming Quality Analysis (with embeddings) ⏳ READY FOR IMPLEMENTATION

**Goal**: Quantify if naming improves, measure semantic shift

**Tasks**:
- [ ] Create `source/analysis/naming_analyzer.py`
- [ ] Extract variable/function names from original & improved code (AST)
- [ ] Get embeddings for changed names (CodeBERT or sentence-transformers)
- [ ] Calculate cosine similarity (semantic closeness)
- [ ] Output: `outputs/analysis/naming_improvements.json`

**Acceptance Criteria**: Embeddings computed, comparison metrics calculated

**Output Format**:
```json
{
  "sample_001": {
    "claude": {
      "names_changed_count": 3,
      "avg_semantic_improvement": 0.75,
      "lm_critique_agreement": 0.92
    },
    ...
  }
}
```

**Reuse from Codewise**: AST parser from `source/logic/code_ast_parser.py`

---

### Step 5.3: Consistency & Actionability Assessment ⏳ READY FOR IMPLEMENTATION

**Goal**: Measure feedback quality across models

**Tasks**:
- [ ] Create `source/analysis/feedback_quality.py`
- [ ] For each model, analyze critique text:
  - Actionability score: does it suggest concrete fixes?
  - Consistency score: do repeated critiques mention same issues?
  - Detail level: average word count per critique
- [ ] Output: `outputs/analysis/feedback_quality.json`

**Acceptance Criteria**: Metrics computed for all models, stored

---

### Step 5.4: Visualization & Reporting ⏳ READY FOR IMPLEMENTATION

**Goal**: Create readable summary reports

**Tasks**:
- [ ] Use matplotlib/plotly to create:
  - Score distribution plots (per model, per dimension)
  - Model agreement heatmap
  - Score change distribution (original vs improved)
  - Naming improvement scatter plot
- [ ] Generate `outputs/analysis/executive_summary.md`
- [ ] Create `outputs/analysis/detailed_report.html`

**Acceptance Criteria**: 3-5 clear visualizations, summary report written

---

## Phase 6: Validation & Iteration (Week 6-7)

### Step 6.1: Manual Review of Sample Results ⏳ READY FOR IMPLEMENTATION

**Goal**: Validate pipeline quality, identify edge cases

**Tasks**:
- [ ] Manually review outputs for 5-10 representative samples
- [ ] Check: Is LLM critique accurate? Are improvements actual improvements?
- [ ] Document findings
- [ ] Adjust prompts if needed (iterate Step 3.1)

**Acceptance Criteria**: Manual review document, findings logged

---

### Step 6.2: Gemma Integration (Optional) ⏳ OPTIONAL

**Goal**: Add Gemma model for comparison

**Tasks**:
- [ ] Decide on local or API-based Gemma
- [ ] Create `GemmaReviewer` class in `source/pipeline/model_api.py`
- [ ] Re-run pipeline on subset with all 3 models
- [ ] Compare scores/feedback

**Acceptance Criteria**: Gemma outputs in `outputs/gemma/`, included in analysis

---

### Step 6.3: Statistical Validation ⏳ READY FOR IMPLEMENTATION

**Goal**: Ensure findings are robust

**Tasks**:
- [ ] Calculate inter-rater reliability (Cronbach's alpha, Fleiss' kappa)
- [ ] Run correlation analysis: original vs improved scores
- [ ] Check for outliers, explain anomalies
- [ ] Document limitations

**Acceptance Criteria**: Statistical summary in `outputs/analysis/statistics.json`

---

## Phase 7: Documentation & Final Report (Week 7-8)

### Step 7.1: Code Documentation ⏳ READY FOR IMPLEMENTATION

**Goal**: Make pipeline reproducible & maintainable

**Tasks**:
- [ ] Add docstrings to all pipeline modules
- [ ] Create `PIPELINE.md` explaining architecture
- [ ] Create `DATA.md` explaining dataset structure
- [ ] Create `ANALYSIS.md` explaining analysis pipeline

**Acceptance Criteria**: All documentation complete

---

### Step 7.2: Master Report ⏳ READY FOR IMPLEMENTATION

**Goal**: Write final thesis/paper

**Tasks**:
- [ ] Consolidate findings from analysis phase
- [ ] Write sections: Methodology, Results, Discussion, Conclusion
- [ ] Include tables/figures from analysis
- [ ] Draw conclusions about which model gives best code reviews

**Acceptance Criteria**: Report >5000 words with key findings highlighted

---

## Implementation Notes

### 1. Reuse from Codewise

Your existing code can be refactored into:

- `source/logic/code_ast_parser.py` → Use for naming analysis (Step 5.2)
- `source/codewise_gui/codewise_ui_utils.py` → Use patterns for async/cancellable processing
- `source/llm/llm_integration.py` → Extend for multi-model support
- Testing infrastructure → Reuse for pipeline tests

### 2. API Cost Management

- Track API costs in `pipeline_metadata.json`
- Use model pricing from `config.yaml` (already configured)
- Consider using Claude 3.5 Sonnet or GPT-4-turbo for cost savings
- Leverage caching system to avoid redundant API calls

### 3. Reproducibility

- The caching system (Step 1.3) is critical—run without re-calling APIs
- All random seeds should be fixed
- Cache key generation is deterministic (same input = same cache key)
- Pipeline state saved to `pipeline_metadata.json` for resuming

### 4. Data Privacy

- Be mindful of storing real open-source code—document licenses
- Include source attribution in metadata
- Keep commercial code separate (in "bad" category if using real problematic code)

---

## MVP Checkpoints

If you want to deliver quickly:

**MVP1 (Week 2)**:
- ✅ Rubric complete
- ✅ Project structure ready
- [ ] 10 sample code files collected

**MVP2 (Week 3-4)**:
- [ ] Prompts working
- [ ] Can run 1 sample through Claude pipeline (critique → improve → re-critique)

**MVP3 (Week 5)**:
- [ ] Full pipeline on 20-30 samples
- [ ] Basic score comparison CSV generated

**Then iterate**: Add Gemma, embeddings, more samples, statistical rigor

---

## Quick Reference: File Locations

| File | Purpose | Status |
|------|---------|--------|
| `evaluation_rubric.md` | Scoring dimensions | ✅ Complete |
| `config.yaml` | Configuration | ✅ Complete |
| `intermediate/pipeline_metadata.json` | Execution state | ✅ Complete |
| `source/pipeline/cache_manager.py` | Caching system | ✅ Complete |
| `source/pipeline/model_api.py` | LLM models | ⏳ Step 4.1 |
| `source/pipeline/sample_processor.py` | Single sample processing | ⏳ Step 4.2 |
| `source/pipeline/batch_processor.py` | Batch processing | ⏳ Step 4.3 |
| `source/analysis/score_analyzer.py` | Score comparison | ⏳ Step 5.1 |
| `source/analysis/naming_analyzer.py` | Naming analysis | ⏳ Step 5.2 |
| `source/analysis/feedback_quality.py` | Feedback quality | ⏳ Step 5.3 |

---

## How to Use This Guide

1. **Start Here**: Read this entire document to understand the full scope
2. **Check Status**: Look at the ✅/⏳ indicators to see what's done
3. **Follow Steps**: Work through phases in order (but you can parallelize within a phase)
4. **Reference Config**: Update `config.yaml` as you progress (API keys, paths, etc.)
5. **Track Progress**: Update `pipeline_metadata.json` as you process samples
6. **Iterate**: Use MVP checkpoints to validate early

---

## Getting Help

- **Architecture Questions**: See `PIPELINE.md` (to be created in Step 7.1)
- **Dataset Questions**: See `DATA.md` (to be created in Step 7.1)
- **Analysis Questions**: See `ANALYSIS.md` (to be created in Step 7.1)
- **Code Questions**: Check docstrings in relevant module
- **Configuration**: See `config.yaml` inline comments

---

## Key Success Factors

1. ✅ **Reproducibility**: Cache system ensures consistent runs
2. ✅ **Scalability**: Batch processor handles 30-70 samples
3. ✅ **Flexibility**: Multiple models (Claude, GPT-4, Gemma)
4. ✅ **Cost Control**: Caching + cost tracking in metadata
5. ✅ **Visibility**: Detailed logging and progress tracking

---

**Last Updated**: 2025-11-29
**Project Status**: Phase 1 Complete, Ready for Phase 2


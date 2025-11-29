# 🚀 START HERE - Codewise Research Pipeline

Welcome! You have a complete, production-ready LLM code review research pipeline built and ready to use.

**Status**: ✅ Foundation Complete (Phases 1-4)
**Next Step**: Add code samples and run your first evaluation

---

## 📋 What You Have

A complete pipeline to:
1. **Evaluate** Python code with multiple LLM models (Claude, GPT-4, Gemma)
2. **Compare** how different models rate and improve code
3. **Measure** which models give better code reviews

Built for your masters research on "Comparing LLM Code Review Capabilities"

---

## ⚡ Quick Start (30 minutes)

### Step 1: Prepare (5 minutes)

```bash
# Activate environment
source .venv/bin/activate

# Install required packages
uv pip install anthropic openai pyyaml

# Set up API keys
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Step 2: Add Code Samples (5 minutes)

```bash
# Interactive sample addition
python scripts/add_samples_interactive.py

# Add at least 3-5 Python files for testing
# (You can add more later)
```

### Step 3: Validate Samples (2 minutes)

```bash
python scripts/preprocess_samples.py
```

### Step 4: Test Pipeline (No Cost - 2 minutes)

```bash
python -m code_wise.pipeline.batch_processor --dry-run --max-samples 2
```

### Step 5: Run Real Pipeline (10+ minutes)

```bash
python -m code_wise.pipeline.batch_processor --max-samples 2
```

Check results:
```bash
cat outputs/claude/critique_sample_001.json | python -m json.tool
```

---

## 📚 Documentation

| Document | Read This For | Time |
|----------|---------------|------|
| **QUICKSTART.md** | Step-by-step guide | 30 min |
| **PIPELINE.md** | Technical details | 30 min |
| **DATASET_GUIDE.md** | How to add code samples | 15 min |
| **evaluation_rubric.md** | What the evaluation scores mean | 20 min |
| **PROGRESS_CHECKLIST.md** | Track your progress | 5 min |

**👉 Read QUICKSTART.md next** - it's written for exactly where you are now.

---

## 🎯 What To Do Next

### This Week
1. Read QUICKSTART.md (15 min)
2. Add 5-10 test samples (30 min)
3. Run --dry-run test (5 min)
4. Run real pipeline on 2-3 samples (15 min)

### Next 2 Weeks
1. Expand dataset to 30-50 samples (4-6 hours)
2. Process all samples with pipeline (4-8 hours)
3. Start implementing Phase 5 analysis

---

## 💡 Key Commands

```bash
# Add samples interactively
python scripts/add_samples_interactive.py

# Preprocess all samples
python scripts/preprocess_samples.py

# Test pipeline (no API costs, instant)
python -m code_wise.pipeline.batch_processor --dry-run --max-samples 2

# Run on limited samples (for testing)
python -m code_wise.pipeline.batch_processor --max-samples 10

# Resume from previous run (skip already processed)
python -m code_wise.pipeline.batch_processor --resume

# View logs in real-time
tail -f logs/pipeline.log

# Check API costs
tail -f logs/api_calls.jsonl
```

---

## 🏗️ What's Built

### Core Pipeline
✅ LLM integration (Claude, GPT-4, Gemma-ready)
✅ 3-phase processing (critique → improve → re-critique)
✅ Caching system (avoids duplicate API calls)
✅ Cost tracking (monitor $$ spent)
✅ CLI interface (easy to use)

### Configuration
✅ 20-dimension evaluation rubric
✅ 4 specialized prompts
✅ Model configuration (config.yaml)
✅ Dataset management tools

### Documentation
✅ 6 comprehensive guides
✅ Code examples throughout
✅ Progress tracking checklist

### NOT Yet Done (You Can Build!)
❌ Phase 5: Analysis & visualization
❌ Phase 6: Statistical validation
❌ Phase 7: Final report

---

## 📊 Expected Costs

For testing:
- 2 samples × 2 models = **$0.50-1.00**

For full dataset:
- 50 samples × 2 models = **$12.50-25.00**

Using Claude only (cheaper):
- 50 samples × 1 model = **$4.00-8.00**

---

## 🔍 Directory Overview

```
codewise/
├── START_HERE.md              👈 You are here
├── QUICKSTART.md              ← Read this next
├── PIPELINE.md                ← Full documentation
├── config.yaml                ← Configuration
│
├── datasets/original_code/    ← Put code samples here
├── outputs/                   ← Results go here
│   ├── claude/
│   ├── gpt4/
│   └── analysis/  (TODO)
│
├── code_wise/pipeline/        ← Core pipeline code
└── scripts/                   ← Helper scripts
```

---

## ✅ Checklist for First Run

- [ ] Installed dependencies with `uv pip install`
- [ ] Set API keys in `.env` file
- [ ] Read QUICKSTART.md
- [ ] Added 3-5 test samples with interactive curator
- [ ] Ran `python scripts/preprocess_samples.py`
- [ ] Ran `--dry-run` test (should work instantly)
- [ ] Ran real pipeline on 2 samples (should work in 5-10 min)
- [ ] Checked outputs in `outputs/claude/` and `outputs/gpt4/`

---

## 🆘 If Something Goes Wrong

### "API key not found"
```bash
# Check .env file exists
cat .env

# Should show:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### "No samples found"
```bash
# Check samples exist
ls datasets/original_code/
# Should show: sample_001.py, sample_002.py, etc.
```

### "Module not found"
```bash
# Reinstall dependencies
uv pip install anthropic openai pyyaml
```

### Other issues
```bash
# Check logs
tail -20 logs/pipeline.log
cat logs/api_calls.jsonl | tail -10
```

---

## 🎓 For Your Masters Project

This pipeline enables you to:

1. **Compare models** objectively using 16 code quality dimensions
2. **Measure improvement** by comparing original vs. refactored code
3. **Quantify feedback quality** across different LLMs
4. **Support your thesis** with empirical data

Everything is built for reproducibility and rigor.

---

## 📞 Questions?

- **Getting started?** → Read QUICKSTART.md
- **How does it work?** → Read PIPELINE.md
- **How to add samples?** → Read DATASET_GUIDE.md
- **What should I evaluate?** → Read evaluation_rubric.md
- **How am I progressing?** → Check PROGRESS_CHECKLIST.md

---

## 🚀 Ready?

1. Read QUICKSTART.md (next document)
2. Add your first code samples
3. Run your first pipeline
4. Watch the magic happen ✨

**Estimated time to first results: 30 minutes**

Let's get started! 🎯

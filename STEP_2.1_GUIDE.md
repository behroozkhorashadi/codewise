# Step 2.1: Curate Dataset of 30-70 Code Samples - Complete Guide

## Overview

You need to collect **30-70 code samples** with this breakdown:
- **15-20 samples**: Open-source Python code (from GitHub)
- **15-20 samples**: LLM-generated code (from Claude/GPT-4)
- **5-15 samples**: Intentionally problematic code

## Quick Start: Three Methods

### Method 1: Interactive Script (Easiest) ⭐ RECOMMENDED

```bash
# Activate your environment
source .venv/bin/activate

# Run the interactive curator
python scripts/add_samples_interactive.py
```

This will guide you through adding samples one by one with a menu interface.

### Method 2: Programmatic (Fast for Bulk)

Create a Python script to add multiple samples at once:

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()
curator.create_metadata_csv()

# Add your samples here (see examples below)
# ...

print(f"Total samples: {curator.get_sample_count()}")
```

### Method 3: Manual (For GitHub Code)

1. Copy code from GitHub
2. Save as `datasets/original_code/sample_XXX.py`
3. Manually edit `datasets/original_code/metadata.csv`

---

## Detailed Instructions by Sample Type

### Part A: Open-Source Code (15-20 samples)

#### Where to Find Code

**Option 1: Browse GitHub**
1. Go to https://github.com/search?q=language:python&type=Repositories
2. Filter by: Stars > 100, Recently updated
3. Look for utility functions, helper methods, or standalone functions

**Good Repositories to Check:**
- **Flask**: https://github.com/pallets/flask (web utilities)
- **Requests**: https://github.com/psf/requests (HTTP utilities)
- **Click**: https://github.com/pallets/click (CLI utilities)
- **Pandas**: https://github.com/pandas-dev/pandas (data processing)
- **Scikit-learn**: https://github.com/scikit-learn/scikit-learn (ML utilities)

**Option 2: Use GitHub Code Search**
- Search: `language:python function def` in popular repos
- Look for functions 20-100 lines long
- Extract single functions (not entire classes)

#### How to Add OSS Samples

**Using Interactive Script:**
```bash
python scripts/add_samples_interactive.py
# Choose: 1 (Add sample)
# Source: 1 (github)
# Then paste the code
```

**Using Python Script:**
```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()

# Example: Good utility function from GitHub
curator.add_sample(
    sample_id='oss_001',
    code_content='''
def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
''',
    source='github',
    category='utility',
    quality_expectation='good',
    description='Email validation function',
    source_url='https://github.com/example/repo',
    author='Original Author',
    license='MIT',
    complexity='low'
)
```

**What to Extract:**
- ✅ Single functions or methods (20-100 lines)
- ✅ Complete, runnable code
- ✅ Different categories: utilities, ML, web, data processing
- ❌ Don't extract: entire classes, incomplete snippets, test code

---

### Part B: LLM-Generated Code (15-20 samples)

#### How to Generate

**Option 1: Use Claude/GPT-4 Directly**
1. Go to claude.ai or chat.openai.com
2. Use this prompt template:

```
Write a Python function that [TASK].

Requirements:
- Include a docstring
- Add error handling
- Follow Python best practices
- The function should be complete and runnable
- Aim for 20-100 lines of code

Return ONLY the function code, no explanations.
```

**Task Ideas:**
- Calculate Fibonacci numbers efficiently
- Parse CSV files with error handling
- Validate email addresses
- Find duplicate items in a list
- Implement a cache with expiration
- Sort nested dictionaries
- Merge two sorted arrays
- Count word frequencies in a document
- Generate random passwords
- Format currency values
- Validate credit card numbers
- Convert between timezones
- Parse JSON with error handling
- Calculate distance between coordinates
- Generate unique IDs

**Option 2: Use the API (Programmatic)**

```python
import anthropic  # or openai

client = anthropic.Anthropic(api_key="your-key")

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": "Write a Python function that calculates the factorial of a number with error handling and a docstring."
    }]
)

code = response.content[0].text
# Then add to dataset using curator
```

#### How to Add LLM Samples

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()

# Example: LLM-generated code
curator.add_sample(
    sample_id='llm_001',
    code_content='''
def calculate_factorial(n: int) -> int:
    """Calculate the factorial of a number.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
''',
    source='llm_generated',
    category='utility',
    quality_expectation='good',
    description='Factorial calculator (generated by Claude)',
    author='Claude 3.5 Sonnet',
    complexity='low'
)
```

---

### Part C: Intentionally Problematic Code (5-15 samples)

#### What Makes Code "Bad"

Create or find code that violates quality criteria:
- ❌ Poor variable names (`x`, `d`, `temp`)
- ❌ Tight coupling (hard dependencies)
- ❌ Missing error handling
- ❌ Inefficient algorithms (O(n²) when O(n) possible)
- ❌ Over-complex functions (too many responsibilities)
- ❌ Security vulnerabilities
- ❌ Code smells (duplicate code, long methods)

#### How to Create Bad Samples

**Example 1: Poor Naming + Tight Coupling**
```python
def f(d):
    x = []
    for k in d:
        if isinstance(d[k], list):
            for i in range(len(d[k])):
                if d[k][i] > 0 and d[k][i] < 100:
                    x.append(d[k][i] * 2)
    return x
```

**Example 2: Missing Error Handling**
```python
def divide_numbers(a, b):
    return a / b  # No check for b == 0
```

**Example 3: Inefficient Algorithm**
```python
def find_max(numbers):
    max_val = numbers[0]
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if numbers[j] > max_val:
                max_val = numbers[j]
    return max_val  # O(n²) instead of O(n)
```

#### How to Add Bad Samples

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()

# Example: Intentionally bad code
curator.add_sample(
    sample_id='bad_001',
    code_content='''
def process_data(d):
    x = []
    for k in d:
        for i in range(len(d[k])):
            if d[k][i] > 0 and d[k][i] < 100:
                x.append(d[k][i] * 2)
    return x
''',
    source='intentionally_bad',
    category='data_processing',
    quality_expectation='bad',
    description='Poor naming and inefficient nested loops',
    complexity='medium',
    notes='Violates: naming, efficiency, clarity'
)
```

---

## Complete Example: Adding All Three Types

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()
curator.create_metadata_csv()

# ===== OPEN-SOURCE SAMPLES =====

# OSS Sample 1: Utility function
curator.add_sample(
    sample_id='oss_001',
    code_content='''
def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
''',
    source='github',
    category='utility',
    quality_expectation='good',
    description='Email validation',
    source_url='https://github.com/example/repo',
    license='MIT'
)

# OSS Sample 2: Data processing
curator.add_sample(
    sample_id='oss_002',
    code_content='''
def flatten_list(nested_list):
    """Flatten a nested list."""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result
''',
    source='github',
    category='data_processing',
    quality_expectation='good',
    description='List flattening utility'
)

# ===== LLM-GENERATED SAMPLES =====

# LLM Sample 1
curator.add_sample(
    sample_id='llm_001',
    code_content='''
def calculate_fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
''',
    source='llm_generated',
    category='utility',
    quality_expectation='good',
    description='Fibonacci calculator (Claude-generated)',
    author='Claude 3.5 Sonnet'
)

# LLM Sample 2
curator.add_sample(
    sample_id='llm_002',
    code_content='''
def merge_sorted_arrays(arr1: list, arr2: list) -> list:
    """Merge two sorted arrays."""
    result = []
    i = j = 0
    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1
    result.extend(arr1[i:])
    result.extend(arr2[j:])
    return result
''',
    source='llm_generated',
    category='utility',
    quality_expectation='good',
    description='Merge sorted arrays (GPT-4 generated)',
    author='GPT-4'
)

# ===== INTENTIONALLY BAD SAMPLES =====

# Bad Sample 1: Poor naming
curator.add_sample(
    sample_id='bad_001',
    code_content='''
def f(d):
    x = []
    for k in d:
        for i in range(len(d[k])):
            if d[k][i] > 0 and d[k][i] < 100:
                x.append(d[k][i] * 2)
    return x
''',
    source='intentionally_bad',
    category='data_processing',
    quality_expectation='bad',
    description='Poor variable names and inefficient loops',
    notes='Violates: naming, efficiency'
)

# Bad Sample 2: Missing error handling
curator.add_sample(
    sample_id='bad_002',
    code_content='''
def divide(a, b):
    return a / b
''',
    source='intentionally_bad',
    category='utility',
    quality_expectation='bad',
    description='No error handling for division by zero',
    notes='Violates: error handling'
)

print(f"\n✓ Total samples: {curator.get_sample_count()}")
curator.list_samples()
```

---

## Verification Checklist

After adding samples, verify:

```bash
# Check sample count
python -c "from scripts.curate_dataset import DatasetCurator; c = DatasetCurator(); print(f'Samples: {c.get_sample_count()}')"

# List all samples
python -c "from scripts.curate_dataset import DatasetCurator; DatasetCurator().list_samples()"

# Check files exist
ls -la datasets/original_code/*.py

# Check metadata CSV
head -5 datasets/original_code/metadata.csv
```

**Acceptance Criteria:**
- ✅ 30-70 samples in `datasets/original_code/`
- ✅ Each sample has a `.py` file
- ✅ `metadata.csv` exists with columns: sample_id, source, category, quality_expectation
- ✅ Roughly balanced: 15-20 OSS, 15-20 LLM, 5-15 bad
- ✅ Variety in categories (utility, ml, web, data_processing)

---

## Tips for Efficiency

1. **Batch Process**: Create a script with all samples and run once
2. **Use Templates**: Save common code patterns as templates
3. **GitHub Search**: Use advanced search filters to find good code quickly
4. **LLM Batch**: Generate 5-10 LLM samples in one session
5. **Reuse Bad Code**: Look for code review examples online (Stack Overflow, Reddit)

---

## Next Steps

Once you have 30-70 samples:

1. **Verify**: Run the checklist above
2. **Preprocess**: Run `python scripts/preprocess_samples.py`
3. **Continue**: Move to Step 2.2 (AST parsing and preprocessing)

---

## Troubleshooting

**Problem**: "Module not found" when running scripts
```bash
# Solution: Make sure you're in the project root
cd /Users/peejakhorashadi/masters_project/codewise
source .venv/bin/activate
```

**Problem**: Metadata CSV not updating
```bash
# Solution: Check file permissions
chmod 644 datasets/original_code/metadata.csv
```

**Problem**: Need to start over
```bash
# Solution: Clear and restart
rm -rf datasets/original_code/*.py
rm datasets/original_code/metadata.csv
python scripts/add_samples_interactive.py
```

Good luck with curation! 🚀


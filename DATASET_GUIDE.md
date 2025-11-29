# Dataset Curation Guide

This guide explains how to curate your 30-70 code samples for the research pipeline.

## Dataset Composition

Your dataset should include:

- **15-20 samples**: Open-source Python code (from GitHub)
- **15-20 samples**: LLM-generated code (from Claude, GPT-4, etc.)
- **5-15 samples**: Intentionally problematic code (with known issues)

## Where to Find Code Samples

### Option 1: Open-Source Code (GitHub)

Good sources for Python code:
- **Utility functions**: [Awesome Python](https://awesome-python.com/)
- **Real projects**: Search on GitHub for popular Python repos with good documentation
- **Specific domains**:
  - Data processing: pandas, numpy examples
  - Web: Flask, FastAPI snippets
  - ML: scikit-learn utilities
  - CLI tools: click, argparse examples

**How to extract samples**:
1. Find a public GitHub repo with good code quality
2. Copy a single function or method (typically 20-100 lines)
3. Save as `datasets/original_code/sample_XXX.py`
4. Record metadata using the curator script

**Example sources**:
- https://github.com/pallets/flask (web framework)
- https://github.com/pandas-dev/pandas (data manipulation)
- https://github.com/scikit-learn/scikit-learn (ML)
- https://github.com/psf/cpython (standard library examples)

### Option 2: Generate Code Using LLMs

Use Claude, GPT-4, or other models to generate code samples.

**Prompts to use**:
```
Write a Python function that [TASK].
The function should be well-structured and follow Python best practices.
Include a docstring and error handling.
```

**Task examples**:
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

**Important**: Document that these are LLM-generated and include the model name.

### Option 3: Intentionally Problematic Code

Create or find code with known issues:
- Tight coupling between modules
- Poor variable naming
- Missing error handling
- Inefficient algorithms
- Over-complex functions
- Security vulnerabilities
- Code smells (long methods, duplicate code, etc.)

**Example**: Create a function that violates multiple rubric criteria:
```python
# BAD: This violates multiple criteria
def f(d):
    x = []
    for k in d:
        if isinstance(d[k], list):
            for i in range(len(d[k])):
                if d[k][i] > 0:
                    x.append(d[k][i] * 2)
    return x
```

## Using the Dataset Curator Script

The `scripts/curate_dataset.py` script helps manage your dataset.

### Setup

```bash
python -c "
from scripts.curate_dataset import DatasetCurator
curator = DatasetCurator()
curator.create_metadata_csv()
"
```

### Add a Sample

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()

code = '''
def calculate_sum(numbers):
    \"\"\"Calculate sum of numbers.\"\"\"
    total = 0
    for n in numbers:
        total += n
    return total
'''

curator.add_sample(
    sample_id='sample_001',
    code_content=code,
    source='github',
    category='utility',
    quality_expectation='good',
    description='Simple sum calculator',
    source_url='https://github.com/example/repo',
    author='John Doe',
    license='MIT',
    complexity='low',
    notes='Extracted from main repo'
)
```

### List Samples

```python
curator.list_samples()
```

### Check Count

```python
print(f"Total samples: {curator.get_sample_count()}")
```

## Metadata Fields

For each sample, record:

| Field | Description | Example |
|-------|-------------|---------|
| sample_id | Unique identifier | sample_001 |
| source | Where code came from | github, llm_generated, intentionally_bad |
| category | Type of code | utility, ml, web, data_processing |
| quality_expectation | Expected quality | good, bad, average |
| description | What code does | Calculates word frequency |
| file_path | Path to .py file | datasets/original_code/sample_001.py |
| source_url | Original URL | https://github.com/... |
| author | Original author | GitHub username or "AI model" |
| license | License type | MIT, Apache, GPL, unknown |
| lines_of_code | Count of lines | 42 |
| complexity | Cognitive complexity | low, medium, high |
| notes | Special notes | "Simplified from larger function" |

## Quality Tips

1. **Variety**: Include different code styles and domains
2. **Size**: Aim for 20-100 lines per sample (not too small, not too large)
3. **Completeness**: Each sample should be a runnable function/method
4. **Balance**: Roughly equal split between good/bad/average code
5. **Documentation**: Always include source information and metadata

## Minimum Dataset for MVP

To get started quickly with an MVP (3-4 samples):

```python
from scripts.curate_dataset import DatasetCurator

curator = DatasetCurator()
curator.create_metadata_csv()

# Sample 1: Good open-source code
curator.add_sample(
    sample_id='oss_001',
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
    quality_expectation='good'
)

# Sample 2: LLM-generated code
curator.add_sample(
    sample_id='llm_001',
    code_content="""
def merge_sorted_lists(list1: list, list2: list) -> list:
    '''Merge two sorted lists.'''
    result = []
    i = j = 0
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result
""",
    source='llm_generated',
    category='utility',
    quality_expectation='good'
)

# Sample 3: Intentionally bad code
curator.add_sample(
    sample_id='bad_001',
    code_content="""
def process_data(d):
    x = []
    for k in d:
        for i in range(len(d[k])):
            if d[k][i] > 0 and d[k][i] < 100:
                x.append(d[k][i] * 2)
    return x
""",
    source='intentionally_bad',
    category='data_processing',
    quality_expectation='bad'
)

print(f"Created {curator.get_sample_count()} samples")
```

## Next Steps

Once you have 30-70 samples:
1. Run Phase 2.2 (preprocessing with AST parser)
2. Generate `intermediate/parsed_code_metadata.json`
3. Start Phase 3 (prompt template design)

Good luck with curation!

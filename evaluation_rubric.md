# Code Quality Evaluation Rubric

This comprehensive rubric evaluates Python code quality across **22 scoring dimensions**:
- **17 Code Quality Dimensions** (Codewise's 16 core criteria + dedicated Naming Quality dimension)
- **6 LLM Critique Quality Dimensions** (evaluates the quality of LLM-generated feedback)

The rubric is designed for both standalone code evaluation and comparative analysis of LLM code review capabilities.

## Quick Reference: All 22 Dimensions

### Code Quality Dimensions (17 total)
| # | Dimension | Focus |
|---|-----------|-------|
| 1 | Separation of Concerns | Single responsibility principle |
| 2 | Documentation | Docstrings, PEP 257 compliance |
| 3 | Logic Clarity | Correctness, Pythonic idioms |
| 4 | Understandability | Code readability, structure |
| 4.5 | **Naming Quality** | Variable/function/class naming clarity |
| 5 | Efficiency | Time/space complexity |
| 6 | Error Handling | Exception handling, edge cases |
| 7 | Testability | Unit test friendliness |
| 8 | Reusability | Modularity, flexibility |
| 9 | Code Consistency | PEP 8, conventions |
| 10 | Dependency Management | Module coupling |
| 11 | Security Awareness | Vulnerabilities, secure practices |
| 12 | Side Effects | Unintended state changes |
| 13 | Scalability | Performance under load |
| 14 | Resource Management | File/DB/network resource handling |
| 15 | Encapsulation and Access Control | Information hiding |
| 16 | Readability of Complex Logic | Complex logic decomposition |

### LLM Critique Quality Dimensions (6 total)
| # | Dimension | Focus |
|---|-----------|-------|
| 17 | Critique Actionability | Specificity and implementability of feedback |
| 18 | Critique Consistency | Consistency across similar code patterns |
| 19 | Refactoring Quality | Quality of suggested improvements |
| 20 | Rubric Alignment | Alignment with evaluation criteria |
| 21 | Code Review Depth | Comprehensiveness of analysis |
| 22 | Refactoring Feasibility | Practicality and safety of suggestions |

---

## Core Code Quality Dimensions (Based on Codewise)

### 1. Separation of Concerns
**Definition**: Does the method adhere to the single-responsibility principle, focusing on one clear task?

**Scoring Guide**:
- **9-10**: Method has a single, well-defined responsibility. No mixing of concerns.
- **7-8**: Generally focused, minor mixing of unrelated logic.
- **5-6**: Some responsibilities mixed; could be split into 2-3 methods.
- **3-4**: Multiple distinct concerns in one method; significant refactoring needed.
- **1-2**: Highly mixed concerns; method does multiple unrelated things.

**Example**: ✅ Good: Method validates user input only. ❌ Bad: Method validates input AND writes to database AND sends email in one function.

---

### 2. Documentation
**Definition**: Is the method well-documented with a clear docstring explaining purpose, parameters, and return values? (PEP 257 compliance)

**Scoring Guide**:
- **9-10**: Comprehensive docstring with purpose, params, return type, exceptions, and examples.
- **7-8**: Good docstring covering purpose, params, and returns; may lack examples.
- **5-6**: Basic docstring; missing parameter types or return description.
- **3-4**: Minimal or incomplete docstring; missing key information.
- **1-2**: No docstring or completely unhelpful documentation.

**Example**:
```python
# ✅ Good:
def calculate_tax(income: float, rate: float = 0.15) -> float:
    """
    Calculate tax based on income and rate.

    Args:
        income: Annual income in USD.
        rate: Tax rate (default 15%).

    Returns:
        Total tax amount.

    Raises:
        ValueError: If income or rate is negative.
    """
```

---

### 3. Logic Clarity
**Definition**: Are there obvious logical issues, potential bugs, or Python best practices violations?

**Scoring Guide**:
- **9-10**: Correct logic, no bugs, follows Pythonic idioms.
- **7-8**: Generally sound logic; minor inefficiencies or non-Pythonic patterns.
- **5-6**: Logic is correct but contains unnecessary complexity or awkward patterns.
- **3-4**: Logic has edge case bugs or significant violations of Python idioms.
- **1-2**: Major logical flaws, off-by-one errors, or fundamentally broken logic.

**Example**: ✅ Using `if not lst:` instead of ❌ `if len(lst) == 0:`.

---

### 4. Understandability (Code Readability)
**Definition**: Is code straightforward and easy to read? Are variable/function names descriptive and PEP 8 compliant?

**Scoring Guide**:
- **9-10**: Crystal clear; names are descriptive, PEP 8 compliant, easy to follow.
- **7-8**: Mostly clear; minor naming or structure issues.
- **5-6**: Readable but names could be more descriptive; moderate structure issues.
- **3-4**: Hard to follow; poor naming conventions; PEP 8 violations.
- **1-2**: Very difficult to understand; cryptic names, no clear structure.

**Example**: ✅ `user_email_list` vs ❌ `u_em_l` or `list1`.

---

### 4.5. Naming Quality
**Definition**: Are variable, function, and class names clear, descriptive, and self-documenting? Do names convey intent and follow Python naming conventions (snake_case for variables/functions, PascalCase for classes)?

**Scoring Guide**:
- **9-10**: Excellent naming; every identifier is self-documenting. Names reveal intent without needing comments. Full PEP 8 compliance.
  - ✅ `calculate_user_age()`, `is_valid_email`, `MAX_RETRY_ATTEMPTS`, `UserRepository`
- **7-8**: Good naming; mostly clear and descriptive. One or two opportunities for improvement.
  - ✅ `get_data()` (could be `get_user_data()`), consistent casing
- **5-6**: Acceptable naming; some names lack clarity. Would benefit from refinement.
  - ⚠️ `process_info()`, `temp_var`, `x1`, `list_of_things`
- **3-4**: Poor naming; many names are unclear or non-standard. Violates conventions.
  - ❌ `d` for data, `fn` for function, `getX()` mixing conventions, `TempVariable` for local variable
- **1-2**: Very poor naming; names are cryptic, inconsistent, or misleading. No apparent convention.
  - ❌ `a`, `temp123`, `bad_var_name_that_doesnt_describe_anything`, `x_y_z_final`

**Specific Criteria**:
- Single-letter names (except loop counters `i`, `j`, `k`) deduct points
- Boolean names should start with `is_`, `has_`, `can_`, `should_` (e.g., `is_active`, `has_permission`)
- Names should be pronounceable and searchable
- Acronyms should be avoided unless universally known (e.g., `url` is fine, `u` is not)
- Names should avoid `temp`, `tmp`, `data`, `info`, `thing`, `stuff` unless truly generic

**Example Naming Progression**:
- ❌ **Poor**: `def f(x): return x * 2`
- ⚠️ **Fair**: `def multiply(n): return n * 2`
- ✅ **Good**: `def double_value(number): return number * 2`
- ✅ **Excellent**: `def calculate_doubled_tax_basis(income_amount: float) -> float:`

---

### 5. Efficiency
**Definition**: Is the method optimized for performance? Avoid unnecessary loops, redundant calculations, or poor time complexity.

**Scoring Guide**:
- **9-10**: Optimal time/space complexity; no unnecessary operations.
- **7-8**: Generally efficient; minor redundancies.
- **5-6**: Acceptable performance; some avoidable inefficiencies (e.g., nested loops that could be flattened).
- **3-4**: Noticeably inefficient; O(n²) where O(n) is possible.
- **1-2**: Very inefficient; e.g., sorting inside a loop, repeated calculations.

**Example**: ✅ `if x in set(items)` vs ❌ `if x in [items]` (linear search each time).

---

### 6. Error Handling
**Definition**: Does the method handle edge cases gracefully and use exception handling appropriately?

**Scoring Guide**:
- **9-10**: All edge cases handled; specific exception types caught; informative error messages.
- **7-8**: Good error handling; minor gaps in edge cases.
- **5-6**: Basic error handling; catches some exceptions but may be too broad or too narrow.
- **3-4**: Minimal error handling; some edge cases unhandled.
- **1-2**: No error handling or catches all exceptions with bare `except:`.

**Example**: ✅ `except ValueError: ...` vs ❌ `except: ...`.

---

### 7. Testability
**Definition**: Is the method designed for straightforward unit testing? Avoid over-reliance on global state.

**Scoring Guide**:
- **9-10**: Pure function or clear I/O; easy to test with mocks if needed.
- **7-8**: Testable; may require minor setup.
- **5-6**: Testable but with some dependencies; requires test fixtures.
- **3-4**: Hard to test; relies on global state or external dependencies.
- **1-2**: Nearly impossible to test; tightly coupled to global state or singletons.

---

### 8. Reusability
**Definition**: Is the method modular and flexible for reuse in different contexts?

**Scoring Guide**:
- **9-10**: Highly modular; could be reused in many contexts; no hard-coded values.
- **7-8**: Generally reusable; minor specific dependencies.
- **5-6**: Somewhat reusable; some hard-coded values or specific data structure assumptions.
- **3-4**: Limited reusability; specific to one use case.
- **1-2**: Not reusable; tightly coupled to specific context.

---

### 9. Code Consistency
**Definition**: Does the method follow consistent Python conventions (PEP 8, indentation, spacing, import ordering)?

**Scoring Guide**:
- **9-10**: Consistent with project conventions; follows PEP 8 throughout.
- **7-8**: Mostly consistent; minor style variations.
- **5-6**: Some inconsistencies; would benefit from formatting tools.
- **3-4**: Several PEP 8 violations; inconsistent style.
- **1-2**: No apparent attempt at consistency; random formatting.

---

### 10. Dependency Management
**Definition**: Does the method avoid unnecessary dependencies or tight coupling? Are dependencies justified?

**Scoring Guide**:
- **9-10**: Minimal, justified dependencies; clear dependency injection.
- **7-8**: Good dependency management; minor unnecessary imports.
- **5-6**: Some unnecessary dependencies; generally decoupled.
- **3-4**: Several unnecessary dependencies; some tight coupling.
- **1-2**: Highly dependent on external modules; tightly coupled.

---

### 11. Security Awareness
**Definition**: Does the method avoid common security issues (SQL injection, data leaks, improper logging)?

**Scoring Guide**:
- **9-10**: Secure code; no obvious vulnerabilities; appropriate logging.
- **7-8**: Generally secure; minor concerns.
- **5-6**: No glaring issues; some areas could be hardened.
- **3-4**: Contains potential security risks (e.g., unsanitized input handling).
- **1-2**: Serious security vulnerabilities present.

---

### 12. Side Effects
**Definition**: Does the method minimize unintended changes to external state?

**Scoring Guide**:
- **9-10**: Pure function; no unintended side effects.
- **7-8**: Minimal side effects; clear when state is modified.
- **5-6**: Some side effects; mostly acceptable.
- **3-4**: Multiple side effects; some unintended or unclear.
- **1-2**: Significant, unexpected side effects; modifies global state.

---

### 13. Scalability
**Definition**: If used in high-traffic/large-scale scenarios, does it handle data efficiently under load?

**Scoring Guide**:
- **9-10**: Scales well; handles large datasets efficiently; no memory leaks.
- **7-8**: Scalable; minor performance concerns with large data.
- **5-6**: Acceptable for moderate loads; would struggle with large datasets.
- **3-4**: Poor scalability; significant performance degradation with size.
- **1-2**: Not scalable; fails or is extremely slow with large data.

---

### 14. Resource Management
**Definition**: Does the method correctly handle resources (file handles, DB connections, network calls)?

**Scoring Guide**:
- **9-10**: Proper resource management; uses context managers (`with` statements).
- **7-8**: Generally good; minor resource handling issues.
- **5-6**: Resources managed but not optimally; missing context managers.
- **3-4**: Poor resource handling; potential for leaks.
- **1-2**: No resource cleanup; likely resource leaks.

---

### 15. Encapsulation and Access Control
**Definition**: Does the method use appropriate access modifiers and minimize exposure of internals?

**Scoring Guide**:
- **9-10**: Proper encapsulation; uses `_` or `__` prefixes appropriately; minimal public API.
- **7-8**: Good encapsulation; minor exposure of internals.
- **5-6**: Adequate encapsulation; some over-exposure of details.
- **3-4**: Poor encapsulation; internals exposed.
- **1-2**: No attempt at encapsulation; all internals exposed.

---

### 16. Readability of Complex Logic
**Definition**: For intricate logic, is it broken down into smaller, well-named functions?

**Scoring Guide**:
- **9-10**: Complex logic well-decomposed; each sub-function is clear.
- **7-8**: Generally well-structured; could be slightly more modular.
- **5-6**: Some complex blocks; moderate decomposition.
- **3-4**: Complex logic not well-broken down; long nested structures.
- **1-2**: Very complex with no decomposition; hard to follow.

---

## LLM Code Review Comparison Dimensions

These dimensions evaluate the **quality of LLM critique** rather than the code itself.

### 17. Critique Actionability
**Definition**: Are the suggested improvements specific, concrete, and implementable?

**Scoring Guide**:
- **9-10**: Highly specific suggestions with code examples or clear instructions.
- **7-8**: Good suggestions; mostly concrete with minor vagueness.
- **5-6**: General suggestions; requires some interpretation.
- **3-4**: Vague feedback; hard to know how to implement.
- **1-2**: Non-actionable; criticizes without suggesting solutions.

**Example**:
- ✅ "Refactor the nested loops using a list comprehension: `result = [x*2 for x in items if x > 0]`"
- ❌ "Your loop could be more efficient."

---

### 18. Critique Consistency
**Definition**: Does the model give consistent feedback on similar code patterns?

**Scoring Guide** (evaluated across multiple samples):
- **9-10**: Highly consistent; same issues flagged for similar code patterns.
- **7-8**: Generally consistent; minor inconsistencies.
- **5-6**: Somewhat inconsistent; feedback varies for similar issues.
- **3-4**: Inconsistent; different feedback for same anti-pattern.
- **1-2**: Very inconsistent; contradictory feedback.

**Example**: If the model critiques `if len(x) == 0:` in Sample A, does it also flag it in Sample B?

---

### 19. Refactoring Quality
**Definition**: When the LLM suggests improvements, are the refactored versions actually better?

**Scoring Guide**:
- **9-10**: Refactored code is significantly better (more readable, efficient, maintainable).
- **7-8**: Improved code is noticeably better; minor issues remain.
- **5-6**: Some improvements; may introduce new issues.
- **3-4**: Marginal improvements; may be lateral changes.
- **1-2**: Refactored code is worse or breaks functionality.

**Measured by**: Re-evaluation score improvement, absence of regressions.

---

### 20. Rubric Alignment
**Definition**: Does the model's critique align with the evaluation rubric dimensions?

**Scoring Guide**:
- **9-10**: All critiques map directly to rubric dimensions; no arbitrary feedback.
- **7-8**: Most feedback aligns with rubric; some general comments.
- **5-6**: Partial alignment; some feedback outside rubric scope.
- **3-4**: Weak alignment; significant off-topic feedback.
- **1-2**: Little alignment; feedback focuses on arbitrary preferences.

**Example**:
- ✅ "This violates #3 (Logic Clarity): the nested ternary is hard to parse."
- ❌ "I don't like your variable names."

---

### 21. Code Review Depth
**Definition**: Does the model's review comprehensively analyze all aspects of the code, or does it focus on surface-level issues?

**Scoring Guide**:
- **9-10**: Deep analysis addressing multiple rubric dimensions; examines edge cases, performance implications, maintainability.
- **7-8**: Good depth; covers most important aspects; may miss minor considerations.
- **5-6**: Moderate depth; reviews 5-8 dimensions; misses some relevant aspects.
- **3-4**: Shallow; focuses on 2-3 dimensions; misses significant code issues.
- **1-2**: Very shallow; surface-level observations only; major blind spots.

**Measured by**: Number of distinct rubric dimensions addressed, depth of analysis per dimension, consideration of edge cases and long-term implications.

**Example**:
- ❌ **Shallow**: "This code works, but variable names could be better."
- ✅ **Deep**: "While the logic is correct, this method has three issues: (1) poor naming reduces clarity; (2) nested loops create O(n²) complexity; (3) no error handling for invalid inputs. Consider refactoring by extracting the inner loop into a helper function and adding validation at entry points."

---

### 22. Refactoring Feasibility
**Definition**: When the LLM suggests improvements, are they practical and achievable without introducing risk?

**Scoring Guide**:
- **9-10**: Suggestions are low-risk, backward-compatible, and easy to implement incrementally.
- **7-8**: Mostly practical; may require moderate effort but well-worth it.
- **5-6**: Some suggestions are practical; others may be risky or require significant refactoring.
- **3-4**: Suggestions are risky, break backward compatibility, or require extensive rewrites.
- **1-2**: Suggestions are impractical, unsafe, or impossible without major architectural changes.

**Measured by**: Technical feasibility, effort required, risk level, backward compatibility.

**Example**:
- ✅ **Feasible**: "Replace `if len(x) == 0:` with `if not x:` - simple text replacement, no behavioral change."
- ❌ **Infeasible**: "Refactor this entire module to use async/await" (without justifying why or addressing migration complexity).
- ❌ **Risky**: "Change the function signature to return a different type" (breaks API contract).

---

## Scoring Methodology

### Overall Score Calculation
For each code sample, two composite scores are calculated:

1. **Code Quality Score** (Dimensions 1-16 + 4.5): Average of all code quality dimensions (17 total, with Naming Quality as a dedicated dimension).
2. **LLM Review Score** (Dimensions 17-22): Average of critique quality dimensions (6 dimensions for evaluating LLM feedback).

### Score Interpretation
- **9-10**: Excellent (ready for production / excellent feedback)
- **7-8**: Good (minor improvements needed / good feedback)
- **5-6**: Fair (noticeable issues / acceptable feedback)
- **3-4**: Poor (significant issues / poor feedback)
- **1-2**: Very Poor (unacceptable / very poor feedback)

### Weighted Scoring (Optional)
For final analysis, dimensions can be weighted by importance:

**Code Quality Scoring (Dimensions 1-16 + 4.5)**:
- High priority (weight 2.0): Separation of Concerns (#1), Documentation (#2), Logic Clarity (#3), Naming Quality (#4.5)
- Medium priority (weight 1.5): Error Handling (#6), Testability (#7), Security Awareness (#11)
- Standard priority (weight 1.0): All others

**LLM Review Scoring (Dimensions 17-22)**:
- High priority (weight 2.0): Actionability (#17), Consistency (#18)
- Medium priority (weight 1.5): Code Review Depth (#21), Refactoring Feasibility (#22)
- Standard priority (weight 1.0): Refactoring Quality (#19), Rubric Alignment (#20)

---

## Evaluation Process

### Single Code Evaluation
1. Read code sample carefully.
2. Score each dimension 1-10 with brief justification.
3. Special attention to Naming Quality (#4.5) as explicit requirement.
4. Provide overall code quality score (average of Dimensions 1-16 + 4.5).

### Single LLM Critique Evaluation
1. Analyze the LLM's feedback on the code sample.
2. Score Dimensions 17-22 (critique quality dimensions):
   - Actionability (#17)
   - Consistency (#18)
   - Refactoring Quality (#19)
   - Rubric Alignment (#20)
   - Code Review Depth (#21)
   - Refactoring Feasibility (#22)
3. Provide overall LLM Review Score (average of Dimensions 17-22).

### Comparative Evaluation (For LLM Comparison Study)
1. Evaluate code sample with Rubric Dimensions 1-16 + 4.5 for Code Quality Score.
2. Collect critiques from multiple models (e.g., Claude, GPT-4, Gemma, etc.).
3. For each model's critique, score Dimensions 17-22 for LLM Review Score.
4. Track how each model's score changes after refactoring.
5. Analyze patterns in Naming Quality feedback (#4.5) across models.

---

## Usage in Pipeline

This rubric is integrated into the evaluation pipeline as follows:

1. **Code Evaluation Phase**: LLM receives rubric and scores code on Dimensions 1-16 + 4.5 (including Naming Quality).
2. **Critique Generation Phase**: LLM provides detailed feedback, particularly addressing weak dimensions.
3. **Improvement Phase**: LLM refactors code to improve weak dimensions, with special focus on Naming Quality where applicable.
4. **Re-Evaluation Phase**: LLM scores the improved version on Dimensions 1-16 + 4.5.
5. **Critique Quality Analysis Phase**: Researchers evaluate LLM feedback quality (Dimensions 17-22):
   - Does the feedback demonstrate depth (#21)?
   - Are suggestions actionable (#17) and feasible (#22)?
   - Does the feedback maintain consistency (#18) across samples?
   - Is the refactoring actually an improvement (#19)?
   - Does feedback align with rubric dimensions (#20)?

---

## Version History

- **v1.1** (2025-11-29): Enhanced rubric with Naming Quality as dedicated dimension (#4.5) + 2 additional LLM comparison dimensions (Code Review Depth #21, Refactoring Feasibility #22). Total: 22 scoring dimensions (17 for code quality, 6 for LLM critique quality). Updated evaluation process and pipeline integration documentation.

- **v1.0** (2025-11-02): Initial rubric with 16 Codewise criteria + 4 LLM-specific dimensions (20 total).

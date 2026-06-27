# CodeWise Demo Script

Master's project demo walkthrough for "Evaluating the Impact of Call Site Context on LLM Based Code Review Using Abstract Syntax Tree Analysis."

---

## How to Run the Demo

### Prerequisites

Make sure you have completed the initial setup at least once:

```bash
uv python install 3.13
uv python pin 3.13
uv venv
source .venv/bin/activate
uv pip install .
```

Make sure your `.env` file exists in the project root with both API keys:

```
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Starting the Demo

```bash
# From the project root
source .venv/bin/activate
python demo_gui.py
```

The GUI window will open at 1440×880. If running on an external monitor or presenting full-screen, you may want to increase your system font size or zoom before starting.

### Demo Steps (Quick Reference)

1. GUI opens → **Example 4** is pre-selected by default. Change it using the "Load example" dropdown if needed.
2. Confirm model is set to **Claude 3.5 Sonnet** (or switch to GPT-4o if you want to show the model toggle).
3. Click **▶ Analyze Code**.
4. Wait ~15–30 seconds for Phase 1 (Critique) to complete → tab auto-switches.
5. Wait ~15–30 seconds for Phase 2 (Improved Code) to complete → tab auto-switches.
6. Wait ~15–30 seconds for Phase 3 (Re-critique) to complete → tab auto-switches.
7. Talk through each tab after it populates.

Total runtime per analysis: approximately 45–90 seconds depending on API latency.

---

## Demo Script

### Before Opening the GUI

Set context before touching the screen:

> "My research investigates whether providing LLMs with *call-site context* — extracted automatically using AST analysis — changes the quality of AI-generated code reviews in measurable ways. To illustrate how the evaluation system works, I built this interactive demo that lets you see the core LLM pipeline in action: a model critiques a piece of code, rewrites it, then re-scores the result. This is the same scoring infrastructure that powered the full experiment."

---

### Step 1 — Load the Example

**Action:** Open the GUI. Leave the model on **Claude 3.5 Sonnet**. Select **"Example 4 — Mixed concerns, no resource mgmt"** from the "Load example" dropdown if it is not already selected.

**Say:**

> "I'm going to use a deliberately problematic function — one that mixes multiple responsibilities in a single block. It opens a file, parses CSV data, writes JSON output, calculates an average, and prints a result — all in one function with no error handling and no `with` statements for resource management. This kind of function is exactly what shows up in real codebases and exactly what the evaluation rubric is designed to catch."

---

### Step 2 — Explain the Model Selector and Rubric

**Action:** Point to the model dropdown without clicking yet.

**Say:**

> "I can switch between Claude Sonnet and GPT-4o — the same two models used in the actual experiment. One of my key findings is that these two models respond to the same code in systematically different directions, so the choice of model actually matters. I'll come back to that."

> "The evaluation rubric covers 16 dimensions of code quality — things like Separation of Concerns, Documentation, Error Handling, Resource Management, Efficiency. These map to the ISO/IEC 25010 software quality standard. Each is scored 1 through 10. The LLM returns structured JSON, so scores are machine-parseable and directly comparable across models and conditions."

---

### Step 3 — Run the Pipeline / Critique Tab

**Action:** Click **▶ Analyze Code**. Watch the progress bar advance to Phase 1. Wait for the Critique tab to populate (~15–30 seconds).

**Say while it is running:**

> "The pipeline makes API calls to the model's endpoint. I've set temperature to 0.2 — low enough to get consistent, reproducible output, but not zero, which would eliminate all natural variation and make it impossible to distinguish signal from the floor. The model receives the function body and the rubric as a structured prompt and returns a JSON object with all 16 dimension scores plus written feedback."

**Say once the Critique tab shows results — point to specific low-scoring bars:**

> "Look at Documentation — probably a 1 or 2, because there is no docstring at all. Resource Management will score low because the file handles are not opened with `with` statements, so if anything throws mid-function those handles leak. Separation of Concerns will also be low — this function is doing file I/O, data parsing, JSON serialization, aggregation, and printing, all in one place."

> "This is exactly the kind of feedback a human reviewer would give. The key contribution of my research is asking: does the model give *better* feedback when it can also see where and how this function is being called elsewhere in the codebase? That is the call-site context question."

---

### Step 4 — Improved Code Tab

**Action:** Phase 2 completes and the tab auto-switches. Point to the side-by-side code panes.

**Say:**

> "Phase 2 takes the critique as input and asks the model to rewrite the code to address the identified weaknesses. On the left is the original — 17 lines, mixed concerns, no error handling, open file handles. On the right is what the model produces."

> "You will typically see a docstring added, `with` statements for file handling so resources are always cleaned up, the parsing and serialization separated into their own logical blocks, and proper exception handling at the boundary. The model also explains each change it made in the list below."

> "This is the improvement phase. In my actual experiment, I did not run a rewrite step — the focus was on scoring, not generation. But this illustrates the downstream utility: a system that can score code can also guide systematic improvement."

---

### Step 5 — Re-critique Tab

**Action:** Phase 3 completes and the tab auto-switches. Point to the Before / After / Improvement score cards at the top, then gesture at the dimension comparison rows.

**Say:**

> "Phase 3 scores the improved version using the same rubric — a re-critique. Look at the delta between before and after. Documentation probably jumped from a 1 or 2 to a 7 or 8. Resource Management went from low to high because we now have proper context managers. Error Handling improved similarly."

> "This validates that the scoring system is working correctly — the dimensions the model identified as weak are the same ones that improved most after the rewrite. That internal consistency matters. One of my findings was that providing call-site context actually *reduces scoring variance* — both models assign more internally consistent scores across the 16 dimensions when they can see how a function is used. GPT-4o showed a 29% reduction in variance; Claude showed 8%."

---

### After the Demo — Connecting Back to the Research

> "What this demo shows is the evaluation infrastructure. The actual experiment ran this scoring system on 204 Python methods pulled from four production open-source libraries — requests, flask, click, and httpx — under two conditions. Condition A: function body only. Condition B: function body plus call-site context, where the call sites were extracted automatically using Python's `ast` module."

> "The AST extraction works by building a full parse tree for each file, then walking that tree to find every `Call` node. The key technical challenge is that Python's AST does not give you parent pointers natively — so I attach them manually before traversal, which lets me walk upward from any call node to its enclosing function definition. That enclosing function body becomes the call-site context passed to the LLM."

> "The experiment made 816 total API calls — 204 methods × 2 models × 2 conditions. The results were surprising. I had three research questions."

> "**RQ1 — Does context change scores?** Yes, but in opposite directions depending on the model. GPT-4o scored functions *higher* with context, with an overall delta of +0.31. Claude scored functions *slightly lower*, delta of −0.08. The biggest single effect was GPT-4o's Documentation score, which increased by +0.80 on average — nearly a full point on a 10-point scale. When GPT-4o can see how a function is called, it appears to interpret that as confirmation the function is well-documented enough for its callers to use it. Claude interprets the same call sites as a list of requirements the function might not fully satisfy."

> "**RQ2 — Does context make two models agree more?** Counterintuitively, no. Pearson r between the two models' scores dropped from 0.563 to 0.409 — a 27% reduction in agreement — consistently across all four libraries. I call this the *Confirmatory vs. Evaluative* hypothesis: GPT-4o uses call-site context as social proof that a function is working in practice; Claude uses it as a stricter benchmark revealing where the function falls short. More shared information actually amplified their differences rather than resolving them."

> "**RQ3 — Does context improve scoring consistency?** Yes, for both models. GPT-4o's per-method variance across dimensions dropped 29%, Claude's dropped 8%. Context anchors the model to something concrete — actual usage patterns — rather than abstract principles, which produces more internally coherent evaluations."

> "The practical implication is that if you are building an automated code review system, your choice of model is not neutral. It encodes an implicit theory of what good code review means. And the fix is not necessarily picking the right model — it is knowing which biases each model has and designing your system accordingly."

---

## Technical Questions — Prepared Answers

These are likely follow-up questions. Use whichever ones come up.

**Why AST and not regex or string search?**

> "AST gives you structural context — you know whether a token is a function call, a string literal, or a comment. Regex cannot distinguish `f()` inside a quoted string from an actual call. It also cannot tell you which enclosing function owns that call site without a full parse."

**How does the parent pointer traversal work?**

> "Python's `ast` module builds a downward tree — each node knows its children but not its parent. To walk upward from a `Call` node to its enclosing `FunctionDef`, I attach parent pointers to every node before traversal with a simple recursive function. Once those are in place, I walk the `.parent` chain from any call until I hit a `FunctionDef`, and that body becomes a call-site context entry."

**Why cap call sites at 10?**

> "Prompt length constraints. Highly-called utility functions can have dozens of call sites, and including all of them would push the prompt past the practical token limit. Ten was chosen as the minimum that provides meaningful usage diversity. A future improvement would be selecting the most informative call sites — ones that cover different code paths or argument types — rather than sampling randomly."

**Why temperature 0.2 and not 0?**

> "Temperature 0 would make the model fully deterministic, which sounds ideal for reproducibility. The problem is that on a 1-to-10 integer scale with a ceiling effect, zero temperature collapses variation in a way that makes it impossible to see signal in the deltas. 0.2 provides just enough variation to make scores meaningful while keeping outputs consistent enough to treat as reliable estimates."

**Why Pearson r for inter-model agreement and not Spearman or ICC?**

> "We are measuring linear co-variation between two numeric score vectors — whether a function GPT-4o scores high also receives a proportionally high score from Claude. Spearman ρ only captures rank order and discards magnitude information. Intraclass correlation would require both models to assign numerically identical scores, which is too strict a criterion — we care whether they rank methods similarly, not whether they use the same absolute scale. As a sensitivity check I computed Spearman ρ and it differed from Pearson r by less than 0.03 across the dataset, so the linear assumption holds."

**Why no p-values or inferential statistics?**

> "The 204 methods are the full experimental population, not a sample drawn from a larger population. Reporting p-values would imply a generalizability claim that the study design does not support. The results describe how call-site context changed LLM evaluation behavior for this specific dataset — the right framing is descriptive, not inferential."

**Why these four libraries specifically?**

> "They were chosen to maximize diversity across domain, architecture, and codebase size while keeping the dataset manageable. requests is a flat HTTP client. flask is a layered web framework mixing routing and context management. click uses decorators and context-passing patterns where many methods are only meaningful in a specific invocation chain — which makes call-site context especially relevant. httpx mirrors requests' public interface but adds async execution, letting us check whether the effect is consistent across synchronous and asynchronous APIs in the same domain."

**What is the Confirmatory vs. Evaluative hypothesis?**

> "It is my proposed explanation for why GPT-4o and Claude respond to context in opposite directions. Through a confirmatory lens — which seems to be GPT-4o's approach — call-site frequency and diversity serves as social proof: if many callers are using a function, it must be meeting their needs, so scores go up. Through an evaluative lens — Claude's approach — call sites expose additional requirements the function must satisfy, so scores go down when those requirements are not met. Both are defensible review strategies. A senior engineer deciding whether to ship code might be more confirmatory; an engineer doing a deep architecture review might be more evaluative. What is interesting is that two state-of-the-art models appear to have fully internalized these different frameworks consistently across four separate codebases."

---

## Which Example to Use

| Example | Best for showing... |
|---|---|
| Example 1 — Poor naming | Documentation, Understandability, Logic Clarity scores |
| Example 2 — God function | Separation of Concerns, Reusability, Testability scores |
| Example 3 — O(n²) duplicate finder | Efficiency, Scalability scores |
| **Example 4 — Mixed concerns** | **Resource Management, Separation of Concerns, Error Handling — most dramatic before/after** |

Example 4 is the recommended default for a demo because it hits the most rubric dimensions at once and produces the most visually striking before/after score comparison.

---

## Switching Models Mid-Demo

To show that different models score differently:

1. Run with Claude first. Note the overall score and which dimensions are lowest.
2. Paste the same code (or use the same example from the dropdown).
3. Switch to GPT-4o and run again.
4. Compare the overall scores side by side.

This connects directly to RQ1 and the Confirmatory vs. Evaluative finding: GPT-4o will typically score higher, Claude will often penalize more aggressively on efficiency and consistency dimensions.

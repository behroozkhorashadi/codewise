# Reference Summaries for Khorashadi Master's Thesis

**Thesis title:** "Evaluating the Impact of Call Site Context on LLM-Based Code Review Using Abstract Syntax Tree Analysis"

---

## Group 1: Code Review

---

### 1. bacchelli2013expectations — Bacchelli & Bird (2013)

**Full citation:** Alberto Bacchelli and Christian Bird. "Expectations, Outcomes, and Challenges of Modern Code Review." In *Proceedings of the 35th International Conference on Software Engineering (ICSE 2013)*, San Francisco, CA, USA, pp. 712–721. IEEE, 2013.

**Summary:** This paper presents an in-depth empirical study of modern code review practices at Microsoft, using observations, interviews, and surveys of 17 industrial developers and manual analysis of 570 review comments across 16 product teams. The study finds that while finding defects is the top stated motivation, reviews in practice yield far broader benefits including knowledge transfer, code improvement, team awareness, and alternative solutions. Crucially, it establishes that *code and change understanding* is the key challenge developers face during review.

**Relevance to thesis:** This paper establishes the empirical baseline for what human reviewers actually look for and what makes reviews valuable — dimensions beyond simple defect detection. The thesis proposes automating multi-dimensional code quality assessment via LLMs, and the quality criteria it evaluates (documentation, logic clarity, separation of concerns, etc.) map directly to the non-defect outcomes Bacchelli and Bird identify. The finding that reviewers prioritize understanding over pure defect detection also motivates why call-site context (which aids understanding) might shift LLM review scores.

**Key quotes:**
> "While finding defects remains the main motivation for review, reviews are less about defects than expected and instead provide additional benefits such as knowledge transfer, increased team awareness, and creation of alternative solutions to problems." — (Abstract)

> "Context and change understanding is the key aspect of code reviewing and that developers employ a wide range of mechanisms to meet their understanding needs, most of which are not met by current tools." — (Abstract)

> "[Code review] also has several beneficial influences: (1) makes people less protective about their code, (2) gives another person insight into the code, so there is (3) better sharing of information across the team, (4) helps support coding conventions on the team, and [...] (5) helps improving the overall process and quality of code." — (Section IV, developer quote)

---

### 2. sadowski2018modern — Sadowski, Söderberg, Church, Sipko & Bacchelli (2018)

**Full citation:** Caitlin Sadowski, Emma Söderberg, Luke Church, Michal Sipko, and Alberto Bacchelli. "Modern Code Review: A Case Study at Google." In *Proceedings of the 40th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP '18)*, Gothenburg, Sweden, May 27–June 3, 2018, pp. 1–10. ACM, 2018. DOI: 10.1145/3183519.3183525.

**Summary:** This paper makes an exploratory investigation of modern code review at Google, using 12 semi-structured interviews, a survey of 44 respondents, and log analysis of 9 million reviews over two years. It finds that review at Google is markedly lighter-weight than other contexts, centred on a single reviewer with small, quick changes, and that developer expectations cluster around four themes: education, maintaining norms, gatekeeping, and accident prevention. The paper concludes that the code review tool is used beyond collaborative review — also as an educational tool and for corroboration.

**Relevance to thesis:** The paper documents the norms and multi-dimensional expectations that practitioners bring to code review. The four expectation themes (education, norms, gatekeeping, accident prevention) align closely with the 16 quality criteria the thesis asks LLMs to score. By establishing what practitioners value in review, this paper contextualises why an automated, multi-criteria LLM reviewer is worth building and why context (call sites) might matter to those criteria.

**Key quotes:**
> "Employing lightweight, tool-based code review of code changes (aka modern code review) has become the norm for a wide variety of open-source and industrial systems." — (Abstract)

> "Reviewing was introduced at Google to ensure code readability and maintainability. Today's developers also perceive this educational aspect, in addition to maintaining norms, tracking history, gatekeeping, and accident prevention. Defect finding is welcomed but not the only focus." — (Finding 1, Section 4)

> "Expectations about a specific code review at Google depend on the work relationship between the author and reviewers." — (Finding 2, Section 4)

---

### 3. rigby2013convergent — Rigby & Bird (2013)

**Full citation:** Peter C. Rigby and Christian Bird. "Convergent Contemporary Software Peer Review Practices." In *Proceedings of the 2013 9th Joint Meeting on Foundations of Software Engineering (ESEC/FSE 2013)*, Saint Petersburg, Russia, pp. 202–212. ACM, 2013. DOI: 10.1145/2491411.2491444.

**Summary:** This paper examines code review data from six contemporary software projects (Android, Chrome, Bing, Office, MS SQL, AMD) and six historical open-source projects (Apache, Linux, KDE, etc.) to identify convergent practices across radically different organisational settings. Despite differences in culture, incentive systems, and time pressures, the study finds five converging traits of modern code review: it is lightweight and flexible, happens early, involves small changes, uses an optimal number of reviewers (~two), and has shifted from a defect-finding activity to a group problem-solving activity.

**Relevance to thesis:** Rigby and Bird's five convergent practices define what "standard" human code review looks like — the baseline against which LLM-based review is compared. The finding that reviews involve small changes reviewed by roughly two people in a lightweight manner is important context for why feeding an isolated method body plus call-site examples is a reasonable unit for LLM analysis. The shift from defect-finding to problem-solving also supports the thesis's multi-dimensional quality scoring approach.

**Key quotes:**
> "Despite the drastically different settings, cultures, incentive systems, time pressures, etc., the parameters of peer review converge in contemporary software projects." — (Abstract, paraphrased from Microsoft Research publication page)

> "Contemporary peer review follows a lightweight, flexible process." — (Table 1, Convergent Practice CP₁)

> "Review has changed from a defect finding activity to a group problem solving activity." — (Table 1, Convergent Practice CP₅)

---

### 4. mcintosh2016empirical — McIntosh, Kamei, Adams & Hassan (2016)

**Full citation:** Shane McIntosh, Yasutaka Kamei, Bram Adams, and Ahmed E. Hassan. "An Empirical Study of the Impact of Modern Code Review Practices on Software Quality." *Empirical Software Engineering*, vol. 21, no. 5, pp. 2146–2189. Springer, 2016. DOI: 10.1007/s10664-015-9381-9.

**Summary:** This paper conducts a case study of the Qt, VTK, and ITK open-source projects to measure how code review coverage, reviewer participation, and reviewer expertise relate to post-release defect density. It finds that all three dimensions share a statistically significant link with software quality, with poorly-reviewed code being substantially more likely to contain post-release defects. The study is notable for being one of the first large-scale empirical demonstrations that the *quality* of modern lightweight review — not just whether review happened — influences downstream defect rates.

**Relevance to thesis:** This paper provides the empirical motivation that code review quality matters quantifiably. Because the thesis evaluates whether *enriching* a review prompt with call-site context changes LLM quality scores, this paper's finding that reviewer expertise and participation (analogous to the richness of context available to a reviewer) affect quality outcomes provides a direct human-review parallel for the thesis's experimental design.

**Key quotes:**
> "The formal code inspection process mandates strict review criteria (e.g., in-person meetings and reviewer checklists) to ensure a base level of review quality, while the modern, lightweight code reviewing process does not." — (Abstract)

> "Code review coverage, participation, and expertise share a significant link with software quality." — (Abstract / Key Findings)

> "Our results empirically confirm the intuition that poorly-reviewed code has a negative impact on software quality in large systems using modern reviewing tools." — (Abstract)

---

### 5. czerwonka2015code — Czerwonka, Greiler & Tilford (2015)

**Full citation:** Jacek Czerwonka, Michaela Greiler, and Jack Tilford. "Code Reviews Do Not Find Bugs: How the Current Code Review Best Practice Slows Us Down." In *Proceedings of the 37th International Conference on Software Engineering (ICSE 2015)*, vol. 2, pp. 27–28. IEEE Press, 2015.

**Summary:** Drawing on experience and data from Microsoft, this short paper challenges the dominant assumption that bug detection is the primary value of code review. The authors find that only about 15% of review comments indicate a possible defect, and argue that effective reviews require reviewers with specific skills, that organisational and team experience correlates with review usefulness, and that the social dimension of review is irreplaceable. The paper calls for more precision in how review best practices are applied.

**Relevance to thesis:** This paper directly motivates multi-dimensional LLM code review: if human reviewers rarely find bugs and instead produce commentary spanning style, knowledge transfer, and design, then an LLM evaluator scoring 16 quality dimensions (as in the thesis) is actually more aligned with real review behaviour than a bug-finding tool. The finding that only ~15% of comments flag defects supports the thesis's broader quality-scoring approach.

**Key quotes:**
> "Code reviews are a standard part of the modern software engineering workflow. Since they require involvement of people, code reviewing is often the longest part of the code integration activities." — (Microsoft Research abstract page)

> "Only about 15% of comments provided by reviewers indicate a possible defect, much less a blocking defect." — (Key finding, cited in web summary of the paper)

> "Code review practices deserve to be better understood, systematized and applied to software engineering workflow with more precision than the best practice currently prescribes." — (Conclusion, Microsoft Research publication page)

---

## Group 2: LLM-Based Code Review

---

### 6. li2022codereviewer — Li, Lu, Guo, Duan et al. (2022)

**Full citation:** Zhiyu Li, Shuai Lu, Daya Guo, Nan Duan, Shailesh Jannu, Grant Jenks, Deep Majumder, Jared Green, Alexey Svyatkovskiy, Shengyu Fu, and Neel Sundaresan. "Automating Code Review Activities by Large-Scale Pre-training." In *Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE '22)*, Singapore, November 14–18, 2022. ACM, 2022. DOI: 10.1145/3540250.3549081.

**Summary:** This paper proposes CodeReviewer, a pre-trained encoder-decoder transformer model specialised for three code review tasks: code change quality estimation (predicting whether a diff needs a review comment), review comment generation (producing natural-language review text), and code refinement (revising code given a reviewer comment). The model is pre-trained on a new large-scale dataset of real-world code changes and reviews collected from nine programming languages on GitHub, using four novel pre-training tasks tailored to the diff format. CodeReviewer outperforms prior state-of-the-art models on all three tasks.

**Relevance to thesis:** CodeReviewer is the closest prior work to the thesis in the automated code review space. While the thesis uses a general-purpose LLM (GPT-4o) with structured prompting rather than a task-specific pre-trained model, CodeReviewer demonstrates that context in the diff format (which lines changed and surrounding code) is essential for meaningful review generation — a finding that directly motivates the thesis's hypothesis that adding call-site context improves LLM review quality.

**Key quotes:**
> "Code review is an essential part to software development lifecycle since it aims at guaranteeing the quality of codes." — (Abstract)

> "It turns out that developers have to spend far too much time reviewing the code of their peers. Accordingly, it is in significant demand to automate the code review process." — (Abstract)

> "Considering the naturalness of software, language models can capture general statistical properties of programs due to programs tend to be repetitive and predictable." — (Section 2.3, Code Review Generation)

---

### 7. Smolic2024MIPRO — Smolić, Pavelić, Boras, Mekterović & Jagušt (2024)

**Full citation:** E. Smolić, M. Pavelić, B. Boras, I. Mekterović, and T. Jagušt. "LLM Generative AI and Students' Exam Code Evaluation: Qualitative and Quantitative Analysis." In *Proceedings of the 47th MIPRO ICT and Electronics Convention (MIPRO 2024)*, Opatija, Croatia, May 20–24, 2024, pp. 1261–1266. IEEE, 2024. DOI: 10.1109/MIPRO60963.2024.10569820.

**Summary:** This paper evaluates whether GPT-3.5 and Gemini can reliably grade student C programming assignments on a percentage-score scale, using zero-shot and few-shot prompting against human TA grades. Human experts then independently evaluate the LLM commentary and score correspondence. The study finds that LLM commentary is often useful but not perfectly reliable, that score assignment aligns only moderately with human graders (GPT-3.5 Pearson r ≈ 0.64, Gemini r ≈ 0.23), and that few-shot prompting offers limited improvement in score alignment while improving contextual calibration.

**Relevance to thesis:** This paper is the closest direct precedent to the thesis's experimental design: it uses LLMs to evaluate code quality on a numeric scale, compares LLM scores to human baselines, and tests the impact of additional prompt context (few-shot examples). The thesis extends this line of work by (1) targeting professional Python code rather than student assignments, (2) systematically varying contextual input via AST-extracted call sites, and (3) using more capable models (GPT-4o, Claude Sonnet).

**Key quotes:**
> "Since the introduction of generative artificial intelligence (GAI) technology in the context of large language models (LLMs), it has been widely used for information extraction and/or extrapolation from different sources." — (Abstract)

> "LLMs are currently not capable of evaluating code or mathematical expressions with 100% reliability, i.e. beyond token pattern recognition and subsequent probabilistic answer generation." — (Abstract)

> "Commercial general LLMs can be useful in providing supplementary insight on code, but with required human supervision." — (Section V, Conclusion)

---

### 8. yuen2024prompting — Yuen, Pangas, Polash & Abdellatif (2025)

**Full citation:** Adam Yuen, John Pangas, Md Mainul Hasan Polash, and Ahmad Abdellatif. "Prompting Matters: Assessing the Effect of Prompting Techniques on LLM-Generated Class Code." In *Proceedings of the 2025 IEEE International Conference on Software Maintenance and Evolution (ICSME 2025)*, pp. 803–807. IEEE, 2025. DOI: 10.1109/ICSME64153.2025.00083.

**Summary:** This paper systematically evaluates four prompting strategies (Zero-Shot, Few-Shot, Chain-of-Thought, and CoT-Few-Shot) on GPT-4o and Llama3-70B for class-level Python code generation, using the ClassEval benchmark. It finds that contextual strategies (CoT, CoT-Few-Shot) achieve pass rates of ~83–85%, substantially outperforming Zero-Shot (~58%), and also produce code with higher BLEU-3 and ROUGE-L similarity to human-written oracle code. Zero-Shot prompting produced 536 test failures versus ~180 in all other strategies.

**Relevance to thesis:** This paper demonstrates that adding context to prompts — particularly examples and step-by-step reasoning — substantially changes LLM output quality for code tasks. The thesis applies a directly analogous logic: adding call-site context (real usage examples extracted via AST) to a code review prompt may substantially change how LLMs score quality. The paper's finding that "prompting strategies that incorporate reasoning or illustrative examples substantially improve LLM performance" is a key theoretical parallel for the thesis's experimental hypothesis.

**Key quotes:**
> "The performance of LLMs, particularly in code generation, is heavily dependent on prompting." — (Introduction)

> "Strategies incorporating more contextual guidance (Few-Shot, Chain-of-Thought, and Chain-of-Thought-Few-Shot) outperform Zero-Shot prompting by up to 25% in functional correctness, 31% in BLEU-3 score, and 50% in ROUGE-L." — (Abstract)

> "Prompting strategies that incorporate reasoning or illustrative examples substantially improve LLM performance by reducing structural, logical, and integration-related errors." — (Section IV, Overall Findings)

---

## Group 3: Foundation Models for Code

---

### 9. devlin2019bert — Devlin, Chang, Lee & Toutanova (2019)

**Full citation:** Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding." In *Proceedings of NAACL-HLT 2019*, Minneapolis, Minnesota, pp. 4171–4186. ACL, 2019. arXiv:1810.04805.

**Summary:** BERT introduces a new pre-training methodology for language representations based on masked language modelling (predicting randomly masked tokens) and next sentence prediction, trained on large unlabelled text corpora. Unlike prior unidirectional language models, BERT conditions on both left and right context simultaneously in all transformer layers, producing deeply bidirectional representations. Fine-tuned BERT achieved state-of-the-art results on eleven NLP benchmarks at the time of publication, including GLUE, SQuAD, and MultiNLI.

**Relevance to thesis:** BERT is the architectural ancestor of every code-focused pre-trained model cited in the thesis (CodeBERT, GraphCodeBERT, CodeReviewer, CodeT5). Understanding BERT's masked pre-training objective and fine-tuning paradigm is essential context for understanding why and how those code models work, and why general LLMs like GPT-4o differ from them (generation vs. representation learning). The thesis uses GPT-4o rather than BERT-family models precisely because generation is needed, not just representation.

**Key quotes:**
> "BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers." — (Abstract)

> "As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications." — (Abstract)

---

### 10. feng2020codebert — Feng, Guo, Tang, Duan et al. (2020)

**Full citation:** Zhangyin Feng, Daya Guo, Duyu Tang, Nan Duan, Xiaocheng Feng, Ming Gong, Linjun Shou, Bing Qin, Ting Liu, Daxin Jiang, and Ming Zhou. "CodeBERT: A Pre-Trained Model for Programming and Natural Languages." In *Findings of EMNLP 2020*, pp. 1536–1547. ACL, 2020. arXiv:2002.08155.

**Summary:** CodeBERT is a bimodal transformer pre-trained on both natural language and six programming languages (Python, Java, JavaScript, PHP, Ruby, Go) using a hybrid objective combining masked language modelling and replaced token detection. It achieves state-of-the-art performance on natural language code search and code documentation generation. Unlike purely code-oriented models, CodeBERT learns to align the semantic spaces of natural language descriptions and programming language constructs.

**Relevance to thesis:** CodeBERT is a foundational model for the domain in which the thesis operates (understanding both natural language prompts and Python code). It demonstrates that joint NL-PL pre-training yields better code understanding than either language alone — a finding that supports why a general LLM with strong NL capability (GPT-4o) can be effective for code review when given rich natural-language context (call-site usage descriptions).

**Key quotes:**
> "We present CodeBERT, a bimodal pre-trained model for programming language (PL) and natural language (NL)." — (Abstract)

> "CodeBERT learns general-purpose representations that support downstream NL-PL applications such as natural language code search, code documentation generation, etc." — (Abstract)

> "Results show that CodeBERT achieves state-of-the-art performance on both natural language code search and code documentation generation." — (Abstract)

---

### 11. wang2021codet5 — Wang, Wang, Joty & Hoi (2021)

**Full citation:** Yue Wang, Weishi Wang, Shafiq Joty, and Steven C.H. Hoi. "CodeT5: Identifier-aware Unified Pre-trained Encoder-Decoder Models for Code Understanding and Generation." In *Proceedings of EMNLP 2021*, pp. 8696–8708. ACL, 2021. arXiv:2109.00859.

**Summary:** CodeT5 introduces a unified encoder-decoder transformer architecture for code that explicitly exploits developer-assigned identifiers (variable names, function names) via a novel identifier-aware pre-training task. Unlike encoder-only models such as CodeBERT, CodeT5 supports both code understanding and generation tasks within a single framework. It achieves state-of-the-art results across a wide range of code tasks including defect detection, clone detection, code summarisation, and code generation.

**Relevance to thesis:** CodeT5's identifier-aware pre-training directly reflects the insight that meaningful identifiers carry rich semantic information about what code does — an insight central to the thesis, where method names and parameter names extracted via AST analysis provide the LLM with important semantic context alongside call-site examples. CodeReviewer (li2022codereviewer) is initialised from CodeT5, making it the direct technical predecessor of the most relevant prior automated code review system.

**Key quotes:**
> "Pre-trained models for Natural Languages (NL) like BERT and GPT have been recently shown to transfer well to Programming Languages (PL)." — (Abstract)

> "We present CodeT5, a unified pre-trained encoder-decoder Transformer model that better leverages the code semantics conveyed from the developer-assigned identifiers." — (Abstract)

> "Comprehensive experiments show that CodeT5 significantly outperforms prior methods on understanding tasks such as code defect detection and clone detection." — (Abstract)

---

### 12. alon2019code2vec — Alon, Zilberstein, Levy & Yahav (2019)

**Full citation:** Uri Alon, Meital Zilberstein, Omer Levy, and Eran Yahav. "code2vec: Learning Distributed Representations of Code." In *Proceedings of the ACM on Programming Languages (POPL 2019)*, vol. 3, pp. 1–29. ACM, 2019. arXiv:1803.09473.

**Summary:** code2vec presents a neural model that encodes code snippets as fixed-length continuous vectors by decomposing each snippet into a collection of paths through its Abstract Syntax Tree (AST). An attention mechanism aggregates these path-context vectors into a single code embedding, which is then used to predict semantic properties — specifically, method names. Trained on 14 million Java methods, the model achieves a 75% relative improvement over prior work on method name prediction.

**Relevance to thesis:** code2vec is directly relevant because it establishes the AST path-decomposition paradigm for code representation — the same class of structural analysis that the thesis uses (Python AST traversal to collect method definitions and call sites). The thesis's approach of extracting call-site context via AST analysis is a natural extension of code2vec's insight that AST paths encode meaningful semantic properties of code.

**Key quotes:**
> "We present a neural model for representing snippets of code as continuous distributed vectors ('code embeddings')." — (Abstract)

> "We demonstrate the effectiveness of our approach by using it to predict a method's name from the vector representation of its body." — (Abstract)

> "We decompose code to a collection of paths in its abstract syntax tree, and [learn] ... both a representation for each path and a model for aggregating a set of them." — (Introduction)

---

### 13. guo2021graphcodebert — Guo, Ren, Lu, Feng, Tang et al. (2021)

**Full citation:** Daya Guo, Shuo Ren, Shuai Lu, Zhangyin Feng, Duyu Tang, Shujie Liu, Long Zhou, Nan Duan, Alexey Svyatkovskiy, Shengyu Fu, Michele Tufano, Shao Kun Deng, Colin Clement, Dawn Drain, Neel Sundaresan, Jian Yin, Daxin Jiang, and Ming Zhou. "GraphCodeBERT: Pre-training Code Representations with Data Flow." In *Proceedings of ICLR 2021*. arXiv:2009.08366.

**Summary:** GraphCodeBERT extends CodeBERT by incorporating semantic-level structural information: instead of treating code as a flat token sequence or using syntactic AST structure, it uses the data-flow graph, which encodes where each variable's value comes from. Two structure-aware pre-training tasks are added alongside masked language modelling, implemented through a graph-guided masked attention mechanism. GraphCodeBERT achieves state-of-the-art performance on code search, clone detection, code translation, and code refinement.

**Relevance to thesis:** GraphCodeBERT's use of data-flow relationships between variables is conceptually parallel to the thesis's use of call-site context: both provide the model with information about how code components relate to each other *at runtime*, not just what they look like syntactically. The thesis's argument that call-site usage changes LLM scoring is grounded in the same semantic insight that data-flow information (rather than syntax alone) is needed for deep code understanding.

**Key quotes:**
> "Pre-trained models for programming language have achieved dramatic empirical improvements on a variety of code-related tasks such as code search, code completion, code summarization, etc." — (Abstract)

> "Instead of taking syntactic-level structure of code like abstract syntax tree (AST), we use data flow in the pre-training stage, which is a semantic-level structure of code that encodes the relation of 'where-the-value-comes-from' between variables." — (Abstract)

> "We evaluate our model on four tasks, including code search, clone detection, code translation, and code refinement." — (Abstract)

---

### 14. allamanis2018survey — Allamanis, Barr, Devanbu & Sutton (2018)

**Full citation:** Miltiadis Allamanis, Earl T. Barr, Premkumar Devanbu, and Charles Sutton. "A Survey of Machine Learning for Big Code and Naturalness." *ACM Computing Surveys*, vol. 51, no. 4, pp. 1–37. ACM, 2018. arXiv:1709.06182.

**Summary:** This survey systematically reviews research at the intersection of machine learning, programming languages, and software engineering, covering probabilistic models of source code that exploit its statistical regularities. The paper introduces a taxonomy of model families (token-level, tree-level, graph-level, etc.), contrasts programming languages with natural languages, and reviews applications including code completion, bug detection, code summarisation, and method naming. It establishes the "naturalness hypothesis" — that code is a form of human communication exhibiting repetitive patterns amenable to statistical modelling.

**Relevance to thesis:** This survey provides the conceptual foundation for why LLMs can be applied to code understanding and review. The naturalness hypothesis justifies the use of language models for code tasks, and the taxonomy of code representations (including AST-based approaches) situates the thesis's AST parsing methodology within the broader ML-for-code literature. The survey also surveys method naming and code summarisation tasks that are closely related to the quality criteria the thesis evaluates.

**Key quotes:**
> "Research at the intersection of machine learning, programming languages, and software engineering has recently taken important steps in proposing learnable probabilistic models of source code that exploit code's abundance of patterns." — (Abstract)

> "We contrast programming languages against natural languages and discuss how these similarities and differences drive the design of probabilistic models." — (Abstract)

> "The promise and power of machine learning rests on its ability to generalize from examples and handle noise." — (Introduction)

---

## Group 4: LLMs and In-Context Learning

---

### 15. chen2021codex — Chen, Tworek, Jun, Yuan et al. (2021)

**Full citation:** Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde de Oliveira Pinto, Jared Kaplan, Harri Edwards, Yuri Burda, Nicholas Joseph, Greg Brockman, et al. "Evaluating Large Language Models Trained on Code." arXiv:2107.03374. OpenAI, 2021.

**Summary:** This paper introduces Codex, a GPT language model fine-tuned on 159 GB of Python code from GitHub, and evaluates it on HumanEval — a new benchmark of 164 hand-written programming problems. A 12B-parameter Codex model solves 28.8% of problems with a single sample, and the Codex-S variant (further fine-tuned on correctly implemented standalone functions) solves 37.7%. Repeated sampling with 100 attempts per problem solves 70.2%. The paper also introduces the pass@k metric for evaluating functional correctness of code generation.

**Relevance to thesis:** Codex (and its successor GPT-4o, used in the thesis) demonstrates that LLMs trained on code can perform sophisticated code understanding tasks with no task-specific fine-tuning — purely from natural language prompts. The thesis relies on this same capability: it prompts GPT-4o to review code quality without fine-tuning. Codex's HumanEval benchmark also established the Python function-from-docstring setting that is closely related to the thesis's per-method analysis unit.

**Key quotes:**
> "We introduce Codex, a GPT language model fine-tuned on publicly available code from GitHub, and study its Python code-writing capabilities." — (Abstract)

> "On HumanEval, a new evaluation set we release to measure functional correctness for synthesizing programs from docstrings, our model solves 28.8% of the problems, while GPT-3 solves 0% and GPT-J solves 11.4%." — (Abstract)

> "We find that repeated sampling from the model is a surprisingly effective strategy for producing working solutions to difficult prompts." — (Abstract)

---

### 16. brown2020gpt3 — Brown, Mann, Ryder, Subbiah et al. (2020)

**Full citation:** Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. "Language Models are Few-Shot Learners." In *Advances in Neural Information Processing Systems (NeurIPS 2020)*, vol. 33, pp. 1877–1901. 2020. arXiv:2005.14165.

**Summary:** GPT-3 is a 175-billion-parameter autoregressive language model that achieves strong few-shot performance across dozens of NLP tasks without any gradient updates or fine-tuning, purely through in-context examples or instructions in the prompt. The paper demonstrates that model scale dramatically improves task-agnostic few-shot performance, sometimes rivalling fine-tuned models. It also introduces the three in-context learning settings: zero-shot, one-shot, and few-shot.

**Relevance to thesis:** GPT-3 is the direct architectural ancestor of GPT-4o used in the thesis, and the paper establishes the theoretical basis for the thesis's entire approach: that sufficiently large language models can perform novel tasks (including code review with multi-dimensional quality scoring) from prompt-specified instructions and examples alone. The few-shot setting described in GPT-3 is precisely the mechanism by which the thesis's prompts work.

**Key quotes:**
> "By contrast, humans can generally perform a new language task from only a few examples or from simple instructions – something which current NLP systems still largely struggle to do." — (Abstract)

> "Here we show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches." — (Abstract)

> "GPT-3 is applied without any gradient updates or fine-tuning, with tasks and few-shot demonstrations specified purely via text interaction with the model." — (Abstract)

---

### 17. wei2022chain — Wei, Wang, Schuurmans, Bosma et al. (2022)

**Full citation:** Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." In *Advances in Neural Information Processing Systems (NeurIPS 2022)*, vol. 35, pp. 24824–24837. 2022. arXiv:2201.11903.

**Summary:** This paper introduces chain-of-thought prompting, where few-shot exemplars in the prompt include intermediate reasoning steps (the "chain of thought") rather than just input-output pairs. Experiments across three large language models show that this technique substantially improves performance on arithmetic, commonsense, and symbolic reasoning tasks. Crucially, chain-of-thought reasoning only emerges reliably in sufficiently large models (above ~100B parameters).

**Relevance to thesis:** Chain-of-thought prompting is a critical prompt engineering technique that supports the thesis's approach. The thesis's prompts ask LLMs to reason about 16 quality dimensions and justify their scores — a form of structured chain-of-thought. The paper's finding that adding intermediate reasoning steps produces better, more reliable outputs from LLMs directly supports the thesis's use of detailed rubric-based prompting over simple one-shot scoring.

**Key quotes:**
> "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning." — (Abstract)

> "In particular, we show how such reasoning abilities emerge naturally in sufficiently large language models via a simple method called chain-of-thought prompting, where a few chain of thought demonstrations are provided as exemplars in prompting." — (Abstract)

> "Experiments on three large language models show that chain-of-thought prompting improves performance on a range of arithmetic, commonsense, and symbolic reasoning tasks." — (Abstract)

---

### 18. ouyang2022instructgpt — Ouyang, Wu, Jiang, Almeida et al. (2022)

**Full citation:** Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, John Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul Christiano, Jan Leike, and Ryan Lowe. "Training Language Models to Follow Instructions with Human Feedback." In *Advances in Neural Information Processing Systems (NeurIPS 2022)*, vol. 35, pp. 27730–27744. 2022. arXiv:2203.02155.

**Summary:** This paper presents InstructGPT, a GPT-3 model fine-tuned with reinforcement learning from human feedback (RLHF) to better follow user instructions. Starting from a set of labeller-written prompts, the method uses supervised learning on demonstrated outputs followed by a reward model trained on human preference rankings. The resulting 1.3B-parameter InstructGPT model is preferred by human evaluators over the 175B GPT-3 base model despite being 100x smaller, with improvements in truthfulness and reductions in harmful output.

**Relevance to thesis:** InstructGPT is the direct predecessor to the GPT-4o model used in the thesis, and this paper explains *why* modern GPT models follow structured natural-language instructions reliably — a property the thesis depends on when asking GPT-4o to score code quality across 16 named dimensions and provide written justifications. The alignment between human preferences and model outputs also underpins the thesis's use of LLM scores as proxies for human quality judgments.

**Key quotes:**
> "Making language models bigger does not inherently make them better at following a user's intent." — (Abstract)

> "In this paper, we show an avenue for aligning language models with user intent on a wide range of tasks by fine-tuning with human feedback." — (Abstract)

> "Outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3, despite having 100x fewer parameters." — (Abstract)

---

## Group 5: LLMs as Evaluators

---

### 19. zheng2023judging — Zheng, Chiang, Sheng, Zhuang et al. (2023)

**Full citation:** Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." In *Advances in Neural Information Processing Systems (NeurIPS 2023) Datasets and Benchmarks Track*. 2023. arXiv:2306.05685.

**Summary:** This paper systematically studies the use of strong LLMs (particularly GPT-4) as automated judges of open-ended LLM responses, introducing MT-Bench (a multi-turn question set) and Chatbot Arena (a crowdsourced battle platform) as calibration benchmarks. It identifies key failure modes of LLM judges — position bias, verbosity bias, and self-enhancement bias — and proposes mitigation strategies. The central finding is that GPT-4 as a judge achieves over 80% agreement with human preference judgments, matching inter-human agreement levels.

**Relevance to thesis:** This paper is the most direct methodological foundation for the thesis's use of LLMs (GPT-4o, Claude Sonnet) as evaluators of code quality. The LLM-as-a-judge paradigm validated here is exactly the paradigm the thesis employs. The documented biases (position, verbosity, self-enhancement) are important threats to validity that the thesis must acknowledge, and the 80% human-agreement finding provides the strongest empirical argument that LLM scores are meaningful proxies for human quality assessments.

**Key quotes:**
> "Evaluating large language model (LLM) based chat assistants is challenging due to their broad capabilities and the inadequacy of existing benchmarks in measuring human preferences." — (Abstract)

> "Our results reveal that strong LLM judges like GPT-4 can match both controlled and crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement between humans." — (Abstract)

> "LLM-as-a-judge is a scalable and explainable way to approximate human preferences, which are otherwise very expensive to obtain." — (Abstract)

---

### 20. liu2023geval — Liu, Iter, Xu, Wang, Xu & Zhu (2023)

**Full citation:** Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, and Chenguang Zhu. "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment." In *Proceedings of EMNLP 2023*, pp. 2511–2522. ACL, 2023. arXiv:2303.16634.

**Summary:** G-Eval is a framework for automatic natural language generation (NLG) evaluation that uses GPT-4 with chain-of-thought prompting and a structured form-filling paradigm. The evaluator is provided with evaluation criteria, a chain-of-thought explanation of what to consider, and asked to score a generated text on each criterion. On summarisation tasks, G-Eval with GPT-4 achieves a Spearman correlation of 0.514 with human judgments, outperforming all prior methods by a large margin. The paper also identifies and documents a bias toward LLM-generated text.

**Relevance to thesis:** G-Eval's methodology is extremely close to the thesis's approach: a GPT-4 model is prompted with explicit evaluation criteria and a structured scoring form to assess text quality. The thesis applies the same paradigm to code quality, with 16 criteria and a 1–10 scoring scale for each. The G-Eval finding that LLM-based evaluation outperforms traditional metrics validates the thesis's choice to use LLM scores as the primary evaluation signal.

**Key quotes:**
> "The quality of texts generated by natural language generation (NLG) systems is hard to measure automatically." — (Abstract)

> "Conventional reference-based metrics, such as BLEU and ROUGE, have been shown to have relatively low correlation with human judgments, especially for tasks that require creativity and diversity." — (Abstract)

> "We show that G-Eval with GPT-4 as the backbone model achieves a Spearman correlation of 0.514 with human on summarization task, outperforming all previous methods by a large margin." — (Abstract)

---

### 21. liang2022helm — Liang, Bommasani, Lee, Tsipras, Soylu et al. (2023)

**Full citation:** Percy Liang, Rishi Bommasani, Tony Lee, Dimitris Tsipras, Dilara Soylu, Michihiro Yasunaga, Yian Zhang, Deepak Narayanan, Yuhuai Wu, Ananya Kumar, et al. "Holistic Evaluation of Language Models." *Transactions on Machine Learning Research*, August 2023. arXiv:2211.09110.

**Summary:** HELM (Holistic Evaluation of Language Models) presents a comprehensive benchmark framework for evaluating 30 prominent language models across 42 scenarios and 7 metric categories (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency). The framework's key innovations are its top-down taxonomy of scenarios and desiderata, its multi-metric approach that refuses to reduce evaluation to a single accuracy number, and standardised evaluation conditions that allow direct model comparisons. Prior to HELM, models on average were evaluated on only 17.9% of the core scenarios.

**Relevance to thesis:** HELM's multi-metric, holistic evaluation philosophy directly mirrors the thesis's 16-dimension code quality scoring approach. Both reject single-metric reduction in favour of structured, multi-dimensional evaluation. HELM also provides the methodological precedent for using LLMs to evaluate on multiple dimensions simultaneously, and its standardisation principles (same scenarios, same metrics, same conditions across models) are directly applicable to the thesis's two-model, two-condition experimental design comparing GPT-4o and Claude Sonnet with and without call-site context.

**Key quotes:**
> "Language models (LMs) are becoming the foundation for almost all major language technologies, but their capabilities, limitations, and risks are not well understood." — (Abstract)

> "We adopt a multi-metric approach: We measure 7 metrics (accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency) for each of 16 core scenarios to the extent possible (87.5% of the time), ensuring that metrics beyond accuracy don't fall to the wayside." — (Abstract)

> "Holistic evaluation builds transparency by assessing language models in their totality. Rather than honing in on a specific aspect, we strive for a fuller characterization of language models to improve scientific understanding and orient societal impact." — (Introduction)

---

*Document compiled for Khorashadi Master's Thesis, 2026. All quotes are drawn verbatim from paper abstracts, introductions, or key results sections as indicated.*

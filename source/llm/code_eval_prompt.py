prompt = """
    Task: Evaluate the quality of each method on a scale of 1 to 10, where 1 represents a poorly written method and 10 represents an excellent method. Consider the following criteria when scoring:
        1.  Separation of Concerns: Does the method adhere to the single-responsibility principle, focusing on one clear task?
        2.  Documentation: Is the method well-documented with a clear, descriptive docstring explaining its purpose, parameters, and return values? Documentation should align with Python's style and conventions (PEP 257).
        3.  Logic Clarity: Are there any obvious logical issues or potential bugs in the method? Does the logic follow Pythonic idioms and best practices, making it easy to understand?
        4.  Understandability: Is the code straightforward and easy to read? Are variable and function names descriptive and compliant with PEP 8 naming conventions?
        5.  Efficiency: Is the method optimized for performance, particularly with regards to time-complexity and memory usage? Avoid unnecessary loops, list comprehensions, or redundant calculations.
        6.  Error Handling: Does the method handle potential edge cases gracefully, using Python's exception handling appropriately to manage unexpected inputs or conditions?
        7.  Testability: Is the method designed to make unit testing straightforward? Avoid over-reliance on global state, and ensure the method has clear input/output behavior.
        8.  Reusability: Is the method modular and flexible enough to be reused in different contexts, without unnecessary dependencies on specific data structures or modules?
        9.  Code Consistency: Does the method follow consistent Python conventions, like indentation (PEP 8), spacing, and ordering (e.g., imports, helper functions)? Consistency improves readability and maintainability.
        10. Dependency Management: Does the method avoid unnecessary dependencies or tightly coupling with external modules? If it does rely on other modules, are these dependencies clear and justified?
        11. Security Awareness: Does the method avoid common Python security issues, such as using untrusted data in SQL queries or mishandling sensitive data? Ensure that logging is appropriate and non-sensitive.
        12. Side Effects: Does the method make unintended changes to objects or variables outside its scope? Side effects should be minimized unless they're explicitly required.
        13. Scalability: If the method is likely to be used in high-traffic or large-scale scenarios, does it handle data efficiently, avoid excessive memory consumption, and work effectively under load?
        14. Resource Management: Does the method correctly handle resources like file handles, database connections, or network calls? For instance, use Python's with statements to manage resources safely and prevent leaks.
        15. Encapsulation and Access Control: Does the method use appropriate access modifiers and minimize exposure of internal workings? Private methods or functions (using _ prefix) should be used where needed.
        16. Readability of Complex Logic: For more intricate logic, does the method break it down into smaller, well-named functions? Deeply nested structures or long functions should be refactored for clarity.

    IMPORTANT: Return your evaluation ONLY as valid JSON (no additional text or markdown). Use the following JSON structure:
    {{
        "overall_score": <integer 1-10>,
        "overall_feedback": "<general assessment of the method>",
        "criteria_scores": {{
            "separation_of_concerns": <1-10>,
            "documentation": <1-10>,
            "logic_clarity": <1-10>,
            "understandability": <1-10>,
            "efficiency": <1-10>,
            "error_handling": <1-10>,
            "testability": <1-10>,
            "reusability": <1-10>,
            "code_consistency": <1-10>,
            "dependency_management": <1-10>,
            "security_awareness": <1-10>,
            "side_effects": <1-10>,
            "scalability": <1-10>,
            "resource_management": <1-10>,
            "encapsulation": <1-10>,
            "readability": <1-10>
        }},
        "criteria_feedback": {{
            "separation_of_concerns": "<brief feedback or null>",
            "documentation": "<brief feedback or null>",
            "logic_clarity": "<brief feedback or null>",
            "understandability": "<brief feedback or null>",
            "efficiency": "<brief feedback or null>",
            "error_handling": "<brief feedback or null>",
            "testability": "<brief feedback or null>",
            "reusability": "<brief feedback or null>",
            "code_consistency": "<brief feedback or null>",
            "dependency_management": "<brief feedback or null>",
            "security_awareness": "<brief feedback or null>",
            "side_effects": "<brief feedback or null>",
            "scalability": "<brief feedback or null>",
            "resource_management": "<brief feedback or null>",
            "encapsulation": "<brief feedback or null>",
            "readability": "<brief feedback or null>"
        }},
        "suggestions": ["<improvement suggestion 1>", "<improvement suggestion 2>", ...],
        "strengths": ["<strength 1>", "<strength 2>", ...]
    }}

    Here is the input for you to analyze:

    Method Definition:
    {method_body}

    {usage_example}

    Provide ONLY the JSON response with no additional text.
    """


def generate_code_evaluation_prompt(method_body: str, usage_example: str = "") -> str:
    """
    Generate a code evaluation prompt by injecting the method definition and optional usage example.

    Args:
        method_body (str): The code block for the method to evaluate.
        usage_example (str): An optional usage example for the method.

    Returns:
        str: The full prompt with the injected method and usage example.
    """

    # Inject method and usage example dynamically
    return prompt.format(
        method_body=method_body.strip(),
        usage_example=(f"Usage Example:\n{usage_example.strip()}" if usage_example else ""),
    )

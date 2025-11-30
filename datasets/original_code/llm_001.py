def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number efficiently.

    Uses iterative approach for O(n) time complexity.

    Args:
        n: Non-negative integer representing position in sequence

    Returns:
        The nth Fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Fibonacci sequence is not defined for negative numbers")
    if n < 2:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

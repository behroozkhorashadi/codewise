def merge_sorted_arrays(arr1: list, arr2: list) -> list:
    """Merge two sorted arrays into a single sorted array.

    Args:
        arr1: First sorted array
        arr2: Second sorted array

    Returns:
        Merged sorted array
    """
    result = []
    i = j = 0

    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1

    # Add remaining elements
    result.extend(arr1[i:])
    result.extend(arr2[j:])

    return result

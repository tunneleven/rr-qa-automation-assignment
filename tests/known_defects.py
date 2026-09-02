"""Narrow failure type for confirmed product-defect signatures."""


class KnownDefectError(AssertionError):
    """Signal only a reproduced, documented product-defect signature."""

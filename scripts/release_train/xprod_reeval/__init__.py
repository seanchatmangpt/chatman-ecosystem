"""Re-evaluation of committed cross-product cases.

This package lives outside ``cross_product_court`` on purpose: it touches
bytes on disk and (online mode only) the GitHub API, while the court itself
stays a pure function over an admitted case with no consequence surface.
"""

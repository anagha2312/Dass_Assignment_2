"""Convenience runner for MoneyPoly tests.

Run from q1/moneypoly:
    python test_import.py
"""

import unittest

from moneypoly.test_import import *  # noqa: F401,F403


if __name__ == "__main__":
    unittest.main(verbosity=2)

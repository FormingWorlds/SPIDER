"""SPIDER pytest suite.

A regular package (not a namespace package) so that ``tests._json_utils``
imports resolve here even when an installed third-party distribution
ships a stray top-level ``tests`` package.
"""

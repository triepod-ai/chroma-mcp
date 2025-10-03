#!/usr/bin/env python3
"""
Main entry point for running chroma_mcp as a module.

This allows execution via: python -m chroma_mcp
"""

from .server import main

if __name__ == "__main__":
    main()
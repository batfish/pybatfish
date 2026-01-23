#!/usr/bin/env python3
"""Strip execution metadata and Python version from notebooks for comparison."""

import sys
from pathlib import Path

import nbformat


def strip_metadata(nb_path):
    """Remove execution timestamps and Python version from notebook."""
    nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)

    # Strip execution metadata from cells
    for cell in nb.cells:
        if "execution" in cell.metadata:
            del cell.metadata["execution"]

    # Strip Python version from language_info if present
    if "language_info" in nb.metadata and "version" in nb.metadata.language_info:
        del nb.metadata.language_info["version"]

    nbformat.write(nb, nb_path)


if __name__ == "__main__":
    for nb_path in sys.argv[1:]:
        strip_metadata(Path(nb_path))

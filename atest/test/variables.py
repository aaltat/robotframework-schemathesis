from pathlib import Path


def get_variables():
    return {
        "LIBRARY_OUTPUT_DIR_BASE": str(Path(__file__).parent.parent / "output_library"),
        "LIBRARY_PYTHON_PATH": str(Path(__file__).parent.parent.parent),
    }

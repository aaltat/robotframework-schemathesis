from pathlib import Path

from robot.api import logger


def get_suite_path(suite_source: str) -> str:
    """Returns library suite path based on the runner suite ${SUITE SOURCE}."""
    logger.info(f"Suite source: {suite_source}")
    suite_source_path = Path(suite_source).absolute()
    suite_file = suite_source_path.name
    library_path = suite_source_path.parent.parent / "library" / suite_file
    return str(library_path)


def get_suite_output_path(suite_source: str, output_dir: str) -> str:
    suite_source_cleaned = suite_source.replace(".robot", "")
    suite_source_path = Path(suite_source_cleaned)
    suite_name = suite_source_path.parts[-1]
    output_dir_path = Path(output_dir)
    return str(output_dir_path / suite_name)

from pathlib import Path

from robot.api import logger


def get_suite_path(suite_source: str) -> str:
    """Returns library suite path based on the runner suite ${SUITE SOURCE}."""
    logger.info(f"Suite source: {suite_source}")
    suite_source = Path(suite_source).absolute()
    suite_file = suite_source.name
    library_path = suite_source.parent.parent / "library" / suite_file
    return str(library_path)


def get_suite_output_path(suite_source: str, output_dir: str) -> str:
    suite_source = suite_source.replace(".robot", "")
    suite_source = Path(suite_source)
    suite_source = suite_source.parts[-1]
    output_dir = Path(output_dir)
    return str(output_dir / suite_source)

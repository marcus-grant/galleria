import settings
from pathlib import Path
from typing import Optional, List


def ls_full(path: Optional[str | Path] = None) -> List[Path]:
    if path is None:
        path = settings.PIC_SOURCE_PATH_FULL
    root = Path(path)
    if not root.exists():
        return []

    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    result = []

    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            result.append(file_path)

    return result

import logging
import json
from pathlib import Path
from app.utils.ocr import ocr_processor

logger = logging.getLogger(__name__)

class DocumentLoader:
    def load(self, file_path: str, content_type: str = None) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        try:
            if ext == ".pdf":
                return self._load_pdf(path)
            elif ext in [".txt", ".md"]:
                return path.read_text(encoding="utf-8")
            elif ext == ".json":
                return json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
            elif ext in [".jpg", ".png", ".jpeg", ".tiff", ".bmp"]:
                return ocr_processor.process_image(str(path))
            else:
                return f"Unsupported file type: {ext}"
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return ""

    def _load_pdf(self, path: Path) -> str:
        # Pypdf logic is now handled inside ocr_processor.process_scanned_pdf 
        # which attempts extraction AND OCR on images
        return ocr_processor.process_scanned_pdf(str(path))

loader = DocumentLoader()

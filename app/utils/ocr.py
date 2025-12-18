import logging
import pytesseract
from PIL import Image
import shutil
import os
import sys

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Implements OCR using Tesseract.
    Requires Tesseract binary installed on the system.
    """
    
    def __init__(self):
        # Attempt to find tesseract in common paths (Windows/Linux) if needed,
        # or rely on PATH.
        self._check_tesseract_availability()

    def _check_tesseract_availability(self):
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR detected.")
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found in PATH. Please install Tesseract-OCR.")
            # For Windows, sometimes we might need to set the path explicitly if known, 
            # but standard practice is adding to PATH.
        except Exception as e:
            logger.warning(f"Tesseract check failed: {str(e)}")

    def process_image(self, file_path: str) -> str:
        """
        Extract text from an image file.
        """
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            if not text.strip():
                return "[OCR_PROCESSED] No text found in image."
            
            return text
        except Exception as e:
            logger.error(f"OCR Failed for {file_path}: {e}")
            return f"[OCR_ERROR] Failed to process image: {str(e)}"

    def process_scanned_pdf(self, file_path: str) -> str:
        """
        Handle PDF that has no text layer (scanned).
        Uses pdf2image or similar? 
        Wait, requirements.txt doesn't have pdf2image/poppler which is heavy.
        Simple fallback: Log expectation or try to use pypdf if it supports images (it doesn't do OCR).
        
        Correction: To do PDF OCR properly without heavy poppler deps, 
        we often need to convert PDF to images first.
        
        Given constraints ("No Docker", "Easy to run"), installing Poppler for pdf2image is hard for users.
        
        Strategy: Warn user that PDF OCR requires Poppler, OR 
        if the user uploads an IMAGE, it works. 
        For PDF, we will return a message saying "Please upload scanned documents as individual images for OCR" 
        unless we want to add `pdf2image` and ask user to install Poppler.
        
        Let's try to be helpful: The user demanded "Scanned PDFs must not be ignored".
        I will add a note that for Scanned PDFs, they should ideally be images, 
        but if I can't convert PDF->Image easily without Poppler, I will note this limitation.
        
        ACTUALLY: I can try to extract images FROM the PDF using pypdf and then OCR them.
        """
        text_content = ""
        try:
            import pypdf
            from io import BytesIO
            
            reader = pypdf.PdfReader(file_path)
            
            for i, page in enumerate(reader.pages):
                # 1. Try text extraction
                page_text = page.extract_text()
                if page_text and page_text.strip():
                     text_content += page_text + "\n"
                
                # 2. Extract images for OCR
                # Loop through images on the page
                for image_file_object in page.images:
                    try:
                        # image_file_object.data is the bytes
                        image = Image.open(BytesIO(image_file_object.data))
                        ocr_text = pytesseract.image_to_string(image)
                        if ocr_text.strip():
                             text_content += f"\n[Page {i+1} Image OCR]:\n{ocr_text}\n"
                    except Exception as img_err:
                        logger.warning(f"Failed to OCR image on page {i}: {img_err}")
            
            if not text_content.strip():
                 return "[OCR_EMPTY] Could not extract text or OCR images from PDF."
                 
            return text_content
            
        except ImportError:
             return "pypdf not installed."
        except Exception as e:
            logger.error(f"PDF OCR Error: {e}")
            return f"[OCR_ERROR] {str(e)}"

ocr_processor = OCRProcessor()

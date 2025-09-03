"""
File processing service for extracting text content from various file formats.
Supports PDF, Word documents, and images with OCR.
"""

import os
import io
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import mimetypes

# PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PDF_AVAILABLE = True
        USE_PDFPLUMBER = True
    except ImportError:
        PDF_AVAILABLE = False
        USE_PDFPLUMBER = False

# Word document processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Image OCR processing
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 100000  # Maximum extracted text length

# Supported file types
SUPPORTED_FILE_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/bmp': 'image',
    'image/tiff': 'image',
    'text/plain': 'text'
}


class FileProcessor:
    """File processing service for extracting text content."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"File processor initialized with temp dir: {self.temp_dir}")
    
    def is_supported_file_type(self, content_type: str) -> bool:
        """Check if the file type is supported."""
        return content_type in SUPPORTED_FILE_TYPES
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size is within limits."""
        return file_size <= MAX_FILE_SIZE
    
    async def extract_text_from_file(self, file_content: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Extract text content from uploaded file based on its type.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            file_type = SUPPORTED_FILE_TYPES.get(content_type)
            if not file_type:
                logger.warning(f"Unsupported file type: {content_type}")
                return None
            
            # Create temporary file
            temp_file_path = os.path.join(self.temp_dir, filename)
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            
            text_content = None
            
            if file_type == 'pdf':
                text_content = await self._extract_from_pdf(temp_file_path)
            elif file_type in ['docx', 'doc']:
                text_content = await self._extract_from_word(temp_file_path)
            elif file_type == 'image':
                text_content = await self._extract_from_image(temp_file_path)
            elif file_type == 'text':
                text_content = await self._extract_from_text(temp_file_path)
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            # Limit text length
            if text_content and len(text_content) > MAX_TEXT_LENGTH:
                text_content = text_content[:MAX_TEXT_LENGTH] + "\n\n[Text truncated due to length limit]"
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from file {filename}: {str(e)}")
            return None
    
    async def _extract_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            logger.error("PDF processing not available. Install PyPDF2 or pdfplumber.")
            return None
        
        try:
            if USE_PDFPLUMBER:
                import pdfplumber
                text_content = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                return "\n\n".join(text_content)
            else:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = []
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                    return "\n\n".join(text_content)
                    
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return None
    
    async def _extract_from_word(self, file_path: str) -> Optional[str]:
        """Extract text from Word document."""
        if not DOCX_AVAILABLE:
            logger.error("Word document processing not available. Install python-docx.")
            return None
        
        try:
            doc = Document(file_path)
            text_content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error processing Word document: {str(e)}")
            return None
    
    async def _extract_from_image(self, file_path: str) -> Optional[str]:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE:
            logger.error("OCR processing not available. Install pytesseract and pillow.")
            return None
        
        try:
            # Open image with PIL
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            # Support both English and Chinese
            text_content = pytesseract.image_to_string(image, lang='eng+chi_sim')
            
            # Clean up the extracted text
            text_content = text_content.strip()
            if not text_content:
                logger.warning("No text found in image")
                return None
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            return None
    
    async def _extract_from_text(self, file_path: str) -> Optional[str]:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except Exception:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        return file.read()
                except Exception as e:
                    logger.error(f"Error reading text file: {str(e)}")
                    return None
    
    def cleanup(self):
        """Clean up temporary directory."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {str(e)}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup()


# Global file processor instance
_file_processor = None

def get_file_processor() -> FileProcessor:
    """Get or create global file processor instance."""
    global _file_processor
    if _file_processor is None:
        _file_processor = FileProcessor()
    return _file_processor

def cleanup_file_processor():
    """Manually cleanup the global file processor."""
    global _file_processor
    if _file_processor is not None:
        _file_processor.cleanup()
        _file_processor = None
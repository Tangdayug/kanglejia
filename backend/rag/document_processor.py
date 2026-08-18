"""
Document Processor - Extract text from PDF/Word documents and prepare for vectorization
"""
import os
from typing import List, Dict, Any
from pathlib import Path

# Document processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


class DocumentProcessor:
    """Process documents (PDF/Word) and extract text content"""

    # 最大回退距离，避免在寻找分隔符时回退太远
    MAX_LOOKBACK = 100

    def __init__(self, knowledge_base_path: str):
        """
        Initialize document processor

        Args:
            knowledge_base_path: Path to knowledge base directory
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.chunk_size = 500  # Characters per chunk
        self.chunk_overlap = 50  # Overlap between chunks

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is not installed. Install with: pip install PyPDF2")

        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extract text from Word document

        Args:
            docx_path: Path to Word file

        Returns:
            Extracted text content
        """
        if DocxDocument is None:
            raise ImportError("python-docx is not installed. Install with: pip install python-docx")

        text = ""
        try:
            doc = DocxDocument(docx_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX {docx_path}: {e}")
            return ""

        return text

    def extract_text_from_txt(self, txt_path: str) -> str:
        """
        Extract text from plain text file

        Args:
            txt_path: Path to TXT file

        Returns:
            Extracted text content
        """
        text = ""
        try:
            # 尝试 UTF-8；失败则回退到 GBK，兼容中文 Windows 生成的文本
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    with open(txt_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Error reading TXT {txt_path}: {e}")
            return ""

        return text

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks for vectorization

        Args:
            text: Text content to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of text chunks with metadata
        """
        if metadata is None:
            metadata = {}

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings with limited lookback
                search_start = max(start, end - self.MAX_LOOKBACK)
                for delimiter in ['。', '！', '？', '. ', '! ', '? ', '\n\n']:
                    last_pos = text.rfind(delimiter, search_start, end)
                    if last_pos != -1:
                        end = last_pos + len(delimiter)
                        break
                else:
                    # 如果没找到句子分隔符，尝试在空格处断开
                    space_pos = text.rfind(' ', max(start, end - 50), end)
                    if space_pos != -1:
                        end = space_pos + 1

            chunk = text[start:end].strip()
            if chunk:
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = len(chunks)
                chunk_metadata['text_length'] = len(chunk)
                chunks.append({
                    'text': chunk,
                    'metadata': chunk_metadata
                })

            start = end - self.chunk_overlap if end < text_length else end

        return chunks

    def load_documents(self) -> List[Dict[str, Any]]:
        """
        Load all documents from knowledge base

        Returns:
            List of document chunks with metadata
        """
        all_chunks = []

        if not self.knowledge_base_path.exists():
            print(f"Knowledge base path does not exist: {self.knowledge_base_path}")
            return all_chunks

        # Supported file extensions
        pdf_extensions = ['.pdf']
        docx_extensions = ['.docx', '.doc']
        txt_extensions = ['.txt']

        # Walk through directory
        for file_path in self.knowledge_base_path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                relative_path = file_path.relative_to(self.knowledge_base_path)

                print(f"Processing file: {file_path}")

                # Extract text based on file type
                text = ""
                if ext in pdf_extensions:
                    text = self.extract_text_from_pdf(str(file_path))
                elif ext in docx_extensions:
                    text = self.extract_text_from_docx(str(file_path))
                elif ext in txt_extensions:
                    text = self.extract_text_from_txt(str(file_path))
                else:
                    continue

                if not text:
                    continue

                # Chunk the text
                metadata = {
                    'source': str(relative_path),
                    'filename': file_path.name,
                    'file_type': ext
                }
                chunks = self.chunk_text(text, metadata)
                all_chunks.extend(chunks)

                print(f"  Extracted {len(text)} characters, created {len(chunks)} chunks")

        return all_chunks


def get_document_processor(knowledge_base_path: str = None) -> DocumentProcessor:
    """Get or create document processor instance"""
    from common.constant import RAG_KNOWLEDGE_BASE_PATH

    if knowledge_base_path is None:
        knowledge_base_path = os.getenv("RAG_KNOWLEDGE_BASE_PATH", RAG_KNOWLEDGE_BASE_PATH)

    return DocumentProcessor(knowledge_base_path)

"""
Content Extraction Tool
Extracts clean text from HTML pages and PDF documents
"""

import os
import logging
import requests
from typing import Optional, Dict
from urllib.parse import urlparse
import trafilatura
from pypdf import PdfReader
import io
import tempfile

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Tool for extracting content from web pages and PDFs"""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the content extractor
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_content(self, url: str) -> Dict[str, str]:
        """
        Extract content from a URL (HTML or PDF)
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary with extracted content, title, and metadata
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Download the content
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'pdf' in content_type or url.lower().endswith('.pdf'):
                return self._extract_pdf_content(response.content, url)
            else:
                return self._extract_html_content(response.text, url)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return {
                'content': '',
                'title': '',
                'url': url,
                'error': f"Failed to fetch content: {str(e)}",
                'success': False
            }
        except Exception as e:
            logger.error(f"Unexpected error extracting content from {url}: {str(e)}")
            return {
                'content': '',
                'title': '',
                'url': url,
                'error': f"Content extraction failed: {str(e)}",
                'success': False
            }
    
    def _extract_html_content(self, html: str, url: str) -> Dict[str, str]:
        """
        Extract content from HTML using trafilatura
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            # Use trafilatura to extract clean text
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                favor_precision=True
            )
            
            if not content:
                # Fallback: try basic extraction
                content = trafilatura.extract(html, favor_recall=True)
            
            if not content:
                return {
                    'content': '',
                    'title': '',
                    'url': url,
                    'error': 'No content could be extracted from HTML',
                    'success': False
                }
            
            # Extract title
            title = trafilatura.extract_metadata(html).title or "Untitled"
            
            return {
                'content': content.strip(),
                'title': title.strip(),
                'url': url,
                'word_count': len(content.split()),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"HTML extraction failed for {url}: {str(e)}")
            return {
                'content': '',
                'title': '',
                'url': url,
                'error': f"HTML extraction failed: {str(e)}",
                'success': False
            }
    
    def _extract_pdf_content(self, pdf_content: bytes, url: str) -> Dict[str, str]:
        """
        Extract content from PDF using pypdf
        
        Args:
            pdf_content: PDF file content as bytes
            url: Source URL
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            # Create a file-like object from bytes
            pdf_file = io.BytesIO(pdf_content)
            
            # Read PDF
            pdf_reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            if not text_content:
                return {
                    'content': '',
                    'title': '',
                    'url': url,
                    'error': 'No text content found in PDF',
                    'success': False
                }
            
            content = '\n\n'.join(text_content)
            
            # Try to get title from PDF metadata
            title = "PDF Document"
            try:
                if pdf_reader.metadata and pdf_reader.metadata.title:
                    title = pdf_reader.metadata.title
                else:
                    # Use filename from URL as fallback
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    if filename:
                        title = filename
            except:
                pass
            
            return {
                'content': content.strip(),
                'title': title.strip(),
                'url': url,
                'page_count': len(pdf_reader.pages),
                'word_count': len(content.split()),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {str(e)}")
            return {
                'content': '',
                'title': '',
                'url': url,
                'error': f"PDF extraction failed: {str(e)}",
                'success': False
            }
    
    def is_extractable_url(self, url: str) -> bool:
        """
        Check if URL is likely to contain extractable content
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to contain extractable content
        """
        if not url:
            return False
            
        # Skip social media redirects and non-content URLs
        skip_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'pinterest.com'
        ]
        
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        if any(skip_domain in domain for skip_domain in skip_domains):
            return False
            
        # Check for obvious non-content file types
        skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.exe']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
            
        return True
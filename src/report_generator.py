"""
Report Generator using OpenAI LLM with Google AI fallback
Generates structured research reports from extracted content
"""

import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ReportGenerator:
    """LLM-powered report generator with multiple provider support"""
    
    def __init__(self, openai_api_key: Optional[str] = None, google_api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the report generator
        
        Args:
            openai_api_key: OpenAI API key (if not provided, will use environment variable)
            google_api_key: Google API key (if not provided, will use environment variable)
            model: OpenAI model to use for generation
        """
        # Setup OpenAI
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Setup Google AI
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.google_client = None
        if self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
                self.google_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Google AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI client: {e}")
        
        if not self.openai_client and not self.google_client:
            raise ValueError("At least one API key is required (OpenAI or Google AI)")
        
        self.model = model
    
    def generate_report(self, query: str, sources: List[Dict]) -> Dict[str, str]:
        """
        Generate a structured research report
        
        Args:
            query: Original research query
            sources: List of extracted content from sources
            
        Returns:
            Dictionary containing the structured report
        """
        try:
            logger.info(f"Generating report for query: {query}")
            
            # Filter successful extractions
            valid_sources = [s for s in sources if s.get('success', False) and s.get('content')]
            
            if not valid_sources:
                return {
                    'summary': 'No valid content could be extracted from the found sources.',
                    'key_points': [],
                    'sources_analyzed': 0,
                    'error': 'No extractable content found'
                }
            
            # Prepare content for LLM
            content_summary = self._prepare_content_for_llm(query, valid_sources)
            
            # Generate report using LLM
            report = self._call_llm_for_report(content_summary)
            
            # Add metadata
            report.update({
                'sources_analyzed': len(valid_sources),
                'total_sources_found': len(sources),
                'success': True
            })
            
            logger.info(f"Report generated successfully with {len(valid_sources)} sources")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return {
                'summary': f'Failed to generate report: {str(e)}',
                'key_points': [],
                'sources_analyzed': 0,
                'error': str(e),
                'success': False
            }
    
    def _prepare_content_for_llm(self, query: str, sources: List[Dict]) -> str:
        """
        Prepare extracted content for LLM processing
        
        Args:
            query: Research query
            sources: List of valid sources with content
            
        Returns:
            Formatted content string for LLM
        """
        content_parts = [f"Research Query: {query}\n"]
        
        for i, source in enumerate(sources, 1):
            content_parts.append(f"\n--- Source {i}: {source.get('title', 'Untitled')} ---")
            content_parts.append(f"URL: {source.get('url', 'Unknown')}")
            
            # Truncate content if too long (to fit within token limits)
            content = source.get('content', '')
            if len(content) > 3000:  # Rough character limit
                content = content[:3000] + "...\n[Content truncated]"
            
            content_parts.append(f"Content: {content}")
        
        return "\n".join(content_parts)
    
    def _call_llm_for_report(self, content: str) -> Dict[str, str]:
        """
        Call LLM to generate structured report (tries OpenAI first, then Google AI)
        
        Args:
            content: Prepared content for analysis
            
        Returns:
            Dictionary with report components
        """
        system_prompt = """You are a research analyst. Create a structured research report based on the provided sources.

Your response should be in the following JSON format:
{
    "summary": "A comprehensive 2-3 paragraph summary of the key findings",
    "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
    "methodology": "Brief description of how the research was conducted",
    "limitations": "Any limitations or caveats about the findings"
}

Guidelines:
- Summary should be comprehensive but concise (2-3 paragraphs)
- Include 3-5 key points that are the most important findings
- Be objective and factual
- Note any conflicting information between sources
- If sources are limited or of questionable quality, mention this in limitations"""

        user_prompt = f"""Please analyze the following research content and create a structured report:

{content}

Remember to format your response as valid JSON with the specified structure."""

        # Try OpenAI first
        if self.openai_client:
            try:
                logger.info("Attempting to generate report with OpenAI")
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                response_text = response.choices[0].message.content.strip()
                logger.info("OpenAI successfully generated report")
                return self._parse_llm_response(response_text)
                
            except Exception as e:
                logger.warning(f"OpenAI failed: {str(e)}")
                if "quota" not in str(e).lower() and "rate limit" not in str(e).lower():
                    # If it's not a quota/rate limit error, don't try fallback
                    raise
        
        # Try Google AI as fallback
        if self.google_client:
            try:
                logger.info("Attempting to generate report with Google AI")
                
                # Combine system and user prompts for Google AI
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.google_client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=1500
                    )
                )
                
                response_text = response.text.strip()
                logger.info("Google AI successfully generated report")
                return self._parse_llm_response(response_text)
                
            except Exception as e:
                logger.error(f"Google AI also failed: {str(e)}")
                raise
        
        # If we get here, both failed or no clients available
        raise Exception("No available LLM providers could generate the report")
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse LLM response (tries JSON first, then fallback parsing)
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dictionary with parsed report components
        """
        # Try to parse as JSON first
        try:
            import json
            report_data = json.loads(response_text)
            
            # Validate expected fields
            required_fields = ['summary', 'key_points', 'methodology', 'limitations']
            for field in required_fields:
                if field not in report_data:
                    report_data[field] = f"No {field} provided"
            
            return report_data
            
        except json.JSONDecodeError:
            # Fallback: parse as plain text
            logger.warning("Failed to parse JSON response, using fallback parser")
            return self._parse_plain_text_response(response_text)
    
    def _parse_plain_text_response(self, text: str) -> Dict[str, str]:
        """
        Fallback parser for non-JSON LLM responses
        
        Args:
            text: LLM response text
            
        Returns:
            Dictionary with parsed report components
        """
        # Simple fallback parsing
        lines = text.split('\n')
        
        return {
            'summary': text[:500] + "..." if len(text) > 500 else text,
            'key_points': [line.strip('- ') for line in lines if line.strip().startswith('- ')][:5],
            'methodology': "Analyzed multiple web sources using AI summarization",
            'limitations': "Automated analysis may miss nuanced details"
        }
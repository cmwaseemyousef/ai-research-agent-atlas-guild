"""
AI Research Agent
Main orchestrator that combines search, extraction, and report generation
"""

import logging
from typing import Dict, List, Optional
from .tools import SearchTool, ContentExtractor
from .report_generator import ReportGenerator
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class ResearchAgent:
    """AI agent that conducts research and generates reports"""
    
    def __init__(self, 
                 tavily_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 google_api_key: Optional[str] = None,
                 db_path: str = "research_db.sqlite"):
        """
        Initialize the research agent
        
        Args:
            tavily_api_key: Tavily API key for search
            openai_api_key: OpenAI API key for report generation
            google_api_key: Google API key for report generation (fallback)
            db_path: Path to SQLite database
        """
        try:
            self.search_tool = SearchTool(tavily_api_key)
            self.content_extractor = ContentExtractor()
            self.report_generator = ReportGenerator(
                openai_api_key=openai_api_key,
                google_api_key=google_api_key
            )
            self.db = DatabaseManager(db_path)
            
            logger.info("Research agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize research agent: {str(e)}")
            raise
    
    def conduct_research(self, query: str) -> Dict:
        """
        Conduct complete research process
        
        Args:
            query: Research query
            
        Returns:
            Dictionary with complete research results
        """
        query_id = None
        
        try:
            # Create database record
            query_id = self.db.create_research_query(query)
            
            # Step 1: Search for sources
            logger.info(f"Starting research for: {query}")
            self.db.update_query_status(query_id, 'searching')
            
            search_results = self.search_tool.search(query, max_results=3)
            
            if not search_results:
                self.db.update_query_status(query_id, 'failed', 'No search results found')
                return {
                    'success': False,
                    'error': 'No search results found',
                    'query_id': query_id
                }
            
            # Step 2: Extract content from sources
            logger.info(f"Extracting content from {len(search_results)} sources")
            self.db.update_query_status(query_id, 'extracting')
            
            extracted_sources = []
            for result in search_results:
                if self.content_extractor.is_extractable_url(result['url']):
                    extraction_result = self.content_extractor.extract_content(result['url'])
                    # Merge search result with extraction result
                    merged_result = {**result, **extraction_result}
                    extracted_sources.append(merged_result)
                else:
                    # Mark as skipped
                    skipped_result = {
                        **result,
                        'content': '',
                        'success': False,
                        'error': 'URL type not supported for extraction'
                    }
                    extracted_sources.append(skipped_result)
            
            # Save sources to database
            self.db.save_sources(query_id, extracted_sources)
            
            # Check if we have any successful extractions
            successful_extractions = [s for s in extracted_sources if s.get('success', False)]
            
            if not successful_extractions:
                self.db.update_query_status(query_id, 'failed', 'No content could be extracted from sources')
                return {
                    'success': False,
                    'error': 'No content could be extracted from sources',
                    'query_id': query_id,
                    'sources': extracted_sources
                }
            
            # Step 3: Generate report
            logger.info(f"Generating report from {len(successful_extractions)} sources")
            self.db.update_query_status(query_id, 'generating')
            
            report = self.report_generator.generate_report(query, extracted_sources)
            
            if not report.get('success', True):
                self.db.update_query_status(query_id, 'failed', report.get('error', 'Report generation failed'))
                return {
                    'success': False,
                    'error': report.get('error', 'Report generation failed'),
                    'query_id': query_id,
                    'sources': extracted_sources
                }
            
            # Save report to database
            report_id = self.db.save_report(query_id, report)
            
            # Mark as completed
            self.db.update_query_status(query_id, 'completed')
            
            # Return complete results
            result = {
                'success': True,
                'query_id': query_id,
                'report_id': report_id,
                'query': query,
                'report': report,
                'sources': extracted_sources,
                'sources_found': len(search_results),
                'sources_extracted': len(successful_extractions)
            }
            
            logger.info(f"Research completed successfully for query {query_id}")
            return result
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg)
            
            if query_id:
                self.db.update_query_status(query_id, 'failed', error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'query_id': query_id
            }
    
    def get_saved_reports(self, limit: int = 50) -> List[Dict]:
        """
        Get list of all saved reports
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of report summaries
        """
        return self.db.get_all_queries(limit)
    
    def get_report_details(self, query_id: int) -> Optional[Dict]:
        """
        Get detailed report data
        
        Args:
            query_id: Query ID
            
        Returns:
            Complete report data or None if not found
        """
        return self.db.get_query_with_report(query_id)
    
    def get_agent_stats(self) -> Dict:
        """
        Get agent statistics
        
        Returns:
            Dictionary with agent statistics
        """
        return self.db.get_database_stats()
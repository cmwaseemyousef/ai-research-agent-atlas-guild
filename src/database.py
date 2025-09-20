"""
Database management for storing research queries and reports
Uses SQLite for persistent storage
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database for storing research data"""
    
    def __init__(self, db_path: str = "research_db.sqlite"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create research_queries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS research_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        sources_found INTEGER DEFAULT 0,
                        sources_extracted INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_id INTEGER NOT NULL,
                        url TEXT NOT NULL,
                        title TEXT,
                        snippet TEXT,
                        content TEXT,
                        extraction_success BOOLEAN DEFAULT FALSE,
                        extraction_error TEXT,
                        word_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (query_id) REFERENCES research_queries (id)
                    )
                """)
                
                # Create reports table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_id INTEGER NOT NULL,
                        summary TEXT NOT NULL,
                        key_points TEXT NOT NULL,  -- JSON array
                        methodology TEXT,
                        limitations TEXT,
                        sources_analyzed INTEGER DEFAULT 0,
                        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (query_id) REFERENCES research_queries (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON research_queries(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_query_id ON sources(query_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_query_id ON reports(query_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def create_research_query(self, query: str) -> int:
        """
        Create a new research query record
        
        Args:
            query: Research query text
            
        Returns:
            Query ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO research_queries (query, timestamp, status)
                    VALUES (?, ?, ?)
                """, (query, datetime.now(), 'started'))
                
                query_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created research query {query_id}: {query}")
                return query_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to create research query: {str(e)}")
            raise
    
    def update_query_status(self, query_id: int, status: str, error_message: str = None):
        """
        Update query status
        
        Args:
            query_id: Query ID
            status: New status ('started', 'searching', 'extracting', 'generating', 'completed', 'failed')
            error_message: Optional error message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE research_queries 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, (status, error_message, query_id))
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update query status: {str(e)}")
    
    def save_sources(self, query_id: int, sources: List[Dict]):
        """
        Save search sources
        
        Args:
            query_id: Query ID
            sources: List of source dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for source in sources:
                    cursor.execute("""
                        INSERT INTO sources (
                            query_id, url, title, snippet, content, 
                            extraction_success, extraction_error, word_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        query_id,
                        source.get('url', ''),
                        source.get('title', ''),
                        source.get('snippet', ''),
                        source.get('content', ''),
                        source.get('success', False),
                        source.get('error', ''),
                        source.get('word_count', 0)
                    ))
                
                # Update query with source counts
                cursor.execute("""
                    UPDATE research_queries 
                    SET sources_found = ?, sources_extracted = ?
                    WHERE id = ?
                """, (
                    len(sources),
                    len([s for s in sources if s.get('success', False)]),
                    query_id
                ))
                
                conn.commit()
                logger.info(f"Saved {len(sources)} sources for query {query_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save sources: {str(e)}")
            raise
    
    def save_report(self, query_id: int, report: Dict) -> int:
        """
        Save generated report
        
        Args:
            query_id: Query ID
            report: Report dictionary
            
        Returns:
            Report ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert key_points list to JSON
                key_points_json = json.dumps(report.get('key_points', []))
                
                cursor.execute("""
                    INSERT INTO reports (
                        query_id, summary, key_points, methodology, 
                        limitations, sources_analyzed
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    query_id,
                    report.get('summary', ''),
                    key_points_json,
                    report.get('methodology', ''),
                    report.get('limitations', ''),
                    report.get('sources_analyzed', 0)
                ))
                
                report_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved report {report_id} for query {query_id}")
                return report_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save report: {str(e)}")
            raise
    
    def get_all_queries(self, limit: int = 50) -> List[Dict]:
        """
        Get all research queries with basic info
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        q.id, q.query, q.timestamp, q.status, 
                        q.sources_found, q.sources_extracted,
                        q.error_message, q.created_at,
                        r.id as report_id
                    FROM research_queries q
                    LEFT JOIN reports r ON q.id = r.query_id
                    ORDER BY q.created_at DESC
                    LIMIT ?
                """, (limit,))
                
                queries = []
                for row in cursor.fetchall():
                    queries.append({
                        'id': row['id'],
                        'query': row['query'],
                        'timestamp': row['timestamp'],
                        'status': row['status'],
                        'sources_found': row['sources_found'],
                        'sources_extracted': row['sources_extracted'],
                        'error_message': row['error_message'],
                        'created_at': row['created_at'],
                        'has_report': row['report_id'] is not None
                    })
                
                return queries
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get queries: {str(e)}")
            return []
    
    def get_query_with_report(self, query_id: int) -> Optional[Dict]:
        """
        Get complete query data with report and sources
        
        Args:
            query_id: Query ID
            
        Returns:
            Complete query dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get query and report
                cursor.execute("""
                    SELECT 
                        q.*, r.summary, r.key_points, r.methodology, 
                        r.limitations, r.sources_analyzed, r.generated_at
                    FROM research_queries q
                    LEFT JOIN reports r ON q.id = r.query_id
                    WHERE q.id = ?
                """, (query_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get sources
                cursor.execute("""
                    SELECT url, title, snippet, extraction_success, extraction_error
                    FROM sources
                    WHERE query_id = ?
                    ORDER BY id
                """, (query_id,))
                
                sources = []
                for source_row in cursor.fetchall():
                    sources.append({
                        'url': source_row['url'],
                        'title': source_row['title'],
                        'snippet': source_row['snippet'],
                        'extraction_success': source_row['extraction_success'],
                        'extraction_error': source_row['extraction_error']
                    })
                
                # Build complete result
                result = {
                    'id': row['id'],
                    'query': row['query'],
                    'timestamp': row['timestamp'],
                    'status': row['status'],
                    'sources_found': row['sources_found'],
                    'sources_extracted': row['sources_extracted'],
                    'error_message': row['error_message'],
                    'created_at': row['created_at'],
                    'sources': sources
                }
                
                # Add report data if exists
                if row['summary']:
                    result['report'] = {
                        'summary': row['summary'],
                        'key_points': json.loads(row['key_points']) if row['key_points'] else [],
                        'methodology': row['methodology'],
                        'limitations': row['limitations'],
                        'sources_analyzed': row['sources_analyzed'],
                        'generated_at': row['generated_at']
                    }
                
                return result
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get query with report: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count queries by status
                cursor.execute("SELECT status, COUNT(*) FROM research_queries GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Total counts
                cursor.execute("SELECT COUNT(*) FROM research_queries")
                total_queries = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sources")
                total_sources = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM reports")
                total_reports = cursor.fetchone()[0]
                
                return {
                    'total_queries': total_queries,
                    'total_sources': total_sources,
                    'total_reports': total_reports,
                    'status_counts': status_counts,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            return {}
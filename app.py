"""
Flask Web Interface for the AI Research Agent
Provides a simple UI for conducting research and viewing saved reports
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
from src.research_agent import ResearchAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize research agent
try:
    agent = ResearchAgent(
        tavily_api_key=os.getenv('TAVILY_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        db_path=os.getenv('DATABASE_PATH', 'research_db.sqlite')
    )
    logger.info("Research agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize research agent: {str(e)}")
    agent = None

@app.route('/')
def index():
    """Home page with search form and recent reports"""
    try:
        recent_reports = agent.get_saved_reports(limit=10) if agent else []
        stats = agent.get_agent_stats() if agent else {}
        
        return render_template('index.html', 
                             recent_reports=recent_reports,
                             stats=stats,
                             agent_available=agent is not None)
    except Exception as e:
        logger.error(f"Error loading home page: {str(e)}")
        return render_template('index.html', 
                             recent_reports=[],
                             stats={},
                             agent_available=False,
                             error=str(e))

@app.route('/search', methods=['POST'])
def search():
    """Handle research query submission"""
    if not agent:
        return jsonify({
            'success': False,
            'error': 'Research agent is not available. Please check your API keys.'
        }), 500
    
    try:
        query = request.form.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Please enter a research query.'
            }), 400
        
        # Conduct research
        result = agent.conduct_research(query)
        
        if result['success']:
            return jsonify({
                'success': True,
                'query_id': result['query_id'],
                'redirect_url': url_for('view_report', query_id=result['query_id'])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Research failed for unknown reason')
            }), 500
            
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500

@app.route('/reports')
def reports():
    """List all saved reports"""
    try:
        all_reports = agent.get_saved_reports(limit=100) if agent else []
        stats = agent.get_agent_stats() if agent else {}
        
        return render_template('reports.html', 
                             reports=all_reports,
                             stats=stats,
                             agent_available=agent is not None)
    except Exception as e:
        logger.error(f"Error loading reports page: {str(e)}")
        return render_template('reports.html', 
                             reports=[],
                             stats={},
                             agent_available=False,
                             error=str(e))

@app.route('/report/<int:query_id>')
def view_report(query_id):
    """View detailed report"""
    if not agent:
        return render_template('error.html', 
                             error="Research agent is not available")
    
    try:
        report_data = agent.get_report_details(query_id)
        
        if not report_data:
            return render_template('error.html', 
                                 error=f"Report {query_id} not found")
        
        return render_template('report.html', data=report_data)
        
    except Exception as e:
        logger.error(f"Error loading report {query_id}: {str(e)}")
        return render_template('error.html', 
                             error=f"Failed to load report: {str(e)}")

@app.route('/api/status/<int:query_id>')
def api_status(query_id):
    """API endpoint to check research status"""
    if not agent:
        return jsonify({'error': 'Agent not available'}), 500
    
    try:
        report_data = agent.get_report_details(query_id)
        
        if not report_data:
            return jsonify({'error': 'Query not found'}), 404
        
        return jsonify({
            'status': report_data.get('status', 'unknown'),
            'has_report': 'report' in report_data,
            'sources_found': report_data.get('sources_found', 0),
            'sources_extracted': report_data.get('sources_extracted', 0),
            'error_message': report_data.get('error_message')
        })
        
    except Exception as e:
        logger.error(f"Error getting status for query {query_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for agent statistics"""
    if not agent:
        return jsonify({'error': 'Agent not available'}), 500
    
    try:
        stats = agent.get_agent_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('error.html', error="Internal server error"), 500

# Template filters
@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime for display"""
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return value
    return value

@app.template_filter('truncate_words')
def truncate_words_filter(text, length=50):
    """Truncate text to specified number of words"""
    if not text:
        return ""
    words = text.split()
    if len(words) <= length:
        return text
    return ' '.join(words[:length]) + '...'

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
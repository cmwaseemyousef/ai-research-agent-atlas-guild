"""
Demo script showing AI Research Agent functionality
This script demonstrates the core features without the web interface
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.research_agent import ResearchAgent

# Load environment variables
load_dotenv()

# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_separator(title):
    """Print a formatted separator"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_report(result):
    """Print a formatted research report"""
    if not result['success']:
        print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Research completed successfully!")
    print(f"🆔 Query ID: {result['query_id']}")
    print(f"📊 Sources found: {result['sources_found']}")
    print(f"📄 Sources extracted: {result['sources_extracted']}")
    
    report = result.get('report', {})
    if not report:
        print("❌ No report generated")
        return
    
    print("\n📝 SUMMARY:")
    print("-" * 40)
    print(report.get('summary', 'No summary available'))
    
    key_points = report.get('key_points', [])
    if key_points:
        print("\n🔑 KEY POINTS:")
        print("-" * 40)
        for i, point in enumerate(key_points, 1):
            print(f"{i}. {point}")
    
    print(f"\n📈 METHODOLOGY:")
    print("-" * 40)
    print(report.get('methodology', 'No methodology provided'))
    
    print(f"\n⚠️  LIMITATIONS:")
    print("-" * 40)
    print(report.get('limitations', 'No limitations noted'))
    
    # Show sources
    sources = result.get('sources', [])
    if sources:
        print(f"\n🔗 SOURCES ANALYZED ({len(sources)}):")
        print("-" * 40)
        for i, source in enumerate(sources, 1):
            status = "✅" if source.get('success', False) else "❌"
            title = source.get('title', 'Untitled')[:50] + "..." if len(source.get('title', '')) > 50 else source.get('title', 'Untitled')
            print(f"{i}. {status} {title}")
            print(f"   URL: {source.get('url', 'Unknown')}")
            if not source.get('success', False) and source.get('error'):
                print(f"   Error: {source.get('error', '')[:100]}")
            print()

def demo_research_queries():
    """Demonstrate research with multiple example queries"""
    
    print_separator("AI RESEARCH AGENT DEMO")
    
    # Initialize agent
    try:
        print("🤖 Initializing AI Research Agent...")
        agent = ResearchAgent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Please check your API keys in the .env file")
        return
    
    # Example queries to demonstrate
    example_queries = [
        "Benefits of Python programming language",
        "Latest trends in renewable energy",
        "Impact of artificial intelligence on healthcare"
    ]
    
    print(f"\n📋 Will demonstrate with {len(example_queries)} research queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    # Ask user which demo to run
    print("\nSelect demo option:")
    print("1. Run all queries (will take several minutes)")
    print("2. Run single query")
    print("3. Show saved reports only")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Run all queries
        for i, query in enumerate(example_queries, 1):
            print_separator(f"RESEARCH {i}: {query}")
            try:
                result = agent.conduct_research(query)
                print_report(result)
            except Exception as e:
                print(f"❌ Research failed: {e}")
            
            if i < len(example_queries):
                input("\nPress Enter to continue to next query...")
    
    elif choice == "2":
        # Run single query
        print("\nSelect a query to research:")
        for i, query in enumerate(example_queries, 1):
            print(f"{i}. {query}")
        print("4. Enter custom query")
        
        query_choice = input("\nEnter your choice (1-4): ").strip()
        
        if query_choice in ["1", "2", "3"]:
            query = example_queries[int(query_choice) - 1]
        elif query_choice == "4":
            query = input("Enter your research query: ").strip()
            if not query:
                print("❌ No query entered")
                return
        else:
            print("❌ Invalid choice")
            return
        
        print_separator(f"RESEARCH: {query}")
        try:
            result = agent.conduct_research(query)
            print_report(result)
        except Exception as e:
            print(f"❌ Research failed: {e}")
    
    elif choice == "3":
        # Show saved reports only
        print_separator("SAVED REPORTS")
        try:
            reports = agent.get_saved_reports(limit=10)
            if not reports:
                print("📭 No saved reports found")
                return
            
            print(f"Found {len(reports)} saved reports:\n")
            for i, report in enumerate(reports, 1):
                status_emoji = {
                    'completed': '✅',
                    'failed': '❌', 
                    'searching': '🔍',
                    'extracting': '📥',
                    'generating': '📝'
                }.get(report.get('status', ''), '❓')
                
                print(f"{i}. {status_emoji} {report.get('query', 'Unknown query')}")
                print(f"   Status: {report.get('status', 'Unknown')}")
                print(f"   Created: {report.get('created_at', 'Unknown')}")
                print(f"   Sources: {report.get('sources_found', 0)} found, {report.get('sources_extracted', 0)} extracted")
                print()
        
        except Exception as e:
            print(f"❌ Failed to get saved reports: {e}")
    
    else:
        print("❌ Invalid choice")
        return
    
    # Show final statistics
    print_separator("AGENT STATISTICS")
    try:
        stats = agent.get_agent_stats()
        print(f"📊 Total queries: {stats.get('total_queries', 0)}")
        print(f"📄 Total reports: {stats.get('total_reports', 0)}")
        print(f"🔗 Total sources: {stats.get('total_sources', 0)}")
        print(f"💾 Database size: {stats.get('database_size', 0) / 1024:.1f} KB")
        
        status_counts = stats.get('status_counts', {})
        if status_counts:
            print("\n📈 Query status breakdown:")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
    
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
    
    print_separator("DEMO COMPLETE")
    print("🌐 To use the web interface, run: python app.py")
    print("📱 Then visit: http://localhost:5000")

if __name__ == "__main__":
    demo_research_queries()
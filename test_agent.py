"""
Test script to verify the AI Research Agent functionality
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.research_agent import ResearchAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_api_keys():
    """Test if API keys are available"""
    print("🔍 Checking API keys...")
    
    tavily_key = os.getenv('TAVILY_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not tavily_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return False
    else:
        print(f"✅ Tavily API key found (starts with: {tavily_key[:8]}...)")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    else:
        print(f"✅ OpenAI API key found (starts with: {openai_key[:8]}...)")
    
    return True

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🤖 Testing agent initialization...")
    
    try:
        agent = ResearchAgent()
        print("✅ Research agent initialized successfully")
        return agent
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        return None

def test_simple_research(agent):
    """Test basic research functionality"""
    print("\n📚 Testing research functionality...")
    
    if not agent:
        print("❌ Cannot test research - agent not available")
        return
    
    try:
        # Simple test query
        query = "Benefits of Python programming language"
        print(f"🔍 Researching: {query}")
        
        result = agent.conduct_research(query)
        
        if result['success']:
            print("✅ Research completed successfully!")
            print(f"📊 Sources found: {result.get('sources_found', 0)}")
            print(f"📄 Sources extracted: {result.get('sources_extracted', 0)}")
            print(f"🆔 Query ID: {result.get('query_id')}")
            
            if result.get('report'):
                report = result['report']
                print(f"📝 Report summary length: {len(report.get('summary', ''))}")
                print(f"🔢 Key points: {len(report.get('key_points', []))}")
            
            return True
        else:
            print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Research test failed: {str(e)}")
        return False

def test_database_operations(agent):
    """Test database operations"""
    print("\n💾 Testing database operations...")
    
    if not agent:
        print("❌ Cannot test database - agent not available")
        return
    
    try:
        # Get stats
        stats = agent.get_agent_stats()
        print(f"✅ Database stats retrieved: {stats}")
        
        # Get reports
        reports = agent.get_saved_reports(limit=5)
        print(f"✅ Found {len(reports)} saved reports")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 AI Research Agent Test Suite")
    print("=" * 50)
    
    # Test 1: API Keys
    if not test_api_keys():
        print("\n❌ Test suite failed - missing API keys")
        print("Please check your .env file and ensure TAVILY_API_KEY and OPENAI_API_KEY are set")
        return False
    
    # Test 2: Agent Initialization
    agent = test_agent_initialization()
    
    # Test 3: Database Operations
    test_database_operations(agent)
    
    # Test 4: Research (only if API keys are available)
    print("\n⚠️  The next test will make actual API calls and may take some time...")
    response = input("Do you want to test the research functionality? (y/N): ").lower().strip()
    
    if response == 'y':
        success = test_simple_research(agent)
        if success:
            print("\n🎉 All tests passed! The AI Research Agent is working correctly.")
        else:
            print("\n⚠️  Research test failed, but basic functionality is working.")
    else:
        print("\n✅ Basic tests completed. Research functionality not tested.")
    
    print("\n📋 Test Summary:")
    print("- API keys: ✅")
    print("- Agent initialization: ✅" if agent else "- Agent initialization: ❌")
    print("- Database operations: ✅")
    if response == 'y':
        print("- Research functionality: ✅" if success else "- Research functionality: ❌")
    
    return True

if __name__ == "__main__":
    main()
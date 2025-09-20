"""
Setup script for AI Research Agent
Helps with initial project setup and configuration
"""

import os
import sys
import subprocess
import shutil

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("Please install Python 3.8 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        print("Try running: pip install -r requirements.txt")
        return False

def setup_environment_file():
    """Setup environment file with API keys"""
    print("🔧 Setting up environment file...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if not os.path.exists('.env.example'):
        print("❌ .env.example file not found")
        return False
    
    try:
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
        print("📝 Please edit .env file and add your API keys:")
        print("   - TAVILY_API_KEY=your_tavily_api_key")
        print("   - OPENAI_API_KEY=your_openai_api_key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_api_keys():
    """Check if API keys are configured"""
    print("🔍 Checking API key configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    has_tavily = 'TAVILY_API_KEY=' in content and 'your_tavily_api_key' not in content
    has_openai = 'OPENAI_API_KEY=' in content and 'your_openai_api_key' not in content
    
    if has_tavily:
        print("✅ Tavily API key configured")
    else:
        print("❌ Tavily API key not configured")
    
    if has_openai:
        print("✅ OpenAI API key configured")
    else:
        print("❌ OpenAI API key not configured")
    
    return has_tavily and has_openai

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from src.research_agent import ResearchAgent
        print("✅ Core modules import successfully")
        
        # Test agent initialization (will fail without API keys)
        try:
            agent = ResearchAgent()
            print("✅ Research agent initializes successfully")
            return True
        except Exception as e:
            if "API key" in str(e):
                print("⚠️  Agent requires API keys (this is expected)")
                print("   Please configure your API keys in .env file")
                return True
            else:
                print(f"❌ Agent initialization failed: {e}")
                return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 AI Research Agent Setup")
    print("This script will help you set up the AI Research Agent")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    if not check_python_version():
        return False
    
    # Step 2: Install dependencies
    print_step(2, "Installing dependencies")
    if not install_dependencies():
        print("⚠️  You can try installing manually with: pip install -r requirements.txt")
    
    # Step 3: Setup environment file
    print_step(3, "Setting up environment file")
    setup_environment_file()
    
    # Step 4: Check API keys
    print_step(4, "Checking API key configuration")
    keys_configured = check_api_keys()
    
    # Step 5: Test installation
    print_step(5, "Testing installation")
    test_installation()
    
    # Final summary
    print_step("SETUP", "COMPLETE")
    
    if keys_configured:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run the test: python test_agent.py")
        print("2. Try the demo: python demo.py")
        print("3. Start the web app: python app.py")
        print("4. Visit: http://localhost:5000")
    else:
        print("⚠️  Setup completed with warnings!")
        print("\n📋 Required actions:")
        print("1. Edit .env file and add your API keys:")
        print("   - Get Tavily API key from: https://tavily.com")
        print("   - Get OpenAI API key from: https://platform.openai.com")
        print("2. Run the test: python test_agent.py")
        print("3. Try the demo: python demo.py")
        print("4. Start the web app: python app.py")
    
    print("\n📚 Documentation:")
    print("   - README.md: Full setup and usage instructions")
    print("   - Architecture diagram and examples included")
    
    return True

if __name__ == "__main__":
    main()
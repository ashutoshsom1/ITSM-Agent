#!/usr/bin/env python3
"""
Simple run script for local development
"""
import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import azure.cosmos
        import openai
        print("✅ All required packages found")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if environment file exists"""
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if not env_file.exists():
        if env_template.exists():
            print("❌ .env file not found")
            print("📋 Copy .env.template to .env and fill in your Azure credentials:")
            print(f"   cp {env_template} {env_file}")
            return False
        else:
            print("❌ No environment configuration found")
            return False
    
    print("✅ Environment file found")
    return True

def run_server():
    """Run the development server"""
    print("🚀 Starting ITSM AI Agent development server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("🤖 ITSM AI Agent - Development Server")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    # Run server
    run_server()

if __name__ == "__main__":
    main()

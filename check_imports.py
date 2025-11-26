import os
import sys
import traceback

print(f"CWD: {os.getcwd()}")

# 1. Check langchain.agents.create_agent
print("\n--- Checking langchain.agents.create_agent ---")
try:
    from langchain.agents import create_agent
    print("SUCCESS: Found langchain.agents.create_agent")
except ImportError:
    print("FAILURE: Could not import create_agent from langchain.agents")
except Exception:
    traceback.print_exc()

# 2. Check chromadb path resolution
print("\n--- Checking ChromaDB Path ---")
print(f"Abspath of '../memories': {os.path.abspath('../memories')}")
print(f"Abspath of 'memories': {os.path.abspath('memories')}")

# 3. Check src.tools import
print("\n--- Checking src.tools import ---")
sys.path.append(os.getcwd())
try:
    # We need to mock google.genai.types if it's not installed or configured, 
    # but let's assume the environment is set up or we'll catch the error.
    # src.tools imports chromadb, requests, etc.
    from src import tools
    print("SUCCESS: Successfully imported src.tools")
    print(f"tools.chroma_client path setting: {tools.chroma_client._settings.require('persist_directory') if hasattr(tools.chroma_client, '_settings') else 'Unknown'}")
except Exception:
    traceback.print_exc()

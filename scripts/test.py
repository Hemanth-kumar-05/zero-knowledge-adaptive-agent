import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.pipeline import RAGPipeline

rag_agent = RAGPipeline(verbose=True)
result = rag_agent.query("Hi there!")

print("Keys in result:", result.keys())
print("\nResponse:", result)
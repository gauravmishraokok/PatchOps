import os
import sys
from groq import Groq
import httpx

print("Testing Groq client initialization...")
print(f"Python version: {sys.version}")
print(f"Groq module location: {Groq.__module__}")

# Check all environment variables
print("\nRelevant environment variables:")
for key, value in os.environ.items():
    if any(keyword in key.lower() for keyword in ['proxy', 'http', 'groq', 'api', 'curl']):
        print(f"  {key}: {value}")

# Test httpx client directly
print("\nTesting httpx client creation...")
try:
    http_client = httpx.Client()
    print("✅ httpx client created successfully")
except Exception as e:
    print(f"❌ Error creating httpx client: {e}")

# Try to inspect the Groq Client class
print(f"\nGroq Client init signature:")
import inspect
try:
    sig = inspect.signature(Groq.__init__)
    print(f"  Parameters: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"  Error getting signature: {e}")

# Try to create client with explicit http_client
try:
    api_key = os.environ.get("GROQ_API_KEY")
    print(f"\nAPI Key found: {bool(api_key)}")
    
    # Try with explicit http_client to avoid proxy issues
    print("Attempting to create client with explicit http_client...")
    http_client = httpx.Client()
    client = Groq(api_key=api_key, http_client=http_client)
    print("✅ Groq client created successfully with explicit http_client")
    
except Exception as e:
    print(f"❌ Error creating Groq client: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

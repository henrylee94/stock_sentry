"""
OpenAI API Connection Diagnostic Tool
Version: 1.51.2
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("🔍 OpenAI API Connection Diagnostic Tool")
print("="*70)

# Step 1: Check Python version
print("\n1️⃣ Python Environment")
print(f"   Python version: {sys.version}")
print(f"   Platform: {sys.platform}")

# Step 2: Check OpenAI installation
print("\n2️⃣ OpenAI Package Check")
try:
    import openai
    print(f"   ✅ OpenAI package installed")
    print(f"   Version: {openai.__version__}")
    
    if openai.__version__ != "1.51.2":
        print(f"   ⚠️  WARNING: Version mismatch! Expected 1.51.2, got {openai.__version__}")
        print(f"   Fix: pip install openai==1.51.2")
except ImportError as e:
    print(f"   ❌ OpenAI package not found!")
    print(f"   Fix: pip install openai==1.51.2")
    sys.exit(1)

# Step 3: Check for API key
print("\n3️⃣ API Key Check")
api_key = os.environ.get("OPENAI_KEY")

if not api_key:
    print(f"   ❌ No API key found in environment variables")
    print(f"   Checked: OPENAI_API_KEY, OPENAI_KEY", api_key)
    print(f"\n   Fix: Set your API key:")
    print(f"   export OPENAI_API_KEY='your-key-here'")
    api_key = input("\n   Enter your API key manually to test: ").strip()

if api_key:
    # Clean the API key
    api_key = api_key.strip().strip('"').strip("'").strip()
    
    print(f"   ✅ API key found")
    print(f"   Length: {len(api_key)}")
    print(f"   Starts with: {api_key[:7]}...")
    print(f"   Ends with: ...{api_key[-4:]}")
    
    # Validate format
    if not api_key.startswith('sk-'):
        print(f"   ❌ ERROR: Invalid format (should start with 'sk-')")
        print(f"   Your key starts with: {api_key[:10]}")
    elif len(api_key) < 20:
        print(f"   ❌ ERROR: Key too short (should be 51+ characters)")
    else:
        print(f"   ✅ Format looks valid")
else:
    print(f"   ❌ No API key available")
    sys.exit(1)

# Step 4: Check proxy settings
print("\n4️⃣ Proxy Settings Check")
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
              'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
proxy_found = False
for var in proxy_vars:
    if var in os.environ:
        print(f"   ⚠️  Found: {var} = {os.environ[var]}")
        proxy_found = True

if proxy_found:
    print(f"   ⚠️  Proxies detected - this may cause connection issues")
    print(f"   Try removing them temporarily:")
    for var in proxy_vars:
        if var in os.environ:
            print(f"   unset {var}")
else:
    print(f"   ✅ No proxy settings detected")

# Step 5: Test basic client initialization
print("\n5️⃣ Client Initialization Test")
try:
    from openai import OpenAI
    
    # Method 1: With explicit API key
    print(f"   Attempting to create client...")
    client = OpenAI(api_key=api_key)
    print(f"   ✅ Client created successfully!")
    
except Exception as e:
    print(f"   ❌ Client creation failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Test API connection
print("\n6️⃣ API Connection Test")
try:
    print(f"   Testing with a simple API call...")
    
    # Use the chat completions endpoint (most reliable)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Connection successful!' and nothing else."}
        ],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print(f"   ✅ API CONNECTION SUCCESSFUL!")
    print(f"   Response: {result}")
    
except Exception as e:
    print(f"   ❌ API call failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    
    # Common error explanations
    error_str = str(e).lower()
    print(f"\n   💡 Troubleshooting:")
    
    if "authentication" in error_str or "401" in error_str:
        print(f"   • Invalid API key - check if it's correct and active")
        print(f"   • Verify at: https://platform.openai.com/api-keys")
    
    elif "rate" in error_str or "429" in error_str:
        print(f"   • Rate limit exceeded - wait a moment and try again")
    
    elif "quota" in error_str or "billing" in error_str:
        print(f"   • Billing issue - check your OpenAI account")
        print(f"   • Verify at: https://platform.openai.com/account/billing")
    
    elif "connection" in error_str or "timeout" in error_str:
        print(f"   • Network issue - check your internet connection")
        print(f"   • Try: ping api.openai.com")
        print(f"   • Check firewall/VPN settings")
    
    elif "ssl" in error_str or "certificate" in error_str:
        print(f"   • SSL certificate issue")
        print(f"   • Try updating certifi: pip install --upgrade certifi")
    
    else:
        print(f"   • Unknown error - see full error above")
    
    import traceback
    print(f"\n   Full traceback:")
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test model availability
print("\n7️⃣ Available Models Check")
try:
    models = client.models.list()
    print(f"   ✅ Successfully retrieved model list")
    print(f"   Sample models available:")
    for i, model in enumerate(list(models)[:5]):
        print(f"   • {model.id}")
except Exception as e:
    print(f"   ⚠️  Could not list models: {e}")

print("\n" + "="*70)
print("✅ DIAGNOSTIC COMPLETE")
print("="*70)
print("\nIf all tests passed, your OpenAI client is working correctly!")
print("If any tests failed, follow the troubleshooting steps above.")
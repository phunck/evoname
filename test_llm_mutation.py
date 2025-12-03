import urllib.request
import json
import sys
import time

def query_ollama(prompt, model="qwen2.5-coder:1.5b"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        start_time = time.time()
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            duration = time.time() - start_time
            print(f"⏱️ Response time: {duration:.2f}s")
            return result.get("response", "")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("Make sure Ollama is running and the model is downloaded ('ollama run qwen2.5-coder:1.5b')")
        return None

def test_repair():
    print(f"🚀 Testing connection to Ollama (Model: qwen2.5-coder:1.5b)...")
    
    broken_code = """
def parse_name(name):
    # Currently fails on "Dr. Hans Müller" because it splits by space and takes first/last
    parts = name.split(" ")
    return {"given": parts[0], "family": parts[1]}
"""
    
    prompt = f"""
You are an expert Python developer.
Fix the following Python function so it correctly handles titles like "Dr." or "Prof.".
The function should return a dictionary with "title", "given", and "family".
Return ONLY the fixed Python code, no explanations.

{broken_code}
"""
    
    print("\n📝 Sending Prompt:")
    print("-" * 40)
    print(prompt.strip())
    print("-" * 40)
    
    response = query_ollama(prompt)
    
    if response:
        print("\n🤖 LLM Response:")
        print("=" * 40)
        print(response.strip())
        print("=" * 40)
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed.")

if __name__ == "__main__":
    test_repair()

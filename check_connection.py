import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
 
def main():
    env_found = load_dotenv()
    print(f"[setup] .env loaded: {env_found}")
 
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            "[error] No API key found in environment. "
            "Make sure a .env file with GOOGLE_API_KEY=... exists in this directory, "
            "or export it directly in your shell."
        )
        sys.exit(1)
 
    print("[setup] API key found, initializing model...")
 
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash", 
        temperature=0.2,
    )
 
    prompt = "In one sentence, explain what a 'slab' means in a Pakistani electricity bill."
    print(f"[test] Sending prompt: {prompt}")
 
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        print(f"[error] Model call failed: {e}")
        sys.exit(1)
 
    print("\n[success] Response from Gemini:")
    print(response.content)
 
 
if __name__ == "__main__":
    main()
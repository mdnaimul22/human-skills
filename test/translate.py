import os
import re
import json
import hashlib
import time
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY = os.environ.get("LLM_API_KEY", "").strip()
API_BASE = os.environ.get("LLM_BASE_URL", "http://13.204.27.202:8000/v1").strip()
MODEL_ID = os.environ.get("LLM_MODEL", "CohereForAI_C4AI_Command") 
CACHE_FILE = ".translation-cache.json"
SKILLS_DIR = "skills"
BATCH_SIZE = 5 # Process 5 files at a time for faster progress
DELAY_SECONDS = 5 # Reduced delay for this API

# Regex for Chinese characters
CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]')

def has_chinese(text):
    return bool(CHINESE_PATTERN.search(text))

def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def translate_text(text):
    invoke_url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    prompt = f"""
You are a professional technical translator specializing in software documentation and Markdown.

TASK: Translate the following Markdown content from Chinese to English.

STRICT INSTRUCTIONS:
1. PRESERVE STRUCTURE: Maintain all Markdown syntax, headers, code blocks, lists, and tables EXACTLY as they are.
2. WHITESPACE INTEGRITY: Do not remove or add any empty lines. Every single line break and spacing must be identical to the original. Ensure there is an empty line before every header if it existed in the original.
3. TECHNICAL TERMS: Keep all English technical terms, library names (AntV, G2, etc.), API methods (chart.options(), etc.), and variable names in their original form.
4. NO EXPLANATIONS: Provide ONLY the translated Markdown content. Do not include any introductory or concluding remarks.
5. QUALITY: Ensure the English translation is professional, clear, and follows technical writing best practices.

CONTENT TO TRANSLATE:
{text}
"""
    
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1, # Lower temperature for more deterministic/stable formatting
        "top_p": 0.95,
        "max_tokens": 16384,
        "stream": False
    }
    
    try:
        print(f"DEBUG: Sending request for translation using model {MODEL_ID} (standard)...")
        start_time = time.time()
        # Large timeout for deep-thinking models
        response = requests.post(invoke_url, headers=headers, json=payload, timeout=600)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: Received response in {duration:.2f} seconds.")
            
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                content = message.get('content', "")
                
                # Handle cases where content might be empty but reasoning/thinking exists
                if not content and 'reasoning_content' in message:
                    print("DEBUG: Content empty but reasoning_content found. Using reasoning_content.")
                    content = message['reasoning_content']
                
                if content:
                    print(f"DEBUG: Successfully received {len(content)} characters of translation.")
                    return content
                else:
                    print(f"DEBUG: Choice found but content is empty. Message: {json.dumps(message)}")
            else:
                print(f"DEBUG: No choices found in response. Data: {json.dumps(data)}")
        else:
            print(f"Error during translation: Status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during translation exception: {e}")
    
    return None

def split_markdown(text):
    """Splits markdown into chunks based on headers."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current_chunk = []
    
    for line in lines:
        # Split by level 1, 2, or 3 headers
        if re.match(r'^#{1,3} ', line):
            if current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
        current_chunk.append(line)
    
    if current_chunk:
        chunks.append("".join(current_chunk))
    
    return chunks

def main():
    if not API_KEY:
        print("Error: LLM_API_KEY not found in environment.")
        return

    # Load cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)

    # Find all .md files in skills directory
    md_files = list(Path(SKILLS_DIR).rglob("*.md"))
    if os.path.exists("README.md"):
        md_files.append(Path("README.md"))

    print(f"Found {len(md_files)} Markdown files.")

    files_to_process = []
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Always process if it has Chinese, regardless of cache for now to ensure thoroughness
        # or use hash-based cache on the whole file to skip unchanged files
        file_id = str(md_path)
        content_hash = get_hash(content)

        if cache.get(file_id) == content_hash:
            continue
            
        files_to_process.append((md_path, content, content_hash))

    print(f"Queue size: {len(files_to_process)} files need checking/translation.")
    
    # Take only the first BATCH_SIZE files
    batch = files_to_process[:BATCH_SIZE]
    if batch:
        print(f"Processing batch of {len(batch)} files...")
    else:
        print("No new files to translate.")
        return

    for md_path, content, original_hash in batch:
        print(f"\n--- Processing: {md_path} ---")
        chunks = split_markdown(content)
        print(f"File split into {len(chunks)} chunks.")
        
        translated_chunks = []
        chunks_updated = 0
        
        for i, chunk in enumerate(chunks):
            if has_chinese(chunk):
                print(f"  Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
                translated = translate_text(chunk)
                if translated:
                    translated_chunks.append(translated)
                    chunks_updated += 1
                    
                    # SAVE PROGRESS IMMEDIATELY after each chunk
                    temp_processed = []
                    for j, c in enumerate(translated_chunks):
                        content_to_add = c
                        # If this is not the first chunk and it starts with a header,
                        # ensure the previous chunk ended with two newlines for professional spacing.
                        if j > 0 and re.match(r'^#{1,3} ', content_to_add):
                            # Strip any trailing whitespace from previous chunk before adding newlines
                            temp_processed[-1] = temp_processed[-1].rstrip() + '\n\n'
                        
                        # Ensure the current chunk ends with at least one newline for safety
                        if j < len(chunks) - 1 and not content_to_add.endswith('\n'):
                            content_to_add += '\n'
                            
                        temp_processed.append(content_to_add)
                    
                    # Add remaining original chunks to keep the file structure
                    temp_processed.extend(chunks[i+1:])
                    
                    final_temp = "".join(temp_processed)
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(final_temp)
                    
                    # Small delay between chunks
                    time.sleep(1) 
                else:
                    print(f"  ✗ Failed to translate chunk {i+1}. Keeping original.")
                    translated_chunks.append(chunk)
            else:
                # Keep original English/already translated chunk
                translated_chunks.append(chunk)
        
        if chunks_updated > 0:
            # Final save and update cache
            cache[str(md_path)] = original_hash
            save_cache(cache)
            print(f"  ✓ Finished {md_path} ({chunks_updated} chunks translated).")
        else:
            print(f"  - No Chinese found in {md_path} chunks (or translation failed).")

    print("\nBatch finished.")

if __name__ == "__main__":
    main()

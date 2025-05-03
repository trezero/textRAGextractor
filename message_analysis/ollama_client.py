import requests
import json
from pathlib import Path

def analyze_conversation(contact_name, messages_file):
    """Send conversation to Ollama for style analysis"""
    url = "http://localhost:11434/api/generate"
    
    with open(messages_file) as f:
        messages = f.read()
    
    # Include the messages directly in the prompt instead of using the deprecated context parameter
    prompt = f"""Analyze the following conversation history between USER and {contact_name}:

{messages[:30000]}

Identify communication patterns, preferred topics, and linguistic styles.

CRITICAL INSTRUCTION: Your response MUST ONLY contain the final style guide with NO thinking process, NO drafts, NO notes, and NO meta-commentary. DO NOT include ANY <think> tags or similar markers. ANY content that is not part of the final style guide will be considered an error.

Your response must START DIRECTLY with the first heading and END with the last content item. Format your response EXACTLY as follows:

# Communication Style
[Your analysis of communication patterns here]

# Key Topics
[Your analysis of preferred topics here]

# Suggested Approaches
[Your suggested approaches here]"""
    
    payload = {
        "model": "qwen3:14b-32k",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 32768  # Increased context window for qwen3 model
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()["response"]
        
        # Post-process to remove any thinking tags or meta-commentary
        import re
        # Remove content between <think> tags
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
        # Remove any remaining <think> or </think> tags
        result = re.sub(r'</?think>', '', result)
        # Ensure the response starts with a heading
        result = re.sub(r'^\s*(?!#)', '# ', result)
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return None

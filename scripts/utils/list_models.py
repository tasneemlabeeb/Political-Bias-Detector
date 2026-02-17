#!/usr/bin/env python3
"""
Quick script to list available Gemini models
"""
import google.generativeai as genai
import sys

if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not api_key:
        print("Usage: python list_models.py <api_key>")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    print("Available Gemini models:")
    print("=" * 60)
    
    for model in genai.list_models():
        print(f"\nModel: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Supported Methods: {model.supported_generation_methods}")

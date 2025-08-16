#!/usr/bin/env python3
"""
Debug script to test the workflow directly
"""

import sys
import asyncio
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.nlp.language_detector import detect_language, determine_project_type
from backend.core.workflow import MultiAgentWorkflow

async def debug_workflow():
    """Debug the workflow directly"""
    description = "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text"
    name = "Persian Speech Translator"
    
    print(f"Description: {description}")
    
    # Test language detection
    detected_language = detect_language(description)
    project_type = determine_project_type(description, detected_language)
    
    print(f"🔍 Language detected: {detected_language}")
    print(f"📋 Project type: {project_type.value}")
    
    # Test workflow
    workflow = MultiAgentWorkflow()
    result = await workflow.execute({
        'description': description,
        'name': name,
        'language': detected_language,
        'project_type': project_type.value
    })
    
    # Check the generated content
    files = result.get('files', [])
    for file in files:
        if file.get('name') == 'main.py':
            content = file.get('content', '')
            print(f"\n📄 main.py content (first 10 lines):")
            lines = content.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                print(f"  {i}: {line}")
            
            # Check for specific imports
            has_speech = 'speech_recognition' in content
            has_google = 'googletrans' in content
            has_persian = 'persian' in content.lower() or 'farsi' in content.lower()
            
            print(f"\n🔍 Content analysis:")
            print(f"  Speech recognition: {'✅' if has_speech else '❌'}")
            print(f"  Google translate: {'✅' if has_google else '❌'}")
            print(f"  Persian/Farsi: {'✅' if has_persian else '❌'}")
            break

if __name__ == "__main__":
    asyncio.run(debug_workflow())
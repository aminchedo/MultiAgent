"""
Language Detection Module for Multi-Agent System

This module provides intelligent language detection based on project descriptions
and requirements to ensure the correct programming language is selected for code generation.
"""

from typing import Dict, List, Optional
from enum import Enum


class ProjectType(Enum):
    """Types of projects that can be generated"""
    CLI_TOOL = "cli_tool"
    WEB_APP = "web_app"
    API = "api"
    MOBILE_APP = "mobile_app"
    LIBRARY = "library"
    DESKTOP_APP = "desktop_app"
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"


def detect_language(description: str) -> str:
    """
    Detect the primary programming language from a project description.
    
    Args:
        description: Natural language project description
        
    Returns:
        Detected programming language (python, javascript, java, etc.)
    """
    description_lower = description.lower()
    
    # Comprehensive language indicators
    language_indicators = {
        'python': [
            'python', 'py', 'pip', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 
            'speech', 'audio', 'microphone', 'recognition', 'translation', 'persian', 
            'farsi', 'scikit-learn', 'tensorflow', 'pytorch', 'matplotlib', 'seaborn',
            'jupyter', 'anaconda', 'conda', 'virtualenv', 'pipenv', 'poetry'
        ],
        'javascript': [
            'javascript', 'js', 'node', 'nodejs', 'npm', 'react', 'vue', 'angular', 
            'express', 'next.js', 'nextjs', 'typescript', 'ts', 'webpack', 'babel',
            'jquery', 'lodash', 'moment', 'axios', 'fetch'
        ],
        'java': [
            'java', 'spring', 'springboot', 'maven', 'gradle', 'junit', 'hibernate',
            'jpa', 'servlet', 'jsp', 'android', 'kotlin'
        ],
        'go': [
            'go', 'golang', 'gin', 'echo', 'gorilla', 'cobra', 'viper'
        ],
        'rust': [
            'rust', 'cargo', 'actix', 'tokio', 'serde', 'clap'
        ],
        'csharp': [
            'c#', 'csharp', '.net', 'dotnet', 'asp.net', 'entity framework', 'linq'
        ],
        'php': [
            'php', 'laravel', 'symfony', 'composer', 'wordpress', 'drupal'
        ],
        'ruby': [
            'ruby', 'rails', 'gem', 'bundler', 'rake'
        ],
        'swift': [
            'swift', 'ios', 'xcode', 'cocoa', 'swiftui'
        ],
        'kotlin': [
            'kotlin', 'android', 'jetpack', 'compose'
        ]
    }
    
    max_matches = 0
    detected_language = 'python'  # Default fallback
    
    for language, indicators in language_indicators.items():
        matches = sum(1 for ind in indicators if ind in description_lower)
        if matches > max_matches:
            max_matches = matches
            detected_language = language
    
    return detected_language


def determine_project_type(description: str, detected_language: str = None) -> ProjectType:
    """
    Determine the project type based on description and detected language.
    
    Args:
        description: Natural language project description
        detected_language: Previously detected programming language
        
    Returns:
        ProjectType enum value
    """
    if detected_language is None:
        detected_language = detect_language(description)
    
    description_lower = description.lower()
    
    if detected_language == 'python':
        # Python-specific project type detection
        if any(word in description_lower for word in ['speech', 'audio', 'microphone', 'recognition', 'translation']):
            return ProjectType.CLI_TOOL
        elif any(word in description_lower for word in ['cli', 'command line', 'terminal', 'script', 'tool']):
            return ProjectType.CLI_TOOL
        elif any(word in description_lower for word in ['web', 'flask', 'django', 'fastapi', 'website']):
            return ProjectType.WEB_APP
        elif any(word in description_lower for word in ['api', 'rest', 'graphql', 'service']):
            return ProjectType.API
        elif any(word in description_lower for word in ['library', 'package', 'module', 'sdk']):
            return ProjectType.LIBRARY
        elif any(word in description_lower for word in ['data', 'analysis', 'pandas', 'numpy', 'matplotlib']):
            return ProjectType.DATA_ANALYSIS
        elif any(word in description_lower for word in ['ml', 'machine learning', 'ai', 'neural', 'model']):
            return ProjectType.MACHINE_LEARNING
        else:
            # Default for Python projects is CLI tool, not web app
            return ProjectType.CLI_TOOL
    
    elif detected_language == 'javascript':
        if any(word in description_lower for word in ['react', 'vue', 'angular', 'frontend', 'ui', 'interface']):
            return ProjectType.WEB_APP
        elif any(word in description_lower for word in ['node', 'express', 'api', 'backend']):
            return ProjectType.API
        elif any(word in description_lower for word in ['mobile', 'react native', 'flutter']):
            return ProjectType.MOBILE_APP
        else:
            return ProjectType.WEB_APP
    
    elif detected_language == 'java':
        if any(word in description_lower for word in ['android', 'mobile']):
            return ProjectType.MOBILE_APP
        elif any(word in description_lower for word in ['api', 'rest']):
            return ProjectType.API
        elif any(word in description_lower for word in ['spring', 'boot', 'web']):
            return ProjectType.WEB_APP
        else:
            return ProjectType.WEB_APP
    
    elif detected_language == 'swift':
        return ProjectType.MOBILE_APP
    
    elif detected_language == 'kotlin':
        return ProjectType.MOBILE_APP
    
    else:
        # Default to CLI tool for general scripts/tools
        return ProjectType.CLI_TOOL


def get_language_specific_prompt(language: str, project_type: ProjectType) -> str:
    """
    Get language-specific prompt for AI agents.
    
    Args:
        language: Detected programming language
        project_type: Determined project type
        
    Returns:
        Specialized prompt for the agent
    """
    base_prompts = {
        'python': {
            ProjectType.CLI_TOOL: "Senior Python CLI Developer with expertise in command-line tools, audio processing, and system automation",
            ProjectType.WEB_APP: "Senior Python Web Developer with expertise in Django, Flask, and FastAPI",
            ProjectType.API: "Senior Python API Developer with expertise in REST APIs, GraphQL, and microservices",
            ProjectType.DATA_ANALYSIS: "Senior Python Data Scientist with expertise in pandas, numpy, and data visualization",
            ProjectType.MACHINE_LEARNING: "Senior Python ML Engineer with expertise in scikit-learn, TensorFlow, and PyTorch"
        },
        'javascript': {
            ProjectType.WEB_APP: "Senior Frontend Developer with expertise in React, Vue, and modern JavaScript",
            ProjectType.API: "Senior Node.js Backend Developer with expertise in Express and REST APIs",
            ProjectType.MOBILE_APP: "Senior React Native Developer with expertise in mobile app development"
        },
        'java': {
            ProjectType.WEB_APP: "Senior Java Web Developer with expertise in Spring Boot and enterprise applications",
            ProjectType.API: "Senior Java API Developer with expertise in Spring REST and microservices",
            ProjectType.MOBILE_APP: "Senior Android Developer with expertise in Java and mobile app development"
        }
    }
    
    return base_prompts.get(language, {}).get(project_type, f"Senior {language.title()} Developer")


def validate_language_detection(description: str, expected_language: str) -> bool:
    """
    Validate that language detection is working correctly.
    
    Args:
        description: Project description
        expected_language: Expected language
        
    Returns:
        True if detection matches expectation
    """
    detected = detect_language(description)
    return detected == expected_language


# Test cases for validation
TEST_CASES = [
    {
        "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text",
        "expected_language": "python",
        "expected_type": ProjectType.CLI_TOOL
    },
    {
        "description": "Build a React web application with dashboard and charts",
        "expected_language": "javascript", 
        "expected_type": ProjectType.WEB_APP
    },
    {
        "description": "Create a Node.js REST API with Express and MongoDB",
        "expected_language": "javascript",
        "expected_type": ProjectType.API
    },
    {
        "description": "Develop a Java Spring Boot application for user management",
        "expected_language": "java",
        "expected_type": ProjectType.WEB_APP
    }
]


def run_language_detection_tests() -> bool:
    """
    Run comprehensive tests on language detection.
    
    Returns:
        True if all tests pass
    """
    print("🧪 TESTING REAL LANGUAGE DETECTION")
    print("=" * 50)
    
    all_passed = True
    
    for i, case in enumerate(TEST_CASES, 1):
        description = case["description"]
        expected_lang = case["expected_language"]
        expected_type = case["expected_type"]
        
        detected_lang = detect_language(description)
        detected_type = determine_project_type(description, detected_lang)
        
        lang_match = detected_lang == expected_lang
        type_match = detected_type == expected_type
        
        status = "✅ PASS" if (lang_match and type_match) else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"Description: {description[:60]}...")
        print(f"Language - Expected: {expected_lang}, Got: {detected_lang} {'✅' if lang_match else '❌'}")
        print(f"Type - Expected: {expected_type.value}, Got: {detected_type.value} {'✅' if type_match else '❌'}")
        
        if not (lang_match and type_match):
            all_passed = False
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    return all_passed


if __name__ == "__main__":
    run_language_detection_tests()
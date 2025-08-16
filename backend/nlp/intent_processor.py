"""
NLP Intent Processor for Natural Language Requirement Analysis

This module processes natural language user stories and requirements
to extract structured information for the multi-agent system.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import structlog

from backend.models.models import ProjectType, ComplexityLevel


logger = structlog.get_logger()


class RequirementType(Enum):
    """Types of requirements that can be extracted"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    TECHNICAL = "technical"
    USER_INTERFACE = "user_interface"
    DATA = "data"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class ExtractedFeature:
    """Represents an extracted feature from user story"""
    name: str
    description: str
    type: RequirementType
    priority: str  # p0, p1, p2, p3
    entities: List[str]
    actions: List[str]
    constraints: List[str]
    acceptance_criteria: List[str]


@dataclass
class ProjectIntent:
    """Structured representation of project intent"""
    project_type: ProjectType
    features: List[ExtractedFeature]
    tech_stack: Dict[str, List[str]]  # frontend, backend, database, etc.
    integrations: List[str]
    constraints: Dict[str, Any]
    complexity: ComplexityLevel
    priority_order: List[str]


class IntentProcessor:
    """
    Advanced NLP processor for extracting structured requirements
    from natural language descriptions.
    """
    
    def __init__(self, model_name: str = "bert-base-cased"):
        # Load spaCy model for linguistic analysis
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize transformers for advanced NLP
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.ner_pipeline = pipeline("ner", aggregation_strategy="simple")
        
        # Patterns and keywords
        self.tech_patterns = self._load_tech_patterns()
        self.feature_patterns = self._load_feature_patterns()
        self.project_type_indicators = self._load_project_type_indicators()
        
        logger.info("Intent processor initialized")
    
    async def process_requirements(self, user_story: str) -> ProjectIntent:
        """
        Process natural language requirements and extract structured intent.
        
        Args:
            user_story: Natural language project description
            
        Returns:
            Structured project intent
        """
        # Preprocess text
        cleaned_text = self._preprocess_text(user_story)
        
        # Extract components in parallel for efficiency
        doc = self.nlp(cleaned_text)
        
        # Extract various components
        project_type = self._identify_project_type(cleaned_text, doc)
        features = self._extract_features(cleaned_text, doc)
        tech_stack = self._extract_tech_stack(cleaned_text, doc)
        integrations = self._extract_integrations(cleaned_text, doc)
        constraints = self._extract_constraints(cleaned_text, doc)
        complexity = self._assess_complexity(features, tech_stack, integrations)
        priority_order = self._determine_priority_order(features)
        
        intent = ProjectIntent(
            project_type=project_type,
            features=features,
            tech_stack=tech_stack,
            integrations=integrations,
            constraints=constraints,
            complexity=complexity,
            priority_order=priority_order
        )
        
        logger.info("Processed requirements", 
                   features_count=len(features),
                   project_type=project_type.value)
        
        return intent
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Expand common contractions
        contractions = {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _identify_project_type(self, text: str, doc: spacy.tokens.Doc) -> ProjectType:
        """Identify the type of project from the description"""
        text_lower = text.lower()
        
        # Use zero-shot classification
        candidate_labels = [pt.value for pt in ProjectType]
        result = self.classifier(text, candidate_labels)
        
        # Get top prediction
        top_label = result['labels'][0]
        confidence = result['scores'][0]
        
        # Verify with keyword matching
        for project_type, indicators in self.project_type_indicators.items():
            indicator_count = sum(1 for ind in indicators if ind in text_lower)
            if indicator_count >= 2:
                return ProjectType(project_type)
        
        # Use classification result if confident
        if confidence > 0.7:
            return ProjectType(top_label)
        
        # Default fallback
        return ProjectType.WEB_APP
    
    def _extract_features(self, text: str, doc: spacy.tokens.Doc) -> List[ExtractedFeature]:
        """Extract features from the requirements"""
        features = []
        
        # Split into sentences for better feature extraction
        sentences = [sent.text.strip() for sent in doc.sents]
        
        for sentence in sentences:
            # Check for feature indicators
            feature_match = None
            for pattern in self.feature_patterns:
                match = re.search(pattern['regex'], sentence, re.IGNORECASE)
                if match:
                    feature_match = match
                    feature_type = RequirementType(pattern['type'])
                    break
            
            if feature_match:
                # Extract entities and actions from the sentence
                sent_doc = self.nlp(sentence)
                entities = [ent.text for ent in sent_doc.ents]
                actions = [token.text for token in sent_doc if token.pos_ == "VERB"]
                
                # Extract feature details
                feature = ExtractedFeature(
                    name=self._generate_feature_name(sentence, actions),
                    description=sentence,
                    type=feature_type,
                    priority=self._determine_priority(sentence),
                    entities=entities,
                    actions=actions,
                    constraints=self._extract_feature_constraints(sentence),
                    acceptance_criteria=self._generate_acceptance_criteria(sentence, actions, entities)
                )
                
                features.append(feature)
        
        # Also extract features using NER
        ner_features = self._extract_features_with_ner(text)
        features.extend(ner_features)
        
        # Deduplicate features
        unique_features = self._deduplicate_features(features)
        
        return unique_features
    
    def _extract_features_with_ner(self, text: str) -> List[ExtractedFeature]:
        """Use NER to extract additional features"""
        features = []
        
        # Custom patterns for feature extraction
        feature_patterns = [
            r"(?:user|admin|customer) (?:can|should be able to|must) (\w+\s*\w*)",
            r"(?:system|application) (?:shall|must|should) (\w+\s*\w*)",
            r"(?:need|require|want) (?:a|an|the)? (\w+\s*\w*)",
            r"(?:implement|create|build|develop) (?:a|an|the)? (\w+\s*\w*)"
        ]
        
        for pattern in feature_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action = match.group(1)
                
                # Create feature from match
                feature = ExtractedFeature(
                    name=f"{action}_feature",
                    description=match.group(0),
                    type=RequirementType.FUNCTIONAL,
                    priority="p2",
                    entities=[],
                    actions=[action],
                    constraints=[],
                    acceptance_criteria=[]
                )
                
                features.append(feature)
        
        return features
    
    def _extract_tech_stack(self, text: str, doc: spacy.tokens.Doc) -> Dict[str, List[str]]:
        """Extract technology stack from requirements"""
        tech_stack = {
            "frontend": [],
            "backend": [],
            "database": [],
            "deployment": [],
            "tools": []
        }
        
        text_lower = text.lower()
        
        # Check against known technology patterns
        for category, patterns in self.tech_patterns.items():
            for tech, keywords in patterns.items():
                if any(keyword in text_lower for keyword in keywords):
                    tech_stack[category].append(tech)
        
        # Use NER to find additional technologies
        entities = self.ner_pipeline(text)
        for entity in entities:
            if entity['entity_group'] in ['ORG', 'PRODUCT']:
                tech_name = entity['word'].lower()
                # Categorize based on common patterns
                if any(kw in tech_name for kw in ['react', 'vue', 'angular', 'next']):
                    tech_stack['frontend'].append(tech_name)
                elif any(kw in tech_name for kw in ['node', 'python', 'java', 'go']):
                    tech_stack['backend'].append(tech_name)
                elif any(kw in tech_name for kw in ['postgres', 'mysql', 'mongo', 'redis']):
                    tech_stack['database'].append(tech_name)
        
        # Remove duplicates
        for category in tech_stack:
            tech_stack[category] = list(set(tech_stack[category]))
        
        return tech_stack
    
    def _extract_integrations(self, text: str, doc: spacy.tokens.Doc) -> List[str]:
        """Extract third-party integrations"""
        integrations = []
        
        # Common integration patterns
        integration_patterns = [
            r"integrate(?:s|d)?\s+(?:with\s+)?(\w+)",
            r"connect(?:s|ed)?\s+(?:to|with)\s+(\w+)",
            r"(?:use|using)\s+(\w+)\s+API",
            r"(?:payment|auth|authentication)\s+(?:via|through|using)\s+(\w+)"
        ]
        
        for pattern in integration_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                integration = match.group(1)
                integrations.append(integration)
        
        # Check for known integration services
        known_integrations = {
            'stripe': ['stripe', 'payment processing'],
            'paypal': ['paypal'],
            'auth0': ['auth0', 'authentication'],
            'oauth': ['oauth', 'oauth2'],
            'google': ['google maps', 'google analytics', 'google auth'],
            'facebook': ['facebook login', 'facebook api'],
            'twitter': ['twitter api', 'twitter integration'],
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure', 'microsoft azure'],
            'twilio': ['twilio', 'sms', 'text messaging'],
            'sendgrid': ['sendgrid', 'email service'],
            'slack': ['slack integration', 'slack api'],
            'github': ['github', 'github api'],
            'jira': ['jira', 'jira integration']
        }
        
        text_lower = text.lower()
        for service, keywords in known_integrations.items():
            if any(keyword in text_lower for keyword in keywords):
                integrations.append(service)
        
        return list(set(integrations))
    
    def _extract_constraints(self, text: str, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Extract project constraints"""
        constraints = {
            'performance': [],
            'security': [],
            'compatibility': [],
            'timeline': [],
            'budget': [],
            'regulatory': []
        }
        
        # Performance constraints
        perf_patterns = [
            r"(?:must|should)\s+(?:handle|support)\s+(\d+)\s+(?:users|requests|transactions)",
            r"(?:response time|latency)\s+(?:under|less than|<)\s+(\d+)\s*(?:ms|milliseconds|seconds)",
            r"(?:load|handle)\s+(\d+)\s+(?:concurrent|simultaneous)"
        ]
        
        for pattern in perf_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                constraints['performance'].append(match.group(0))
        
        # Security constraints
        if any(word in text.lower() for word in ['secure', 'encryption', 'ssl', 'https', 'authentication', 'authorization']):
            constraints['security'].append('Security requirements mentioned')
        
        # Compatibility constraints
        compat_patterns = [
            r"(?:compatible|support)\s+(?:with\s+)?(\w+\s+\d+(?:\.\d+)?)",
            r"(?:browser|device)\s+(?:support|compatibility)"
        ]
        
        for pattern in compat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                constraints['compatibility'].append(match.group(0))
        
        # Timeline constraints
        timeline_patterns = [
            r"(?:complete|deliver|launch)\s+(?:by|within|in)\s+(\d+\s+(?:days|weeks|months))",
            r"(?:deadline|due date)\s+(?:is|:)\s+([^\n.]+)"
        ]
        
        for pattern in timeline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                constraints['timeline'].append(match.group(0))
        
        return constraints
    
    def _assess_complexity(self, 
                          features: List[ExtractedFeature],
                          tech_stack: Dict[str, List[str]],
                          integrations: List[str]) -> ComplexityLevel:
        """Assess project complexity based on extracted information"""
        complexity_score = 0
        
        # Feature complexity
        complexity_score += len(features) * 0.5
        
        # Technical complexity
        total_tech = sum(len(techs) for techs in tech_stack.values())
        complexity_score += total_tech * 0.3
        
        # Integration complexity
        complexity_score += len(integrations) * 0.7
        
        # Feature type complexity
        complex_features = [f for f in features if f.type in [
            RequirementType.INTEGRATION,
            RequirementType.SECURITY,
            RequirementType.PERFORMANCE
        ]]
        complexity_score += len(complex_features) * 1.0
        
        # Determine complexity level
        if complexity_score < 5:
            return ComplexityLevel.SIMPLE
        elif complexity_score < 10:
            return ComplexityLevel.MODERATE
        elif complexity_score < 20:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.ENTERPRISE
    
    def _determine_priority_order(self, features: List[ExtractedFeature]) -> List[str]:
        """Determine the order in which features should be implemented"""
        # Sort features by priority
        priority_map = {'p0': 0, 'p1': 1, 'p2': 2, 'p3': 3}
        sorted_features = sorted(features, key=lambda f: priority_map.get(f.priority, 3))
        
        # Group by dependency
        core_features = [f.name for f in sorted_features if f.type in [
            RequirementType.DATA,
            RequirementType.SECURITY
        ]]
        
        functional_features = [f.name for f in sorted_features if f.type == RequirementType.FUNCTIONAL]
        
        ui_features = [f.name for f in sorted_features if f.type == RequirementType.USER_INTERFACE]
        
        integration_features = [f.name for f in sorted_features if f.type == RequirementType.INTEGRATION]
        
        # Build priority order
        priority_order = core_features + functional_features + ui_features + integration_features
        
        # Remove duplicates while preserving order
        seen = set()
        priority_order = [x for x in priority_order if not (x in seen or seen.add(x))]
        
        return priority_order
    
    def _generate_feature_name(self, sentence: str, actions: List[str]) -> str:
        """Generate a concise feature name"""
        if actions:
            return f"{actions[0]}_feature"
        
        # Extract key nouns
        doc = self.nlp(sentence)
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        
        if nouns:
            return f"{nouns[0]}_feature"
        
        # Fallback
        return "unnamed_feature"
    
    def _determine_priority(self, sentence: str) -> str:
        """Determine feature priority from text"""
        sentence_lower = sentence.lower()
        
        # Priority indicators
        if any(word in sentence_lower for word in ['critical', 'must', 'essential', 'required']):
            return 'p0'
        elif any(word in sentence_lower for word in ['should', 'important', 'needed']):
            return 'p1'
        elif any(word in sentence_lower for word in ['could', 'nice to have', 'optional']):
            return 'p2'
        else:
            return 'p3'
    
    def _extract_feature_constraints(self, sentence: str) -> List[str]:
        """Extract constraints specific to a feature"""
        constraints = []
        
        # Time constraints
        time_match = re.search(r'within\s+(\d+\s+(?:seconds|minutes|hours))', sentence, re.IGNORECASE)
        if time_match:
            constraints.append(f"Time limit: {time_match.group(1)}")
        
        # Quantity constraints
        quantity_match = re.search(r'(?:up to|maximum|at least|minimum)\s+(\d+)', sentence, re.IGNORECASE)
        if quantity_match:
            constraints.append(f"Quantity: {quantity_match.group(0)}")
        
        # Format constraints
        format_match = re.search(r'(?:format|type):\s*(\w+)', sentence, re.IGNORECASE)
        if format_match:
            constraints.append(f"Format: {format_match.group(1)}")
        
        return constraints
    
    def _generate_acceptance_criteria(self, 
                                    sentence: str, 
                                    actions: List[str], 
                                    entities: List[str]) -> List[str]:
        """Generate acceptance criteria for a feature"""
        criteria = []
        
        # Basic criteria structure
        if actions:
            criteria.append(f"User can {actions[0]}")
            criteria.append(f"System validates {actions[0]} action")
            criteria.append(f"Error handling for {actions[0]} failure")
        
        # Entity-based criteria
        for entity in entities:
            criteria.append(f"{entity} is properly handled")
        
        # Performance criteria
        if 'fast' in sentence.lower() or 'quick' in sentence.lower():
            criteria.append("Response time under 2 seconds")
        
        # Security criteria
        if any(word in sentence.lower() for word in ['secure', 'auth', 'private']):
            criteria.append("Proper authentication required")
            criteria.append("Data is encrypted")
        
        return criteria[:5]  # Limit to 5 criteria
    
    def _deduplicate_features(self, features: List[ExtractedFeature]) -> List[ExtractedFeature]:
        """Remove duplicate features"""
        seen = set()
        unique_features = []
        
        for feature in features:
            # Create a simple hash for comparison
            feature_hash = f"{feature.name}:{':'.join(feature.actions)}"
            
            if feature_hash not in seen:
                seen.add(feature_hash)
                unique_features.append(feature)
        
        return unique_features
    
    def _load_tech_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Load technology detection patterns"""
        return {
            'frontend': {
                'react': ['react', 'reactjs', 'react.js'],
                'vue': ['vue', 'vuejs', 'vue.js'],
                'angular': ['angular', 'angularjs'],
                'nextjs': ['next', 'nextjs', 'next.js'],
                'svelte': ['svelte', 'sveltekit'],
                'tailwind': ['tailwind', 'tailwindcss']
            },
            'backend': {
                'nodejs': ['node', 'nodejs', 'node.js', 'express'],
                'python': ['python', 'django', 'flask', 'fastapi'],
                'java': ['java', 'spring', 'springboot'],
                'go': ['go', 'golang', 'gin', 'echo'],
                'rust': ['rust', 'actix', 'rocket'],
                'csharp': ['c#', 'csharp', '.net', 'dotnet']
            },
            'database': {
                'postgresql': ['postgres', 'postgresql', 'pg'],
                'mysql': ['mysql', 'mariadb'],
                'mongodb': ['mongo', 'mongodb'],
                'redis': ['redis', 'cache'],
                'elasticsearch': ['elasticsearch', 'elastic'],
                'sqlite': ['sqlite', 'sqlite3']
            },
            'deployment': {
                'docker': ['docker', 'container', 'dockerfile'],
                'kubernetes': ['kubernetes', 'k8s'],
                'aws': ['aws', 'ec2', 's3', 'lambda'],
                'gcp': ['gcp', 'google cloud'],
                'azure': ['azure', 'microsoft cloud'],
                'vercel': ['vercel', 'zeit'],
                'netlify': ['netlify']
            }
        }
    
    def _load_feature_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns for feature extraction"""
        return [
            {
                'regex': r'(?:user|users|customer|admin)\s+(?:can|should|must|shall)\s+(\w+)',
                'type': 'functional'
            },
            {
                'regex': r'(?:login|authentication|auth|sign\s*in|register)',
                'type': 'security'
            },
            {
                'regex': r'(?:dashboard|ui|interface|design|layout|theme)',
                'type': 'user_interface'
            },
            {
                'regex': r'(?:api|endpoint|rest|graphql|websocket)',
                'type': 'integration'
            },
            {
                'regex': r'(?:database|data|storage|model|schema)',
                'type': 'data'
            },
            {
                'regex': r'(?:performance|speed|fast|optimization|cache)',
                'type': 'performance'
            },
            {
                'regex': r'(?:test|testing|quality|qa)',
                'type': 'technical'
            }
        ]
    
    def _load_project_type_indicators(self) -> Dict[str, List[str]]:
        """Load indicators for project type detection"""
        return {
            'web_app': ['website', 'web application', 'web app', 'portal', 'dashboard'],
            'api': ['api', 'rest api', 'graphql', 'backend service', 'microservice'],
            'mobile_app': ['mobile', 'ios', 'android', 'react native', 'flutter'],
            'desktop_app': ['desktop', 'windows app', 'mac app', 'electron'],
            'cli_tool': ['cli', 'command line', 'terminal', 'console app'],
            'library': ['library', 'package', 'sdk', 'framework', 'module'],
            'microservice': ['microservice', 'service mesh', 'distributed'],
            'fullstack': ['full stack', 'fullstack', 'frontend and backend']
        }
    
    def to_dict(self, intent: ProjectIntent) -> Dict[str, Any]:
        """Convert ProjectIntent to dictionary format"""
        return {
            'project_type': intent.project_type.value,
            'features': [
                {
                    'name': f.name,
                    'description': f.description,
                    'type': f.type.value,
                    'priority': f.priority,
                    'entities': f.entities,
                    'actions': f.actions,
                    'constraints': f.constraints,
                    'acceptance_criteria': f.acceptance_criteria
                }
                for f in intent.features
            ],
            'tech_stack': intent.tech_stack,
            'integrations': intent.integrations,
            'constraints': intent.constraints,
            'complexity': intent.complexity.value,
            'priority_order': intent.priority_order
        }
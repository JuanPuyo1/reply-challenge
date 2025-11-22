"""
AI Triage Agent Service
Uses LangChain and OpenAI to create dynamic, contextual form interactions
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class TriageAgent:
    
    def __init__(self, api_key: str):
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=api_key
        )
    
    def generate_dynamic_placeholder(self, symptoms: str, has_clinical_history: bool = False) -> str:
        """
        Generate a personalized placeholder for the additional context field
        based on the symptoms described by the user
        
        Args:
            symptoms: User's described symptoms
            has_clinical_history: Whether user uploaded clinical history
            
        Returns:
            Contextual placeholder text
        """
        system_prompt = """You are a compassionate clinical intake coordinator AI. 
        Your role is to help patients provide relevant information for matching them with specialists.
        
        Based on the user's symptoms, generate a SHORT, EMPATHETIC prompt (1-2 sentences max) 
        asking for additional relevant context that would help match them with the right specialist.
        
        Examples:
        - For anxiety: "When does this anxiety feel strongest? Are there specific triggers?"
        - For sleep issues: "How long have you been experiencing this? Does it affect your daily life?"
        - For academic stress: "Are you currently in school or university? What support have you tried so far?"
        
        Keep it conversational, warm, and specific to their situation.
        DO NOT use generic placeholders. Make it personalized."""
        
        history_context = ""
        if has_clinical_history:
            history_context = " (Note: The user has uploaded clinical history.)"
        
        human_prompt = f"User's symptoms: '{symptoms}'{history_context}\n\nGenerate a personalized placeholder prompt:"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            placeholder = response.content.strip()
            # Remove quotes if the model added them
            placeholder = placeholder.strip('"').strip("'")
            return placeholder
        except Exception as e:
            # Fallback to generic placeholder
            print(f"Error generating placeholder: {e}")
            return "Tell us more about your situation, including duration, severity, and what you've tried so far..."
    
    def analyze_symptoms(self, symptoms: str, additional_context: str = "") -> dict:
        """
        Analyze symptoms to determine urgency and initial categorization
        Phase 1: Basic analysis for safety guardrails
        
        Returns:
            dict with 'urgency', 'category', 'safety_concern'
        """
        system_prompt = """You are a clinical triage AI assistant. 
        Analyze the user's symptoms and provide:
        1. Urgency level (low, medium, high, crisis)
        2. Main category (anxiety, depression, trauma, relationship, academic, other)
        3. Safety concern flag (true if mentions self-harm, suicide, or harming others)
        
        Respond ONLY in this JSON format:
        {"urgency": "level", "category": "category", "safety_concern": true/false, "reasoning": "brief explanation"}
        """
        
        full_input = f"Symptoms: {symptoms}\nAdditional Context: {additional_context}" if additional_context else f"Symptoms: {symptoms}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_input)
        ]
        
        try:
            response = self.llm.invoke(messages)
            # Parse JSON response
            import json
            result = json.loads(response.content.strip())
            return result
        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return {
                "urgency": "medium",
                "category": "other",
                "safety_concern": False,
                "reasoning": "Unable to analyze at this time"
            }
    
    def process_full_submission(self, email: str, symptoms: str, additional_context: str = "", 
                               has_clinical_history: bool = False) -> str:
        """
        SECOND AGENT: Deep processing of the complete submission
        
        Creates a unified text document containing:
        1. User submission data (formatted clearly)
        2. Comprehensive AI analysis
        
        Args:
            email: User's email
            symptoms: User's symptoms
            additional_context: Additional context provided
            has_clinical_history: Whether clinical history was uploaded
            
        Returns:
            str: Complete unified text with user data + AI analysis
        """
        # Create user submission section
        user_data = self._create_user_submission_text(
            email=email,
            symptoms=symptoms,
            additional_context=additional_context,
            has_clinical_history=has_clinical_history
        )
        
        # Deep analysis system prompt
        system_prompt = """You are a senior clinical psychologist and referral specialist with 20+ years of experience.

Your task is to perform a COMPREHENSIVE analysis of a patient's intake submission. Pay special attention to:

1. **Patient Profile**: Email/contact info, communication style, emotional tone
2. **Clinical Presentation**: Primary symptoms, secondary symptoms, duration, severity
3. **Psychosocial Context**: Life circumstances, stressors, support systems
4. **Treatment Readiness**: Motivation, insight, barriers to treatment
5. **Risk Assessment**: Safety concerns, urgency factors
6. **Specialist Recommendation**: What type of specialist would be BEST suited (be specific)

Write your analysis as a comprehensive clinical report (3-5 paragraphs). Be thorough, empathetic, and clinically precise.
Include a clear recommendation for specialist type at the end."""
        
        human_prompt = f"""Please analyze this patient intake submission:

{user_data}

Provide your comprehensive clinical analysis as a detailed report."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            ai_analysis = response.content.strip()
            
            # Combine user data and AI analysis into unified text
            unified_text = self._create_unified_document(user_data, ai_analysis)
            
            return unified_text
            
        except Exception as e:
            print(f"Error in deep processing: {e}")
            # Fallback response
            ai_analysis = "Unable to complete comprehensive analysis at this time. Patient presents with symptoms requiring professional evaluation. Recommend general mental health assessment."
            return self._create_unified_document(user_data, ai_analysis)
    
    def _create_user_submission_text(self, email: str, symptoms: str, 
                                     additional_context: str = "", 
                                     has_clinical_history: bool = False) -> str:
        """
        Helper method to create formatted user submission text
        """
        from datetime import datetime
        
        text_parts = [
            "=" * 70,
            "PATIENT INTAKE SUBMISSION",
            "=" * 70,
            f"\nSubmission Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"Patient Contact: {email}",
            f"Clinical History on File: {'Yes' if has_clinical_history else 'No'}",
            "\n" + "-" * 70,
            "PRESENTING SYMPTOMS:",
            "-" * 70,
            symptoms,
        ]
        
        if additional_context and additional_context.strip():
            text_parts.extend([
                "\n" + "-" * 70,
                "ADDITIONAL CONTEXT:",
                "-" * 70,
                additional_context
            ])
        
        text_parts.append("\n" + "=" * 70)
        
        return "\n".join(text_parts)
    
    def _create_unified_document(self, user_data: str, ai_analysis: str) -> str:
        """
        Combines user submission data and AI analysis into single unified text
        """
        unified_parts = [
            user_data,
            "",
            "",
            "=" * 70,
            "AI CLINICAL ANALYSIS",
            "=" * 70,
            "",
            ai_analysis,
            "",
            "=" * 70,
            "END OF REPORT",
            "=" * 70
        ]
        
        return "\n".join(unified_parts)


# Singleton instance manager
_agent_instance: Optional[TriageAgent] = None


def get_triage_agent(api_key: Optional[str] = None) -> TriageAgent:
    """
    Get or create the triage agent singleton
    """
    global _agent_instance
    
    if _agent_instance is None:
        if api_key is None:
            # Try to get from environment
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not provided and not found in environment")
        
        _agent_instance = TriageAgent(api_key)
    
    return _agent_instance


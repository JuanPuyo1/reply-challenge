"""
Mental Health Specialist Matching Agent

This agent analyzes user mental health concerns and matches them with
the most appropriate specialist from a CSV database.
"""

import os
import json
import pandas as pd
from openai import OpenAI
from typing import Dict, List, Optional
from enum import Enum
from dotenv import load_dotenv


class ConversationState(Enum):
    """Enum for tracking conversation state."""
    GREETING = "greeting"
    ASKING_PATIENT_INFO = "asking_patient_info"
    ASKING_SYMPTOMS = "asking_symptoms"
    ASKING_CLINICAL_HISTORY = "asking_clinical_history"
    ASKING_CONTEXT = "asking_context"
    PROCESSING = "processing"
    COMPLETED = "completed"


class MentalHealthAgent:
    """
    Agent that matches users with mental health specialists based on their concerns.
    """

    def __init__(self, api_key: Optional[str] = None, specialists_csv: str = "specialists.csv"):
        """
        Initialize the Mental Health Agent.

        Args:
            api_key: OpenAI API key (if None, loads from environment)
            specialists_csv: Path to CSV file containing specialist information
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file or pass as argument.")

        self.client = OpenAI(api_key=self.api_key)
        self.specialists_csv = specialists_csv
        self.specialists_df = None
        self._load_specialists()

        # Conversation state management
        self.state = ConversationState.GREETING
        self.collected_info = {
            "patient_name": None,
            "patient_age": None,
            "patient_address": None,
            "patient_gender": None,
            "symptoms": None,
            "clinical_history": None,
            "context": None
        }

    def _load_specialists(self):
        """Load specialist data from CSV file."""
        try:
            self.specialists_df = pd.read_excel(self.specialists_csv)
            print(f"Loaded {len(self.specialists_df)} specialists from {self.specialists_csv}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Specialists CSV file not found: {self.specialists_csv}")
        except Exception as e:
            raise Exception(f"Error loading specialists CSV: {str(e)}")

    def _parse_patient_info(self, user_input: str):
        """
        Parse patient information from user input using GPT.

        Args:
            user_input: Raw text containing patient information
        """
        parse_prompt = f"""
Extract the following patient information from the text below. If any field is not found, use "Not provided" as the value.

Text: "{user_input}"

Please provide a JSON response with the following structure:
{{
    "patient_name": "full name of the patient",
    "patient_age": "age of the patient",
    "patient_address": "address of the patient",
    "patient_gender": "gender of the patient"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                    {"role": "user", "content": parse_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            parsed_info = json.loads(response.choices[0].message.content)
            self.collected_info["patient_name"] = parsed_info.get("patient_name", "Not provided")
            self.collected_info["patient_age"] = parsed_info.get("patient_age", "Not provided")
            self.collected_info["patient_address"] = parsed_info.get("patient_address", "Not provided")
            self.collected_info["patient_gender"] = parsed_info.get("patient_gender", "Not provided")

        except Exception as e:
            # Fallback: store raw input if parsing fails
            self.collected_info["patient_name"] = "Not provided"
            self.collected_info["patient_age"] = "Not provided"
            self.collected_info["patient_address"] = "Not provided"
            self.collected_info["patient_gender"] = "Not provided"
            print(f"Warning: Could not parse patient info: {str(e)}")

    def reset_conversation(self):
        """Reset the conversation to start over."""
        self.state = ConversationState.GREETING
        self.collected_info = {
            "patient_name": None,
            "patient_age": None,
            "patient_address": None,
            "patient_gender": None,
            "symptoms": None,
            "clinical_history": None,
            "context": None
        }

    def chat(self, user_input: str) -> Dict:
        """
        Handle conversational interaction with the user.

        Args:
            user_input: The user's current message

        Returns:
            Dictionary containing:
                - response: The agent's response to the user
                - state: Current conversation state
                - completed: Whether all information has been collected
        """
        if self.state == ConversationState.GREETING:
            self.state = ConversationState.ASKING_PATIENT_INFO
            return {
                "response": "Hello! I'm here to help match you with the right mental health specialist. To provide the best recommendation, I'd like to start by collecting some basic information.\n\nPlease provide the following information:\n- Full Name:\n- Age:\n- Address:\n- Gender:",
                "state": self.state.value,
                "completed": False
            }

        elif self.state == ConversationState.ASKING_PATIENT_INFO:
            # Parse patient information from user input using GPT
            self._parse_patient_info(user_input)
            self.state = ConversationState.ASKING_SYMPTOMS
            return {
                "response": f"Thank you, {self.collected_info['patient_name']}! Now let's discuss your concerns.\n\nCould you please describe the symptoms you've been experiencing? This could include feelings, behaviors, or physical sensations.",
                "state": self.state.value,
                "completed": False
            }

        elif self.state == ConversationState.ASKING_SYMPTOMS:
            self.collected_info["symptoms"] = user_input
            self.state = ConversationState.ASKING_CLINICAL_HISTORY
            return {
                "response": "Thank you for sharing that with me. I understand this can be difficult to talk about.\n\nNext, could you tell me about your clinical history? This includes any previous mental health diagnoses, past treatments or therapy, medications you're taking, or relevant medical conditions.",
                "state": self.state.value,
                "completed": False
            }

        elif self.state == ConversationState.ASKING_CLINICAL_HISTORY:
            self.collected_info["clinical_history"] = user_input
            self.state = ConversationState.ASKING_CONTEXT
            return {
                "response": "I appreciate you sharing that information.\n\nFinally, could you provide some context about your situation? This might include when these symptoms started, what triggers them, how they're affecting your daily life, work, or relationships, and what you hope to achieve through treatment.",
                "state": self.state.value,
                "completed": False
            }

        elif self.state == ConversationState.ASKING_CONTEXT:
            self.collected_info["context"] = user_input
            self.state = ConversationState.PROCESSING
            return {
                "response": "Thank you for providing all that information. Let me analyze your needs and find the most suitable specialist for you...",
                "state": self.state.value,
                "completed": True
            }

        else:
            return {
                "response": "I've already collected all the necessary information. Processing your request...",
                "state": self.state.value,
                "completed": True
            }

    def _calculate_location_proximity(self, patient_address: str, doctor_address: str) -> float:
        """
        Use GPT to calculate proximity score between patient and doctor locations.

        Args:
            patient_address: Patient's address
            doctor_address: Doctor's address

        Returns:
            Float score representing proximity (higher = closer)
        """
        proximity_prompt = f"""
You are a location analysis assistant. Compare the following two addresses and determine their proximity.

Patient Address: "{patient_address}"
Doctor Address: "{doctor_address}"

Please provide a JSON response with the following structure:
{{
    "estimated_distance_category": "less than 1km/1-5km/5-10km/more than 10km/different city/different country/unknown",
    "proximity_score": <number between 0 and 5, where 5 is same location, 4 is within 1km, 3 is 1-5km, 2 is 5-10km, 1 is more than 10km same city, 0 is different city, -1 is different country>,
    "reasoning": "brief explanation of the proximity assessment"
}}

Consider:
- Same street/building = highest score
- Same neighborhood = high score
- Same city but different area = medium score
- Different cities in same region = low score
- Different countries = lowest score
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a geographic location analysis expert."},
                    {"role": "user", "content": proximity_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            proximity_data = json.loads(response.choices[0].message.content)
            return proximity_data.get("proximity_score", 5.0)

        except Exception as e:
            print(f"Warning: Could not calculate location proximity: {str(e)}")
            return 5.0  # Default medium score if calculation fails

    def _analyze_user_concerns(self, address: str,
                               symptoms: str, clinical_history: str, context: str) -> Dict:
        """
        Use GPT to analyze user's mental health concerns and extract key information.

        Args:
            symptoms: User's description of their symptoms
            clinical_history: User's clinical history
            context: User's contextual information

        Returns:
            Dictionary containing analyzed concerns, severity, and keywords
        """
        analysis_prompt = f"""
You are a mental health triage assistant. Analyze the following user's information and extract key details.

"Location": "{address}"
Symptoms: "{symptoms}"
Clinical History: "{clinical_history}"
Context: "{context}"

Please provide a JSON response with the following structure:
{{
    "primary_concerns": ["list of main mental health issues mentioned"],
    "symptoms": ["list of specific symptoms or behaviors"],
    "urgency_level": "low/moderate/high",
    "keywords": ["keywords that would help match with specialist expertise"],
    "summary": "brief summary of the user's situation"
}}

Be empathetic but professional. Focus on identifying the type of help needed.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a compassionate mental health triage assistant."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            raise Exception(f"Error analyzing user concerns: {str(e)}")

    def _match_specialist(self, analysis: Dict, patient_address: str) -> Dict:
        """
        Match the user's concerns with the most appropriate specialist.

        Args:
            analysis: Dictionary containing analyzed user concerns
            patient_address: Patient's address for location proximity calculation

        Returns:
            Dictionary containing matched specialist information
        """
        keywords = analysis.get("keywords", [])
        primary_concerns = analysis.get("primary_concerns", [])

        # Create search terms from keywords and concerns
        search_terms = " ".join(keywords + primary_concerns).lower()

        # Score each specialist based on expertise match and location proximity
        specialists_list = self.specialists_df.to_dict('records')
        scored_specialists = []

        print(f"Evaluating {len(specialists_list)} specialists...")

        for idx, specialist in enumerate(specialists_list):
            expertise_score = 0
            expertise = str(specialist.get('Specialist', '')).lower()
            specialization = str(specialist.get('Subspecialty', '')).lower()

            # Check how many keywords match the specialist's expertise
            for term in search_terms.split():
                term_lower = term.lower()
                if term_lower in expertise:
                    expertise_score += 2
                if term_lower in specialization:
                    expertise_score += 1

            # Calculate location proximity score using GPT
            doctor_address = str(specialist.get('Address', ''))
            print(f"  [{idx+1}/{len(specialists_list)}] Calculating proximity for {specialist.get('Name', 'Unknown')}...")

            location_score = self._calculate_location_proximity(patient_address, doctor_address)

            # Combined score: expertise weighted 70%, location weighted 30%
            total_score = (expertise_score * 0.7) + (location_score * 0.3)

            specialist['expertise_score'] = expertise_score
            specialist['location_score'] = location_score
            specialist['match_score'] = total_score
            scored_specialists.append(specialist)

        # Sort by total score and get top match
        scored_specialists.sort(key=lambda x: x['match_score'], reverse=True)

        if scored_specialists[0]['match_score'] == 0:
            # No strong match found, return first specialist with a note
            best_match = scored_specialists[0]
            best_match['match_note'] = "General recommendation - please describe your concerns to the specialist"
        else:
            best_match = scored_specialists[0]
            expertise_desc = f"expertise match: {best_match['expertise_score']:.1f}"
            location_desc = f"location score: {best_match['location_score']:.1f}/10"
            best_match['match_note'] = f"Best match ({expertise_desc}, {location_desc}) for: {', '.join(primary_concerns[:3])}"

        return best_match

    def _generate_recommendations(self, symptoms: str, clinical_history: str, context: str, analysis: Dict, specialist: Dict) -> str:
        """
        Generate personalized recommendations using GPT.

        Args:
            symptoms: User's symptoms
            clinical_history: User's clinical history
            context: User's context
            analysis: Analyzed concerns
            specialist: Matched specialist information

        Returns:
            String containing recommendations
        """
        recommendation_prompt = f"""
Based on the following information, provide brief, actionable recommendations for the user:

Symptoms: {symptoms}
Clinical History: {clinical_history}
Context: {context}
Summary: {analysis.get('summary', '')}
Primary issues: {', '.join(analysis.get('primary_concerns', []))}
Urgency level: {analysis.get('urgency_level', 'moderate')}
Matched specialist: {specialist.get('name', '')} - {specialist.get('specialization', '')}

Provide 3-4 brief recommendations on:
1. What to prepare before the first appointment
2. Self-care steps they can take now
3. What to expect from therapy with this specialist
4. When to seek immediate help (if urgency is high)

Keep it supportive, practical, and under 200 words.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a supportive mental health advisor providing practical guidance."},
                    {"role": "user", "content": recommendation_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )

            recommendations = response.choices[0].message.content
            return recommendations

        except Exception as e:
            return f"Unable to generate detailed recommendations at this time. Please discuss your concerns directly with the specialist."

    def process_collected_information(self) -> Dict:
        """
        Process the collected information and generate specialist recommendation.

        Returns:
            Dictionary containing:
                - patient_info: Patient's basic information
                - summary: Brief summary of user's concerns
                - specialist: Information about matched specialist
                - recommendations: Personalized recommendations
                - analysis: Detailed analysis of concerns
        """
        # Check that at least the critical medical information is collected
        required_fields = ["patient_name", "patient_age",
                           "patient_address", "patient_gender",
                           "symptoms", "clinical_history", "context"]
        if not all(self.collected_info[field] for field in required_fields):
            raise ValueError("Not all information has been collected. Please complete the conversation first.")

        address = self.collected_info["patient_address"]
        symptoms = self.collected_info["symptoms"]
        clinical_history = self.collected_info["clinical_history"]
        context = self.collected_info["context"]

        print("Analyzing user concerns...")
        analysis = self._analyze_user_concerns(address, symptoms, clinical_history, context)

        print("Matching with appropriate specialist based on expertise and location...")
        specialist = self._match_specialist(analysis, address)

        print("Generating personalized recommendations...")
        recommendations = self._generate_recommendations(symptoms, clinical_history, context, analysis, specialist)

        self.state = ConversationState.COMPLETED

        # Prepare output
        result = {
            "patient_info": {
                "name": self.collected_info.get("patient_name", ""),
                "age": self.collected_info.get("patient_age", ""),
                "address": self.collected_info.get("patient_address", ""),
                "gender": self.collected_info.get("patient_gender", "")
            },
            "summary": analysis.get("summary", ""),
            "urgency_level": analysis.get("urgency_level", ""),
            "specialist": {
                "name": specialist.get("Name", ""),
                "expertise": specialist.get("Subspecialty", ""),
                "location": specialist.get("Address", ""),
                "phone_number": specialist.get("Phone", ""),
                "email": specialist.get("Email", ""),
                "schedule": specialist.get("Available Hours", ""),
                "modality": specialist.get("Modality", ""),
                "match_note": specialist.get("match_note", ""),
                "expertise_score": specialist.get("expertise_score", 0),
                "location_score": specialist.get("location_score", 0),
                "total_score": specialist.get("match_score", 0)
            },
            "recommendations": recommendations,
            "analysis": {
                "symptoms": analysis.get("symptoms", [])
            }
        }

        return result


def main():
    """Example usage of the Mental Health Agent with conversational flow."""
    # Initialize agent
    agent = MentalHealthAgent(specialists_csv="static/Specialist_EN.xlsx")

    print("=== Mental Health Specialist Matching - Conversational Mode ===\n")

    # Start the conversation
    response = agent.chat("")
    print(f"Agent: {response['response']}\n")

    # Example user responses
    user_responses = [
        # General information from patient
        """
        Name: Alice Brown
        Age: 29
        Address: Via Maria Ausilliatrice 32, Turin, Italy
        Gender: Female
        """,
        
        # Response to symptoms question
        """I've been feeling really anxious lately, especially in social situations.
        My heart races, I start sweating, and sometimes I feel like I can't breathe.""",

        # Response to clinical history question
        """I was diagnosed with generalized anxiety disorder about 2 years ago,
        but I've never really stuck with treatment. I tried therapy briefly
        and was prescribed SSRIs, but I stopped taking them after a few weeks.""",

        # Response to context question
        """These symptoms started getting worse about 6 months ago after I started
        a new job. It's affecting my work performance and I've started avoiding
        social events. I really want to learn coping strategies and understand
        why this is happening to me."""
    ]

    # Simulate conversation
    for i, user_input in enumerate(user_responses, 1):
        print(f"User: {user_input}\n")
        response = agent.chat(user_input)
        print(f"Agent: {response['response']}\n")

        if response['completed']:
            # All information collected, process the request
            print("\n" + "="*70)
            result = agent.process_collected_information()
            print(result)
            return result

    return None

if __name__ == "__main__":
    main()

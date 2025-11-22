from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import json
import os

from .forms import HealthForm
from .models import TriageSubmission
from .services.gptapi import get_triage_agent
from .services.mental_health_agent import MentalHealthAgent


# OpenAI API Key - In production, store in environment variables
OPENAI_API_KEY = "***REMOVED***"


class HealthView(View):
    """Main health triage form view"""
    
    def get(self, request):
        """Display the health intake form"""
        form = HealthForm()
        return render(request, 'core/health.html', {'form': form})
    
    def post(self, request):
        """Handle form submission with dual-agent processing"""
        form = HealthForm(request.POST, request.FILES)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            address = form.cleaned_data['address']
            symptoms = form.cleaned_data['symptoms']
            clinical_history = form.cleaned_data.get('clinical_history')
            additional_context = form.cleaned_data.get('additional_context', '')
            
            # Initialize AI agent
            try:
                agent = get_triage_agent(OPENAI_API_KEY)
                
                # FIRST AGENT: Quick triage analysis for safety and categorization
                print("Running First Agent: Quick Triage Analysis...")
                analysis = agent.analyze_symptoms(symptoms, additional_context)
                
                # Check for safety concerns
                if analysis.get('safety_concern', False):
                    # Create crisis text
                    crisis_text = f"""
CRISIS SUBMISSION - {email}
Submission Date: {analysis.get('timestamp', 'Now')}

SAFETY CONCERN DETECTED
Category: {analysis.get('category', 'Crisis')}
Urgency: CRISIS
Reasoning: {analysis.get('reasoning', 'Safety concern detected')}

Immediate intervention required. Patient requires crisis support.
Standard processing bypassed for immediate response.
"""
                    # Save the submission even in crisis
                    submission = TriageSubmission.objects.create(
                        email=email,
                        full_text_content=crisis_text,
                        processed=True
                    )
                    
                    return render(request, 'core/health.html', {
                        'form': form,
                        'safety_alert': True,
                        'crisis_hotline': '988',
                        'analysis': analysis,
                        'submission_id': submission.id
                    })
                
                # SECOND AGENT: Deep processing of full submission
                print("Running Second Agent: Deep Processing Analysis...")
                unified_text = agent.process_full_submission(
                    email=email,
                    address=address,
                    symptoms=symptoms,
                    additional_context=additional_context,
                    has_clinical_history=clinical_history is not None
                )
                
                # Create and save the complete submission
                submission = TriageSubmission.objects.create(
                    email=email,
                    full_text_content=unified_text,
                    processed=True
                )
                
                print(f"✓ Submission saved with ID: {submission.id}")
                
                # Store in session for Phase 2 (specialist matching)
                request.session['triage_data'] = {
                    'submission_id': submission.id,
                    'email': email,
                    'address': address,
                    'symptoms': symptoms,
                    'additional_context': additional_context,
                    'has_clinical_history': clinical_history is not None,
                    'analysis': analysis
                }
                
                # Success - show results with full text
                return render(request, 'core/health.html', {
                    'form': form,
                    'submitted': True,
                    'submission': submission,
                    'analysis': analysis,
                    'symptoms': symptoms,
                    'email': email
                })
                
            except Exception as e:
                print(f"Error processing form: {e}")
                import traceback
                traceback.print_exc()
                return render(request, 'core/health.html', {
                    'form': form,
                    'error': f'An error occurred processing your request: {str(e)}'
                })
        
        # Form invalid
        return render(request, 'core/health.html', {'form': form})


@method_decorator(csrf_exempt, name='dispatch')
class GeneratePlaceholderView(View):
    """
    AJAX endpoint to generate dynamic placeholder text
    Called when user types symptoms
    """
    
    def post(self, request):
        """Generate personalized placeholder for additional context field"""
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms', '').strip()
            has_clinical_history = data.get('has_clinical_history', False)
            
            if not symptoms or len(symptoms) < 10:
                return JsonResponse({
                    'success': False,
                    'placeholder': 'Tell us more about your situation...'
                })
            
            # Initialize AI agent
            agent = get_triage_agent(OPENAI_API_KEY)
            
            # Generate dynamic placeholder
            placeholder = agent.generate_dynamic_placeholder(symptoms, has_clinical_history)
            
            return JsonResponse({
                'success': True,
                'placeholder': placeholder
            })
            
        except Exception as e:
            print(f"Error generating placeholder: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'placeholder': 'Tell us more about your situation...'
            }, status=500)
        


class DoctorRecommendationsView(View):
    """
    View to display doctor recommendations
    Phase 2: Process doctor recommendation data using Mental Health Agent
    """
    def get(self, request):
        """
        Display the doctor recommendations page
        Processes doctor information using mental_health_agent
        """
        

        
        # Get submission data from session (if available)
        triage_data = request.session.get('triage_data', {})
        submission_id = triage_data.get('submission_id')
        
        # Retrieve the submission to show context
        submission = None
        if submission_id:
            try:
                submission = TriageSubmission.objects.get(id=submission_id)
            except TriageSubmission.DoesNotExist:
                pass
        
        # Get the data from triage
        email = triage_data.get('email', '')
        address = triage_data.get('address', '')
        symptoms = triage_data.get('symptoms', '')
        additional_context = triage_data.get('additional_context', '')
        
        try:
            # Initialize Mental Health Agent
            specialists_path = os.path.join(settings.BASE_DIR, 'static', 'Specialist_EN.xlsx')
            agent = MentalHealthAgent(
                api_key=OPENAI_API_KEY,
                specialists_csv=specialists_path
            )
            
            print("=" * 70)
            print("MENTAL HEALTH AGENT - DOCTOR MATCHING")
            print("=" * 70)
            
            # Manually populate the agent's collected info (bypass conversation)
            agent.collected_info = {
                "patient_name": email.split('@')[0],  # Use email prefix as name
                "patient_age": "Not provided",
                "patient_address": address,
                "patient_gender": "Not provided",
                "symptoms": symptoms,
                "clinical_history": "Not provided",
                "context": additional_context if additional_context else "No additional context provided"
            }
            agent.state = agent.state.PROCESSING
            
            # Process and get specialist match
            result = agent.process_collected_information()
            
            print("Match found!")
            print(f"Specialist: {result['specialist']['name']}")
            print("=" * 70)
            
            # Format into expected structure
            doctor_recommendation = {
                "status": "success",
                "matched": True,
                "doctor": {
                    "id": 1,
                    "name": result['specialist']['name'],
                    "specialist": result['specialist']['expertise'].split('-')[0].strip() if '-' in result['specialist']['expertise'] else "Clinical Psychologist",
                    "subspecialty": result['specialist']['expertise'],
                    "address": result['specialist']['location'].split(',')[0].strip() if ',' in result['specialist']['location'] else result['specialist']['location'],
                    "city": result['specialist']['location'].split(',')[-1].strip() if ',' in result['specialist']['location'] else "Turin",
                    "phone": result['specialist']['phone_number'],
                    "email": result['specialist']['email']
                },
                "match_reasoning": result['specialist']['match_note']
            }
            
        except Exception as e:
            print(f"Error using mental health agent: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to mock data if agent fails
            doctor_recommendation = {
                "status": "success",
                "matched": True,
                "doctor": {
                    "id": 1,
                    "name": "Dr. Luca Bianchi",
                    "specialist": "Clinical Psychologist",
                    "subspecialty": "Anxiety and Depression",
                    "address": "Via Roma 25",
                    "city": "Turin",
                    "phone": "+39 345 112233 4",
                    "email": "luca.bianchi@mail.com"
                },
                "match_reasoning": "Based on your symptoms, Dr. Bianchi is an excellent match. He specializes in treating anxiety and depression with evidence-based approaches."
            }
        
        # Format the full text representation (for processing/logging)
        full_text_recommendation = self._format_doctor_recommendation_text(doctor_recommendation)
        
        print("=" * 70)
        print("DOCTOR RECOMMENDATION (Full Text)")
        print("=" * 70)
        print(full_text_recommendation)
        print("=" * 70)
        
        # Render the template with doctor data
        return render(request, 'core/doctor_recommendations.html', {
            'doctor_recommendation': doctor_recommendation,
            'full_text': full_text_recommendation,
            'submission': submission,
            'user_email': email
        })
    
    def _format_doctor_recommendation_text(self, data: dict) -> str:
        """
        Format doctor recommendation data as full text
        This is what would be received from the external agent
        """
        doctor = data.get('doctor', {})
        
        text_parts = [
            "=" * 70,
            "DOCTOR RECOMMENDATION - PHASE 2",
            "=" * 70,
            f"\nStatus: {data.get('status', 'Unknown').upper()}",
            f"Match Found: {'Yes' if data.get('matched') else 'No'}",
            "\n" + "-" * 70,
            "RECOMMENDED SPECIALIST",
            "-" * 70,
            f"ID: {doctor.get('id', 'N/A')}",
            f"Name: {doctor.get('name', 'N/A')}",
            f"Specialist: {doctor.get('specialist', 'N/A')}",
            f"Subspecialty: {doctor.get('subspecialty', 'N/A')}",
            f"Address: {doctor.get('address', 'N/A')}",
            f"City: {doctor.get('city', 'N/A')}",
            f"Phone: {doctor.get('phone', 'N/A')}",
            f"Email: {doctor.get('email', 'N/A')}",
            "\n" + "-" * 70,
            "MATCH REASONING",
            "-" * 70,
            data.get('match_reasoning', 'N/A'),
            "\n" + "=" * 70,
            "END OF RECOMMENDATION",
            "=" * 70
        ]
        
        return "\n".join(text_parts)
    


class AvailabilityView(View):
    """
    View to display availability and booking
    Phase 3: Process availability data from external agent
    """
    def get(self, request):
        """
        Display the availability/booking page
        Processes booking data from external agent and displays it
        """
        
        # Get triage and doctor data from session
        triage_data = request.session.get('triage_data', {})
        
        # ========================================
        # MOCK DATA: Example of booking data from external agent
        # In production, this would come from the external agent API
        # ========================================
        booking_data = {
            "selected_date": "2025-11-25",
            "selected_time": "05:30 PM",
            "patient_notes": "",
            "status": "confirmed",
            "created_at": "2025-11-22T13:42:39.991778",
            "conversation_complete": True,
            "doctor": {
                "name": "Dr. Luca Bianchi",
                "specialist": "Clinical Psychologist",
                "subspecialty": "Anxiety and Depression",
                "address": "Via Roma 25",
                "city": "Turin",
                "phone": "+39 345 112233 4",
                "email": "luca.bianchi@mail.com"
            },
            "patient_email": triage_data.get('email', '')
        }
        
        # Format the full text representation (for processing/logging)
        full_text_booking = self._format_booking_text(booking_data)
        
        print("=" * 70)
        print("BOOKING DATA (Full Text)")
        print("=" * 70)
        print(full_text_booking)
        print("=" * 70)
        
        # Render the template with booking data
        return render(request, 'core/best_match_booking.html', {
            'booking': booking_data,
            'full_text': full_text_booking
        })
    
    def _format_booking_text(self, data: dict) -> str:
        """
        Format booking data as full text
        This is what would be received from the external agent
        """
        doctor = data.get('doctor', {})
        
        text_parts = [
            "=" * 70,
            "APPOINTMENT BOOKING - PHASE 3",
            "=" * 70,
            f"\nStatus: {data.get('status', 'Unknown').upper()}",
            f"Conversation Complete: {'Yes' if data.get('conversation_complete') else 'No'}",
            f"Created At: {data.get('created_at', 'N/A')}",
            "\n" + "-" * 70,
            "APPOINTMENT DETAILS",
            "-" * 70,
            f"Selected Date: {data.get('selected_date', 'N/A')}",
            f"Selected Time: {data.get('selected_time', 'N/A')}",
            f"Patient Notes: {data.get('patient_notes', 'None')}",
            "\n" + "-" * 70,
            "DOCTOR INFORMATION",
            "-" * 70,
            f"Name: {doctor.get('name', 'N/A')}",
            f"Specialist: {doctor.get('specialist', 'N/A')}",
            f"Subspecialty: {doctor.get('subspecialty', 'N/A')}",
            f"Address: {doctor.get('address', 'N/A')}",
            f"City: {doctor.get('city', 'N/A')}",
            f"Phone: {doctor.get('phone', 'N/A')}",
            f"Email: {doctor.get('email', 'N/A')}",
            "\n" + "-" * 70,
            "PATIENT CONTACT",
            "-" * 70,
            f"Email: {data.get('patient_email', 'N/A')}",
            "\n" + "=" * 70,
            "END OF BOOKING",
            "=" * 70
        ]
        
        return "\n".join(text_parts)
    
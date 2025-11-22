from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import json

from .forms import HealthForm
from .models import TriageSubmission
from .services.gptapi import get_triage_agent


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
    Phase 2: Process doctor recommendation data from external agent
    """
    def get(self, request):
        """
        Display the doctor recommendations page
        Processes doctor information from external agent and displays it
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
        
        # ========================================
        # MOCK DATA: Example of doctor recommendation from external agent
        # Based on doctors database table structure
        # In production, this would come from the external agent API
        # ========================================
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
            "match_reasoning": "Based on your symptoms of anxiety and sleep disturbance related to stress, Dr. Bianchi is an excellent match. He specializes in treating anxiety and depression with evidence-based approaches. His practice focuses on helping patients develop coping strategies and regain emotional balance."
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
            'user_email': triage_data.get('email', '')
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
    

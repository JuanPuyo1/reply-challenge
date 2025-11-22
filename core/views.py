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
from django import forms

class HealthForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        }),
        help_text="We'll use this to send you a link to your analysis."
    )
    
    address = forms.CharField(
        label="Address",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country, City, Address (e.g., "Italy, Turin, Via Roma 15")'
        }),
        help_text="Your location helps us match you with nearby specialists."
    )
    
    symptoms = forms.CharField(
        label="Symptoms",
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Describe what you are experiencing... (e.g., "I feel anxious in social situations" or "I can\'t sleep because of exam stress")',
            'class': 'form-control',
            'required': True
        }),
        help_text="Tell us what brings you here today. Be as specific as you can."
    )
    
    clinical_history = forms.FileField(
        label="Clinical History (Optional)",
        required=False,
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx,.txt',
            'class': 'form-control'
        }),
        help_text="Upload any previous medical records, diagnoses, or therapy notes (PDF, DOC, DOCX, or TXT)"
    )
    
    additional_context = forms.CharField(
        label="Additional Context",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Tell us more about your situation...',
            'class': 'form-control',
            'id': 'id_additional_context'
        }),
        help_text="Any other information that might help us match you with the right specialist"
    )


class AvailabilityPreferenceForm(forms.Form):
    """Form to collect user's time preference for scheduling"""
    
    TIME_PREFERENCE_CHOICES = [
        ('', 'Select your preferred time...'),
        ('morning', 'Morning (6:00 AM - 12:00 PM)'),
        ('afternoon', 'Afternoon (12:00 PM - 6:00 PM)'),
        ('evening', 'Evening (6:00 PM - 11:00 PM)'),
    ]
    
    time_preference = forms.ChoiceField(
        label="When would you prefer to have your appointment?",
        choices=TIME_PREFERENCE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your preferred time of day for the appointment"
    )
    
    is_urgent = forms.BooleanField(
        label="Is this urgent?",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text="Check this if you need an appointment as soon as possible"
    )
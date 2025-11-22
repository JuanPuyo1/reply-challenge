from django.db import models
from django.utils import timezone


class TriageSubmission(models.Model):
    """
    Stores complete triage submissions as unified text
    Contains both user submission data and AI-generated analysis
    """
    # User contact
    email = models.EmailField(help_text="User's email for follow-up")
    
    # Complete submission text (user data + AI analysis combined)
    full_text_content = models.TextField(
        help_text="Complete submission including user data and AI analysis"
    )
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(
        default=True,
        help_text="Whether the submission has been processed"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Triage Submission"
        verbose_name_plural = "Triage Submissions"
    
    def __str__(self):
        return f"{self.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_preview(self, length=200):
        """Returns a preview of the full text content"""
        if len(self.full_text_content) <= length:
            return self.full_text_content
        return self.full_text_content[:length] + "..."

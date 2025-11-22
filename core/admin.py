from django.contrib import admin
from django.utils.html import format_html
from .models import TriageSubmission


@admin.register(TriageSubmission)
class TriageSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Triage Submissions"""
    
    list_display = [
        'id',
        'email',
        'text_preview',
        'created_at',
        'processed_badge'
    ]
    
    list_filter = [
        'processed',
        'created_at'
    ]
    
    search_fields = [
        'email',
        'full_text_content'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'full_text_display'
    ]
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('email', 'created_at', 'updated_at')
        }),
        ('Complete Submission', {
            'fields': ('full_text_display',)
        }),
        ('Status', {
            'fields': ('processed',)
        })
    )
    
    def text_preview(self, obj):
        """Display preview of the submission"""
        preview = obj.get_preview(100)
        return format_html('<span style="font-size: 0.85rem; color: #666;">{}</span>', preview)
    text_preview.short_description = 'Preview'
    
    def processed_badge(self, obj):
        """Display processing status as badge"""
        if obj.processed:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem;">✓ Processed</span>'
            )
        return format_html(
            '<span style="background: #ff9800; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem;">⏳ Pending</span>'
        )
    processed_badge.short_description = 'Status'
    
    def full_text_display(self, obj):
        """Display full text in readable format"""
        return format_html(
            '<pre style="white-space: pre-wrap; line-height: 1.6; font-size: 0.9rem; background: #f9f9f9; padding: 1rem; border-radius: 4px; overflow-x: auto;">{}</pre>',
            obj.full_text_content
        )
    full_text_display.short_description = 'Complete Report (User Data + AI Analysis)'

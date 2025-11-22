from django.urls import path
from .views import HealthView, GeneratePlaceholderView

app_name = 'core'

urlpatterns = [
    path('', HealthView.as_view(), name='health'),
    path('api/generate-placeholder/', GeneratePlaceholderView.as_view(), name='generate_placeholder'),
]
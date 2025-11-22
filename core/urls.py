from django.urls import path
from .views import HealthView, GeneratePlaceholderView, DoctorRecommendationsView

app_name = 'core'

urlpatterns = [
    path('', HealthView.as_view(), name='health'),
    path('api/generate-placeholder/', GeneratePlaceholderView.as_view(), name='generate_placeholder'),
    path('doctor-recommendations/', DoctorRecommendationsView.as_view(), name='doctor_recommendations'),
]
from django.urls import path
from .views import (
    HealthView, 
    GeneratePlaceholderView, 
    DoctorRecommendationsView, 
    AvailabilityPreferenceView,
    AvailabilityView,
    BookAppointmentView
)

app_name = 'core'

urlpatterns = [
    path('', HealthView.as_view(), name='health'),
    path('api/generate-placeholder/', GeneratePlaceholderView.as_view(), name='generate_placeholder'),
    path('doctor-recommendations/', DoctorRecommendationsView.as_view(), name='doctor_recommendations'),
    path('availability-preference/', AvailabilityPreferenceView.as_view(), name='availability_preference'),
    path('availability/', AvailabilityView.as_view(), name='availability'),
    path('book-appointment/', BookAppointmentView.as_view(), name='book_appointment'),
]
from django.urls import path
from .views import HealthView

app_name = 'core'

urlpatterns = [
    path('', HealthView.as_view(), name='health'),
]
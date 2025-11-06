from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import requests
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        total_tasks = Task.objects.count()
        completed = Task.objects.filter(status='completed').count()
        pending = Task.objects.filter(status='pending').count()
        in_progress = Task.objects.filter(status='in_progress').count()
        
        priority_stats = Task.objects.values('priority').annotate(count=Count('id'))
        
        last_7_days = timezone.now() - timedelta(days=7)
        recent_tasks = Task.objects.filter(created_at__gte=last_7_days).values('created_at__date').annotate(count=Count('id'))
        
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return Response({
            'total_tasks': total_tasks,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'priority_stats': list(priority_stats),
            'recent_tasks': list(recent_tasks),
            'completion_rate': round(completion_rate, 2)
        })
    
    @action(detail=False, methods=['get'])
    def weather(self, request):
        latitude = request.query_params.get('latitude', '40.7128')
        longitude = request.query_params.get('longitude', '-74.0060')
        
        try:
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'timezone': 'auto',
                'forecast_days': 7
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return Response({
                'current': data.get('current', {}),
                'daily': data.get('daily', {}),
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch weather data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

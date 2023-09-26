from django.urls import path
from . import views


app_name = 'reciept'

urlpatterns = [
    path('printer/', views.PrinterListAPIView.as_view(), name='printer-list'),
    path('printer/<int:pk>/', views.PrinterDetailAPIView.as_view(), name='printer-detail'),
    path('check/', views.CheckListAPIView.as_view(), name='check-list'),
    path('check/<int:pk>/', views.CheckDetailAPIView.as_view(), name='check-detail'),
    path('check/create/', views.CheckCreateAPIView.as_view(), name='check-create'),
    path('check/<int:pk>/update/', views.CheckRetrieveUpdateAPIView.as_view(), name='check-update-retrieve'),
]

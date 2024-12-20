from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', views.index, name='index'),
    path('doctor_login/', views.login_view, name='doctor_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashbord'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor_and_nurse_info/', views.doctor_and_nurse_info, name='doctor_and_nurse_info'),
    path('upload/', views.upload_results, name='upload_results'),
    path('medical_record/', views.medical_record, name='medical_record'),
    path('nurse_dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('add_user/', views.add_user, name='add_user'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('contact_us_submit/', views.contact_us_submit, name='contact_us_submit'),  
    path('upload_model/', views.upload_model, name='upload_model'),
    path('model_history/', views.model_history, name='model_history'), 
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

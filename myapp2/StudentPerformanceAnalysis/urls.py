from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty_dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('subadmin_dashboard/', views.subadmin_dashboard, name='subadmin_dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    #path('logout/',views.login_view, name='login'),
    path('get-test-responses/<int:test_id>/', views.get_test_responses, name='get_test_responses'),
    path('get-test-question-count/<int:test_id>/', views.get_test_question_count, name='get_test_question_count'),
]
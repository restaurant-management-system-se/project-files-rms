from django.urls import path
from . import views
urlpatterns = [
    path('api/admin/menu', views.MenuManage.as_view()),
    path('api/admin/menu/<int:pk>', views.MenuManage.as_view()),
    path('manage/menu/', views.manage_page),
]

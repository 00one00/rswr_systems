from django.urls import path
from . import views

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("detail/", views.index_job, name="index_job"),
]
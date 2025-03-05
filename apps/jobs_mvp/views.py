from django.shortcuts import render
from django.http import HttpResponse
from .models import Jobs

# Create your views here.
def index_job(response):
    return HttpResponse("Hello, world!")

def job_list(request):
    jobs = Jobs.objects.all()
    job_info = []
    for job in jobs:
        job_info.append(f"{job.customer_name} - {job.get_status_display()}")
    return HttpResponse(f"Job info: {job_info}")
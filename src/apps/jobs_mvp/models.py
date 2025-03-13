from django.db import models
from django.utils import timezone
import datetime
# Create your models here.
class Jobs(models.Model):
    customer_name = models.CharField(max_length=20, null=True, unique=True)
    customer_email = models.EmailField(max_length=246, null=True, blank=True)
    job_description = models.TextField(blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    date_submitted = models.DateTimeField("date submitted", default=timezone.now)


    # create the __str__ method to return the customer name and date submitted in a human readable format 
    def __str__(self):
        return f"{self.customer_name} - {self.date_submitted}"
        

    def get_status_display(self):
        return f"Status: {self.status}"
    
    def posted_recently(self):
        now = timezone.now()
        return now >= self.date_submitted >= now - datetime.timedelta(days=1)
    
    
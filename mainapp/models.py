from django.db import models
from django.utils.timezone import now

class PatientVisit(models.Model):
    doctor_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='uploads/')
    result = models.CharField(max_length=255)
    dr_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Patient(models.Model):
    file_number = models.CharField(max_length=255, unique=True)
    VA_od = models.CharField(max_length=50, blank=True, null=True)
    VA_os = models.CharField(max_length=50, blank=True, null=True)
    lop_od = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Patient {self.file_number}"
    

class ModelUpload(models.Model):
    model_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    upload_date = models.DateTimeField(default=now)
    admin_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)  # URL to the model file

    def __str__(self):
        return f"{self.model_name} (v{self.version})"

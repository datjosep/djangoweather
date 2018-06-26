from django.db import models


class DataHandling(models.Model):
    site = models.CharField(max_length=4, required=True)
    start_time = models.DateTimeField(input_formats=['%Y,%m,%d,%H,%M'], required=True)
    end_time = models.DateTimeField(input_formats=['%Y,%m,%d,%H,%M'], required=True)
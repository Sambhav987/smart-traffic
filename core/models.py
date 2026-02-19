from django.db import models

class Congestion(models.Model):
    timestamp = models.CharField(max_length=25)  # Using CharField as per original script behavior
    num_cars = models.IntegerField()
    section = models.CharField(max_length=25, default="Unknown")

    def __str__(self):
        return f"Congestion at {self.timestamp}: {self.num_cars} cars in {self.section} section"

class Accident(models.Model):
    timestamp = models.CharField(max_length=25)
    num_instances = models.IntegerField()
    section = models.CharField(max_length=25, default="Unknown")

    def __str__(self):
        return f"Accident at {self.timestamp}: {self.num_instances} instances in {self.section} section"

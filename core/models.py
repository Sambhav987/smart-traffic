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

class HistoricData(models.Model):
    timestamp = models.CharField(max_length=25)
    num_cars_left = models.IntegerField(default=0)
    num_cars_right = models.IntegerField(default=0)
    num_cars_top = models.IntegerField(default=0)
    num_cars_bottom = models.IntegerField(default=0)
    total_cars = models.IntegerField(default=0)

    class Meta:
        db_table = "historic_data"

    def __str__(self):
        return f"HistoricData at {self.timestamp}: total {self.total_cars} cars"


class PushToken(models.Model):
    token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token
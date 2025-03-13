from django.db import models

class SimulationResult(models.Model):
    slice_type = models.CharField(max_length=10)  # eMBB, URLLC, mMTC
    timestamp = models.FloatField()
    bytes_transmitted = models.IntegerField()

    def __str__(self):
        return f"{self.slice_type} - {self.timestamp}s - {self.bytes_transmitted}B"

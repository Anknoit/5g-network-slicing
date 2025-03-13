from django.db import models

class SimulationResult(models.Model):

    slice_type = models.CharField(max_length=50)

    timestamp = models.FloatField(default=0)

    bytes_transmitted = models.IntegerField(default=0)

    latency = models.FloatField(default=0)

    jitter = models.FloatField(default=0)

    packet_loss = models.FloatField(default=0)

    throughput = models.FloatField(default=0)

    user_count = models.IntegerField(default=0)

    signal_strength = models.FloatField(default=0)


    def __str__(self):

        return f"{self.slice_type} at {self.timestamp}"
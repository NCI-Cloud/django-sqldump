# This is an auto-generated Django model module.

from django.db import models

class Hosts(models.Model):
    tstamp = models.IntegerField()
    host = models.CharField(primary_key=True, max_length=64)
    vcpus = models.IntegerField(blank=True, null=True)
    wall_time = models.IntegerField(blank=True, null=True)
    cpu_time = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hosts'
        unique_together = (('tstamp', 'host'),)


class Instances(models.Model):
    tstamp = models.IntegerField()
    uuid = models.CharField(primary_key=True, max_length=36)
    host = models.CharField(max_length=64, blank=True, null=True)
    vcpus = models.IntegerField(blank=True, null=True)
    wall_time = models.IntegerField(blank=True, null=True)
    cpu_time = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'instances'
        unique_together = (('tstamp', 'uuid'),)

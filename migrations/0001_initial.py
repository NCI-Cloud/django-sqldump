# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Hosts',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('tstamp', models.IntegerField()),
                ('host', models.CharField(max_length=64)),
                ('vcpus', models.IntegerField(blank=True, null=True)),
                ('wall_time', models.IntegerField(blank=True, null=True)),
                ('cpu_time', models.FloatField(blank=True, null=True)),
            ],
            options={
                'db_table': 'hosts',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Instances',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('tstamp', models.IntegerField()),
                ('uuid', models.CharField(max_length=36)),
                ('host', models.CharField(blank=True, max_length=64, null=True)),
                ('vcpus', models.IntegerField(blank=True, null=True)),
                ('wall_time', models.IntegerField(blank=True, null=True)),
                ('cpu_time', models.FloatField(blank=True, null=True)),
            ],
            options={
                'db_table': 'instances',
                'managed': False,
            },
        ),
    ]

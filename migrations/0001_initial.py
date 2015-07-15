# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('key', models.CharField(primary_key=True, max_length=32, serialize=False)),
                ('sql', models.TextField()),
                ('root', models.CharField(default='root', max_length=64)),
                ('row', models.CharField(default='row', max_length=64)),
            ],
        ),
    ]

from django.conf import settings

# all queries will go through this entry in DATABASES
DB_CON = getattr(settings, 'DUMP_DATABASE_CONNECTION', 'default')

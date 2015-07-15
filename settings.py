from django.conf import settings

# all queries will go through this entry in DATABASES
DB_CON = getattr(settings, 'DUMP_DATABASE_CONNECTION', 'default')

# when running test scripts, use this connection instead
# (this is more powerful than setting DATABASES['whatever']['TEST'] = {...},
# because the latter cannot override ENGINE or HOST)
TEST_DB_CON = getattr(settings, 'DUMP_TEST_DATABASE_CONNECTION', DB_CON)

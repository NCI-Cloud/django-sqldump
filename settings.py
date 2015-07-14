from django.conf import settings

# all queries will go through this entry in DATABASES
DB_CON = getattr(settings, 'DUMP_DATABASE_CONNECTION', 'default')

# maps query_key : {sql:blah, [root:blah,] [row:blah,]}
# each query_key must match \w+ (according to urls.py)
QUERIES = getattr(settings, 'DUMP_QUERIES', {})

from django.db import models, connections
from .settings import *

class Query(models.Model):
    """
        key    - to go in the url when requesting this query
        sql    - query to be executed
        root   - name of root element, for xml output
        row    - name of each record, for xml output
    """
    key  = models.CharField(primary_key=True, max_length=32)
    sql  = models.TextField()
    root = models.CharField(default='root', max_length=64)
    row  = models.CharField(default='row',  max_length=64)

    def get(self):
        """Return [{col1:val1, col2:val2, ...} ...]."""
        cursor = connections[DB_CON].cursor()
        cursor.execute(self.sql)
        self.cols = [col[0] for col in cursor.description]
        return [{col:val for (col, val) in zip(self.cols, row)} for row in cursor.fetchall()]

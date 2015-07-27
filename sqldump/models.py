from django.db import models, connections
from .settings import DB_CON

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

    db_con = DB_CON

    @staticmethod
    def set_db_con(db_con):
        """
        Specify which database connection (key in settings.DATABASES) to use to execute sql.
        Decided not to give each Query its own db_con, since that seems needlessly complicated.
        """
        Query.db_con = db_con

    def get(self):
        """Return [{col1:val1, col2:val2, ...} ...]."""
        with connections[Query.db_con].cursor() as cursor:
            cursor.execute(self.sql)
            self.cols = [col[0] for col in cursor.description]
            return [{col:val for (col, val) in zip(self.cols, row)} for row in cursor.fetchall()]

    def restrict(self, condition):
        """Apply `condition` to this query.

        This is a very fragile implementation, but hopefully that's excusable because this
        code will be replaced by our restful reporting api.
        """
        self.sql += ' WHERE '+condition

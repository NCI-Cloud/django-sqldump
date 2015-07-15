from django.test import TestCase
from django.db import connections
from django.db import models
from dump.models import Query
from .settings import TEST_DB_CON
from .views import get_xml, get_json
from lxml import etree
import json

class ValidationTests(TestCase):
    """
    Creates Citizen model and some Query objects to query the dump_citizen table,
    then does various tests...
    """
    @classmethod
    def setUpClass(cls):
        """
        Create model and database table.
        This is a hack to prevent django from doing automatic magic when it sees a Model,
        which would fail because the table for this model does not yet exist.
        (If the model is defined at a higher level in the code then this happens.)
        """
        super().setUpClass()
        class Citizen(models.Model):
            first_name = models.CharField(max_length=64)
            last_name  = models.CharField(max_length=64)
            dob        = models.DateField()
            iq         = models.IntegerField()
        ValidationTests.Citizen = Citizen

        # create table
        with connections[TEST_DB_CON].schema_editor() as schema_editor:
            schema_editor.create_model(ValidationTests.Citizen)

        # make sure testing queries will go to testing db
        Query.set_db_con(TEST_DB_CON)

        # this query gets used enough to make it worth saving here...
        ValidationTests.citizen_query = Query(
            key  = 'citizens',
            sql  = 'SELECT * FROM dump_citizen',
            root = 'citizens',
            row  = 'citizen'
        )

    @classmethod
    def tearDownClass(cls):
        """Remove model tables (even though this would happen automatically anyway)."""
        with connections[TEST_DB_CON].schema_editor() as schema_editor:
            schema_editor.delete_model(ValidationTests.Citizen)
        super().tearDownClass()

    def test_empty_json(self):
        citizens = json.loads(get_json(self.citizen_query))
        self.assertEqual(citizens, [], msg='got nonempty json result from empty table')

    def test_empty_xml(self):
        xml = get_xml(self.citizen_query)
        root = etree.fromstring(xml)
        self.assertEqual(len(root), 0, msg='got nonempty xml result from empty table')

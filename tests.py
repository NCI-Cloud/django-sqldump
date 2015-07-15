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
        cls.Citizen = Citizen

        # create table
        with connections[TEST_DB_CON].schema_editor() as schema_editor:
            schema_editor.create_model(cls.Citizen)

        # make sure testing queries will go to testing db
        Query.set_db_con(TEST_DB_CON)

        # this query gets used enough to make it worth saving here...
        cls.citizen_query = Query(
            key  = 'citizens',
            sql  = 'SELECT * FROM dump_citizen',
            root = 'citizens',
            row  = 'citizen'
        )

    @classmethod
    def tearDownClass(cls):
        """Remove model tables (even though this would happen automatically anyway)."""
        with connections[TEST_DB_CON].schema_editor() as schema_editor:
            schema_editor.delete_model(cls.Citizen)
        super().tearDownClass()

    @classmethod
    def get_citizen(cls):
        return cls.Citizen(
            first_name = 'First',
            last_name  = 'Last',
            dob        = '1955-11-05',
            iq         = 100,
        )

    @classmethod
    def get_bobby(cls):
        return cls.Citizen(
            first_name = "Robert'); DROP TABLE Studeñts;--",
            last_name  = '<3',
            dob        = '1984-10-17',
            iq         = 0,
        )

    @classmethod
    def insert_citizen(cls, citizen=None):
        citizen = citizen or cls.get_citizen()
        citizen.save(using=TEST_DB_CON)

    def tearDown(self):
        """Kill every citizen, so each test method starts with no citizens."""
        self.Citizen.objects.all().delete()

    def test_json_empty(self):
        citizens = json.loads(get_json(self.citizen_query))
        self.assertEqual(citizens, [], msg='got nonempty json result from empty table')

    def test_xml_empty(self):
        root = etree.fromstring(get_xml(self.citizen_query))
        self.assertEqual(len(root), 0, msg='got nonempty xml result from empty table')

    def test_xml_nonempty(self):
        fields = [field.name for field in self.Citizen._meta.get_fields()]

        # test with one bland citizen and one spicy citizen
        original_citizens = [self.get_citizen(), self.get_bobby()]
        for c in original_citizens:
            self.insert_citizen(c)
        retrieved_citizens = etree.fromstring(get_xml(self.citizen_query))

        # N.B. this relies on the rows being retrieved in the order they were created
        for (original, retrieved) in zip(original_citizens, retrieved_citizens):
            # create Citizen object from retrieved data
            attributes = {k:retrieved.attrib[k] for k in retrieved.attrib}
            citizen = self.Citizen(**attributes)

            # make sure all the fields have the same type before comparison
            citizen.clean_fields()
            original.clean_fields()

            # __eq__ is defined just to compare primary keys, which is insufficient here
            for field in fields:
                self.assertEqual(
                    getattr(citizen,  field),
                    getattr(original, field),
                    'retrieved "{r}" instead of "{o}" for field "{f}"'.format(
                        r = getattr(citizen,  field),
                        o = getattr(original, field),
                        f = field,
                    ),
                )

    def test_xml_rootrow(self):
        self.insert_citizen()
        root = etree.fromstring(get_xml(self.citizen_query))
        self.assertEqual(root.tag, self.citizen_query.root, msg='got different root tag name')
        self.assertEqual(root[0].tag, self.citizen_query.row, msg='got different row tag name')

    def test_xml_valid(self):
        for _ in range(5):
            self.insert_citizen()
        self.insert_citizen(self.get_bobby())

        parser = etree.XMLParser(dtd_validation=True)
        root = etree.fromstring(get_xml(self.citizen_query), parser) # raises exception on failure

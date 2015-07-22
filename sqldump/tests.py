from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.db import connections
from django.db import models
from .models import Query
from .settings import TEST_DB_CON
from .views import get_query_xml, get_query_json
from .models import Query
from lxml import etree
import json

class ViewsTests(TestCase):
    def setUp(self):
        self.qkey = 'reflect'
        Query(
            key=self.qkey,
            sql='SELECT * FROM {0}'.format(Query._meta.db_table),
            root='queries',
            row='query',
        ).save()

    def test_404(self):
        response = Client().get(reverse('sqldump:query', args=(None,)))
        self.assertEqual(response.status_code, 404, 'should hit 404 for invalid query key')

    def test_accepts(self):
        ct = 'application/xml'
        cu = 'application/json'

        # test sending single content type in http header
        c = Client(HTTP_ACCEPT='{content_type}'.format(content_type=ct))
        response = c.get(reverse('sqldump:query', args=(self.qkey,)))
        self.assertTrue(response.has_header('content-type'), msg='http response needs content-type')
        self.assertEqual(response['content-type'], ct, msg='should receive content-type "{0}" when requesting it'.format(ct))

        # test sending multiple content types
        c = Client(HTTP_ACCEPT='{other_type}; q=0.2, {content_type}'.format(content_type=ct, other_type=cu))
        response = c.get(reverse('sqldump:query', args=(self.qkey,)))
        self.assertEqual(response['content-type'], ct, msg='should receive content-type "{0}" when requesting it with higher precedence'.format(ct))

        # test overriding with query parameter
        c = Client(HTTP_ACCEPT=cu)
        response = c.get(reverse('sqldump:query', args=(self.qkey,)), {'accept':ct})
        self.assertEqual(response['content-type'], ct, msg='should receive content-type "{0}" when passing in url'.format(ct))

class ValidationTests(TestCase):
    """
    Creates Citizen model and some Query objects to query the sqldump_citizen table,
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
            sql  = 'SELECT * FROM sqldump_citizen',
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

    def compare_citizens(self, received, expected):
        """
        Check if all the fields of the given Citizen objects match.
        __eq__ is defined just to compare primary keys, which is insufficient here.

        """
        fields = [field.name for field in self.Citizen._meta.get_fields()]

        # make sure all the fields have the same type before comparison
        received.clean_fields()
        expected.clean_fields()

        for field in fields:
            self.assertEqual(
                getattr(received, field),
                getattr(expected, field),
                'received "{r}" instead of "{o}" for field "{f}"'.format(
                    r = getattr(received, field),
                    o = getattr(expected, field),
                    f = field,
                ),
            )

    def tearDown(self):
        """Kill every citizen, so each test method starts with no citizens."""
        self.Citizen.objects.all().delete()

    def test_json_empty(self):
        citizens = json.loads(get_query_json(self.citizen_query))
        self.assertEqual(citizens, [], msg='got nonempty json result from empty table')

    def test_xml_empty(self):
        root = etree.fromstring(get_query_xml(self.citizen_query))
        self.assertEqual(len(root), 0, msg='got nonempty xml result from empty table')

    def test_json_nonempty(self):
        # test with one bland citizen and one spicy citizen
        original_citizens = [self.get_citizen(), self.get_bobby()]
        for c in original_citizens:
            self.insert_citizen(c)
        rows = json.loads(get_query_json(self.citizen_query))
        retrieved_citizens = [self.Citizen(**att) for att in rows]

        # N.B. this relies on the rows being retrieved in the order they were created
        for (retrieved, original) in zip(retrieved_citizens, original_citizens):
            self.compare_citizens(retrieved, original)

    def test_xml_nonempty(self):
        # see comments in test_json_nonempty
        original_citizens = [self.get_citizen(), self.get_bobby()]
        for c in original_citizens:
            self.insert_citizen(c)
        root = etree.fromstring(get_query_xml(self.citizen_query))
        retrieved_citizens = [self.Citizen(**row.attrib) for row in root]
        for (retrieved, original) in zip(retrieved_citizens, original_citizens):
            self.compare_citizens(retrieved, original)

    def test_xml_rootrow(self):
        self.insert_citizen()
        root = etree.fromstring(get_query_xml(self.citizen_query))
        self.assertEqual(root.tag, self.citizen_query.root, msg='got different root tag name')
        self.assertEqual(root[0].tag, self.citizen_query.row, msg='got different row tag name')

    def test_xml_valid(self):
        for _ in range(5):
            self.insert_citizen()
        self.insert_citizen(self.get_bobby())

        parser = etree.XMLParser(dtd_validation=True)
        root = etree.fromstring(get_query_xml(self.citizen_query), parser) # raises exception on failure

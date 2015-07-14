from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import connections
from .models import *
import json
from lxml import etree
from django.conf import settings

class Query(object):
    def __init__(self, sql, root='list', row='object'):
        """
            sql    - query to be executed
            root   - name of root element, for xml output
            row    - name of each record, for xml output
        """
        self.sql, self.root, self.row = sql, root, row

    def get(self):
        """Return [{col1:val1, col2:val2, ...} ...]."""
        cursor = connections['stats'].cursor() # TODO fix this hard-coded string everywhere
        cursor.execute(self.sql)
        self.cols = [col[0] for col in cursor.description]
        return [{col:val for (col, val) in zip(self.cols, row)} for row in cursor.fetchall()]

    def get_as(self, f):
        """Return results as string, formatted as f. Raise ValueError for unknown f."""
        rows = self.get()
        if f == 'xml':
            root = etree.Element(self.root)
            for row in rows:
                root.append(etree.Element(self.row, **{k:str(row[k]) for k in row}))

            #root.append(etree.Element('rabs', **{'español':'hi'}))
            out = etree.tostring(root, pretty_print=True, encoding='utf-8')
            p = etree.XMLParser(dtd_validation=False)
            tst = etree.fromstring(out, p)

            # can get actual field types by inspecting cursor.description,
            # but these (I think) depend on the database back-end
            # so I decided it was too hard to be smart here,
            # and instead just say that everything is "CDATA #REQURED"...
            attlist = '\n'.join('  {col} CDATA #REQUIRED'.format(col=col) for col in self.cols)

            # generating dtd means we can automatically validate output, for testing
            dtd = '<!DOCTYPE {root} [\n' \
                  ' <!ELEMENT {root} ({row})*>\n' \
                  ' <!ELEMENT {row} EMPTY>\n' \
                  ' <!ATTLIST {row}\n{attlist}\n' \
                  ' >\n' \
                  ']>'.format(root=self.root, row=self.row, attlist=attlist)

            # DEFAULT_CHARSET is used by HttpResponse, so make etree use it too.
            # Output may become invalid if DEFAULT_CHARSET cannot be used to encode field names!
            # e.g. MySQL columns may include characters from Unicode Basic Multiingual Plane,
            # which could be inexpressible if DEFAULT_CHARSET were ascii, giving invalid xml.
            return etree.tostring(
                root,
                pretty_print    = False,
                encoding        = settings.DEFAULT_CHARSET,
                xml_declaration = True,
                doctype         = dtd,
            )
        elif f == 'json':
            return json.dumps(rows, indent=2)
        else:
            raise ValueError('unknown format "{0}"'.format(f))

# TODO this should be in a config file somewhere
# keys must match \w+ (because of specification in urls.py)
QUERIES = {
    'hallo' : Query(
        sql  = "SELECT * FROM hosts LIMIT 10",
        root = 'hosts',
        row  = 'host',
    ),
}

def query(request, query_key):
    if query_key not in QUERIES:
        raise Http404('unknown query key')

    f = request.GET.get('format', default='xml') # TODO maybe should come from http header

    ct = {'json' : 'application/json', 'xml' : 'application/xml'} # TODO clean up
    return HttpResponse(QUERIES[query_key].get_as(f), content_type=ct[f])

def index(request):
    return HttpResponse('have some options') # TODO implement

def hosts(request):
    data = Hosts.objects.all()[:10] # TODO get rid of this eventually...

    t = request.GET.get('type') # TODO maybe should come from http header
    if t == 'json':
        out = json.dumps([{field.attname : getattr(h, field.attname) for field in h._meta.get_fields()} for h in data], indent=None)
        return HttpResponse(out, content_type='application/json')

    # return xml by default
    context = {'hosts' : data}
    return render(request, 'dump/hosts.xml', context, content_type='application/xml')

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import connections
import json
from lxml import etree
from django.conf import settings
from .settings import *

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
        cursor = connections[DB_CON].cursor()
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

def query(request, query_key):
    if query_key not in QUERIES:
        raise Http404('unknown query key')

    f = request.GET.get('format', default='xml') # TODO maybe should come from http header

    ct = {'json' : 'application/json', 'xml' : 'application/xml'} # TODO clean up
    return HttpResponse(Query(**QUERIES[query_key]).get_as(f), content_type=ct[f])

def index(request):
    return HttpResponse('have some options') # TODO implement

import json
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from lxml import etree
from .models import Query

def get_etree(query):
    rows = query.get()
    root = etree.Element(query.root)
    for row in rows:
        root.append(etree.Element(query.row, **{k:str(row[k]) for k in row}))
    return root

def get_xml(query):
    """Return xml-formatted string representing query result."""
    root = get_etree(query)

    # can get actual field types by inspecting cursor.description,
    # but these (I think) depend on the database back-end
    # so I decided it was too hard to be smart here,
    # and instead just say that everything is "CDATA #REQURED"...
    attlist = '\n'.join('  {col} CDATA #REQUIRED'.format(col=col) for col in query.cols)

    # generating dtd means we can automatically validate output, for testing
    dtd = '<!DOCTYPE {root} [\n' \
          ' <!ELEMENT {root} ({row})*>\n' \
          ' <!ELEMENT {row} EMPTY>\n' \
          ' <!ATTLIST {row}\n{attlist}\n' \
          ' >\n' \
          ']>'.format(root=query.root, row=query.row, attlist=attlist)

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

def get_json(query):
    """Return json-formatted string representing query result."""
    rows = [dict(row.attrib) for row in get_etree(query)]
    return json.dumps(rows, indent=2)

def query(request, query_key):
    q = get_object_or_404(Query, pk=query_key)
    f = request.GET.get('format', default='xml') # TODO maybe should come from http header

    if f == 'xml':
        return HttpResponse(get_xml(q), content_type='application/xml')
    elif f == 'json':
        return HttpResponse(get_json(q), content_type='application/json')
    else:
        raise ValueError('unknown format "{0}"'.format(f))

def index(request):
    return HttpResponse('have some options') # TODO implement

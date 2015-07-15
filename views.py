import json
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from lxml import etree
from .models import Query

def query(request, query_key):
    q = get_object_or_404(Query, pk=query_key)
    f = request.GET.get('format', default='xml') # TODO maybe should come from http header
    rows = q.get()

    if f == 'xml':
        root = etree.Element(q.root)
        for row in rows:
            root.append(etree.Element(q.row, **{k:str(row[k]) for k in row}))

        #root.append(etree.Element('rabs', **{'español':'hi'}))
        out = etree.tostring(root, pretty_print=True, encoding='utf-8')
        p = etree.XMLParser(dtd_validation=False)
        tst = etree.fromstring(out, p)

        # can get actual field types by inspecting cursor.description,
        # but these (I think) depend on the database back-end
        # so I decided it was too hard to be smart here,
        # and instead just say that everything is "CDATA #REQURED"...
        attlist = '\n'.join('  {col} CDATA #REQUIRED'.format(col=col) for col in q.cols)

        # generating dtd means we can automatically validate output, for testing
        dtd = '<!DOCTYPE {root} [\n' \
              ' <!ELEMENT {root} ({row})*>\n' \
              ' <!ELEMENT {row} EMPTY>\n' \
              ' <!ATTLIST {row}\n{attlist}\n' \
              ' >\n' \
              ']>'.format(root=q.root, row=q.row, attlist=attlist)

        # DEFAULT_CHARSET is used by HttpResponse, so make etree use it too.
        # Output may become invalid if DEFAULT_CHARSET cannot be used to encode field names!
        # e.g. MySQL columns may include characters from Unicode Basic Multiingual Plane,
        # which could be inexpressible if DEFAULT_CHARSET were ascii, giving invalid xml.
        return HttpResponse(
            etree.tostring(
                root,
                pretty_print    = False,
                encoding        = settings.DEFAULT_CHARSET,
                xml_declaration = True,
                doctype         = dtd,
            ),
            content_type = 'application/xml',
        )
    elif f == 'json':
        return HttpResponse(
            json.dumps(rows, indent=2),
            content_type = 'application/json',
        )
    else:
        raise ValueError('unknown format "{0}"'.format(f))

def index(request):
    return HttpResponse('have some options') # TODO implement

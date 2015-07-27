import json
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import loader
from lxml import etree
from .models import Query
from pygments import highlight
from pygments.lexers.sql import SqlLexer
from pygments.formatters import HtmlFormatter

class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406

def get_query_etree(query):
    rows = query.get()
    root = etree.Element(query.root)
    for row in rows:
        root.append(etree.Element(query.row, **{k:str(row[k]) for k in row}))
    return root

def get_query_xml(query):
    """Return xml-formatted string representing query result."""
    root = get_query_etree(query)

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

def get_query_json(query):
    """Return json-formatted string representing query result."""
    rows = [dict(row.attrib) for row in get_query_etree(query)]
    return json.dumps(rows, indent=2)

def get_queries_html():
    def dumper_name(media):
        fst = media[0] # this always exists because we never make a Dumper to accept nothing
        typ, sub = fst.split('/')
        if typ == '*':
            return fst # */*
        if sub == '*':
            return typ
        return sub

    lexer = SqlLexer()
    formatter = HtmlFormatter(style='monokai')
    formatter.style.background_color = ''
    queries = Query.objects.all()
    for q in queries:
        q.highlight = highlight(q.sql, lexer, formatter)

    tpl = loader.get_template('sqldump/index.html')
    return tpl.render({
        'queries' : queries,
        'dumpers' : [(dumper_name(a), a[0]) for a in DUMPER.dumpers if DUMPER.dumpers[a][0]],
        'highlight' : formatter.get_style_defs('.highlight'),
    })

class Dumper():
    """Output query results or queries list, in various formats."""
    def __init__(self, dumpers):
        """dumpers is {accepted-types-list : (query_fn, queries_fn)}"""
        self.dumpers = dumpers

    def route(self, media):
        """Return (query_fn, queries_fn) best-suited to given list of media ranges."""
        for mr in media:
            for accepted in self.dumpers:
                if mr in accepted:
                    self.content_type = mr # TODO handle "*" in media range
                    return self.dumpers[accepted]
        return (None, None)

    def query(self, media, query):
        query_fn, _ = self.route(media)
        if query_fn is None: return HttpResponseNotAcceptable()
        return HttpResponse(query_fn(query), self.content_type)

    def queries(self, media):
        _, queries_fn = self.route(media)
        if queries_fn is None: return HttpResponseNotAcceptable()
        return HttpResponse(queries_fn(), self.content_type)

DUMPER = Dumper({
    ('application/xml', 'text/xml') : (get_query_xml, None),
    ('application/json', )          : (get_query_json, None),
    ('text/html', )                 : (None, get_queries_html),
})

def get_media_ranges(request):
    """
    Return a list of media "type/subtype" string, each with no parameters.
    The list is sorted such that the most preferred media ranges come first.

    If 'accept' is specified in request.GET, it gets highest priority, and we assume that
    it is a single media type and subtype, with no parameters, e.g. "?accept=application/json".

    Then anything from HTTP_ACCEPT header is listed.

    See: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
    """
    # list of all media-ranges
    nospace = ''.join(request.META.get('HTTP_ACCEPT', '').split())
    mrs = nospace.split(',')

    def param_free(mr):
        return mr if mr.find(';')==-1 else mr[:mr.find(';')]

    # sort according to quality parameter
    def get_q(mr): # get q parameter from a media-range
        params = mr.split(';')[1:] # skip first element of list, which is the media-range
        for p in params:
            if p.find('q=') == 0:
                return float(p[2:])
        return 1.
    mrs.sort(key=get_q, reverse=True) # highest q first

    # sort according to specificity
    def get_specificity(mr): # 0 for type/subtype, 1 for type/*, 2 for */*
        mr = param_free(mr) # technically the parameters should increase specificity
        if mr == '*/*': return 2
        elif mr.find('/*') != -1: return 1
        return 0
    mrs.sort(key=get_specificity) # most specific first

    # include GET media as highest priority
    if 'accept' in request.GET:
        mrs.insert(0, request.GET['accept']) # invalid input will just be ignored

    # now return parameterless media-ranges (potentially includes duplicates)
    return [param_free(mr) for mr in mrs]

def query(request, key, uuid=None):
    q = get_object_or_404(Query, pk=key)
    if uuid:
        q.restrict("uuid='{}'".format(uuid)) # url regex ensures this is safe
    return DUMPER.query(get_media_ranges(request), q)

def index(request):
    return DUMPER.queries(get_media_ranges(request))

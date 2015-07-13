from django.shortcuts import render
from django.http import HttpResponse
from .models import *
import json

def index(request):
    return HttpResponse('have some options')

def hosts(request):
    data = Hosts.objects.all()[:10] # TODO get rid of this eventually...

    t = request.GET.get('type') # TODO maybe should come from http header
    if t == 'json':
        out = json.dumps([{field.attname : getattr(h, field.attname) for field in h._meta.get_fields()} for h in data], indent=None)
        return HttpResponse(out, content_type='application/json')

    # return xml by default
    context = {'hosts' : data}
    return render(request, 'dump/hosts.xml', context, content_type='application/xml')

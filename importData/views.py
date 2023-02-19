""" view for ImportData"""
import json
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.http import HttpResponseNotFound


# Create your views here.

class LoadDatabasePage(TemplateView):
    """ file upload page"""
    template_name = 'importData/load_database.html'


def get_record(request):
    """ response function """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(data)
            return JsonResponse({'status': 200, })
        except ValueError:
            return JsonResponse({'status': 500, })
    return HttpResponseNotFound()

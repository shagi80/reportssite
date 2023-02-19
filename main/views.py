from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import *
from django.contrib import messages
from .my_validators import superuser_validation, staff_validation, StaffUserMixin, user_validation
from .business_logic import datafile_uploaded, datafile_get_format, BASE_PRICE_TYPE
from django.views.generic import View, ListView, TemplateView
from .models import ChangeLogs, TYPE_MODEL
from reports.models import Reports
from servicecentres.models import ServiceCenters
from reports.forms import ReportTitleForm

#начальная страница сайта - авторизация пользователя

class HelpPage(TemplateView):
    template_name = 'main/help_page.html'
    

def site_stop(request):
    return render(request, 'main/site_stop.html')


def start_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect('staff_home')
            else:
                try:
                    ServiceCenters.objects.get(user=request.user, is_active=True)
                    return redirect('user_home')
                except Exception:
                    messages.error(request, 'Ошибка привязки логина. Продолжение работы не возможно !')
                    return redirect('login_page')
        else:
            messages.error(request, 'Неверное имя пользовтаеля или пароль')
    else:
        form = UserLoginForm()
    return render(request, 'main/index.html', {'form': form})


#домашняя страница рядового пользователя
@user_passes_test(user_validation)
def user_home(request):
    cont = dict()
    reports = Reports.objects.filter(service_center__user=request.user)
    form = ReportTitleForm()
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    cont['page_obj'] = page_obj
    cont['reports'] = reports
    cont['rep_form'] = form
    return render(request, 'main/user_home.html', cont)


#домашяя страница персоланала
@user_passes_test(staff_validation)
def staff_home(request):
    from .business_logic import STATUS_SEND
    cont = dict()
    logs = ChangeLogs.objects.all()[:3]
    reports = Reports.objects.filter(status=STATUS_SEND)
    if not request.user.groups.filter(name='GeneralStaff').exists() and not request.user.is_superuser:
        reports = reports.filter(service_center__staff_user=request.user)
    cont['staff_actions'] = logs
    cont['reports'] = reports
    return render(request, 'main/staff_home.html', cont)


#выход пользователя
def userlogout(request):
    logout(request)
    return redirect('login_page')


#страница загрузки моделей из файла
@user_passes_test(superuser_validation)
def admin_load_data(request, mod_name):
    cont = {'mod_name': mod_name, 'format_help': datafile_get_format(mod_name)}
    if request.method == 'POST':
        form = DataFileLoadForm(request.POST, request.FILES)
        cont['form'] = form
        if form.is_valid():
            result = datafile_uploaded(request.FILES['file'],mod_name)
            if len(result) != 0:
                msg = 'Ошибки в строках файла: ' +', '.join(result)
                messages.error(request, msg)
            redirect_url = '/admin/' + mod_name.replace('.', '/') + '/'
            return redirect(redirect_url)
    else:
        form = DataFileLoadForm()
        cont['form'] = form
    return render(request, 'main/admin_load_data.html', cont)


#базовый класс для представлений изспользующих формы - позволяет выводить сообщения валидации
class MyFormMessagesView(View):
    success_message = 'my meesage'

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        ctx = self.get_context_data(**kwargs)
        text=''
        for error in form.errors:
            text = text + form.errors[error]
        messages.error(self.request, text)
        ctx['form'] = form
        return self.render_to_response(ctx)


class LogsList(LoginRequiredMixin, StaffUserMixin, ListView):
    model = ChangeLogs
    template_name = 'main/logs_list.html'
    context_object_name = 'logs'
    extra_context = {'title': 'Изменения данных'}
    paginate_by = 20

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LogsFilterForm(self.request.GET)
        context['obj_count'] = self.object_list.count()
        return (context)

    def get_queryset(self):
        logs = ChangeLogs.objects.all()
        if self.request.GET.get("model", '') != '' and self.request.GET.get("model", '') != 'empty':
            logs = logs.filter(model=self.request.GET.get("model"))
        if self.request.GET.get("action_on_model", '') != '' and self.request.GET.get("action_on_model", '') != 'empty':
            logs = logs.filter(action_on_model=self.request.GET.get("action_on_model"))
        if self.request.GET.get("staff_user", '') != '':
            logs = logs.filter(user=self.request.GET.get("staff_user"))
        return logs


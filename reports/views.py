from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from main.my_validators import *
from .forms import *
from .models import *
from servicecentres.models import ServiceCenters
import io
from django.http import FileResponse
from django.http import HttpResponse
import xlwt
from django.core.mail import send_mail


def SendReportSatus(email, report, note):
    msg = f'Статус вашего отчета за {report.get_report_month()} изменен на "{report.get_status_display()}"\n\n'
    if note:
        msg = msg + 'Сообщение от менедежера:\n'
        msg = msg + note + '\n\n'
    msg = msg + 'Это письмо сформированно автоматическа, отвечать на него не нужно.'
    send_mail(
        'RENOVA. Статус вашего отчета изменен',
        msg,
        'report_service@re-nova.com',
        ['shagi80@mail.ru'],
        fail_silently=False,
    )


def SendReportToStaff(report):
    email = report.service_center.staff_user.email
    if email:
        msg = f'Получен отчет от {report.service_center} за {report.get_report_month()}.\n\n'
        msg = msg + 'Это письмо сформированно автоматическа, отвечать на него не нужно.'
        send_mail(
            'RENOVA. Получен новый отчет.',
            msg,
            'report_service@re-nova.com',
            ['shagi80@mail.ru'],
            fail_silently=False,
        )


@user_passes_test(user_validation)
def export_report_xls(request, report_pk):
    report = get_object_or_404(Reports, pk = report_pk)
    report_date = report.get_report_month()

    response = HttpResponse(content_type='application/ms-excel')
    disp = f'attachment; filename="Report of ' + report.report_date.strftime("%b %Y") + ' .xls"'
    response['Content-Disposition'] = disp
    workBook = xlwt.Workbook(encoding='utf-8')
    workSheet = workBook.add_sheet(report_date)

    # Sheet header, first row
    boldStyle = xlwt.XFStyle()
    boldStyle.font.bold = True
    row_num = 0
    workSheet.write(row_num, 0, f'Статистическая таблица за {report_date}. {report.service_center}', boldStyle)

    # Table header, third row
    row_num = 2
    workSheet.row(row_num).height = 600
    headerStyle = xlwt.easyxf('font: bold off, color black; borders: left thin, right thin, top thin, bottom thin;\
     pattern: pattern solid, fore_color white, fore_colour gray25; align: horiz center, vert top;')
    headerStyle.alignment.wrap = 1
    columns = ['№', 'Клиент', 'Адрес', 'Телефон', 'Модель', 'Серийный номер', 'Дата продажи', 'Дата приема',
               'Дата ремонта', 'Описание датали', 'Цена детали', 'Кол-во штук', 'Номер накладной', 'Выезд',
               'За работы', 'Заявленный дефект', 'Описание работ', 'Код неисправности']
    for col_num in range(len(columns)):
        workSheet.write(row_num, col_num, columns[col_num], headerStyle)

    # Sheet body, remaining rows
    style = xlwt.XFStyle()
    records = ReportsRecords.objects.filter(report=report)
    row_num_str = 0
    for record in records:
        row_num += 1
        row_num_str += 1
        workSheet.col(0).width = 1000
        workSheet.write(row_num, 0, str(row_num_str), style)
        workSheet.col(1).width = 5000
        workSheet.write(row_num, 1, record.client, style)
        workSheet.write(row_num, 2, record.client_addr, style)
        workSheet.write(row_num, 3, record.client_phone, style)
        workSheet.col(4).width = 5000
        workSheet.write(row_num, 4, record.model_description, style)
        workSheet.col(5).width = 5000
        workSheet.write(row_num, 5, record.serial_number, style)
        if record.buy_date:
            workSheet.write(row_num, 6, record.buy_date.strftime("%d.%m.%y"), style)
        if record.start_date:
            workSheet.write(row_num, 7, record.start_date.strftime("%d.%m.%y"), style)
        if record.end_date:
            workSheet.write(row_num, 8, record.end_date.strftime("%d.%m.%y"), style)
        if record.move_cost:
            workSheet.write(row_num, 13, record.move_cost, style)
        if record.work_cost:
            workSheet.write(row_num, 14, record.work_cost, style)
        workSheet.col(15).width = 8000
        workSheet.write(row_num, 15, record.problem_description, style)
        workSheet.col(16).width = 8000
        workSheet.write(row_num, 16, record.work_description, style)
        workSheet.col(17).width = 2000
        workSheet.write(row_num, 17, record.code.code, style)
        parts = ReportsParts.objects.filter(record=record)
        for part in parts:
            workSheet.col(9).width = 8000
            workSheet.write(row_num, 9, part.title, style)
            if part.price:
                workSheet.write(row_num, 10, part.price, style)
            if part.count:
                workSheet.write(row_num, 11, part.count, style)
            workSheet.write(row_num, 12, part.document, style)
            row_num += 1
        if parts:
            row_num -= 1

    # Footer
    row_num += 1
    workSheet.write(row_num, 10, f'{report.total_part} руб',boldStyle)
    workSheet.write(row_num, 13, f'{report.total_move} руб', boldStyle)
    workSheet.write(row_num, 14, f'{report.total_work} руб', boldStyle)
    workSheet.write(row_num+1, 0, f'Всего по отчету: {report.total_cost} рублей.', boldStyle)

    workBook.save(response)
    return response


@user_passes_test(staff_validation)
def ReportChangeStatus(request):
    from main.business_logic import REPORT_STATUS
    if request.method == 'POST':
        new_status = None
        report_id = None
        mail_note = ''
        if 'send_refinement' in request.POST:
            report_id = request.POST.get('send_refinement')
            new_status = 'refinement'
            mail_note = request.POST.get('message')
        else:
            for status in REPORT_STATUS:
                if status[0] in request.POST:
                    report_id = request.POST.get(status[0])
                    if status[0] == 'draft':
                        new_status = 'send'
                    elif status[0] == 'send':
                        new_status = 'received'
                    elif status[0] == 'received':
                        new_status = 'verified'
                    elif status[0] == 'refinement':
                        new_status = 'send'
                    elif status[0] == 'verified':
                        new_status = 'accepted'
                    elif status[0] == 'accepted':
                        new_status = 'payment'
                    elif status[0] == 'payment':
                        new_status = 'draft'
        if new_status and report_id:
            report = get_object_or_404(Reports, pk=int(report_id))
            if report.service_center.staff_user == request.user or request.user.is_superuser or \
                    request.user.groups.filter(name='GeneralStaff').exists():
                report.status = new_status
                report.save()
                email = report.service_center.user.email
                if email:
                    SendReportSatus(email, report, mail_note)
                if new_status == 'received':
                    return redirect('report_page', report.pk)
    return redirect('reports_list')


@user_passes_test(staff_validation)
def ReportDocumet(request):
    if request.method == 'POST':
        if 'save' in request.POST:
            report_id = request.POST.get('save')
            if report_id:
                report = get_object_or_404(Reports, pk=int(report_id))
                if 'invoice' in request.POST:
                    report.invoice = request.POST.get('invoice')
                else:
                    report.invoice = None
                if 'act' in request.POST:
                    report.act = request.POST.get('act')
                else:
                    report.act = request.POST.get('act')
                if 'mail_date' in request.POST:
                    report.mail_date = request.POST.get('mail_date')
                else:
                    report.mail_date = None
                report.save()
                return redirect('report_page', report.pk)
    return redirect('staff_home')


class ReportsForStaff(LoginRequiredMixin, StaffUserMixin, ListView):
    model = Reports
    template_name = 'reports/staff_reports_list.html'
    context_object_name = 'reports'
    extra_context = {'title': 'Все отчеты:'}
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            reports = Reports.objects.all()
        elif self.request.user.groups.filter(name='GeneralStaff').exists():
            reports = Reports.objects.all().exclude(status='draft')
        else:
            reports = Reports.objects.filter(service_center__staff_user=self.request.user).exclude(status='draft')
        if self.request.GET.get("service_center", '') != '':
            reports = reports.filter(service_center=self.request.GET.get("service_center"))
        if self.request.GET.get("staff_user", '') != '':
            reports = reports.filter(service_center__staff_user=self.request.GET.get("staff_user"))
        if self.request.GET.get("use_status", '') == 'on' and self.request.GET.get("status", '') != '':
            reports = reports.filter(status=self.request.GET.get("status"))
        if self.request.GET.get("use_date", '') == 'on' and self.request.GET.get("month", '') != '' and \
                self.request.GET.get("year", '') != '':
            report_date = datetime.date(int(self.request.GET.get("year", '')), int(self.request.GET.get("month", '')),
                                        1)
            reports = reports.filter(report_date=report_date)
        return reports

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReportsFilterForm(self.request.GET)
        context['obj_count'] = self.object_list.count()
        return context


@user_passes_test(user_validation)
def ReportAdd(request):
    if request.method == 'POST':
        form = ReportTitleForm(request.POST)
        if form.is_valid():
            report_date = datetime.date(form.cleaned_data['year'], form.cleaned_data['month'], 1)
            note = form.cleaned_data['note']
            user = request.user
            try:
                center = ServiceCenters.objects.get(user=user, is_active=True)
            except():
                messages.error(request, 'Ощибка при добавлении отчета: сервисный центр не найден !')
                return redirect('user_home')
            if Reports.objects.filter(report_date=report_date, service_center=center):
                messages.error(request, 'Отчет для этого периода уже существует !')
                return redirect('user_home')
            else:
                report = Reports(service_center=center, user=user, report_date=report_date, note=note)
                report.save()
                return redirect('user_home')
    else:
        return redirect('user_home')


@user_passes_test(user_validation)
def ReportUpdate(request, report_pk):
    if request.method == 'POST':
        form = ReportTitleForm(request.POST)
        if form.is_valid():
            report = get_object_or_404(Reports, pk=report_pk)
            if report.service_center.user == request.user or request.user.is_superuser:
                report_date = datetime.date(form.cleaned_data['year'], form.cleaned_data['month'], 1)
                note = form.cleaned_data['note']
                if Reports.objects.filter(report_date=report_date, service_center=report.service_center).exclude(
                        pk=report_pk):
                    messages.error(request, 'Отчет для этого периода уже существует !')
                    return redirect('report_page', report_pk)
                else:
                    report.report_date = report_date
                    report.note = note
                    report.save()
                    return redirect('report_page', report_pk)
    else:
        return redirect('report_page', report_pk)


@user_passes_test(user_validation)
def ReportSend(request):
    if request.method == 'POST':
        if 'send' in request.POST:
            report_id = request.POST.get('send')
            if report_id:
                report = get_object_or_404(Reports, pk=int(report_id))
                if report.service_center.user == request.user or request.user.is_superuser:
                    report.status = 'send'
                    report.save()
                    SendReportToStaff(report)
    return redirect('user_home')


class ReportDetail(LoginRequiredMixin, UserMixin, DetailView):
    model = Reports
    template_name = 'reports/report_page.html'
    context_object_name = 'report'
    extra_context = {'title': 'Отчет за '}

    def test_func(self):
        report = self.get_object()
        return report.service_center.user == self.request.user or self.request.user.is_superuser or \
               (report.status != 'draft' and (report.service_center.staff_user == self.request.user or
                                              self.request.user.groups.filter(name='GeneralStaff').exists()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = ReportTitleForm()
        form.initial['month'] = self.object.report_date.month
        form.initial['year'] = self.object.report_date.year
        form.initial['note'] = self.object.note
        context['records'] = ReportsRecords.objects.filter(report=self.object)
        context['rep_form'] = form
        return context


@user_passes_test(staff_validation)
def RecordRemarks(request):
    if request.method == 'POST':
        if 'save' in request.POST:
            record_id = request.POST.get('save')
            remarks = None
            if 'remarks' in request.POST:
                remarks = request.POST.get('remarks')
            if record_id:
                record = get_object_or_404(ReportsRecords, pk=int(record_id))
                record.remarks = remarks
                record.save()
                return redirect('record_update_page', record.pk)
    return redirect('user_home')


@user_passes_test(staff_validation)
def RecordVerified(request):
    from datetime import datetime
    if request.method == 'POST':
        if 'save' in request.POST:
            record_id = request.POST.get('save')
            if record_id:
                record = get_object_or_404(ReportsRecords, pk=int(record_id))
                record.remarks = None
                record.verified = True
                record.verified_date = datetime.now().date()
                record.save()
                return redirect('record_update_page', record.pk)
    return redirect('user_home')


# общие процеудуры представлений добавления и обновления записи
class RecordView(View):
    success_message = 'my meesage'
    form_class = RecordForm
    error_message = 'Пожалуйста, проверьте форму !'
    template_name = 'reports/records_add.html'
    report = None

    def test_func(self):
        if self.object:
            report = self.object
        else:
            report = get_object_or_404(Reports, pk=self.kwargs['report_pk'])
        return report.service_center.user == self.request.user or self.request.user.is_superuser or (
                report.status != 'draft' and (self.request.user.groups.filter(name='GeneralStaff').exists() or
                                              report.service_center.staff_user == self.request.user))

    def form_invalid(self, form, **kwargs):
        ctx = self.get_context_data(**kwargs)
        parts_formset = PartsFormset(form.data, instance=form.instance, prefix='parts_formset')
        ctx['form'] = form
        ctx['parts_formset'] = parts_formset
        if 'errors' not in form.errors:
            # messages.error(self.request, form.errors)
            messages.error(self.request, self.error_message)
        return render(self.request, self.template_name, ctx)

    def form_valid(self, form):
        # if not form.instance.pk:
        #   form.save()
        parts_formset = PartsFormset(form.data, instance=form.instance, prefix='parts_formset')
        if parts_formset.is_valid():
            form.save()
            parts_formset.save()
            # сохраняем как есть по соответствующей кнопке или проверяем некритичные ошибки
            if form.cleaned_data['errors'] and 'save_with_warning' not in self.request.POST:
                errors_list = form.cleaned_data['errors'].split(';')
                form.add_error('errors', errors_list)
                return self.form_invalid(form)
            else:
                messages.success(self.request, self.success_message)
                form.save()
                return HttpResponseRedirect(self.get_success_url())
        else:
            form.is_valid = False
            errors = []
            num = 1
            for form_error in parts_formset.errors:
                if form_error:
                    for key in form_error:
                        err_string = 'Деталь №' + str(num) + ': ' + key + ' ' + form_error[key].as_text()
                        err_string = err_string.replace('title', 'Наименование')
                        err_string = err_string.replace('count', 'Количество')
                        err_string = err_string.replace('document', 'Документ')
                        err_string = err_string.replace('price', 'Цена')
                        err_string = err_string.replace('*', '-')
                        errors.append(err_string)
                num += 1
            form.add_error('parts_cost', errors)
            return self.form_invalid(form)

    def get_success_url(self):
        return self.request.path_info


class RecordAdd(LoginRequiredMixin, RecordView, CreateView):
    success_message = 'Ремонт успешно добавлен !'
    extra_context = {'title': 'Добавление ремонта в отчет за '}

    def setup(self, request, *args, **kwargs):
        super(RecordAdd, self).setup(request, *args, **kwargs)
        self.report = get_object_or_404(Reports, pk=self.kwargs['report_pk'])

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['report'] = self.report
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = get_object_or_404(Reports, pk=self.kwargs['report_pk'])
        context['can_edit'] = True
        context['parts_formset'] = PartsFormset(instance=self.object, prefix='parts_formset', user=self.request.user)
        return context


class RecordUpdate(LoginRequiredMixin, RecordView, UpdateView):
    model = ReportsRecords
    extra_context = {'title': 'Ремонт из отчета  '}
    success_message = 'Ремонт успешно изменен !'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object.report
        context['record'] = self.object
        context['can_edit'] = (self.object.report.status == 'draft' or self.object.report.status == 'refinement') and \
                              (
                                          not self.request.user.is_staff or self.request.user.is_superuser) and not self.object.verified
        context['parts_formset'] = PartsFormset(instance=self.object, prefix='parts_formset', user=self.request.user)
        return context


# обработка AJAX скрипта динамической формы
def load_codes_data(request):
    from django.db.models import Q
    groups = None
    codes = None
    code_id = None
    if 'product' in request.GET and request.GET.get('product'):
        product_id = request.GET.get('product')
        codes = Codes.objects.filter(Q(product_id=product_id) | Q(product_id=None), is_folder=False,
                                     is_active=True).order_by('code')
        groups = Codes.objects.filter(Q(product_id=product_id) | Q(product_id=None), is_folder=True,
                                      is_active=True).order_by('code')
        code_id = 0
        if 'code' in request.GET and request.GET.get('code'):
            code_id = int(request.GET.get('code'))
    return render(request, 'reports/codes_list_get.html', {'groups': groups, 'codes': codes, 'select_id': code_id})


# обработка AJAX скрипта динамической формы
def load_models_data(request):
    models_list = None
    if 'product' in request.GET and request.GET.get('product'):
        product_id = request.GET.get('product')
        models_list = Models.objects.filter(product_id=product_id).order_by('title')
    return render(request, 'reports/models_list_get.html', {'groups': models_list})


# обработка AJAX скрипта динамической формы
def load_work_price_data(request):
    price = 0
    if 'code' in request.GET and 'report' in request.GET and request.GET.get('code') and request.GET.get('report'):
        code_id = request.GET.get('code')
        report_id = request.GET.get('report')
        code = get_object_or_404(Codes, pk=code_id)
        report = get_object_or_404(Reports, pk=report_id)
        price_dict = GetPrices(code, report.service_center)
        if 'price' in price_dict:
            price = price_dict['price']
    return render(request, 'reports/price_get.html', {'price': price})


# удаление отета
def ReportDelete(request, report_pk):
    report = get_object_or_404(Reports, pk=report_pk)
    if request.user.is_superuser or request.user == report.user:
        report.delete()
        messages.success(request, 'Отчет успешно удален !')
        return redirect('user_home')
    else:
        return HttpResponseForbidden()


# удаление отета
def RecordDelete(request, report_pk):
    record = get_object_or_404(ReportsRecords, pk=report_pk)
    report = record.report
    if request.user.is_superuser or request.user == report.user:
        record.delete()
        messages.success(request, 'Запись успешно удалена !')
        report.save()
        return redirect(report.get_absolute_url())
    else:
        return HttpResponseForbidden()





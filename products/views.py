import os
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, FormView
from main.my_validators import StaffUserMixin, GeneralStaffUserMixin, general_staff_validation, UserMixin, \
    SuperUserMixin
from django.contrib import messages
from .models import *
from .forms import CodeForm, PriceForm, IndividualPriceForm, ProductionLoadForm, ProductionFilesLoadForm
from main.views import MyFormMessagesView
from servicecentres.models import ServiceCenters
from reportssite.settings import MEDIA_ROOT
from django.utils.timezone import make_aware


class ProductsList(LoginRequiredMixin, ListView):
    model = Models
    template_name = 'product/products_list.html'
    context_object_name = 'models'
    extra_context = {'title': 'Продукция',
                     'products': MainProducts.objects.all().order_by('short_title')
                     }


class CodeAndPriceList(LoginRequiredMixin, UserMixin, ListView):
    model = Codes
    template_name = 'product/codes_list.html'

    def test_func(self):
        center = ServiceCenters.objects.get(pk=self.kwargs['center_pk'])
        return center.user == self.request.user or self.request.user.is_superuser or center.staff_user == \
               self.request.user or self.request.user.groups.filter(name='GeneralStaff').exists()

    # вот это все что ниже вставляет страницу ожидания загрузки
    def get(self, request, *args, **kwargs):
        return render(request, 'product/codes_list_pause.html')

    def post(self, request, *args, **kwargs):
        request.POST.get('button')
        center = None
        if 'center_pk' in self.kwargs:
            center = ServiceCenters.objects.get(pk=self.kwargs['center_pk'])
        codeset = Codes.objects.all()
        context = {'products': MainProducts.objects.all().order_by('short_title'),
                   'center': center, }
        if center:
            context['title'] = 'Расценки для : '
        else:
            context['title'] = 'Коды и диапазоны расценок'
        return render(request, self.template_name, context)


class CodesAdd(LoginRequiredMixin, GeneralStaffUserMixin, MyFormMessagesView, CreateView):
    form_class = CodeForm
    template_name = 'product/code_add.html'
    extra_context = {'title': 'Добавление кода'}
    success_message = 'Код успешно добавлен !'

    def get_success_url(self):
        if 'close' in self.request.POST:
            return redirect('code_and_prices_page')
        else:
            return self.request.path_info


class CodesUpdate(LoginRequiredMixin, GeneralStaffUserMixin, MyFormMessagesView, UpdateView):
    model = Codes
    form_class = CodeForm
    template_name = 'product/code_add.html'
    extra_context = {'title': 'Изменение кода', 'is_update': True}
    success_url = reverse_lazy('code_and_prices_page')
    success_message = 'Код успешно обновлен !'


# -------------------------------------------------------------------------------------------------------------


class BasePriceList(LoginRequiredMixin, StaffUserMixin, ListView):
    model = BasePrice
    template_name = 'product/baseprices_list.html'
    context_object_name = 'prices'
    extra_context = {'products': MainProducts.objects.all().order_by('short_title'), }

    def get_context_data(self, **kwargs):
        from main.business_logic import GetBasePriceTitle
        context = super().get_context_data(**kwargs)
        key = self.kwargs['price_type']
        context['general_prices'] = BasePrice.objects.filter(product=None, price_type=key)
        context['price_type'] = key
        context['title'] = 'Базовые расценки для прайса "' + GetBasePriceTitle(key) + '"'
        return context

    def get_queryset(self):
        return BasePrice.objects.filter(price_type=self.kwargs['price_type']).order_by('price')


class BasePriceFormView(View):
    form_class = PriceForm
    next = None

    def get_initial(self):
        if 'next' in self.request.GET:
            self.next = self.request.GET['next']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.next
        return context

    def get_success_url(self):
        if 'close' in self.request.POST:
            if self.next:
                return self.next
            else:
                price_type = self.object.price_type
                return reverse_lazy('prices_list_page', kwargs={'price_type': price_type})
        else:
            return self.request.path_info


class BasePriceAdd(LoginRequiredMixin, GeneralStaffUserMixin, BasePriceFormView, MyFormMessagesView, CreateView):
    template_name = 'product/baseprice_add.html'
    success_message = 'Расценка успешно добавлена !'
    extra_context = {'title': 'Добавление базовой расценки', }

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if 'code_pk' in self.kwargs:
            kwargs['code'] = Codes.objects.get(pk=self.kwargs['code_pk'])
        if 'price_type' in self.kwargs:
            kwargs['price_type'] = self.kwargs['price_type']
        return kwargs


class BasePriceUpdate(LoginRequiredMixin, GeneralStaffUserMixin, BasePriceFormView, MyFormMessagesView, UpdateView):
    model = BasePrice
    template_name = 'product/baseprice_add.html'
    extra_context = {'title': 'Изменение базовой расценки', }
    success_message = 'Расценка успешно изменена !'


@user_passes_test(general_staff_validation)
def BasePriceDelete(request, price_pk):
    obj = get_object_or_404(BasePrice, pk=price_pk)
    price_type = obj.price_type
    obj.delete()
    messages.success(request, 'Расценка успешно удалена')
    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('prices_list_page', price_type)


# -------------------------------------------------------------------------------------------------------------


class CodePricesPage(LoginRequiredMixin, GeneralStaffUserMixin, ListView):
    model = CentersPrices
    template_name = 'product/prices_for_code_list.html'
    context_object_name = 'prices'
    allow_empty = True

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        code = Codes.objects.get(pk=self.kwargs['code_pk'])
        context['title'] = 'Расценки для кода'
        context['code'] = code
        context['base_prices'] = BasePrice.objects.filter(product=code.product, repair_type=code.repair_type).order_by(
            'price')
        return context

    def get_queryset(self):
        return CentersPrices.objects.filter(code=self.kwargs['code_pk'])


class CodePriceFormView(View):
    form_class = IndividualPriceForm
    template_name = 'product/center_price_add.html'
    next = None

    def get_initial(self):
        if 'next' in self.request.GET:
            self.next = self.request.GET['next']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.next
        return context

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        ctx = self.get_context_data(**kwargs)
        keys = list(form.errors)
        if '__all__' in form.errors:
            messages.error(self.request, form.errors['__all__'])
        else:
            messages.error(self.request, 'Проверьте форму!')
        ctx['form'] = form
        return self.render_to_response(ctx)

    def get_success_url(self):
        if 'close' in self.request.POST:
            if self.next:
                return self.next
            else:
                return reverse_lazy('code_and_prices_page', args=[self.object.service_center.pk, ])
        else:
            return self.request.path_info


class CenterPriceAdd(LoginRequiredMixin, GeneralStaffUserMixin, CodePriceFormView, CreateView):
    extra_context = {'title': 'Добавление индивидуальной расценки'}
    success_message = 'Расценка успешно добавлен !'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        if 'code_pk' in self.kwargs and self.kwargs['code_pk'] != 0:
            kwargs['code'] = self.code = get_object_or_404(Codes, pk=self.kwargs['code_pk'])
        if 'center_pk' in self.kwargs:
            kwargs['center'] = get_object_or_404(ServiceCenters, pk=self.kwargs['center_pk'])
        return kwargs


class CenterPriceUpdate(LoginRequiredMixin, GeneralStaffUserMixin, CodePriceFormView, UpdateView):
    model = CentersPrices
    extra_context = {'title': 'Изменекние индивидуальной расценки'}
    success_message = 'Расценка успешно изменена !'


# обработка AJAX скрипта динамической формы
def load_groups(request):
    if 'product' in request.GET:
        product_id = request.GET.get('product')
        groups = Codes.objects.filter(product_id=product_id, is_folder=True, is_active=True).order_by('code')
        return render(request, 'product/grouplist_get.html', {'groups': groups})
    if 'group' in request.GET:
        group_id = request.GET.get('group')
        codes = Codes.objects.filter(parent_id=group_id, is_folder=False, is_active=True).order_by('code')
        return render(request, 'product/grouplist_get.html', {'groups': codes})


@user_passes_test(general_staff_validation)
def CenterPriceDelete(request, price_pk):
    obj = get_object_or_404(CentersPrices, pk=price_pk)
    center = obj.service_center
    obj.delete()
    messages.success(request, 'Расценка успешно удалена')
    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('code_and_prices_page', center.pk)


# ------------------------------------------------------------------------------------------------------------------


class ProductionsList(LoginRequiredMixin, ListView):
    model = Production
    template_name = 'product/productions_list.html'
    context_object_name = 'records'
    extra_context = {'title': 'Результаты производства', }
    paginate_by = 100
    allow_empty = True

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        # form = CenterFilterForm(self.request.GET)
        # context['form'] = form
        # context['obj_count'] = self.object_list.count()
        return (context)

    def get_queryset(self):
        records = Production.objects.all().order_by('-date')
        # if self.request.GET.get("staff_user", '') != '':
        #    centres = centres.filter(staff_user=self.request.GET.get("staff_user"))
        return records


def MoveProductionFiles(request):
    if request.method == 'POST':
        form = ProductionLoadForm(request.POST, request.FILES)
        files = request.FILES.getlist('files')
        if form.is_valid():
            for file in files:
                path = os.sep.join([MEDIA_ROOT, 'productsFiles', str(file)])
                with open(path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
    else:
        pass
    return redirect('products_loading_page')


def UploadProductionFiles(request):
    files = os.listdir(path=os.sep.join([MEDIA_ROOT, 'productsFiles']))
    add_form = ProductionLoadForm()
    if request.method == 'POST':
        form = ProductionFilesLoadForm(request.POST)
        if form.is_valid():
            product_id = request.POST['product']
            shop_char = request.POST['shop']
            counter = 0
            if shop_char in [FACTORY_NOVATEK, FACTORY_NOVASIB]:
                for file in files:
                    path = os.sep.join([MEDIA_ROOT, 'productsFiles', file])
                    try:
                        with open(path, "r") as fileData:
                            for line in fileData:
                                string_dict = list(line.split("\t"))
                                date_time = make_aware(datetime.datetime.strptime(string_dict[0], '%y.%m.%d %H:%M:%S'))
                                #date_time = make_aware(datetime.datetime.strptime(string_dict[0], '%Y-%m-%d %H:%M:%S'))
                                code = ''.join(filter(str.isalnum, string_dict[2]))
                                try:
                                    if shop_char == FACTORY_NOVATEK:
                                        model = Models.objects.get(product_id=product_id, east_id=int(code[:2]))
                                    else:
                                        model = Models.objects.get(product_id=product_id, east_id=int(code[:2]))
                                except Models.DoesNotExist:
                                    continue
                                except Models.MultipleObjectsReturned:
                                    continue
                                shifts = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
                                code = ''.join([shop_char, model.code_chars, code[2:8], shifts[int(code[8])-1],
                                                code[9:]])
                                if not Production.objects.filter(code=code, shop=shop_char, type_pk=product_id):
                                    new_record = Production(date=date_time, type_pk=product_id, code=code,
                                                            shop=shop_char)
                                    new_record.save()
                                    counter += 1
                        os.remove(path)
                    except FileNotFoundError:
                        pass
            Production.objects.all().delete()
            if counter:
                messages.success(request, f'{counter} записей успешно загружено !')
            else:
                messages.error(request, f'Ни одной записи не загружено !')
            # Production.objects.all().delete()
            return redirect('productions_list_page')
    else:
        form = ProductionFilesLoadForm()
    return render(request, 'product/products_loading.html', {'form': form, 'files': files, 'add_form': add_form,
                                                             'title': 'Загрузка производства'})

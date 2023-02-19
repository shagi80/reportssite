from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View, DeleteView
from django.contrib import messages
from main.my_validators import SuperUserMixin, StaffUserMixin, GeneralStaffUserMixin
from main.views import MyFormMessagesView
from .forms import *
from .models import ServiceContacts


class ServiceCentersRegionList(LoginRequiredMixin, StaffUserMixin, ListView):
    model = ServiceRegions
    template_name = 'servicecentres/centres_regions_list.html'
    context_object_name = 'regions'
    extra_context = {'title': 'Регионы сервисных центров'}
    paginate_by = 10
    allow_empty = True


class ServiceCentersList(LoginRequiredMixin, StaffUserMixin, ListView):
    model = ServiceCenters
    template_name = 'servicecentres/centres_list.html'
    context_object_name = 'centres'
    extra_context = {'title': 'Сервисные центры'}
    paginate_by = 20

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CenterFilterForm(self.request.GET)
        context['form'] = form
        context['obj_count'] = self.object_list.count()
        return (context)

    def get_queryset(self):
        centres = ServiceCenters.objects.all()
        if self.request.GET.get("staff_user", '') != '':
            centres = centres.filter(staff_user=self.request.GET.get("staff_user"))
        if self.request.GET.get("active_only", '') != '':
            centres = centres.filter(is_active=True)
        if self.request.GET.get("filter", '') != '':
            centres = centres.filter(Q(title__contains=self.request.GET.get("filter")) | Q(city__contains=self.request.GET.get("filter")))
        if self.request.GET.get("region", '') != '':
            centres = centres.filter(region__pk=self.request.GET.get("region"))
        return centres


class ServiceCentersAdd(LoginRequiredMixin, GeneralStaffUserMixin, MyFormMessagesView, CreateView):
    form_class = CenterCreateForm
    template_name = 'servicecentres/centres_add.html'
    extra_context = {'title': 'Добавление сервисного центра'}
    success_message = 'Сервисный центр успешно добавлен'

    def get_success_url(self):
        if 'close' in self.request.POST:
            return reverse_lazy('centres_list_page')
        else:
            return reverse_lazy('centres_update_page', args=(self.object.id,))

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['def_user'] = self.request.user
        return kwargs


class ServiceCenterUpdate(LoginRequiredMixin, UserPassesTestMixin, MyFormMessagesView, UpdateView):
    model = ServiceCenters
    form_class = CenterCreateForm
    template_name = 'servicecentres/centres_add.html'
    success_message = 'Обьект успешно изменен'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['def_user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if 'close' in self.request.POST:
            if 'next' in self.request.GET:
                return self.request.GET['next']+'#Item-'+str(self.object.pk)
            else:
                return reverse_lazy('centres_list_page')
        else:
            return self.request.path_info

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or (self.request.user.is_staff and obj.staff_user == self.request.user) or \
               self.request.user.groups.filter(name='GeneralStaff').exists()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['title'] = obj.title
        context['object'] = obj
        return (context)


class ServiceCentersContactsList(LoginRequiredMixin, StaffUserMixin, ListView):
    model = ServiceContacts
    template_name = 'servicecentres/centres_contacts_list.html'
    context_object_name = 'contacts'
    extra_context = {'title': 'Контакты сервисных центров'}
    paginate_by = 21

    def get_queryset(self):
        centres = ServiceContacts.objects.all()
        if self.request.GET.get("filter", '') != '':
            centres = centres.filter(Q(service_center__title__contains=self.request.GET.get("filter")) | Q(name__contains=self.request.GET.get("filter")))
        return centres


class ServiceCentersContactsByCenter(LoginRequiredMixin, StaffUserMixin, ListView):
    model = ServiceContacts
    template_name = 'servicecentres/centres_contacts_list.html'
    context_object_name = 'contacts'
    extra_context = {'title': 'Контакты ораганизации '}
    allow_empty = True

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['center'] = ServiceCenters.objects.get(pk=self.kwargs['center_pk'])
        return (context)

    def get_queryset(self):
        return ServiceContacts.objects.filter(service_center_id=self.kwargs['center_pk']).select_related('service_center')


class ServiceContactAdd(LoginRequiredMixin, StaffUserMixin, MyFormMessagesView, CreateView):
    form_class = ContactCreateForm
    template_name = 'servicecentres/centres_contact_add.html'
    extra_context = {'title': 'Добавление контакта'}
    success_message = 'Контакт успешно добавлен'

    def get_success_url(self):
        def get_success_url(self):
            if 'close' in self.request.POST:
                return reverse_lazy('centres_contact_page', args=(self.object.service_center_id,))
            else:
                return reverse_lazy('contact_add_page')

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['staff_user'] = self.request.user
        return kwargs


class ServiceContactUpdate(LoginRequiredMixin, UserPassesTestMixin, MyFormMessagesView, UpdateView):
    model = ServiceContacts
    form_class = ContactCreateForm
    template_name = 'servicecentres/centres_contact_add.html'
    extra_context = {'title': 'Изменение контакта'}
    success_message = 'Контакт успешно изменен'

    def test_func(self):
        cnt = self.get_object()
        obj = ServiceCenters.objects.get(pk=cnt.service_center_id)
        return self.request.user.is_superuser or (self.request.user.is_staff and obj.staff_user == self.request.user) or\
               self.request.user.groups.filter(name='GeneralStaff').exists()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['center_id'] = obj.service_center_id
        return (context)

    def get_success_url(self):
        return reverse_lazy('centres_contact_page', args=(self.object.service_center_id,))

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['staff_user'] = self.request.user
        return kwargs


def ContactDelete(request, contact_pk):
    obj = get_object_or_404(ServiceContacts, pk=contact_pk)
    if request.user.is_superuser or request.user == obj.staff_user or request.user.groups.filter(name='GeneralStaff').exists():
        reverse_id = obj.service_center_id
        obj.delete()
        messages.success(request, 'Контакт успешно удален')
        return redirect('centres_contact_page', reverse_id)
    else:
        return HttpResponseForbidden()


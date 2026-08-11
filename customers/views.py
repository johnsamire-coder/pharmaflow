from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .models import Area, Route, Customer
from .forms import AreaForm, RouteForm, CustomerForm


# ====== Area Views ======
class AreaListView(LoginRequiredMixin, ListView):
    model = Area
    template_name = 'customers/area_list.html'
    context_object_name = 'areas'
    paginate_by = 20

    def get_queryset(self):
        qs = Area.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(area_name__icontains=q) | Q(city__icontains=q))
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs.order_by('area_name')


class AreaCreateView(LoginRequiredMixin, CreateView):
    model = Area
    form_class = AreaForm
    template_name = 'customers/area_form.html'
    success_url = reverse_lazy('customers:area_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.save()
        messages.success(self.request, 'تم إنشاء المنطقة بنجاح')
        return redirect(self.get_success_url())


class AreaUpdateView(LoginRequiredMixin, UpdateView):
    model = Area
    form_class = AreaForm
    template_name = 'customers/area_form.html'
    success_url = reverse_lazy('customers:area_list')

    def get_queryset(self):
        return Area.objects.filter(company=self.request.company)

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل المنطقة بنجاح')
        return redirect(self.get_success_url())


@require_POST
@login_required
def area_toggle_status(request, pk):
    obj = get_object_or_404(Area, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة المنطقة')
    return redirect('customers:area_list')


# ====== Route Views ======
class RouteListView(LoginRequiredMixin, ListView):
    model = Route
    template_name = 'customers/route_list.html'
    context_object_name = 'routes'
    paginate_by = 20

    def get_queryset(self):
        qs = Route.objects.filter(company=self.request.company).select_related('area', 'rep')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(route_name__icontains=q)
        status = self.request.GET.get('status', '').strip()
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs.order_by('route_name')


class RouteCreateView(LoginRequiredMixin, CreateView):
    model = Route
    form_class = RouteForm
    template_name = 'customers/route_form.html'
    success_url = reverse_lazy('customers:route_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.save()
        messages.success(self.request, 'تم إنشاء خط السير بنجاح')
        return redirect(self.get_success_url())


class RouteUpdateView(LoginRequiredMixin, UpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'customers/route_form.html'
    success_url = reverse_lazy('customers:route_list')

    def get_queryset(self):
        return Route.objects.filter(company=self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل خط السير بنجاح')
        return redirect(self.get_success_url())


@require_POST
@login_required
def route_toggle_status(request, pk):
    obj = get_object_or_404(Route, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة خط السير')
    return redirect('customers:route_list')


# ====== Customer Views ======
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        qs = Customer.objects.filter(company=self.request.company).select_related('area', 'route', 'rep')
        q = self.request.GET.get('q', '').strip()
        area_id = self.request.GET.get('area', '').strip()
        rep_id = self.request.GET.get('rep', '').strip()
        payment_type = self.request.GET.get('payment_type', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(
                Q(customer_code__icontains=q) |
                Q(pharmacy_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(contact_person__icontains=q)
            )
        if area_id:
            qs = qs.filter(area_id=area_id)
        if rep_id:
            qs = qs.filter(rep_id=rep_id)
        if payment_type:
            qs = qs.filter(payment_type=payment_type)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs.order_by('pharmacy_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['areas'] = Area.objects.filter(company=self.request.company, is_active=True).order_by('area_name')
        context['reps'] = self.request.company.users.filter(is_active=True).order_by('full_name', 'username')
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, 'تم إنشاء العميل بنجاح')
        return redirect(self.get_success_url())


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل بيانات العميل بنجاح')
        return redirect('customers:customer_detail', pk=self.object.pk)


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.company).select_related('area', 'route', 'rep')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['balance'] = self.object.get_balance_summary()
        context['credit_check'] = self.object.check_credit_limit()
        return context


@require_POST
@login_required
def customer_toggle_status(request, pk):
    obj = get_object_or_404(Customer, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة العميل')
    return redirect('customers:customer_list')

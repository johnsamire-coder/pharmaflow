from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import Q, Sum, Count
from decimal import Decimal
import json

from .models import (
    Consignment, ConsignmentItem,
    ConsignmentReturn, ConsignmentReturnItem
)
from .forms import (
    ConsignmentForm, ConsignmentItemFormSet,
    ConsignmentReturnForm, SettleConsignmentForm
)
from products.models import Product
from inventory.models import Batch
from core.models import AuditLog


def get_next_consignment_number(company):
    """توليد رقم أمر التصريف التالي"""
    prefix = "CS"
    year = timezone.now().year
    last = Consignment.objects.filter(
        company=company,
        consignment_number__startswith=f"{prefix}-{year}-"
    ).order_by('-id').first()
    if last:
        try:
            last_num = int(last.consignment_number.split('-')[-1])
            return f"{prefix}-{year}-{last_num + 1:04d}"
        except (ValueError, IndexError):
            pass
    return f"{prefix}-{year}-0001"


class ConsignmentListView(ListView):
    model = Consignment
    template_name = 'consignments/list.html'
    context_object_name = 'consignments'
    paginate_by = 20

    def get_queryset(self):
        qs = Consignment.objects.filter(
            company=self.request.company
        ).select_related('customer', 'sent_by').prefetch_related('items')

        # فلترة
        status = self.request.GET.get('status', '')
        search = self.request.GET.get('search', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(consignment_number__icontains=search) |
                Q(customer__customer_name__icontains=search)
            )
        if date_from:
            qs = qs.filter(sent_date__gte=date_from)
        if date_to:
            qs = qs.filter(sent_date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Consignment.STATUS_CHOICES
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['search'] = self.request.GET.get('search', '')
        ctx['date_from'] = self.request.GET.get('date_from', '')
        ctx['date_to'] = self.request.GET.get('date_to', '')

        # إحصائيات
        all_cs = Consignment.objects.filter(company=self.request.company)
        ctx['stats'] = {
            'total': all_cs.count(),
            'sent': all_cs.filter(status='sent').count(),
            'partial': all_cs.filter(status='partial_returned').count(),
            'settled': all_cs.filter(status='settled').count(),
        }
        return ctx


class ConsignmentCreateView(View):
    template_name = 'consignments/form.html'

    def get(self, request):
        form = ConsignmentForm(company=request.company)
        formset = ConsignmentItemFormSet(
            form_kwargs={'company': request.company}
        )
        context = {
            'form': form,
            'formset': formset,
            'title': 'إنشاء أمر تصريف جديد',
            'next_number': get_next_consignment_number(request.company),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = ConsignmentForm(company=request.company, data=request.POST)
        formset = ConsignmentItemFormSet(
            request.POST,
            form_kwargs={'company': request.company}
        )

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    consignment = form.save(commit=False)
                    consignment.company = request.company
                    consignment.sent_by = request.user
                    consignment.consignment_number = get_next_consignment_number(
                        request.company
                    )
                    consignment.status = Consignment.STATUS_DRAFT
                    consignment.save()

                    formset.instance = consignment
                    items = formset.save(commit=False)

                    for item in items:
                        item.save()

                    for obj in formset.deleted_objects:
                        obj.delete()

                    AuditLog.objects.create(
                        company=request.company,
                        user=request.user,
                        action='create',
                        model_name='Consignment',
                        object_id=consignment.id,
                        description=f'إنشاء أمر تصريف {consignment.consignment_number}'
                    )

                    messages.success(
                        request,
                        f'✅ تم إنشاء أمر التصريف {consignment.consignment_number} بنجاح'
                    )
                    return redirect('consignments:detail', pk=consignment.pk)

            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')
        else:
            messages.error(request, '❌ يرجى مراجعة البيانات المدخلة')

        context = {
            'form': form,
            'formset': formset,
            'title': 'إنشاء أمر تصريف جديد',
            'next_number': get_next_consignment_number(request.company),
        }
        return render(request, self.template_name, context)


class ConsignmentDetailView(View):
    template_name = 'consignments/detail.html'

    def get(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        items = consignment.items.select_related('product', 'batch').all()
        returns = consignment.returns.prefetch_related('items__consignment_item__product').all()

        context = {
            'consignment': consignment,
            'items': items,
            'returns': returns,
            'can_send': consignment.status == Consignment.STATUS_DRAFT,
            'can_return': consignment.status in [
                Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL
            ],
            'can_settle': consignment.status in [
                Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL
            ],
            'can_cancel': consignment.status in [
                Consignment.STATUS_DRAFT, Consignment.STATUS_SENT
            ],
        }
        return render(request, self.template_name, context)


class ConsignmentUpdateView(View):
    template_name = 'consignments/form.html'

    def get(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status != Consignment.STATUS_DRAFT:
            messages.error(request, '❌ لا يمكن تعديل أمر تصريف مرسل')
            return redirect('consignments:detail', pk=pk)

        form = ConsignmentForm(company=request.company, instance=consignment)
        formset = ConsignmentItemFormSet(
            instance=consignment,
            form_kwargs={'company': request.company}
        )
        context = {
            'form': form,
            'formset': formset,
            'consignment': consignment,
            'title': f'تعديل أمر التصريف {consignment.consignment_number}',
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status != Consignment.STATUS_DRAFT:
            messages.error(request, '❌ لا يمكن تعديل أمر تصريف مرسل')
            return redirect('consignments:detail', pk=pk)

        form = ConsignmentForm(
            company=request.company, data=request.POST, instance=consignment
        )
        formset = ConsignmentItemFormSet(
            request.POST,
            instance=consignment,
            form_kwargs={'company': request.company}
        )

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    consignment = form.save()
                    items = formset.save(commit=False)
                    for item in items:
                        item.save()
                    for obj in formset.deleted_objects:
                        obj.delete()

                    messages.success(request, '✅ تم تحديث أمر التصريف بنجاح')
                    return redirect('consignments:detail', pk=pk)
            except Exception as e:
                messages.error(request, f'❌ خطأ: {str(e)}')

        context = {
            'form': form,
            'formset': formset,
            'consignment': consignment,
            'title': f'تعديل أمر التصريف {consignment.consignment_number}',
        }
        return render(request, self.template_name, context)


class ConsignmentSendView(View):
    """تغيير حالة أمر التصريف لـ 'مرسلة'"""

    def post(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status != Consignment.STATUS_DRAFT:
            messages.error(request, '❌ الأمر ليس في حالة مسودة')
            return redirect('consignments:detail', pk=pk)

        if not consignment.items.exists():
            messages.error(request, '❌ لا يمكن إرسال أمر تصريف بدون بنود')
            return redirect('consignments:detail', pk=pk)

        consignment.status = Consignment.STATUS_SENT
        consignment.save()

        AuditLog.objects.create(
            company=request.company,
            user=request.user,
            action='update',
            model_name='Consignment',
            object_id=consignment.id,
            description=f'إرسال أمر التصريف {consignment.consignment_number}'
        )

        messages.success(request, f'✅ تم إرسال أمر التصريف {consignment.consignment_number}')
        return redirect('consignments:detail', pk=pk)


class ConsignmentReturnView(View):
    """تسجيل مرتجع من أمر التصريف"""
    template_name = 'consignments/return_form.html'

    def get(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status not in [Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL]:
            messages.error(request, '❌ لا يمكن تسجيل مرتجع لهذا الأمر')
            return redirect('consignments:detail', pk=pk)

        items = consignment.items.select_related('product').all()
        form = ConsignmentReturnForm()

        context = {
            'consignment': consignment,
            'items': items,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status not in [Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL]:
            messages.error(request, '❌ لا يمكن تسجيل مرتجع لهذا الأمر')
            return redirect('consignments:detail', pk=pk)

        form = ConsignmentReturnForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    consignment_return = form.save(commit=False)
                    consignment_return.consignment = consignment
                    consignment_return.received_by = request.user
                    consignment_return.save()

                    # معالجة كميات المرتجع لكل بند
                    has_items = False
                    for item in consignment.items.all():
                        qty_key = f'return_qty_{item.id}'
                        qty_str = request.POST.get(qty_key, '0').strip()
                        try:
                            qty = int(qty_str)
                        except (ValueError, TypeError):
                            qty = 0

                        if qty > 0:
                            if qty > item.quantity_remaining:
                                raise ValueError(
                                    f'الكمية المرتجعة ({qty}) أكبر من المتبقي '
                                    f'({item.quantity_remaining}) للمنتج '
                                    f'{item.product.product_name}'
                                )

                            ConsignmentReturnItem.objects.create(
                                consignment_return=consignment_return,
                                consignment_item=item,
                                quantity_returned=qty
                            )

                            item.quantity_returned += qty
                            item.save()
                            has_items = True

                    if not has_items:
                        raise ValueError('يجب إدخال كمية مرتجعة واحدة على الأقل')

                    # تحديث حالة أمر التصريف
                    all_settled = all(
                        i.quantity_remaining == 0
                        for i in consignment.items.all()
                    )
                    if all_settled:
                        consignment.status = Consignment.STATUS_SETTLED
                        consignment.settled_date = timezone.now().date()
                    else:
                        consignment.status = Consignment.STATUS_PARTIAL
                    consignment.save()

                    messages.success(request, '✅ تم تسجيل المرتجع بنجاح')
                    return redirect('consignments:detail', pk=pk)

            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
                consignment_return.delete()
            except Exception as e:
                messages.error(request, f'❌ خطأ غير متوقع: {str(e)}')
        else:
            messages.error(request, '❌ بيانات غير صحيحة')

        items = consignment.items.select_related('product').all()
        context = {
            'consignment': consignment,
            'items': items,
            'form': form,
        }
        return render(request, self.template_name, context)


class ConsignmentSettleView(View):
    """تسوية أمر التصريف وتحويل المباع لفاتورة"""
    template_name = 'consignments/settle_form.html'

    def get(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status not in [Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL]:
            messages.error(request, '❌ لا يمكن تسوية هذا الأمر')
            return redirect('consignments:detail', pk=pk)

        items = consignment.items.select_related('product').all()
        form = SettleConsignmentForm()

        context = {
            'consignment': consignment,
            'items': items,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status not in [Consignment.STATUS_SENT, Consignment.STATUS_PARTIAL]:
            messages.error(request, '❌ لا يمكن تسوية هذا الأمر')
            return redirect('consignments:detail', pk=pk)

        form = SettleConsignmentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # معالجة الكميات المباعة
                    has_sold = False
                    for item in consignment.items.all():
                        qty_key = f'sold_qty_{item.id}'
                        qty_str = request.POST.get(qty_key, '0').strip()
                        try:
                            qty = int(qty_str)
                        except (ValueError, TypeError):
                            qty = 0

                        if qty > 0:
                            if qty > item.quantity_remaining:
                                raise ValueError(
                                    f'الكمية المباعة ({qty}) أكبر من المتبقي '
                                    f'({item.quantity_remaining}) للمنتج '
                                    f'{item.product.product_name}'
                                )
                            item.quantity_sold += qty
                            item.save()
                            has_sold = True

                    if not has_sold:
                        raise ValueError('يجب إدخال كمية مباعة واحدة على الأقل')

                    # تحديث حالة الأمر
                    consignment.status = Consignment.STATUS_SETTLED
                    consignment.settled_date = timezone.now().date()
                    consignment.save()

                    AuditLog.objects.create(
                        company=request.company,
                        user=request.user,
                        action='update',
                        model_name='Consignment',
                        object_id=consignment.id,
                        description=f'تسوية أمر التصريف {consignment.consignment_number}'
                    )

                    messages.success(
                        request,
                        f'✅ تمت تسوية أمر التصريف {consignment.consignment_number} بنجاح'
                    )
                    return redirect('consignments:detail', pk=pk)

            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
            except Exception as e:
                messages.error(request, f'❌ خطأ غير متوقع: {str(e)}')

        items = consignment.items.select_related('product').all()
        context = {
            'consignment': consignment,
            'items': items,
            'form': form,
        }
        return render(request, self.template_name, context)


class ConsignmentCancelView(View):
    """إلغاء أمر التصريف"""

    def post(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        if consignment.status not in [
            Consignment.STATUS_DRAFT, Consignment.STATUS_SENT
        ]:
            messages.error(request, '❌ لا يمكن إلغاء هذا الأمر')
            return redirect('consignments:detail', pk=pk)

        consignment.status = Consignment.STATUS_CANCELLED
        consignment.save()

        AuditLog.objects.create(
            company=request.company,
            user=request.user,
            action='update',
            model_name='Consignment',
            object_id=consignment.id,
            description=f'إلغاء أمر التصريف {consignment.consignment_number}'
        )

        messages.warning(
            request,
            f'⚠️ تم إلغاء أمر التصريف {consignment.consignment_number}'
        )
        return redirect('consignments:list')


class ConsignmentPrintView(View):
    """طباعة أمر التصريف"""
    template_name = 'consignments/print.html'

    def get(self, request, pk):
        consignment = get_object_or_404(
            Consignment, pk=pk, company=request.company
        )
        items = consignment.items.select_related('product', 'batch').all()
        context = {
            'consignment': consignment,
            'items': items,
            'company': request.company,
        }
        return render(request, self.template_name, context)


def ajax_product_price(request):
    """AJAX: جلب سعر المنتج"""
    product_id = request.GET.get('product_id')
    company = request.company

    try:
        product = Product.objects.get(pk=product_id, company=company)
        return JsonResponse({
            'success': True,
            'price': str(product.selling_price),
            'unit': product.unit or '',
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'price': '0'})


def ajax_product_batches(request):
    """AJAX: جلب دفعات المنتج"""
    product_id = request.GET.get('product_id')
    company = request.company

    try:
        batches = Batch.objects.filter(
            company=company,
            product_id=product_id,
            status='available'
        ).order_by('expiry_date').values(
            'id', 'batch_number', 'expiry_date', 'quantity_available'
        )

        data = []
        for b in batches:
            data.append({
                'id': b['id'],
                'text': f"{b['batch_number']} - ينتهي: {b['expiry_date']} (متاح: {b['quantity_available']})",
                'expiry': str(b['expiry_date']),
                'available': b['quantity_available'],
            })

        return JsonResponse({'success': True, 'batches': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

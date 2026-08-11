
handler404 = 'pharmaflow.views.handler404'
handler500 = 'pharmaflow.views.handler500'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('products/', include('products.urls')),
    path('inventory/', include('inventory.urls')),
    path('customers/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('collections/', include('customer_collections.urls')),
    path('returns/', include('returns.urls')),
    path('reports/', include('reports.urls')),
    path('bonuses/', include('bonuses.urls')),
    path('notifications/', include('notifications.urls')),
    path('manufacturing/', include('manufacturing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

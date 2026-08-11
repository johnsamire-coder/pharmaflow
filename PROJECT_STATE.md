# PharmaFlow - Project State

## Server
- Ubuntu 22.04
- Domain: https://pharmaflow.jssolutions-eg.com
- Project Path: /var/www/pharmaflow
- Gunicorn Port: 8001
- Service: pharmaflow.service
- Nginx + SSL: Active

## Tech Stack
- Backend: Django 4.2
- Database: PostgreSQL 14
- Frontend: Bootstrap 5 RTL + Django Templates
- Auth: Django Built-in

## Architecture
- SaaS Multi-tenant
- Company isolation via company FK
- Middleware: TenantMiddleware, AuditLogMiddleware

## Apps Status - ALL COMPLETE
- core ✅
- products ✅
- inventory ✅
- customers ✅
- sales ✅
- customer_collections ✅
- bonuses ✅
- returns ✅
- reports ✅
- notifications ✅
- dashboard ✅
- manufacturing ⏳
- consignments ⏳

## Current Working URLs
- /dashboard/
- /products/ , /products/categories/ , /products/forms/
- /inventory/ , /inventory/batches/ , /inventory/warehouses/ , /inventory/movements/
- /customers/ , /customers/areas/ , /customers/routes/
- /sales/orders/ , /sales/invoices/
- /collections/ , /collections/cheques/
- /returns/ , /returns/credit-notes/
- /reports/ , /reports/sales/ , /reports/collections/ , /reports/inventory/ , /reports/aging/
- /bonuses/ , /bonuses/customer-rules/ , /bonuses/report/
- /notifications/
- /users/
- /settings/
- /superadmin/

## Admin Credentials
- username: admin
- password: 1234

## Important Technical Notes
- Bonus calculation: customer-specific rules (approved only) > general rules
- Invoice numbering uses system settings prefix
- Notifications: auto-check for expiry, low-stock, cheques via /notifications/run-checks/
- Returns: auto-creates credit note on warehouse receipt
- Collections: recalculates invoice status on every save/confirm/bounce

## Next
- Manufacturing (التصنيع لدى الغير)
- Consignments (تحت التصريف)

# AGENTS.md — Sistema Post

## Project overview

Django 6 POS system. 7 apps under `apps/` namespace. Custom user model (`accounts.User`) with roles: admin, supervisor, user.
**Obsidian & Copper** theme (warm dark + copper accents). Tailwind CSS CDN, HTMX for partial updates, Alpine.js for client-side state.

## Commands

```powershell
# Everything runs through .venv Python directly (no activation needed)
..\.venv\Scripts\python.exe manage.py <command>

# Install deps (uv auto-discovers .venv from any subdirectory)
uv pip install -r requirements.txt
uv pip install <package>

# Migrations
..\.venv\Scripts\python.exe manage.py makemigrations <app_name>
..\.venv\Scripts\python.exe manage.py migrate

# Create superuser (use shell to pass role=admin)
..\.venv\Scripts\python.exe manage.py shell -c "from apps.accounts.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'admin123', role='admin')"

# Dev server (default http://127.0.0.1:8000)
..\.venv\Scripts\python.exe manage.py runserver

# Check
..\.venv\Scripts\python.exe manage.py check

# Collect static files (for production)
..\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

## Seed data

Creates admin/supervisor/user accounts, categories, products, clients, and a supplier:

```powershell
..\.venv\Scripts\python.exe manage.py shell -c "
from apps.accounts.models import User; from apps.inventory.models import Category, Product
from apps.clients.models import Client; from apps.suppliers.models import Supplier
User.objects.create_superuser('admin','admin@test.com','admin123',role='admin')
User.objects.create_user('supervisor','super@test.com','super123',role='supervisor')
User.objects.create_user('vendedor','user@test.com','user123',role='user')
Category.objects.create(name='Electrodomesticos'); Category.objects.create(name='Ropa')
Category.objects.create(name='Computadores y Accesorios')
Product.objects.create(sku='ELE-001',name='Cafetera',price=150000,stock=10,min_stock=1)
Product.objects.create(sku='ROP-001',name='Camisa',price=60000,stock=20,min_stock=1)
Product.objects.create(sku='COM-001',name='Laptop',price=500000,stock=5,min_stock=1)
Client.objects.create(name='Juan Pérez',email='juan@test.com',phone='555-0101')
Client.objects.create(name='Margarita Campos',email='marga@test.com',phone='3045678833')
Client.objects.create(name='Jose Ortega',email='jose@test.com',phone='3225780034')
Supplier.objects.create(name='Distribuidora ABC',email='abc@test.com',phone='555-0201')
print('Seed data created')
"
```

## Architecture

- **Custom user model**: `accounts.User` extends `AbstractUser`, adds `role` (admin/supervisor/user) + `phone`.
- **Permissions**: decorators in `accounts.decorators` — `role_required(allowed_roles=[...])`, `admin_required`. Templates check `user.is_admin()`, `user.can_update()`, `user.can_delete()`.
- **URLs**: each app mounts under its prefix (`/accounts/`, `/inventory/`, `/clients/`, `/suppliers/`, `/sales/`, `/reports/`, `/` for core).
- **Templates**: root `templates/` dir, namespaced by app subdirectory. Extends `layouts/base.html`.
- **Frontend**: Tailwind CSS via CDN, HTMX for partial updates, Alpine.js for client-side state. **Chart.js 4.4.8 via CDN** for report charts (doughnut + bar). `app.css` has full design system with CSS vars, grain texture overlay, animations.
- **Theme**: "Obsidian & Copper" — warm dark obsidian backgrounds (`#0d0a07`–`#201d18`), copper accent (`#d4834a`), gradient icon backgrounds with glow + inset highlight.
- **Typography**: Sora (body), Archivo (headings), DM Mono (data/monospace). All loaded via Google Fonts in `app.css`.
- **Layout patterns**: list views use `max-w-7xl mx-auto` with `table-container`. Forms use `max-w-2xl mx-auto` with `card`. Sale new view uses `lg:grid-cols-2` (search/products left, summary right with `sticky top-24`).
- **Static/media**: `STATICFILES_DIRS` → `static/`, `MEDIA_ROOT` → `media/`.
- **Currency**: `apps.core.templatetags.currency_tags` filter `|pesos` for COP formatting. Alpine uses `formatPeso()` JS function with `toLocaleString('es-CO')`.
- **Toast messages**: Fixed bottom-center (`bottom-4 left-1/2 -translate-x-1/2 z-[100]`), auto-dismiss at 5s via Alpine `x-init`, close button `×`. Rendered for all users (not just authenticated) — gating removed so login errors display correctly.
- **Login flow**: Custom `login_view` in `accounts.views`. Uses PRG pattern on failure: `messages.error()` + `return redirect('accounts:login')` to avoid form resubmission prompts and clear fields. `authenticate()` + `login()` on success → `core:dashboard`.
- **Password reset (admin-mediated)**: Admin can reset any user's password via `accounts.views.admin_password_reset` (`@admin_required`). Uses `AdminPasswordResetForm` in `accounts.forms` (validates password match). URL: `users/<pk>/reset-password/`. Template: `accounts/admin_password_reset.html`.
- **Dashboard ranking**: Card "Productos Más Vendidos" shows top 6 products by `SUM(quantity)` from `SaleItem`. Best-selling category displayed as a pill badge in the card header. Positions 1-3 use gold/silver/bronze gradient circles. Revenue column (`total_revenue`) only visible to `admin`/`supervisor` via `{% if user.is_admin or user.is_supervisor %}`.
- **Report print**: "Imprimir" button in `reports/detail.html` hidden for `role='user'` via `{% if user.role != 'user' %}`.
- **Report charts**: Two Chart.js graphs in `reports/detail.html`, visible only to `admin` (`{% if user.is_admin %}`). Doughnut chart (payment method distribution) and bar chart (daily sales totals). Data fetched client-side from `/reports/chart-data/?date_from=&date_to=` JSON endpoint. Endpoint uses `TruncDate` aggregation + `_get_sales_data` helper. Chart colors match theme (emerald/blue/purple for payment methods, copper `#d4834a` for daily bars). Tooltips formatted in COP.

## Key patterns

- **Views**: function-based, `@login_required` + role decorators. CRUD = 4-view pattern (list, create, update, delete).
- **Forms**: `ModelForm` subclass with `{'class': 'form-input'}` in `__init__` for dark theme styling.
- **Invoice numbers**: `sales.utils.InvoiceCounter` model with `select_for_update()` for atomic sequential counters (prefixes: `VNT`, `FAC`).
- **Sale flow**: `add_item` (JSON POST validates stock) → `sale_complete` (atomic, prefetches products with `select_for_update()`, deducts stock, creates Sale + SaleItems). `sale_pay` validates status is PENDING first.
- **Product search**: returns JSON when `?format=json` (for Alpine.js product filters), HTML partial for other requests.
- **Reports/dashboard**: only count sales with `status='pagada'`. All date filters use `date__gte`/`date__lt` (sargable). Report page supports `preset=` (hoy/semana/mes) and custom `date_from=`/`date_to=` GET params. Charts endpoint `/reports/chart-data/` (admin-only) returns `payment_breakdown` + `daily_totals` for the given date range.
- **Pagination**: `Paginator` at 25 items/page on all list views.
- **Password toggle**: Password fields on login, user creation, and admin reset use Alpine.js `x-ref="pwd"` + `$refs.pwd.type` to toggle visibility. Eye icon SVGs toggle via `x-show` bound to `show` boolean in `x-data`.
- **Indexes**: `db_index=True` on frequently filtered fields. Composite index `idx_sale_active_status_date` on Sale.
- **Language**: es-es. Timezone: America/Mexico_City.

## Gotchas

- `.venv` is in parent dir (`../.venv/`). Use `..\.venv\Scripts\python.exe manage.py ...` from `system_post/`.
- `uv pip install` works from any subdirectory — uv auto-discovers `.venv` in parent dirs.
- **No git repo initialized** — `git init` hasn't been run. Add `.gitignore` before first commit.
- **No `.gitignore` exists** — neither at project root nor in `system_post/`. Would commit `.venv/`, `db.sqlite3`, `__pycache__/`, etc.
- `{% block content %}` must appear exactly once in `base.html` — Django errors on duplicates even inside `{% if %}`.
- Sale `status` and `is_active` are separate: `status` = pendiente/pagada, `is_active` = False means cancelled.
- `@role_required()` with no args denegates access to non-admin users (not silently allows).
- No tests, no CI, no lint/typecheck config yet.

## Design decisions

- **Avoid Tailwind utility conflicts**: Don't duplicate CSS class properties with Tailwind utilities on the same element. E.g., `.quick-card` already sets `display: flex` + `gap` + `padding`, so don't also add `flex gap-4 p-5`. The CSS file loads after Tailwind CDN and will override, but it causes unexpected overflow/layout issues.
- **Alpine.js `x-data`**: Every component that uses Alpine directives (`x-model`, `x-show`, `@click`, etc.) must have `x-data="componentName()"` on a parent element. Losing this breaks all interactivity.
- **Sale new page layout**: Grid is `lg:grid-cols-2` — left column has search + items table, right column has summary card with `sticky top-24 self-start` for scroll persistence.

# Sistema Post

Sistema de punto de venta (POS) completo con Django, Tailwind CSS, HTMX y Alpine.js. Tema **Obsidiana & Cobre** — oscuro cálido con textura de grano, acentos cobrizos y diseño responsive.

## Características

- **Dashboard** con resumen de ventas, stock bajo, clientes, proveedores y ranking top 6 productos más vendidos
- **Toast notifications** automáticos (5s) para errores y confirmaciones, visibles en toda la app
- **Usuarios** CRUD con roles: admin, supervisor, usuario
- **Recuperación de contraseña** administrador restablece contraseña de cualquier usuario desde el panel
- **Toggle de visibilidad** en campos de contraseña (login, creación de usuario, reset por admin) con icono de ojo
- **Inventario** con productos, categorías y alertas de stock mínimo
- **Clientes** CRUD con facturas (pendiente/pagada/cancelada)
- **Proveedores** CRUD con facturas (pendiente/pagada/cancelada)
- **Ventas** con buscador de productos en tiempo real, carrito, y generación de factura
- **Estados de venta**: pagada / pendiente (solo se reflejan en reportes las pagadas)
- **Facturación automática** para clientes registrados al hacer una venta
- **Reportes** diarios, semanales y mensuales
- **Filtros** en tiempo real por categoría, estado, cliente y vendedor
- **Responsive** adaptable a computadoras, tablets y celulares
- **Pesos colombianos** como moneda predeterminada

## Roles y Permisos

| Rol         | Crear | Ver | Actualizar | Eliminar | Cancelar ventas | Imprimir reportes | Ver ingresos ranking |
|-------------|-------|-----|------------|----------|-----------------|-------------------|---------------------|
| Admin       | ✓     | ✓   | ✓          | ✓        | ✓               | ✓                 | ✓                   |
| Supervisor  | ✓     | ✓   | ✓          | ✓        | ✗               | ✓                 | ✓                   |
| Usuario     | ✓     | ✓   | ✗          | ✗        | ✗               | ✗                 | ✗                   |

## Requisitos

- Python 3.10+
- uv (gestor de paquetes)

## Instalación

```bash
# 1. Clonar y entrar al proyecto
git clone <repo-url>
cd system_post

# 2. Crear entorno virtual con uv
uv venv

# 3. Activar (Windows)
.venv\Scripts\activate
# o Linux/Mac: source .venv/bin/activate

# 4. Instalar dependencias
uv pip install -r requirements.txt

# 5. Migrar base de datos
python manage.py migrate

# 6. Cargar datos de prueba (opcional)
python manage.py shell  "
from apps.accounts.models import User
from apps.inventory.models import Category, Product
from apps.clients.models import Client
from apps.suppliers.models import Supplier

User.objects.create_superuser('admin', 'admin@test.com', 'admin123', role='admin')
User.objects.create_user('supervisor', 'super@test.com', 'super123', role='supervisor')
User.objects.create_user('vendedor', 'user@test.com', 'user123', role='user')

cat1 = Category.objects.create(name='Electrodomesticos')
cat2 = Category.objects.create(name='Ropa')
cat3 = Category.objects.create(name='Computadores y Accesorios')
Product.objects.create(sku='ELE-001', name='Cafetera', category=cat1, price=150000, stock=10, min_stock=1)
Product.objects.create(sku='ROP-001', name='Camisa', category=cat2, price=60000, stock=20, min_stock=1)
Product.objects.create(sku='COM-001', name='Laptop', category=cat3, price=500000, stock=5, min_stock=1)
Client.objects.create(name='Juan Pérez', email='juan@test.com', phone='555-0101')
Client.objects.create(name='Margarita Campos', email='marga@test.com', phone='3045678833')
Client.objects.create(name='Jose Ortega', email='jose@test.com', phone='3225780034')
Supplier.objects.create(name='Distribuidora ABC', email='abc@test.com', phone='555-0201')
print('Datos creados')
"

# 7. Iniciar servidor
python manage.py runserver
```

## Usuarios por Defecto

| Usuario    | Contraseña | Rol         |
|------------|------------|-------------|
| admin      | admin123   | Admin       |
| supervisor | super123   | Supervisor  |
| usuario    | user123    | Usuario     |

## Dashboard

- **Resumen** con cards de Ventas Hoy, Productos, Clientes y Proveedores
- **Productos Más Vendidos**: ranking top 6 por unidades vendidas, con medallas visuales para 1.º, 2.º y 3.º (oro/plata/bronce)
- **Categoría top**: badge en el header del ranking mostrando la categoría con más ventas
- **Acceso rápido** a Nueva Venta, Inventario, Clientes y Proveedores
- **Ventas recientes**: listado de últimas 5 ventas pagadas

## Flujo de Venta

1. **Buscar producto** en el panel izquierdo (búsqueda en tiempo real por SKU/nombre/categoría)
2. Ajustar **cantidad** directamente en la tabla
3. Elegir **cliente** (opcional — si se selecciona, se genera factura automática)
4. Elegir **método de pago** y monto recibido (el resumen se mantiene visible con `sticky`)
5. **Cobrar Venta** → status `pagada`, aparece en reportes
6. **Pendiente** (solo con cliente) → status `pendiente`, no aparece en reportes, se puede cobrar después
7. Las ventas pendientes se pueden **cobrar** desde la lista o el detalle

## Estructura del Proyecto

```
system_post/
├── config/                    # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               # Usuarios y autenticación
│   ├── core/                   # Dashboard + template tags (moneda)
│   ├── inventory/              # Productos y categorías
│   ├── clients/                # Clientes y facturas
│   ├── suppliers/              # Proveedores y facturas
│   ├── sales/                  # Ventas (POS), utilidades (folios)
│   └── reports/                # Reportes de ventas
├── templates/                  # Templates por app
│   ├── layouts/                # Base template
│   └── {accounts,inventory,clients,suppliers,sales,reports,core}/
├── static/
│   ├── css/app.css             # Sistema de diseño completo
│   └── js/
├── media/                      # Archivos subidos
├── manage.py
├── requirements.txt
├── AGENTS.md                   # Instrucciones para asistentes IA
└── README.md
```

## Tecnologías

- **Backend:** Django 6
- **Frontend:** Tailwind CSS (CDN) + CSS personalizado con textura de grano
- **Reactivity:** HTMX + Alpine.js
- **Tipografía:** Archivo (headings) + Sora (body) + DM Mono (datos)
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)

## Rendimiento

- `select_for_update()` en operaciones críticas de stock (evita race conditions)
- `Prefetch` de productos en ventas (1 query vs N+1)
- `db_index` en todos los campos filtrados
- Índice compuesto `idx_sale_active_status_date` en ventas
- Queries sargables en reportes (`date__gte` en vez de `date__date__gte`)
- Paginación (25 items/página) en todas las listas

## Licencia

MIT

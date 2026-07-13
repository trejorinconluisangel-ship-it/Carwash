"""Script para poblar datos iniciales de demo."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carwash.settings')
django.setup()

from datetime import date, timedelta
import random
from insumos.models import Proveedor, Insumo, Compra
from servicios.models import TipoServicio, TipoVehiculo, InsumoEnServicio, Servicio

print("Limpiando datos anteriores...")
Servicio.objects.all().delete()
InsumoEnServicio.objects.all().delete()
Compra.objects.all().delete()
Insumo.objects.all().delete()
Proveedor.objects.all().delete()
TipoServicio.objects.all().delete()
TipoVehiculo.objects.all().delete()

# ── Proveedores ───────────────────────────────────────────
print("Creando proveedores...")
p1 = Proveedor.objects.create(nombre='Quimex Querétaro', contacto='Ramón Torres', telefono='442-311-0045', email='ventas@quimex.mx', notas='Entrega los martes y jueves')
p2 = Proveedor.objects.create(nombre='Limpieza Total SA', contacto='Sofía Ruiz', telefono='442-188-9900', email='sofia@limpiezatotal.mx')
p3 = Proveedor.objects.create(nombre='AutoParts & Supply', contacto='Jorge Mendez', telefono='442-500-1234')

# ── Insumos ───────────────────────────────────────────────
print("Creando insumos...")
shampoo = Insumo.objects.create(nombre='Shampoo Concentrado', categoria='shampoo', unidad_medida='litro', costo_unitario=85, proveedor=p1, stock_minimo=2)
desengrasante = Insumo.objects.create(nombre='Desengrasante Industrial', categoria='desengrasante', unidad_medida='litro', costo_unitario=120, proveedor=p1, stock_minimo=1)
cera = Insumo.objects.create(nombre='Cera Carnauba Líquida', categoria='cera', unidad_medida='litro', costo_unitario=250, proveedor=p2, stock_minimo=0.5)
aromatizante = Insumo.objects.create(nombre='Aromatizante Tropical', categoria='aromatizante', unidad_medida='litro', costo_unitario=70, proveedor=p2, stock_minimo=0.5)
limpiador_tapiz = Insumo.objects.create(nombre='Limpiador de Tapicería', categoria='limpiador', unidad_medida='litro', costo_unitario=160, proveedor=p1, stock_minimo=1)
microfibra = Insumo.objects.create(nombre='Paños Microfibra', categoria='microfibra', unidad_medida='pieza', costo_unitario=25, proveedor=p3, stock_minimo=5)

# ── Compras iniciales ─────────────────────────────────────
print("Creando compras...")
hoy = date.today()
Compra.objects.create(insumo=shampoo, cantidad=10, costo_unitario=85, fecha=hoy - timedelta(days=15), proveedor=p1)
Compra.objects.create(insumo=desengrasante, cantidad=5, costo_unitario=120, fecha=hoy - timedelta(days=15), proveedor=p1)
Compra.objects.create(insumo=cera, cantidad=3, costo_unitario=250, fecha=hoy - timedelta(days=10), proveedor=p2)
Compra.objects.create(insumo=aromatizante, cantidad=4, costo_unitario=70, fecha=hoy - timedelta(days=10), proveedor=p2)
Compra.objects.create(insumo=limpiador_tapiz, cantidad=3, costo_unitario=160, fecha=hoy - timedelta(days=5), proveedor=p1)
Compra.objects.create(insumo=microfibra, cantidad=20, costo_unitario=25, fecha=hoy - timedelta(days=5), proveedor=p3)

# ── Tipos de servicio ─────────────────────────────────────
print("Creando tipos de servicio...")
express_ext = TipoServicio.objects.create(nombre='Lavado Express Exterior', precio_base=80, descripcion='Lavado rápido solo exterior con shampoo y enjuague')
express_comp = TipoServicio.objects.create(nombre='Lavado Completo', precio_base=150, descripcion='Exterior e interior, aspirado y aromatizante')
motor = TipoServicio.objects.create(nombre='Detallado de Motor', precio_base=200, descripcion='Limpieza profunda del compartimento del motor')
vestiduras = TipoServicio.objects.create(nombre='Lavado de Vestiduras', precio_base=300, descripcion='Limpieza profunda de tapicería y alfombras')
encerado = TipoServicio.objects.create(nombre='Encerado y Pulido', precio_base=250, descripcion='Aplicación de cera carnauba para protección y brillo')
premium = TipoServicio.objects.create(nombre='Servicio Premium Full', precio_base=500, descripcion='Todos los servicios: exterior, interior, motor, cera y aromatizante')

# ── Tipos de vehículo ─────────────────────────────────────
print("Creando tipos de vehículo...")
moto      = TipoVehiculo.objects.create(nombre='Moto', multiplicador_precio=0.6)
auto_ch   = TipoVehiculo.objects.create(nombre='Auto Pequeño', multiplicador_precio=0.9)
sedan     = TipoVehiculo.objects.create(nombre='Sedán / Auto Mediano', multiplicador_precio=1.0)
pickup    = TipoVehiculo.objects.create(nombre='Pick Up', multiplicador_precio=1.4)
camioneta = TipoVehiculo.objects.create(nombre='Camioneta / SUV', multiplicador_precio=1.5)
van       = TipoVehiculo.objects.create(nombre='Van / Minivan', multiplicador_precio=1.6)
camion    = TipoVehiculo.objects.create(nombre='Camión', multiplicador_precio=2.0)

# ── Insumos en servicios ──────────────────────────────────
print("Asignando insumos a servicios...")
InsumoEnServicio.objects.create(tipo_servicio=express_ext, insumo=shampoo, cantidad_por_servicio=0.1)
InsumoEnServicio.objects.create(tipo_servicio=express_comp, insumo=shampoo, cantidad_por_servicio=0.1)
InsumoEnServicio.objects.create(tipo_servicio=express_comp, insumo=aromatizante, cantidad_por_servicio=0.05)
InsumoEnServicio.objects.create(tipo_servicio=motor, insumo=desengrasante, cantidad_por_servicio=0.15)
InsumoEnServicio.objects.create(tipo_servicio=vestiduras, insumo=limpiador_tapiz, cantidad_por_servicio=0.2)
InsumoEnServicio.objects.create(tipo_servicio=encerado, insumo=cera, cantidad_por_servicio=0.08)
InsumoEnServicio.objects.create(tipo_servicio=premium, insumo=shampoo, cantidad_por_servicio=0.12)
InsumoEnServicio.objects.create(tipo_servicio=premium, insumo=cera, cantidad_por_servicio=0.1)
InsumoEnServicio.objects.create(tipo_servicio=premium, insumo=aromatizante, cantidad_por_servicio=0.06)
InsumoEnServicio.objects.create(tipo_servicio=premium, insumo=desengrasante, cantidad_por_servicio=0.1)

# ── Servicios de demo ─────────────────────────────────────
print("Creando servicios de demo...")
tipos_s = [express_ext, express_comp, motor, vestiduras, encerado, premium]
tipos_v = [moto, auto_ch, sedan, pickup, camioneta]

for dia_offset in range(30):
    fecha = hoy - timedelta(days=dia_offset)
    num_servicios = random.randint(3, 12)
    for _ in range(num_servicios):
        ts = random.choice(tipos_s)
        tv = random.choice(tipos_v)
        precio = round(float(ts.precio_base) * float(tv.multiplicador_precio), 0)
        Servicio.objects.create(fecha=fecha, tipo_servicio=ts, tipo_vehiculo=tv, precio_cobrado=precio)

print("\n✅ Datos de demo cargados exitosamente!")
print(f"   Proveedores: {Proveedor.objects.count()}")
print(f"   Insumos: {Insumo.objects.count()}")
print(f"   Compras: {Compra.objects.count()}")
print(f"   Tipos de servicio: {TipoServicio.objects.count()}")
print(f"   Tipos de vehículo: {TipoVehiculo.objects.count()}")
print(f"   Servicios: {Servicio.objects.count()}")

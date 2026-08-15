"""Script para poblar datos iniciales de demo."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carwash.settings')
django.setup()

from datetime import date, timedelta
import random
from insumos.models import Proveedor, Insumo, Compra
from servicios.models import TipoServicio, TipoVehiculo, Servicio, PrecioPaquete

print("Limpiando datos anteriores...")
Servicio.objects.all().delete()
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
shampoo = Insumo.objects.create(nombre='Shampoo Concentrado', categoria='shampoo', unidad_medida='litro', proveedor=p1, envases_stock_minimo=1)
desengrasante = Insumo.objects.create(nombre='Desengrasante Industrial', categoria='desengrasante', unidad_medida='litro', proveedor=p1, envases_stock_minimo=1)
cera = Insumo.objects.create(nombre='Cera Carnauba Líquida', categoria='cera', unidad_medida='litro', proveedor=p2, envases_stock_minimo=1)
aromatizante = Insumo.objects.create(nombre='Aromatizante Tropical', categoria='aromatizante', unidad_medida='litro', proveedor=p2, envases_stock_minimo=1)
limpiador_tapiz = Insumo.objects.create(nombre='Limpiador de Tapicería', categoria='limpiador', unidad_medida='litro', proveedor=p1, envases_stock_minimo=1)
microfibra = Insumo.objects.create(nombre='Paños Microfibra', categoria='microfibra', unidad_medida='pieza', proveedor=p3, envases_stock_minimo=3)

# ── Compras iniciales (suman envases a la bodega) ──────────
print("Creando compras...")
hoy = date.today()
Compra.objects.create(insumo=shampoo, envases=10, costo_por_envase=85, fecha=hoy - timedelta(days=15), proveedor=p1)
Compra.objects.create(insumo=desengrasante, envases=5, costo_por_envase=120, fecha=hoy - timedelta(days=15), proveedor=p1)
Compra.objects.create(insumo=cera, envases=3, costo_por_envase=250, fecha=hoy - timedelta(days=10), proveedor=p2)
Compra.objects.create(insumo=aromatizante, envases=4, costo_por_envase=70, fecha=hoy - timedelta(days=10), proveedor=p2)
Compra.objects.create(insumo=limpiador_tapiz, envases=3, costo_por_envase=160, fecha=hoy - timedelta(days=5), proveedor=p1)
Compra.objects.create(insumo=microfibra, envases=20, costo_por_envase=25, fecha=hoy - timedelta(days=5), proveedor=p3)

# Costo estimado por servicio (mientras no haya historial de rendimiento real)
for insumo, costo in [(shampoo, 8), (desengrasante, 12), (cera, 15), (aromatizante, 5), (limpiador_tapiz, 18), (microfibra, 3)]:
    insumo.costo_estimado_servicio = costo
    insumo.save(update_fields=['costo_estimado_servicio'])

# ── Tipos de servicio ─────────────────────────────────────
print("Creando tipos de servicio...")
express_ext = TipoServicio.objects.create(nombre='Lavado Express Exterior', descripcion='Lavado rápido solo exterior con shampoo y enjuague')
express_comp = TipoServicio.objects.create(nombre='Lavado Completo', descripcion='Exterior e interior, aspirado y aromatizante')
motor = TipoServicio.objects.create(nombre='Detallado de Motor', descripcion='Limpieza profunda del compartimento del motor')
vestiduras = TipoServicio.objects.create(nombre='Lavado de Vestiduras', descripcion='Limpieza profunda de tapicería y alfombras')
encerado = TipoServicio.objects.create(nombre='Encerado y Pulido', descripcion='Aplicación de cera carnauba para protección y brillo')
premium = TipoServicio.objects.create(nombre='Servicio Premium Full', descripcion='Todos los servicios: exterior, interior, motor, cera y aromatizante')

# ── Tipos de vehículo ─────────────────────────────────────
print("Creando tipos de vehículo...")
moto      = TipoVehiculo.objects.create(nombre='Moto')
auto_ch   = TipoVehiculo.objects.create(nombre='Auto Pequeño')
sedan     = TipoVehiculo.objects.create(nombre='Sedán / Auto Mediano')
pickup    = TipoVehiculo.objects.create(nombre='Pick Up')
camioneta = TipoVehiculo.objects.create(nombre='Camioneta / SUV')
van       = TipoVehiculo.objects.create(nombre='Van / Minivan')
camion    = TipoVehiculo.objects.create(nombre='Camión')

# ── Precios por paquete × vehículo ─────────────────────────
print("Creando precios de paquetes...")
_precio_base = {express_ext: 80, express_comp: 150, motor: 200, vestiduras: 300, encerado: 250, premium: 500}
_multiplicador = {moto: 0.6, auto_ch: 0.9, sedan: 1.0, pickup: 1.4, camioneta: 1.5, van: 1.6, camion: 2.0}
for ts, base in _precio_base.items():
    for tv, mult in _multiplicador.items():
        PrecioPaquete.objects.create(tipo_servicio=ts, tipo_vehiculo=tv, precio=round(base * mult, 2))

# ── Productos que usa cada paquete ─────────────────────────
print("Asignando insumos a servicios...")
express_ext.insumos.add(shampoo)
express_comp.insumos.add(shampoo, aromatizante)
motor.insumos.add(desengrasante)
vestiduras.insumos.add(limpiador_tapiz)
encerado.insumos.add(cera)
premium.insumos.add(shampoo, cera, aromatizante, desengrasante)

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
        precio = round(_precio_base[ts] * _multiplicador[tv], 0)
        Servicio.objects.create(fecha=fecha, tipo_servicio=ts, tipo_vehiculo=tv, precio_cobrado=precio)

print("\n✅ Datos de demo cargados exitosamente!")
print(f"   Proveedores: {Proveedor.objects.count()}")
print(f"   Insumos: {Insumo.objects.count()}")
print(f"   Compras: {Compra.objects.count()}")
print(f"   Tipos de servicio: {TipoServicio.objects.count()}")
print(f"   Tipos de vehículo: {TipoVehiculo.objects.count()}")
print(f"   Servicios: {Servicio.objects.count()}")

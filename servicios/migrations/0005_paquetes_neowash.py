from django.db import migrations


VEHICULOS = [
    ('Autos compactos y sedanes', 1),
    ('Camioneta pick up pequeña', 2),
    ('Camioneta familiar', 3),
    ('Camioneta grande', 4),
    ('Camioneta pasajeros', 5),
]

PAQUETES = [
    (
        'Neo Express', 1,
        'Exterior: Hidro + Espuma activa + Microfibra + Secado + Brillo llantas',
        {'Autos compactos y sedanes': 80, 'Camioneta pick up pequeña': 100,
         'Camioneta familiar': 110, 'Camioneta grande': 130, 'Camioneta pasajeros': 150},
    ),
    (
        'Neo Completo', 2,
        'Exterior + Interior: Todo lo Express + Aspirado + Tablero + Cristales + Tapetes + Aromatizante',
        {'Autos compactos y sedanes': 150, 'Camioneta pick up pequeña': 170,
         'Camioneta familiar': 180, 'Camioneta grande': 200, 'Camioneta pasajeros': 230},
    ),
]


def crear_paquetes_neowash(apps, schema_editor):
    TipoServicio = apps.get_model('servicios', 'TipoServicio')
    TipoVehiculo = apps.get_model('servicios', 'TipoVehiculo')
    PrecioPaquete = apps.get_model('servicios', 'PrecioPaquete')

    # Los tipos existentes (del sistema anterior de precio base × multiplicador)
    # se desactivan en vez de borrarse, para no romper el historial de servicios ya cobrados.
    TipoServicio.objects.update(activo=False)
    TipoVehiculo.objects.update(activo=False)

    vehiculos = {}
    for nombre, orden in VEHICULOS:
        tv, _ = TipoVehiculo.objects.update_or_create(
            nombre=nombre, defaults={'orden': orden, 'activo': True}
        )
        vehiculos[nombre] = tv

    for nombre, orden, descripcion, precios in PAQUETES:
        ts, _ = TipoServicio.objects.update_or_create(
            nombre=nombre, defaults={'orden': orden, 'descripcion': descripcion, 'activo': True}
        )
        for nombre_vehiculo, precio in precios.items():
            PrecioPaquete.objects.update_or_create(
                tipo_servicio=ts, tipo_vehiculo=vehiculos[nombre_vehiculo],
                defaults={'precio': precio},
            )


def revertir(apps, schema_editor):
    TipoServicio = apps.get_model('servicios', 'TipoServicio')
    TipoVehiculo = apps.get_model('servicios', 'TipoVehiculo')
    TipoServicio.objects.filter(nombre__in=[p[0] for p in PAQUETES]).delete()
    TipoVehiculo.objects.filter(nombre__in=[v[0] for v in VEHICULOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0004_alter_tiposervicio_options_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_paquetes_neowash, revertir),
    ]

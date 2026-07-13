#!/bin/bash
# ─────────────────────────────────────────────────
#  CarWash Pro — Script de arranque
#  Doble clic en este archivo para abrir el sistema
# ─────────────────────────────────────────────────

cd "$(dirname "$0")"

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║      🚗  CarWash Pro             ║"
echo "  ║      Sistema de Gestión          ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Activar entorno virtual
source /Users/maccasa/venv/bin/activate

# Verificar que Django está disponible
python -c "import django" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "  ❌ Error: no se encontró el entorno virtual."
  echo "  Contacta al administrador del sistema."
  read -p "Presiona Enter para cerrar..."
  exit 1
fi

echo "  ✅ Sistema listo"
echo "  🌐 Abriendo en: http://localhost:8080"
echo ""
echo "  Para cerrar el sistema: cierra esta ventana"
echo "  o presiona Ctrl+C"
echo ""

# Abrir el navegador después de 2 segundos
(sleep 2 && open "http://localhost:8080") &

# Iniciar el servidor
python manage.py runserver 8080 --noreload

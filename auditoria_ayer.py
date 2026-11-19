"""
auditoria_ayer.py — Ejecución rápida de auditoría sin correr el algoritmo de pronósticos.

Uso desde PowerShell:
  py auditoria_ayer.py                    -> Audita ayer + madrugada de hoy (100% partidos -> tu Bot de Auditorías)
  py auditoria_ayer.py 2026-11-18         -> Audita una fecha exacta + madrugada siguiente (solo a tu Bot de Auditorías)
  py auditoria_ayer.py --clientes         -> Además envía la imagen oficial y texto al Canal FREE, Canal VIP y Bot de Auditorías
  py auditoria_ayer.py 2026-11-18 --clientes --sync-web -> Audita esa fecha, envía a FREE/VIP/Bot y sincroniza la Web App
"""
import os
import sys
from datetime import datetime, timedelta, timezone

if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import mercados_optimizados as m
import generador_videos_redes as g


def obtener_ahora_espana():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)


def main():
    args = [a.strip() for a in sys.argv[1:] if a.strip()]
    enviar_clientes = "--clientes" in args
    sync_web = ("--sync-web" in args) or enviar_clientes
    fechas_arg = [a for a in args if not a.startswith("--")]

    ahora_esp = obtener_ahora_espana()
    if fechas_arg:
        fecha_auditar = fechas_arg[0]
    else:
        # Si es de noche (>= 21:00h ESP), audita la jornada de hoy; de mañana/tarde, audita ayer + madrugada de hoy
        if ahora_esp.hour >= 21:
            fecha_auditar = ahora_esp.strftime("%Y-%m-%d")
        else:
            fecha_auditar = (ahora_esp - timedelta(days=1)).strftime("%Y-%m-%d")

    dt_aud = datetime.strptime(fecha_auditar, "%Y-%m-%d")
    fecha_siguiente = (dt_aud + timedelta(days=1)).strftime("%Y-%m-%d")

    api_token = os.getenv("API_SPORTS_KEY", "48f391f30e76d9c84e5c94b6a4cccdb4")
    headers = {"x-apisports-key": api_token}
    ligas_permitidas = m.obtener_ligas_permitidas_oficiales()

    print("=" * 90)
    print(f" 📊 AUDITORÍA RÁPIDA ({fecha_auditar} + MADRUGADA {fecha_siguiente})")
    print("=" * 90)

    # 1. Refrescar únicamente los marcadores FT de esa jornada y su madrugada
    m.obtener_datos_api_partidos(fecha_auditar, headers, forzar_refresco=True)
    m.resolver_apuestas_pendientes(api_token)

    # 2. Enviar Auditoría #1 (7 Tarjetas) + Auditoría #2 (100% de los partidos del día + madrugada) a tu Bot Privado
    m.auditar_todos_los_partidos_fecha_bot_auditorias(fecha_siguiente, ligas_permitidas, headers, api_token)
    print(f"✅ Reporte 100% completo ({fecha_auditar} + madrugada {fecha_siguiente}) enviado a tu Bot de Auditorías.")

    # 3. Si se pide --clientes (ej. disparo nocturno 23:15h o manual), enviar imagen + texto a Bot, Canal FREE y Canal VIP
    if enviar_clientes:
        g.publicar_auditoria_nocturna_canal_free(fecha_auditar)

    # 4. Sincronizar CSV y cachés con la Web App en GitHub (cuando se corre desde tu PC)
    if sync_web and not os.getenv("GITHUB_ACTIONS"):
        m.actualizar_webapp_github_automatico(fecha_auditar)

    print("🏁 Auditoría rápida finalizada sin tocar los partidos futuros.")


if __name__ == "__main__":
    main()

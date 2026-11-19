"""
auditoria_ayer.py — Ejecución rápida de auditoría sin correr el algoritmo de pronósticos.

Uso desde PowerShell:
  py auditoria_ayer.py                       -> Envía a TU BOT DE AUDITORÍAS: la imagen vertical + texto de las 7 tarjetas VIP/FREE y el reporte exacto del CSV (sin enviar a clientes).
  py auditoria_ayer.py 2026-11-18            -> Lo mismo para una fecha específica + su madrugada (solo para ti).
  py auditoria_ayer.py --clientes            -> Envía la imagen vertical + textos respectivos a TU BOT, CANAL FREE y CANAL VIP + actualiza Web.
  py auditoria_ayer.py 2026-11-18 --clientes -> Envía ahora mismo la imagen + texto oficial del día 18 + madrugada del 19 a TU BOT, CANAL FREE y CANAL VIP + actualiza Web.
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
    if "--noche" in args:
        modo_horario = "noche"
    elif "--manana" in args:
        modo_horario = "manana"
    else:
        modo_horario = "noche" if ahora_esp.hour >= 21 else "manana"

    if fechas_arg:
        fecha_auditar = fechas_arg[0]
    else:
        if modo_horario == "noche":
            fecha_auditar = ahora_esp.strftime("%Y-%m-%d")
        else:
            fecha_auditar = (ahora_esp - timedelta(days=1)).strftime("%Y-%m-%d")

    dt_aud = datetime.strptime(fecha_auditar, "%Y-%m-%d")
    fecha_siguiente = (dt_aud + timedelta(days=1)).strftime("%Y-%m-%d")

    api_token = os.getenv("API_SPORTS_KEY", "48f391f30e76d9c84e5c94b6a4cccdb4")
    headers = {"x-apisports-key": api_token}
    ligas_permitidas = m.obtener_ligas_permitidas_oficiales()

    print("=" * 90)
    print(f" 📊 AUDITORÍA RÁPIDA ({fecha_auditar} + MADRUGADA {fecha_siguiente}) | MODO: {modo_horario.upper()} | CLIENTES: {'SÍ' if enviar_clientes else 'SOLO PRIVADO'}")
    print("=" * 90)

    # 1. Refrescar únicamente marcadores FT de esa jornada y su madrugada, y resolver pendientes en CSV (sin modificar apuestas pasadas)
    m.obtener_datos_api_partidos(fecha_auditar, headers, forzar_refresco=True)
    m.resolver_apuestas_pendientes(api_token)

    # 2. Enviar SIEMPRE la imagen vertical oficial + texto (estilo auditoría de 7 tarjetas VIP/FREE)
    #    - Si enviar_clientes=False -> solo a tu Bot de Auditorías y tu Chat Privado
    #    - Si enviar_clientes=True  -> a tu Bot de Auditorías, Chat Privado, Canal FREE y Canal VIP (con textos separados)
    g.publicar_auditoria_nocturna_canal_free(
        fecha_auditar,
        enviar_a_clientes=enviar_clientes,
        modo_horario=modo_horario,
    )

    # 3. Enviar a tu Bot Privado el desglose fiel en texto (AUDITORÍA #1 + AUDITORÍA #2 leyendo 100% del CSV sin recalcular nada)
    m.auditar_todos_los_partidos_fecha_bot_auditorias(fecha_siguiente, ligas_permitidas, headers, api_token)
    print(f"✅ Reporte exacto del CSV ({fecha_auditar} + madrugada {fecha_siguiente}) enviado a tu Bot de Auditorías.")

    # 4. Sincronizar CSV y cachés con la Web App en GitHub (cuando se corre desde tu PC)
    if sync_web and not os.getenv("GITHUB_ACTIONS"):
        m.actualizar_webapp_github_automatico(fecha_auditar)

    print("🏁 Auditoría rápida finalizada al 100%.")


if __name__ == "__main__":
    main()

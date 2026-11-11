import csv
from datetime import datetime
import json
import logging
import os
import re
import time
import pandas as pd
import requests

# ==============================================================================
# CONFIGURACIÓN DEL BOT DE SOPORTE 24/7 + AUDITORÍA + PUENTE ANÓNIMO MULTIMEDIA
# ==============================================================================
TOKEN_SOPORTE = "8772561913:AAHktSUiEvSJ8z3uj-l4pam9Fkg2GCdddrM"
TOKEN_GENERAL = "8980476304:AAHloqUSHMgQddi2eupz6FjrqliVDi6BDzQ"
TOKEN_VIP_PERSONAL = "8912732307:AAFG9S1FjNfSGugySoBduyjWb03kf38a63o"
TOKEN_TICKETS = "8805035408:AAGPYUxmFz-Spfum1P2vacMZz5bToXUPMWI"

ADMIN_CHAT_ID = "1491740882"
CHAT_ID_TICKETS = "1491740882"

LINK_PASARELA_VIP = "https://whop.com/youtube-d4c7/quantbet22-canal-vip/"
LINK_PASARELA_PRO = "https://whop.com/youtube-d4c7/products/uantbet22-membresia-pro-avanzada/?ref=related_products"
LINK_CANAL_FREE = "https://t.me/+aYoc_N6oiU1lODU0"

ARCHIVO_CSV_AUDITORIA = "auditoria_apuestas.csv"
ARCHIVO_MEMORIA_BOTONES = "memoria_botones.json"

COLUMNAS_OFICIALES_CSV = [
    "Fecha_Registro",
    "ID_Partido",
    "Partido",
    "Mercado",
    "Cuota_Compra",
    "Cuota_Cierre_CLV",
    "Probabilidad",
    "Semaforo",
    "Stake_COP",
    "Estado",
    "Retorno_COP",
    "CLV_Status",
]

logging.basicConfig(
    filename="soporte_empresa.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
)

URL_SOPORTE = f"https://api.telegram.org/bot{TOKEN_SOPORTE}"
mapa_mensajes_clientes = {}
seguimiento_10_min = {}


# ==============================================================================
# 1. REPARADOR AUTOMÁTICO DE CSV Y AUDITORÍA INSTANTÁNEA DE BOTONES
# ==============================================================================
def reparar_y_leer_csv_auditoria():
    if not os.path.exists(ARCHIVO_CSV_AUDITORIA):
        with open(ARCHIVO_CSV_AUDITORIA, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNAS_OFICIALES_CSV)
        return pd.DataFrame(columns=COLUMNAS_OFICIALES_CSV)

    filas_limpias = []
    try:
        with open(ARCHIVO_CSV_AUDITORIA, "r", encoding="utf-8", errors="replace") as f:
            lector = csv.reader(f)
            for idx, fila in enumerate(lector):
                if not fila:
                    continue
                if idx == 0 and ("Fecha" in fila[0] or "Partido" in str(fila)):
                    continue
                if len(fila) == 10:
                    fila_12 = [
                        fila[0], fila[1], fila[2], fila[3], fila[4],
                        "PENDIENTE_CLV", fila[5], fila[6], fila[7],
                        fila[8], fila[9], "AUDITANDO"
                    ]
                    filas_limpias.append(fila_12)
                elif len(fila) >= 12:
                    filas_limpias.append(fila[:12])
                elif len(fila) == 11:
                    filas_limpias.append(fila + ["AUDITANDO"])

        with open(ARCHIVO_CSV_AUDITORIA, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNAS_OFICIALES_CSV)
            writer.writerows(filas_limpias)

        return pd.read_csv(ARCHIVO_CSV_AUDITORIA)
    except Exception as e:
        logging.error(f"Error reparando CSV auditoría: {e}")
        return pd.DataFrame(columns=COLUMNAS_OFICIALES_CSV)


def inicializar_csv_auditoria():
    reparar_y_leer_csv_auditoria()


def calcular_stake_kelly(prob_pct, cuota_compra, bankroll_actual=100000.0):
    if prob_pct is None or cuota_compra <= 1.0:
        return 500.0
    p = prob_pct / 100.0
    q = 1.0 - p
    b = cuota_compra - 1.0
    if b <= 0:
        return 500.0
    kelly_fraction = (b * p - q) / b
    if kelly_fraction <= 0:
        return 500.0
    mult = 0.25 if cuota_compra < 1.80 else (0.15 if cuota_compra < 2.50 else 0.08)
    stake_sug = bankroll_actual * kelly_fraction * mult
    return max(500.0, round(min(stake_sug, bankroll_actual * 0.05), -2))


def cargar_memoria_botones():
    if os.path.exists(ARCHIVO_MEMORIA_BOTONES):
        try:
            with open(ARCHIVO_MEMORIA_BOTONES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_memoria_botones(datos):
    try:
        with open(ARCHIVO_MEMORIA_BOTONES, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error guardando memoria botones: {e}")


def registrar_apuesta_instantanea(info):
    reparar_y_leer_csv_auditoria()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cuota_num = float(info["cuota"])
    prob_num = float(info["prob"]) if info["prob"] != "N/A" else 68.0
    mercado_str = str(info["mercado"])
    partido_str = str(info["partido"])
    semaforo = str(info.get("semaforo", "🟢"))
    soporte = str(info.get("soporte", "Análisis Cuantitativo"))

    stake = calcular_stake_kelly(prob_num, cuota_num)

    with open(ARCHIVO_CSV_AUDITORIA, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            fecha_hoy, info["id_partido"], partido_str, mercado_str,
            cuota_num, "PENDIENTE_CLV", prob_num, semaforo,
            stake, "Pendiente", 0, "AUDITANDO"
        ])

    print(f"\n[AUDITORÍA EN VIVO] ✅ Guardada desde tu dispositivo: {partido_str} | {mercado_str} | Cuota: {cuota_num}")

    ticket = (
        f"🎟️ <b>TICKET OFICIAL AUDITADO (KELLY + CLV)</b> 🎟️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏟 <b>{partido_str}</b>\n\n"
        f"🎯 <b>SELECCIÓN:</b> {mercado_str}\n"
        f"📊 <b>Probabilidad Modelo:</b> {prob_num}%\n"
        f"💵 <b>Precio Mínimo Entrada:</b> > {cuota_num}\n"
        f"💰 <b>Stake Dinámico (Kelly):</b> ${stake:,.0f} COP\n\n"
        f"<i>💡 Contexto: {soporte}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN_TICKETS}/sendMessage",
            json={"chat_id": CHAT_ID_TICKETS, "text": ticket, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception as e:
        logging.error(f"Error enviando ticket oficial: {e}")


def marcar_boton_presionado(token, callback_id, chat_id, message_id, cb_data_pulsado, teclado_actual, nombre_mercado):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/answerCallbackQuery",
            json={
                "callback_query_id": callback_id,
                "text": f"✅ Registrada en auditoria_apuestas.csv: {nombre_mercado}",
                "show_alert": True,
            },
            timeout=5,
        )
        nuevas_filas = []
        for fila in teclado_actual.get("inline_keyboard", []):
            nueva_fila = []
            for boton in fila:
                if boton.get("callback_data") == cb_data_pulsado:
                    nueva_fila.append({
                        "text": f"✅ REGISTRADA: {nombre_mercado}",
                        "callback_data": "ya_registrada"
                    })
                else:
                    nueva_fila.append(boton)
            nuevas_filas.append(nueva_fila)

        requests.post(
            f"https://api.telegram.org/bot{token}/editMessageReplyMarkup",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": {"inline_keyboard": nuevas_filas},
            },
            timeout=5,
        )
    except Exception as e:
        logging.error(f"Error actualizando botón de auditoría: {e}")


# ==============================================================================
# 2. PUENTE ANÓNIMO BIDIRECCIONAL Y MENÚ DE CONVERSIÓN
# ==============================================================================
def enviar_mensaje_soporte(chat_id, texto, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(f"{URL_SOPORTE}/sendMessage", json=payload, timeout=8)
        return res.json()
    except Exception as e:
        logging.error(f"Error enviando mensaje soporte: {e}")
        return {}


def extraer_id_cliente_de_mensaje(msg_respondido):
    """Extrae el ID del cliente incluso si el bot se reinició."""
    id_msg = msg_respondido.get("message_id")
    if id_msg in mapa_mensajes_clientes:
        return mapa_mensajes_clientes[id_msg]
    texto_base = str(msg_respondido.get("text") or msg_respondido.get("caption") or "")
    m = re.search(r"ID(?:\s*Cliente)?:\s*(\d+)", texto_base)
    if m:
        return m.group(1)
    return None


def notificar_radar_admin(chat_id_cliente, nombre, username, accion):
    if str(chat_id_cliente) == ADMIN_CHAT_ID:
        return
    aviso = (
        f"👀 <b>[RADAR DE CLIENTES EN VIVO]</b>\n"
        f"👤 <b>Usuario:</b> {nombre} ({username})\n"
        f"🆔 <b>ID Cliente:</b> <code>{chat_id_cliente}</code>\n"
        f"⚡ <b>Acción:</b> {accion}\n\n"
        f"<i>↩️ Desliza este mensaje hacia la izquierda (Responder / Reply) para escribirle tú directamente desde el bot de forma 100% anónima.</i>"
    )
    res = enviar_mensaje_soporte(ADMIN_CHAT_ID, aviso)
    if res.get("ok"):
        id_msg_admin = res["result"]["message_id"]
        mapa_mensajes_clientes[id_msg_admin] = str(chat_id_cliente)


def menu_principal():
    return {
        "inline_keyboard": [
            [{"text": "🎁 Prueba 24h ($1) + Pase 10 Días ($7.99) | Pase 3 Días ($4.99)", "callback_data": "info_planes"}],
            [{"text": "🇨🇴 🇪🇸 Pagar por Nequi / Bancolombia / Bizum / USDT", "callback_data": "pago_local"}],
            [{"text": "🎟️ Tengo un Código de Descuento (Ej: DARMANI)", "callback_data": "codigo_descuento"}],
            [{"text": "✅ Ya realicé el pago / Enviar Comprobante", "callback_data": "ya_pague"}],
            [{"text": "💬 Hablar con un Analista de Soporte", "callback_data": "hablar_humano"}],
        ]
    }


def verificar_seguimientos_10_minutos():
    ahora = time.time()
    for cid, datos in list(seguimiento_10_min.items()):
        if not datos.get("enviado") and (ahora - datos["tiempo_inicio"]) >= 600:
            nombre = datos.get("nombre", "amigo")
            msg_auto = (
                f"👋 ¡Hola de nuevo, <b>{nombre}</b>! 😊\n\n"
                f"Vi que estuviste revisando nuestras opciones en <b>QuantBet22</b>. "
                f"Recuerda que puedes probar <b>24 horas VIP por solo 1.00 USD</b> (o el Pase de 3 Días por 4.99 USD), "
                f"y si tienes un código de referido (como <b>DARMANI</b>) recibes un descuento especial en tu primer acceso.\n\n"
                f"🤝 <i>Escríbeme por aquí cualquier duda que tengas y te ayudo enseguida.</i>"
            )
            enviar_mensaje_soporte(cid, msg_auto, reply_markup=menu_principal())
            datos["enviado"] = True


# ==============================================================================
# 3. BUCLE MAESTRO 24/7
# ==============================================================================
def ejecutar_centro_operaciones():
    reparar_y_leer_csv_auditoria()
    offset_soporte = 0
    offset_general = 0
    print("\n" + "=" * 100)
    print(" 🤖 CENTRO DE OPERACIONES 24/7 ACTIVO (@QuantBetSoporte_bot)")
    print("    • Todos los mensajes y fotos de clientes te llegan a tu Telegram privado.")
    print("    • Para responder de forma anónima, solo dale a 'Responder' (Reply) al mensaje en tu móvil.")
    print("=" * 100 + "\n")

    while True:
        try:
            verificar_seguimientos_10_minutos()
        except Exception as e:
            logging.error(f"Error en seguimiento 10 min: {e}")

        try:
            res_s = requests.get(f"{URL_SOPORTE}/getUpdates?offset={offset_soporte}&timeout=2", timeout=5).json()
            for update in res_s.get("result", []):
                offset_soporte = update["update_id"] + 1

                if "callback_query" in update:
                    cb = update["callback_query"]
                    chat_id = str(cb["message"]["chat"]["id"])
                    nombre = cb["from"].get("first_name", "Amigo")
                    username = f"@{cb['from'].get('username')}" if cb["from"].get("username") else "Sin usuario"
                    data = cb.get("data", "")
                    requests.post(f"{URL_SOPORTE}/answerCallbackQuery", json={"callback_query_id": cb["id"]}, timeout=5)

                    if chat_id != ADMIN_CHAT_ID:
                        seguimiento_10_min[chat_id] = {
                            "nombre": nombre,
                            "tiempo_inicio": time.time(),
                            "toco_boton": True,
                            "ultimo_boton": data,
                            "enviado": False,
                        }

                    if data == "info_planes":
                        notificar_radar_admin(chat_id, nombre, username, "Consultó planes VIP (3 días / 10 días / Mes) y PRO")
                        txt = (
                            "🚀 <b>PLANES OFICIALES QUANTBET22 (ACCESO INMEDIATO)</b> 🚀\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "⚡ <b>1. PASE 3 DÍAS FECHA FIFA / FIN DE SEMANA (4.99 USD)</b>\n"
                            "• Pago único sin suscripción recurrente (72 horas de acceso VIP total).\n\n"
                            "🔥 <b>2. PRUEBA 24H (1.00 USD) + PASE 10 DÍAS VIP (7.99 USD)</b>\n"
                            "• 4 Tarjetas VIP diarias + Combinada Doble VIP + Soporte 24/7.\n"
                            f"👉 <a href='{LINK_PASARELA_VIP}'><b>HAZ CLIC AQUÍ PARA ELEGIR TU PLAN VIP EN WHOP</b></a>\n\n"
                            "👑 <b>3. PROMO PRO CIERRE DE AÑO (49.99 USD en vez de 74.99 USD)</b>\n"
                            "• 100% de los partidos de todas las ligas + Combinada Triple Sniper PRO.\n"
                            f"👉 <a href='{LINK_PASARELA_PRO}'><b>HAZ CLIC AQUÍ PARA ACTIVAR EL PLAN PRO</b></a>"
                        )
                        enviar_mensaje_soporte(chat_id, txt, reply_markup=menu_principal())

                    elif data == "pago_local":
                        notificar_radar_admin(chat_id, nombre, username, "🔥 Quiere pagar por Nequi / Bancolombia / Bizum / USDT")
                        txt = (
                            "🇨🇴 🇪🇸 <b>PAGOS LOCALES DIRECTOS (NEQUI / BANCOLOMBIA / BIZUM / USDT)</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "Puedes activar cualquiera de nuestros pases sin tarjeta internacional:\n"
                            "• ⚡ <b>Pase 3 Días VIP:</b> 4.99 USD (20.000 COP / 4.50 EUR)\n"
                            "• 🔥 <b>Pase 10 Días VIP:</b> 7.99 USD (32.000 COP / 7.50 EUR)\n"
                            "• 💎 <b>Mes Completo VIP:</b> 24.99 USD (98.000 COP / 23 EUR)\n"
                            "• 👑 <b>Promo PRO Cierre de Año:</b> 49.99 USD (195.000 COP / 46 EUR)\n\n"
                            "✍️ <b>Escribe aquí abajo qué método prefieres (Nequi, Bancolombia, Bizum o USDT) y si tienes un código de descuento</b> para pasarte el dato exacto de transferencia al instante:"
                        )
                        enviar_mensaje_soporte(chat_id, txt)

                    elif data == "codigo_descuento":
                        notificar_radar_admin(chat_id, nombre, username, "🎟️ Pulsó 'Tengo un Código de Descuento'")
                        txt = (
                            "🎟️ <b>CÓDIGO DE DESCUENTO EN TU PRIMERA COMPRA</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "• Si pagas con tarjeta en <b>Whop</b>, solo introduce tu código (por ejemplo: <b>DARMANI</b>) en la casilla <i>'Add promo code'</i> antes de pagar y se te descontará automáticamente.\n\n"
                            "• Si vas a pagar por <b>Nequi, Bancolombia, Bizum o USDT</b>, escribe aquí abajo el código del creador de parte de quien vienes para aplicarte el descuento en tu primer acceso:"
                        )
                        enviar_mensaje_soporte(chat_id, txt)

                    elif data == "ya_pague":
                        notificar_radar_admin(chat_id, nombre, username, "✅ Pulsó 'Ya realicé el pago / Enviar Comprobante'")
                        txt = (
                            "✅ <b>VERIFICACIÓN DE PAGO Y ACCESO INMEDIATO</b>\n\n"
                            "Por favor, <b>envía por aquí mismo la foto o captura de tu comprobante de pago</b> (o tu correo si pagaste en Whop) y te enviaremos tu enlace único de acceso en menos de 2 minutos:"
                        )
                        enviar_mensaje_soporte(chat_id, txt)

                    elif data == "hablar_humano":
                        notificar_radar_admin(chat_id, nombre, username, "💬 Pulsó 'Hablar con un Analista de Soporte'")
                        enviar_mensaje_soporte(
                            chat_id,
                            "🤝 <b>ATENCIÓN PERSONALIZADA QUANTBET22</b>\n\nEscribe tu consulta o mensaje aquí abajo y un analista de nuestro equipo te responderá personalmente por este mismo chat:"
                        )

                elif "message" in update:
                    msg = update["message"]
                    chat_id = str(msg["chat"]["id"])
                    texto = msg.get("text") or msg.get("caption") or ""
                    nombre = msg["from"].get("first_name", "Amigo")
                    username = f"@{msg['from'].get('username')}" if msg["from"].get("username") else "Sin usuario"

                    # A. SI TÚ (ADMIN) RESPONDES DESLIZANDO EL MENSAJE EN TU TELEGRAM:
                    if chat_id == ADMIN_CHAT_ID and "reply_to_message" in msg:
                        cliente_destino = extraer_id_cliente_de_mensaje(msg["reply_to_message"])
                        if cliente_destino:
                            if cliente_destino in seguimiento_10_min:
                                seguimiento_10_min[cliente_destino]["enviado"] = True
                            enviar_mensaje_soporte(
                                cliente_destino,
                                f"👨‍💻 <b>Soporte Oficial QuantBet22:</b>\n\n{texto}",
                                reply_markup=menu_principal()
                            )
                            enviar_mensaje_soporte(ADMIN_CHAT_ID, f"✅ <i>Respuesta enviada de forma anónima a ID {cliente_destino}.</i>")
                        else:
                            enviar_mensaje_soporte(ADMIN_CHAT_ID, "⚠️ <i>No se encontró el ID del cliente en ese mensaje.</i>")
                        continue

                    # B. SI EL CLIENTE INICIA EL BOT (/start)
                    if texto.startswith("/start"):
                        if chat_id != ADMIN_CHAT_ID:
                            seguimiento_10_min[chat_id] = {
                                "nombre": nombre,
                                "tiempo_inicio": time.time(),
                                "toco_boton": False,
                                "ultimo_boton": "Inicio",
                                "enviado": False,
                            }
                        notificar_radar_admin(chat_id, nombre, username, "Inició el Bot de Soporte (/start)")
                        bienvenida = (
                            f"👋 ¡Hola <b>{nombre}</b>! Bienvenido al Centro de Atención de <b>QuantBet22</b> 🤝.\n\n"
                            "Selecciona una opción aquí abajo para ver nuestros pases, activar un código de descuento o pagar por Nequi / Bizum / USDT:"
                        )
                        enviar_mensaje_soporte(chat_id, bienvenida, reply_markup=menu_principal())

                    # C. SI EL CLIENTE ESCRIBE CUALQUIER PREGUNTA O ENVÍA FOTO DE COMPROBANTE
                    elif chat_id != ADMIN_CHAT_ID:
                        if chat_id in seguimiento_10_min:
                            seguimiento_10_min[chat_id]["enviado"] = True

                        aviso_admin = (
                            f"📩 <b>NUEVO MENSAJE DE CLIENTE</b>\n"
                            f"👤 <b>Nombre:</b> {nombre} ({username})\n"
                            f"🆔 <b>ID Cliente:</b> <code>{chat_id}</code>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"💬 <b>Mensaje:</b> {texto if texto else '[Envió una foto / comprobante]'}\n\n"
                            f"<i>↩️ Desliza este mensaje (Responder/Reply) para contestarle de forma anónima.</i>"
                        )

                        # Si el cliente envió una foto (comprobante Nequi/Bizum), enviarte la FOTO directamente a tu Telegram
                        if "photo" in msg and len(msg["photo"]) > 0:
                            file_id_foto = msg["photo"][-1]["file_id"]
                            res_f = requests.post(
                                f"{URL_SOPORTE}/sendPhoto",
                                json={"chat_id": ADMIN_CHAT_ID, "photo": file_id_foto, "caption": aviso_admin, "parse_mode": "HTML"},
                                timeout=10
                            ).json()
                            if res_f.get("ok"):
                                mapa_mensajes_clientes[res_f["result"]["message_id"]] = chat_id
                        elif "document" in msg:
                            file_id_doc = msg["document"]["file_id"]
                            res_d = requests.post(
                                f"{URL_SOPORTE}/sendDocument",
                                json={"chat_id": ADMIN_CHAT_ID, "document": file_id_doc, "caption": aviso_admin, "parse_mode": "HTML"},
                                timeout=10
                            ).json()
                            if res_d.get("ok"):
                                mapa_mensajes_clientes[res_d["result"]["message_id"]] = chat_id
                        else:
                            res_envio = enviar_mensaje_soporte(ADMIN_CHAT_ID, aviso_admin)
                            if res_envio.get("ok"):
                                mapa_mensajes_clientes[res_envio["result"]["message_id"]] = chat_id

                        enviar_mensaje_soporte(
                            chat_id,
                            "✅ <b>¡Mensaje recibido!</b> Un analista de nuestro equipo ya lo está revisando y te responderá por este mismo chat en unos instantes."
                        )
        except Exception as e:
            logging.error(f"Error en bucle soporte: {e}")

        try:
            url_gen = f"https://api.telegram.org/bot{TOKEN_GENERAL}/getUpdates?offset={offset_general}&timeout=1"
            res_g = requests.get(url_gen, timeout=4).json()
            for update in res_g.get("result", []):
                offset_general = update["update_id"] + 1
                if "callback_query" in update:
                    cb = update["callback_query"]
                    cb_id = cb["id"]
                    cb_data = cb.get("data", "")
                    msg = cb.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    message_id = msg.get("message_id")
                    teclado_actual = msg.get("reply_markup", {})

                    if cb_data == "ya_registrada":
                        requests.post(
                            f"https://api.telegram.org/bot{TOKEN_GENERAL}/answerCallbackQuery",
                            json={"callback_query_id": cb_id, "text": "⚠️ Esta apuesta ya fue registrada en el CSV.", "show_alert": False},
                            timeout=4,
                        )
                        continue

                    memoria = cargar_memoria_botones()
                    if cb_data in memoria:
                        info = memoria[cb_data]
                        registrar_apuesta_instantanea(info)
                        marcar_boton_presionado(
                            TOKEN_GENERAL, cb_id, chat_id, message_id,
                            cb_data, teclado_actual, info["mercado"]
                        )
                        del memoria[cb_data]
                        guardar_memoria_botones(memoria)
        except Exception as e:
            logging.error(f"Error en bucle auditoría botones: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    ejecutar_centro_operaciones()
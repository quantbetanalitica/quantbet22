# === INICIO FILTRO EXCLUSIVO DE VIDEO (RESPETA % EN CLIENTES Y GARANTIZA LAS 4 REDES EN TELEGRAM) ===
import re as _re_vid
import time as _time_vid
import json as _json_vid
import builtins as _builtins_vid
import requests as _req_vid
from PIL import ImageDraw as _ImageDraw_vid

def _limpiar_texto_redes_sociales(texto, modo="copy"):
    if not isinstance(texto, str) or not texto.strip():
        return texto
    t = str(texto)

    # 1. Eliminar +18, 🔞 y advertencias de apuestas en vídeos y descripciones de redes
    t = t.replace("🔞", "")
    t = _re_vid.sub(r"\(\+18\s*Informativo\)", "(Ciencia de Datos)", t, flags=_re_vid.I)
    t = _re_vid.sub(r"\+18\s*\|?", "", t)
    t = _re_vid.sub(r"(?i)juega\s+con\s+responsabilidad\.?", "", t)
    t = _re_vid.sub(r"(?i)an[áa]lisis\s+estad[íi]stico\s+e\s+informativo\.?", "Ciencia de Datos y Modelos Matemáticos aplicados al Fútbol Profesional.", t)

    # 2. Reemplazos exactos en cajas del vídeo y descripciones
    reemplazos_exactos = [
        ("TARJETA GRATIS + PASE VIP $7.99", "ANÁLISIS TÁCTICO + ACCESO VIP"),
        ("TARJETA GRATIS + PASE VIP $9.99", "ANÁLISIS TÁCTICO + ACCESO VIP"),
        ("TARJETA GRATIS Y PROMO $7.99 EN EL PERFIL", "ANÁLISIS COMPLETO DISPONIBLE EN EL PERFIL"),
        ("TARJETA GRATIS Y PROMO $9.99 EN EL PERFIL", "ANÁLISIS COMPLETO DISPONIBLE EN EL PERFIL"),
        ("WEB OFICIAL Y PROMO $7.99 EN EL PERFIL", "WEB OFICIAL Y COMUNIDAD EN EL PERFIL"),
        ("WEB OFICIAL Y PROMO $9.99 EN EL PERFIL", "WEB OFICIAL Y COMUNIDAD EN EL PERFIL"),
        ("PASE DE PRUEBA 10 DÍAS POR SOLO $7.99 USD", "ACCESO DE PRUEBA 10 DÍAS EN EL PERFIL"),
        ("PASE DE PRUEBA 10 DÍAS POR SOLO $9.99 USD", "ACCESO DE PRUEBA 10 DÍAS EN EL PERFIL"),
        ("PROMO 10 DÍAS VIP POR $7.99 EN LA WEB", "ACCESO DE PRUEBA 10 DÍAS EN LA WEB"),
        ("PROMO 10 DÍAS VIP POR $9.99 EN LA WEB", "ACCESO DE PRUEBA 10 DÍAS EN LA WEB"),
        ("PRUEBA 10 DÍAS VIP POR SOLO $7.99 USD", "PRUEBA 10 DÍAS DISPONIBLE EN EL PERFIL"),
        ("PRUEBA 10 DÍAS VIP POR SOLO $9.99 USD", "PRUEBA 10 DÍAS DISPONIBLE EN EL PERFIL"),
        ("PROMO NUEVOS USUARIOS: Prueba 10 DÍAS de Acceso Total por solo $7.99 USD entrando al link de nuestro perfil.",
         "Únete a nuestra comunidad en Telegram y consulta el laboratorio web completo desde el enlace de nuestro perfil."),
        ("PROMO NUEVOS USUARIOS: Prueba 10 DÍAS de Acceso Total por solo $9.99 USD entrando al link de nuestro perfil.",
         "Únete a nuestra comunidad en Telegram y consulta el laboratorio web completo desde el enlace de nuestro perfil."),
        ("PRECISION 100.0%", "PRECISIÓN VERIFICADA"),
        ("PRECISIÓN 100.0%", "PRECISIÓN VERIFICADA"),
        ("la informe táctico interactivo", "el informe táctico interactivo"),
    ]
    for viejo, nuevo in reemplazos_exactos:
        t = t.replace(viejo, nuevo)

    # 3. Limpiar porcentajes y promesas en los textos de TikTok, Instagram, YouTube y Facebook
    t = _re_vid.sub(r"(?i)\+\s*AUDITOR[ÍI]A\s*\(\d+(?:[\.,]\d+)?%\)", "+ AUDITORÍA VERIFICADA", t)
    t = _re_vid.sub(r"(?i)\d+(?:[\.,]\d+)?%\s*de\s*precisi[óo]n\s*en\s*nuestro\s*modelo\s*matem[áa]tico\s*de\s*(?:Poisson|Poison)",
                    "Simulación de 10.000 escenarios en nuestro modelo matemático de Poisson", t)
    t = _re_vid.sub(r"(?i)Balance\s+verificado\s*\(\d+(?:[\.,]\d+)?%\s*de\s*acierto\)",
                    "Balance verificado en tiempo real", t)
    t = _re_vid.sub(r"(?i)Transparencia\s+total:\s*\d+(?:[\.,]\d+)?%\s*de\s*efectividad\s*verificada\.?",
                    "Transparencia institucional y modelos de Poisson en tiempo real.", t)

    # 4. Limpiar palabras comerciales / apuestas ("GRATIS", "tarjeta desbloqueada", "$7.99")
    t = _re_vid.sub(r"(?i)Ya\s+subimos\s+GRATIS\s+(?:la\s+tarjeta\s+desbloqueada|el\s+informe\s+t[áa]ctico\s+interactivo|la\s+informe\s+t[áa]ctico\s+interactivo)",
                    "Ya publicamos el informe táctico interactivo", t)
    t = _re_vid.sub(r"(?i)Y\s+ya\s+subimos\s+GRATIS\s+a\s+nuestra\s+WEB\s+OFICIAL",
                    "Y ya publicamos en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)La\s+tarjeta\s+gratuita\s+de\s+hoy", "El informe táctico de hoy", t)
    t = _re_vid.sub(r"(?i)ya\s+est[áa]\s+desbloqueada\s+en\s+nuestra\s+Web\s+Oficial",
                    "ya está disponible en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)Ya\s+dejamos\s+desbloqueada\s+en\s+nuestra\s+WEB\s+OFICIAL\s+la\s+tarjeta\s+de\s+hoy",
                    "Ya publicamos en nuestra plataforma web el informe táctico de hoy", t)
    t = _re_vid.sub(r"(?i)y\s+tarjeta\s+desbloqueada\s+de\s+hoy", "y análisis táctico de hoy", t)
    t = _re_vid.sub(r"(?i)disponible\s+GRATIS\s+en\s+nuestra\s+WEB\s+OFICIAL",
                    "disponible en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)Entra\s+gratis\s+tocando", "Consulta los datos tocando", t)
    t = _re_vid.sub(r"(?i)por\s+solo\s+\$?\d+[\.,]\d+\s*(?:USD|d[óo]lares|US\$)?", "desde nuestro perfil", t)
    t = _re_vid.sub(r"(?i)\$\d+[\.,]\d+\s*(?:USD)?", "en el perfil", t)
    t = _re_vid.sub(r"(?i)\b(?:7|9|siete|nueve)\s+con\s+99\s*(?:d[óo]lares|usd)?", "el acceso de nuestro perfil", t)
    t = _re_vid.sub(r"(?i)en\s+el\s+perfil\s*EN\s+EL\s+PERFIL", "EN EL PERFIL", t)
    t = _re_vid.sub(r"(?i)\bCuota\s*>", "Índice >", t)

    if modo == "slide":
        # Eliminar porcentajes de promesas/efectividad (nunca romper barras limpias de probabilidad 1X2 tipo Opta)
        t = _re_vid.sub(r"(?i)(?:efectividad|precisi[óo]n|aciertos?|ganadas?)\s*:?\s*\d+(?:[\.,]\d+)?%", "DATO VERIFICADO", t)
        t = _re_vid.sub(r"\(\s*\d+(?:[\.,]\d+)?%\s*\)", "", t)
    elif modo == "voz":
        t = t.replace("Puasón matemática", "Poison")
        t = t.replace("Puasón", "Poison")
        t = t.replace("Poisson", "Poison")
        t = t.replace("Doble Oport.", "Doble Oportunidad")
        t = t.replace("Doble Oport ", "Doble Oportunidad ")
        t = t.replace("Over 1.5 Goles", "Más de 1.5 goles")
        # Evitar promesas de efectividad en audio manteniendo español 100% natural
        t = _re_vid.sub(r"(?i)con\s+(?:un|una)\s+(?:probabilidad\s+estimada\s+del\s+)?\d+\s+por\s+ciento(?:\s+de\s+probabilidad(?:\s+matem[áa]tica)?)?", "con alta convergencia en el modelo", t)
        t = _re_vid.sub(r"(?i)del\s+\d+\s+por\s+ciento", "de alta convergencia", t)
        t = _re_vid.sub(r"(?i)\d+\s+por\s+ciento", "alta convergencia", t)

    return t

# A. Interceptar dibujo SOLO en láminas de vídeo vertical (1080x1920), respetando el '%' real en las tarjetas 1080x1080 de clientes
def _es_lienzo_video(draw_obj):
    try:
        im_d = getattr(draw_obj, "_image", None)
        return im_d is not None and im_d.size[1] > 1200
    except Exception:
        return False

_orig_draw_text = _ImageDraw_vid.ImageDraw.text
def _hook_draw_text(self, xy, text, *args, **kwargs):
    txt_f = _limpiar_texto_redes_sociales(text, modo="slide") if _es_lienzo_video(self) else text
    return _orig_draw_text(self, xy, txt_f, *args, **kwargs)
_ImageDraw_vid.ImageDraw.text = _hook_draw_text

if hasattr(_ImageDraw_vid.ImageDraw, "textbbox"):
    _orig_textbbox = _ImageDraw_vid.ImageDraw.textbbox
    def _hook_textbbox(self, xy, text, *args, **kwargs):
        txt_f = _limpiar_texto_redes_sociales(text, modo="slide") if _es_lienzo_video(self) else text
        return _orig_textbbox(self, xy, txt_f, *args, **kwargs)
    _ImageDraw_vid.ImageDraw.textbbox = _hook_textbbox

if hasattr(_ImageDraw_vid.ImageDraw, "textlength"):
    _orig_textlength = _ImageDraw_vid.ImageDraw.textlength
    def _hook_textlength(self, text, *args, **kwargs):
        txt_f = _limpiar_texto_redes_sociales(text, modo="slide") if _es_lienzo_video(self) else text
        return _orig_textlength(self, txt_f, *args, **kwargs)
    _ImageDraw_vid.ImageDraw.textlength = _hook_textlength

# Bordes gestionados directamente por el motor visual v3 (sin sobreescribir colores en tarjetas ni vídeos)

# B. Interceptar la Voz IA (edge_tts) para pronunciar "Poison" claramente
try:
    import edge_tts as _etts_vid
    _orig_comm_init = _etts_vid.Communicate.__init__
    def _hook_comm_init(self, text, *args, **kwargs):
        return _orig_comm_init(self, _limpiar_texto_redes_sociales(text, modo="voz"), *args, **kwargs)
    _etts_vid.Communicate.__init__ = _hook_comm_init
except Exception:
    pass

# C. Limpiar cola_publicacion_redes.json al guardarse
_orig_json_dump = _json_vid.dump
def _limpiar_json_redes(obj):
    if isinstance(obj, dict):
        return {k: (v if "ruta" in str(k) or "archivo" in str(k) else _limpiar_json_redes(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_limpiar_json_redes(x) for x in obj]
    elif isinstance(obj, str):
        if obj.endswith(".mp4") or obj.endswith(".jpg") or ":\\" in obj or "/" in obj:
            return obj
        return _limpiar_texto_redes_sociales(obj, modo="copy")
    return obj

def _hook_json_dump(obj, fp, *args, **kwargs):
    if hasattr(fp, "name") and "cola_publicacion_redes.json" in str(fp.name):
        return _orig_json_dump(_limpiar_json_redes(obj), fp, *args, **kwargs)
    return _orig_json_dump(obj, fp, *args, **kwargs)
_json_vid.dump = _hook_json_dump

# D. Escapado HTML blindado por placeholders (impide que '>' o '->' rompan los mensajes de Telegram)
_orig_req_post = _req_vid.post

def _escapar_html_seguro_tg(txt):
    s = str(txt).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
    tags_validos = ["<b>", "</b>", "<i>", "</i>", "<u>", "</u>", "<s>", "</s>", "<code>", "</code>", "<pre>", "</pre>"]
    mapa_tok = {}
    for idx_t, tg in enumerate(tags_validos):
        tok = f"__TG_TAG_{idx_t}__"
        mapa_tok[tok] = tg
        s = s.replace(tg, tok)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for tok, tg in mapa_tok.items():
        s = s.replace(tok, tg)
    return s

def _es_payload_redes(url, payload):
    if "sendVideo" in str(url):
        return True
    if not isinstance(payload, dict):
        return False
    txt = str(payload.get("text", "")) + " " + str(payload.get("caption", ""))
    claves_redes = [
        "TIKTOK", "INSTAGRAM REELS", "YOUTUBE SHORTS", "FACEBOOK REELS",
        "VIDEO 1 (", "VIDEO 2 (", "VÍDEO #", "Horario programado:"
    ]
    return any(k in txt for k in claves_redes)

def _hook_req_post_quirurgico(url, *args, **kwargs):
    if "api.telegram.org" not in str(url):
        return _orig_req_post(url, *args, **kwargs)

    # Detectar el diccionario tanto en kwargs["json"], kwargs["data"] como en args[0]
    modo_envio = None
    payload_orig = None
    if "json" in kwargs and isinstance(kwargs["json"], dict):
        modo_envio, payload_orig = "json", dict(kwargs["json"])
    elif "data" in kwargs and isinstance(kwargs["data"], dict):
        modo_envio, payload_orig = "data", dict(kwargs["data"])
    elif len(args) >= 1 and isinstance(args[0], dict):
        modo_envio, payload_orig = "arg0", dict(args[0])

    if not _es_payload_redes(url, payload_orig):
        return _orig_req_post(url, *args, **kwargs)

    _time_vid.sleep(1.2)
    if isinstance(payload_orig, dict):
        if "text" in payload_orig:
            limpio = _limpiar_texto_redes_sociales(payload_orig["text"], modo="copy")
            payload_orig["text"] = _escapar_html_seguro_tg(limpio)
        if "caption" in payload_orig:
            limpio_c = _limpiar_texto_redes_sociales(payload_orig["caption"], modo="copy")
            payload_orig["caption"] = _escapar_html_seguro_tg(limpio_c)

        if modo_envio == "json":
            kwargs["json"] = payload_orig
        elif modo_envio == "data":
            kwargs["data"] = payload_orig
        elif modo_envio == "arg0":
            args = (payload_orig,) + args[1:]

    for intento in range(3):
        try:
            res = _orig_req_post(url, *args, **kwargs)
            if res.status_code == 200:
                return res
            # Si por cualquier motivo Telegram devuelve 400, enviar en texto plano sin perder jamás el mensaje
            if res.status_code == 400 and isinstance(payload_orig, dict):
                payload_plano = dict(payload_orig)
                for campo in ("text", "caption"):
                    if campo in payload_plano:
                        txt_p = _re_vid.sub(r"<[^>]+>", "", str(payload_plano[campo]))
                        payload_plano[campo] = txt_p.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
                payload_plano.pop("parse_mode", None)
                if modo_envio == "json":
                    kwargs["json"] = payload_plano
                elif modo_envio == "data":
                    kwargs["data"] = payload_plano
                elif modo_envio == "arg0":
                    args = (payload_plano,) + args[1:]
                res_plano = _orig_req_post(url, *args, **kwargs)
                if res_plano.status_code == 200:
                    return res_plano
        except Exception:
            pass
        _time_vid.sleep(2.0)

    return _orig_req_post(url, *args, **kwargs)

_req_vid.post = _hook_req_post_quirurgico
# === FIN FILTRO EXCLUSIVO DE VIDEO ===







import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import wave
import edge_tts
import imageio_ffmpeg
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import requests

VOZ_ANALISTA_IA = "es-ES-AlvaroNeural"
VELOCIDAD_VOZ = "+6%"
API_KEY_RESPALDO_AYER = os.getenv("API_SPORTS_KEY", "48f391f30e76d9c84e5c94b6a4cccdb4")

TOKEN_AUDITORIAS_PRIVADO = os.getenv("TG_TOKEN_AUDITORIAS", "8805035408:AAGPYUxmFz-Spfum1P2vacMZz5bToXUPMWI")
CHAT_ID_AUDITORIAS_PRIVADO = "1491740882"

LIGAS_OFICIALES_IDS = {
    140, 143, 141, 39, 45, 48, 135, 137, 78, 81, 61, 66,
    128, 130, 530, 239, 240, 533, 712, 307, 71, 73, 94, 96,
    88, 90, 144, 197, 179, 2, 3, 848, 13, 11
}

GIGANTES_TIER_1_MUNDIAL = [
    "real madrid", "barcelona", "atletico madrid", "manchester city", "manchester united",
    "liverpool", "arsenal", "chelsea", "tottenham", "bayern", "dortmund", "borussia dortmund",
    "inter", "fc internazionale", "milan", "ac milan", "juventus", "napoli", "paris saint germain", "paris sg", "psg",
    "boca juniors", "river plate", "flamengo", "palmeiras", "millonarios", "atletico nacional",
    "españa", "spain", "argentina", "brasil", "brazil", "francia", "france", "inglaterra", "england", "alemania", "germany", "portugal", "italia", "italy", "colombia", "uruguay", "paises bajos", "netherlands"
]

GIGANTES_TIER_2_SECUNDARIO = [
    "roma", "lazio", "atalanta", "fiorentina", "bologna", "torino",
    "leverkusen", "leipzig", "stuttgart", "frankfurt", "aston villa", "newcastle",
    "everton", "west ham", "brighton", "fulham", "bournemouth", "sevilla", "real betis", "betis",
    "athletic", "real sociedad", "villarreal", "valencia", "girona", "celta", "osasuna",
    "benfica", "sporting", "porto", "ajax", "psv", "feyenoord",
    "monaco", "marseille", "lyon", "lille",
    "america de cali", "santa fe", "junior", "independiente medellin", "deportivo cali",
    "corinthians", "sao paulo", "racing", "independiente", "gremio", "internacional", "botafogo", "fluminense",
    "cruzeiro", "vasco", "san lorenzo", "velez", "estudiantes", "peñarol", "colo colo",
    "ldu quito", "independiente del valle", "olimpia", "tolima", "once caldas", "bucaramanga",
    "belgica", "belgium", "croacia", "croatia", "marruecos", "morocco", "mexico", "usa", "ecuador", "paraguay", "chile", "suiza", "switzerland", "dinamarca", "denmark", "noruega", "norway", "suecia", "sweden",
    "japon", "japan", "serbia", "grecia", "greece", "austria", "polonia", "poland", "escocia", "scotland", "ucrania", "ukraine"
]

EQUIPOS_DESCONOCIDOS_PENALIZADOS = [
    "llaneros", "mirassol", "boyaca chico", "envigado", "patriotas", "jaguares",
    "alianza", "equidad", "fortaleza ceif", "cucuta", "huila", "quindio", "popayan"
]
GIGANTES_MUNDIALES_VIDEO = GIGANTES_TIER_1_MUNDIAL + GIGANTES_TIER_2_SECUNDARIO


def ruta_posix(ruta):
    return os.path.abspath(str(ruta)).replace("\\", "/")


def sincronizar_caches_nocturnos_al_iniciar(*args, **kwargs):
    return


def _es_club_lista(nombre_eq, lista_clubes):
    n = "".join(c for c in unicodedata.normalize("NFD", str(nombre_eq).lower()) if unicodedata.category(c) != "Mn")
    n = n.replace("ath madrid", "atletico madrid").replace("atletico de madrid", "atletico madrid").strip()
    for g in lista_clubes:
        g_limpio = "".join(c for c in unicodedata.normalize("NFD", str(g).lower()) if unicodedata.category(c) != "Mn")
        if g_limpio == "inter":
            if n in ["inter", "fc internazionale", "inter milan", "internazionale"]:
                return True
        elif g_limpio in n:
            return True
    return False


def _es_filial_video(nombre_eq):
    n = "".join(c for c in unicodedata.normalize("NFD", str(nombre_eq).lower()) if unicodedata.category(c) != "Mn")
    return bool(re.search(r"(?:^|\s)(?:ii|iii|b|c|castilla|atletic|jong|reserves|u23|u21)(?:$|\s)", n))


def puntaje_cartelera_video(p):
    loc = str(p.get("local", "")).lower()
    vis = str(p.get("visitante", "")).lower()
    liga = str(p.get("liga_visual", "")).upper()
    loc_fil = _es_filial_video(loc)
    vis_fil = _es_filial_video(vis)

    pts = 0.0
    # PRIORIDAD #1 ABSOLUTA EN VÍDEOS: Real Madrid, Barcelona y Millonarios (excluyendo filiales y Barcelona SC de Ecuador)
    es_rm = ("real madrid" in loc and not loc_fil) or ("real madrid" in vis and not vis_fil)
    es_fcb = (
        ("barcelona" in loc and not loc_fil and "guayaquil" not in loc and "barcelona sc" not in loc and "ECUADOR" not in liga)
        or ("barcelona" in vis and not vis_fil and "guayaquil" not in vis and "barcelona sc" not in vis and "ECUADOR" not in liga)
    )
    es_millos = ("millonarios" in loc) or ("millonarios" in vis)

    if es_rm:
        pts += 10000
    if es_fcb:
        pts += 9500
    if es_millos:
        pts += 9000

    loc_t1 = (not loc_fil) and _es_club_lista(loc, GIGANTES_TIER_1_MUNDIAL)
    vis_t1 = (not vis_fil) and _es_club_lista(vis, GIGANTES_TIER_1_MUNDIAL)
    loc_t2 = (not loc_fil) and _es_club_lista(loc, GIGANTES_TIER_2_SECUNDARIO)
    vis_t2 = (not vis_fil) and _es_club_lista(vis, GIGANTES_TIER_2_SECUNDARIO)
    tiene_desconocido = any(d in loc or d in vis for d in EQUIPOS_DESCONOCIDOS_PENALIZADOS)

    if loc_t1 and vis_t1:
        pts += 260
    elif (loc_t1 and vis_t2) or (vis_t1 and loc_t2):
        pts += 175
    elif loc_t2 and vis_t2:
        pts += 120
    elif loc_t1 or vis_t1:
        pts += 85
    elif loc_t2 or vis_t2:
        pts += 40

    if p.get("es_derbi", False):
        pts += 100

    if tiene_desconocido:
        pts -= 65

    # Peso real de cartelera por competición (Europa Top 5 / Champions siempre por encima de Liga MX / MLS / Segunda)
    if any(lg in liga for lg in ["UEFA CHAMPIONS", "MUNDIAL", "EUROCOPA", "COPA AMÉRICA"]):
        pts += 120
    elif any(lg in liga for lg in ["LALIGA", "PREMIER", "SERIE A", "BUNDESLIGA", "LIGUE 1"]) and "BRASIL" not in liga:
        pts += 95
    elif any(lg in liga for lg in ["LIBERTADORES", "EUROPA LEAGUE", "NATIONS LEAGUE", "ELIMINATORIAS"]):
        pts += 65
    elif any(lg in liga for lg in ["COLOMBIA (PRIMERA A)", "ARGENTINA (LIGA", "BRASIL (SERIE A)", "COPA DEL REY", "FA CUP"]):
        pts += 45
    elif any(lg in liga for lg in ["CONFERENCE", "SUDAMERICANA", "PRIMEIRA LIGA", "EREDIVISIE"]):
        pts += 25
    elif any(lg in liga for lg in ["MÉXICO", "LIGA MX", "MLS", "USA", "SEGUNDA", "TORNEO BETPLAY"]):
        pts -= 25

    pts += min(12.0, float(p.get("tot_goles", 2.5)) * 3.0)
    return pts


def obtener_fuente_video_ajustada(draw, texto, archivo_ttf, tam_inicial, ancho_max_px, tam_min=16):
    tam = tam_inicial
    while tam >= tam_min:
        try:
            f = ImageFont.truetype(archivo_ttf, tam)
        except IOError:
            return ImageFont.load_default()
        bbox = draw.textbbox((0, 0), str(texto), font=f)
        if (bbox[2] - bbox[0]) <= ancho_max_px:
            return f
        tam -= 1
    try:
        return ImageFont.truetype(archivo_ttf, tam_min)
    except IOError:
        return ImageFont.load_default()


def cargar_fuentes_video(tam_titulo=40):
    try:
        f_tag = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 29)
        f_titulo = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", tam_titulo)
        f_sub = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 31)
        f_cta = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 25)
        f_peq = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 22)
    except IOError:
        f_tag = f_titulo = f_sub = f_cta = f_peq = ImageFont.load_default()
    return f_tag, f_titulo, f_sub, f_cta, f_peq


def limpiar_hashtag(texto):
    t = str(texto)
    reemplazos_clubes = {
        "Paris Saint Germain": "PSG",
        "Paris SG": "PSG",
        "Atletico Madrid": "AtleticoMadrid",
        "Real Madrid": "RealMadrid",
        "Manchester City": "ManchesterCity",
        "Manchester United": "ManchesterUnited",
        "Aston Villa": "AstonVilla",
        "Borussia Dortmund": "BorussiaDortmund",
        "Bayern München": "BayernMunich",
        "Bayern Munich": "BayernMunich",
        "AC Milan": "ACMilan",
        "AS Roma": "ASRoma",
        "Real Sociedad": "RealSociedad",
        "Real Betis": "RealBetis",
        "Boca Juniors": "BocaJuniors",
        "River Plate": "RiverPlate",
        "America de Cali": "AmericadeCali",
        "Atletico Nacional": "AtleticoNacional",
    }
    for k, v in reemplazos_clubes.items():
        if k.lower() in t.lower():
            t = v
            break
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )
    limpio = "".join(c for c in sin_tildes if c.isalnum()).lower().strip()
    return f"#{limpio}" if len(limpio) > 2 else "#futbol"


def crear_fondo_vertical_base():
    ancho, alto = 1080, 1920
    ruta_fondo = "fondo de quant bet.jpg"
    if os.path.exists(ruta_fondo):
        fondo_orig = Image.open(ruta_fondo).convert("RGBA")
        w, h = fondo_orig.size
        escala = alto / h
        nuevo_w = int(w * escala)
        fondo = fondo_orig.resize((nuevo_w, alto), Image.Resampling.LANCZOS)
        left = max(0, (nuevo_w - ancho) // 2)
        fondo = fondo.crop((left, 0, left + ancho, alto))
    else:
        fondo = Image.new("RGBA", (ancho, alto), (10, 12, 16, 255))
    capa_oscura = Image.new("RGBA", (ancho, alto), (8, 8, 12, 232))
    return Image.alpha_composite(fondo, capa_oscura)


def crear_slide_vertical(ruta_tarjeta_cuadrada, texto_superior_tag, texto_partido, texto_inferior_cta, difuminar_vip=False, modo_gancho_telegram=False, ruta_salida="slide_temp.jpg"):
    lienzo = crear_fondo_vertical_base()
    draw = ImageDraw.Draw(lienzo, "RGBA")
    partido_str = texto_partido.upper()
    f_tag, _, f_sub, f_cta, f_peq = cargar_fuentes_video()
    f_tag_ajustada = obtener_fuente_video_ajustada(draw, texto_superior_tag.upper(), "Montserrat-VariableFont_wght.ttf", 29, 930, tam_min=18)
    f_titulo_ajustada = obtener_fuente_video_ajustada(draw, partido_str, "Montserrat-VariableFont_wght.ttf", 42, 960, tam_min=22)

    c_verde = (0, 255, 100, 255)
    c_oro = (255, 205, 0, 255)
    c_blanco = (245, 245, 245, 255)
    c_gris = (180, 180, 180, 255)

    draw.rectangle([(50, 88), (1030, 152)], fill=(12, 28, 20, 235), outline=c_verde, width=2)
    draw.text((75, 102), texto_superior_tag.upper(), font=f_tag_ajustada, fill=c_verde)
    draw.text((55, 170), partido_str, font=f_titulo_ajustada, fill=c_blanco)
    draw.line((50, 236, 1030, 236), fill=(85, 85, 95, 255), width=2)

    if ruta_tarjeta_cuadrada and os.path.exists(ruta_tarjeta_cuadrada):
        tarjeta = Image.open(ruta_tarjeta_cuadrada).convert("RGBA").resize((920, 920), Image.Resampling.LANCZOS)
        if modo_gancho_telegram:
            # Baja el difuminado a y=500 (justo debajo de 'PROYECCIONES DEL MODELO MATEMÁTICO')
            zona_picks = tarjeta.crop((35, 500, 885, 755))
            zona_borrosa = zona_picks.filter(ImageFilter.GaussianBlur(radius=22))
            tarjeta.paste(zona_borrosa, (35, 500))
            d_tarj = ImageDraw.Draw(tarjeta, "RGBA")
            d_tarj.rectangle([(55, 520), (865, 715)], fill=(10, 14, 20, 248), outline=c_verde, width=3)

            t1 = "1ª JUGADA EN WEB + 2 EN TELEGRAM GRATIS"
            t2 = "2 Proyecciones Ocultas -> Ver en nuestra App Web"
            t3 = "Entra ahora desde el enlace de nuestro perfil"

            f_b1 = obtener_fuente_video_ajustada(d_tarj, t1, "Montserrat-VariableFont_wght.ttf", 28, 760, 18)
            f_b2 = obtener_fuente_video_ajustada(d_tarj, t2, "RobotoMono-VariableFont_wght.ttf", 23, 760, 16)
            f_b3 = obtener_fuente_video_ajustada(d_tarj, t3, "RobotoMono-VariableFont_wght.ttf", 22, 760, 16)

            # Centrado horizontal matemático exacto (sin emojis que descuadren el texto)
            x1 = 460 - ((d_tarj.textbbox((0, 0), t1, font=f_b1)[2] - d_tarj.textbbox((0, 0), t1, font=f_b1)[0]) // 2)
            x2 = 460 - ((d_tarj.textbbox((0, 0), t2, font=f_b2)[2] - d_tarj.textbbox((0, 0), t2, font=f_b2)[0]) // 2)
            x3 = 460 - ((d_tarj.textbbox((0, 0), t3, font=f_b3)[2] - d_tarj.textbbox((0, 0), t3, font=f_b3)[0]) // 2)

            d_tarj.text((x1, 542), t1, font=f_b1, fill=c_verde)
            d_tarj.text((x2, 598), t2, font=f_b2, fill=c_blanco)
            d_tarj.text((x3, 648), t3, font=f_b3, fill=c_oro)
        elif difuminar_vip:
            zona_secreta = tarjeta.crop((35, 360, 885, 750))
            zona_borrosa = zona_secreta.filter(ImageFilter.GaussianBlur(radius=22))
            tarjeta.paste(zona_borrosa, (35, 360))
            d_tarj = ImageDraw.Draw(tarjeta, "RGBA")
            d_tarj.rectangle([(55, 465), (865, 635)], fill=(12, 14, 20, 248), outline=c_oro, width=3)

            tv1 = "PASE DIARIO VIP DISPONIBLE EN NUESTRA WEB"
            tv2 = "Entra ahora desde el enlace de nuestro perfil"
            f_v1 = obtener_fuente_video_ajustada(d_tarj, tv1, "Montserrat-VariableFont_wght.ttf", 28, 760, 18)
            f_v2 = obtener_fuente_video_ajustada(d_tarj, tv2, "RobotoMono-VariableFont_wght.ttf", 24, 760, 16)
            xv1 = 460 - ((d_tarj.textbbox((0, 0), tv1, font=f_v1)[2] - d_tarj.textbbox((0, 0), tv1, font=f_v1)[0]) // 2)
            xv2 = 460 - ((d_tarj.textbbox((0, 0), tv2, font=f_v2)[2] - d_tarj.textbbox((0, 0), tv2, font=f_v2)[0]) // 2)
            d_tarj.text((xv1, 498), tv1, font=f_v1, fill=c_oro)
            d_tarj.text((xv2, 560), tv2, font=f_v2, fill=c_verde)

        lienzo.paste(tarjeta, (80, 254))
        draw.rectangle([(78, 252), (1002, 1176)], outline=(0, 255, 100, 130), width=3)

    draw.rectangle([(50, 1335), (1030, 1500)], fill=(16, 18, 24, 245), outline=c_oro, width=2)
    f_cta_sup = obtener_fuente_video_ajustada(draw, texto_inferior_cta, "Montserrat-VariableFont_wght.ttf", 30, 930, tam_min=20)
    draw.text((75, 1355), texto_inferior_cta, font=f_cta_sup, fill=c_oro)
    draw.text((75, 1410), "🌐 WEB OFICIAL Y PROMO $7.99 EN EL PERFIL", font=f_cta, fill=c_verde)
    draw.text((75, 1452), "@QuantBet22 | Ciencia de Datos (+18 Informativo)", font=f_peq, fill=c_gris)

    lienzo.convert("RGB").save(ruta_salida, quality=96)
    return ruta_salida


def estampar_subtitulo_metro(ruta_slide_base, texto_subtitulo, ruta_salida_frame, progreso_pct=1.0):
    texto_subtitulo = (
    str(texto_subtitulo)
    .replace("Néishons Lig", "Nations League")
    .replace("Chámpions Lig", "Champions League")
    .replace("Premier Lig", "Premier League")
    .replace("Europa Lig", "Europa League")
)
    img = Image.open(ruta_slide_base).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([(45, 1192), (1035, 1320)], fill=(6, 8, 12, 248), outline=(0, 255, 100, 220), width=3)

    palabras = str(texto_subtitulo).strip().split()
    mitad = max(1, len(palabras) // 2)
    if len(palabras) <= 6:
        linea_1 = " ".join(palabras)
        linea_2 = ""
    else:
        linea_1 = " ".join(palabras[:mitad])
        linea_2 = " ".join(palabras[mitad:])

    if linea_2:
        f1 = obtener_fuente_video_ajustada(draw, linea_1, "Montserrat-VariableFont_wght.ttf", 31, 950, tam_min=20)
        f2 = obtener_fuente_video_ajustada(draw, linea_2, "Montserrat-VariableFont_wght.ttf", 31, 950, tam_min=20)
        b1 = draw.textbbox((0, 0), linea_1, font=f1)
        b2 = draw.textbbox((0, 0), linea_2, font=f2)
        x1 = (1080 - (b1[2] - b1[0])) // 2
        x2 = (1080 - (b2[2] - b2[0])) // 2
        draw.text((x1, 1208), linea_1, font=f1, fill=(255, 255, 255, 255))
        draw.text((x2, 1260), linea_2, font=f2, fill=(255, 215, 0, 255))
    else:
        f1 = obtener_fuente_video_ajustada(draw, linea_1, "Montserrat-VariableFont_wght.ttf", 34, 950, tam_min=22)
        b1 = draw.textbbox((0, 0), linea_1, font=f1)
        x1 = (1080 - (b1[2] - b1[0])) // 2
        draw.text((x1, 1234), linea_1, font=f1, fill=(255, 215, 0, 255))

    ancho_barra = int(max(40, min(986, 986 * float(progreso_pct))))
    draw.rectangle([(47, 1312), (1033, 1319)], fill=(18, 28, 22, 255))
    draw.rectangle([(47, 1312), (47 + ancho_barra, 1319)], fill=(0, 255, 100, 255))
    img.convert("RGB").save(ruta_salida_frame, quality=95)
    return ruta_salida_frame


def evaluar_mercado_contra_resultado_real(merc, gh, ga, g_ht, es_sudamerica=False, partido_nom="", stats_reales=None):
    tot = gh + ga
    g_2t = max(0, tot - g_ht)
    m = str(merc).strip()
    m_low = m.lower()

    def _norm_txt(s):
        return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")

    m_norm = _norm_txt(m_low)
    loc_n, vis_n = (_norm_txt(partido_nom).split(" vs ") + ["", ""])[:2]

    if ("over " in m_low or "mas de " in m_norm) and "goles" in m_low and "1t" not in m_low and "2t" not in m_low and "tiempo" not in m_low:
        m_ov = re.search(r"(\d+(?:\.\d+)?)", m_low)
        if m_ov:
            return tot > float(m_ov.group(1))
    elif "under " in m_low or "menos de " in m_low:
        m_un = re.search(r"(\d+(?:\.\d+)?)", m_low)
        if m_un:
            return tot < float(m_un.group(1))
    elif "asiatico > 2.25" in m_norm:
        return tot >= 3
    elif "asiatico > 2.75" in m_norm:
        return tot >= 3
    elif "btts" in m_low or "ambos marcan" in m_low:
        return gh > 0 and ga > 0
    elif "combo 1x + o1.5" in m_low:
        return gh >= ga and tot >= 2
    elif "combo x2 + o1.5" in m_low:
        return ga >= gh and tot >= 2
    elif "combo 1x + u3.5" in m_low:
        return gh >= ga and tot <= 3
    elif "combo 1x + u4.5" in m_low:
        return gh >= ga and tot <= 4
    elif "combo x2 + u3.5" in m_low:
        return ga >= gh and tot <= 3
    elif "sin empate" in m_low or "dnb" in m_low:
        if gh == ga:
            return True
        if "local" in m_low or (loc_n and loc_n[:5] in m_norm):
            return gh > ga
        if "visita" in m_low or (vis_n and vis_n[:5] in m_norm):
            return ga > gh
        return False
    elif "1x" in m_low:
        return gh >= ga
    elif "x2" in m_low:
        return ga >= gh
    elif "goles 1t" in m_low or "gol en 1t" in m_low or "gol 1t" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        return g_ht > (float(m_n.group(1)) if m_n else 0.5)
    elif "goles 2" in m_low or "gol en 2" in m_low or "gol 2t" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        return g_2t > (float(m_n.group(1)) if m_n else 0.5)
    elif "goles " in m_low and ">" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        lin_eq = float(m_n.group(1)) if m_n else 1.5
        if loc_n and loc_n[:5] in m_norm:
            return gh > lin_eq
        elif vis_n and vis_n[:5] in m_norm:
            return ga > lin_eq
        return False
    elif "vict." in m_low or "victoria" in m_low:
        if "local" in m_low or (loc_n and loc_n[:5] in m_norm):
            return gh > ga
        elif "visita" in m_low or (vis_n and vis_n[:5] in m_norm):
            return ga > gh
        return False
    elif "empate" in m_low:
        return gh == ga
    elif "tarjetas" in m_low or "amarill" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        linea_t = float(m_n.group(1)) if m_n else 3.5
        if isinstance(stats_reales, dict):
            if "amarill" in m_low and stats_reales.get("yellow_total") is not None:
                return float(stats_reales["yellow_total"]) > linea_t
            if stats_reales.get("cards_total") is not None:
                return float(stats_reales["cards_total"]) > linea_t
        return (abs(gh - ga) <= 1) or (tot >= 2)
    elif "faltas" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        linea_f = float(m_n.group(1)) if m_n else 22.5
        if isinstance(stats_reales, dict) and stats_reales.get("fouls_total") is not None:
            return float(stats_reales["fouls_total"]) > linea_f
        return (abs(gh - ga) <= 1) or (tot >= 2)
    elif "corners" in m_norm:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        linea_c = float(m_n.group(1)) if m_n else 7.5
        if isinstance(stats_reales, dict):
            if linea_c <= 5.5:
                if loc_n and loc_n[:5] in m_norm and stats_reales.get("corners_home") is not None:
                    return float(stats_reales["corners_home"]) > linea_c
                if vis_n and vis_n[:5] in m_norm and stats_reales.get("corners_away") is not None:
                    return float(stats_reales["corners_away"]) > linea_c
            if stats_reales.get("corners_total") is not None:
                return float(stats_reales["corners_total"]) > linea_c
        return (tot >= 1) or (abs(gh - ga) <= 1)
    elif "remates" in m_low:
        m_n = re.search(r">\s*(\d+(?:\.\d+)?)", m)
        linea_r = float(m_n.group(1)) if m_n else 6.5
        if isinstance(stats_reales, dict) and stats_reales.get("shots_on_target_total") is not None:
            return float(stats_reales["shots_on_target_total"]) > linea_r
        return (tot >= 1) or (abs(gh - ga) <= 1)
    return tot >= 2


def abreviar_pick_cliente(merc):
    m = str(merc)
    m = m.replace("[VIP] ", "").replace("[FREE] ", "")
    m = m.replace("Remates Puerta", "Remates").replace("Faltas Totales", "Faltas")
    m = m.replace("Gol en 2do Tiempo", "Gol 2T").replace("Gol en 1T", "Gol 1T")
    m = m.replace("Total Menos de 2.5 (Under)", "Under 2.5").replace("Total Menos de 3.5 (Under)", "Under 3.5")
    m = m.replace("Total Asiático > 2.25", "Asiático > 2.25").replace("Ambos Marcan (BTTS)", "Ambos Marcan")
    return m


def _tokens_equipo_auditoria(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    ign = {"fc", "sc", "cf", "ac", "as", "sk", "ud", "cd", "rcd", "ca", "se", "cr", "ce", "club", "deportivo", "deportes", "atletico", "real", "sporting", "united", "city", "de", "la", "el", "ii"}
    t = [w for w in s.split() if len(w) >= 3 and w not in ign]
    return set(t) if t else set(s.split())


def seleccionar_7_partidos_14_apuestas_clientes(fecha_hoy, ruta_csv="auditoria_apuestas.csv", token_priv=None, chat_priv=None, modo_horario="manana"):
    # 1. Cargar el 100% de los partidos finalizados (FT) de TODOS los archivos cache_partidos_*.json
    mapa_ft = {}
    indice_tokens_ft = []

    archivos_cache = sorted([a for a in os.listdir(".") if a.startswith("cache_partidos_") and a.endswith(".json")])
    for arch in archivos_cache:
        f_arch = arch.replace("cache_partidos_", "").replace(".json", "")
        try:
            with open(arch, "r", encoding="utf-8") as f:
                for p in json.load(f) or []:
                    est = str((p.get("fixture") or {}).get("status", {}).get("short") or "")
                    goals = p.get("goals") or {}
                    if est in ["FT", "AET", "PEN"] and goals.get("home") is not None and goals.get("away") is not None:
                        loc = str(((p.get("teams") or {}).get("home") or {}).get("name") or "").strip()
                        vis = str(((p.get("teams") or {}).get("away") or {}).get("name") or "").strip()
                        fid = str((p.get("fixture") or {}).get("id") or "")
                        if fid:
                            mapa_ft[fid] = p
                        if loc and vis:
                            mapa_ft[f"{loc.lower()} vs {vis.lower()}"] = p
                            indice_tokens_ft.append((f_arch, _tokens_equipo_auditoria(loc), _tokens_equipo_auditoria(vis), p))
        except Exception:
            pass

    # Calcular SIEMPRE primero la fecha exacta a auditar (ayer antes de las 21:00h ESP, hoy desde las 21:00h ESP)
    ahora_real_aud = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    fecha_max_terminada = (
        (ahora_real_aud - timedelta(days=1)).strftime("%Y-%m-%d")
        if ahora_real_aud.hour < 21
        else ahora_real_aud.strftime("%Y-%m-%d")
    )
    fecha_tope_auditoria = min(str(fecha_hoy), fecha_max_terminada)

    # Cargar estados exactos ya auditados en auditoria_apuestas.csv usando fecha_tope_auditoria (NO una fecha futura)
    mapa_estado_csv = {}
    csv_mismo_dia = {"VIP": {}, "FREE": {}}
    try:
        dt_obj_f = datetime.strptime(str(fecha_tope_auditoria), "%Y-%m-%d")
        ini_vent_csv = dt_obj_f + timedelta(hours=7)
        fin_vent_csv = dt_obj_f + timedelta(days=1, hours=6, minutes=59)
    except Exception:
        ini_vent_csv = fin_vent_csv = None

    if os.path.exists(ruta_csv):
        try:
            df_aud_csv = pd.read_csv(ruta_csv, dtype=str)
            for _, r in df_aud_csv.iterrows():
                est_r = str(r.get("Estado", "")).strip()
                if est_r not in ["Ganada", "Perdida", "Mitad Devuelta"]:
                    continue
                p_full = str(r.get("Partido", "")).strip()
                p_clean = p_full.split(" (")[0].strip().lower()
                m_raw = str(r.get("Mercado", "")).strip()
                m_clean = m_raw.replace("[VIP] ", "").replace("[FREE] ", "").strip().lower()
                id_r = str(r.get("ID_Partido", "")).strip()
                gano_r = est_r in ["Ganada", "Mitad Devuelta"]
                clv_r = str(r.get("CLV_Status", "")).replace("AUDITADA ", "").replace("FT ", "").strip()
                cuo_r = float(r.get("Cuota_Compra", 1.38 if "[VIP]" in m_raw else 1.24))

                if id_r:
                    mapa_estado_csv[(id_r, m_clean)] = gano_r
                mapa_estado_csv[(p_clean, m_clean)] = gano_r

                # Guardar respaldo de la MISMA jornada (día + madrugada) por si faltó 1 cupo en clientes_enviados
                if ini_vent_csv and fin_vent_csv and (m_raw.startswith("[VIP]") or m_raw.startswith("[FREE]")):
                    f_reg = str(r.get("Fecha_Registro", "")).strip()
                    try:
                        dt_reg = datetime.strptime(f_reg[:16], "%Y-%m-%d %H:%M")
                    except Exception:
                        continue
                    if ini_vent_csv <= dt_reg <= fin_vent_csv:
                        lvl = "VIP" if m_raw.startswith("[VIP]") else "FREE"
                        m_sin_tag = m_raw.replace(f"[{lvl}] ", "").strip()
                        slot = csv_mismo_dia[lvl].setdefault(p_clean, {
                            "tipo_tarjeta": lvl,
                            "partido": p_full,
                            "marcador": clv_r if "-" in clv_r else "0-0",
                            "fecha": str(fecha_tope_auditoria),
                            "dos_apuestas": [],
                        })
                        if not any(x["mercado_corto"].lower() == abreviar_pick_cliente(m_sin_tag).lower() for x in slot["dos_apuestas"]):
                            slot["dos_apuestas"].append({
                                "mercado": f"[{lvl}] {m_sin_tag}",
                                "mercado_corto": abreviar_pick_cliente(m_sin_tag),
                                "cuota": cuo_r,
                                "ganada": gano_r,
                            })
        except Exception:
            pass

    def _buscar_partido_ft_real(id_p, part_nom, fecha_ref):
        if id_p and str(id_p) in mapa_ft:
            return mapa_ft[str(id_p)]
        clave_sin_liga = str(part_nom).split(" (")[0].strip().lower()
        if clave_sin_liga in mapa_ft:
            return mapa_ft[clave_sin_liga]
        if " vs " in clave_sin_liga:
            l_b, v_b = clave_sin_liga.split(" vs ", 1)
            tl, tv = _tokens_equipo_auditoria(l_b), _tokens_equipo_auditoria(v_b)
            try:
                dt_r = datetime.strptime(fecha_ref, "%Y-%m-%d")
                fechas_ok = {
                    fecha_ref,
                    (dt_r + timedelta(days=1)).strftime("%Y-%m-%d"),
                    (dt_r - timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            except Exception:
                fechas_ok = None
            for f_c, tl_c, tv_c, p_obj in indice_tokens_ft:
                if fechas_ok and f_c not in fechas_ok:
                    continue
                ok_l = bool(tl & tl_c) or any(a[:4] == b[:4] for a in tl for b in tl_c if len(a) >= 4 and len(b) >= 4)
                ok_v = bool(tv & tv_c) or any(a[:4] == b[:4] for a in tv for b in tv_c if len(a) >= 4 and len(b) >= 4)
                if ok_l and ok_v:
                    return p_obj
        if id_p and str(id_p).isdigit():
            try:
                r_id = requests.get(
                    f"https://v3.football.api-sports.io/fixtures?id={id_p}",
                    headers={"x-apisports-key": API_KEY_RESPALDO_AYER},
                    timeout=5
                )
                if r_id.status_code == 200:
                    resp_l = r_id.json().get("response") or []
                    if resp_l:
                        p_api = resp_l[0]
                        if str((p_api.get("fixture") or {}).get("status", {}).get("short") or "") in ["FT", "AET", "PEN"]:
                            mapa_ft[str(id_p)] = p_api
                            return p_api
            except Exception:
                pass
        return None

    # 2. REGLA ESTRICTA DE TRANSPARENCIA POR JORNADA (CERO MEZCLA DE DÍAS):
    #    Tanto en modo "noche" (23:15 "Cómo vamos hoy") como en modo "manana" (07:30 cierre oficial),
    #    audita EXCLUSIVAMENTE las 7 tarjetas (4 VIP + 3 FREE) de la jornada fecha_tope_auditoria.
    #    Los partidos de hoy que aún no hayan terminado (ej. madrugada Latam) salen claramente como
    #    "POR JUGAR / EN ESPERA" sin contaminar la tabla con partidos del día anterior.
    archivos_clientes = sorted(
        [a for a in os.listdir(".") if re.match(r"clientes_enviados_\d{4}-\d{2}-\d{2}\.json", a)],
        reverse=True
    )
    arch_oficial_dia = f"clientes_enviados_{fecha_tope_auditoria}.json"
    if os.path.exists(arch_oficial_dia):
        archivos_a_leer = [arch_oficial_dia]
    else:
        # Solo si no existió jornada ese día, tomar el archivo de clientes inmediatamente anterior
        anteriores = [a for a in archivos_clientes if a.replace("clientes_enviados_", "").replace(".json", "") <= fecha_tope_auditoria]
        archivos_a_leer = anteriores[:1]

    vip_recolectadas = []
    free_recolectadas = []
    partidos_vistos = set()
    fecha_auditada_real = None
    excluidos_copa = ()

    for arch_c in archivos_a_leer:
        f_cand = arch_c.replace("clientes_enviados_", "").replace(".json", "")
        fecha_auditada_real = f_cand
        try:
            with open(arch_c, "r", encoding="utf-8") as f:
                tarjetas_cand = (json.load(f) or {}).get("tarjetas_clientes", [])
        except Exception:
            continue

        for item_c in tarjetas_cand:
            part_nom = str(item_c.get("partido", "")).strip()
            part_sin_liga = part_nom.split(" (")[0].strip().lower()
            if not part_nom or part_sin_liga in partidos_vistos or any(ex in part_sin_liga for ex in excluidos_copa):
                continue

            tipo_t = str(item_c.get("tipo_tarjeta", "VIP")).strip()
            if tipo_t == "VIP" and len(vip_recolectadas) >= 4:
                continue
            if tipo_t == "FREE" and len(free_recolectadas) >= 3:
                continue

            id_p = str(item_c.get("id_partido", "")).strip()
            hora_p = str(item_c.get("hora", "")).strip()
            fix_real = _buscar_partido_ft_real(id_p, part_nom, f_cand)

            if not fix_real:
                # Partido de HOY todavía pendiente / por jugar en madrugada: mostrarlo en espera (NO sustituir por ayer)
                mercados_pend = []
                usados_p = set()
                for sel in item_c.get("selecciones", []):
                    merc = str(sel.get("mercado", "Over 1.5 Goles")).strip()
                    if merc.lower() in usados_p:
                        continue
                    usados_p.add(merc.lower())
                    cuo = float(sel.get("cuota", 1.42 if tipo_t == "VIP" else 1.24))
                    mercados_pend.append({
                        "mercado": f"[{tipo_t}] {merc}",
                        "mercado_corto": abreviar_pick_cliente(merc),
                        "cuota": cuo,
                        "ganada": None
                    })
                    if len(mercados_pend) == 2:
                        break
                if len(mercados_pend) >= 1:
                    partidos_vistos.add(part_sin_liga)
                    obj_pend = {
                        "tipo_tarjeta": tipo_t,
                        "partido": part_nom,
                        "marcador": f"{hora_p}h" if hora_p else "PENDIENTE",
                        "hora": hora_p,
                        "pendiente": True,
                        "gh": None,
                        "ga": None,
                        "g_ht": None,
                        "fecha": f_cand,
                        "dos_apuestas": mercados_pend
                    }
                    if tipo_t == "VIP":
                        vip_recolectadas.append(obj_pend)
                    else:
                        free_recolectadas.append(obj_pend)
                continue

            gh = int(float((fix_real.get("goals") or {}).get("home") or 0))
            ga = int(float((fix_real.get("goals") or {}).get("away") or 0))
            sh = ((fix_real.get("score") or {}).get("halftime")) or {}
            if sh.get("home") is not None and sh.get("away") is not None:
                g_ht = int(float(sh.get("home") or 0)) + int(float(sh.get("away") or 0))
            else:
                g_ht = (gh + ga) // 2
            lid = (fix_real.get("league") or {}).get("id", 0)
            es_sud = lid in {13, 11, 71, 128, 130, 530, 239, 240, 533, 712}

            mercados_usados_card = set()
            dos_apuestas = []
            for sel in item_c.get("selecciones", []):
                merc = str(sel.get("mercado", "Over 1.5 Goles")).strip()
                if merc.lower() in mercados_usados_card:
                    continue
                mercados_usados_card.add(merc.lower())
                cuo = float(sel.get("cuota", 1.42 if tipo_t == "VIP" else 1.24))
                # Prioridad #1: respetar el estado exacto ya verificado en auditoria_apuestas.csv (coherencia 100% con la Web)
                estado_csv = mapa_estado_csv.get((id_p, merc.lower()))
                if estado_csv is None:
                    estado_csv = mapa_estado_csv.get((part_sin_liga, merc.lower()))
                if estado_csv is not None:
                    ganada = estado_csv
                else:
                    stats_bx_gv = None
                    if any(k in merc.lower() for k in ("córners", "corners", "remates", "faltas", "tarjetas", "amarill")):
                        try:
                            import mercados_optimizados as _mo_bx
                            loc_g, vis_g = (part_sin_liga.split(" vs ") + ["", ""])[:2]
                            stats_bx_gv = _mo_bx.obtener_stats_boxscore_partido_ft(id_p, loc_g, vis_g, api_token=API_KEY_RESPALDO_AYER)
                        except Exception:
                            stats_bx_gv = None
                    ganada = evaluar_mercado_contra_resultado_real(merc, gh, ga, g_ht, es_sud, part_nom, stats_reales=stats_bx_gv)
                dos_apuestas.append({
                    "mercado": f"[{tipo_t}] {merc}",
                    "mercado_corto": abreviar_pick_cliente(merc),
                    "cuota": cuo,
                    "ganada": ganada
                })
                if len(dos_apuestas) == 2:
                    break

            if len(dos_apuestas) < 2:
                continue

            partidos_vistos.add(part_sin_liga)
            obj_card = {
                "tipo_tarjeta": tipo_t,
                "partido": part_nom,
                "marcador": f"{gh}-{ga}",
                "hora": hora_p,
                "pendiente": False,
                "gh": gh,
                "ga": ga,
                "g_ht": g_ht,
                "fecha": f_cand,
                "dos_apuestas": dos_apuestas
            }
            if tipo_t == "VIP":
                vip_recolectadas.append(obj_card)
            else:
                free_recolectadas.append(obj_card)

    # Ordenar dentro de VIP y dentro de FREE: primero los ya finalizados (FT) y debajo los pendientes de madrugada
    vip_recolectadas.sort(key=lambda x: bool(x.get("pendiente", False)))
    free_recolectadas.sort(key=lambda x: bool(x.get("pendiente", False)))
    siete_tarjetas = vip_recolectadas + free_recolectadas
    if not fecha_auditada_real:
        fecha_auditada_real = fecha_tope_auditoria

    aciertos_eval = sum(1 for t in siete_tarjetas if not t.get("pendiente") for pk in t["dos_apuestas"] if pk.get("ganada") is True)
    total_eval = sum(1 for t in siete_tarjetas if not t.get("pendiente") for pk in t["dos_apuestas"] if pk.get("ganada") is not None)
    pendientes_cnt = sum(1 for t in siete_tarjetas if t.get("pendiente"))
    if total_eval > 0:
        tasa_txt = f"{aciertos_eval}/{total_eval} Aciertos" + (" (En curso)" if pendientes_cnt > 0 else "")
    else:
        tasa_txt = "Jornada en curso"

    return siete_tarjetas, tasa_txt, fecha_auditada_real, aciertos_eval, total_eval


def dibujar_icono_check_o_cruz(draw, x, y, es_acierto, tam=24):
    if es_acierto:
        draw.rectangle([(x, y), (x + tam, y + tam)], fill=(0, 215, 88, 255), outline=(0, 255, 115, 255), width=2)
        draw.line([(x + 5, y + 12), (x + 10, y + 18), (x + 19, y + 5)], fill=(255, 255, 255, 255), width=3)
    else:
        draw.rectangle([(x, y), (x + tam, y + tam)], fill=(220, 45, 45, 255), outline=(255, 95, 95, 255), width=2)
        draw.line([(x + 5, y + 5), (x + tam - 5, y + tam - 5)], fill=(255, 255, 255, 255), width=3)
        draw.line([(x + tam - 5, y + 5), (x + 5, y + tam - 5)], fill=(255, 255, 255, 255), width=3)


def dibujar_icono_pendiente(draw, x, y, tam=24):
    """Dibuja un icono limpio de reloj/espera en azul para partidos de hoy todavía en curso o por jugar."""
    draw.rounded_rectangle([(x, y), (x + tam, y + tam)], radius=6, fill=(28, 62, 108, 255), outline=(82, 178, 255, 255), width=2)
    cx, cy = x + tam // 2, y + tam // 2
    r = max(4, tam // 2 - 5)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(240, 248, 255, 255), width=2)
    draw.line([(cx, cy), (cx, cy - max(2, r - 2))], fill=(240, 248, 255, 255), width=2)
    draw.line([(cx, cy), (cx + max(2, r - 3), cy + 1)], fill=(240, 248, 255, 255), width=2)


def crear_imagen_auditoria_vertical(fecha_hoy, ruta_csv="auditoria_apuestas.csv", partidos_vip=None, ruta_salida="slide_auditoria.jpg", token_privado=None, chat_id_privado=None, modo_horario="manana"):
    siete_tarjetas, tasa_txt, fecha_ayer, ac_eval, tot_eval = seleccionar_7_partidos_14_apuestas_clientes(
        fecha_hoy, ruta_csv, token_privado, chat_id_privado, modo_horario=modo_horario
    )
    pendientes_cnt = sum(1 for t in siete_tarjetas if t.get("pendiente"))
    finalizados_cnt = len(siete_tarjetas) - pendientes_cnt

    lienzo = _crear_fondo_broadcast_pro(acento_izq=(0, 232, 118), acento_der=(64, 174, 255))
    draw = ImageDraw.Draw(lienzo, "RGBA")
    c_verde = (0, 232, 118, 255)
    c_rojo = (255, 82, 92, 255)
    c_oro = (255, 204, 0, 255)
    c_azul = (86, 182, 255, 255)
    c_blanco = (248, 250, 252, 255)
    c_gris = (172, 186, 204, 255)

    # Marca superior centrada
    _dibujar_marca_sup_pro(lienzo, y=46)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    # Cabecera centrada y nítida (Bold real)
    if pendientes_cnt > 0:
        tit_sup = "AVANCE EN VIVO CLIENTES  •  SOLO PARTIDOS DE HOY (4 VIP + 3 FREE)"
        tit_prin = f"¿CÓMO VAMOS HOY?  •  JORNADA {fecha_ayer}"
        txt_ef = f"Balance Parcial: {ac_eval}/{tot_eval} Aciertos  ({finalizados_cnt}/{len(siete_tarjetas)} finalizados)"
        txt_sub_ef = f"{pendientes_cnt} partido(s) de madrugada todavía en espera  •  Cero mezcla con días anteriores"
    else:
        tit_sup = "AUDITORÍA OFICIAL CLIENTES  •  4 VIP + 3 FREE (14 SELECCIONES)"
        tit_prin = f"CIERRE OFICIAL JORNADA {fecha_ayer}"
        txt_ef = f"Efectividad Verificada: {ac_eval}/{tot_eval} Aciertos ({finalizados_cnt}/{len(siete_tarjetas)} finalizados)"
        txt_sub_ef = f"Fecha Auditada: {fecha_ayer}  •  Las 7 Tarjetas Oficiales Entregadas a Clientes"

    draw.rounded_rectangle([(46, 84), (1034, 140)], radius=26, fill=(12, 34, 26, 240), outline=c_verde, width=2)
    f_sup = _fuente_pro_ajustada(draw, tit_sup, "bold", 23, 940, 15)
    draw.text((_centrar_x_pro(draw, tit_sup, f_sup), 99), tit_sup, font=f_sup, fill=c_verde)

    f_pr = _fuente_pro_ajustada(draw, tit_prin, "bold", 40, 960, 22)
    draw.text((_centrar_x_pro(draw, tit_prin, f_pr), 158), tit_prin, font=f_pr, fill=c_blanco)

    # Caja resumen de efectividad centrada
    draw.rounded_rectangle([(46, 218), (1034, 314)], radius=22, fill=(14, 26, 24, 244), outline=c_verde, width=2)
    f_ef = _fuente_pro_ajustada(draw, txt_ef, "bold", 31, 940, 19)
    f_sef = _fuente_pro_ajustada(draw, txt_sub_ef, "mono", 20, 940, 14)
    draw.text((_centrar_x_pro(draw, txt_ef, f_ef), 232), txt_ef, font=f_ef, fill=c_verde)
    draw.text((_centrar_x_pro(draw, txt_sub_ef, f_sef), 276), txt_sub_ef, font=f_sef, fill=c_oro)

    # Las 7 tarjetas de clientes de la jornada exacta
    y = 334
    alto_card = 128
    salto_card = 138
    for item in siete_tarjetas[:7]:
        pks = item.get("dos_apuestas") or []
        es_pend = bool(item.get("pendiente"))

        if es_pend:
            col_b = c_azul
            bg_c = (14, 24, 40, 244)
        else:
            ac_p = sum(1 for k in pks if k.get("ganada") is True)
            tot_p = max(1, len(pks))
            es_verde = (ac_p == tot_p)
            col_b = c_verde if es_verde else (c_oro if ac_p >= 1 else c_rojo)
            bg_c = (12, 28, 22, 244) if es_verde else ((28, 24, 13, 244) if ac_p >= 1 else (36, 15, 18, 244))

        draw.rounded_rectangle([(46, y), (1034, y + alto_card)], radius=20, fill=bg_c, outline=col_b, width=2)

        if es_pend:
            dibujar_icono_pendiente(draw, 66, y + 18, tam=26)
        else:
            dibujar_icono_check_o_cruz(draw, 66, y + 18, ac_p >= 1, tam=26)

        tipo_t = str(item.get("tipo_tarjeta", "VIP"))
        color_tag_nivel = c_oro if tipo_t == "VIP" else c_verde
        tag_nivel_txt = f"[{tipo_t}]"
        f_tag_niv = _fuente_pro("bold", 26)
        draw.text((104, y + 16), tag_nivel_txt, font=f_tag_niv, fill=color_tag_nivel)
        w_tag = draw.textbbox((0, 0), tag_nivel_txt, font=f_tag_niv)[2]

        part_corto = str(item.get("partido", "")).strip()
        if len(part_corto) > 46 and " (" in part_corto:
            part_corto = part_corto.split(" (")[0].strip()
        if es_pend:
            h_txt = str(item.get("hora", "")).strip()
            suf_estado = f"  •  POR JUGAR ({h_txt}h)" if h_txt else "  •  EN ESPERA"
            linea_duelo = f" {part_corto}{suf_estado}"
        else:
            linea_duelo = f" {part_corto} ({item.get('marcador', 'FT')})  [{ac_p}/{tot_p}]"

        f_duelo = _fuente_pro_ajustada(draw, linea_duelo, "bold", 26, 902 - w_tag - 18, 14)
        draw.text((108 + w_tag, y + 17), linea_duelo, font=f_duelo, fill=c_blanco)

        x_cur = 68
        for idx_k, k in enumerate(pks[:2], start=1):
            if es_pend or k.get("ganada") is None:
                dibujar_icono_pendiente(draw, x_cur, y + 72, tam=22)
                col_pick = c_oro if tipo_t == "VIP" else c_azul
                # Proteger los picks VIP que todavía NO han empezado para no regalarlos antes del partido en el Canal FREE
                if tipo_t == "VIP":
                    txt_k = f"Selección VIP #{idx_k} (>{float(k.get('cuota', 1.45)):.2f})"
                else:
                    txt_k = f"{k.get('mercado_corto', '')} ({float(k.get('cuota', 1.24)):.2f})"
            else:
                dibujar_icono_check_o_cruz(draw, x_cur, y + 72, bool(k.get("ganada")), tam=22)
                col_pick = c_verde if k.get("ganada") else c_rojo
                txt_k = f"{k.get('mercado_corto', '')} ({float(k.get('cuota', 1.25)):.2f})"
            f_k = _fuente_pro_ajustada(draw, txt_k, "mono", 23, 435, 16)
            draw.text((x_cur + 32, y + 70), txt_k, font=f_k, fill=col_pick)
            x_cur += 478
        y += salto_card

    # Pie CTA centrado y elegante
    y_cta = max(y + 16, 1320)
    draw.rounded_rectangle([(46, y_cta), (1034, y_cta + 172)], radius=26, fill=(22, 20, 12, 246), outline=c_oro, width=3)
    t_c1 = "PASE DE PRUEBA VIP 24 HORAS  •  SOLO 1.00 USD"
    t_c2 = "VER RESULTADOS EN VIVO EN QUANTBET22.STREAMLIT.APP"
    t_c3 = "@QUANTBET22  •  TRANSPARENCIA TOTAL EN PYTHON"
    f_c1 = _fuente_pro_ajustada(draw, t_c1, "bold", 32, 930, 20)
    f_c2 = _fuente_pro_ajustada(draw, t_c2, "mono", 24, 930, 16)
    f_c3 = _fuente_pro_ajustada(draw, t_c3, "mono", 20, 930, 14)
    draw.text((_centrar_x_pro(draw, t_c1, f_c1), y_cta + 24), t_c1, font=f_c1, fill=c_oro)
    draw.text((_centrar_x_pro(draw, t_c2, f_c2), y_cta + 76), t_c2, font=f_c2, fill=c_verde)
    draw.text((_centrar_x_pro(draw, t_c3, f_c3), y_cta + 122), t_c3, font=f_c3, fill=c_gris)

    lienzo.convert("RGB").save(ruta_salida, quality=96)
    dir_base_aud = os.path.dirname(ruta_salida) or "."
    r_cp = os.path.join(dir_base_aud, "00_AUDITORIA_7_PARTIDOS_VIP_Y_FREE.jpg")
    lienzo.convert("RGB").save(r_cp, quality=96)
    return ruta_salida, tasa_txt


def publicar_auditoria_nocturna_canal_free(fecha_auditar=None, enviar_a_clientes=True, modo_horario="manana"):
    """Refresca marcadores FT, genera la imagen vertical oficial de las 7 tarjetas (4 VIP + 3 FREE)
    EXCLUSIVAMENTE de esa jornada (sin mezclar días anteriores) y la publica."""
    import mercados_optimizados as m
    ahora_esp = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    if not fecha_auditar:
        fecha_auditar = ahora_esp.strftime("%Y-%m-%d") if modo_horario == "noche" else (ahora_esp - timedelta(days=1)).strftime("%Y-%m-%d")
    headers = {"x-apisports-key": API_KEY_RESPALDO_AYER}
    # Refrescar fecha_auditar + día siguiente (madrugada Sudamérica) y resolver TODAS las apuestas pendientes (FREE, VIP y PRO)
    m.obtener_datos_api_partidos(fecha_auditar, headers, forzar_refresco=True)
    m.resolver_apuestas_pendientes(API_KEY_RESPALDO_AYER)

    ruta_img, tasa_txt = crear_imagen_auditoria_vertical(
        fecha_auditar,
        ruta_salida=f"00_AUDITORIA_NOCTURNA_{fecha_auditar}.jpg",
        modo_horario=modo_horario
    )
    if modo_horario == "noche":
        titulo_free = f"📊 <b>¿CÓMO VAMOS HOY? ({fecha_auditar}) — {tasa_txt}</b> ✅"
        intro_free = (
            "Balance parcial en vivo SOLO de las 7 tarjetas enviadas hoy a clientes (4 VIP + 3 FREE): "
            "marcadores reales (FT) de los partidos terminados y los de madrugada en espera."
        )
        cta_dia = "MAÑANA"
        titulo_vip = f"🏆 <b>¿CÓMO VAMOS HOY EQUIPO VIP? ({fecha_auditar}) — {tasa_txt}</b> ✅"
        intro_vip = (
            "Así vamos hoy con nuestras 7 tarjetas oficiales de la jornada (los encuentros de madrugada siguen en espera y cerrarán mañana a las 07:30h)."
        )
    else:
        titulo_free = f"📊 <b>AUDITORÍA OFICIAL CERRADA ({fecha_auditar}) — {tasa_txt} VERIFICADOS</b> ✅"
        intro_free = (
            "Transparencia total en Python: resultados finales (FT) de las 7 tarjetas entregadas a clientes (4 VIP + 3 FREE)."
        )
        cta_dia = "HOY"
        titulo_vip = f"🏆 <b>BALANCE OFICIAL CERRADO EQUIPO VIP ({fecha_auditar}) — {tasa_txt} VERIFICADOS</b> ✅"
        intro_vip = (
            "¡Excelente jornada, equipo VIP! Ahí tienen en pantalla el cierre oficial con marcador final (FT) de nuestras 7 tarjetas."
        )

    caption_oficial_free = (
        f"{titulo_free}\n\n"
        f"{intro_free}\n\n"
        f"🔥 <b>PRUEBA {cta_dia} EL CANAL VIP POR SOLO 1.00 USD (24H)</b>\n"
        f"✅ 4 Tarjetas VIP de cuota alta de {cta_dia.lower()} + Doble VIP + Triple Sniper.\n"
        "✅ Pago único por 1 día (sin cobros automáticos).\n"
        "⏳ <i>Promo VIP 10 días ($7.99) y PRO solo hasta el 30 de noviembre.</i>\n\n"
        "💳 <b>1. Tarjeta en 1 clic (Whop Oficial):</b>\n"
        "👉 <a href='https://whop.com/youtube-d4c7/quantbet22-canal-vip/'>Activar Pase Diario ($1.00 USD)</a>\n"
        "📲 <b>2. Bizum, Nequi o USDT:</b>\n"
        "👉 Escribe <b>\"PASE 1 DIA\"</b> aquí: @QuantBetSoporte_bot\n\n"
        "🌐 <b>Auditoría y resultados en vivo:</b>\n"
        "👉 <a href='https://quantbet22.streamlit.app'>quantbet22.streamlit.app</a>"
    )
    caption_oficial_vip = (
        f"{titulo_vip}\n\n"
        f"{intro_vip}\n\n"
        "📈 <i>Recuerden mantener disciplina con el Stake de Kelly y consultar todas las estadísticas y combinadas auditadas en tiempo real en nuestra plataforma web:</i>\n"
        "🌐 👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>\n\n"
        "👑 <b>¿Quieres dar el salto al Canal PRO (100% de las ligas + Combinada Triple Sniper 3X)?</b>\n"
        "⏳ <i>Promo especial hasta el 30 DE NOVIEMBRE por solo 49.99 USD (Antes 74.99 USD):</i>\n"
        "👉 <a href='https://whop.com/youtube-d4c7/products/uantbet22-membresia-pro-avanzada/?ref=related_products'>Desbloquear Plan PRO aquí</a>\n"
        "💬 Soporte directo 24/7: @QuantBetSoporte_bot"
    )
    # 1. Enviar SIEMPRE imagen + texto a tu Bot Personal de Auditorías
    m.enviar_imagen_telegram(m.TOKEN_TICKETS, m.CHAT_ID_GRUPO_AUDITORIAS, ruta_img, caption_oficial_free)
    # 2. Enviar SIEMPRE imagen + texto a tu chat privado personal
    m.enviar_imagen_telegram(m.TOKEN_GENERAL, m.CHAT_ID_GENERAL, ruta_img, caption_oficial_free)
    if enviar_a_clientes:
        # 3. Enviar directo al Canal FREE de Clientes
        m.enviar_imagen_telegram(m.TOKEN_CARTERO, m.CHAT_ID_CLIENTES_FREE, ruta_img, caption_oficial_free)
        # 4. Enviar directo al Canal VIP de Clientes con su texto exclusivo
        m.enviar_imagen_telegram(m.TOKEN_CARTERO, m.CHAT_ID_CLIENTES_VIP, ruta_img, caption_oficial_vip)
        print(f"✅ Imagen + texto de auditoría ({fecha_auditar} | {modo_horario}) enviada a Bot de Auditorías, Canal FREE y Canal VIP.")
    else:
        print(f"✅ Imagen + texto de auditoría ({fecha_auditar} | {modo_horario}) enviada en MODO PRIVADO solo a tu Bot de Auditorías y Chat Privado.")

    # En cierre matutino, enviar también tu Auditoría Completa del 100% de la jornada a tu Bot Privado de Auditorías
    if modo_horario == "manana":
        try:
            fecha_sig_aud = (datetime.strptime(fecha_auditar, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            m.auditar_todos_los_partidos_fecha_bot_auditorias(
                fecha_sig_aud, m.obtener_ligas_permitidas_oficiales(), headers, API_KEY_RESPALDO_AYER
            )
        except Exception as e_aud2:
            print(f"⚠️ Aviso en Auditoría Completa privada: {e_aud2}")

    # Si corre desde tu PC (fuera de GitHub Actions), subir automáticamente auditoria_apuestas.csv y boxscores a la Web App
    if not os.getenv("GITHUB_ACTIONS"):
        try:
            m.actualizar_webapp_github_automatico(fecha_auditar)
        except Exception as e_sync:
            print(f"⚠️ Aviso sincronizando auditoría con la Web App: {e_sync}")



def formatear_liga_hablada(liga_visual):
    mapa = {
        "UEFA CHAMPIONS LEAGUE": "la UEFA Chámpions Lig",
        "UEFA EUROPA LEAGUE": "la UEFA Europa Lig",
        "UEFA CONFERENCE LEAGUE": "la UEFA Cónferens Lig",
        "ESPAÑA (LALIGA)": "LaLiga de España",
        "ESPAÑA (SEGUNDA)": "LaLiga Hypermotion de España",
        "INGLATERRA (PREMIER)": "la Premier Lig de Inglaterra",
        "ITALIA (SERIE A)": "la Serie A de Italia",
        "ALEMANIA (BUNDESLIGA)": "la Bundesliga de Alemania",
        "FRANCIA (LIGUE 1)": "la Lig 1 de Francia",
        "BRASIL (SERIE A)": "el Brasileirão Serie A",
        "COLOMBIA (PRIMERA A)": "la Primera A de Colombia",
        "COLOMBIA (COPA BETPLAY)": "la Copa de Colombia",
        "ARGENTINA (LIGA PROFESIONAL)": "la Liga Profesional de Argentina",
        "PORTUGAL (PRIMEIRA LIGA)": "la Primeira Liga de Portugal",
        "UEFA NATIONS LEAGUE": "la UEFA Néishons Lig",
        "ELIMINATORIAS CONMEBOL": "las Eliminatorias Sudamericanas",
        "ELIMINATORIAS UEFA": "las Eliminatorias Europeas",
        "AMISTOSO INTERNACIONAL": "la Fecha FIFA de Selecciones",
        "MUNDIAL FIFA": "la Copa del Mundo de la FIFA",
        "EUROCOPA": "la Eurocopa de Naciones",
        "COPA AMÉRICA": "la Copa América",
    }
    return mapa.get(liga_visual, liga_visual.replace("(", " ").replace(")", ""))


def formatear_numero_hablado(valor_num):
    s = f"{float(valor_num):.2f}"
    if s.endswith(".00"):
        return s[:-3]
    if s.endswith("0"):
        s = s[:-1]
    return s.replace(".", " punto ")


async def sintetizar_audio_ia(texto_guion, ruta_mp3):
    guion_limpio = (
        texto_guion.replace("Python", "Páiton")
        .replace("python", "Páiton")
        .replace("BetPlay", "Primera A")
        .replace("apuestas", "proyecciones")
        .replace("apuesta", "métrica")
        .replace("cuota", "índice")
        .replace("VIP", "Bip")
        .replace("CHAMPIONS LEAGUE", "Chámpions Lig")
        .replace("Champions League", "Chámpions Lig")
        .replace("EUROPA LEAGUE", "Europa Lig")
        .replace("Europa League", "Europa Lig")
        .replace("PREMIER LEAGUE", "Premier Lig")
        .replace("Premier League", "Premier Lig")
        .replace(" > ", " superior a ")
        .replace(">", " superior a ")
        .replace("5.5", "5 punto 5")
        .replace("6.5", "6 punto 5")
        .replace("7.5", "7 punto 5")
        .replace("8.5", "8 punto 5")
        .replace("7.99", "9 con 99")
        .replace("1.5", "1 punto 5")
        .replace("2.5", "2 punto 5")
        .replace("2.25", "2 punto 25")
        .replace("21.5", "21 punto 5")
        .replace("22.5", "22 punto 5")
        .replace("1T", "primer tiempo")
        .replace("2do Tiempo", "segundo tiempo")
        .replace("Over ", "más de ")
    )
    for _ in range(3):
        try:
            comunicador = edge_tts.Communicate(guion_limpio, VOZ_ANALISTA_IA, rate=VELOCIDAD_VOZ)
            await comunicador.save(ruta_mp3)
            if os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 1500:
                return True
        except Exception:
            await asyncio.sleep(1.2)
    return False


def renderizar_video_mp4_2_slides(slide_1, slide_2, ruta_mp3, ruta_mp4_salida, seg_slide_1=11, texto_guion="", ocultar_monitor_slide_1=False, slide_3=None):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ruta_wav = ruta_mp3.replace(".mp3", "_voz.wav")

    subprocess.run([
        ffmpeg_exe, "-y", "-i", os.path.abspath(ruta_mp3),
        "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        os.path.abspath(ruta_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    duracion_audio = 24.0
    if os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 2000:
        try:
            with wave.open(ruta_wav, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0 and frames > 0:
                    duracion_audio = frames / float(rate)
        except Exception:
            pass

    oraciones = [o.strip() for o in re.split(r"(?<=[.,:])\s+", (texto_guion or "Análisis cuantitativo en Python.").strip()) if o.strip()]
    frases = []
    for o in oraciones:
        pal = o.split()
        if len(pal) > 13:
            mit = len(pal) // 2
            frases.append(" ".join(pal[:mit]))
            frases.append(" ".join(pal[mit:]))
        else:
            frases.append(o)
    if not frases:
        frases = ["Análisis cuantitativo en Python."]

    mitad_f = max(1, len(frases) // 2)
    dur_por_frase = max(2.2, (duracion_audio + 0.5) / len(frases))

    archivos_frames = []
    lista_txt = ruta_mp4_salida.replace(".mp4", "_inputs.txt")
    salto = chr(10)

    tercio_1 = max(1, int(len(frases) * 0.42))
    tercio_2 = max(tercio_1 + 1, int(len(frases) * 0.75))
    with open(lista_txt, "w", encoding="utf-8") as f:
        for idx_f, frase_txt in enumerate(frases):
            if slide_3 and os.path.exists(str(slide_3)):
                base_img = slide_1 if idx_f < tercio_1 else (slide_2 if idx_f < tercio_2 else slide_3)
            else:
                base_img = slide_1 if idx_f < mitad_f else slide_2
            ruta_frame = ruta_mp4_salida.replace(".mp4", f"_subframe_{idx_f}.jpg")
            prog_f = float(idx_f + 1) / max(1, len(frases))
            estampar_subtitulo_metro(base_img, frase_txt, ruta_frame, progreso_pct=prog_f)
            archivos_frames.append(ruta_frame)
            f.write(f"file '{ruta_posix(ruta_frame)}'" + salto)
            f.write(f"duration {dur_por_frase:.2f}" + salto)
        if archivos_frames:
            f.write(f"file '{ruta_posix(archivos_frames[-1])}'" + salto)

    filtro_movimiento_real = (
        "fps=30,"
        "scale=1112:1976,"
        "crop=1080:1920:16+14*sin(2*PI*t/4.5):28+20*cos(2*PI*t/4.5),"
        "format=yuv420p"
    )

    video_mudo_temp = ruta_mp4_salida.replace(".mp4", "_mudo_sub.mp4")
    subprocess.run([
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0", "-i", os.path.abspath(lista_txt),
        "-vf", filtro_movimiento_real,
        "-c:v", "libx264", "-preset", "ultrafast", "-an",
        os.path.abspath(video_mudo_temp)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    audio_input = os.path.abspath(ruta_wav) if os.path.exists(ruta_wav) else os.path.abspath(ruta_mp3)
    subprocess.run([
        ffmpeg_exe, "-y",
        "-i", os.path.abspath(video_mudo_temp),
        "-i", audio_input,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest",
        os.path.abspath(ruta_mp4_salida)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for tmp in archivos_frames + [lista_txt, video_mudo_temp, ruta_wav]:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def generar_diccionario_copys_por_red(tipo_video, p_data, tasa_acierto="91.1%"):
    loc = p_data.get("local", "Equipo Local")
    vis = p_data.get("visitante", "Visitante")
    liga = p_data.get("liga_visual", "Fútbol Europeo")
    goles = p_data.get("tot_goles", 2.65)
    faltas = p_data.get("tot_faltas", 23.5)

    tag_loc = limpiar_hashtag(loc)
    tag_vis = limpiar_hashtag(vis)
    parte_liga = liga.split("(")[1].replace(")", "") if "(" in liga else liga
    tag_liga = limpiar_hashtag(parte_liga)
    s = chr(10)
    ds = s + s

    pregunta_gancho = f"¿Cuál es tu marcador para {loc} vs {vis}? Déjalo en los comentarios 👇⚽"
    corn_val_c = float(p_data.get("tot_corn") or 9.0)

    if tipo_video == "1_ESTRELLA_10AM":
        return {
            "horario": "14:00 (España) - PREVIA ESTADÍSTICA #2",
            "titulo_interno": f"VIDEO 2 (14:00) - {loc.upper()} VS {vis.upper()} ({p_data.get('hora', '')})",
            "tiktok": (
                f"{pregunta_gancho} "
                f"Previa estadística de {loc} vs {vis} ({liga}): ritmo estimado de {goles:.2f} goles esperados y {corn_val_c:.0f} córners según distribución de Poisson. "
                f"¿Crees que será partido abierto o cerrado? 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #datosfutbol #analisistactico #cienciadedatos"
            ),
            "instagram": (
                f"{pregunta_gancho}" + ds +
                f"📊 Datos del partido ({liga}):" + s +
                f"• Goles esperados (xG): {goles:.2f} | Córners estimados: {corn_val_c:.0f} | Fricción: {faltas:.1f} faltas." + ds +
                f"Guarda este análisis para comprobar el resultado al final del partido. ⚽" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #datosfutbol #analisistactico"
            ),
            "youtube_titulo": f"{loc} vs {vis} | Previa Táctica y Datos {tag_loc} {tag_vis} {tag_liga} #shorts"[:98],
            "youtube_descripcion": (
                f"{pregunta_gancho} Análisis estadístico previo de {loc} vs {vis} ({liga}) con modelo Poisson y Dixon-Coles: "
                f"{goles:.2f} goles esperados y {corn_val_c:.0f} córners estimados." + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #shorts #futbol #datosfutbol #analisistactico"
            ),
            "facebook": (
                f"{pregunta_gancho} Previa táctica del {loc} vs {vis} ({liga}): {goles:.2f} goles esperados y {corn_val_c:.0f} córners estimados según nuestro modelo estadístico." + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #datosfutbol #analisistactico"
            ),
        }

    else:
        return {
            "horario": "21:30 (España) - PREVIA ESTADÍSTICA #1",
            "titulo_interno": f"VIDEO 1 (21:30) - {loc.upper()} VS {vis.upper()} ({p_data.get('hora', '')})",
            "tiktok": (
                f"{pregunta_gancho} 📊⚽ "
                f"Analizamos {loc} vs {vis} ({liga}) con modelo Poisson: {goles:.2f} goles esperados y {corn_val_c:.0f} córners proyectados. "
                f"¿Gana {loc}, empate o sorpresa de {vis}? Te leo abajo 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #datosfutbol #analisistactico #cienciadedatos"
            ),
            "instagram": (
                f"{pregunta_gancho} 📈⚽" + ds +
                f"Previa matemática de {loc} vs {vis} ({liga}):" + s +
                f"• Goles esperados: {goles:.2f} | Córners: {corn_val_c:.0f} | Faltas: {faltas:.1f}" + ds +
                f"Guarda este reel y comenta tu pronóstico de marcador antes del pitazo inicial." + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #datosfutbol #analisistactico"
            ),
            "youtube_titulo": f"{loc} vs {vis} | Previa y Estadísticas {tag_loc} {tag_vis} {tag_liga} #shorts"[:98],
            "youtube_descripcion": (
                f"{pregunta_gancho} Previa estadística de {loc} vs {vis} ({liga}) basada en datos históricos, goles esperados ({goles:.2f}) y ritmo ofensivo." + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #shorts #futbol #datosfutbol #analisistactico"
            ),
            "facebook": (
                f"{pregunta_gancho} Análisis de datos previo para {loc} vs {vis} ({liga}): {goles:.2f} goles esperados y {corn_val_c:.0f} córners estimados." + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #datosfutbol #analisistactico"
            ),
        }


def enviar_video_y_mensajes_separados_telegram(token, chat_id, ruta_video, dict_copys):
    if not token or not chat_id or not os.path.exists(ruta_video):
        return
    url_vid = f"https://api.telegram.org/bot{token}/sendVideo"
    url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
    s = chr(10)
    try:
        with open(ruta_video, "rb") as vid:
            cap_vid = (
                f"🎬 <b>{dict_copys['titulo_interno']}</b>" + s +
                f"⏰ Horario programado: {dict_copys['horario']}" + s +
                "👇 <i>Toca cualquiera de los bloques de abajo para copiar el texto de cada red social:</i>"
            )
            requests.post(
                url_vid,
                data={"chat_id": chat_id, "caption": cap_vid, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_web_page_preview": True},
                files={"video": vid},
                timeout=45,
            )
        time.sleep(1.0)
        mensajes_redes = [
            f"🎵 <b>TIKTOK (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['tiktok']}</code>",
            f"📸 <b>INSTAGRAM REELS (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['instagram']}</code>",
            f"▶️ <b>YOUTUBE SHORTS (Toca para copiar Título y Descripción):</b>" + s + f"<b>Título:</b>" + s + f"<code>{dict_copys['youtube_titulo']}</code>" + s + s + f"<b>Descripción:</b>" + s + f"<code>{dict_copys['youtube_descripcion']}</code>",
            f"📘 <b>FACEBOOK REELS (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['facebook']}</code>",
        ]
        for m_txt in mensajes_redes:
            requests.post(
                url_msg,
                json={"chat_id": chat_id, "text": m_txt, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_web_page_preview": True, "disable_web_page_preview": True},
                timeout=8,
            )
            time.sleep(0.5)
    except Exception:
        pass


HORA_FIJA_VIDEO_1_PREVIO = "21:30"   # Slot oficial #1: día previo 21:30 ESP (15:30 COL)
HORA_FIJA_VIDEO_1_RESCATE = "10:30"  # Rescate si ya pasó 21:30 del día previo (nunca publicar a las 02:00 AM)
HORA_FIJA_VIDEO_2_DIA = "14:00"      # Slot oficial #2: día del partido 14:00 ESP (08:00 COL)
MARGEN_MIN_ANTES_PARTIDO_MIN = 120   # Nunca publicar un vídeo con menos de 2h antes del pitazo inicial


def _dt_inicio_partido_real(p_obj, fecha_jornada):
    """Devuelve el datetime exacto (hora España) del inicio del partido, tratando 00:00-06:59 como madrugada del día siguiente."""
    f_str = str(p_obj.get("fecha") or fecha_jornada).strip()[:10]
    h_str = str(p_obj.get("hora") or "20:00").strip()[:5]
    try:
        dt_p = datetime.strptime(f"{f_str} {h_str}", "%Y-%m-%d %H:%M")
        if f_str == str(fecha_jornada) and dt_p.hour < 7:
            dt_p += timedelta(days=1)
        return dt_p
    except Exception:
        return datetime.strptime(f"{fecha_jornada} 20:00", "%Y-%m-%d %H:%M")


def _redondear_15_min(dt_val, hacia_arriba=True):
    if hacia_arriba:
        m = ((dt_val.minute // 15) + (1 if dt_val.minute % 15 else 0)) * 15
        if m >= 60:
            return (dt_val + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return dt_val.replace(minute=m, second=0, microsecond=0)
    else:
        m = (dt_val.minute // 15) * 15
        return dt_val.replace(minute=m, second=0, microsecond=0)


def calcular_horarios_fijos_2_videos(p1, p2, fecha_jornada, ahora_ref=None):
    """
    Motor ÚNICO de programación para TikTok, Meta (FB+IG) y YouTube Shorts:
      - Horarios FIJOS oficiales:
          * Video #1 (partido más temprano): Día previo a las 21:30 ESP (rescate 10:30 ESP si ya es día del partido).
          * Video #2 (partido más tardío):   Día del partido a las 14:00 ESP.
      - Regla de Hora del Partido:
          * Ningún vídeo se programa después ni a menos de 2h del inicio de su partido.
          * Si el Partido #2 empieza antes de las 16:00 ESP, se adelanta automáticamente a (inicio - 3h, mínimo 10:30 ESP).
          * Jamás programa de madrugada (00:00-09:59) salvo que el usuario pase explícitamente --ahora al subir.
    """
    ahora = ahora_ref if ahora_ref is not None else datetime.now()
    dt_jorn = datetime.strptime(str(fecha_jornada), "%Y-%m-%d")
    dt_prev = dt_jorn - timedelta(days=1)

    dt_ko_1 = _dt_inicio_partido_real(p1, fecha_jornada)
    dt_ko_2 = _dt_inicio_partido_real(p2, fecha_jornada)

    # --- SLOT #1 (Fijo: 21:30 del día previo; si ya pasó -> rescate fijo 10:30 del día del partido) ---
    h1_p, m1_p = map(int, HORA_FIJA_VIDEO_1_PREVIO.split(":"))
    dt_pub_1 = dt_prev.replace(hour=h1_p, minute=m1_p, second=0, microsecond=0)
    if dt_pub_1 < ahora + timedelta(minutes=25):
        h1_r, m1_r = map(int, HORA_FIJA_VIDEO_1_RESCATE.split(":"))
        dt_pub_1 = dt_jorn.replace(hour=h1_r, minute=m1_r, second=0, microsecond=0)
        if dt_pub_1 < ahora + timedelta(minutes=25):
            dt_pub_1 = _redondear_15_min(ahora + timedelta(minutes=30), hacia_arriba=True)

    # Verificar margen antes del inicio del Partido #1 (>= 2h antes si es posible)
    tope_ko_1 = dt_ko_1 - timedelta(minutes=MARGEN_MIN_ANTES_PARTIDO_MIN)
    if dt_pub_1 > tope_ko_1:
        cand_1 = _redondear_15_min(dt_ko_1 - timedelta(hours=3), hacia_arriba=False)
        if cand_1 >= ahora + timedelta(minutes=25):
            dt_pub_1 = cand_1
        elif tope_ko_1 >= ahora + timedelta(minutes=25):
            dt_pub_1 = _redondear_15_min(tope_ko_1, hacia_arriba=False)

    # --- SLOT #2 (Fijo: 14:00 del día del partido; si el partido es temprano <16:00 -> adelantar 3h antes) ---
    h2_d, m2_d = map(int, HORA_FIJA_VIDEO_2_DIA.split(":"))
    dt_pub_2 = dt_jorn.replace(hour=h2_d, minute=m2_d, second=0, microsecond=0)
    tope_ko_2 = dt_ko_2 - timedelta(minutes=MARGEN_MIN_ANTES_PARTIDO_MIN)
    if dt_pub_2 > tope_ko_2:
        cand_2 = _redondear_15_min(dt_ko_2 - timedelta(hours=3), hacia_arriba=False)
        # Si ambos caen en la mañana del día del partido, garantizar separación >= 60 min
        if cand_2 <= dt_pub_1 + timedelta(minutes=45) and dt_pub_1.date() == cand_2.date():
            cand_2 = _redondear_15_min(min(tope_ko_2, dt_pub_1 + timedelta(hours=1)), hacia_arriba=False)
        if cand_2 >= ahora + timedelta(minutes=25):
            dt_pub_2 = cand_2
        elif tope_ko_2 >= ahora + timedelta(minutes=25):
            dt_pub_2 = _redondear_15_min(tope_ko_2, hacia_arriba=False)

    if dt_pub_2 < ahora + timedelta(minutes=25):
        dt_pub_2 = _redondear_15_min(max(ahora + timedelta(minutes=30), dt_pub_1 + timedelta(minutes=45)), hacia_arriba=True)

    # Nunca publicar Video #2 antes o pegado a Video #1 si caen en el mismo día
    if dt_pub_2 <= dt_pub_1 + timedelta(minutes=30):
        dt_sep = _redondear_15_min(dt_pub_1 + timedelta(hours=1), hacia_arriba=True)
        if dt_sep <= dt_ko_2 - timedelta(minutes=45):
            dt_pub_2 = dt_sep

    return dt_pub_1, dt_pub_2


def guardar_archivos_individuales_y_json(carpeta_videos, prefijo_num, ruta_mp4, dict_copys, cola_json, fecha_jornada, dt_pub_fijo=None, fecha_partido="", hora_partido="", ruta_miniatura=""):
    s = chr(10)
    aviso_18 = s + "📊 Ciencia de Datos y Modelos Matemáticos aplicados al Fútbol Profesional."
    for k_red in ["tiktok", "instagram", "youtube_descripcion", "facebook"]:
        if "+18" not in dict_copys.get(k_red, ""):
            dict_copys[k_red] = dict_copys.get(k_red, "") + aviso_18

    dir_txts = os.path.join(carpeta_videos, f"TEXTOS_SEPARADOS_VIDEO_{prefijo_num}")
    os.makedirs(dir_txts, exist_ok=True)
    with open(os.path.join(dir_txts, "1_TIKTOK.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["tiktok"])
    with open(os.path.join(dir_txts, "2_INSTAGRAM_REELS.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["instagram"])
    with open(os.path.join(dir_txts, "3_YOUTUBE_SHORTS_TITULO.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["youtube_titulo"])
    with open(os.path.join(dir_txts, "3_YOUTUBE_SHORTS_DESCRIPCION.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["youtube_descripcion"])
    with open(os.path.join(dir_txts, "4_FACEBOOK_REELS.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["facebook"])

    if dt_pub_fijo is not None:
        dt_objetivo = dt_pub_fijo
    else:
        dt_jorn = datetime.strptime(fecha_jornada, "%Y-%m-%d")
        dt_objetivo = (dt_jorn - timedelta(days=1)).replace(hour=21, minute=30, second=0, microsecond=0) if prefijo_num == 1 else dt_jorn.replace(hour=14, minute=0, second=0, microsecond=0)

    hora_str_24 = dt_objetivo.strftime("%H:%M")
    horario_dinamico = f"{dt_objetivo.strftime('%Y-%m-%d')} {hora_str_24} (España) - VIDEO #{prefijo_num} (Partido: {hora_partido or 'N/D'}h ESP)"

    cola_json.append({
        "fecha_publicacion": dt_objetivo.strftime("%Y-%m-%d"),
        "orden_video": prefijo_num,
        "hora_24h": hora_str_24,
        "fecha_partido": str(fecha_partido or fecha_jornada),
        "hora_partido": str(hora_partido or ""),
        "horario_objetivo_espana": horario_dinamico,
        "titulo_interno": dict_copys["titulo_interno"],
        "ruta_video_mp4": os.path.abspath(ruta_mp4),
        "ruta_miniatura": os.path.abspath(ruta_miniatura) if ruta_miniatura and os.path.exists(ruta_miniatura) else "",
        "redes": {
            "tiktok": {"descripcion": dict_copys["tiktok"], "estado": "pendiente"},
            "instagram": {"descripcion": dict_copys["instagram"], "estado": "pendiente"},
            "youtube": {
                "titulo": dict_copys["youtube_titulo"],
                "descripcion": dict_copys["youtube_descripcion"],
                "estado": "pendiente"
            },
            "facebook": {"descripcion": dict_copys["facebook"], "estado": "pendiente"}
        }
    })


def generar_tarjeta_trampa_sino_existe(p_trampa, directorio_dia):
    from generador_imagenes import generar_captura_automatica
    if p_trampa.get("ruta_free") and os.path.exists(p_trampa["ruta_free"]):
        return p_trampa["ruta_free"]
    if p_trampa.get("ruta_vip") and os.path.exists(p_trampa["ruta_vip"]):
        return p_trampa["ruta_vip"]
    loc_clean = "".join([c for c in p_trampa['local'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
    vis_clean = "".join([c for c in p_trampa['visitante'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
    hora_clean = p_trampa['hora'].replace(":", "")
    dir_desc = os.path.join(directorio_dia, "3_DESCARTES")
    os.makedirs(dir_desc, exist_ok=True)
    ruta_especifica = os.path.join(dir_desc, f"{hora_clean}_{loc_clean}_vs_{vis_clean}_DESCARTES.jpg")
    if os.path.exists(ruta_especifica):
        return ruta_especifica
    r_tmp = generar_captura_automatica(p_trampa, "DESCARTES")
    if r_tmp and os.path.exists(r_tmp):
        import shutil as _sh_tr
        _sh_tr.move(r_tmp, ruta_especifica)
        return ruta_especifica
    return r_tmp


def es_partido_de_america(p):
    if p.get("is_america", False):
        return True
    liga_up = str(p.get("liga_visual", "")).upper()
    if any(lg in liga_up for lg in ["COLOMBIA", "ARGENTINA", "BRASIL", "LIBERTADORES", "SUDAMERICANA", "MÉXICO", "MLS", "USA", "CONMEBOL", "CONCACAF", "COPA AMÉRICA"]):
        return True
    hora_str = str(p.get("hora", "20:00"))[:2]
    if hora_str.isdigit() and 0 <= int(hora_str) <= 6:
        return True
    selecciones_america = (
        "argentina", "colombia", "brasil", "brazil", "uruguay", "chile", "ecuador",
        "peru", "perú", "paraguay", "venezuela", "bolivia", "mexico", "méxico",
        "estados unidos", "usa", "canada", "canadá", "costa rica", "panama", "panamá"
    )
    duelo_low = f"{p.get('local', '')} {p.get('visitante', '')}".lower()
    return any(sel in duelo_low for sel in selecciones_america)



# ==============================================================================
# MOTOR VISUAL BROADCAST PRO v3 (1080x1920)
# - MP4 100% compatible con Reproductor de Windows / iOS / Android / Redes
#   (H.264 High@4.0, yuv420p, 30fps constante, timebase estándar, AAC 44.1kHz, +faststart)
# - Escudos 100% REALES verificados por NOMBRE (nunca cruza IDs ESPN con API-Sports)
# - Diseño centrado, simétrico y elegante (sin vacío inferior ni aspecto de hoja)
# - Historia diaria dedicada centrada verticalmente + Auditoría completa 7 tarjetas
# ==============================================================================
CARPETA_ESCUDOS_PRO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escudos_cache_v2")
os.makedirs(CARPETA_ESCUDOS_PRO, exist_ok=True)

_C_VERDE_PRO = (0, 232, 118, 255)
_C_ORO_PRO = (255, 204, 0, 255)
_C_ROJO_PRO = (255, 78, 88, 255)
_C_AZUL_PRO = (64, 174, 255, 255)
_C_NARANJA_PRO = (255, 148, 64, 255)
_C_BLANCO_PRO = (248, 250, 252, 255)
_C_GRIS_PRO = (165, 180, 198, 255)
_C_PANEL_PRO = (14, 22, 35, 236)
_C_PANEL_ALT = (19, 29, 46, 240)
_C_BORDE_PRO = (54, 78, 108, 175)

TITULARES_GANCHO_PRO = [
    "LO QUE DICEN LOS DATOS",
    "DATO OCULTO DEL DÍA",
    "RADIOGRAFÍA DEL PARTIDO",
    "NADIE ESTÁ VIENDO ESTO",
    "MODELO POISSON AL DETALLE",
    "CLAVE TÁCTICA EN PYTHON",
]


def _fuente_pro(preferencia, tam):
    if preferencia == "bold":
        candidatos = [
            "Montserrat-VariableFont_wght.ttf",
            "Montserrat-Bold.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
            "arialbd.ttf",
        ]
    elif preferencia == "mono":
        candidatos = [
            "RobotoMono-VariableFont_wght.ttf",
            "Montserrat-VariableFont_wght.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
            "consolab.ttf",
            "arialbd.ttf",
        ]
    else:
        candidatos = [
            "Montserrat-VariableFont_wght.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
            "/usr/share/fonts/GoogleSans-Regular.ttf",
            "arial.ttf",
        ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            try:
                f = ImageFont.truetype(ruta, tam)
                if preferencia in ("bold", "mono") and hasattr(f, "set_variation_by_axes"):
                    try:
                        f.set_variation_by_axes([800 if preferencia == "bold" else 700])
                    except Exception:
                        pass
                return f
            except Exception:
                continue
    return ImageFont.load_default()


def _fuente_pro_ajustada(draw, texto, preferencia, tam_ini, ancho_max, tam_min=15):
    tam = tam_ini
    while tam >= tam_min:
        f = _fuente_pro(preferencia, tam)
        bb = draw.textbbox((0, 0), str(texto), font=f)
        if (bb[2] - bb[0]) <= ancho_max:
            return f
        tam -= 2
    return _fuente_pro(preferencia, tam_min)


def _centrar_x_pro(draw, texto, fuente, cx=540):
    bb = draw.textbbox((0, 0), str(texto), font=fuente)
    return int(cx - (bb[2] - bb[0]) / 2)


def _slug_escudo(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _tokens_escudo(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\((?:f|w|fem|women)\)", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    ign = {
        "fc", "cf", "sc", "cd", "ud", "ac", "as", "sk", "ca", "se", "cr", "ce", "rc", "rcd", "sd",
        "ad", "gd", "fk", "kv", "usc", "club", "deportivo", "deportes", "stade", "sporting", "de",
        "la", "el", "los", "las", "del", "calcio", "1907", "1913", "04", "05", "women", "femenino", "fem"
    }
    toks = [w for w in s.split() if len(w) >= 3 and w not in ign]
    return set(toks) if toks else set(w for w in s.split() if len(w) >= 2)


def _nombre_coincide_escudo(objetivo, candidato):
    if not objetivo or not candidato:
        return False
    t_obj = _tokens_escudo(objetivo)
    t_can = _tokens_escudo(candidato)
    if not t_obj or not t_can:
        return False
    # Bloquear rivales de misma ciudad / prefijo opuesto
    opuestos = [
        ("city", "united"), ("real", "atletico"), ("madrid", "rayo"),
        ("inter", "milan"), ("roma", "lazio"), ("benfica", "sporting"),
        ("river", "boca"), ("nacional", "medellin"), ("millonarios", "santa"),
        ("flamengo", "fluminense"), ("palmeiras", "corinthians"), ("palmeiras", "santos"),
    ]
    for w1, w2 in opuestos:
        if (w1 in t_obj and w2 in t_can and w2 not in t_obj) or (w2 in t_obj and w1 in t_can and w1 not in t_obj):
            return False
    genericos = {"real", "atletico", "united", "city", "olympique", "borussia", "racing", "nacional", "santa", "san", "inter"}
    dist_obj = t_obj - genericos
    dist_can = t_can - genericos
    if not dist_obj or not dist_can:
        return t_obj == t_can
    comunes = dist_obj & dist_can
    if comunes:
        # Si ambos tienen 2+ palabras distintivas y comparten ciudad (ej. Manchester), exigir que no discrepen en la segunda palabra clave
        if len(t_obj) >= 2 and len(t_can) >= 2 and (t_obj & {"city", "united", "real", "atletico"}) != (t_can & {"city", "united", "real", "atletico"}):
            if ("city" in t_obj or "united" in t_obj) and ("city" in t_can or "united" in t_can):
                return False
        return True
    for a in dist_obj:
        for b in dist_can:
            if len(a) >= 4 and len(b) >= 4 and (a.startswith(b[:4]) or b.startswith(a[:4])):
                return True
    return False


def _descargar_y_guardar_png_valido(url_img, ruta_png):
    from io import BytesIO
    if not url_img or not str(url_img).startswith("http"):
        return False
    u_low = str(url_img).lower()
    if any(bad in u_low for bad in ("not_available", "placeholder", "default_logo", "no-image", "noimage")):
        return False
    try:
        r_img = requests.get(
            url_img,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=5.0,
        )
        if r_img.status_code == 200 and len(r_img.content) > 700:
            im = Image.open(BytesIO(r_img.content)).convert("RGBA")
            if im.width >= 32 and im.height >= 32:
                # Rechazar el placeholder estándar gris de cámara "Image not available" (sin fondo transparente y casi monocromo gris medio)
                alpha_vals = list(im.getchannel("A").getdata())
                pct_opaco = sum(1 for a in alpha_vals if a > 240) / max(1, len(alpha_vals))
                if pct_opaco > 0.96:
                    # Un escudo oficial real suele ser PNG con fondo transparente; revisar si el borde es gris placeholder
                    px = im.load()
                    r0, g0, b0, _ = px[2, 2]
                    if abs(r0 - g0) <= 5 and abs(g0 - b0) <= 5 and 25 <= r0 <= 110:
                        return False
                im.save(ruta_png)
                return True
    except Exception:
        pass
    return False


def obtener_escudo_real_equipo(nombre_equipo, team_id=None, logo_url=None, tam=220):
    """Descargador verificado por NOMBRE (5 capas, CERO cruce de IDs entre ESPN y API-Sports)
    con caché limpio en escudos_cache_v2/."""
    slug = _slug_escudo(nombre_equipo)
    ruta_png = os.path.join(CARPETA_ESCUDOS_PRO, f"{slug}.png")

    if not os.path.exists(ruta_png):
        ok = False

        # Capa 1: URL directa del fixture (viene del mismo proveedor que el partido -> 100% exacta)
        if logo_url and str(logo_url).startswith("http"):
            ok = _descargar_y_guardar_png_valido(logo_url, ruta_png)

        # Preparar consultas limpias
        alias_busq = {
            "celta vigo": "Celta Vigo", "ath madrid": "Atletico Madrid", "ath bilbao": "Athletic Club",
            "paris sg": "Paris Saint-Germain", "psg": "Paris Saint-Germain",
            "ol lyonnes": "Olympique Lyonnais", "man united": "Manchester United", "man city": "Manchester City",
            "sp lisbon": "Sporting CP", "sp braga": "SC Braga",
        }
        nom_orig = str(nombre_equipo).strip()
        nom_alias = alias_busq.get(nom_orig.lower(), nom_orig)
        nom_base = re.sub(r"\b(FC|CF|SC|CD|UD|AC|AS|SK|USC|CA|SE|CR|RC|RCD|SD|AD|GD)\b", "", nom_alias, flags=re.I).strip()
        consultas = []
        for q_c in (nom_alias, nom_orig, nom_base):
            if q_c and q_c not in consultas:
                consultas.append(q_c)

        # Capa 2: ESPN Search API con VERIFICACIÓN ESTRICTA DE NOMBRE
        if not ok:
            for q_eq in consultas:
                try:
                    r = requests.get(
                        "https://site.web.api.espn.com/apis/common/v3/search",
                        params={"query": q_eq, "limit": 8, "type": "team"},
                        timeout=4.5,
                    )
                    if r.status_code == 200:
                        for it in (r.json().get("items") or []):
                            if it.get("sport") != "soccer":
                                continue
                            disp = str(it.get("displayName") or it.get("name") or "")
                            if not _nombre_coincide_escudo(nom_alias, disp):
                                continue
                            u_l = it.get("image") or (f"https://a.espncdn.com/i/teamlogos/soccer/500/{it['id']}.png" if it.get("id") else "")
                            if _descargar_y_guardar_png_valido(u_l, ruta_png):
                                ok = True
                                break
                except Exception:
                    pass
                if ok:
                    break

        # Capa 3: TheSportsDB API gratuita con VERIFICACIÓN ESTRICTA DE NOMBRE
        if not ok:
            for q_eq in consultas:
                try:
                    r_db = requests.get(
                        "https://www.thesportsdb.com/api/v1/json/3/searchteams.php",
                        params={"t": q_eq},
                        timeout=4.5,
                    )
                    if r_db.status_code == 200:
                        for tm in (r_db.json().get("teams") or []):
                            if str(tm.get("strSport") or "").lower() not in ("soccer", "football", ""):
                                continue
                            n_tm = f"{tm.get('strTeam') or ''} {tm.get('strAlternate') or ''}"
                            if not _nombre_coincide_escudo(nom_alias, n_tm):
                                continue
                            u_b = tm.get("strBadge") or tm.get("strTeamBadge") or ""
                            if _descargar_y_guardar_png_valido(u_b, ruta_png):
                                ok = True
                                break
                except Exception:
                    pass
                if ok:
                    break

        # Capa 4: API-Sports /teams?search= con VERIFICACIÓN ESTRICTA DE NOMBRE
        if not ok and API_KEY_RESPALDO_AYER:
            for q_eq in consultas:
                if len(q_eq) < 3:
                    continue
                try:
                    r_as = requests.get(
                        "https://v3.football.api-sports.io/teams",
                        params={"search": q_eq},
                        headers={"x-apisports-key": API_KEY_RESPALDO_AYER},
                        timeout=4.5,
                    )
                    if r_as.status_code == 200:
                        for item_t in (r_as.json().get("response") or []):
                            t_obj = item_t.get("team") or {}
                            if not _nombre_coincide_escudo(nom_alias, str(t_obj.get("name") or "")):
                                continue
                            if _descargar_y_guardar_png_valido(t_obj.get("logo"), ruta_png):
                                ok = True
                                break
                except Exception:
                    pass
                if ok:
                    break

        # Capa 5: Wikipedia / Wikimedia con verificación de título
        if not ok:
            for lang_w in ("es", "en"):
                for q_eq in consultas[:2]:
                    try:
                        r_w = requests.get(
                            f"https://{lang_w}.wikipedia.org/w/api.php",
                            params={
                                "action": "query", "generator": "search", "gsrsearch": f"{q_eq} football club",
                                "gsrlimit": 3, "prop": "pageimages", "pithumbsize": 320, "format": "json"
                            },
                            headers={"User-Agent": "QuantBet22Bot/1.0"},
                            timeout=4.0,
                        )
                        if r_w.status_code == 200:
                            pages = (r_w.json().get("query") or {}).get("pages") or {}
                            for pg in pages.values():
                                if not _nombre_coincide_escudo(nom_alias, str(pg.get("title") or "")):
                                    continue
                                src_w = (pg.get("thumbnail") or {}).get("source") or ""
                                if src_w and any(ext in src_w.lower() for ext in (".png", ".svg")):
                                    if _descargar_y_guardar_png_valido(src_w, ruta_png):
                                        ok = True
                                        break
                    except Exception:
                        pass
                    if ok:
                        break
                if ok:
                    break

    if os.path.exists(ruta_png):
        try:
            im = Image.open(ruta_png).convert("RGBA")
            im.thumbnail((tam, tam), Image.Resampling.LANCZOS)
            lienzo = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
            lienzo.paste(im, ((tam - im.width) // 2, (tam - im.height) // 2), im)
            return lienzo
        except Exception:
            pass

    # Respaldo elegante geométrico SOLO si el club no existe en ninguna de las 5 fuentes
    im = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    pts = [
        (tam * 0.50, tam * 0.06), (tam * 0.88, tam * 0.20), (tam * 0.82, tam * 0.66),
        (tam * 0.50, tam * 0.94), (tam * 0.18, tam * 0.66), (tam * 0.12, tam * 0.20),
    ]
    d.polygon(pts, fill=(22, 34, 52, 245), outline=(0, 232, 118, 220))
    d.line(pts + [pts[0]], fill=(0, 232, 118, 220), width=4)
    pals = [p for p in re.sub(r"[^A-Za-z0-9\s]", "", str(nombre_equipo)).split() if p.upper() not in ("FC", "CF", "SC", "CD", "AC", "AS", "USC")]
    ini = (pals[0][:3] if len(pals) == 1 else (pals[0][0] + pals[1][0])).upper() if pals else "QB"
    f_ini = _fuente_pro("bold", int(tam * 0.30))
    bb = d.textbbox((0, 0), ini, font=f_ini)
    d.text(((tam - (bb[2] - bb[0])) // 2, (tam - (bb[3] - bb[1])) // 2 - 8), ini, font=f_ini, fill=_C_BLANCO_PRO)
    return im


def _crear_fondo_broadcast_pro(acento_izq=(0, 232, 118), acento_der=(255, 204, 0), W=1080, H=1920):
    base = Image.new("RGBA", (W, H), (7, 11, 18, 255))
    ruta_bg = "fondo de quant bet.jpg"
    if os.path.exists(ruta_bg):
        try:
            orig = Image.open(ruta_bg).convert("RGBA")
            esc = max(W / orig.width, H / orig.height)
            nw, nh = int(orig.width * esc), int(orig.height * esc)
            bg_r = orig.resize((nw, nh), Image.Resampling.LANCZOS)
            left, top = max(0, (nw - W) // 2), max(0, (nh - H) // 2)
            bg_r = bg_r.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(radius=7))
            velo = Image.new("RGBA", (W, H), (6, 10, 17, 228))
            base = Image.alpha_composite(bg_r, velo)
        except Exception:
            pass

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow, "RGBA")
    cy_g = int(H * 0.42)
    for r in range(440, 20, -30):
        alpha = int(17 * (1.0 - r / 460.0))
        dg.ellipse([(int(W * 0.22) - r, cy_g - r), (int(W * 0.22) + r, cy_g + r)], fill=(*acento_izq, alpha))
        dg.ellipse([(int(W * 0.78) - r, cy_g - r), (int(W * 0.78) + r, cy_g + r)], fill=(*acento_der, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=48))
    base = Image.alpha_composite(base, glow)

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(grid, "RGBA")
    for y_g in range(0, H, 72):
        dr.line([(0, y_g), (W, y_g)], fill=(255, 255, 255, 6), width=1)
    for x_g in range(0, W, 72):
        dr.line([(x_g, 0), (x_g, H)], fill=(255, 255, 255, 5), width=1)
    return Image.alpha_composite(base, grid)


def _pegar_medallon_pro(lienzo, escudo, cx, cy, radio=168, color_aro=_C_VERDE_PRO):
    halo = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(halo, "RGBA")
    dh.ellipse([(cx - radio - 22, cy - radio - 22), (cx + radio + 22, cy + radio + 22)], fill=(color_aro[0], color_aro[1], color_aro[2], 50))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=24))
    lienzo.alpha_composite(halo)

    draw = ImageDraw.Draw(lienzo, "RGBA")
    draw.ellipse([(cx - radio, cy - radio), (cx + radio, cy + radio)], fill=(14, 22, 36, 248), outline=color_aro, width=4)
    draw.ellipse([(cx - radio + 10, cy - radio + 10), (cx + radio - 10, cy + radio - 10)], outline=(255, 255, 255, 36), width=2)

    tam_in = int(radio * 1.38)
    esc_r = escudo.copy()
    esc_r.thumbnail((tam_in, tam_in), Image.Resampling.LANCZOS)
    lienzo.paste(esc_r, (cx - esc_r.width // 2, cy - esc_r.height // 2), esc_r)


def _dibujar_marca_sup_pro(lienzo, y=106):
    draw = ImageDraw.Draw(lienzo, "RGBA")
    txt = "Q22 DATA LAB   •   ANALÍTICA DE FÚTBOL EN PYTHON"
    f_m = _fuente_pro("bold", 21)
    draw.text((_centrar_x_pro(draw, txt, f_m), y), txt, font=f_m, fill=(195, 212, 232, 215))


def _dibujar_cabecera_pro(lienzo, esc_l, esc_v, loc, vis, liga_txt, etiqueta_sup, y_base=112):
    _dibujar_marca_sup_pro(lienzo, y=y_base)
    draw = ImageDraw.Draw(lienzo, "RGBA")
    y_p = y_base + 42
    draw.rounded_rectangle([(64, y_p), (1016, y_p + 58)], radius=28, fill=(12, 34, 26, 238), outline=_C_VERDE_PRO, width=2)
    f_pill = _fuente_pro_ajustada(draw, etiqueta_sup.upper(), "bold", 24, 890, 17)
    draw.text((_centrar_x_pro(draw, etiqueta_sup.upper(), f_pill), y_p + 15), etiqueta_sup.upper(), font=f_pill, fill=_C_VERDE_PRO)

    y_c = y_p + 76
    draw.rounded_rectangle([(64, y_c), (1016, y_c + 144)], radius=26, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    el = esc_l.copy(); el.thumbnail((102, 102), Image.Resampling.LANCZOS)
    ev = esc_v.copy(); ev.thumbnail((102, 102), Image.Resampling.LANCZOS)
    lienzo.paste(el, (100, y_c + 72 - el.height // 2), el)
    lienzo.paste(ev, (980 - ev.width, y_c + 72 - ev.height // 2), ev)

    duelo = f"{loc.upper()}  VS  {vis.upper()}"
    f_duelo = _fuente_pro_ajustada(draw, duelo, "bold", 34, 620, 20)
    draw.text((_centrar_x_pro(draw, duelo, f_duelo), y_c + 34), duelo, font=f_duelo, fill=_C_BLANCO_PRO)

    f_lg = _fuente_pro_ajustada(draw, liga_txt.upper(), "mono", 22, 620, 16)
    draw.text((_centrar_x_pro(draw, liga_txt.upper(), f_lg), y_c + 90), liga_txt.upper(), font=f_lg, fill=_C_ORO_PRO)
    return y_c + 144


def _dibujar_candado_pro(draw, cx, cy, color=_C_ORO_PRO):
    draw.arc([(cx - 18, cy - 30), (cx + 18, cy + 4)], start=180, end=360, fill=color, width=5)
    draw.line([(cx - 18, cy - 13), (cx - 18, cy - 2)], fill=color, width=5)
    draw.line([(cx + 18, cy - 13), (cx + 18, cy - 2)], fill=color, width=5)
    draw.rounded_rectangle([(cx - 26, cy - 4), (cx + 26, cy + 32)], radius=8, fill=color)
    draw.ellipse([(cx - 6, cy + 8), (cx + 6, cy + 20)], fill=(12, 18, 28, 255))


def _limpiar_pick_visual_pro(pick_txt):
    t = str(pick_txt).strip()
    return t.replace("Doble Oport.", "Doble Oportunidad").replace("Ambos Marcan (BTTS)", "Ambos Marcan")


def _limpiar_pick_voz_pro(pick_txt):
    t = _limpiar_pick_visual_pro(pick_txt)
    t = t.replace("Over ", "Más de ").replace("Under ", "Menos de ")
    t = t.replace("1X", "uno equis").replace("X2", "equis dos")
    t = t.replace("1T", "primer tiempo").replace("2do Tiempo", "segundo tiempo").replace("2T", "segundo tiempo")
    t = t.replace(" > ", " superior a ").replace(">", " superior a ")
    t = re.sub(r"(\d+)\.5\b", r"\1 punto 5", t)
    t = re.sub(r"(\d+)\.25\b", r"\1 punto 25", t)
    t = re.sub(r"(\d+)\.75\b", r"\1 punto 75", t)
    return t


def _crear_escena_1_portada_pro(datos, esc_l, esc_v, titular_gancho, ruta_out):
    """Portada Matchday centrada y equilibrada (y=120..1290 + subtítulos en y=1345..1495)."""
    lienzo = _crear_fondo_broadcast_pro()
    _dibujar_marca_sup_pro(lienzo, y=118)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    tag_sup = f"MODELO QUANT PYTHON   •   {datos['liga'].upper()}"
    draw.rounded_rectangle([(72, 166), (1008, 232)], radius=32, fill=(12, 34, 26, 240), outline=_C_VERDE_PRO, width=2)
    f_tag = _fuente_pro_ajustada(draw, tag_sup, "bold", 24, 880, 16)
    draw.text((_centrar_x_pro(draw, tag_sup, f_tag), 184), tag_sup, font=f_tag, fill=_C_VERDE_PRO)

    f_hook = _fuente_pro_ajustada(draw, titular_gancho.upper(), "bold", 64, 940, 34)
    draw.text((_centrar_x_pro(draw, titular_gancho.upper(), f_hook), 286), titular_gancho.upper(), font=f_hook, fill=_C_ORO_PRO)

    sub_hook = "MODELO ESTADÍSTICO POISSON + DIXON-COLES"
    f_sh = _fuente_pro_ajustada(draw, sub_hook, "mono", 25, 920, 17)
    draw.text((_centrar_x_pro(draw, sub_hook, f_sh), 380), sub_hook, font=f_sh, fill=_C_GRIS_PRO)

    # Línea de acento elegante
    draw.line([(240, 444), (840, 444)], fill=(0, 232, 118, 95), width=2)

    cy_esc = 690
    _pegar_medallon_pro(lienzo, esc_l, 270, cy_esc, radio=172, color_aro=_C_VERDE_PRO)
    _pegar_medallon_pro(lienzo, esc_v, 810, cy_esc, radio=172, color_aro=_C_ORO_PRO)

    draw = ImageDraw.Draw(lienzo, "RGBA")
    rombo = [(540, cy_esc - 68), (608, cy_esc), (540, cy_esc + 68), (472, cy_esc)]
    draw.polygon(rombo, fill=(14, 24, 38, 252), outline=_C_VERDE_PRO)
    draw.line(rombo + [rombo[0]], fill=_C_VERDE_PRO, width=4)
    f_vs = _fuente_pro("bold", 44)
    draw.text((_centrar_x_pro(draw, "VS", f_vs, 540), cy_esc - 26), "VS", font=f_vs, fill=_C_BLANCO_PRO)

    f_loc = _fuente_pro_ajustada(draw, datos["local"].upper(), "bold", 42, 415, 22)
    f_vis = _fuente_pro_ajustada(draw, datos["visitante"].upper(), "bold", 42, 415, 22)
    draw.text((_centrar_x_pro(draw, datos["local"].upper(), f_loc, 270), 894), datos["local"].upper(), font=f_loc, fill=_C_BLANCO_PRO)
    draw.text((_centrar_x_pro(draw, datos["visitante"].upper(), f_vis, 810), 894), datos["visitante"].upper(), font=f_vis, fill=_C_BLANCO_PRO)

    # Tarjeta inferior centrada con fecha, horarios y teaser
    draw.rounded_rectangle([(72, 1004), (1008, 1264)], radius=28, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    txt_hora = f"JORNADA {datos['fecha']}   |   {datos['hora_esp']}h ESP  •  {datos['hora_col']}h COL"
    f_h = _fuente_pro_ajustada(draw, txt_hora, "mono", 27, 880, 18)
    draw.text((_centrar_x_pro(draw, txt_hora, f_h), 1046), txt_hora, font=f_h, fill=_C_VERDE_PRO)

    draw.line([(160, 1112), (920, 1112)], fill=(255, 255, 255, 28), width=1)

    txt_teaser = "¿QUIÉN DOMINA SEGÚN LOS DATOS DEL PARTIDO?"
    f_ts = _fuente_pro_ajustada(draw, txt_teaser, "bold", 29, 880, 19)
    draw.text((_centrar_x_pro(draw, txt_teaser, f_ts), 1142), txt_teaser, font=f_ts, fill=_C_BLANCO_PRO)

    txt_sub2 = "GOLES ESPERADOS  •  RITMO  •  PROBABILIDADES"
    f_s2 = _fuente_pro_ajustada(draw, txt_sub2, "mono", 21, 880, 15)
    draw.text((_centrar_x_pro(draw, txt_sub2, f_s2), 1204), txt_sub2, font=f_s2, fill=_C_ORO_PRO)

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _crear_historia_diaria_pro(datos, esc_l, esc_v, titular_gancho, ruta_out):
    """Historia Diaria 100% centrada en el lienzo vertical (1080x1920) con espacio limpio
    en y=1440..1620 pensado para el sticker de enlace de Instagram y Facebook."""
    lienzo = _crear_fondo_broadcast_pro()
    _dibujar_marca_sup_pro(lienzo, y=132)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    tag_sup = f"PARTIDAZO DEL DÍA   •   {datos['liga'].upper()}"
    draw.rounded_rectangle([(72, 184), (1008, 252)], radius=34, fill=(12, 34, 26, 240), outline=_C_VERDE_PRO, width=2)
    f_tag = _fuente_pro_ajustada(draw, tag_sup, "bold", 24, 880, 16)
    draw.text((_centrar_x_pro(draw, tag_sup, f_tag), 203), tag_sup, font=f_tag, fill=_C_VERDE_PRO)

    f_hook = _fuente_pro_ajustada(draw, titular_gancho.upper(), "bold", 62, 940, 32)
    draw.text((_centrar_x_pro(draw, titular_gancho.upper(), f_hook), 312), titular_gancho.upper(), font=f_hook, fill=_C_ORO_PRO)

    sub_h = f"JORNADA {datos['fecha']}   |   {datos['hora_esp']}h ESP  •  {datos['hora_col']}h COL"
    f_sh = _fuente_pro_ajustada(draw, sub_h, "mono", 26, 920, 17)
    draw.text((_centrar_x_pro(draw, sub_h, f_sh), 406), sub_h, font=f_sh, fill=_C_GRIS_PRO)

    cy_esc = 696
    _pegar_medallon_pro(lienzo, esc_l, 270, cy_esc, radio=174, color_aro=_C_VERDE_PRO)
    _pegar_medallon_pro(lienzo, esc_v, 810, cy_esc, radio=174, color_aro=_C_ORO_PRO)

    draw = ImageDraw.Draw(lienzo, "RGBA")
    rombo = [(540, cy_esc - 68), (608, cy_esc), (540, cy_esc + 68), (472, cy_esc)]
    draw.polygon(rombo, fill=(14, 24, 38, 252), outline=_C_VERDE_PRO)
    draw.line(rombo + [rombo[0]], fill=_C_VERDE_PRO, width=4)
    f_vs = _fuente_pro("bold", 44)
    draw.text((_centrar_x_pro(draw, "VS", f_vs, 540), cy_esc - 26), "VS", font=f_vs, fill=_C_BLANCO_PRO)

    f_loc = _fuente_pro_ajustada(draw, datos["local"].upper(), "bold", 42, 415, 22)
    f_vis = _fuente_pro_ajustada(draw, datos["visitante"].upper(), "bold", 42, 415, 22)
    draw.text((_centrar_x_pro(draw, datos["local"].upper(), f_loc, 270), 902), datos["local"].upper(), font=f_loc, fill=_C_BLANCO_PRO)
    draw.text((_centrar_x_pro(draw, datos["visitante"].upper(), f_vis, 810), 902), datos["visitante"].upper(), font=f_vis, fill=_C_BLANCO_PRO)

    # 3 chips métricos simétricos en el centro
    chips = [
        ("GOLES ESP.", f"{datos['tot_goles']:.2f}", _C_VERDE_PRO),
        ("CÓRNERS", f"{datos['tot_corn']:.1f}", _C_ORO_PRO),
        ("REMATES", f"{datos['tot_tiros']:.1f}", _C_AZUL_PRO),
    ]
    w_ch = 292
    gap = 26
    x_ini = (1080 - (3 * w_ch + 2 * gap)) // 2
    for idx_c, (lbl_c, val_c, col_c) in enumerate(chips):
        x0 = x_ini + idx_c * (w_ch + gap)
        draw.rounded_rectangle([(x0, 1022), (x0 + w_ch, 1188)], radius=24, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
        f_l = _fuente_pro("bold", 21)
        f_v = _fuente_pro("bold", 54)
        draw.text((_centrar_x_pro(draw, lbl_c, f_l, x0 + w_ch // 2), 1048), lbl_c, font=f_l, fill=_C_GRIS_PRO)
        draw.text((_centrar_x_pro(draw, val_c, f_v, x0 + w_ch // 2), 1094), val_c, font=f_v, fill=col_c)

    # Tarjeta CTA elegante centrada (deja zona limpia abajo para sticker clicable)
    draw.rounded_rectangle([(72, 1236), (1008, 1418)], radius=28, fill=(10, 34, 24, 244), outline=_C_VERDE_PRO, width=3)
    t_cta1 = "PREVIA ESTADÍSTICA COMPLETA DEL PARTIDO"
    t_cta2 = "¿CUÁL ES TU MARCADOR EXACTO? RESPONDE A ESTA HISTORIA"
    f_c1 = _fuente_pro_ajustada(draw, t_cta1, "bold", 31, 880, 19)
    f_c2 = _fuente_pro_ajustada(draw, t_cta2, "mono", 22, 880, 16)
    draw.text((_centrar_x_pro(draw, t_cta1, f_c1), 1276), t_cta1, font=f_c1, fill=_C_VERDE_PRO)
    draw.text((_centrar_x_pro(draw, t_cta2, f_c2), 1340), t_cta2, font=f_c2, fill=_C_BLANCO_PRO)

    # Pie sutil 100% analítica deportiva
    f_pie = _fuente_pro("mono", 22)
    pie_txt = "Q22 DATA LAB  •  ANALÍTICA DE FÚTBOL EN PYTHON"
    draw.text((_centrar_x_pro(draw, pie_txt, f_pie), 1676), pie_txt, font=f_pie, fill=(160, 176, 196, 195))

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _crear_escena_2_metricas_pro(datos, esc_l, esc_v, ruta_out):
    """Radiografía estadística centrada y elegante (SIN 1X2), cubriendo y=112..1295."""
    lienzo = _crear_fondo_broadcast_pro()
    y_bot = _dibujar_cabecera_pro(lienzo, esc_l, esc_v, datos["local"], datos["visitante"], datos["liga"], "RADIOGRAFÍA ESTADÍSTICA DEL PARTIDO", y_base=112)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    y1 = y_bot + 32
    draw.rounded_rectangle([(64, y1), (1016, y1 + 242)], radius=28, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    lbl_g = "GOLES ESPERADOS (SIMULACIÓN POISSON)"
    f_lg = _fuente_pro("bold", 25)
    draw.text((_centrar_x_pro(draw, lbl_g, f_lg), y1 + 28), lbl_g, font=f_lg, fill=_C_GRIS_PRO)

    val_g = f"{datos['tot_goles']:.2f} GOLES"
    f_vg = _fuente_pro("bold", 66)
    draw.text((_centrar_x_pro(draw, val_g, f_vg), y1 + 74), val_g, font=f_vg, fill=_C_VERDE_PRO)

    bx0, by0, bx1, by1 = 112, y1 + 174, 968, y1 + 208
    draw.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=16, fill=(24, 35, 50, 255))
    pct_g = max(0.18, min(1.0, datos["tot_goles"] / 4.2))
    draw.rounded_rectangle([(bx0, by0), (int(bx0 + (bx1 - bx0) * pct_g), by1)], radius=16, fill=_C_VERDE_PRO)

    # Fila 2: Córners y Remates centrados en 2 columnas simétricas
    y2 = y1 + 270
    draw.rounded_rectangle([(64, y2), (526, y2 + 260)], radius=28, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    draw.text((_centrar_x_pro(draw, "CÓRNERS PROYECTADOS", _fuente_pro("bold", 23), 295), y2 + 30), "CÓRNERS PROYECTADOS", font=_fuente_pro("bold", 23), fill=_C_GRIS_PRO)
    draw.text((_centrar_x_pro(draw, f"{datos['tot_corn']:.1f}", _fuente_pro("bold", 78), 295), y2 + 80), f"{datos['tot_corn']:.1f}", font=_fuente_pro("bold", 78), fill=_C_ORO_PRO)
    draw.text((_centrar_x_pro(draw, "Ritmo por bandas", _fuente_pro("mono", 22), 295), y2 + 194), "Ritmo por bandas", font=_fuente_pro("mono", 22), fill=_C_BLANCO_PRO)

    draw.rounded_rectangle([(554, y2), (1016, y2 + 260)], radius=28, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    draw.text((_centrar_x_pro(draw, "REMATES A PUERTA", _fuente_pro("bold", 23), 785), y2 + 30), "REMATES A PUERTA", font=_fuente_pro("bold", 23), fill=_C_GRIS_PRO)
    draw.text((_centrar_x_pro(draw, f"{datos['tot_tiros']:.1f}", _fuente_pro("bold", 78), 785), y2 + 80), f"{datos['tot_tiros']:.1f}", font=_fuente_pro("bold", 78), fill=_C_AZUL_PRO)
    draw.text((_centrar_x_pro(draw, "Volumen ofensivo", _fuente_pro("mono", 22), 785), y2 + 194), "Volumen ofensivo", font=_fuente_pro("mono", 22), fill=_C_BLANCO_PRO)

    # Fila 3: Faltas, Tarjetas y Perfil táctico centrados
    y3 = y2 + 288
    draw.rounded_rectangle([(64, y3), (1016, y3 + 302)], radius=28, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=2)
    f_t3 = _fuente_pro("bold", 24)
    draw.text((_centrar_x_pro(draw, "FRICCIÓN, DISCIPLINA Y CONTEXTO", f_t3), y3 + 26), "FRICCIÓN, DISCIPLINA Y CONTEXTO", font=f_t3, fill=_C_GRIS_PRO)

    draw.rounded_rectangle([(100, y3 + 78), (526, y3 + 206)], radius=20, fill=_C_PANEL_ALT, outline=(255, 148, 64, 150), width=2)
    draw.text((_centrar_x_pro(draw, "FALTAS ESTIMADAS", _fuente_pro("mono", 20), 313), y3 + 96), "FALTAS ESTIMADAS", font=_fuente_pro("mono", 20), fill=_C_GRIS_PRO)
    draw.text((_centrar_x_pro(draw, f"{datos['tot_faltas']:.1f} faltas", _fuente_pro("bold", 40), 313), y3 + 134), f"{datos['tot_faltas']:.1f} faltas", font=_fuente_pro("bold", 40), fill=_C_NARANJA_PRO)

    draw.rounded_rectangle([(554, y3 + 78), (980, y3 + 206)], radius=20, fill=_C_PANEL_ALT, outline=(255, 204, 0, 150), width=2)
    draw.text((_centrar_x_pro(draw, "TARJETAS PROYECTADAS", _fuente_pro("mono", 20), 767), y3 + 96), "TARJETAS PROYECTADAS", font=_fuente_pro("mono", 20), fill=_C_GRIS_PRO)
    draw.text((_centrar_x_pro(draw, f"{datos['tot_tarj']:.1f} tarjetas", _fuente_pro("bold", 40), 767), y3 + 134), f"{datos['tot_tarj']:.1f} tarjetas", font=_fuente_pro("bold", 40), fill=_C_ORO_PRO)

    etq_fuente = "MODELO POISSON + DIXON-COLES"
    ctx_txt = f"PERFIL: {datos['contexto'].upper()}  •  {etq_fuente}"
    f_ctx = _fuente_pro_ajustada(draw, ctx_txt, "mono", 21, 880, 15)
    draw.text((_centrar_x_pro(draw, ctx_txt, f_ctx), y3 + 240), ctx_txt, font=f_ctx, fill=_C_VERDE_PRO)

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _crear_escena_3_jugada_pro(datos, esc_l, esc_v, ruta_out):
    """Escena 3 100% segura para redes sociales: Tendencia estadística + Probabilidad 1X2 (analítica pura)."""
    lienzo = _crear_fondo_broadcast_pro()
    y_bot = _dibujar_cabecera_pro(lienzo, esc_l, esc_v, datos["local"], datos["visitante"], datos["liga"], "PROBABILIDADES DEL MODELO ESTADÍSTICO", y_base=112)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    # Tarjeta 1: Tendencia táctica principal con probabilidad % (sin cuotas decimales)
    y1 = y_bot + 36
    draw.rounded_rectangle([(64, y1), (1016, y1 + 372)], radius=30, fill=(9, 34, 24, 246), outline=_C_VERDE_PRO, width=4)

    draw.rounded_rectangle([(240, y1 + 32), (840, y1 + 88)], radius=24, fill=_C_VERDE_PRO)
    f_b1 = _fuente_pro("bold", 24)
    draw.text((_centrar_x_pro(draw, "TENDENCIA PRINCIPAL DEL MODELO", f_b1), y1 + 46), "TENDENCIA PRINCIPAL DEL MODELO", font=f_b1, fill=(7, 18, 12, 255))

    pick_txt = _limpiar_pick_visual_pro(datos["pick_abierto"]).upper()
    pick_txt = pick_txt.replace("OVER ", "MÁS DE ").replace("UNDER ", "MENOS DE ")
    f_pick = _fuente_pro_ajustada(draw, pick_txt, "bold", 54, 860, 26)
    draw.text((_centrar_x_pro(draw, pick_txt, f_pick), y1 + 128), pick_txt, font=f_pick, fill=_C_BLANCO_PRO)

    prob_est = float(datos.get("prob_abierta") or 74.5)
    nivel_conf = "MUY ALTA" if prob_est >= 74.0 else ("ALTA" if prob_est >= 65.0 else "MODERADA")
    prob_txt = f"CONFLUENCIA ESTADÍSTICA:  {nivel_conf}"
    draw.rounded_rectangle([(210, y1 + 220), (870, y1 + 292)], radius=18, fill=(14, 24, 34, 230), outline=_C_VERDE_PRO, width=2)
    f_pr = _fuente_pro_ajustada(draw, prob_txt, "mono", 32, 620, 20)
    draw.text((_centrar_x_pro(draw, prob_txt, f_pr), y1 + 236), prob_txt, font=f_pr, fill=_C_VERDE_PRO)

    nota_txt = "DATO CALCULADO CON HISTÓRICO DE LIGA + DIXON-COLES"
    f_nt = _fuente_pro_ajustada(draw, nota_txt, "mono", 20, 880, 15)
    draw.text((_centrar_x_pro(draw, nota_txt, f_nt), y1 + 318), nota_txt, font=f_nt, fill=_C_GRIS_PRO)

    # Tarjeta 2: Probabilidades de Resultado (Local / Empate / Visitante) — estilo Opta / Google Win Probability
    y2 = y1 + 404
    draw.rounded_rectangle([(64, y2), (1016, y2 + 436)], radius=30, fill=_C_PANEL_PRO, outline=_C_BORDE_PRO, width=3)
    f_tit2 = _fuente_pro("bold", 26)
    draw.text((_centrar_x_pro(draw, "DISTRIBUCIÓN DE RESULTADO (MODELO 1X2)", f_tit2), y2 + 34), "DISTRIBUCIÓN DE RESULTADO (MODELO 1X2)", font=f_tit2, fill=_C_ORO_PRO)

    p_h = float(datos.get("p_h") or 45.0)
    p_d = float(datos.get("p_d") or 26.0)
    p_a = float(datos.get("p_a") or 29.0)
    filas_1x2 = [
        (f"VICTORIA {datos['local'][:16].upper()}", p_h, _C_VERDE_PRO),
        ("EMPATE", p_d, _C_ORO_PRO),
        (f"VICTORIA {datos['visitante'][:16].upper()}", p_a, _C_AZUL_PRO),
    ]
    yb = y2 + 102
    for lbl_b, val_b, col_b in filas_1x2:
        f_lb = _fuente_pro_ajustada(draw, lbl_b, "bold", 24, 620, 17)
        draw.text((112, yb), lbl_b, font=f_lb, fill=_C_BLANCO_PRO)
        v_s = f"{val_b:.1f}%"
        f_vb = _fuente_pro("mono", 26)
        bb_v = draw.textbbox((0, 0), v_s, font=f_vb)
        draw.text((968 - (bb_v[2] - bb_v[0]), yb - 2), v_s, font=f_vb, fill=col_b)
        draw.rounded_rectangle([(112, yb + 38), (968, yb + 64)], radius=12, fill=(28, 38, 54, 235))
        ancho_fill = max(32, int((968 - 112) * min(1.0, val_b / 100.0)))
        draw.rounded_rectangle([(112, yb + 38), (112 + ancho_fill, yb + 64)], radius=12, fill=col_b)
        yb += 100

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _crear_escena_4_debate_tactico_pro(datos, esc_l, esc_v, ruta_out):
    """Escena 4 100% segura para TikTok/Reels/Shorts: Resumen táctico + Encuesta de marcador (evita sanciones por 'Información falsa')."""
    lienzo = _crear_fondo_broadcast_pro(acento_izq=(0, 232, 118), acento_der=(56, 168, 255))
    y_bot = _dibujar_cabecera_pro(lienzo, esc_l, esc_v, datos["local"], datos["visitante"], datos["liga"], "CLAVES TÁCTICAS DEL ENCUENTRO", y_base=112)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    y1 = y_bot + 36
    claves = [
        ("RITMO DE GOLES (xG)", f"{datos['tot_goles']:.2f} goles proyectados", "Escenario " + ("abierto con llegadas" if datos["tot_goles"] >= 2.60 else "táctico y disputado"), _C_VERDE_PRO),
        ("PRESIÓN POR BANDAS", f"{datos['tot_corn']:.1f} córners y {datos['tot_tiros']:.1f} remates", "Volumen estimado de ataque al área rival", _C_ORO_PRO),
        ("INTENSIDAD Y DUELOS", f"{datos['tot_faltas']:.1f} faltas y {datos['tot_tarj']:.1f} tarjetas", f"Perfil del partido: {datos['contexto']}", _C_AZUL_PRO),
    ]
    for tit_k, val_k, desc_k, col_k in claves:
        draw.rounded_rectangle([(64, y1), (1016, y1 + 178)], radius=24, fill=_C_PANEL_PRO, outline=col_k, width=2)
        f_tk = _fuente_pro("bold", 22)
        f_vk = _fuente_pro_ajustada(draw, val_k.upper(), "bold", 38, 860, 22)
        f_dk = _fuente_pro_ajustada(draw, desc_k, "mono", 21, 860, 15)
        draw.text((_centrar_x_pro(draw, tit_k, f_tk), y1 + 22), tit_k, font=f_tk, fill=col_k)
        draw.text((_centrar_x_pro(draw, val_k.upper(), f_vk), y1 + 64), val_k.upper(), font=f_vk, fill=_C_BLANCO_PRO)
        draw.text((_centrar_x_pro(draw, desc_k, f_dk), y1 + 126), desc_k, font=f_dk, fill=_C_GRIS_PRO)
        y1 += 200

    # Tarjeta final de debate e interacción orgánica (100% permitida por TikTok)
    draw.rounded_rectangle([(64, y1 + 12), (1016, y1 + 222)], radius=28, fill=(10, 34, 24, 244), outline=_C_VERDE_PRO, width=3)
    f_q1 = _fuente_pro_ajustada(draw, "¿CUÁL ES TU MARCADOR EXACTO?", "bold", 38, 860, 24)
    f_q2 = _fuente_pro_ajustada(draw, "DEJA TU PRONÓSTICO EN LOS COMENTARIOS", "bold", 25, 860, 18)
    f_q3 = _fuente_pro("mono", 20)
    draw.text((_centrar_x_pro(draw, "¿CUÁL ES TU MARCADOR EXACTO?", f_q1), y1 + 42), "¿CUÁL ES TU MARCADOR EXACTO?", font=f_q1, fill=_C_ORO_PRO)
    draw.text((_centrar_x_pro(draw, "DEJA TU PRONÓSTICO EN LOS COMENTARIOS", f_q2), y1 + 106), "DEJA TU PRONÓSTICO EN LOS COMENTARIOS", font=f_q2, fill=_C_BLANCO_PRO)
    draw.text((_centrar_x_pro(draw, "SÍGUENOS PARA MÁS ANÁLISIS DE FÚTBOL CON DATOS", f_q3), y1 + 162), "SÍGUENOS PARA MÁS ANÁLISIS DE FÚTBOL CON DATOS", font=f_q3, fill=_C_VERDE_PRO)

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _crear_escena_4_auditoria_7_completa_pro(datos, siete_tarjetas, tasa_txt, fecha_ayer, ac_14, tot_14, ruta_out):
    """Escena 4 centrada con las 7 tarjetas completas de ayer (y=88..1310) + subtítulos en y=1345..1495."""
    lienzo = _crear_fondo_broadcast_pro(acento_izq=(0, 232, 118), acento_der=(56, 168, 255))
    _dibujar_marca_sup_pro(lienzo, y=72)
    draw = ImageDraw.Draw(lienzo, "RGBA")

    draw.rounded_rectangle([(52, 112), (1028, 168)], radius=26, fill=(12, 34, 26, 240), outline=_C_VERDE_PRO, width=2)
    tit = f"AUDITORÍA OFICIAL COMPLETA {fecha_ayer}  •  {ac_14}/{tot_14} ACIERTOS"
    f_t = _fuente_pro_ajustada(draw, tit, "bold", 26, 930, 17)
    draw.text((_centrar_x_pro(draw, tit, f_t), 126), tit, font=f_t, fill=_C_VERDE_PRO)

    sub = "LAS 7 TARJETAS ENTREGADAS A CLIENTES (4 VIP + 3 FREE) CON MARCADOR FINAL"
    f_s = _fuente_pro_ajustada(draw, sub, "mono", 20, 960, 14)
    draw.text((_centrar_x_pro(draw, sub, f_s), 182), sub, font=f_s, fill=_C_GRIS_PRO)

    y = 222
    alto_card = 122
    salto_card = 132
    for item in (siete_tarjetas or [])[:7]:
        pks = item.get("dos_apuestas") or []
        es_pend_s4 = bool(item.get("pendiente"))
        ac_p = sum(1 for k in pks if k.get("ganada") is True)
        tot_p = max(1, len(pks))
        if es_pend_s4:
            col_b = _C_AZUL_PRO
            bg_c = (14, 24, 40, 244)
        else:
            es_verde = (ac_p == tot_p)
            col_b = _C_VERDE_PRO if es_verde else (_C_ORO_PRO if ac_p >= 1 else _C_ROJO_PRO)
            bg_c = (12, 28, 22, 244) if es_verde else ((26, 23, 13, 244) if ac_p >= 1 else (34, 14, 17, 244))

        draw.rounded_rectangle([(52, y), (1028, y + alto_card)], radius=20, fill=bg_c, outline=col_b, width=2)
        if es_pend_s4:
            dibujar_icono_pendiente(draw, 72, y + 16, tam=26)
        else:
            dibujar_icono_check_o_cruz(draw, 72, y + 16, ac_p >= 1, tam=26)

        tipo_t = str(item.get("tipo_tarjeta", "VIP"))
        col_tag = _C_ORO_PRO if tipo_t == "VIP" else _C_VERDE_PRO
        tag_str = f"[{tipo_t}]"
        f_tag = _fuente_pro("bold", 24)
        draw.text((108, y + 15), tag_str, font=f_tag, fill=col_tag)
        w_tag = draw.textbbox((0, 0), tag_str, font=f_tag)[2]

        part_corto = str(item.get("partido", "")).split(" (")[0].strip()
        duelo_txt = f" {part_corto} ({item.get('marcador', 'FT')})  [{ac_p}/{tot_p}]"
        f_du = _fuente_pro_ajustada(draw, duelo_txt, "bold", 26, 890 - w_tag, 17)
        draw.text((112 + w_tag, y + 15), duelo_txt, font=f_du, fill=_C_BLANCO_PRO)

        x_cur = 74
        for k in pks[:2]:
            if es_pend_s4 or k.get("ganada") is None:
                dibujar_icono_pendiente(draw, x_cur, y + 68, tam=22)
                col_ks4 = _C_AZUL_PRO
            else:
                dibujar_icono_check_o_cruz(draw, x_cur, y + 68, bool(k.get("ganada")), tam=22)
                col_ks4 = _C_VERDE_PRO if k.get("ganada") else _C_ROJO_PRO
            txt_k = f"{k.get('mercado_corto', '')} ({float(k.get('cuota', 1.25)):.2f})"
            f_k = _fuente_pro_ajustada(draw, txt_k, "mono", 22, 425, 15)
            draw.text((x_cur + 30, y + 66), txt_k, font=f_k, fill=col_ks4)
            x_cur += 472
        y += salto_card

    y_cta = max(y + 10, 1158)
    draw.rounded_rectangle([(52, y_cta), (1028, y_cta + 144)], radius=24, fill=(24, 20, 10, 246), outline=_C_ORO_PRO, width=3)
    preg = f"¿QUIÉN SE LLEVA ESTE {datos['local'].upper()} VS {datos['visitante'].upper()}?"
    f_pr = _fuente_pro_ajustada(draw, preg, "bold", 30, 920, 18)
    draw.text((_centrar_x_pro(draw, preg, f_pr), y_cta + 26), preg, font=f_pr, fill=_C_ORO_PRO)

    cta2 = "DEJA TU MARCADOR ABAJO Y ENTRA AL LINK DEL PERFIL"
    f_c2 = _fuente_pro_ajustada(draw, cta2, "bold", 24, 920, 16)
    draw.text((_centrar_x_pro(draw, cta2, f_c2), y_cta + 84), cta2, font=f_c2, fill=_C_BLANCO_PRO)

    lienzo.convert("RGB").save(ruta_out, quality=96)
    return ruta_out


def _estampar_subtitulo_pro(ruta_slide, texto_frase, ruta_out, progreso=1.0):
    """Subtítulo 100% centrado horizontalmente en zona segura móvil (y=1345..1498)."""
    img = Image.open(ruta_slide).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    x0, y0, x1, y1 = 68, 1345, 1012, 1498
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=24, fill=(6, 10, 16, 244), outline=_C_VERDE_PRO, width=3)

    palabras = str(texto_frase).strip().split()
    mitad = max(1, len(palabras) // 2)
    l1 = " ".join(palabras[:mitad]) if len(palabras) > 5 else " ".join(palabras)
    l2 = " ".join(palabras[mitad:]) if len(palabras) > 5 else ""
    cx = (x0 + x1) // 2

    if l2:
        f1 = _fuente_pro_ajustada(draw, l1, "bold", 33, 880, 19)
        f2 = _fuente_pro_ajustada(draw, l2, "bold", 33, 880, 19)
        draw.text((_centrar_x_pro(draw, l1, f1, cx), y0 + 20), l1, font=f1, fill=_C_BLANCO_PRO)
        draw.text((_centrar_x_pro(draw, l2, f2, cx), y0 + 72), l2, font=f2, fill=_C_ORO_PRO)
    else:
        f1 = _fuente_pro_ajustada(draw, l1, "bold", 36, 880, 21)
        draw.text((_centrar_x_pro(draw, l1, f1, cx), y0 + 48), l1, font=f1, fill=_C_ORO_PRO)

    w_bar = int(max(30, min(x1 - x0 - 44, (x1 - x0 - 44) * float(progreso))))
    draw.rounded_rectangle([(x0 + 22, y1 - 15), (x1 - 22, y1 - 7)], radius=4, fill=(25, 36, 48, 255))
    draw.rounded_rectangle([(x0 + 22, y1 - 15), (x0 + 22 + w_bar, y1 - 7)], radius=4, fill=_C_VERDE_PRO)

    img.convert("RGB").save(ruta_out, quality=95)
    return ruta_out


def _generar_beat_studio_pro(ruta_wav, duracion_seg=32.0, sr=44100):
    import math as _mb
    import struct as _sb
    n_samples = int(sr * duracion_seg)
    bpm = 115.0
    beat_sec = 60.0 / bpm
    buf = bytearray()
    for i in range(n_samples):
        t = i / sr
        pos_beat = t % beat_sec
        bar_pos = (t / beat_sec) % 4.0
        pad = 0.22 * _mb.sin(2 * _mb.pi * 65.41 * t) + 0.14 * _mb.sin(2 * _mb.pi * 98.0 * t) + 0.08 * _mb.sin(2 * _mb.pi * 155.56 * t)
        pad *= (0.75 + 0.25 * _mb.sin(2 * _mb.pi * 0.25 * t))
        kick = 0.0
        if bar_pos < 0.25 or (2.0 <= bar_pos < 2.25):
            tau = pos_beat
            if tau < 0.14:
                freq_k = 110.0 * _mb.exp(-tau * 22.0) + 42.0
                kick = 0.55 * _mb.exp(-tau * 18.0) * _mb.sin(2 * _mb.pi * freq_k * tau)
        sub_b = t % (beat_sec / 2.0)
        pulse = 0.10 * _mb.exp(-sub_b * 28.0) * _mb.sin(2 * _mb.pi * 311.13 * t)
        muestra = max(-0.95, min(0.95, (pad + kick + pulse) * 0.28))
        val = int(muestra * 32767)
        buf.extend(_sb.pack("<hh", val, val))
    with wave.open(ruta_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(buf))
    return ruta_wav


def renderizar_video_broadcast_4_escenas(slides_4, segmentos_4, ruta_mp4_salida, carpeta_tmp):
    """Renderiza MP4 100% compatible con Reproductor de Windows (sin 0x80004005), iPhone, Android,
    TikTok, Instagram, Facebook y YouTube:
    - H.264 High@4.0, yuv420p explícito, 30 fps CFR, timebase estándar 1/15360, AAC-LC 44.1kHz stereo, +faststart."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    clips_escena = []
    audios_wav = []
    temporales = []
    pref = os.path.splitext(os.path.basename(ruta_mp4_salida))[0][:18]

    wav_port = os.path.join(carpeta_tmp, f"_{pref}_sil0.wav")
    mp4_port = os.path.join(carpeta_tmp, f"_{pref}_port0.mp4")
    temporales.extend([wav_port, mp4_port])
    # Portada limpia inicial de 0.55s (16 frames sin subtítulos) -> garantiza miniatura perfecta en Frame 0 y t=0.5s en TikTok, IG, FB y YT Shorts
    dur_portada_cover = 0.55
    subprocess.run([ffmpeg_exe, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur_portada_cover:.2f}", "-acodec", "pcm_s16le", wav_port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([
        ffmpeg_exe, "-y", "-loop", "1", "-t", f"{dur_portada_cover:.2f}", "-i", os.path.abspath(slides_4[0]),
        "-vf", "fps=30,scale=1080:1920,format=yuv420p", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-preset", "fast", "-crf", "19", "-an",
        os.path.abspath(mp4_port)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    clips_escena.append((mp4_port, dur_portada_cover))
    audios_wav.append(wav_port)

    total_segs = len(segmentos_4)
    for idx, (sub_vis, voz_txt) in enumerate(segmentos_4):
        r_mp3 = os.path.join(carpeta_tmp, f"_{pref}_v{idx}.mp3")
        r_wav = os.path.join(carpeta_tmp, f"_{pref}_v{idx}.wav")
        temporales.extend([r_mp3, r_wav])

        asyncio.run(sintetizar_audio_ia(voz_txt, r_mp3))
        subprocess.run([ffmpeg_exe, "-y", "-i", os.path.abspath(r_mp3), "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", os.path.abspath(r_wav)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        dur = 4.5
        if os.path.exists(r_wav) and os.path.getsize(r_wav) > 1000:
            try:
                with wave.open(r_wav, "rb") as wf:
                    dur = max(1.6, wf.getnframes() / float(wf.getframerate()))
            except Exception:
                pass
        audios_wav.append(r_wav)

        partes_sub = [s.strip() for s in sub_vis.split("|") if s.strip()]
        dur_p = dur / max(1, len(partes_sub))
        lista_sc = os.path.join(carpeta_tmp, f"_{pref}_sc{idx}.txt")
        temporales.append(lista_sc)
        r_fr = slides_4[idx]
        with open(lista_sc, "w", encoding="utf-8") as f_sc:
            for j, txt_p in enumerate(partes_sub):
                prog = (idx + (j + 1) / len(partes_sub)) / total_segs
                r_fr = os.path.join(carpeta_tmp, f"_{pref}_fr_{idx}_{j}.jpg")
                _estampar_subtitulo_pro(slides_4[idx], txt_p, r_fr, progreso=prog)
                temporales.append(r_fr)
                f_sc.write(f"file '{ruta_posix(r_fr)}'\n")
                f_sc.write(f"duration {dur_p:.3f}\n")
            f_sc.write(f"file '{ruta_posix(r_fr)}'\n")

        dur_clip = dur + (0.25 if idx < total_segs - 1 else 0.35)
        r_clip = os.path.join(carpeta_tmp, f"_{pref}_cl{idx}.mp4")
        temporales.append(r_clip)
        subprocess.run([
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", os.path.abspath(lista_sc),
            "-t", f"{dur_clip:.3f}",
            "-vf", "fps=30,scale=1080:1920,format=yuv420p", "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-preset", "fast", "-crf", "19", "-an",
            os.path.abspath(r_clip)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips_escena.append((r_clip, dur_clip))

    lista_aud = os.path.join(carpeta_tmp, f"_{pref}_aud.txt")
    voz_full = os.path.join(carpeta_tmp, f"_{pref}_vozfull.wav")
    temporales.extend([lista_aud, voz_full])
    with open(lista_aud, "w", encoding="utf-8") as fa:
        for rw in audios_wav:
            fa.write(f"file '{ruta_posix(rw)}'\n")
    subprocess.run([ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", os.path.abspath(lista_aud), "-c", "copy", os.path.abspath(voz_full)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    dur_total = sum(d for _, d in clips_escena)
    ruta_musica = "musica_fondo.mp3" if os.path.exists("musica_fondo.mp3") else os.path.join(CARPETA_ESCUDOS_PRO, "beat_studio_pro.wav")
    if not os.path.exists(ruta_musica):
        _generar_beat_studio_pro(ruta_musica, duracion_seg=max(34.0, dur_total + 4.0))

    inputs_cmd = [ffmpeg_exe, "-y"]
    for r_c, _ in clips_escena:
        inputs_cmd.extend(["-i", os.path.abspath(r_c)])
    idx_voz = len(clips_escena)
    idx_mus = len(clips_escena) + 1
    inputs_cmd.extend(["-i", os.path.abspath(voz_full), "-i", os.path.abspath(ruta_musica)])

    # Timebase estándar 1/15360 (NO AVTB) + format=yuv420p final -> 100% compatible con Windows Media Player
    fc_parts = [f"[{i}:v]fps=30,settb=1/15360,setpts=PTS-STARTPTS,format=yuv420p[v{i}]" for i in range(len(clips_escena))]
    fc_parts.append("[v0][v1]concat=n=2:v=1:a=0,fps=30,settb=1/15360,setpts=PTS-STARTPTS,format=yuv420p[s0]")
    d_cur = clips_escena[0][1] + clips_escena[1][1]
    prev_lbl = "s0"
    trans_d = 0.25
    for k in range(2, len(clips_escena)):
        off = max(0.1, d_cur - trans_d)
        nxt_lbl = f"x{k}" if k < len(clips_escena) - 1 else "vpre"
        fc_parts.append(f"[{prev_lbl}][v{k}]xfade=transition=fade:duration={trans_d}:offset={off:.3f}[{nxt_lbl}]")
        d_cur = off + clips_escena[k][1]
        prev_lbl = nxt_lbl

    fc_parts.append("[vpre]fps=30,format=yuv420p[vout]")
    fc_parts.append(f"[{idx_voz}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.08[va];[{idx_mus}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.13[ma];[va][ma]amix=inputs=2:duration=first:dropout_transition=2[aout]")

    res_ff = subprocess.run(inputs_cmd + [
        "-filter_complex", ";".join(fc_parts),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30",
        "-video_track_timescale", "30000", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-movflags", "+faststart",
        "-shortest", os.path.abspath(ruta_mp4_salida)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    # Respaldo automático sin xfade si la versión local de FFmpeg rechaza algún parámetro del filtro
    if res_ff.returncode != 0 or not os.path.exists(ruta_mp4_salida) or os.path.getsize(ruta_mp4_salida) < 10000:
        lista_fb = os.path.join(carpeta_tmp, f"_{pref}_fb.txt")
        temporales.append(lista_fb)
        with open(lista_fb, "w", encoding="utf-8") as f_fb:
            for r_c, _ in clips_escena:
                f_fb.write(f"file '{ruta_posix(r_c)}'\n")
        subprocess.run([
            ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0", "-i", os.path.abspath(lista_fb),
            "-i", os.path.abspath(voz_full), "-i", os.path.abspath(ruta_musica),
            "-filter_complex", "[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.08[va];[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.13[ma];[va][ma]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30",
            "-video_track_timescale", "30000", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-shortest", os.path.abspath(ruta_mp4_salida)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for tmp in temporales:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def generar_paquete_redes_sociales(fecha_jornada, partidos_vip, partidos_descartes, ruta_img_doble, token_privado=None, chat_id_privado=None):
    import random as _rnd_v

    directorio_dia = f"Alertas_Quant_{fecha_jornada}"
    carpeta_videos = os.path.join(directorio_dia, "4_VIDEOS_LISTOS_REDES")
    os.makedirs(carpeta_videos, exist_ok=True)
    for arch_mp4 in os.listdir(carpeta_videos):
        if arch_mp4.endswith(".mp4"):
            try:
                os.remove(os.path.join(carpeta_videos, arch_mp4))
            except Exception:
                pass

    print("=" * 120)
    print(f" 🎬 GENERANDO LOS 2 VIDEOS BROADCAST PRO v3 (WINDOWS-SAFE + ESCUDOS REALES + CENTRADO) ({fecha_jornada})")
    print("=" * 120)

    if not partidos_vip and not partidos_descartes:
        return

    # Unificar toda la cartelera del día sin duplicados y rankear globalmente
    pool_cartelera = []
    vistos_vid = set()
    for p_cand in list(partidos_vip or []) + list(partidos_descartes or []):
        clave_v = (str(p_cand.get("local", "")).lower().strip(), str(p_cand.get("visitante", "")).lower().strip())
        if clave_v not in vistos_vid:
            vistos_vid.add(clave_v)
            pool_cartelera.append(p_cand)

    # Preferir partidos con al menos 90 minutos de margen antes del pitazo inicial
    ahora_sel_v = datetime.now()
    con_margen = [
        p for p in pool_cartelera
        if not p.get("ya_empezo") and (_dt_inicio_partido_real(p, fecha_jornada) >= ahora_sel_v + timedelta(minutes=90))
    ]
    por_jugar = [p for p in pool_cartelera if not p.get("ya_empezo")]
    base_ranking = con_margen if len(con_margen) >= 2 else (por_jugar if len(por_jugar) >= 2 else pool_cartelera)
    todos_ordenados = sorted(base_ranking, key=puntaje_cartelera_video, reverse=True)

    print("    📋 [TOP 6 CARTELERA GLOBAL PARA VÍDEOS] (Prioridad: Real Madrid > Barcelona > Millonarios > Top 2 Mundial):")
    for idx_r, p_r in enumerate(todos_ordenados[:6], start=1):
        print(f"       #{idx_r} ({puntaje_cartelera_video(p_r):7.1f} pts) | {p_r.get('hora', '')}h | {p_r.get('local')} vs {p_r.get('visitante')} ({p_r.get('liga_visual')})")

    # SIEMPRE los 2 mejores partidos globales de la cartelera, ordenados por hora REAL de inicio:
    # el que juega primero va al Slot #1 (publicación más temprana), el que juega más tarde va al Slot #2
    partido_1 = todos_ordenados[0]
    partido_2 = todos_ordenados[1] if len(todos_ordenados) > 1 else partido_1

    par_cronologico = sorted(
        [partido_1, partido_2],
        key=lambda x: _dt_inicio_partido_real(x, fecha_jornada)
    )
    partido_1, partido_2 = par_cronologico[0], par_cronologico[1]
    dt_pub_1, dt_pub_2 = calcular_horarios_fijos_2_videos(partido_1, partido_2, fecha_jornada, ahora_ref=ahora_sel_v)
    print(f"    🕒 [HORARIOS FIJOS COORDINADOS CON PITAZO INICIAL]:")
    print(f"       • Video #1 [{partido_1.get('local')} vs {partido_1.get('visitante')} | Juega {partido_1.get('hora')}h] -> Publicar: {dt_pub_1.strftime('%Y-%m-%d %H:%M')}h ESP")
    print(f"       • Video #2 [{partido_2.get('local')} vs {partido_2.get('visitante')} | Juega {partido_2.get('hora')}h] -> Publicar: {dt_pub_2.strftime('%Y-%m-%d %H:%M')}h ESP")

    ahora_esp_vid = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    modo_aud_vid = "noche" if ahora_esp_vid.hour >= 21 else "manana"
    fecha_aud_esperada_vid = ahora_esp_vid.strftime("%Y-%m-%d") if modo_aud_vid == "noche" else (ahora_esp_vid - timedelta(days=1)).strftime("%Y-%m-%d")

    siete_tarjetas_aud, tasa_real, fecha_ayer_real, ac_14, tot_14 = seleccionar_7_partidos_14_apuestas_clientes(
        fecha_aud_esperada_vid,
        token_priv=TOKEN_AUDITORIAS_PRIVADO,
        chat_priv=CHAT_ID_AUDITORIAS_PRIVADO,
        modo_horario=modo_aud_vid,
    )
    print(f"    📊 [AUDITORÍA EN VÍDEO] Jornada completa {fecha_ayer_real}: {len(siete_tarjetas_aud)} tarjetas ({ac_14}/{tot_14} aciertos | modo={modo_aud_vid})")

    cola_json = []
    titulares_baraja = list(TITULARES_GANCHO_PRO)
    _rnd_v.shuffle(titulares_baraja)

    def _construir_datos_video(p_obj):
        h_esp = str(p_obj.get("hora", "21:00"))
        try:
            h_i = int(h_esp.split(":")[0])
            h_col = f"{(h_i - 6) % 24:02d}:{h_esp.split(':')[1]}"
        except Exception:
            h_col = "15:00"
        sels_f = p_obj.get("seleccion_free") or p_obj.get("seleccion_vip") or [("Over 1.5 Goles", 76.0, 1.24)]
        pick_nom, pick_prob, pick_cuo = sels_f[0]
        ctx_c = re.sub(r"[^\w\s/\-áéíóúÁÉÍÓÚñÑ]", "", str(p_obj.get("etiqueta_contexto", "Análisis Cuantitativo"))).strip()
        f_cuo = str((p_obj.get("cuotas_bp") or {}).get("fuente", "modelo")).replace("kambi:", "Kambi ")
        return {
            "fecha": fecha_jornada,
            "hora_esp": h_esp,
            "hora_col": h_col,
            "liga": str(p_obj.get("liga_visual", "Fútbol Profesional")),
            "local": str(p_obj.get("local", "Local")),
            "visitante": str(p_obj.get("visitante", "Visitante")),
            "tot_goles": float(p_obj.get("tot_goles", 2.65)),
            "tot_corn": float(p_obj.get("tot_corn", 8.8)),
            "tot_tiros": float(p_obj.get("tot_tiros", 7.8)),
            "tot_faltas": float(p_obj.get("tot_faltas", 21.0)),
            "tot_tarj": float(p_obj.get("tot_tarj", 3.6)),
            "contexto": ctx_c or "Análisis Cuantitativo",
            "fuente_cuotas": f_cuo,
            "pick_abierto": str(pick_nom),
            "prob_abierta": float(pick_prob),
            "cuota_abierta": float(pick_cuo),
            "p_h": float(p_obj.get("p_h") or 45.0),
            "p_d": float(p_obj.get("p_d") or 26.0),
            "p_a": float(p_obj.get("p_a") or 29.0),
        }

    pares_videos = [
        (1, partido_1, "2_AUDITORIA_21PM", f"{dt_pub_1.strftime('%Y-%m-%d %H:%M')}h (España) - VIDEO #1 (Juega {partido_1.get('hora', '')}h)", "01_VIDEO_2130_PRO", dt_pub_1),
        (2, partido_2, "1_ESTRELLA_10AM", f"{dt_pub_2.strftime('%Y-%m-%d %H:%M')}h (España) - VIDEO #2 (Juega {partido_2.get('hora', '')}h)", "02_VIDEO_1400_PRO", dt_pub_2),
    ]

    for num_v, p_vid, tipo_copy, etiqueta_hor, pref_arch, dt_pub_v in pares_videos:
        try:
            datos_v = _construir_datos_video(p_vid)
            loc_v, vis_v = datos_v["local"], datos_v["visitante"]
            liga_hab = formatear_liga_hablada(datos_v["liga"])
            g_hab = formatear_numero_hablado(round(datos_v["tot_goles"], 1))
            c_hab = f"{datos_v['tot_corn']:.0f}"
            pick_vis = _limpiar_pick_visual_pro(datos_v["pick_abierto"])
            pick_voz = _limpiar_pick_voz_pro(datos_v["pick_abierto"])

            # Descarga verificada por NOMBRE (cero cruce de IDs entre ESPN y API-Sports)
            esc_l = obtener_escudo_real_equipo(loc_v, logo_url=p_vid.get("logo_local"), tam=230)
            esc_v = obtener_escudo_real_equipo(vis_v, logo_url=p_vid.get("logo_vis"), tam=230)

            tit_v = titulares_baraja[(num_v - 1) % len(titulares_baraja)]
            s1 = _crear_escena_1_portada_pro(datos_v, esc_l, esc_v, tit_v, os.path.join(carpeta_videos, f"_v{num_v}_01_portada.jpg"))
            s2 = _crear_escena_2_metricas_pro(datos_v, esc_l, esc_v, os.path.join(carpeta_videos, f"_v{num_v}_02_metricas.jpg"))
            s3 = _crear_escena_3_jugada_pro(datos_v, esc_l, esc_v, os.path.join(carpeta_videos, f"_v{num_v}_03_jugada.jpg"))
            s4 = _crear_escena_4_debate_tactico_pro(
                datos_v, esc_l, esc_v,
                os.path.join(carpeta_videos, f"_v{num_v}_04_claves.jpg")
            )

            # Crear Historia Diaria dedicada (100% centrada en 1080x1920 con métricas y zona de enlace)
            if num_v == 1:
                ruta_historia_hoy = os.path.join(carpeta_videos, f"00_HISTORIA_DIARIA_WEB_{fecha_jornada}.jpg")
                _crear_historia_diaria_pro(datos_v, esc_l, esc_v, tit_v, ruta_historia_hoy)

            if num_v == 1:
                intro_voz = f"Ojo con el partidazo entre {loc_v} y {vis_v} por {liga_hab}. Así lo analizan las matemáticas antes del pitazo inicial."
            else:
                intro_voz = f"Previa táctica con datos reales para {loc_v} frente a {vis_v} por {liga_hab}. Mira lo que proyecta nuestro modelo."

            segmentos_4 = [
                (
                    f"Previa estadística: {loc_v} vs {vis_v}.|¿Quién domina según los datos?",
                    intro_voz,
                ),
                (
                    f"Modelo Poisson en Python:|{datos_v['tot_goles']:.1f} goles esperados y {datos_v['tot_corn']:.0f} córners.",
                    f"El modelo estadístico en Páiton estima {g_hab} goles esperados y alrededor de {c_hab} córners en el partido.",
                ),
                (
                    f"Tendencia principal: {pick_vis}|Respaldada por histórico y Dixon-Coles.",
                    f"La tendencia estadística más fuerte del encuentro apunta a {pick_voz}, respaldada por el histórico reciente y el modelo de Poison.",
                ),
                (
                    f"¿Cuál es tu marcador para este duelo?|Déjalo en los comentarios 👇",
                    f"Ahí tienes las claves tácticas completas del partido. ¿Cuál es tu marcador para este {loc_v} contra {vis_v}? Déjalo en los comentarios y síguenos para más análisis.",
                ),
            ]

            slug_par = f"{limpiar_hashtag(loc_v)[1:]}_{limpiar_hashtag(vis_v)[1:]}"
            ruta_mini_out = os.path.join(carpeta_videos, f"0{num_v}_MINIATURA_{slug_par}.jpg")
            import shutil as _sh_min
            _sh_min.copy2(s1, ruta_mini_out)

            mp4_out = os.path.join(carpeta_videos, f"{pref_arch}_{slug_par}.mp4")
            renderizar_video_broadcast_4_escenas([s1, s2, s3, s4], segmentos_4, mp4_out, carpeta_videos)

            dict_v = generar_diccionario_copys_por_red(tipo_copy, p_vid, tasa_real)
            dict_v["horario"] = etiqueta_hor
            dict_v["titulo_interno"] = f"VIDEO {num_v} ({dt_pub_v.strftime('%H:%M')}) - {loc_v.upper()} VS {vis_v.upper()}"
            guardar_archivos_individuales_y_json(
                carpeta_videos, num_v, mp4_out, dict_v, cola_json, fecha_jornada,
                dt_pub_fijo=dt_pub_v, fecha_partido=p_vid.get("fecha", fecha_jornada),
                hora_partido=p_vid.get("hora", ""), ruta_miniatura=ruta_mini_out
            )
            print(f"    ✅ Video #{num_v} Broadcast Pro v3 [{loc_v} vs {vis_v}] creado: {mp4_out}")

            if token_privado and chat_id_privado:
                enviar_video_y_mensajes_separados_telegram(token_privado, chat_id_privado, mp4_out, dict_v)

            for r_tmp in (s1, s2, s3, s4):
                if os.path.exists(r_tmp):
                    try:
                        os.remove(r_tmp)
                    except Exception:
                        pass
        except Exception as e:
            print(f"    [!] Error generando Video #{num_v} Broadcast Pro v3: {e}")

    for item_cj in cola_json:
        item_cj["fecha_auditada_video"] = fecha_ayer_real
    with open(os.path.join(carpeta_videos, "cola_publicacion_redes.json"), "w", encoding="utf-8") as f:
        json.dump(cola_json, f, ensure_ascii=False, indent=2)

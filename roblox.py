import os, time, requests
from datetime import datetime, timezone

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
USER_IDS = [8630245318, 7316166768, 7769764881, 5820233922, 8582784594,
            10140803220, 7025395079, 7287146277, 7467786517, 8805340445,
            932901452]
OBJETIVO = 109629391874197

COOKIE = os.environ.get("ROBLOSECURITY", "")
SES = requests.Session()
SES.cookies.set(".ROBLOSECURITY", COOKIE, domain=".roblox.com")
if not COOKIE:
    print("AVISO: falta la cookie ROBLOSECURITY, no se vera el juego")

ultimo = {}
sesion = {}
cache = {}
fin = time.time() + 350 * 60

def perfil(uid):
    if uid not in cache:
        user, display, foto = "?", "?", None
        try:
            d = requests.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10).json()
            user, display = d.get("name", "?"), d.get("displayName", "?")
        except Exception:
            pass
        try:
            t = requests.get("https://thumbnails.roblox.com/v1/users/avatar-headshot",
                             params={"userIds": uid, "size": "150x150", "format": "Png"},
                             timeout=10).json()
            foto = t["data"][0].get("imageUrl")
        except Exception:
            pass
        cache[uid] = (user, display, foto)
    return cache[uid]

def es_objetivo(p):
    return OBJETIVO in (p.get("placeId"), p.get("rootPlaceId"), p.get("universeId"))

def nombre_juego(p):
    uni = p.get("universeId")
    if uni:
        try:
            d = requests.get("https://games.roblox.com/v1/games",
                             params={"universeIds": uni}, timeout=10).json()
            if d.get("data"):
                return d["data"][0]["name"]
        except Exception:
            pass
    return p.get("lastLocation") or "Desconocida"

def duracion(seg):
    h, r = divmod(int(seg), 3600)
    m, s = divmod(r, 60)
    return (f"{h} h " if h else "") + (f"{m} min " if m or h else "") + f"{s} s"

def enviar(uid, titulo, color, juego, extra=None, join=None, srv=None):
    user, display, foto = perfil(uid)
    campos = [
        {"name": "👤 Usuario", "value": f"[@{user}](https://www.roblox.com/users/{uid}/profile)", "inline": True},
        {"name": "✨ Nombre visible", "value": display, "inline": True},
        {"name": "🎮 Experiencia", "value": f"[{juego}](https://www.roblox.com/games/{OBJETIVO})", "inline": False},
    ]
    if srv:
        campos.append({"name": "🖥️ Servidor", "value": srv, "inline": True})
    if join:
        campos.append({"name": "🔗 Unirse", "value": f"[Entrar a su servidor]({join})", "inline": False})
    if extra:
        campos.append({"name": "⏱️ Tiempo jugado", "value": extra, "inline": False})
    embed = {
        "title": titulo, "color": color, "fields": campos,
        "footer": {"text": f"ID {uid}"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if foto:
        embed["thumbnail"] = {"url": foto}
    requests.post(WEBHOOK, json={"embeds": [embed]}, timeout=10)

while time.time() < fin:
    try:
        r = SES.post("https://presence.roblox.com/v1/presence/users",
                     json={"userIds": USER_IDS}, timeout=10).json()
        for p in r.get("userPresences", []):
            uid = p["userId"]
            jugando = p["userPresenceType"] == 2 and es_objetivo(p)
            antes = ultimo.get(uid, False)
            if jugando and not antes:
                juego = nombre_juego(p)
                sesion[uid] = (time.time(), juego)
                gid, pid = p.get("gameId"), p.get("placeId")
                if gid and pid:
                    join = f"https://www.roblox.com/games/start?placeId={pid}&gameInstanceId={gid}"
                    srv = "🌐 Público (probable)"
                else:
                    join = f"https://www.roblox.com/users/{uid}/profile"
                    srv = "🔒 Privado u oculto (probable)"
                enviar(uid, "🟢 Empezó a jugar", 0x57F287, juego, join=join, srv=srv)
            elif not jugando and antes:
                inicio, juego = sesion.pop(uid, (time.time(), "Desconocida"))
                enviar(uid, "🔴 Dejó de jugar", 0xED4245, juego,
                       extra=duracion(time.time() - inicio))
            ultimo[uid] = jugando
    except Exception as e:
        print("Error:", e)
    time.sleep(30)

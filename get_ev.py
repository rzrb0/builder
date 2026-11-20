import urllib.request
import sys
import os
import json
import base64


HERO_URL = os.getenv("HERO_URL")
HERO_UA = "MandraKodi2@@2.2.1@@@@A7B9X2"
LOGO = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/international/dazn-int.png"
TEAMS = {"Atalanta", "Bologna", "Cagliari", "Como", "Fiorentina",
        "Frosinone", "Genoa", "Inter", "Juventus", "Lazio",
        "Lecce", "Milan", "Monza", "Napoli", "Parma",
        "Roma", "Sassuolo", "Torino", "Udinese", "Venezia"}


def makeRequest(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print(f"API non raggiungibile. [{e}]")
        return None

def getSource(url):
    response = makeRequest(url, headers={'User-Agent': HERO_UA})
    if not response:
        return None
    res = json.loads(response)
    return res

def main():
    
    data = getSource(HERO_URL)
    events = []

    if data:
        try:
            for item in data["items"]:
                target = any(i in item["title"] for i in TEAMS)
                if target:
                    start = item["title"].find("]")
                    end = item["title"].find("[", start)
                    title = item["title"][start + 1:end]
                    b64 = item["myresolve"].replace("amstaff@@","").strip()
                    payload = base64.b64decode(b64).decode("utf-8")
                    arrTmp = payload.split("|")
                    link = arrTmp[0]
                    key = arrTmp[1]
                    events.append('\n#EXTINF:-1 tvg-logo="'+LOGO+'" group-title="Eventi",'+title)
                    events.append('\n#KODIPROP:inputstream.adaptive.manifest_type=mpd')
                    events.append('\n#KODIPROP:inputstream.adaptive.license_type=clearkey')
                    events.append('\n#KODIPROP:inputstream.adaptive.license_key='+key)
                    events.append('\n'+link)
        except:
            print("La struttura dei dati ricevuti non corrisponde al previsto.")

    with open('events.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U")
        for line in events:
            f.write(line)    

    if events:
        print(f"{len(events)//5} eventi trovati.")
    else:
        print("Nessun evento trovato!")


if __name__ == '__main__':
    main()

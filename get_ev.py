import urllib.request
import urllib.parse
import sys
import os
import json
import base64


HERO_URL = os.getenv("HERO_URL")
HERO_UA = "MandraKodi2@@2.2.1@@@@A7B9X2"
VLC_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
LOGO = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/international/dazn-int.png"


def makeRequest(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print(f"API non raggiungibile: {e}")
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
                target = item["title"].find("(ITA - MPD - WARP)")
                if target != -1:
                    start = item["title"].find("]")
                    end = item["title"].find("[", start)
                    title = item["title"][start + 1:end].replace(" (ITA - MPD - WARP)","")
                    b64 = item["myresolve"].replace("amstaff@@","").strip()
                    payload = base64.b64decode(b64).decode("utf-8")
                    arrTmp = payload.split("|")
                    link = urllib.parse.unquote(arrTmp[0])
                    key = arrTmp[1]
                    events.append('\n#EXTINF:-1 tvg-logo="'+LOGO+'" group-title="DAZN",'+title)
                    events.append('\n#EXTVLCOPT:http-user-agent='+VLC_UA)
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
        print(f"Eventi trovati: {len(events)//5}")
    else:
        print("Nessun evento trovato!")


if __name__ == '__main__':
    main()

import requests
import sys
import os
import json

SUPABASE_TOKEN = os.getenv("SUPABASE_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
CATEGORY_NAMES = {"sky italia", "dazn", "timvision"}
PLAY_FILE = "dynamic.m3u"

def get_all_channels():
    # Recupera tutti i canali da Supabase.
    headers = {
        "user-agent": "Mozilla/5.0",
        'x-client-info': 'supabase-js-web/2.99.3',
        'apikey': SUPABASE_TOKEN,
        'authorization': 'Bearer ' + SUPABASE_TOKEN
    }
    params = {"select": "*", "order": "title.asc"}
    try:
        r = requests.get(SUPABASE_URL, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Errore nel recupero canali: {e}", file=sys.stderr)
        return None

def parse_old_file(filepath):
    # Legge la vecchia playlist e restituisce una lista ordinata di blocchi.
    # Ogni blocco è un dizionario con chiavi: 'lines' (tutte le righe del blocco), 'name' (normalizzato).
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            # Raccogli il blocco fino all'URL incluso
            block_start = i
            # Estrai nome
            name = line.split(',', 1)[-1].strip()
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('http'):
                i += 1
            if i < len(lines) and lines[i].strip().startswith('http'):
                blocks.append({
                    'lines': lines[block_start:i+1],  # tutte le righe del blocco
                    'name': name.strip().lower()
                })
        else:
            i += 1
    return blocks

def find_in_supabase(name, supabase_data):
    # Cerca il canale in Supabase (confronto case‑insensitive).
    if not supabase_data:
        return None
    target = name.lower()
    for item in supabase_data:
        title = item.get('title', '').strip().lower()
        if title == target:
            return item
    return None

def main():
    print("📡 Recupero canali da Supabase...")
    supabase_data = get_all_channels()
    if supabase_data is None:
        print("❌ Supabase irraggiungibile. La lista non verrà modificata.")
        # Se il file esiste già, non facciamo nulla; altrimenti errore
        if not os.path.exists(PLAY_FILE):
            print(f"❌ Il file {PLAY_FILE} non esiste e non possiamo generarlo.")
            sys.exit(1)
        return
    # Filtra per categoria
    supabase_channels = [c for c in supabase_data if c.get('category', '').strip().lower() in CATEGORY_NAMES]
    print(f"📌 Trovati {len(supabase_channels)} canali in Supabase.")

    old_blocks = parse_old_file(PLAY_FILE)
    if not old_blocks:
        print(f"❌ Il file {PLAY_FILE} è vuoto o non esiste. Nessun aggiornamento possibile.")
        sys.exit(1)

    updated_blocks = []
    tally = 0
    for block in old_blocks:
        name = block['name']
        sup_item = find_in_supabase(name, supabase_channels)
        if sup_item:
            # Aggiorna solo URL e DRM; il resto (logo, gruppo, nome) resta uguale
            kids = sup_item.get('drm_key_id', '')
            keys = sup_item.get('drm_key', '')
            mpd = sup_item.get('mpd_url', '')
            # Ricostruisci le righe KODIPROP
            new_lines = [block['lines'][0]]  # EXTINF (logo, gruppo, nome originali)
            if kids and keys:
                kids_list = [k.strip() for k in kids.split(',') if k.strip()]
                keys_list = [k.strip() for k in keys.split(',') if k.strip()]
                license_key = ','.join(f"{kid}:{key}" for kid, key in zip(kids_list, keys_list))
                new_lines.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd\n')
                new_lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                new_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={license_key}\n')
            else:
                # Mantieni le vecchie righe KODIPROP se non ci sono nuove chiavi
                # Prendi tutte le righe dopo EXTINF fino all'URL escluso
                old_kodis = block['lines'][1:-1]  # escludendo EXTINF e URL
                new_lines.extend(old_kodis)
            new_lines.append(mpd + '\n')
            updated_blocks.append(''.join(new_lines))
            tally += 1
        else:
            # Canale non trovato in Supabase: mantieni il blocco originale
            updated_blocks.append(''.join(block['lines']))

    # Scrivi il file
    with open(PLAY_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for blk in updated_blocks:
            f.write(blk)
    print(f"✔️ {PLAY_FILE} generato con {len(old_blocks)} canali, di cui {tally} aggiornati.")

if __name__ == "__main__":
    main()

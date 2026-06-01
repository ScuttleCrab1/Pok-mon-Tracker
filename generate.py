#!/usr/bin/env python3
"""
Pokémon Collection Tracker — Générateur automatique
"""

import csv, json, os, glob, re, time, urllib.request, urllib.parse
from datetime import datetime

ROOT        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(ROOT, 'data')
PERIODS_DIR = os.path.join(ROOT, 'periodes')
IMAGES_DIR  = os.path.join(ROOT, 'images')
OUTPUT      = os.path.join(ROOT, 'index.html')
TEMPLATE    = os.path.join(ROOT, 'template.html')

TCG_API_KEY = 'ea266427-2a4b-4dbb-9a98-b54aec7a2a4f'

SET_MAP = {
    '151':'sv3pt5','Alliance Infaillible':'sm10','Aquapolis':'ecard2',
    'Astres Radieux':'swsh10','Aventures Ensemble':'sv6','Couronne Stellaire':'sv7',
    'Dechainement':'ex15','Deoxys':'ex14','Destinees de Paldea':'sv4pt5',
    'Dragon':'ex12','Dragons Exaltes':'bw6','Duo de Choc':'sm9',
    'Ecarlate et Violet':'sv1','Emeraude':'ex10','Espece Delta':'ex11',
    'Etincelles Deferlantes':'sv8','Evolutions Prismatiques':'sv8pt5',
    'Expedition':'ecard1','Fable Nebuleuse':'sv6pt5','Faille Paradoxe':'sv4',
    'Flamme Blanche':'bw9','Flammes Fantasmagoriques':'sv3',
    'Flammes Obsidiennes':'sv3pt5','Forces Cachees':'swsh6',
    'Forces Temporelles':'sv5','Foudre Noire':'bw5','Frontieres Franchies':'swsh7',
    'Glaciation Plasma':'bw8','Heartgold Soulsilver':'hgss1',
    'Heros Transcendants':'sv5','Ile des Dragons':'ex4','Indomptable':'hgss2',
    'L Appel des Legendes':'hgss3','Legendes Oubliees':'cel25',
    'Mascarade Crepusculaire':'sv6pt5','Mega-Evolution':'xy8',
    'Origine Perdue':'swsh11','Pouvoirs Emergeants':'bw2',
    'Promos Black Star Noir et Blanc':'bwp','Promos Ecarlate et Violet':'svp',
    'Promos Mega-Evolution':'xyp','Rivalites Destinees':'sm8',
    'Rivaux Emergeants':'bw3','Rouge Feu Vert Feuille':'ex2',
    'Rubis et Saphir':'ex1','Set de Base':'base1','Stars Etincelantes':'swsh9',
    'Team Magma Vs Team Aqua':'ex5','Team Rocket':'base4',
    'Tempete de Sable':'ex3','Tresors Mysterieux':'ex13',
    'Triomphe':'hgss4','Vainqueurs Supremes':'hgss3','Zenith Supreme':'swsh12pt5',
}

# ── HELPERS ────────────────────────────────────────────────────────

def parse_num(s):
    if not s: return 0.0
    return float(str(s).replace('€','').replace('\xa0','').replace(' ','').replace(',','.').strip()) or 0.0

def parse_cartes(filepath):
    cartes = []
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            row['_achat']  = parse_num(row.get('Prix Achat', 0))
            row['_actuel'] = parse_num(row.get('Prix Actuel', 0))
            row['_gain']   = row['_actuel'] - row['_achat'] if row['_achat'] > 0 else None
            row['_key']    = f"{row.get('Nom','')}|{row.get('Numéro','')}|{row.get('Série','')}|{row.get('État','')}|{row.get('Version','')}"
            if row.get('Nom'):
                cartes.append(row)
    return cartes

def parse_items(filepath):
    items = []
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            row['_qte']    = int(row.get('Quantité', 1) or 1)
            row['_achat']  = parse_num(row.get('Prix Achat', 0))
            row['_actuel'] = parse_num(row.get('Prix Actuel', 0))
            row['_gain']   = parse_num(row.get('Gain Théorique', 0))
            row['_pct']    = round(row['_gain'] / row['_achat'] * 100, 2) if row['_achat'] > 0 else None
            row['_key']    = f"{row.get('Item','')}|{row.get('Série','')}"
            if row.get('Série'):
                items.append(row)
    return items

# ── IMAGES PAR BATCH ───────────────────────────────────────────────

def api_get(query, page_size=250):
    url = f"https://api.pokemontcg.io/v2/cards?q={urllib.parse.quote(query)}&pageSize={page_size}"
    req = urllib.request.Request(url, headers={
        'X-Api-Key': TCG_API_KEY,
        'User-Agent': 'PokemonTracker/1.0'
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()).get('data', [])

def fetch_set_images(set_id):
    """Récupère TOUTES les cartes d'un set en une seule requête"""
    try:
        cards = api_get(f"set.id:{set_id}", page_size=250)
        # Indexer par numéro
        index = {}
        for c in cards:
            num = str(c.get('number', ''))
            img = c.get('images', {}).get('large') or c.get('images', {}).get('small')
            if img:
                index[num] = img
                index[num.lstrip('0') or num] = img
        return index
    except Exception as e:
        print(f"    ⚠ Erreur set {set_id}: {e}")
        return {}

def download_images(cartes):
    """Récupère les images par SET (1 requête par set au lieu d'1 par carte)"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    cache_path = os.path.join(IMAGES_DIR, 'cache.json')

    # Charger le cache
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            cache = json.load(f)

    # Regrouper les cartes par set
    sets_needed = {}
    for c in cartes:
        if c['_key'] in cache:
            continue
        serie  = c.get('Série', '')
        set_id = SET_MAP.get(serie)
        if set_id:
            if set_id not in sets_needed:
                sets_needed[set_id] = []
            sets_needed[set_id].append(c)
        else:
            # Pas de mapping — mettre None dans le cache
            cache[c['_key']] = None

    cached_count = sum(1 for c in cartes if c['_key'] in cache)
    print(f"  → {cached_count} en cache, {len(sets_needed)} sets à récupérer")

    # Récupérer les images set par set
    for set_id, set_cartes in sets_needed.items():
        print(f"    Récupération set {set_id} ({len(set_cartes)} cartes)...")
        set_index = fetch_set_images(set_id)

        for c in set_cartes:
            num_orig  = c.get('Numéro', '').split('/')[0]
            num_clean = num_orig.lstrip('0') or num_orig
            img = set_index.get(num_orig) or set_index.get(num_clean)
            cache[c['_key']] = img

        time.sleep(0.3)  # Respecter le rate limit entre les sets

    # Sauvegarder le cache
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

    # Construire le dict final
    images = {c['_key']: cache.get(c['_key']) for c in cartes}
    found  = sum(1 for v in images.values() if v)
    print(f"  ✓ Images : {found}/{len(cartes)} trouvées")
    return images

# ── LOAD/SAVE PERIODS ──────────────────────────────────────────────

def load_periods():
    os.makedirs(PERIODS_DIR, exist_ok=True)
    periods = []
    for f in sorted(glob.glob(os.path.join(PERIODS_DIR, '*.json'))):
        with open(f, encoding='utf-8') as fp:
            periods.append(json.load(fp))
    return periods

def save_current_as_period(cartes, items, name, date_str):
    os.makedirs(PERIODS_DIR, exist_ok=True)
    period = {
        'id': int(datetime.now().timestamp()),
        'name': name, 'date': date_str,
        'cartes': cartes, 'items': items,
        'totalCartes': sum(c['_actuel'] for c in cartes),
        'totalItems':  sum(i['_actuel'] for i in items),
    }
    filename = f"{date_str}_{re.sub(r'[^a-zA-Z0-9]', '_', name)}.json"
    with open(os.path.join(PERIODS_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(period, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ Période sauvegardée : {filename}")
    return period

def find_csv_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    cartes_file = items_file = None
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        b = os.path.basename(f).lower()
        if 'cartes' in b or 'carte' in b:
            cartes_file = f
        elif 'items' in b or 'item' in b:
            items_file = f
    return cartes_file, items_file

# ── GENERATE HTML ──────────────────────────────────────────────────

def fix_period_data(p):
    """Recalcule _key, _actuel, _achat sur les données d'une période"""
    for c in p.get('cartes', []):
        if not c.get('_key'):
            c['_key'] = f"{c.get('Nom','')}|{c.get('Numéro','')}|{c.get('Série','')}|{c.get('État','')}|{c.get('Version','')}"
        if c.get('_actuel') is None:
            c['_actuel'] = parse_num(c.get('Prix Actuel', 0))
        if c.get('_achat') is None:
            c['_achat'] = parse_num(c.get('Prix Achat', 0))
    for i in p.get('items', []):
        if not i.get('_key'):
            i['_key'] = f"{i.get('Item','')}|{i.get('Série','')}"
        if i.get('_actuel') is None:
            i['_actuel'] = parse_num(i.get('Prix Actuel', 0))
        if i.get('_achat') is None:
            i['_achat'] = parse_num(i.get('Prix Achat', 0))
        if i.get('_gain') is None:
            i['_gain'] = parse_num(i.get('Gain Théorique', 0))
        if i.get('_qte') is None:
            i['_qte'] = int(i.get('Quantité', 1) or 1)
        if i.get('_pct') is None:
            i['_pct'] = round(i['_gain'] / i['_achat'] * 100, 2) if i['_achat'] > 0 else None
    if not p.get('totalCartes'):
        p['totalCartes'] = sum(c.get('_actuel', 0) for c in p.get('cartes', []))
    if not p.get('totalItems'):
        p['totalItems'] = sum(i.get('_actuel', 0) for i in p.get('items', []))

def generate_html(cartes, items, periods, images):
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()

    # Recalculer les données manquantes sur toutes les périodes
    for p in periods:
        fix_period_data(p)

    for c in cartes:
        c['_img'] = images.get(c['_key'])
    for p in periods:
        for c in p.get('cartes', []):
            if '_key' in c:
                c['_img'] = images.get(c['_key'])

    html = template
    html = html.replace('__SEED_CARTES__',  json.dumps(cartes,   ensure_ascii=False, separators=(',',':'), default=str))
    html = html.replace('__SEED_ITEMS__',   json.dumps(items,    ensure_ascii=False, separators=(',',':'), default=str))
    html = html.replace('__SEED_PERIODS__', json.dumps(periods,  ensure_ascii=False, separators=(',',':'), default=str))
    html = html.replace('__GEN_DATE__', datetime.now().strftime('%Y-%m-%d %H:%M'))

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ index.html généré ({len(html):,} caractères)")

# ── MAIN ───────────────────────────────────────────────────────────

def main():
    print("\n🎴 Pokémon Tracker — Génération automatique")
    print("=" * 45)

    cartes_file, items_file = find_csv_files()
    if not cartes_file or not items_file:
        print("  ✗ Fichiers CSV introuvables dans /data/")
        exit(1)

    print(f"  ✓ Cartes  : {os.path.basename(cartes_file)}")
    print(f"  ✓ Items   : {os.path.basename(items_file)}")

    cartes = parse_cartes(cartes_file)
    items  = parse_items(items_file)
    total  = sum(c['_actuel'] for c in cartes) + sum(i['_actuel'] for i in items)
    print(f"  ✓ {len(cartes)} cartes · {len(items)} items · Total : {total:.2f} €")

    print("  → Récupération des images par set...")
    images = download_images(cartes)

    periods = load_periods()
    today = datetime.now().strftime('%Y-%m-%d')
    should_save = True
    if periods:
        last = periods[-1]
        last_total = last.get('totalCartes', 0) + last.get('totalItems', 0)
        if abs(last_total - total) < 0.01 and last.get('date') == today:
            should_save = False
            print("  ℹ Période d'aujourd'hui déjà enregistrée, pas de doublon")

    if should_save:
        period_name = f"Période {len(periods) + 1}"
        new_period  = save_current_as_period(cartes, items, period_name, today)
        periods.append(new_period)

    print(f"  ✓ {len(periods)} période(s) dans l'historique")
    generate_html(cartes, items, periods, images)
    print("\n✅ Terminé !")
    print("=" * 45)

if __name__ == '__main__':
    main()

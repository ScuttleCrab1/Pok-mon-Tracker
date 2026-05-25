#!/usr/bin/env python3
"""
Pokémon Collection Tracker — Générateur automatique
----------------------------------------------------
Ce script lit les fichiers CSV dans /data/ et les fichiers
de périodes sauvegardées dans /periodes/, puis regénère index.html.

Usage : python3 generate.py
"""

import csv, json, os, glob, re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(ROOT, 'data')
PERIODS_DIR = os.path.join(ROOT, 'periodes')
OUTPUT      = os.path.join(ROOT, 'index.html')
TEMPLATE    = os.path.join(ROOT, 'template.html')

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

# ── LOAD PERIODS ───────────────────────────────────────────────────

def load_periods():
    """Charge toutes les périodes sauvegardées depuis /periodes/*.json"""
    os.makedirs(PERIODS_DIR, exist_ok=True)
    periods = []
    for f in sorted(glob.glob(os.path.join(PERIODS_DIR, '*.json'))):
        with open(f, encoding='utf-8') as fp:
            p = json.load(fp)
            periods.append(p)
    return periods

def save_current_as_period(cartes, items, name, date_str):
    """Sauvegarde les données courantes comme nouvelle période"""
    os.makedirs(PERIODS_DIR, exist_ok=True)
    period = {
        'id': int(datetime.now().timestamp()),
        'name': name,
        'date': date_str,
        'cartes': cartes,
        'items': items,
        'totalCartes': sum(c['_actuel'] for c in cartes),
        'totalItems': sum(i['_actuel'] for i in items),
    }
    filename = f"{date_str}_{re.sub(r'[^a-zA-Z0-9]', '_', name)}.json"
    filepath = os.path.join(PERIODS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(period, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ Période sauvegardée : {filepath}")
    return period

# ── FIND CSV FILES ─────────────────────────────────────────────────

def find_csv_files():
    """Cherche les fichiers CSV dans /data/"""
    os.makedirs(DATA_DIR, exist_ok=True)
    cartes_file = None
    items_file  = None
    for f in glob.glob(os.path.join(DATA_DIR, '*.csv')):
        basename = os.path.basename(f).lower()
        if 'cartes' in basename or 'carte' in basename:
            cartes_file = f
        elif 'items' in basename or 'item' in basename or 'portefeuille_items' in basename:
            items_file = f
    return cartes_file, items_file

# ── GENERATE HTML ──────────────────────────────────────────────────

def generate_html(cartes, items, periods):
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()

    cartes_js  = json.dumps(cartes,  ensure_ascii=False, separators=(',',':'), default=str)
    items_js   = json.dumps(items,   ensure_ascii=False, separators=(',',':'), default=str)
    periods_js = json.dumps(periods, ensure_ascii=False, separators=(',',':'), default=str)

    html = template
    html = html.replace('__SEED_CARTES__', cartes_js)
    html = html.replace('__SEED_ITEMS__',  items_js)
    html = html.replace('__SEED_PERIODS__', periods_js)
    html = html.replace('__GEN_DATE__', datetime.now().strftime('%Y-%m-%d %H:%M'))

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ index.html généré ({len(html):,} caractères)")

# ── MAIN ───────────────────────────────────────────────────────────

def main():
    print("\n🎴 Pokémon Tracker — Génération automatique")
    print("=" * 45)

    # 1. Chercher les CSV
    cartes_file, items_file = find_csv_files()
    if not cartes_file or not items_file:
        print(f"  ✗ Fichiers CSV introuvables dans /data/")
        print(f"    Attendu : portefeuille_cartes.csv + portefeuille_items.csv")
        exit(1)

    print(f"  ✓ Cartes  : {os.path.basename(cartes_file)}")
    print(f"  ✓ Items   : {os.path.basename(items_file)}")

    # 2. Parser les CSV
    cartes = parse_cartes(cartes_file)
    items  = parse_items(items_file)
    total  = sum(c['_actuel'] for c in cartes) + sum(i['_actuel'] for i in items)
    print(f"  ✓ {len(cartes)} cartes · {len(items)} items · Total : {total:.2f} €")

    # 3. Charger les périodes existantes
    periods = load_periods()

    # 4. Sauvegarder automatiquement comme nouvelle période
    #    (si les données sont différentes de la dernière période)
    today = datetime.now().strftime('%Y-%m-%d')
    should_save = True
    if periods:
        last = periods[-1]
        last_total = last.get('totalCartes', 0) + last.get('totalItems', 0)
        if abs(last_total - total) < 0.01 and last.get('date') == today:
            should_save = False
            print(f"  ℹ Période d'aujourd'hui déjà enregistrée, pas de doublon")

    if should_save:
        period_name = f"Période {len(periods) + 1}"
        new_period  = save_current_as_period(cartes, items, period_name, today)
        periods.append(new_period)

    print(f"  ✓ {len(periods)} période(s) dans l'historique")

    # 5. Générer l'HTML
    generate_html(cartes, items, periods)
    print("\n✅ Terminé ! Uploadez index.html sur GitHub Pages.")
    print("=" * 45)

if __name__ == '__main__':
    main()

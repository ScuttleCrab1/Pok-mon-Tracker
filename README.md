# 🎴 Pokémon Collection Tracker

Dashboard de suivi de ta collection Pokémon, mis à jour automatiquement via GitHub Actions.

## 📁 Structure du projet

```
pokemon-tracker/
├── index.html                  ← Le dashboard (généré automatiquement)
├── template.html               ← Template HTML (ne pas modifier)
├── generate.py                 ← Script de génération
├── data/
│   ├── portefeuille_cartes.csv ← Tes exports iEstim (à uploader)
│   └── portefeuille_items.csv  ← Tes exports iEstim (à uploader)
├── periodes/
│   └── *.json                  ← Historique des périodes (auto-généré)
└── .github/
    └── workflows/
        └── generate.yml        ← GitHub Actions (automatisation)
```

---

## 🚀 Mise en place initiale (une seule fois)

### 1. Activer GitHub Pages
- Va dans **Settings** → **Pages**
- Source : **Deploy from a branch**
- Branch : `main` / `/ (root)`
- Clique **Save**

### 2. Autoriser GitHub Actions à écrire dans le dépôt
- Va dans **Settings** → **Actions** → **General**
- Tout en bas : **Workflow permissions**
- Sélectionne **Read and write permissions**
- Clique **Save**

---

## 📤 Mettre à jour la collection (utilisation normale)

C'est la seule chose à faire à chaque mise à jour :

1. Va sur ton dépôt GitHub
2. Clique sur le dossier **`data/`**
3. Clique **"Add file"** → **"Upload files"**
4. Glisse tes 2 fichiers CSV depuis iEstim :
   - `portefeuille_cartes.csv`
   - `portefeuille_items.csv`
5. Clique **"Commit changes"**

⚡ GitHub Actions se déclenche automatiquement et en 30 secondes :
- Régénère `index.html` avec tes nouvelles données
- Sauvegarde automatiquement la nouvelle période dans `/periodes/`
- Ton URL est à jour !

---

## 🔧 Lancer manuellement

Si tu veux forcer une régénération sans uploader de nouveaux CSV :
- Va dans **Actions** → **🎴 Régénérer le Pokémon Tracker**
- Clique **"Run workflow"**

---

## 📊 Fonctionnalités du dashboard

| Onglet | Contenu |
|--------|---------|
| **Vue d'ensemble** | KPIs, Top 10 cartes, répartition par état/bloc |
| **Cartes** | Tableau filtrable de toutes les cartes |
| **Scellé** | Items scellés avec gains et rendements |
| **Comparaison P1→P2** | Différences entre deux périodes importées |
| **📈 Évolution** | Graphiques multi-périodes + Top 10 performers |

---

## ❓ FAQ

**Les périodes sont-elles conservées à chaque update ?**
Oui ! Chaque mise à jour ajoute une nouvelle période dans `/periodes/` sans effacer les anciennes.

**Que se passe-t-il si j'uploade les mêmes données deux fois le même jour ?**
Le script détecte le doublon et ne crée pas de période en double.

**Puis-je renommer une période ?**
Oui, en renommant le fichier `.json` correspondant dans `/periodes/` et en modifiant le champ `"name"` à l'intérieur.

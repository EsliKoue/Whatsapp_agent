# 🤖 Agent IA WhatsApp Premium & Assistant Personnel Modulaire

[![Python](https://shields.io)](https://python.org)
[![Package Manager](https://shields.io)](https://github.com)
[![LLM](https://shields.io)](https://groq.com)
[![Database](https://shields.io)](https://postgresql.org)

Cet agent WhatsApp open-source haut de gamme combine la puissance des modèles de pointe de **Groq (Llama 3.3 & Whisper)** avec une persistance d'historique sous **PostgreSQL**. Conçu de manière modulaire, il intègre un algorithme d'agrégation asynchrone et une capacité d'exécution d'outils en temps réel (_Function Calling_).

---

## ✨ Fonctionnalités Clés

- 🧠 **Cerveau Hybride de Production** : Propulsé par `llama-3.3-70b-versatile` pour un raisonnement rapide, précis et multilingue.
- ⏳ **Algorithme d'Agrégation Temporelle (Debounce)** : Système intelligent à base de threads (`threading.Timer`) qui regroupe les messages rapides d'un utilisateur pour éviter le spam et économiser les jetons (tokens) d'API.
- 🗄️ **Persistance Relationnelle Stable** : Historique complet indexé sous **PostgreSQL** offrant une mémoire contextuelle infinie aux conversations.
- 🛠️ **Function Calling (Appel d'Outils)** : Capacité pour l'IA de déclencher de manière autonome des scripts Python locaux (ex: vérification de l'heure, planification de rappels).
- 🗣️ **Pipeline Audio (Whisper-Turbo)** : Interception et transcription instantanée des messages vocaux WhatsApp via le modèle `whisper-large-v3-turbo`.
- 👔 **Posture Humaine & Professionnelle** : Prompt système avancé configuré pour agir comme un secrétaire exécutif premium (aucune mention robotique).

---

## 📂 Architecture Modulaire du Projet

Le code a été découpé selon les principes de conception SOLID pour faciliter la maintenance et l'évolutivité :

```text
mon-agent-groq/
├── database/
│   ├── __init__.py
│   └── models.py             # Gestionnaire d'infrastructure PostgreSQL
├── services/
│   ├── __init__.py
│   ├── ai_service.py         # Routage des LLM Groq (Texte & Whisper)
│   └── tools_service.py      # Définition et exécution des outils locaux (Tools)
├── .gitignore                # Protection des variables sensibles et de l'environnement
├── pyproject.toml            # Manifeste des dépendances géré par uv
├── main.py                   # Point d'entrée de l'orchestrateur (Client Neonize)
└── README.md                 # Documentation technique du dépôt
```

---

## 🚀 Installation et Lancement

### 📋 Prérequis

- **Python 3.11 ou supérieur**
- Gestionnaire de paquets [uv](https://github.com) (`pip install uv`)
- Une base de données **PostgreSQL** active (Locale ou Cloud via Supabase/Neon)
- Une clé d'API valide sur la [Console Groq](https://groq.com)

### 🛠️ Configuration de l'environnement

1. Clonez votre dépôt GitHub personnel :

   ```bash
   git clone https://github.com
   cd mon-agent-groq
   ```

2. Créez et activez votre environnement virtuel synchronisé automatiquement grâce à `uv` :

   ```bash
   uv venv
   # Sur Windows (PowerShell) :
   .venv\Scripts\activate
   ```

3. Installez l'ensemble des dépendances gelées dans le projet :

   ```bash
   uv pip install groq psycopg2-binary python-dotenv neonize
   ```

4. Configurez vos clés secrètes dans votre fichier `.env` ou directement dans `services/ai_service.py` :
   ```ini
   DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/postgres
   ```

### 🏃‍♂️ Exécution du projet

Lancez l'orchestrateur principal de production :

```bash
uv run python main.py
```

_Note : Lors du tout premier lancement, un **QR Code** s'affichera dans votre terminal. Scannez-le via l'application WhatsApp de votre smartphone (**Appareils connectés** ➡️ **Connecter un appareil**) pour lier votre instance._

---

## 🤝 Contribution & Conventions Git

Ce projet adopte les standards de commits **Conventional Commits** :

- `feat:` pour l'ajout d'une nouvelle fonctionnalité.
- `fix:` pour la résolution d'un bug.
- `docs:` pour la modification de la documentation.

Pour pousser vos modifications locales vers ce dépôt GitHub :

```bash
git add .
git commit -m "feat: stable production release with tool calling integrations"
git push origin main
```

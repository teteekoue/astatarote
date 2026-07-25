#!/bin/bash

# Style colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=================================================================="
echo "    🛡️  ASTATAROTE - INITIALISATION ET INSTALLATION LOCALE  🛡️"
echo "=================================================================="
echo -e "${NC}"

# Check for Python 3
echo -e "[*] Vérification de Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[-] Erreur: Python 3 n'est pas installé sur votre machine.${NC}"
    echo "Veuillez installer Python 3.10+ pour continuer."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[+] Trouvé: $PYTHON_VERSION${NC}"

# Check for Node.js / NPM
echo -e "[*] Vérification de Node.js et NPM..."
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}[!] Attention: Node.js n'est pas installé sur votre machine.${NC}"
    echo "Vous aurez besoin de Node.js (v18+) et npm pour exécuter le frontend localement."
fi
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}[!] Attention: npm n'est pas installé sur votre machine.${NC}"
fi
echo -e "${GREEN}[+] Trouvé: Node $(node -v) / NPM $(npm -v)${NC}"

# 1. Setup Backend virtual environment and dependencies
echo -e "\n${BLUE}[1/3] Configuration du Backend (Python)...${NC}"
cd backend || { echo -e "${RED}[-] Dossier 'backend' manquant.${NC}"; exit 1; }

if [ ! -d ".venv" ]; then
    echo -e "[*] Création de l'environnement virtuel Python (.venv)..."
    python3 -m venv .venv
fi

echo -e "[*] Activation de l'environnement virtuel et mise à jour de pip..."
source .venv/bin/activate

echo -e "[*] Installation des dépendances Python du backend..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] Dépendances Backend installées avec succès !${NC}"
else
    echo -e "${RED}[-] Erreur lors de l'installation des dépendances Backend.${NC}"
    exit 1
fi

deactivate
cd ..

# 2. Setup Frontend dependencies
echo -e "\n${BLUE}[2/3] Configuration du Frontend (React / TypeScript)...${NC}"
cd frontend || { echo -e "${RED}[-] Dossier 'frontend' manquant.${NC}"; exit 1; }

echo -e "[*] Installation des modules Node.js..."
npm install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] Dépendances Frontend installées avec succès !${NC}"
else
    echo -e "${RED}[-] Erreur lors de l'installation des dépendances Frontend.${NC}"
    exit 1
fi
cd ..

# 3. Setup Environment Variables
echo -e "\n${BLUE}[3/3] Configuration des variables d'environnement...${NC}"
if [ ! -f ".env" ]; then
    echo -e "[*] Création du fichier de configuration .env par défaut..."
    cat <<EOT > .env
# Configuration locale d'Astatarote
DATABASE_URL=sqlite://///home/user/astarote/astarote.db

# Clés d'API d'IA optionnelles (Groq, NVIDIA, Cohere, Together, Fireworks)
# GROQ_API_KEY=
# NVIDIA_API_KEY=
EOT
    echo -e "${GREEN}[+] Fichier .env créé à la racine.${NC}"
else
    echo -e "${YELLOW}[!] Le fichier .env existe déjà, saut de cette étape.${NC}"
fi

echo -e "${GREEN}"
echo "=================================================================="
echo "    🎉 TOUTES LES DÉPENDANCES ONT ÉTÉ INSTALLÉES AVEC SUCCÈS ! 🎉"
echo "=================================================================="
echo -e "${NC}"
echo -e "Pour démarrer le projet localement (sans Docker) :"
echo -e ""
echo -e "👉 ${YELLOW}Dans un premier terminal (Backend) :${NC}"
echo -e "   cd backend"
echo -e "   source .venv/bin/activate"
echo -e "   uvicorn app.main:app --reload"
echo -e ""
echo -e "👉 ${YELLOW}Dans un second terminal (Frontend) :${NC}"
echo -e "   cd frontend"
echo -e "   npm run dev"
echo -e ""
echo -e "Et ouvrez l'adresse http://localhost:3000 dans votre navigateur."

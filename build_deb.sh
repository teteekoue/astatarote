#!/bin/bash

# Script to build .deb packages for amd64 and i386 architectures
ARCH=${1:-"amd64"}
VERSION="1.0.0"
PKG_DIR="pkg_build_${ARCH}"

echo "[*] Initialisation de la construction du paquet .deb pour l'architecture ${ARCH}..."

# Remove any old build folders
rm -rf "${PKG_DIR}"
rm -f "astatarote_${VERSION}_${ARCH}.deb"

# 1. Create Debian directory structure
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/astatarote"
mkdir -p "${PKG_DIR}/usr/share/applications"

# 2. Copy application source files
echo "[*] Copie des sources de l'application..."
# Copy backend code (excluding virtual environments and database)
mkdir -p "${PKG_DIR}/usr/share/astatarote/backend"
cp -r backend/app "${PKG_DIR}/usr/share/astatarote/backend/"
cp backend/requirements.txt "${PKG_DIR}/usr/share/astatarote/backend/"

# Copy frontend compiled build
mkdir -p "${PKG_DIR}/usr/share/astatarote/frontend"
cp -r frontend/dist "${PKG_DIR}/usr/share/astatarote/frontend/"

# Copy logo asset
cp frontend/public/logo.png "${PKG_DIR}/usr/share/astatarote/"

# 3. Create /usr/bin/astatarote launcher script
echo "[*] Création du script de lancement /usr/bin/astatarote..."
cat << 'EOF' > "${PKG_DIR}/usr/bin/astatarote"
#!/bin/bash

# Check arguments
if [ "$1" == "off" ]; then
    echo "[*] Arrêt complet d'Astatarote (Serveurs et services)..."
    pkill -f "uvicorn backend.app.main:app" && echo "[+] Tous les services ont été arrêtés !" || echo "[-] Aucun service Astatarote actif trouvé."
    exit 0
fi

if [ "$1" == "on" ] || [ -z "$1" ]; then
    PORT=8000
    if lsof -i :$PORT &>/dev/null; then
        echo "[!] Le port $PORT est déjà utilisé. Lancement du navigateur..."
    else
        echo "[*] Démarrage du serveur backend d'Astatarote sur le port $PORT..."
        cd /usr/share/astatarote
        PYTHONPATH=/usr/share/astatarote /usr/share/astatarote/backend/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port $PORT > /tmp/astatarote_backend.log 2>&1 &
        # Give the backend 3 seconds to spin up
        sleep 3
    fi

    # Automatically open browser
    echo "[*] Ouverture du navigateur vers la console Astatarote..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://127.0.0.1:$PORT/"
    elif command -v gnome-open &> /dev/null; then
        gnome-open "http://127.0.0.1:$PORT/"
    else
        echo "[!] Navigateur introuvable. Veuillez ouvrir manuellement : http://127.0.0.1:$PORT/"
    fi
    exit 0
fi

echo "Usage : astatarote [on|off]"
exit 1
EOF

chmod +x "${PKG_DIR}/usr/bin/astatarote"

# 4. Create Desktop Entry shortcut
echo "[*] Création du raccourci d'application .desktop..."
cat << EOF > "${PKG_DIR}/usr/share/applications/astatarote.desktop"
[Desktop Entry]
Name=Astatarote
Comment=Plateforme d'apprentissage Linux et Cybersécurité adaptative
Exec=/usr/bin/astatarote
Icon=/usr/share/astatarote/logo.png
Terminal=false
Type=Application
Categories=Education;Development;ComputerScience;
EOF

# 5. Create Debian metadata CONTROL file
echo "[*] Création du fichier DEBIAN/control..."
cat << EOF > "${PKG_DIR}/DEBIAN/control"
Package: astatarote
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: teteekoue <teteekoue@users.noreply.github.com>
Depends: python3, python3-pip, python3-venv, lsof
Description: Plateforme d'apprentissage Linux et Cybersécurité adaptative
 Astatarote est une plateforme d'apprentissage gamifiée pour l'administration Linux
 et la cybersécurité. L'IA génère dynamiquement des scénarios d'apprentissage adaptés.
EOF

# 6. Create post-installation script (compiles python venv & sets permissions)
echo "[*] Création du script de post-installation (postinst)..."
cat << 'EOF' > "${PKG_DIR}/DEBIAN/postinst"
#!/bin/bash
set -e

echo "[*] Configuration de l'environnement virtuel pour Astatarote..."
cd /usr/share/astatarote/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Create initial directory permissions
chmod -R 777 /usr/share/astatarote

echo "[+] Installation d'Astatarote terminée avec succès !"
echo "Vous pouvez maintenant lancer l'application en tapant 'astatarote' dans la console ou depuis votre menu d'applications."
EOF

chmod +x "${PKG_DIR}/DEBIAN/postinst"

# 7. Create pre-removal script (cleans virtualenv)
echo "[*] Création du script de pré-désinstallation (prerm)..."
cat << 'EOF' > "${PKG_DIR}/DEBIAN/prerm"
#!/bin/bash
set -e

echo "[*] Nettoyage de l'environnement d'Astatarote..."
pkill -f uvicorn || true
rm -rf /usr/share/astatarote/backend/.venv
EOF

chmod +x "${PKG_DIR}/DEBIAN/prerm"

# 8. Build the Debian Package
echo "[*] Construction du fichier de paquet .deb..."
dpkg-deb --build "${PKG_DIR}" "astatarote_${VERSION}_${ARCH}.deb"

if [ $? -eq 0 ]; then
    echo "[+] Paquet construit avec succès : astatarote_${VERSION}_${ARCH}.deb !"
else
    echo "[-] Échec de la construction du paquet."
    exit 1
fi

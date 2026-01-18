#!/bin/bash
# Automatická instalace a spuštění importu na serveru
# Použití: bash install_on_server.sh

echo "================================================"
echo " Automatická instalace mob_proto import skriptu"
echo "================================================"
echo ""

# Zkontrolovat Python
echo "[1/6] Kontrola Python..."
if ! command -v python3 &> /dev/null; then
    echo "CHYBA: Python3 není nainstalován!"
    echo "Nainstalovat? (y/n)"
    read -p "> " INSTALL_PYTHON
    if [ "$INSTALL_PYTHON" = "y" ]; then
        apt-get update && apt-get install python3 python3-pip -y
    else
        echo "Ukončuji..."
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Python nainstalován: $PYTHON_VERSION"
echo ""

# Zkontrolovat pip3
echo "[2/6] Kontrola pip3..."
if ! command -v pip3 &> /dev/null; then
    echo "CHYBA: pip3 není nainstalován!"
    apt-get install python3-pip -y
fi
echo "✓ pip3 nainstalován"
echo ""

# Nainstalovat MySQL connector
echo "[3/6] Instalace MySQL connector..."
pip3 install mysql-connector-python --quiet
if [ $? -eq 0 ]; then
    echo "✓ MySQL connector nainstalován"
else
    echo "! Varování: MySQL connector se nepovedlo nainstalovat přes pip"
    echo "  Zkouším přes apt..."
    apt-get install python3-mysql.connector -y
fi
echo ""

# Stáhnout skript
echo "[4/6] Stahování importního skriptu..."
SCRIPT_URL="https://raw.githubusercontent.com/delamvec/SF2/claude/fix-mob-proto-import-hupq7/import_mob_proto_to_db.py"
SCRIPT_PATH="/root/import_mob_proto_to_db.py"

wget -q -O "$SCRIPT_PATH" "$SCRIPT_URL"

if [ $? -eq 0 ]; then
    echo "✓ Skript stažen do $SCRIPT_PATH"
    chmod +x "$SCRIPT_PATH"
else
    echo "CHYBA: Nepodařilo se stáhnout skript!"
    echo "URL: $SCRIPT_URL"
    exit 1
fi
echo ""

# Najít soubory
echo "[5/6] Hledání mob_proto.txt souborů..."
echo "Hledám v /home, /usr, /opt, /root..."
MOB_PROTO_FILES=$(find /home /usr /opt /root -name "mob_proto.txt" 2>/dev/null)

if [ -z "$MOB_PROTO_FILES" ]; then
    echo "! Soubory nenalezeny automaticky"
    echo "Zadejte cestu k adresáři s mob_proto.txt:"
    read -p "Cesta: " MOB_DIR
else
    echo "Nalezené soubory:"
    echo "$MOB_PROTO_FILES"
    echo ""
    echo "Použít první nalezený soubor? (y/n)"
    read -p "> " USE_FIRST

    if [ "$USE_FIRST" = "y" ]; then
        FIRST_FILE=$(echo "$MOB_PROTO_FILES" | head -1)
        MOB_DIR=$(dirname "$FIRST_FILE")
    else
        echo "Zadejte cestu k adresáři s mob_proto.txt:"
        read -p "Cesta: " MOB_DIR
    fi
fi

# Zkontrolovat, že soubory existují
if [ ! -f "$MOB_DIR/mob_proto.txt" ]; then
    echo "CHYBA: Soubor $MOB_DIR/mob_proto.txt neexistuje!"
    exit 1
fi

echo "✓ Použijí se soubory z: $MOB_DIR"
echo ""

# Databázové údaje
echo "[6/6] Konfigurace databáze..."
read -p "Host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Uživatel (default: root): " DB_USER
DB_USER=${DB_USER:-root}

read -sp "Heslo: " DB_PASS
echo ""

read -p "Databáze (default: srv1_common): " DB_NAME
DB_NAME=${DB_NAME:-srv1_common}

echo ""
echo "================================================"
echo " Připraveno k importu"
echo "================================================"
echo "Skript:      $SCRIPT_PATH"
echo "mob_proto:   $MOB_DIR/mob_proto.txt"
echo "mob_names:   $MOB_DIR/mob_names.txt"
echo "Host:        $DB_HOST"
echo "Uživatel:    $DB_USER"
echo "Databáze:    $DB_NAME"
echo "================================================"
echo ""

# Nabídnout zálohu
echo "Chcete zálohovat stávající tabulku mob_proto? (DOPORUČENO) (y/n)"
read -p "> " DO_BACKUP

if [ "$DO_BACKUP" = "y" ]; then
    BACKUP_FILE="/root/mob_proto_backup_$(date +%Y%m%d_%H%M%S).sql"
    echo "Zálohuji do $BACKUP_FILE..."
    mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" mob_proto > "$BACKUP_FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Záloha vytvořena"
    else
        echo "! Varování: Záloha se nezdařila (možná tabulka neexistuje)"
    fi
    echo ""
fi

# Nabídnout smazání starých dat
echo "Smazat staré záznamy před importem? (y/n)"
read -p "> " DO_TRUNCATE

if [ "$DO_TRUNCATE" = "y" ]; then
    echo "Mažu staré záznamy..."
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "TRUNCATE TABLE mob_proto;" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Staré záznamy smazány"
    else
        echo "! Varování: Mazání selhalo (možná tabulka neexistuje)"
    fi
    echo ""
fi

# Spustit import
echo "================================================"
echo " Spouštím import..."
echo "================================================"
echo ""

cd "$MOB_DIR"

python3 "$SCRIPT_PATH" \
    "$MOB_DIR/mob_proto.txt" \
    "$MOB_DIR/mob_names.txt" \
    --host "$DB_HOST" \
    --user "$DB_USER" \
    --password "$DB_PASS" \
    --database "$DB_NAME"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "================================================"
    echo " ✓ Import dokončen úspěšně!"
    echo "================================================"
    echo ""

    # Zobrazit statistiky
    echo "Statistiky:"
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        SELECT
            COUNT(*) as 'Celkem mobů',
            MIN(vnum) as 'Min VNUM',
            MAX(vnum) as 'Max VNUM',
            COUNT(DISTINCT type) as 'Různých typů'
        FROM mob_proto;
    " 2>/dev/null

    echo ""
    echo "Ukázka dat:"
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        SELECT vnum, name, level, type
        FROM mob_proto
        ORDER BY vnum
        LIMIT 5;
    " 2>/dev/null

else
    echo "================================================"
    echo " ✗ Import selhal s kódem $EXIT_CODE"
    echo "================================================"

    if [ "$DO_BACKUP" = "y" ] && [ -f "$BACKUP_FILE" ]; then
        echo ""
        echo "Pro obnovení zálohy použijte:"
        echo "  mysql -u $DB_USER -p $DB_NAME < $BACKUP_FILE"
    fi

    exit $EXIT_CODE
fi

echo ""
echo "Hotovo!"

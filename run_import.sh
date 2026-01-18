#!/bin/bash
# Importní skript pro mob_proto do databáze

echo "========================================="
echo " Import mob_proto.txt do MySQL databáze"
echo "========================================="
echo ""

# Zkontrolovat, jestli existuje import skript
SCRIPT_DIR="/home/user/SF2"
IMPORT_SCRIPT="$SCRIPT_DIR/import_mob_proto_to_db.py"

if [ ! -f "$IMPORT_SCRIPT" ]; then
    echo "CHYBA: Skript $IMPORT_SCRIPT nenalezen!"
    exit 1
fi

# Zeptat se na cestu k souborům
echo "Zadejte cestu k adresáři se soubory mob_proto.txt a mob_names.txt:"
echo "(Příklad: /home/serverfiles/main/srv1/share/conf)"
read -p "Cesta: " DATA_DIR

# Zkontrolovat, jestli soubory existují
if [ ! -f "$DATA_DIR/mob_proto.txt" ]; then
    echo "CHYBA: Soubor $DATA_DIR/mob_proto.txt nenalezen!"
    exit 1
fi

if [ ! -f "$DATA_DIR/mob_names.txt" ]; then
    echo "VAROVÁNÍ: Soubor $DATA_DIR/mob_names.txt nenalezen!"
    echo "Pokračovat bez lokalizovaných názvů? (y/n)"
    read -p "> " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
    # Vytvořit prázdný soubor
    touch /tmp/mob_names_empty.txt
    MOB_NAMES="/tmp/mob_names_empty.txt"
else
    MOB_NAMES="$DATA_DIR/mob_names.txt"
fi

# Nastavení databáze
echo ""
echo "Nastavení databáze:"
read -p "Host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Uživatel (default: root): " DB_USER
DB_USER=${DB_USER:-root}

read -sp "Heslo: " DB_PASS
echo ""

read -p "Databáze (default: srv1_common): " DB_NAME
DB_NAME=${DB_NAME:-srv1_common}

echo ""
echo "========================================="
echo "Připraveno k importu:"
echo "  mob_proto.txt: $DATA_DIR/mob_proto.txt"
echo "  mob_names.txt: $MOB_NAMES"
echo "  Host: $DB_HOST"
echo "  Uživatel: $DB_USER"
echo "  Databáze: $DB_NAME"
echo "========================================="
echo ""
read -p "Pokračovat? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Import zrušen."
    exit 0
fi

echo ""
echo "Spouštím import..."
echo ""

# Spustit import
python3 "$IMPORT_SCRIPT" \
    "$DATA_DIR/mob_proto.txt" \
    "$MOB_NAMES" \
    --host "$DB_HOST" \
    --user "$DB_USER" \
    --password "$DB_PASS" \
    --database "$DB_NAME"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "========================================="
    echo " Import dokončen úspěšně!"
    echo "========================================="
    echo ""
    echo "Zkontrolujte data v databázi:"
    echo "  mysql -u $DB_USER -p $DB_NAME -e 'SELECT COUNT(*) FROM mob_proto;'"
else
    echo "========================================="
    echo " Import selhal s chybou $EXIT_CODE"
    echo "========================================="
    exit $EXIT_CODE
fi

#!/bin/bash
# Testovací skript pro import mob_proto

echo "=== Test importu mob_proto ==="
echo ""
echo "Tento skript otestuje import s ukázkovými daty."
echo "Použijte své heslo k databázi."
echo ""

# Přejít do adresáře se skriptem
cd /home/user/SF2

# Spustit import s ukázkovými soubory
python3 import_mob_proto_to_db.py \
    mob_proto_example.txt \
    mob_names_example.txt \
    --host localhost \
    --user root \
    --password "$1" \
    --database srv1_common

echo ""
echo "=== Test dokončen ==="
echo "Zkontrolujte databázi:"
echo "mysql -u root -p srv1_common -e 'SELECT * FROM mob_proto WHERE vnum IN (101,102,107);'"

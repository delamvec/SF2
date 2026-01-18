# Rychlý start - Import mob_proto.txt

## Krok 1: Spuštění importu

```bash
cd /home/user/SF2
./run_import.sh
```

Skript se vás zeptá na:
1. **Cestu k adresáři** se soubory (např. `/home/serverfiles/main/srv1/share/conf`)
2. **Databázové údaje**:
   - Host (default: localhost)
   - Uživatel (default: root)
   - Heslo
   - Databáze (default: srv1_common)

## Krok 2: Kontrola importu

Po úspěšném importu zkontrolujte data:

```bash
mysql -u root -p srv1_common -e "SELECT COUNT(*) FROM mob_proto;"
mysql -u root -p srv1_common -e "SELECT vnum, name, locale_name, level FROM mob_proto LIMIT 10;"
```

## Manuální spuštění (bez interaktivního skriptu)

Pokud znáte všechny údaje předem:

```bash
cd /home/user/SF2

python3 import_mob_proto_to_db.py \
    /home/serverfiles/main/srv1/share/conf/mob_proto.txt \
    /home/serverfiles/main/srv1/share/conf/mob_names.txt \
    --host localhost \
    --user root \
    --password VASE_HESLO \
    --database srv1_common
```

## Řešení problémů

### Chyba: "No such file or directory"
- Zkontrolujte, že soubory existují: `ls -l /cesta/k/mob_proto.txt`
- Zkontrolujte oprávnění: `chmod 644 /cesta/k/mob_proto.txt`

### Chyba: "Access denied for user"
- Zkontrolujte heslo k databázi
- Zkontrolujte, že uživatel má oprávnění k databázi

### Chyba: "mysql-connector-python not found"
```bash
pip3 install mysql-connector-python
```

### Chyba: "Incorrect integer value"
- Tato chyba by se již neměla objevit - skript správně převádí hodnoty
- Pokud ano, zkontrolujte formát souboru mob_proto.txt

## Co skript dělá

1. Načte mob_names.txt pro lokalizované názvy
2. Přečte mob_proto.txt (přeskočí hlavičku "VNUM...")
3. Převede textové hodnoty na formát databáze:
   - RANK (PAWN→0, BOSS→4, atd.)
   - TYPE (MONSTER→0, NPC→1, atd.)
   - SIZE (SMALL/MEDIUM/BIG)
   - FLAGS (AGGR, ANIMAL, STUN, atd.)
4. Vloží data do MySQL

## Poznámky

- Skript automaticky přeskakuje hlavičky (řádky začínající na "VNUM")
- Používá TAB jako oddělovač sloupců
- Podporuje UTF-8 i CP1252 kódování
- Zobrazuje progress každých 100 mobů

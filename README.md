# SF2 - Metin2 mob_proto nástroje

Nástroje pro import a opravu mob_proto databáze pro Metin2 server.

## Obsah

- `mob_proto.sql` - SQL soubor s kompletní tabulkou mob_proto ve správném formátu
- `import_mob_proto_to_db.py` - **NOVÝ** Python skript pro import mob_proto.txt a mob_names.txt přímo do databáze
- `install_on_server.sh` - **NOVÝ** Automatický instalační a importní skript pro server
- `convert_mob_proto.py` - Python skript pro opravu SQL souborů s textovými hodnotami typu
- `IMPORT_GUIDE.md` - Detailní průvodce importem
- `MOB_PROTO_IMPORT.md` - Průvodce pro import z mob_proto.txt souborů
- `SERVER_INSTALL.md` - Průvodce pro instalaci a spuštění přímo na serveru
- `QUICK_START.md` - Rychlý start pro lokální použití

## Rychlý start

### Spuštění přímo na serveru (NEJJEDNODUŠŠÍ)

Pokud chcete spustit import **přímo na vašem serveru**:

```bash
# Na serveru - automatická instalace a import
wget https://raw.githubusercontent.com/delamvec/SF2/claude/fix-mob-proto-import-hupq7/install_on_server.sh
bash install_on_server.sh
```

Nebo manuálně:

```bash
# 1. Stáhnout skript
wget https://raw.githubusercontent.com/delamvec/SF2/claude/fix-mob-proto-import-hupq7/import_mob_proto_to_db.py

# 2. Nainstalovat prerekvizity
pip3 install mysql-connector-python

# 3. Spustit import (upravte cesty)
python3 import_mob_proto_to_db.py \
    /home/serverfiles/main/srv1/share/conf/mob_proto.txt \
    /home/serverfiles/main/srv1/share/conf/mob_names.txt \
    --host localhost \
    --user root \
    --password VASE_HESLO \
    --database srv1_common
```

**Viz [SERVER_INSTALL.md](SERVER_INSTALL.md) pro detailní instrukce**

### Import z mob_proto.txt (lokálně)

Pokud máte **mob_proto.txt** a **mob_names.txt** soubory:

```bash
# Nainstalovat MySQL connector
pip3 install mysql-connector-python

# Importovat data
python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt --password HESLO
```

Tento skript:
- Načte mob_proto.txt ve formátu, který používá server
- Správně převede textové hodnoty (NPC, PAWN, SMALL, atd.) na formát databáze
- Použije mob_names.txt pro lokalizované názvy
- Vloží data přímo do MySQL

**Viz [MOB_PROTO_IMPORT.md](MOB_PROTO_IMPORT.md) pro detaily**

### Pokud máte správný SQL soubor

```bash
mysql -u root -p srv1_common < mob_proto.sql
```

### Pokud dostáváte chybu "Incorrect integer value: 'NPC'"

To znamená, že se pokušíte importovat data v textovém formátu.

**Řešení 1: Použít import z mob_proto.txt (DOPORUČENO)**
```bash
python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt --password HESLO
```

**Řešení 2: Opravit SQL soubor**
```bash
# 1. Opravit soubor
python3 convert_mob_proto.py vas_soubor.sql opraveny_soubor.sql

# 2. Importovat opravený soubor
mysql -u root -p srv1_common < opraveny_soubor.sql
```

## Popis chyby

Chyba vzniká, když se pokusíte vložit textovou hodnotu (např. 'NPC') do pole `type`, které očekává číslo:

```
Error: (1366, "Incorrect integer value: 'NPC' for column `srv1_common`.`mob_proto`.`type` at row 1")
```

**Správný formát:**
```sql
INSERT INTO `mob_proto` VALUES (101, ..., 0, ...);  -- type = 0 (číslo)
```

**Chybný formát:**
```sql
INSERT INTO `mob_proto` VALUES (101, ..., 'NPC', ...);  -- type = 'NPC' (text)
```

## Mapování typů

Skript `convert_mob_proto.py` převádí:

| Textová hodnota | Číselná hodnota |
|----------------|-----------------|
| NPC            | 0               |
| MONSTER        | 0               |
| BOSS           | 1               |
| STONE          | 2               |
| WARP           | 3               |
| DOOR           | 4               |
| BUILDING       | 5               |
| PC             | 6               |
| POLY           | 7               |
| HORSE          | 8               |
| GOTO           | 9               |

## Podpora

Pro detailnější informace viz [IMPORT_GUIDE.md](IMPORT_GUIDE.md).

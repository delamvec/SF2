# SF2 - Metin2 mob_proto nástroje

Nástroje pro import a opravu mob_proto databáze pro Metin2 server.

## Obsah

- `mob_proto.sql` - SQL soubor s kompletní tabulkou mob_proto ve správném formátu
- `convert_mob_proto.py` - Python skript pro opravu SQL souborů s textovými hodnotami typu
- `IMPORT_GUIDE.md` - Detailní průvodce importem

## Rychlý start

### Pokud máte správný SQL soubor

```bash
mysql -u root -p srv1_common < mob_proto.sql
```

### Pokud dostáváte chybu "Incorrect integer value: 'NPC'"

To znamená, že váš SQL soubor obsahuje textové hodnoty typu místo číselných. Opravte to:

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

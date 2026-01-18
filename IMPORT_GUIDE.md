# Průvodce importem mob_proto do databáze

## Problém
Pokud dostáváte chybu:
```
Incorrect integer value: 'NPC' for column `srv1_common`.`mob_proto`.`type`
```

To znamená, že pole `type` očekává číslo, ne text.

## Řešení 1: Přímý import SQL souboru

Použijte soubor `mob_proto.sql`, který je již ve správném formátu:

```bash
mysql -u root -p srv1_common < mob_proto.sql
```

Nebo z MySQL konzole:
```sql
USE srv1_common;
source /cesta/k/mob_proto.sql;
```

## Řešení 2: Převod typu z textu na číslo

Pokud máte mob_proto SQL soubor s textovými hodnotami 'NPC', použijte konverzní skript:

```bash
# Opravit soubor s textovými hodnotami
python3 convert_mob_proto.py vstupni_soubor.sql opraveny_soubor.sql

# Importovat opravený soubor
mysql -u root -p srv1_common < opraveny_soubor.sql
```

### Mapování typů:
- 'MONSTER' nebo 'NPC' → 0
- 'BOSS' → 1
- 'STONE' → 2
- 'WARP' → 3
- 'DOOR' → 4
- 'BUILDING' → 5
- jiné hodnoty → 0

### Příklad použití:
```bash
# Pokud máte soubor s chybami
python3 convert_mob_proto.py mob_proto_old.sql mob_proto_fixed.sql

# Pak importujte opravený soubor
mysql -u root -p srv1_common < mob_proto_fixed.sql
```

## Struktura tabulky

Pole `type` musí být číslo:
- `type` tinyint UNSIGNED NOT NULL DEFAULT 0

Správný INSERT vypadá takto:
```sql
INSERT INTO `mob_proto` VALUES (101, 0xB5E9B0B3, 0x57696C6420446F67, 0, 0, 0, 1, ...);
                                                                            ^
                                                                      type = 0 (číslo)
```

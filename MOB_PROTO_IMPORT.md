# Import mob_proto.txt do databáze

Tento průvodce vysvětluje, jak importovat mob_proto.txt a mob_names.txt soubory do MySQL databáze.

## Prerekvizity

1. Python 3.x
2. MySQL connector pro Python:
```bash
pip3 install mysql-connector-python
```

## Formát souborů

### mob_proto.txt

Textový soubor oddělený TABulátory s následujícími sloupci (podle server source):

1. vnum - ID mobu
2. name - Interní název
3. rank - PAWN, S_PAWN, KNIGHT, S_KNIGHT, BOSS, KING
4. type - MONSTER, NPC, STONE, WARP, DOOR, BUILDING, PC, POLYMORPH_PC, HORSE, GOTO
5. battle_type - MELEE, RANGE, MAGIC, SPECIAL, POWER, TANKER, SUPER_POWER, SUPER_TANKER
6. level - Úroveň
7. size - SMALL, MEDIUM, BIG
8. ai_flag - Seznam oddělený čárkami: AGGR, NOMOVE, COWARD, atd.
9. mount_capacity - Kapacita pro mount (přeskočeno)
10. race_flag - Seznam oddělený čárkami: ANIMAL, UNDEAD, DEVIL, HUMAN, atd.
11. immune_flag - Seznam oddělený čárkami: STUN, SLOW, FALL, CURSE, POISON, TERROR, REFLECT
12. empire - Říše (0-3)
13. folder - Cesta ke složce s grafikou
14. on_click - Typ akce při kliknutí
15-18. st, dx, ht, iq - Statistiky
19-20. damage_min, damage_max - Rozsah poškození
21. max_hp - Maximální zdraví
22-23. regen_cycle, regen_percent - Regenerace
24-25. gold_min, gold_max - Rozsah zlata
26. exp - Zkušenosti
27. def - Obrana
28-29. attack_speed, move_speed - Rychlosti
30-31. aggressive_hp_pct, aggressive_sight - Agresivita
32. attack_range - Dosah útoku
33. drop_item - VNUM předmětu
34. resurrection_vnum - VNUM pro vzkříšení
35-40. enchant_curse až enchant_penetrate - Enchantmenty (6)
41-51. resist_sword až resist_poison - Odpory (11)
52. dam_multiply - Násobič poškození
53. summon - VNUM pro přivolání
54. drain_sp - Vysávání SP
55. mob_color - Barva (přeskočeno)
56. polymorph_item - VNUM pro polymorph
57-66. skill_level0-4, skill_vnum0-4 - Dovednosti (5 párů)
67-71. sp_berserk až sp_revive - SP body (5)

### mob_names.txt

Formát:
```
vnum<TAB>Lokalizovaný název
```

Příklad:
```
101	Divoký pes
102	Vlk
103	Alfa vlk
```

## Použití

### Základní použití

```bash
python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt --password HESLO
```

### S vlastním databázovým nastavením

```bash
python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt \
    --host localhost \
    --user root \
    --password heslo \
    --database srv1_common
```

### Pokud nemáte mob_names.txt

Skript použije interní názvy z mob_proto.txt:

```bash
python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt --password HESLO
# (mob_names.txt může být prázdný nebo neexistující soubor)
```

## Co skript dělá

1. **Načte mob_names.txt** - Vytvoří mapování vnum → lokalizovaný název
2. **Parsuje mob_proto.txt** - Čte řádek po řádce
3. **Převádí hodnoty**:
   - `rank`, `type`, `battle_type` → čísla (0, 1, 2, ...)
   - `size` → ENUM ('SMALL', 'MEDIUM', 'BIG')
   - `ai_flag` → SET ('AGGR,NOMOVE,COWARD', ...)
   - `race_flag` → SET ('ANIMAL,UNDEAD', ...)
   - `immune_flag` → SET ('STUN,SLOW', ...)
   - `name`, `locale_name` → varbinary (hexadecimální)
4. **Vkládá do databáze** - INSERT INTO mob_proto

## Mapování hodnot

### Rank
- PAWN → 0
- S_PAWN → 1
- KNIGHT → 2
- S_KNIGHT → 3
- BOSS → 4
- KING → 5

### Type
- MONSTER → 0
- NPC → 1
- STONE → 2
- WARP → 3
- DOOR → 4
- BUILDING → 5
- PC → 6
- POLYMORPH_PC → 7
- HORSE → 8
- GOTO → 9

### Battle Type
- MELEE → 0
- RANGE → 1
- MAGIC → 2
- SPECIAL → 3
- POWER → 4
- TANKER → 5
- SUPER_POWER → 6
- SUPER_TANKER → 7

### AI Flags (SET)
- AGGR, NOMOVE, COWARD, NOATTSHINSU, NOATTCHUNJO, NOATTJINNO
- ATTMOB, BERSERK, STONESKIN, GODSPEED, DEATHBLOW, REVIVE

### Race Flags (SET)
- ANIMAL, UNDEAD, DEVIL, HUMAN, ORC, MILGYO, INSECT
- FIRE, ICE, DESERT, TREE
- ATT_ELEC, ATT_FIRE, ATT_ICE, ATT_WIND, ATT_EARTH, ATT_DARK
- ZODIAC

### Immune Flags (SET)
- STUN, SLOW, FALL, CURSE, POISON, TERROR, REFLECT

## Řešení problémů

### Chyba: "Incorrect integer value: 'NPC'"

Tato chyba nastává, když se pokusíte importovat SQL soubor s textovými hodnotami místo čísel.

**Řešení**: Použijte tento skript `import_mob_proto_to_db.py`, který správně převádí textové hodnoty.

### Chyba: "Too many values"

Zkontrolujte, že mob_proto.txt má správný počet sloupců (minimálně 60).

### Encoding chyby

Skript podporuje různá kódování (UTF-8, CP1252). Pokud máte problémy:
- Zkuste převést soubor na UTF-8
- Nebo upravte encoding v kódu na řádku s `open()`

## Výstup

Skript zobrazuje:
```
Loading mob names from mob_names.txt...
Loaded 150 mob names
Reading mob_proto.txt...
Progress: 100 mobs inserted...
Progress: 200 mobs inserted...
...

Import complete!
Successfully inserted: 2864
Errors: 0
```

## Poznámky

- Skript přeskakuje prázdné řádky a komentáře (začínající #)
- Pokud se vyskytne více než 10 chyb, import se zastaví
- Každých 100 mobů se zobrazí progress
- Pokud mob není v mob_names.txt, použije se interní název

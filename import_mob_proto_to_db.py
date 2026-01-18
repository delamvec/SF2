#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import mob_proto.txt a mob_names.txt do MySQL databáze
Převádí textový formát na SQL INSERT příkazy
"""

import sys
import os
import re
import mysql.connector
from mysql.connector import Error

# Mapování podle server source kódu (ProtoReader.cpp)
RANK_MAP = {
    'PAWN': 0,
    'S_PAWN': 1,
    'KNIGHT': 2,
    'S_KNIGHT': 3,
    'BOSS': 4,
    'KING': 5
}

TYPE_MAP = {
    'MONSTER': 0,
    'NPC': 1,
    'STONE': 2,
    'WARP': 3,
    'DOOR': 4,
    'BUILDING': 5,
    'PC': 6,
    'POLYMORPH_PC': 7,
    'HORSE': 8,
    'GOTO': 9
}

BATTLE_TYPE_MAP = {
    'MELEE': 0,
    'RANGE': 1,
    'MAGIC': 2,
    'SPECIAL': 3,
    'POWER': 4,
    'TANKER': 5,
    'SUPER_POWER': 6,
    'SUPER_TANKER': 7
}

SIZE_VALUES = ['SMALL', 'MEDIUM', 'BIG']

AI_FLAG_MAP = {
    'AGGR': 0,
    'NOMOVE': 1,
    'COWARD': 2,
    'NOATTSHINSU': 3,
    'NOATTCHUNJO': 4,
    'NOATTJINNO': 5,
    'ATTMOB': 6,
    'BERSERK': 7,
    'STONESKIN': 8,
    'GODSPEED': 9,
    'DEATHBLOW': 10,
    'REVIVE': 11
}

RACE_FLAG_MAP = {
    'ANIMAL': 0,
    'UNDEAD': 1,
    'DEVIL': 2,
    'HUMAN': 3,
    'ORC': 4,
    'MILGYO': 5,
    'INSECT': 6,
    'FIRE': 7,
    'ICE': 8,
    'DESERT': 9,
    'TREE': 10,
    'ATT_ELEC': 11,
    'ATT_FIRE': 12,
    'ATT_ICE': 13,
    'ATT_WIND': 14,
    'ATT_EARTH': 15,
    'ATT_DARK': 16,
    'ZODIAC': 17
}

IMMUNE_FLAG_MAP = {
    'STUN': 0,
    'SLOW': 1,
    'FALL': 2,
    'CURSE': 3,
    'POISON': 4,
    'TERROR': 5,
    'REFLECT': 6
}


def parse_flags_to_set(flag_string, flag_map, separator=','):
    """Převede řetězec flags na SET formát pro MySQL (oddělené čárkami)"""
    if not flag_string or flag_string.strip() == '':
        return ''

    flags = [f.strip().upper() for f in flag_string.split(separator)]
    valid_flags = []

    for flag in flags:
        if flag in flag_map:
            valid_flags.append(flag)

    return ','.join(valid_flags)


def parse_size(size_string):
    """Převede size string na ENUM hodnotu"""
    size_clean = size_string.strip().upper()
    if size_clean in SIZE_VALUES:
        return size_clean
    return 'SMALL'  # Default


def load_mob_names(filename):
    """Načte mob_names.txt a vrátí slovník {vnum: locale_name_bytes}"""
    names = {}

    if not os.path.exists(filename):
        print(f"Warning: {filename} not found, using internal names")
        return names

    try:
        # Zkusit různá kódování pro české znaky
        for encoding in ['cp1250', 'utf-8', 'iso-8859-2']:
            try:
                with open(filename, 'r', encoding=encoding, errors='strict') as f:
                    for line in f:
                        line = line.strip()
                        # Přeskočit prázdné řádky, komentáře a hlavičku
                        if not line or line.startswith('#') or line.startswith('VNUM'):
                            continue

                        # Formát: vnum\tname
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            try:
                                vnum = int(parts[0].strip())
                                name = parts[1].strip()
                                # Uložit jako bytes v UTF-8 pro databázi
                                names[vnum] = name.encode('utf-8')
                            except ValueError:
                                continue
                    print(f"mob_names.txt read with {encoding} encoding")
                    break
            except (UnicodeDecodeError, LookupError):
                continue
    except Exception as e:
        print(f"Error reading {filename}: {e}")

    return names


def parse_mob_proto_line(line_bytes, mob_names):
    """Parsuje jednu řádku z mob_proto.txt a vrátí SQL hodnoty

    Args:
        line_bytes: Surové byty řádku
        mob_names: Slovník {vnum: locale_name_bytes}
    """
    # Helper pro dekódování textových polí
    def decode_field(b):
        return b.strip().decode('ascii', errors='ignore')

    # Rozdělit podle TABu - pracovat s byty
    parts = line_bytes.split(b'\t')

    if len(parts) < 60:
        return None

    col = 0

    # Vnum
    try:
        vnum = int(decode_field(parts[col]))
    except (ValueError, UnicodeDecodeError):
        return None
    col += 1

    # Name - zachovat jako surové byty (korejské znaky v cp949/euc-kr)
    name_bytes = parts[col].strip()
    col += 1

    # Locale name (z mob_names.txt nebo použít name)
    locale_name_bytes = mob_names.get(vnum, name_bytes)

    # Rank
    rank = RANK_MAP.get(decode_field(parts[col]).upper(), 0)
    col += 1

    # Type
    mob_type = TYPE_MAP.get(decode_field(parts[col]).upper(), 0)
    col += 1

    # Battle Type
    battle_type = BATTLE_TYPE_MAP.get(decode_field(parts[col]).upper(), 0)
    col += 1

    # Level
    level = int(decode_field(parts[col]) or '1')
    col += 1

    # Size (ENUM)
    size = parse_size(decode_field(parts[col]))
    col += 1

    # AI Flag (SET)
    ai_flag = parse_flags_to_set(decode_field(parts[col]), AI_FLAG_MAP, ',')
    col += 1

    # Mount capacity (skip)
    col += 1

    # Race Flag (SET)
    race_flag = parse_flags_to_set(decode_field(parts[col]), RACE_FLAG_MAP, ',')
    col += 1

    # Immune Flag (SET)
    immune_flag = parse_flags_to_set(decode_field(parts[col]), IMMUNE_FLAG_MAP, ',')
    col += 1

    # Empire
    empire = int(decode_field(parts[col]) or '0')
    col += 1

    # Folder
    folder = decode_field(parts[col])
    col += 1

    # OnClick
    on_click = int(decode_field(parts[col]) or '0')
    col += 1

    # Stats: ST, DX, HT, IQ
    st = int(decode_field(parts[col]) or '0')
    col += 1
    dx = int(decode_field(parts[col]) or '0')
    col += 1
    ht = int(decode_field(parts[col]) or '0')
    col += 1
    iq = int(decode_field(parts[col]) or '0')
    col += 1

    # Damage
    damage_min = int(decode_field(parts[col]) or '0')
    col += 1
    damage_max = int(decode_field(parts[col]) or '0')
    col += 1

    # Max HP
    max_hp = int(decode_field(parts[col]) or '0')
    col += 1

    # Regen
    regen_cycle = int(decode_field(parts[col]) or '0')
    col += 1
    regen_percent = int(decode_field(parts[col]) or '0')
    col += 1

    # Gold
    gold_min = int(decode_field(parts[col]) or '0')
    col += 1
    gold_max = int(decode_field(parts[col]) or '0')
    col += 1

    # Exp
    exp = int(decode_field(parts[col]) or '0')
    col += 1

    # Def
    def_val = int(decode_field(parts[col]) or '0')
    col += 1

    # Attack Speed
    attack_speed = int(decode_field(parts[col]) or '100')
    col += 1

    # Move Speed
    move_speed = int(decode_field(parts[col]) or '100')
    col += 1

    # Aggressive
    aggressive_hp_pct = int(decode_field(parts[col]) or '0')
    col += 1
    aggressive_sight = int(decode_field(parts[col]) or '0')
    col += 1

    # Attack Range
    attack_range = int(decode_field(parts[col]) or '0')
    col += 1

    # Drop Item
    drop_item = int(decode_field(parts[col]) or '0')
    col += 1

    # Resurrection Vnum
    resurrection_vnum = int(decode_field(parts[col]) or '0')
    col += 1

    # Enchants (6)
    enchants = []
    for i in range(6):
        enchants.append(int(decode_field(parts[col]) or '0'))
        col += 1

    # Resists (11)
    resists = []
    for i in range(11):
        resists.append(int(decode_field(parts[col]) or '0'))
        col += 1

    # Dam Multiply
    dam_multiply = float(decode_field(parts[col]) or '1.0') if parts[col].strip() else None
    col += 1

    # Summon
    summon = int(decode_field(parts[col]) or '0') if parts[col].strip() else None
    col += 1

    # Drain SP
    drain_sp = int(decode_field(parts[col]) or '0') if parts[col].strip() else None
    col += 1

    # Mob Color (skip)
    col += 1

    # Polymorph Item
    polymorph_item = int(decode_field(parts[col]) or '0')
    col += 1

    # Skills (5 pairs of level + vnum = 10 fields)
    skills = []
    for i in range(5):
        skill_level = int(decode_field(parts[col]) or '0') if col < len(parts) and parts[col].strip() else None
        col += 1
        skill_vnum = int(decode_field(parts[col]) or '0') if col < len(parts) and parts[col].strip() else None
        col += 1
        skills.append((skill_level, skill_vnum))

    # SP Points (5)
    sp_berserk = int(decode_field(parts[col]) or '0') if col < len(parts) else 0
    col += 1
    sp_stoneskin = int(decode_field(parts[col]) or '0') if col < len(parts) else 0
    col += 1
    sp_godspeed = int(decode_field(parts[col]) or '0') if col < len(parts) else 0
    col += 1
    sp_deathblow = int(decode_field(parts[col]) or '0') if col < len(parts) else 0
    col += 1
    sp_revive = int(decode_field(parts[col]) or '0') if col < len(parts) else 0

    # Sestavit SQL INSERT - použít surové byty pro name a locale_name
    sql_values = [
        vnum,
        f"0x{name_bytes.hex().upper()}",  # name jako hex (zachované originální byty)
        f"0x{locale_name_bytes.hex().upper()}",  # locale_name jako hex (UTF-8 bytes)
        rank,
        mob_type,
        battle_type,
        level,
        size,  # size enum - textová hodnota
        ai_flag,  # ai_flag set - textové hodnoty oddělené čárkami
        0,  # mount_capacity
        race_flag,  # setRaceFlag - textové hodnoty oddělené čárkami
        immune_flag,  # setImmuneFlag - textové hodnoty oddělené čárkami
        empire,
        folder,
        on_click,
        st, dx, ht, iq,
        damage_min, damage_max,
        max_hp,
        regen_cycle, regen_percent,
        gold_min, gold_max,
        exp,
        def_val,
        attack_speed, move_speed,
        aggressive_hp_pct, aggressive_sight,
        attack_range,
        drop_item,
        resurrection_vnum,
    ]

    # Enchants
    sql_values.extend(enchants)

    # Resists
    sql_values.extend(resists)

    # Floats/NULL
    sql_values.append('NULL' if dam_multiply is None else dam_multiply)
    sql_values.append('NULL' if summon is None else summon)
    sql_values.append('NULL' if drain_sp is None else drain_sp)
    sql_values.append('NULL')  # mob_color
    sql_values.append(polymorph_item)

    # Skills
    for skill_level, skill_vnum in skills:
        sql_values.append('NULL' if skill_level is None else skill_level)
        sql_values.append('NULL' if skill_vnum is None else skill_vnum)

    # SP Points
    sql_values.extend([sp_berserk, sp_stoneskin, sp_godspeed, sp_deathblow, sp_revive])

    return sql_values


def import_mob_proto(mob_proto_file, mob_names_file, db_config):
    """Import mob_proto.txt do MySQL databáze"""

    print(f"Loading mob names from {mob_names_file}...")
    mob_names = load_mob_names(mob_names_file)
    print(f"Loaded {len(mob_names)} mob names")

    print(f"Reading {mob_proto_file}...")

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Načíst mob_proto.txt jako BINÁRNÍ soubor (zachovat originální byty)
        with open(mob_proto_file, 'rb') as f:
            lines = f.readlines()
        print(f"Reading mob_proto.txt as binary (preserving original bytes)")

        inserted = 0
        errors = 0

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Přeskočit prázdné řádky, komentáře a hlavičku (pracujeme s byty)
            if not line or line.startswith(b'#') or line.startswith(b'VNUM'):
                continue

            try:
                sql_values = parse_mob_proto_line(line, mob_names)

                if sql_values is None:
                    print(f"Warning: Skipping line {line_num} (insufficient columns)")
                    continue

                # Vytvořit INSERT - použít UNHEX() pro binární pole
                placeholders = []
                final_values = []

                for idx, val in enumerate(sql_values):
                    # Pro pole name (index 1) a locale_name (index 2) použít UNHEX()
                    if idx in [1, 2] and isinstance(val, str) and val.startswith('0x'):
                        placeholders.append(f"UNHEX('{val[2:]}')")
                    elif val == 'NULL':
                        placeholders.append('NULL')
                    elif isinstance(val, str) and not val.startswith('0x'):
                        placeholders.append('%s')
                        final_values.append(val)
                    else:
                        placeholders.append('%s')
                        final_values.append(val)

                sql = f"INSERT INTO `mob_proto` VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, final_values)
                inserted += 1

                if inserted % 100 == 0:
                    print(f"Progress: {inserted} mobs inserted...")

            except Exception as e:
                errors += 1
                print(f"Error on line {line_num}: {e}")
                if errors > 10:
                    print("Too many errors, stopping...")
                    break

        connection.commit()
        cursor.close()
        connection.close()

        print(f"\nImport complete!")
        print(f"Successfully inserted: {inserted}")
        print(f"Errors: {errors}")

    except Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <mob_proto.txt> <mob_names.txt> [options]")
        print()
        print("Options:")
        print("  --host HOST        Database host (default: localhost)")
        print("  --user USER        Database user (default: root)")
        print("  --password PASS    Database password")
        print("  --database DB      Database name (default: srv1_common)")
        print()
        print("Example:")
        print(f"  python3 {sys.argv[0]} mob_proto.txt mob_names.txt --password mypass")
        sys.exit(1)

    mob_proto_file = sys.argv[1]
    mob_names_file = sys.argv[2]

    # Parse options
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'srv1_common'
    }

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--host' and i + 1 < len(sys.argv):
            db_config['host'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--user' and i + 1 < len(sys.argv):
            db_config['user'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--password' and i + 1 < len(sys.argv):
            db_config['password'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--database' and i + 1 < len(sys.argv):
            db_config['database'] = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not os.path.exists(mob_proto_file):
        print(f"Error: {mob_proto_file} not found!")
        sys.exit(1)

    import_mob_proto(mob_proto_file, mob_names_file, db_config)


if __name__ == '__main__':
    main()

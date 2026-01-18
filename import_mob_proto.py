#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import mob_proto.txt and mob_names.txt to MySQL database
"""

import sys
import pymysql as MySQLdb

# Database configuration
DB_HOST = "127.0.0.1"
DB_USER = "mt2"
DB_PASS = "TyPicoToJeExtrem"
DB_NAME = "srv1_common"

# File paths
MOB_PROTO_FILE = "/home/serverfiles/main/srv1/share/conf/mob_proto.txt"
MOB_NAMES_FILE = "/home/serverfiles/main/srv1/share/conf/mob_names.txt"

# Column mapping from TXT to DB (in order as they appear in TXT)
COLUMNS = [
    'vnum', 'name', 'rank', 'type', 'battle_type', 'level', 'size',
    'ai_flag', 'mount_capacity', 'setRaceFlag', 'setImmuneFlag', 'empire',
    'folder', 'on_click', 'st', 'dx', 'ht', 'iq', 'damage_min', 'damage_max',
    'max_hp', 'regen_cycle', 'regen_percent', 'gold_min', 'gold_max', 'exp',
    'def', 'attack_speed', 'move_speed', 'aggressive_hp_pct', 'aggressive_sight',
    'attack_range', 'drop_item', 'resurrection_vnum', 'enchant_curse',
    'enchant_slow', 'enchant_poison', 'enchant_stun', 'enchant_critical',
    'enchant_penetrate', 'resist_sword', 'resist_twohand', 'resist_dagger',
    'resist_bell', 'resist_fan', 'resist_bow', 'resist_fire', 'resist_elect',
    'resist_magic', 'resist_wind', 'resist_poison', 'dam_multiply', 'summon',
    'drain_sp', 'mob_color', 'polymorph_item', 'skill_level0', 'skill_vnum0',
    'skill_level1', 'skill_vnum1', 'skill_level2', 'skill_vnum2', 'skill_level3',
    'skill_vnum3', 'skill_level4', 'skill_vnum4', 'sp_berserk', 'sp_stoneskin',
    'sp_godspeed', 'sp_deathblow', 'sp_revive'
]

def load_locale_names(filename):
    """Load mob locale names from mob_names.txt"""
    locale_map = {}
    try:
        with open(filename, 'r', encoding='latin1') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if i == 0:  # Skip header
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    vnum = parts[0].strip()
                    locale_name = parts[1].strip()
                    locale_map[vnum] = locale_name
    except Exception as e:
        print(f"Error loading locale names: {e}")
        return {}
    return locale_map

def parse_value(value, column):
    """Parse and convert value based on column type"""
    value = value.strip()

    # Handle empty values
    if not value or value == '0' and column in ['ai_flag', 'setRaceFlag', 'setImmuneFlag']:
        if column in ['dam_multiply', 'summon', 'drain_sp', 'mob_color',
                      'skill_level0', 'skill_vnum0', 'skill_level1', 'skill_vnum1',
                      'skill_level2', 'skill_vnum2', 'skill_level3', 'skill_vnum3',
                      'skill_level4', 'skill_vnum4']:
            return None
        elif column in ['ai_flag', 'setRaceFlag', 'setImmuneFlag']:
            return ''
        else:
            return '0'

    # Handle float
    if column == 'dam_multiply':
        try:
            return str(float(value))
        except:
            return None

    return value

def import_mob_proto():
    """Import mob_proto.txt to MySQL"""
    print("Loading locale names...")
    locale_map = load_locale_names(MOB_NAMES_FILE)
    print(f"Loaded {len(locale_map)} locale names")

    print("Connecting to MySQL...")
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='latin1')
        cursor = db.cursor()
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        return False

    print("Truncating mob_proto table...")
    cursor.execute("TRUNCATE TABLE mob_proto")

    print("Reading mob_proto.txt...")
    inserted = 0
    errors = 0

    try:
        with open(MOB_PROTO_FILE, 'r', encoding='latin1') as f:
            lines = f.readlines()

            for line_num, line in enumerate(lines):
                if line_num == 0:  # Skip header
                    continue

                parts = line.strip().split('\t')
                if len(parts) < len(COLUMNS):
                    print(f"Warning: Line {line_num+1} has only {len(parts)} columns, skipping")
                    errors += 1
                    continue

                # Get vnum for locale_name lookup
                vnum = parts[0].strip()
                locale_name = locale_map.get(vnum, 'Noname')

                # Build values dict
                values = {}
                for i, col in enumerate(COLUMNS):
                    if i < len(parts):
                        values[col] = parse_value(parts[i], col)

                # Add locale_name
                values['locale_name'] = locale_name

                # Build INSERT query with correct column order matching server's SQL SELECT
                # Server expects: vnum, name, locale_name, type, rank, battle_type, level, size, ...
                cols = [
                    'vnum', 'name', 'locale_name', 'type', 'rank', 'battle_type', 'level', 'size',
                    'ai_flag', 'setRaceFlag', 'setImmuneFlag', 'on_click', 'empire', 'drop_item',
                    'resurrection_vnum', 'folder', 'st', 'dx', 'ht', 'iq', 'damage_min', 'damage_max', 'max_hp',
                    'regen_cycle', 'regen_percent', 'gold_min', 'gold_max', 'exp', 'def',
                    'attack_speed', 'move_speed', 'aggressive_hp_pct', 'aggressive_sight', 'attack_range',
                    'polymorph_item', 'enchant_curse', 'enchant_slow', 'enchant_poison',
                    'enchant_stun', 'enchant_critical', 'enchant_penetrate', 'resist_sword',
                    'resist_twohand', 'resist_dagger', 'resist_bell', 'resist_fan', 'resist_bow',
                    'resist_fire', 'resist_elect', 'resist_magic', 'resist_wind',
                    'resist_poison', 'dam_multiply', 'summon', 'drain_sp',
                    'mob_color',
                    'skill_vnum0', 'skill_level0', 'skill_vnum1', 'skill_level1',
                    'skill_vnum2', 'skill_level2', 'skill_vnum3', 'skill_level3',
                    'skill_vnum4', 'skill_level4', 'sp_berserk', 'sp_stoneskin',
                    'sp_godspeed', 'sp_deathblow', 'sp_revive'
                ]
                placeholders = ', '.join(['%s'] * len(cols))
                col_names = ', '.join(cols)

                sql = f"INSERT INTO mob_proto ({col_names}) VALUES ({placeholders})"

                # Build values tuple
                val_tuple = tuple(values.get(c) for c in cols)

                try:
                    cursor.execute(sql, val_tuple)
                    inserted += 1
                    if inserted % 100 == 0:
                        print(f"Inserted {inserted} mobs...")
                except Exception as e:
                    print(f"Error inserting vnum {vnum} (line {line_num+1}): {e}")
                    errors += 1

        db.commit()
        print(f"\nImport complete!")
        print(f"Successfully inserted: {inserted}")
        print(f"Errors: {errors}")

        cursor.close()
        db.close()
        return True

    except Exception as e:
        print(f"Error reading file: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Metin2 mob_proto.txt to MySQL Importer")
    print("=" * 60)
    import_mob_proto()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ItemList Generator for Metin2
==============================

This script generates itemlist.txt from NEWVNUM.csv based on item types.

Usage:
  python generate_itemlist.py

Requirements:
  - NEWVNUM.csv (new item vnums with type and subtype)

Output:
  - itemlist.txt (formatted itemlist for client)

Item Types:
  - WEAPON (type 0-5): Includes .gr2 model path
  - ARMOR (type 2+): Icon only
  - ETC: Everything else
"""

import csv
from pathlib import Path


# Item type mapping (based on Metin2 item_proto type field)
WEAPON_TYPES = [0, 1, 2, 3, 4, 5]  # sword, dagger, bow, bell, fan, two-hand
ARMOR_TYPES = [2]  # Will check differently - armor is complex


def determine_item_category(type_val, subtype_val):
    """Determine if item is WEAPON, ARMOR, or ETC"""
    try:
        type_num = int(type_val)
    except:
        return 'ETC'

    # Based on Metin2 item types:
    # Type 0 = Sword (one-handed) - WEAPON
    # Type 1 = Dagger - WEAPON
    # Type 2 = Bow - WEAPON
    # Type 3 = Bell - WEAPON
    # Type 4 = Fan - WEAPON
    # Type 5 = Two-handed sword - WEAPON
    # But in this CSV, type=1 means all weapons, type=2 means armor

    # Weapons: type 0-5 OR type 1 (in this specific CSV)
    if type_num in [0, 1, 2, 3, 4, 5]:
        return 'WEAPON'

    # Armor: type 2 (body armor)
    # In some versions, armor types are different
    # Let's check both old and new formats
    if type_num in [2]:
        return 'ARMOR'

    # Everything else is ETC
    return 'ETC'


def load_items_from_csv(filename):
    """Load items from CSV and return list of items with vnum, type, subtype"""
    items = []

    print(f"Loading {filename}...")
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue

            try:
                vnum = row[0].strip()
                name = row[1].strip()
                type_val = row[3].strip()
                subtype_val = row[4].strip()

                items.append({
                    'vnum': vnum,
                    'name': name,
                    'type': type_val,
                    'subtype': subtype_val
                })
            except:
                continue

    print(f"  Loaded {len(items)} items")
    return items


def generate_itemlist(items, output_file='itemlist.txt'):
    """Generate itemlist.txt from items"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("// ItemList generated from NEWVNUM.csv\n")
        f.write("// Format: vnum<TAB>type<TAB>icon_path<TAB>model_path\n\n")

        processed_count = 0

        for item in items:
            vnum = item['vnum']
            name = item['name']
            type_val = item['type']
            subtype_val = item['subtype']

            # Only process +0 items (they define the base)
            if not name.endswith('+0'):
                continue

            # Determine category
            category = determine_item_category(type_val, subtype_val)

            # Generate 10 entries (+0 to +9)
            base_vnum = int(vnum)

            for i in range(10):
                current_vnum = base_vnum + i
                # Icon path always uses +0 vnum with 5 digits
                icon_path = f"icon/item/{int(vnum):05d}.tga"

                if category == 'WEAPON':
                    # WEAPON: includes .gr2 model path
                    model_path = f"d:/ymir work/item/weapon/{int(vnum):05d}.gr2"
                    f.write(f"{current_vnum}\tWEAPON\t{icon_path}\t{model_path}\n")

                elif category == 'ARMOR':
                    # ARMOR: icon only
                    f.write(f"{current_vnum}\tARMOR\t{icon_path}\n")

                else:
                    # ETC: icon only
                    f.write(f"{current_vnum}\tETC\t{icon_path}\n")

            processed_count += 1

        print(f"\nGenerated {processed_count} item sets (10 entries each)")
        print(f"Total entries: {processed_count * 10}")


def main():
    print("=" * 80)
    print("  ItemList Generator for Metin2")
    print("=" * 80)
    print()

    # Check if CSV exists
    if not Path('NEWVNUM.csv').exists():
        print("Error: NEWVNUM.csv not found!")
        print("Please put NEWVNUM.csv in the same folder as this script.")
        return

    # Load items
    items = load_items_from_csv('NEWVNUM.csv')

    if not items:
        print("\nNo items loaded!")
        return

    # Generate itemlist
    generate_itemlist(items, output_file='itemlist.txt')

    print(f"\nitemlist.txt created successfully!")
    print("\nPreview (first 20 lines):")
    print("-" * 80)

    with open('itemlist.txt', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 20:
                break
            print(line.rstrip())

    print("-" * 80)
    print("\nDone! Check itemlist.txt")


if __name__ == '__main__':
    main()

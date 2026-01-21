#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mob Drop Item Generator for Metin2
===================================

This script generates mob_drop_item.txt from mob_names file.

Usage:
  python generate_mob_drop.py

Requirements:
  - mob_names.txt (file with mob vnums and names)

Output:
  - mob_drop_item.txt (formatted drop file for server)
"""

import re
from pathlib import Path


def remove_diacritics(text):
    """
    Remove diacritics (accents, háčky, čárky) from text.
    Simple character-by-character replacement.

    Examples:
        'Silný Vlk' -> 'Silny Vlk'
        'Černý Medvěd' -> 'Cerny Medved'
        'Šedý vlk' -> 'Sedy vlk'
    """
    # Complete Czech character mapping
    replacements = {
        'á': 'a', 'Á': 'A',
        'č': 'c', 'Č': 'C',
        'ď': 'd', 'Ď': 'D',
        'é': 'e', 'É': 'E',
        'ě': 'e', 'Ě': 'E',
        'í': 'i', 'Í': 'I',
        'ň': 'n', 'Ň': 'N',
        'ó': 'o', 'Ó': 'O',
        'ř': 'r', 'Ř': 'R',
        'š': 's', 'Š': 'S',
        'ť': 't', 'Ť': 'T',
        'ú': 'u', 'Ú': 'U',
        'ů': 'u', 'Ů': 'U',
        'ý': 'y', 'Ý': 'Y',
        'ž': 'z', 'Ž': 'Z',
    }

    result = text
    for czech, ascii in replacements.items():
        result = result.replace(czech, ascii)

    return result


def sanitize_group_name(name):
    """
    Sanitize mob name for Group usage:
    - Remove diacritics (č→c, ř→r, á→a, etc.)
    - Replace spaces with underscores
    - Remove any other special characters
    """
    # Remove diacritics
    name = remove_diacritics(name)

    # Replace spaces with underscores
    name = name.replace(' ', '_')

    # Remove any other special characters (keep only alphanumeric and underscore)
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)

    return name


def load_mob_names(filename):
    """Load mob names from file"""
    mobs = []

    print(f"Loading {filename}...")

    if not Path(filename).exists():
        print(f"Error: {filename} not found!")
        return mobs

    # Try different encodings (Czech files are often in cp1250/windows-1250)
    encodings = ['cp1250', 'windows-1250', 'iso-8859-2', 'utf-8']
    file_content = None

    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                file_content = f.readlines()
                print(f"  Successfully loaded with encoding: {encoding}")
                break
        except (UnicodeDecodeError, LookupError):
            continue

    if file_content is None:
        print(f"  Warning: Could not detect encoding, using utf-8 with errors='replace'")
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.readlines()

    for line in file_content:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('//') or line.startswith('#') or line.startswith('VNUM'):
            continue

        # Parse line (format: vnum<TAB>name or vnum<SPACE>name)
        parts = re.split(r'\s+', line, maxsplit=1)

        if len(parts) >= 2:
            try:
                vnum = int(parts[0])
                name = parts[1].strip()

                mobs.append({
                    'vnum': vnum,
                    'name': name,
                    'sanitized_name': sanitize_group_name(name)
                })
            except ValueError:
                # Skip lines that don't start with a number
                continue

    print(f"  Loaded {len(mobs)} mobs")
    return mobs


def generate_mob_drop_item(mobs, output_file='mob_drop_item.txt'):
    """Generate mob_drop_item.txt from mobs"""

    print(f"\nGenerating {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("// Mob Drop Item file generated from mob_names\n")
        f.write("// Format: Group name { Mob vnum, Type drop }\n\n")

        for mob in mobs:
            vnum = mob['vnum']
            sanitized_name = mob['sanitized_name']

            # Write Group block
            f.write(f"Group\t{sanitized_name}\n")
            f.write("{\n")
            f.write(f"\tMob\t{vnum}\n")
            f.write("\tType\tdrop\n")
            f.write("\n")
            f.write("}\n\n")

    print(f"  Generated {len(mobs)} mob drop entries")


def main():
    print("=" * 80)
    print("  Mob Drop Item Generator for Metin2")
    print("=" * 80)
    print()

    # Check if mob_names exists
    if not Path('mob_names.txt').exists():
        print("Error: mob_names.txt not found!")
        print("Please put mob_names.txt in the same folder as this script.")
        print("\nTrying alternative names...")

        # Try alternative filenames
        for alt_name in ['mob_names', 'mobnames.txt', 'MobNames.txt']:
            if Path(alt_name).exists():
                print(f"Found: {alt_name}")
                mob_file = alt_name
                break
        else:
            print("\nNo mob_names file found!")
            return
    else:
        mob_file = 'mob_names.txt'

    # Load mobs
    mobs = load_mob_names(mob_file)

    if not mobs:
        print("\nNo mobs loaded!")
        return

    # Show examples
    print("\nExamples of sanitization:")
    print("-" * 80)
    for mob in mobs[:5]:
        print(f"  {mob['name']:30s} -> {mob['sanitized_name']}")
    print("-" * 80)

    # Generate mob_drop_item.txt
    generate_mob_drop_item(mobs, output_file='mob_drop_item.txt')

    print(f"\nmob_drop_item.txt created successfully!")
    print("\nPreview (first 5 entries):")
    print("-" * 80)

    with open('mob_drop_item.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Print first ~30 lines (5 entries × ~6 lines each)
        for line in lines[:35]:
            print(line.rstrip())

    print("-" * 80)
    print("\nDone! Check mob_drop_item.txt")


if __name__ == '__main__':
    main()

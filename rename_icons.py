#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icon Renamer for Metin2 Items
==============================

This script renames item icons based on vnum changes between old and new item_proto exports.

Usage:
  python rename_icons.py

Requirements:
  - OLDVNUM.csv (old item vnums)
  - NEWVNUM.csv (new item vnums)
  - icons/ folder with icon files (*.tga, *.dds, *.png, etc.)

Output:
  - Renamed icons in icons/ folder
  - rename_log.txt with detailed change log
"""

import os
import csv
import shutil
from pathlib import Path


def load_items_from_csv(filename):
    """Load items from CSV file and return dict: name -> vnum"""
    items = {}

    print(f"Loading {filename}...")
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue

            vnum = row[0].strip()
            name = row[1].strip()

            # Only track +0 items (they have the icon)
            if '+0' in name:
                items[name] = vnum

    print(f"  Loaded {len(items)} +0 items")
    return items


def create_vnum_mapping(old_items, new_items):
    """Create mapping: old_vnum -> new_vnum based on item names"""
    mapping = {}

    print("\nCreating vnum mapping...")
    for name, old_vnum in old_items.items():
        if name in new_items:
            new_vnum = new_items[name]
            if old_vnum != new_vnum:
                mapping[old_vnum] = new_vnum
                print(f"  {name}: {old_vnum} -> {new_vnum}")

    print(f"\nTotal changes: {len(mapping)}")
    return mapping


def find_icon_files(icons_folder, vnum):
    """Find all icon files for given vnum (handles different extensions)"""
    extensions = ['.tga', '.dds', '.png', '.jpg', '.bmp', '.TGA', '.DDS', '.PNG']
    found = []

    for ext in extensions:
        icon_file = icons_folder / f"{vnum}{ext}"
        if icon_file.exists():
            found.append(icon_file)

    return found


def rename_icons(mapping, icons_folder='icons', backup=True):
    """Rename icon files based on vnum mapping"""
    icons_path = Path(icons_folder)

    if not icons_path.exists():
        print(f"\nError: Folder '{icons_folder}' not found!")
        print("Please create 'icons' folder and put your icon files there.")
        return

    # Create backup folder if requested
    if backup:
        backup_path = icons_path / 'backup'
        backup_path.mkdir(exist_ok=True)
        print(f"\nBackup folder created: {backup_path}")

    # Open log file
    log_file = open('rename_log.txt', 'w', encoding='utf-8')
    log_file.write("Icon Rename Log\n")
    log_file.write("=" * 80 + "\n\n")

    renamed_count = 0
    not_found_count = 0

    print("\nRenaming icons...")
    for old_vnum, new_vnum in mapping.items():
        # Find icon files for old vnum
        icon_files = find_icon_files(icons_path, old_vnum)

        if not icon_files:
            log_file.write(f"[NOT FOUND] {old_vnum} -> {new_vnum} (no icon file found)\n")
            not_found_count += 1
            continue

        # Rename each found icon
        for old_icon in icon_files:
            extension = old_icon.suffix
            new_icon = icons_path / f"{new_vnum}{extension}"

            # Backup original
            if backup:
                try:
                    backup_file = backup_path / old_icon.name
                    # Use str() to avoid Path issues on Windows
                    shutil.copy2(str(old_icon), str(backup_file))
                except Exception as e:
                    print(f"  ! Warning: Backup failed for {old_icon.name}: {e}")
                    log_file.write(f"[BACKUP FAILED] {old_vnum}: {e}\n")

            # Rename
            try:
                old_icon.rename(new_icon)
                print(f"  ✓ {old_icon.name} -> {new_icon.name}")
                log_file.write(f"[OK] {old_vnum} -> {new_vnum}: {old_icon.name} -> {new_icon.name}\n")
                renamed_count += 1
            except Exception as e:
                print(f"  ✗ Error renaming {old_icon.name}: {e}")
                log_file.write(f"[ERROR] {old_vnum} -> {new_vnum}: {e}\n")

    log_file.write("\n" + "=" * 80 + "\n")
    log_file.write(f"Summary:\n")
    log_file.write(f"  Total mappings: {len(mapping)}\n")
    log_file.write(f"  Successfully renamed: {renamed_count}\n")
    log_file.write(f"  Not found: {not_found_count}\n")
    log_file.close()

    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Total mappings: {len(mapping)}")
    print(f"  Successfully renamed: {renamed_count}")
    print(f"  Not found: {not_found_count}")
    print(f"\nLog saved to: rename_log.txt")


def main():
    print("=" * 80)
    print("  Icon Renamer for Metin2 Items")
    print("=" * 80)
    print()

    # Check if CSV files exist
    if not os.path.exists('OLDVNUM.csv'):
        print("Error: OLDVNUM.csv not found!")
        print("Please put OLDVNUM.csv in the same folder as this script.")
        return

    if not os.path.exists('NEWVNUM.csv'):
        print("Error: NEWVNUM.csv not found!")
        print("Please put NEWVNUM.csv in the same folder as this script.")
        return

    # Load items
    old_items = load_items_from_csv('OLDVNUM.csv')
    new_items = load_items_from_csv('NEWVNUM.csv')

    # Create mapping
    mapping = create_vnum_mapping(old_items, new_items)

    if not mapping:
        print("\nNo changes detected! All vnums are the same.")
        return

    # Rename icons
    rename_icons(mapping, icons_folder='icons', backup=True)

    print("\n" + "=" * 80)
    print("Done! Check rename_log.txt for details.")
    print("=" * 80)


if __name__ == '__main__':
    main()

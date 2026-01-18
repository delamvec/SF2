#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript pro opravu mob_proto SQL souboru - převod textových typů na číselné hodnoty
"""

import re
import sys

# Mapování textových typů na číselné hodnoty
TYPE_MAPPING = {
    'NPC': 0,
    'MONSTER': 0,
    'BOSS': 1,
    'STONE': 2,
    'WARP': 3,
    'DOOR': 4,
    'BUILDING': 5,
    'PC': 6,
    'POLY': 7,
    'HORSE': 8,
    'GOTO': 9
}

def convert_type_value(value):
    """
    Převede textovou hodnotu typu na číslo
    """
    # Odstranění uvozovek
    clean_value = value.strip().strip("'\"").upper()

    # Pokud je už číslo, vrátit ho
    if clean_value.isdigit():
        return clean_value

    # Převést text na číslo podle mapování
    return str(TYPE_MAPPING.get(clean_value, 0))

def fix_mob_proto_sql(input_file, output_file):
    """
    Opraví SQL soubor - převede textové hodnoty type na čísla
    """
    print(f"Načítám soubor: {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Zkusit jiné kódování
        with open(input_file, 'r', encoding='cp1250', errors='ignore') as f:
            content = f.read()

    # Najít všechny INSERT příkazy a opravit hodnotu type
    # Formát: INSERT INTO `mob_proto` VALUES (vnum, name, locale_name, rank, type, ...)

    lines = content.split('\n')
    fixed_lines = []
    errors_fixed = 0

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('INSERT INTO `mob_proto`'):
            # Najít hodnoty v závorkách
            match = re.search(r'VALUES\s*\((.*)\)', line)
            if match:
                values_str = match.group(1)
                values = []
                current_value = ''
                in_quotes = False
                paren_depth = 0

                # Parsovat hodnoty (respektovat uvozovky a závorky)
                for char in values_str:
                    if char == "'" and (not current_value or current_value[-1] != '\\'):
                        in_quotes = not in_quotes
                        current_value += char
                    elif char == '(' and not in_quotes:
                        paren_depth += 1
                        current_value += char
                    elif char == ')' and not in_quotes:
                        paren_depth -= 1
                        current_value += char
                    elif char == ',' and not in_quotes and paren_depth == 0:
                        values.append(current_value.strip())
                        current_value = ''
                    else:
                        current_value += char

                if current_value:
                    values.append(current_value.strip())

                # Opravit hodnotu type (5. pozice, index 4)
                if len(values) > 4:
                    old_type = values[4]
                    # Zkontrolovat, zda je to textová hodnota v uvozovkách
                    if old_type.strip().startswith("'") or old_type.strip().startswith('"'):
                        new_type = convert_type_value(old_type)
                        values[4] = new_type
                        errors_fixed += 1
                        print(f"Řádek {line_num}: Opraveno {old_type} → {new_type}")

                # Sestavit opravenou řádku
                new_values = ', '.join(values)
                line = re.sub(r'VALUES\s*\(.*\)', f'VALUES ({new_values})', line)

        fixed_lines.append(line)

    # Uložit opravený soubor
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))

    print(f"\nHotovo!")
    print(f"Opravených řádků: {errors_fixed}")
    print(f"Výstupní soubor: {output_file}")
    print(f"\nNyní můžete importovat:")
    print(f"mysql -u root -p srv1_common < {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Použití:")
        print(f"  python3 {sys.argv[0]} <vstupní_soubor> [výstupní_soubor]")
        print()
        print("Příklad:")
        print(f"  python3 {sys.argv[0]} mob_proto_old.sql mob_proto_fixed.sql")
        print()
        print("Nebo použijte existující mob_proto.sql:")
        print("  mysql -u root -p srv1_common < mob_proto.sql")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'mob_proto_fixed.sql'

    fix_mob_proto_sql(input_file, output_file)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mysql2Proto - MySQL to Proto converter for Metin2 (Fixed version with exact structures)
Converts between MySQL database and binary proto files (item_proto, mob_proto)

Usage:
    python mysql2proto_fixed.py -pim    # Pack: MySQL -> proto files
    python mysql2proto_fixed.py -umi    # Unpack: proto files -> MySQL
    python mysql2proto_fixed.py -dumi   # Debug: proto files -> SQL dump

Requirements:
    pip install pymysql python-lzo
"""

import struct
import sys
import json
import os
import pymysql

try:
    import lzo
    HAS_LZO = True
except ImportError:
    print("Warning: python-lzo not installed. Trying without compression...")
    HAS_LZO = False

# TEA Encryption Keys
MOB_PROTO_KEY = [4813894, 18955, 552631, 6822045]
ITEM_PROTO_KEY = [173217, 72619434, 408587239, 27973291]

# FOURCC magic numbers
FOURCC_MIPT = 0x5450494D  # 'MIPT' for item_proto
FOURCC_MMPT = 0x54504D4D  # 'MMPT' for mob_proto

class TEA:
    """TEA (Tiny Encryption Algorithm) cipher"""
    DELTA = 0x9E3779B9
    ROUNDS = 32

    @staticmethod
    def _u32(v):
        """Ensure 32-bit unsigned integer"""
        return v & 0xFFFFFFFF

    @classmethod
    def encrypt_block(cls, v0, v1, key):
        """Encrypt single 64-bit block"""
        sum_val = 0
        for _ in range(cls.ROUNDS):
            v0 = cls._u32(v0 + ((cls._u32((v1 << 4) ^ (v1 >> 5)) + v1) ^ (sum_val + key[sum_val & 3])))
            sum_val = cls._u32(sum_val + cls.DELTA)
            v1 = cls._u32(v1 + ((cls._u32((v0 << 4) ^ (v0 >> 5)) + v0) ^ (sum_val + key[(sum_val >> 11) & 3])))
        return v0, v1

    @classmethod
    def decrypt_block(cls, v0, v1, key):
        """Decrypt single 64-bit block"""
        sum_val = cls._u32(cls.DELTA * cls.ROUNDS)
        for _ in range(cls.ROUNDS):
            v1 = cls._u32(v1 - ((cls._u32((v0 << 4) ^ (v0 >> 5)) + v0) ^ (sum_val + key[(sum_val >> 11) & 3])))
            sum_val = cls._u32(sum_val - cls.DELTA)
            v0 = cls._u32(v0 - ((cls._u32((v1 << 4) ^ (v1 >> 5)) + v1) ^ (sum_val + key[sum_val & 3])))
        return v0, v1

    @classmethod
    def encrypt(cls, data, key):
        """Encrypt data with TEA"""
        # Pad to 8-byte boundary
        size = len(data)
        if size % 8 != 0:
            data += b'\x00' * (8 - (size % 8))

        result = bytearray()
        for i in range(0, len(data), 8):
            v0, v1 = struct.unpack('<II', data[i:i+8])
            v0, v1 = cls.encrypt_block(v0, v1, key)
            result.extend(struct.pack('<II', v0, v1))

        return bytes(result)

    @classmethod
    def decrypt(cls, data, key):
        """Decrypt data with TEA"""
        result = bytearray()
        for i in range(0, len(data), 8):
            v0, v1 = struct.unpack('<II', data[i:i+8])
            v0, v1 = cls.decrypt_block(v0, v1, key)
            result.extend(struct.pack('<II', v0, v1))

        return bytes(result)


class ItemTableR156:
    """TItemTable_r156 structure - 156 bytes - EXACT match from ItemData.h"""

    # struct SItemTable_r156 {
    #   DWORD dwVnum;                   // 4
    #   DWORD dwVnumRange;              // 4
    #   char szName[25];                // 25
    #   char szLocaleName[25];          // 25
    #   BYTE bType;                     // 1
    #   BYTE bSubType;                  // 1
    #   BYTE bWeight;                   // 1
    #   BYTE bSize;                     // 1
    #   DWORD dwAntiFlags;              // 4
    #   DWORD dwFlags;                  // 4
    #   DWORD dwWearFlags;              // 4
    #   DWORD dwImmuneFlag;             // 4
    #   DWORD dwIBuyItemPrice;          // 4
    #   DWORD dwISellItemPrice;         // 4
    #   TItemLimit aLimits[2];          // 2 * 8 = 16  (BYTE+long with padding)
    #   TItemApply aApplies[3];         // 3 * 8 = 24  (BYTE+long with padding)
    #   long alValues[6];               // 6 * 4 = 24
    #   long alSockets[3];              // 3 * 4 = 12
    #   DWORD dwRefinedVnum;            // 4
    #   WORD wRefineSet;                // 2
    #   BYTE bAlterToMagicItemPct;      // 1
    #   BYTE bSpecular;                 // 1
    #   BYTE bGainSocketPct;            // 1
    #   // padding to align                  3
    # } = 156 bytes total

    SIZE = 156

    @staticmethod
    def pack_from_db_row(row):
        """Pack ItemTable from MySQL row - EXACT binary format"""
        data = bytearray(ItemTableR156.SIZE)

        offset = 0

        # dwVnum (DWORD - 4 bytes)
        struct.pack_into('<I', data, offset, row[0] or 0)
        offset += 4

        # dwVnumRange (DWORD - 4 bytes) - auto-detect for DS items (type 28)
        vnum_range = 99 if (row[1] == 28) else 0
        struct.pack_into('<I', data, offset, vnum_range)
        offset += 4

        # szName (char[25])
        name = (row[3] or '')[:24].encode('utf-8')
        data[offset:offset+25] = name.ljust(25, b'\x00')
        offset += 25

        # szLocaleName (char[25])
        locale_name = (row[4] or '')[:24].encode('utf-8')
        data[offset:offset+25] = locale_name.ljust(25, b'\x00')
        offset += 25

        # bType, bSubType, bWeight, bSize (4 BYTEs)
        struct.pack_into('<BBBB', data, offset,
                        row[1] or 0,  # type
                        row[2] or 0,  # subtype
                        row[7] or 0,  # weight
                        row[8] or 0)  # size
        offset += 4

        # dwAntiFlags, dwFlags, dwWearFlags, dwImmuneFlag (4 DWORDs)
        struct.pack_into('<IIII', data, offset,
                        row[11] or 0,  # antiflag
                        row[9] or 0,   # flag
                        row[10] or 0,  # wearflag
                        row[12] or 0)  # immuneflag
        offset += 16

        # dwIBuyItemPrice, dwISellItemPrice (2 DWORDs)
        struct.pack_into('<II', data, offset,
                        row[5] or 0,   # gold
                        row[6] or 0)   # shop_buy_price
        offset += 8

        # aLimits[2] - TItemLimit { BYTE bType; long lValue; } with padding
        # Each TItemLimit is 8 bytes (BYTE + 3 padding + long)
        for i in range(2):
            limit_type = row[19 + i*2] or 0
            limit_value = row[20 + i*2] or 0
            struct.pack_into('<Bxxxl', data, offset, limit_type, limit_value)
            offset += 8

        # aApplies[3] - TItemApply { BYTE bType; long lValue; } with padding
        # Each TItemApply is 8 bytes (BYTE + 3 padding + long)
        for i in range(3):
            apply_type = row[23 + i*2] or 0
            apply_value = row[24 + i*2] or 0
            struct.pack_into('<Bxxxl', data, offset, apply_type, apply_value)
            offset += 8

        # alValues[6] (6 longs)
        for i in range(6):
            struct.pack_into('<l', data, offset, row[29 + i] or 0)
            offset += 4

        # alSockets[3] (3 longs) - always 0
        struct.pack_into('<lll', data, offset, 0, 0, 0)
        offset += 12

        # dwRefinedVnum (DWORD)
        struct.pack_into('<I', data, offset, row[13] or 0)
        offset += 4

        # wRefineSet (WORD)
        struct.pack_into('<H', data, offset, row[14] or 0)
        offset += 2

        # bAlterToMagicItemPct, bSpecular, bGainSocketPct (3 BYTEs)
        struct.pack_into('<BBB', data, offset,
                        row[15] or 0,  # magic_pct
                        row[16] or 0,  # specular
                        row[17] or 0)  # socket_pct
        offset += 3

        # Padding to 156 bytes (should be 3 bytes)
        # Already handled by bytearray initialization

        assert offset + 3 == ItemTableR156.SIZE, f"Size mismatch: {offset} + 3 != {ItemTableR156.SIZE}"

        return bytes(data)


class Mysql2Proto:
    def __init__(self, config_file='Mysql2Proto.json'):
        self.config = self.load_config(config_file)
        self.conn = None

    def load_config(self, filename):
        """Load configuration from JSON"""
        if not os.path.exists(filename):
            print(f"Error: {filename} not found")
            sys.exit(1)

        with open(filename, 'r') as f:
            config = json.load(f)

        print(f"<ConfigFile> LOAD '{filename}' BEGIN")
        print(f"<ConfigFile> s_szdatabase changed to '{config.get('database', 'player')}'.")
        print(f"<ConfigFile> s_szhostname changed to '{config.get('hostname', 'localhost')}'.")
        print(f"<ConfigFile> s_szuser changed to '{config.get('user', 'root')}'.")
        print(f"<ConfigFile> s_szpassword changed to '{config.get('password', '')}'.")
        print(f"<ConfigFile> s_szport changed to '{config.get('port', 3306)}'.")
        print(f"<ConfigFile> LOAD '{filename}' END")

        return config

    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.conn = pymysql.connect(
                host=self.config.get('hostname', 'localhost'),
                port=int(self.config.get('port', 3306)),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', ''),
                database=self.config.get('database', 'player'),
                charset='utf8mb4'
            )
            print("<ConfigFile> MYSQL SUCCESSFULLY CONNECTED")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def pack_item_proto(self):
        """Export item_proto from MySQL to binary file"""
        if not self.connect_db():
            return False

        cursor = self.conn.cursor()

        query = """
            SELECT vnum, type, subtype, name, locale_name, gold, shop_buy_price, weight, size,
                   flag, wearflag, antiflag, immuneflag+0, refined_vnum, refine_set, magic_pct,
                   specular, socket_pct, addon_type,
                   limittype0, limitvalue0, limittype1, limitvalue1,
                   applytype0, applyvalue0, applytype1, applyvalue1, applytype2, applyvalue2,
                   value0, value1, value2, value3, value4, value5
            FROM item_proto ORDER BY vnum
        """

        print(f"sizeof(CItemData::TItemTable): {ItemTableR156.SIZE}")
        print("Loading item_proto from MySQL")

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"Complete! {len(rows)} Items loaded.")

        # Build binary data
        data = bytearray()
        for row in rows:
            data.extend(ItemTableR156.pack_from_db_row(row))

        print(f"lzo.real_alloc  {hex(id(data))}({len(data)})")

        # Compress with LZO
        if HAS_LZO:
            try:
                compressed = lzo.compress(bytes(data), 1)  # level 1 = lzo1x_1
                print(f"{len(data)} --Compress--> {len(compressed)} bytes")
            except Exception as e:
                print(f"Warning: LZO compression failed: {e}, using uncompressed data")
                compressed = bytes(data)
        else:
            print("Warning: LZO not available, using uncompressed data")
            compressed = bytes(data)

        # Encrypt with TEA
        # Prepend 4-byte size header before encryption
        size_header = struct.pack('<I', len(compressed))
        to_encrypt = size_header + compressed

        encrypted = TEA.encrypt(to_encrypt, ITEM_PROTO_KEY)
        print(f"{len(compressed)} --Encrypt--> {len(encrypted)} bytes")

        # Write to file
        with open('item_proto', 'wb') as f:
            f.write(struct.pack('<I', FOURCC_MIPT))           # fourcc 'MIPT'
            f.write(struct.pack('<I', len(rows)))             # element count
            f.write(struct.pack('<I', len(encrypted)))        # data size
            f.write(encrypted)

        print("item_proto created successfully!")
        print(f"File size: {os.path.getsize('item_proto')} bytes")

        cursor.close()
        self.conn.close()
        return True

    def pack_mob_proto(self):
        """Export mob_proto from MySQL to binary file"""
        print("mob_proto packing not yet implemented (need TMobTable structure)")
        print("Please provide PythonNonPlayer.h file")
        return False

    def run(self, args):
        """Main execution"""
        if len(args) < 2:
            print(__doc__)
            return

        mode = args[1].lower()

        if 'p' in mode:  # Pack
            if 'i' in mode:
                self.pack_item_proto()
            if 'm' in mode:
                self.pack_mob_proto()
        elif 'u' in mode:  # Unpack
            print("Unpack mode not implemented yet")
        elif 'd' in mode:  # Debug
            print("Debug mode not implemented yet")
        else:
            print("Unknown mode. Use -pim, -umi, or -dumi")


if __name__ == '__main__':
    tool = Mysql2Proto()
    tool.run(sys.argv)

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
    LZO_LIBRARY = 'python-lzo'
    lzo_compressor = None
except ImportError:
    lzo = None
    try:
        from lzallright import LZOCompressor
        HAS_LZO = True
        LZO_LIBRARY = 'lzallright'
        lzo_compressor = LZOCompressor()
        print("Using lzallright for LZO compression (python-lzo alternative)")
    except ImportError:
        LZOCompressor = None
        lzo_compressor = None
        print("Warning: python-lzo/lzallright not installed. Trying without compression...")
        HAS_LZO = False
        LZO_LIBRARY = None


def lzo_compress(data):
    """Compress data using available LZO library"""
    if not HAS_LZO:
        return bytes(data)

    try:
        if LZO_LIBRARY == 'python-lzo':
            # python-lzo API: lzo.compress(data, level)
            return lzo.compress(bytes(data), 1)
        elif LZO_LIBRARY == 'lzallright':
            # lzallright API: LZOCompressor().compress(data)
            return lzo_compressor.compress(bytes(data))
        else:
            return bytes(data)
    except Exception as e:
        print(f"Warning: LZO compression failed: {e}")
        return bytes(data)

# TEA Encryption Keys
MOB_PROTO_KEY = [4813894, 18955, 552631, 6822045]
ITEM_PROTO_KEY = [173217, 72619434, 408587239, 27973291]

# FOURCC magic numbers
FOURCC_MIPT = 0x5450494D  # 'MIPT' for item_proto (standard)
FOURCC_MIPX = 0x5850494D  # 'MIPX' for item_proto (extended with version/stride)
FOURCC_MMPT = 0x54504D4D  # 'MMPT' for mob_proto
FOURCC_MCOZ = 0x5A4F434D  # 'MCOZ' for LZO compression header

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


def to_bytes(value, encoding='utf-8'):
    """Convert string or bytes to bytes"""
    if isinstance(value, bytes):
        return value
    elif isinstance(value, str):
        return value.encode(encoding)
    elif value is None:
        return b''
    else:
        return str(value).encode(encoding)


def to_int(value):
    """Convert value to int, handling bytes, Decimal, None"""
    if value is None:
        return 0
    if isinstance(value, bytes):
        try:
            return int(value.decode('utf-8'))
        except:
            return 0
    try:
        return int(value)
    except:
        return 0


class ItemTableR156:
    """TItemTable_r156 structure - 156 bytes - EXACT match from ItemData.h"""

    # struct SItemTable_r156 {  (PACKED - no padding)
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
    #   TItemLimit aLimits[2];          // 2 * 5 = 10  (BYTE+long, PACKED)
    #   TItemApply aApplies[3];         // 3 * 5 = 15  (BYTE+long, PACKED)
    #   long alValues[6];               // 6 * 4 = 24
    #   long alSockets[3];              // 3 * 4 = 12
    #   DWORD dwRefinedVnum;            // 4
    #   WORD wRefineSet;                // 2
    #   BYTE bAlterToMagicItemPct;      // 1
    #   BYTE bSpecular;                 // 1
    #   BYTE bGainSocketPct;            // 1
    # } = 156 bytes total (PACKED)

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
        name = to_bytes(row[3] or '')[:24]
        data[offset:offset+25] = name.ljust(25, b'\x00')
        offset += 25

        # szLocaleName (char[25])
        locale_name = to_bytes(row[4] or '')[:24]
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

        # aLimits[2] - TItemLimit { BYTE bType; long lValue; } WITHOUT padding (packed)
        # Each TItemLimit is 5 bytes (BYTE + long, no padding)
        for i in range(2):
            limit_type = row[19 + i*2] or 0
            limit_value = row[20 + i*2] or 0
            struct.pack_into('<Bl', data, offset, limit_type, limit_value)
            offset += 5

        # aApplies[3] - TItemApply { BYTE bType; long lValue; } WITHOUT padding (packed)
        # Each TItemApply is 5 bytes (BYTE + long, no padding)
        for i in range(3):
            apply_type = row[23 + i*2] or 0
            apply_value = row[24 + i*2] or 0
            struct.pack_into('<Bl', data, offset, apply_type, apply_value)
            offset += 5

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

        # No padding needed - struct is packed to exactly 156 bytes

        assert offset == ItemTableR156.SIZE, f"Size mismatch: {offset} != {ItemTableR156.SIZE}"

        return bytes(data)


class MobTableR255:
    """TMobTable_r255 structure - 255 bytes - PACKED (no padding)"""
    SIZE = 255
    CHARACTER_NAME_MAX_LEN = 24
    MOB_ENCHANTS_MAX_NUM = 6
    MOB_RESISTS_MAX_NUM = 11
    MOB_SKILL_MAX_NUM = 5

    @staticmethod
    def pack_from_db_row(row):
        """Pack MobTable from MySQL row - PACKED binary format (no alignment padding)"""
        data = bytearray(MobTableR255.SIZE)
        offset = 0

        # dwVnum (DWORD - 4 bytes)
        struct.pack_into('<I', data, offset, to_int(row[0]))
        offset += 4

        # szName (char[25])
        name = to_bytes(row[1] or '')[:MobTableR255.CHARACTER_NAME_MAX_LEN]
        data[offset:offset+25] = name.ljust(25, b'\x00')
        offset += 25

        # szLocaleName (char[25])
        locale_name = to_bytes(row[2] or '')[:MobTableR255.CHARACTER_NAME_MAX_LEN]
        data[offset:offset+25] = locale_name.ljust(25, b'\x00')
        offset += 25

        # bType, bRank, bBattleType, bLevel, bSize (5 BYTEs)
        struct.pack_into('<BBBBB', data, offset,
                        to_int(row[3]),   # type
                        to_int(row[4]),   # rank
                        to_int(row[5]),   # battle_type
                        to_int(row[6]),   # level
                        to_int(row[7]))   # size
        offset += 5

        # dwGoldMin, dwGoldMax, dwExp, dwMaxHP (4 DWORDs)
        struct.pack_into('<IIII', data, offset,
                        to_int(row[26]),  # gold_min
                        to_int(row[27]),  # gold_max
                        to_int(row[25]),  # exp
                        to_int(row[22]))  # max_hp
        offset += 16

        # bRegenCycle, bRegenPercent (2 BYTEs)
        struct.pack_into('<BB', data, offset,
                        to_int(row[23]),  # regen_cycle
                        to_int(row[24]))  # regen_percent
        offset += 2

        # wDef (WORD)
        struct.pack_into('<H', data, offset, to_int(row[28]))
        offset += 2

        # dwAIFlag, dwRaceFlag, dwImmuneFlag (3 DWORDs)
        struct.pack_into('<III', data, offset,
                        to_int(row[8]),   # ai_flag
                        to_int(row[9]),   # setRaceFlag
                        to_int(row[10]))  # setImmuneFlag
        offset += 12

        # bStr, bDex, bCon, bInt (4 BYTEs)
        struct.pack_into('<BBBB', data, offset,
                        to_int(row[16]),  # st
                        to_int(row[17]),  # dx
                        to_int(row[18]),  # ht
                        to_int(row[19]))  # iq
        offset += 4

        # dwDamageRange[2] (2 DWORDs)
        struct.pack_into('<II', data, offset,
                        to_int(row[20]),  # damage_min
                        to_int(row[21]))  # damage_max
        offset += 8

        # sAttackSpeed, sMovingSpeed (2 shorts)
        struct.pack_into('<hh', data, offset,
                        to_int(row[29]),  # attack_speed
                        to_int(row[30]))  # move_speed
        offset += 4

        # bAggresiveHPPct (BYTE)
        struct.pack_into('<B', data, offset, to_int(row[31]))
        offset += 1

        # wAggressiveSight (WORD)
        struct.pack_into('<H', data, offset, to_int(row[32]))
        offset += 2

        # wAttackRange (WORD)
        struct.pack_into('<H', data, offset, to_int(row[33]))
        offset += 2

        # cEnchants[6] (6 signed chars)
        struct.pack_into('<bbbbbb', data, offset,
                        to_int(row[35]),  # enchant_curse
                        to_int(row[36]),  # enchant_slow
                        to_int(row[37]),  # enchant_poison
                        to_int(row[38]),  # enchant_stun
                        to_int(row[39]),  # enchant_critical
                        to_int(row[40]))  # enchant_penetrate
        offset += 6

        # cResists[11] (11 signed chars)
        struct.pack_into('<bbbbbbbbbbb', data, offset,
                        to_int(row[41]),  # resist_sword
                        to_int(row[42]),  # resist_twohand
                        to_int(row[43]),  # resist_dagger
                        to_int(row[44]),  # resist_bell
                        to_int(row[45]),  # resist_fan
                        to_int(row[46]),  # resist_bow
                        to_int(row[47]),  # resist_fire
                        to_int(row[48]),  # resist_elect
                        to_int(row[49]),  # resist_magic
                        to_int(row[50]),  # resist_wind
                        to_int(row[51]))  # resist_poison
        offset += 11

        # dwResurrectionVnum (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[14]))
        offset += 4

        # dwDropItemVnum (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[13]))
        offset += 4

        # bMountCapacity (BYTE) - this field exists in DB but not in query
        # According to SQL schema, this is mount_capacity field
        # We'll set it to 0 since it's not in our query
        struct.pack_into('<B', data, offset, 0)
        offset += 1

        # bOnClickType (BYTE)
        struct.pack_into('<B', data, offset, to_int(row[11]))
        offset += 1

        # bEmpire (BYTE)
        struct.pack_into('<B', data, offset, to_int(row[12]))
        offset += 1

        # szFolder (char[65])
        folder = to_bytes(row[15] or '')[:64]
        data[offset:offset+65] = folder.ljust(65, b'\x00')
        offset += 65

        # fDamMultiply (float - 4 bytes)
        struct.pack_into('<f', data, offset, float(row[52] or 0.0))
        offset += 4

        # dwSummonVnum (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[53]))
        offset += 4

        # dwDrainSP (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[54]))
        offset += 4

        # dwMonsterColor (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[55]))
        offset += 4

        # dwPolymorphItemVnum (DWORD)
        struct.pack_into('<I', data, offset, to_int(row[34]))
        offset += 4

        # Skills[5] - each TMobSkillLevel is PACKED: { DWORD dwVnum; BYTE bLevel; } = 5 bytes
        for i in range(MobTableR255.MOB_SKILL_MAX_NUM):
            skill_vnum = to_int(row[56 + i*2])
            skill_level = to_int(row[57 + i*2])
            struct.pack_into('<IB', data, offset, skill_vnum, skill_level)
            offset += 5

        # Special Points (5 BYTEs)
        struct.pack_into('<BBBBB', data, offset,
                        to_int(row[66]),  # sp_berserk
                        to_int(row[67]),  # sp_stoneskin
                        to_int(row[68]),  # sp_godspeed
                        to_int(row[69]),  # sp_deathblow
                        to_int(row[70]))  # sp_revive
        offset += 5

        assert offset == MobTableR255.SIZE, f"Size mismatch: {offset} != {MobTableR255.SIZE}"

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
        compressed = lzo_compress(data)
        if len(compressed) < len(data):
            print(f"{len(data)} --Compress--> {len(compressed)} bytes")
        else:
            if HAS_LZO:
                print(f"Warning: Compression didn't reduce size, using uncompressed ({len(data)} bytes)")
            else:
                print(f"Warning: LZO not available, using uncompressed data ({len(data)} bytes)")
            compressed = bytes(data)

        # Build data to encrypt: MCOZ fourcc + size + compressed data
        # After decryption, first 4 bytes MUST be 'MCOZ' (client checks this)
        to_encrypt = struct.pack('<I', FOURCC_MCOZ) + struct.pack('<I', len(compressed)) + compressed

        # Pad to 8-byte boundary for TEA encryption
        if len(to_encrypt) % 8:
            padded_size = (len(to_encrypt) // 8 + 1) * 8
        else:
            padded_size = len(to_encrypt)
        to_encrypt_padded = to_encrypt + b'\x00' * (padded_size - len(to_encrypt))

        # Encrypt padded data
        encrypted = TEA.encrypt(to_encrypt_padded, ITEM_PROTO_KEY)
        print(f"{len(data)} --Compress--> {len(compressed)} --Encrypt--> {len(encrypted)} bytes")

        # Write to file with MIPX format (extended format with version and stride)
        # Format: MIPX header + encrypted data (MCOZ is inside encrypted data)
        with open('item_proto', 'wb') as f:
            f.write(struct.pack('<I', FOURCC_MIPX))           # fourcc 'MIPX' (extended format)
            f.write(struct.pack('<I', 1))                     # version = 1
            f.write(struct.pack('<I', ItemTableR156.SIZE))    # stride = 156 bytes
            f.write(struct.pack('<I', len(rows)))             # element count
            f.write(struct.pack('<I', len(encrypted)))        # data size (encrypted size)
            f.write(encrypted)                                 # encrypted data

        print("item_proto created successfully!")
        print(f"File size: {os.path.getsize('item_proto')} bytes")

        cursor.close()
        self.conn.close()
        return True

    def pack_mob_proto(self):
        """Export mob_proto from MySQL to binary file"""
        if not self.connect_db():
            return False

        cursor = self.conn.cursor()

        query = """
            SELECT vnum, name, locale_name, type, rank, battle_type, level,
                   CASE size WHEN 'SMALL' THEN 0 WHEN 'MEDIUM' THEN 1 WHEN 'BIG' THEN 2 ELSE 0 END as size,
                   ai_flag+0 as ai_flag, setRaceFlag+0 as setRaceFlag, setImmuneFlag+0 as setImmuneFlag,
                   on_click, empire, drop_item, resurrection_vnum, folder,
                   st, dx, ht, iq, damage_min, damage_max, max_hp,
                   regen_cycle, regen_percent, exp, gold_min, gold_max, def,
                   attack_speed, move_speed, aggressive_hp_pct, aggressive_sight, attack_range, polymorph_item,
                   enchant_curse, enchant_slow, enchant_poison, enchant_stun, enchant_critical, enchant_penetrate,
                   resist_sword, resist_twohand, resist_dagger, resist_bell, resist_fan, resist_bow,
                   resist_fire, resist_elect, resist_magic, resist_wind, resist_poison, dam_multiply, summon, drain_sp,
                   mob_color,
                   skill_vnum0, skill_level0, skill_vnum1, skill_level1, skill_vnum2, skill_level2,
                   skill_vnum3, skill_level3, skill_vnum4, skill_level4,
                   sp_berserk, sp_stoneskin, sp_godspeed, sp_deathblow, sp_revive
            FROM mob_proto ORDER BY vnum
        """

        print(f"sizeof(CPythonNonPlayer::TMobTable): {MobTableR255.SIZE}")
        print("Loading mob_proto from MySQL")

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"Complete! {len(rows)} Mobs loaded.")

        # Build binary data
        data = bytearray()
        for row in rows:
            data.extend(MobTableR255.pack_from_db_row(row))

        print(f"lzo.real_alloc  {hex(id(data))}({len(data)})")

        # Compress with LZO
        compressed = lzo_compress(data)
        if len(compressed) < len(data):
            print(f"{len(data)} --Compress--> {len(compressed)} bytes")
        else:
            if HAS_LZO:
                print(f"Warning: Compression didn't reduce size, using uncompressed ({len(data)} bytes)")
            else:
                print(f"Warning: LZO not available, using uncompressed data ({len(data)} bytes)")
            compressed = bytes(data)

        # Build data to encrypt: MCOZ fourcc + size + compressed data
        # After decryption, first 4 bytes MUST be 'MCOZ' (client checks this)
        to_encrypt = struct.pack('<I', FOURCC_MCOZ) + struct.pack('<I', len(compressed)) + compressed

        # Pad to 8-byte boundary for TEA encryption
        if len(to_encrypt) % 8:
            padded_size = (len(to_encrypt) // 8 + 1) * 8
        else:
            padded_size = len(to_encrypt)
        to_encrypt_padded = to_encrypt + b'\x00' * (padded_size - len(to_encrypt))

        # Encrypt padded data
        encrypted = TEA.encrypt(to_encrypt_padded, MOB_PROTO_KEY)
        print(f"{len(data)} --Compress--> {len(compressed)} --Encrypt--> {len(encrypted)} bytes")

        # Write to file with MMPT format
        # Format: MMPT header + encrypted data (MCOZ is inside encrypted data)
        with open('mob_proto', 'wb') as f:
            f.write(struct.pack('<I', FOURCC_MMPT))           # fourcc 'MMPT'
            f.write(struct.pack('<I', len(rows)))             # element count
            f.write(struct.pack('<I', len(encrypted)))        # data size (encrypted size)
            f.write(encrypted)                                 # encrypted data

        print("mob_proto created successfully!")
        print(f"File size: {os.path.getsize('mob_proto')} bytes")

        cursor.close()
        self.conn.close()
        return True

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

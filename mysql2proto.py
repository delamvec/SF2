#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mysql2Proto - MySQL to Proto converter for Metin2
Converts between MySQL database and binary proto files (item_proto, mob_proto)

Usage:
    python mysql2proto.py -pim    # Pack: MySQL -> proto files
    python mysql2proto.py -umi    # Unpack: proto files -> MySQL
    python mysql2proto.py -dumi   # Debug: proto files -> SQL dump

Requirements:
    pip install pymysql lzo
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
    print("Warning: python-lzo not installed. Compression will be disabled.")
    print("Install with: pip install python-lzo")
    HAS_LZO = False

# TEA Encryption Keys
MOB_PROTO_KEY = [4813894, 18955, 552631, 6822045]
ITEM_PROTO_KEY = [173217, 72619434, 408587239, 27973291]

# FOURCC magic numbers
FOURCC_MIPT = 0x5450494D  # 'MIPT' for item_proto
FOURCC_MMPT = 0x54504D4D  # 'MMPT' for mob_proto

# Structure sizes
ITEM_TABLE_SIZE = 156  # TItemTable size
MOB_TABLE_SIZE = 312   # TMobTable size (approximate)

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


class ItemTable:
    """TItemTable structure (156 bytes)"""
    FORMAT = '<I24s24sBBBBIIIIII2I2i6I12i3i6i3iHBBB'  # 156 bytes
    SIZE = 156

    @staticmethod
    def from_db_row(row):
        """Create ItemTable from MySQL row"""
        data = []

        # dwVnum (4)
        data.append(row[0] or 0)

        # szName (24), szLocaleName (24)
        data.append((row[3] or '').encode('utf-8')[:24].ljust(24, b'\x00'))
        data.append((row[4] or '').encode('utf-8')[:24].ljust(24, b'\x00'))

        # bType, bSubType, bWeight, bSize (4)
        data.extend([row[1] or 0, row[2] or 0, row[7] or 0, row[8] or 0])

        # dwAntiFlags, dwFlags, dwWearFlags, dwImmuneFlag (16)
        data.extend([row[11] or 0, row[9] or 0, row[10] or 0, row[12] or 0])

        # dwIBuyItemPrice, dwISellItemPrice (8)
        data.extend([row[5] or 0, row[6] or 0])

        # aLimits[2]: bType, lValue (16)
        data.extend([row[19] or 0, row[20] or 0, row[21] or 0, row[22] or 0])

        # aApplies[3]: bType, lValue (24)
        data.extend([row[23] or 0, row[24] or 0, row[25] or 0, row[26] or 0, row[27] or 0, row[28] or 0])

        # alValues[6] (24)
        data.extend([row[29] or 0, row[30] or 0, row[31] or 0, row[32] or 0, row[33] or 0, row[34] or 0])

        # alSockets[3] (12) - padded
        data.extend([0, 0, 0])

        # dwRefinedVnum (4)
        data.append(row[13] or 0)

        # wRefineSet (2)
        data.append(row[14] or 0)

        # bAlterToMagicItemPct, bSpecular, bGainSocketPct (3)
        data.extend([row[15] or 0, row[16] or 0, row[17] or 0])

        # dwVnumRange - auto-detect for DS items
        if row[1] == 28:  # ITEM_TYPE_DS
            data.append(99)
        else:
            data.append(0)

        return struct.pack(ItemTable.FORMAT, *data)


class MobTable:
    """TMobTable structure"""
    # Approximate structure based on code analysis
    FORMAT = '<I24s24sBBBBIII B64sBBBBII2IB Bff HH I 6b 11b f 2I I I 10I 5B'
    SIZE = 312

    @staticmethod
    def from_db_row(row):
        """Create MobTable from MySQL row"""
        data = []

        # dwVnum
        data.append(row[0] or 0)

        # szName, szLocaleName
        data.append((row[1] or '').encode('utf-8')[:24].ljust(24, b'\x00'))
        data.append((row[2] or '').encode('utf-8')[:24].ljust(24, b'\x00'))

        # bType, bRank, bBattleType, bLevel
        data.extend([row[3] or 0, row[4] or 0, row[5] or 0, row[6] or 0])

        # dwAIFlag, dwRaceFlag, dwImmuneFlag
        data.extend([row[8] or 0, row[9] or 0, row[10] or 0])

        # bEmpire
        data.append(row[12] or 0)

        # szFolder
        data.append((row[15] or '').encode('utf-8')[:64].ljust(64, b'\x00'))

        # bOnClickType, bStr, bDex, bCon, bInt
        data.extend([row[11] or 0, row[16] or 0, row[17] or 0, row[18] or 0, row[19] or 0])

        # dwDamageRange[2], dwMaxHP
        data.extend([row[20] or 0, row[21] or 0, row[22] or 0])

        # bRegenCycle, bRegenPercent
        data.extend([row[23] or 0, row[24] or 0])

        # fDamMultiply (placeholder), exp as float
        data.extend([1.0, float(row[25] or 0)])

        # dwGoldMin, dwGoldMax, wDef
        data.extend([row[26] or 0, row[27] or 0, row[28] or 0])

        # sAttackSpeed, sMovingSpeed
        data.extend([row[29] or 0, row[30] or 0])

        # bAggresiveHPPct
        data.append(row[31] or 0)

        # cEnchants[6]
        data.extend([row[34] or 0, row[35] or 0, row[36] or 0, row[37] or 0, row[38] or 0, row[39] or 0])

        # cResists[11]
        data.extend([row[40] or 0, row[41] or 0, row[42] or 0, row[43] or 0, row[44] or 0, row[45] or 0,
                    row[46] or 0, row[47] or 0, row[48] or 0, row[49] or 0, row[50] or 0])

        # fDamMultiply (actual value)
        data.append(float(row[51] or 1.0))

        # dwSummonVnum, dwDrainSP
        data.extend([row[52] or 0, row[53] or 0])

        # dwDropItemVnum
        data.append(row[13] or 0)

        # dwResurrectionVnum, dwPolymorphItemVnum, dwMonsterColor
        data.extend([row[14] or 0, row[33] or 0, row[54] or 0])

        # Skills[5]: dwVnum, bLevel (10 DWORDs)
        data.extend([row[55] or 0, row[56] or 0, row[57] or 0, row[58] or 0, row[59] or 0,
                    row[60] or 0, row[61] or 0, row[62] or 0, row[63] or 0, row[64] or 0])

        # bBerserkPoint, bStoneSkinPoint, bGodSpeedPoint, bDeathBlowPoint, bRevivePoint
        data.extend([row[65] or 0, row[66] or 0, row[67] or 0, row[68] or 0, row[69] or 0])

        return struct.pack(MobTable.FORMAT, *data)


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
        print(f"<ConfigFile> database: {config.get('database', 'N/A')}")
        print(f"<ConfigFile> hostname: {config.get('hostname', 'N/A')}")
        print(f"<ConfigFile> user: {config.get('user', 'N/A')}")
        print(f"<ConfigFile> port: {config.get('port', 3306)}")
        print(f"<ConfigFile> LOAD '{filename}' END")

        return config

    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.conn = pymysql.connect(
                host=self.config.get('hostname', 'localhost'),
                port=self.config.get('port', 3306),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', ''),
                database=self.config.get('database', 'player'),
                charset='utf8mb4'
            )
            print("<ConfigFile> MYSQL SUCCESSFULLY CONNECTED")
            return True
        except Exception as e:
            print(f"Error: Can't connect to MySQL - {e}")
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

        print(f"sizeof(CItemData::TItemTable): {ItemTable.SIZE}")
        print("Loading item_proto from MySQL")

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"Complete! {len(rows)} Items loaded.")

        # Build binary data
        data = bytearray()
        for row in rows:
            data.extend(ItemTable.from_db_row(row))

        # Compress with LZO (if available)
        if HAS_LZO:
            try:
                compressed = lzo.compress(bytes(data))
                print(f"{len(data)} --Compress--> {len(compressed)} bytes")
            except Exception as e:
                print(f"LZO compression failed: {e}")
                compressed = bytes(data)
        else:
            print("Warning: Skipping LZO compression (not available)")
            compressed = bytes(data)

        # Encrypt with TEA
        encrypted = TEA.encrypt(compressed, ITEM_PROTO_KEY)
        print(f"{len(compressed)} --Encrypt--> {len(encrypted)} bytes")

        # Write to file
        with open('item_proto', 'wb') as f:
            f.write(struct.pack('<I', FOURCC_MIPT))  # fourcc
            f.write(struct.pack('<I', ItemTable.SIZE))  # stride
            f.write(struct.pack('<I', len(rows)))  # element count
            f.write(struct.pack('<I', len(encrypted)))  # data size
            f.write(encrypted)

        print("item_proto created successfully!")
        cursor.close()
        self.conn.close()
        return True

    def pack_mob_proto(self):
        """Export mob_proto from MySQL to binary file"""
        if not self.connect_db():
            return False

        cursor = self.conn.cursor()

        query = """
            SELECT vnum, name, locale_name, type, rank, battle_type, level, size+0,
                   ai_flag+0, setRaceFlag+0, setImmuneFlag+0, on_click, empire, drop_item,
                   resurrection_vnum, folder, st, dx, ht, iq, damage_min, damage_max, max_hp,
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

        print(f"sizeof(CPythonNonPlayer::TMobTable): {MobTable.SIZE}")
        print("Loading mob_proto from MySQL")

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"Complete! {len(rows)} Mobs loaded.")

        # Build binary data
        data = bytearray()
        for row in rows:
            data.extend(MobTable.from_db_row(row))

        # Compress with LZO (if available)
        if HAS_LZO:
            try:
                compressed = lzo.compress(bytes(data))
                print(f"{len(data)} --Compress--> {len(compressed)} bytes")
            except Exception as e:
                print(f"LZO compression failed: {e}")
                compressed = bytes(data)
        else:
            print("Warning: Skipping LZO compression (not available)")
            compressed = bytes(data)

        # Encrypt with TEA
        encrypted = TEA.encrypt(compressed, MOB_PROTO_KEY)
        print(f"{len(compressed)} --Encrypt--> {len(encrypted)} bytes")

        # Write to file
        with open('mob_proto', 'wb') as f:
            f.write(struct.pack('<I', FOURCC_MMPT))  # fourcc
            f.write(struct.pack('<I', len(rows)))  # element count
            f.write(struct.pack('<I', len(encrypted)))  # data size
            f.write(encrypted)

        print("mob_proto created successfully!")
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

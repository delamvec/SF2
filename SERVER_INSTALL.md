# Instalace a spuštění na serveru

## Krok 1: Nahrát soubory na server

Máte několik možností:

### Možnost A: SCP (z vašeho počítače)

```bash
# Nahrát skript na server
scp import_mob_proto_to_db.py root@VAS_SERVER:/root/

# Nebo nahrát celý adresář
scp -r SF2/ root@VAS_SERVER:/root/
```

### Možnost B: Git (pokud máte git na serveru)

```bash
# Na serveru
cd /root
git clone https://github.com/delamvec/SF2.git
cd SF2
git checkout claude/fix-mob-proto-import-hupq7
```

### Možnost C: Wget (stáhnout přímo ze serveru)

```bash
# Na serveru
cd /root
wget https://raw.githubusercontent.com/delamvec/SF2/claude/fix-mob-proto-import-hupq7/import_mob_proto_to_db.py
```

### Možnost D: Manuální nahrání přes FTP/SFTP

Použijte FileZilla nebo WinSCP a nahrajte:
- `import_mob_proto_to_db.py`

## Krok 2: Nainstalovat prerekvizity na serveru

```bash
# Připojit se k serveru přes SSH
ssh root@VAS_SERVER

# Zkontrolovat Python verzi
python3 --version

# Nainstalovat MySQL connector
pip3 install mysql-connector-python

# NEBO pokud pip3 nefunguje:
apt-get update
apt-get install python3-pip -y
pip3 install mysql-connector-python
```

## Krok 3: Najít soubory mob_proto.txt a mob_names.txt

```bash
# Najít soubory na serveru
find /home -name "mob_proto.txt" 2>/dev/null
find /home -name "mob_names.txt" 2>/dev/null

# Pravděpodobné cesty:
# /home/serverfiles/main/srv1/share/conf/mob_proto.txt
# /usr/metin2/share/conf/mob_proto.txt
# /root/server_files/share/conf/mob_proto.txt
```

## Krok 4: Spustit import

### Možnost A: Zkopírovat skript k souborům (JEDNODUŠŠÍ)

```bash
# Zkopírovat skript do adresáře se soubory
cp /root/import_mob_proto_to_db.py /home/serverfiles/main/srv1/share/conf/

# Přejít tam
cd /home/serverfiles/main/srv1/share/conf/

# Spustit import
python3 import_mob_proto_to_db.py \
    mob_proto.txt \
    mob_names.txt \
    --host localhost \
    --user root \
    --password VASE_HESLO \
    --database srv1_common
```

### Možnost B: Použít plné cesty

```bash
# Spustit odkudkoliv s plnými cestami
python3 /root/import_mob_proto_to_db.py \
    /home/serverfiles/main/srv1/share/conf/mob_proto.txt \
    /home/serverfiles/main/srv1/share/conf/mob_names.txt \
    --host localhost \
    --user root \
    --password VASE_HESLO \
    --database srv1_common
```

## Krok 5: Zkontrolovat výsledek

```bash
# Přihlásit se do MySQL
mysql -u root -p srv1_common

# V MySQL konzoli
SELECT COUNT(*) FROM mob_proto;
SELECT vnum, name, level, type FROM mob_proto LIMIT 10;
exit;
```

## Kompletní příklad - kopírování z GitHubu

```bash
# 1. Připojit se k serveru
ssh root@VAS_SERVER

# 2. Stáhnout skript
cd /tmp
wget https://raw.githubusercontent.com/delamvec/SF2/claude/fix-mob-proto-import-hupq7/import_mob_proto_to_db.py

# 3. Nainstalovat prerekvizity
pip3 install mysql-connector-python

# 4. Najít soubory
find /home -name "mob_proto.txt" 2>/dev/null

# 5. Přejít do adresáře se soubory (upravte cestu)
cd /home/serverfiles/main/srv1/share/conf/

# 6. Zkopírovat skript tam
cp /tmp/import_mob_proto_to_db.py .

# 7. Spustit import (zadejte své heslo)
python3 import_mob_proto_to_db.py \
    mob_proto.txt \
    mob_names.txt \
    --host localhost \
    --user root \
    --password VASE_HESLO \
    --database srv1_common

# 8. Zkontrolovat výsledek
mysql -u root -p srv1_common -e "SELECT COUNT(*) FROM mob_proto;"
```

## Řešení problémů na serveru

### Python3 není nainstalován

```bash
# Debian/Ubuntu
apt-get update
apt-get install python3 python3-pip -y

# CentOS/RHEL
yum install python3 python3-pip -y
```

### pip3 nefunguje

```bash
# Debian/Ubuntu
apt-get install python3-pip -y

# CentOS/RHEL
yum install python3-pip -y

# Nebo použít easy_install
easy_install-3 pip
```

### MySQL connector se nenainstaluje

```bash
# Zkusit přes apt (Debian/Ubuntu)
apt-get install python3-mysql.connector -y

# Nebo
pip3 install --user mysql-connector-python
```

### Chyba: "Permission denied"

```bash
# Dát oprávnění ke spuštění
chmod +x import_mob_proto_to_db.py

# Nebo zkontrolovat oprávnění k souborům
chmod 644 mob_proto.txt mob_names.txt
```

### Databáze neexistuje

```bash
# Vytvořit databázi
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS srv1_common;"

# Nebo importovat strukturu z mob_proto.sql
mysql -u root -p srv1_common < mob_proto.sql
```

## Tipy

1. **Zálohujte databázi před importem**:
   ```bash
   mysqldump -u root -p srv1_common mob_proto > mob_proto_backup.sql
   ```

2. **Smazat staré záznamy před importem**:
   ```bash
   mysql -u root -p srv1_common -e "TRUNCATE TABLE mob_proto;"
   ```

3. **Import v noci** (pokud je databáze velká):
   ```bash
   nohup python3 import_mob_proto_to_db.py mob_proto.txt mob_names.txt \
       --password HESLO --database srv1_common > import.log 2>&1 &

   # Sledovat progress
   tail -f import.log
   ```

4. **Testovací import** (jen prvních 10 řádků):
   ```bash
   # Vytvořit testovací soubor
   head -11 mob_proto.txt > mob_proto_test.txt  # +1 pro hlavičku

   # Importovat test
   python3 import_mob_proto_to_db.py \
       mob_proto_test.txt \
       mob_names.txt \
       --password HESLO \
       --database srv1_common
   ```

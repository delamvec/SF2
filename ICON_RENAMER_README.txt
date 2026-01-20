================================================================================
                    Icon Renamer - Návod k použití
================================================================================

Tento script přejmenuje ikony itemů podle změn vnum mezi starou a novou databází.


POTŘEBUJEŠ:
-----------
1. OLDVNUM.csv - CSV soubor se starými vnumy
2. NEWVNUM.csv - CSV soubor s novými vnumy
3. icons\ - složka s ikonami (*.tga, *.dds, *.png, atd.)


INSTALACE:
----------
1. Stáhni soubory z gitu:
   cd C:\Users\StevieKL\Desktop\Pytohn\SF2
   git pull origin claude/investigate-mysql-export-eCVj3

2. Zkopíruj do pracovní složky:
   cd ..
   copy SF2\rename_icons.py rename_icons.py
   copy SF2\rename_icons.bat rename_icons.bat
   copy SF2\OLDVNUM.csv OLDVNUM.csv
   copy SF2\NEWVNUM.csv NEWVNUM.csv


POUŽITÍ:
--------
1. Vytvoř složku "icons":
   mkdir icons

2. Zkopíruj všechny ikony do složky icons\
   (Soubory typu: 1400.tga, 1401.tga, atd.)

3. Spusť script:
   - Dvakrát klikni na rename_icons.bat
   NEBO
   - python rename_icons.py

4. Script udělá:
   - Načte staré a nové vnumy z CSV
   - Najde +0 itemy (ty mají ikonu)
   - Vytvoří mapování: starý_vnum -> nový_vnum
   - Přejmenuje ikony
   - Vytvoří backup do icons\backup\
   - Vytvoří rename_log.txt s detailním logem


PŘÍKLAD:
--------
Starý vnum:  1400 = Stinovy mec duchu+0
Nový vnum:  23090 = Stinovy mec duchu+0

Ikona:
  PŘED:  icons\1400.tga
  PO:    icons\23090.tga
  BACKUP: icons\backup\1400.tga


VÝSTUP:
-------
- icons\            - přejmenované ikony
- icons\backup\     - záloha původních ikon
- rename_log.txt    - detailní log o všech změnách


CO SCRIPT DĚLÁ:
---------------
1. Načte OLDVNUM.csv a NEWVNUM.csv
2. Najde všechny +0 itemy (ty mají ikonu)
3. Porovná názvy itemů mezi starou a novou verzí
4. Vytvoří mapování změn vnum
5. Pro každý změněný vnum:
   - Najde ikonu (1400.tga, 1400.dds, atd.)
   - Vytvoří backup
   - Přejmenuje na nový vnum (23090.tga)
6. Zapíše log do rename_log.txt


POZNÁMKY:
---------
- Script hledá ikony s různými příponami (.tga, .dds, .png, .jpg)
- Přejmenuje JEN +0 itemy (protože ikona je jen jedna)
- +1, +2, +3... se nepřejmenovávají (sdílí ikonu s +0)
- Vždy vytvoří backup do icons\backup\
- Pokud ikona není nalezena, zapíše to do logu


TROUBLESHOOTING:
----------------
Q: "OLDVNUM.csv not found"
A: Zkopíruj OLDVNUM.csv do stejné složky jako script

Q: "icons\ folder not found"
A: Vytvoř složku icons\ a dej do ní ikony

Q: "No changes detected"
A: Všechny vnumy jsou stejné, není co měnit

Q: Script přejmenoval jen některé ikony
A: Zkontroluj rename_log.txt - tam je seznam těch co nebyly nalezeny


PŘÍKLAD LOGU (rename_log.txt):
-------------------------------
Icon Rename Log
================================================================================

[OK] 1400 -> 23090: 1400.tga -> 23090.tga
[OK] 1410 -> 23100: 1410.tga -> 23100.tga
[NOT FOUND] 1420 -> 23110 (no icon file found)
[OK] 1430 -> 23120: 1430.dds -> 23120.dds

================================================================================
Summary:
  Total mappings: 150
  Successfully renamed: 148
  Not found: 2


KONTAKT:
--------
Pokud máš problém, pošli:
1. rename_log.txt
2. Screenshot chyby
3. První 10 řádků z OLDVNUM.csv a NEWVNUM.csv


================================================================================

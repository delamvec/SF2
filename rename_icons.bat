@echo off
REM Icon Renamer for Metin2 Items

echo ========================================
echo  Icon Renamer for Metin2 Items
echo ========================================
echo.
echo Tento script prejmenuje ikony podle zmeny vnum.
echo.
echo Potrebujes:
echo  1. OLDVNUM.csv (stare vnumy)
echo  2. NEWVNUM.csv (nove vnumy)
echo  3. icons\ slozku s ikonami
echo.
echo Vytvorit slozku icons? (Y/N)
set /p create_folder=

if /i "%create_folder%"=="Y" (
    mkdir icons 2>nul
    echo Slozka icons vytvorena!
    echo.
    echo Zkopiruj ikony do slozky icons\ a spust tento script znovu.
    echo.
    pause
    exit
)

if not exist icons (
    echo.
    echo CHYBA: Slozka icons\ neexistuje!
    echo Vytvor ji a vloz do ni ikony.
    echo.
    pause
    exit
)

if not exist OLDVNUM.csv (
    echo.
    echo CHYBA: OLDVNUM.csv nenalezen!
    echo.
    pause
    exit
)

if not exist NEWVNUM.csv (
    echo.
    echo CHYBA: NEWVNUM.csv nenalezen!
    echo.
    pause
    exit
)

echo Spoustim prejmenovani...
echo.

python rename_icons.py

echo.
echo ========================================
echo Hotovo!
echo ========================================
echo.
echo Zkontroluj:
echo  - rename_log.txt (log o zmenach)
echo  - icons\backup\ (zaloha puvodních ikon)
echo  - icons\ (prejmenovane ikony)
echo.
pause

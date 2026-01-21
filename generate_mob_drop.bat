@echo off
REM Mob Drop Item Generator for Metin2

echo ========================================
echo  Mob Drop Item Generator
echo ========================================
echo.

if not exist mob_names.txt (
    echo CHYBA: mob_names.txt nenalezen!
    echo.
    echo Zkus tyto alternativni nazvy:
    echo  - mob_names.txt
    echo  - mob_names
    echo  - mobnames.txt
    echo.
    pause
    exit
)

echo Generuji mob_drop_item.txt...
echo.

python generate_mob_drop.py

if exist mob_drop_item.txt (
    echo.
    echo ========================================
    echo Hotovo!
    echo ========================================
    echo.
    echo mob_drop_item.txt byl vytvoren.
    echo Zkopiruj ho do serveru (share/locale/cz/).
    echo.
) else (
    echo.
    echo CHYBA: mob_drop_item.txt nebyl vytvoren!
    echo.
)

pause

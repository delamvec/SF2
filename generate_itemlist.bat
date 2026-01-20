@echo off
REM ItemList Generator for Metin2

echo ========================================
echo  ItemList Generator for Metin2
echo ========================================
echo.

if not exist NEWVNUM.csv (
    echo CHYBA: NEWVNUM.csv nenalezen!
    echo.
    pause
    exit
)

echo Generuji itemlist.txt...
echo.

python generate_itemlist.py

if exist itemlist.txt (
    echo.
    echo ========================================
    echo Hotovo!
    echo ========================================
    echo.
    echo itemlist.txt byl vytvoren.
    echo Zkopiruj ho do klienta.
    echo.
) else (
    echo.
    echo CHYBA: itemlist.txt nebyl vytvoren!
    echo.
)

pause

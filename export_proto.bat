@echo off
REM Export item_proto a mob_proto z MySQL databaze

cd /d C:\Users\StevieKL\Desktop\Pytohn
echo ========================================
echo  MySQL to Proto Exporter
echo ========================================
echo.
echo Spoustim export...
echo.

python mysql2proto_fixed.py -pim

echo.
echo ========================================
echo Export dokoncen!
echo.
echo Soubory byly vytvořeny:
echo  - item_proto
echo  - mob_proto
echo.
echo Zkopiruj je do složky klienta.
echo ========================================
echo.
pause

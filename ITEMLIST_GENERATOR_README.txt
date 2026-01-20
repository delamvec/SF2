================================================================================
                ItemList Generator - Návod k použití
================================================================================

Tento script vygeneruje itemlist.txt pro nové itemy z NEWVNUM.csv.


POTŘEBUJEŠ:
-----------
1. NEWVNUM.csv - CSV soubor s novými vnumy (včetně type a subtype sloupců)


CO SCRIPT DĚLÁ:
---------------
1. Načte NEWVNUM.csv
2. Najde všechny +0 itemy (končí na '+0')
3. Pro každý +0 item vytvoří 10 řádků (+0 až +9)
4. Formát závisí na typu itemu:

   WEAPON (type=0-5):
   7100    WEAPON    icon/item/07100.tga    d:/ymir work/item/weapon/07100.gr2
   7101    WEAPON    icon/item/07100.tga    d:/ymir work/item/weapon/07100.gr2
   ... (celkem 10 řádků)

   ARMOR (type=2):
   11640   ARMOR     icon/item/11640.tga
   11641   ARMOR     icon/item/11640.tga
   ... (celkem 10 řádků)

   ETC (ostatní):
   10520   ETC       icon/item/10520.tga
   10521   ETC       icon/item/10520.tga
   ... (celkem 10 řádků)


POUŽITÍ:
--------
1. Stáhni soubory z gitu:
   cd C:\Users\StevieKL\Desktop\Pytohn\SF2
   git pull origin claude/investigate-mysql-export-eCVj3

2. Zkopíruj do pracovní složky:
   cd ..
   copy SF2\generate_itemlist.py .
   copy SF2\generate_itemlist.bat .
   copy SF2\NEWVNUM.csv .

3. Spusť script:
   - Dvakrát klikni na generate_itemlist.bat
   NEBO
   - python generate_itemlist.py

4. Výstup:
   - itemlist.txt


DŮLEŽITÉ:
---------
- Všechny +1 až +9 itemy sdílí STEJNOU IKONU jako +0
- Ikona se vždy odkazuje na +0 vnum (např. všechny 7100-7109 používají 07100.tga)
- WEAPON itemy mají navíc .gr2 model path
- ARMOR a ETC mají jen ikonu


PŘÍKLAD:
--------
Input (NEWVNUM.csv):
23090,Stinovy mec duchu+0,St�nov� me� duch� +0,1,0,...
23091,Stinovy mec duchu+1,St�nov� me� duch� +1,1,0,...
...

Output (itemlist.txt):
23090   WEAPON  icon/item/23090.tga     d:/ymir work/item/weapon/23090.gr2
23091   WEAPON  icon/item/23090.tga     d:/ymir work/item/weapon/23090.gr2
23092   WEAPON  icon/item/23090.tga     d:/ymir work/item/weapon/23090.gr2
...
23099   WEAPON  icon/item/23090.tga     d:/ymir work/item/weapon/23090.gr2


TYPY ITEMŮ:
-----------
Type 0 = Jednoruční meč (WEAPON)
Type 1 = Dýka (WEAPON)
Type 2 = Luk (WEAPON)
Type 3 = Zvon (WEAPON)
Type 4 = Vějíř (WEAPON)
Type 5 = Dvouruční meč (WEAPON)
Type 2 = Brnění (ARMOR) - pozor, type 2 může být bow nebo armor!
Type 16+ = Ostatní (ETC)


TROUBLESHOOTING:
----------------
Q: "NEWVNUM.csv not found"
A: Zkopíruj NEWVNUM.csv do stejné složky jako script

Q: "No items loaded"
A: Zkontroluj že NEWVNUM.csv má správný formát (CSV s comma separator)

Q: itemlist.txt je prázdný
A: Zkontroluj že NEWVNUM.csv obsahuje itemy končící na '+0'


FORMÁT VÝSTUPU:
---------------
[vnum]<TAB>[type]<TAB>[icon_path]<TAB>[model_path]

- vnum: číslo itemu (7100, 7101, ...)
- type: WEAPON, ARMOR nebo ETC
- icon_path: cesta k ikoně (vždy +0 vnum)
- model_path: (jen u WEAPON) cesta k 3D modelu


================================================================================

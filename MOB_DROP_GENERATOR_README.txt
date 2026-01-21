================================================================================
                Mob Drop Item Generator - Návod k použití
================================================================================

Tento script vygeneruje mob_drop_item.txt z mob_names souboru.


POTŘEBUJEŠ:
-----------
1. mob_names.txt - soubor s čísly a jmény mobů


CO SCRIPT DĚLÁ:
---------------
1. Přečte mob_names.txt
2. Pro každého moba vytvoří Group blok v mob_drop_item.txt
3. Odstraní české znaky (diakritiku) z názvů
4. Nahradí mezery podtržítkem (_)


FORMÁT VÝSTUPU:
---------------
Group   Silny_Vlk
{
        Mob     103
        Type    drop

}

Group   Cerny_Medved
{
        Mob     104
        Type    drop

}


POUŽITÍ:
--------
1. Stáhni soubory z gitu:
   cd C:\Users\StevieKL\Desktop\Pytohn\SF2
   git pull origin claude/investigate-mysql-export-eCVj3

2. Zkopíruj do pracovní složky:
   cd ..
   copy SF2\generate_mob_drop.py .
   copy SF2\generate_mob_drop.bat .

3. Zkopíruj mob_names.txt do stejné složky

4. Spusť script:
   - Dvakrát klikni na generate_mob_drop.bat
   NEBO
   - python generate_mob_drop.py

5. Výstup:
   - mob_drop_item.txt


FORMÁT mob_names.txt:
---------------------
Soubor může být ve formátu:
103     Silný Vlk
104     Černý Medvěd
105     Ohnivý Démon
...

Nebo s tabulátorem:
103<TAB>Silný Vlk
104<TAB>Černý Medvěd
...


ODSTRANĚNÍ ČESKÝCH ZNAKŮ:
--------------------------
Script automaticky převede:

á → a    Á → A
č → c    Č → C
ď → d    Ď → D
é → e    É → E
ě → e    Ě → E
í → i    Í → I
ň → n    Ň → N
ó → o    Ó → O
ř → r    Ř → R
š → s    Š → S
ť → t    Ť → T
ú → u    Ú → U
ů → u    Ů → U
ý → y    Ý → Y
ž → z    Ž → Z


PŘÍKLADY TRANSFORMACE:
----------------------
Silný Vlk           → Silny_Vlk
Černý Medvěd        → Cerny_Medved
Ohnivý Démon        → Ohnivy_Demon
Ledový Škorpión     → Ledovy_Skorpion
Kamenný Golem       → Kamenny_Golem
Ďábelský Rytíř      → Dabelsky_Rytir


DŮLEŽITÉ:
---------
- Mezery se nahradí podtržítkem (_)
- České znaky se odstraní (čárky, háčky)
- Ostatní speciální znaky se odstraní
- Výsledek je použitelný v konfiguračních souborech serveru


KDE POUŽÍT:
-----------
Vygenerovaný mob_drop_item.txt zkopíruj do:
- Server: share/locale/cz/mob_drop_item.txt
- Nebo: locale/cz/mob_drop_item.txt


TROUBLESHOOTING:
----------------
Q: "mob_names.txt not found"
A: Zkopíruj mob_names.txt do stejné složky jako script

Q: "No mobs loaded"
A: Zkontroluj formát mob_names.txt - měl by být vnum<TAB>název

Q: Některé moba chybí
A: Zkontroluj že mob_names.txt obsahuje všechny moby

Q: Znaky stále obsahují diakritiku
A: Zkontroluj že používáš nejnovější verzi scriptu

Q: Písmena zmizí (např. "Divok_pes" místo "Divoky_pes")
A: Script automaticky detekuje správné kódování souboru (UTF-8, CP1250, atd.)
   Pokud problém přetrvává, zkus uložit mob_names.txt jako UTF-8


KÓDOVÁNÍ SOUBORŮ:
-----------------
Script automaticky detekuje správné kódování mob_names.txt:
- Zkouší UTF-8, CP1250, Windows-1250, ISO-8859-2
- Ověřuje že dekódovaný text nedělá nesmysly
- Používá první kódování které dává správné výsledky

Podporovaná kódování:
- UTF-8 (doporučeno pro nové soubory)
- Windows-1250 / CP1250 (staré české soubory)
- ISO-8859-2 (méně časté)


PŘÍKLAD mob_names.txt:
----------------------
101     Modrý Vlk
102     Žlutý Pes
103     Silný Vlk
104     Černý Medvěd
105     Ohnivý Démon
106     Ledový Škorpión
107     Kamenný Golem
108     Ďábelský Rytíř
109     Divoký Kanec
110     Zuřivý Orel


PŘÍKLAD VÝSTUPU:
----------------
Group   Modry_Vlk
{
        Mob     101
        Type    drop

}

Group   Zluty_Pes
{
        Mob     102
        Type    drop

}

Group   Silny_Vlk
{
        Mob     103
        Type    drop

}

... atd.


================================================================================

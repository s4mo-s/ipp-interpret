## Implementačná dokumentácia k 2. úlohe do IPP 2021/2022
Jméno a příjmení: `Samuel Šulo`  
Login: `xsulos00`

### Interpret XML reprezentácie kódu
Skript načíta XML reprezentáciu programu, ktorý s využitím vstupu podľa parametrov v príkazovej riadke interpretuje a generuje výstup.
Kontroluje výskyty parametrov:  
``--help``: vypisuje na štandardný výstup nápovedu skriptu.  
``--source=file``: vstupný súbor s XML reprezentáciou zdrojového kódu.  
``--input=file``: súbor so vstupmi pre samotnú interpretáciu, ak parameter nieje zadaný tak načíta štandardný vstup.  

## Implementácia
### Center.py
Má na starosti celý beh programu, konkrétne metóda start(), na začiatok prejde cez všetky labely, skontroluje či sa nerovnajú ich mená 
a uloží ich do dictionary kde kľúč je meno labelu a hodnota order number inštrukcie. Potom nastaví inštrukcie do správneho poradia a 
metóda `exec()` ich postupne po jednej spracuje. Spočíta počet argumentov danej inštrukcie ktorú následne porovnáva s opcodmi.

```define()``` metódu volá inštrukcia DEFVAR. Definuje premennú na danom rámci bez inicializácie.  
```set_value()``` metóda nastaví hodnoty definovaným premenným v daných rámcoch.  
```get_value()``` metóda je volaná pre získanie hodnoty argumentu, ak sa jedná o variable tak porovná rámce a načíta jej hodnotu z 
vybraného rámca, ak sa nejedná o variable tak vráti nemenenú hodnotu.  
```get_tmp_frame()``` vráti dočasný rámec ak nejaký existuje.  
```get_local_frame()``` vráti lokálny rámec ak nejaký existuje.  

### XmlControl.py
Prejde cez celú XML reprezentáciu kódu načítaného zo vstupného source súboru a skontroluje formát. Pomocou regex výrazov taktiež skontroluje hodnoty 
argumentov na základe ich typu.

### CommandLine.py
Skontroluje parametre na príkazovej riadke a načíta prípadné vstupné súbory.

### class Argument
Skontroluje argument danej inštrukcie a priradí mu jeho hodnotu, ak sa jedná o var tak jej priradí aj jej rámec.


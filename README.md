# Dokumentace k úkolu 2

Cílem tohoto programu je zjistit dostupnost kontejnerů na tříděný odpad v dané čtvrti, a to tak, že se vypočítá průměr, medián a maximum vzdálenosti jednotlivých adresních bodů k nejbližšímu veřejně přístupnému kontejneru.



## Vstup

Program pracuje se souborem `adresy.geojson`, který by měl obsahovat:

- adresní body dané čtvrti ve formátu WGS-84,
- klíče `addr:street` a `addr:housenumber` pro identifikaci jednotlivých adres.

Dále je potřeba mít soubor `kontejnery.geojson`, ve kterém by měly být zahrnuty:

- souřadnice kontejnerů na tříděný odpad ve formátu S-JTSK,
- atribut `STATIONNAME` pro identifikaci místa 
- a atribut `PRISTUP` pro zjištění přístupnosti kontejneru.

V repozitáři tohoto projektu lze naleznout dva malé soubory s body v okolí Letňan – adresy byly vygenerované na stránce [Overpass Turbo](http://overpass-turbo.eu/s/119J) a souřadnice kontejnerů stažené z [pražského Geoportálu](https://www.geoportalpraha.cz/cs/data/otevrena-data/8726EF0E-0834-463B-9E5F-FE09E62D73FB). Tyto soubory by měly sloužit pouze k testovacím účelům a také pro představu, jak by příslušná data měla vypadat. Obsahují totiž nesprávné údaje, pomocí kterých je demonstrována schopnost zachytit tyto chyby.



## Výstup

Program vypíše počet načtených unikátních adresních bodů dané čtvrti, počet volně přístupných kontejnerů, průměrnou vzdálenost adresního bodu k nejbližšímu veřejnému kontejneru, medián této vzdálenosti a nakonec adresu nejvzdálenějšího bodu včetně příslušné hodnoty.

Všechny vzdálenosti jsou uváděny v metrech a pokud jeden z adresních bodů bude vzdálen od nejbližšího kontejneru více než 10 000 metrů, program tuto skutečnost nahlásí a ukončí se.

Níže je možné vidět příkladný výstup pro čtvrť Staré Město a kompletní dataset pražských kontejnerů ze 17.12.2020:

```
Upozorneni: bylo vyrazeno 2 adresnich bodu kvuli chybejicimu klici.
Nacteno 1633 unikatnich adresnich bodu.
Nacteno 3441 kontejneru na trideny odpad.

Prumerna vzdalenost adresniho bodu k verejnemu kontejneru: 136 metru.
Median vzdalenosti ke kontejneru: 129 metru.
Nejdelsi vzdalenost ke kontejnerum je z adresy 'Na příkopě 1096/19' a to 323 metru.
```


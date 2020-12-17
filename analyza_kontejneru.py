import json
from math import sqrt
from pyproj import CRS, Transformer


# definice pro prevod

crs_wgs = CRS.from_epsg(4326)  # WGS-84
crs_jtsk = CRS.from_epsg(5514)  # S-JTSK

wgs2jtsk = Transformer.from_crs(crs_wgs, crs_jtsk)

# https://www.estudanky.eu/prevody/jtsk.php

jtsk = wgs2jtsk.transform(50, 15)  # sirka, delka

print(jtsk)

jtsk2wgs = Transformer.from_crs(crs_jtsk, crs_wgs)

print(jtsk2wgs.transform(*jtsk))

# loadovani dat

with open("stare_mesto_small.geojson", "r", encoding="UTF-8") as file:
    adresy = json.load(file)

adresy_info = adresy["features"]

with open("kontejnery_small.geojson", "r", encoding="UTF-8") as file:
    kont = json.load(file)

kont_info = kont["features"]


# jtsk souradnice kontejneru
print(kont_info[2]["geometry"]["coordinates"])
# adresa kontejneru
print(kont_info[2]["properties"]["STATIONNAME"])
# dostupnost kontejneru
print(kont_info[2]["properties"]["PRISTUP"])

# ulice
print(adresy_info[2]["properties"]["addr:street"])
# cislo popisne
print(adresy_info[2]["properties"]["addr:housenumber"])
# kombinace ulice a cp hazi unikatni adresni body

# wgs souradnice adresy
print(adresy_info[2]["geometry"]["coordinates"])

jtsk_adresy = wgs2jtsk.transform(adresy_info[2]["geometry"]["coordinates"][1],
                                 adresy_info[2]["geometry"]["coordinates"][0])

print(jtsk_adresy[1])


# vzdalenost
jtsk_kont = kont_info[4]["geometry"]["coordinates"]

odvesna1 = abs(jtsk_kont[0] - jtsk_adresy[0])
odvesna2 = abs(jtsk_kont[1] - jtsk_adresy[1])

vzdalenost = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))  # v metrech
print(vzdalenost)

# TODO přiřadit každé adrese nejbližší kontejner
# z těchto dvojic zjistit průměr a maximum
# vyplatí se to házet do dvojic (asi slovník), protože pak budu volat nejdelší
# vzdálenost


# vybudovani slovniku kontejneru adresa : souradnice x y

# TODO přidat nějaký check, kdyby to nebyl float (pak skip)
# TODO pomocí xlsx souborů najít divný hodnoty typu missing

slovnik_kont = {}

for i in range(len(kont_info)):
    # osetreni chybejicich klicu
    try:
        kont_ulice_cp = kont_info[i]["properties"]["STATIONNAME"]
        kont_souradnice = kont_info[i]["geometry"]["coordinates"]
        kont_pristup = kont_info[i]["properties"]["PRISTUP"]
    except KeyError:
        continue
    
    if kont_pristup == "volně":
        slovnik_kont[kont_ulice_cp] = kont_souradnice


# pokud je slovnik_kont prazdny, vypni program
if len(slovnik_kont) == 0:
    print("V souboru s kontejnery neni zadny volny kontejner."
          "Program se ukonci")
    exit(0)
    

# vybudovani slovniku adres adresa : souradnice x y

slovnik_adresy = {}

for j in range(len(adresy_info)):
    # osetreni chybejicich klicu
    try:
        adresa_cp = adresy_info[j]["properties"]["addr:housenumber"]
        adresa_ulice = adresy_info[j]["properties"]["addr:street"]
        adresa_sirka = adresy_info[j]["geometry"]["coordinates"][1]
        adresa_delka = adresy_info[j]["geometry"]["coordinates"][0]
    except KeyError:
        continue
    
    adresa_jtsk = wgs2jtsk.transform(adresa_sirka, adresa_delka)
    # ulice mezera cislo popisne
    adresa_ulice_cp = adresa_ulice + " " + adresa_cp
    
    # budovani slovniku
    slovnik_adresy[adresa_ulice_cp] = adresa_jtsk

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

with open("kontejnery_small.json", "r", encoding="UTF-8") as file:
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

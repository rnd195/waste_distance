import json
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

import json
from math import sqrt
from statistics import mean, median
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

with open("stare_mesto.geojson", "r", encoding="UTF-8") as file:
    adresy = json.load(file)

adresy_info = adresy["features"]

with open("kontejnery.geojson", "r", encoding="UTF-8") as file:
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


# hledani nejmensi vzdalenosti pro danou adresu

slovnik_adresy_minkont = {}

for (klic_adresy, hodnota_adresy) in slovnik_adresy.items():
    x_1 = hodnota_adresy[0]
    y_1 = hodnota_adresy[1]

    docasny_seznam = []

    for hodnota_kont in slovnik_kont.values():
        x_2 = hodnota_kont[0]
        y_2 = hodnota_kont[1]

        # pythagoras
        odvesna1 = abs(x_1 - x_2)
        odvesna2 = abs(y_1 - y_2)
        prepona = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))

        docasny_seznam.append(prepona)

    min_vzdalenost = min(docasny_seznam)

    slovnik_adresy_minkont[klic_adresy] = min_vzdalenost


# TODO def prumer
mean(slovnik_adresy_minkont.values())
prumer_m = sum(slovnik_adresy_minkont.values()) / len(slovnik_adresy_minkont)

# TODO premistit nahoru


def median_slovnik(slovnik):
    seznam = list(slovnik.values())
    seznam.sort()
    n = len(seznam)
    pozice = (n - 1) // 2

    if n % 2:
        return seznam[pozice]

    return (seznam[pozice] + seznam[pozice + 1]) / 2


median_m = median_slovnik(slovnik_adresy_minkont)
median_kontrola = median(slovnik_adresy_minkont.values())

max_m = max(slovnik_adresy_minkont.values())

for (klic, hodnota) in slovnik_adresy_minkont.items():
    if hodnota == max_m:
        max_adresa = klic

print(f"Nacteno {len(slovnik_adresy)} adresnich bodu.")
print(f"Nacteno {len(slovnik_kont)} kontejneru na trideny odpad.")

print("\n"
      "Prumerna vzdalenost adresniho bodu ke kontejneru je "
      f"{prumer_m:.0f} metru.")
print(f"Median je {median_m:.0f} metru.")
print(f"Nejdelsi vzdalenost ke kontejnerum je z adresy {max_adresa} "
      f"a to {max_m:.0f} metru.")

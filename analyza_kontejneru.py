import json
import os
from sys import exit
from math import sqrt
from pyproj import CRS, Transformer

# from statistics import mean, median  # na kontrolu prumeru a medianu


def prumer_slovnik(slovnik):
    """Vypocita prumer hodnot jednoducheho slovniku."""
    prumer = sum(slovnik.values()) / len(slovnik)
    return prumer


def median_slovnik(slovnik):
    """Vypocita median jednoducheho slovniku."""
    seznam = list(slovnik.values())
    seznam.sort()
    n = len(seznam)
    pozice = (n - 1) // 2

    # Pokud je zbytek po deleni 0 => False, pokud je 1 => True
    if n % 2:
        return seznam[pozice]

    return (seznam[pozice] + seznam[pozice + 1]) / 2


# DEFINICE PRO PREVOD SOURADNIC

crs_wgs = CRS.from_epsg(4326)  # WGS-84
crs_jtsk = CRS.from_epsg(5514)  # S-JTSK
# Konvertovani souradnic z wgs do jtsk formatu
wgs2jtsk = Transformer.from_crs(crs_wgs, crs_jtsk)


# NACITANI DAT

# Nastavi pracovni adresar na filepath
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Pokud soubor chybi nebo je vadny, vypni program
try:
    with open("adresy.geojson", "r", encoding="UTF-8") as file:
        adresy = json.load(file)
# ValueError zahrnuje JSONDecodeError
except (FileNotFoundError, NameError, ValueError):
    print(
        "Soubor adresy.geojson neexistuje nebo je chybny. Program se ukonci."
    )
    exit()

adresy_info = adresy["features"]

# Pokud je soubor adres delky 0 (validni, ale prazdny), vypnu program
if len(adresy_info) == 0:
    print("Soubor s adresami je prazdny. Program se ukonci.")

try:
    with open("kontejnery.geojson", "r", encoding="UTF-8") as file:
        kont = json.load(file)
except (FileNotFoundError, NameError, ValueError):
    print(
        "Soubor kontejnery.geojson neexistuje nebo je chybny. "
        "Program se ukonci."
    )
    exit()

kont_info = kont["features"]


# SLOVNIK VEREJNYCH KONTEJNERU

# Vytvori se slovnik s unikatnim klicem ulice a cisla popisneho,
# kde hodnoty daneho slovniku jsou souradnice.

slov_kont = {}

for i in range(len(kont_info)):
    # Osetreni chybejicich klicu
    try:
        kont_ulice_cp = kont_info[i]["properties"]["STATIONNAME"]
        kont_souradnice = kont_info[i]["geometry"]["coordinates"]
        kont_pristup = kont_info[i]["properties"]["PRISTUP"]
    except KeyError:
        continue

    # Zapisuje do slovniku pouze volne pristupne kontejnery
    if kont_pristup == "volně":
        slov_kont[kont_ulice_cp] = kont_souradnice


# Pokud nejsou v souboru zadne volne kontejnery, vypni program.
# Zde se zachyti i pripadny prazdny geojson s kontejnery (netreba duplikovat).
if len(slov_kont) == 0:
    print(
        "V souboru s kontejnery neni zadny volne pristupny. Program se ukonci"
    )
    exit()


# SLOVNIK ADRESNICH BODU

slov_adresy = {}

# Vytvori slovnik adresnich bodu s prevedenymi jtsk souradnicemi
for j in range(len(adresy_info)):
    try:
        adresa_cp = adresy_info[j]["properties"]["addr:housenumber"]
        adresa_ulice = adresy_info[j]["properties"]["addr:street"]
        # Souradnice jsou prehozene v souboru s adresami
        adresa_sirka = adresy_info[j]["geometry"]["coordinates"][1]
        adresa_delka = adresy_info[j]["geometry"]["coordinates"][0]
    except KeyError:
        continue

    # Prevod wgs souradnic na jtsk format
    adresa_jtsk = wgs2jtsk.transform(adresa_sirka, adresa_delka)

    adresa_ulice_cp = adresa_ulice + " " + adresa_cp
    slov_adresy[adresa_ulice_cp] = adresa_jtsk


# HLEDANI NEJMENSI VZDALENOSTI PRO DANOU ADRESU

slov_adresy_minkont = {}

for (klic_adresy, hodnota_adresy) in slov_adresy.items():
    # Souradnice adresniho bodu
    x_1 = hodnota_adresy[0]
    y_1 = hodnota_adresy[1]

    docasny_seznam = []

    for hodnota_kont in slov_kont.values():
        # Souradnice kontejneru
        x_2 = hodnota_kont[0]
        y_2 = hodnota_kont[1]

        # Pomoci Pythagorovy vety vypocte vzdalenost v metrech (prepona)
        odvesna1 = abs(x_1 - x_2)
        odvesna2 = abs(y_1 - y_2)
        prepona = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))

        # A vzniknlou vzdalenost prida do seznamu, ve kterem pak hleda min
        docasny_seznam.append(prepona)

    min_vzdalenost = min(docasny_seznam)

    # Osetreni 10km vzdaleneho kontejneru
    if min_vzdalenost > 10000:
        print(
            "Kontejner je prilis daleko. Mate spravna data? "
            "Program se ukonci."
        )
        exit()

    slov_adresy_minkont[klic_adresy] = min_vzdalenost


# PRUMER, MEDIAN A MAXIMUM

# print(mean(slov_adresy_minkont.values()))
prumer_m = prumer_slovnik(slov_adresy_minkont)

# print(median(slov_adresy_minkont.values()))
median_m = median_slovnik(slov_adresy_minkont)

max_m = max(slov_adresy_minkont.values())

# K maximu priradit odpovidajici adresu
for (klic, hodnota) in slov_adresy_minkont.items():
    if hodnota == max_m:
        max_adresa = klic


# FINALNI SOUHRN

print(f"Nacteno {len(slov_adresy)} adresnich bodu.")
print(f"Nacteno {len(slov_kont)} kontejneru na trideny odpad.")

print(
    "\n"
    "Prumerna vzdalenost adresniho bodu k verejnemu kontejneru: "
    f"{prumer_m:.0f} metru."
)
print(f"Median vzdalenosti ke kontejneru: {median_m:.0f} metru.")
print(
    f"Nejdelsi vzdalenost ke kontejnerum je z adresy '{max_adresa}' "
    f"a to {max_m:.0f} metru."
)

input(
    "\n"
    "Stisknete klavesu Enter pro ukonceni programu. "
)

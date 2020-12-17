import json
from math import sqrt
from pyproj import CRS, Transformer
from sys import exit
# from statistics import mean, median  # na kontrolu


def prumer_slovnik(slovnik):
    prumer = sum(slovnik.values()) / len(slovnik)
    return prumer


def median_slovnik(slovnik):
    seznam = list(slovnik.values())
    seznam.sort()
    n = len(seznam)
    pozice = (n - 1) // 2

    if n % 2:
        return seznam[pozice]

    return (seznam[pozice] + seznam[pozice + 1]) / 2


# DEFINICE PRO PREVOD SOURADNIC
crs_wgs = CRS.from_epsg(4326)  # WGS-84
crs_jtsk = CRS.from_epsg(5514)  # S-JTSK
# Konvertovani souradnic z wgs do jtsk formatu
wgs2jtsk = Transformer.from_crs(crs_wgs, crs_jtsk)


# NACITANI DAT
# Pokud soubor chybi nebo je vadny, vypni program
try:
    with open("stare_mesto_small.geojson", "r", encoding="UTF-8") as file:
        adresy = json.load(file)
# ValueError zahrnuje JSONDecodeError
except (FileNotFoundError, NameError, ValueError):
    print("Soubor adresy.geojson neexistuje nebo je chybny. "
          "Program se ukonci.")
    exit()

adresy_info = adresy["features"]

# Pokud mam prazdny seznam adres, vypnu program
if len(adresy_info) == 0:
    print("Soubor s adresami je prazdny.\n"
          "Program se ukonci.")

try:
    with open("kontejnery_small.geojson", "r", encoding="UTF-8") as file:
        kont = json.load(file)
except (FileNotFoundError, NameError, ValueError):
    print("Soubor kontejnery.geojson neexistuje nebo je chybny. "
          "Program se ukonci.")
    exit()

kont_info = kont["features"]


# VYTVARENI SLOVNIKU
# Vytvori se slovnik s unikatnim klicem ulice a cisla popisneho,
# kde hodnoty daneho slovniku jsou souradnice.
slovnik_kont = {}

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
        slovnik_kont[kont_ulice_cp] = kont_souradnice


# Pokud nejsou v souboru zadne volne kontejnery, vypni program
# Zde se zachyti i pripadny prazdny geojson s kontejnery (netreba duplikovat)
if len(slovnik_kont) == 0:
    print("V souboru s kontejnery neni zadny volny kontejner."
          "Program se ukonci")
    exit()

slovnik_adresy = {}

for j in range(len(adresy_info)):
    try:
        adresa_cp = adresy_info[j]["properties"]["addr:housenumber"]
        adresa_ulice = adresy_info[j]["properties"]["addr:street"]
        adresa_sirka = adresy_info[j]["geometry"]["coordinates"][1]
        adresa_delka = adresy_info[j]["geometry"]["coordinates"][0]
    except KeyError:
        continue

    adresa_jtsk = wgs2jtsk.transform(adresa_sirka, adresa_delka)

    adresa_ulice_cp = adresa_ulice + " " + adresa_cp
    slovnik_adresy[adresa_ulice_cp] = adresa_jtsk


# HLEDANI NEJMENSI VZDALENOSTI PRO DANOU ADRESU

slovnik_adresy_minkont = {}

for (klic_adresy, hodnota_adresy) in slovnik_adresy.items():
    # Souradnice adresniho bodu
    x_1 = hodnota_adresy[0]
    y_1 = hodnota_adresy[1]

    docasny_seznam = []

    for hodnota_kont in slovnik_kont.values():
        # Souradnice kontejneru
        x_2 = hodnota_kont[0]
        y_2 = hodnota_kont[1]

        # Pomoci Pythagorovy vety vypocti vzdalenost v metrech (prepona)
        odvesna1 = abs(x_1 - x_2)
        odvesna2 = abs(y_1 - y_2)
        prepona = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))

        # A vzniknlou vzdalenost pridej do seznamu
        docasny_seznam.append(prepona)

    min_vzdalenost = min(docasny_seznam)
    
    # Osetreni 10km vzdaleneho kontejneru
    if min_vzdalenost > 10000:
        print("Kontejner je prilis daleko. Mate spravna data? "
              "Program se ukonci.")
        exit()

    slovnik_adresy_minkont[klic_adresy] = min_vzdalenost


# PRUMER, MEDIAN A MAXIMUM

# print(mean(slovnik_adresy_minkont.values()))
prumer_m = prumer_slovnik(slovnik_adresy_minkont)

# print(median(slovnik_adresy_minkont.values()))
median_m = median_slovnik(slovnik_adresy_minkont)

max_m = max(slovnik_adresy_minkont.values())

for (klic, hodnota) in slovnik_adresy_minkont.items():
    if hodnota == max_m:
        max_adresa = klic


# FINALNI SOUHRN

print(f"Nacteno {len(slovnik_adresy)} adresnich bodu.")
print(f"Nacteno {len(slovnik_kont)} kontejneru na trideny odpad.")

print("\n"
      "Prumerna vzdalenost adresniho bodu k verejnemu kontejneru: "
      f"{prumer_m:.0f} metru.")
print(f"Median vzdalenosti ke kontejneru: {median_m:.0f} metru.")
print(f"Nejdelsi vzdalenost ke kontejnerum je z adresy '{max_adresa}' "
      f"a to {max_m:.0f} metru.")

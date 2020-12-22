import json
import os
from sys import exit
from math import sqrt
from pyproj import CRS, Transformer

# from statistics import mean, median  # na kontrolu prumeru a medianu


def nacitani_geojson(jmeno_souboru):
    """Nacte validni geojson soubor. Pri spatnem vstupu vypne program."""
    try:
        with open(jmeno_souboru, "r", encoding="UTF-8") as file:
            soubor = json.load(file)
    except FileNotFoundError:
        print(f"Soubor {jmeno_souboru} neexistuje.")
        exit()
    # ValueError zahrnuje JSONDecodeError
    except ValueError as err:
        print(
            f"Soubor {jmeno_souboru} je chybny.\n",
            err
        )
        exit()
    except NameError as err:
        print(
            "Soubor nebylo mozne nacist. Importovali jste modul json?\n",
            err
        )
        exit()

    if len(jmeno_souboru) == 0:
        print(
            "Soubor je prazdny. "
            "Zkontrolujte, jestli nacitate spravny soubor."
        )
        exit()

    return soubor


def vzdalenost_pythagoras(bod_x1, bod_x2, bod_y1, bod_y2):
    """Vypocita vzdalenost dvou bodu podle Pythagorovy vety."""
    odvesna1 = abs(bod_x1 - bod_x2)
    odvesna2 = abs(bod_y1 - bod_y2)

    prepona = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))

    return prepona


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

adresy_info = nacitani_geojson("adresy.geojson")["features"]
kont_info = nacitani_geojson("kontejnery.geojson")["features"]


# SLOVNIK VEREJNYCH KONTEJNERU

# Vytvori se slovnik s unikatnim klicem ulice a cisla popisneho,
# kde hodnoty daneho slovniku jsou souradnice.

slov_kont = {}
# Osetreni chybejicich klicu
vyrazene_kont = 0

for kontejner in kont_info:
    try:
        kont_ulice_cp = kontejner["properties"]["STATIONNAME"]
        kont_souradnice = kontejner["geometry"]["coordinates"]
        kont_pristup = kontejner["properties"]["PRISTUP"]
    # Zapise, ze chybel klic a pozdeji pripadne nahlasi
    except KeyError:
        vyrazene_kont += 1
        continue

    # Zapisuje do slovniku pouze volne pristupne kontejnery
    if kont_pristup == "volně":
        slov_kont[kont_ulice_cp] = kont_souradnice

if vyrazene_kont > 0:
    print(
        f"Upozorneni: bylo vyrazeno {vyrazene_kont} kontejneru kvuli "
        "chybejicimu klici."
    )


# Pokud nejsou v souboru zadne volne kontejnery, vypni program.
# Zde se zachyti i pripadny prazdny geojson s kontejnery (netreba duplikovat).
if len(slov_kont) == 0:
    print(
        "V souboru s kontejnery neni zadny volne pristupny. Program skonci."
    )
    exit()


# SLOVNIK ADRESNICH BODU

slov_adresy = {}
vyrazene_body = 0

# Vytvori slovnik adresnich bodu s prevedenymi jtsk souradnicemi
for bod in adresy_info:
    try:
        adresa_cp = bod["properties"]["addr:housenumber"]
        adresa_ulice = bod["properties"]["addr:street"]
        # Souradnice jsou prehozene v souboru s adresami
        adresa_sirka = bod["geometry"]["coordinates"][1]
        adresa_delka = bod["geometry"]["coordinates"][0]
    except KeyError:
        vyrazene_body += 1
        continue

    # Prevod wgs souradnic na jtsk format
    adresa_jtsk = wgs2jtsk.transform(adresa_sirka, adresa_delka)

    adresa_ulice_cp = adresa_ulice + " " + adresa_cp
    slov_adresy[adresa_ulice_cp] = adresa_jtsk

if vyrazene_body > 0:
    print(
        f"Upozorneni: bylo vyrazeno {vyrazene_body} adresnich bodu kvuli "
        "chybejicimu klici."
    )


# HLEDANI NEJMENSI VZDALENOSTI PRO DANOU ADRESU

slov_adresy_minkont = {}

for (adresa_bod, souradnice_bod) in slov_adresy.items():
    # Souradnice adresniho bodu
    x_1 = souradnice_bod[0]
    y_1 = souradnice_bod[1]

    docasny_seznam = []

    for adresa_kont in slov_kont.values():
        # Souradnice kontejneru
        x_2 = adresa_kont[0]
        y_2 = adresa_kont[1]

        vzdalenost = vzdalenost_pythagoras(x_1, x_2, y_1, y_2)

        # Vzniknlou vzdalenost prida do seznamu, ve kterem pak hleda min
        docasny_seznam.append(vzdalenost)

    min_vzdalenost = min(docasny_seznam)

    # Osetreni 10km vzdaleneho kontejneru
    if min_vzdalenost > 10000:
        print(
            "Kontejner je prilis daleko. Mate spravna data? "
            "Program se ukonci."
        )
        exit()

    slov_adresy_minkont[adresa_bod] = min_vzdalenost


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

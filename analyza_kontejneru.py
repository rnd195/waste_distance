import json
import os
from sys import exit
from math import sqrt
from pyproj import CRS, Transformer

# from statistics import mean, median  # na kontrolu prumeru a medianu


def nacitani_geojson(jmeno_souboru):
    """Nacte validni geojson soubor. Pokud soubor neexistuje, je chybny nebo
    neni pristupny, da vedet a ukonci program.
    """
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
    except PermissionError:
        print(
            f"Program nema pristup k {jmeno_souboru}.\n",
        )
        exit()

    if len(jmeno_souboru) == 0:
        print(
            "Soubor je prazdny. "
            "Zkontrolujte, jestli nacitate spravny soubor."
        )
        exit()

    return soubor


def slovnik_verejne_kont(konejnery_info):
    """Vytvori slovnik s unikatnim klicem ulice a cisla popisneho, kde hodnoty
    daneho slovniku jsou souradnice. V pripade duplicitnich adres se z
    podstaty slovniku bere v potaz jen 1 adresa. Proto se muze pocet prvku
    vlozeneho slovniku lisit od poctu prvku ve finalnim (novem) slovniku."""

    slovnik_kontejnery = {}
    # Pocitadlo chybejicich klicu - chybi-li klic, pricte 1 a pozdeji upozorni
    vyrazene_kont = 0

    for kontejner in konejnery_info:
        try:
            kont_ulice_cp = kontejner["properties"]["STATIONNAME"]
            kont_souradnice = kontejner["geometry"]["coordinates"]
            kont_pristup = kontejner["properties"]["PRISTUP"]
        except KeyError:
            vyrazene_kont += 1
            continue

        # Zapisuje do slovniku pouze volne pristupne kontejnery
        if kont_pristup == "volně":
            slovnik_kontejnery[kont_ulice_cp] = kont_souradnice

    if vyrazene_kont > 0:
        print(
            f"Upozorneni: bylo vyrazeno {vyrazene_kont} kontejneru kvuli "
            "chybejicimu klici."
        )

    # Pokud nejsou v souboru zadne volne kontejnery, vypni program.
    if len(slovnik_kontejnery) == 0:
        print(
            "V souboru s kontejnery neni zadny volne pristupny. "
            "Program skonci."
        )
        exit()

    return slovnik_kontejnery


def slovnik_adresnich_bodu(adresni_body_info):
    """Vytvori slovnik adresnich bodu s prevedenymi jtsk souradnicemi.
    Principielne funguje stejne jako funkce slovnik_verejne_kont."""

    slovnik_adresy = {}
    vyrazene_body = 0

    for bod in adresni_body_info:
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
        slovnik_adresy[adresa_ulice_cp] = adresa_jtsk

    if vyrazene_body > 0:
        print(
            f"Upozorneni: bylo vyrazeno {vyrazene_body} adresnich bodu kvuli "
            "chybejicimu klici."
        )

    return slovnik_adresy


def vzdalenost_pythagoras(bod1_x, bod2_x, bod1_y, bod2_y):
    """Vypocita vzdalenost dvou bodu podle Pythagorovy vety."""
    odvesna1 = abs(bod1_x - bod2_x)
    odvesna2 = abs(bod1_y - bod2_y)

    prepona = sqrt((odvesna1 * odvesna1) + (odvesna2 * odvesna2))

    return prepona


def min_vzdal_adresa_kont(slovnik_kontejnery, slovnik_adresy):
    """Z vytvorenych slovniku adres a kontejneru za pomoci funkce
    vzdalenost_pythagoras vygeneruje slovnik s adresnimi body a vzdalenosti
    k nejblizsimu kontejneru."""

    slovnik_adresy_minkont = {}

    for (adresa_bod, souradnice_bod) in slovnik_adresy.items():
        # Souradnice adresniho bodu
        x_1 = souradnice_bod[0]
        y_1 = souradnice_bod[1]

        # Dummy minimalni hodnota na porovnavani vzdalenosti v cyklu nize
        min_vzdalenost = 999999

        for souradnice_kont in slovnik_kontejnery.values():
            # Souradnice kontejneru
            x_2 = souradnice_kont[0]
            y_2 = souradnice_kont[1]

            vzdalenost = vzdalenost_pythagoras(x_1, x_2, y_1, y_2)

            # Porovnava aktualni hodnoty proti nejnizsi (zatim) nalezene
            if vzdalenost < min_vzdalenost:
                min_vzdalenost = vzdalenost

        # Osetreni 10+km vzdaleneho kontejneru
        if min_vzdalenost > 10000:
            print(
                "Nektery z kontejneru je vzdalen vice nez 10 km od "
                "nejblizsiho adresniho bodu.\n"
                "Mate spravna data? Program se ukonci."
            )
            exit()

        slovnik_adresy_minkont[adresa_bod] = min_vzdalenost

    return slovnik_adresy_minkont


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

kont_info = nacitani_geojson("kontejnery.geojson")["features"]
adresy_info = nacitani_geojson("adresy.geojson")["features"]


# SLOVNIK VEREJNYCH KONTEJNERU
slov_kont = slovnik_verejne_kont(kont_info)


# SLOVNIK ADRESNICH BODU
slov_adresy = slovnik_adresnich_bodu(adresy_info)


# HLEDANI NEJMENSI VZDALENOSTI PRO DANOU ADRESU
slov_adresy_minkont = min_vzdal_adresa_kont(slov_kont, slov_adresy)


# PRUMER, MEDIAN A MAXIMUM

# print(mean(slov_adresy_minkont.values()))
prumer_m = prumer_slovnik(slov_adresy_minkont)

# print(median(slov_adresy_minkont.values()))
median_m = median_slovnik(slov_adresy_minkont)

max_m = max(slov_adresy_minkont.values())

# K maximu vzdalenosti priradit odpovidajici adresu
for (adresa, vzdal) in slov_adresy_minkont.items():
    if vzdal == max_m:
        max_adresa = adresa


# FINALNI SOUHRN

print(f"Nacteno {len(slov_adresy)} unikatnich adresnich bodu.")
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

from os import chdir
from os.path import dirname, abspath
from json import load
from sys import exit
from math import sqrt
from pyproj import CRS, Transformer


def load_geojson(file_name):
    """Loads a valid geojson file. In case it doesn't exist / is broken / isn't
    accessible, the program lets the user know and stops.
    """
    try:
        with open(file_name, "r", encoding="UTF-8") as file:
            file = load(file)
    except FileNotFoundError:
        print(f"The file {file_name} does not exist.")
        exit()
    # ValueError contains JSONDecodeError
    except ValueError as err:
        print(
            f"The file {file_name} is invalid.\n",
            err
        )
        exit()
    except PermissionError:
        print(
            f"The program lacks permissions to access {file_name}.\n",
        )
        exit()

    if len(file_name) == 0:
        print(
            "The file is empty. "
            "Please, make sure that you're loading the correct file."
        )
        exit()

    return file


def dict_pub_containers(containers_info):
    """Creates a dictionary with a unique key using the streetname and
    housenumber, where the individual values are coordinates of the address
    points. Duplicate addresses are ignored.
    """

    dict_containers = {}
    # Missing key counter
    missing_cont = 0

    for container in containers_info:
        try:
            cont_street_num = container["properties"]["STATIONNAME"]
            cont_coord = container["geometry"]["coordinates"]
            cont_access = container["properties"]["PRISTUP"]
        except KeyError:
            missing_cont += 1
            continue

        # "volně" means publicly/freely available
        if cont_access == "volně":
            dict_containers[cont_street_num] = cont_coord

    if missing_cont > 0:
        print(
            f"Warning: {missing_cont} containers were discarded due to a "
            "missing key."
        )

    # If there are no publicly accessible containers in the dataset - stop
    if len(dict_containers) == 0:
        print(
            "There are no freely accessible containers in the dataset. "
            "The program will stop now."
        )
        exit()

    return dict_containers


def dict_address_pts(address_pts_info):
    """Creates a dictionary of address points with coordinates in the JTSK
    format.
    """

    dict_addresses = {}
    missing_pts = 0

    for pt in address_pts_info:
        try:
            address_num = pt["properties"]["addr:housenumber"]
            address_street = pt["properties"]["addr:street"]
            # Mind the width/length placement in the original file
            address_width = pt["geometry"]["coordinates"][1]
            address_length = pt["geometry"]["coordinates"][0]
        except KeyError:
            missing_pts += 1
            continue

        # Convert WGS coords to JTSK
        address_jtsk = wgs2jtsk.transform(address_width, address_length)

        address_street_num = address_street + " " + address_num
        dict_addresses[address_street_num] = address_jtsk

    if missing_pts > 0:
        print(
            f"Warning: {missing_pts} address points were discarded due to a "
            "missing key."
        )

    return dict_addresses


def dist_pythag(pt1_x, pt2_x, pt1_y, pt2_y):
    """Calculates the distance between two points using the Pythagorean
    theorem
    """
    side_a = abs(pt1_x - pt2_x)
    side_b = abs(pt1_y - pt2_y)

    hypotenuse = sqrt((side_a * side_a) + (side_b * side_b))

    return hypotenuse


def min_dist_address_cont(dict_containers, dict_addresses):
    """Generates a dictionary of address points and the distance to the closest
    waste container using the dist_pythag function.
    """

    dict_addresses_mincont = {}

    for (address_pt, coords_pt) in dict_addresses.items():
        # Address point coordinates
        x_1 = coords_pt[0]
        y_1 = coords_pt[1]

        # Dummy minimal value to compare distances in the cycle below
        min_distance = 999999

        for coords_cont in dict_containers.values():
            # Container coordinates
            x_2 = coords_cont[0]
            y_2 = coords_cont[1]

            distance = dist_pythag(x_1, x_2, y_1, y_2)

            # Compares the current values to the minimal distance found
            if distance < min_distance:
                min_distance = distance

        # 10+km accounted for
        if min_distance > 10000:
            print(
                "Some of the containers are more than 10 kilometers away "
                "from the closest address point.\n"
                "Are you sure you have the correct data?"
            )
            exit()

        dict_addresses_mincont[address_pt] = min_distance

    return dict_addresses_mincont


def mean_dict(dictionary):
    """Finds the mean of dictionary values."""
    mean_val = sum(dictionary.values()) / len(dictionary)
    return mean_val


def median_dict(dictionary):
    """Finds the median of dictionary values."""
    list_median = list(dictionary.values())
    list_median.sort()
    n = len(list_median)
    pos = (n - 1) // 2

    if n % 2:
        return list_median[pos]

    return (list_median[pos] + list_median[pos + 1]) / 2


# DEFINITIONS FOR COORDINATE CONVERSION

crs_wgs = CRS.from_epsg(4326)  # WGS-84
crs_jtsk = CRS.from_epsg(5514)  # S-JTSK

wgs2jtsk = Transformer.from_crs(crs_wgs, crs_jtsk)


# LOADING DATA

# Set working directory to filepath
chdir(dirname(abspath(__file__)))

cont_info = load_geojson("containers.geojson")["features"]
addr_info = load_geojson("address.geojson")["features"]


# DICTIONARY PUBLIC CONTAINERS
dict_cont = dict_pub_containers(cont_info)


# DICTIONARY ADDRESS POINTS
dict_addr = dict_address_pts(addr_info)


# FINDING THE SMALLEST DISTANCE FROM AN ADDRESS PT TO A CONTAINER
dict_addr_mindist = min_dist_address_cont(dict_cont, dict_addr)


# MEAN, MEDIAN & MAX
mean_m = mean_dict(dict_addr_mindist)
median_m = median_dict(dict_addr_mindist)
max_m = max(dict_addr_mindist.values())

# Add the address to the max distance
for (addr, dist) in dict_addr_mindist.items():
    if dist == max_m:
        max_addr = addr


# SUMMARY

print(f"Loaded {len(dict_addr)} unique address points.")
print(f"Loaded {len(dict_cont)} unique waste container coordinates.")

print(
    "\n"
    "Average distance to a freely accessible waste container: "
    f"{mean_m:.0f} meters."
)

print(f"Median distance to a container: {median_m:.0f} meters.")

print(
    f"The longest distance to a public container, {max_m:.0f} meters, is from "
    f"the address '{max_addr}'."
)

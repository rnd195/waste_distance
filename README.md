# Distance to waste containers

The aim of this program is to determine the availability of containers in a given place (for example, a city district) by calculating the average, median and maximum distance of individual address points to the nearest publicly accessible container. 



## Input

The program works with `.geojson` files, which should include:

- address points of the given district in WGS-84 format, 
- `addr:street` a `addr:housenumber` keys to identify individual addresses.

Next, the file `containers.geojson` should include: 

- coordinates of waste containers in [S-JTSK format](https://epsg.io/5514),
- `STATIONNAME` attribute to identify the place 
- and the `PRISTUP` attribute to determine the access to the container.

In the repository of this project, you may find the `address.geojson` file, which comprises of addresses from the Old Town district in Prague, Czech Republic. These were generated using [Overpass Turbo](http://overpass-turbo.eu/s/119J). Furthermore, the `containers.geojson` file contains data from the [Prague Geoportal](https://www.geoportalpraha.cz/cs/data/otevrena-data/8726EF0E-0834-463B-9E5F-FE09E62D73FB).



## Output

The program lists the number of loaded unique address points of the given district, the number of freely accessible containers, the average distance of the address point to the nearest public container, the median of this distance, and finally, the address of the furthermost point with the corresponding distance.

All distances are given in meters, and if one of the address points is more than 10,000 meters away from the nearest container, the program will let the user know and will not continue with the calculations. 

In the code block below, you may see the output for the Old Town address file and the complete dataset of Prague waste containers:

```
Warning: 2 address points were discarded due to a missing key.
Loaded 1633 unique address points.
Loaded 3441 unique waste container coordinates.

Average distance to a freely accessible waste container: 136 meters.
Median distance to a container: 129 meters.
The longest distance to a public container, 323 meters, is from the address 'Na příkopě 1096/19'.
```

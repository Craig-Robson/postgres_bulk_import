import gzip, shutil, os
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from geopandas_postgis import PostGIS


def gml_to_shp(input_list, data_dir_output):
    for data_dir in input_list:

        files = []
        for f in os.listdir(data_dir):
            files.append(f)

        for file in files:

            if file.split('.')[-1] == 'gz':
                file_name = file.split('.')[0]

                with gzip.open('%s' % (os.path.join(data_dir, file)), 'rb') as f_in:
                    with open('%s.gml' % (os.path.join(data_dir_output, 'gml', file_name)), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                gdf = gpd.read_file('%s.gml' % (os.path.join(data_dir_output, 'gml', file_name)))

                gdf.to_file('%s.shp' % (os.path.join(data_dir_output, 'shp', file_name)))


def write_to_database(merge, data_dir, database, schema_name, table_name, username, password, host, port, format='gml'):
    """
    """
    engine = create_engine("postgresql+psycopg2://%s:%s@%s:%s/%s" % (username, password, host, port, database))

    files = []
    for f in os.listdir(data_dir):
        files.append(f)

    first = True
    for file in files:

        file_name = file.split('.')[0]

        if file.split('.')[-1] == format:

            if merge is True and first is False:
                gdf_ = gpd.read_file('%s' % (os.path.join(data_dir, file)))
                gdf = gdf.append(gdf_, ignore_index=True)
            else:
                first = False
                gdf = gpd.read_file('%s' % (os.path.join(data_dir, file)))

            if gdf.crs == '':
                gdf.crs = "EPSG:27700"

            if gdf.geom_type[0] is None:
                geom_type = 'LineStringZ'
            else:
                geom_type = str(gdf.geom_type[0])
                if geom_type == 'LineString':
                    geom_type = 'LineStringZ'
            
            if merge is False:
                gdf.postgis.to_postgis(con=engine, table_name=file_name.lower(), schema=schema_name, geometry=geom_type)

        print('Written %s to database' % file_name )

    if merge is True:
        print('Writing data to database')
        gdf.postgis.to_postgis(con=engine, table_name=table_name, schema=schema_name, geometry=geom_type)


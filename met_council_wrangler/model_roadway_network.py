import os
import pandas as pd
import geopandas as gpd
import numpy as pd

from network_wrangler import RoadwayNetwork
from cube_wrangler.logger import WranglerLogger
from model_parameters import MetCouncil_Parameters


def roadway_standard_to_met_council_network(
    roadway_net=None, parameters=None, output_epsg=None
):
    """
    Rename and format roadway attributes to be consistent with what metcouncil's model is expecting.

    Args:
        roadway_net (ModelRoadwayNetwork): A Network Wrangler Roadway Network.
        parameters (Parameters): MetCouncil Parameters, which stores input files.
        output_epsg (int): epsg number of output network.

    Returns:
        None
    """

    WranglerLogger.info(
        "Renaming roadway attributes to be consistent with what metcouncil's model is expecting"
    )

    if type(parameters) is dict:
        parameters = MetCouncil_Parameters(**parameters)
    elif isinstance(parameters, MetCouncil_Parameters):
        parameters = MetCouncil_Parameters(**parameters.__dict__)
    else:
        msg = "Parameters should be a dict or instance of Parameters: found {} which is of type:{}".format(
            parameters, type(parameters)
        )
        WranglerLogger.error(msg)
        raise ValueError(msg)

    """
    Verify inputs
    """
    output_epsg = output_epsg if output_epsg else parameters.output_epsg

    """
    Start actual process
    """
    if "managed" in roadway_net.links_df.columns:
        if 1 in roadway_net.links_df["managed"].values:
            WranglerLogger.info("Creating managed lane network.")
            roadway_net.create_managed_lane_network(in_place=True)

        # when ML and assign_group projects are applied together, assign_group is filled as "" by wrangler for ML links
        for c in parameters.calculated_values:
            if c in roadway_net.links_df.columns and c in parameters.int_col:
                roadway_net.links_df[c] = roadway_net.links_df[c].replace("", 0)
    else:
        WranglerLogger.info("Didn't detect managed lanes in network.")

    roadway_net.create_calculated_variables()
    roadway_net.create_ML_variable()
    roadway_net.reate_hov_corridor_variable()
    roadway_net.create_managed_variable()
    roadway_net = calculate_area_type(roadway_net, parameters)
    roadway_net = calculate_county(roadway_net, parameters)
    roadway_net = calculate_mpo(roadway_net, parameters)
    roadway_net = add_counts(roadway_net, parameters)

    roadway_net.fill_na()
    # no method to calculate price yet, will be hard coded in project card
    WranglerLogger.info("Splitting variables by time period and category")
    roadway_net.split_properties_by_time_period_and_category(
        properties_to_split=parameters.properties_to_split
    )
    roadway_net.convert_int(int_col_names=parameters.int_col)

    roadway_net.links_metcouncil_df = roadway_net.links_df.copy()
    roadway_net.nodes_metcouncil_df = roadway_net.nodes_df.copy()

    roadway_net.links_metcouncil_df = pd.merge(
        roadway_net.links_metcouncil_df.drop(
            "geometry", axis=1
        ),  # drop the stick geometry in links_df
        roadway_net.shapes_df[[RoadwayNetwork.UNIQUE_SHAPE_KEY, "geometry"]],
        how="left",
        on=RoadwayNetwork.UNIQUE_SHAPE_KEY,
    )

    roadway_net.links_metcouncil_df.crs = "EPSG:4269"
    roadway_net.nodes_metcouncil_df.crs = "EPSG:4269"
    WranglerLogger.info("Setting Coordinate Reference System to EPSG 26915")
    roadway_net.links_metcouncil_df = roadway_net.links_metcouncil_df.to_crs(epsg=26915)
    roadway_net.nodes_metcouncil_df = roadway_net.nodes_metcouncil_df.to_crs(epsg=26915)

    roadway_net.nodes_metcouncil_df["X"] = (
        roadway_net.nodes_metcouncil_df.geometry.apply(lambda g: g.x)
    )
    roadway_net.nodes_metcouncil_df["Y"] = (
        roadway_net.nodes_metcouncil_df.geometry.apply(lambda g: g.y)
    )

    # CUBE expect node id to be N
    roadway_net.nodes_metcouncil_df.rename(columns={"model_node_id": "N"}, inplace=True)


def calculate_area_type(
    roadway_net=None,
    parameters=None,
    area_type_shape=None,
    area_type_shape_variable=None,
    network_variable="area_type",
    area_type_codes_dict=None,
    downtown_area_type_shape=None,
    downtown_area_type=None,
    overwrite=False,
):
    """
    Calculates area type variable.

    This uses the centroid of the geometry field to determine which area it should be labeled.
    This isn't perfect, but it much quicker than other methods.

    Args:
        roadway_net (ModelRoadwayNetwork): A Network Wrangler Roadway Network.
        parameters (Parameters): MetCouncil Parameters, which stores input files.
        area_type_shape (str): The File path to area geodatabase.
        area_type_shape_variable (str): The variable name of area type in area geodadabase.
        network_variable (str): The variable name of area type in network standard.  Default to "area_type".
        area_type_codes_dict: The dictionary to map input area_type_shape_variable to network_variable
        downtown_area_type_shape: The file path to the downtown area type boundary.
        downtown_area_type (int): Integer value of downtown area type
        overwrite (Bool): True if overwriting existing county variable in network.  Default to False.

    Returns:
        roadway network object

    """

    if network_variable in roadway_net.links_df:
        if overwrite:
            WranglerLogger.info(
                "Overwriting existing Area Type Variable '{}' already in network".format(
                    network_variable
                )
            )
        else:
            # check if some links miss area type
            if roadway_net.links_df[network_variable].isnull().values.any():
                WranglerLogger.info(
                    "Area Type Variable '{}' already in network. But some records are missing. Calcualting the missing values without overwriting existing.".format(
                        network_variable
                    )
                )
            else:
                WranglerLogger.info(
                    "Area Type Variable '{}' already in network. Returning without overwriting.".format(
                        network_variable
                    )
                )
                return

    WranglerLogger.info(
        "Calculating Area Type from Spatial Data and adding as roadway network variable: {}".format(
            network_variable
        )
    )

    """
    Verify inputs
    """

    area_type_shape = area_type_shape if area_type_shape else parameters.area_type_shape

    if not area_type_shape:
        msg = "No area type shape specified"
        WranglerLogger.error(msg)
        raise ValueError(msg)
    if not os.path.exists(area_type_shape):
        msg = "File not found for area type shape: {}".format(area_type_shape)
        WranglerLogger.error(msg)
        raise ValueError(msg)

    area_type_shape_variable = (
        area_type_shape_variable
        if area_type_shape_variable
        else parameters.area_type_variable_shp
    )

    if not area_type_shape_variable:
        msg = "No area type shape varible specified"
        WranglerLogger.error(msg)
        raise ValueError(msg)

    area_type_codes_dict = (
        area_type_codes_dict if area_type_codes_dict else parameters.area_type_code_dict
    )
    if not area_type_codes_dict:
        msg = "No area type codes dictionary specified"
        WranglerLogger.error(msg)
        raise ValueError(msg)

    downtown_area_type_shape = (
        downtown_area_type_shape
        if downtown_area_type_shape
        else parameters.downtown_area_type_shape
    )

    if not downtown_area_type_shape:
        msg = "No downtown area type shape specified"
        WranglerLogger.error(msg)
        raise ValueError(msg)
    if not os.path.exists(downtown_area_type_shape):
        msg = "File not found for downtown area type shape: {}".format(
            downtown_area_type_shape
        )
        WranglerLogger.error(msg)
        raise ValueError(msg)

    downtown_area_type = (
        downtown_area_type if downtown_area_type else parameters.downtown_area_type
    )
    if not downtown_area_type:
        msg = "No downtown area type value specified"
        WranglerLogger.error(msg)
        raise ValueError(msg)

    """
    Start actual process
    """
    centroids_gdf = roadway_net.links_df.copy()
    centroids_gdf["geometry"] = centroids_gdf["geometry"].centroid

    WranglerLogger.debug("Reading Area Type Shapefile {}".format(area_type_shape))
    area_type_gdf = gpd.read_file(area_type_shape)
    area_type_gdf = area_type_gdf.to_crs(epsg=RoadwayNetwork.CRS)

    downtown_gdf = gpd.read_file(downtown_area_type_shape)
    downtown_gdf = downtown_gdf.to_crs(epsg=RoadwayNetwork.CRS)

    if (int(gpd.__version__.split(".")[0]) == 0) & (
        int(gpd.__version__.split(".")[1]) < 10
    ):
        joined_gdf = gpd.sjoin(
            centroids_gdf, area_type_gdf, how="left", op="intersects"
        )
    else:
        joined_gdf = gpd.sjoin(
            centroids_gdf, area_type_gdf, how="left", predicate="intersects"
        )

    joined_gdf[area_type_shape_variable] = (
        joined_gdf[area_type_shape_variable]
        .map(area_type_codes_dict)
        .fillna(1)
        .astype(int)
    )

    WranglerLogger.debug("Area Type Codes Used: {}".format(area_type_codes_dict))

    if (int(gpd.__version__.split(".")[0]) == 0) & (
        int(gpd.__version__.split(".")[1]) < 10
    ):
        d_joined_gdf = gpd.sjoin(
            centroids_gdf, downtown_gdf, how="left", op="intersects"
        )
    else:
        d_joined_gdf = gpd.sjoin(
            centroids_gdf, downtown_gdf, how="left", predicate="intersects"
        )

    d_joined_gdf["downtown_area_type"] = d_joined_gdf["Id"].fillna(-99).astype(int)

    joined_gdf.loc[
        d_joined_gdf["downtown_area_type"] == 0, area_type_shape_variable
    ] = downtown_area_type

    WranglerLogger.debug(
        "Downtown Area Type used boundary file: {}".format(downtown_area_type_shape)
    )

    if overwrite:
        roadway_net.links_df[network_variable] = joined_gdf[area_type_shape_variable]
    elif network_variable not in roadway_net.links_df.columns:
        roadway_net.links_df[network_variable] = joined_gdf[area_type_shape_variable]
    else:
        # replace "" with na
        roadway_net.links_df[network_variable] = roadway_net.links_df[
            network_variable
        ].replace("", np.nan)
        # update missing values
        roadway_net.links_df[network_variable] = roadway_net.links_df[
            network_variable
        ].fillna(joined_gdf[area_type_shape_variable])

    WranglerLogger.info(
        "Finished Calculating Area Type from Spatial Data into variable: {}".format(
            network_variable
        )
    )

    return roadway_net


def calculate_county(
    roadway_net=None,
    parameters=None,
    county_shape=None,
    county_shape_variable=None,
    network_variable="county",
    county_codes_dict=None,
    overwrite=False,
):
    """
    Calculates county variable.

    This uses the centroid of the geometry field to determine which county it should be labeled.
    This isn't perfect, but it much quicker than other methods.

    Args:
        roadway_net (ModelRoadwayNetwork): A Network Wrangler Roadway Network.
        parameters (Parameters): MetCouncil Parameters, which stores input files.
        county_shape (str): The File path to county geodatabase.
        county_shape_variable (str): The variable name of county in county geodadabase.
        network_variable (str): The variable name of county in network standard.  Default to "county".
        overwrite (Bool): True if overwriting existing county variable in network.  Default to False.

    Returns:
        roadway network object
    """
    if network_variable in roadway_net.links_df:
        if overwrite:
            WranglerLogger.info(
                "Overwriting existing County Variable '{}' already in network".format(
                    network_variable
                )
            )
        else:
            WranglerLogger.info(
                "County Variable '{}' already in network. Returning without overwriting.".format(
                    network_variable
                )
            )
            return

    """
    Verify inputs
    """

    county_shape = county_shape if county_shape else parameters.county_shape

    county_shape_variable = (
        county_shape_variable
        if county_shape_variable
        else parameters.county_variable_shp
    )

    WranglerLogger.info(
        "Adding roadway network variable for county using a spatial join with: {}".format(
            county_shape
        )
    )

    """
    Start actual process
    """

    centroids_gdf = roadway_net.links_df.copy()
    centroids_gdf["geometry"] = centroids_gdf["geometry"].centroid

    county_gdf = gpd.read_file(county_shape)
    county_gdf = county_gdf.to_crs(epsg=RoadwayNetwork.CRS_alt)
    joined_gdf = gpd.sjoin(centroids_gdf, county_gdf, how="left", op="intersects")

    joined_gdf[county_shape_variable] = (
        joined_gdf[county_shape_variable].map(county_codes_dict).fillna(10).astype(int)
    )

    roadway_net.links_df[network_variable] = joined_gdf[county_shape_variable]

    nodes_gdf = roadway_net.nodes_df.copy()
    joined_gdf = gpd.sjoin(nodes_gdf, county_gdf, how="left", op="intersects")

    joined_gdf[county_shape_variable] = (
        joined_gdf[county_shape_variable].map(county_codes_dict).fillna(10).astype(int)
    )

    joined_gdf = joined_gdf.drop_duplicates(subset=["model_node_id"])
    joined_gdf[network_variable] = joined_gdf[county_shape_variable]

    if network_variable in roadway_net.nodes_df.columns:
        roadway_net.nodes_df = roadway_net.nodes_df.drop(network_variable, axis=1)

    roadway_net.nodes_df = pd.merge(
        roadway_net.nodes_df,
        joined_gdf[["model_node_id", network_variable]],
        how="left",
        on="model_node_id",
    )

    WranglerLogger.info(
        "Finished Calculating county variable: {}".format(network_variable)
    )

    return roadway_net


def calculate_mpo(
    roadway_net=None,
    parameters=None,
    county_network_variable="county",
    network_variable="mpo",
    as_integer=True,
    mpo_counties=None,
    overwrite=False,
):
    """
    Calculates mpo variable.

    Args:
        roadway_net (ModelRoadwayNetwork): A Network Wrangler Roadway Network.
        parameters (Parameters): MetCouncil Parameters, which stores input files.
        county_variable (str): Name of the variable where the county names are stored.  Default to "county".
        network_variable (str): Name of the variable that should be written to.  Default to "mpo".
        as_integer (bool): If true, will convert true/false to 1/0s.
        mpo_counties (list): List of county names that are within mpo region.
        overwrite (Bool): True if overwriting existing county variable in network.  Default to False.

    Returns:
        roadway network object
    """

    if network_variable in roadway_net.links_df:
        if overwrite:
            WranglerLogger.info(
                "Overwriting existing MPO Variable '{}' already in network".format(
                    network_variable
                )
            )
        else:
            WranglerLogger.info(
                "MPO Variable '{}' already in network. Returning without overwriting.".format(
                    network_variable
                )
            )
            return

    WranglerLogger.info(
        "Calculating MPO as roadway network variable: {}".format(network_variable)
    )

    """
    Verify inputs
    """
    county_network_variable = (
        county_network_variable
        if county_network_variable
        else parameters.county_network_variable
    )

    if not county_network_variable:
        msg = "No variable specified as containing 'county' in the network."
        WranglerLogger.error(msg)
        raise ValueError(msg)
    if county_network_variable not in roadway_net.links_df.columns:
        msg = "Specified county network variable: {} does not exist in network. Try running or debuging county calculation."
        WranglerLogger.error(msg)
        raise ValueError(msg)

    mpo_counties = mpo_counties if mpo_counties else parameters.mpo_counties

    if not mpo_counties:
        msg = "No MPO Counties specified in method call or in parameters."
        WranglerLogger.error(msg)
        raise ValueError(msg)

    WranglerLogger.debug("MPO Counties: {}".format(",".join(str(mpo_counties))))

    """
    Start actual process
    """

    mpo = roadway_net.links_df[county_network_variable].isin(mpo_counties)

    if as_integer:
        mpo = mpo.astype(int)

    roadway_net.links_df[network_variable] = mpo

    WranglerLogger.info(
        "Finished calculating MPO variable: {}".format(network_variable)
    )


def add_counts(
    roadway_net=None,
    parameters=None,
    network_variable="AADT",
    mndot_count_shst_data=None,
    widot_count_shst_data=None,
    mndot_count_variable_shp=None,
    widot_count_variable_shp=None,
):
    """
    Adds count variable.

    join the network with count node data, via SHST API node match result

    Args:
        roadway_net (ModelRoadwayNetwork): A Network Wrangler Roadway Network.
        parameters (Parameters): MetCouncil Parameters, which stores input files.
        network_variable (str): Name of the variable that should be written to.  Default to "AADT".
        mndot_count_shst_data (str): File path to MNDOT count location SHST API node match result.
        widot_count_shst_data (str): File path to WIDOT count location SHST API node match result.
        mndot_count_variable_shp (str): File path to MNDOT count location geodatabase.
        widot_count_variable_shp (str): File path to WIDOT count location geodatabase.

    Returns:
        roadway network object
    """

    WranglerLogger.info("Adding Counts")

    """
    Verify inputs
    """

    mndot_count_shst_data = (
        mndot_count_shst_data
        if mndot_count_shst_data
        else parameters.mndot_count_shst_data
    )
    widot_count_shst_data = (
        widot_count_shst_data
        if widot_count_shst_data
        else parameters.widot_count_shst_data
    )
    mndot_count_variable_shp = (
        mndot_count_variable_shp
        if mndot_count_variable_shp
        else parameters.mndot_count_variable_shp
    )
    widot_count_variable_shp = (
        widot_count_variable_shp
        if widot_count_variable_shp
        else parameters.widot_count_variable_shp
    )

    for varname, var in {
        "mndot_count_shst_data": mndot_count_shst_data,
        "widot_count_shst_data": widot_count_shst_data,
    }.items():
        if not var:
            msg = "'{}' not found in method or lasso parameters.".format(varname)
            WranglerLogger.error(msg)
            raise ValueError(msg)
        if not os.path.exists(var):
            msg = "{}' not found at following location: {}.".format(varname, var)
            WranglerLogger.error(msg)
            raise ValueError(msg)

    for varname, var in {
        "mndot_count_variable_shp": mndot_count_variable_shp,
        "widot_count_variable_shp": widot_count_variable_shp,
    }.items():
        if not var:
            msg = "'{}' not found in method or lasso parameters.".format(varname)
            WranglerLogger.error(msg)
            raise ValueError(msg)

    """
    Start actual process
    """
    WranglerLogger.debug(
        "Adding MNDOT Counts using \n- shst file: {}\n- shp file: {}\n- as network variable: {}".format(
            mndot_count_shst_data, mndot_count_variable_shp, network_variable
        )
    )
    # Add Minnesota Counts
    roadway_net.add_variable_using_shst_reference(
        var_shst_csvdata=mndot_count_shst_data,
        shst_csv_variable=mndot_count_variable_shp,
        network_variable=network_variable,
        network_var_type=int,
        overwrite=True,
    )
    WranglerLogger.debug(
        "Adding WiDot Counts using \n- shst file: {}\n- shp file: {}\n- as network variable: {}".format(
            widot_count_shst_data, widot_count_variable_shp, network_variable
        )
    )
    # Add Wisconsin Counts, but don't overwrite Minnesota
    roadway_net.add_variable_using_shst_reference(
        var_shst_csvdata=widot_count_shst_data,
        shst_csv_variable=widot_count_variable_shp,
        network_variable=network_variable,
        network_var_type=int,
        overwrite=False,
    )

    roadway_net.links_df["count_AM"] = roadway_net.links_df[network_variable] / 4
    roadway_net.links_df["count_MD"] = roadway_net.links_df[network_variable] / 4
    roadway_net.links_df["count_PM"] = roadway_net.links_df[network_variable] / 4
    roadway_net.links_df["count_NT"] = roadway_net.links_df[network_variable] / 4

    roadway_net.links_df["count_daily"] = roadway_net.links_df[network_variable]
    # add COUNTYEAR
    roadway_net.links_df["count_year"] = 2017

    WranglerLogger.info("Finished adding counts variable: {}".format(network_variable))

    return roadway_net

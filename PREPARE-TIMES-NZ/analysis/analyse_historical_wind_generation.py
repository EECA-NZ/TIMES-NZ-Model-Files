# This script is intended to read our historical wind generation and find availability per timeslice 

# We will need: 

# the md data 
# our concordance table of capacities per wind farm 
# a timeslice definition (for aggregating generation per timeslice) 

# this script only shows plots and is not intended to be included in a main workflow.
# the results on availability factors will be saved and hardcoded as an assumption.

# it requires the script at  scripts/stage_1_prep_raw_data/extra_ea_data.py to be run first to generate the input EMI data. 
# This is part of the main workflow



#region LIBRARIES ------------------------------------------------------------
import sys 
import os 
import polars as pl 
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import logging 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../", "library"))
from filepaths import DATA_INTERMEDIATE, CUSTOM_ELE_ASSUMPTIONS

output_location = f"{DATA_INTERMEDIATE}/stage_1_extracted_data/wind_af_analysis/"
os.makedirs(output_location, exist_ok = True)

#endregion

#region SETTINGS ------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
pl.Config.set_tbl_cols(100) 
pl.Config.set_tbl_rows(100)

#endregion 

#region GET_DATA ------------------------------------------------------------

# our fleet metadata
eeca_fleet_data = pl.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/GenerationFleet.csv")
# full emi md generation data 
emi_md = pl.read_parquet(f"{DATA_INTERMEDIATE}/stage_1_external_data/electricity_authority/emi_md.parquet")

# assumptions: we're pulling in the times 2 onshore wind availability factors from a hardcoded csv 
# this is stored in archive because it's not part of the main workflow and is not intended to be updated

times_2_wind_af = pl.read_csv(f"{CUSTOM_ELE_ASSUMPTIONS}/archive/WindAF_from_TIMES2.csv")

#endregion 

#region FUNCTIONS ------------------------------------------------------------


def convert_hour_to_timeofday(df: pl.DataFrame, hour_col: str = "Hour") -> pl.DataFrame:

    """
    This function takes a dataframe with an hour variable  and creates the TIMES timeofday variable 
    ideally, we would be able to pull the time settings from a config file, but for now we will hardcode them

    hour_col: str = "Hour". A string that references the hour column we're working with.
    This should be an integer variable as createed by convert_TP_to_hour.
    

    """
    
    df = df.with_columns([
        pl.when(pl.col(hour_col) == 18).then(pl.lit("P"))
        .when((pl.col(hour_col) >= 7) & (pl.col(hour_col) <= 17)).then(pl.lit("D"))
        .otherwise(pl.lit("N")).alias("Time_Of_Day")
        ])
    
    return df 


def convert_date_to_daytype(df: pl.DataFrame, date_col: str = "Trading_Date") -> pl.DataFrame:
    """
    This function takes a dataframe with a date variable and creates the TIMES daytype variable 
    date_col: str = "Trading_Date". A string that references the date column we're working with.
    This must be a date variable. 
    
    """

    


    df = df.with_columns([
        pl.when(pl.col(date_col).dt.weekday().is_in([6,7])).then(pl.lit("WE-"))
        .when(pl.col(date_col).dt.weekday().is_in([1,2,3,4,5])).then(pl.lit("WK-"))
        .otherwise(pl.lit("ERROR")).alias("Day_Type")
        ])
    
    
    
    return df

def convert_date_to_season(df: pl.DataFrame, date_col: str = "Trading_Date") -> pl.DataFrame:

    """
    This function takes a dataframe with a date variable and creates the TIMES season variable 
    date_col: str = "Trading_Date". A string that references the date column we're working with.
    This must be a date variable. 
    
    """

    # create a month variable 
    df = df.with_columns(pl.col(date_col).dt.month().alias("Month"))

    # define the seasons 
    df = df.with_columns([
        pl.when(pl.col("Month").is_in([12, 1, 2])).then(pl.lit("SUM-"))
        .when(pl.col("Month").is_in([3, 4, 5])).then(pl.lit("FAL-"))
        .when(pl.col("Month").is_in([6, 7, 8])).then(pl.lit("WIN-"))
        .when(pl.col("Month").is_in([9, 10, 11])).then(pl.lit("SPR-"))
        .otherwise(pl.lit("ERROR")).alias("Season")
        ])
    
    df = df.drop("Month")


    return df

def create_timeslices(df: pl.DataFrame, hour_col:str = "Hour", date_col: str = "Trading_Date", tp_col: str = "Trading_Period") -> pl.DataFrame:
    """
    This function takes a dataframe with a date and time variable and creates the TIMES time slice variable 
    date_col: str = "Trading_Date". A string that references the date column we're working with.
    tp_col: str = "Trading_Period". A string that references the trading period column we're working with.
    
    """

    # create the time of day variable 
    df = convert_hour_to_timeofday(df, hour_col)

    # create the day type variable 
    df = convert_date_to_daytype(df, date_col)

    # create the season variable 
    df = convert_date_to_season(df, date_col)

    # create the timeslice variable 
    df = (df.
          # combine to create timeslices
          with_columns((pl.col("Season") + pl.col("Day_Type") + pl.col("Time_Of_Day")).alias("Timeslice"))
          # remove the original vars to tidy up 
          .drop(["Season", "Day_Type", "Time_Of_Day"])
    )

    return df

def check_grain(df: pl.DataFrame, grain_variables) -> pl.DataFrame:
    """
    This function checks the grain of the dataframe to ensure that it is at the correct level for our analysis.
    It will check that there are no duplicates in the Trading_Date and Trading_Period columns.

    the df is a polars dataframe
    the cols are the variables we think define the grain of the dataframe.
    
    """


    grain_check = df.group_by(grain_variables).agg(pl.count()).filter(pl.col("count") > 1)


    if grain_check.shape[0] > 0:
        logging.warning("These variables do not uniquely define the grain of the dataframe:")
        for var in grain_variables:
            print(var)

        logging.info("The following rows are duplicates:")
        print(grain_check)
    else:
        logging.info("Dataframe is successfully defined by the following varaibles:")
        for var in grain_variables:
            logging.info(var)

#endregion 

#region AGGREGATE_EMI_DATA ------------------------------------------------------------

check_grain(emi_md, ["Trading_Date", "Trading_Period", "Gen_Code", "POC_Code", "Nwk_Code"])

# POC_Code and NWK_Code are required to define each row. However, we don't actually care about these so are happy to aggregate across them. 

emi_md = (emi_md
    .filter(pl.col("Value").is_not_null())
    .group_by(["Trading_Date", "Trading_Period", "Gen_Code"]).
    agg([pl.sum("Value").alias("Value")]))
    
# still half-hourly data. We will get our metadata elsewhere rather than using EMI metadata.

#endregion 

#region CREATE_TIMESLICES ------------------------------------------------------------

def add_timeslices_to_emi(df: pl.DataFrame, date_col: str = "Trading_Date", tp_col: str = "Trading_Period") -> pl.DataFrame:

    # Step 1: Create dates
    df = df.with_columns([
        pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d")
    
    ])

    # Step 2: Create Hour variable based on trading period 
    # first make an integer variable from the trading period
    df = df.with_columns([
        (pl.col(tp_col)
        .str.replace_all("TP", "")
        .filter(pl.col(tp_col).is_not_null())        
        .cast(pl.Int32)   
        ).alias("Trading_Time")
        ])
    # create an hour by subtracting 1, making minutes (*30) then dividing by 60 (no remainder) 
    # so 0 is midnight-1am, 1 is 1am-2am, etc.
    # there is a 24 - this is the extra hour for DST days with additional hours 
    # because DST is whatever, we just say this is effectively an additional night hour (default night in our timeslice)
    df = (df.with_columns([((pl.col("Trading_Time")-1) * 30 // 60).alias("Hour")]))

    # with relevant variables created, we can define the timeslices
    df = create_timeslices(df)

    return df


emi_timeslices = add_timeslices_to_emi(emi_md)

#endregion

#region ADD_METADATA ------------------------------------------------------------

# left join onto 5m rows? probably fine 
metadata = eeca_fleet_data[[    
    "EMI_Name",
    "TechnologyCode",
    "FuelType",
    "CapacityMW"
]]

# some plants have multiple names in our data which correspond to only one EMI name. 
# for these we just combine the capacities 
metadata = metadata.group_by(["EMI_Name", "TechnologyCode", "FuelType"]).agg([
    pl.sum("CapacityMW").alias("CapacityMW")
])

# change our emi code to match the metadata variable name before join. Could also do this within the join. 
emi_timeslices = emi_timeslices.rename({"Gen_Code": "EMI_Name"})
# join 
emi_timeslices = emi_timeslices.join(metadata, on = "EMI_Name", how = "left")

# check failed joins 
failed_metadata_joins = emi_timeslices.filter(pl.col("CapacityMW").is_null())
failed_plants = failed_metadata_joins["EMI_Name"].unique().sort()
logging.info("Failed plant joins - in EMI but not in metadata:")
for plant in failed_plants:
    logging.info(plant)


# not too stressed about these so just remove them
emi_timeslices = emi_timeslices.filter(pl.col("CapacityMW").is_not_null())

#endregion 

#region WIND_CAPACITY_FACTORS------------------------------------------------------------

emi_timeslice_wind = emi_timeslices.filter(pl.col("FuelType") == "Wind")

# some aggregation (this should have maybe happened elsewhere but whatever)
emi_timeslice_wind = (emi_timeslice_wind
                      # aggregate by hour 
                      .group_by(["EMI_Name", "TechnologyCode", "Trading_Date", "Hour", "Timeslice", "FuelType"])
                      .agg([pl.sum("Value").alias("Value"), pl.max("CapacityMW").alias("CapacityMW")])
                      # change value to MWh 
                      .with_columns([(pl.col("Value") / 1e3).alias("Value_MWh")])
                      # create hourly capacity factor
                      .with_columns([(pl.col("Value_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")])
                      # create a datetime - first remove the dodgy additional DST hours (bit of a hack but whatever)
                      .filter(pl.col("Hour") < 24)
                      .with_columns([
                          pl.datetime(                              
                              year=pl.col("Trading_Date").dt.year(),
                              month=pl.col("Trading_Date").dt.month(),
                              day=pl.col("Trading_Date").dt.day(),
                              hour=pl.col("Hour"),
                              minute=pl.lit(0),
                              second=pl.lit(0),
                              ).alias("DateTime")
                        ])
    
)

#endregion 

#region CHECK_CAPACITY_FACTORS ------------------------------------------------------------

# convert to pandas for plotting 
# hourly capacity factors for each plant
plot_hourly_cfs = False
if plot_hourly_cfs:
    pdf = emi_timeslice_wind.to_pandas()
    pdf = pdf.sort_values(["EMI_Name", "DateTime"])

    g = sns.FacetGrid(pdf, col="EMI_Name", col_wrap=4, height=3.5, sharey=True)
    g.map(sns.lineplot, "DateTime", "Capacity_Factor")
    g.map(plt.axhline, y=1, linestyle=':', color='black')

    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Time", "Capacity Factor")
    g.tight_layout()
    plt.show()

#endregion

#region REMOVE_PARTIAL_YEARS ------------------------------------------------------------

# hardcoded partial years - sorry

partial_year_dict = {
    "KaiweraDowns": [2024],
    "turitea": [2024],
    "waipipi" : [2022,2023,2024], #very close on 2021 but not quite full generation. 
    "west_wind":[2020, 2021, 2022],
    "white_hill": [2020, 2024] # strange performance dip: maintenance??
    }

# generating a filter expression based on the dict
# if a plant is not in the dict, we take everything, otherwise we filter by the years in the dict

# list of all expressions 
exprs = [
    (pl.col("EMI_Name") == plant) & pl.col("Year").is_in(valid_years)
    for plant, valid_years in partial_year_dict.items()
]
# combine the expressions with OR in between
combined_expr = exprs[0]
for expr in exprs[1:]:
    combined_expr = combined_expr | expr

# add the default plant filter (ie keep everything if EMI_name not in dict)
valid_wind_years_filter = combined_expr | (~pl.col("EMI_Name").is_in(list(partial_year_dict.keys())))

# Apply it
emi_timeslice_wind_valid = (
    emi_timeslice_wind
    # need to add a year 
    .with_columns(pl.col("DateTime").dt.year().alias("Year"))
    .filter(valid_wind_years_filter)
)

# just testing that this worked (it did)
# print(emi_timeslice_wind_valid[["EMI_Name", "Year"]].unique().sort(["EMI_Name", "Year"]))

#endregion

#region CREATE_AGGREGATE_DATASETS ------------------------------------------------------------

# get annual avg cap factors 
emi_avg_cf_by_plant = (emi_timeslice_wind_valid                       
                       .group_by(["EMI_Name"])
                       .agg([pl.max("CapacityMW").alias("CapacityMW"),
                             pl.sum("Value_MWh").alias("Value_MWh"),
                             pl.mean("Value_MWh").alias("Average_MWh"),
                             pl.count("DateTime").alias("Hours")])            
                             ).with_columns([(pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")])

#aggregate by timeslice and plant
emi_ts_cf_by_plant = (emi_timeslice_wind_valid
      .group_by(["EMI_Name","Timeslice"])
      .agg([pl.max("CapacityMW").alias("CapacityMW"),
            pl.sum("Value_MWh").alias("Value_MWh"),
            pl.mean("Value_MWh").alias("Average_MWh"),
            pl.count("DateTime").alias("Hours")])            
            ).with_columns([(pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")])


emi_ts_cf_by_island = (
    emi_timeslice_wind_valid
    # .filter(pl.col("Year") == 2024)                    
    .with_columns([pl.when(pl.col("EMI_Name").is_in(["KaiweraDowns","white_hill"])).
                   then(pl.lit("SI")).
                   otherwise(pl.lit("NI")).
                   alias("Region")])                   
    # get sum of capacity and output per hour 
    .group_by(["Region", "DateTime", "Hour", "Timeslice"])
    .agg([pl.sum("CapacityMW").alias("CapacityMW"),pl.sum("Value_MWh").alias("Value_MWh")])
    # then aggregate by timeslice. Here the capacity is the mean over the years where that timeslice is available. 
    .group_by(["Region","Timeslice"])
    .agg([pl.mean("CapacityMW").alias("CapacityMW"),pl.mean("Value_MWh").alias("Average_MWh")])
    # can now calculate the capacity factor
    .with_columns([(pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")])
)


# aggregate by region and plant 
    
emi_avg_cf_by_island = (emi_timeslice_wind_valid                        
    # .filter(pl.col("Year") == 2024)                    
    .with_columns([pl.when(pl.col("EMI_Name").is_in(["KaiweraDowns","white_hill"])).
                   then(pl.lit("SI")).
                   otherwise(pl.lit("NI")).
                   alias("Region")])                   
    # get sum of capacity and output per hour 
    .group_by(["Region", "DateTime", "Hour", "Timeslice"])
    .agg([pl.sum("CapacityMW").alias("CapacityMW"),pl.sum("Value_MWh").alias("Value_MWh")])
    # then aggregate by region. Here the capacity is the mean over the years where that timeslice is available. 
    .group_by(["Region"])
    .agg([pl.mean("CapacityMW").alias("CapacityMW"),pl.mean("Value_MWh").alias("Average_MWh")])
    # can now calculate the capacity factor
    .with_columns([(pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")])
)

# add the average capacity factor for plotting annuals on top of the main bars 
emi_ts_cf_by_island = (emi_ts_cf_by_island
                       .join(emi_avg_cf_by_island[["Region", "Capacity_Factor"]]
                             .rename({"Capacity_Factor": "Weighted_CF"}),
                             on="Region", how="left"))
                        
emi_peak_availability = (emi_timeslice_wind_valid
                         .filter(pl.col("Hour") == 18) # 6pm 
                         .filter(pl.col("Trading_Date").dt.month().is_in([6,7,8])) # winter months 
                         # we want total generation and capacity per each slice, but we don't care about the plants
                         .group_by(["DateTime"])
                         .agg(pl.sum("CapacityMW"), pl.sum("Value_MWh"))
                         # everything is just one hour so this is a simple division
                         .with_columns((pl.col("Value_MWh")/pl.col("CapacityMW")).alias("Capacity_Factor"))
)

#endregion

#region PLOT_CF_BY_PLANT ------------------------------------------------------------
                                     
# adding a season colour dict that we can add to the plot 
season_colors = {
    "FAL": "orange",
    "SPR": "green",
    "WIN": "lightblue",
    "SUM": "red"
}

plot_plant_timeslice_cfs = False

if plot_plant_timeslice_cfs:

    # add the average capacity factor for plotting annuals on top of the main bars 
    emi_ts_cf_by_plant = (emi_ts_cf_by_plant
                          .join(emi_avg_cf_by_plant[["EMI_Name", "Capacity_Factor"]]
                                 .rename({"Capacity_Factor": "Weighted_CF"}),
                                   on="EMI_Name", how="left"))

    # Add season column to timeslice dataframe
    pdf = emi_ts_cf_by_plant.to_pandas()
    pdf = pdf.sort_values(["EMI_Name", "Timeslice"])
    pdf["Season"] = pdf["Timeslice"].str[:3]

    # Facet plot
    g = sns.FacetGrid(pdf, col="EMI_Name", col_wrap=6, height=3.5)
    def facet_barplot_with_line(data, **kwargs):
        # Barplot with seasonal coloring
        sns.barplot(
            data=data,
            x="Capacity_Factor",
            y="Timeslice",
            hue="Season",
            palette=season_colors,
            dodge=False,
            legend=False,
            **kwargs
        )

        # Add average: first draw reference line 
        avg = data["Weighted_CF"].iloc[0]
        plt.axvline(avg, color="black", linestyle="--", linewidth=1)
        # Then add label 
        plt.text(
            x=avg + 0.005, y=0.5,  # Adjust x/y for aesthetics
            s=f"avg: {avg:.2f}",
            va='center',
            fontsize=10,
            color="black"
        )

    g.map_dataframe(facet_barplot_with_line)
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Capacity Factor", "Timeslice")
    g.tight_layout()
    plt.show()

#endregion

#region PLOT_CF_BY_ISLAND ------------------------------------------------------------


plot_island_timeslice_cfs = False
if plot_island_timeslice_cfs:

    # Add season column to timeslice dataframe
    pdf = emi_ts_cf_by_island.to_pandas()
    pdf = pdf.sort_values(["Region", "Timeslice"])
    pdf["Season"] = pdf["Timeslice"].str[:3]

    # Facet plot
    g = sns.FacetGrid(pdf, col="Region", col_wrap=2, height=3.5)
    def facet_barplot_with_line(data, **kwargs):
        # Barplot with seasonal coloring
        sns.barplot(
            data=data,
            x="Capacity_Factor",
            y="Timeslice",
            hue="Season",
            palette=season_colors,
            dodge=False,
            legend=False,
            **kwargs
        )

        # Add average: first draw reference line 
        avg = data["Weighted_CF"].iloc[0]
        plt.axvline(avg, color="black", linestyle="--", linewidth=1)
        # Then add label 
        plt.text(
            x=avg + 0.005, y=0.5,  # Adjust x/y for aesthetics
            s=f"avg: {avg:.2f}",
            va='center',
            fontsize=10,
            color="black"
        )

    g.map_dataframe(facet_barplot_with_line)
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Capacity Factor", "Timeslice")
    g.tight_layout()
    plt.show()

#endregion

#region COMPARE_TO_TIMES_2 ------------------------------------------------------------

compare_version_wind_afs = (emi_ts_cf_by_island.with_columns([pl.lit("EMI_DATA").alias("Source")]))


# ensure the variables match and are in the same order 
comparison_variables = ["Region", "Timeslice", "Capacity_Factor", "Weighted_CF", "Source"]
# add the times 2 data
compare_version_wind_afs = pl.concat([
    compare_version_wind_afs.select(comparison_variables),
    times_2_wind_af.select(comparison_variables)
])
# plot (if switch is on)

plot_source_cf_comparison = False
if plot_source_cf_comparison:

    # Add season column to timeslice dataframe
    pdf = compare_version_wind_afs.to_pandas()
    pdf = pdf.sort_values(["Region", "Timeslice", "Source"])
    pdf["Season"] = pdf["Timeslice"].str[:3]

    # Facet plot
    g = sns.FacetGrid(pdf, col="Source", row = "Region", height=3.5)
    def facet_barplot_with_line(data, **kwargs):
        # Barplot with seasonal coloring
        sns.barplot(
            data=data,
            x="Capacity_Factor",
            y="Timeslice",
            hue="Season",
            palette=season_colors,
            dodge=False,
            legend=False,
            **kwargs
        )

        # Add average: first draw reference line 
        avg = data["Weighted_CF"].iloc[0]
        plt.axvline(avg, color="black", linestyle="--", linewidth=1)
        # Then add label 
        plt.text(
            x=avg + 0.005, y=0.5,  # Adjust x/y for aesthetics
            s=f"avg: {avg:.2f}",
            va='center',
            fontsize=10,
            color="black"
        )

    g.map_dataframe(facet_barplot_with_line)
    g.set_titles(col_template="{col_name}", row_template="{row_name}")
    g.set_axis_labels("Capacity Factor", "Timeslice")
    g.tight_layout()
    plt.show()

#endregion 

#region PEAK_AVAILABILITY ---------------------------------------------------


hist_data = emi_peak_availability["Capacity_Factor"].to_numpy()

plot_peak_availability = False 

if plot_peak_availability:
    # Compute histogram
    counts, bins = np.histogram(hist_data, bins=30)
    total = counts.sum()
    percentages = counts / total * 100

    # Midpoints of bins
    bin_centers = (bins[:-1] + bins[1:]) / 2

    # Plot histogram
    plt.bar(bin_centers, percentages, width=(bins[1] - bins[0]), edgecolor='black')
    plt.title("6pm winter capacity factors (onshore wind)")
    plt.xlabel("Capacity Factor")
    plt.ylabel("Likelihood (%)")

    # Compute summary statistics
    mean_val = np.mean(hist_data)
    p10 = np.percentile(hist_data, 10)
    p50 = np.percentile(hist_data, 50)
    p90 = np.percentile(hist_data, 90)

    # Add vertical lines
    plt.axvline(mean_val, color='black', linestyle='--', linewidth=2, label=f'Mean ({mean_val:.2f})')
    plt.axvline(p10, color='green', linestyle=':', linewidth=2, label=f'10th pct ({p10:.2f})')
    plt.axvline(p50, color='blue', linestyle=':', linewidth=2, label=f'Median ({p50:.2f})')
    plt.axvline(p90, color='red', linestyle=':', linewidth=2, label=f'90th pct ({p90:.2f})')

    # Add legend
    plt.legend()
    plt.show()

#endregion

#region OUTPUT_RESULTS  --------------------------------------------------------
emi_ts_cf_by_island = emi_ts_cf_by_island.sort(["Region", "Timeslice"])
emi_ts_cf_by_island.write_csv(f"{output_location}/emi_ts_cf_by_island.csv")


#endregion --------------------------------------------------------



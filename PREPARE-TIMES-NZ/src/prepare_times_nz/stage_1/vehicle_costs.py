CATEGORY_TO_VEHICLE_CLASS = {
    "LPV": ["Compact", "Midsize", "Midsize SUV", "Small SUV"],
    "LCV": [
        "Pickup",
        "Class 2 Medium Van",
        "Class 3 Medium Pickup",
        "Class 3 Medium School",
        "Class 3 Medium Van",
    ],
    "Light Truck": [
        "Class 4 Medium Box",
        "Class 4 Medium Service",
        "Class 4 Medium StepVan",
        "Class 5 Medium Utility",
        "Class 6 Medium Box",
        "Class 6 Medium Construction",
        "Class 6 Medium StepVan",
    ],
    "Medium Truck": [
        "Class 7 Medium Box",
        "Class 7 Medium School",
        "Class 7 Tractor DayCab",
    ],
    "Heavy Truck": [
        "Class 8 Beverage DayCab",
        "Class 8 Drayage DayCab",
        "Class 8 Longhaul Sleeper",
        "Class 8 Regional DayCab",
        "Class 8 Vocational Heavy",
    ],
    "Bus": ["Class 8 Transit Heavy"],
}

TECH_TO_POWERTRAIN = {
    "Battery Electric": "Battery Electric",
    "Diesel Hybrid": "Diesel Hybrid",
    "Diesel ICE": "Diesel",
    "Dual Fuel": "Dual Fuel",
    "Hydrogen Fuel Cell": "Hydrogen Fuel Cell",
    "Petrol Hybrid": "Gasoline Hybrid",
    "Petrol ICE": "Gasoline",
    "Plug-in Hybrid": "Plug-in Hybrid",
    "LPG": "Natural Gas",
}


def get_rail_columns(df):
    """Selects and renames relevant columns from the pj_rail dataframe"""
    df = df[["Fuel Type", "Transport", "End-use Energy (output energy)"]].rename(
        columns={
            "Fuel Type": "fueltype",
            "Transport": "vehicletype",
            "End-use Energy (output energy)": "pjvalue",
        }
    )
    return df

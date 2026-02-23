MOTIVE_GROUP_MAP = {
    "BEV": ("Electricity", "BEV"),
    "Petrol_Hybrid": ("Petrol", "ICE Hybrid"),
    "Diesel_ICE": ("Diesel", "ICE"),
    "Petrol_ICE": ("Petrol", "ICE"),
    "LPG_ICE": ("LPG", "ICE"),
}


FUEL_SPLIT_MAP = {
    ("LPV", "PHEV"): [
        {"fueltype": "Petrol", "technology": "PHEV", "fraction": 0.4},
        {"fueltype": "Electricity", "technology": "PHEV", "fraction": 0.6},
    ]
}


REGIONAL_SPLIT = {
    "LPV": {"NI": 0.73, "SI": 0.27},
    "LCV": {"NI": 0.73, "SI": 0.27},
    "Motorcycle": {"NI": 0.73, "SI": 0.27},
    "Bus": {"NI": 0.73, "SI": 0.27},
    "Light Truck": {"NI": 0.73, "SI": 0.27},
    "Medium Truck": {"NI": 0.73, "SI": 0.27},
    "Heavy Truck": {"NI": 0.73, "SI": 0.27},
    ("Rail Freight", "Diesel"): {"NI": 0.74, "SI": 0.26},
    ("Rail Freight", "Electricity"): {"NI": 1.0, "SI": 0.0},
    ("Passenger Rail", "Diesel"): {"NI": 1.0, "SI": 0.0},
    ("Passenger Rail", "Electricity"): {"NI": 0.74, "SI": 0.26},
    "Domestic Aviation": {"NI": 0.58, "SI": 0.42},
    "International Aviation": {"NI": 0.80, "SI": 0.20},
    "Domestic Shipping": {"NI": 0.34, "SI": 0.66},
    "International Shipping": {"NI": 0.72, "SI": 0.28},
}


TRUCK_NAMES = {
    "MedTr": "Light Truck",
    "HevTr": "Medium Truck",
    "VHevTr": "Heavy Truck",
}


FUEL_SHARE = {
    ("LPV", "Petrol", "PHEV"): {"fuelshare": 0.40},
    ("LPV", "Electricity", "PHEV"): {"fuelshare": 0.60},
    ("Heavy Truck", "Diesel", "Dual Fuel"): {"fuelshare": 0.70},
    ("Heavy Truck", "Hydrogen", "Dual Fuel"): {"fuelshare": 0.30},
    ("NI", "Passenger Rail", "Electricity"): {"fuelshare": 0.79},
    ("NI", "Passenger Rail", "Diesel"): {"fuelshare": 0.21},
    ("NI", "Rail Freight", "Diesel"): {"fuelshare": 0.97},
    ("NI", "Rail Freight", "Electricity"): {"fuelshare": 0.03},
}


MJ_PER_LITRE = {
    "Petrol": 35.18,
    "Diesel": 38.49,
    "LPG": 26.3735798,
}

# ================================================================================================ #
# Description: load_data.r loads the data from the output_combined_df_vA_B_C.csv file for the Shiny app.
#
# Input: 
#
# Processed model output:
#   "output_combined_df_vA_B_C.csv" - outputs from Tui and Kea models, processed for Shiny app
# 
# Schema inputs
#   "schema.csv" For restricting TIMES model and 'natural language' translations from TIMES codes                
#   "schema_colors.csv"  To specify the color and shape for each Fuel and Technology              
#   "schema_technology.csv" For defining the Technology groups 
# 
# Assumption and Key insight data
#   "assumptions.csv"                      The assumption data            
#   "key_insight.csv"                      The Key-Insight data
#   "assumptions_insight_comments.csv"     Plot commentary
# 
# Captions and pup-ups data
#   "caption_table.csv"                # Pop-up caption
#   "intro.csv"                         # Text for introduction to tour     
# 
# Output: Data for App
#
# History (reverse order): 
# 1 June 2024 WC removed the data cleaning - this script now only loads the data and saves to rda file
# 17 May 2021 KG v1 - Wrote the deliverable source code 
# ================================================================================================ #

# Load libraries required
library(readr)
library(magrittr) #allows piping (more available options than just those in dplyr/tidyr)
library(tidyverse) # data manipulation, gather and spread commands
library(conflicted)
options(scipen=999) # eliminates scientific notation

conflicts_prefer(dplyr::filter)

times_nz_version <- "2.1.2"
times_nz_version_str <- gsub("\\.", "_", times_nz_version)

# Reading in intro Data --------------------------
intro <- read_delim("..\\data\\intro.csv", delim = ";", col_types = cols())

# Schema inputs read from CSV
print("schema_colors.csv")
schema_colors <- read_csv("..\\data\\schema_colors.csv", locale = locale(encoding = "UTF-8"), show_col_types = FALSE)
print("caption_table.csv")
caption_list <- read_csv("..\\data\\caption_table.csv", locale = locale(encoding = "UTF-8"), show_col_types = FALSE)
print("schema_technology.csv")
schema_technology <- read_csv("..\\data\\schema_technology.csv", locale = locale(encoding = "UTF-8"), show_col_types = FALSE)
print("output_combined_df_vA_B_C.csv")
combined_df <- read_csv(paste0("..\\..\\TIMES-NZ-OUTPUT-PROCESSING\\data\\output\\", "output_combined_df_v", times_nz_version_str, ".csv"), locale = locale(encoding = "UTF-8"), show_col_types = FALSE)

# List generation
hierarchy_list <- combined_df %>%
  distinct(Sector, Subsector, Enduse, Technology, Unit, Fuel) %>%
  arrange(across(everything()))

fuel_list <- distinct(hierarchy_list, Fuel) # Fuel list
sector_list <- distinct(hierarchy_list, Sector) # Sector list

# Reading in assumption data
print("assumptions.csv")
assumptions_df <- read_csv("..\\data\\assumptions.csv") %>%
  gather(Period, Value, `2022`:`2060`) %>%
  mutate(across(c(tool_tip_pre, tool_tip_trail), ~replace_na(., ""))) %>%
  # Changing total GDP 2022 period to 2018
  mutate(Period =  ifelse(Parameter == "Total GDP" & Period == 2022, 2018, Period))

assumptions_list <- distinct(assumptions_df, Parameter) %>% pull(Parameter)

# Reading in insight data to extract assumptions for charting
print("key_insight.csv")
insight_df <- read_csv("..\\data\\key_insight.csv", locale = locale(encoding = "UTF-8"), show_col_types = FALSE) %>%
  gather(Period, Value, `2018`:`2060`)

insight_list <- distinct(insight_df, Parameter) %>% pull(Parameter)

# Reading in assumption key insight comments
print("assumptions_insight_comments.csv")
Assumptions_Insight_df <- read_csv("..\\data\\assumptions_insight_comments.csv", locale = locale(encoding = "UTF-8"), show_col_types = FALSE)

# Ordered attributes
order_attr = c("Emissions","Fuel Consumption", "End Use Demand", "Annualised Capital Costs", 
               "Number of Vehicles", "Distance Travelled", "Electricity Generation",   
               "Gross Electricity Storage", "Grid Injection (from Storage)", 
               "Feedstock")

# Create the R data set for Shiny to use
save(combined_df, # data for charting
     fuel_list,  # list of fuel
     sector_list,  # list of sectors
     assumptions_df,  # data behind assumptions
     assumptions_list,  # list of assumptions for input$assumptions drop-down
     insight_df,  # data behind insight
     insight_list,  # list of insight for input$insight drop-down
     Assumptions_Insight_df, # Add Assumptions Insight comments
     schema_colors, # Color scheme
     order_attr, # Ordered attribute
     caption_list, # Add caption list
     intro, # Add introduction tour comments
     file = "../app/data/data_for_shiny.rda")

print("Data for Shiny app has been saved to data_for_shiny.rda")

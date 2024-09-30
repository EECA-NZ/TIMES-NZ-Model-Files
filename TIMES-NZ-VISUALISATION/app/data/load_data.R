# Load data objects from rda file
load("data/data_for_shiny.rda")

# Replace NAs in main dataset with missing
combined_df <- combined_df %>% 
  mutate(across(where(is.character), ~ifelse(is.na(.), "", .)))

# # Create 'hierarchy' file. Based on all combinations of dropdowns.
# hierarchy <- combined_df %>% 
#   distinct(data_group, Sector, Attribute, Technology, Fuel) %>% 
#   arrange(across()) #%>% 
#   # mutate(across(where(is.character), ~ifelse(is.na(.), "", .)))



# Create 'hierarchy' file. Based on all combinations of dropdowns.
hierarchy <- combined_df %>%
  distinct(
    Sector, 
    Subsector, 
    Enduse, 
    Technology, 
    Unit, 
    Parameters
  ) %>%
  union_all(
    distinct(
      .,
      Sector, 
      Enduse, 
      Technology, 
      Unit, 
      Parameters
    ) %>% 
      mutate(
        Subsector = "All Subsectors"
      )
  ) %>% 
  union_all(
    distinct(
      .,
      Sector, 
      Subsector, 
      Technology, 
      Unit, 
      Parameters
    ) %>% 
      mutate(
        Enduse = "All End Use"
      )
  ) %>% 
  union_all(
    distinct(
      .,
      Sector, 
      Subsector, 
      Enduse, 
      Unit, 
      Parameters
    ) %>% 
      mutate(
        Technology = "All Technology"
      )
  ) %>% 
  arrange(across()) 

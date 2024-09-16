# This script is used to deploy the App
library(rsconnect) # Library needed for the App

deployApp(
  # Name of Account 
  account = "eeca-nz", 
  
  # App Name
  appName = "TIMES_V2",
  
  # The file to be uploaded
  appFiles = c("data", 
               "functions.R" ,
               "renv\\activate.R",
               "renv.lock" ,
               "rsconnect", 
               "server.R" ,
               "ui.R",
               "www", 
               "data/data_for_shiny.rda",
               "data\\load_data.R"),
  # Force Update
  forceUpdate = TRUE)
# This script deploys the RShiny app to the RStudio Connect server.
# It is designed to be run from the command line using the Rscript
# command, typically by one of the main orchestration scripts. The
# script takes a version string as an argument, which is used to 
# name the deployed app. Be careful to ensure that the version string
# is unique and follows the naming conventions of the deployment.

library('renv')

# Function to get the directory of the current script
get_script_dir <- function() {
  all_args <- commandArgs(trailingOnly = FALSE)
  script_arg <- all_args[grep("--file=", all_args)]
  if (length(script_arg) > 0) {
    return(dirname(sub("--file=", "", script_arg[1])))
  } else {
    stop("Cannot determine script path. Ensure script is run with 'Rscript --file=path_to_script'.")
  }
}

# Set the working directory to the visualization tool's base directory to load the renv environment
vis_base_dir <- file.path(get_script_dir(), "..")
renv::load(vis_base_dir)
setwd(file.path(vis_base_dir, "app"))

# Load remaining libraries
library(rsconnect)   # For app deployment
library(dotenv)      # For loading environment variables

# Retrieve command-line arguments
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("No version string provided. Usage: Rscript deployApp.R <version_string>", call. = FALSE)
}

# Process the version string for naming the app
times_nz_version_str <- gsub("\\.", "_", args[1])

# Load environment variables from .env file
dotenv::load_dot_env('../.env')

# Ensure essential environment variables are available
if (is.na(Sys.getenv("ACCOUNT")) || is.na(Sys.getenv("TOKEN")) || is.na(Sys.getenv("SECRET"))) {
  stop("Missing required environment variables: ACCOUNT, TOKEN, or SECRET.")
}

# Set account info using environment variables
rsconnect::setAccountInfo(
  name = Sys.getenv("ACCOUNT"),
  token = Sys.getenv("TOKEN"),
  secret = Sys.getenv("SECRET")
)

# Deploy the app with the version number in the app name
deployApp(
  account = Sys.getenv("ACCOUNT"),
  appName = paste0("TIMES_V", times_nz_version_str),
  appFiles = c(
    "data",
    "functions.R",
    "../renv/activate.R",
    "../renv.lock",
    "rsconnect",
    "server.R",
    "ui.R",
    "www",
    "data/data_for_shiny.rda",
    "data/load_data.R"
  ),
  forceUpdate = TRUE
)
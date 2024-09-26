get_script_dir <- function() {
  # Fetch all command arguments
  all_args <- commandArgs(trailingOnly = FALSE)
  # Look for the argument that's the script's own name
  script_arg <- all_args[grep("--file=", all_args)]
  # Extract the script path
  if (length(script_arg) > 0) {
    script_path <- sub("--file=", "", script_arg[1])
    return(dirname(script_path))
  } else {
    stop("Script path cannot be determined. Ensure the script is run with 'Rscript --file=path_to_script'")
  }
}

# Set the working directory to the script's directory
script_dir <- get_script_dir()
setwd(script_dir)

shiny::runApp("../app")
# TIMES-NZ Data Visualization App
This folder contains the README, source code and data behind the TIMES-NZ visualisation tool. The app is located on the [shinyapps.io](https://shinyapps.io) platform and it can be viewed through [EECA's website](http://www.eeca.govt.nz/TIMES-NZ).

## Background
The New Zealand Energy Scenarios Times-NZ website presents model insights for the latest TIMES-NZ scenarios to contribute to decision making by businesses and Government. The New Zealand Energy Scenarios TIMES-NZ 2.0 visualisation tool allows users to explore how New Zealand energy futures may look like based on outputs from the [New Zealand Energy Scenarios TIMES-NZ 2.0 model](https://github.com/EECA-NZ/TIMES-NZ-Model-Files). A detailed description of the  model and the app is found on the [EECA website](https://www.eeca.govt.nz/New-Zealand-Energy-Scenarios-TIMES-NZ-2.pdf).

## Software requirements
- [R (v4.4+)](https://cran.r-project.org/bin/windows/base/)
- [Rtools44](https://cran.r-project.org/bin/windows/Rtools/)

## Before running the app

It is assumed that the steps outlined in the README files in the following folders have already been done:
* `PREPARE-TIMES-NZ`
* `TIMES-NZ`
* `TIMES-NZ-GAMS`
* `TIMES-NZ-OUTPUT-PROCESSING`

Having done the above steps, the data loaded by the app locally can be updated (step 1 below). After this, the app run locally using the `shiny::runApp()` command should present the latest verion of the model.

## To run the app
To restore the required packages and run the app, follow the steps below:

* open the `TIMES_shiny_app.Rproj` project file. This will open the project in an RStudio window. (Alternatively, enter the `TIMES-NZ-VISUALISATION` folder and run `R.exe` in the console to open an interactive R session.)
* run `renv::restore()` in the console to install all required packages.

There are two R steps required to run this app:
1. The data loading script (`Load_Data.R`) which is in the `scripts` folder.
	* run `source('Load_Data.R', echo=TRUE)` in the console to generate the required data. This data is saved as `data_for_shiny.rda` in the `app/data` folder.
2. The Shiny app project (`TIMES_shiny_app.Rproj`) which is in the app folder.
	* To run:
		* open the `TIMES_shiny_app.Rproj` project file in the root folder. (Alternatively, enter the `TIMES-NZ-VISUALISATION` folder and run `R.exe` in the console to open an interactive R session.)
		* If you haven't already, run `renv::restore()` to install all required packages for the app.
		* run `shiny::runApp('app')` in the console to run the app locally.

## Deploy app
To deploy the app, run `source('Deploy_App.R', echo=TRUE)` in the console. The user will need to configure the `rsconnect` package to use EECA's shinyapps.io account. A detailed description on how to configure `rsconnect` is located [here](https://shiny.rstudio.com/articles/shinyapps.html). Before running the `Deploy_App.R` script, the user will need to set up EECA's shinyapps.io account using the `rsconnect` package. The shinyapps.io site automatically generates a secret token, which the `rsconnect` package can use to link the shinyapps.io account to your local set-up. Step by step instructions can be found [here](https://shiny.rstudio.com/articles/shinyapps.html) under the **Configure rsconnect** section.
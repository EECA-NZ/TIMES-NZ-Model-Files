# Description: ui.R defines the UI component of the Shiny app, such as the buttons, pickers, menus, 
# etc. ui.R also loads all the required libraries, the datasets and the functions. 
#
# Input: www/*
# 
# Output: Generates the front facing app that the user can interface with. 
#
# Author: Kenny Graham (KG) and Conrad MacCormick (CM)
#
# Dependencies: 
# The libraries that are required by the ui.R are version controlled using renv. Refer to 
# https://rstudio.github.io/renv/articles/renv.html on restoring the state of the environment 
# using the lock file. use renv::restore() to restore
# 
# ui.R also depends on three other source files: 
# - server.R
# - load_data.R
# - functions.R
#
# ui.R also depends on css file to define the layout of the web app, and the components defined 
# in the folder www, e.g.,  www/css/styles.css are required for .css formatting of the UI 
# elements in the app when it is loaded. 
#  
# Notes:
# 
# Issues:
#
# History (reverse order): 
# 17 May 2021 KG v1 - Wrote the deliverable source code 
# 25 May 2021 KG Deployed App
# ================================================================================================ #


# Load libraries
# These are the libraries needed for the App. 
# All the these libraries and depended packages are archived in the environment
# To restore the the archived libraries one needs to run the line below
#  renv::restore()


library(shiny)
library(shinyBS)
library(bslib)
library(shinythemes)
library(shinyBS)
library(highcharter)
library(tidyverse)
library(readr)
library(stringr)
library(shinyWidgets) # For the fancy radio buttons
library(shinyhelper)
library(rintrojs) # Needed for the introductory tour
library(shinyjs)

# Source script that loads data
# This is where the .rda file is loaded and the hierarchy dataframe is created
source("data/load_data.R")


# Load the plot functions and the helper functions
source("functions.R")



# Start of the user interface code
ui <- navbarPage(
  
  # Page title. Currently set to black since it is not needed
  title = "",
  

  # USing the readable theme
  theme = shinytheme("readable"),
  
  #########################################
  ############# Background tab ############
  #########################################
  tabPanel(
    
    # Title of the tab
    "Overview",
    
    # Defining the background content
    fluidRow(
      
      column(
        
        width = 12,
        
        h3("New Zealand Energy Scenarios TIMES-NZ 2.0"),
        
        # The background text
        HTML("Climate change is one of the most urgent environmental issues of our time. 
        Almost 41% of New Zealand’s total greenhouse gas emissions come from our 
        energy use and the challenge is to get this number down. The New Zealand 
        Energy Scenarios TIMES-NZ 2.0 website presents model insights for the 
        latest TIMES-NZ scenarios to contribute to decision making in businesses 
        and Government. 
        TIMES-NZ 2.0 was developed by  <a href='https://www.eeca.govt.nz/' 
        style='color:#333333; '>EECA</a> in partnership with the  
        <a href='https://www.bec.org.nz/' style='color:#333333;'>BusinessNZ 
        Energy Council (BEC)</a>   and <a href='https://www.psi.ch/en' 
        style='color:#333333;'> The Paul Scherrer Institut</a>. <br><br>
        Welcome to the New Zealand Energy Scenarios TIMES-NZ 2.0 visualisation tool. 
        This tool will allow you to explore how New Zealand energy futures may 
        look like based on outputs from the New Zealand Energy Scenarios TIMES-NZ 
        2.0 model." ),
              

        

    
    
    # Adding the Energy System Scenarios row
    fluidRow(
      
      column(
        
        width = 12,
        
        h3("Scenarios"),
        
        HTML("TIMES-NZ 2.0 includes two
        scenarios Kea (Cohesive) and T\u16b\u12b (Individualistic): <br><br>"),
        
        # Adding Kea and Tui comment 
        HTML("<div class='wrapper'>
                
        <div class='box a'><strong>Kea </strong> represents a scenario where 
        climate change is prioritised as the most pressing issue and New Zealand 
        deliberately pursues cohesive ways to achieve a low-emissions economy.</div>
       
        
        <div class='box b'><strong>T\u16b\u12b </strong>represents a scenario 
        where climate change is an important issue to be addressed as one of 
        many priorities, with most decisions being left up to individuals and 
        market mechanisms.  </div>
        </div>"
     
             
        )

        
      )),
      )
      
      
    ),
    
    
    # Adding the Assumption and Key insight plots
    fluidRow(
      
      column(
        
        width = 12,

        HTML("<br><br><br>"),
        
        # Adding a sidebar for selection
        sidebarLayout(
          
          sidebarPanel = sidebarPanel(
            
            width = 3,
            
            # Adding switch button
            # Adding an introduction tour
            introBox(data.step = 1, data.intro = intro$text[1],
                     
                     # Used spa to add tooltip info
                     span(switchButton(inputId = "Insght_Switch",
                                       
                                       label = NULL, 
                                       
                                       value = TRUE, col = "RG", type = "OO"),
                          
                          
                          # Tooltip info 
                          title="Switch to show Key Insight or Assumptions")),
            
            
            # Adding the dropbox 
            span(uiOutput("Assumption_drop_downs"), 
                 
                 title="Dropdown for selecting Parameter")
            
          ),
          
          # Adding the key insight and assumtption plot 
          mainPanel = mainPanel(
            
            width = 9,
            
            fluidRow(
              
              column(
                
                width = 12,
                
                highchartOutput("assumptions_plot",height = 500)
                
                
              )
            )
          )
        )
      )
    )
    
    
    
  ),
  
  
  #########################################
  ########## Data Explorer tab ############
  #########################################
  tabPanel(
    
    "Data Explorer",
    
    # The sidebarLayout is a specific built-in layout type which takes 
    # two arguments: a sidebarPanel and a mainPanel.
    
    
    sidebarLayout(
      
      # Creating the chart type selection
      sidebarPanel = sidebarPanel(
        
        width = 3,
        
        introBox(data.step = 2, data.intro = intro$text[2],
                 
                 uiOutput("radioGroup")
                 
          ),
        
        
        
        # Adding tech and fuel switch
        introBox(data.step = 3, data.intro = intro$text[3],
        span(switchButton(inputId = "Tech_Fuel_Switch",

                          label = NULL,

                          value = TRUE, col = "RG", type = "TF"),
             
             # uiOutput("switch"),

             title=HTML("Toggle to switch between <b>Plot by Fuels</b> and <b>Plot by Technologies</b>")
        )),

        
        introBox(data.step = 4, data.intro = intro$text[4],
                 span(uiOutput("plot_by_dropdowns"),
                      title=HTML("Dropdown to select between Fuels or Technologies in groups or separated")  
                      )
        ),
        
        

        # Intro-tour for drilldowns
        introBox(data.step = 5, data.intro = intro$text[5],
                 
                 # This is where the drop downs are inserted in to the UI. 
                 # They are created dynamically on the server side.  
                 # The metric dropdown is added separately 
                 uiOutput("drop_downs")),
        
        
        # Intro-tour for Metric
        introBox(data.step = 6, data.intro = intro$text[6],
                 
                 # Adding the metric dropdown
                 selectInput(
                   
                   "unit",
                   
                   label = NULL,
                   
                   choices = unique(sort(hierarchy$Parameters))
                   
                 ))
        

        
      ),
      
      # Adding the Sector tabs
      mainPanel = mainPanel(
        
        # Using this to hide the error
        # tags$style(type="text/css",
        #            ".shiny-output-error { visibility: hidden; }",
        #            ".shiny-output-error:before { visibility: hidden; }"),
        
        width = 9,
        
        introBox(data.step = 7, data.intro = intro$text[7],
                 
                 tabsetPanel(
                   
                   # This is needed so that we can reference when someone clicks a tab
                   id = "tabs", 
                   
                   type = "pills",
                   
                   # Adding All Sector tab
                   tabPanel(
                     
                     "All Sectors",
                     
                     # This is the value (of input$tabs) returned when the user 
                     # clicks the 'Overview' tab
                     value = "Overview", 
                     
                     fluidRow(
                       

                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_overview", inline = TRUE)),

                         
                         highchartOutput("overview_kea") 
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b", ),
                         
                         highchartOutput("overview_tui")
                         
                       )
                       
                     )
                   ),
                   
                   tabPanel(
                     
                     "Transport",
                     
                     value = "Transport",
                     
                     fluidRow(
                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_transport", inline = TRUE)),
                         
                         highchartOutput("transport_kea")
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b"),
                         
                         highchartOutput("transport_tui")
                       )
                     )
                     
                     
                   ),
                   
                   
                   
                   
                   # Adding industry stuff
                   tabPanel(
                     
                     "Industrial",
                     
                     value = "Industry",
                     
                     fluidRow(
                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_industry", inline = TRUE)),
                         
                         highchartOutput("industry_kea")
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b"),
                         
                         highchartOutput("industry_tui")
                       )
                     )
                     
                     
                   ),
                   
                   
                   # Adding Commercial stuff
                   tabPanel(
                     
                     "Commercial",
                     
                     value = "Commercial",
                     
                     fluidRow(
                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_commercial", inline = TRUE)),
                         
                         highchartOutput("Commercial_kea")
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b"),
                         
                         highchartOutput("Commercial_tui")
                       )
                     )
                     
                     
                     
                   ),
                   
                   # Adding Residential stuff
                   tabPanel(
                     "Residential",
                     
                     value = "Residential",
                     
                     fluidRow(
                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_residential", inline = TRUE)),
                         
                         highchartOutput("Residential_kea")
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b"),
                         
                         highchartOutput("Residential_tui")
                       )
                     )
                     
                   ),
                   
                   # Adding Agriculture stuff
                   tabPanel(span("Agriculture", title="Agriculture, Forestry and Fishing"),

                            value = "Agriculture",
                            
                            fluidRow(
                              
                              # Plot outputs
                              column(
                                
                                width = 12,
                                
                                h3("Kea", uiOutput("info_agriculture", inline = TRUE)),
                                
                                highchartOutput("Agriculture_kea")
                                
                              ),
                              
                              column(
                                
                                width = 12,
                                
                                h3("T\u16b\u12b"),
                                
                                highchartOutput("Agriculture_tui")
                              )
                            )
                            
                   ),
                   
                   
                   # Adding Other stuff
                   tabPanel(
                     
                     span("Electricity", title = "Electricity Generation"),

                     value = "Other",
                     
                     fluidRow(
                       
                       # Plot outputs
                       column(
                         
                         width = 12,
                         
                         h3("Kea", uiOutput("info_other", inline = TRUE)),
                         
                         highchartOutput("Other_kea")
                         
                       ),
                       
                       column(
                         
                         width = 12,
                         
                         h3("T\u16b\u12b"),
                         
                         highchartOutput("Other_tui")
                       )
                     )
                     
                   )
                   
                 ))
        
      )
      
    ),
    # This initiates the introjs functionality
    introjsUI(),
    
  ),  
  
  
  ##############################
  ######### About tab ##########
  ##############################
  
  # Adding the About Tab 
  tabPanel(
    
    # For some reason the title doesn't like the name "About".
    # "About " was used to get around this 
    title = "About ",
    
    # icon = icon("info"),
    
    fluidRow(
      
      column(
        
        width = 12,
        
        h3("New Zealand Energy Scenarios TIMES-NZ 2.0"),
        
        HTML("The New Zealand Energy Scenarios TIMES-NZ 2.0, developed by  
              <a href='https://www.eeca.govt.nz/' style='color:#333333;
             '>EECA</a> in partnership with the <a href='https://www.bec.org.nz/' 
             style='color:#333333;'>BusinessNZ Energy Council (BEC)</a> and <a 
             href='https://www.psi.ch/en' style='color:#333333;'> The Paul 
             Scherrer Institut</a>, is based on the International Energy Agency 
             Energy Technology Systems Analysis Program TIMES model, an energy 
             system model that has been used by over 60 countries worldwide. 
             <br><br> TIMES-NZ 2.0 is a technology-based optimisation model 
             that represents the entire New Zealand energy system, encompassing 
             energy carriers and processes from primary resources to final 
             energy consumption. The model is based on the IEA ETSAP TIMES 
             energy model generator, and models scenarios for the energy system, 
             incorporating both technical, engineering and economic considerations. 
             TIMES is an integrated energy system model, meaning that it 
             simultaneously models all components of the energy system, 
             ensuring that any interdependencies and trade-offs are reflected.
        <br><br>TIMES uses a linear-programming solver to minimise the total 
             discounted energy system cost over the entire modelled time horizon. 
             The cost minimisation is achieved by choosing between technologies 
             and fuels to meet expected energy demand. The model effectively 
             ‘invests in’ the various available technologies based on the 
             combinations of cost, efficiency, and fuel availability. 
             TIMES models are particularly suited to explore the evolution of 
             possible least-cost configurations of the system. The scenarios were 
             originally developed by the <a href=' https://www.bec2060.org.nz/' 
             style='color:#333333; '>BEC2060</a>  project - this updated 
             TIMES-NZ model adds more detail and sophistication to sectors, 
             subsectors, technologies and end uses."),
       
        h3("The TIMES-NZ 2.0 Scenarios " ),
        
        HTML("The New Zealand Energy Scenarios TIMES-NZ 2.0 project grew out of 
             BEC2060, which provided two plausible and coherent scenarios about 
             New Zealand's energy future: Kea and T\u16b\u12b. These scenarios have been 
             extended in this latest iteration to include more granular data."),
        
        
        # Adding Kea and Tui comment 
        HTML("<div class='wrapper'>
                
        <div class='box a'><strong> Kea (cohesive) </strong> <br>
        <strong>Kea</strong> represents a scenario where 
        climate change is prioritised as the most pressing issue and New Zealand 
        deliberately pursues cohesive ways to achieve a low-emissions economy.</div>
       
        
        <div class='box b'><strong>T\u16b\u12b (individualistic)</strong><br>
        <strong>T\u16b\u12b</strong> represents a scenario where climate change is an 
        important issue to be addressed as one of many priorities, 
        with most decisions being left up to individuals and 
        market mechanisms.  </div>
        </div>"
             
             
        ),
        
 
        
        h3("Find out more about TIMES-NZ 2.0"),
        HTML("For more detail about the data input assumptions and methodology of 
        TIMES-NZ 2.0, read the TIMES-NZ 2.0 Methodology and Insights paper 
        “New Zealand Energy Scenarios TIMES-NZ 2.0. - 
        <i>A guide to understanding the TIMES-NZ 2.0 model</i>”. 
        <a href='https://www.eeca.govt.nz/New-Zealand-Energy-Scenarios-TIMES-NZ-2.pdf' target='_blank' rel='noopener noreferrer' style='color:#333333;
             '><i class='fa fa-file-pdf-o' style='font-size:28px;color:grey'></a></i>"

        ),
        
        HTML("<br><br>"),

        div(
          HTML('<iframe class="frame-boader" width="560" height="315" src="https://www.youtube.com/embed/yxNVJMkPvhs" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'),
          HTML('<iframe class="frame-boader" width="560" height="315" src="https://www.youtube.com/embed/cX0SgDliiMk" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'),
          align = "center"),
        
        
        div(
          actionButton(inputId = "intro", 
                       
                       label = HTML("Click here for a quick introduction tour"),
                       
                       icon = icon("info-circle")),
          
          align = "center"),
        
        
        
        #  Creative Commons Attribution 3.0 New Zealand License
        HTML("<br>"),
        div(HTML('<a rel="license" href="https://creativecommons.org/licenses/by/4.0">
          <img alt="Creative Commons License" style="border-width:0" src="img/creative_logo.svg"   /></a>
          <br />This work is licensed under a <a rel="license" href="https://creativecommons.org/licenses/by/4.0">
          Creative Commons Attribution 4.0 New Zealand License</a>.') ),
          
        

        
    ))
    
    
  ),
  
  
  
  
  # These are CSS files that are needed for displaying the fontawesome icons
  header = tags$head(
    tags$link(rel = "stylesheet", type = "text/css", href = "font-awesome-5.3.1/css/all.min.css"),
    tags$link(rel = "stylesheet", type = "text/css", href = "font-awesome-5.3.1/css/v4-shims.min.css"),
    tags$link(rel = "stylesheet", type = "text/css", href = "css/styles.css"),
    tags$script(type = "text/javascript", "$(function () {$('[data-toggle=\"popover\"]').popover()})")
  ),
  
  # Adding the Footer to the App
  footer = tags$footer(
    div(HTML('<a href="https://www.eeca.govt.nz/">
          <img class="logo_image" style="border-width:0; " src="img/EECA_BEC.svg" height = 120 width = 660  </a>
          </img>'), align = "center")),
  
                collapsible =FALSE
  
  

)
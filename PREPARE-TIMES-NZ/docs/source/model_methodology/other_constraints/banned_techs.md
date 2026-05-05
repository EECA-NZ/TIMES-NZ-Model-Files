# Disabled base year technologies

By default, TIMES-NZ will enable all existing technologies to be built again in the future, at whatever costs were specified in the original data. These existing technologies are called "base year" technologies. 

In many cases, this is appropriate, such as allowing the model to build more heat pumps based on existing heat pump technology. However, for some technologies, it is not appropriate to build more. 

Key reasons for disabling: 

 - Electricity: we list all named electricity generation plants, so these are all disabled for future builds. It would not be sensible to build additional Benmore hydro stations, for example. 
 - Some other existing technologies we either assume there will be no future investment, such as with medium-sized petrol trucks.
 - For other uncommon technologies in the existing set, there is limited information on likely costs and efficiencies. If our data on a technology is limited, we may disable the technology for future investment so as to limit unrealistic or implausible investment results.

The full list of disabled base year technologies, and equivalent model codes and wildcards, are listed in {numref}`tab-banned-techs`. 

```{csv-table} Disabled base technologies
:header-rows: 1
:name: tab-banned-techs
:file: tables/banned_techs.csv
```

# Disabled base year technologies

By default, TIMES-NZ will enable all existing technologies to have more of themselves built in the future, at whatever costs were specified in the original data. These existing technologies are called "base year" technologies. 

In many cases, this is appropriate, such as allowing the model to build more heatpumps based on existing heatpump technology. However, for some technologies, it is not appropriate to build more. 

Key reasons for disabling: 

 - Electricity: we list all named electricity generation plants, so these are all disabled for future builds. It would not be sensible to build additional Benmore hydro stations, for example. 
 - Some other existing technologies we either assume there will be no future investment, such as with medium-sized petrol trucks.
 - For other uncommon technologies in the existing set, there is limited information on likely costs and efficiencies. If our data on a technology is limited, we may disable the technology for future investment so as to limit unrealistic or implausible investment results.

The full list of banned technologies, and equivalent model codes and wildcards, are listed in {numref}`tab-banned-techs`. 

```{list-table} Banned technologies
:header-rows: 1
:name: tab-banned-techs
Code,Label
ELC_*,All electricity
RES*COA**,Residential coal
RES*WOD*,Residential wood
T_F*PET*,Light petrol trucks
T_P_B*PET*,Petrol buses
T_P_B*LPG*,LPG buses
C_*-HEATX-GEO,Commercial geothermal
C*CK*-LPG*,Commercial cooking LPG
C*CK*-NGA*,Commercial cooking natural gas
C*SH-Boiler-LPG*,Commercial space heating LPG
C*SH-Boiler-NGA*,Commercial space heating natural gas
C*WH*-NGA*,Commercial water heating natural gas
C*MPM-PET*,Commercial Mobile motive power petrol
C*MPM-LPG*,Commercial Mobile motive power LPG
C*MPM-NGA*,Commercial Mobile motive power natural gas
C*Boiler-DSL*,Commercial diesel boilers
AFISH*-PET,Fishing boat petrol
*PET-ICENG-MTV_MOB,Industrial petrol mobile motive power
*NGA-ICENG-MTV_MOB,Industrial natural gas mobile motive power
*PET-ENGIN-MTV_STA,Industrial petrol stationary motive power
C_*INC*,Commercial incandescent lighting
*FOL*PH*,Industrial fuel oil process heat
```

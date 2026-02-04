# Transmission and distribution

In TIMES-NZ, we model transmission and distribution through separate network processes. Transmission process represents all Transpower transmission assets, and the Distribution process represents all assets owned and operated by Electricity Distribution Businesses (EDBs). For each of these we include assumptions on existing capacity, associated losses, costs of new installed network capacity, and operating costs. TIMES-NZ operates on a 2-region model (North and South Islands), and the HVDC link is represented separately.  

These assumptions are represented in {numref}`tab-transmission-distribution`.

```{list-table} Transmission and distribution network assumptions
:header-rows: 1
:name: tab-transmission-distribution
* - Assumption
  - Transmission assets
  - Distribution assets
* - Existing capacity GW (North Island)
  - 5
  - 4.74
* - Existing capacity GW (South Island)
  - 2.5
  - 2.07
* - Investment cost ($m 2023 NZD/GW)
  - 700
  - 2,371.10
* - Fixed OM costs ($m 2023 NZD/GW/year)
  - 108
  - 296.2
* - Efficiency
  - 98.50%
  - 94.60%
```


## Transmission

The efficiency data and existing capacity are by assumption. Capacity represents an assumed maximum total load at any given moment, and efficiency represents losses on the grid. Fixed costs are based on CAPEX and OPEX costs from Transpower’s Regulatory Control Period 4 proposal[^rcp4], and include asset replacement. 

High level investment costs have been provided by Transpower and are based on actual costing for a small number of recent grid backbone enhancement projects. However, there is considerable variation in transmission investment costs depending on the specifics of the network and the overlay of demand and generation. True investment costs may be significantly lower or higher, depending on the project. Note that HVDC costs and efficiency are excluded from the above, as these are represented separately. 


[^rcp4]: RCP4 Main Proposal | Transpower: <https://static.transpower.co.nz/public/2023-11/RCP4%20Main%20Proposal%202023.pdf> (Table 56)

## Distribution

Distribution capacity, cost, and efficiency data is taken from the Commerce Commission’s information Disclosure Requirements for EDBs[^comcom_edbs]. Cost figures used are 2021-2023 averages, rebased to 2023 NZD. For some parameters required for the modelling, there are not clear real-world analogues, so some assumptions are made. These are described below. 

Existing capacity in TIMES-NZ is defined as the maximum demand the network can handle at any given moment. The closest available analogue in the data is Maximum Coincident System Demand (MCSD), or the maximum load the system experienced. This figure was 6.81GW in 2023. We distribute this capacity figure across islands by EDB. True maximum possible demand is likely higher than this figure, as there is some slack in the system. However, by setting capacity equal to MCSD, the model will continually invest in expanding the network as peak demand grows. 

Investment cost in TIMES-NZ is defined as the cost of increasing maximum possible load. For this figure we use the EDB’s capital expenditure on System Growth, averaged over 2021-2023 ($186m). The denominator is the increase in MCSD, also averaged over 2021-2023 (78MW). 

Fixed OM costs in TIMES-NZ are defined as the cost of maintaining existing capacity. For this figure we use the are the remaining EDB expenditure on OPEX, and the sum of CAPEX components excluding system growth. The expenditure is then divided by the existing capacity assumption to estimate maintenance costs based on the size of the network.


[^comcom_edbs]: Commerce Commission - Performance summaries for electricity distributors: <https://comcom.govt.nz/__data/assets/excel_doc/0018/360423/Performance-summaries-for-electricity-distributors-Year-to-31-March-2023.xlsx>

## HVDC link

In TIMES-NZ, the HVDC is used to facilitate inter-regional transfer of electricity. The relevant model parameters are in {numref}`tab-hvdc-assumptions`.

```{list-table} HVDC assumptions
:header-rows: 1
:name: tab-hvdc-assumptions
* - HVDC Assumption
  - Value
* - Efficiency
  - 97%
* - Investment cost
  - $650m NZD/GW
* - Fixed OM costs
  - $80m NZD/GW/year  
* - Capacity (current)
  - 1,200MW (limited to 950MW southbound)
* - Capacity (from 2031)
  - 1,400MW (limited to 950MW southbound)

```

Cost estimates have been provided directly by Transpower. This includes an estimated 130m NZD for the 200MW enhancement in 2031, and an estimated 95m NZD annually in lifetime maintenance of the current capacity. These costs are normalised per GW of capacity. Note that costs and investment timing assumptions are fixed, meaning the cost assumptions will not impact the model’s investment or dispatch decisions.

Losses on the HVDC are a function of load and can reach 10% during peak demand. TIMES-NZ uses a simple average estimate of 97% efficiency. Future iterations of TIMES-NZ may implement a more sophisticated representation of the HVDC and transmission/distribution networks to adjust losses as a function of demand. 

We set a single upgrade for the HVDC to 1,400MW from 2031, following Transpower announcements[^hvdc_link_upgrade]. HVDC capacity is otherwise fixed. There is potential for a further upgrade in 2042 when Pole 2 is due for replacement, but this is not included in the model at this stage. 

[^hvdc_link_upgrade]: HVDC link upgrade programme | Transpower: <https://www.transpower.co.nz/hvdc-upgrade>


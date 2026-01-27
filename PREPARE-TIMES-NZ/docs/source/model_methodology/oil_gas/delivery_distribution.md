# Delivery and distribution costs 

This section details the delivery cost assumptions associated with getting oil and gas to commercial, industrial, and residential consumers. Note that delivery costs for electricity generation are not included here. These are done at the individual plant level and are instead included in the TIMES-NZ 3.0 electricity assumptions. 

## Natural gas

Natural gas distribution costs are based on pricing schedules available from Clarus (previously known as Firstgas)[^firstgas]. We assume these prices are sufficiently representative of the distribution prices of other networks, including Gasnet[^gasnet], Vector[^vector], and Powerco[^powerco].

Distribution costs include fixed and variable components, and these are converted into per-unit delivery costs for TIMES-NZ. To do this, we estimate the average consumption per sector connection based on sectoral ICP count data from the GIC[^gic_switching] and sectoral consumption from MBIE. Some assumptions are required to distribute the demand across specific price categories, and so the resulting estimated demand per connection for each category is necessarily an estimate only and subject to inevitable error. 

The daily fixed cost and average unit cost are then distributed across the total assumed consumption per connection to estimate average distribution costs per unit and price category. The results are as follows: 


```{csv-table} Estimated natural gas demand and distribution costs per connection and price category
:name: tab_gas_deliv_cost_categories
:header-rows: 1

Firstgas price category,Category name ,Estimated annual demand per connection (GJ),Average distribution cost (NZD/GJ)
GN0R,Residential,25,15.23
GN0V,"Residential, variable charge",25,19.64
GN01,General business,30,14.19
GN02,Small commercial,300,3.64
GN03,Large commercial ,"5,000",3.21
GN04,Industrial,"70,000",2.66
GN05,Large industrial ,"2,000,000",0.68
```
[^firstgas]: Firstgas | [Annual price review 2023](https://cms.firstgas.co.nz/assets/Uploads/Distribution-PDFs-/Price/Annual-Price-Review-2023.pdf)
[^gasnet]: GasNet | [2023/2024 Pricing methodology](https://www.gasnet.co.nz/wp-content/uploads/2017/11/GasNet-Pricing-Methodology-1-October-2023-approved.pdf)
[^vector]: Vector Gas | [Gas network pricing schedule](https://blob-static.vector.co.nz/blob/vector/media/vector-2025/py26-gas-network-pricing-schedule-2026-1.pdf)
[^powerco]: Powerco | [Gas Distribution Pricing Schedule](https://www.powerco.co.nz/-/media/project/powerco/powerco-documents/who-we-are---pricing-and-disclosures/pricing/gas-pricing/1-prices-for-our-gas-network/gas-pricing-schedule-1-october-2025---30-september-2026.pdf)
[^gic_switching]: Gas Industry Co. | [Switching](https://www.gasindustry.co.nz/data/switching/)


```{csv-table} Natural gas distribution costs per TIMES-NZ sector
:name: tab_gas_dist_costs
:header-rows: 1

TIMES-NZ sector,Included price categories,Average distribution cost (NZD/GJ)
Residential,"GN0R, GN0V",17.4
Commercial,"GN01, GN02, GN03",7.01
"Agriculture, Forestry, Fishing","GN02, GN03, GN04",3.17
Industrial,"GN04, GN05",1.67
```

Note that distribution costs are reduced for industrial demand at Methanex and Ballance due to the model’s treatment of feedstock gas. This reduced cost may reflect the reality of contracts for these larger users. 

Previous instances of TIMES-NZ estimated delivery costs based on the difference between reported wholesale and sectoral natural gas prices. These include margins, which are not system costs and can negatively impact the model’s optimisation. 

## Other fuel delivery costs 

Petrol and diesel delivery costs are set at a flat rate of 0.92 NZD/GJ in TIMES-NZ, representing the average cost of local distribution from ports. These costs are applied to all downstream sectors, except electricity, where costs are estimated individually per plant (such as diesel delivery costs to the Whirinaki peaking plant). We assume no meaningful distribution costs for aviation fuel or fuel oil, and these are currently set to zero. 
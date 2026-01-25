# Imported LNG

New Zealand does not yet have LNG importing capacity, and there are no firm plans to invest in the required infrastructure. However, given the low projected output of domestic natural gas production, the model includes potential LNG investment options. LNG import options are made available to the model, with relevant capital costs, fuel import costs, and supply limitations. We do not presuppose that LNG is an optimal choice for the system but rather allow the model to invest in LNG infrastructure if that is cheaper than alternatives. 

We model two broad options, following recent reports from Gas Strategies prepared for the New Zealand market. The first is the standard configuration[^gas_strategies_standard], which includes floating storage offshore and onshore regasification through standard size vessels. The second is small-scale[^gas_strategies_small], where smaller cargoes are received regularly over the course of a year, and stored onshore. We make some small adjustments to these to align with the input requirements of the TIMES model framework.  Broadly, the small-scale configuration is cheaper and may be faster to implement but offers less flexibility and capacity than the standard configuration. The technical specifications are summarised in {numref}`tab_lng_imports`. 


[^gas_strategies_standard]: Gas Strategies standard configuration LNG assumptions can be found at <https://cms.clarus.co.nz/assets/Uploads/PDFs/LNG/Public-Release-NZ-LNG-Import-Feasibility-Assessment-1.pdf> 

[^gas_strategies_small]: Gas Strategies small-scale LNG assumptions can be found at: <https://cms.clarus.co.nz/assets/Uploads/PDFs/LNG/Public-Release-NZ-LNG-Addendum-on-Small-Scale-LNG-1.pdf>


## Standard configuration 

The standard configuration includes a bespoke FSU (Floating Storage Unit) and onshore regasification. The original report notes capital expenditure may range between \$189m and \$1,000m, with annualised costs over a 15-year duration of \$170m-\$210m. We assume the annualised cost represents the annualised capital cost and ongoing (annual) operational cost.

For the purposes of TIMES-NZ, we require separate capital and operational expenditure costs, in order that scenario-specific costs of capital can be modelled. To calculate this from the aggregate annualised costs presented in the report, we take the mid-point of the annualised cost range, being \$190m, and assume that this is a 50:50 split of annualised capital cost and operational cost (i.e., each of these costs are \$95m per annum). We then back-calculate the capital cost based on a cost of capital of 8.4% as stated in the report[^lng_discount]. This results in a capital cost of \$794m, which is towards the upper end of the quoted range.

We assume no annual limitation of total deliveries under this configuration, and full flexibility of purchasing. 

The landed cost of LNG under this configuration is estimated between 17.83 and 18.27 NZD/GJ, depending on market conditions. For TIMES-NZ, we assume a midrange value of 18 NZD/GJ. Note that this price is based on forward market prices. International LNG prices have stabilised in recent years, but have shown historical volatility, so this figure is subject to error.

We assume that the earliest possible operational year for this configuration is 2029, aligning with the Gas Strategies assumption.  


[^lng_discount]: This discount rate of 8.4% was used by the Gas Strategies report and is based on the cost of capital faced by the port industry. This figure was used to estimate the capital component of the report’s quoted annualised costs.


## Small-scale configuration 

The small-scale configuration assumes smaller, regular cargoes, delivered on a schedule. The key constraint here is the limitation in flexibility, as it assumes 27 smaller cargoes are delivered across the year for a total of 9 PJ. This means there is limited access to the spot market in dry years.

The report notes an estimated \$295m on terminal CAPEX, which includes onshore storage, and an annualised cost of \$230m (including the cost of LNG). When excluding the commodity price of LNG and amortised CAPEX, this leaves around \$10m in annual operating and maintenance costs.

The mid-case landed price of LNG is 20.55 NZD/GJ in this scenario, which is higher than the standard configuration. This is due to additional delivery costs, such as chartering a small-scale LNG carrier for transit between Australia and Port Taranaki. For TIMES-NZ, we therefore assume additional delivery costs of 2.55 NZD/GJ in this configuration but otherwise assume consistent LNG prices between each configuration. 

Small-scale contracts imply an ongoing term obligation to purchase LNG, so we constrain the modelled version such that 9 PJ is delivered annually, every year. This limitation in flexibility may prove less desirable in the optimal model solution even if overall costs are lower. 

We assume that the lower capital investment required means that this option could be brought forward to the earliest possible installation year of 2028.


## Assumptions reference


```{csv-table} LNG import option assumptions
:name: tab_lng_imports
:header-rows: 1

Variable,Standard configuration,Small-scale configuration
Annual maximum output,N/A,9 PJ
Capital cost NZDm,794,295
Operating cost NZDm pa,95,10
LNG commodity cost NZD/GJ,18,18
Additional delivery costs NZD/GJ,0,2.55 
Earliest possible installation year,2029,2028
```

Note that we assume that LNG consumption will be subject to the same emissions factor as domestic natural gas. We also set both options as integer options within TIMES-NZ, meaning it is not possible for the model to build fractions of an import terminal[^mip].

[^mip]: In its default state, TIMES reaches an optimal model solution as a linear programming solution. This means that it could choose to build, for example, a fraction of an LNG import terminal. This is not realistic, so we limit LNG import options to “integer states”, meaning either the entire facility is built or not at all. This requires a Mixed Integer Programming solution, which increases the computational load of the model but is necessary for plausible results.
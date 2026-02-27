# Imported LNG

New Zealand does not yet have LNG importing capacity. During development of TIMES-NZ, The New Zealand government confirmed plans[^lng_pr] to establish a liquiefied natural gas import facility. This facility could be operational as early as 2027. 

[^lng_pr]: MBIE | [Government says yes to liquefied natural gas](https://www.mbie.govt.nz/about/news/government-says-yes-to-liquefied-natural-gas)


Previous versions of TIMES-NZ considered the costs of LNG import terminals under different configurations, allowing the model to choose between different terminal options based on overall costs and the requirements of the energy system. We have instead adjusted the LNG approach to ensure a fixed install date of the standard terminal configuration in 2027 in the Traditional scenario, and removed LNG import options entirely from the Transformation scenario to allow for comparison.


For LNG import terminal cost modelling, we reference recent reports from Gas Strategies prepared for the New Zealand market. Specifically, we look at the standard configuration option, which allows for flexible wholesale purchasing[^gas_strategies_standard]. It is possible to also model other approaches, such as the small-scale configuration[^gas_strategies_small], but this is not used in the current model version.

## Standard configuration details

The standard configuration includes a bespoke FSU (Floating Storage Unit) and onshore regasification. The original report notes capital expenditure may range between \$189m and \$1,000m, with annualised costs over a 15-year duration of \$170m-\$210m. We assume the annualised cost represents the annualised capital cost and ongoing (annual) operational cost.

For the purposes of TIMES-NZ, we require separate capital and operational expenditure costs, in order that scenario-specific costs of capital can be modelled. To calculate this from the aggregate annualised costs presented in the report, we take the mid-point of the annualised cost range, being \$190m, and assume that this is a 50:50 split of annualised capital cost and operational cost (i.e., each of these costs are \$95m per annum). We then back-calculate the capital cost based on a cost of capital of 8.4% as stated in the report[^lng_discount]. This results in a capital cost of \$794m, which is towards the upper end of the quoted range.

We assume no annual limitation of total deliveries under this configuration, and full flexibility of purchasing. 

The landed cost of LNG under this configuration is estimated between 17.83 and 18.27 NZD/GJ, depending on market conditions. For TIMES-NZ, we assume a midrange value of 18 NZD/GJ. Note that this price is based on forward market prices. International LNG prices have stabilised in recent years, but have shown historical volatility, so this figure is subject to error.

We assume a fixed install date of 2027 for the Traditional scenario, which is the earlist possible date the terminal may be operational[^lng_factsheet]. 

```{eval-rst}
.. note::

   Capital and operating cost specifications are important if allowing the model to choose between different terminal options, or whether to import LNG at all.   

   Because installation dates are fixed in current TIMES-NZ scenarios, these cost specifications are less important, but still contribute to total system cost reporting. They remain in the model to allow simple adjustment to LNG import optimisation modelling methods if desired. 

```


[^lng_factsheet]: Beehive.govt.nz | [LNG Factsheet](https://www.mbie.govt.nz/about/news/government-says-yes-to-liquefied-natural-gas)

[^gas_strategies_standard]: Gas Strategies standard configuration LNG assumptions can be found at <https://cms.clarus.co.nz/assets/Uploads/PDFs/LNG/Public-Release-NZ-LNG-Import-Feasibility-Assessment-1.pdf> 

[^gas_strategies_small]: Gas Strategies small-scale LNG assumptions can be found at: <https://cms.clarus.co.nz/assets/Uploads/PDFs/LNG/Public-Release-NZ-LNG-Addendum-on-Small-Scale-LNG-1.pdf>


[^lng_discount]: This discount rate of 8.4% was used by the Gas Strategies report and is based on the cost of capital faced by the port industry. This figure was used to estimate the capital component of the report’s quoted annualised costs.

## Assumptions summary

```{csv-table} LNG import option assumptions
:name: tab_lng_imports
:header-rows: 1

Variable,Standard terminal 
Annual maximum output,Unlimited[^import_limits]
Capital cost NZDm,794
Operating cost NZDm pa,95
LNG commodity cost NZD/GJ,18
Installation date, 2027
```


Note that we assume that LNG consumption will be subject to the same emissions factor as domestic natural gas. Additional emissions factors associated with regasification or leakage of LNG are not currently included. 

Because we currently set fixed install dates for terminals, assuming a single terminal is installed in 2027, the modelling solution is straightforward. Note that if you wished to expand the method to allow the model to choose optimal installation dates for the terminal, a Mixed Integer Programming[^mip] solution would be required to ensure that no partial terminals could be constructed.

[^import_limits]: We assume that the maximum annual LNG demand will never exceed the throughput of the standard terminal configuration.

[^mip]: In its default state, TIMES reaches an optimal model solution as a linear programming solution. This means that it could choose to build, for example, a fraction of an LNG import terminal. This is not realistic, so we limit LNG import options to “integer states”, meaning either the entire facility is built or not at all. This requires a Mixed Integer Programming solution, which increases the computational load of the model but is necessary for plausible results.
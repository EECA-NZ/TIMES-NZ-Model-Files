# Time of use and meeting peak demand

Electricity demand, generation, and storage are modelled different across 24 different time slices. These are formed using every combination of the below: 

```{list-table} Time slice definitions
:header-rows: 1
:name: tab-timeslice-definitions
* - Season
  - Day of week
  - Time of day
* - Spring
  - Weekday
  - Day (11 hours)
* - Summer
  - Weekend
  - Night (12 hours)
* - Autumn
  - 
  - Peak (6pm-7pm)
* - Winter
  - 
  -
```
The model must provide a solution that includes electricity generation capacity to meet peak demand across all time slices. Note that this means we operate across 24 different timeslices. 

While peak is defined as a single hour, it is important to note it is not "the" peak hour. Rather, it represents the average peak hour in each day in each parent timeslice. For example, the Winter/Weekday/Peak timeslice represents every winter weekday 6pm-7pm, or roughly 66 hours in total. To better account for the true peak hour in any given year, we also consider a peak constraint (see below).


## Energy and capacity constraints
TIMES-NZ also includes capacity and energy margin constraints to represent security of supply margins. 

The Winter Energy Margin (WEM) and Winter Capacity Margin (WCM) are defined by the Electricity Authority Participant Code (Section 7.3)[^ea_participation_code]:
 - the energy security of supply standard is a winter energy margin of 14-16% for New Zealand and a winter energy margin of 25.5-30% for the South Island; and
 - the capacity security of supply standard is a winter capacity margin of 630-780 MW for the North Island

We assume that the electricity generation market will meet these security of supply standards throughout the model horizon, ensuring enough capacity and energy to meet the upper bounds of these margins. These are implemented through two model constraints: the Winter capacity margin (WCM) and Winter energy margin (WEM).

### Winter capacity margin 

This means the model solution must include enough capacity to meet demand, and an additional 780MW of North Island capacity, during all time slices. This is mostly relevant for winter peak time slices, as these have the highest demand. This constraint considers all other relevant model elements during the relevant time slices, including available battery discharge, regional demand curves, and HVDC transfer capacity.

When assessing the generation capacity available to meet peak demand, the peak contribution assumptions (as defined in {numref}`tab-peak_contribution`) are used. These are different to the average availability factor used for generation during any given time slice. For example, fossil fuel peakers might have lower average generation during an average peak time slice, but higher availability to meet that season’s peak constraint. Wind generation, on the other hand, might have higher average generation during those time slices, but a lower peak contribution factor; wind is less reliably available to meet peak at any given moment. 

The Winter Capacity margin is included in TIMES-NZ as a percentage share of total capacity. 780MW is roughly equivalent to 15% of North Island peak demand. However, because we use low peak contribution rates for some of our plants, representing their lower reliability, we risk "double-counting" the margin if we use this figure. We therefore use a lower peak margin of 5% in TIMES-NZ.

### Winter energy margin

We further introduce additional constraints on the model solution to represent winter energy margins for electricity supply. The model must provide a solution where total electricity capacity exceeds demand by specific margins in autumn and winter. The margins are set at 28% additional capacity in the South Island, and 16% nationally. 

This constraint is applied through the following constraint equation, which must hold true in the model solution: 

```{math}
:label: eq-wcm

\sum_{i,r} (Capacity_{i,r} \cdot Availability_{{AW}_{i,r}})
    \ge (1 + \alpha) \cdot 
    \sum_{r} CapacityDemand_{{AW}_{r}}

```


Where:
 - $Capacity_{i,r}$ is the capacity of each plant $i$ in region $r$
 - $Availability_{{AW}_{i,r}}$ is the average availability during Autumn and Winter for each plant $i$ in region $r$
 - $\alpha$ is the relevant parameter (28% for the South Island, 16% for the whole country)
 - $CapacityDemand_{{AW}_{r}}$ is the capacity that would be required to meet total electricity demand during Autumn and Winter in region $r$


Put another way, total generation capacity during Autumn and Winter must be higher than the required capacity to meet demand. This considers the availability of specific technologies during those time periods, and the ability of the HVDC to move electricity between islands. It also only considers grid demand, excluding demand already met by distributed generation such as rooftop solar. The model builds additional capacity to meet this constraint, leading to lower overall capacity factors.


[^ea_participation_code]: Electricity Industry Participation Code: <https://www.ea.govt.nz/documents/2547/FULL_MERGED_CODE_-_1_APRIL_2023.pdf>
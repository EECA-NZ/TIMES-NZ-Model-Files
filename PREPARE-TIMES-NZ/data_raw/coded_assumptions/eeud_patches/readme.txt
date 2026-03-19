Here, we include data from EECA's internal databases on biomass demand for energy outside of the official balance tables.


The official balance tables exclude all biomass used for energy outside of wood processing and residential use. 

So to get better coverage of the system, we need to include this patch, which is based on internal databases of every known commercial or industrial bioenergy boiler.

End use is therefore estimated based on the size of the boiler, so these are estimates only. 

We will use these to patch the EEUD and have that flow through to the rest of TIMES. 


The input file should match the structure of the EEUD for easy joining

We do not use the internal EECA regional splits for these. 

Rather we assess the regional splits separately, internally and then can use them for regional share assumptions if necessary for extra precision 

The reason for this is they need to go into the data BEFORE the other regional split calculations so the entire system can balance correctly 



Note: we allocated all education demand to "Education and Training: Pre-School, Primary and Secondary". 
This isn't correct, as some is tertiary, but it doesn't matter: TIMES aggregates all education subsectors into a single education sector. 

We do not distinguish different kinds of wood fuel in this system currently. We could, from the original data, but TIMES-NZ does not currently use this level of detail.
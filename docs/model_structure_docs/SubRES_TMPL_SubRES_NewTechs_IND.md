[Back to Model Structure Index](../model-structure.md)
## SubRES_TMPL/SubRES_NewTechs_IND.xlsx
### WorkSheet: IND_NEW
**IndustryNewTechParameters**: 
Defines technical parameters for future industry technologies


 - Veda Tag: `~FI_T`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_ind/future_industry_parameters.csv`


**IndustryNewTechProcessDefinitions**: 
Defines processes for future industry technologies


 - Veda Tag: `~FI_Process`


 - Data Location: `data_intermediate/stage_4_veda_format/subres_ind/future_industry_processes.csv`


### WorkSheet: IND_EAF
**EAFProcessDefinitions**: 
Declares new process to represent EAF (Electric Arc Furnace). Note that other settings assume this is available.


 - Veda Tag: `~FI_Process`


 - Data Location: `NewTech_IND.toml`


**EAFCommodityDefinitions**: 
Declares new commodity for recycled steel from EAF


 - Veda Tag: `~FI_Comm`


 - Data Location: `NewTech_IND.toml`


**EAFParameters**: 
Specific settings for EAF, including install dates/size


 - Veda Tag: `~FI_T`


 - Data Location: `NewTech_IND.toml`


### WorkSheet: IND_NEWDEM
**NewDemandProcessDefinitions**: 
Declares new process to represent 'New demand', representing additional electricity load in some scenarios.


 - Veda Tag: `~FI_Process`


 - Data Location: `NewTech_IND.toml`


**NewDemandCommodityDefinitions**: 
Declares new commodity for 'New demand'


 - Veda Tag: `~FI_Comm`


 - Data Location: `NewTech_IND.toml`


**NewDemandParameters**: 
Basic parameters for 'New demand'. Note that these are very minimal: this is effectively an industrial electricity sink, defined in newtech demand scenario


 - Veda Tag: `~FI_T`


 - Data Location: `NewTech_IND.toml`


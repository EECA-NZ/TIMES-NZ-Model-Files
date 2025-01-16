import os 
import sys
from pathlib import Path
import pandas as pd

import chardet


# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from config import TIMES_OUTPUTS_RAW, qa_runs
from qa_data_retrieval import get_veda_data




#region NOTES


## we want to take a much closer look at the available attributes in the vd files for clues as to what the heck happened here 

"""
This script is designed specifically to investigate and understand some strange behaviour when testing the automatically generated 
SysSettings.xlsx file 

When doing a new run with all the same parameters, but an automatic SysSettings file, several processes shift around, which leads 
to differences getting flagged in the current delta tests.

Need to understand: 

a) why this is happening
b) do we care 

If we don't care, we'll need to adjust the current tests to ignore this noise. If we do care, we need to ensure that we have some way 
of controlling for this stuff.

"""

"""
Current key (?) Differences:

    So, the only input difference we should have is an increase in float precision in two lil numbers in syssettings. 
    specifically, .SPR-WE-N demand proportion changes from 0.034 to 0.0339999999999999 in NI and SI. That's it. 
    (It's the excel version that has this float error)
    this should make no difference but we of course have some category shifts in the output tests. Need to understand these.

    We note that the generated load curve files match even though we have this float point error, so I guess GAMS doesn't actually care
    about this part of things. It seems to set everything to the same precision which is a nice touch. 
    

Other differences: 
    We also see no differences in any other input files EXCEPT the vde files 
    These list attribute codes and descriptions and at first glance appear to have (for some reason) rearranged some of the rows. 


Working theory: 

    The current working theory is that all the changes we are seeing in outputs are 
    actually different codes being arbitrarily selected by the model. These are also only process codes (ie not commodity codes)
    These process codes, when arbitrarily swapped, make no difference (because they have exactly the same parameters)

    This means they CAN be arbitrarily swapped by the model solve. Increasing precision can adjust compute or whatever, and stuff bounces around
    And gets selected randomly when it makes no difference to the objective function. 

Tests: 

There are a few tests we want to perform here: 

    1) read in both vde files and confirm that they match (but are in different orders) 
        a) if they don't we need to inspect the actual differences more closely
        RESULT: these files do match as expected
    2) check if the vd files match when we group by everything we can EXCEPT process. What are the actual changes? 
        a) as above, these should match when igoring process codes. If not we need to find more differences. 
    3) Try rerunning TIMES for IAT testing within the repo (not Veda) after swapping the vde file to match the base file
        a) this SHOULD produce a match. If not, we need to find other input differences. 
            If it does, we need to consider how to better run tests given this issue. 
        RESULT: This test could not be executed as the core order is set elsewhere and we might just need to ignore it. Inconclusive.
    4) Try rerunning TIMES for IAT testing from Veda after producing the auto files with matching precision for SPR-WE-N distribution
        a) as above, this SHOULD produce a match    
    5) when we run the delta app, which codes aren't showing up in the concordance? 
        a) this is limited to a specific atty, which helps cut down noise a bit
    6) do all our busted codes (either showing differences or not showing up at all) relate to dodgy concordance matches? 
    7) 


# Potential Process improvements from all of this: 


    1) the delta testing should not consider process codes if a lot of them are just the bloody same but can bounce around randomly.
    Catching them means catching noise. 
    2) The concordance file needs to be better fleshed out



"""

#region TEST ONE 
# VDE FILES MATCH

def get_vde_file(scenario, sort_dfs = True):
    # find the file 
    file_path = Path(f"{TIMES_OUTPUTS_RAW}/{scenario}/{scenario}.vde")
    column_names = ['Variable', 'Region', 'Code', 'Description']
    # read in with sp
    df = pd.read_csv(file_path, low_memory = False, encoding='ISO-8859-1',
                     header=None, names=column_names)
    
    if sort_dfs: 
        df = df.sort_values(['Variable', 'Region', 'Code', 'Description']).reset_index(drop = True)
    
    # df["Scenario"] = scenario
    
    return df


def test_vde_files_match(qa_runs, sort_dfs = True):
    df = pd.DataFrame()

    df1 = get_vde_file(qa_runs[0], sort_dfs)
    df2 = get_vde_file(qa_runs[1], sort_dfs)

    # note that these have been sorted !! 

    are_equal = df1.equals(df2)

    if sort_dfs:
        sort_string = "when sorted"
    else:
        sort_string = "when unsorted"

    print(f"Dataframes {qa_runs[0]}.vde and {qa_runs[1]}.vde match exactly {sort_string}: {are_equal}")


test_vde_files_match(qa_runs, sort_dfs = False)
test_vde_files_match(qa_runs, sort_dfs = True)

"""
Output: 
Dataframes tui-v2_1_3.vde and tui-v2_1_3_iat.vde match exactly when unsorted: False
Dataframes tui-v2_1_3.vde and tui-v2_1_3_iat.vde match exactly when sorted: True
"""



#region TEST TWO

"""
Comparing if the vd files match

We'll bring in both vd files and aggregate by a bunch of stuff 

"""

run_a = qa_runs[0]
run_b = qa_runs[1]


df = get_veda_data("VAR_FIn")

grouping_vars = [
    'Scenario',
    'Attribute',
    'Period',
    'Region',
    'Vintage',
    'Technology', 
    'Fuel',
    'Enduse',
    'Unit',
    'Parameters', 
    'FuelGroup']

df_test2 = df.groupby(grouping_vars).sum("PV").reset_index()
index_cols = [col for col in df_test2.columns if col not in ["PV", "Scenario"]]


delta_test = df_test2.pivot(    
        index = index_cols,
        columns = "Scenario",
        values = "PV"
    ).fillna(0).reset_index()

    # Create delta
delta_test["Delta"] = delta_test[run_a] - delta_test[run_b]
# tolerance within 0.1% change
# i thought i would need to mess around with the way it handles 0s but it seems to work fine 
delta_test["Delta_Proc"] = delta_test[run_b] / delta_test[run_a] - 1
delta_test =  delta_test[(abs(delta_test["Delta_Proc"]) > 0.001 )] 

# delta_test
# print(delta_test)
# delta_test.to_csv('delta_test.csv', index=False)


"""

RESULT: THis is still showing differences. But, if we arbitrarily swap to a new process with a different code,
and this process has not been coded the same (or not coded at all) in our concordance table, 

then this will impact how it is being registered and it won't show up the same in our categories. 


A few test thoughts that come from this: 

1) Do the Will concordance rules capture things differently depending on which codes come through? This would mean 
that we're not capturing the fulsome list in our concordance table 

2) Identify a specific set of codes that seem to swap. OTH-FOL-FOL-Tech15 and OTH-FOL-FOL-Tech seems to be a good example here.
    a) confirm that these do swap between the runs
    b) identify their characteristics in the dd files - confirm that they are the same
    c) try and figure out how the Will code might handle these. Currently, OTH-FOL-FOL-Tech15 only comes through the concordance as CAP
        but comes out of the 

Potential solutions: 

Manually add these to the concordance!!! 
To speed this up, add a concordance step that identifies Att/Proc combinations, 
and flags an error if they exist in the relevant Att table but not the concordance (ie please fill this out!)

should add this to the delta test app tbh. Have added test 6. 

"""

#region TEST THREE

"""
Not actually a script I'm just going to:
a) copy the tui-v2_1_3 vde file to the tui-v2_1_3_iat directory in veda
b) run pre-processing for iat in the repo (pulls from veda, executes)
c) re-check the 

This test effectively asks: does the order of these items impact which of an arbitrary set of processes are selected from? 
If so, that would explain a lot of what we are seeing (but won't actually resolve the issue) 


A few concerns are that I am not 100% across which files are in/outputs when Veda processes and when our repo runs processing:

I am assumning that our repo will pull in all the dd and vde files etc and just use these when rerunning, no longer looking at veda
I am also assuming that the vde file won't be recreated from some other file in the gams working directory when running. 

Will check that:
    a) the models match after making this change and 
    b) the vde file in the iat testing area remains the same (ie matches when unsorted). This implies the changes are pulled through properly.


RESULT:

replacing the vde file in the Veda end and then preprocessing does not adjust the vde files on the repo end 
this might imply some of our workflow assumptions are wrong

As a subtest, we're going to: 
 1) replace the files on the repo end
 2) run the vde match tests (these match now so we copy-pasted correctly)
 3) if these match, run the model in preprocessing without veda import
 4) run the vde match tests again (maybe they get overwritten somehow)
 These no longer match so they are differently getting overwritten somehow which is quite interesting
 I guess they come from the GDX and I really can't be bothered messing with that 
 5) if they're still different, run the qa tests



"""


# Redoing the vde tests after importing: 

print(f"Redoing the vde tests after importing")
test_vde_files_match(qa_runs, sort_dfs = False)
test_vde_files_match(qa_runs, sort_dfs = True)

# Interestingly they do not match, implying a 

#region TEST FOUR 


"""
We're replacing the SPR-WE-N demand proportion (currently 0.034 in the generated csv) with 0.0339999999999999 to match the excel

This results in a perfectly aligned set of scenarios 
I don't know how to feel about this 
OTH-FOL-FOL-Tech15

"""

df.to_csv('var_fin.csv', index=False)
# df = get_veda_data("VAR_FIn")


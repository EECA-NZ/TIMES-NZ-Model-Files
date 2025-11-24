"""

Builds new processes and commodities for the EAF

Note that the input assumptions for this include
processes that have demand decrease when the EAF is installed.


These are:

a) Iron and Steel "motive power" STEEL-MOTOR-ISTEEL
b) Iron and Steel "iron and steel manufacturing) STEEL-FURNC-ISTEEL
c) coal feedstock STEEL-FDSTK-FDSTK
d) wee also halve the generation of the cogen plant

We also invent a new process just called EAF with the commodity demand "recycled steel"

This just goes into a subres

So we need a subres to introduce STEEL-ELC-EAF which produces ET

I THINK the easiest way to do this is have the EAF produce those commodities
So we don't mess with COM_PROJ, but rather force the EAF to produce them and reduce the generation

Then, if the EAF is cheaper, it should just retire the old demand.

BUT We do actually need to reduce the feedstock commodity demand

So since we're in the com_proj then might as well reduce the commodity demand!

Set EAF to 1 efficiency - its a 30MW draw at 50% capacity




START HERE

Build several files:

SUBRES:
EAF (tech and commodity)
NewTech (tech and commodity)

MODIFY BASE YEAR FILES

ELC_CoalCHP_GlenbrookSteel should be COA in and INDELC out

SCENARIO:

new scenario for demand (not in demand section, confusingly)

EAF demand trad/trans (this should include ELC_CoalCHP_GlenbrookSteel demand reductions)
Newtech demand (only one, for trans)

DEMAND MODIFICATIONS

reduce the indices for base year commodities:

STEEL-MOTOR-ISTEEL
STEEL-FURNC-ISTEEL
STEEL-FDSTK-FDSTK

by half with initial EAF, then to 0 in full recycling scenario (trad/trans)

(reduce gas also?? I dont think so?)



"""

eaf_install_dates = [2026, 2036]


# read in

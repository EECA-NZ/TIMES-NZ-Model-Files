#!/usr/bin/env python3
"""
Stage 4 – VEDA-format builders for the transport (TRA) sector.

• Reads stage 2 base-year demand CSV
• Builds commodity / process / parameter tables
• Writes them to   DATA_INTERMEDIATE/stage_4_veda_format/base_year_tra
"""


from prepare_times_nz.stage_4.transport import main as create_baseyear_tra_files

create_baseyear_tra_files()

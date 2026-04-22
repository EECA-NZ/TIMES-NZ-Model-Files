"""
Writes all the standard input scenarios

 - Carbon prices
 - Coal ban

"""

from prepare_times_nz.stage_4.carbon_prices import main as write_carbon_prices
from prepare_times_nz.stage_4.coal_ban import main as build_coal_ban
from prepare_times_nz.stage_4.discount_rates import main as write_discount_rates


def main():
    """
    Entrypoint
    """
    write_carbon_prices()
    write_discount_rates()
    build_coal_ban()


if __name__ == "__main__":
    main()

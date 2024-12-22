'''
Download the IRS tables from the IRS website and save them as a dictionary of pandas dataframes.
'''


from pathlib import Path
import pandas as pd


class TaxTable:
    '''
    A tax lookup table, as from from the IRS.
    '''
    year: int
    table: pd.DataFrame

    def __init__(self, year: int, file: Path):
        self.year = year
        self.table = pd.read_csv(file) # type: ignore

IRS_2024 = TaxTable(2024, Path(__file__).parent / 'data/IRS-rates-2024.csv')
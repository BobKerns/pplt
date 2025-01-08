'''
Various types of lookup tables.
'''

from pathlib import Path
import pandas as pd
from typing import cast, Any

from pplt.dates import parse_month

class LookupTable:
    '''
    A lookup table.
    '''
    table: pd.DataFrame

    def __init__(self, file: Path):
        self.table = pd.read_csv(file) # type: ignore
        if 'Month' in self.table:
            self.table['Month'] =  self.table['Month'].apply(parse_month) # type: ignore

    def lookup(self, key: str, value: str, column: str):
        '''
        Lookup a value in the table.
        '''
        return cast(float, self.table[self.table[key] == value].iloc[0][column])

    def interpolate(self, key: str, date: Any, column: str) -> float:
        '''
        Interpolate a value in the table.
        '''
        date_ = parse_month(date)
        df0 = self.table[self.table[key] >= date_]
        t0 = df0.iloc[0]['Month'] # type: ignore
        t1 = df0.iloc[1]['Month'] # type: ignore
        v0 = df0.iloc[0][column] # type: ignore
        v1 = df0.iloc[1][column] # type: ignore
        num: int = (date_ - t0).days # type: ignore
        den: int = (t1 - t0).days # type: ignore
        ratio = num / den # type: ignore
        return v0 + (v1 - v0) * ratio # type: ignore
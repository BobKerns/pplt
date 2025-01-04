'''
Test load_data
'''

from pathlib import Path

from pplt.loader import load_scenario

ROOT=Path(__file__).parent.parent

def test_load():
    '''
    At least test our example file.
    '''
    load_scenario(ROOT / 'data.yml')

import pandas as pd
from pathlib import Path
from datetime import datetime

def create_custom_period(start='', end=''):
    df_custom = pd.read_csv(Path.cwd() / 'Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_2.csv',
                                sep=',', encoding='latin_1', parse_dates=['Fecha'], infer_datetime_format=True)
    units_row = df_custom.iloc[0]
    df_custom = df_custom.set_index('Fecha')
    start = datetime.strptime(start, '%d/%m/%Y')
    end = datetime.strptime(end, '%d/%m/%Y')
    df_custom = df_custom.loc[start:end]
    df_custom = df_custom.reset_index(drop=False)
    df_custom = pd.concat([pd.DataFrame([units_row]), df_custom], ignore_index=True)
    df_custom.to_csv(Path.cwd() / 'Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_CUSTOM.csv', index=False, sep=',', encoding='latin-1', decimal='.')
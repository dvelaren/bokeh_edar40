import os
from pathlib import Path

## Mask Constants
# Vars ABSOLUTAS file name directory
OUT_VARS_ABSOLUTAS_FILE_NAME=Path('./static/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_VARIABLES_ABSOLUTAS.csv')

# Vars RENDIMIENTOS file name directory
OUT_VARS_RENDIMIENTOS_FILE_NAME=Path('./static/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_VARIABLES_RENDIMIENTOS.csv')

# Vars out column names
VARS_COLUMN_NAMES = ['Atributo', 'Valor_MAX_NORMA']

# Vars norma names and values
VARS_NORMA_ABSOLUTAS = {'efluente_MES_conc': 35, 'efluente_DBO5t_conc': 25, 'efluente_DQOt_conc': 125, 'efluente_Pt_conc': 1, 'efluente_Ntk_conc': 10}
VARS_NORMA_RENDIMIENTOS = {'efluente_rend_elim_SST': 0.7, 'efluente_rend_elim_DBO5': 0.7, 'efluente_rend_elim_DQOt': 0.75, 'efluente_rend_elim_Pt': 0.8, 'efluente_rend_elim_NTK': 0.9}

## Meteo Constants
# Specify INPUT data Excel file name provided by Veolia/UTEDEZA (EDAR Cartuja)
IN_METEO_DATA_FILE_DIR=Path('./data/Meteo/')
# IN_METEO_LIVE_FILE = Path('./data/METEO UTEDEZA EDAR 4.0.xlsx') # No dropbox
IN_METEO_LIVE_FILE = Path('/home/edar/Dropbox/Data/METEO UTEDEZA EDAR 4.0.xlsx') # Dropbox

# OUT_DATA_FILE_NAME_PERIOD_2='../OUT_data/EDAR4.0_EDAR_Cartuja_METEO_PERIOD_2.csv'
OUT_METEO_DATA_FILE_NAME_PERIOD_2=Path('./data/METEO_PERIOD_2.xlsx')

# Year folders
# YEAR_FOLDERS=['2018','2019']
YEAR_FOLDERS = [f.name for f in os.scandir(IN_METEO_DATA_FILE_DIR) if f.is_dir()]

# Months folder names
MONTH_FOLDER_NAMES=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio',
                    'Agosto','Septiembre','Octubre','Noviembre','Diciembre']

# Month selection dictionary depending on year. For 2018 it starts from May until Nov (Dec is empty)
# For 2019 only Jan and Feb are available
# YEAR_MONTHS={'2018':MONTH_FOLDER_NAMES[4:],'2019':MONTH_FOLDER_NAMES[0:9]}
YEAR_MONTHS={year: (MONTH_FOLDER_NAMES[4:] if year == '2018' else MONTH_FOLDER_NAMES[0:len([f.name for f in os.scandir(IN_METEO_DATA_FILE_DIR / year) if f.is_dir()])]) for year in YEAR_FOLDERS}

# Data file names dictionary
DATA_FILE_NAMES = {'P24':'PrecipitacionHorariaZaragoza.csv', 'TMED':'TemperaturaMediaZaragoza.csv',
                   'PRES':'PresionZaragoza.csv'}

# Columns that will be parsed
COLUMN_NAMES={'P24':['P24'],'TMED':['TMED'],'PRES':['PRES00','PRES07','PRES13','PRES18']}

# Meteo live column names mapping
COLUMN_NAMES_METEO_LIVE = {
    'P24':'P24',
    'TMED':'TMED',
    'PRES':['PRES00', 'PRES07', 'PRES13', 'PRES18']
}

# Units row to add at the beginning of dataframe
UNITS={'Fecha':'NaT','P24':'mm','TMED':'(1/10)C','PRES00':'(1/10)hPa','PRES07':'(1/10)hPa','PRES13':'(1/10)hPa','PRES18':'(1/10)hPa'}

METEO_SHEET_NAME_PERIOD_2='PERIOD2(2018-NOW)'

METEO_LIVE_SHEET_NAME='Presion'

## Main Constants 
# Specify INPUT data Excel file name provided by Veolia/UTEDEZA (EDAR Cartuja)
# IN_DATA_FILE_NAME=Path('./data/ID UTEDEZA EDAR 4.0.xlsx') # No dropbox
IN_DATA_FILE_NAME=Path('/home/edar/Dropbox/Data/ID UTEDEZA EDAR 4.0.xlsx') # Dropbox

# Specify INPUT data for metereologic info
IN_METEO_FILE_NAME_PERIOD_1=Path('./data/METEO_PERIOD_1.xlsx')
IN_METEO_FILE_NAME_PERIOD_2=Path('./data/METEO_PERIOD_2.xlsx')

# Sheet ID
IN_DATA_SHEET_NAME_ID='ID'

# Specify if it is requested to create the list of column names of sheet ID
blnCreate_ID_sheet_columns_list=True
ID_EDAR_CARTUJA_ID_sheet_column_names_FILE_NAME=Path('./static/Cartuja_Datos/ID_EDAR_Cartuja_column_names_sheet_ID.md')

# Sheet YOKO
IN_DATA_SHEET_NAME_YOKO='YOKO'

# Specify if it is requested to create the list of column names of sheet YOKO
blnCreate_YOKO_sheet_columns_list=True
ID_EDAR_CARTUJA_YOKO_sheet_column_names_FILE_NAME=Path('./static/Cartuja_Datos/ID_EDAR_Cartuja_column_names_sheet_YOKO.md')

# Sheet ANALITICA
IN_DATA_SHEET_NAME_ANALITICA='ANALITICA'

# Specify if it is requested to create the list of column names of sheet ANALITICA
blnCreate_ANALITICA_sheet_columns_list=True
ID_EDAR_CARTUJA_ANALITICA_sheet_column_names_FILE_NAME=Path('./static/Cartuja_Datos/ID_EDAR_Cartuja_column_names_sheet_ANALITICA.md')

# Specify Excel file name specifiying variables ro be read
VARIABLES_TO_READ_FILE_NAME=Path('./data/EDAR4.0_EDAR_Cartuja_VARIABLES_V5.0.xlsx')

# Sheet ID_INFLUENTE
VARIABLES_FILE_SHEET_ID_INFLUENTE='ID_INFLUENTE'

# Sheet ID_BIOS
VARIABLES_FILE_SHEET_ID_BIOS='ID_BIOS'

# Sheet ID_FANGOS
VARIABLES_FILE_SHEET_ID_FANGOS='ID_FANGOS'

# Sheet ID_HORNO
VARIABLES_FILE_SHEET_ID_HORNO='ID_HORNO'

# Sheet ID_EFLUENTE
VARIABLES_FILE_SHEET_ID_EFLUENTE='ID_EFLUENTE'

# Sheet ID_ELECTRICIDAD
VARIABLES_FILE_SHEET_ID_ELECTRICIDAD='ID_ELECTRICIDAD'

# Sheet YOKO
VARIABLES_FILE_SHEET_YOKO='YOKO'

# Sheet ANALITICA
VARIABLES_FILE_SHEET_ANALITICA='ANALITICA'

# Variables file's sheets' column names
VARS_ORIGEN_COL_NAME = 'ORIGEN'
VARS_DESTINO_COL_NAME = 'DESTINO'
VARS_CALCULADAS_COL_NAME = 'CALCULADAS'

# Specify OUTPUT DATA CSV file (for PERIODS 1 & 2; see time filters for PERIOD 1 & 2 below)
OUT_DATA_FILE_NAME_PERIOD_1=Path('./static/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_1.csv')
OUT_DATA_FILE_NAME_PERIOD_2=Path('./static/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_2.csv')
LATEST_DATE_FILE=Path('./data/latest_date.pkl')

# Other constants of interest
DATE_COLUMN_NAME = 'Fecha'
FIRST_UNKONW_COLUMN_NAME = 'Unnamed: 0'
# Import required libraries
import pandas as pd
import pickle
# total_model_dict = {}
# Functions to save and load objects
def save_obj(obj, name):
    """Stores an object (obj) into ROM with a desired name inside /obj folder
    
    Parameters:
        obj: Object to be stored
        name: Desired filename with path to be stored
    """
    with open(name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    """Loads an object into RAM with a desired name inside /obj folder
    
    Parameters:
        name: Desired filename to be loaded
        
    Returns:
        Loaded object
    """
    with open(name, 'rb') as f:
        return pickle.load(f)

# Read all possible models
def create_df_outs(file, sheets, cols):
    """Creates df and outs_dict from excel file using specifyed sheets () and column names (cols)
    
    Parameters:
        file: Excel file to be used
        sheets: Working sheets desired to be used
        cols: Columns from sheet that will be used
    
    Returns:
        df, outs_dict: tuple with the following variables
            df: Dataframe with processed file
            outs_dict: Dictionary with all the outputs that can be modeled
    """
    # print('Entre aqui')
    outs_dict = {}
    df = {}
    for ws in sheets:
        df[ws] = pd.read_excel(file, sheet_name=ws, usecols=cols)
        for out in list(df[ws]['OUT'].dropna()):
            outs_dict.update({out:ws})
    return df, outs_dict

# Read all possible in variables for each model
def create_model_vars_dict(df, outs_dict):
    """Creates the models variables dictionary which include all the variables that can be used to model each output
    
    Parameters:
        df: Dataframe with all the parsed data
        outs_dict: Dictonary including all the outputs that can be modeled as key and the sheet location as value
        
    Returns:
        total_model_dict: Total model dictionary with model as key and a list variables that can be used as value
    """
    total_model_dict = {}
    for out in outs_dict:
        proc_in_list = []
        for proc_in in list(df[outs_dict[out]]['PROCESOS_IN'].dropna()):
            # import pdb; pdb.set_trace()
            proc_in_list = proc_in_list + list(df[proc_in]['OUT'].dropna()) + list(df[proc_in]['IN'].dropna()) + list(df[proc_in]['MANIPULABLES'].dropna())
        total_model_dict.update({out: list(df[outs_dict[out]]['IN'].dropna()) + list(df[outs_dict[out]]['MANIPULABLES'].dropna()) + proc_in_list})
    return total_model_dict

def load_or_create_model_vars(model_vars_file, mask_file, sheets, cols, force_create=False):
    """Loads from ROM the total_model_dict file if it exists. In other case it creates a new file in ROM
    
    Parameters:
        model_vars_file: Model variables existing file name or new name
        mask_file: Model variables excel mask
        sheets: List with sheet names to read
        cols: Column names inside sheet to process
        force_create: Forces to read again the mask_file and create a new model_vars_file in ROM and RAM
        
    Returns:
        total_model_dict: Total model dictionary with model as key and a list variables that can be used as value
    """
    total_model_dict = {}
    def create_obj():
        df, outs_dict = create_df_outs(mask_file, sheets, cols)
        total_model_dict = create_model_vars_dict(df, outs_dict)
        save_obj(total_model_dict, model_vars_file)
        return total_model_dict
        # import pdb; pdb.set_trace()

    if force_create:
        print('Creando nuevo archivo')
        total_model_dict = create_obj()
    else:
        try:
            total_model_dict = load_obj(model_vars_file)
            print('Cargando archivo pre-creado')
        except (OSError, IOError):
            print('Creando nuevo archivo - sin forzar')
            total_model_dict = create_obj()
    return total_model_dict
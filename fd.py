import h2o

from datetime import datetime as dt
from datetime import timedelta as td

from recordclass import recordclass

from collections import defaultdict

class NBA(object):

    ## variables shared by instances
    ## should be constant but can
    ## be changed on the fly with
    ## set_point_vals()
    ppa = 1.5 ## points per assist 
    ppb = 3.0 ## points per block
    ppp = 1.0 ## points per point
    ppr = 1.2 ## points per rebound
    pps = 3.0 ## points per steal
    ppt = -1. ## points per turnover

    def __init__(self, date=None, n_training_days=20, validation=True):
    
        ## initialize h2o if not already running
        if h2o.connection() is None:
            h2o.init()
        
        ## default value of date is today
        if date is None:
            date = str(dt.now()).split()[0]
        
        ## validation frame
        self.valid=None
        if validation:
            self.valid = h2o.import_file('data/rotoguru-'+date+'.csv')

        ## make list of csv files and import as training
        train_files = []
        self.dt_gameday = dt.strptime(date, '%Y-%m-%d')
        for it in range(1,n_training_days+1):
            tmp_date = str((self.dt_gameday-td(days=it))).split()[0]
            train_files.append('data/rotoguru-'+tmp_date+'.csv')

        self.train = h2o.import_file(train_files)

        ## output variable
        self.response = 'Fan Points'

        ## recordclass for vars_dict
        self.Var = recordclass('Var', 'include is_cat')
        V = self.Var ## for readability/to avoid overflow

        self.var_dict = defaultdict(lambda: V(0,1), {
            ## rotoguru
            'Date':       V(0,1), 'GID':       V(0,1),
            'Pos':        V(1,1), 'Name':      V(1,1),
            'Starter':    V(0,1), 'FD Pts':    V(0,0),
            'FD Salary':  V(1,0), 'Team':      V(1,1),
            'H/A':        V(1,1), 'Oppt':      V(1,1),
            'Team Score': V(0,0), 'Oppt Score':V(0,0),
            'Minutes':    V(0,0), 'Stat line': V(0,1),
            ## derived
            'Fan Points': V(0,0), 
            'Assists':    V(0,0), 'Rebounds':  V(0,0),
            'Blocks':     V(0,0), 'Points':    V(0,0),
            'Steals':     V(0,0), 'Turnovers': V(0,0),
        })

    def get_frames(self, ):
        """returns list of frames associated with instance"""

        frame_list = [self.train, self.valid]

        return [frame for frame in frame_list if frame is not None]

    def set_point_vals(self, ppa=1.5, ppb=3.0, ppp=1.0, ppr=1.2, pps=3.0, ppt=-1.,
                       is_global=False):
        """Use this function to change point totals 
        is_global=False (default) for specific instance
        is_global=True for all instances"""
        
        if is_global:
            NBA.ppa = ppa
            NBA.ppb = ppb
            NBA.ppp = ppp
            NBA.ppr = ppr
            NBA.pps = pps
            NBA.ppt = ppt
        else:
            self.ppa = ppa
            self.ppb = ppb
            self.ppp = ppp
            self.ppr = ppr
            self.pps = pps
            self.ppt = ppt
                                    

    def include_vars(self, var_list, strict=False):
        """Function to modify self.var_dict seamlessly 

        If var already in self.var_dict, will turn value to True

        If var not already in self.var_dict, will add var as new key and 
        set its value to True

        If strict=True, will set all other vars in self.var_dict to false

        If strict=False (default), will not modify any other values in self.var_dict
        is_cat can be a list of ints (bools) indicating which vars are categorial
        or is_cat can be a single int (bool) if all are of same type
        by default, all variabls are considered to be numeric
        """
        
        for it in range(len(var_list)):
            self.var_dict[var_list[it]].include = True
                                    
        ## remove other vars only if strict=True
        if strict:
            others = [var for var in self.var_dict if var not in var_list]
            for var in others:
                self.var_dict[var].include = False
                
    def exclude_vars(self, var_list, strict=False):
        """Function to modify self.var_dict seamlessly 

        If var already in self.var_dict, will turn value to False
        If var not already in self.var_dict, will add var as 
        new key and set its value to False

        If strict=True, will set all other vars in self.var_dict to True

        If strict=False (default), will not modify any other values in self.var_dict
        """

        for var in var_list:
            self.var_dict[var].include = False

        ## include other vars only if strict=True
        if strict:
            others = [var for var in self.var_dict if var not in var_list]
            for var in others:
                    self.var_dict[var].include = True

    def prep_vars(self,):
        """Set asfactor() and asnumeric()"""

        for df in self.get_frames():
            for var in df.columns:
                if self.var_dict[var].is_cat:
                    df[var] = df[var].asfactor()
                else:
                    df[var] = df[var].asnumeric()

    def replace_missing(self,):
        """Missing values need to be filled in
        Only fixing known issues, should check for nans later"""

        ## non-starter=0 instead of nan
        for frame in self.get_frames():
            frame[frame["Starter"].isna(), "Starter"] = 0
            frame[frame["Points"].isna(), "Points"] = 0
            frame[frame["Rebounds"].isna(), "Rebounds"] = 0       
            frame[frame["Assists"].isna(), "Assists"] = 0
            frame[frame["Steals"].isna(), "Steals"] = 0
            frame[frame["Blocks"].isna(), "Blocks"] = 0
            frame[frame["Turnovers"].isna(), "Turnovers"] = 0

    def split_stats(self, ):
        """Stat line is given as one column. Need to split into each"""

        
        for df in self.get_frames():
            df['Stat line'] = df['Stat line'].ascharacter()
            df['Points'] = df['Stat line'].sub('pt.*','').sub('.* ','').asnumeric()
            df['Rebounds'] = df['Stat line'].sub('rb.*','').sub('.* ','').asnumeric()
            df['Assists'] = df['Stat line'].sub('as.*','').sub('.* ','').asnumeric()
            df['Steals'] = df['Stat line'].sub('st.*','').sub('.* ','').asnumeric()
            df['Blocks'] = df['Stat line'].sub('bl.*','').sub('.* ','').asnumeric()
            df['Turnovers'] = df['Stat line'].sub('to.*','').sub('.* ','').asnumeric()
            df['Stat line'] = df['Stat line'].asfactor()

    def score_data(self,):
        """Compute the fantasy points for each player for all dataframes"""

        for frame in self.get_frames():
            frame['Fan Points'] = (self.ppa*frame['Assists'] +
                                   self.ppb*frame['Blocks'] +
                                   self.ppp*frame['Points'] +
                                   self.ppr*frame['Rebounds'] +
                                   self.pps*frame['Steals'] +
                                   self.ppt*frame['Turnovers'])

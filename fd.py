import h2o
from datetime import datetime as dt
from datetime import timedelta as td

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
            tmp_date = str((self.dt_gameday-td(days=it)).split())[0]
            train_files.append('data/rotoguru-'+tmp_date+'.csv')

        self.train = h2o.import_file(train_files)

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

    def prep_vars(self,):
        """Set asfactor() and asnumeric()"""

        return 0 ## placeholder

    def replace_missing(self,):
        """Missing values need to be filled in
        Only fixing known issues, should check for nans later"""

        ## non-starter=0 instead of nan
        for frame in get_frames():
            frame['Starter'] = frame[frame["Starter"].isna(), "Starter"] = 0


    def score_data(self,):
        """Compute the fantasy points for each player for all dataframes"""

        for frame in get_frames():
            frame['fan_points'] = (self.ppa*frame['Assists']*self.ppa +
                                   self.ppb*frame['Blocks']*self.ppb +
                                   self.ppp*frame['Points']*self.ppp +
                                   self.ppr*frame['Rebounds']*self.ppr +
                                   self.pps*frame['Steals']*self.pps +
                                   self.ppt*frame['Turnovers']*self.ppt)

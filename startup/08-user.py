import sys
import os
import shutil
from distutils.dir_util import copy_tree
import json

run_report(__file__)


class BMM_User():
    def __init__(self):
        self.DATA = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'
        self.prompt = True
        self.final_log_entry = True
        self.date = ''
        self.gup = 0
        self.saf = 0
        self.name = None
        self.staff = False
        self.read_foils = None

    def new_experiment(self, folder, gup=0, saf=0, name='Betty Cooper'):
        '''
        Get ready for a new experiment.  Run this first thing when a user
        sits down to start their beamtime.  This will:
        1. Create a folder, if needed, and set the DATA variable
        2. Set up the experimental log, creating an experiment.log file, if needed
        3. Write templates for scan.ini and macro.py, if needed
        4. Set the GUP and SAF numbers as metadata

        Input:
          folder:   data destination
          gup:      GUP number
          saf:      SAF number
          name:     name of PI (optional)
        '''

        step = 1
        ## make folder
        if not os.path.isdir(folder):
            os.makedirs(folder)
            print('%d. Created data folder' % step)
        else:
            print('%d. Found data folder' % step)
        imagefolder = os.path.join(folder, 'snapshots')
        if not os.path.isdir(imagefolder):
            os.mkdir(imagefolder)
            print('   Created snapshot folder')
        else:
            print('   Found snapshot folder')
    
        global DATA
        DATA = folder + '/'
        self.DATA = folder + '/'
        print('   DATA = %s' % DATA)
        print('   snapshots in %s' % imagefolder)
        step += 1

        #if os.path.isdir('NIST/'):
    
        ## setup logger
        BMM_user_log(os.path.join(folder, 'experiment.log'))
        print('%d. Set up experimental log file: %s' % (step, os.path.join(folder, 'experiment.log')))
        step += 1

        startup = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup')

        ## write scan.ini template
        initmpl = os.path.join(startup, 'scan.tmpl')
        scanini = os.path.join(folder, 'scan.ini')
        if not os.path.isfile(scanini):
            with open(initmpl) as f:
                content = f.readlines()
            o = open(scanini, 'w')
            o.write(''.join(content).format(folder=folder, name=name))
            o.close()
            print('%d. Created INI template: %s' % (step, scanini))
        else:
            print('%d. Found INI template: %s' % (step, scanini))
        step += 1

        ## write macro template
        macrotmpl = os.path.join(startup, 'macro.tmpl')
        macropy = os.path.join(folder, 'macro.py')
        if not os.path.isfile(macropy):
            with open(macrotmpl) as f:
                content = f.readlines()
            o = open(macropy, 'w')
            o.write(''.join(content).format(folder=folder))
            o.close()
            print('%d. Created macro template: %s' % (step, macropy))
        else:
            print('%d. Found macro template: %s' % (step, macropy))
        step += 1

        ## copy energy change instructions
        # eci = os.path.join(startup, 'Energy Change')
        # ecitarget = os.path.join(folder, 'Energy Change')
        # if not os.path.isfile(ecitarget):
        #     shutil.copyfile(eci, ecitarget)
        #     print('%d. Copied energy change instructions', step)
        # else:
        #     print('%d. Found energy change instructions', step)
        # step += 1
    
        ## make html folder, copy static html generation files
        htmlfolder = os.path.join(folder, 'dossier')
        if not os.path.isdir(htmlfolder):
            os.mkdir(htmlfolder)
            for f in ('sample.tmpl', 'manifest.tmpl', 'logo.png', 'style.css', 'trac.css'):
                shutil.copyfile(os.path.join(startup, f),  os.path.join(htmlfolder, f))
            manifest = open(os.path.join(DATA, 'dossier', 'MANIFEST'), 'a')
            manifest.close()
            print('%d. Created dossier folder, copied html generation files, touched MANIFEST' % step)
        else:
            print('%d. Found dossier folder' % step)
        print('   dossiers in %s' % htmlfolder)
        step += 1
     
        ## make prj folder
        prjfolder = os.path.join(folder, 'prj')
        if not os.path.isdir(prjfolder):
            os.mkdir(prjfolder)
            print('%d. Created Athena prj folder' % step)
        else:
            print('%d. Found Athena prj folder' % step)
        print('   projects in %s' % prjfolder)
        step += 1
   
        self.gup = gup
        self.saf = saf
        print('%d. Set GUP and SAF numbers as metadata' % step)
        step += 1

        global _user_is_defined
        _user_is_defined = True
    
        return None

    def start_experiment(self, name=None, date=None, gup=0, saf=0):
        '''
        Get ready for a new experiment.  Run this first thing when a user
        sits down to start their beamtime.  This will:
          * Create a folder, if needed, and set the DATA variable
          * Set up the experimental log, creating an experiment.log file, if needed
          * Write templates for scan.ini and macro.py, if needed
          * Copy some other useful files
          * Make snapshots, dossier, and prj folders
          * Set the GUP and SAF numbers as metadata

        Input:
          name:     name of PI
          date:     YYYY-MM-DD start date of experiment (e.g. 2018-11-29)
          gup:      GUP number
          saf:      SAF number
        '''
        if name is None:
            print(colored('You did not supply the user\'s name', 'red'))
            return()
        if date is None:
            print(colored('You did not supply the start date', 'red'))
            return()
        if gup == 0:
            print(colored('You did not supply the GUP number', 'red'))
            return()
        if saf == 0:
            print(colored('You did not supply the SAF number', 'red'))
            return()
        if name in BMM_STAFF:
            self.staff = True
            folder = os.path.join(os.getenv('HOME'), 'Data', 'Staff', name, date)
        else:
            self.staff = False
            folder = os.path.join(os.getenv('HOME'), 'Data', 'Visitors', name, date)
        self.name = name
        self.date = date
        self.new_experiment(folder, saf=saf, gup=gup, name=name)

        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            os.chmod(jsonfile, 0o644)
        with open(jsonfile, 'w') as outfile:
            json.dump({'name': name, 'date': date, 'gup' : gup, 'saf' : saf}, outfile)
        os.chmod(jsonfile, 0o444)


    def start_experiment_from_serialization(self):
        '''In the situation where bsui needs to be stopped (or crashes) before
        an experiment is properly ended using the end_experiment()
        command, this function will read a json serialization of the
        arguments to the start_experiment() command.

        The intent is that, if that serialization file is found at
        bsui start-up, this function is run so that the session is
        immediately ready for the current user.

        In the situation where this start-up script is "%run -i"-ed,
        the fact that _user_is_defined is True will be recognized.
        '''
        global _user_is_defined
        if _user_is_defined:
            return()
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            user = json.load(open(jsonfile))
            if 'name' in user:
                self.start_experiment(name=user['name'], date=user['date'], gup=user['gup'], saf=user['saf'])
            if 'foils' in user:
                self.read_foils = user['foils'] # see 76-edge.py, line 111, need to delay configuring foils until 76-edge is read

    def show_experiment(self):
        print('DATA  = %s' % DATA)
        print('GUP   = %d' % self.gup)
        print('SAF   = %d' % self.saf)
        print('foils = %s' % ' '.join(map(str, foils.slots)))

    def end_experiment(self, force=False):
        '''
        Copy data from the experiment that just finished to the NAS, then
        unset the logger and the DATA variable at the end of an experiment.
        '''
        global DATA
        global _user_is_defined

        if not force:
            if not _user_is_defined:
                print(colored('There is not a current experiment!', 'lightred'))
                return(None)

            #######################################################################################
            # create folder and sub-folders on NAS server for this user & experimental start date #
            #######################################################################################
            destination = os.path.join('/nist', 'xf06bm', 'user', self.name, self.date)
            if not os.path.isdir(destination):
                os.makedirs(destination)
            for d in ('dossier', 'prj', 'snapshots'):
                if not os.path.isdir(os.path.join(destination, d)):
                    os.makedirs(os.path.join(destination, d))
            try:
                copy_tree(DATA, destination)
                report('NAS data store: "%s"' % destination, 'white')
                #print(colored('NAS data store: "%s"' % destination, 'white'))
                #BMM_log_info('NAS data store: "%s"' % destination)
            except:
                print(colored('Unable to write data to NAS server', 'red'))
        
            #####################################################################
            # remove the json serialization of the start_experiment() arguments #
            #####################################################################
            jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
            if os.path.isfile(jsonfile):    
                os.chmod(jsonfile, 0o644)
                os.remove(jsonfile)

        ###############################################################
        # unset self attributes, DATA, and experiment specific logger #
        ###############################################################
        BMM_unset_user_log()
        DATA = os.path.join(os.environ['HOME'], 'Data', 'bucket') + '/'
        self.DATA = os.path.join(os.environ['HOME'], 'Data', 'bucket') + '/'
        self.date = ''
        self.gup = 0
        self.saf = 0
        self.name = None
        self.staff = False
        _user_is_defined = False

        return None

BMMuser = BMM_User()
BMMuser.start_experiment_from_serialization()

## some backwards compatibility....
whoami           = BMMuser.show_experiment
start_experiment = BMMuser.start_experiment
end_experiment   = BMMuser.end_experiment

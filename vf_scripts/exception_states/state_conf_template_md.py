from data import univ_settings
univ_settings = reload(univ_settings)
import os, imp
from data import state_specific
state_specific.STATE = 'NJ'
state_specific.ELECTION = 2012
state_specific.VIP_SOURCE = state_specific.STATE+'VIP'
state_specific.VF_SOURCE = state_specific.STATE+'VF'
state_specific.CANDIDATE_SOURCE = state_specific.STATE+'Candidates'
state_specific.VIP_FEED_LOCATION = '/tmp/temp'
state_specific.ED_MAP_LOCATION = '/home/gaertner/bip-data/data/voterfiles/{state}/ed_map.py'.format(state=state_specific.STATE.lower())
#state_specific.ED_MAP_CSV_LOCATION = '/home/gaertner/bip-data/data/voterfiles/nj/ed_map.csv'
state_specific.CANDIDATE_FILE_LOCATION = '/home/gaertner/Dropbox/BIP Production/{state} Candidates.csv'.format(state=state_specific.STATE)
state_specific.UNCOMPRESSED_VOTER_FILE_LOCATION = 'example' 
state_specific.VOTER_FILE_LOCATION = '/home/gaertner/bip-data/data/voterfiles/{state}/vf_compressed'.format(state=state_specific.STATE.lower())
state_specific.HOME = '/home/gaertner/bip-data/data/voterfiles/{state}'.format(state=state_specific.STATE.lower())
state_specific.VOTER_FILE_SCHEMA = '/home/gaertner/bip-data/schema/ts_voter_file.sql'
state_specific.districts = imp.load_source('districts',os.path.join('data','voterfiles',state_specific.STATE.lower(), 'districts.py'))
state_specific.COUNTY_SCHOOL_DISTRICT = True
state_specific.COUNTY_JUDICIAL_DISTRICT = False
state_specific.STATE_EDMAP = univ_settings.table_functions.get_edmap(state_specific.ED_MAP_LOCATION)
from data.state_specific import *
from data import target_smart_defaults as tsd
tsd = reload(tsd)
from data import candidate_defaults as cd
cd = reload(cd)
#VOTER_FILE = tsd.VOTER_FILE
VOTER_FILE_DISTRICTS = tsd.VOTER_FILE_DISTRICTS
SCHOOL_DISTRICT_IMPORT = dict(tsd.td.DEFAULT_VF_TABLE)
SCHOOL_DISTRICT_IMPORT['udcs'] = dict(tsd.td.DEFAULT_VF_TABLE['udcs'])
SCHOOL_DISTRICT_IMPORT['udcs'].update({'type':'school_district'})
SCHOOL_DISTRICT_IMPORT.update({
    'table':'electoral_district_schd_import',
    'columns':{
        'name':{'function':tsd.td.reformat.concat_us, 'columns':(22,33,)},
        'identifier':{'function':tsd.td.reformat.ed_concat,'columns':(22,33,),'defaults':{'type':'school_district'}},
        'id_long':{'function':tsd.td.reformat.ed_concat,'columns':(22,33,),'defaults':{'type':'school_district'}}
        },
    })

SCHOOL_DISTRICT_ACTUAL = dict(tsd.td.DEFAULT_ACTUAL_TABLE)
SCHOOL_DISTRICT_ACTUAL.update({
    'schema_table':'electoral_district',
    'import_table':SCHOOL_DISTRICT_IMPORT,
    'long_fields':({'long':'id_long','real':'id'},),
    'long_from':('id_long',),
    'distinct_on':('id_long',),
    })

SCHOOL_DISTRICT__PRECINCT_IMPORT = dict(tsd.td.DEFAULT_VF_TABLE)
SCHOOL_DISTRICT__PRECINCT_IMPORT.update({
    'table':'electoral_district__precinct_schd_import',
    'filename':state_specific.VOTER_FILE_LOCATION,
    'columns':{
        'electoral_district_id_long':{'function':tsd.td.reformat.ed_concat,'columns':(22,33,),'defaults':{'type':'school_district'}},
        'precinct_id_long':{'function':tsd.td.reformat.concat_us,'columns':(22,29,28)},
        },
    })

SCHOOL_DISTRICT__PRECINCT_ACTUAL = dict(tsd.td.DEFAULT_ACTUAL_TABLE)
SCHOOL_DISTRICT__PRECINCT_ACTUAL.update({
    'schema_table':'electoral_district__precinct',
    'import_table':SCHOOL_DISTRICT__PRECINCT_IMPORT,
    'long_fields':({'long':'electoral_district_id_long','real':'electoral_district_id'},{'long':'precinct_id_long','real':'precinct_id'},),
    'distinct_on':('precinct_id_long','electoral_district_id_long',),
    'long_to':(
        {
            'to_table':'electoral_district_schd_import',
            'local_key':'electoral_district_id_long',
            'to_key':'id_long',
            'real_to_key':'id',
            },
        ),
    })

ACTUAL_TABLES = (
        tsd.PRECINCT_ACTUAL,
        tsd.LOCALITY_ACTUAL,
        tsd.CONGRESSIONAL_DISTRICT_ACTUAL,
        tsd.STATE_REP_DISTRICT_ACTUAL,
        tsd.JUDICIAL_DISTRICT_ACTUAL,
        SCHOOL_DISTRICT_ACTUAL, 
        tsd.COUNTY_COUNCIL_ACTUAL,
        tsd.COUNTY_ACTUAL,
        tsd.STATE_ACTUAL,
        tsd.STATE_SENATE_DISTRICT_ACTUAL,
        tsd.CONGRESSIONAL_DISTRICT__PRECINCT_ACTUAL,
        tsd.STATE_REP_DISTRICT__PRECINCT_ACTUAL,
        tsd.JUDICIAL_DISTRICT__PRECINCT_ACTUAL,
        SCHOOL_DISTRICT__PRECINCT_ACTUAL,
        tsd.COUNTY_COUNCIL__PRECINCT_ACTUAL,
        tsd.COUNTY__PRECINCT_ACTUAL,
        tsd.STATE_SENATE_DISTRICT__PRECINCT_ACTUAL,
        tsd.STATE__PRECINCT_ACTUAL,
        cd.CANDIDATE_ACTUAL,
        cd.CONTEST_ACTUAL,
        cd.CANDIDATE_IN_CONTEST_ACTUAL,
        )

GROUPS = {
        #        'vf_group':TABLE_GROUP,
        }

UNIONS = (
        tsd.ELECTORAL_DISTRICT_UNION,
        )
ERSATZPG_CONFIG = dict(univ_settings.ERSATZPG_CONFIG)
ERSATZPG_CONFIG.update({
    'use_utf':True,
    'tables':{
        #        'voter_file':VOTER_FILE,
        'precinct':tsd.PRECINCT_IMPORT,
        'locality':tsd.LOCALITY_IMPORT,
        'congressional_district':tsd.CONGRESSIONAL_DISTRICT_IMPORT,
        'state_rep_district':tsd.STATE_REP_DISTRICT_IMPORT,
        'judicial_district':tsd.JUDICIAL_DISTRICT_IMPORT,
        'school_district':SCHOOL_DISTRICT_IMPORT,
        'county_council':tsd.COUNTY_COUNCIL_IMPORT,
        'county':tsd.COUNTY_IMPORT,
        'state':tsd.STATE_IMPORT,
        'state_senate_district':tsd.STATE_SENATE_DISTRICT_IMPORT,
        'congressional_district__precinct':tsd.CONGRESSIONAL_DISTRICT__PRECINCT_IMPORT,
        'state_rep_district__precinct':tsd.STATE_REP_DISTRICT__PRECINCT_IMPORT,
        'state_senate_district__precinct':tsd.STATE_SENATE_DISTRICT__PRECINCT_IMPORT,
        'judicial_district__precinct':tsd.JUDICIAL_DISTRICT__PRECINCT_IMPORT,
        'school_district__precinct':SCHOOL_DISTRICT__PRECINCT_IMPORT,
        'county_council__precinct':tsd.COUNTY_COUNCIL__PRECINCT_IMPORT,
        'county__precinct':tsd.COUNTY__PRECINCT_IMPORT,
        'state__precinct':tsd.STATE__PRECINCT_IMPORT,
        'candidate':cd.CANDIDATE_IMPORT,
        'contest':cd.CONTEST_IMPORT,
        'candidate_in_contest':cd.CANDIDATE_IN_CONTEST_IMPORT,
        },
        'key_sources':{
            #'precinct':1,
            #'district':1,
            #'locality':1,
            },
        'parallel_load':(
            {'tables':('precinct','locality','congressional_district','state_rep_district','state_senate_district','judicial_district','school_district','county_council','county','state','congressional_district__precinct','state_rep_district__precinct','state_senate_district__precinct','judicial_district__precinct','school_district__precinct','county_council__precinct','county__precinct','state__precinct'),'keys':{}},
            )
        })
from data import univ_settings
univ_settings = reload(univ_settings)
import os, imp
from data import state_specific
from collections import OrderedDict
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
state_specific.COUNTY_SCHOOL_DISTRICT = False
state_specific.COUNTY_JUDICIAL_DISTRICT = False
state_specific.STATE_EDMAP = univ_settings.table_functions.get_edmap(state_specific.ED_MAP_LOCATION)
from data.state_specific import *
from data import target_smart_defaults as tsd
tsd = reload(tsd)
from data import candidate_defaults as cd
cd = reload(cd)
#VOTER_FILE = tsd.VOTER_FILE
VOTER_FILE_DISTRICTS = (
'state',
'county_id',
'county_council',
'city_council',
#'municipal_district',
'school_district',
'judicial_district',
'congressional_district',
'state_rep_district',
'state_senate_district',
#'township',
#'ward'
)

SUPREME_COURT_IMPORT = dict(tsd.td.DEFAULT_VF_TABLE)
SUPREME_COURT_IMPORT['udcs'] = dict(tsd.td.DEFAULT_VF_TABLE['udcs'])
SUPREME_COURT_IMPORT['udcs'].update({'source':'NYVF','type':'special_1_judicial_district'})
SUPREME_COURT_IMPORT.update({
    'table':'electoral_district_special_1_import',
    'columns':{
        'name':tsd.VFMAX + 1,
        'identifier':{'function':tsd.td.reformat.ed_concat,'columns':(tsd.VFMAX+1,),'defaults':{'type':'special_1_judicial_district'}},
        'id_long':{'function':tsd.td.reformat.ed_concat,'columns':(tsd.VFMAX+1,),'defaults':{'type':'special_1_judicial_district'}}
        },
    })

SUPREME_COURT_ACTUAL = dict(tsd.td.DEFAULT_ACTUAL_TABLE)
SUPREME_COURT_ACTUAL.update({
    'schema_table':'electoral_district',
    'import_table':SUPREME_COURT_IMPORT,
    'long_fields':({'long':'id_long','real':'id'},),
    'long_from':('id_long',),
    'distinct_on':('id_long',),
    })

EXTRA_DISTRICTS = OrderedDict({
        'special_1_judicial_district':{'filename':'20121024_NY_StateSupremeCourt.txt','column':2,'prepend':()},
        })

CITY_COUNCIL_IMPORT = dict(tsd.td.DEFAULT_VF_TABLE)
CITY_COUNCIL_IMPORT['udcs'] = dict(tsd.td.DEFAULT_VF_TABLE['udcs'])
CITY_COUNCIL_IMPORT['udcs'].update({'type':'city_council'})
CITY_COUNCIL_IMPORT.update({
    'table':'electoral_district_cico_import',
    'columns':{
        'name':31,
        'identifier':{'function':tsd.td.reformat.ed_concat,'columns':(31,),'defaults':{'type':'city_council'}},
        'id_long':{'function':tsd.td.reformat.ed_concat,'columns':(31,),'defaults':{'type':'city_council'}}
        },
    })

CITY_COUNCIL_ACTUAL = dict(tsd.td.DEFAULT_ACTUAL_TABLE)
CITY_COUNCIL_ACTUAL.update({
    'schema_table':'electoral_district',
    'import_table':CITY_COUNCIL_IMPORT,
    'long_fields':({'long':'id_long','real':'id'},),
    'long_from':('id_long',),
    'distinct_on':('id_long',),
    })

CITY_COUNCIL__PRECINCT_IMPORT = dict(tsd.td.DEFAULT_VF_TABLE)
CITY_COUNCIL__PRECINCT_IMPORT.update({
    'table':'electoral_district__precinct_cico_import',
    'filename':state_specific.VOTER_FILE_LOCATION,
    'columns':{
        'electoral_district_id_long':{'function':tsd.td.reformat.ed_concat,'columns':(31,),'defaults':{'type':'township'}},
        'precinct_id_long':{'function':tsd.td.reformat.concat_us,'columns':(22,29,28)},
        },
    })

CITY_COUNCIL__PRECINCT_ACTUAL = dict(tsd.td.DEFAULT_ACTUAL_TABLE)
CITY_COUNCIL__PRECINCT_ACTUAL.update({
    'schema_table':'electoral_district__precinct',
    'import_table':CITY_COUNCIL__PRECINCT_IMPORT,
    'long_fields':({'long':'electoral_district_id_long','real':'electoral_district_id'},{'long':'precinct_id_long','real':'precinct_id'},),
    'distinct_on':('precinct_id_long','electoral_district_id_long',),
    'long_to':(
        {
            'to_table':'electoral_district_cico_import',
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
        tsd.SCHOOL_DISTRICT_ACTUAL,
        tsd.COUNTY_COUNCIL_ACTUAL,
        tsd.COUNTY_ACTUAL,
        tsd.STATE_ACTUAL,
        CITY_COUNCIL_ACTUAL,
        SUPREME_COURT_ACTUAL,
        tsd.STATE_SENATE_DISTRICT_ACTUAL,
        tsd.CONGRESSIONAL_DISTRICT__PRECINCT_ACTUAL,
        tsd.STATE_REP_DISTRICT__PRECINCT_ACTUAL,
        tsd.JUDICIAL_DISTRICT__PRECINCT_ACTUAL,
        tsd.SCHOOL_DISTRICT__PRECINCT_ACTUAL,
        tsd.COUNTY_COUNCIL__PRECINCT_ACTUAL,
        tsd.COUNTY__PRECINCT_ACTUAL,
        tsd.STATE_SENATE_DISTRICT__PRECINCT_ACTUAL,
        tsd.STATE__PRECINCT_ACTUAL,
        CITY_COUNCIL__PRECINCT_ACTUAL,
        cd.CANDIDATE_ACTUAL,
        cd.CONTEST_ACTUAL,
        cd.CANDIDATE_IN_CONTEST_ACTUAL,
        )

GROUPS = {
        #        'vf_group':TABLE_GROUP,
        }

ELECTORAL_DISTRICT_UNION = {
        'name':'electoral_district_import',
        'components':(
            'electoral_district_cd_import',
            'electoral_district_jd_import',
            'electoral_district_schd_import',
            'electoral_district_srd_import',
            'electoral_district_ssd_import',
            'electoral_district_cc_import',
            'electoral_district_c_import',
            'electoral_district_s_import',
            'electoral_district_cico_import',
            'electoral_district_special_1_import',
            )
        }
UNIONS = (
        ELECTORAL_DISTRICT_UNION,
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
        'school_district':tsd.SCHOOL_DISTRICT_IMPORT,
        'county_council':tsd.COUNTY_COUNCIL_IMPORT,
        'county':tsd.COUNTY_IMPORT,
        'state':tsd.STATE_IMPORT,
        'city_council':CITY_COUNCIL_IMPORT,
        'state_senate_district':tsd.STATE_SENATE_DISTRICT_IMPORT,
        'special_1_judicial_district':SUPREME_COURT_IMPORT,
        'congressional_district__precinct':tsd.CONGRESSIONAL_DISTRICT__PRECINCT_IMPORT,
        'state_rep_district__precinct':tsd.STATE_REP_DISTRICT__PRECINCT_IMPORT,
        'state_senate_district__precinct':tsd.STATE_SENATE_DISTRICT__PRECINCT_IMPORT,
        'judicial_district__precinct':tsd.JUDICIAL_DISTRICT__PRECINCT_IMPORT,
        'school_district__precinct':tsd.SCHOOL_DISTRICT__PRECINCT_IMPORT,
        'county_council__precinct':tsd.COUNTY_COUNCIL__PRECINCT_IMPORT,
        'county__precinct':tsd.COUNTY__PRECINCT_IMPORT,
        'state__precinct':tsd.STATE__PRECINCT_IMPORT,
        'city_council__precinct':CITY_COUNCIL__PRECINCT_IMPORT,
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
            {'tables':('precinct','locality','congressional_district','state_rep_district','state_senate_district','judicial_district','school_district','county_council','county','state','city_council','congressional_district__precinct','state_rep_district__precinct','state_senate_district__precinct','judicial_district__precinct','school_district__precinct','county_council__precinct','county__precinct','state__precinct','city_council__precinct','special_1_judicial_district'),'keys':{}},
            )
        })

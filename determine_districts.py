import sys
import csv
import os
import imp
from collections import defaultdict, namedtuple
import time
state = sys.argv[1].lower()
state_conf = os.path.join(*['data','voterfiles',state,'state_conf.py'])
state_conf = imp.load_source('state_conf', state_conf)
from state_conf import *
vf_districts = dict([(k,v-1) for k,v in VOTER_FILE['columns'].iteritems() if k in VOTER_FILE_DISTRICTS])
precincts = defaultdict(lambda:dict((k,defaultdict(lambda:0)) for k in vf_districts.keys()))
district_entries = defaultdict(lambda:set())
vf_precincts = (
        ('county_number',VOTER_FILE['columns']['county_number']-1),
        #('county_id',VOTER_FILE['columns']['county_id']-1),
        #('residential_city',VOTER_FILE['columns']['residential_city']-1),
        #('township', VOTER_FILE['columns']['township']-1),
        ('precinct_code',VOTER_FILE['columns']['precinct_code']-1),
        ('precinct_name',VOTER_FILE['columns']['precinct_name']-1))
with open(VOTER_FILE_LOCATION,'r') as f:
    csvr = csv.reader(f, delimiter=VOTER_FILE['field_sep'])
    csvr.next()
    x = 1
    t = time.time()
    for line in csvr:
        precinct_code = tuple(line[i] for n,i in vf_precincts)
        for k,v in vf_districts.iteritems():
            precincts[precinct_code][k][line[v]] += 1
            district_entries[k].add(line[v])
        if x % 100000 == 0:
            print len(precincts)
            print sys.getsizeof(district_entries)
            print sys.getsizeof(precincts)
            print "{count}, {time}".format(count=x, time=time.time() - t)
            t = time.time()
        x+=1
with open('precincts','w') as f, open('districts','w') as g:
    print len(precincts)
    num_undet = defaultdict(lambda:0)
    for k,v in precincts.iteritems():
            if any([len(l) > 1 for l in v.values()]):
                f.write("{precinct} HAS UNDETERMINED: {districts}\t".format(precinct=k, districts=','.join(l for l in v.keys() if len(v[l]) > 1)))
                for l,m in v.iteritems():
                    if len(m) > 1:
                        num_undet[l] += 1
                        f.write("POSSIBLE {district} VALUES: {values}\t".format(district=l, values=[(k,v) for k,v in m.iteritems()]))
                f.write('\n')
    for k,v in num_undet.iteritems():
        print "NUM PRECINCTS WITH UNDETERMINED {district}: {num}".format(district=k, num=v)
    for k,v in district_entries.iteritems():
        g.write("{district} takes values: {values}\n".format(district=k, values=','.join(v)))

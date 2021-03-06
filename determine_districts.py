import sys, csv, os, imp, time, subprocess
from collections import defaultdict

def main(state, remove = False):
    minim = 20
    maxim = 34
    shift = minim - 2
    default_state_stuff = os.path.join(*['data','default_state_stuff.py'])
    default_state_stuff = imp.load_source('default_state_stuff', default_state_stuff)
    state_conf = os.path.join(*['data','voterfiles',state,'state_conf.py'])
    state_conf = imp.load_source('state_conf', state_conf)
    vf_districts = dict([(k,v-1 - shift) for k,v in default_state_stuff.VOTER_FILE['columns'].iteritems() if k in state_conf.VOTER_FILE_DISTRICTS])
    district_entries = defaultdict(lambda:set())
    district_lists = defaultdict(lambda:[])
    vf_precincts = (
            ('county_number',default_state_stuff.VOTER_FILE['columns']['county_number']-1 - shift),
            #('county_id',VOTER_FILE['columns']['county_id']-1),
            #('residential_city',VOTER_FILE['columns']['residential_city']-1),
            #('township', VOTER_FILE['columns']['township']-1),
            #('ward',default_state_stuff.VOTER_FILE['columns']['ward']- 1 - shift),
            ('precinct_code',default_state_stuff.VOTER_FILE['columns']['precinct_code']-1 - shift),
            ('precinct_name',default_state_stuff.VOTER_FILE['columns']['precinct_name']-1 - shift))
    county_idx = default_state_stuff.VOTER_FILE['columns']['county_id']-1 - shift
    sd_idx = default_state_stuff.VOTER_FILE['columns']['school_district']-1 - shift
    jd_idx = default_state_stuff.VOTER_FILE['columns']['judicial_district']-1 - shift
    if not os.path.exists(state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION):
        pipe = subprocess.Popen(['unzip',state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION.replace('.txt','.zip'), '-d', os.path.split(os.path.abspath(state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION))[0]],stdin=subprocess.PIPE)
        pipe.wait()
    t = time.time()
    pipe = subprocess.Popen(['cut','-f','1,{min}-{max}'.format(min=minim,max=maxim),state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION],stdout=subprocess.PIPE)
    cut_location = state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION.replace('.txt','.cut')
    with open(cut_location,'w') as f:
        f.writelines(pipe.stdout)
    print 'cutting time: {t}'.format(t=(time.time() - t))

    with open(cut_location,'r') as f, open(os.path.join(*[state_conf.VOTER_FILE_LOCATION]),'w') as g:
        csvr = csv.reader(f, delimiter=default_state_stuff.VOTER_FILE['field_sep'])
        csvw = csv.writer(g, delimiter=default_state_stuff.VOTER_FILE['field_sep'])
        extra_district_dicts = []
        extra_district_names = []
        if state_conf.__dict__.has_key('EXTRA_DISTRICTS'):
            for k,v in state_conf.EXTRA_DISTRICTS.iteritems():
                extra_district_names.append(k)
                edfile = os.path.join('data','voterfiles',v['filename'])
                edcsv = csv.reader(open(edfile),delimiter='\t')
                edcsv.next()
                extra_district_dicts.append(dict((l[0],l[v['column']-1]) for l in edcsv))
        precincts = defaultdict(lambda:dict((k,defaultdict(lambda:0)) for k in vf_districts.keys() + ['county_school_district','county_judicial_district'] + extra_district_names))
        header = csvr.next() + extra_district_names
        header.pop(0)
        csvw.writerow(header)
        x = 1
        t = time.time()
        time1 = 0
        time2 = 0
        time3 = 0
        precinct_ed = set()
        for line in csvr:
            precinct_code = tuple(line[i] for n,i in vf_precincts)
            peds =[]
            write_flag=False
            for k,v in vf_districts.iteritems():
                val = line[v]
                if val == '':
                    continue
                if k == 'county_council':
                    if val.startswith(line[county_idx]):
                        ed = val
                    else:
                        ed = line[county_idx] + ' ' + val
                    district_entries[k].add(ed)
                else:
                    ed = val
                    district_entries[k].add(ed)
                precincts[precinct_code][k][ed] += 1
                if not write_flag and precincts[precinct_code][k][ed] == 1:
                    precinct_ed.add(precinct_code + (k,ed))
                    write_flag=True
            if state_conf.__dict__.has_key('EXTRA_DISTRICTS'):
                for edd,ed_name,edd_settings in zip(extra_district_dicts,state_conf.EXTRA_DISTRICTS.keys(),state_conf.EXTRA_DISTRICTS.values()):
                    if not edd.has_key(line[0]):
                        line.append('')
                        continue
                    val = edd[line[0]]
                    if val == '':
                        line.append('')
                        continue
                    pre_list = []
                    for pre in edd_settings['prepend']:
                        pre_idx = default_state_stuff.VOTER_FILE['columns'][pre]-1 - shift
                        pre_list.append(line[pre_idx])
                    pre_list.append(val)
                    ed = '_'.join(pre_list)
                    district_entries[ed_name].add(ed)
                    precincts[precinct_code][ed_name][ed] += 1
                    line.append(ed)
                    if not write_flag and precincts[precinct_code][ed_name][ed] == 1:
                        precinct_ed.add(precinct_code + (ed_name,ed))
                        write_flag=True
            if state_conf.COUNTY_SCHOOL_DISTRICT and line[sd_idx] != '':
                ed = line[county_idx]+ ' ' + line[sd_idx]
                district_entries['county_school_district'].add(ed)
                if not write_flag and precincts[precinct_code]['county_school_district'][ed] == 1:
                    precinct_ed.add(precinct_code + ('county_school_district',ed))
                    write_flag=True
            if state_conf.COUNTY_JUDICIAL_DISTRICT and line[jd_idx] != '':
                ed = line[county_idx]+ ' ' + line[jd_idx]
                district_entries['county_judicial_district'].add(ed)
                if not write_flag and precincts[precinct_code]['county_judicial_district'][ed] == 1:
                    precinct_ed.add(precinct_code + ('county_judicial_district',ed))
                    write_flag=True
                #peds.append(precinct_code + (k,ed))
            #if len(precinct_ed.intersection(peds)) < len(peds):
            #    precinct_ed.update(peds)
            #    csvw.writerow(line)
            if write_flag:
                line.pop(0)
                csvw.writerow(line)
            if x % 100000 == 0:
                print "{state}, {count}, {time}".format(state=state,count=x, time=time.time() - t)
                #print "time1: {0}, time2: {1}, time3: {2}".format(time1,time2,time3)
                time1 = 0
                time2 = 0
                time3 = 0
                t = time.time()
            x+=1
    with open(os.path.join(*['data','voterfiles',state,'precincts']),'w') as f, open(os.path.join(*['data','voterfiles',state,'districts.py']),'w') as g, open(os.path.join('data','voterfiles',state,'counts.csv'),'w') as h, open(os.path.join('data','voterfiles',state,'names.csv'),'w') as namesfile:
        print "TOTAL PRECINCTS: {precincts}".format(precincts=len(precincts))
        csvh = csv.writer(h)
        csvnames = csv.writer(namesfile)
        csvh.writerow(['precinct','district type','d1','d2','d3','d4','d5','etc'])
        csvnames.writerow(['precinct','district type','d1','d2','d3','d4','d5','etc'])
        num_undet = defaultdict(lambda:0)
        for k,v in precincts.iteritems():
            if any([len(l) > 1 for l in v.values()]):
                f.write("{precinct} HAS UNDETERMINED: {districts}\t".format(precinct=k, districts=','.join(l for l in v.keys() if len(v[l]) > 1)))
                for l,m in v.iteritems():
                    if len(m) > 1:
                        num_undet[l] += 1
                        f.write("POSSIBLE {district} VALUES: {values}\t".format(district=l, values=[(distk,distv) for distk,distv in m.iteritems()]))
                        distnames = []
                        distcounts = []
                        for distk,distv in m.iteritems():
                            distnames.append(distk)
                            distcounts.append(str(distv))
                        csvh.writerow([k,l] + distcounts)
                        csvnames.writerow([k,l] + distnames)
                f.write('\n')
        for k,v in num_undet.iteritems():
            print "NUM PRECINCTS WITH UNDETERMINED {district}: {num}".format(district=k, num=v)
        for k in set(district_entries.keys()).union(set(vf_districts.keys())):
            v = district_entries[k]
            lv = list(v)
            lv.sort()
            g.write("{district} = {values}\n".format(district=k, values=lv))
    if remove:
        pipe = subprocess.Popen(['rm',state_conf.UNCOMPRESSED_VOTER_FILE_LOCATION],stdin=subprocess.PIPE)
        pipe.wait()
    pipe = subprocess.Popen(['rm',cut_location],stdin=subprocess.PIPE)
    pipe.wait()

if __name__=='__main__':
    state = sys.argv[1].lower()
    main(state)

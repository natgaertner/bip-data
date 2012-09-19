from ersatzpg import ersatz
from schema import process_schema, table_tools, create_partitions, create_precinct_to_ed
import determine_districts
from state_abbr import states
import time, sys, imp, os, random, csv
from multiprocessing import Pool
from collections import defaultdict

do_all = ['-clean','-partition','-clean_import','-build','-distinct','-unions','-rekey','-export']
do_all_no_clean =['-clean_import','-build','-distinct','-unions','-rekey','-export']
if '-thread' in sys.argv:
    pool = Pool(processes=4)

if '-all' in sys.argv:
    sys.argv = sys.argv[:-1] + do_all + [sys.argv[-1]]

if '-all_no_clean' in sys.argv:
    sys.argv = sys.argv[:-1] + do_all_no_clean + [sys.argv[-1]]

state_ins = sys.argv[-1].lower()
rep_state = random.sample(state_ins.split(','),1)[0]
print rep_state
rep_state_conf = os.path.join(*['data','voterfiles',rep_state,'state_conf.py'])
rep_state_conf = imp.load_source('rep_state_conf', rep_state_conf)
tables, enums, fks, seqs = process_schema.rip_schema('schema/bip_model_cleaned.sql')
table_tools.define_long_tables(tables, fks)

if '-clean' in sys.argv:
    t =time.time()
    connection = ersatz.db_connect(rep_state_conf.ERSATZPG_CONFIG)
    table_tools.delete_tables(tables, connection)
    table_tools.create_tables(tables, connection)
    table_tools.delete_import_tables(rep_state_conf.ACTUAL_TABLES, rep_state_conf.UNIONS, connection)
    table_tools.create_import_tables(rep_state_conf.ACTUAL_TABLES, tables, connection)
    connection.commit()
    connection.close()
    t = time.time() - t
    print "Elapsed: %s" % (t,)
if '-partition' in sys.argv:
    from collections import OrderedDict
    t =time.time()
    connection = ersatz.db_connect(rep_state_conf.ERSATZPG_CONFIG)
    #connection.cursor().execute('DROP TABLE IF EXISTS voter_file CASCADE;')
    #connection.cursor().execute(open(state_conf.VOTER_FILE_SCHEMA,'r').read())
    finished_schema_tables = []
    for table in rep_state_conf.ACTUAL_TABLES:
        if table['schema_table'] not in finished_schema_tables:
            finished_schema_tables.append(table['schema_table'])
            od = OrderedDict([('source',table['import_table']['sources']),('election_key',table['import_table']['elections'])])
            create_partitions.create_discrete_partitions([table['schema_table']], od, connection.cursor())
            connection.commit()
                #create_partitions.create_discrete_partitions([tname for tname in ['precinct','electoral_district','electoral_district__precinct','locality'] if tname in table_subset], {'source':[s+'VF' for s in states],'election_key':['2012']}, connection.cursor())
                #create_partitions.create_discrete_partitions([tname for tname in ['candidate_long','contest_long','candidate_in_contest_long'] if tname in table_subset], {'source':[s+'Candidates' for s in states],'election_key':['2012']}, connection.cursor())
    connection.close()
    t = time.time() - t
    print "Elapsed: %s" % (t,)
for state in state_ins.split(','):
    print "processing {state} out of {states}".format(state=state, states=state_ins)
    state = state.strip()
    state_conf = os.path.join(*['data','voterfiles',state,'state_conf.py'])
    state_conf = imp.load_source('state_conf', state_conf)

    if '-t' in sys.argv:
        table_subset = eval(sys.argv[sys.argv.index('-t') + 1])
        table_subdict = dict([(t, tables[t]) for t in tables.keys() if t in table_subset])
    else:
        table_subdict = tables

    if '-clean_keyed' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.delete_tables(tables, connection)
        table_tools.create_tables(tables, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-compress' in sys.argv:
        t = time.time()
        if '-thread' in sys.argv:
            pool.apply_async(determine_districts.main, [state, '-remove' in sys.argv])
        else:
            determine_districts.main(state, '-remove' in sys.argv)
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-rebuild_districts' in sys.argv:
        t =time.time()
        with open(state_conf.VOTER_FILE_LOCATION,'r') as f, open(os.path.join('data','voterfiles',state_conf.STATE.lower(),'districts.py'),'w') as g:
            csvr = csv.reader(f, delimiter=state_conf.VOTER_FILE['field_sep'])
            csvr.next()
            district_entries = defaultdict(lambda:set())
            vf_districts = dict([(k,v-1) for k,v in state_conf.VOTER_FILE['columns'].iteritems() if k in state_conf.VOTER_FILE_DISTRICTS])
            for line in csvr:
                for k,v in vf_districts.iteritems():
                    if line[v] == '':
                        continue
                    if k == 'county_council':
                        ed = line[state_conf.VOTER_FILE['columns']['county_id']-1] + ' ' + line[v]
                        district_entries[k].add(line[state_conf.VOTER_FILE['columns']['county_id']-1] + ' ' + line[v])
                    else:
                        ed = line[v]
                        district_entries[k].add(line[v])
            for k in vf_districts.keys():
                v = district_entries[k]
                lv = list(v)
                lv.sort()
                g.write("{district} = {values}\n".format(district=k, values=lv))
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-clean_import' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.delete_import_tables(state_conf.ACTUAL_TABLES, state_conf.UNIONS, connection)
        table_tools.create_import_tables(state_conf.ACTUAL_TABLES, tables, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-build' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        #state_conf.ERSATZPG_CONFIG['tables'] = dict([(tname,state_conf.ERSATZPG_CONFIG['tables'][tname]) for tname in state_conf.ERSATZPG_CONFIG['tables'] if tname in table_subset])
        #state_conf.ERSATZPG_CONFIG['parallel_load'] = tuple(p for p in state_conf.ERSATZPG_CONFIG['parallel_load'] if all(tab in table_subset for tab in p['tables']))
        for group_name, group in state_conf.GROUPS.iteritems():
            state_conf.ERSATZPG_CONFIG['tables'].update({group_name:table_tools.create_import_group(group_name, group, tables, connection)})
        ersatz.new_process_copies(state_conf, connection)
        for group_name, group in state_conf.GROUPS.iteritems():
            table_tools.split_group_tables(group_name, group, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-grouptest' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        for group_name, group in state_conf.GROUPS.iteritems():
            table_tools.split_group_tables(group_name, group, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-distinct' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.distinct_imports(state_conf.ACTUAL_TABLES, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-unions' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.create_union_tables(state_conf.ACTUAL_TABLES, tables, state_conf.UNIONS, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-rekey' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.rekey_imports(state_conf.ACTUAL_TABLES, state_conf.UNIONS, tables, connection, ['source','election_key'])
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-j' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        for s in states:
            create_precinct_to_ed.create_joined(s, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-count' in sys.argv:
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        for s in states:
            create_precinct_to_ed.make_counts(s, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-pk' in sys.argv:
        state = sys.argv[-1].lower()
        state_conf = os.path.join(*['data','voterfiles',state,'state_conf.py'])
        state_conf = imp.load_source('state_conf', state_conf)
        t =time.time()
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.pk_tables(table_subdict, connection)
        connection.commit()
        connection.close()
        t = time.time() - t
        print "Elapsed: %s" % (t,)

    if '-export' in sys.argv:
        connection = ersatz.db_connect(state_conf.ERSATZPG_CONFIG)
        table_tools.export_candidate_tables(state, state_conf.ELECTION, os.path.join(*[os.getcwd(),'data','voterfiles',state,'out']), connection)

if '-thread' in sys.argv:
    pool.close()
    pool.join()

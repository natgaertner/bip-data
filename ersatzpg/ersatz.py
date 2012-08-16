﻿from collections import defaultdict
from itertools import izip
from cStringIO import StringIO
import psycopg2.psycopg1 as psycopg
import re, imp, csv, sys, time
from utffile import utffile

def parse_config(config_file):
    with open(config_file, 'r') as cf:
        universal_config_dict = {'reformat_path':None, 'debug': False}
        table_config_dict = defaultdict(lambda: {'copy_every':100000, 'format':'csv','field_sep':',','quotechar':'"'})
        def parse_table_conf(tconf, tdict):
            for l in tconf:
                if l.startswith('#'): continue
                if re.match(r'\}', l):
                    if not tdict.has_key('table') or not tdict.has_key('filename') or not tdict.has_key('columns'):
                        raise Exception('table config must contain table, filename, and columns')
                    return tdict
                m = re.match(r'(\w+)\s*=\s*(.+)', l)
                if m:
                    tdict.update([m.groups()])
            if not tdict.has_key('table') or not tdict.has_key('filename') or not tdict.has_key('columns'):
                raise Exception('table config must contain table, filename, and columns')
            return tdict
        for l in cf:
            if l.startswith('#'): continue
            m = re.match(r'(\w+)\s*\{', l)
            if m:
                table_config_dict[m.groups()[0]] = parse_table_conf(cf, table_config_dict[m.groups()[0]])
            else:
                m = re.match(r'(\w+)\s*=\s*(.+)', l)
                if m:
                    universal_config_dict.update([m.groups()])
    if not universal_config_dict.has_key('user') or not universal_config_dict.has_key('db') or not universal_config_dict.has_key('pw'):
        raise Exception('config must contain user, db, and pw for postgres db')
    return universal_config_dict, table_config_dict

def new_process_config(universal_config):
    universal_config_dict = {'reformat_path':None, 'debug': False, 'use_utf': False, 'testonly': False}
    table_config_dict = defaultdict(lambda: {'copy_every':100000, 'format':'csv','field_sep':',','quotechar':'"'})
    universal_config_dict.update(universal_config)
    for t in universal_config_dict['tables']:
        table_config_dict[t].update(universal_config_dict['tables'][t])
        if not table_config_dict[t].has_key('table') or not table_config_dict[t].has_key('filename') or not table_config_dict[t].has_key('columns'):
            raise Exception('table config must contain table, filename, and columns')
    parallel_config_tuple = universal_config_dict['parallel_load']
    keys = {}
    for p in universal_config_dict['parallel_load']:
        p['tables'] = dict([(k, table_config_dict.pop(k)) for k in p['tables']])
        keys.update(p['keys'])
    return universal_config_dict, table_config_dict, parallel_config_tuple, keys

def db_connect(config):
    connstr = []
    if config.has_key('host'):
        connstr.append("host=%s" % config['host'])
    if config.has_key('port'):
        connstr.append("port=%s" % config['port'])
    if config.has_key('sslmode'):
        connstr.append("sslmode=%s" % config['sslmode'])
    connstr.append("dbname=%s user=%s password=%s" % (config['db'], config['user'], config['pw']))
    return psycopg.connect(' '.join(connstr))

def process_columns(table_conf, default_reformat_path):
    r_path = table_conf['reformat_path'] if table_conf.has_key('reformat_path') else default_reformat_path
    columns = table_conf['columns'].split(',')
    numbered_columns = []
    transformed_columns = []
    for c in columns:
        c = c.strip()
        m = re.match(r'(\w+)\s*:\s*(\d+)', c)
        if m:
            numbered_columns.append((m.groups()[0], int(m.groups()[1]) - 1))
        else:
            m = re.match(r'(\w+(?:\s+\w+)*)\s*:\s*(\w+)\.(\w+)\((\d+(?:\s+\d+)*)\)', c)
            if m:
                transformed_columns.append((re.split(r'\s+', m.groups()[0]), function_lookup(m.groups()[1], m.groups()[2], r_path), [int(x) - 1 for x in re.split(r'\s+', m.groups()[3])]))
    udcs = [tuple(s.strip() for s in t.split(':')) for t in table_conf['udcs'].split(',')] if table_conf.has_key('udcs') else []
    return numbered_columns, transformed_columns, udcs

def new_process_columns(table_conf):
    numbered_columns = []
    transformed_columns = []
    key_columns = []
    columns = table_conf['columns']
    for k,v in columns.iteritems():
        if type(v) == int and type(k) == str:
            numbered_columns.append((k,v-1))
        elif type(v) == dict and v.has_key('function') and (type(k) == str or type(k) == tuple):
            transformed_columns.append(((k,) if type(k) == str else k, v['function'], [i-1 for i in v['columns']]))
        elif type(v) == dict and v.has_key('key'):
            key_columns.append((k,v['key']))
        else:
            raise Exception('Invalid column definition in table %s: key(s):%s value:%s' % (table_conf['table'], str(k), str(v)))

    udcs = [(k,v) for k,v in table_conf['udcs'].iteritems()] if table_conf.has_key('udcs') else []
    return numbered_columns, transformed_columns, udcs, key_columns

def function_lookup(module_name, func_name, reformat_path):
    module = imp.load_module(module_name, *imp.find_module(module_name, reformat_path))
    return module.__dict__[func_name]

def process_data(row, numbered_columns, transformed_columns,udcs, key_values = []):
    return [row[i] for name,i in numbered_columns] + [v for tr in transformed_columns for v in tr[1](*[row[i] for i in tr[2]])] + [i for name, i in udcs] + key_values

def create_keys(used_keys, keys, sources):
    key_values = {}
    for k in used_keys:
        if k == 'locality' and sources[keys[k]] == 331269:
            import pdb; pdb.set_trace()
        key_values[k] = sources[keys[k]]
        sources[keys[k]]+=1
    return key_values

def process_parallel(p_conf, keys, univ_conf, connection):
    numbered_columns, transformed_columns, udcs, key_columns = {},{},{},{}
    table_def = {}
    force_not_null = {}
    sql = {}
    field_sep = {}
    quote_char = {}
    copy_every = {}
    fs = {}
    buf = {}
    csvr = {}
    csvw = {}
    lines = {}
    generators = []
    used_keys = set()
    for table, table_conf in p_conf['tables'].iteritems():
        numbered_columns[table], transformed_columns[table], udcs[table], key_columns[table] = new_process_columns(table_conf)
        used_keys.update((v for (k,v) in key_columns[table]))
        table_def[table] = "%s(%s)" % (table_conf['table'],','.join([name for name, i in numbered_columns[table]]+[n for names, f, i in transformed_columns[table] for n in names] + [name for name, t in udcs[table]] + [name for name, t in key_columns[table]]))
        force_not_null[table] = 'FORCE NOT NULL ' + ','.join(s.strip() for s in table_conf['force_not_null']) if table_conf.has_key('force_not_null') else ''
        sql[table] = "COPY %s from STDOUT WITH CSV %s" % (table_def[table], force_not_null[table])
        field_sep[table] = table_conf['field_sep']
        quote_char[table] = table_conf['quotechar']
        copy_every[table] = int(table_conf['copy_every'])
    cursor = connection.cursor()
    try:
        for table, table_conf in p_conf['tables'].iteritems():
            if not fs.has_key(table_conf['filename']):
                fs[table_conf['filename']] = utffile(table_conf, 'rb') if univ_conf['use_utf'] else open(table_conf['filename'],'rb')
            buf[table] = StringIO()
            if not csvr.has_key(table_conf['filename']):
                csvr[table_conf['filename']] = csv.reader(fs[table_conf['filename']], quotechar=quote_char[table], delimiter=field_sep[table])
                if table_conf.has_key('skip_head_lines'):
                    shl = int(table_conf['skip_head_lines'])
                    for i in range(shl):
                        csvr[table_conf['filename']].next()
                generators.append(((table_conf['filename'],l) for l in csvr[table_conf['filename']]))
            csvw[table] = csv.writer(buf[table])

        x = 0
        ptime = dict([(t,0) for t in p_conf['tables']])
        ctime = 0
        for lines in izip(*generators):
            lines = dict(lines)
            key_values = create_keys(used_keys, keys, univ_conf['key_sources'])
            x+=1
            for table, table_conf in p_conf['tables'].iteritems():
                ptime[table] -= time.time()
                l = lines[table_conf['filename']]
                try:
                    if table == 'locality' and key_values['locality'] == 331269:
                        import pdb; pdb.set_trace()
                    csvw[table].writerow(process_data(l, numbered_columns[table], transformed_columns[table], udcs[table], [key_values[k] for n,k in key_columns[table]]))
                except Exception, error:
                    if univ_conf['debug']:
                        import pdb; pdb.set_trace()
                    else:
                        raise error
                ptime[table] += time.time()
                if x % copy_every[table] == 0:
                    print "Copying {num} lines in table {table}".format(num=copy_every[table],table=table)
                    buf[table].seek(0)
                    try:
                        ctime -= time.time()
                        cursor.copy_expert(sql[table], buf[table])
                        ctime += time.time()
                    except Exception, error:
                        if univ_conf['debug']:
                            import pdb; pdb.set_trace()
                        else:
                            raise error
                    buf[table].close()
                    buf[table] = StringIO()
                    csvw[table] = csv.writer(buf[table])
                    print "Time spent on building buffer: %s" % ptime[table]
                    print "Time spent copying table {table}: {num}".format(table=table, num=ctime)
                    ctime = 0
                    ptime[table] = 0
        for t in buf:
            buf[t].seek(0)
            print "Copying {num} lines in table {table}".format(num=(x % copy_every[t]), table=t)
            try:
                ctime -= time.time()
                cursor.copy_expert(sql[t], buf[t])
                ctime += time.time()
            except Exception, error:
                if univ_conf['debug']:
                    import pdb; pdb.set_trace()
                else:
                    raise error
            buf[t].close()
            print "Time spent on building buffer: %s" % ptime[t]
            print "Time spent copying: %s" % ctime
            ctime = 0
    finally:
        for f in fs.values():
            f.close()

def process_table(table_conf, univ_conf, connection):
    numbered_columns, transformed_columns, udcs, keys = new_process_columns(table_conf)
    table_def = "%s(%s)" % (table_conf['table'],','.join([name for name, i in numbered_columns]+[n for names, f, i in transformed_columns for n in names] + [name for name, t in udcs]))
    force_not_null = 'FORCE NOT NULL ' + ','.join(s.strip() for s in table_conf['force_not_null']) if table_conf.has_key('force_not_null') else ''
    sql = "COPY %s from STDOUT WITH CSV %s" % (table_def, force_not_null)
    field_sep = table_conf['field_sep']
    quote_char = table_conf['quotechar']
    copy_every = int(table_conf['copy_every'])
    cursor = connection.cursor()
    with utffile(table_conf['filename'],'rb') if univ_conf['use_utf'] else open(table_conf['filename'], 'rb') as f:
        buf = StringIO()
        csvr = csv.reader(f, quotechar=quote_char, delimiter=field_sep)
        csvw = csv.writer(buf)
        if table_conf.has_key('skip_head_lines'):
            shl = int(table_conf['skip_head_lines'])
            for i in range(shl):
                csvr.next()
        x = 0
        ptime = 0
        ctime = 0
        for l  in csvr:
            ptime -= time.time()
            try:
                csvw.writerow(process_data(l, numbered_columns, transformed_columns, udcs))
            except Exception, error:
                if univ_conf['debug']:
                    import pdb; pdb.set_trace()
                else:
                    raise error
            ptime += time.time()
            x+=1
            if x % copy_every == 0:
                print "Copying %s lines" % copy_every
                buf.seek(0)
                try:
                    ctime -= time.time()
                    cursor.copy_expert(sql, buf)
                    ctime += time.time()
                except Exception, error:
                    if univ_conf['debug']:
                        import pdb; pdb.set_trace()
                    else:
                        raise error
                buf.close()
                print "Time spent on building buffer: %s" % ptime
                print "Time spent copying: %s" % ctime
                ptime = 0
                ctime = 0
                buf = StringIO()
                csvw = csv.writer(buf)
        buf.seek(0)
        print "Copying %s lines" % (x % copy_every)
        try:
            ctime -= time.time()
            cursor.copy_expert(sql, buf)
            ctime += time.time()
        except Exception, error:
            if univ_conf['debug']:
                import pdb; pdb.set_trace()
            else:
                raise error
        buf.close()
        print "Time spent on building buffer: %s" % ptime
        print "Time spent copying: %s" % ctime

def new_process_copies(config_module, connection=None):
    universal_conf, table_confs, parallel_confs, keys = new_process_config(config_module.ERSATZPG_CONFIG)
    local_connection = False
    if not connection:
        local_connection = True
        connection = db_connect(universal_conf)
    try:
        for table in table_confs:
            print "Processing table {table}".format(table=table)
            process_table(table_confs[table], universal_conf, connection)
        for p_dict in parallel_confs:
            print "Processing tables {tables} in parallel".format(tables=', '.join(p_dict['tables']))
            process_parallel(p_dict, keys, universal_conf, connection)
    except Exception, error:
        if universal_conf['debug']:
            import traceback; print traceback.format_exc()
            import pdb; pdb.set_trace()
        else:
            raise error
    finally:
        if universal_conf['testonly']:
            if local_connection:
                connection.rollback()
        else:
            connection.commit()
        if local_connection:
            connection.close()

def process_copies(config_file):
    universal_conf, table_confs = parse_config(config_file)
    connection = db_connect(universal_conf)
    for table in table_confs:
        process_table(table_confs[table], universal_conf, connection)
if __name__ == "__main__":
    new_process_copies(imp.load_source('config',sys.argv[1]))

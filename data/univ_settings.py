import imp
ELECTION = '2012'
table_functions = imp.load_module('reformat', *imp.find_module('reformat', ['data']))
DATABASE_CONFIG = {
        'user':'postgres',
        'db':'bip3',
        'pw':'|-|3lp3rb34r'
        }
ERSATZPG_CONFIG = {
        'debug':True
        }
ERSATZPG_CONFIG.update(DATABASE_CONFIG)


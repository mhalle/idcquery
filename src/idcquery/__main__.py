import sys
import json
from os import getenv
from google.cloud import bigquery
from google.oauth2 import service_account
from idcquery import load, load_from_url, run_query
import argparse

if __name__ == '__main__':

    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print(f'usage: idcquery [args] <file or url>', file=sys.stderr)
        sys.exit(1)

    credfile = getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credfile:
        print(f'idcquery: GOOGLE_APPLICATION_CREDENTIALS environment variable must be set', 
              file=sys.stderr)
        sys.exit(1)

    credentials = service_account.Credentials.from_service_account_file(credfile)

    client = bigquery.Client(credentials=credentials)
    src = sys.argv[1]
    if src.startswith('http'):
        queryinfo = load_from_url(src)
    else:
        with open(src) as fp:
            queryinfo = load(fp)

    try:
        query_parameter_info = queryinfo['queryParameters']
    except KeyError:
        query_parameter_info = []
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('querysrc', help="file or url of query description")
    argparser.add_argument('--dry_run', 
                           action='store_true',
                           help='do not execute query, just check its syntax')
    for q in query_parameter_info:
        if 'type' in q:
            argparser.add_argument('--' + q['name'],
                                   default = q.get('defaultValue', None),
                                   help = q.get('description', None))
        elif 'arrayType' in q:
            argparser.add_argument('--' + q['name'], 
                                   default = q.get('defaultValue', None),
                                   help = q.get('description', None),
                                   nargs='*')
            
    args = argparser.parse_args()

    q = run_query(queryinfo, client, 
                  parameter_values = vars(args), 
                  job_config_args={ 'dry_run': args.dry_run })
    for row in q:
        print(json.dumps(dict(row), default=str))


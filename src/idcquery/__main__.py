import sys
import json
from google.cloud import bigquery
from google.oauth2 import service_account
from idcquery import load, load_from_url
import argparse
import click


@click.group()
def cli():
    pass

@cli.command()
@click.argument('querysrc')
@click.option('-c', '--credentialfile', 
    envvar='GOOGLE_APPLICATION_CREDENTIALS',
    required=True)

@click.option('--dry-run', is_flag=True, default=False)
@click.option('-p', '--parameter', type=(str, str), multiple=True)
def runquery(querysrc, credentialfile, dry_run, parameter):    
    queryinfo = loadq(querysrc)

    credentials = service_account.Credentials.from_service_account_file(credentialfile)
    client = bigquery.Client(credentials=credentials)

    parameter_values = {param[0]: param[1] for param in parameter}

    job_config_args={ 'dry_run': dry_run }
    q = queryinfo.run_query(client, parameter_values, job_config_args)
    for row in q:
        print(json.dumps(dict(row), default=str))


@cli.command('print')
@click.argument('querysrc')
@click.option('--format', type=click.Choice(['text', 'markdown']), default='text')
def print_(querysrc, format): 
    queryinfo = loadq(querysrc)
    if format == 'text':
        print(queryinfo.to_text())
    elif format == 'markdown':
        print(queryinfo.to_markdown())
    return 0
   
        
def loadq(querysrc):
    if querysrc.startswith('http'):
        queryinfo = load_from_url(querysrc)
    else:
        with open(querysrc) as fp:
            queryinfo = load(fp)
    return queryinfo


'''

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

    for p in parameter:
    

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

    q = queryinfo.run_query(client, 
                  parameter_values = vars(args), 
                  job_config_args={ 'dry_run': args.dry_run })
    for row in q:
        print(json.dumps(dict(row), default=str))

'''

if __name__ == '__main__':
        cli()

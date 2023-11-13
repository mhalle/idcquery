import sys
import json
from google.cloud import bigquery
import google.api_core
from google.oauth2 import service_account
from idcquery import load, load_from_url
import click
import jsonschema

@click.group()
def cli():
    pass

# -------------   runquery  ----------------- #

@cli.command()
@click.argument('querysrc')
@click.option('-c', '--credentialfile', envvar='GOOGLE_APPLICATION_CREDENTIALS',
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


# -------------   validate ----------------- #
@cli.command()
@click.argument('querysrc', nargs=-1)
@click.option('-c', '--credentialfile', envvar='GOOGLE_APPLICATION_CREDENTIALS', default=None)
@click.option('-q', '--quiet', is_flag=True, default=False, 
              help="don't print output, only set return value")
@click.option('-k', '--keep-going', is_flag=True, default=False, 
              help="keep going after first error")
@click.option('-e', '--errors-only', is_flag=True, default=False, 
              help="print only errors and not successes")
@click.option('--format-only', is_flag=True, default=False,
              help="only validate the description format")
def validate(querysrc, credentialfile, quiet, keep_going, 
                errors_only, format_only):
    """validate a list of query descriptions by verifying the format and then
        verifying the query syntax by performing a bigquery dry run"""

    do_format = True
    do_query = not format_only

    if do_query:
        if not credentialfile:
            print("credential file missing", file=sys.stderr)
            sys.exit(1)

        credentials = service_account.Credentials.from_service_account_file(credentialfile)
        client = bigquery.Client(credentials=credentials)

    ret_val = 0
    for q in querysrc:
        queryinfo = loadq(q)

        this_format_valid = True
        if do_format:
            try:
                queryinfo.validate_format()
                if not quiet and not errors_only:
                    print(f'{q}: format: no formatting errors')
            except jsonschema.exceptions.ValidationError as e:
                this_format_valid = False
                if not quiet:
                    print(f'{q}: format: {e.message}')
                ret_val = 1
                if not keep_going:
                    sys.exit(1)

        if do_query and this_format_valid:
            parameter_values = []
            job_config_args={ 'dry_run': True }
            try:
                queryinfo.run_query(client, parameter_values, job_config_args)
                if not quiet and not errors_only:
                    print(f'{q}: no query errors')
            except google.api_core.exceptions.BadRequest as e:
                for ee in e.errors:
                    if not quiet:
                        print(f'{q}: {ee["reason"]}: {ee["message"]}')
                ret_val = 1
                if not keep_going:
                    sys.exit(ret_val)

    sys.exit(ret_val)

# -------------   print  ----------------- #
@cli.command('print')
@click.argument('querysrc', nargs=-1)
@click.option('--format', type=click.Choice(['text', 'markdown']), default='text')
@click.option('--include-src', is_flag=True, default=False)
def print_(querysrc, format, include_src): 
    """Print documentation for a list of queries in text or markdown format"""
    for q in querysrc:
        if include_src:
            print(q)
        name = q.split('/')[-1].split('.')[0]
        queryinfo = loadq(q)
        if format == 'text':
            print(queryinfo.to_text(default_title=name))
        elif format == 'markdown':
            print(queryinfo.to_markdown(default_title=name))
        if len(querysrc) > 0:
            if format == 'markdown':
                print('-------------') # two lines
            print('-------------')
    return 0

def loadq(querysrc):
    if querysrc.startswith('http'):
        queryinfo = load_from_url(querysrc)
    else:
        with open(querysrc) as fp:
            queryinfo = load(fp)
    return queryinfo


if __name__ == '__main__':
        cli()

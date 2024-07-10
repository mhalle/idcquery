import sys
import json
from google.cloud import bigquery
import google.api_core
from google.oauth2 import service_account
from idcquery import load, load_from_url, get_yaml_error_text, interpret_template
import click
import jsonschema
import yaml
from .markdown_utils import  concatenate_markdown_with_toc, concatenate_markdown_multi, get_path_component
import os.path

@click.group()
def cli():
    pass


# -------------  tojson -------------------  #

@cli.command()
@click.argument('querysrc', nargs=-1)
def tojson(querysrc):
    """Output query description as json """
    for q in querysrc:
        queryinfo = loadq(q)
        print(json.dumps(queryinfo.queryinfo))

# -------------  getquery -------------------  #

@cli.command()
@click.argument('querysrc')
def getquery(querysrc):
    """Output a query as plain text. """
    queryinfo = loadq(querysrc)
    print(queryinfo.get_query())

# -------------- create ---------------------- #
    
@cli.command()
@click.option('--title')
@click.option('--summary')
@click.option('--description')
@click.option('--queryfile')
@click.option('--identifier')
@click.option('--all', is_flag=True, default=False, 
              help="include all fields, with unused ones commented out")
def create(title, summary, description, queryfile, identifier, all):
    """Create an empty query. Fields may be specified on command line. """

    data = {}
    data['all'] = all
    if not title is None:
        data['title'] = title
    if not summary is None:
        data['summary'] = summary
    if not description is None:
        data['description'] = description
    if not identifier is None:
        data['identifier'] = identifier
    if queryfile:
        data['query'] = open(queryfile).read()
    else:
        data['query'] = ''

    print(interpret_template('empty_template.jinja2', data).replace('\n\n', '\n'))

    
    
# -------------   runquery  ----------------- #

@cli.command()
@click.argument('querysrc')
@click.option('-c', '--credentialfile', envvar='GOOGLE_APPLICATION_CREDENTIALS',
    required=True)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('-p', '--parameter', type=(str, str), multiple=True)
def runquery(querysrc, credentialfile, dry_run, parameter):
    """Run a BigQuery query from a query description."""    
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

    do_query = not format_only

    if do_query:
        if not credentialfile:
            print("credential file missing", file=sys.stderr)
            sys.exit(1)

        credentials = service_account.Credentials.from_service_account_file(credentialfile)
        client = bigquery.Client(credentials=credentials)

    ret_val = 0
    for q in querysrc:
        try:
            queryinfo = loadq(q)
        except (yaml.scanner.ScannerError, yaml.YAMLError) as e:
            ret_val = 1
            this_format_valid = False
            if not quiet:
                print(f'{q}: read: {get_yaml_error_text(e)}')
            if not keep_going:
                break
            continue

        try:
            queryinfo.validate_format()
            if not quiet and not errors_only:
                print(f'{q}: format: no formatting errors')
        except jsonschema.exceptions.ValidationError as e:
            ret_val = 1
            if not quiet:
                print(f'{q}: format: {e.message}')
            if not keep_going:
                break
            continue

        if do_query:
            try:
                queryinfo.run_query(client, dry_run=True)
                if not quiet and not errors_only:
                    print(f'{q}: no query errors')
            except google.api_core.exceptions.BadRequest as e:
                ret_val = 1
                for ee in e.errors:
                    if not quiet:
                        print(f'{q}: {ee["reason"]}: {ee["message"]}')
                if not keep_going:
                    break

    sys.exit(ret_val)

# -------------   format  ----------------- #
@cli.command('format')
@click.argument('querysrc', nargs=-1)
@click.option('--format', type=click.Choice(['text', 'markdown']), default='text')
@click.option('--include-src', is_flag=True, default=False)
@click.option('--strip-src-path', is_flag=True, default=False)
@click.option('--include-toc', is_flag=True, default=False)
@click.option('--document-title', default=None)
@click.option('--introduction-file', default=None)
def format(querysrc, format, include_src=False, strip_src_path=False, introduction_file=None, include_toc=True, document_title=None): 
    """Format documentation for a list of queries in text or markdown format"""
    if format == 'markdown':
        if len(querysrc) == 1:
            include_toc = False

        markdown_docs = []
        for q in querysrc:
            name = q.split('/')[-1].split('.')[0]
            src = None
            if include_src:
                src = q
                if strip_src_path:
                    try:
                        src = src.split('/')[-1]
                    except IndexError:
                        pass
            queryinfo = loadq(q)        
            markdown_docs.append(queryinfo.to_markdown(default_title=name, src=src))

        introduction = None
        if introduction_file:
            with open(introduction_file) as fp:
                introduction = fp.read()
        
        print(concatenate_markdown_with_toc(markdown_docs, document_title, introduction, include_toc))
        return 0

    for q in querysrc:
        name = q.split('/')[-1].split('.')[0]
        if include_src:
            pq = q
            if strip_src_path:
                try:
                    pq = pq.split('/')[-1]
                except IndexError:
                    pass
                print(f'{pq}')
                print()
        queryinfo = loadq(q)
        if format == 'text':
            print(queryinfo.to_text(default_title=name))
        elif format == 'markdown':
            print(queryinfo.to_markdown(default_title=name))
        if len(querysrc) > 0:
            print()
    return 0

# -------------   format  ----------------- #
@cli.command('format-multi')
@click.argument('files', nargs=-1)
@click.option('--include-src', is_flag=True, default=False)
@click.option('--strip-src-path', type=int, default=1)
@click.option('--introduction', default=None)

def format_multi(files,
                 include_src=False, 
                 strip_src_path=0, 
                 introduction=None): 
    """Format enhanced documentation for a list of queries in markdown format"""

    intro_info = None
    if introduction: 
        if introduction.endswith('.md'):
            with open(introduction, 'r') as fp:
                intro_info = {
                    'filename': introduction,
                    'content': fp.read(),
                    'type': 'intro'
                }
        else:
            intro_info = {
                'filename': None,
                'content': f'# {introduction}',
                'type': 'intro'
            }

    fileinfo = []
    for file in files:
        if file.endswith('.yaml'):
            if strip_src_path != 0:
                src_text = get_path_component(file, strip_src_path)
            else:
                src_text = None
            name = file.split('/')[-1].split('.')[0]
            queryinfo = loadq(file)
            fileinfo.append({
                'content': queryinfo.to_markdown(default_title=name, src=src_text),
                'filename': file,
                'type': 'query'
            })

        elif file.endswith('.md'):
            with open(file, 'r') as fp:
                fileinfo.append({'content': fp.read(), 'filename': file, 'type': 'group'})

        else: # just a string
            fileinfo.append({'filename': None, 'content': f'# {file}', 'type': 'group'})
    md = concatenate_markdown_multi(fileinfo, 
                                   introduction=intro_info, 
                                   strip_src_path=strip_src_path, include_toc=True)
        
    print(md)
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


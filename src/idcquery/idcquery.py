from yaml import safe_load as yaml_load
import urllib.request
import urllib.parse
import json
from google.cloud import bigquery

"""
    Simple implmentation of a human-authorable IDC bigquery 
    description format reader.

    The query description can be read from a string, file, URL, 
    or public GitHub repository. The description can be written in 
    either YAML or JSON. (In the current implementation of the Python
    client library, the description is parsed using the PyYAML module
    assuming that JSON is a strict subset of YAML.)

    The current implementation uses a simple Python dictionary to
    store the parsed query information. The format schema is also 
    freeform for the initial release. A future version using a 
    formal schema can provide access methods to all data fields as 
    well as methods to create a query description.

    The functions for reading and parsing query descritions include:

    * loads(str): parse a query description from a string

    * load(fp): read and parse description from file

    * load_from_url(url): read and parse description from url

    * load_from_github(user, repo, branch, querypath): read and
    parse a query description available on a public GitHub repository.

    The run_query function runs a bigquery query using queryinfo,
    a bigquery client object created externally, and optional 
    information about query and job parameters. Query parameters should
    be named using the BigQuery SQL  "@param" syntax and specified as 
    "queryParameters" in the query description.

    * run_query(queryinfo, client, parameter_values={}, job_config_args={})
"""

def loads(querytext):
    """Parse a string containing a queryinfo description. 
    Currently, the parser just loads the query using a YAML
    parser, but may do more format-specific parsing in the future."""
    return yaml_load(querytext)

def load(fp):
    """Read a queryinfo description from a file object"""
    # PyYAML supports files
    return yaml_load(fp)

def load_from_url(url):
    """Read a queryinfo description from a URL and return a
    parsed version. The URL will first be tried as specified, if
    that fails, a ".yaml" extension will be added. The extensions
    ".query.yaml", ".json", and ".query.json" will be tried in order."""

    urls_to_try = [
        url, 
        url + '.yaml', 
        url + '.query.yaml',
        url + '.json', 
        url + '.query.json'
    ]
    for u in urls_to_try:
        try:
            with urllib.request.urlopen(u) as fp:
                return yaml_load(fp)
        except urllib.error.HTTPError:
            continue
    return None

# https://raw.githubusercontent.com/mhalle/idc-queries/main/anisotopic_pixel_not_square.query.yaml
def load_from_github(user, repo, branch, querypath):
    """Read a queryinfo description from github using HTTPS. The
     query is specified by the GitHub user, repo, branch, and path."""
    base = 'https://raw.githubusercontent.com'

    u = urllib.parse.quote(user)
    r = urllib.parse.quote(repo)
    b = urllib.parse.quote(branch)
    q = urllib.parse.quote(querypath)
    github_url = f'{base}/{u}/{r}/{b}/{q}'
    return load_from_url(github_url)

def run_query(queryinfo, client, parameter_values = {}, job_config_args = {}):
    """Runs a bigquery query given a parsed queryinfo description, 
    a bigquery client, an optional dictionary of query parameter values, and
    an optional dictionary of query job configuration args."""

    query = queryinfo['query']
    try:
        params = queryinfo['queryParameters']
    except KeyError:
        params = None
    query_parameters = []
    if params:
        for p in params:
            pv = parameter_values.get(p['name'], p['defaultValue'])
            qp = None
            if 'type' in p:
                qp = bigquery.ScalarQueryParameter(p['name'], 
                                                p['type'], 
                                                pv)
                query_parameters.append(qp)
            elif 'arrayType' in p:
                pv = parameter_values.get(p['name'], p['defaultValue'])
                if not isinstance(pv, list):
                    pv = json.dumps(pv)

                qp = bigquery.ArrayQueryParameter(p['name'], 
                                                p['arrayType'], 
                                                pv)
                query_parameters.append(qp)
    
    jq = bigquery.QueryJobConfig(query_parameters=query_parameters, 
                                    **job_config_args)
            
    return client.query(query, job_config = jq)


import urllib.request
import urllib.parse
import json
from yaml import safe_load as yaml_load
from google.cloud import bigquery
from jinja2 import Environment, BaseLoader
from .templates import idcquery_markdown_template, idcquery_text_template
import importlib.resources
import jsonschema

SCHEMA_PATH = 'schema/idcquery.schema.json'
SCHEMA_JSON = None
TEMPLATE_ROOT = 'templates'
MODULE_NAME = 'idcquery'

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

class QueryInfo:
    def __init__(self, queryinfodict):
        self.queryinfo = queryinfodict
        self.schema = None

    def get(self, attrname):
        return self.queryinfo.get(attrname)
    
    def __getitem__(self, attrname):
        return self.queryinfo[attrname]

    def get_query(self):
        return self.queryinfo['query']
    
    @classmethod
    def loads(cls, querytext):
        return cls(yaml_load(querytext))

    @classmethod
    def load(cls, fp):
        """Read a queryinfo description from a file object"""
        # PyYAML supports files
        return cls(yaml_load(fp))
    
    @classmethod
    def load_from_url(cls, url):
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
                    return cls(yaml_load(fp))
            except urllib.error.HTTPError:
                continue
        return None

    @classmethod
    def load_from_github(cls, user, repo, querypath, branch='HEAD'):
        """
        Read a queryinfo description from github using HTTPS. The
        query is specified by the GitHub user, repo, path and optionally
        branch. If branch is not specified, the latest commit of the
        default branch is used.
        """
        base = 'https://raw.githubusercontent.com'

        u = urllib.parse.quote(user)
        r = urllib.parse.quote(repo)
        b = urllib.parse.quote(branch) 
        q = urllib.parse.quote(querypath)
        github_url = f'{base}/{u}/{r}/{b}/{q}'
        return cls.load_from_url(github_url)
    

class IDCQueryInfo(QueryInfo):
    def to_markdown(self, template_string=None, default_title=None):
        if not template_string:
            if not hasattr(self, 'idcquery_markdown_template'):
                self.idcquery_markdown_template = read_template('idcquery_markdown_template.jinja2')
            template_string = self.idcquery_markdown_template

        rtemplate = Environment().from_string(template_string)
        if default_title and 'title' not in self.queryinfo:
            render_args = dict.copy(self.queryinfo)
            render_args.update({'title': default_title})        
        else:
            render_args = self.queryinfo
        formatted = rtemplate.render(**render_args).replace('\n\n', '\n')
        return formatted
        
    def to_text(self, template_string=None, default_title=None):
        if not template_string:
            if not hasattr(self, 'idcquery_text_template'):
                self.idcquery_text_template = read_template('idcquery_text_template.jinja2')
            template_string = self.idcquery_text_template

        rtemplate = Environment().from_string(template_string)
        if default_title and 'title' not in self.queryinfo:
            render_args = dict.copy(self.queryinfo)
            render_args.update({'title': default_title})
        else:
            render_args = self.queryinfo
        formatted = rtemplate.render(**render_args)
        return formatted
    
    def run_query(self, client, parameter_values = {}, job_config_args = {}, dry_run=False):
        """Runs a bigquery query given a parsed queryinfo description, 
        a bigquery client, an optional dictionary of query parameter values, and
        an optional dictionary of query job configuration args. If the flag
        dry_run is True, then a dry run of the query will be made to check its
        syntax."""

        queryinfo = self.queryinfo
        query = queryinfo['query']

        try:
            params = queryinfo['queryParameters']
        except KeyError:
            params = None

        if dry_run:
            job_config_args = job_config_args.copy()
            job_config_args['dry_run'] = True

        query_parameters = []
        if params:
            for p in params:
                pv = parameter_values.get(p['name'], p.get('defaultValue', None))
                qp = None
                if 'type' in p:
                    qp = bigquery.ScalarQueryParameter(p['name'], 
                                                    p['type'], 
                                                    pv)
                    query_parameters.append(qp)
                elif 'arrayType' in p:
                    pv = parameter_values.get(p['name'], p('defaultValue', None))
                    if not isinstance(pv, list):
                        pv = json.dumps(pv)

                    qp = bigquery.ArrayQueryParameter(p['name'], 
                                                    p['arrayType'], 
                                                    pv)
                    query_parameters.append(qp)
                else:
                    raise ValueError("type or arrayType must be specified for each queryParameter")
        
        jq = bigquery.QueryJobConfig(query_parameters=query_parameters, 
                                        **job_config_args)
                
        return client.query(query, job_config = jq)
            
    
    def validate_format(self, schema=None):
        """Validate the format of the queryinfo format using JSON schema.
        If no schema is provided, a default schema will be used."""
        
        global SCHEMA_JSON
        if not schema:
            if not SCHEMA_JSON:
                SCHEMA_JSON = read_schema()
            schema = SCHEMA_JSON

        return jsonschema.validate(instance=self.queryinfo, schema=schema)
    

def loads(querytext):
    """Parse a string containing a queryinfo description. 
    Currently, the parser just loads the query using a YAML
    parser, but may do more format-specific parsing in the future."""
    return IDCQueryInfo.loads(querytext)

def load(fp):
    """Read a queryinfo description from a file object"""
    # PyYAML supports files
    return IDCQueryInfo.load(fp)

def load_from_url(url):
    """Read a queryinfo description from a URL and return a
    parsed version. The URL will first be tried as specified, if
    that fails, a ".yaml" extension will be added. The extensions
    ".query.yaml", ".json", and ".query.json" will be tried in order."""
    return IDCQueryInfo.load_from_url(url)

# https://raw.githubusercontent.com/mhalle/idc-queries/main/anisotopic_pixel_not_square.query.yaml
def load_from_github(user, repo, branch, querypath):
    """Read a queryinfo description from github using HTTPS. The
     query is specified by the GitHub user, repo, branch, and path."""
    return IDCQueryInfo.load_from_github(user, repo, branch, querypath)

def get_yaml_error_text(exc):
    """Return formatted text from a YAML parser exception"""
    if exc and hasattr(exc, 'problem_mark'):
        if exc.context != None:
            return f'yaml parse error: {exc.problem_mark}\n{exc.problem} {exc.context}'
        else:
            return f'yaml parse error: {exc.problem_mark}\n{exc.problem}'
    else:
        return f'yaml parse error'

def read_template(template_name):
    return (importlib.resources.files(MODULE_NAME)
                    .joinpath(TEMPLATE_ROOT, template_name)
                    .read_text())

def read_schema():
    return json.loads(
        importlib.resources.files(MODULE_NAME)
            .joinpath(SCHEMA_PATH)
            .read_text())

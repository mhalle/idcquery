
# IDC query description parser for Python

The `idcquery` Python module parses a simple description of an IDC
BigQuery query description written in YAML or JSON. It also provides a command
line program to run queries, validate queries and descriptions, and format 
descriptions in either MarkDown or text format.

See [FORMAT.md](FORMAT.md) for details about the query description format.

This query description format is designed to encourage the reuse of
IDC queries by representing them in a self-describing, self-documenting,
modular, and easy-to-author way.  


## idcquery Python module

```pip install https://github.com/mhalle/idcquery/releases/download/0.3.4/idcquery-0.3.4-py3-none-any.whl```

The `idcquery` Python module provides a simple loader and parser for the IDC query description. It provides the following functions:

* `loads(str)`: parse a query description from a string

* `load(fp)`: read and parse description from file

* `load_from_url(url)`: read and parse description from url

* `load_from_github(user, repo, branch, querypath)`: read and
    parse a query description available on a public GitHub repository.

Each of these functions returns an IDCQueryInfo object that describes the query. 

The `run_query` method of an IDCQueryInfo provides a way to use a 
parsed query description to make to IDC query:

`query_info.run_query(client, parameter_values={}, job_config_args={}, dry_run=False)`: 
The run_query method runs a bigquery query using 
a bigquery client object created externally, and optional 
information about query and job parameters. Query parameters should
be named using the BigQuery SQL  "@param" syntax and specified as 
"queryParameters" in the query description. 

The `job_config_args` are passed directly to the BigQuery query call. 
In particular, adding `"dry_run": True` to the dictionary allows 
the syntax of the query to be validated without actually running a
(potentially long-running and expensive) query. A shortcut is to use
a `True value for the `dry_run` argument to the `run_query` call.

The 


## Running command line queries

The `idcquery` module can be called directly from the command line to
run queries using the `runquery` subcommand:

```python -m idcquery runquery [--dry-run] [-c credentialsfile] [-p parameterName1 value1] ... <query_filename_or_url>```

The module retrieves the query from a file or URL. If the query contains query
parameters, the value of those parameters can be set using command line flags.

The results of the query are returned with each for being respresented in JSON, 
separated by newlines. 

The flag ``--dry-run`` sends the query but does not execute it, allowing it to be 
checked for syntax.

Running a query requires setting up Google authentication using 
a credentials file. The location of the file should be set using the `-c` 
option or the GOOGLE_APPLICATION_CREDENTIALS environment variable.

## Storing query results in an sqlite database

Using the idcquery command line mode, it's easy to save the results of a query
in an sqlite database. Use the `sqlite-utils` package, which can be installed as
follows: 

```pip install sqlite-utils```

Then, do the following:

```python -m idcquery runquery <file-or-url> | sqlite-utils insert output.db tablename - --nl```

## Printing query documentation

The `idcquery print` subcommand can be used to generate formatted information about the query:

```python -m idcquery print --format [text,markdown] <query_filename_or_url> ```

The print subcommand can take a list of queries and will output them all onto stdout. The 
flag `--include-src` will add the location of the query at the top of the output.

## Validating query description

The `idcquery print` subcommand can be used to validate the query:

```python -m idcquery validate [-c credentialsfile] [--format-only] [--errors-only] [--quiet][--keep-going] <query_filename_or_url> ...```

Validation has two steps. First, the query description is validated against a schema for correctness. Then, if it passes, the BigQuery syntax is validated by making a "dry run" query. 

The `--format-only` option can be used to only do the format check. `--errors-only` will not print successful results, only failures. `--keep-going` will continue to test the all documents (the default
is to fail and exit on first error.) `--quiet` will suppress text output; the shell status is 0 if no errors were encountered, 1 otherwise.

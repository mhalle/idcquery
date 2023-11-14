# IDC Query Description Format

This draft document describes the preliminary schema for the IDC query description format.

**All fields except the query are optional. If specified, queryParameters are used to 
build a query to execute it. All other fields are currently for documentation only.**

## Query metadata fields
* title: Title of the query (supports Markdown formatting)
* summary: A short summary of the query (supports Markdown formatting)
* description: A longer textual description of the query and how it it used. (supports Markdown formatting)
* identifier: A permalink, DOI, or other unique identifier for the query
* documentationUrl: A link to additional documentation about the query.
* discussionUrl: A link to a discussion thread about the query.
* funding: A list of funding sources for developing this query.
    - name: Name of grant or other funding
    - sponsor: Sponsor of this work
    - identifier: Unique identifier of this grant
    - homepageUrl: Homepage of grant or sponsorship
* keywords: List of keywords describing this query
* contributors: List of people or groups that contributed to the development of this query
    - name: Name of contributor
    - affiliation: Institutional affiliation of this contributor
    - email: Email address of contributor
    - homepageUrl: Homepage of contributor
    - identifier: Unique identifier associated with this person (e.g., ORCID ID)
* exampleResult: A Markdown-formatted table showing an example of the query result for documentation purposes.
* references: Published references related to the query
    - citation: text citation of the reference (supports Markdown formatting)
    - identifier: unique identifier for this reference
    - url: URL to the reference
* seeAlso: Links to items related to the query
    - description: a textual description of the item (supports Markdown formatting)
    - url: a link to the item

## Query fields
* queryParameters: A list of named parameters used in the querty
    - name: name of the parameter
    - type or arrayType: BigQuery type or arrayType for parameter
    - defaultValue: Default value for parameter, in JSON-parsable form
    - description: test description of parameter
* queryResultColumns: List of columns returned by query for documentation purposes.
    - name: name of column
    - type: type of column value
    - description: description of column
* query: query expressed in BigQuery format. Often expressed as a multi-line string started with a "|" in YAML. YAML multi-line strings should be intented at least one space.
* queryIsCacheable: if true, states that the query always returns the same values for a given set of queryParameters. Such a query is also known as a "pure" function (the same
query and arguments always produce the same results).

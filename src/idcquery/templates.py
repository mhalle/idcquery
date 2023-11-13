idcquery_markdown_template = '''
{%- if title -%}
# {{ title }}
{% endif -%}

{%- if summary %}
## Summary
{{ summary }}
{% endif -%}

{%- if description %}
## Description
{{ description }}
{% endif -%}

{%- if keywords %}
## Keywords
{% for keyword in keywords %}{{ keyword }}{{ ", " if not loop.last else "" }}{% endfor %}
{% endif -%}

{%- if contributors -%}
## Contributors
{% for contributor in contributors %}
- **{{ contributor.name }}**  
{% if contributor.affiliation -%}{{ contributor.affiliation }}{{ '  \n' }}{%- endif -%}
{% if contributor.email -%}{{ contributor.email }}{{ '  \n' }}{%- endif -%}
{% if contributor.homepageUrl -%}{{ contributor.homepageUrl }}{{ '  \n' }}{%- endif -%}
{% if contributor.identifier -%}{{ contributor.identifier }}{{ '  \n' }}{%- endif -%}

{% endfor %}
{% endif -%}

{%- if funding -%}
## Funding
{% for source in funding %}
- **{{ source.name }}**  
{% if source.sponsor -%}{{ source.sponsor }}{{ '  \n' }}{%- endif -%}
{% if source.identifier -%}{{ source.identifier }}{{ '  \n' }}{%- endif -%}
{% if source.homepageUrl -%}{{ source.homepageUrl }}{{ '  \n' }}{%- endif -%}
{% endfor %}
{% endif -%}

{%- if identifier -%}
## Identifier
{{ identifier }}
{% endif -%}
{% if query %}
## Query
```sql
{{ query }}
```
{% endif -%}

{%- if queryParameters %}
### Parameters
{% for parameter in queryParameters %}
- **{{ parameter.name }}**  
{% if parameter.description -%}Description: {{ parameter.description }}{{ '  \n' }}{%- endif -%}
{% if parameter.type -%}Type: {{ parameter.type }}{{ '  \n' }}{%- endif -%}
{% if parameter.arrayType -%}Array type: {{ parameter.arrayType }}{{ '  \n' }}{%- endif -%}
{% if parameter.defaultValue -%} Default value: {{ parameter.defaultValue }}{{ '  \n' }}{%- endif -%}

{% endfor %}
{% endif -%}

{%- if queryResultColumns %}
### Result columns
{% for resultColumn in queryResultColumns %}
- **{{ resultColumn.name}}**  
{% if resultColumn.description -%}Description: {{ resultColumn.description }}{{ '  \n' }}{%- endif -%}
{% if resultColumn.type -%}Type: {{ resultColumn.type }}{{ '  \n' }}{%- endif -%}

{% endfor %}
{% endif -%}

{%- if not queryIsCacheable %}

**Query is cacheable.**
{% else %}
**Query is not cacheable.**

{% endif -%}
'''

idcquery_text_template = '''
{%- if title -%}
{{ title }}
{% endif -%}

{%- if summary %}
Summary: {{ summary }}
{% endif -%}

{%- if description %}
Description: {{ description }}
{% endif -%}

{%- if keywords %}
Keywords: {% for keyword in keywords %}{{ keyword }}{{ ", " if not loop.last else "" }}{% endfor %}
{% endif -%}

{%- if contributors %}
Contributors:
{%- for contributor in contributors %}
{{ contributor.name }}  
{% if contributor.affiliation -%}{{ contributor.affiliation }}{{ '  \n' }}{%- endif -%}
{% if contributor.email -%}{{ contributor.email }}{{ '  \n' }}{%- endif -%}
{% if contributor.homepageUrl -%}{{ contributor.homepageUrl }}{{ '  \n' }}{%- endif -%}
{% if contributor.identifier -%}{{ contributor.identifier }}{{ '  \n' }}{%- endif -%}

{% endfor -%}
{% endif -%}

{%- if funding %}
Funding:
{%- for source in funding %}
{{ source.name }}
{% if source.sponsor -%}{{ source.sponsor }}{{ '  \n' }}{%- endif -%}
{% if source.identifier -%}{{ source.identifier }}{{ '  \n' }}{%- endif -%}
{% if source.homepageUrl -%}{{ source.homepageUrl }}{{ '  \n' }}{%- endif -%}
{% endfor -%}
{% endif -%}

{%- if identifier -%}
## Identifier
{{ identifier }}
{% endif -%}

{%- if query %}
Query:
{{ query }}
{% endif -%}
{%- if queryParameters %}
Query parameters:
{%- for parameter in queryParameters %}
{% if parameter.name -%}Name: {{ parameter.name }}{{ '  \n' }}{%- endif -%}
{% if parameter.description -%}Description: {{ parameter.description }}{{ '  \n' }}{%- endif -%}
{% if parameter.type -%}Type: {{ parameter.type }}{{ '  \n' }}{%- endif -%}
{% if parameter.arrayType -%}Array type: {{ parameter.arrayType }}{{ '  \n' }}{%- endif -%}
{% if parameter.defaultValue -%} Default value: {{ parameter.defaultValue }}{{ '  \n' }}{%- endif -%}

{% endfor -%}
{% endif -%}

{%- if queryResultColumns %}
Result columns:
{%- for resultColumn in queryResultColumns %}
{% if resultColumn.name -%}Name: {{ resultColumn.name }}{{ '  \n' }}{%- endif -%}
{% if resultColumn.description -%}Description: {{ resultColumn.description }}{{ '  \n' }}{%- endif -%}
{% if resultColumn.type -%}Type: {{ resultColumn.type }}{{ '  \n' }}{%- endif -%}

{% endfor -%}
{% endif -%}

{%- if queryIsCacheable %}
Query Is Cacheable: True
{% endif -%}
'''
import re, os

def create_anchor(header):
    anchor = header.lower().strip()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = anchor.replace(' ', '-')
    return f'#{anchor}'

def extract_header(markdown_content):
    lines = markdown_content.split('\n')
    for line in lines:
        if line.startswith('#'):
            return line.strip('# ').strip()
    return None

def adjust_heading_levels(content):
    """If H1 headers are present, increase the header level of all headers."""
    if re.search(r'^# ', content, flags=re.MULTILINE):
        content = re.sub(r'^(#{1,5})', r'#\1', content, flags=re.MULTILINE)
    return content

def get_path_component(file_path, depth):
    parts = file_path.split('/')
    if depth >= len(parts):
        return file_path
    return '/'.join(parts[-depth:])

def increase_header_level(markdown_text):
    # Define the regular expression for markdown headers
    header_pattern = re.compile(r'^(#{1,5})(\s)', re.MULTILINE)
    
    # Define the substitution function
    def substitute_header(match):
        header = match.group(1)
        space = match.group(2)
        return '#' * (len(header) + 1) + space
    
    # Use re.sub with the substitution function
    updated_text = header_pattern.sub(substitute_header, markdown_text)
    return updated_text

def concatenate_markdown_with_toc(markdown_texts, document_title, introduction, include_toc=True):
    # Initialize the concatenated document

    title_text = f"# {document_title}\n\n" if document_title else ''
    introduction = introduction + '\n\n' if introduction else ''
    table_of_contents = ''

    if include_toc:
        table_of_contents = "## Table of Contents\n\n"
    
    concatenated_document = ''
    for markdown_text in markdown_texts:
        # Extract the title (assuming it's the first header in each document)
        title_match = re.match(r'^\s*#+\s+(.+)', markdown_text, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
            anchor_link = create_anchor(title)
            
            # Add to table of contents if include_toc is True
            if include_toc:
                table_of_contents += f"- [{title}]({anchor_link})\n"
        
        # Increase the header level in the markdown text
        updated_text = adjust_heading_levels(markdown_text)
        
        # Append the updated markdown text to the concatenated document
        concatenated_document += updated_text + "\n\n---\n\n"

    if include_toc:
        table_of_contents += '\n'

    
    # Combine the table of contents and the concatenated document
    final_document = title_text + introduction + table_of_contents + concatenated_document

    return final_document


def concatenate_markdown_multi(files, introduction=None, strip_src_path=1, include_toc=True):
    toc = []
    composite_markdown = []
    introduction_content = ""

    if introduction:
        introduction_content = introduction['content']

    for file in files:
        if file['type'] == 'group':
            content = file['content']
            header = extract_header(content)
            group_name = header
            content = increase_header_level(content)
            composite_markdown.append(content)
            anchor = create_anchor(group_name)
            if include_toc:
                toc.append(f"- [{group_name}]({anchor})")

        elif file['type'] == 'query':
            content = file['content']
            header = extract_header(content)
            query_name = header
            content = increase_header_level(content)
            content = increase_header_level(content)

            composite_markdown.append(content)

            anchor = create_anchor(query_name)
            if include_toc:
                toc.append(f"   + [{query_name}]({anchor})")

    toc_str = "\n".join(toc)
    if include_toc:
        composite_document = introduction_content + "\n" + toc_str + "\n" +  '\n--------\n'.join(composite_markdown)
    else:
        composite_document = introduction_content + "\n\n" + '\n--------\n'.join(composite_markdown)
    return composite_document



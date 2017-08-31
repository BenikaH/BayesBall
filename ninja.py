from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(searchpath="templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('basic.html')
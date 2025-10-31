from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import settings


class TemplateRenderer:
    def __init__(self):
        template_dir = Path("src/template")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render(self, template_path, context):
        # Add settings to template context
        template_context = context.copy()
        template_context['PICS_BASE_URL'] = getattr(settings, 'PICS_BASE_URL', None)
        
        template = self.env.get_template(template_path)
        return template.render(template_context)
    
    def render_gallery(self, pic_data):
        return self.render("gallery.j2.html", pic_data)
    
    def save_html(self, html_content, output_path):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html_content)
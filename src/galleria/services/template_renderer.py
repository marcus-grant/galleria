# S3 URL construction is removed when the config surface is reworked.
# pyright: reportOptionalMemberAccess=false
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import settings
from galleria.services.s3_storage import is_dual_bucket_configured


class TemplateRenderer:
    def __init__(self):
        template_dir = Path("src/galleria/template")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def render(self, template_path, context):
        # Add settings to template context
        template_context = context.copy()
        template_context["PICS_BASE_URL"] = self._generate_pics_base_url()

        template = self.env.get_template(template_path)
        return template.render(template_context)

    def _generate_pics_base_url(self):
        """Generate PICS_BASE_URL based on dual vs single bucket configuration"""
        if is_dual_bucket_configured():
            # Dual bucket: pics are in separate S3_PICS_* bucket
            endpoint = settings.S3_PICS_ENDPOINT.replace("https://", "")
            return f"https://{settings.S3_PICS_BUCKET}.{endpoint}"
        else:
            # Single bucket: pics are in /pics directory of S3_SITE_* bucket
            endpoint = settings.S3_SITE_ENDPOINT.replace("https://", "")
            return f"https://{settings.S3_SITE_BUCKET}.{endpoint}/pics"

    def render_gallery(self, pic_data):
        return self.render("gallery.j2.html", pic_data)

    def save_html(self, html_content, output_path):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html_content)


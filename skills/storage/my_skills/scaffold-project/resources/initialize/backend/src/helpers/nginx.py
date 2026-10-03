"""
Helper function to automatically compile and generate Nginx config from settings.
"""
from src.config import Settings, exists, read_text, write_text, ensure_dir


def generate_nginx_config() -> bool:
    """
    Dynamically compile Nginx rate limiting and port configuration from settings.
    """
    template_rel = "deploy/nginx/nginx.conf.template"
    output_rel = "deploy/nginx/nginx.conf"

    if not exists(template_rel):
        return False

    try:
        content = read_text(template_rel)

        replacements = {
            "${API_PORT}": str(Settings.API_PORT),
            "${NGINX_RATE_LIMIT_ZONE_SIZE}": str(Settings.NGINX_RATE_LIMIT_ZONE_SIZE),
            "${NGINX_RATE_LIMIT_RATE}": str(Settings.NGINX_RATE_LIMIT_RATE),
            "${NGINX_RATE_LIMIT_BURST}": str(Settings.NGINX_RATE_LIMIT_BURST),
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        # Get parent directory and ensure it exists
        output_dir = output_rel.rsplit("/", 1)[0]
        ensure_dir(output_dir)
        
        write_text(output_rel, content)
        return True
    except Exception:
        return False

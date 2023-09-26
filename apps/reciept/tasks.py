from config.celery import app

from .utils import create_pdf


@app.task
def async_create_pdf(id, check_type, order_detail):
    """
    Asynchronously creates a PDF file for a check.
    """
    create_pdf(id, check_type, order_detail)
    return None
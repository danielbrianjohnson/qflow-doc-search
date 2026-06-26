import logging

from celery import shared_task

from app.models import Document
from app.services.processing import mark_document_failed, process_document

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_document_task(self, document_id: int):
    try:
        document = Document.objects.filter(pk=document_id).first()
        if document is None:
            logger.warning("Document %s not found.", document_id)
            return

        process_document(document_id)
    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        mark_document_failed(document_id, str(exc))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise

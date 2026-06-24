import os

from django.core.management.base import BaseCommand

from app.services.embeddings import get_embedding_service


class Command(BaseCommand):
    help = "Load the embedding model into memory."

    def handle(self, *args, **options):
        service = get_embedding_service()
        service.warmup()
        self.stdout.write(self.style.SUCCESS("Embedding model is ready."))

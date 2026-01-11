from django.core.management.base import BaseCommand
from artworks.import_romanian import import_romanian_heritage

class Command(BaseCommand):
    help = 'Import Romanian cultural heritage from data.gov.ro'

    def handle(self, *args, **options):
        import_romanian_heritage()
        self.stdout.write(self.style.SUCCESS('Successfully imported Romanian heritage'))

from django.core.management.base import BaseCommand , CommandError
from core import worker

class Command(BaseCommand):
    help = 'will run the Job Queue'

    def add_arguments(self, parser):
        pass

    def handle(self , *args , **options):
        self.stdout.write(self.style.SUCCESS('Workers Started'))
        worker.Main()()
        self.stdout.write(self.style.SUCCESS('Workers Ends'))

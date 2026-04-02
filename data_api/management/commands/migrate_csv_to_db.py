import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from data_api.models import YahooFinanceData
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrates Yahoo Finance data from CSV to Postgres'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'gs_yahoo_finance.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found at {csv_file_path}"))
            return

        with open(csv_file_path, mode='r') as f:
            reader = csv.DictReader(f)
            count = 0
            to_create = []
            
            for row in reader:
                # Format: 1999-05-04 00:00:00-04:00
                # Django's DateTimeField handles ISO-like strings with offsets quite well if format is consistent.
                # However, for safety, let's just create the objects.
                
                try:
                    obj = YahooFinanceData(
                        date=row['Date'],
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(float(row['Volume'])),
                        dividends=float(row['Dividends']),
                        stock_splits=float(row['Stock Splits']),
                        source=row['Source']
                    )
                    to_create.append(obj)
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping row on error: {e}"))

            if to_create:
                YahooFinanceData.objects.bulk_create(to_create)
                self.stdout.write(self.style.SUCCESS(f"Successfully migrated {count} rows from CSV to database."))
            else:
                self.stdout.write(self.style.WARNING("No data to migrate."))

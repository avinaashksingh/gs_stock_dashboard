from django.db import models

class YahooFinanceData(models.Model):
    date = models.DateTimeField(db_index=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()
    dividends = models.FloatField()
    stock_splits = models.FloatField()
    source = models.CharField(max_length=100)

    class Meta:
        ordering = ['date']
        verbose_name_plural = "Yahoo Finance Data"

    def __str__(self):
        return f"{self.date} - {self.close}"

import os
import time
import random
import pandas as pd
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from django.db.models import Avg, StdDev
from .models import YahooFinanceData

class YahooFinanceUpdateView(APIView):
    def get(self, request):
        try:
            # 1. Fetch data for long-term momentum (1 year = ~252 records)
            history_all = YahooFinanceData.objects.order_by('-date')
            count = history_all.count()
            
            if count < 300:
                return Response({"error": "Insufficient history for 1-year momentum analysis"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            p_last_rec = history_all[0]
            # Get the price from roughly 252 trading days ago
            p_year_ago_rec = history_all[252]
            
            # Global aggregates for scaling and mean reversion
            aggregates = YahooFinanceData.objects.aggregate(
                avg_close=Avg('close'),
                std_close=StdDev('close'),
                avg_vol=Avg('volume'),
                std_vol=StdDev('volume')
            )
            
            # 2. Long-Term Momentum Strategy: Yearly Drift + Random Walk
            long_mean = float(aggregates['avg_close'] or 400.0)
            
            # Yearly momentum (percentage change over ~252 records)
            yearly_momentum = (p_last_rec.close - p_year_ago_rec.close) / p_year_ago_rec.close if p_year_ago_rec.close > 0 else 0
            # Normalize specific yearly momentum into a 5-second step drift
            # We scale it down significantly to make each dashboard update realistic
            drift = yearly_momentum * 0.0001
            
            # Mean Reversion: pull towards the mean
            gravity = (long_mean - p_last_rec.close) / long_mean * 0.001
            
            # 3. Smooth Step Generation
            vol_scale = 0.002
            noise = random.gauss(0, vol_scale)
            
            # Calculate Next Close
            gen_close = float(p_last_rec.close) * (1 + drift + gravity + noise)
            
            # 4. Derive OHLC
            gen_open = float(p_last_rec.close)
            intra_vol = abs(noise) * 0.5 + 0.001
            gen_high = max(gen_open, gen_close) * (1 + random.uniform(0, intra_vol))
            gen_low = min(gen_open, gen_close) * (1 - random.uniform(0, intra_vol))
            
            # 5. Volume Correlated with Activity
            price_change_pct = abs(gen_close - gen_open) / gen_open if gen_open > 0 else 0.001
            vol_multiplier = (price_change_pct / vol_scale)
            
            m_vol = float(p_last_rec.volume)
            gen_volume = int(max(100000, m_vol * (1 + random.uniform(-0.1, 0.1) + vol_multiplier * 0.05)))
            
            # 6. Save new row
            now = datetime.now()
            new_entry = YahooFinanceData.objects.create(
                date=now,
                open=round(gen_open, 4),
                high=round(gen_high, 4),
                low=round(gen_low, 4),
                close=round(gen_close, 4),
                volume=gen_volume,
                dividends=0.0,
                stock_splits=0.0,
                source="Yahoo Finance (Yearly Momentum)"
            )
            
            # 7. Maintain Table Size
            oldest = YahooFinanceData.objects.order_by('date').first()
            if oldest:
                oldest.delete()
            
            # 8. Dashboard Return - Show last 100
            final_history_qs = YahooFinanceData.objects.order_by('-date')[:100]
            data_list = list(final_history_qs)
            data_list.reverse()
            
            response_data = []
            for item in data_list:
                response_data.append({
                    "Date": item.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "Open": item.open,
                    "High": item.high,
                    "Low": item.low,
                    "Close": item.close,
                    "Volume": item.volume,
                    "Dividends": item.dividends,
                    "Stock Splits": item.stock_splits,
                    "Source": item.source
                })
            
            return Response({"data": response_data, "latest": response_data[-1]}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

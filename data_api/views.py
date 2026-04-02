import os
import time
import random
import pandas as pd
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from django.db.models import Avg, StdDev, Func
from .models import YahooFinanceData

# Add scipy for t-distribution
try:
    from scipy.stats import t
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

class YahooFinanceUpdateView(APIView):
    def get(self, request):
        try:
            # 1. Fetch data for multi-timeframe momentum analysis
            history_all = YahooFinanceData.objects.order_by('-date')
            count = history_all.count()
            
            if count < 300:
                return Response({"error": "Insufficient history for momentum analysis"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            p_last_rec = history_all[0]
            
            # 2. Compute rolling volatility (30-day window)
            recent_30 = YahooFinanceData.objects.order_by('-date')[:30]
            if recent_30:
                rolling_std = recent_30.aggregate(std=StdDev('close'))['std'] or 0.02
                rolling_vol = float(rolling_std) / float(p_last_rec.close) if p_last_rec.close > 0 else 0.02
            else:
                rolling_vol = 0.02
            
            # 3. Global aggregates for mean reversion
            aggregates = YahooFinanceData.objects.aggregate(
                avg_close=Avg('close'),
                std_close=StdDev('close'),
                avg_vol=Avg('volume'),
                std_vol=StdDev('volume')
            )
            
            long_mean = float(aggregates['avg_close'] or 400.0)
            
            # 4. Multi-timeframe momentum calculation
            # Yearly momentum (~252 records)
            p_year_ago_rec = history_all[252] if count > 252 else history_all[count-1]
            yearly_momentum = (p_last_rec.close - p_year_ago_rec.close) / p_year_ago_rec.close if p_year_ago_rec.close > 0 else 0
            
            # Medium-term momentum (30-day)
            p_30day_rec = history_all[30] if count > 30 else history_all[count-1]
            medium_momentum = (p_last_rec.close - p_30day_rec.close) / p_30day_rec.close if p_30day_rec.close > 0 else 0
            
            # Short-term momentum (5-day)
            p_5day_rec = history_all[5] if count > 5 else history_all[count-1]
            short_momentum = (p_last_rec.close - p_5day_rec.close) / p_5day_rec.close if p_5day_rec.close > 0 else 0
            
            # Weighted combination
            drift = (yearly_momentum * 0.3 + medium_momentum * 0.5 + short_momentum * 0.2) * 0.0001
            
            # 5. Adaptive mean reversion
            deviation = abs(p_last_rec.close - long_mean) / long_mean
            if deviation > 0.1:
                gravity_strength = 0.002
            elif deviation > 0.05:
                gravity_strength = 0.001
            else:
                gravity_strength = 0.0005
            gravity = (long_mean - p_last_rec.close) / long_mean * gravity_strength
            
            # 6. Volatility clustering and scaling
            recent_changes = [abs(r.close - r.open) / r.open for r in history_all[:10] if r.open > 0]
            avg_recent_vol = sum(recent_changes) / len(recent_changes) if recent_changes else 0.01
            
            vol_scale = max(0.005, min(0.05, rolling_vol))
            if avg_recent_vol > 0.02:  # High vol regime
                vol_scale *= 1.5
            elif avg_recent_vol < 0.01:  # Low vol regime
                vol_scale *= 0.7
            
            # 7. Seasonal adjustments
            now = datetime.now()
            day_of_week = now.weekday()  # 0=Monday
            if day_of_week == 0:  # Monday higher vol
                vol_scale *= 1.2
            elif day_of_week == 4:  # Friday lower vol
                vol_scale *= 0.9
            
            if now.month == 10:  # October volatility
                vol_scale *= 1.3
            
            # 8. Generate noise with fat tails
            if SCIPY_AVAILABLE:
                # t-distribution with 4.5 degrees of freedom for fat tails
                noise = t.rvs(4.5, loc=0, scale=vol_scale, size=1)[0]
            else:
                # Fallback to normal if scipy not available
                noise = random.gauss(0, vol_scale)
            
            # 9. Calculate next close
            gen_close = float(p_last_rec.close) * (1 + drift + gravity + noise)
            
            # 10. Realistic OHLC generation
            gen_open = float(p_last_rec.close)
            typical_range_pct = 0.015 + vol_scale * 10  # 1.5-3% typical range
            range_noise = random.uniform(0.5, 1.5)
            range_pct = typical_range_pct * range_noise
            
            mid_price = (gen_open + gen_close) / 2
            range_half = mid_price * range_pct / 2
            
            gen_high = mid_price + range_half
            gen_low = mid_price - range_half
            
            # Ensure proper OHLC bounds
            gen_high = max(gen_high, gen_open, gen_close)
            gen_low = min(gen_low, gen_open, gen_close)
            
            # 11. Enhanced volume modeling
            price_change_pct = abs(gen_close - gen_open) / gen_open if gen_open > 0 else 0.001
            price_elasticity = 2.0
            vol_multiplier = 1 + price_change_pct * price_elasticity
            
            # Base volume on recent average
            recent_volumes = [r.volume for r in history_all[:10]]
            avg_recent_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 1000000
            
            vol_noise = random.normalvariate(0, 0.2) if hasattr(random, 'normalvariate') else random.gauss(0, 0.2)
            gen_volume = int(max(100000, avg_recent_volume * vol_multiplier * (1 + vol_noise)))
            
            # 12. Save new row
            new_entry = YahooFinanceData.objects.create(
                date=now,
                open=round(gen_open, 4),
                high=round(gen_high, 4),
                low=round(gen_low, 4),
                close=round(gen_close, 4),
                volume=gen_volume,
                dividends=0.0,
                stock_splits=0.0,
                source="Synthetic (Realistic Model)"
            )
            
            # 13. Maintain Table Size (FIFO)
            oldest = YahooFinanceData.objects.order_by('date').first()
            if oldest:
                oldest.delete()
            
            # 14. Dashboard Return - Show last 100
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

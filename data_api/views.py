import os
import time
import random
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class CSVDataView(APIView):
    def get(self, request, filename):
        # Derive the actual filename from the endpoint name
        # If the endpoint is /barchart, the file is gs_barchart.csv
        actual_filename = f"gs_{filename}.csv"
        file_path = os.path.join(settings.BASE_DIR, 'data', actual_filename)
        
        if not os.path.exists(file_path):
            return Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Introduce a random delay (e.g., between 0.1 and 2.0 seconds)
        delay = random.uniform(0.1, 2.0)
        time.sleep(delay)
        
        try:
            df = pd.read_csv(file_path)
            data = df.to_dict(orient='records')
            return Response({"data": data})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
Configuration Settings
---------------------
Central configuration for the GDELT document processing pipeline.
Contains API keys, database connection details, and processing parameters.
"""

import os
from typing import Dict, Any
from apisecrets.geminapi import api_key

# Gemini AI Configuration
GEMINI_API_KEY = api_key
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
GEMINI_EMBEDDING_DIMENSION = 768

# Milvus Vector Database Configuration
MILVUS_URI = os.getenv(
    "MILVUS_URI", 
    "https://in03-74754152a0ad853.serverless.gcp-us-west1.cloud.zilliz.com"
)
MILVUS_TOKEN = os.getenv(
    "MILVUS_TOKEN",
    "1e310bee8464f1e8838f0b90938e3121697a6df878074a1b1c0657460b45837450b262cde5cd9756c868bb3e87e7b9d6b4f2c01a"
)
MILVUS_COLLECTION_NAME = "political_risk_docs_filtered"
MILVUS_MAX_VARCHAR_LENGTH = 65535

# GDELT Processing Configuration
GKG_URL_FETCH_LIMIT = 10

import csv
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
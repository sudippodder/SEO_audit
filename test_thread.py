import sys
sys.path.append('d:/AI/seo_audit')
from core.external_validator import _validate_trustpilot
import threading

def test():
    print(_validate_trustpilot('virtualemployee.com'))

t = threading.Thread(target=test)
t.start()
t.join()

# core.py — replace your fetch_page() function with this version
import utils.compat 
import socket
import urllib3

# Silence urllib3's own noisy warnings on Windows
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control":   "no-cache",
}

# Retry adapter — retries on connection errors automatically
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,                        # retry up to 3 times
        backoff_factor=0.5,             # wait 0.5s, 1s, 2s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://",  adapter)
    session.mount("https://", adapter)
    return session


def fetch_page(
    url: str,
) -> tuple:
    """
    Fetch a URL with retry logic and graceful error handling.

    Returns:
        (soup, raw_html, status_code, fetch_time_ms, response_headers)
        On failure: (None, None, error_code, 0, {})
    """
    session = _build_session()

    try:
        t0   = time.time()
        resp = session.get(
            url,
            headers=HEADERS,
            timeout=(10, 25),       # (connect_timeout, read_timeout)
            allow_redirects=True,
            verify=True,            # SSL verification
        )
        ms   = int((time.time() - t0) * 1000)
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        return soup, html, resp.status_code, ms, dict(resp.headers)

    except requests.exceptions.SSLError:
        # Retry without SSL verification (self-signed certs etc.)
        try:
            t0   = time.time()
            resp = session.get(
                url,
                headers=HEADERS,
                timeout=(10, 25),
                allow_redirects=True,
                verify=False,
            )
            ms   = int((time.time() - t0) * 1000)
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            return soup, html, resp.status_code, ms, dict(resp.headers)
        except Exception as e:
            return None, None, 0, 0, {"_error": f"SSL error: {e}"}

    except requests.exceptions.ConnectionError as e:
        err = str(e)
        if "10054" in err or "ConnectionReset" in err:
            # Server closed the connection — try a plain GET with no keep-alive
            try:
                plain_headers = {**HEADERS, "Connection": "close"}
                t0   = time.time()
                resp = requests.get(
                    url,
                    headers=plain_headers,
                    timeout=(10, 25),
                    allow_redirects=True,
                    verify=False,
                )
                ms   = int((time.time() - t0) * 1000)
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
                return soup, html, resp.status_code, ms, dict(resp.headers)
            except Exception as e2:
                return None, None, 0, 0, {"_error": f"Connection reset: {e2}"}
        return None, None, 0, 0, {"_error": f"Connection error: {e}"}

    except requests.exceptions.Timeout:
        return None, None, 0, 0, {"_error": "Request timed out after 25 seconds"}

    except requests.exceptions.TooManyRedirects:
        return None, None, 0, 0, {"_error": "Too many redirects — possible redirect loop"}

    except Exception as e:
        return None, None, 0, 0, {"_error": f"Unexpected fetch error: {e}"}

    finally:
        session.close()
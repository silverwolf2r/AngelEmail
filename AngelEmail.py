import re
import time
from collections import deque, Counter
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
import tldextract
import smtplib


def get_page_content(url, timeout=8, headers=None):
    headers = headers or {
        "User-Agent": "Mozilla/5.0 (compatible; EmailScraper/1.0; +https://example.com/bot)"
    }
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "")
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            return None
        return resp.text
    except requests.RequestException:
        return None


def extract_emails(html_content):
    if not html_content:
        return set()
    email_regex = r'(?i)(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.+-])'
    return set(m.group(1) for m in re.finditer(email_regex, html_content))


def same_registered_domain(u1, u2):
    d1 = tldextract.extract(u1)
    d2 = tldextract.extract(u2)
    return (d1.domain, d1.suffix) == (d2.domain, d2.suffix)


def scrape_domain_emails(start_url, max_pages=60, max_depth=2, delay_s=0.15):
    parsed_start = urlparse(start_url)
    if parsed_start.scheme not in ("http", "https"):
        raise ValueError("start_url must be http(s).")

    start_url = urldefrag(start_url)[0]
    visited = set()
    queue = deque([(start_url, 0)])
    extracted_emails = set()
    pages_crawled = 0

    while queue and pages_crawled < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        html = get_page_content(url)
        if html:
            emails = extract_emails(html)
            extracted_emails.update(emails)

            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().startswith("mailto:"):
                    continue
                absolute = urljoin(url, href)
                absolute = urldefrag(absolute)[0]
                parsed = urlparse(absolute)
                if parsed.scheme not in ("http", "https"):
                    continue
                if same_registered_domain(start_url, absolute) and absolute not in visited:
                    queue.append((absolute, depth + 1))

        pages_crawled += 1
        if delay_s:
            time.sleep(delay_s)

    return extracted_emails, visited


def most_common_domain_from_emails(emails):
    domains = [e.split("@", 1)[1] for e in emails if "@" in e]
    if not domains:
        return None
    return Counter(domains).most_common(1)[0][0]


def try_port25_banner(host, timeout=8):
    try:
        s = smtplib.SMTP(timeout=timeout)
        code, banner = s.connect(host, 25)
        s.close()
        banner_text = banner.decode("utf-8", "ignore") if isinstance(banner, (bytes, bytearray)) else str(banner)
        first_line = banner_text.splitlines()[0] if banner_text else ""
        return {"connected": (200 <= code < 400), "code": code, "banner": first_line}
    except Exception:
        return {"connected": False}


def normalize_domain(user_input):
    text = user_input.strip()
    if "://" not in text:
        base_domain = tldextract.extract(text)
        domain = ".".join([p for p in [base_domain.domain, base_domain.suffix] if p])
        return domain, f"https://{domain}"

    parsed = urlparse(text)
    ext = tldextract.extract(parsed.netloc or parsed.path)
    domain = ".".join([p for p in [ext.domain, ext.suffix] if p])
    return domain, f"https://{domain}"


def try_http_fallback(start_url):
    if get_page_content(start_url) is not None:
        return start_url
    if start_url.startswith("https://"):
        alt = "http://" + start_url[len("https://"):]
        if get_page_content(alt) is not None:
            return alt
    return start_url


def main():
    user_input = input("Enter a domain (e.g., example.com): ").strip()
    input_domain, start_url = normalize_domain(user_input)
    start_url = try_http_fallback(start_url)

    emails, _ = scrape_domain_emails(start_url=start_url, max_pages=40, max_depth=2)

    derived_domain = most_common_domain_from_emails(emails)

    probe_domain = derived_domain or input_domain
    email_server = f"{probe_domain.replace('.', '-')}.mail.protection.outlook.com"

    scan = try_port25_banner(email_server)

    print("\n=== Summary ===")
    print(f"Input Domain:            {input_domain}")
    print(f"Derived Email Domain:    {derived_domain or '(none found)'}")
    print(f"Email Server Tested:     {email_server}")
    if scan.get("connected"):
        print(f"Port 25 Result:          OPEN (code={scan['code']})")
        if scan.get("banner"):
            print(f"Banner:                  {scan['banner']}")
    else:
        print("Port 25 Result:          UNREACHABLE or CLOSED")

    print("\n=== Emails Found ===")
    if emails:
        for e in sorted(emails):
            print(e)
    else:
        print("(none)")

if __name__ == "__main__":
     main()
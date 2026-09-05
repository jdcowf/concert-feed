import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
from pathlib import Path
import sys
from dataclasses import dataclass
import datetime as dt
import functools
import itertools
import json
import logging
from typing import List, Optional
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

log = logging.getLogger(__name__)


@dataclass
class EventInfo:
    title: str = ""
    link: str = "#"
    date_obj: dt.datetime = dt.datetime.max
    time: str = ""
    venue: str = ""
    tickets: str = ""

    @property
    def date_str(self):
        return self.date_obj.strftime("%A %B %d %Y")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

BROWSER_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)

def _get(url: str, ua: str = BROWSER_UA, **kwargs) -> requests.Response:
    """GET with a consistent User-Agent and raise on HTTP errors."""
    headers = {'User-Agent': ua}
    log.debug(f"GET {url}")
    resp = requests.get(url, headers=headers, timeout=15, **kwargs)
    log.debug(f"  -> HTTP {resp.status_code}  ({len(resp.content)} bytes)")
    resp.raise_for_status()
    return resp


# ---------------------------------------------------------------------------
# Cat's Cradle
# ---------------------------------------------------------------------------

def scrape_catscradle_events() -> List[EventInfo]:
    """Fetches and parses events from Cat's Cradle."""
    VENUE = "Cat's Cradle"
    URL = 'https://catscradle.com/events/'
    log.info(f"[{VENUE}] Scraping {URL}")

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'June': 6, 'July': 7, 'Aug': 8,
        'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str: str) -> dt.datetime:
        match = re.search(r'\w{3}, (\w{3,4}) (\d{1,2})', date_str)
        if not match:
            log.warning(f"  [{VENUE}] Could not parse date string: {date_str!r}")
            return dt.datetime.max
        month_abbr, day = match.groups()
        month_num = month_map.get(month_abbr)
        if month_num is None:
            log.warning(f"  [{VENUE}] Unknown month abbreviation: {month_abbr!r} in {date_str!r}")
            return dt.datetime.max
        year = dt.datetime.now().year
        return dt.datetime(year, month_num, int(day))

    resp = _get(URL, ua='concert-feed')
    soup = BeautifulSoup(resp.text, 'html.parser')
    event_divs = soup.find_all('div', class_='rhpSingleEvent')
    log.info(f"  [{VENUE}] Found {len(event_divs)} rhpSingleEvent divs")

    events = []
    for i, event in enumerate(event_divs):
        title_tag  = event.select_one('h2')
        link_tag   = event.select_one('a.url')
        date_tag   = event.select_one('.singleEventDate')
        time_tag   = event.select_one('.rhp-event__time-text--list')
        venue_tag  = event.select_one('.rhp-event__venue-text--list')
        ticket_tag = event.select_one('.rhp-event-list-cta a')

        title    = title_tag.text.strip()  if title_tag   else 'Untitled'
        link     = link_tag['href']         if link_tag and link_tag.has_attr('href') else '#'
        date_raw = date_tag.text.strip()   if date_tag    else ''
        date_obj = parse_event_date(date_raw) if date_raw else dt.datetime.max
        time     = time_tag.text.strip()   if time_tag    else ''
        venue    = venue_tag.text.strip()  if venue_tag   else VENUE
        tickets  = ticket_tag['href']      if ticket_tag and ticket_tag.has_attr('href') else ''

        log.debug(f"  [{VENUE}] [{i}] title={title!r}  date_raw={date_raw!r}  "
                  f"date_parsed={date_obj}  time={time!r}  tickets={'yes' if tickets else 'no'}")

        if title == 'Untitled':
            log.warning(f"  [{VENUE}] [{i}] No title found - skipping")
            continue
        if date_obj == dt.datetime.max:
            log.warning(f"  [{VENUE}] [{i}] No valid date for {title!r} - will sort to bottom")

        events.append(EventInfo(title=title, link=link, date_obj=date_obj,
                                time=time, venue=venue, tickets=tickets))

    events.sort(key=lambda e: e.date_obj)
    log.info(f"  [{VENUE}] Returning {len(events)} events")
    return events


# ---------------------------------------------------------------------------
# Local 506
# ---------------------------------------------------------------------------

def scrape_local506_events() -> List[EventInfo]:
    """Fetches and parses events from Local 506."""
    VENUE = "Local 506"
    URL = 'https://local506.com/events/'
    log.info(f"[{VENUE}] Scraping {URL}")

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'June': 6, 'July': 7, 'Aug': 8,
        'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str: str) -> dt.datetime:
        match = re.search(r'\w{3}, (\w{3,4}) (\d{1,2})', date_str)
        if not match:
            log.warning(f"  [{VENUE}] Could not parse date string: {date_str!r}")
            return dt.datetime.max
        month_abbr, day = match.groups()
        month_num = month_map.get(month_abbr)
        if month_num is None:
            log.warning(f"  [{VENUE}] Unknown month abbreviation: {month_abbr!r} in {date_str!r}")
            return dt.datetime.max
        year = dt.datetime.now().year
        return dt.datetime(year, month_num, int(day))

    resp = _get(URL, ua='concert-feed')
    soup = BeautifulSoup(resp.text, 'html.parser')
    event_divs = soup.find_all('div', class_='rhpSingleEvent')
    log.info(f"  [{VENUE}] Found {len(event_divs)} rhpSingleEvent divs")

    events = []
    for i, event in enumerate(event_divs):
        title_tag  = event.select_one('h2')
        link_tag   = event.select_one('a.url')
        date_tag   = event.select_one('.singleEventDate')
        time_tag   = event.select_one('.rhp-event__time-text--list')
        venue_tag  = event.select_one('.rhp-event__venue-text--list')
        ticket_tag = event.select_one('.rhp-event-list-cta a')

        title    = title_tag.text.strip()  if title_tag   else 'Untitled'
        link     = link_tag['href']         if link_tag and link_tag.has_attr('href') else '#'
        date_raw = date_tag.text.strip()   if date_tag    else ''
        date_obj = parse_event_date(date_raw) if date_raw else dt.datetime.max
        time     = time_tag.text.strip()   if time_tag    else ''
        venue    = venue_tag.text.strip()  if venue_tag   else VENUE
        tickets  = ticket_tag['href']      if ticket_tag and ticket_tag.has_attr('href') else ''

        log.debug(f"  [{VENUE}] [{i}] title={title!r}  date_raw={date_raw!r}  "
                  f"date_parsed={date_obj}  time={time!r}  tickets={'yes' if tickets else 'no'}")

        if title == 'Untitled':
            log.warning(f"  [{VENUE}] [{i}] No title found - skipping")
            continue
        if date_obj == dt.datetime.max:
            log.warning(f"  [{VENUE}] [{i}] No valid date for {title!r} - will sort to bottom")

        events.append(EventInfo(title=title, link=link, date_obj=date_obj,
                                time=time, venue=venue, tickets=tickets))

    events.sort(key=lambda e: e.date_obj)
    log.info(f"  [{VENUE}] Returning {len(events)} events")
    return events


# ---------------------------------------------------------------------------
# The Ritz Raleigh
# ---------------------------------------------------------------------------

def scrape_ritz_events() -> List[EventInfo]:
    VENUE = "The Ritz Raleigh"
    URL = 'https://ritzraleigh.com/shows'
    log.info(f"[{VENUE}] Scraping {URL}")

    def parse_event_date(date_str: str) -> dt.datetime:
        for fmt in ('%a %b %d, %Y', '%a %b %d %Y'):
            try:
                return dt.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        log.warning(f"  [{VENUE}] Could not parse date string: {date_str!r}")
        return dt.datetime.max

    resp = _get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    groups = soup.find_all('div', class_='chakra-linkbox')
    log.info(f"  [{VENUE}] Found {len(groups)} chakra-linkbox divs")

    events = []
    for i, group in enumerate(groups):
        try:
            title_tag = group.select_one('p.chakra-text.css-zvlevn')
            date_tag  = group.select_one('p.chakra-text.css-aqbsuf')
            link_tag  = group.select_one('a.chakra-button.css-1d2qex5')

            title    = title_tag.text.strip() if title_tag else ''
            date_raw = date_tag.text.strip()  if date_tag  else ''
            tickets  = link_tag['href']        if link_tag and link_tag.has_attr('href') else '#'
            date_obj = parse_event_date(date_raw) if date_raw else dt.datetime.max

            log.debug(f"  [{VENUE}] [{i}] title={title!r}  date_raw={date_raw!r}  "
                      f"date_parsed={date_obj}  tickets={'yes' if tickets != '#' else 'no'}")

            if not title:
                log.warning(f"  [{VENUE}] [{i}] Empty title - skipping")
                continue
            if date_obj == dt.datetime.max:
                log.warning(f"  [{VENUE}] [{i}] No valid date for {title!r}")

            events.append(EventInfo(title=title, date_obj=date_obj,
                                    tickets=tickets, venue=VENUE))
        except Exception:
            log.exception(f"  [{VENUE}] [{i}] Error parsing event block")

    log.info(f"  [{VENUE}] Returning {len(events)} events")
    return events


# ---------------------------------------------------------------------------
# The Fillmore Charlotte
# ---------------------------------------------------------------------------

def scrape_fillmore_charlotte() -> List[EventInfo]:
    VENUE = "The Fillmore Charlotte"
    URL = "https://www.fillmorenc.com/shows"
    log.info(f"[{VENUE}] Scraping {URL}")

    resp = _get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    containers = soup.select('div[role="group"].chakra-linkbox')
    log.info(f"  [{VENUE}] Found {len(containers)} chakra-linkbox[role=group] divs")

    events = []
    for i, container in enumerate(containers):
        title_tag   = container.select_one("p.chakra-text.css-zvlevn")
        date_tag    = container.select_one("p.chakra-text.css-lfdvoo")
        link_tag    = container.select_one("a[href*='ticketmaster.com']")
        overlay_tag = container.select_one("a.chakra-linkbox__overlay")

        title    = title_tag.get_text(strip=True) if title_tag   else ''
        date_raw = date_tag.get_text(strip=True)  if date_tag    else ''
        tickets  = link_tag['href']                if link_tag    else '#'
        link     = overlay_tag['href']             if overlay_tag else tickets

        date_obj = dt.datetime.max
        for fmt in ('%a %b %d, %Y', '%a %b %d %Y'):
            try:
                date_obj = dt.datetime.strptime(date_raw, fmt)
                break
            except ValueError:
                continue
        if date_obj == dt.datetime.max and date_raw:
            log.warning(f"  [{VENUE}] [{i}] Could not parse date: {date_raw!r}")

        log.debug(f"  [{VENUE}] [{i}] title={title!r}  date_raw={date_raw!r}  "
                  f"date_parsed={date_obj}  tickets={'yes' if tickets != '#' else 'no'}")

        if not title:
            log.warning(f"  [{VENUE}] [{i}] Empty title - skipping")
            continue

        events.append(EventInfo(title=title, link=link, date_obj=date_obj,
                                venue=VENUE, tickets=tickets))

    log.info(f"  [{VENUE}] Returning {len(events)} events")
    return events


# ---------------------------------------------------------------------------
# Motor Co Music
# ---------------------------------------------------------------------------

def scrape_motorco_events(url: str = "https://motorcomusic.com/calendar") -> List[EventInfo]:
    VENUE = "Motor Co Music"
    log.info(f"[{VENUE}] Scraping {url}")

    try:
        resp = _get(url)
        soup = BeautifulSoup(resp.content, 'html.parser')

        events: List[EventInfo] = []
        script_tags = soup.find_all('script')
        log.debug(f"  [{VENUE}] Scanning {len(script_tags)} <script> tags for inline event data")

        for script in script_tags:
            if script.string and 'title:' in script.string and 'start:' in script.string:
                event_pattern = (
                    r'\{\s*title:\s*[\'"]([^\'"]*)[\'"],'
                    r'\s*start:\s*[\'"]([^\'"]*)[\'"],'
                    r'\s*end:\s*[\'"]([^\'"]*)[\'"],'
                    r'\s*url:\s*[\'"]([^\'"]*)[\'"]'
                )
                matches = re.findall(event_pattern, script.string)
                log.debug(f"  [{VENUE}] Inline JS regex matched {len(matches)} events")

                for title, start_time, end_time, event_url in matches:
                    try:
                        start_dt = dt.datetime.strptime(start_time, '%Y-%m-%d %H:%M')
                        time_str = start_dt.strftime('%H:%M')
                    except ValueError:
                        log.warning(f"  [{VENUE}] Could not parse start: {start_time!r} for {title!r}")
                        start_dt = dt.datetime.max
                        time_str = ""

                    log.debug(f"  [{VENUE}]   title={title!r}  start={start_time!r}  parsed={start_dt}")
                    events.append(EventInfo(
                        title=title.strip(),
                        link=urljoin(url, event_url),
                        date_obj=start_dt,
                        time=time_str,
                        venue=VENUE,
                        tickets=""
                    ))

        if not events:
            log.info(f"  [{VENUE}] Primary JS parsing found nothing - trying DOM fallback")
            events = _motorco_dom_fallback(soup, url, VENUE)

        events.sort(key=lambda x: x.date_obj if x.date_obj != dt.datetime.max else dt.datetime.min)
        log.info(f"  [{VENUE}] Returning {len(events)} events")
        return events

    except requests.RequestException as e:
        log.error(f"  [{VENUE}] Network error: {e}")
        return []
    except Exception:
        log.exception(f"  [{VENUE}] Unexpected error during parse")
        return []


def _motorco_dom_fallback(soup: BeautifulSoup, base_url: str, venue: str) -> List[EventInfo]:
    """DOM-based fallback for Motor Co when JS data is absent."""
    events = []
    containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|calendar'))
    log.debug(f"  [{venue}] DOM fallback: found {len(containers)} candidate containers")

    for container in containers:
        title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|event'))
        link_elem  = container.find('a', href=True)
        date_elem  = container.find(['time', 'span'], class_=re.compile(r'date|time'))

        if not (title_elem and link_elem):
            continue

        title = title_elem.get_text(strip=True)
        link  = urljoin(base_url, link_elem['href'])
        date_obj = dt.datetime.max
        time_str = ""

        if date_elem:
            date_text = date_elem.get_text(strip=True)
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
                try:
                    date_obj = dt.datetime.strptime(date_text, fmt)
                    time_str = date_obj.strftime('%H:%M') if '%H:%M' in fmt else ""
                    break
                except ValueError:
                    continue
            if date_obj == dt.datetime.max:
                log.warning(f"  [{venue}] DOM fallback: unparseable date {date_text!r} for {title!r}")

        log.debug(f"  [{venue}] DOM fallback: title={title!r}  date_parsed={date_obj}")
        events.append(EventInfo(title=title, link=link, date_obj=date_obj,
                                time=time_str, venue=venue, tickets=""))
    return events


# ---------------------------------------------------------------------------
# Lincoln Theatre (via Bandsintown)
# ---------------------------------------------------------------------------

def scrape_lincoln_theatre_events() -> List[EventInfo]:
    """
    Fetches events for Lincoln Theatre from Bandsintown.

    Bandsintown renders its venue pages client-side (Next.js), so a plain
    requests fetch only gets the shell HTML.  The approach here is:

      1. Fetch the venue page and extract the __NEXT_DATA__ JSON blob that
         Next.js embeds server-side in a <script> tag.  This blob contains
         the full event list without any JavaScript execution required.

      2. Fall back to light DOM scraping of server-rendered <script
         type="application/ld+json"> structured-data blocks, which many
         Bandsintown pages also include.

      3. If both are empty (e.g. the page is fully CSR), log a clear
         warning so you know to investigate.

    The venue page URL is: https://www.bandsintown.com/v/10001999-lincoln-theatre
    """
    VENUE = "Lincoln Theatre"
    URL   = "https://www.bandsintown.com/v/10001999-lincoln-theatre"
    log.info(f"[{VENUE}] Scraping {URL}")

    headers = {
        'User-Agent': BROWSER_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    log.debug(f"  [{VENUE}] GET {URL}")
    resp = requests.get(URL, headers=headers, timeout=15)
    log.debug(f"  [{VENUE}] HTTP {resp.status_code}  ({len(resp.content)} bytes)  "
              f"x-deny-reason={resp.headers.get('x-deny-reason', 'none')}")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')
    events: List[EventInfo] = []

    # ── Strategy 1: __NEXT_DATA__ SSR JSON ──────────────────────────────
    next_data_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')
    if next_data_tag and next_data_tag.string:
        log.debug(f"  [{VENUE}] Found __NEXT_DATA__ blob ({len(next_data_tag.string)} chars)")
        try:
            next_data = json.loads(next_data_tag.string)

            # The event list lives at different paths depending on the page version.
            # Try common locations; log what we find so future changes are visible.
            candidates = _extract_json_paths(next_data, [
                ('props', 'pageProps', 'venueEvents'),
                ('props', 'pageProps', 'events'),
                ('props', 'pageProps', 'initialData', 'events'),
                ('props', 'pageProps', 'data', 'events'),
            ])
            log.debug(f"  [{VENUE}] __NEXT_DATA__ candidate paths found: {list(candidates.keys())}")

            raw_events = None
            for path, value in candidates.items():
                if isinstance(value, list) and len(value) > 0:
                    raw_events = value
                    log.info(f"  [{VENUE}] Using __NEXT_DATA__ path '{path}' ({len(value)} items)")
                    break

            if raw_events is None:
                # Log top-level keys to help diagnose structure changes
                log.warning(f"  [{VENUE}] __NEXT_DATA__ found but no recognised event list. "
                            f"Top-level pageProps keys: {list(next_data.get('props', {}).get('pageProps', {}).keys())}")
            else:
                for i, ev in enumerate(raw_events):
                    try:
                        events.append(_parse_bandsintown_event(ev, VENUE, i))
                    except Exception:
                        log.exception(f"  [{VENUE}] Error parsing __NEXT_DATA__ event [{i}]: {ev}")

        except json.JSONDecodeError:
            log.exception(f"  [{VENUE}] Failed to parse __NEXT_DATA__ JSON")

    # ── Strategy 2: JSON-LD structured data ─────────────────────────────
    if not events:
        log.info(f"  [{VENUE}] __NEXT_DATA__ yielded nothing — trying JSON-LD blocks")
        for i, tag in enumerate(soup.find_all('script', type='application/ld+json')):
            try:
                data = json.loads(tag.string or '{}')
                # MusicEvent or array of them
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get('@type') not in ('MusicEvent', 'Event'):
                        continue
                    ev = _parse_jsonld_event(item, VENUE)
                    if ev:
                        events.append(ev)
            except Exception:
                log.exception(f"  [{VENUE}] Error in JSON-LD block [{i}]")
        log.debug(f"  [{VENUE}] JSON-LD yielded {len(events)} events")

    # ── Strategy 3: DOM scraping fallback ───────────────────────────────
    if not events:
        log.info(f"  [{VENUE}] JSON-LD empty — trying DOM scrape")
        events = _scrape_bandsintown_dom(soup, VENUE)

    if not events:
        log.warning(
            f"  [{VENUE}] All strategies returned 0 events. "
            f"The page may be fully client-side rendered and requires a headless browser "
            f"(e.g. playwright/selenium) to execute JavaScript. "
            f"HTTP status was {resp.status_code}."
        )

    events = [e for e in events if e.title]
    events.sort(key=lambda e: e.date_obj)
    log.info(f"  [{VENUE}] Returning {len(events)} events")
    return events


def _extract_json_paths(data: dict, paths: list) -> dict:
    """Walk a nested dict following each path; return {dotted_path: value} for hits."""
    results = {}
    for path in paths:
        node = data
        for key in path:
            if not isinstance(node, dict):
                break
            node = node.get(key)
        else:
            if node is not None:
                results['.'.join(path)] = node
    return results


def _parse_bandsintown_event(ev: dict, venue: str, idx: int) -> EventInfo:
    """Parse a single event dict from Bandsintown's __NEXT_DATA__ structure."""
    title   = ev.get('title') or ev.get('name') or ev.get('artistName') or ''
    link    = ev.get('url') or ev.get('eventUrl') or '#'
    tickets = ev.get('ticketUrl') or ev.get('offers', [{}])[0].get('url', '') if ev.get('offers') else ev.get('ticketUrl', '')
    if not tickets:
        tickets = link  # use event page as fallback

    # Date: try multiple field names and formats
    date_raw = (ev.get('datetime') or ev.get('startDate') or
                ev.get('date') or ev.get('startsAt') or '')
    date_obj = dt.datetime.max
    time_str = ''
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            date_obj = dt.datetime.strptime(date_raw[:19], fmt[:len(date_raw[:19])])
            if '%H' in fmt:
                time_str = date_obj.strftime('%-I:%M %p').lstrip('0')
            break
        except (ValueError, TypeError):
            continue
    if date_obj == dt.datetime.max and date_raw:
        log.warning(f"  Could not parse Bandsintown date: {date_raw!r} for {title!r}")

    log.debug(f"    [BIT event {idx}] title={title!r}  date_raw={date_raw!r}  parsed={date_obj}  tickets={'yes' if tickets else 'no'}")
    return EventInfo(title=title, link=link, date_obj=date_obj,
                     time=time_str, venue=venue, tickets=tickets)


def _parse_jsonld_event(item: dict, venue: str) -> Optional[EventInfo]:
    """Parse a JSON-LD MusicEvent/Event object."""
    title    = item.get('name', '')
    link     = item.get('url', '#')
    date_raw = item.get('startDate', '')
    offers   = item.get('offers', {})
    tickets  = ''
    if isinstance(offers, list) and offers:
        tickets = offers[0].get('url', '')
    elif isinstance(offers, dict):
        tickets = offers.get('url', '')

    date_obj = dt.datetime.max
    time_str = ''
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d'):
        try:
            date_obj = dt.datetime.strptime(date_raw[:19], fmt[:len(date_raw[:19])])
            if 'T' in date_raw and '%H' in fmt:
                time_str = date_obj.strftime('%-I:%M %p').lstrip('0')
            break
        except (ValueError, TypeError):
            continue

    if not title:
        return None
    log.debug(f"    [JSON-LD] title={title!r}  date={date_raw!r}  parsed={date_obj}")
    return EventInfo(title=title, link=link, date_obj=date_obj,
                     time=time_str, venue=venue, tickets=tickets or link)


def _scrape_bandsintown_dom(soup: BeautifulSoup, venue: str) -> List[EventInfo]:
    """
    Last-resort DOM scrape for Bandsintown venue pages.
    Looks for common event container patterns in server-rendered HTML.
    """
    events = []

    # Bandsintown uses data-testid attributes on some builds
    for container in soup.select('[data-testid="event-item"], [data-testid="event-card"], .event-item'):
        title_el  = container.select_one('[data-testid="event-name"], h2, h3')
        date_el   = container.select_one('[data-testid="event-date"], time, .date')
        link_el   = container.select_one('a[href]')
        ticket_el = container.select_one('a[href*="ticket"]')

        title = title_el.get_text(strip=True) if title_el else ''
        link  = link_el['href'] if link_el else '#'
        tickets = ticket_el['href'] if ticket_el else link

        date_raw = date_el.get('datetime') or (date_el.get_text(strip=True) if date_el else '')
        date_obj, time_str = dt.datetime.max, ''
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y'):
            try:
                date_obj = dt.datetime.strptime(date_raw[:len(fmt)+2], fmt)
                break
            except (ValueError, TypeError):
                continue

        if title:
            log.debug(f"    [DOM] title={title!r}  date={date_raw!r}  parsed={date_obj}")
            events.append(EventInfo(title=title, link=link, date_obj=date_obj,
                                    time=time_str, venue=venue, tickets=tickets))

    log.debug(f"  [{venue}] DOM fallback: found {len(events)} events")
    return events


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def render_event_html(event: EventInfo, template: str) -> str:
    """Render a single event using the event template."""
    if event.date_obj <= dt.datetime.today() - dt.timedelta(days=1):
        return ""

    escaped_title = event.title.replace('"', '&quot;').replace("'", "\\'")

    html = template
    html = html.replace('{e.title}', event.title)
    html = html.replace('{e.link}', event.link)
    html = html.replace('{e.venue}', event.venue)
    html = html.replace('{e.date_str}', event.date_str)
    html = html.replace('{e.tickets}', event.tickets or '#')
    html = html.replace('{escaped_title}', escaped_title)
    html = html.replace('{e.title.lower()}', event.title.lower())
    html = html.replace('{e.venue.lower()}', event.venue.lower())

    # Simplified time placeholder (no more f-string embedded in template)
    if event.time:
        time_span = f'<span class="tag">{event.time}</span>'
        html = html.replace("{TIME_SPAN}", time_span)
    else:
        html = html.replace("{TIME_SPAN}", "")

    return html


def generate_html(events: List[EventInfo], title: str = "Upcoming Concerts") -> str:
    """Generate full HTML page using external templates."""
    template_path       = Path(__file__).parent / 'template.html'
    event_template_path = Path(__file__).parent / 'event-template.html'

    if not template_path.exists():
        log.error(f"Template not found: {template_path}")
        return ""
    if not event_template_path.exists():
        log.error(f"Event template not found: {event_template_path}")
        return ""

    main_template  = template_path.read_text(encoding='utf-8')
    event_template = event_template_path.read_text(encoding='utf-8')

    venues = sorted(set(e.venue for e in events if e.venue))
    venues_options = '\n'.join(f'<option value="{v}">{v}</option>' for v in venues)

    rendered = 0
    skipped_past = 0
    events_html = ""
    for event in events:
        html = render_event_html(event, event_template)
        if html:
            events_html += html + '\n'
            rendered += 1
        else:
            skipped_past += 1

    log.info(f"Rendered {rendered} upcoming events, skipped {skipped_past} past events")

    html = main_template.replace('{{TITLE}}', title)
    html = html.replace('{{VENUES_OPTIONS}}', venues_options)
    html = html.replace('{{EVENTS}}', events_html)
    return html


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    all_events: List[EventInfo] = []

    scrapers = [
        scrape_catscradle_events,
        scrape_ritz_events,
        scrape_fillmore_charlotte,
        scrape_motorco_events,
        scrape_local506_events,
        scrape_lincoln_theatre_events,
    ]

    results_summary = {}
    for scraper in scrapers:
        name = scraper.__name__
        try:
            events = scraper()
            all_events.extend(events)
            results_summary[name] = f"OK  {len(events)} events"
        except Exception:
            log.exception(f"Unhandled exception in {name}")
            results_summary[name] = "FAILED"

    log.info("── Scraper summary ───────────────────────────────────────────")
    for name, result in results_summary.items():
        status = "OK " if result.startswith("OK") else "ERR"
        log.info(f"  [{status}] {name:42s}  {result}")
    log.info("──────────────────────────────────────────────────────────────")

    all_events.sort(key=lambda e: e.date_obj)

    html_content = generate_html(all_events)

    if '--output' in sys.argv:
        dest = Path(sys.argv[sys.argv.index('--output') + 1])
    else:
        dest = Path('public/index.html')

    dest.parent.mkdir(exist_ok=True, parents=True)
    dest.write_text(html_content, encoding='utf-8')
    log.info(f"Saved {len(all_events)} total events to {dest}")

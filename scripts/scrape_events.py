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
    

def scrape_catscradle_events():
    """Fetches and parses events from Cat's Cradle."""
    URL = 'https://catscradle.com/events/'
    headers = {
        'User-Agent': 'concert-feed'
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    event_divs = soup.find_all('div', class_='rhpSingleEvent')

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'June': 6, 'July': 7, 'Aug': 8,
        'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str):
        match = re.search(r'\w{3}, (\w{3,4}) (\d{1,2})', date_str)
        
        if not match:
            logging.error(f"Error matching: {date_str}")
            return datetime.max
        month, day = match.groups()
        year = datetime.now().year
        return datetime(year, month_map.get(month, 1), int(day))

    events = []

    for event in event_divs:
        title = event.select_one('h2')
        link = event.select_one('a.url')
        date_str = event.select_one('.singleEventDate')
        time_details = event.select_one('.rhp-event__time-text--list')
        venue = event.select_one('.rhp-event__venue-text--list')
        image = event.select_one('.eventListImage')
        tickets = event.select_one('.rhp-event-list-cta a')

        event_data = {
            'title': title.text.strip() if title else 'Untitled',
            'link': link['href'] if link and link.has_attr('href') else '#',
            'date_obj': parse_event_date(date_str.text.strip()) if date_str else datetime.max,
            'time': time_details.text.strip() if time_details else '',
            'venue': venue.text.strip() if venue else '',
            'tickets': tickets['href'] if tickets and tickets.has_attr('href') else '',
        }
        events.append(EventInfo(**event_data))

    events.sort(key=lambda e: e.date_obj)
    return events

def scrape_local506_events():
    """Fetches and parses events from Cat's Cradle."""
    URL = 'https://local506.com/events/'
    headers = {
        'User-Agent': 'concert-feed'
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    event_divs = soup.find_all('div', class_='rhpSingleEvent')

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'June': 6, 'July': 7, 'Aug': 8,
        'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str):
        match = re.search(r'\w{3}, (\w{3,4}) (\d{1,2})', date_str)
        if not match:
            logging.error(f"Error matching: {date_str}")
            return datetime.max
        month, day = match.groups()
        year = datetime.now().year
        return datetime(year, month_map.get(month, 1), int(day))

    events = []

    for event in event_divs:
        title = event.select_one('h2')
        link = event.select_one('a.url')
        date_str = event.select_one('.singleEventDate')
        time_details = event.select_one('.rhp-event__time-text--list')
        venue = event.select_one('.rhp-event__venue-text--list')
        image = event.select_one('.eventListImage')
        tickets = event.select_one('.rhp-event-list-cta a')

        event_data = {
            'title': title.text.strip() if title else 'Untitled',
            'link': link['href'] if link and link.has_attr('href') else '#',
            'date_obj': parse_event_date(date_str.text.strip()) if date_str else datetime.max,
            'time': time_details.text.strip() if time_details else '',
            'venue': venue.text.strip() if venue else 'Local 506',
            'tickets': tickets['href'] if tickets and tickets.has_attr('href') else '',
        }

        events.append(EventInfo(**event_data))

    events.sort(key=lambda e: e.date_obj)
    return events


def scrape_ritz_events():
    # If you have the HTML in a file or a string, replace the following line accordingly
    url = 'https://ritzraleigh.com/shows'  # Replace with actual page URL
    html = requests.get(url).text

    soup = BeautifulSoup(html, 'html.parser')

    def parse_event_date(date_str):
        return dt.datetime.strptime(date_str, "%a %b %d, %Y")

    events = []
    for group in soup.find_all('div', class_='chakra-linkbox'):
        try:
            title_tag = group.select_one('p.chakra-text.css-zvlevn')
            date_tag = group.select_one('p.chakra-text.css-aqbsuf')
            link_tag = group.select_one('a.chakra-button.css-1d2qex5')
            event = {
                'title': title_tag.text.strip(),
                'date_obj': parse_event_date(date_tag.text.strip()) if date_tag else datetime.max,
                'tickets': link_tag['href'],
                'venue': "The Ritz Raleigh"
            }

            events.append(EventInfo(**event))
        except Exception as e:
            logging.exception(f"Error parsing event")
    return events


def scrape_fillmore_charlotte() -> list[EventInfo]:
    url = "https://www.fillmorenc.com/shows"
    headers = {
        'User-Agent': 'concert-feed'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    for container in soup.select('div[role="group"].chakra-linkbox'):
        title_tag = container.select_one("p.chakra-text.css-zvlevn")
        date_tag = container.select_one("p.chakra-text.css-lfdvoo")
        link_tag = container.select_one("a[href*='ticketmaster.com']")
        overlay_tag = container.select_one("a.chakra-linkbox__overlay")

        title = title_tag.get_text(strip=True) if title_tag else ""
        date_str = date_tag.get_text(strip=True) if date_tag else ""
        tickets = link_tag['href'] if link_tag else "#"
        link = overlay_tag['href'] if overlay_tag else tickets

        try:
            date_obj = dt.datetime.strptime(date_str, "%a %b %d, %Y")
        except ValueError:
            logging.exception("")
            try:
                date_obj = dt.datetime.strptime(date_str, "%a %b %d %Y")
            except Exception:
                logging.exception("")
                date_obj = dt.datetime.max

        events.append(EventInfo(
            title=title,
            link=link,
            date_obj=date_obj,
            venue="The Fillmore Charlotte",
            tickets=tickets
        ))

    return events


def scrape_motorco_events(url: str = "https://motorcomusic.com/calendar") -> List[EventInfo]:
    """
    Scrape calendar events from Motor Co Music website.
    
    Args:
        url: The URL of the Motor Co Music calendar page
    
    Returns:
        List of EventInfo objects containing event details
    """
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find JavaScript code containing event data
        events = []
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string and 'title:' in script.string and 'start:' in script.string:
                # Extract event data using regex
                event_pattern = r'\{\s*title:\s*[\'"]([^\'"]*)[\'"],\s*start:\s*[\'"]([^\'"]*)[\'"],\s*end:\s*[\'"]([^\'"]*)[\'"],\s*url:\s*[\'"]([^\'"]*)[\'"]'
                matches = re.findall(event_pattern, script.string)
                
                for match in matches:
                    title, start_time, end_time, event_url = match
                    
                    # Parse the start time
                    try:
                        start_dt = dt.datetime.strptime(start_time, '%Y-%m-%d %H:%M')
                        date_str = start_dt.strftime('%Y-%m-%d')
                        time_str = start_dt.strftime('%H:%M')
                    except ValueError:
                        # Fallback parsing if format is different
                        start_dt = dt.datetime.max
                        date_str = start_time
                        time_str = ""
                    
                    # Create EventInfo object
                    event_info = EventInfo(
                        title=title.strip(),
                        link=urljoin(url, event_url),
                        date_obj=start_dt,
                        time=time_str,
                        venue="Motor Co Music",  # Default venue
                        tickets=""  # Could be populated by scraping individual event pages
                    )
                    
                    events.append(event_info)
        
        # If no events found with the above method, try alternative parsing
        if not events:
            events = _alternative_event_parsing(soup, url)
        
        # Sort events by date
        events.sort(key=lambda x: x.date_obj if x.date_obj != dt.datetime.max else dt.datetime.min)
        
        return events
    
    except requests.RequestException as e:
        logging.error(f"Error fetching webpage: {e}")
        return []
    except Exception as e:
        logging.error(f"Error parsing events: {e}")
        return []

def _alternative_event_parsing(soup: BeautifulSoup, base_url: str) -> List[EventInfo]:
    """
    Alternative parsing method in case the primary method fails.
    """
    events = []
    
    # Look for alternative event containers
    event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|calendar'))
    
    for container in event_containers:
        # Extract basic event information
        title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|event'))
        link_elem = container.find('a', href=True)
        date_elem = container.find(['time', 'span'], class_=re.compile(r'date|time'))
        
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = urljoin(base_url, link_elem['href'])
            
            # Try to extract date information
            date_str = ""
            date_obj = dt.datetime.max
            time_str = ""
            
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Try to parse various date formats
                for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
                    try:
                        date_obj = dt.datetime.strptime(date_text, fmt)
                        date_str = date_obj.strftime('%Y-%m-%d')
                        time_str = date_obj.strftime('%H:%M') if '%H:%M' in fmt else ""
                        break
                    except ValueError:
                        continue
            
            event_info = EventInfo(
                title=title,
                link=link,
                date_obj=date_obj,
                time=time_str,
                venue="Motor Co Music",
                tickets=""
            )
            
            events.append(event_info)
    
    return events

def get_event_details(event_url: str) -> dict:
    """
    Scrape additional details from an individual event page.
    
    Args:
        event_url: URL of the specific event page
    
    Returns:
        Dictionary containing additional event details
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract additional details
        details = {
            'description': '',
            'price': '',
            'venue_details': '',
            'tickets_link': ''
        }
        
        # Look for ticket information
        ticket_elem = soup.find('a', href=re.compile(r'ticket|buy'))
        if ticket_elem:
            details['tickets_link'] = ticket_elem.get('href', '')
        
        # Look for price information
        price_elem = soup.find(['span', 'div'], class_=re.compile(r'price|cost'))
        if price_elem:
            details['price'] = price_elem.get_text(strip=True)
        
        return details
    
    except Exception as e:
        logging.error(f"Error getting event details: {e}")
        return {}


def generate_html(events, title="Upcoming Concerts"):
    """Generate HTML content using external template"""
    template_path = Path(__file__).parent / 'template.html'
    
    if not template_path.exists():
        logging.error(f"Template file not found: {template_path}")
        return ""
    
    with template_path.open('r', encoding='utf-8') as f:
        template = f.read()
    
    # Generate venue options
    venues = sorted(set(e.venue for e in events if e.venue))
    venues_options = '\n'.join(f'<option value="{v}">{v}</option>' for v in venues)
    
    # Generate events HTML
    events_html = ""
    for e in events:
        # Don't bother showing past events
        if e.date_obj <= dt.datetime.today() - dt.timedelta(days=1):
            continue

        escaped_title = e.title.replace('"', '&quot;').replace("'", "\\'")
        events_html += f"""
    <div class="event" data-title="{e.title.lower()}" data-venue="{e.venue.lower()}" data-date="{e.date_str}">
      <h2><a href="{e.link}" target="_blank" rel="noopener">{e.title}</a></h2>
      <p class="venue">{e.venue}</p>
      <div class="event-details">
        <span class="date">{e.date_str}</span>
        {f'<span class="time">{e.time}</span>' if e.time else ''}
      </div>
      <div class="event-actions">
        <a class="button" href="{e.tickets}" target="_blank" rel="noopener">Buy Tickets</a>
        <button class="star-button" aria-label="Toggle favorite" onclick="toggleFavoriteFromEvent(this, '{escaped_title}')">☆</button>
      </div>
    </div>
"""
    
    # Replace placeholders in template
    html = template.replace('{{TITLE}}', title)
    html = html.replace('{{VENUES_OPTIONS}}', venues_options)
    html = html.replace('{{EVENTS}}', events_html)
    
    return html


if __name__ == "__main__":
    all_events = []

    # Parse each venue individually and label the source in the venue field
    for scraper in [
            scrape_catscradle_events,
            scrape_ritz_events,
            scrape_fillmore_charlotte,
            scrape_motorco_events,
            scrape_local506_events
    ]:
        try:
            all_events.extend(scraper())
        except Exception as e:
            logging.exception("unhandled exception in parser")

    # Interleave events by date
    all_events.sort(key=lambda e: e.date_obj)

    html_content = generate_html(all_events)

    if '--output' in sys.argv:
        dest = Path(sys.argv[sys.argv.index('--output') + 1])
    else:
        dest = Path('public/index.html')
    dest.parent.mkdir(exist_ok=True, parents=True)
    with dest.open('w', encoding='utf-8') as f:
        f.write(html_content)
    logging.info(f"✅ Saved {len(all_events)} events to {dest}")
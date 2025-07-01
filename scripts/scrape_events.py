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

@dataclass
class EventInfo:
    title: str = ""
    link: str = "#"
    date_str: str = ""
    date_obj: dt.datetime = dt.datetime.max
    time: str = ""
    venue: str = ""
    tickets: str = ""


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
        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str):
        match = re.search(r'\w{3}, (\w{3}) (\d{1,2})', date_str)
        if not match:
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
            'date_str': date_str.text.strip() if date_str else 'TBA',
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
        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def parse_event_date(date_str):
        match = re.search(r'\w{3}, (\w{3}) (\d{1,2})', date_str)
        if not match:
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
            'date_str': date_str.text.strip() if date_str else 'TBA',
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
            link_tag = group.select_one('a.chakra-button[href*="ticketmaster.com"]')
            event = {
                'title': title_tag.text.strip(),
                'date_str': date_tag.text.strip(),
                'date_obj': parse_event_date(date_tag.text.strip()) if date_tag else datetime.max,
                'tickets': link_tag['href'],
                'venue': "The Ritz Raleigh"
            }

            events.append(EventInfo(**event))
        except Exception as e:
            print(f"Error parsing event: {e}")
    return events

def generate_html(events, title="Upcoming Concerts"):
    venues = sorted(set(e.venue for e in events if e.venue))
    venues_options = '\n'.join(f'<option value="{v}">{v}</option>' for v in venues)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{
      font-family: system-ui, sans-serif;
      background: #f4f4f4;
      color: #111;
      margin: 0;
      padding: 2rem;
    }}
    .event {{
      background: #fff;
      padding: 1rem;
      margin-bottom: 1rem;
      border-left: 4px solid #444;
    }}
    .event.favorite {{
      border-color: gold;
      background: #fffbe6;
    }}
    .button {{
      display: inline-block;
      margin-top: 0.5rem;
      padding: 0.4rem 0.8rem;
      background: #222;
      color: #fff;
      border-radius: 3px;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>

  <input type="text" id="search" placeholder="Search events..." />
  <select id="venueFilter">
    <option value="">All Venues</option>
    {venues_options}
  </select>
  <div>
    <input type="text" id="favoriteInput" placeholder="Add favorite keyword..." />
    <button onclick="addFavorite()">Add</button>
    <label><input type="checkbox" id="favoritesOnly" /> Show only favorites</label>
  </div>

  <div id="events">
"""
    for e in events:
        html += f"""
    <div class="event" data-title="{e.title.lower()}" data-venue="{e.venue.lower()}">
      <h2><a href="{e.link}" target="_blank">{e.title}</a></h2>
      <p class="venue">{e.venue}</p>
      <p><strong>Date:</strong> {e.date_str}</p>
      <p><strong>Time:</strong> {e.time}</p>
      <p><a class="button" href="{e.tickets}" target="_blank">Buy Tickets</a></p>
    </div>
"""
    html += """
  </div>
  <script>
    const searchInput = document.getElementById('search');
    const venueSelect = document.getElementById('venueFilter');
    const favoritesOnly = document.getElementById('favoritesOnly');
    const favoriteInput = document.getElementById('favoriteInput');
    const events = document.querySelectorAll('.event');
    let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');

    function saveFavorites() {
      localStorage.setItem('favorites', JSON.stringify(favorites));
    }

    function isFavorite(title) {
      return favorites.some(f => title.includes(f.toLowerCase()));
    }

    function renderEvents() {
      const searchTerm = searchInput.value.toLowerCase();
      const venueFilter = venueSelect.value.toLowerCase();
      const showFavoritesOnly = favoritesOnly.checked;

      events.forEach(event => {
        const title = event.dataset.title;
        const venue = event.dataset.venue;
        const isFav = isFavorite(title);
        event.classList.toggle('favorite', isFav);
        const matches = title.includes(searchTerm) && (venueFilter === '' || venue === venueFilter);
        const visible = matches && (!showFavoritesOnly || isFav);
        event.style.display = visible ? '' : 'none';
      });
    }

    function addFavorite() {
      const keyword = favoriteInput.value.trim().toLowerCase();
      if (keyword && !favorites.includes(keyword)) {
        favorites.push(keyword);
        saveFavorites();
        favoriteInput.value = '';
        renderEvents();
      }
    }

    searchInput.addEventListener('input', renderEvents);
    venueSelect.addEventListener('change', renderEvents);
    favoritesOnly.addEventListener('change', renderEvents);
    window.addEventListener('load', renderEvents);
  </script>
</body>
</html>
"""
    return html






if __name__ == "__main__":
    all_events = []

    # Parse each venue individually and label the source in the venue field
    
    all_events = list(itertools.chain.from_iterable([
        scrape_catscradle_events(),
        scrape_local506_events(),
        scrape_ritz_events()
    ]))

    # Future: Add more venue parsers here
    # other_venue_events = parse_other_venue_events()
    # for e in other_venue_events:
    #     e['venue'] = f"Other Venue – {e['venue']}"
    # all_events.extend(other_venue_events)

    # Interleave events by date
    all_events.sort(key=lambda e: e.date_obj)

    html_content = generate_html(all_events)

    if '--output' in sys.argv:
        dest = Path(sys.argv[sys.argv.index('--output') + 1])
    else:
        dest = Path('public/index.html')
    dest.parent.mkdir(exist_ok=True, parents=True)
    with dest.open('w') as f:
        f.write(html_content)
    print(f"✅ Saved {len(all_events)} events to {dest}")

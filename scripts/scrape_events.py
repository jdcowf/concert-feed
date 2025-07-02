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
            try:
                date_obj = dt.datetime.strptime(date_str, "%a %b %d %Y")
            except Exception:
                date_obj = dt.datetime.max

        events.append(EventInfo(
            title=title,
            link=link,
            date_str=date_str,
            date_obj=date_obj,
            venue="The Fillmore Charlotte",
            tickets=tickets
        ))

    return events


def scrape_motorco_calendar(url="https://motorcomusic.com/calendar/", venue_name="Motorco Music Hall"):
    headers = {"User-Agent": "concert-feed"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # Each date cell has a list of events
    for day_cell in soup.select(".calendar-day"):
        date_header = day_cell.select_one("time")
        date_text = date_header.get("datetime", "").strip()
        # Extract date object
        try:
            date_obj = dt.datetime.fromisoformat(date_text).date()
        except Exception:
            date_obj = dt.date.max

        for ev in day_cell.select("ul li"):
            text = ev.get_text(" ", strip=True)  # e.g., "09:00 PM Daft Disko : A French House & Disco Party"
            parts = text.split(" ", 2)
            time_str = parts[0] + " " + parts[1] if len(parts) >= 2 else ""
            title = parts[2] if len(parts) >= 3 else ev.get_text(strip=True)

            link_tag = ev.select_one("a")
            link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "#"

            event = EventInfo(
                title=title,
                link=link,
                date_str=date_obj.isoformat(),
                date_obj=dt.datetime.combine(date_obj, dt.datetime.min.time()),
                time=time_str,
                venue=venue_name,
                tickets=link
            )
            events.append(event)

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
    h1 {{
      font-size: 1.8rem;
    }}
    #search, #venueFilter {{
      padding: 0.5rem;
      font-size: 1rem;
      margin: 0.5rem 0;
      width: 100%;
      max-width: 400px;
    }}
    .event {{
      background: #fff;
      padding: 1rem;
      margin-bottom: 1rem;
      border-left: 4px solid #444;
      position: relative;
    }}
    .event.favorite {{
      border-color: gold;
      background: #fffbe6;
    }}
    .star-button {{
      position: absolute;
      top: 1rem;
      right: 1rem;
      font-size: 1.5rem;
      cursor: pointer;
      user-select: none;
      color: #ccc;
      transition: color 0.2s ease-in-out;
      border: none;
      background: none;
      padding: 0;
      line-height: 1;
    }}
    .star-button.favorited {{
      color: gold;
      text-shadow: 0 0 3px #daa520;
    }}
    .button {{
      display: inline-block;
      padding: 0.4rem 0.8rem;
      background: #222;
      color: #fff;
      font-size: 0.9rem;
      border-radius: 3px;
      margin-right: 0.5rem;
      cursor: pointer;
      text-decoration: none;
    }}
    .button:hover {{
      background: #444;
    }}
    .settings {{
      background: #fff;
      padding: 1rem;
      border: 1px solid #ccc;
      margin-top: 1rem;
      max-width: 500px;
    }}
    .settings h2 {{
      margin-top: 0;
    }}
    .settings ul {{
      list-style: none;
      padding: 0;
    }}
    .settings li {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 0.25rem 0;
    }}
    .settings input[type="text"] {{
      width: calc(100% - 100px);
    }}
    .settings-toggle {{
      margin-top: 1rem;
      background: #666;
      color: #fff;
      padding: 0.4rem 0.8rem;
      border-radius: 4px;
      cursor: pointer;
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
  <label><input type="checkbox" id="favoritesOnly" /> Show only favorites</label>
  <button class="settings-toggle" onclick="toggleSettings()">⚙️ Favorites Settings</button>

  <div id="settingsPanel" class="settings" style="display:none;">
    <h2>Favorite Keywords</h2>
    <input type="text" id="newFavoriteInput" placeholder="Add new favorite..." />
    <button onclick="addFavorite()">Add</button>
    <ul id="favoritesList"></ul>
    <h3>Import/Export</h3>
    <textarea id="favoritesJson" rows="4" style="width:100%;"></textarea>
    <button onclick="exportFavorites()">Export</button>
    <button onclick="importFavorites()">Import</button>
  </div>

  <div id="events">
"""
    for e in events:
        escaped_title = e.title.replace('"', '&quot;').replace("'", "\\'")
        html += f"""
    <div class="event" data-title="{e.title.lower()}" data-venue="{e.venue.lower()}">
      <h2><a href="{e.link}" target="_blank" rel="noopener">{e.title}</a></h2>
      <p class="venue">{e.venue}</p>
      <p><strong>Date:</strong> {e.date_str}</p>
      <p><strong>Time:</strong> {e.time}</p>
      <p>
        <a class="button" href="{e.tickets}" target="_blank" rel="noopener">Buy Tickets</a>
      </p>
      <button class="star-button" aria-label="Toggle favorite" onclick="toggleFavoriteFromEvent(this, '{escaped_title}')">☆</button>
    </div>
"""
    html += """
  </div>

  <script>
    const searchInput = document.getElementById('search');
    const venueSelect = document.getElementById('venueFilter');
    const favoritesOnly = document.getElementById('favoritesOnly');
    const favoritesList = document.getElementById('favoritesList');
    const newFavoriteInput = document.getElementById('newFavoriteInput');
    const settingsPanel = document.getElementById('settingsPanel');
    const favoritesJson = document.getElementById('favoritesJson');
    const eventsContainer = document.getElementById('events');

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

      const eventElements = Array.from(document.querySelectorAll('.event'));

      // Sort so favorites appear first
      const sorted = eventElements.sort((a, b) => {
        const aFav = isFavorite(a.dataset.title);
        const bFav = isFavorite(b.dataset.title);
        return (aFav === bFav) ? 0 : aFav ? -1 : 1;
      });

      eventsContainer.innerHTML = '';
      sorted.forEach(event => {
        const title = event.dataset.title;
        const venue = event.dataset.venue;
        const isFav = isFavorite(title);
        event.classList.toggle('favorite', isFav);

        // Update star button color
        const starBtn = event.querySelector('.star-button');
        if (starBtn) {
          if (isFav) {
            starBtn.textContent = '★';
            starBtn.classList.add('favorited');
          } else {
            starBtn.textContent = '☆';
            starBtn.classList.remove('favorited');
          }
        }

        const matches = title.includes(searchTerm) && (venueFilter === '' || venue === venueFilter);
        const visible = matches && (!showFavoritesOnly || isFav);
        if (visible) {
          eventsContainer.appendChild(event);
        }
      });
    }

    function addFavorite() {
      const keyword = newFavoriteInput.value.trim().toLowerCase();
      if (keyword && !favorites.includes(keyword)) {
        favorites.push(keyword);
        newFavoriteInput.value = '';
        saveFavorites();
        renderFavoritesList();
        renderEvents();
      }
    }

    function removeFavorite(keyword) {
      favorites = favorites.filter(f => f !== keyword);
      saveFavorites();
      renderFavoritesList();
      renderEvents();
    }

    function renderFavoritesList() {
      favoritesList.innerHTML = '';
      favorites.forEach(fav => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${fav}</span> <button onclick="removeFavorite('${fav}')">Remove</button>`;
        favoritesList.appendChild(li);
      });
    }

    function toggleSettings() {
      settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
    }

    function toggleFavoriteFromEvent(button, title) {
      // Show prompt for substring selection (default full title)
      const substr = prompt("Enter keyword to save as favorite (default: full title):", title);
      if (!substr) return; // canceled

      const cleaned = substr.toLowerCase().trim();
      const isFav = favorites.includes(cleaned);
      if (isFav) {
        // Remove favorite
        favorites = favorites.filter(f => f !== cleaned);
      } else {
        // Add favorite
        favorites.push(cleaned);
      }
      saveFavorites();
      renderFavoritesList();
      renderEvents();
    }

    function exportFavorites() {
      favoritesJson.value = JSON.stringify(favorites, null, 2);
    }

    function importFavorites() {
      try {
        const imported = JSON.parse(favoritesJson.value);
        if (Array.isArray(imported)) {
          favorites = imported.map(f => f.toLowerCase().trim()).filter(Boolean);
          saveFavorites();
          renderFavoritesList();
          renderEvents();
        }
      } catch (e) {
        alert("Invalid JSON");
      }
    }

    searchInput.addEventListener('input', renderEvents);
    venueSelect.addEventListener('change', renderEvents);
    favoritesOnly.addEventListener('change', renderEvents);

    window.addEventListener('load', () => {
      renderFavoritesList();
      renderEvents();
    });
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
        scrape_ritz_events(),
        scrape_fillmore_charlotte(),
        scrape_motorco_calendar(),
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

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
    venues_options = '\n'.join(
        f'<option value="{v}">{v}</option>' for v in venues
    )

    html = html_template = html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Concert Listings</title>
  <style>
    body {{
      font-family: sans-serif;
      background: #f8f9fa;
      color: #222;
    }}
    .event {{
      border: 1px solid #ccc;
      margin: 1em;
      padding: 1em;
      border-radius: 8px;
      position: relative;
      background: white;
    }}
    .event.favorite {{
      border-color: gold;
      background: #fffbe6;
    }}
    .favorite-toggle {{
      position: absolute;
      top: 0.5em;
      right: 0.5em;
      font-size: 1.5em;
      background: none;
      border: none;
      cursor: pointer;
    }}
    #controls {{
      margin: 1em;
    }}
    #controls form {{
      margin-top: 1em;
    }}
    #favorites-list {{
      font-size: 0.9em;
      color: #666;
      margin-top: 0.5em;
    }}
    #importExport {{
      margin-top: 1em;
    }}
  </style>
</head>
<body>
  <div id="controls">
    <label><input type="checkbox" id="showFavoritesOnly"> Show only favorites</label>

    <form id="addFavoriteForm">
      <input type="text" id="manualFavoriteInput" placeholder="Add favorite artist..." required />
      <button type="submit">Add</button>
    </form>

    <div id="importExport">
      <button id="exportFavorites">Export Favorites</button>
      <input type="file" id="importFavorites" accept=".json" />
    </div>

    <div id="favorites-list"></div>
  </div>

  <div id="events">
    {"".join(f'''
    <div class="event" data-title="{e.title}">
      <button class="favorite-toggle" data-title="{e.title}">☆</button>
      <h2>{e.title}</h2>
      <p>{e.date_str}</p>
      <a href="{e.tickets}" target="_blank">Buy Tickets</a>
    </div>''' for e in events)}
  </div>

  <script>
    let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");

    function saveFavorites() {{
      localStorage.setItem("favorites", JSON.stringify(favorites));
    }}

    function renderFavoritesList() {{
      const list = document.getElementById("favorites-list");
      list.textContent = favorites.length ? "Favorites: " + favorites.join(", ") : "No favorites set.";
    }}

    function isFavorite(title) {{
      const lcTitle = title.toLowerCase();
      return favorites.some(fav => lcTitle.includes(fav.toLowerCase()));
    }}

    function renderEvents() {{
      const showOnlyFavorites = document.getElementById("showFavoritesOnly").checked;
      const allEvents = Array.from(document.querySelectorAll(".event"));

      allEvents.forEach(div => {{
        const title = div.dataset.title;
        const matched = isFavorite(title);
        div.classList.toggle("favorite", matched);
        div.style.display = (!showOnlyFavorites || matched) ? "block" : "none";
        div.querySelector(".favorite-toggle").textContent = matched ? "★" : "☆";
      }});
    }}

    function bindFavorites() {{
      document.querySelectorAll(".favorite-toggle").forEach(button => {{
        button.addEventListener("click", () => {{
          const title = button.dataset.title;
          const guess = prompt("Enter a keyword to favorite based on this title:", title);
          if (!guess) return;
          if (!favorites.includes(guess)) {{
            favorites.push(guess);
            saveFavorites();
            renderEvents();
            renderFavoritesList();
          }}
        }});
      }});
    }}

    document.getElementById("showFavoritesOnly").addEventListener("change", renderEvents);

    document.getElementById("addFavoriteForm").addEventListener("submit", (e) => {{
      e.preventDefault();
      const input = document.getElementById("manualFavoriteInput");
      const keyword = input.value.trim();
      if (keyword && !favorites.includes(keyword)) {{
        favorites.push(keyword);
        saveFavorites();
        renderEvents();
        renderFavoritesList();
        input.value = "";
      }}
    }});

    document.getElementById("exportFavorites").addEventListener("click", () => {{
      const blob = new Blob([JSON.stringify(favorites, null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "favorites.json";
      a.click();
      URL.revokeObjectURL(url);
    }});

    document.getElementById("importFavorites").addEventListener("change", (e) => {{
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {{
        try {{
          const imported = JSON.parse(reader.result);
          if (Array.isArray(imported)) {{
            favorites = imported;
            saveFavorites();
            renderEvents();
            renderFavoritesList();
          }} else {{
            alert("Invalid format");
          }}
        }} catch {{
          alert("Invalid JSON file");
        }}
      }};
      reader.readAsText(file);
    }});

    renderEvents();
    renderFavoritesList();
    bindFavorites();
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

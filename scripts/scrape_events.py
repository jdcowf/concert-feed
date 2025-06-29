import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

def parse_catscradle_events():
    """Fetches and parses events from Cat's Cradle."""
    URL = 'https://catscradle.com/events/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
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
            'image': image['src'] if image and image.has_attr('src') else '',
            'tickets': tickets['href'] if tickets and tickets.has_attr('href') else ''
        }

        events.append(event_data)

    events.sort(key=lambda e: e['date_obj'])
    return events


def generate_html(events, title="Upcoming Concerts"):
    venues = sorted(set(e['venue'] for e in events if e['venue']))
    venues_options = '\n'.join(
        f'<option value="{v}">{v}</option>' for v in venues
    )

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
      line-height: 1.5;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 1.2rem;
    }}
    #search, #venueFilter {{
      width: 100%;
      max-width: 400px;
      padding: 0.5rem;
      font-size: 1rem;
      margin-bottom: 1rem;
      border: 1px solid #ccc;
      border-radius: 4px;
    }}
    .event {{
      background: #fff;
      padding: 1rem;
      margin-bottom: 1rem;
      border-left: 4px solid #444;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .event h2 {{
      font-size: 1.25rem;
      margin: 0 0 0.5rem 0;
    }}
    .event .venue {{
      font-weight: bold;
      color: #333;
    }}
    .event p {{
      margin: 0.2rem 0;
    }}
    a {{
      color: #0066cc;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .button {{
      display: inline-block;
      margin-top: 0.5rem;
      padding: 0.4rem 0.8rem;
      background: #222;
      color: #fff;
      text-decoration: none;
      font-size: 0.9rem;
      border-radius: 3px;
    }}
    .button:hover {{
      background: #444;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>

  <input type="text" id="search" placeholder="Search events..." aria-label="Search events" />
  <select id="venueFilter" aria-label="Filter by venue">
    <option value="">All Venues</option>
    {venues_options}
  </select>

  <div id="events">
"""
    for e in events:
        html += f"""
    <div class="event" data-venue="{e['venue'].lower()}">
      <h2><a href="{e['link']}" target="_blank" rel="noopener">{e['title']}</a></h2>
      <p class="venue">{e['venue']}</p>
      <p><strong>Date:</strong> {e['date_str']}</p>
      <p><strong>Time:</strong> {e['time']}</p>
      <p><a class="button" href="{e['tickets']}" target="_blank" rel="noopener">Buy Tickets</a></p>
    </div>
"""
    html += """
  </div>

  <script>
    const searchInput = document.getElementById('search');
    const venueSelect = document.getElementById('venueFilter');
    const events = document.querySelectorAll('.event');

    // Utility: read URL params
    function getUrlParams() {
      return new URLSearchParams(window.location.search);
    }

    // Utility: update URL params without reloading
    function updateUrlParams(params) {
      const newUrl = window.location.pathname + '?' + params.toString();
      history.replaceState(null, '', newUrl);
    }

    function filterEvents() {
      const searchTerm = searchInput.value.toLowerCase();
      const venueFilter = venueSelect.value.toLowerCase();
      events.forEach(event => {
        const text = event.textContent.toLowerCase();
        const venue = event.dataset.venue || '';
        const matchesSearch = text.includes(searchTerm);
        const matchesVenue = venueFilter === '' || venue === venueFilter;
        event.style.display = matchesSearch && matchesVenue ? '' : 'none';
      });

      // Update URL params
      const params = getUrlParams();
      if (searchTerm) {
        params.set('search', searchTerm);
      } else {
        params.delete('search');
      }
      if (venueFilter) {
        params.set('venue', venueFilter);
      } else {
        params.delete('venue');
      }
      updateUrlParams(params);
    }

    // Initialize inputs from URL params on load
    function initFiltersFromUrl() {
      const params = getUrlParams();
      if (params.has('search')) {
        searchInput.value = params.get('search');
      }
      if (params.has('venue')) {
        venueSelect.value = params.get('venue');
      }
      filterEvents();
    }

    searchInput.addEventListener('input', filterEvents);
    venueSelect.addEventListener('change', filterEvents);

    window.addEventListener('load', initFiltersFromUrl);
  </script>

</body>
</html>
"""
    return html





if __name__ == "__main__":
    all_events = []

    # Parse each venue individually and label the source in the venue field
    catscradle_events = parse_catscradle_events()
    for e in catscradle_events:
        e['venue'] = f"Cat’s Cradle – {e['venue']}"  # Expand label
    all_events.extend(catscradle_events)

    # Future: Add more venue parsers here
    # other_venue_events = parse_other_venue_events()
    # for e in other_venue_events:
    #     e['venue'] = f"Other Venue – {e['venue']}"
    # all_events.extend(other_venue_events)

    # Interleave events by date
    all_events.sort(key=lambda e: e['date_obj'])

    html_content = generate_html(all_events)
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f:
        f.write(html_content)
    print(f"✅ Saved {len(all_events)} events to public/index.html")

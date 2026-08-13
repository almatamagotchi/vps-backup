#!/bin/sh
/usr/bin/fetch -q -o /tmp/stanford-events.json 'https://events.stanford.edu/api/2/events?days=30&per_page=20&sort=date&direction=asc' && python3 -c "
import json
with open('/tmp/stanford-events.json', 'r') as f:
    data = json.load(f)
events = data.get('events', [])
out = []
for e in events:
    event = e.get('event', {})
    filters = event.get('filters', {})
    types = [t.get('name','') for t in filters.get('event_types', [])]
    if 'Exhibition' not in types: continue
    out.append({
        'title': event.get('title', ''),
        'location': event.get('location_name', '') or '',
        'first_date': event.get('first_date', ''),
        'last_date': event.get('last_date', ''),
        'url': event.get('url', '')
    })
with open('/usr/local/www/alma/paloalto/stanford-events.json', 'w') as f:
    json.dump(out[:5], f)
" && chown www:www /usr/local/www/alma/paloalto/stanford-events.json

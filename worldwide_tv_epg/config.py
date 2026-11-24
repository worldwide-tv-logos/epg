"""Settings shared by every command. URLs can be changed by environment variables (the public domain, later)."""
import os

# the channel registry published by worldwide-tv-logos/database: channels.json and guides.json
REGISTRY_URL = os.environ.get('EPG_REGISTRY_URL', 'https://worldwide-tv-logos.github.io/database').rstrip('/')
# where the guides are published (used for the links written in index.json)
PUBLIC_URL = os.environ.get('EPG_PUBLIC_URL', 'https://worldwide-tv-logos.github.io/epg').rstrip('/')

PAST_DAYS = 7          # days kept before today (the sources do not give them back: they come from the archives)
FUTURE_DAYS = 7        # days published after today
MIN_SCORE = 0.9        # a guide ID of guides.json maps to a channel only from this score
SIZE_ALERT = 900 * 1024 * 1024   # GitHub Pages sites are limited to 1 GB
USER_AGENT = 'worldwide-tv-epg (+https://github.com/worldwide-tv-logos/epg)'
PAUSE = 2.0            # seconds between two downloads of the same run

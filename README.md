# supybot-soccer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Plugin for Supybot/Limnoria to display soccer (football!) scores. The main code
is in [`plugin.py`](plugin.py).

This plugin was primarily written for use in #soccer on EFnet. Contributions are
welcome!

## Installation

1. Clone the repository to your `~/.supybot/plugins` directory (note that the
   case is important):

        git clone https://github.com/paultownsend/supybot-soccer ~/.supybot/plugins/Soccer

2. Activate your virtual environment, if necessary, and install the
   requirements:

        pip3 install -r ~/.supybot/plugins/Soccer/requirements.txt

3. Tell your bot to load the plugin:

        .load soccer

## Commands

- `.soccer -l`: List all available competitions.
- `.soccer -t <competition>`: Show the current table for a competition/league,
  e.g. `.soccer -t epl`.
- `.soccer <competition>`: List the fixtures/scores/results for `<competition>`,
  e.g. `.soccer epl`.
- `.soccer <team>`: List the fixtures/scores/results for `<team>`, e.g. `.soccer
  everton`.

## Adding new competitions

Competition data is stored in [`competitions.json`](competitions.json) with the
following structure:
```json
{
    "epl": {
        "id": "eng.1",
        "name": "English Premier League"
    }
}
```

In this example:
- `epl` is what the user will reference as `<competition>` when querying the bot.
- `eng.1` is the slug used by ESPN to identify this competition.
- `English Premier League` is the friendly name to display when listing all
  available competitions with `.soccer -l`.

To add a new competition you just need to find the slug to use and add a new
object to `competitions.json`. Finding the slug is as simple as going to
https://www.espn.co.uk/football/competitions, clicking on the relevant
league/competition, and noting the end part of the URL. For example:
- Italian Serie A (**ita.1**): http://www.espn.co.uk/football/league/_/name/ita.1
- Dutch Eredivisie (**ned.1**): http://www.espn.co.uk/football/league/_/name/ned.1
- FIFA World Cup Qualifying - UEFA (**fifa.worldq.uefa**): http://www.espn.co.uk/football/league/_/name/fifa.worldq.uefa

## Note on data sources

All data is pulled from ESPN via an undocumented API that's exposed via their
website. API URLs and structures have been discovered via browser tools, general
poking around, and scrolling through lots of JSON data.

There's also some useful information in this Gist and the comments: [ESPN's
hidden API endpoints](https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b).
I would **highly** recommend the
[JSONView](https://chrome.google.com/webstore/detail/jsonview/chklaanhfefbnpoihckbnefhakgolnmc)
extension for Chrome if you want to take a look around and make sense of the
data structures.

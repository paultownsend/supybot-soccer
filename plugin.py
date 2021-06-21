import json
import os
import time

import pendulum
import requests
from supybot import callbacks, ircutils
from supybot.commands import getopts, optional, wrap

# fmt: off
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/soccer/{slug}/standings"
# fmt: on


class Soccer(callbacks.Plugin):
    """Fetches soccer fixtures, scores, etc."""

    def __init__(self, irc):
        self.__parent = super(Soccer, self)
        self.__parent.__init__(irc)
        self.competitions = self.load_json("competitions.json")

    @wrap(
        [
            getopts({"l": "", "t": "text"}),
            optional("text"),
        ]
    )
    def soccer(self, irc, msg, args, optlist, query):
        """[-l] [-t <competition>] [<team|competition>]
        Use -l to list available competitions."""

        for opt, arg in optlist:
            if type(arg) is str:
                arg = arg.lower()

            if opt == "l":
                competitions = self.competition_list()
                self.say(irc, competitions, separator=", ")
            elif opt == "t":
                if self.valid_competition(arg):
                    id = self.competitions[arg]["id"]
                    table = self.format_table(id)
                    self.say(irc, table, separator=", ")
                else:
                    self.error(
                        irc,
                        f"{ircutils.bold(arg)} is not a valid competition. Use {ircutils.bold('.soccer -l')} to list available competitions.",
                    )

        if query:
            query = query.lower()
            if self.valid_competition(query):
                competition = self.competitions[query]["id"]
                results = self.get_match_data(competition)
            else:
                results = self.get_match_data("all", query)

            if len(results) > 0:
                self.say(irc, results, separator=" | ")
            else:
                self.error(irc, "No teams found matching query.")

    def load_json(self, file):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, file)) as f:
            data = json.load(f)
        return data

    # TODO: handle exceptions thrown by requests.
    def get_data(self, url, no_cache=True):
        """Gets data from the API. Setting no_cache will append a timestamp to
        the URL to force fresh data."""
        if no_cache:
            url = url + "?" + str(time.time())
        r = requests.get(url, timeout=(6.05, 3.0))
        if r.status_code == requests.codes.ok:
            return r.json()

    def reply(self, irc, msg):
        irc.reply(msg, prefixNick=False, noLengthCheck=True)

    def error(self, irc, msg):
        self.reply(irc, f"Error: {msg}")

    def say(self, irc, content, separator):
        """Outputs a reply that's spread over multiple lines if necessary,
        with no breaks in the middle of information."""
        max_length = 400
        message = []
        if (sum(len(item) for item in content)) >= max_length:
            for item in content:
                if ((sum(len(m) for m in message)) + len(item)) <= max_length:
                    message.append(item)
                else:
                    self.reply(irc, separator.join(message))
                    message.clear()
                    message.append(item)
            self.reply(irc, separator.join(message))
        else:
            self.reply(irc, separator.join(content))

    def valid_competition(self, competition):
        """Checks if the chosen competition is a valid one."""
        if competition in self.competitions.keys():
            return True

    def competition_list(self):
        """Returns a formatted list of competitions."""
        competitions = []
        for competition in sorted(self.competitions.keys()):
            key = ircutils.bold(competition)
            name = self.competitions[competition]["name"]
            competitions.append(f"{key} ({name})")
        return competitions

    def get_match_data(self, competition, query=None):
        """Gets match data from API and compiles into a dictionary, which is
        then formatted appropriately and pushed into an array for say()."""
        data = self.get_data(SCOREBOARD_URL.format(slug=competition))
        match = {}
        formatted_data = []

        for event in data["events"]:
            match = {
                "game_id": event["competitions"][0]["id"],
                "status": event["competitions"][0]["status"]["type"]["name"],
                "kick_off": event["date"],
                "clock": event["competitions"][0]["status"]["displayClock"],
                "home_team": event["competitions"][0]["competitors"][0]["team"]["name"],
                "home_team_goals": int(
                    event["competitions"][0]["competitors"][0]["score"]
                ),
                "home_team_agg": int(
                    event["competitions"][0]["competitors"][0].get("aggregateScore", -1)
                ),
                "home_team_pens": int(
                    event["competitions"][0]["competitors"][0].get("shootoutScore", -1)
                ),
                "away_team": event["competitions"][0]["competitors"][1]["team"]["name"],
                "away_team_goals": int(
                    event["competitions"][0]["competitors"][1]["score"]
                ),
                "away_team_agg": int(
                    event["competitions"][0]["competitors"][1].get("aggregateScore", -1)
                ),
                "away_team_pens": int(
                    event["competitions"][0]["competitors"][1].get("shootoutScore", -1)
                ),
            }

            if query:
                query = query.lower()
                if (
                    query in match["home_team"].lower()
                    or query in match["away_team"].lower()
                ):
                    formatted_data.append(
                        f"{self.format_match_time(match)} {self.format_match_status(match)}"
                    )
                    # First match is usually the one we want so break the loop
                    # and return.
                    break
            else:
                # No query means this is a competition/league lookup with
                # multiple results. Add to the array and keep loopin'.
                formatted_data.append(
                    f"{self.format_match_time(match)} {self.format_match_status(match)}"
                )

        return formatted_data

    def format_match_time(self, match):
        """Returns kick off time, time on the clock, or
        half-time/full-time/etc. status."""
        if match["status"] == "STATUS_SCHEDULED":
            time = pendulum.parse(match["kick_off"])
            if time.day == pendulum.now("UTC").day:
                time = time.strftime("%-l:%M%p")
            elif time.week_of_year == pendulum.now("UTC").week_of_year:
                time = time.strftime("%a @ %-l:%M%p")
            else:
                time = time.strftime("%a %-d %b @ %-l:%M%p")
        elif match["status"] in (
            "STATUS_ABANDONED",
            "STATUS_CANCELED",
            "STATUS_DELAYED",
            "STATUS_POSTPONED",
        ):
            time = ircutils.mircColor("PP", "yellow")
        elif match["status"] in (
            "STATUS_IN_PROGRESS",
            "STATUS_FIRST_HALF",
            "STATUS_SECOND_HALF",
            "STATUS_OVERTIME",
        ):
            time = ircutils.mircColor(match["clock"], "green")
        elif match["status"] == "STATUS_HALFTIME":
            time = ircutils.mircColor("HT", "yellow")
        elif match["status"] == "STATUS_HALFTIME_ET":
            time = ircutils.mircColor("ET-HT", "yellow")
        elif match["status"] in ("STATUS_END_OF_REGULATION", "STATUS_FULL_TIME"):
            time = ircutils.mircColor("FT", "red")
        elif match["status"] == "STATUS_FINAL_AET":
            time = ircutils.mircColor("AET", "red")
        elif match["status"] == ("STATUS_END_OF_EXTRATIME", "STATUS_SHOOTOUT"):
            time = ircutils.mircColor("Pens", "green")
        elif match["status"] == "STATUS_FINAL_PEN":
            time = ircutils.mircColor("FT-Pens", "red")
        else:
            # We're flying blind with this API, so if no matches are found
            # let's just output the raw string (STATUS_FOO) so we can add it to
            # the list.
            time = match["status"]
        return time

    def format_match_status(self, match):
        """Returns a formatted string with the match status - who's playing
        who, what the score is, etc."""
        if match["status"] in (
            "STATUS_SCHEDULED",
            "STATUS_ABANDONED",
            "STATUS_CANCELED",
            "STATUS_DELAYED",
            "STATUS_POSTPONED",
        ):
            status = f"{match['home_team']} v {match['away_team']}"
        elif match["status"] in ("STATUS_SHOOTOUT", "STATUS_FINAL_PEN"):
            if match["home_team_pens"] > match["away_team_pens"]:
                match["home_team"] = ircutils.bold(match["home_team"])
                match["home_team_pens"] = ircutils.bold(match["home_team_pens"])
            elif match["away_team_pens"] > match["home_team_pens"]:
                match["away_team"] = ircutils.bold(match["away_team"])
                match["away_team_pens"] = ircutils.bold(match["away_team_pens"])
            status = (
                f"{match['home_team']} {match['home_team_goals']}({match['home_team_pens']})-"
                f"{match['away_team_goals']}({match['away_team_pens']}) {match['away_team']}"
            )
        else:
            if match["home_team_goals"] > match["away_team_goals"]:
                match["home_team"] = ircutils.bold(match["home_team"])
                match["home_team_goals"] = ircutils.bold(match["home_team_goals"])
            elif match["away_team_goals"] > match["home_team_goals"]:
                match["away_team"] = ircutils.bold(match["away_team"])
                match["away_team_goals"] = ircutils.bold(match["away_team_goals"])
            status = (
                f"{match['home_team']} {match['home_team_goals']}-"
                f"{match['away_team_goals']} {match['away_team']}"
            )
        return status

    def format_table(self, competition):
        """Returns a list with an ordered league table containing games played,
        goal difference, and points total."""
        data = self.get_data(
            "https://site.api.espn.com/apis/v2/sports/soccer/"
            + competition
            + "/standings"
        )
        table = []

        for entry in data["children"][0]["standings"]["entries"]:
            position = entry["stats"][8]["displayValue"]
            team = entry["team"]["displayName"]
            games_played = entry["stats"][3]["displayValue"]
            goal_difference = entry["stats"][9]["displayValue"]
            if goal_difference[0] == "+":
                goal_difference = ircutils.mircColor(goal_difference, "green")
            elif goal_difference[0] == "-":
                goal_difference = ircutils.mircColor(goal_difference, "red")
            points = entry["stats"][6]["displayValue"]
            table.append(
                f"{ircutils.bold(position)}. {team} ({games_played}|{goal_difference}|{points})"
            )
        return table


Class = Soccer

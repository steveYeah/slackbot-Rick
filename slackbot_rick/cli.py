# -*- coding: utf-8 -*-

import datetime
import os
import random
import re
import time

from github import Github

from slackclient import SlackClient


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

GITHUB_ORG = os.environ.get("GITHUB_ORG")

MAX_PR_AGE = int(os.environ.get("MAX_PR_AGE", "172800"))

BOT_ID = os.environ.get("BOT_ID")

AT_BOT = "<@" + BOT_ID + ">"

slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))


WEIRD_MADEUP_SOUNDING_CATCHPHRASES = [
    'wubba lubba dub dub',
    'Ricky ticky taffy beeeeeartch!',
    'And that\'s the waaaaaaaay the news goes!',
    'Hit the sack, Jack',
    'Uh ohhhh! Somersoult jump',
    'AIDS!',
    'And that\'s why I always say, Shumshumschilpiddydah!',
    'GRASSSSS... tastes bad!',
    'No jumping in the sewer!',
    'BURGERTIME!',
    'Lick, lick, lick, my BALLS!',
]


def random_catchphrase():
    return random.choice(WEIRD_MADEUP_SOUNDING_CATCHPHRASES)


def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return "{} days {} h {} mins".format(days, hours, minutes)
    elif hours > 0:
        return "{} h {} mins".format(hours, minutes)
    elif minutes > 0:
        return "{} mins".format(minutes)
    return "{} s".format(seconds)


def get_prs(repo_name):
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_organization(GITHUB_ORG).get_repo(repo_name)
    now = datetime.datetime.now()
    return [
        (pr, now - pr.created_at)
        for pr in repo.get_pulls(state="open", sort="created")
    ]


def format_pr(data, age):
    age_seconds = age.total_seconds()
    desc = "<{}|{}> by {} (created {} ago)".format(
        data.html_url,
        data.head.label,
        data.user.name or data.user.login,
        pretty_time_delta(age_seconds)
    )
    if age_seconds > MAX_PR_AGE:
        return ":fire: {}".format(desc)
    return desc


def prs(channel, repo_name):
    slack_client.api_call(
            "chat.postMessage", channel=channel, text="Wait for the ramp Morty, they love the slow ramp..", as_user=True
    )
    prs = get_prs(repo_name)
    prs.sort(key=lambda e: e[1].total_seconds())
    response = "\n".join(format_pr(pr[0], pr[1]) for pr in prs)
    slack_client.api_call(
        "chat.postMessage", channel=channel, text=response, as_user=True
    )


def get_release(pr_label):
    _, name = pr_label.split(':')
    parts = name.split('/')
    if len(parts) < 2:
        return None
    tag, desc = parts
    if tag != 'release':
        return None
    return desc


def releases(channel, repo_name):
    slack_client.api_call(
        "chat.postMessage", channel=channel, text="All in good time <blurrp>..", as_user=True
    )

    minors, hotfixes = [], []
    for pr, age in get_prs(repo_name):
        ver = get_release(pr.head.label)
        if ver is None:
            continue
        _, minor, hotfix = ver[1:].split('.')
        if minor != '0':
            minors.append((pr, age))
        else:
            hotfixes.append((pr, age))

    if not minors and not hotfixes:
        slack_client.api_call(
            "chat.postMessage", channel=channel, text="No releases going on", as_user=True
        )
        return

    response_lines = []

    if minors:
        response_lines.append("Releases:\n")
        response_lines.append("\n".join(format_pr(pr[0], pr[1]) for pr in minors))
    if hotfixes:
        response_lines.append("Hotfixes:\n")
        response_lines.append("\n".join(format_pr(pr[0], pr[1]) for pr in hotfixes))

    response = "\n".join(response_lines)
    slack_client.api_call(
        "chat.postMessage", channel=channel, text=response, as_user=True
    )

COMMANDS = {
    "prs": prs,
    "releases": releases,
}


def handle_command(command, channel):
    """
    Receives commands directed at Rick and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
    """
    print(command, channel)
    cmd, *args = [s.strip() for s in command.split(" ") if s.strip()]
    impl = COMMANDS.get(cmd)
    if impl is None:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=random_catchphrase(),
            as_user=True
        )
        return
    impl(channel, *args)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if not output:
                continue
            text = output.get('text', '').strip()
            if text.startswith(AT_BOT):
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']

            text = text.lower()
    return None, None


def main():
    if slack_client.rtm_connect():
        print("I'm Slackbot Riiiiick!!!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

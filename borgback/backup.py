import itertools
import logging
import subprocess

from datetime import datetime
from datetime import timedelta
from json import loads
from pathlib import Path
from sys import argv
from time import sleep

from dateutil.parser import parse
from toml import load as toml_load
from xdg import XDG_CONFIG_HOME


def get_conf():
    """Load the borgback configuration from a filename."""
    conf_path = Path(XDG_CONFIG_HOME) / "borgback.toml"
    with conf_path.open() as fd:
        conf = toml_load(fd)

    # Infer full repository path
    conf["backup"]["full_name"] = conf["borg"]["repository"] + "::" + conf["backup"]["name"]

    # Convert types
    conf["schedule"]["backup_interval"] = timedelta(minutes=conf["schedule"]["backup_interval"])
    conf["schedule"]["retry_interval"] = timedelta(minutes=conf["schedule"]["retry_interval"])

    return conf


def backup(conf):
    """Make a backup"""
    logging.debug("Preparing to backup")

    # Get configuration
    borg_path = conf["borg"]["local_path"]
    borg_repo = conf["borg"]["repository"]
    backup_name = conf["backup"]["full_name"]
    backup_dirs = conf["backup"]["directories"]
    backup_exclude = conf["backup"]["exclude"]

    try:
        create_cmd = [borg_path, 'create'] \
                     + _intersperse('--exclude', backup_exclude) \
                     + [backup_name] \
                     + backup_dirs
        subprocess.run(create_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as err:
        logging.error("Failed to make backup.")
        raise err

    else:
        notify("Backup done.")
        logging.info("Backup done.")


def last_backup(conf):
    """Retrieve datetime of last backup"""
    borg_path = conf["borg"]["local_path"]
    borg_repo = conf["borg"]["repository"]

    try:
        last = subprocess.run(
            [borg_path, 'list', '--last', '1', '--json', borg_repo],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as err:
        logging.error("Failed to retrieve last backup info.")
        raise err

    else:
        last = loads(last.stdout.decode('utf-8'))
        time = last['archives'][-1]['time']
        return parse(time)


def notify(message):
    """Send a notification to Gnome."""
    try:
        subprocess.run(
            ["notify-send", message],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as err:
        logging.warning("Failed to display notification.")


def _intersperse(elem, xs):
    """Return a list like: [elem, xs[0], elem, xs[1], elem, xs[2], ...]"""
    return list(itertools.chain(*zip(itertools.repeat(elem), xs)))


def schedule():
    """Does a backup now if needed, or sleep until next backup time."""
    # Load configuration
    try:
        conf = get_conf()
    except FileNotFoundError as err:
        logging.error("Failed to load configuration file, exiting.")
        exit(1)

    backup_interval = conf["schedule"]["backup_interval"]
    retry_interval = conf["schedule"]["retry_interval"]

    # Check if a backup is needed now, otherwise wait until it is time to do so.
    retry_in = retry_interval
    try:
        delta = datetime.now() - last_backup(conf)
        if delta > backup_interval:
            logging.info("Time to backup!")
            backup(conf)
            retry_in = backup_interval
        else:
            logging.info("Not a time to backup. Time since last backup: {} < {}."
                          .format(delta, backup_interval))
            retry_in = backup_interval - delta

    except subprocess.CalledProcessError as err:
        logging.error("Got an error while trying to backup: {}. Retrying in {}."
                      .format(err.stderr, retry_in))

    finally:
        logging.debug("Sleeping for {}.".format(retry_in))
        sleep(retry_in / timedelta(seconds=1))

def main():
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.DEBUG if "--debug" in argv else logging.INFO)

    while True:
        schedule()  # schedule() is in charge of making calls to time.sleep()

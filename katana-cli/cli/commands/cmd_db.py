import os
import requests
import json
import yaml
import subprocess

import click


@click.group()
def cli():
    """Manage MongoDB"""
    pass


@click.command()
def init():
    """
    Init database
    """

    url = "http://localhost:8000/api/db"
    r = None
    try:
        r = requests.post(url, timeout=3)
        r.raise_for_status()

        click.echo(r.content)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Error:", err)


cli.add_command(init)

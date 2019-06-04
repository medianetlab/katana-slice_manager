import os
import requests
import json
import yaml
import subprocess

import click
import datetime


@click.group()
def cli():
    """Manage NFVOs"""
    pass


@click.command()
def ls():
    """
    List nfvos
    """

    url = "http://localhost:8000/api/nfvo"
    r = None
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        json_data = json.loads(r.content)
        # indent=2 "beautifies" json
        #click.echo(json.dumps(json_data, indent=2))
        print(console_formatter("NFVO_ID", "CREATED AT", "TYPE"))
        for i in range(len(json_data)):
            print(console_formatter(
                json_data[i]["_id"],
                datetime.datetime.fromtimestamp(json_data[i]["created_at"]).strftime('%Y-%m-%d %H:%M:%S'),
                json_data[i]["type"]
                )
            )
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Error:", err)


@click.command()
@click.argument('id')
def inspect(id):
    """
    Display detailed information of NFVO
    """
    url = "http://localhost:8000/api/nfvo/"+id
    r = None
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        json_data = json.loads(r.content)
        # indent=2 "beautifies" json
        click.echo(json.dumps(json_data, indent=2))
        if not json_data:
            click.echo("Error: No such nfvo: {}".format(id))
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Error:", err)


@click.command()
@click.option('-f', '--file', required=True, type=str, help='yaml file with NFVO details')
def add(file):
    """
    Add new NFVO
    """
    with open(file, 'r') as stream:
        data = yaml.load(stream)

    url = "http://localhost:8000/api/nfvo"
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=10)
        r.raise_for_status()

        click.echo(r.content)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
        click.echo(r.content)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Error:", err)


@click.command()
@click.argument('id')
def rm(id):
    """
    Remove NFVO
    """
    url = "http://localhost:8000/api/nfvo/"+id
    r = None
    try:
        r = requests.delete(url, timeout=3)
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


@click.command()
@click.option('-f', '--file', required=True, type=str, help='yaml file with NFVO details')
@click.argument('id')
def update(file, id):
    """
    Update NFVO
    """
    with open(file, 'r') as stream:
        data = yaml.load(stream)

    url = "http://localhost:8000/api/nfvo/"+id
    r = None
    try:
        r = requests.put(url, json=json.loads(json.dumps(data)), timeout=3)
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


cli.add_command(ls)
cli.add_command(inspect)
cli.add_command(add)
cli.add_command(rm)
cli.add_command(update)


def console_formatter(uuid,created_at,nfvotype):
    return '{0: <40}{1: <25}{2: <20}'.format(
        uuid,
        created_at,
        nfvotype
    )
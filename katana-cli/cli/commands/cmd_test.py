import os
import subprocess

import click


@click.group()
def cli():
    """
    Used for test commands
    """
    pass



@click.command()
@click.argument('name')
def hi(name):
    """
    says hi to the NAME provided
    """

    cmd = 'echo Hi {0}!'.format(name)
    return subprocess.call(cmd, shell=True)


@click.command()
def slice():
    """
    Tries to create a slice
    """

@click.command()
def cleanup():
    """
    Tries to cleanup the slice
    """

cli.add_command(hi)
cli.add_command(slice)
cli.add_command(cleanup)

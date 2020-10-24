import click

from src.utils import bcolors


def _echo(pre, msg, *args):
    if args:
        msg = "%s %s" % (msg, " ".join(args))
    click.echo("%s%s%s" % (pre, msg, bcolors.ENDC))


def info(msg: str, *args):
    if args:
        msg = "%s %s" % (msg, " ".join(args))
    click.echo(msg)


def blod(msg: str, *args):
    _echo(bcolors.Bold, msg, *args)


def binfo(msg: str, *args):
    _echo(bcolors.Blue, msg, *args)


def succ(msg: str, *args):
    _echo(bcolors.Green, msg, *args)


def tips(msg: str, *args):
    _echo(bcolors.Purple, msg, *args)


def warn(msg: str, *args):
    _echo(bcolors.Yellow, msg, *args)


def fail(msg: str, *args):
    _echo(bcolors.Red, msg, *args)

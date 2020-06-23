# -*- coding: utf-8 -*-
__author__ = "@buzz"

import json
import os

import click

from .core import ComponentManager, ComponentSniffer
from .log import setup_logger
from .utils import bcolors


# register main group
main_cmd_group = click.group('main')(lambda: None)


@main_cmd_group.command("scan")
@click.option("-u", "--url", type=click.STRING, help="Target", required=True)
@click.option("-d", "--directory", default=os.path.join(os.getcwd(), "components"), help="Components directory, default ./components")
# request
@click.option("-a", "--aggression", is_flag=True, default=False, help="Open aggression mode")
@click.option("-U", "--user-agent", type=click.STRING, help="Custom user agent")
@click.option("-H", "--header", multiple=True, help="Pass custom header LINE to serve")
@click.option("--disallow-redirect", is_flag=True, default=False, help="Disallow redirect")
# component
@click.option("-c", "--component", multiple=True, help="Specify component")
# max-threads
@click.option("-t", "--max-threads", type=click.INT, default=8, help="Set the maximum number of threads")
# proxy
@click.option("--proxy", type=click.STRING, help="Set proxy is like: '[HTTP/SOCKS4/SOCKS5]/[username]@[password]/[addr]:[port]' ")
@click.option("--proxy_rdns", is_flag=True, default=False, help="Proxy uses rdns")
# verbose
@click.option("-v", "--verbose", is_flag=True, default=False, help="Output detailed debugging information")
def component_sniffer(url, directory, aggression, user_agent, header, disallow_redirect, component, max_threads, proxy, proxy_rdns, verbose):
    """Component scanning on the target"""
    setup_logger(verbose)

    sniffer = ComponentSniffer(url, directory)
    sniffer.aggression = aggression
    sniffer.max_threads = max_threads
    if header:
        sniffer.headers = header
    if user_agent:
        sniffer.user_agent = user_agent
    if proxy:
        sniffer.set_proxy(proxy, proxy_rdns)
    if disallow_redirect:
        sniffer.allow_redirect = not disallow_redirect

    if component:
        results = sniffer.test(component)
    else:
        results = sniffer.start()
    click.echo(bcolors.OKGREEN+json.dumps(results,
                                          ensure_ascii=False)+bcolors.ENDC)


@main_cmd_group.command("manage")
@click.option("-d", "--directory", default=os.path.join(os.getcwd(), "components"), help="Components directory, default ./components")
# list
@click.option("-l", "--list", is_flag=True, default=False, help="List components")
# pull
@click.option("--pull", is_flag=True, default=False, help="Pull custom components from remote database")
@click.option("--pull_webanalyzer", is_flag=True, default=False, help="Pull custom components from remote database")
# sync
@click.option("--sync", is_flag=True, default=False, help="Synchronize to remote database")
@click.option("--sync-updating", is_flag=True, default=False, help="Update existing components when synchronizing to remote database")
@click.option("--host", type=click.STRING, default="127.0.0.1", help="MySQL database host")
@click.option("--port", type=click.INT, default=3306, help="MySQL database port")
@click.option("--db", type=click.STRING, help="MySQL database name")
@click.option("--user", type=click.STRING, help="MySQL database user")
@click.option("--passwd", type=click.STRING, help="MySQL database password")
# search
@click.option("--search", multiple=True, help="Search component name")
# verbose
@click.option("-v", "--verbose", is_flag=True, default=False, help="Output detailed debugging information")
def component_manager(directory, list, pull, pull_webanalyzer, sync, host, port, db, user, passwd, sync_updating, search, verbose):
    """Management components"""
    setup_logger(verbose)

    manager = ComponentManager(directory)
    if list:
        manager.lists()
        return
    elif pull_webanalyzer:
        manager.pull_from_webanalyzer()
    elif pull:
        if db and user and passwd:
            manager.pull_from_remote_database(db, user, passwd, host, port)
            return
        click.echo("%sPull component need 'db','user','passwd'.%s" %
                   (bcolors.FAIL, bcolors.ENDC))
    elif sync:
        if db and user and passwd:
            manager.sync(db, user, passwd, host, port, sync_updating)
            return
        click.echo("%sSync component need 'db','user','passwd'.%s" %
                   (bcolors.FAIL, bcolors.ENDC))
        return
    elif search:
        manager.search(search)
    else:
        click.echo("%sNo Action.%s" %
                   (bcolors.HEADER, bcolors.ENDC))


if __name__ == "__main__":
    main_cmd_group()

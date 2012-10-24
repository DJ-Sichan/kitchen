"""Dashboard app views"""
import os
import time

from django.contrib.messages import add_message, ERROR, WARNING
from django.shortcuts import render_to_response
from django.template import RequestContext
from logbook import Logger

from kitchen.dashboard.chef import (get_nodes_extended, get_roles,
                                    get_role_groups, get_environments,
                                    filter_nodes, group_nodes_by_host,
                                    get_nodes, RepoError)
from kitchen.dashboard import graphs
from kitchen.settings import (REPO, SHOW_VIRT_VIEW, SHOW_HOST_NAMES,
                              SYNCDATE_FILE)

log = Logger(__name__)


def _get_data(env, roles, virt):
    """Returns processed repository data, filtering nodes based on given args
    """
    data = {'filter_env': env, 'filter_roles': roles, 'filter_virt': virt}
    nodes = get_nodes_extended()
    data['roles'] = get_roles()
    roles_groups = get_role_groups(data['roles'])
    data['roles_groups'] = roles_groups
    data['virt_roles'] = ['host', 'guest']
    # Get environments before we filter nodes
    data['environments'] = get_environments(nodes)
    if data['filter_env'] or data['filter_roles'] or data['filter_virt']:
        nodes = filter_nodes(nodes, data['filter_env'],
                             data['filter_roles'], data['filter_virt'])
    data['nodes'] = nodes
    return data


def _show_repo_sync_date(request):
    """Shows the sync date, which will be the modified date of a file"""
    try:
        sync_age = (time.time() - os.stat(SYNCDATE_FILE).st_mtime) / 60
    except OSError:
        add_message(request, ERROR, "There have been errors while "
                                    "syncing the repo")
    else:
        sync_lim = REPO['SYNC_PERIOD'] * 2.5
        if sync_age > sync_lim:
            add_message(request, WARNING, "The {0} repo is getting out of "
                        "sync. Last pull was {1} minutes "
                        "ago.".format(REPO['NAME'], int(sync_age)))


def _set_options(options):
    """Sets default options if none are given"""
    if options is None:
        # Set defaults
        options = ''
        if SHOW_HOST_NAMES:
            options += 'show_hostnames,'
    return options


def main(request):
    """Default main view showing a list of nodes"""
    data = {}
    try:
        data = _get_data(request.GET.get('env', REPO['DEFAULT_ENV']),
                         request.GET.get('roles', ''),
                         request.GET.get('virt', REPO['DEFAULT_VIRT']))
        _show_repo_sync_date(request)
    except RepoError as e:
        add_message(request, ERROR, str(e))
    if not len(data.get('nodes', [])):
        add_message(request, WARNING,
                    "There are no nodes that fit the supplied criteria.")
    data['show_virt'] = SHOW_VIRT_VIEW
    data['query_string'] = request.META['QUERY_STRING']
    data['nodes_simple'] = get_nodes()
    return render_to_response('main.html',
                              data, context_instance=RequestContext(request))


def virt(request):
    """Displays a view where the nodes are grouped by physical host"""
    data = {}
    try:
        roles = request.GET.get('roles', '')
        data = _get_data(request.GET.get('env', REPO['DEFAULT_ENV']),
                         '',
                         request.GET.get('virt', None))
    except RepoError as e:
        add_message(request, ERROR, str(e))
    else:
        data['nodes'] = group_nodes_by_host(data['nodes'],
                                            roles=roles)
        data['filter_roles'] = roles
        if not len(data.get('nodes', [])):
            add_message(request, WARNING,
                        "There are no nodes that fit the supplied criteria.")
    data['query_string'] = request.META['QUERY_STRING']
    return render_to_response('virt.html',
                              data, context_instance=RequestContext(request))


def graph(request):
    """Graph view where users can visualize graphs of their nodes
    generated using Graphviz open source graph visualization library

    """
    options = _set_options(request.GET.get('options'))
    data = {}
    env_filter = request.GET.get('env', REPO['DEFAULT_ENV'])
    try:
        data = _get_data(env_filter, request.GET.get('roles', ''), 'guest')
    except RepoError as e:
        add_message(request, ERROR, str(e))
    else:
        if env_filter:
            success, msg = graphs.generate_node_map(data['nodes'],
                                                    data.get('roles', []),
                                                    'show_hostnames' in options)
            if not success:
                add_message(request, ERROR, msg)
        else:
            add_message(request, WARNING, "Please select an environment")

    data['show_hostnames'] = 'show_hostnames' in options
    data['query_string'] = request.META['QUERY_STRING']
    return render_to_response('graph.html',
                              data, context_instance=RequestContext(request))

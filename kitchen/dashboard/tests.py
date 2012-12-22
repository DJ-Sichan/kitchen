"""Tests for the kitchen.dashboard app"""
import os

import simplejson as json
from django.test import TestCase
from mock import patch

from kitchen.backends import lchef as chef, plugins
from kitchen.dashboard import graphs
from kitchen.dashboard.templatetags import filters
from kitchen.settings import STATIC_ROOT, REPO

# We need to always regenerate the node data bag in case there where changes
chef.build_node_data_bag()
TOTAL_NODES = 9


class TestViews(TestCase):
    filepath = os.path.join(STATIC_ROOT, 'img', 'node_map.svg')

    def setUp(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    @patch('kitchen.backends.lchef.KITCHEN_DIR', '/badrepopath/')
    def test_list_no_repo(self):
        """Should display a RepoError message when repo dir doesn't exist"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)
        expected = "Repo dir doesn&#39;t exist at &#39;/badrepopath/&#39;"
        self.assertTrue(expected in resp.content)

    def test_list(self):
        """Should display the default node list when no params are given"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)
        self.assertTrue("Environment" in resp.content)
        self.assertTrue("Roles" in resp.content)
        # 3 nodes in the production environment, which is default
        nodes = ["testnode" + str(i) for i in range(1, 4)]
        for node in nodes:
            self.assertTrue(node in resp.content, node)

    def test_list_env(self):
        """Should display proper nodes when an environment is given"""
        resp = self.client.get("/?env=staging&virt=")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<td>testnode4</td>" in resp.content)
        self.assertFalse("<td>testnode5</td>" in resp.content)
        self.assertFalse("<td>testnode1</td>" in resp.content)
        self.assertFalse("<td>testnode2</td>" in resp.content)
        self.assertFalse("<td>testnode6</td>" in resp.content)
        # Should not display any nodes
        resp = self.client.get("/?env=testing")
        self.assertEqual(resp.status_code, 200)
        nodes = ["<td>testnode{0}</td>".format(str(i) for i in range(1, 7))]
        for node in nodes:
            self.assertTrue(node not in resp.content, node)

    def test_list_roles(self):
        """Should display proper nodes when a role is given"""
        resp = self.client.get("/?env=&roles=dbserver&virt=")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<td>testnode3</td>" in resp.content)
        self.assertTrue("<td>testnode5</td>" in resp.content)
        self.assertTrue("<td>testnode1</td>" not in resp.content)
        self.assertTrue("<td>testnode2</td>" not in resp.content)
        self.assertTrue("<td>testnode4</td>" not in resp.content)
        self.assertTrue("<td>testnode6</td>" not in resp.content)

    def test_list_tags(self):
        """Should display tags when selected nodes have tags"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('btn-custom  disabled">ATest</a>' in resp.content)

    def test_list_tags_class(self):
        """Should display tags with css class when selected nodes have tags"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('tn-custom btn-warning disabled">WIP<' in resp.content)

    def test_list_links(self):
        """Should display links when selected nodes have links"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('href="http://testnode1:22002"' in resp.content)
        self.assertTrue('src="http://haproxy.1wt.eu/img' in resp.content)
        self.assertTrue('href="http://testnode1/api' in resp.content)

    @patch('kitchen.dashboard.views.SHOW_LINKS', False)
    def test_list_links_disabled(self):
        """Should not display links when SHOW_LINKS is False"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('href="http://testnode1:22002"' not in resp.content)
        self.assertTrue('src="http://haproxy.1wt.eu/img' not in resp.content)

    def test_virt(self):
        """Should display nodes when repo is correct"""
        resp = self.client.get("/virt/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)

    def test_virt_tags(self):
        """Should display tags with css class when selected nodes have tags"""
        resp = self.client.get("/virt/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            'btn-small btn-custom btn-warning disabled">WIP<' in resp.content)
        self.assertTrue(
            'btn-custom btn-danger disabled">dummy<' in resp.content)

    def test_virt_links(self):
        """Should display links when selected nodes have links"""
        resp = self.client.get("/virt/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('href="http://testnode1:22002"' in resp.content)
        self.assertTrue('src="http://haproxy.1wt.eu/img' in resp.content)
        self.assertTrue('href="http://testnode1/api' in resp.content)

    @patch('kitchen.dashboard.views.SHOW_LINKS', False)
    def test_virt_links_disabled(self):
        """Should not display links when SHOW_LINKS is False"""
        resp = self.client.get("/virt/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('href="http://testnode1:22002"' not in resp.content)
        self.assertTrue('src="http://haproxy.1wt.eu/img' not in resp.content)

    def test_graph_no_env(self):
        """Should not generate a graph when no environment is selected"""
        resp = self.client.get("/graph/?env=")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)
        self.assertTrue("Environment" in resp.content)
        self.assertTrue("Please select an environment" in resp.content)
        self.assertFalse('<img src="/static/img/node_map.svg"' in resp.content)
        self.assertTrue("webserver" in resp.content)
        self.assertTrue("staging" in resp.content)
        self.assertFalse(os.path.exists(self.filepath))
        self.assertFalse("Hidden relationships: " in resp.content)

    @patch('kitchen.backends.lchef.KITCHEN_DIR', '/badrepopath/')
    def test_graph_no_nodes(self):
        """Should display an error message when there is a repo error"""
        resp = self.client.get("/graph/")
        self.assertEqual(resp.status_code, 200)
        expected = "Repo dir doesn&#39;t exist at &#39;/badrepopath/&#39;"
        self.assertTrue(expected in resp.content)

    def test_graph_graphviz_error(self):
        """Should display an error message when there is a GraphViz error"""
        error_msg = "GraphVizs executables not found"

        def mock_factory():
            def mock_method(a, b, c):
                return False, error_msg
            return mock_method
        with patch.object(graphs, 'generate_node_map',
                          new_callable=mock_factory):
            resp = self.client.get("/graph/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(error_msg in resp.content,
                        "Did not find expected string '{0}'".format(error_msg))
        self.assertFalse(os.path.exists(self.filepath))

    def test_graph_extra_roles_display(self):
        """Should display an extra roles message when graph detects new relations"""
        resp = self.client.get("/graph/?env=production&roles=dbserver")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Hidden relationships: " in resp.content)
        self.assertTrue('<a href="#" data-type="roles" data-name="webserver"'
                        ' class="sidebar_link" id="related_role">webserver'
                        '</a>,' in resp.content)
        self.assertTrue('<a href="#" data-type="roles" data-name="worker" '
                        'class="sidebar_link" id="related_role">worker'
                        '</a>' in resp.content)

    def test_graph_extra_roles_no_display_when_no_roles(self):
        """Should not display an extra roles message when there are no given roles"""
        resp = self.client.get("/graph/?env=production&roles=")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse("Hidden relationships: " in resp.content)

    @patch('kitchen.backends.plugins.loader.ENABLE_PLUGINS', [])
    def test_plugin_interface_no_plugin(self):
        """Should return a 404 when a requested plugin does not exist"""
        reload(plugins)
        reload(chef)
        with self.settings(DEBUG=True):
            resp = self.client.get("/plugins/name/method")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue("Requested plugin &#39;name&#39; not found" in str(resp))

    @patch('kitchen.backends.plugins.loader.ENABLE_PLUGINS', ['monitoring'])
    def test_plugin_interface_missing_method(self):
        """Should evaluate view when a requested plugin does exist"""
        reload(plugins)
        reload(chef)
        with self.settings(DEBUG=True):
            resp = self.client.get("/plugins/monitoring/boo")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue("has no method &#39;boo&#39;" in str(resp))

    @patch('kitchen.backends.plugins.loader.ENABLE_PLUGINS', ['monitoring'])
    def test_plugin_interface_wrong_arguments(self):
        """Should evaluate view when a requested plugin does exist"""
        reload(plugins)
        reload(chef)
        with self.settings(DEBUG=True):
            resp = self.client.get("/plugins/monitoring/links")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue("returned unexpected result: None" in str(resp))

    @patch('kitchen.backends.plugins.loader.ENABLE_PLUGINS', ['monitoring'])
    def test_plugin_interface_no_view(self):
        """Should evaluate view when a requested plugin does exist"""
        reload(plugins)
        reload(chef)
        with self.settings(DEBUG=True):
            resp = self.client.get("/plugins/monitoring/inject")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue("is not defined as a view" in str(resp))

    @patch('kitchen.backends.plugins.loader.ENABLE_PLUGINS', ['monitoring'])
    def test_plugin_interface(self):
        """Should evaluate view when a requested plugin does exist"""
        reload(plugins)
        reload(chef)
        resp = self.client.get("/plugins/monitoring/links?fqdn=testnode1")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'], 'http://monitoring.mydomain.com/testnode1')


class TestGraph(TestCase):
    nodes = chef.get_nodes_extended()
    roles = chef.get_roles()
    filepath = os.path.join(STATIC_ROOT, 'img', 'node_map.svg')

    def setUp(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_build_links_empty(self):
        """Should not generate links when nodes do not have any defined"""
        data = chef.filter_nodes(self.nodes, 'staging', virt_roles='guest')
        links = graphs._build_links(data)
        expected = {'testnode4': {'role_prefix': 'webserver'}}
        self.assertEqual(links, expected)

    def test_build_links_client_nodes(self):
        """Should generate links when nodes have client_nodes set"""
        data = chef.filter_nodes(self.nodes, 'production',
                                 'loadbalancer,webserver,dbserver', 'guest')
        links = graphs._build_links(data)
        self.maxDiff = None
        expected = {
            'testnode1': {'role_prefix': 'loadbalancer'},
            'testnode2': {
                'role_prefix': 'webserver',
                'client_nodes': [('testnode1', 'apache2')]
            },
            'testnode3.mydomain.com': {
                'role_prefix': 'dbserver',
                'client_nodes': [
                    ('testnode2', 'mysql'), ('testnode7', 'mysql')
                ]
            },
            'testnode7': {
                'role_prefix': 'webserver',
                'client_nodes': [('testnode1', 'apache2')]
            }
        }
        self.assertEqual(links, expected)

    def test_build_links_needs_nodes(self):
        """Should generate links when nodes have needs_nodes set"""
        data = chef.filter_nodes(self.nodes, 'production', 'dbserver,worker',
                                 'guest')
        links = graphs._build_links(data)
        expected = {
            'testnode3.mydomain.com': {'role_prefix': 'dbserver'},
            'testnode8': {
                'role_prefix': 'worker',
                'needs_nodes': [
                    ('testnode3.mydomain.com', 'mysql')
                ]
            }
        }
        self.assertEqual(links, expected)

    def test_build_links_all(self):
        """Should generate all links when nodes define connections"""
        data = chef.filter_nodes(self.nodes, 'production', virt_roles='guest')
        links = graphs._build_links(data)
        expected = {
            'testnode1': {'role_prefix': 'loadbalancer'},
            'testnode2': {
                'role_prefix': 'webserver',
                'client_nodes': [('testnode1', 'apache2')]
            },
            'testnode3.mydomain.com': {
                'role_prefix': 'dbserver',
                'client_nodes': [
                    ('testnode2', 'mysql'), ('testnode7', 'mysql')
                ]
            },
            'testnode7': {
                'role_prefix': 'webserver',
                'client_nodes': [('testnode1', 'apache2')]
            },
            'testnode8': {
                'role_prefix': 'worker',
                'needs_nodes': [
                    ('testnode3.mydomain.com', 'mysql')
                ]
            }
        }
        self.assertEqual(links, expected)

    def test_generate_empty_graph(self):
        """Should generate an empty graph when no nodes are given"""
        data = chef.filter_nodes(self.nodes, 'badenv')
        graphs.generate_node_map(data, self.roles)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        max_size = 650
        self.assertTrue(size < max_size,
                        "Size greater than {0}: {1}".format(max_size, size))

    def test_generate_small_graph(self):
        """Should generate a graph when some nodes are given"""
        data = chef.filter_nodes(self.nodes, 'staging', virt_roles='guest')
        graphs.generate_node_map(data, self.roles)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        #min_size = 3000  # png
        #max_size = 4000  # png
        min_size = 1000  # svg
        max_size = 1500  # svg
        self.assertTrue(size > min_size and size < max_size,
                        "Size not between {0} and {1}: {2}".format(
                            min_size, max_size, size))

    def test_generate_connected_graph(self):
        """Should generate a connected graph when connected nodes are given"""
        data = chef.filter_nodes(self.nodes, 'production', virt_roles='guest')
        graphs.generate_node_map(data, self.roles)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        # Graph size with connections
        #min_size = 20000  # png
        #max_size = 23000  # png
        min_size = 5000  # svg
        max_size = 7000  # svg
        self.assertTrue(size > min_size and size < max_size,
                        "Size not between {0} and {1}: {2}".format(
                            min_size, max_size, size))

    def test_graph_timeout(self):
        """Should display an error message when GraphViz excesses the timeout
        """
        error_msg = "Unable to draw graph, timeout exceeded"
        data = chef.filter_nodes(self.nodes, 'production')

        with patch('kitchen.dashboard.graphs.GraphThread.isAlive',
                   return_value=True):
            with patch('kitchen.dashboard.graphs.GraphThread.kill',
                       return_value=True):
                success, msg = graphs.generate_node_map(data, self.roles)
        self.assertFalse(success)
        self.assertTrue(error_msg in msg)

    def test_get_role_relations(self):
        """Should return role dependencies when roles with relationships are given"""
        prod_nodes = chef.filter_nodes(self.nodes, 'production')
        extra_roles = graphs.get_role_relations('production', 'dbserver',
                                                prod_nodes)
        self.assertEqual(extra_roles, ['webserver', 'worker'])
        extra_roles = graphs.get_role_relations('production', 'loadbalancer',
                                                prod_nodes)
        self.assertEqual(extra_roles, ['webserver'])
        extra_roles = graphs.get_role_relations('production', 'worker',
                                                prod_nodes)
        self.assertEqual(extra_roles, ['dbserver'])
        extra_roles = graphs.get_role_relations('production', 'webserver',
                                                prod_nodes)
        self.assertEqual(extra_roles, ['dbserver', 'loadbalancer'])

    def test_get_role_relations_empty_when_roles(self):
        """Should obtain no roles when the given roles have no extra relationships"""
        stag_nodes = chef.filter_nodes(self.nodes, 'staging')
        extra_roles = graphs.get_role_relations('staging', 'webserver',
                                                stag_nodes)
        self.assertEqual(extra_roles, [])

    def test_get_role_relations_empty_when_no_roles(self):
        """Should obtain no roles when a role filter list is not given"""
        prod_nodes = chef.filter_nodes(self.nodes, 'staging')
        extra_roles = graphs.get_role_relations('production', '', prod_nodes)
        self.assertEqual(extra_roles, [])


class TestAPI(TestCase):

    def test_get_roles_not_allowed(self):
        """Should return NOT ALLOWED when HTTP method is not GET"""
        resp = self.client.post("/api/roles")
        self.assertEqual(resp.status_code, 405)

    def test_get_roles(self):
        """Should return all available roles in JSON format"""
        resp = self.client.get("/api/roles")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 4)
        existing_roles = ['loadbalancer', 'webserver', 'dbserver', 'worker']
        for role in data:
            self.assertTrue(role['name'] in existing_roles,
                            role['name'] + " is not an existing role name")
        self.assertEqual(data[0]['name'], 'dbserver')
        self.assertEqual(data[0]['run_list'], ['recipe[mysql::server]'])

    def test_get_nodes_not_allowed(self):
        """Should return NOT ALLOWED when HTTP method is not GET"""
        resp = self.client.post("/api/nodes")
        self.assertEqual(resp.status_code, 405)

    def test_get_nodes(self):
        """Should return all available nodes when no parameters are given"""
        resp = self.client.get("/api/nodes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), TOTAL_NODES)
        self.assertTrue('role' not in data[0])  # not extended

    def test_get_nodes_env_filter(self):
        """Should return filtered nodes when filter parameters are given"""
        resp = self.client.get("/api/nodes/?env=staging")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 1)
        expected_node = {
            'chef_environment': 'staging', 'ipaddress': '4.4.4.4',
            'virtualization': {'role': 'guest'},
            'run_list': ['role[webserver]'], 'name': 'testnode4'
        }
        self.assertEqual(data[0], expected_node)

    def test_get_nodes_extended(self):
        """Should return available nodes with extended info when extended=true
        """
        resp = self.client.get("/api/nodes/?extended=true")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), TOTAL_NODES)
        self.assertTrue('role' in data[0])

    def test_get_nodes_extended_env_filter(self):
        """Should return filtered nodes when filter parameters are given"""
        resp = self.client.get("/api/nodes/?env=staging&extended=true")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['chef_environment'], 'staging')
        self.assertEqual(data[0]['role'], ['webserver'])

    def test_get_node(self):
        """Should return a node hash when node name is found"""
        resp = self.client.get("/api/nodes/testnode6")
        self.assertEqual(resp.status_code, 200)
        expected_response = {
            'name': 'testnode6', 'run_list': ['role[webserver]']
        }
        self.assertEqual(json.loads(resp.content), expected_response)

    def test_get_node_not_found(self):
        """Should return NOT FOUND when node name does not exist"""
        resp = self.client.get("/api/nodes/node_does_not_exist")
        self.assertEqual(resp.status_code, 404)


class TestTemplateTags(TestCase):
    run_list = [
        "role[dbserver]", "recipe[haproxy]", "role[webserver]",
        "role[worker]", "recipe[apache2]", "role[loadbalancer]",
        "recipe[mysql::server]"
    ]

    def test_role_filter_with_valid_runlist(self):
        """Should return a role list when a valid run list is given"""
        role_list = filters.get_role_list(self.run_list)
        expected_roles = ['dbserver', 'webserver', 'worker', 'loadbalancer']
        self.assertEqual(len(role_list), len(expected_roles))
        for role in role_list:
            self.assertTrue(role in expected_roles)
            expected_roles.remove(role)
        self.assertEqual(len(expected_roles), 0)

    def test_role_filter_with_runlist_and_exclude_node_prefix(self):
        """Should exclude roles with prefix when EXCLUDE_ROLE_PREFIX is set"""
        role_to_filter = REPO['EXCLUDE_ROLE_PREFIX'] + "_filterthisrole"
        run_list_with_excluded = self.run_list + [role_to_filter]
        role_list = filters.get_role_list(run_list_with_excluded)
        expected_roles = ['dbserver', 'webserver', 'worker', 'loadbalancer']
        self.assertEqual(len(role_list), len(expected_roles))
        for role in role_list:
            self.assertTrue(role in expected_roles)
            expected_roles.remove(role)
        self.assertEqual(len(expected_roles), 0)

    def test_role_filter_with_wrong_runlist(self):
        """Should return an empty role list when an invalid run list is given
        """
        role_list = filters.get_role_list(None)
        self.assertEqual(role_list, [])

    def test_recipe_filter_with_valid_runlist(self):
        """Should return a recipe list when a valid run list is given"""
        recipe_list = filters.get_recipe_list(self.run_list)
        expected_recipes = ['haproxy', 'apache2', 'mysql::server']
        self.assertEqual(len(recipe_list), len(expected_recipes))
        for recipe in recipe_list:
            self.assertTrue(recipe in expected_recipes)
            expected_recipes.remove(recipe)
        self.assertEqual(len(expected_recipes), 0)

    def test_recipe_filter_with_wrong_runlist(self):
        """Should return an empty recipe list when an invalid run list is given
        """
        recipe_list = filters.get_recipe_list(None)
        self.assertEqual(recipe_list, [])

    def test_memory_GB_filter_with_valid_string(self):
        """Should return memory in GB when given value is in kB"""
        memory = filters.get_memory_in_GB('7124000kB')
        self.assertEqual(memory, '7 GB')
        memory = filters.get_memory_in_GB('1024000kB')
        self.assertEqual(memory, '1 GB')

    def test_memory_GB_filter_with_invalid_string(self):
        """Should return an empty string when an invalid value is given"""
        invalid_strings = ['java', '1024000KFC', 'itsover9000', '12', '1']
        for string in invalid_strings:
            memory = filters.get_memory_in_GB(string)
            self.assertEqual(memory, '')

    def test_memory_GB_filter_with_empty_string(self):
        """Should return an empty string when None is given"""
        self.assertEqual(filters.get_memory_in_GB(None), '')

    def test_get_tag_class(self):
        """Should return a css class when tag has a defined class"""
        self.assertEqual(filters.get_tag_class("WIP"), "btn-warning")
        self.assertEqual(filters.get_tag_class("dummy"), "btn-danger")
        specific_tags = ["Node", "Node1", "NodeSpecial3", "Node*", "Node_"]
        for specific_tag in specific_tags:
            self.assertEqual(filters.get_tag_class(specific_tag), "btn-info")

    def test_get_tag_class_no_class(self):
        """Should return an empty string when tag has no defined class"""
        undefined_tags = ["foo", "Nod", "DUMMY", "Dummy", "wip", "WiP",
                          "node", "NoDe", "", "12", "", "_-_"]
        for undefined_tag in undefined_tags:
            self.assertEqual(filters.get_tag_class(undefined_tag), "")

    def test_get_link_no_url(self):
        """Should return an empty string when link has no url
        """
        link = {"title": "foo"}
        self.assertEqual(filters.get_link(link), "")

    def test_get_link_no_img_no_title(self):
        """Should return an empty string when link has no img and no title key
        """
        link = {"url": "https://github.com/edelight/kitchen"}
        self.assertEqual(filters.get_link(link), "")

    def test_get_link_no_img(self):
        """Should return a text link when link has an empty img field"""
        link = {
            "url": "https://github.com/edelight/kitchen",
            "title": "api", "img": ""
        }
        expected_link_html = ('<a href="{0}" target="_blank" title="{1}"'
                              ' class="btn btn-small btn-custom">{1}'
                              '</a>'.format(link['url'], link['title']))
        self.assertEqual(filters.get_link(link), expected_link_html)

    def test_get_link(self):
        """Should return a text link when link has an empty img field"""
        link = {
            "url": "https://github.com/edelight/kitchen",
            "title": "api", "img": "http://foo/bar.png",
        }
        expected_link_html = ('<a href="{url}" target="_blank" title="{title}"'
                              ' class="btn-custom"><img width="25"'
                              ' height="25" src="{img}"></a>'.format(**link))
        self.assertEqual(filters.get_link(link), expected_link_html)

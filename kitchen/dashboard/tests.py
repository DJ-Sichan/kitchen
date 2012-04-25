"""Tests for the kitchen.dashboard app"""
import os
import json

from django.test import TestCase
from mock import patch

from kitchen.dashboard import chef, graphs
from kitchen.settings import STATIC_ROOT

# We need to always regenerate the node data bag in case there where changes
chef.build_node_data_bag()


class TestRepo(TestCase):

    def test_good_repo(self):
        """Should return true when a valid repository is found"""
        self.assertTrue(chef._check_kitchen())

    @patch('kitchen.dashboard.chef.KITCHEN_DIR', '/badrepopath/')
    def test_bad_repo(self):
        """Should raise RepoError when the kitchen is not found"""
        self.assertRaises(chef.RepoError, chef._check_kitchen)

    @patch('kitchen.dashboard.chef.KITCHEN_DIR', '../kitchen/')
    def test_invalid_kitchen(self):
        """Should raise RepoError when the kitchen is incomplete"""
        self.assertRaises(chef.RepoError, chef._check_kitchen)


class TestData(TestCase):
    nodes = chef.load_extended_node_data()

    def test_load_data_nodes(self):
        """Should return nodes when the given argument is 'nodes'"""
        data = chef._load_data('nodes')
        self.assertEqual(len(data), 7)
        self.assertEqual(data[1]['name'], "testnode2")

    def test_get_nodes(self):
        """Should return all nodes"""
        data = chef.get_nodes()
        self.assertEqual(len(data), 7)
        self.assertEqual(data[1]['name'], "testnode2")

    def test_load_data_roles(self):
        """Should return roles when the given argument is 'roles'"""
        data = chef._load_data('roles')
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], "dbserver")

    def test_load_data_unsupported(self):
        """Should return an empty dict when an invalid arg is given"""
        data = chef._load_data('rolezzzz')
        self.assertEqual(len(data), 0)

    def test_get_environments(self):
        """Should return a list of all chef_environment values found"""
        data = chef.get_environments(self.nodes)
        self.assertEqual(len(data), 3)
        expected = [{'counts': 1, 'name': 'none'},
                    {'counts': 4, 'name': 'production'},
                    {'counts': 2, 'name': 'staging'}]
        self.assertEqual(data, expected)

    def test_filter_nodes_all(self):
        """Should return all nodes when empty filters are are given"""
        data = chef.filter_nodes(self.nodes, '', '')
        self.assertEqual(len(data), 7)

    def test_filter_nodes_env(self):
        """Should filter nodes belonging to a given environment"""
        data = chef.filter_nodes(self.nodes, 'production')
        self.assertEqual(len(data), 4)

        data = chef.filter_nodes(self.nodes, 'staging')
        self.assertEqual(len(data), 2)

        data = chef.filter_nodes(self.nodes, 'non_existing_env')
        self.assertEqual(len(data), 0)

    def test_filter_nodes_roles(self):
        """Should filter nodes acording to their virt value"""
        data = chef.filter_nodes(self.nodes, roles='dbserver')
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], "testnode3.mydomain.com")

        data = chef.filter_nodes(self.nodes, roles='loadbalancer')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "testnode1")

        data = chef.filter_nodes(self.nodes, roles='webserver')
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['name'], "testnode2")

        data = chef.filter_nodes(self.nodes, roles='webserver,dbserver')
        self.assertEqual(len(data), 6)
        self.assertEqual(data[1]['name'], "testnode3.mydomain.com")

    def test_filter_nodes_virt(self):
        """Should filter nodes acording to their virt value"""
        data = chef.filter_nodes(self.nodes, virt_roles='guest')
        self.assertEqual(len(data), 6)

        data = chef.filter_nodes(self.nodes, virt_roles='host')
        self.assertEqual(len(data), 1)

        data = chef.filter_nodes(self.nodes, virt_roles='host,guest')
        self.assertEqual(len(data), 7)

    def test_filter_nodes_combined(self):
        """Should filter nodes acording to their virt value"""
        data = chef.filter_nodes(self.nodes,
                                 env='production',
                                 roles='loadbalancer,webserver',
                                 virt_roles='guest')
        self.assertEqual(len(data), 3)

        data = chef.filter_nodes(self.nodes,
            env='staging', roles='webserver', virt_roles='guest')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "testnode4")


class TestGraph(TestCase):
    nodes = chef.load_extended_node_data()
    filepath = os.path.join(STATIC_ROOT, 'img', 'node_map.png')

    def setUp(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_build_links_empty(self):
        """Should not generate links when nodes do not have any defined"""
        data = chef.filter_nodes(self.nodes, 'staging')
        links = graphs._build_links(data)
        self.assertEqual(links, {})

    def test_build_links_client_nodes(self):
        """Should generate links when nodes have client_nodes set"""
        data = chef.filter_nodes(self.nodes, 'production')
        links = graphs._build_links(data)
        expected = {
            'testnode2': {'client_nodes': [('testnode1', 'apache2')]},
            'testnode3.mydomain.com': {
                'client_nodes': [
                    ('testnode2', 'mysql'), ('testnode7', 'mysql')
                ]
            },
            'testnode7': {'client_nodes': [('testnode1', 'apache2')]}
        }
        self.assertEqual(links, expected)

    def test_generate_empty_graph(self):
        """Should generate an empty graph when no nodes are given"""
        data = chef.filter_nodes(self.nodes, 'badenv')
        graphs.generate_node_map(data)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        self.assertTrue(os.path.getsize(self.filepath) < 100,
                        "Size greater than 1000: {0}".format(size))

    def test_generate_small_graph(self):
        """Should generate a graph when some nodes are given"""
        data = chef.filter_nodes(self.nodes, 'staging')
        graphs.generate_node_map(data)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        self.assertTrue(size > 1700 and size < 2000,
                        "Size not between 1700 and 2000: {0}".format(size))

    def test_generate_connected_graph(self):
        """Should generate a connected graph when connected nodes are given"""
        data = chef.filter_nodes(self.nodes, 'production')
        graphs.generate_node_map(data)
        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        # Size with connections
        max_size = 12000
        min_size = 10000
        self.assertTrue(size > min_size and size < max_size,
                        "Size not between {0} and {1}: {2}".format(
                            min_size, max_size, size))


class TestViews(TestCase):
    filepath = os.path.join(STATIC_ROOT, 'img', 'node_map.png')

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
        self.assertTrue("testnode4" in resp.content)
        self.assertTrue("testnode5" in resp.content)
        self.assertTrue("testnode1" not in resp.content)
        self.assertTrue("testnode2" not in resp.content)
        self.assertTrue("testnode6" not in resp.content)
        # Should not display any nodes
        resp = self.client.get("/?env=testing")
        self.assertEqual(resp.status_code, 200)
        nodes = ["testnode" + str(i) for i in range(1, 7)]
        for node in nodes:
            self.assertTrue(node not in resp.content, node)

    def test_list_roles(self):
        """Should display proper nodes when a role is given"""
        resp = self.client.get("/?env=&roles=dbserver&virt=")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("testnode3.mydomain.com" in resp.content)
        self.assertTrue("testnode5" in resp.content)
        self.assertTrue("testnode1" not in resp.content)
        self.assertTrue("testnode2" not in resp.content)
        self.assertTrue("testnode4" not in resp.content)
        self.assertTrue("testnode6" not in resp.content)

    @patch('kitchen.dashboard.chef.KITCHEN_DIR', '/badrepopath/')
    def test_list_no_repo(self):
        """Should display a RepoError message when repo dir doesn't exist"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)
        expected = "Repo dir doesn&#39;t exist at &#39;/badrepopath/&#39;"
        self.assertTrue(expected in resp.content)

    def test_graph_no_env(self):
        """Should not generate a graph when no environment is selected"""
        resp = self.client.get("/graph/?env=")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("<title>Kitchen</title>" in resp.content)
        self.assertTrue("Environment" in resp.content)
        self.assertTrue("Please select an environment" in resp.content)

        self.assertTrue(os.path.exists(self.filepath))
        size = os.path.getsize(self.filepath)
        self.assertTrue(os.path.getsize(self.filepath) < 100,
                        "Size greater than 1000: {0}".format(size))

    @patch('kitchen.dashboard.chef.KITCHEN_DIR', '/badrepopath/')
    def test_graph_no_nodes(self):
        """Should display an error message when there is a repo error"""
        resp = self.client.get("/graph/")
        self.assertEqual(resp.status_code, 200)
        expected = "Repo dir doesn&#39;t exist at &#39;/badrepopath/&#39;"
        self.assertTrue(expected in resp.content)


class TestAPI(TestCase):

    def test_get_roles(self):
        """Should return all available roles in JSON format"""
        resp = self.client.get("/api/roles")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 3)
        existing_roles = ['loadbalancer', 'webserver', 'dbserver']
        for role in data:
            self.assertTrue(role['name'] in existing_roles,
                            role['name'] + " is not an existing role name")
        self.assertEqual(data[0]['name'], 'dbserver')
        self.assertEqual(data[0]['run_list'], ['recipe[mysql::server]'])

    def test_get_nodes(self):
        """Should return all available nodes in JSON format"""
        resp = self.client.get("/api/nodes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 7)
        self.assertTrue('role' not in data[0])

    def test_get_nodes_extended(self):
        """Should return all available nodes with extended info"""
        resp = self.client.get("/api/nodes/?extended=true")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 7)
        self.assertTrue('role' in data[0])

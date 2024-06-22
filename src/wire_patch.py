import json
from .nodes import NODE_CLASS_NAMES


class Coords:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other_coords):
        return Coords(self.x + other_coords.x, self.y + other_coords.y)

    def __str__(self):
        return f'Coords: ({self.x}, {self.y})'


class Bounds:
    def __init__(self, coords, width, height):
        self.coords = coords
        self.width = width
        self.height = height

    @property
    def upper_left(self):
        return self.coords

    @property
    def upper_right(self):
        return Coords(self.coords.x + self.width, self.coords.y)

    @property
    def bottom_left(self):
        return Coords(self.coords.x, self.coords.y + self.height)

    @property
    def bottom_right(self):
        return Coords(self.coords.x + self.width, self.coords.y + self.height)

    @property
    def has_width(self):
        return self.width > 0.0

    @property
    def has_height(self):
        return self.height > 0.0

    def contains(self, bounds):
        return self.upper_left.x < bounds.upper_left.x and \
               self.upper_left.y < bounds.upper_left.y and \
               self.bottom_right.x > bounds.bottom_right.x and \
               self.bottom_right.y > bounds.bottom_right.y


class NodeConnection:
    def __init__(self, from_node, from_output, to_node, to_input):
        self.from_node = from_node
        self.from_output = from_output
        self.to_node = to_node
        self.to_input = to_input

    @property
    def as_dict(self):
        return {
            'from': [
                self.from_node.node_id,
                self.from_output,
            ],
            'to': [
                self.to_node.node_id,
                self.to_input,
            ],
        }

    def __str__(self):
        return f'{self.from_node}/{self.from_output} -> {self.to_node}/{self.to_input}'


class NodeConnectionGraph:
    def __init__(self):
        self.nodes = {}
        self.connections = []

    def add_node(self, node_id, node_dict):
        node = Node(node_id, node_dict)
        self.nodes[node.node_id] = node
        return node

    def add_connection(self, from_node, from_output, to_node, to_input):
        connection = NodeConnection(from_node, from_output, to_node, to_input)
        self.connections.append(connection)
        return connection

    def remove_node(self, node):
        del self.nodes[node.node_id]
        self.connections = [c for c in self.connections if c.from_node != node and c.to_node != node]

    def get_node_by_id(self, node_id):
        return self.nodes[node_id]

    @property
    def node_ids(self):
        return list(self.nodes.keys())

    def is_connected(self, node1, node2):
        for conn in self.connections:
            if (conn.from_node == node1 and conn.to_node == node2) or \
               (conn.from_node == node2 and conn.to_node == node1):
                return True

        return False

    def connections_from_node(self, node):
        return [conn for conn in self.connections if conn.from_node == node]

    def connections_to_node(self, node):
        return [conn for conn in self.connections if conn.to_node == node]


class Node:
    def __init__(self, node_id, node_dict):
        self.node_id = int(node_id)
        self.key = str(self.node_id)
        self.name = node_dict['name']
        self.node_class = node_dict['class']['id']
        self.node_type = NODE_CLASS_NAMES[self.node_class]
        self.node_dict = node_dict
        self.bounds = self.get_bounds()

    def move_to(self, coords):
        self.node_dict['bounds']['x'] = coords.x
        self.node_dict['bounds']['y'] = coords.y
        self.bounds = self.get_bounds()

    def resize(self, width, height):
        self.node_dict['bounds']['width'] = width
        self.node_dict['bounds']['height'] = height
        self.bounds = self.get_bounds()

    def contains(self, other_node):
        return self.bounds.contains(other_node.bounds)

    def get_bounds(self):
        bounds = Bounds(
            Coords(self.node_dict['bounds']['x'], self.node_dict['bounds']['y']),
            self.node_dict['bounds']['width'],
            self.node_dict['bounds']['height'],
        )
        return bounds

    @property
    def attributes(self):
        return self.node_dict['attributes']

    @property
    def as_dict(self):
        return self.node_dict

    def __str__(self):
        return f'{self.name} ({self.node_id})'


class WirePatch:
    def __init__(self, patch_dict):
        self.format_version = patch_dict['formatVersion']
        self.patch = patch_dict['patch']
        self.next_node_id = self.patch['nextNodeId']
        self.resources = patch_dict['resources']
        self.ui = patch_dict['ui']

        self.node_graph = NodeConnectionGraph()

        nodes = patch_dict['patch']['nodes']
        for node_id, node_dict in nodes.items():
            self.node_graph.add_node(node_id, node_dict)

        connections = patch_dict['patch']['connections']
        for connection in connections:
            from_node_id = connection['from'][0]
            from_output = connection['from'][1]
            from_node = self.node_graph.get_node_by_id(from_node_id)

            to_node_id = connection['to'][0]
            to_input = connection['to'][1]
            to_node = self.node_graph.get_node_by_id(to_node_id)

            self.node_graph.add_connection(from_node, from_output, to_node, to_input)

    def add_node(self, node, coords):
        new_node = self.node_graph.add_node(self.next_node_id, node.node_dict)
        new_node.move_to(coords)
        self.next_node_id += 1
        return new_node

    def add_connection(self, from_node, from_output, to_node, to_input):
        return self.node_graph.add_connection(from_node, from_output, to_node, to_input)

    @property
    def as_dict(self):
        return {
            'formatVersion': self.format_version,
            'patch': {
                'connections': [c.as_dict for c in self.node_graph.connections],
                'inputOrder': self.patch['inputOrder'],
                'meta': self.patch['meta'],
                'nextNodeId': self.next_node_id,
                'nodes': {n.key: n.as_dict for n in self.node_graph.nodes.values()},
                'ui': self.patch['ui'],
            },
            'resources': self.resources,
            'ui': self.ui,
        }

    @staticmethod
    def from_file(filename):
        with open(filename, 'r') as f:
            return WirePatch(json.load(f))

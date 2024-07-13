import json
from .nodes import NODE_CLASS_NAMES


class InvalidNode(Exception):
    pass


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


class Node:
    def __init__(self, node_id, node_data):
        try:
            self.node_id = int(node_id)
        except ValueError:
            raise InvalidNode(f'Invalid node_id: {node_id}')

        self.node_data = node_data
        self.name = node_data['name']
        self.node_class = node_data['class']['id']
        self.node_type = NODE_CLASS_NAMES[self.node_class]
        self.bounds = self.get_bounds()

    def move_to(self, coords):
        self.node_data['bounds']['x'] = coords.x
        self.node_data['bounds']['y'] = coords.y
        self.bounds = self.get_bounds()

    def resize(self, width, height):
        self.node_data['bounds']['width'] = width
        self.node_data['bounds']['height'] = height
        self.bounds = self.get_bounds()

    def contains(self, other_node):
        return self.bounds.contains(other_node.bounds)

    def get_bounds(self):
        coords = Coords(self.node_data['bounds']['x'], self.node_data['bounds']['y'])
        bounds = Bounds(
            coords,
            self.node_data['bounds']['width'],
            self.node_data['bounds']['height'],
        )
        return bounds

    def clone(self):
        return Node(self.node_id, self.node_data)

    @property
    def attributes(self):
        return self.node_data['attributes']

    @property
    def as_dict(self):
        return self.node_data

    def __str__(self):
        return f'{self.name} ({self.node_id})'


class NodeConnection:
    def __init__(self, from_node, outlet, to_node, inlet):
        self.from_node = from_node
        self.outlet = outlet
        self.to_node = to_node
        self.inlet = inlet

    @property
    def as_dict(self):
        return {
            'from': [
                self.from_node.node_id,
                self.outlet,
            ],
            'to': [
                self.to_node.node_id,
                self.inlet,
            ],
        }

    def clone(self):
        return NodeConnection(self.from_node, self.outlet, self.to_node, self.inlet)

    def __str__(self):
        return f'{self.from_node}/{self.outlet} -> {self.to_node}/{self.inlet}'


class NodeConnectionGraph:
    def __init__(self):
        self.node_map = {}
        self.connections = []

    def add_node(self, node):
        self.node_map[node.node_id] = node

    def add_connection(self, connection):
        self.connections.append(connection)

    def remove_node(self, node):
        del self.nodes[node.node_id]
        self.connections = [c for c in self.connections if c.from_node != node and c.to_node != node]

    def get_node_by_id(self, node_id):
        return self.node_map[node_id]

    @property
    def node_ids(self):
        return list(self.node_map.keys())

    @property
    def nodes(self):
        return list(self.node_map.values())

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


class WirePatch:
    def __init__(self, patch_dict):
        self.format_version = patch_dict['formatVersion']
        self.patch = patch_dict['patch']
        self.next_node_id = self.patch['nextNodeId']
        self.resources = patch_dict['resources']
        self.ui = patch_dict['ui']

        self.node_graph = NodeConnectionGraph()

        nodes = patch_dict['patch']['nodes']
        for node_id, node_data in nodes.items():
            self.node_graph.add_node(Node(node_id, node_data))

        connections = patch_dict['patch']['connections']
        for connection in connections:
            from_node = self.node_graph.get_node_by_id(connection['from'][0])
            outlet = connection['from'][1]

            to_node = self.node_graph.get_node_by_id(connection['to'][0])
            inlet = connection['to'][1]

            connection = NodeConnection(from_node, outlet, to_node, inlet)
            self.node_graph.add_connection(connection)

    def add_node(self, node, coords):
        new_node = node.clone()
        new_node.move_to(coords)
        self.node_graph.add_node(new_node)
        self.next_node_id += 1
        return new_node

    def remove_node(self, node):
        self.node_graph.remove_node(node)

    def add_connection(self, connection):
        return self.node_graph.add_connection(connection.clone())

    @property
    def as_dict(self):
        return {
            'formatVersion': self.format_version,
            'patch': {
                'connections': [c.as_dict for c in self.node_graph.connections],
                'inputOrder': self.patch['inputOrder'],
                'meta': self.patch['meta'],
                'nextNodeId': self.next_node_id,
                'nodes': {str(n.node_id): n.as_dict for n in self.node_graph.nodes},
                'ui': self.patch['ui'],
            },
            'resources': self.resources,
            'ui': self.ui,
        }

    @staticmethod
    def from_file(filename):
        with open(filename, 'r') as f:
            return WirePatch(json.load(f))

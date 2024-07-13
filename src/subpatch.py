import json
from .nodes import COMMENT_NODE_CLASS, HUB_NODE_CLASS
from .wire_patch import Bounds, Coords, Node, NodeConnectionGraph, WirePatch


class InvalidContainerNodeException(Exception):
    pass


class InvalidSubpatchException(Exception):
    pass


class SubpatchNotFoundException(Exception):
    pass


class SubpatchInjectionException(Exception):
    pass


class SubpatchContainerNode(Node):
    def __init__(self, node_id, node_dict):
        super().__init__(node_id, node_dict)

        if self.node_class != COMMENT_NODE_CLASS:
            raise InvalidContainerNode('Invalid container node: must be a Comment node')

        if not self.text.startswith(SubpatchContainerNode.COMMENT_PREFIX):
            raise InvalidContainerNode('Invalid container node text')

        lines = text.split('\n')

    @property
    def text(self):
        return self.attributes['text']['value']

        self.subpatch_name = lines[0].split(Subpatch.COMMENT_PREFIX)[1].strip()
        self.description = '\n'.join(lines[1:]).strip()

    @staticmethod
    def find_in(nodes):
        # Given a list of nodes, return all the subpatch container nodes.
        # This will be a list of SubpatchContainerNode objects.
        container_nodes = []

        comment_nodes = [node for node in nodes if node.node_class == COMMENT_NODE_CLASS]
        for node in comment_nodes:
            text = node.attributes['text']['value']
            if text and text.startswith(Subpatch.COMMENT_PREFIX):
                container_node = SubpatchContainerNode(node.node_id, node.node_dict)
                container_nodes.append(container_node)

        return container_nodes


class SubpatchInjector:
    HEADER_MIN_HEIGHT = 50.0
    LEFT_MARGIN = 10.0
    RIGHT_MARGIN = 10.0
    INPUT_NODE_VERT_SPACING = 5.0
    INPUT_NODE_CONNECTION_MARGIN = 10.0
    OUTPUT_NODE_VERT_SPACING = 5.0
    OUTPUT_NODE_CONNECTION_MARGIN = 10.0
    FOOTER_HEIGHT = 10.0

    def __init__(self, subpatch):
        self.subpatch = subpatch
        self.input_node_column_bounds = self._get_input_node_column_bounds()
        self.node_cluster_column_bounds = self._get_node_cluster_column_bounds()
        self.output_node_column_bounds = self._get_output_node_column_bounds()
        self.container_bounds = self._get_container_bounds()

    def _get_input_node_column_bounds(self):
        xy = Coords(self.LEFT_MARGIN, self.HEADER_MIN_HEIGHT)

        nodes = self.subpatch.input_nodes
        if not nodes:
            return Bounds(xy, 0.0, 0.0)

        max_node_width = max([node.bounds.width for node in nodes])
        column_height = sum([(node.bounds.height + self.INPUT_NODE_VERT_SPACING) for node in nodes])

        return Bounds(xy, max_node_width, column_height)

    def _get_node_cluster_column_bounds(self):
        xy = self.input_node_column_bounds.coords + \
             Coords(self.input_node_column_bounds.width, 0.0) + \
             Coords(self.INPUT_NODE_CONNECTION_MARGIN, 0.0)

        nodes = self.subpatch.node_cluster_nodes
        if not nodes:
            return Bounds(xy, 0.0, 0.0)

        max_width = max([node.bounds.width for node in nodes])
        max_height = max([node.bounds.height for node in nodes])

        return Bounds(xy, max_width, max_height)

    def _get_output_node_column_bounds(self):
        xy = self.node_cluster_column_bounds.coords + \
             Coords(self.node_cluster_column_bounds.width, 0.0) + \
             Coords(self.OUTPUT_NODE_CONNECTION_MARGIN, 0.0)

        nodes = self.subpatch.output_nodes
        if not nodes:
            return Bounds(xy, 0.0, 0.0)

        max_node_width = max([node.bounds.width for node in nodes])
        column_height = sum([(node.bounds.height + self.OUTPUT_NODE_VERT_SPACING) for node in nodes])

        return Bounds(xy, max_node_width, column_height)

    def _get_container_bounds(self):
        xy = Coords(0.0, 0.0)

        width = 0.0
        width += self.LEFT_MARGIN
        if self.input_node_column_bounds.has_width:
            width += self.input_node_column_bounds.width + self.INPUT_NODE_CONNECTION_MARGIN
        if self.node_cluster_column_bounds.has_width:
            width += self.node_cluster_column_bounds.width + self.OUTPUT_NODE_CONNECTION_MARGIN
        if self.output_node_column_bounds.has_width:
            width += self.output_node_column_bounds.width
        width += self.RIGHT_MARGIN

        height = 0.0
        height += self.HEADER_MIN_HEIGHT
        input_col_height = self.input_node_column_bounds.height
        cluster_col_height = self.node_cluster_column_bounds.height
        output_col_height = self.output_node_column_bounds.height
        height += max([input_col_height, cluster_col_height, output_col_height])
        height += self.FOOTER_HEIGHT

        return Bounds(xy, width, height)

    def inject_into(self, patch, coords):
        new_node_id_map = {}

        xy = coords + self.container_bounds.coords
        new_container_node = patch.add_node(self.subpatch.container_node, xy)
        new_node_id_map[new_container_node.node_id] = new_container_node
        new_container_node.resize(self.container_bounds.width, self.container_bounds.height)

        xy = coords + self.input_node_column_bounds.coords
        for node in self.subpatch.input_nodes:
            new_node = patch.add_node(node, xy)
            new_node_id_map[node.node_id] = new_node
            xy += Coords(0.0, new_node.bounds.height + self.INPUT_NODE_VERT_SPACING)

        xy = coords + self.node_cluster_column_bounds.coords
        for node in self.subpatch.node_cluster_nodes:
            new_node = patch.add_node(node, xy)
            new_node_id_map[node.node_id] = new_node

        xy = coords + self.output_node_column_bounds.coords
        for node in self.subpatch.output_nodes:
            new_node = patch.add_node(node, xy)
            new_node_id_map[node.node_id] = new_node
            xy += Coords(0.0, new_node.bounds.height + self.OUTPUT_NODE_VERT_SPACING)

        for connection in self.subpatch.node_graph.connections:
            from_node = new_node_id_map[connection.from_node.node_id]
            from_output = connection.from_output
            to_node = new_node_id_map[connection.to_node.node_id]
            to_input = connection.to_input
            patch.add_connection(from_node, from_output, to_node, to_input)


class Subpatch:
    COMMENT_PREFIX = 'Subpatch:'
    VERSION = '0.0.1'

    def __init__(self, subpatch_dict):
        self.node_graph = NodeConnectionGraph()

        nodes = subpatch_dict['nodes']
        for node_id, node_dict in nodes.items():
            node = self.node_graph.add_node(node_id, node_dict)

        connections = subpatch_dict['connections']
        for connection in connections:
            from_node_id = connection['from'][0]
            from_output = connection['from'][1]
            from_node = self.node_graph.get_node_by_id(from_node_id)

            to_node_id = connection['to'][0]
            to_input = connection['to'][1]
            to_node = self.node_graph.get_node_by_id(to_node_id)

            self.node_graph.add_connection(from_node, from_output, to_node, to_input)

        self.reset_node_ids()

        container_nodes = SubpatchContainerNode.find_in(self.node_graph.nodes.values())
        container_nodes = SubpatchContainerNode.find_in(self.node_graph.nodes)
        if not container_nodes:
            raise InvalidSubpatchException('No container node found for subpatch')
        if len(container_nodes) > 1:
            raise InvalidSubpatchException('Multiple container nodes found for subpatch')

        self.container_node = container_nodes[0]

        self.name = self.container_node.subpatch_name
        self.description = self.container_node.description

    def reset_node_ids(self):
        next_node_id = 0
        new_node_graph = NodeConnectionGraph()
        new_node_id_map = {}

        for node in self.node_graph.nodes.values():
            new_node = new_node_graph.add_node(next_node_id, node.node_dict)
            new_node_id_map[node.node_id] = new_node
            next_node_id += 1

        for connection in self.node_graph.connections:
            from_node = new_node_id_map[connection.from_node.node_id]
            from_output = connection.from_output
            to_node = new_node_id_map[connection.to_node.node_id]
            to_input = connection.to_input
            new_node_graph.add_connection(from_node, from_output, to_node, to_input)

        self.node_graph = new_node_graph

    @property
    def input_nodes(self):
        nodes = []
        for node in self.node_graph.nodes.values():
            if node.node_class == HUB_NODE_CLASS and not self.node_graph.connections_to_node(node):
                nodes.append(node)

        return nodes

    @property
    def output_nodes(self):
        nodes = []
        for node in self.node_graph.nodes.values():
            if node.node_class == HUB_NODE_CLASS and not self.node_graph.connections_from_node(node):
                nodes.append(node)

        return nodes

    @property
    def node_cluster_nodes(self):
        # The "node cluster" is any node that is not an input node, an output node,
        # or the container node.
        input_nodes = self.input_nodes
        output_nodes = self.output_nodes

        nodes = []
        for node in self.node_graph.nodes.values():
            if node in input_nodes or node in output_nodes:
                continue

            if node.node_id == self.container_node.node_id:
                continue

            nodes.append(node)

        return nodes

    @property
    def as_dict(self):
        return {
            'name': self.container_node.subpatch_name,
            'description': self.container_node.description,
            'subpatch_version': Subpatch.VERSION,
            'connections': [c.as_dict for c in self.node_graph.connections],
            'nodes': {n.key: n.as_dict for n in self.node_graph.nodes.values()},
        }

    @staticmethod
    def from_file(filename):
        with open(filename, 'r') as f:
            subpatch_dict = json.load(f)

            subpatch_version = subpatch_dict.get('subpatch_version')
            if not subpatch_version:
                raise InvalidSubpatchException('Unable to parse subpatch')

            return Subpatch(subpatch_dict)

    @staticmethod
    def extract_from_patch(patch, subpatch_name):
        container_nodes = SubpatchContainerNode.find_in(patch.node_graph.nodes.values())

        container_node = None
        for node in container_nodes:
            if node.subpatch_name == subpatch_name:
                container_node = node
                break

        if not container_node:
            raise SubpatchNotFoundException(f"Subpatch '{subpatch_name}' not found within patch")

        node_graph = NodeConnectionGraph()

        node_graph.add_node(container_node.node_id, container_node.node_dict)

        for node in patch.node_graph.nodes.values():
            if container_node.contains(node):
                node_graph.add_node(node.node_id, node.node_dict)

        node_ids = node_graph.node_ids
        for connection in patch.node_graph.connections:
            if connection.from_node.node_id in node_ids and connection.to_node.node_id in node_ids:
                node_graph.add_connection(
                    connection.from_node,
                    connection.from_output,
                    connection.to_node,
                    connection.to_input,
                )

        subpatch_dict = {
            'connections': [c.as_dict for c in node_graph.connections],
            'nodes': {n.key: n.as_dict for n in node_graph.nodes.values()},
        }

        return Subpatch(subpatch_dict)

    def insert_into(self, patch, coords):
        SubpatchInjector(self).inject_into(patch, coords)

    def remove_from(self, patch):
        container_to_remove = None

        container_nodes = SubpatchContainerNode.find_in(patch.node_graph.nodes.values())
        for node in container_nodes:
            if node.subpatch_name == self.name:
                container_to_remove = node
                break

        if not container_to_remove:
            raise SubpatchNotFoundException(f'Subpatch not found within patch: {self.name}')

        nodes_to_remove = []
        for node in patch.node_graph.nodes.values():
            if container_to_remove.node_id == node.node_id or container_to_remove.contains(node):
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            patch.node_graph.remove_node(node)

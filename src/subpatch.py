import json
import math
from .nodes import COMMENT_NODE_CLASS, HUB_NODE_CLASS
from .wire_patch import Bounds, Coords, Node, NodeConnection, NodeConnectionGraph, WirePatch


class InvalidContainerNodeException(Exception):
    pass


class InvalidSubpatchException(Exception):
    pass


class SubpatchNotFoundException(Exception):
    pass


class SubpatchInjectionException(Exception):
    pass


class SubpatchContainerNode(Node):
    """A specialized node subclass for dealing with container nodes, which are
    always Comment nodes with text starting with "Subpatch:".
    """
    COMMENT_PREFIX = 'Subpatch:'

    def __init__(self, node):
        super().__init__(node.node_id, node.node_data)

        if self.node_class != COMMENT_NODE_CLASS:
            raise InvalidContainerNode('Invalid container node: must be a Comment node')

        if not self.text.startswith(SubpatchContainerNode.COMMENT_PREFIX):
            raise InvalidContainerNode('Invalid container node text')

        lines = self.text.split('\n')

        self.subpatch_name = lines[0].split(SubpatchContainerNode.COMMENT_PREFIX)[1].strip()
        if len(lines) > 1:
            self.description = '\n'.join(lines[1:]).strip()
        else:
            self.description = ''

    @property
    def text(self):
        return self.attributes['text']['value']

    @property
    def font_size(self):
        return self.attributes['font-size']['value']

    @staticmethod
    def find_in(nodes):
        # Given a list of nodes, return all the subpatch container nodes.
        # This will be a list of SubpatchContainerNode objects.
        container_nodes = []

        comment_nodes = [node for node in nodes if node.node_class == COMMENT_NODE_CLASS]
        for node in comment_nodes:
            container_node = SubpatchContainerNode(node)
            if container_node.text and container_node.text.startswith(SubpatchContainerNode.COMMENT_PREFIX):
                container_nodes.append(container_node)

        return container_nodes


class SubpatchInjector:
    """A class that handles the process of injecting a subpatch into an existing Wire patch."""

    HEADER_MIN_HEIGHT = 50.0
    LEFT_MARGIN = 10.0
    RIGHT_MARGIN = 10.0
    INPUT_NODE_VERT_SPACING = 5.0
    INPUT_NODE_CONNECTION_MARGIN = 10.0
    OUTPUT_NODE_VERT_SPACING = 5.0
    OUTPUT_NODE_CONNECTION_MARGIN = 10.0
    FOOTER_HEIGHT = 10.0
    DESCRIPTION_CHAR_WIDTH = 6.8
    DESCRIPTION_LINE_PADDING = 3

    def __init__(self, subpatch):
        self.subpatch = subpatch

        input_node_column_dimensions = self._get_input_node_column_dimensions()
        node_cluster_column_dimensions = self._get_node_cluster_column_dimensions()
        output_node_column_dimensions = self._get_output_node_column_dimensions()
        container_width = self._get_container_width(
            input_node_column_dimensions[0],
            node_cluster_column_dimensions[0],
            output_node_column_dimensions[0],
        )
        container_header_height = self._get_container_header_height(container_width)
        container_height = self._get_container_height(
            container_header_height,
            input_node_column_dimensions[1],
            node_cluster_column_dimensions[1],
            output_node_column_dimensions[1],
        )

        xy = Coords(0.0, 0.0)
        self.container_bounds = Bounds(xy, container_width, container_height)

        xy = Coords(self.LEFT_MARGIN, container_header_height)
        self.input_node_column_bounds = Bounds(xy,
            input_node_column_dimensions[0],
            input_node_column_dimensions[1],
        )

        xy = self.input_node_column_bounds.coords
        if self.input_node_column_bounds.has_width:
            xy += Coords(self.input_node_column_bounds.width, 0.0) + \
                  Coords(self.INPUT_NODE_CONNECTION_MARGIN, 0.0)
        self.node_cluster_column_bounds = Bounds(xy,
            node_cluster_column_dimensions[0],
            node_cluster_column_dimensions[1],
        )

        xy = self.node_cluster_column_bounds.coords
        if self.node_cluster_column_bounds.has_width:
            xy += Coords(self.node_cluster_column_bounds.width, 0.0) + \
                  Coords(self.OUTPUT_NODE_CONNECTION_MARGIN, 0.0)
        self.output_node_column_bounds = Bounds(xy,
            output_node_column_dimensions[0],
            output_node_column_dimensions[1],
        )

    def _get_input_node_column_dimensions(self):
        nodes = self.subpatch.input_nodes
        if nodes:
            width = max([node.bounds.width for node in nodes])
            height = sum([(node.bounds.height + self.INPUT_NODE_VERT_SPACING) for node in nodes])
        else:
            width = 0.0
            height = 0.0

        return width, height

    def _get_node_cluster_column_dimensions(self):
        nodes = self.subpatch.node_cluster_nodes
        if nodes:
            width = max([node.bounds.width for node in nodes])
            height = max([node.bounds.height for node in nodes])
        else:
            width = 0.0
            height = 0.0

        return width, height

    def _get_output_node_column_dimensions(self):
        nodes = self.subpatch.output_nodes
        if nodes:
            width = max([node.bounds.width for node in nodes])
            height = sum([(node.bounds.height + self.OUTPUT_NODE_VERT_SPACING) for node in nodes])
        else:
            width = 0.0
            height = 0.0

        return width, height

    def _get_container_width(self,
                             input_node_column_width,
                             node_cluster_column_width,
                             output_node_column_width):
        width = self.LEFT_MARGIN
        if input_node_column_width > 0.0:
            width += input_node_column_width + self.INPUT_NODE_CONNECTION_MARGIN
        if node_cluster_column_width > 0.0:
            width += node_cluster_column_width + self.OUTPUT_NODE_CONNECTION_MARGIN
        if output_node_column_width > 0.0:
            width += output_node_column_width
        width += self.RIGHT_MARGIN

        return width

    def _get_container_header_height(self, container_width):
        # When calculating the container node header height, we need to take the
        # entire text of the container node into account.
        height = 0.0
        text = self.subpatch.container_node.text
        if text:
            chars_per_line = math.ceil(container_width / self.DESCRIPTION_CHAR_WIDTH)
            font_size = self.subpatch.container_node.font_size
            description_lines = text.split('\n')
            for line in description_lines:
                n_lines = math.ceil(len(line) / chars_per_line)
                height += n_lines * (font_size + self.DESCRIPTION_LINE_PADDING)

        if height < self.HEADER_MIN_HEIGHT:
            height = self.HEADER_MIN_HEIGHT

        return height

    def _get_container_height(self,
                              container_header_height,
                              input_node_column_height,
                              node_cluster_column_height,
                              output_node_column_height):
        height = container_header_height
        height += max([
            input_node_column_height,
            node_cluster_column_height,
            output_node_column_height,
        ])
        height += self.FOOTER_HEIGHT

        return height

    def inject_into(self, patch, coords):
        new_node_id_map = {}

        xy = coords + self.container_bounds.coords
        next_node_id = patch.next_node_id

        new_container_node = Node(next_node_id, self.subpatch.container_node.node_data)
        patch.add_node(new_container_node, xy)
        new_node_id_map[self.subpatch.container_node.node_id] = new_container_node
        new_container_node.resize(self.container_bounds.width, self.container_bounds.height)
        next_node_id += 1

        xy = coords + self.input_node_column_bounds.coords
        for node in self.subpatch.input_nodes:
            new_node = Node(next_node_id, node.node_data)
            patch.add_node(new_node, xy)
            new_node_id_map[node.node_id] = new_node
            xy += Coords(0.0, new_node.bounds.height + self.INPUT_NODE_VERT_SPACING)
            next_node_id += 1

        xy = coords + self.node_cluster_column_bounds.coords
        for node in self.subpatch.node_cluster_nodes:
            new_node = Node(next_node_id, node.node_data)
            patch.add_node(new_node, xy)
            new_node_id_map[node.node_id] = new_node
            next_node_id += 1

        xy = coords + self.output_node_column_bounds.coords
        for node in self.subpatch.output_nodes:
            new_node = Node(next_node_id, node.node_data)
            patch.add_node(new_node, xy)
            new_node_id_map[node.node_id] = new_node
            xy += Coords(0.0, new_node.bounds.height + self.OUTPUT_NODE_VERT_SPACING)

        for connection in self.subpatch.node_graph.connections:
            from_node = new_node_id_map[connection.from_node.node_id]
            outlet = connection.outlet
            to_node = new_node_id_map[connection.to_node.node_id]
            inlet = connection.inlet
            connection = NodeConnection(from_node, outlet, to_node, inlet)
            patch.add_connection(connection)


class Subpatch:
    VERSION = '0.0.1'

    def __init__(self, subpatch_data):
        self.node_graph = NodeConnectionGraph()

        nodes = subpatch_data['nodes']
        for node_id, node_data in nodes.items():
            self.node_graph.add_node(Node(node_id, node_data))

        connections = subpatch_data['connections']
        for connection in connections:
            from_node = self.node_graph.get_node_by_id(connection['from'][0])
            outlet = connection['from'][1]

            to_node = self.node_graph.get_node_by_id(connection['to'][0])
            inlet = connection['to'][1]

            connection = NodeConnection(from_node, outlet, to_node, inlet)
            self.node_graph.add_connection(connection)

        self.reset_node_ids()

        container_nodes = SubpatchContainerNode.find_in(self.node_graph.nodes)
        if not container_nodes:
            raise InvalidSubpatchException('No container node found for subpatch')
        if len(container_nodes) > 1:
            raise InvalidSubpatchException('Multiple container nodes found for subpatch')

        self.container_node = container_nodes[0]

    def reset_node_ids(self):
        next_node_id = 0
        new_node_graph = NodeConnectionGraph()
        replacement_node_map = {}

        for node in self.node_graph.nodes:
            old_node_id = node.node_id
            new_node = Node(next_node_id, node.node_data)
            new_node_graph.add_node(new_node)
            replacement_node_map[old_node_id] = new_node
            next_node_id += 1

        for connection in self.node_graph.connections:
            old_from_node_id = connection.from_node.node_id
            old_to_node_id = connection.to_node.node_id

            new_from_node = replacement_node_map[old_from_node_id]
            new_to_node = replacement_node_map[old_to_node_id]

            connection = NodeConnection(
                new_from_node,
                connection.outlet,
                new_to_node,
                connection.inlet,
            )
            new_node_graph.add_connection(connection)

        self.node_graph = new_node_graph

    @property
    def name(self):
        return self.container_node.subpatch_name

    @property
    def description(self):
        return self.container_node.description

    @property
    def input_nodes(self):
        nodes = []
        for node in self.node_graph.nodes:
            if node.node_class == HUB_NODE_CLASS and not self.node_graph.connections_to_node(node):
                nodes.append(node)

        return nodes

    @property
    def output_nodes(self):
        nodes = []
        for node in self.node_graph.nodes:
            if node.node_class == HUB_NODE_CLASS and not self.node_graph.connections_from_node(node):
                nodes.append(node)

        return nodes

    @property
    def node_cluster_nodes(self):
        # The "node cluster" includes any node that is not an input node, an output node,
        # or the container node.
        input_nodes = self.input_nodes
        output_nodes = self.output_nodes

        nodes = []
        for node in self.node_graph.nodes:
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
            'nodes': {str(n.node_id): n.as_dict for n in self.node_graph.nodes},
        }

    @staticmethod
    def from_file(filename):
        with open(filename, 'r') as f:
            subpatch_data = json.load(f)

            subpatch_version = subpatch_data.get('subpatch_version')
            if not subpatch_version:
                raise InvalidSubpatchException('Unable to parse subpatch')

            return Subpatch(subpatch_data)

    @staticmethod
    def extract_from_patch(patch, subpatch_name):
        container_nodes = SubpatchContainerNode.find_in(patch.node_graph.nodes)

        container_node = None
        for node in container_nodes:
            if node.subpatch_name == subpatch_name:
                container_node = node
                break

        if not container_node:
            raise SubpatchNotFoundException(f"Subpatch '{subpatch_name}' not found within patch")

        node_graph = NodeConnectionGraph()

        node_graph.add_node(container_node)

        for node in patch.node_graph.nodes:
            if container_node.contains(node):
                node_graph.add_node(node.clone())

        node_ids = node_graph.node_ids
        for connection in patch.node_graph.connections:
            if connection.from_node.node_id in node_ids and connection.to_node.node_id in node_ids:
                node_graph.add_connection(connection.clone())

        subpatch_dict = {
            'connections': [c.as_dict for c in node_graph.connections],
            'nodes': {str(n.node_id): n.as_dict for n in node_graph.nodes},
        }

        return Subpatch(subpatch_dict)

    def insert_into(self, patch, coords):
        SubpatchInjector(self).inject_into(patch, coords)

    def remove_from(self, patch):
        container_to_remove = None

        container_nodes = SubpatchContainerNode.find_in(patch.node_graph.nodes)
        for node in container_nodes:
            if node.subpatch_name == self.name:
                container_to_remove = node
                break

        if not container_to_remove:
            raise SubpatchNotFoundException(f'Subpatch not found within patch: {self.name}')

        nodes_to_remove = []
        for node in patch.node_graph.nodes:
            if container_to_remove.node_id == node.node_id or container_to_remove.contains(node):
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            patch.remove_node(node)

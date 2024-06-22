import json
import sys
from src.subpatch import Subpatch
from src.wire_patch import WirePatch


if __name__ == '__main__':
    patch_filename = sys.argv[1]
    subpatch_name = sys.argv[2]
    replacement_subpatch_filename = sys.argv[3]

    patch = WirePatch.from_file(patch_filename)
    subpatch = Subpatch.extract_from_patch(patch, subpatch_name)
    replacement_subpatch = Subpatch.from_file(replacement_subpatch_filename)

    coords = subpatch.container_node.bounds.coords
    subpatch.remove_from(patch)
    replacement_subpatch.insert_into(patch, coords)

    print(json.dumps(patch.as_dict, indent='\t'))

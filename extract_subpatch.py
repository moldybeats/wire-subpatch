import json
import sys
from src.subpatch import Subpatch
from src.wire_patch import WirePatch


if __name__ == '__main__':
    patch_filename = sys.argv[1]
    subpatch_name = sys.argv[2]

    patch = WirePatch.from_file(patch_filename)
    subpatch = Subpatch.extract_from_patch(patch, subpatch_name)

    print(json.dumps(subpatch.as_dict, indent='\t'))

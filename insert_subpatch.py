import json
import sys
from src.subpatch import Subpatch
from src.wire_patch import Coords, WirePatch


if __name__ == '__main__':
    patch_filename = sys.argv[1]
    subpatch_filename = sys.argv[2]
    x = float(sys.argv[3])
    y = float(sys.argv[4])

    patch = WirePatch.from_file(patch_filename)
    subpatch = Subpatch.from_file(subpatch_filename)
    subpatch.insert_into(patch, Coords(x, y))
    
    print(json.dumps(patch.as_dict, indent='\t'))

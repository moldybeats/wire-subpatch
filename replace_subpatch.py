import argparse
import json
from src.subpatch import Subpatch
from src.wire_patch import Coords, WirePatch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replace a subpatch within a Wire patch.')
    parser.add_argument('patch_filename', help='Filename of the Wire patch you want to insert into.')
    parser.add_argument('subpatch_name', help='Name of the subpatch to replace.')
    parser.add_argument('subpatch_filename', help='Filename of the subpatch to insert.')
    parser.add_argument('-x', help='Coordinates where the subpatch will be inserted (x).', type=int, default=0)
    parser.add_argument('-y', help='Coordinates where the subpatch will be inserted (y).', type=int, default=0)
    args = parser.parse_args()

    patch = WirePatch.from_file(args.patch_filename)
    subpatch = Subpatch.extract_from_patch(patch, args.subpatch_name)
    replacement_subpatch = Subpatch.from_file(args.subpatch_filename)

    subpatch.remove_from(patch)
    xy = Coords(float(args.x), float(args.y))
    replacement_subpatch.insert_into(patch, xy)

    print(json.dumps(patch.as_dict, indent='\t'))

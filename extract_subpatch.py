import argparse
import json
from src.subpatch import Subpatch
from src.wire_patch import WirePatch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract a subpatch from an existing Wire patch.')
    parser.add_argument('patch_filename', help='Filename of the Wire patch containing the subpatch you want to extract.')
    parser.add_argument('subpatch_name', help='Name of the subpatch to extract.')
    args = parser.parse_args()

    patch = WirePatch.from_file(args.patch_filename)
    subpatch = Subpatch.extract_from_patch(patch, args.subpatch_name)

    print(json.dumps(subpatch.as_dict, indent='\t'))

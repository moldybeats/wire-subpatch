# wire-subpatch
An experiment to try to emulate subpatching capabilities in Resolume Wire. Probably a terrible idea.

**NOTE: This is really just a proof of concept and is very experimental. There's a good chance it will corrupt your Wire patch files. Don't use it on anything important.**

Here's how it works:
- Inside a Wire patch, you define a subpatch by creating nodes within a Comment node. The text of the Comment node should start with **"Subpatch:"** followed by the name of your subpatch. You can put more details about the subpatch on the following lines. See the `examples` directory for some guidance.
- Any Hub nodes that don't have an input connection will be considered subpatch inputs.
- Any Hub nodes that don't have an output connection will be considered subpatch outputs.
- When a subpatch is inserted into an existing Wire patch, all nodes will be collapsed visually (ie. they will all overlap), except for input nodes (displayed on the left) and output nodes (displayed on the right).
- Use the `extract_subpatch.py` script to extract a subpatch from a Wire patch file. This script will output the JSON data for a subpatch, which you can then pipe to a file. So let's say you have a Wire patch called `MyWirePatch.wire`, a subpatch within that file called "My Subpatch", and you want to generate a subpatch file called `my_subpatch.subpatch`, you would do this: `python ./extract_subpatch.py MyWirePatch.wire "My Subpatch" > my_subpatch.subpatch`
- Use the `insert_subpatch.py` script to insert a subpatch into an existing Wire patch. This outputs a complete Wire patch with the original patch nodes plus the subpatch nodes. For example, if you have a Wire patch called `MyOtherWirePatch.wire`, you want to insert a subpatch called `my_subpatch.subpatch` and output the result to a file called `MyComboWirePatch.wire`, you would do this: `python ./insert_subpatch.py MyOtherWirePatch.wire my_subpatch.subpatch > MyComboWirePatch.wire`. You can also specify the coordinates where your subpatch will be inserted. For example: `python ./insert_subpatch.py MyOtherWirePatch.wire my_subpatch.subpatch -x 200 -y 200 > MyComboWirePatch.wire`
- I've found it's best to close Wire any time you're changing your Wire patch files with these scripts. Which makes sense. :)


Feel free to open issues for any problems you find, or submit PRs if you have some good example subpatches.

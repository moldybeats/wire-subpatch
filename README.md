# wire-subpatch
An experiment to try to emulate subpatching capabilities in Resolume Wire. Probably a terrible idea.

**This is a work in progress and very experimental. There's a good chance it will corrupt your Wire patch files. Don't use it on anything important.**

Here's how it works:
- Inside a Wire patch, create your subpatch nodes, then create a Comment node that encompasses all of them. The text of the Comment node should start with "Subpatch:" followed by the name of your subpatch. You can put more details about the subpatch on the following lines.
- Any Hub nodes that don't have an input connection will be considered subpatch inputs.
- Any Hub nodes that don't have an output connection will be considered subpatch outputs.
- Use the `extract-subpatch.py` script to extract the subpatch. For example: `python ./extract-subpatch.py MyWirePatch.wire "My Subpatch"`. This will output the JSON for a subpatch. You can pipe that to a file.
- Use the `insert-subpatch.py` script to insert a subpatch into an existing Wire patch. For example: `python ./insert-subpatch.py MyOtherWirePatch.wire my-subpatch.subpatch 0 0`. This will output the JSON for a complete Wire patch with the subpatch nodes inserted at the (x, y) coordinates you give in the final 2 arguments. All nodes from the subpatch will be inserted at the same place, overlapping to hide their connections, except for input nodes (added to the left) and output nodes (added to the right).

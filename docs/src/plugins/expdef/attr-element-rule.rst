.. SPDX-License-Identifier:  MIT

While this format treats keys mapping to subtrees and keys mapping to literal
attributes equivalently, SIERRA does not, in order to provide uniformity across
the different input file types it can handle. Two consequences follow, both of
which result in a warning being logged and *nothing* being modified (SIERRA does
not raise an error, and does not fall back to a "valid for this format" change):

- If you ask SIERRA to change an *attribute*, but the target key actually maps
  to a sub-tree (an *element*), the modification is refused.

- If you ask SIERRA to set an *attribute* value onto a key that is an
  *element*, the modification is likewise refused (an element is not clobbered
  by an attribute value).

An *array* value is treated as an attribute only when all of its members are
primitives (for example ``[80, 443]``). An array whose members are themselves
maps or lists is an element, and is subject to the element rules above. See
:ref:`plugins/expdef` for the full cross-format definition of attributes and
elements.

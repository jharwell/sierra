.. SPDX-License-Identifier:  MIT

.. tab-set-code::

   .. code-block:: XML

      <menu id="file" value="File">
       <popup>
         <menuitem value="New" onclick="CreateNewDoc()" />
         <menuitem value="Open" onclick="OpenDoc()" />
         <menuitem value="Close" onclick="CloseDoc()" />
       </popup>
      </menu>

   .. code-block:: JSON

      {"menu": {
         "id": "file",
         "value": "File",
         "popup": {
           "menuitem": [
             {"value": "New", "onclick": "CreateNewDoc()"},
             {"value": "Open", "onclick": "OpenDoc()"},
             {"value": "Close", "onclick": "CloseDoc()"}
            ]
         }
      }}


   .. code-block:: YAML

      menu:
        id: file
        value: File
        popup:
          menuitem:
             - value: New
               onclick: CreateNewDoc()
             - value: Open
               onclick: OpenDoc()
             - value: Close
               onclick: CloseDoc()

In the above, ``{menu, popup, menuitem}`` are tags, and each identify
unique elements. ``{id, value, onclick}`` are tags identifying attributes.

The distinction between an *array-valued attribute* and an *element* is
illustrated below (JSON/YAML only; XML attribute values are always scalars):

.. tab-set-code::

   .. code-block:: JSON

      {"server": {
         "ports": [80, 443],
         "backends": [
           {"host": "a", "weight": 1},
           {"host": "b", "weight": 2}
         ]
      }}

   .. code-block:: YAML

      server:
        ports:
          - 80
          - 443
        backends:
          - host: a
            weight: 1
          - host: b
            weight: 2

Here ``ports`` is a tag identifying an *attribute*: its value is a flat array of
scalars, so SIERRA can read and modify it as an attribute. ``backends`` is a tag
identifying an *element*: its value is an array whose members are maps, so it is
a sub-tree, not an attribute.

.. SPDX-License-Identifier:  MIT

.. tabs::

   .. group-tab:: XML

      .. code-block:: XML

         <menu id="file" value="File">
          <popup>
            <menuitem value="New" onclick="CreateNewDoc()" />
            <menuitem value="Open" onclick="OpenDoc()" />
            <menuitem value="Close" onclick="CloseDoc()" />
          </popup>
         </menu>

   .. group-tab:: JSON

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


   .. group-tab:: YAML

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

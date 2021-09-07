=={{ '=' * node.name|length }}==
``{{ node.name }}``
=={{ '=' * node.name|length }}==

.. automodule:: {{ node.name }}

   .. contents::
      :local:
{##}
{%- block modules -%}
{%- if subnodes %}

.. toctree::
{% for item in subnodes %}
   {{ item.name }}
{%- endfor %}
{##}
{%- endif -%}
{%- endblock -%}
{##}
.. currentmodule:: {{ node.name }}
{##}
{%- block functions -%}
{%- if node.functions %}

{% for item, obj in node.functions.items() -%}
- :py:func:`{{ item }}`:
  {{ obj|summary }}

{% endfor -%}

{% for item in node.functions %}
.. autofunction:: {{ item }}
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock -%}

{%- block classes -%}
{%- if node.classes %}

{% for item, obj in node.classes.items() -%}
- :py:class:`{{ item }}`:
  {{ obj|summary }}

{% endfor -%}

{% for item in node.classes %}
.. autoclass:: {{ item }}
   :members:

   .. rubric:: Inheritance
   .. inheritance-diagram:: {{ item }}
      :parts: 1
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock -%}

{%- block exceptions -%}
{%- if node.exceptions %}

Exceptions
==========

{% for item, obj in node.exceptions.items() -%}
- :py:exc:`{{ item }}`:
  {{ obj|summary }}

{% endfor -%}

{% for item in node.exceptions %}
.. autoexception:: {{ item }}

   .. rubric:: Inheritance
   .. inheritance-diagram:: {{ item }}
      :parts: 1
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock -%}

{%- block variables -%}
{%- if node.variables %}

{% for item, obj in node.variables.items() -%}
- :py:data:`{{ item }}`
{% endfor -%}

{% for item, obj in node.variables.items() %}
.. autodata:: {{ item }}
   :annotation:

   .. code-block:: text

      {{ obj|pprint|indent(6) }}
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock -%}

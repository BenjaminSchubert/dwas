{%- set data = [
   (attributes, "Module Attributes", "autoattribute"),
   (classes, "Classes", "autoclass"),
   (functions, "Functions", "autofunction"),
   (exceptions, "Exceptions", "autoexception"),
]
-%}
{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

Inventory
---------

{%- for type, title, _auto in data -%}
{% if type %}
{{ _(title) | underline("^")}}

.. autosummary::
   :nosignatures:
   {% for item in type %}
   {{ item }}
   {%- endfor %}
{% endif %}
{% endfor -%}

{% if modules %}
.. rubric:: Modules

.. autosummary::
   :toctree:
   :recursive:
   :template: autosummary/public_api.rst
{% for item in modules %}
   {{ item }}
{% endfor %}
{% endif %}

{%- for type, title, autovalue in data -%}
{% if type %}
{{ _(title) | underline("-") }}
{% for item in type %}
.. {{ autovalue }}:: {{ fullname }}.{{ item }}
{%- endfor %}
{% endif %}
{% endfor -%}

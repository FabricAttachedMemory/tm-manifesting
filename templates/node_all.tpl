<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}</TITLE>
</HEAD>

<BODY>
<H1>
    <IMG SRC='/static/manifest.jpg' align='middle'>
    {{ nodes|length }} {{ label }}
</H1>

{% for node in nodes %}
    <a href="{{ url_base }}{{ node.coordinate }}">{{ node.coordinate }}</a> @ {{ node.hostname }}<br>
{% endfor %}
</BODY>
</HTML>

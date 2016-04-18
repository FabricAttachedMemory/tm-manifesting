<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}</TITLE>
</HEAD>

<BODY>
<H1>
    <IMG SRC='/static/manifest.jpg' align='middle'>
    {{ keys|length }} {{ label }}
</H1>

{% for key in keys %}
    <a href="{{ url_base }}{{ key }}">{{ key }}</a>,
{% endfor %}
</BODY>
</HTML>

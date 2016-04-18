<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}: {{ name }}</TITLE>
</HEAD>

<BODY>
<H1>
<IMG SRC='/static/manifest.jpg' align='middle'>
{{ label }}: {{ name }}
</H1>

<dl>
    {% for key, value in itemdict.items() %}
        <dt>{{ key }}</dt>
        <dd>{{ value }}</dd>
	<p>
    {% endfor %}
<dl>

</BODY>
</HTML>

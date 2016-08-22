<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}: {{ name }}</TITLE>
</HEAD>

<BODY>
<H1>
<IMG SRC='/static/manifest.jpg' align='middle'>
Manifest Binding Details
</H1>

<p>
<dl>
    <dt>{{ node.coordinate }}</dt>
    <p>
    <dd>Hostname: {{ node.hostname }}</dd>
    <p>
{%if ESPURL|length  %}
    <dd>Manifest: {{ status.manifest }}</dd>
    <dd>Status: {{ status.status }}</dd>
    <dd>Details: {{ status.message }}</dd>
    <dd>SDHC/USB image: <a href="{{ ESPURL }}">{{ node.hostname }}.ESP (256M)</a></dd>
{% else %}
    <dd>No manifest is currently bound to this node.</dd>
{% endif %}
<dl>

</BODY>
</HTML>

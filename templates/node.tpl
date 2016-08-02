<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}: {{ name }}</TITLE>
</HEAD>

<BODY>
<H1>
<IMG SRC='/static/manifest.jpg' align='middle'>
Node to manifest
</H1>

<dl>
    <dt>{{ node.coordinate }}</dt>
    <dd>{{ node.hostname }}<br>{{ manifest }}</dd>
<dl>

</BODY>
</HTML>

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
    <dd>{{ node.soc.socMacAddress }}<br>{{ manifest }}</dd>
<dl>

</BODY>
</HTML>

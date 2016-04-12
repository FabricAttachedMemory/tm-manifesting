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
    <a href="{{ url_base }}{{ key }}">{{ key }}</a><br>
{% endfor %}

<p>
<hr><!-------------------------------------------------------------------->
<p>
<form action='' method="POST" enctype="multipart/form-data">
<b>Upload new manifest</b>
<input type='file' name='file[]'><!-- multiple='' -->
<input type='submit' value='Send'>
</form>

<p>
<font color='green'>{{ okmsg }}</font>
<font color='red'>{{ errmsg }}</font>

</BODY>
</HTML>

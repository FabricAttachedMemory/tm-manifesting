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
    <a href="{{ base_url }}{{ key }}">{{ key }}</a><br>
{% endfor %}

<p>
<hr><!-------------------------------------------------------------------->
<h3>Manifest template</h3>
Copy and paste this to a file, fill out packages and tasks,  and upload it.
<PRE>
{
"_comment": "Comments are allowed at any point",
"name": "NoSpacesOrPunctuation",
"description": "Do nothing",
"release": "the operating system release (unstable/testing/stable)",
"tasks" : [],
"packages": []
}
</PRE>
<hr><!-------------------------------------------------------------------->
<p>
<H3>Upload new manifest</H3>
<form action='' method="POST" enctype="multipart/form-data">
<input type='file' name='file[]'><!-- multiple='' -->
<input type='submit' value='Send'>
</form>

<p>
<font color='green'>{{ okmsg }}</font>
<font color='red'>{{ errmsg }}</font>

</BODY>
</HTML>

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
<b>{{node.hostname}} @ {{node.coordinate}}</b>
</p>
{% if status.status == 'ready' or status.status == 'error' %}

    <p>
    {% if status.status == 'error' %}
	Binding to "{{status.manifest}}" failed:<p>{{status.message}}</p>
    {% else %}
	Currently bound to "{{status.manifest}}"
    {% endif %}
    <p>

	<form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
		<input type='submit' name='unbind' value='Unbind'
		 onClick='window.location.reload()'>
        </form>

{% elif not status or status.status != 'building' %}

 	<form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
	Select a manifest&nbsp;&nbsp;
	<select name='manifest_sel'>
                {% for manifest in manifests %}
                    <option value="{{manifest}}">{{manifest}}</option>
                {% endfor %}
        </select>
        &nbsp; and then click &nbsp;
	    <input type="submit" name='bind' value='Bind'>
        </form>
    </p>
{% endif %}
</p>

<p>
{% if status is none %}
        No manifest is currently bound to this node.</dd>
{% elif status.status == 'building' %}
        Building image for manifest "{{ status.manifest }}: {{ status.message }}
{% elif status.status == 'ready' %}
    "{{ status.manifest }}" binding is complete; {{ status.message }}.
    <p>
    {% if ESPURL is none %}
    	No SDHC/USB image was built.
    {% else %}
    SDHC/USB image: <a href="{{ ESPURL }}">{{ node.hostname }}.ESP ({{ ESPsizeMB }}M)</a>
{% endif %}
{% endif %}
</p>

</BODY>
</HTML>

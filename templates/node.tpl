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

    <dd>
        {% if status.status == 'ready' %}
        <p> {{base_url}}{{node.coordinate}}<br>
            <form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
                <input type='submit' name='unbind' value='Unbind' onClick='window.location.reload()'>
            </form>
        </p>
        {%endif %}

    <p>Manifests:
        <form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
            <select name='manifest_sel'>
                {% for manifest in manifests %}
                    <option value="{{manifest}}">{{manifest}}</option>
                {% endfor %}
            </select>
            <input type="submit" name='bind' value='Bind'>
        </form>
    </p>
    </dd>

    <dt>{{ node.coordinate }}</dt>
    <p>
    <dd>Hostname: {{ node.hostname }}</dd>
    <p>
    {% if status is none %}
        <dd>No manifest is currently bound to this node.</dd>
    {% elif status.status == 'building' %}
        <dd>Building image for manifest "{{ status.manifest }}:
            {{ status.message }}
        </dd>
{% elif status.status == 'ready' %}
    <dd>"{{ status.manifest }}" binding is complete; {{ status.message }}.</dd>
    <p>
    {% if ESPURL is none %}
        <dd>No SDHC/USB image was built.</dd>
    {% else %}
        <dd>SDHC/USB image: <a href="{{ ESPURL }}">{{ node.hostname }}.ESP (256M)</a></dd>
    {% endif %}
{% endif %}
<dl>

</BODY>
</HTML>

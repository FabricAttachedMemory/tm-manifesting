<!doctype html>
<HTML>
<HEAD><TITLE>{{ label }}: {{ node.hostname }}</TITLE>
</HEAD>

<BODY>

<nav class="navbar navbar-inverse navbar-static-top" style="margin-bottom: 0;">
    <div class="container-fluid">
        <div class="navbar-header">
            <a class="navbar-brand" href="#" style="text-align:center; margin:auto; padding-top: 5px;">
                <img alt="Brand" src="/static/banner.jpg">
            </a>
          <ul class="nav navbar-nav">

            <li>
                <a href="{{url_base}}../">
                    <span class="glyphicon glyphicon-globe" aria-hidden="true">
                        TMMS
                    </span>
                </a>
            </li>

            <li>
                <a href="{{url_base}}../node/">
                    <span class="glyphicon glyphicon-king" aria-hidden="true">
                        Nodes
                    </span>
                </a>
            </li> <!-- nodes menu btn -->

            <li>
                <a href="{{url_base}}../manifest/">
                    <span class="glyphicon glyphicon-tower" aria-hidden="true">
                        Manifests
                    </span>
                </a>
            </li> <!-- manifests menu btn -->

            <li>
                <a href="{{url_base}}../tasks/">
                    <span class="glyphicon glyphicon-bishop" aria-hidden="true">
                        Tasks
                    </span>
                </a>
            </li> <!-- tasks menu btn -->

            <li class="active">
                <a href="{{url_base}}../packages/">
                    <span class="glyphicon glyphicon-pawn" aria-hidden="true">
                        Packages
                    <span class="sr-only">(current)</span>
                    </span>
                </a>
            </li> <!-- packages menu btn -->

          </ul> <!-- Navbar menu buttons -->
        </div>
    </div>
</nav>

<div class="row" id="headerBg" style="background-image: url('/static/header_bg1.jpg');">
       <!-- <img SRC='/static/manifest.jpg' align='middle'> -->
    <div class="col-md-11 text-center" style='font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif'>
        <h1>TMMS: Packages</h1>
    </div>

    <div class="col-md-11 text-center">
        <p>
            Read-only views of all available L4TM packages and their details.
            The source repo is http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm-pushed,
            release catapult.
        </p>
    </div>


    <div class="col-md-8" style="margin-bottom:-1%;">
        <h4><span class="label label-default">Total number of packages: {{ keys | length }}</span></h4>
    </div>
    <div class="col-md-8">
        <h4><span class="label label-default">Location: {{ base_url }}</span></h4>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>



<H1>
<IMG SRC='/static/manifest.jpg' align='middle'>
Manifest Binding Details
</H1>

<p>
<b>{{node.hostname}} @ {{node.coordinate}}</b>
</p>

<p>
{% if status is none %}
    No manifest is currently bound to this node.</dd>
    {% set action = 'bind' %}
{% elif status.status == 'building' %}
    Building image for manifest "{{ status.manifest }}": {{ status.message }}
    {% set action = 'NADA' %}
{% elif status.status == 'error' %}
    Binding to "{{status.manifest}}" failed:<p>{{status.message}}</p>
    {% set action = 'bind' %}
{% elif status.status == 'ready' %}
    Currently bound to "{{status.manifest}}"
    {% set action = 'unbind' %}
    <p>
    {% if ESPURL is none %}
    	No SDHC/USB image was built.
    {% else %}
        SDHC/USB image: <a href="{{ ESPURL }}">{{ node.hostname }}.ESP ({{ ESPsizeMB }}M)</a>
    {% endif %}
    </p>
{% endif %}

<p>
{% if action == 'unbind' %}
	<form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
		<input type='submit' name='unbind' value='Unbind'/>
        </form>

{% elif action == 'bind' %}

 	<form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
	Select a manifest&nbsp;&nbsp;
	<select name='manifest_sel'>
                {% for manifest in manifests %}
                    <option value="{{ manifest }}">{{ manifest }}</option>
                {% endfor %}
        </select>
        &nbsp; and then click &nbsp;
	    <input type="submit" name='bind' value='Bind'/>
        </form>
{% endif %}
</p>

<!-- chroot install details -->
{% if installlog is not none and (status.status == 'ready' or status.status == 'building') %}
<hr>
<h4>chroot install script</h4>
<pre>{{ installsh }}</pre>
<p>
<hr>
<h4>chroot install log</h4>
<pre>{{ installlog }}</pre>
{% endif %}

</BODY>
</HTML>

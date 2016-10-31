<!doctype html>
<html>
<head><title>{{ label }}: {{ node.hostname }}</title>
<link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="{{url_for('static', filename='plugins/jquery.min.js')}}"></script>
<!-- Bootstrap css link (on this server) -->
<link rel="stylesheet" href="{{url_for('static', filename='plugins/bootstrap/css/bootstrap.min.css')}}">
<link rel="stylesheet" href="{{url_for('static', filename='plugins/local/css/layout.css')}}">

</head>

<body>

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

            <li class="active">
                <a href="{{url_base}}">
                    <span class="glyphicon glyphicon-king" aria-hidden="true">
                        Nodes
                    </span>
                    <span class="sr-only">(current)</span>
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

            <li>
                <a href="{{url_base}}../packages/">
                    <span class="glyphicon glyphicon-pawn" aria-hidden="true">
                        Packages
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
        <h2>Node: "{{node.hostname}}"</h2>
    </div>

    <div class="col-md-2"></div>

    <div class="col-md-7 text-center">
        <p>
Query the manifest currently specified for a node
        </p>
        <p>
The “building” status is transient and will transition to either “ready” or “error”,
depending on whether the building process succeeds or not. If the status is “error”,
then the message value will contain additional information about the cause of the
error which can be presented to the user. Once the list of error causes has been
determined, we’ll list those here.
        </p>
    </div>

    <div class="col-md-8">
        <h4><span class="label label-primary">Location: {{ base_url }}<i>{{node.coordinate}}</i></h4>
        </span>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<div class="row" style="margin-top:2%;">
    <div class="col-md-2"></div>

{% if status is none %}
    {% set alert_type = 'info'  %}
    {% set alert_msg = 'No manifest is currently bound to this node.' %}
    {% set action = 'bind' %}
{% elif status.status == 'building' %}
    {% set alert_type = 'warning'  %}
    {% set alert_msg = 'Building image for manifest "status.manifest" : "status.message"' %}
    {% set action = 'NADA' %}
{% elif status.status == 'error' %}
    {% set alert_type = 'danger'  %}
    {% set alert_msg = 'Binding to <label class="label label-default">' +
                        + status.manifest +
                        '</label> failed: <label class="label label-info">' +
                        + status.message +
                        '</label>' %}
    {% set action = 'bind' %}

{% elif status.status == 'ready' %}
    {% set alert_type = 'success'  %}
    {% set alert_msg = 'Currently bound to' +
                        ' <label class="label label-default">'
                        + status.manifest +
                        '</label> manifest' %}
    {% set action = 'unbind' %}
{% endif %}

    <div class="alert alert-{{alert_type}} col-md-7" role="alert" style="text-align:center;">
            <h4>{{alert_msg}}</h4>
    </div>
</div>


<div class="row">
    <div class="col-md-2"></div>
    {% if ESPURL is none %}
            <div class="alert alert-warning col-md-7" role="alert" style="text-align:center;">
                No SDHC/USB image was built.
            </div>
    {% else %}
        <div class="alert alert-info col-md-7" role="alert" style="text-align:center;">
            <h4>SDHC/USB image:
                <a class="alert-link" href="{{ ESPURL }}">
                    {{ node.hostname }}.ESP ({{ ESPsizeMB }}M)
                </a>
            </h4>
        </div>
    {% endif %}
</div>

<div class="row">
{% if action == 'unbind' %}
    <form action='{{base_url}}{{node.coordinate}}' method='POST' enctype="multipart/form-data">
        <div class="col-md-11" style="text-align:center;">
        <input class="btn btn-danger btn-md" type='submit' name='unbind' value='Unbind Node'/>
        </div>
    </form>
{% elif action == 'bind' %}
    <div class="col-md-4"></div>

    <form action='{{base_url}}{{node.coordinate}}'
            class="form-inline"
            method='POST'
            enctype="multipart/form-data">
        <div class="form-group">
            <label for="manifest_sel" style="margin-right:5px;">
                Select a manifest
            </label>
            <select id="manifest_sel" class="form-control input-sm" name='manifest_sel'>
                {% for manifest in manifests %}
                <option value="{{ manifest }}">{{ manifest }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group" style="margin-left:5px;">
            <label for="bindBtn">and then click</label>
            <input id="bindBtn" class="btn btn-success" type="submit" name='bind' value='Bind'/>
        </div>
    </form>
{% endif %}
</div>

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

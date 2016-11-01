<!doctype html>
<html>
<head><title>{{ name }}</title>
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
                <a href="{{base_url}}/../../">
                    <span class="glyphicon glyphicon-globe" aria-hidden="true">
                        TMMS
                    </span>
                </a>
            </li>

            <li>
                <a href="{{base_url}}/../../node/">
                    <span class="glyphicon glyphicon-king" aria-hidden="true">
                        Nodes
                    </span>
                </a>
            </li> <!-- nodes menu btn -->

            <li class="active">
                <a href="{{base_url}}/../">
                    <span class="glyphicon glyphicon-tower" aria-hidden="true">
                        Manifests
                    </span>
                    <span class="sr-only">(current)</span>
                </a>
            </li> <!-- manifests menu btn -->

            <li>
                <a href="{{base_url}}/../../tasks/">
                    <span class="glyphicon glyphicon-bishop" aria-hidden="true">
                        Tasks
                    </span>
                </a>
            </li> <!-- tasks menu btn -->

            <li>
                <a href="{{base_url}}/../../packages/">
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
        <h2>Manifest: "{{name}}"</h2>
    </div>

    <div class="col-md-2"></div>

    <div class="col-md-7 text-center">
        <p>
 The Machine OS Manifesting Service (TMMS) stores a list of manifests that can be
used to configure the OS for a set of nodes. Those manifests live in the /manifest
tree of the manifesting service. Manifests may be uploaded and downloaded from
the TMMS and the list of available manifests queried.
        </p>
    </div>

    <div class="col-md-8">
        <h4><span class="label label-primary">Location: {{ base_url }}</h4>
        </span>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<div class="row">
    <div class="col-md-2"></div>
    <div class="col-md-5">
        <table class="table table-hover" style="">
            <thead>
                <th>Field</th>
                <th>Value</th>
            </thead>
        {% for field in data.thedict %}
            <tr>
                <td>{{field}}</td>
                <td>{{data.thedict[field]}}</td>
            </tr>
        {% endfor %}
        </table>
    </div>

</div>

<div class="row">
    <div class="col-md-2"></div>
    <div class="col-md-5">
        <div class="panel panel-default">
            <div class="panel-heading">
                Raw Manifest Json
            </div>
            <div class="panel-body">
                {{ rawtext }}
            </div>
        </div>
    </div>
</div>


<!-- dl>
    {% for key, value in itemdict.items() %}
        <dt>{{ key }}</dt>
        <dd>{{ value }}</dd>
	<p>
    {% endfor %}
<dl -->

</BODY>
</HTML>

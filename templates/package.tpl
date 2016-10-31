<!doctype html>
<html>
<head><title>{{ label }}: {{ name }}</title>

<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="{{url_for('static', filename='plugins/jquery.min.js')}}"></script>
<script src="{{url_for('static', filename='plugins/bootstrap/js/bootstrap.min.js')}}"></script>
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
    <div class="col-md-11 text-center" style='font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif'>
        <h4 class="shadowText" style="margin-top:2%;">Metadata of the Package: "{{name}}"</h4>
    </div>

    <div class="col-md-11 text-center">
    </div>

    <div class="col-md-8">
        <h4><span class="label label-default">Location: {{base_url}}/package/{{name}}</span></h4>
    </div>

  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<div class="row" style="margin-top:0%;">

    <div class="col-md-2">
    </div>

    <ul class="list-group">
        <li class="list-group-item col-md-8">
        {% for key, value in itemdict.items() %}
          <ul class="row list-inline">
            <li class="col-md-1"><label></label></li>

            <li class="col-md-2"><label>{{key}}</label></li>
            <li class="col-md-9">{{value}}</li>
          </ul>
        {% endfor %}
        </li>
    </ul>
</div>

<div class="row" style="margin-top:2%;">
    <div class="col-md-3">
        <a class="btn btn-success" href="{{base_url}}/../../packages/" style="margin-left:4%;">Back to Packages</a>
    </div>
</div>

</body>
</html>

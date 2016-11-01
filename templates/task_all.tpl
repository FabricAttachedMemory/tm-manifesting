<!doctype html>
<title>
<head><title>{{ label }}</title>
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
                <a href="{{base_url}}../">
                    <span class="glyphicon glyphicon-globe" aria-hidden="true">
                        TMMS
                    </span>
                </a>
            </li>

            <li>
                <a href="{{base_url}}../node/">
                    <span class="glyphicon glyphicon-king" aria-hidden="true">
                        Nodes
                    </span>
                </a>
            </li> <!-- nodes menu btn -->

            <li>
                <a href="{{base_url}}../manifest/">
                    <span class="glyphicon glyphicon-tower" aria-hidden="true">
                        Manifests
                    </span>
                </a>
            </li> <!-- manifests menu btn -->

            <li class="active">
                <a href="{{base_url}}/../tasks/">
                    <span class="glyphicon glyphicon-bishop" aria-hidden="true">
                        Tasks
                    </span>
                    <span class="sr-only">(current)</span>
                </a>
            </li> <!-- tasks menu btn -->

            <li>
                <a href="{{base_url}}../packages/">
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
        <h2>TMMS: "Tasks"</h2>
    </div>

    <div class="col-md-2"></div>

    <div class="col-md-7 text-center">
        <p>
Tasks are works by the principle of tasks of the Tasksel. Each task defines a
list of packages that can be used in the manifests.
        </p>
    </div>

    <div class="col-md-8">
        <h4><span class="label label-primary">Number Of Tasks: {{ keys|length }}</h4>
        <h4><span class="label label-primary">Location: {{ base_url }}</h4>
        </span>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<div class="row">
    <div class="col-md-2"></div>
    <div class="container col-md-4" style="margin-top: 2%;">
            <div class="list-group" style="
    -webkit-box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
    -moz-box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
    box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
    ">
            {% for key in keys %}
                <a href="{{ base_url }}../task/{{ key }}" class="list-group-item">{{ key }}</a>
            {% endfor %}
            </div>
        </div>
    </div>
</div>

</body>
</html>

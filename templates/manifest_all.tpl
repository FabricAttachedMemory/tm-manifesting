<!doctype html>
<html>
<head><title>{{ label }}</title>

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

            <li class="active">
                <a href="{{base_url}}../manifest/">
                    <span class="glyphicon glyphicon-tower" aria-hidden="true">
                        Manifests
                    </span>
                    <span class="sr-only">(current)</span>
                </a>
            </li> <!-- manifests menu btn -->

            <li>
                <a href="{{base_url}}../tasks/">
                    <span class="glyphicon glyphicon-bishop" aria-hidden="true">
                        Tasks
                    </span>
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
        <h2>Manifests</h2>
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
        <h4><span class="label label-primary">Number of manifests: {{ keys | length }}</h4>
        <h4><span class="label label-primary">Location: {{ base_url }}</h4>
        </span>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>


<div class="container" style="margin-top: 2%;">
    <div class="col-md-2"></div>
        <div class="list-group" style="
-webkit-box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
-moz-box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
box-shadow: -1px -5px 49px -16px rgba(0,0,0,0.75);
">
        {% for key in keys %}
            <a href="{{ base_url }}{{ key }}" class="list-group-item">{{ key }}</a>
        {% endfor %}
        </div>
    </div>
</div>

<hr><!-------------------------------------------------------------------->
<div class="container">


    <h3>Upload new manifest</h3>
    <form class='form-inline' action='' method="POST" enctype="multipart/form-data">
        <div class='form-group'>
            <input type='file' name='file[]' style='display:;'><!-- multiple='' -->
        </div>
        <div class='form-group'>
                <span class="glyphicon glyphicon-hand-right" aria-hidden="true"></span>
                <input class='btn btn-success btn-sm' type='submit' value='Send'>
        </div>
    </form>

{% if okmsg %}
    <div class="alert alert-success col-md-5" style="text-align:center;" role="alert">{{okmsg}}</div>
{% elif errmsg %}
    <div class="alert alert-danger col-md-5" style="text-align:center;" role="alert">{{errmsg}}</div>
{% endif %}
</div>

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

</BODY>
</HTML>

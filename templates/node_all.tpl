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

            <li class="active">
                <a href="{{url_base}}../node/">
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
        <h2>TMMS: Nodes</h2>
    </div>
    <div class="col-md-2"></div>

    <div class="col-md-7 text-center">
        <p>
        Each node within the system has a manifest associated with it. When rebooted,
        the node will load an OS image constructed for it from the specified manifest.
        All node information is stored under the coordinate for the respective node.
        </p>
    </div>


    <div class="col-md-8" style="margin-bottom:-1%;">
        <h4><span class="label label-default">Total number of nodes: {{ nodes | length }}</span></h4>
    </div>
    <div class="col-md-8">
        <h4><span class="label label-default">Location: {{ base_url }}</span></h4>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<div class="container" style="
-webkit-box-shadow: 0px 0px 9px -1px rgba(0,0,0,0.75);
-moz-box-shadow: 0px 0px 9px -1px rgba(0,0,0,0.75);
box-shadow: 0px 0px 9px -1px rgba(0,0,0,0.75);
margin-top:1%;
">

<table class="table table-hover" style="">
    <thead>
        <th>Enclosure</th>
        <th>Coordinate</th>
        <th>Hostname</th>
        <th>Manifest</th>
        <th>Status</th>
    </thead>

    <tbody>
{% for node in nodes %}
        <tr>
            <td style="text-align:center;"><label class="label label-default">{{node.enc}}</label></td>
            <td><a href="{{ base_url }}{{ node.coordinate }}">{{ node.coordinate }}</a></td>
            <td><a href="{{ base_url }}{{ node.coordinate }}" class="label label-info">{{node.hostname}}</a></td>
            <td><label class="label label-default">{{ node.manifest }}</label></td>

<!-- Set lable type based of the status of the node -->
        {% if node.status == "ready" %}
            <td>
                <a class="label label-success" href="{{ base_url }}{{ node.coordinate }}">
                    {{ node.status }}
                </a>
            </td>
        {% endif %}
        {% if node.status == "building" %}
            <td>
                <a class="label label-warning" href="{{ base_url }}{{ node.coordinate }}">
                    {{ node.status }}
                </a>
            </td>
        {% endif %}
        {% if node.status == "error" %}
            <td>
                <a class="label label-danger" href="{{ base_url }}{{ node.coordinate }}">
                    {{ node.status }}
                </a>
            </td>
        {% endif %}

        </tr>
{% endfor %}
    </tbody>

</table>
</div>


</body>
</html>

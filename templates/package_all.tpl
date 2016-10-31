<!doctype html>
<html>
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
                <a href="{{url_base}}../">
                    <span class="glyphicon glyphicon-globe" aria-hidden="true">
                        TMMS
                    </span>
                </a>
            </li>

            <li>
                <a href="{{url_base}}node/">
                    <span class="glyphicon glyphicon-king" aria-hidden="true">
                        Nodes
                    </span>
                </a>
            </li> <!-- nodes menu btn -->

            <li>
                <a href="{{url_base}}manifest/">
                    <span class="glyphicon glyphicon-tower" aria-hidden="true">
                        Manifests
                    </span>
                </a>
            </li> <!-- manifests menu btn -->

            <li>
                <a href="{{url_base}}tasks/">
                    <span class="glyphicon glyphicon-bishop" aria-hidden="true">
                        Tasks
                    </span>
                </a>
            </li> <!-- tasks menu btn -->

            <li class="active">
                <a href="{{url_base}}packages/">
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



<div class="row">
    {% for key in alphabetic_sets.keys()|sort %}
        <!-- Trigger the modal with a button -->
        <div class="col-md-3">
            <ul class="list-group" data-toggle="modal" data-target="#PkgModal_{{key}}" style="cursor:pointer;">
              <li class="list-group-item" style="text-align:center;">
                <span class="badge">{{alphabetic_sets[key]|length}}</span>
                Package Set "{{key}}"
              </li>
            </ul>
        </div>

        <!-- Modal -->
        <div id="PkgModal_{{key}}" class="modal fade" role="dialog">
          <div class="modal-dialog">

            <!-- Modal content-->
            <div class="modal-content">
              <div class="modal-header info">
                <button type="button" class="close" data-dismiss="modal">&times;</button>
                <h3 class="modal-title" style="text-align: center;">Packages Set "{{key}}"</h3>
              </div>
              <div class="modal-body">

<!-- NOTE: base_url is pointint to host_url/packages/, which is incorrect differect
for a single package query: host_url/package/ - (plural vs singular. Thus, we take
a base url, stepping back and hardcoding package/{{pkg}} part to get the right link.) -->
        {% for pkg in alphabetic_sets[key]|sort %}
                    <a class="btn btn-danger" href="{{ base_url }}../package/{{ pkg }}" style="margin:1% 1% 1% 1%;">{{ pkg }}</a>
        {% endfor %}

              </div>
            </div>

          </div>
        </div>

    {% endfor %}
</div>

</BODY>
</HTML>

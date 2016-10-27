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
            <!-- <a class="navbar-brand" href="#">
                TMMS
            </a> -->
            <a class="navbar-brand" href="#" style="text-align:center; margin:auto; padding-top: 5px;">
                <img alt="Brand" src="/static/banner.jpg">
            </a>
            <a class="navbar-brand" href="{{base_url}}../" style="padding-top: 12px;">
                TMMS
            </a>
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

        {% for pkg in alphabetic_sets[key]|sort %}
                    <a class="btn btn-danger" href="{{ base_url }}{{ pkg }}" style="margin:1% 1% 1% 1%;">{{ pkg }}</a>
        {% endfor %}

              </div>
            </div>

          </div>
        </div>

    {% endfor %}
</div>

</BODY>
</HTML>

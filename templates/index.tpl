<!doctype html>
<HTML>

<head><title>Manifesting API 4 The Machine</title>

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

            <li class="active">
                <a href="{{url_base}}">
                    <span class="glyphicon glyphicon-globe" aria-hidden="true">
                        TMMS
                    <span class="sr-only">(current)</span>
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

            <li>
                <a href="{{url_base}}packages/">
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
        <h1>Manifesting for The Machine (TMMS)</h1>
    </div>

    <div class="col-md-11 text-center">
        <p>
            The <a href='http://hlinux-build.us.rdlabs.hpecorp.net/~packardk/software-arch.pdf'>L4TM Software ERS</a> chapter 8
            describes the Manifesting service.  The functions in chapter 7,
            Provisioning, are also covered by this service.
            <br>
            The following topics and links show the type of data available behind
            the API.  The actual API endpoints are given for each topic.
        </p>
        <p>
        To exercise the APIs, get a browser plugin like <a href="http://restclient.net/">RESTClient</a>.
        </p>
    </div>

    <div class="col-md-8" style="margin-bottom:-1%;">
        <h5><span class="label label-default">API Version: 1.0</span></h5>
    </div>
    <div class="col-md-8">
        <h4><span class="label label-default">Location: {{ coordinate }}</span></h4>
    </div>
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>


<!-- ****************** -->

<div class="row" style="margin-top:4%;">
    <div class="col-md-2">
    </div>

    <div class="col-md-4">
        <a href="{{base_url}}node/">
            <h3>
                <span class="glyphicon glyphicon-king" aria-hidden="true"></span>
                    Nodes
            </h3>
        </a>

        <div class="col-md-12 text-justify">
        Apply a manifest to a node by creating a kernel and custom file system
        image and moving those items into the TFTP hierarchy.
        NOTE: this does NOT reboot the node; that's done by the Assembly Agent.
        </div>
    </div>

    <div class="col-md-5">
        <a href="{{base_url}}manifest">
            <h3><span class="glyphicon glyphicon-tower" aria-hidden="true"></span>
                Manifests
            </h3>
        </a>

        <div class="col-md-10 text-justify">
        The Machine OS Manifesting Service (TMMS) stores a list of manifests that
        can be used to configure the OS for a set of nodes. Those manifests live
        in the /manifest tree of the manifesting service. Manifests may be uploaded
        and downloaded from the TMMS and the list of available manifests queried.
        </div>
    </div>
            <n class="glyphicon glyphicon-tower" aria-hidden="true"></span>/li>

</div> <!-- row -->


<div class="row" style="margin-top:2%; margin-bottom:5%;">
    <div class="col-md-2">
    </div>

    <div class="col-md-4">
        <a href="{{base_url}}tasks/">
            <h3><span class="glyphicon glyphicon-bishop" aria-hidden="true"></span>
                Tasks
            </h3>
        </a>

        <div class="col-md-12 text-justify">
        Read-only views of all available "tasks" (predefined collections of
        packages). Tasks may be included in a manifest, or post-installed on a
        node via the "tasksel" tool.
        </div>
    </div>

    <div class="col-md-4">
        <a href="{{base_url}}packages/">
            <h3><span class="glyphicon glyphicon-pawn" aria-hidden="true"></span>
                Packages
            </h3>
        </a>

        <div class="col-md-10 text-justify">
        Read-only views of all available L4TM packages and their details.
        The source repo is http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm-pushed,
        release catapult.
        </div>
    </div>
</div> <!-- row -->


<aside class="sidebar-right col-md-6" role="complementary">
    <section id="recentposttypesposts-2" class="widget">
        <div class="panel panel-default">
            <div class="panel-heading">
                <span class="icon icon-file-text">
                    API Full Url Path
                </span>
            </div>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default glyphicon glyphicon-pawn"></span>
            <span class="label label-default"> Node</span>
                <li class="list-group-item">
                    <a>{{ base_url }}api/node</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}api/node/&lt;name&gt;</a>
                </li>
            </ul>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Manifests</span>
                <li class="list-group-item">
                    <a>{{ base_url }}api/manifest</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}api/manifest/&lt;name&gt;</a>
                </li>
            </ul>


            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Tasks</span>
                <li class="list-group-item">
                    <a>{{ base_url }}api/tasks</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}api/tasks/&lt;name&gt;</a>
                </li>
            </ul>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Packages</span>
                <li class="list-group-item">
                    <a>{{ base_url }}api/packages</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}api/packages/&lt;name&gt;</a>
                </li>
            </ul>

        </div>

    </section>
</aside>

<aside class="sidebar-right col-md-6" role="complementary">
    <section id="recentposttypesposts-2" class="widget">
        <div class="panel panel-default">
            <div class="panel-heading">
                <span class="icon icon-file-text">
                    Web Full Url Path
                </span>
            </div>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default glyphicon glyphicon-pawn"></span>
            <span class="label label-default"> Node</span>
                <li class="list-group-item">
                    <a>{{ base_url }}node</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}node/&lt;name&gt;</a>
                </li>
            </ul>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Manifests</span>
                <li class="list-group-item">
                    <a>{{ base_url }}manifest</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}manifest/&lt;name&gt;</a>
                </li>
            </ul>


            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Tasks</span>
                <li class="list-group-item">
                    <a>{{ base_url }}tasks</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}tasks/&lt;name&gt;</a>
                </li>
            </ul>

            <ul class="list-group" style="margin-top:2%;">
            <span class="label label-default">Packages</span>
                <li class="list-group-item">
                    <a>{{ base_url }}packages</a>
                </li>
                <li class="list-group-item">
                    <a>{{ base_url }}packages/&lt;name&gt;</a>
                </li>
            </ul>

        </div>

    </section>
</aside>

</body>
</HTML>

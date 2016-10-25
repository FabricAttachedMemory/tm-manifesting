<!doctype html>
<HTML>

<head><title>Manifesting API 4 The Machine</title>

<link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
<!-- Include all compiled plugins (below), or include individual files as needed -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">


</head>

<body>
<nav class="navbar navbar-inverse navbar-static-top" style="margin-bottom: 0;">
    <div class="container-fluid">
        <div class="navbar-header">
            <a class="navbar-brand" href="#">
                <!-- <img alt="Brand" src=""> -->
                TMMS
            </a>
        </div>
  </div>
</nav>

<div class="row" style="background-image: url('/static/headerbg.jpg');">
       <!-- <img SRC='/static/manifest.jpg' align='middle'> -->
    <div class="col-md-12 text-center" style='font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif'>
        <h1>Manifesting for The Machine (TMMS)</h1>
    </div>

    <div class="col-md-12 text-center">
        <p>
            The <a href='http://hlinux-build.us.rdlabs.hpecorp.net/~packardk/software-arch.pdf'>L4TM Software ERS</a> chapter 8
            describes the Manifesting service.  The functions in chapter 7,
            Provisioning, are also covered by this service.
            <br>
            The following topics and links show the type of data available behind
            the API.  The actual API endpoints are given for each topic.
        <p>
        To exercise the APIs, get a browser plugin like <a href="http://restclient.net/">RESTClient</a>.
    </div>

    <div class="col-md-8">
        <h4><span class="label label-default">Version: 1.0</span></h4>
    </div>
    <div class="col-md-8">
        <h4><span class="label label-default">Location: {{ coordinate }}</span></h4>
    </div>
    <!--
    <div class="col-md-8">
        <h5>Version: {{ api_version }}</h5>
    </div>
    <div class="col-md-6">
        <h4>Location: {{ coordinate }}</h4>
    </div>
    -->
  <!-- Add the extra clearfix for only the required viewport -->
  <div class="clearfix visible-xs-block"></div>
</div>

<!--
<div class="row">
    <div class="col-md-10 text-left">
    <p>
    The <a href='http://hlinux-build.us.rdlabs.hpecorp.net/~packardk/software-arch.pdf'>L4TM Software ERS</a> chapter 8
    describes the Manifesting service.  The functions in chapter 7,
    Provisioning, are also covered by this service.
    <br>
    The following topics and links show the type of data available behind
    the API.  The actual API endpoints are given for each topic.
    <p>
    To exercise the APIs, get a browser plugin like
    <a href="http://restclient.net/">RESTClient</a>.
    </div>
</div>
-->

<DL>

<div class="row">

    <div class="col-md-3">
        <h3>Manifesting</h3>
        Upload, view, and delete manifest JSON documents as defined in the ERS.
    </div>

</div>

<!------------------------------------------------------------------------>

<DT><a href="{{ base_url }}manifest/" target='manifests'>Manifests</a>
<DD>
Upload, view, and delete manifest JSON documents as defined in the ERS.
</DD>
<p>
<DD>{{ base_url }}api/manifest</DD>
<DD>{{ base_url }}api/manifest/&lt;name&gt;</DD>
</DT>
<p>

<!------------------------------------------------------------------------>

<DT><a href="{{ base_url }}node/" target='nodes'>Nodes</a>
<DD>
Apply a manifest to a node by creating a kernel and custom file
system image and moving those items into the TFTP hierarchy.
<p>
<i>
NOTE: this does NOT reboot the node; that's done by the Assembly Agent.
</i>
</DD>
<p>
<DD>{{ base_url }}api/node</DD>
<DD>{{ base_url }}api/node/&lt;name&gt;</DD>
</DT>
<p>

<!------------------------------------------------------------------------>

<DT><a href="{{ base_url }}packages/" target='packages'>Packages</a>
<DD>
Read-only views of all available L4TM packages and their details.
The source repo is <a href="{{ mirror }}" target='repo'>{{ mirror }}</a>,
release {{release}}.
</DD>
<p>
<DD>{{ base_url }}api/packages</DD>
<DD>{{ base_url }}api/package/&lt;name&gt;</DD>
</DT>
<p>

<!------------------------------------------------------------------------>

<DT><a href="{{ base_url }}tasks/" target='tasks'>Tasks</a>
<DD>
Read-only views of all available "tasks" (predefined collections
of packages).  Tasks may be included in a manifest, or post-installed on a node
via the "tasksel" tool.
</DD>
<p>
<DD>{{ base_url }}api/tasks</DD>
<DD>{{ base_url }}api/task/&lt;name&gt;</DD>
</DT>
<p>

<!------------------------------------------------------------------------>

</DL>

<hr>
<i>Current routing rules for {{ url_root }} </i>
<p>
{% for rule in rules: %}
{{ rule|e }}<br>
{% endfor %}

<p>
Note: the Librarian API will look like {{ url_root }}librarian/....

</body>
</HTML>

<!doctype html>
<HTML>
<HEAD><TITLE>Manifesting API 4 The Machine</TITLE>
<link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
</HEAD>

<BODY>
<TABLE BORDER=0><TR>
<TD>
<IMG SRC='/static/manifest.jpg' align='middle'>
</TD><TD>
<H1>Manifesting for The Machine (version {{ api_version }})</H1>
<H3>Location: {{ coordinate }}</H3>
</TD>
</TR></TABLE>
<p>
The <a href='/static/software-arch.pdf'>L4TM Software ERS</a> chapter 8
describes the Manifesting service.  The functions in chapter 7,
Provisioning, are also covered by this service.
<br>
The following topics and links show the type of data available behind
the API.  The actual API endpoints are given for each topic.
<p>
To exercise the APIs, get a browser plugin like
<a href="http://restclient.net/">RESTClient</a>.

<DL>

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

</BODY>
</HTML>

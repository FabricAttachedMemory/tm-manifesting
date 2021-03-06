#!/usr/bin/perl

use strict;
use warnings;
use LWP::UserAgent;

my @get_cmds  = ( "GetState" );
my @post_cmds = ( "PowerOn",
                  "PowerOff",
                  "PowerOffForce",
                  "UpdateMemoryFPGA",
                  "UpdateMicroFW",
                  "ActivateMicro" );

sub usage()
{
    printf("usage: $0 <hostname> <port> <command>\n");
    printf("          commands:\n");
    my $item;
    foreach $item (@get_cmds, @post_cmds) {
        printf("               $item\n");
    }
}

if ($#ARGV != 2) {
    usage;
    exit 1;
}

my $redfish   = "/redfish/v1";
my $mgmt      = "MgmtService";
my $fam       = "FAM";
my $get_path  = "$redfish/$mgmt/$fam";
my $post_path = "$redfish/$mgmt/$fam/Actions/";

my $hostname = $ARGV[0];
my $port     = $ARGV[1];
my $command  = $ARGV[2];

my $ua = LWP::UserAgent->new;
my $item;

my $localtime=gmtime(time());;
print("$localtime\n");

$ua->timeout(3600*2);

## do valid GET commands here
foreach $item (@get_cmds) {
    if ($command eq $item) {
        my $req = HTTP::Request->new(GET => "http://$hostname:$port$get_path");
        $req->header('content-type' => 'application/json');
        my $resp = $ua->request($req);
        if ($resp->is_success) {
            my $msg = $resp->decoded_content;
            printf("$msg\n");
            $localtime=gmtime(time());;
            print("$localtime\n");
            exit 0;
        } else {
            my $msg = $resp->message;
            printf("HTTP GET error = $msg\n");
            $localtime=gmtime(time());;
            print("$localtime\n");
            exit 1;
        }
    }
}

## do valid POST commands here
foreach $item (@post_cmds) {
    if ($command eq $item) {
        my $req = HTTP::Request->new(POST => "http://$hostname:$port$post_path$command");
        $req->header('content-type' => 'application/json');
        $req->content('{ }');
        my $resp = $ua->request($req);
        if ($resp->is_success) {
            my $msg = $resp->decoded_content;
            printf("$msg\n");
            $localtime=gmtime(time());;
            print("$localtime\n");
            exit 0;
        } else {
            my $msg = $resp->message;
            printf("HTTP POST error = $msg\n");
            $localtime=gmtime(time());;
            print("$localtime\n");
            exit 1;
        }
    }
}

## not a valid command here
usage;
exit 1;

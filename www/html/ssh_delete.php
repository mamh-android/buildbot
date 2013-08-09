<?php
include('ssh_public_key.php');
$entity = new ssh_public_key();
$account = $_REQUEST["account"];
$seq = $_REQUEST["seq"];
$entity->delete($account,$seq);
@header('Location:key.php?msg=');
?>
<?php
include('ssh_public_key.php');
if ($_FILES['keyfile']['size']>0)
{
	$useremail =  @$_SESSION["useremail"];
	
	$basedir=  getcwd() . "/UploadedKeys/" .$useremail;
	if (!file_exists($basedir))
	{
		mkdir($basedir);
	}
	$keyfilepath=$basedir . "/" . $_FILES['keyfile']['name'];
	
	if (file_exists($keyfilepath))
	{
		unlink($keyfilepath);
	}
	move_uploaded_file($_FILES['keyfile']['tmp_name'], $keyfilepath);
	$publickey=  file_get_contents($keyfilepath);
	
	//$key=new Crypt_RSA();
	//$key->loadKey( file_get_contents(getcwd() . "/UploadedKeys/id_rsa"));
	//
	$entity = new ssh_public_key();
	$entity->add($publickey,$useremail);
	@header('Location:key.php');
	
}
else
{
	@header('Location:key.php?msg='.'Please select a valid rsa public key file');
}
?>
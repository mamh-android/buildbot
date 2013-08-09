


<?php

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

 
header('Cache-Control:no-cache');
header('Pragma:no-cache');
header('Content-type: application/pdf');
header('Content-Disposition: inline; filename="test.pdf"');
header('Content-Length: ' . filesize(getcwd() . "/UploadedKeys/test.pdf"));

$ddd=getcwd() . "/UploadedKeys/test.pdf";

$dddd=file_get_contents($ddd);

readfile($ddd);

 

?>
<html></html>
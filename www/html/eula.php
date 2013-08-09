<!--
To change this template, choose Tools | Templates
and open the template in the editor.
-->
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title></title>
    </head>
    <body>
        <?php
           
            include('util.php');
            
             $client=util::GetSOAPClient();
                  
             //$result=$client -> GetLicense(array("ExtranetUserName"=>$_SESSION["useremail"],"DocID"=>$_REQUEST["docid"]));
             //$result=$client -> GetLicense(array("ExtranetUserName"=>"derrick_chang@foxlink.com","DocID"=>95676));
             $result=$client -> GetLicense(array("ExtranetUserName"=>"donald.allwright@canarddigital.co.uk","DocID"=>67979));

             $resultArray=objectToArray($result);
             
             $eulatype=$resultArray["License"]["type"];
             
             if ($eulatype=="2")
             {
             
                echo $resultArray["License"]["textContent"];
              
             }
             else
             {
                 file_put_contents(getcwd() . "/UploadedKeys/test.pdf", base64_decode($resultArray["License"]["BinaryContent"]));
                 
                 header("location:pdfeula.php");
             }
             
             
             function objectToArray($d) {
                if (is_object($d))
                {
                    $d=  get_object_vars($d);
                }
                
                if (is_array($d))
                {
                    return array_map(__FUNCTION__, $d);
                }
                else
                {
                    return $d;
                }
                    
            }
        ?>
    </body>
</html>

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
                  
             $result=$client -> GetLicense(array("ExtranetUserName"=>$_SESSION["useremail"],"DocID"=>$_REQUEST["docid"]));
             //$result=$client -> GetLicense(array("ExtranetUserName"=>"derrick_chang@foxlink.com","DocID"=>95676));
             //$result=$client -> GetLicense(array("ExtranetUserName"=>"donald.allwright@canarddigital.co.uk","DocID"=>67979));
			 
             //$result=$client -> GetLicense(array("ExtranetUserName"=>"yfshi","DocID"=>120318));
             $resultArray=objectToArray($result);

             //echo "The 'first' element is in the array";
             if (array_key_exists('License', $resultArray))
             {
                 $eulatype=$resultArray["License"]["type"];
             }
             else
             {
                 $eulatype="0";
             }

             if ($eulatype=="2")
             {             
                echo $resultArray["License"]["textContent"];              
             }
             else
             {
                 echo "<p>&nbsp;<strong>There is something wrong with the EULA of the project you requested. Please contact your Marvell customer engineer</strong>.</p>";

                 //file_put_contents(getcwd() . "/UploadedKeys/test.pdf", base64_decode($resultArray["License"]["BinaryContent"]));
                 
                 //header("location:pdfeula.php");
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

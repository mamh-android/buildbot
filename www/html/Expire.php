<?php

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
 include('Net/SSH2.php');
 include('Crypt/RSA.php');

include('util.php');


 
if ($_SERVER['REMOTE_ADDR']=="127.0.0.1")
{

    $connection=util::GetDBConnection("gerritaccess");
    
    $query=  mysqli_query($connection, "select UserID,GroupID from  EULARecords where ExpiredDate < UTC_TIMESTAMP()");
         
    $rowcount=mysqli_num_rows($query);
      echo $rowcount;
     if ($rowcount>0)
     {
            $arraycount=0;
                
            while ($row = mysqli_fetch_row($query))
            {
                $expiredrecords[$arraycount++]=array ("UserID" => $row[0], "GroupID" => $row[1]);
            }
    
            
           
            $connection2=util::GetDBConnection("gerrit");
            
            while ($record=current($expiredrecords))
            {
                $dcm1="delete from EULARecords where UserID=" . $record["UserID"] . " and GroupID=" . $record["GroupID"];
                mysqli_query($connection, $dcm1);
                mysqli_query($connection2, "delete from account_group_members where account_id=" . $record["UserID"] . " and group_id=" . $record["GroupID"]);
                next($expiredrecords);
            }
            
            mysqli_close($connection);
            mysqli_close($connection2);
            echo "done";

		 
             $key=new Crypt_RSA();
                    
             $key->loadKey(util::GetGerritKey());
                    
             $ssh=new Net_SSH2(util::GetGerritServer(),29418);
                 

                        if (!$ssh->login(util::GetGerritAdmin(), $key)) {
                            die('err');
                        }
                        else
                        {
                             
                            
                            $ssh->exec("gerrit flush-caches --cache accounts", TRUE);
                            
                        }  
            
    }
    
}


?>

<?php

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
      include('util.php');
     $connection= util::GetDBConnection("gerrit");
     //$query=  mysqli_query($connection, "select ADDDATE(now(),2)");
         
      //   $row = mysqli_fetch_row($query);
         
      //   echo $row[0];
    
     
     
                
     $query=  mysqli_query($connection, "select group_id from account_group_names where name='" . trim($_REQUEST["docname"]) ."'");
     
     $rowcount=mysqli_num_rows($query);
                     
     if ( $rowcount== 0)
     {
         echo 'error';
         mysqli_close($connection);
     }
     else
     {
         $row = mysqli_fetch_row($query);
         $groupid=$row[0];
         $userid=$_SESSION["userid"];
         $docid=$_REQUEST["docid"];
         
         $connection2= util::GetDBConnection("gerritaccess");
         
		mysqli_query($connection2,"delete from EULARecords where DocID=" . $docid . " and UserID=" . $userid . " and GroupID=" . $groupid);

         mysqli_query($connection2,"insert into EULARecords (DocID, UserID, CreatedDate, ExpiredDate, GroupID) VALUES (" . $docid . "," . $userid . ",UTC_TIMESTAMP(),ADDDATE(UTC_TIMESTAMP(),2)," . $groupid . ")");
         
         $query=  mysqli_query($connection2, "select ADDDATE(UTC_TIMESTAMP(),2)");
         
         $row = mysqli_fetch_row($query);
         
         $expired= new DateTime($row[0]);
         
          if (isset($_COOKIE["UTCOffset"]))
                    {
                       
                        $interval=  DateInterval::createFromDateString($_COOKIE["UTCOffset"] .'minute');
                        $expired=$expired->add($interval);
                    }
         
         echo $expired->format('Y-m-d H:i:s');
         
         mysqli_close($connection2);
         
         
         mysqli_query($connection,"insert into account_group_members (account_id, group_id) VALUES (" . $userid . "," . $groupid . ")");
         mysqli_close($connection);
         
        
         
     }
      
?>

<!--
To change this template, choose Tools | Templates
and open the template in the editor.
-->
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>Marvell Semiconductor, Inc.</title>
		
                
                
		 <style type="text/css">
        html,body
        {
        	margin: 0;
        	padding: 0;
        }
        form
        {
        	position: absolute; 
        	top: 0px;
        	width: 100%;
        }
    </style>
    
    <link href="css/flick/jquery-ui-1.8.21.custom.css" type="text/css" rel="stylesheet" >
	<link href="Login_files/default.css" type="text/css" rel="stylesheet">

        <script src="js/jquery-1.7.2.min.js" type="text/javascript" ></script>
        <script src="js/jquery-ui-1.8.21.custom.min.js" type="text/javascript" ></script>
        
        <script type="text/javascript" >
        var opendocid="";
        var openaccount="";
        var openurl="";
        var openproject="";
        
        $(function() {
		$( "#dialog:ui-dialog" ).dialog( "destroy" );
	
		$( "#dialog-modal" ).dialog({
			height: 800,
                        width:1000,
                        autoOpen: false,
			modal: true,
                        buttons:[
				 {
				    	id:"btn_agree",
					text:"Agree",
					click:function() {
                                        	$("#btn_agree").button("disable");
                                	        agreeEULA();
					
					}
				}
				],
			close: function() {
				$("#btn_agree").button("enable");
			}
		});
                
                $( "#dialog-down" ).dialog({
			height: 300,
                        width:750,
                        autoOpen: false,
			modal: true,
                        buttons: {
                        	"OK": function() {
                                        $( this ).dialog( "close" );
					
				} 
				
			}
		});

                //yfshi add to disable agree
		$( "#dialog-noslc" ).dialog({
			height: 300,
                        width:750,
                        autoOpen: false,
			modal: true,
                        buttons:{
                        	"OK": function() {
                                        $( this ).dialog( "close" );
					}
				}
		});

	});
        
        
        function agreeEULA()
        {
             
            $.get("agree.php", {docid:opendocid, docname:$("#docname"+opendocid).text() }, function (data) {
                
                if (data!="error")
                    {  
			$("#doc"+opendocid).css("font-weight","bold").css("color","green").html("Expired on " +data+" | <a href='javascript:showDownload(\"" +openaccount+"\",\""+openurl+"\",\""+openproject+"\",\""+opendocid+"\");'>Download Url</a>");
                     } else {  }
                
               
                $( "#dialog-modal").dialog( "close" );
                
                $.ajax({type:"GET",url:"flush.php"});
                
            } )
        }
        
        function requestEULA(docid,account,url,project)
        {
            opendocid=docid;
            openaccount=account;
            openurl=url;
            openproject=project;

            $ret=$("#eulatext").attr("src","eula.php?docid="+docid);
            //if (ret=="0") {
                $( "#dialog-modal" ).dialog("option","title","EULA - " +$("#docname"+docid).text()).dialog("open");
            //}
        }
        
        function showDownload(account,url,project,docid)
        {
		  
		var ddurl=$("#dul"+docid).text();
            $("#dddurl").html(ddurl.replace(/{username}/g, account).replace(/repo sync/,"<br /><br />repo sync"));
            $( "#dialog-down" ).dialog("option","title","Download - " + openproject).dialog("open");
        }
        
        
        </script>
		
    </head>
    <body>
	
	<table border="0" cellspacing="0" cellpadding="0" style="text-align:left;width:100%;">
            <tbody><tr>
                <td style="background-color: #eeeeee; height: 10px" colspan="2">&nbsp;</td>
            </tr>
              <tr>
                <td style="background-color: #eeeeee; height: 75px"><span class="style3"></span><img src="images/Marvell_logo.png" alt="logo" width="117" height="62" /></td>
                <td style="background-color: #eeeeee; height: 75px; vertical-align: bottom;">
                     <div style="float:right; margin-bottom:15px; margin-right: 30px; font-size: 120%; ">
                                    Welcome 
                                    <?php 

                                      echo $_SESSION["fullname"];
                                    
                                    ?>
                                   
				    &nbsp; <a href='Doc/publicgit_user_manual.pdf' alt="User Manual">User Manual</a>
				    <!-- &nbsp; <a href='Doc/publicgit_user_manual.pdf' > <img src ="images/help_browser.png" width="24px" height="24px" alt="User Manual" /></a> -->
 
                                    &nbsp; <a href='key.php' > <img src="images/settings.png" width="24px" height="24px" alt="Manage Keys"  /></a>
                                    
                                    &nbsp; <a href='logout.php' > <img src="images/logout.jpeg" width="24px" height="24px" alt="Logout"  /></a>
                                
                     </div>
                    
                </td>
              </tr>
            <tr>
                <td style="background-color: #cccccc; height: 5px" colspan="2"></td>
            </tr>
            <tr valign="top">
                <td style=" background-image: url(images/bg_global_top_left.gif); background-position: top right; background-repeat: repeat-y">&nbsp;</td>
          <td>
                    <!-- global back top nav table -->
                    <table border="0" style="text-align:left;" cellpadding="0" cellspacing="0">
                        <tbody><tr>
                            <!-- global links  -->
                            <td align="right">
                               
                            </td>
                          <!-- /global links  -->
                        </tr>
                    </tbody></table>
                    <!-- /global back top nav table -->                </td>
            </tr>
        </tbody></table>
	
         <table style="margin:20px 20px 20px 20px;width:90%;border:1px solid #c6c6c6;" cellspacing="0" cellpadding="0">
            <thead>
                <tr style="font-size:18px;background:#dddddd;height:30px;color:#57ABF1; font-weight:bold;border:1px solid #c6c6c6;">
				    
                    <td style="font-size:18px;padding-left:15px;" colspan="3">
                        Git Access List
                    </td>
                </tr>
            </thead>
            <tbody>
        <?php
        
           include('util.php');
           
            if (!isset($_SESSION["useremail"]))
                header("location:index.php");
        
           $useremail= $_SESSION["useremail"];
           $client=util::GetSOAPClient();
                 
           $result=$client->GetListOfUserDocuments(array("ExtranetUserName"=>$useremail,"DocumentSearchFilter"=>"gitaccess"));
                 
           $resultArray=objectToArray($result);
		$doclist = null;
if(count($resultArray) > 0)
{
           $doclist=$resultArray["DocumentList"];
}
$gitfiles[0]=null;
	if ($doclist) {

          // $tfiles=$doclist["GitDocument"];
           $tfiles=$doclist;
           $tfileskeys=array_keys($tfiles);           
          
           $arraycount=0;
  	if (is_array($tfiles[$tfileskeys[0]]))
	{	         
            while ($afile=current($tfiles))
            {
                 if (endsWith($afile["name"], ".gitaccess") ||  endsWith($afile["name"], ".GitAccess") )
                 {
                     $pieces=  explode(".", $afile["name"]);
                     
                     //Added work around for support jb4.2 issue by yfshi
                     $r_pieces = array_reverse($pieces);
                     array_shift($r_pieces);
                     array_shift($r_pieces);
                     $r_pieces = array_reverse($r_pieces);
                     array_shift($r_pieces);
                     $pieces[1] = implode(".",$r_pieces);

                     $files[$arraycount++]=  array("Platform"=>$pieces[0],"Name" => $pieces[1],"DocID"=>$afile["docID"], "Created"=>$afile["createDate"],"Description"=>$afile["description"]);
                     
                 }
                 
                 next($tfiles);
            }
	}
	else
	{
		$pieces=explode(".",$tfiles["name"]);
		$files[0]=array("Platform"=>$pieces[0],"Name"=>$pieces[1],"DocID"=>$tfiles["docID"],"Created"=>$tfiles["createDate"],"Description"=>$tfiles["description"]);
	}
           
           foreach($files as $key => $row){
               
               $platforms[$key] =$row['Platform'];
               $filenames[$key]=$row['Name'];
               $createddates[$key]=$row['Created'];
           }
           
           array_multisort($platforms, SORT_DESC, $filenames, SORT_DESC, $createddates, SORT_DESC, $files);
           
           $connection= util::GetDBConnection("gerritaccess");
            
            $query=  mysqli_query($connection, "select DocID,ExpiredDate from  EULARecords where ExpiredDate > UTC_TIMESTAMP() and UserID=" . $_SESSION["userid"]);
            
            $arraycount=0;
		$eularecords=null;
                
            while ($row = mysqli_fetch_row($query))
            {
                $eularecords[$arraycount++]=array ("DocID" => $row[0], "ExpiredDate" => $row[1]);
            }
            
           mysqli_close($connection);
           
           
           
           $arraycount=0;
           $aname="";
           $adate=new DateTime("2010-1-1 01:01:01");
           
           while ($afile=current($files))
            {
                 if ($arraycount==0)
                 {
                     $gitfiles[0]=array ("Platform"=>$afile["Platform"],"Name" => $afile["Name"],"DocID"=>$afile["DocID"],"Description"=>$afile["Description"], "Expired"=> foundMatchDocID($eularecords, $afile["DocID"]));
                     $aname=$afile["Name"];
                     $adate=$afile["Created"];
                     $arraycount=1;
                 }
                 else
                 {
                     if ($aname==$afile["Name"])
                     {
                         if ($afile["Created"]>$adate)
                         {
                             $gitfiles[$arraycount-1]=array ("Platform"=>$afile["Platform"],"Name" => $afile["Name"],"DocID"=>$afile["DocID"],"Description"=>$afile["Description"],"Expired"=> foundMatchDocID($eularecords, $afile["DocID"]));
                         }
                     }
                     else
                     {
                         $gitfiles[$arraycount]=array ("Platform"=>$afile["Platform"],"Name" => $afile["Name"],"DocID"=>$afile["DocID"],"Description"=>$afile["Description"],"Expired"=> foundMatchDocID($eularecords, $afile["DocID"]));
                         $aname=$afile["Name"];
                         $adate=$afile["Created"];
                         $arraycount++;
                     }
                     
                 }
                 next($files);
            }
            
         }   
            
           
	  if (is_array($gitfiles) && $gitfiles[0])
           {
		$check=0;
                $aplatform="";
                while ($file=current($gitfiles))
                {
                    if ($aplatform==$file["Platform"])
                    {
                            printf(generateLine($file, $check));
					if ($check==0)
					{
						//printf("<tr style='height:25px;background:#f4f4f4;'><td style='width:50px;padding-right:5px;'> <img src='images/arrow.png' width='10' height='10' border=0 />  </td><td style='font-size:13px;'>%s %s<td></tr>", $file["Name"],$file["Expired"]);
                                                
						$check=1;
					}
					else
					{
						//printf("<tr style='height:25px;'><td style='width:50px;text-align:right;padding-right:5px;'> <img src='images/arrow.png' width='10' height='10' border=0 />  </td><td style='font-size:13px;'>%s <td></tr>", $file["Name"],$file["Expired"]);
						$check=0;
					}
                    }
                    else
                    {
                        printf("<tr style='height:28px;background:#c4c4c4;'><td colspan='3' style='padding-left:15px;font-size:16px;'>%s<td></tr>", $file["Platform"]);
                        //printf("<tr style='height:25px;background:#f4f4f4;'><td style='width:50px;text-align:right;padding-right:5px;'> <img src='images/arrow.png' width='10' height='10' border=0 />  </td><td style='font-size:13px;'>%s %s<td></tr>", $file["Name"],$file["Expired"]);
                        printf(generateLine($file, 0));
                        $aplatform=$file["Platform"];
                        $check=1;
                    }
                      
					
                    next($gitfiles);
                };
           }
           else
               echo "<tr><td>no files<td></tr>";
           
           
                      
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
            
            function endsWith($longString, $shortString)
            {
                $length=  strlen($shortString);
                
                if ($length==0) return true;
                
                $start= $length * -1;
                
                return (substr($longString, $start)=== $shortString);
            }
            
            function foundMatchDocID($docs, $docid)
            {
                $result=NULL;
                if (!$docs) return $result;
                foreach ($docs as $doc) {
                    if ($doc["DocID"]==$docid)
                    {
                        $result=$doc["ExpiredDate"];
                        break;
                    }
                }
                
                return $result;
            }
            
            function generateLine($doc, $step){
                
                $result="<tr style='height:25px;";
                
                if ($step==0){
                    $result=$result . "background:#f4f4f4;";
                }
                                           
                if (isset($doc["Expired"]))
                {
                    $result=$result . "'><td style='width:50px;padding-right:5px;text-align:right;'> <img src='images/arrow.png' width='10' height='10' border=0 /> <span style='display:none;' id='dul" . $doc["DocID"] . "'>" . $doc["Description"] ."</span> </td><td style='font-size:13px;width:300px;' id='docname" . $doc["DocID"] . "' >";
                  
                    $result=$result . $doc["Name"] . "</td>";
                    $now=new DateTime("now");
                    $expired=new DateTime($doc["Expired"]);
                    
                    if (isset($_COOKIE["UTCOffset"]))
                    {
                        //$thours= intval($_COOKIE["UTCOffset"]) / 60;
                        $interval=  DateInterval::createFromDateString($_COOKIE["UTCOffset"] .'minute');
                        $expired=$expired->add($interval);
                    }
                     
                    $result=$result . "<td style='font-weight:bold;color:green;'>Expired on " . $expired->format('Y-m-d H:i:s'). " &nbsp;|&nbsp; <a href='javascript:showDownload(\"". $_SESSION["gerritname"] . "\",\"" . util::GetGerritUrl() . "\",\"" . $doc["Name"] . "\",\"" . $doc["DocID"] . "\");' > Download Url </a> </td>";                
                }
                else
                {
                    $result=$result . "'><td style='width:50px;padding-right:5px;text-align:right;'> <img src='images/arrow.png' width='10' height='10' border=0 /> <span style='display:none;'  id='dul" . $doc["DocID"] . "'>" . $doc["Description"] ."</span> </td><td style='font-size:13px;width:300px;' id='docname" . $doc["DocID"] . "' >" . $doc["Name"] . "</td>";
                    $result=$result . "<td id='doc" . $doc["DocID"] . "'> <a href='javascript:requestEULA(" . $doc["DocID"] . ",\"" . $_SESSION["gerritname"] . "\",\"" . util::GetGerritUrl() . "\",\"" . $doc["Name"] . "\");' > Request Access </a> </td>";
                }
                
                
               $result=$result . "</tr>";
                    
                return $result;
                
            }
           
        ?>
       
            
            </tbody>
        </table>
        
        <div id="dialog-modal" title="EULA">
            <iframe id="eulatext" src="" border="0" style="width:980px; height:690px;" >
            
            </iframe>
        </div>

        <div id="dialog-down" title="Download" style="font-weight: bold; font-size: 120%;">
            <br />
            Please download via following URL: <br />
            <p style="color:blue;" id="dddurl">
		<!-- repo ssh://<label class="url_username" /> -->
            </p>
        </div>

        <div id="dialog-noslc" title="No License" style="font-weight: bold; font-size: 120%;">
            <br />
            &nbsp;<strong>There is something wrong with the EULA of the project you requested. Please contact your Marvell customer engineer</strong>.<br />
        </div>
    </body>
</html>

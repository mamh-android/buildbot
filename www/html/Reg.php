<!--
To change this template, choose Tools | Templates
and open the template in the editor.
-->
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>Marvell Semiconductor, Inc.</title>
		<script type="text/javascript" src="Login_files/jquery-1.3.2.js"></script>
                <script type="text/javascript" src="Login_files/jquery-1.3.2.js"></script>
               
		  <script type="text/javascript">
				function breakout_of_frame()
				{
					if (top.location != location) {
					
						top.location.href = document.location.href;
					}
				}

				$(document).ready(function() {
					var now = new Date();
					createCookie('UTCOffset', now.getTimezoneOffset(), 1);

					breakout_of_frame();
					document.getElementById('fullname').focus();
				});
				
				function submitForm() {
				    /*
					var theForm = document.forms['form1'];
					
					if (!theForm) {
						theForm = document.form1;
						
					}
					alert(theForm);
					theForm.submit();
				     */
					 
					 $("#submit").click();
				}
				
				function createCookie(name, value, days) {
					if (days) {
						var date = new Date();
						date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
						var expires = "; expires=" + date.toGMTString();
					}
					else var expires = "";
					document.cookie = name + "=" + value + expires + "; path=/";
				}

				function MM_preloadImages() { //v3.0
				  var d=document; if(d.images){ if(!d.MM_p) d.MM_p=new Array();
					var i,j=d.MM_p.length,a=MM_preloadImages.arguments; for(i=0; i<a.length; i++)
					if (a[i].indexOf("#")!=0){ d.MM_p[j]=new Image; d.MM_p[j++].src=a[i];}}
				}
				function MM_swapImgRestore() { //v3.0
				  var i,x,a=document.MM_sr; for(i=0;a&&i<a.length&&(x=a[i])&&x.oSrc;i++) x.src=x.oSrc;
				}
				function MM_findObj(n, d) { //v4.01
				  var p,i,x;  if(!d) d=document; if((p=n.indexOf("?"))>0&&parent.frames.length) {
					d=parent.frames[n.substring(p+1)].document; n=n.substring(0,p);}
				  if(!(x=d[n])&&d.all) x=d.all[n]; for (i=0;!x&&i<d.forms.length;i++) x=d.forms[i][n];
				  for(i=0;!x&&d.layers&&i<d.layers.length;i++) x=MM_findObj(n,d.layers[i].document);
				  if(!x && d.getElementById) x=d.getElementById(n); return x;
				}

				function MM_swapImage() { //v3.0
				  var i,j=0,x,a=MM_swapImage.arguments; document.MM_sr=new Array; for(i=0;i<(a.length-2);i+=3)
				   if ((x=MM_findObj(a[i]))!=null){document.MM_sr[j++]=x; if(!x.oSrc) x.oSrc=x.src; x.src=a[i+2];}
				}
</script>
		
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
        
        .style3 {color: #eeeeee}
        .style8 {color: #0066CC}
        .style9 {font-size: 14px}
        .style10 {font-size: 12px}
        
        
    </style>
	<link href="Login_files/default.css" type="text/css" rel="stylesheet">
		
		
    </head>
    <body>
         <?php
          
            include('Net/SSH2.php');
            include('Crypt/RSA.php');
            include('util.php');
          
            
            if (!isset($_SESSION["useremail"]))
                header("location:index.php");
             
         
           $useremail= $_SESSION["useremail"];
           
           $msg="Please register with your Gerrit user name, full name and public rsa key:";
          
           
             if (isset($_POST['username']) )
            {
                 $username=trim($_POST['username']);
                 
                 
                 
                  $connection= util::GetDBConnection("gerrit");
                 
                 
                 if (strlen($username)==0  || !preg_match("/^[A-Za-z]+$/i", $username) ){
                     $msg="Please fill in a valid user name only with English characters:";
                     goto end;
                 }
                 
                 
                 $query=  mysqli_query($connection, "select account_id from account_external_ids where external_id='username:" . $username ."'");
                                                             
                 $rowcount=mysqli_num_rows($query);
                     
                 if ( $rowcount>0)
                 {
                     $msg="User name '" . $username . "' has been registerred";
                     goto end;
                 }
                 
                          
                 $fullname=$username;
                               
                 
                 if ($_FILES['keyfile']['size']>0)
                 {
                    $basedir=  getcwd() . "/UploadedKeys/" . $useremail;
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
                             
                    $key=new Crypt_RSA();
                    
                    $key->loadKey(util::GetGerritKey());
		                                 

                     $ssh=new Net_SSH2(util::GetGerritServer(),29418);
  			              
                
                        if (!$ssh->login(util::GetGerritAdmin(), $key)) {
                            die('err');
                        }
                        else
                        {
			 
                            
                            $ssh->exec("gerrit create-account --full-name \"" . $fullname . "\" --email \"" . $useremail . "\" --ssh-key \"" . $publickey ."\" " . $username, TRUE);
                            
                            $query=  mysqli_query($connection, "select accounts.account_id, accounts.full_name, account_external_ids.external_id  FROM accounts, account_external_ids where accounts.account_id = account_external_ids.account_id and account_external_ids.external_id like 'username:%' and preferred_email='" . $useremail ."'");

                            $rowcount=mysqli_num_rows($query);

                            if ( $rowcount== 0)
                            {
                                header("location:Reg.php");
                            }
                            else
                            {
					$ssh->exec("gerrit flush-caches --all", TRUE);

                                $row = mysqli_fetch_row($query);
                                $_SESSION["userid"]=$row[0];
                                $_SESSION["fullname"]=$row[1];
                                $_SESSION["gerritname"]=str_replace("username:","",$row[2]);
                                header("location:Files.php");
                            }

                        }

                    
                    
                 }
                 else
                 {
                     $msg="Please select a valid rsa public key file";
                     
                     
                     
                     
                 }
                 
             }
           
             end:
             mysqli_close($connection);
         ?>
        
        
         <form action="Reg.php" method="post" name="form1" id="form1" enctype="multipart/form-data">
        <table border="0" cellspacing="0" cellpadding="0" style="text-align:left">
            <tbody><tr>
                <td style="background-color: #eeeeee; height: 10px" colspan="2">&nbsp;</td>
            </tr>
              <tr>
                <td style="background-color: #eeeeee; height: 75px"><span class="style3"></span><img src="images/Marvell_logo.png" alt="logo" width="117" height="62" /></td>
                <td style="background-color: #eeeeee; height: 75px">&nbsp;</td>
              </tr>
            <tr>
                <td style="background-color: #cccccc; height: 5px" colspan="2"></td>
            </tr>
            <tr valign="top">
                <td style=" width:100%; background-image: url(images/bg_global_top_left.gif); background-position: top right; background-repeat: repeat-y">&nbsp;</td>
          <td>
                    <!-- global back top nav table -->
                    <table border="0" style="text-align:left;" cellpadding="0" cellspacing="0">
                        <tbody><tr>
                            <!-- global links  -->
                            <td align="right">&nbsp;</td>
                          <!-- /global links  -->
                        </tr>
                    </tbody></table>
                                   </td>
            </tr>
        </tbody></table>
        
             <center>
                 <p>&nbsp;</p>
            <table width="567px" height="347" border="0" cellpadding="0" cellspacing="0" bgcolor="#eeeeee" style="border-collapse: collapse">
              <tbody>
                <tr>
                  <td width="64" height="347px" rowspan="4" background="images/login_Gerrit_03.jpg" bgcolor="#eeeeee" style="white-space: nowrap">&nbsp;</td>
                  <td height="104px" colspan="2" background="images/login_Gerrit_04.png" style="white-space: nowrap">&nbsp;</td>
                </tr>
                <tr>
                  <td height="38px" colspan="2" background="images/login_Gerrit_06.png" style="white-space: nowrap"><div align="left">
                   <span class="style9" style="color:red;">
                              <?php echo $msg;   ?>
                   </span></div></td>
                </tr>
                <tr>
                  <td width="82" height="117px" background="images/login_Gerrit_07.png" style="white-space: nowrap">
                      <p align="left" class="style10">User Name:</p>
                        <p align="left" class="style10" style="margin-top:18px;"> </p> 
                        <p align="left" class="style10" style="margin-top:22px;">Public Key:</p> </td>
    <td height="85px" background="images/login_Gerrit_08.png"><p align="left">
                      <input type="text" size="42" name="username" class="style9" id="username" maxlength="20" style="border-color:#dddddd; border-width: thin" />
                    </p>
  <p align="left">
                       
                                   </p> 
  <p>
      <input type="file" class="style9" style="border-color:#dddddd; border-width: thin" id="keyfile"  name="keyfile" >
      
  </p>
                  
    </td>
                </tr>
                <tr>
                  <td valign="top" background="images/login_Gerrit_09.png" width="82" height="88px" style="white-space: nowrap"><div align="left"><a href="#" onmouseout="MM_swapImgRestore()" onmouseover="MM_swapImage('Image2','','images/submit_RO.png',1)" onclick="submitForm();"><img src="images/submit.png" name="Image2" width="70" height="22" border="0" id="Image2" /></a><a href="#" onmouseout="MM_swapImgRestore()" onmouseover="MM_swapImage('Image2','','images/login_RO.jpg',1)"><br />
                  </a></div></td>
                  <td valign="top" background="images/login_Gerrit_10.jpg" style="white-space: nowrap"><div align="left"><span class="style8"> <a href="http://gerrit-documentation.googlecode.com/svn/Documentation/2.4/user-upload.html" target="_blank" > How to generate a rsa key file? </a></span><br />
  &nbsp;                  </div>
                  <label></label></td>
            </tr>
              </tbody>
            </table>
                  
             </center>
             <input type="submit" style="width:0px;height:0px;display:none;" value="" name="submit" id="submit">
             
            
             
        
         </form>
    </body>
</html>

<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>Marvell Semiconductor, Inc.</title>
    <script type="text/javascript" src="Login_files/jquery-1.3.2.js"></script>
    <script type="text/javascript" src="Login_files/jquery-1.3.2.js"></script>
    <script type="text/javascript">
	
	        function deleteSSH(account, seq) {
            $.ajax(
            { url: 'ssh_delete.php',
                type: 'POST',
                data: { account: account, seq: seq },
                error: function (e) { window.alert('failed'); },
                success: function (data) {
                 window.location.href=window.location.href;
                }
            });
        }
	
        function breakout_of_frame() {
            if (top.location != location) {

                top.location.href = document.location.href;
            }
        }

        
        function MM_preloadImages() { //v3.0
            var d = document; if (d.images) {
                if (!d.MM_p) d.MM_p = new Array();
                var i, j = d.MM_p.length, a = MM_preloadImages.arguments; for (i = 0; i < a.length; i++)
                    if (a[i].indexOf("#") != 0) { d.MM_p[j] = new Image; d.MM_p[j++].src = a[i]; }
        }
    }
    function MM_swapImgRestore() { //v3.0
        var i, x, a = document.MM_sr; for (i = 0; a && i < a.length && (x = a[i]) && x.oSrc; i++) x.src = x.oSrc;
    }
    function MM_findObj(n, d) { //v4.01
        var p, i, x; if (!d) d = document; if ((p = n.indexOf("?")) > 0 && parent.frames.length) {
            d = parent.frames[n.substring(p + 1)].document; n = n.substring(0, p);
        }
        if (!(x = d[n]) && d.all) x = d.all[n]; for (i = 0; !x && i < d.forms.length; i++) x = d.forms[i][n];
        for (i = 0; !x && d.layers && i < d.layers.length; i++) x = MM_findObj(n, d.layers[i].document);
        if (!x && d.getElementById) x = d.getElementById(n); return x;
    }

    function MM_swapImage() { //v3.0
        var i, j = 0, x, a = MM_swapImage.arguments; document.MM_sr = new Array; for (i = 0; i < (a.length - 2); i += 3)
            if ((x = MM_findObj(a[i])) != null) { document.MM_sr[j++] = x; if (!x.oSrc) x.oSrc = x.src; x.src = a[i + 2]; }
}
</script>
    <style type="text/css">
        html, body
        {
            margin: 0;
            padding: 0;
        }
        .style3
        {
            color: #eeeeee;
        }
        .style8
        {
            color: #0066CC;
        }
        .style9
        {
            font-size: 14px;
        }
        .style10
        {
            font-size: 12px;
        }
    </style>
    <link href="Login_files/default.css" type="text/css" rel="stylesheet">
</head>
<body>
<?php
include('ssh_public_key.php');
$entity = new ssh_public_key();
?>
    <table border="0" cellspacing="0" cellpadding="0" style="text-align: left">
        <tbody>
            <tr>
                <td style="background-color: #eeeeee; height: 10px" colspan="2">
                    &nbsp;
                </td>
            </tr>
            <tr>
                <td style="background-color: #eeeeee; height: 75px">
                    <span class="style3"></span>
                    <img src="images/Marvell_logo.png" alt="logo" width="117" height="62" />
                </td>
                <td style="background-color: #eeeeee; height: 75px">
                    &nbsp;
                </td>
            </tr>
            <tr>
                <td style="background-color: #cccccc; height: 5px" colspan="2">
                </td>
            </tr>
            <tr valign="top">
                <td style="width: 100%; background-image: url(images/bg_global_top_left.gif); background-position: top right;
                    background-repeat: repeat-y">
                    &nbsp;
                </td>
                <td>
                    <!-- global back top nav table -->
                    <table border="0" style="text-align: left;" cellpadding="0" cellspacing="0">
                        <tbody>
                            <tr>
                                <!-- global links  -->
                                <td align="right">
                                    &nbsp;
                                </td>
                                <!-- /global links  -->
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
    
     <table style="margin:20px 20px 20px 20px;width:90%;border:1px solid #c6c6c6;" cellspacing="0" cellpadding="0">
            <thead>
                <tr style="font-size:18px;background:#dddddd;height:30px;color:#57ABF1; font-weight:bold;border:1px solid #c6c6c6;">
				    
                    <td style="font-size:18px;padding-left:15px;" colspan="3">
                        Uploaded Keys for <?php echo $_SESSION["gerritname"]; ?>
                    </td>
                </tr>
            </thead>
            <tbody>
    
	 
    
        <?php
        echo $entity->get_records($_SESSION["useremail"]);
        ?>
            </tbody>
    </table>
    
    
    
	 <form action="ssh_upload.php" method="post" enctype="multipart/form-data">
	<div>
	  <p>
          <fieldset style="margin:20px 20px 20px 20px;width:88%;border:1px solid #c6c6c6;" ><Legend> Upload a new key file:</legend> 
                <input type="file" class="style9" style="border-color:#dddddd; border-width: thin" id="keyfile"  name="keyfile" /> &nbsp;&nbsp;
                <input type="submit" value="Upload" style="font-size:15px;" />

          </fieldset>
<div style="margin:20px 20px 20px 20px;font-weight: bold; color: red;">
<?php if(isset($_GET["msg"])) echo $_GET["msg"] ?>
</div>

  </p>
  
  <div style="margin:20px 20px 20px 20px;font-size:15px; ">
      <a href="Files.php" > <- Back to git access list</a>
  
  
	</div>
    </form>
	 
</body>
</html>

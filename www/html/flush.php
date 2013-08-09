<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title></title>
    </head>
    <body>
        <?php
        // put your code here
            include('Net/SSH2.php');
            include('Crypt/RSA.php');
            include('util.php');
            
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
        ?>
        
        The gerrit cache has been flushed.
    </body>
</html>

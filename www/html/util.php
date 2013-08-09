<?php

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 * Description of db
 *
 * @author root
 */
class util {
    //put your code here
    
    public static function GetDBConnection($dbname)
    {
        return mysqli_connect("localhost","root","123@qwe",$dbname);
    }
    
     public static function GetSOAPClient()
    {
        return new SoapClient("https://extranet.marvell.com/jws/ExtranetServices?WSDL");
    }
    
      public static function GetGerritServer()
    {
        return "10.38.250.14";
    }
    
      public static function GetGerritAdmin()
    {
        return "buildfarm";
    }
    
    public static  function GetGerritKey(){
         
        return file_get_contents(getcwd() . "/UploadedKeys/id_rsa");
    }
    
    public static function GetGerritUrl() {
        return "10.38.250.14:29418";
    }
}

?>

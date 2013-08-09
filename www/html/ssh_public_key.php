<?php
 include('Net/SSH2.php');
 include('Crypt/RSA.php');
require_once("util.php");

class ssh_public_key
{
	private $connection;

	function __construct()
	{
		$this->connection = util::GetDBConnection("gerrit");

	}
	function __destruct()
	{
		mysqli_close($this->connection);
	}
	public function get_records($email)
	{
		$sql_query_ssh = "SELECT ssh_public_key,valid,seq,b.account_id FROM account_ssh_keys 
AS a JOIN accounts AS b on a.account_id= b.account_id WHERE b.preferred_email='$email'";
		$arr = array();
		$rs = mysqli_query($this->connection,$sql_query_ssh);
		$string = "";
		$step=0;
		while($row = mysqli_fetch_row($rs)){
			$ssh_key = substr($row[0],0,100);
			$string = $string."<tr style='height:25px;";
			if ($step==0)
			{
				$string = $string."background:#f4f4f4;";
				$step=1;
			}
			else
			{
				$step=0;
			}
			
			
			$string = $string."'><td style='font-size:13px;padding-left:10px' >$ssh_key...</td><td><input type=\"button\" value=\"delete\" onclick=\"deleteSSH($row[3],$row[2]);\"></td></tr>";
		}
		return $string;
	}
	public function add($ssh_key,$email){
		$query_account_id = "SELECT account_id FROM accounts WHERE preferred_email='$email'";
		$result = mysqli_query($this->connection,$query_account_id);
		$row = mysqli_fetch_row($result);
		$account_id = $row[0];
		
		$query_max_sql = "SELECT MAX(seq) from account_ssh_keys WHERE account_id=$account_id";
		$result2 = mysqli_query($this->connection,$query_max_sql);
		$row2 = mysqli_fetch_row($result2);
		$seq = $row2[0];
		$seq = $seq+1;
		
		$sql_insert = "INSERT INTO account_ssh_keys(ssh_public_key,valid,seq,account_id) VALUES('$ssh_key','Y','$seq','$account_id')";
		$this->execute_command($sql_insert);
                $this->excute_ssh();
                
	}
	
	public function delete($account_id,$seq){
		$sql_delete = "DELETE FROM account_ssh_keys WHERE account_id=$account_id and seq=$seq";
		$this->execute_command($sql_delete);
                $this->excute_ssh();
	}


	public function execute_command($sql_command_text)
	{
		mysqli_query($this->connection,$sql_command_text);
	}
        
        public function  excute_ssh(){
            $key=new Crypt_RSA();                    
            $key->loadKey(util::GetGerritKey());                    
            $ssh=new Net_SSH2(util::GetGerritServer(),29418);                
            if (!$ssh->login(util::GetGerritAdmin(), $key)) {
                die('err');
            }
            else
            {
                $ssh->exec("gerrit flush-caches --cache sshkeys", TRUE);                            
            }
        }
}
?>

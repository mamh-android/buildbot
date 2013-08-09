function setCookie(name, value, hour)
{
    var time = hour;
    var exp  = new Date();  
    exp.setTime(exp.getTime() + time*60*60*1000);
    document.cookie = name + "="+ escape (value) + ";expires=" + exp.toGMTString() + ";path=/";
}
function getCookie(name)  
{
    var arr = document.cookie.match(new RegExp("(^| )"+name+"=([^;]*)(;|$)"));
    if(arr != null) 
	 	return unescape(arr[2]); 
	return null;
}
function delCookie(name)
{
    var exp = new Date();
    exp.setTime(exp.getTime() - 1);
    var cval = getCookie(name);
    if(cval != null) 
		document.cookie = name + "=" + cval + ";expires=" + exp.toGMTString() + ";path=/";
}
function loginOut()
{
	var t = confirm("Are you sure to quit?");
	if (t)
	{
		delCookie('username');
		delCookie('dispname');
		delCookie('email');
		delCookie('lhref');
	}
	location.reload();
}

function jumpCookie()
{
	var lhref = getCookie("lhref");
	if(lhref != null &&  lhref.charAt(lhref.length-1) != "/")
	{		
		window.location.href = getCookie("lhref");
	}
	delCookie("lhref");
}

function checksamebranch()
{
	if(getCookie("samebranch"))
	{
		alert("The build with  same branchname   " + getCookie("samebranch") + "  is  running or pending, please try later or input the other branch...");
		delCookie("samebranch");
	}
}

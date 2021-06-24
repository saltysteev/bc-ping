feather.replace();

function getXML() {
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    refreshTable(this);
  }
  };
  xmlhttp.open("GET", "event_log.xml", true);
  xmlhttp.send();
}

function refreshTable(xml) {
  var i;
  var xmlDoc = xml.responseXML;
  var tbody="";
  var x = xmlDoc.getElementsByTagName("item");
  for (i = 0; i <x.length; i++) {
    tbody += "<tr><td>" +
    x[i].getElementsByTagName("name")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("date")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("duration")[0].childNodes[0].nodeValue +
    "</td></tr>";
  }
  document.getElementById("eventtable").innerHTML = tbody;
  filterFunction();
}
function filterFunction() {
	var input, filter, tr;
	input = document.getElementById("mInput");
	filter = input.value.toUpperCase();
	div = document.getElementById("eventtable");
	tr = div.getElementsByTagName("tr");
	for (i = 0; i < tr.length; i++) {
		txtVal = tr[i].textContent || tr[i].innerText;
		if (txtVal.toUpperCase().indexOf(filter) > -1) {
			tr[i].style.display = "";
		} else {
			tr[i].style.display = "none";
		}
	}
}

getXML();
var vTimer = setInterval(getXML, 10000);
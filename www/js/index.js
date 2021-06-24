feather.replace();

function getXML() {
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    refreshTable(this);
  }
  };
  xmlhttp.open("GET", "hosts.xml", true);
  xmlhttp.send();
}

function refreshTable(xml) {
  var i;
  var xmlDoc = xml.responseXML;
  var tbody="";
  var x = xmlDoc.getElementsByTagName("item");
  var onlist = 0;
  var offlist = 0;
  for (i = 0; i <x.length; i++) {
    if (x[i].getElementsByTagName("status")[0].childNodes[0].nodeValue == "online") {
	onlist += 1;
    }
    if (x[i].getElementsByTagName("status")[0].childNodes[0].nodeValue == "offline") {
	offlist += 1;
    }
    tbody += "<tr class='" + x[i].getElementsByTagName("css")[0].childNodes[0].nodeValue + "'><td class='" +
    x[i].getElementsByTagName("status")[0].childNodes[0].nodeValue + "'></td><td>" +
    x[i].getElementsByTagName("name")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("ip")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("address")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("phone")[0].childNodes[0].nodeValue +
    "</td><td>" +
    x[i].getElementsByTagName("duration")[0].childNodes[0].nodeValue +
    "</td></tr>";
  }
  document.getElementById("demo").innerHTML = tbody;
  document.getElementById("onlist").innerHTML = onlist;
  document.getElementById("offlist").innerHTML = offlist;
  filterFunction();
}
function filterFunction() {
	var input, filter, tr;
	input = document.getElementById("mInput");
	filter = input.value.toUpperCase();
	div = document.getElementById("demo");
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
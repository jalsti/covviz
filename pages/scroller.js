

function scroll_rightmost() {
	console.log("begin scrolling");
	
	
	try {
		// var element = document.getElementById("caption_kreise");
		var element = document.getElementById("tablediv_kreise");
		//console.log(element);
		// var sLeft = element.scrollLeft;
		// console.log(sLeft);
		element.scrollLeft=element.scrollWidth;
	} catch { };
	
	
	try{
		var element = document.getElementById("tablediv_bundeslaender");
		element.scrollLeft=element.scrollWidth;
	} catch { };
}
	
	
function expand_table_div(tablediv_id){
	console.log("expand");
	var element = document.getElementById(tablediv_id);
	if (element.style["max-height"]!='none'){
		element.style["max-height"]='none';
	} else {
		element.style.removeProperty("max-height");
	}
	
}
	
